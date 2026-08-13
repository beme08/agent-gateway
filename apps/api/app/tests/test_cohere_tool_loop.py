"""Regression tests for the Cohere multi-step tool-loop fix.

The orchestrator previously appended tool results to a `history` list, but the
HTTP client only sent the last user message (`_cohere_format`), so tool output
never reached the model and the agent could not iterate on results.

These tests lock the v1 request-body contract for both turns of the loop:
  * first turn:  preamble (system) + message (user) + tools
  * tool turn:   message="" + tool_results + echoed chat_history + tools
"""
from __future__ import annotations

from app.llm.cohere import ChatMessage, _build_v1_body

SYSTEM = ChatMessage(role="system", content="You are the HR Policy Agent.\n<UNTRUSTED>\nrule")
USER = ChatMessage(role="user", content="I'm sick today, can you request sick leave?")
TOOLS = [
    {"name": "search_documents", "description": "search", "parameter_definitions": {}},
    {"name": "create_time_off_request", "description": "create", "parameter_definitions": {}},
]
RESULT = [
    {
        "call": {"name": "create_time_off_request", "parameters": {"leave_type": "sick"}},
        "outputs": [{"request": {"id": "abc", "status": "pending"}}],
    }
]
HISTORY = [{"role": "SYSTEM", "message": "...prompt..."}, {"role": "USER", "message": "hi"}]


def test_first_turn_uses_preamble_and_message():
    body = _build_v1_body([SYSTEM, USER], TOOLS, tool_results=None, chat_history=None)
    assert body["message"] == USER.content
    assert "HR Policy Agent" in body["preamble"]
    assert "<UNTRUSTED>" in body["preamble"]
    assert body["tools"] == TOOLS
    assert "tool_results" not in body
    assert "chat_history" not in body


def test_tool_turn_echoes_history_and_sends_results():
    body = _build_v1_body([SYSTEM, USER], TOOLS, tool_results=RESULT, chat_history=HISTORY)
    assert body["message"] == ""
    assert body["tool_results"] == RESULT
    assert body["chat_history"] == HISTORY
    assert body["tools"] == TOOLS
    assert "preamble" not in body


def test_no_tool_results_no_system_is_plain_message():
    body = _build_v1_body([USER], [], tool_results=None, chat_history=None)
    assert body["message"] == USER.content
    assert "preamble" not in body


def test_tool_turn_without_explicit_history_still_sends_results():
    body = _build_v1_body([SYSTEM, USER], TOOLS, tool_results=RESULT, chat_history=None)
    assert body["message"] == ""
    assert body["tool_results"] == RESULT
    assert "chat_history" not in body