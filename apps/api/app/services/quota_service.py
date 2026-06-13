"""Per-tenant quota + rate-limit helper. In production it queries Supabase;
in unit tests the policy engine can inject a `quota_provider` that returns
a static dict (or None to skip the check)."""
from __future__ import annotations

from typing import Callable, Optional

from ..db import service_client


def default_quota_provider(tenant_id: str) -> Optional[dict]:
    try:
        res = (
            service_client()
            .table("tenants")
            .select("max_messages_per_month, monthly_message_count")
            .eq("id", tenant_id)
            .single()
            .execute()
        )
        return res.data
    except Exception:
        return None


def get_tenant(tenant_id: str) -> Optional[dict]:
    return default_quota_provider(tenant_id)


def get_tenant_usage(tenant_id: str) -> Optional[dict]:
    return get_tenant(tenant_id)


def increment_message_count(tenant_id: str) -> None:
    _simple_increment(tenant_id, "monthly_message_count")


def increment_tool_call_count(tenant_id: str) -> None:
    _simple_increment(tenant_id, "monthly_tool_call_count")


def _simple_increment(tenant_id: str, column: str) -> None:
    try:
        t = get_tenant(tenant_id)
        if not t:
            return
        new_val = (t.get(column) or 0) + 1
        service_client().table("tenants").update({column: new_val}).eq("id", tenant_id).execute()
    except Exception:
        pass
