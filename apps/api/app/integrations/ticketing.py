"""Ticketing adapter: the support ticket system of record (DB-backed mock).

Stands in for Zendesk/Jira-style systems. The mock implementation persists
to the platform's own Postgres (support_tickets / ticket_events) — a clean
boundary now, swappable for a real HTTP client later.
"""
from __future__ import annotations

from typing import Protocol

from ..db import service_client


class TicketingAdapter(Protocol):
    def get_ticket(self, tenant_id: str, ticket_id: str) -> dict: ...
    def list_tickets(self, tenant_id: str) -> list[dict]: ...
    def update_ticket(self, tenant_id: str, ticket_id: str, **fields) -> dict: ...
    def append_event(self, tenant_id: str, ticket_id: str, event_type: str,
                     actor: str, detail: dict, trace_id: str | None = None) -> dict: ...


class DbTicketing:
    def get_ticket(self, tenant_id: str, ticket_id: str) -> dict:
        res = (
            service_client()
            .table("support_tickets")
            .select("*")
            .eq("tenant_id", tenant_id)
            .eq("id", ticket_id)
            .single()
            .execute()
        )
        if not res.data:
            raise ValueError(f"ticket {ticket_id} not found")
        return res.data

    def list_tickets(self, tenant_id: str) -> list[dict]:
        res = (
            service_client()
            .table("support_tickets")
            .select("*")
            .eq("tenant_id", tenant_id)
            .order("created_at", desc=True)
            .limit(100)
            .execute()
        )
        return res.data or []

    def update_ticket(self, tenant_id: str, ticket_id: str, **fields) -> dict:
        fields["updated_at"] = "now()"
        clean = {k: v for k, v in fields.items() if v != "now()"}
        res = (
            service_client()
            .table("support_tickets")
            .update(clean)
            .eq("tenant_id", tenant_id)
            .eq("id", ticket_id)
            .execute()
        )
        return (res.data or [{}])[0]

    def append_event(self, tenant_id: str, ticket_id: str, event_type: str,
                     actor: str, detail: dict, trace_id: str | None = None) -> dict:
        row = {
            "tenant_id": tenant_id,
            "ticket_id": ticket_id,
            "event_type": event_type,
            "actor": actor,
            "detail": detail,
        }
        if trace_id:
            row["trace_id"] = trace_id
        res = service_client().table("ticket_events").insert(row).execute()
        return (res.data or [{}])[0]


_singleton: DbTicketing | None = None


def get_ticketing() -> DbTicketing:
    global _singleton
    if _singleton is None:
        _singleton = DbTicketing()
    return _singleton
