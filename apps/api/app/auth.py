"""JWT verification + caller context derivation.

The agent never trusts client-supplied tenant/role flags. Every request
must carry a Supabase JWT, which we verify against the project's signing
keys, then look up the tenant memberships server-side to derive the
caller's role for the selected tenant.

Supabase projects issue asymmetric (ES256) tokens verified against the
project JWKS; legacy projects issue symmetric (HS256) tokens verified
against the JWT secret. We support both.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, status

from .config import get_settings
from .db import service_client


@dataclass
class CallerContext:
    user_id: str
    email: str
    tenant_id: str
    role: str
    manager_user_id: Optional[str] = None


_jwks_keys: dict[str, str] = {}


def _jwks_signing_key(token: str) -> str | None:
    """Resolve the public key for a token from the project JWKS (ES256 etc.)."""
    s = get_settings()
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            return None
        if kid not in _jwks_keys:
            import httpx

            r = httpx.get(
                f"{s.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json",
                timeout=10,
            )
            r.raise_for_status()
            for k in r.json().get("keys", []):
                _jwks_keys[k["kid"]] = k
        jwk = _jwks_keys.get(kid)
        if not jwk:
            return None
        from jwt.algorithms import RSAAlgorithm, ECAlgorithm

        if jwk.get("kty") == "RSA":
            return RSAAlgorithm.from_jwk(jwk)
        if jwk.get("kty") == "EC":
            return ECAlgorithm.from_jwk(jwk)
        return None
    except Exception:
        return None


def verify_jwt(token: str) -> dict:
    s = get_settings()
    # Try asymmetric verification against the project JWKS first (ES256/RS256).
    pub_key = _jwks_signing_key(token)
    if pub_key is not None:
        try:
            return jwt.decode(
                token,
                pub_key,
                algorithms=["ES256", "RS256", "ES384", "RS384"],
                audience="authenticated",
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "token expired")
        except jwt.InvalidTokenError:
            # fall through to legacy symmetric verification
            pass
    # Legacy symmetric verification against the JWT secret (HS256).
    try:
        return jwt.decode(token, s.supabase_jwt_secret, algorithms=["HS256"], audience="authenticated")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"invalid token: {e}")


def _membership_for(user_id: str, tenant_id: str) -> Optional[dict]:
    res = (
        service_client()
        .table("tenant_memberships")
        .select("role, manager_user_id, tenant_id")
        .eq("user_id", user_id)
        .eq("tenant_id", tenant_id)
        .limit(1)
        .execute()
    )
    if not res.data:
        return None
    return res.data[0]


async def get_caller(
    x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    authorization: Optional[str] = Header(default=None),
) -> CallerContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    claims = verify_jwt(token)
    user_id = claims.get("sub")
    email = claims.get("email") or ""
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing sub claim")

    if not x_tenant_id:
        # Default to the user's first membership.
        memberships = (
            service_client()
            .table("tenant_memberships")
            .select("tenant_id, role, manager_user_id")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if not memberships.data:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "no tenant memberships")
        m = memberships.data[0]
        return CallerContext(
            user_id=user_id,
            email=email,
            tenant_id=m["tenant_id"],
            role=m["role"],
            manager_user_id=m.get("manager_user_id"),
        )

    m = _membership_for(user_id, x_tenant_id)
    if not m:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "not a member of this tenant")
    return CallerContext(
        user_id=user_id,
        email=email,
        tenant_id=x_tenant_id,
        role=m["role"],
        manager_user_id=m.get("manager_user_id"),
    )
