"""Audit logger for security events."""
from __future__ import annotations

from ...db import service_client


def log_security_event(
    tenant_id: str | None,
    user_id: str | None,
    event_type: str,
    severity: str,
    details: dict,
) -> None:
    try:
        service_client().table("security_events").insert(
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "event_type": event_type,
                "severity": severity,
                "details": details,
            }
        ).execute()
    except Exception:
        pass
