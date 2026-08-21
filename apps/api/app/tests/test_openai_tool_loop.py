"""Unit tests for the OpenAI-compatible provider (FreeLLMAPI / OpenRouter).

Locks the request/response contract the orchestrator relies on:
  * Cohere-style tool defs are converted to OpenAI function tools.
  * Turn 1 builds system + user messages with a tools array.
  * Tool turns append ``tool`` role messages keyed by the assistant's
    tool_call ids, paired by position with ``tool_results``.
  * Response tool_calls are normalized to {name, arguments, id} and the
    running OpenAI messages array is echoed back as ``chat_history``.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.llm.cohere import ChatMessage
from app.llm.openai_compat import (
    _apply_tool_results,
    _openai_messages,
    _openai_tools,
    _parse_tool_calls,
    chat,
)

SYSTEM = ChatMessage(role="system", content="You are the HR Policy Agent.\n<UNTRUSTED>\nrule")
USER = ChatMessage(role="user", content="I'm sick today, can you request sick leave?")
TOOLS = [
    {"name": "search_documents", "description": "search", "parameter_definitions": {
        "query": {"type": "string", "description": "query text", "required": True},
        "top_k": {"type": "integer", "description": "count", "required": False},
    }},
    {"name": "create_time_off_request", "description": "create", "parameter_definitions": {
        "leave_type": {"type": "string", "description": "type", "required": True},
    }},
]


def test_tool_conversion_builds_openai_function_tools():
    tools = _openai_tools(TOOLS)
    assert len(tools) == 2
    first = tools[0]
    assert first["type"] == "function"
    assert first["function"]["name"] == "search_documents"
    params = first["function"]["parameters"]
    assert params["type"] == "object"
    assert params["required"] == ["query"]
    assert params["properties"]["query"]["type"] == "string"


def test_turn1_messages_are_system_then_user():
    msgs = _openai_messages([SYSTEM, USER])
    assert msgs == [
        {"role": "system", "content": SYSTEM.content},
        {"role": "user", "content": USER.content},
    ]


def test_tool_results_append_tool_messages_paired_by_position():
    history = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "", "tool_calls": [
            {"id": "call_1", "function": {"name": "create_time_off_request", "arguments": "{}"}},
            {"id": "call_2", "function": {"name": "search_documents", "arguments": "{}"}},
        ]},
    ]
    results = [
        {"call": {"name": "create_time_off_request", "parameters": {}}, "outputs": [{"ok": True}]},
        {"call": {"name": "search_documents", "parameters": {}}, "outputs": [{"n": 3}]},
    ]
    msgs = _apply_tool_results(history, results)
    tool_msgs = [m for m in msgs if m["role"] == "tool"]
    assert [m["tool_call_id"] for m in tool_msgs] == ["call_1", "call_2"]
    assert "ok" in tool_msgs[0]["content"]


def test_parse_tool_calls_normalizes_name_arguments_id():
    message = {
        "content": "",
        "tool_calls": [
            {
                "id": "call_abc",
                "function": {"name": "create_time_off_request", "arguments": '{"leave_type": "sick"}'},
            }
        ],
    }
    calls = _parse_tool_calls(message)
    assert calls == [{"name": "create_time_off_request", "arguments": {"leave_type": "sick"}, "id": "call_abc"}]


def _fake_settings(**overrides):
    settings = {
        "llm_base_url": "http://127.0.0.1:3001/v1",
        "llm_api_key": "freellmapi-test",
        "llm_model": "auto",
        "oai_timeout_s": 120,
    }
    settings.update(overrides)
    return MagicMock(**settings)


def test_chat_turn1_posts_openai_body_and_returns_history():
    resp_payload = {
        "choices": [{
            "message": {
                "content": "",
                "tool_calls": [{
                    "id": "call_1",
                    "function": {"name": "create_time_off_request", "arguments": '{"leave_type": "sick"}'},
                }],
            }
        }],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    fake = MagicMock()
    fake.json.return_value = resp_payload
    fake.raise_for_status = lambda: None

    with patch("app.llm.openai_compat.get_settings", return_value=_fake_settings()), \
         patch("httpx.Client") as mock_client:
        client_mock = mock_client.return_value.__enter__.return_value
        client_mock.post.return_value = fake
        resp = chat([SYSTEM, USER], tools=TOOLS)

    posted = client_mock.post.call_args
    assert posted.args[0].endswith("/chat/completions")
    body = posted.kwargs["json"]
    assert body["model"] == "auto"
    assert [m["role"] for m in body["messages"]] == ["system", "user"]
    assert body["tools"][0]["function"]["name"] == "search_documents"
    assert body["tool_choice"] == "auto"

    assert resp.tool_calls[0]["name"] == "create_time_off_request"
    assert resp.tool_calls[0]["arguments"] == {"leave_type": "sick"}
    # chat_history continues the conversation with the assistant tool-call turn.
    assert resp.chat_history[-1]["role"] == "assistant"
    assert resp.chat_history[-1]["tool_calls"][0]["id"] == "call_1"


def test_chat_tool_turn_appends_tool_messages():
    resp_payload = {
        "choices": [{"message": {"content": "Request created.", "tool_calls": []}}],
        "usage": {},
    }
    fake = MagicMock()
    fake.json.return_value = resp_payload
    fake.raise_for_status = lambda: None

    history = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "", "tool_calls": [
            {"id": "call_1", "function": {"name": "create_time_off_request", "arguments": '{"leave_type": "sick"}'}},
        ]},
    ]
    tool_results = [
        {"call": {"name": "create_time_off_request", "parameters": {"leave_type": "sick"}},
         "outputs": [{"request": {"id": "abc", "status": "pending"}}]},
    ]

    with patch("app.llm.openai_compat.get_settings", return_value=_fake_settings()), \
         patch("httpx.Client") as mock_client:
        client_mock = mock_client.return_value.__enter__.return_value
        client_mock.post.return_value = fake
        resp = chat([SYSTEM, USER], tools=TOOLS, tool_results=tool_results, chat_history=history)

    body = client_mock.post.call_args.kwargs["json"]
    roles = [m["role"] for m in body["messages"]]
    assert roles == ["system", "user", "assistant", "tool"]
    tool_msg = body["messages"][-1]
    assert tool_msg["tool_call_id"] == "call_1"
    assert resp.text == "Request created."
    assert resp.tool_calls == []
