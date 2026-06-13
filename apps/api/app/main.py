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
  GET  /v1/audit/traces         (admin)
  GET  /v1/audit/traces/{id}    (admin)
  POST /v1/admin/reset-demo     (admin)
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .agent.orchestrator import run as run_agent
from .auth import CallerContext, get_caller
from .db import service_client
from .services.leave_service import (
    approve as svc_approve,
    cancel as svc_cancel,
    create_request as svc_create,
    list_balances as svc_balances,
    list_requests as svc_list,
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
    session_id: Optional[str] = None
    agent_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    trace_id: str | None
    tool_calls: list[dict]
    blocked: bool = False
    block_reason: str | None = None


@app.post("/v1/agent/chat", response_model=ChatResponse)
async def agent_chat(req: ChatRequest, caller: CallerContext = Depends(get_caller)):
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
async def get_balances(caller: CallerContext = Depends(get_caller)):
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
    reason: Optional[str] = None


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
    note: Optional[str] = None


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
