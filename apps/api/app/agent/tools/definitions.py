"""Tool definitions + handlers for the HR Policy Agent.

These wrap the LeaveService and the RAG retrieve layer. They are the only
place the agent touches business logic.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .registry import ToolDef, ToolSchema
from ...rag.retrieve import search as rag_search
from ...services.leave_service import (
    approve as svc_approve,
    cancel as svc_cancel,
    create_request as svc_create,
    list_balances as svc_balances,
    list_requests as svc_list,
    reject as svc_reject,
)


# ----- search_documents ------------------------------------------------------

search_documents_schema = ToolSchema(
    name="search_documents",
    description="Search HR policy documents using semantic search. Returns the most relevant chunks with citations.",
    required_role="viewer",
    parameters={
        "query": {"type": "string", "description": "Natural-language search query.", "required": True},
        "top_k": {"type": "integer", "description": "Number of chunks to return (1-10).", "required": False},
    },
)


async def _search_documents(arguments: dict, context: dict) -> dict:
    q = arguments["query"]
    top_k = min(max(int(arguments.get("top_k", 5)), 1), 10)
    chunks = rag_search(context["tenant_id"], context["role"], q, top_k=top_k)
    return {
        "chunks": [
            {
                "id": c["id"],
                "document_id": c["document_id"],
                "chunk_index": c["chunk_index"],
                "content": c["content"],
                "page": c.get("page"),
                "section": c.get("section"),
                "acl_tags": c.get("acl_tags", []),
                "similarity": c.get("similarity", 0.0),
            }
            for c in chunks
        ]
    }


# ----- get_leave_balance -----------------------------------------------------

get_leave_balance_schema = ToolSchema(
    name="get_leave_balance",
    description="Return the caller's current leave balance by type (vacation, sick, personal, etc).",
    required_role="employee",
    parameters={
        "user_id": {"type": "string", "description": "Optional. Defaults to the caller's user id.", "required": False},
    },
)


async def _get_leave_balance(arguments: dict, context: dict) -> dict:
    target = arguments.get("user_id") or context["user_id"]
    if target != context["user_id"] and context["role"] not in ("manager", "admin"):
        return {"error": "cannot view another user's balance"}
    balances = svc_balances(context["tenant_id"], target)
    return {"user_id": target, "balances": balances}


# ----- create_time_off_request ----------------------------------------------

create_time_off_request_schema = ToolSchema(
    name="create_time_off_request",
    description="Create a pending time-off request (vacation, sick, personal, etc). The request is created in 'pending' status and a manager will approve or reject it.",
    required_role="employee",
    parameters={
        "leave_type": {"type": "string", "description": "One of: vacation, sick, personal, unpaid, parental, bereavement.", "required": True},
        "start_date": {"type": "string", "description": "Start date in ISO format YYYY-MM-DD.", "required": True},
        "end_date":   {"type": "string", "description": "End date in ISO format YYYY-MM-DD.", "required": True},
        "reason":     {"type": "string", "description": "Optional reason / note.", "required": False},
    },
)


async def _create_time_off_request(arguments: dict, context: dict) -> dict:
    try:
        sd = date.fromisoformat(arguments["start_date"])
        ed = date.fromisoformat(arguments["end_date"])
    except ValueError as e:
        return {"error": f"invalid date: {e}"}
    if ed < sd:
        return {"error": "end_date must be on or after start_date"}

    req = svc_create(
        tenant_id=context["tenant_id"],
        user_id=context["user_id"],
        leave_type=arguments["leave_type"],
        start_date=sd,
        end_date=ed,
        reason=arguments.get("reason"),
    )
    return {"request": req}


# ----- get_time_off_requests ------------------------------------------------

get_time_off_requests_schema = ToolSchema(
    name="get_time_off_requests",
    description="List time-off requests. Use scope='self' for the caller's requests, or scope='team' (manager+) to see requests awaiting the caller's approval.",
    required_role="employee",
    parameters={
        "scope": {"type": "string", "description": "Either 'self' or 'team'. 'team' requires manager role.", "required": False},
    },
)


async def _get_time_off_requests(arguments: dict, context: dict) -> dict:
    scope = arguments.get("scope", "self")
    if scope == "team":
        if context["role"] not in ("manager", "admin"):
            return {"error": "scope='team' requires manager or admin role"}
        rows = svc_list(context["tenant_id"], manager_user_id=context["user_id"])
    else:
        rows = svc_list(context["tenant_id"], user_id=context["user_id"])
    return {"requests": rows, "scope": scope}


# ----- cancel_time_off_request ---------------------------------------------

cancel_time_off_request_schema = ToolSchema(
    name="cancel_time_off_request",
    description="Cancel one of the caller's own pending time-off requests.",
    required_role="employee",
    parameters={
        "request_id": {"type": "string", "description": "UUID of the pending request to cancel.", "required": True},
    },
)


async def _cancel_time_off_request(arguments: dict, context: dict) -> dict:
    svc_cancel(arguments["request_id"], context["user_id"])
    return {"cancelled": True, "request_id": arguments["request_id"]}


# ----- approve_time_off_request ---------------------------------------------

approve_time_off_request_schema = ToolSchema(
    name="approve_time_off_request",
    description="Approve a pending time-off request. Caller must be the request's manager or an admin.",
    required_role="manager",
    needs_manager_scope=True,
    parameters={
        "request_id": {"type": "string", "description": "UUID of the pending request to approve.", "required": True},
        "note":       {"type": "string", "description": "Optional manager note.", "required": False},
    },
)


async def _approve_time_off_request(arguments: dict, context: dict) -> dict:
    svc_approve(arguments["request_id"], context["user_id"], arguments.get("note"))
    return {"approved": True, "request_id": arguments["request_id"]}


# ----- reject_time_off_request ----------------------------------------------

reject_time_off_request_schema = ToolSchema(
    name="reject_time_off_request",
    description="Reject a pending time-off request. Caller must be the request's manager or an admin. A reason is required.",
    required_role="manager",
    needs_manager_scope=True,
    parameters={
        "request_id": {"type": "string", "description": "UUID of the pending request to reject.", "required": True},
        "reason":     {"type": "string", "description": "Rejection reason (required).", "required": True},
    },
)


async def _reject_time_off_request(arguments: dict, context: dict) -> dict:
    reason = (arguments.get("reason") or "").strip()
    if not reason:
        return {"error": "rejection reason is required"}
    svc_reject(arguments["request_id"], context["user_id"], reason)
    return {"rejected": True, "request_id": arguments["request_id"], "reason": reason}


# ----- Registry factory -----------------------------------------------------

def build_registry() -> "ToolRegistry":
    from .registry import ToolRegistry
    reg = ToolRegistry()
    for schema, handler in [
        (search_documents_schema, _search_documents),
        (get_leave_balance_schema, _get_leave_balance),
        (create_time_off_request_schema, _create_time_off_request),
        (get_time_off_requests_schema, _get_time_off_requests),
        (cancel_time_off_request_schema, _cancel_time_off_request),
        (approve_time_off_request_schema, _approve_time_off_request),
        (reject_time_off_request_schema, _reject_time_off_request),
    ]:
        reg.register(ToolDef(schema=schema, handler=handler))
    return reg
