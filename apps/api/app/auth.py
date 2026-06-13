"""JWT verification + caller context derivation.

The agent never trusts client-supplied tenant/role flags. Every request
must carry a Supabase JWT, which we verify against the project's JWT
secret, then look up the tenant memberships server-side to derive the
caller's role for the selected tenant.
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


def verify_jwt(token: str) -> dict:
    s = get_settings()
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
