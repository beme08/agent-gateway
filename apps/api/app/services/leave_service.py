"""Shared leave service. The only path that mutates leave_requests /
leave_balances. Used by both Next.js server actions (via REST) and the
FastAPI tool executor so the UI and the agent cannot diverge."""
from __future__ import annotations

from datetime import date
from typing import Any

from ..db import service_client


def list_balances(tenant_id: str, user_id: str) -> list[dict]:
    res = (
        service_client()
        .table("leave_balances")
        .select("leave_type, year, allocated_days, used_days, pending_days, remaining_days")
        .eq("tenant_id", tenant_id)
        .eq("user_id", user_id)
        .order("leave_type")
        .execute()
    )
    return res.data or []


def create_request(
    tenant_id: str,
    user_id: str,
    leave_type: str,
    start_date: date,
    end_date: date,
    reason: str | None,
) -> dict:
    res = (
        service_client()
        .rpc(
            "create_leave_request",
            {
                "p_tenant_id": tenant_id,
                "p_user_id": user_id,
                "p_leave_type": leave_type,
                "p_start_date": start_date.isoformat(),
                "p_end_date": end_date.isoformat(),
                "p_reason": reason,
            },
        )
        .execute()
    )
    request_id = res.data
    detail = (
        service_client()
        .table("leave_requests")
        .select("*")
        .eq("id", request_id)
        .single()
        .execute()
    )
    return detail.data or {"id": request_id}


def list_requests(tenant_id: str, user_id: str | None = None, manager_user_id: str | None = None) -> list[dict]:
    q = service_client().table("leave_requests").select("*").eq("tenant_id", tenant_id).order("created_at", desc=True)
    if user_id:
        q = q.eq("user_id", user_id)
    if manager_user_id:
        q = q.eq("manager_user_id", manager_user_id)
    res = q.execute()
    return res.data or []


def cancel(request_id: str, user_id: str) -> None:
    service_client().rpc("cancel_leave_request", {"p_request_id": request_id, "p_user_id": user_id}).execute()


def approve(request_id: str, manager_user_id: str, note: str | None) -> None:
    service_client().rpc(
        "approve_leave_request",
        {"p_request_id": request_id, "p_manager_user_id": manager_user_id, "p_note": note},
    ).execute()


def reject(request_id: str, manager_user_id: str, reason: str) -> None:
    service_client().rpc(
        "reject_leave_request",
        {"p_request_id": request_id, "p_manager_user_id": manager_user_id, "p_reason": reason},
    ).execute()
