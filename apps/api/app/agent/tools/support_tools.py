"""Support Operations tool definitions + handlers.

These wrap the integration adapters (ticketing, observability, deployment,
github, slack) and the RAG layer. Registered alongside the HR tools in the
shared registry — one gateway, multiple environments.

Risk tiers (enforced by the policy engine, not by prompts):
  auto              query_service_health, get_recent_deployments, get_ticket,
                    update_ticket, search_knowledge, verify_service_health,
                    create_github_issue, notify_slack, restart_service
  approval_required scale_service, rollback_deployment
  prohibited        delete_production_data

Verification gate: every mutating action returns an adapter-produced
``verification`` block and records a remediation_actions row whose outcome is
'executed' only when the post-condition is met, else 'verification_failed'.
"""
from __future__ import annotations

from ...db import service_client
from ...integrations import (
    AdapterError,
    get_deployment,
    get_github,
    get_observability,
    get_slack,
    get_ticketing,
)
from ..tools.registry import ToolSchema
from .definitions import _search_documents  # reuse the RAG-backed search

# ----- read / triage ---------------------------------------------------------

get_ticket_schema = ToolSchema(
    name="get_ticket",
    description="Read a support ticket's full content, status, severity, and timeline events.",
    required_role="viewer",
    parameters={
        "ticket_id": {"type": "string", "description": "UUID of the ticket.", "required": True},
    },
)


async def _get_ticket(arguments: dict, context: dict) -> dict:
    ticket = get_ticketing().get_ticket(context["tenant_id"], arguments["ticket_id"])
    events = (
        service_client()
        .table("ticket_events")
        .select("*")
        .eq("ticket_id", arguments["ticket_id"])
        .order("created_at")
        .execute()
        .data
        or []
    )
    return {"ticket": ticket, "events": events}


update_ticket_schema = ToolSchema(
    name="update_ticket",
    description="Update a support ticket's status/severity and append a note to its timeline.",
    required_role="employee",
    parameters={
        "ticket_id": {"type": "string", "description": "UUID of the ticket.", "required": True},
        "status": {"type": "string", "description": "New status.", "required": False},
        "note": {"type": "string", "description": "Timeline note describing what was done/found.", "required": False},
    },
    constraints={"status": {"enum": ["open", "triaged", "in_progress", "pending_approval",
                                     "remediating", "verifying", "resolved", "blocked", "closed"]}},
)

TICKET_STATUSES = set(update_ticket_schema.constraints["status"]["enum"])


async def _update_ticket(arguments: dict, context: dict) -> dict:
    tid = arguments["ticket_id"]
    fields = {}
    if arguments.get("status"):
        if arguments["status"] not in TICKET_STATUSES:
            return {"error": f"invalid status '{arguments['status']}'"}
        fields["status"] = arguments["status"]
    updated = get_ticketing().update_ticket(context["tenant_id"], tid, **fields)
    if arguments.get("note"):
        get_ticketing().append_event(
            context["tenant_id"], tid, "note", "agent",
            {"note": arguments["note"]}, trace_id=context.get("trace_id"),
        )
    return {"ticket": updated}


search_knowledge_schema = ToolSchema(
    name="search_knowledge",
    description="Semantic search over runbooks, incident history, and policy documents. Cite title and section.",
    required_role="viewer",
    parameters={
        "query": {"type": "string", "description": "Natural-language search query.", "required": True},
        "top_k": {"type": "integer", "description": "Number of chunks (1-10).", "required": False},
    },
)


async def _search_knowledge(arguments: dict, context: dict) -> dict:
    return await _search_documents(arguments, context)


# ----- diagnosis -------------------------------------------------------------

query_service_health_schema = ToolSchema(
    name="query_service_health",
    description="Read live health signals for a service: status, error rate, p99 latency, version.",
    required_role="employee",
    parameters={
        "service": {"type": "string", "description": "Service name, e.g. checkout-api.", "required": True},
    },
    constraints={"service": {"enum": ["checkout-api", "payments-api", "search-api", "web-frontend", "analytics"]}},
)


async def _query_service_health(arguments: dict, context: dict) -> dict:
    try:
        return get_observability().get_service_health(arguments["service"])
    except AdapterError as e:
        return {"error": str(e)}


get_recent_deployments_schema = ToolSchema(
    name="get_recent_deployments",
    description="List recent deployments for a service (version, time, status).",
    required_role="employee",
    parameters={
        "service": {"type": "string", "description": "Service name.", "required": True},
    },
    constraints={"service": {"enum": ["checkout-api", "payments-api", "search-api", "web-frontend", "analytics"]}},
)


async def _get_recent_deployments(arguments: dict, context: dict) -> dict:
    try:
        return get_deployment().get_recent_deployments(arguments["service"])
    except AdapterError as e:
        return {"error": str(e)}


# ----- remediation -----------------------------------------------------------

def _record_remediation(context: dict, tool_name: str, arguments: dict, result: dict) -> None:
    """Persist remediation evidence. Outcome reflects the verification gate."""
    try:
        verification = result.get("verification") or {}
        met = bool(verification.get("post_condition_met"))
        service_client().table("remediation_actions").insert({
            "tenant_id": context["tenant_id"],
            "ticket_id": context.get("ticket_id"),
            "trace_id": context.get("trace_id"),
            "tool_name": tool_name,
            "arguments": arguments,
            "outcome": "executed" if met else "verification_failed",
            "verification": verification,
        }).execute()
    except Exception:
        pass


restart_service_schema = ToolSchema(
    name="restart_service",
    description="Restart a service instance to clear transient faults (e.g. connection pool exhaustion). Low-risk, auto-executes, then verifies health.",
    required_role="manager",
    parameters={
        "service": {"type": "string", "description": "Service name.", "required": True},
        "environment": {"type": "string", "description": "staging or production.", "required": True},
    },
    constraints={
        "service": {"enum": ["checkout-api", "payments-api", "search-api", "web-frontend", "analytics"]},
        "environment": {"enum": ["staging", "production"]},
    },
)


async def _restart_service(arguments: dict, context: dict) -> dict:
    result = get_deployment().restart_service(arguments["service"], arguments["environment"])
    _record_remediation(context, "restart_service", arguments, result)
    return result


scale_service_schema = ToolSchema(
    name="scale_service",
    description="Change replica count for a service. REQUIRES HUMAN APPROVAL — calling this creates an approval request; it does not execute.",
    required_role="manager",
    parameters={
        "service": {"type": "string", "description": "Service name.", "required": True},
        "environment": {"type": "string", "description": "staging or production.", "required": True},
        "replicas": {"type": "integer", "description": "Target replica count (2-12).", "required": True},
    },
    constraints={
        "service": {"enum": ["checkout-api", "payments-api", "search-api", "web-frontend", "analytics"]},
        "environment": {"enum": ["staging", "production"]},
        "replicas": {"min": 2, "max": 12},
    },
    risk_tier="approval_required",
)


async def _scale_service(arguments: dict, context: dict) -> dict:
    # Reached only after human approval (policy re-check passed there).
    result = get_deployment().scale_service(
        arguments["service"], arguments["environment"], int(arguments["replicas"]),
    )
    _record_remediation(context, "scale_service", arguments, result)
    return result


rollback_deployment_schema = ToolSchema(
    name="rollback_deployment",
    description="Roll a service back to a previous version. REQUIRES HUMAN APPROVAL — calling this creates an approval request; it does not execute.",
    required_role="manager",
    parameters={
        "service": {"type": "string", "description": "Service name.", "required": True},
        "environment": {"type": "string", "description": "staging or production.", "required": True},
        "to_version": {"type": "string", "description": "Target version, e.g. v1.9.0.", "required": True},
    },
    constraints={
        "service": {"enum": ["checkout-api", "payments-api", "search-api", "web-frontend", "analytics"]},
        "environment": {"enum": ["staging", "production"]},
        "to_version": {"pattern": r"^v\d+\.\d+\.\d+$", "max_length": 20},
    },
    risk_tier="approval_required",
)


async def _rollback_deployment(arguments: dict, context: dict) -> dict:
    result = get_deployment().rollback_deployment(
        arguments["service"], arguments["environment"], arguments["to_version"],
    )
    _record_remediation(context, "rollback_deployment", arguments, result)
    return result


delete_production_data_schema = ToolSchema(
    name="delete_production_data",
    description="Delete a production dataset. PROHIBITED: the gateway blocks this unconditionally — no role or approval can authorize it.",
    required_role="admin",
    parameters={
        "dataset": {"type": "string", "description": "Dataset identifier.", "required": True},
        "environment": {"type": "string", "description": "Target environment.", "required": True},
    },
    risk_tier="prohibited",
)


async def _delete_production_data(arguments: dict, context: dict) -> dict:
    # Unreachable through the gateway: the policy engine denies this tool
    # before any execution path. Kept as a handler for completeness so the
    # registry schema stays honest about what the tool WOULD do.
    raise AdapterError("blocked by gateway policy")


# ----- verification & notifications ------------------------------------------

verify_service_health_schema = ToolSchema(
    name="verify_service_health",
    description="Verify a service's post-remediation state. Returns the health snapshot and whether the expectation is met. A remediation is not successful until this passes.",
    required_role="employee",
    parameters={
        "service": {"type": "string", "description": "Service name.", "required": True},
        "expected_status": {"type": "string", "description": "Expected status (default healthy).", "required": False},
    },
    constraints={
        "service": {"enum": ["checkout-api", "payments-api", "search-api", "web-frontend", "analytics"]},
        "expected_status": {"enum": ["healthy", "degraded", "down"]},
    },
)


async def _verify_service_health(arguments: dict, context: dict) -> dict:
    try:
        health = get_observability().get_service_health(arguments["service"])
    except AdapterError as e:
        return {"error": str(e), "post_condition_met": False}
    expected = arguments.get("expected_status", "healthy")
    health["expected_status"] = expected
    health["post_condition_met"] = health["status"] == expected
    return health


create_github_issue_schema = ToolSchema(
    name="create_github_issue",
    description="File a GitHub issue to track engineering follow-up work.",
    required_role="employee",
    parameters={
        "title": {"type": "string", "description": "Issue title.", "required": True},
        "body": {"type": "string", "description": "Issue body with diagnostic evidence.", "required": True},
        "labels": {"type": "string", "description": "Comma-separated labels.", "required": False},
    },
    constraints={"title": {"max_length": 200}, "body": {"max_length": 4000}},
)


async def _create_github_issue(arguments: dict, context: dict) -> dict:
    labels = [l.strip() for l in (arguments.get("labels") or "").split(",") if l.strip()]
    return get_github().create_issue(arguments["title"], arguments["body"], labels)


notify_slack_schema = ToolSchema(
    name="notify_slack",
    description="Post a notification message to a Slack channel.",
    required_role="employee",
    parameters={
        "channel": {"type": "string", "description": "Channel name, e.g. #ops-alerts.", "required": True},
        "message": {"type": "string", "description": "Message text.", "required": True},
    },
    constraints={"channel": {"max_length": 80}, "message": {"max_length": 2000}},
)


async def _notify_slack(arguments: dict, context: dict) -> dict:
    return get_slack().post_message(arguments["channel"], arguments["message"])


# ----- registration ----------------------------------------------------------

SUPPORT_TOOLS: list[tuple[ToolSchema, object]] = [
    (get_ticket_schema, _get_ticket),
    (update_ticket_schema, _update_ticket),
    (search_knowledge_schema, _search_knowledge),
    (query_service_health_schema, _query_service_health),
    (get_recent_deployments_schema, _get_recent_deployments),
    (restart_service_schema, _restart_service),
    (scale_service_schema, _scale_service),
    (rollback_deployment_schema, _rollback_deployment),
    (delete_production_data_schema, _delete_production_data),
    (verify_service_health_schema, _verify_service_health),
    (create_github_issue_schema, _create_github_issue),
    (notify_slack_schema, _notify_slack),
]
