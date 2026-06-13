"""Sanity tests that verify the role gate on each tool matches the spec."""
import pytest
from app.agent.tools.definitions import build_registry
from app.agent.tools.policy import check, ROLE_RANK


def _caller(role: str) -> dict:
    return {"user_id": "u1", "tenant_id": "t1", "role": role}


@pytest.mark.parametrize("tool,args,allowed_roles", [
    ("search_documents",         {"query": "x"},                   ["viewer", "employee", "manager", "admin"]),
    ("get_leave_balance",        {},                                ["employee", "manager", "admin"]),
    ("create_time_off_request",  {"leave_type": "vacation", "start_date": "2026-06-13", "end_date": "2026-06-13"},
                                                                    ["employee", "manager", "admin"]),
    ("get_time_off_requests",    {"scope": "self"},                 ["employee", "manager", "admin"]),
    ("get_time_off_requests",    {"scope": "team"},                 ["manager", "admin"]),
    ("cancel_time_off_request",  {"request_id": "x"},               ["employee", "manager", "admin"]),
    ("approve_time_off_request", {"request_id": "x"},               ["manager", "admin"]),
    ("reject_time_off_request",  {"request_id": "x", "reason": "r"},["manager", "admin"]),
])
def test_role_authorization(tool, args, allowed_roles):
    reg = build_registry()
    for role in ["viewer", "employee", "manager", "admin"]:
        d = check(reg, _caller(role), tool, args)
        if role in allowed_roles:
            assert d.allow, f"{role} should be allowed to call {tool} with {args}"
        else:
            assert not d.allow, f"{role} should NOT be allowed to call {tool} with {args}"
