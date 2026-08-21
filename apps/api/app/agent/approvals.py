"""Human approval lifecycle for risk-tiered agent actions.

Guardrail semantics:
  - An approval record is created by the ORCHESTRATOR when the policy engine
    classifies a proposed action as approval_required. The action is NOT
    executed at proposal time.
  - approve(): re-runs the FULL policy check with the ORIGINAL caller context
    and original arguments before executing. Approval never bypasses policy:
    if the re-check denies (role changed, quota exhausted, argument invalid,
    or the tool is prohibited), the approval is rejected with the reason and
    nothing executes.
  - reject(): records the human decision; no execution path exists.
  - Prohibited tools can never obtain an approval record in the first place
    (the policy engine denies them before any execution branch), and this
    module re-checks anyway — structural, not instructional.
"""
from __future__ import annotations

from datetime import UTC, datetime

from ..db import service_client
from .tools.executor import execute as exec_tool
from .tools.policy import check as policy_check
from .tools.policy import record as record_tool_call
from .tools.registry import ToolRegistry


def create_approval(
    tenant_id: str,
    trace_id: str | None,
    user_id: str,
    tool_name: str,
    arguments: dict,
    risk_tier: str,
    reason: str,
    context: dict | None = None,
) -> str:
    res = service_client().table("action_approvals").insert({
        "tenant_id": tenant_id,
        "trace_id": trace_id,
        "requested_by": user_id,
        "tool_name": tool_name,
        "arguments": arguments,
        "risk_tier": risk_tier,
        "reason": reason,
        "status": "pending",
        "context": context or {},
    }).execute()
    return res.data[0]["id"]


def list_approvals(tenant_id: str, status: str | None = None) -> list[dict]:
    q = service_client().table("action_approvals").select("*").eq("tenant_id", tenant_id)
    if status:
        q = q.eq("status", status)
    return q.order("created_at", desc=True).limit(100).execute().data or []


def get_approval(tenant_id: str, approval_id: str) -> dict | None:
    res = (
        service_client()
        .table("action_approvals")
        .select("*")
        .eq("tenant_id", tenant_id)
        .eq("id", approval_id)
        .single()
        .execute()
    )
    return res.data or None


async def decide(
    registry: ToolRegistry,
    tenant_id: str,
    approver_user_id: str,
    approver_role: str,
    approval_id: str,
    decision: str,
    note: str | None = None,
) -> dict:
    """Approve or reject a pending approval.

    On approve: re-run the full policy check with the ORIGINAL requester's
    context, then execute through the standard executor. Returns a result
    dict describing what happened; every outcome is persisted.
    """
    approval = get_approval(tenant_id, approval_id)
    if not approval:
        raise ValueError("approval not found")
    if approval["status"] != "pending":
        raise ValueError(f"approval already {approval['status']}")

    now = datetime.now(UTC).isoformat()

    if decision == "reject":
        service_client().table("action_approvals").update({
            "status": "rejected",
            "decided_by": approver_user_id,
            "decision_note": note,
            "decided_at": now,
        }).eq("id", approval_id).execute()
        _append_ticket_event_for_approval(tenant_id, approval, "approval_rejected",
                                          {"approver": approver_user_id, "note": note})
        return {"approval_id": approval_id, "status": "rejected"}

    # ---- approve path: policy is authoritative, approval is not -------------
    tool_name = approval["tool_name"]
    arguments = approval.get("arguments") or {}
    requester_id = approval["requested_by"]
    requester_role = _role_for(tenant_id, requester_id)

    caller_ctx = {
        "user_id": requester_id,
        "tenant_id": tenant_id,
        "role": requester_role,
        "trace_id": approval.get("trace_id"),
        "ticket_id": (approval.get("context") or {}).get("ticket_id"),
    }
    verdict = policy_check(registry, caller_ctx, tool_name, arguments)

    if not verdict.allow:
        # Includes the prohibited gate: even a hand-crafted approval row for a
        # prohibited tool dies here.
        service_client().table("action_approvals").update({
            "status": "rejected",
            "decided_by": approver_user_id,
            "decision_note": f"policy re-check denied: {verdict.reason}",
            "decided_at": now,
        }).eq("id", approval_id).execute()
        record_tool_call(
            tenant_id, requester_id, approval.get("trace_id"), tool_name, arguments,
            {"status": "denied_at_approval"}, "denied",
            verdict.tool_def.schema.required_role if verdict.tool_def else None,
            requester_role, "deny", f"approval re-check: {verdict.reason}", 0,
            risk_tier=verdict.risk_tier,
        )
        _append_ticket_event_for_approval(tenant_id, approval, "approval_blocked_by_policy",
                                          {"tool": tool_name, "reason": verdict.reason})
        return {
            "approval_id": approval_id, "status": "blocked_by_policy",
            "reason": verdict.reason,
        }

    result = await exec_tool(verdict.tool_def, arguments, caller_ctx)
    executed_ok = bool(result.get("ok"))
    service_client().table("action_approvals").update({
        "status": "executed" if executed_ok else "failed",
        "decided_by": approver_user_id,
        "decision_note": note,
        "decided_at": now,
        "executed_at": now if executed_ok else None,
        "execution_result": result.get("data") or {"error": result.get("error")},
    }).eq("id", approval_id).execute()

    record_tool_call(
        tenant_id, requester_id, approval.get("trace_id"), tool_name, arguments,
        result.get("data") or {"error": result.get("error")},
        "allowed" if executed_ok else "error",
        verdict.tool_def.schema.required_role, requester_role,
        "allow:approved_execution", f"approved by {approver_role}", result.get("latency_ms", 0),
        risk_tier=verdict.risk_tier,
    )
    _append_ticket_event_for_approval(tenant_id, approval, "approval_executed" if executed_ok else "execution_failed",
                                      {"tool": tool_name, "result": result.get("data") or {"error": result.get("error")}})
    return {
        "approval_id": approval_id,
        "status": "executed" if executed_ok else "failed",
        "result": result.get("data") or {"error": result.get("error")},
    }


def _role_for(tenant_id: str, user_id: str) -> str:
    res = (
        service_client()
        .table("tenant_memberships")
        .select("role")
        .eq("tenant_id", tenant_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return (res.data or [{"role": "viewer"}])[0]["role"]


def _append_ticket_event_for_approval(tenant_id: str, approval: dict, event_type: str, detail: dict) -> None:
    """Best-effort ticket timeline entry when the approval is linked to one."""
    ticket_id = (approval.get("context") or {}).get("ticket_id")
    if not ticket_id:
        return
    try:
        service_client().table("ticket_events").insert({
            "tenant_id": tenant_id,
            "ticket_id": ticket_id,
            "event_type": event_type,
            "actor": "human",
            "detail": detail,
        }).execute()
    except Exception:
        pass
