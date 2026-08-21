"""FastAPI entry point. Exposes:
  GET  /healthz
  POST /v1/agent/chat           (JWT-auth)
  GET  /v1/agents               (JWT-auth)
  GET  /v1/balances             (JWT-auth)
  GET  /v1/leave/requests       (JWT-auth)
  POST /v1/leave/requests       (JWT-auth)
  POST /v1/leave/requests/{id}/approve
  POST /v1/leave/requests/{id}/reject
  POST /v1/leave/requests/{id}/cancel
  GET  /v1/support/tickets      (JWT-auth)
  POST /v1/support/tickets      (JWT-auth)
  GET  /v1/support/tickets/{id} (JWT-auth)
  POST /v1/support/tickets/{id}/run   (JWT-auth; agent pipeline)
  GET  /v1/approvals            (manager/admin)
  POST /v1/approvals/{id}/approve     (manager/admin; re-checks policy)
  POST /v1/approvals/{id}/reject      (manager/admin)
  GET  /v1/audit/traces         (admin)
  GET  /v1/audit/traces/{id}    (admin)
  POST /v1/admin/reset-demo     (admin)
"""
from __future__ import annotations

from datetime import date

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .agent.approvals import decide as approval_decide
from .agent.approvals import list_approvals as svc_list_approvals
from .agent.orchestrator import run as run_agent
from .agent.tools.definitions import build_registry
from .auth import CallerContext, get_caller
from .db import service_client
from .integrations.ticketing import get_ticketing
from .ratelimit import enforce_chat_limit, enforce_general_limit
from .services.leave_service import (
    approve as svc_approve,
)
from .services.leave_service import (
    cancel as svc_cancel,
)
from .services.leave_service import (
    create_request as svc_create,
)
from .services.leave_service import (
    list_balances as svc_balances,
)
from .services.leave_service import (
    list_requests as svc_list,
)
from .services.leave_service import (
    reject as svc_reject,
)
from .workers.seed_ingest import run_seed_ingest

app = FastAPI(title="Secure Enterprise Agent Gateway API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup():
    try:
        await run_seed_ingest()
    except Exception as e:
        print(f"[startup] seed_ingest failed (non-fatal): {e}")


@app.get("/healthz")
async def healthz():
    return {"ok": True}


# ---- Agent chat -----------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None
    agent_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    trace_id: str | None
    tool_calls: list[dict]
    blocked: bool = False
    block_reason: str | None = None


@app.post("/v1/agent/chat", response_model=ChatResponse)
async def agent_chat(
    req: ChatRequest,
    caller: CallerContext = Depends(get_caller),
    _: None = Depends(enforce_chat_limit),
):
    result = await run_agent(
        caller={
            "user_id": caller.user_id,
            "tenant_id": caller.tenant_id,
            "role": caller.role,
            "email": caller.email,
            "manager_user_id": caller.manager_user_id,
        },
        user_message=req.message,
        session_id=req.session_id,
        agent_id=req.agent_id,
    )
    return ChatResponse(
        answer=result.answer,
        trace_id=result.trace_id,
        tool_calls=result.tool_calls,
        blocked=result.blocked,
        block_reason=result.block_reason,
    )


# ---- Balances / leave -----------------------------------------------------

@app.get("/v1/balances")
async def get_balances(
    caller: CallerContext = Depends(get_caller),
    _: None = Depends(enforce_general_limit),
):
    return {"balances": svc_balances(caller.tenant_id, caller.user_id)}


@app.get("/v1/leave/requests")
async def get_leave_requests(
    scope: str = "self",
    caller: CallerContext = Depends(get_caller),
):
    if scope == "team":
        if caller.role not in ("manager", "admin"):
            raise HTTPException(403, "scope=team requires manager or admin")
        rows = svc_list(caller.tenant_id, manager_user_id=caller.user_id)
    else:
        rows = svc_list(caller.tenant_id, user_id=caller.user_id)
    return {"requests": rows, "scope": scope}


class CreateLeaveReq(BaseModel):
    leave_type: str
    start_date: date
    end_date: date
    reason: str | None = None


@app.post("/v1/leave/requests")
async def create_leave_request(req: CreateLeaveReq, caller: CallerContext = Depends(get_caller)):
    if req.end_date < req.start_date:
        raise HTTPException(400, "end_date must be on or after start_date")
    try:
        result = svc_create(
            tenant_id=caller.tenant_id,
            user_id=caller.user_id,
            leave_type=req.leave_type,
            start_date=req.start_date,
            end_date=req.end_date,
            reason=req.reason,
        )
    except Exception as e:
        raise HTTPException(400, str(e))
    return {"request": result}


class ApproveReq(BaseModel):
    note: str | None = None


@app.post("/v1/leave/requests/{request_id}/approve")
async def approve_request(request_id: str, req: ApproveReq, caller: CallerContext = Depends(get_caller)):
    if caller.role not in ("manager", "admin"):
        raise HTTPException(403, "manager or admin required")
    try:
        svc_approve(request_id, caller.user_id, req.note)
    except Exception as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


class RejectReq(BaseModel):
    reason: str


@app.post("/v1/leave/requests/{request_id}/reject")
async def reject_request(request_id: str, req: RejectReq, caller: CallerContext = Depends(get_caller)):
    if caller.role not in ("manager", "admin"):
        raise HTTPException(403, "manager or admin required")
    try:
        svc_reject(request_id, caller.user_id, req.reason)
    except Exception as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@app.post("/v1/leave/requests/{request_id}/cancel")
async def cancel_request(request_id: str, caller: CallerContext = Depends(get_caller)):
    try:
        svc_cancel(request_id, caller.user_id)
    except Exception as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


# ---- Support Operations -----------------------------------------------------

SUPPORT_AGENT_NAME = "Support Ops Agent"


def _load_support_agent_id(tenant_id: str) -> str:
    res = (
        service_client()
        .table("agents")
        .select("id")
        .eq("tenant_id", tenant_id)
        .eq("name", SUPPORT_AGENT_NAME)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise HTTPException(404, "Support Ops agent not configured for this tenant")
    return res.data[0]["id"]


@app.get("/v1/support/tickets")
async def list_tickets(caller: CallerContext = Depends(get_caller)):
    return {"tickets": get_ticketing().list_tickets(caller.tenant_id)}


class CreateTicketReq(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    body: str = Field("", max_length=8000)
    severity: str = Field("medium")
    category: str = Field("other")
    reporter_email: str | None = None
    affected_service: str | None = None


@app.post("/v1/support/tickets")
async def create_ticket(req: CreateTicketReq, caller: CallerContext = Depends(get_caller)):
    if req.severity not in ("low", "medium", "high", "critical"):
        raise HTTPException(400, "invalid severity")
    if req.category not in ("incident", "bug", "access", "billing", "question", "other"):
        raise HTTPException(400, "invalid category")
    count = len(get_ticketing().list_tickets(caller.tenant_id))
    row = {
        "tenant_id": caller.tenant_id,
        "ticket_ref": f"TKT-{1001 + count}",
        "title": req.title,
        "body": req.body,
        "severity": req.severity,
        "category": req.category,
        "status": "open",
        "reporter_email": req.reporter_email or caller.email,
        "affected_service": req.affected_service,
        "created_by": caller.user_id,
    }
    created = service_client().table("support_tickets").insert(row).execute().data[0]
    return {"ticket": created}


@app.get("/v1/support/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, caller: CallerContext = Depends(get_caller)):
    try:
        ticket = get_ticketing().get_ticket(caller.tenant_id, ticket_id)
    except Exception:
        raise HTTPException(404, "ticket not found")
    events = (
        service_client()
        .table("ticket_events")
        .select("*")
        .eq("ticket_id", ticket_id)
        .order("created_at")
        .execute()
        .data
        or []
    )
    return {"ticket": ticket, "events": events}


class RunTicketReq(BaseModel):
    instruction: str | None = Field(None, max_length=2000)


@app.post("/v1/support/tickets/{ticket_id}/run", response_model=ChatResponse)
async def run_ticket_pipeline(
    ticket_id: str,
    req: RunTicketReq,
    caller: CallerContext = Depends(get_caller),
    _: None = Depends(enforce_chat_limit),
):
    """Run the Support Ops agent pipeline on a ticket:
    triage -> retrieval -> diagnosis -> policy/risk branch ->
    remediation or approval -> verification -> audit."""
    try:
        ticket = get_ticketing().get_ticket(caller.tenant_id, ticket_id)
    except Exception:
        raise HTTPException(404, "ticket not found")

    agent_id = _load_support_agent_id(caller.tenant_id)

    message = req.instruction or (
        f"Handle support ticket {ticket['ticket_ref']}.\n"
        f"Ticket UUID (use this for get_ticket/update_ticket): {ticket_id}\n"
        f"Title: {ticket['title']}\nSeverity as reported: {ticket['severity']}\n"
        f"Affected service: {ticket.get('affected_service') or 'unspecified'}\n"
        f"Body:\n{ticket['body']}"
    )

    # The ticket id rides along so approvals and remediation records can
    # link back to the ticket timeline.
    result = await run_agent(
        caller={
            "user_id": caller.user_id,
            "tenant_id": caller.tenant_id,
            "role": caller.role,
            "email": caller.email,
            "manager_user_id": caller.manager_user_id,
        },
        user_message=message,
        agent_id=agent_id,
        context={"ticket_id": ticket_id, "ticket_ref": ticket["ticket_ref"]},
    )

    # Timeline: the run itself is an event, linked to the trace for audit.
    try:
        get_ticketing().append_event(
            caller.tenant_id, ticket_id,
            "agent_run", "agent",
            {
                "status": "blocked" if result.blocked else "completed",
                "block_reason": result.block_reason,
                "tools": [
                    {"tool": t.get("tool"), "status": t.get("status")}
                    for t in result.tool_calls
                ],
                "answer_excerpt": result.answer[:500],
            },
            trace_id=result.trace_id,
        )
    except Exception:
        pass

    return ChatResponse(
        answer=result.answer,
        trace_id=result.trace_id,
        tool_calls=result.tool_calls,
        blocked=result.blocked,
        block_reason=result.block_reason,
    )


# ---- Human approvals (risk-tiered actions) ----------------------------------

@app.get("/v1/approvals")
async def get_approvals(
    status: str = "pending",
    caller: CallerContext = Depends(get_caller),
):
    if caller.role not in ("manager", "admin"):
        raise HTTPException(403, "manager or admin required")
    return {"approvals": svc_list_approvals(caller.tenant_id, status if status != "all" else None)}


class ApprovalDecisionReq(BaseModel):
    note: str | None = Field(None, max_length=1000)


@app.post("/v1/approvals/{approval_id}/approve")
async def approve_action(
    approval_id: str,
    req: ApprovalDecisionReq,
    caller: CallerContext = Depends(get_caller),
):
    if caller.role not in ("manager", "admin"):
        raise HTTPException(403, "manager or admin required")
    try:
        # decide() re-runs the full policy check with the ORIGINAL requester's
        # context before executing — approval never bypasses policy.
        result = await approval_decide(
            registry=build_registry(),
            tenant_id=caller.tenant_id,
            approver_user_id=caller.user_id,
            approver_role=caller.role,
            approval_id=approval_id,
            decision="approve",
            note=req.note,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return result


@app.post("/v1/approvals/{approval_id}/reject")
async def reject_action(
    approval_id: str,
    req: ApprovalDecisionReq,
    caller: CallerContext = Depends(get_caller),
):
    if caller.role not in ("manager", "admin"):
        raise HTTPException(403, "manager or admin required")
    try:
        result = await approval_decide(
            registry=build_registry(),
            tenant_id=caller.tenant_id,
            approver_user_id=caller.user_id,
            approver_role=caller.role,
            approval_id=approval_id,
            decision="reject",
            note=req.note,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return result


# ---- Audit / admin --------------------------------------------------------

def _require_admin(caller: CallerContext):
    if caller.role != "admin":
        raise HTTPException(403, "admin required")


@app.get("/v1/audit/traces")
async def list_traces(limit: int = 50, caller: CallerContext = Depends(get_caller)):
    _require_admin(caller)
    res = (
        service_client()
        .table("agent_traces")
        .select("id, user_id, agent_id, user_message, final_status, latency_ms, retrieval_safety_status, input_safety_status, created_at, tool_loop_count")
        .eq("tenant_id", caller.tenant_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return {"traces": res.data or []}


@app.get("/v1/audit/traces/{trace_id}")
async def get_trace(trace_id: str, caller: CallerContext = Depends(get_caller)):
    _require_admin(caller)
    t = service_client().table("agent_traces").select("*").eq("id", trace_id).eq("tenant_id", caller.tenant_id).single().execute()
    if not t.data:
        raise HTTPException(404, "trace not found")
    calls = service_client().table("tool_calls").select("*").eq("trace_id", trace_id).order("created_at").execute()
    return {"trace": t.data, "tool_calls": calls.data or []}


@app.get("/v1/audit/security-events")
async def list_security_events(limit: int = 50, caller: CallerContext = Depends(get_caller)):
    _require_admin(caller)
    res = (
        service_client()
        .table("security_events")
        .select("*")
        .eq("tenant_id", caller.tenant_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return {"events": res.data or []}


@app.post("/v1/admin/reset-demo")
async def reset_demo(caller: CallerContext = Depends(get_caller)):
    _require_admin(caller)
    service_client().rpc("reset_demo_tenant", {"p_tenant_id": caller.tenant_id}).execute()
    return {"ok": True}
