"""Tool policy engine — the gateway's guardrail layer.

Enforcement order (each step can only narrow, never widen, permission):

  1. Tool exists in the registry.
  2. PROHIBITED gate: risk_tier == 'prohibited' is denied unconditionally —
     before role, scope, or quota are even considered. Neither the agent,
     a privileged caller, nor an approval flow can bypass this.
  3. Role authorization: caller's role must satisfy required_role.
  4. Scope-based argument rules (e.g. scope=team requires manager+).
  5. Manager scope check.
  6. Argument validation: required args present, enum membership, numeric
     bounds, string length caps, pattern match — all BEFORE the executor
     touches any adapter.
  7. Tenant quota / rate limit (pluggable provider for deterministic tests).

Approval semantics:
  - risk_tier == 'approval_required' -> the orchestrator creates an approval
    record instead of executing. Execution happens only via the approval
    endpoint, which RE-RUNS this full policy check with the original caller
    context. Approval never bypasses policy.
  - risk_tier == 'prohibited' can never reach the approval path: check()
    denies it here, and the approval endpoint re-checks anyway.

Every decision (allow or deny) is written to tool_calls with
policy_decision, policy_reason, and risk_tier.
"""
from __future__ import annotations

import re
from collections.abc import Callable

from ...db import service_client
from ...services.quota_service import get_tenant as _default_get_tenant
from .registry import ToolDef, ToolRegistry

ROLE_RANK = {"viewer": 0, "employee": 1, "manager": 2, "admin": 3}

# Tests can monkey-patch this to a function that returns None to skip the
# quota check, or to a static dict for deterministic limits.
quota_provider: Callable[[str], dict | None] = _default_get_tenant


class PolicyDecision:
    def __init__(self, allow: bool, reason: str, tool_def: ToolDef | None = None,
                 risk_tier: str = "auto"):
        self.allow = allow
        self.reason = reason
        self.tool_def = tool_def
        self.risk_tier = risk_tier if tool_def else "auto"


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

    tier = td.schema.risk_tier

    # PROHIBITED gate: structural denial. Runs before authorization so that
    # even an admin cannot route a prohibited action through the gateway.
    if tier == "prohibited":
        return PolicyDecision(
            False,
            f"prohibited action: '{tool_name}' cannot be executed through the gateway",
            td,
            tier,
        )

    caller_role = caller.get("role", "viewer")
    required = td.schema.required_role
    if ROLE_RANK.get(caller_role, 0) < ROLE_RANK.get(required, 0):
        return PolicyDecision(
            False,
            f"role '{caller_role}' not allowed; tool requires '{required}'",
            td,
            tier,
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
                tier,
            )

    if td.schema.needs_manager_scope and not _is_manager_or_admin(caller):
        return PolicyDecision(False, "manager scope required", td, tier)

    if not _validate_args(arguments, td.schema.parameters):
        return PolicyDecision(False, "argument schema validation failed", td, tier)

    constraint_error = _validate_constraints(arguments, td.schema.constraints)
    if constraint_error:
        return PolicyDecision(False, f"argument constraint violation: {constraint_error}", td, tier)

    quota = quota_provider(caller["tenant_id"])
    if quota:
        if quota.get("monthly_message_count", 0) >= quota.get("max_messages_per_month", 1_000_000):
            return PolicyDecision(False, "tenant message quota exceeded", td, tier)

    return PolicyDecision(True, "allowed", td, tier)


def _is_manager_or_admin(caller: dict) -> bool:
    return caller.get("role") in ("manager", "admin")


def _validate_args(args: dict, schema: dict) -> bool:
    for key, spec in schema.items():
        if spec.get("required") and key not in args:
            return False
    return True


def _validate_constraints(args: dict, constraints: dict) -> str | None:
    """Enforce declared argument constraints. Returns an error string or None.

    Checked here — in the gateway, before the executor — so that malformed
    or malicious arguments (e.g. service='*', replicas=10000, unknown
    environments) never reach an adapter.
    """
    for key, rule in (constraints or {}).items():
        if key not in args:
            continue  # absence is handled by required-arg validation
        value = args[key]
        if "enum" in rule and value not in rule["enum"]:
            return f"{key}='{value}' not in allowed values {rule['enum']}"
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "min" in rule and value < rule["min"]:
                return f"{key}={value} below minimum {rule['min']}"
            if "max" in rule and value > rule["max"]:
                return f"{key}={value} above maximum {rule['max']}"
        if isinstance(value, str):
            if "max_length" in rule and len(value) > rule["max_length"]:
                return f"{key} exceeds maximum length {rule['max_length']}"
            if "pattern" in rule and not re.match(rule["pattern"], value):
                return f"{key} does not match required pattern"
    return None


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
    risk_tier: str | None = None,
) -> None:
    try:
        row = {
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
        if risk_tier:
            row["risk_tier"] = risk_tier
        service_client().table("tool_calls").insert(row).execute()
    except Exception:
        # Audit logging must never break the request.
        pass
