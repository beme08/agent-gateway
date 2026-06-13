"""Tool policy engine.

Checks (in order):
  1. Tool exists in the registry.
  2. Caller's role satisfies the tool's required_role.
  3. Scope-based argument rules (e.g. scope=team requires manager+).
  4. (Optional) Manager scope check.
  5. Arguments validate against the tool's parameter schema (lightweight).
  6. Tenant quota / rate limit (delegated to a pluggable provider so unit
     tests can skip the Supabase round-trip).

Writes a tool_calls row for every decision (allow or deny) with
policy_decision and policy_reason.
"""
from __future__ import annotations

import time
from typing import Any, Callable, Optional

from .registry import ToolRegistry, ToolDef
from ...db import service_client
from ...services.quota_service import get_tenant as _default_get_tenant


ROLE_RANK = {"viewer": 0, "employee": 1, "manager": 2, "admin": 3}

# Tests can monkey-patch this to a function that returns None to skip the
# quota check, or to a static dict for deterministic limits.
quota_provider: Callable[[str], Optional[dict]] = _default_get_tenant


class PolicyDecision:
    def __init__(self, allow: bool, reason: str, tool_def: Optional[ToolDef] = None):
        self.allow = allow
        self.reason = reason
        self.tool_def = tool_def


# Tool-specific scope rules. The handler also enforces them, but the
# policy layer rejects early so we never invoke the handler for an
# obviously-wrong call.
_SCOPE_RULES = {
    "get_time_off_requests": {
        # If caller asks for scope=team, require manager or admin.
        "team": {"min_role": "manager"},
    },
}


def check(
    registry: ToolRegistry,
    caller: dict,
    tool_name: str,
    arguments: dict,
) -> PolicyDecision:
    td = registry.get(tool_name)
    if not td:
        return PolicyDecision(False, f"unknown tool '{tool_name}'")

    caller_role = caller.get("role", "viewer")
    required = td.schema.required_role
    if ROLE_RANK.get(caller_role, 0) < ROLE_RANK.get(required, 0):
        return PolicyDecision(
            False,
            f"role '{caller_role}' not allowed; tool requires '{required}'",
            td,
        )

    # Scope-based rules: e.g. scope=team on get_time_off_requests.
    tool_rules = _SCOPE_RULES.get(tool_name, {})
    scope = arguments.get("scope")
    if scope in tool_rules:
        min_role = tool_rules[scope]["min_role"]
        if ROLE_RANK.get(caller_role, 0) < ROLE_RANK.get(min_role, 0):
            return PolicyDecision(
                False,
                f"scope='{scope}' requires role '{min_role}' or higher",
                td,
            )

    if td.schema.needs_manager_scope and not _is_manager_or_admin(caller):
        return PolicyDecision(False, "manager scope required", td)

    if not _validate_args(arguments, td.schema.parameters):
        return PolicyDecision(False, "argument schema validation failed", td)

    quota = quota_provider(caller["tenant_id"])
    if quota:
        if quota.get("monthly_message_count", 0) >= quota.get("max_messages_per_month", 1_000_000):
            return PolicyDecision(False, "tenant message quota exceeded", td)

    return PolicyDecision(True, "allowed", td)


def _is_manager_or_admin(caller: dict) -> bool:
    return caller.get("role") in ("manager", "admin")


def _validate_args(args: dict, schema: dict) -> bool:
    for key, spec in schema.items():
        if spec.get("required") and key not in args:
            return False
    return True


def record(
    tenant_id: str,
    user_id: str,
    trace_id: str | None,
    tool_name: str,
    arguments: dict,
    result: dict | None,
    status: str,
    required_role: str | None,
    caller_role: str,
    policy_decision: str,
    policy_reason: str,
    latency_ms: int,
) -> None:
    try:
        service_client().table("tool_calls").insert(
            {
                "tenant_id": tenant_id,
                "trace_id": trace_id,
                "user_id": user_id,
                "tool_name": tool_name,
                "arguments": arguments,
                "result": result,
                "status": status,
                "required_role": required_role,
                "caller_role": caller_role,
                "policy_decision": policy_decision,
                "policy_reason": policy_reason,
                "latency_ms": latency_ms,
            }
        ).execute()
    except Exception:
        # Audit logging must never break the request.
        pass
