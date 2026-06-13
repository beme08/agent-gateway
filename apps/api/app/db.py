"""Supabase client singletons. Service-role client bypasses RLS for trusted
backend operations (tool execution, ingestion). User-scoped clients are
created per-request from a verified JWT to enforce RLS.

Imports of the supabase package are deferred so unit tests that exercise
tool policies, RAG chunking, prompt-injection detection, and ACL helpers do
not require supabase to be installed.
"""
from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from supabase import Client


@lru_cache
def service_client() -> "Client":
    from supabase import create_client
    from .config import get_settings
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_role_key)


def user_client(access_token: str) -> "Client":
    from supabase import create_client
    from .config import get_settings
    s = get_settings()
    client = create_client(s.supabase_url, s.supabase_anon_key)
    client.postgrest.auth(access_token)
    return client


def clear_caches() -> None:
    service_client.cache_clear()
