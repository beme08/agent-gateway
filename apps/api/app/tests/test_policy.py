import pytest
from app.agent.tools.definitions import build_registry
from app.agent.tools.policy import check


def caller(role: str) -> dict:
    return {"user_id": "u1", "tenant_id": "t1", "role": role}


def test_viewer_can_search_documents():
    reg = build_registry()
    d = check(reg, caller("viewer"), "search_documents", {"query": "vacation"})
    assert d.allow
    assert d.reason == "allowed"


def test_viewer_cannot_get_leave_balance():
    reg = build_registry()
    d = check(reg, caller("viewer"), "get_leave_balance", {})
    assert not d.allow
    assert "requires 'employee'" in d.reason


def test_employee_can_create_request():
    reg = build_registry()
    d = check(reg, caller("employee"), "create_time_off_request", {
        "leave_type": "sick",
        "start_date": "2026-06-13",
        "end_date": "2026-06-13",
    })
    assert d.allow


def test_employee_cannot_approve():
    reg = build_registry()
    d = check(reg, caller("employee"), "approve_time_off_request", {"request_id": "x"})
    assert not d.allow


def test_manager_can_approve():
    reg = build_registry()
    d = check(reg, caller("manager"), "approve_time_off_request", {"request_id": "x"})
    assert d.allow


def test_admin_can_approve():
    reg = build_registry()
    d = check(reg, caller("admin"), "approve_time_off_request", {"request_id": "x"})
    assert d.allow


def test_unknown_tool_is_denied():
    reg = build_registry()
    d = check(reg, caller("admin"), "drop_database", {})
    assert not d.allow
    assert "unknown tool" in d.reason


def test_missing_required_arg_is_denied():
    reg = build_registry()
    d = check(reg, caller("employee"), "search_documents", {})
    assert not d.allow
    assert "argument schema" in d.reason


def test_reject_requires_reason_at_schema_level():
    reg = build_registry()
    d = check(reg, caller("manager"), "reject_time_off_request", {"request_id": "x"})
    assert not d.allow
