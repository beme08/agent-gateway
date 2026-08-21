"""Unit tests for the ox-alpha provider (OpenRouter) and the provider
failover chain.

Locks:
  * ox-alpha posts to the pinned OpenRouter endpoint with the pinned model.
  * The provider chain honors explicit selection (LLM_PROVIDER / per-agent
    provider) and degrades gracefully: an expired trial (HTTP error) fails
    over to the next configured provider.
  * The chain is empty when nothing is configured (offline mock path).
"""
from __future__ import annotations

import httpx
from unittest.mock import MagicMock, patch

import pytest

from app.agent.orchestrator import _chat_with_failover, _provider_chain
from app.llm.cohere import ChatMessage


SYSTEM = ChatMessage(role="system", content="You are the Support Ops Agent.")
USER = ChatMessage(role="user", content="checkout-api is throwing 503s.")
TOOLS = [
    {"name": "query_service_health", "description": "health",
     "parameter_definitions": {"service": {"type": "string", "description": "s", "required": True}}},
]


def _settings(**overrides):
    base = {
        "openrouter_api_key": "",
        "openrouter_base_url": "https://openrouter.ai/api/v1",
        "oxalpha_model": "stealth/ox-alpha",
        "llm_base_url": "",
        "llm_api_key": "",
        "llm_model": "auto",
        "llm_provider": "",
        "cohere_api_key": "",
        "cohere_model": "command-r-plus",
        "oai_timeout_s": 120,
    }
    base.update(overrides)
    return MagicMock(**base)


def test_chain_empty_when_nothing_configured():
    with patch("app.agent.orchestrator.get_settings", return_value=_settings()):
        assert _provider_chain() == []


def test_chain_prefers_explicit_provider_and_keeps_failovers():
    s = _settings(llm_provider="oxalpha", openrouter_api_key="k",
                  llm_base_url="http://x/v1", llm_api_key="k2", cohere_api_key="k3")
    with patch("app.agent.orchestrator.get_settings", return_value=s):
        chain = _provider_chain()
    assert [c["name"] for c in chain] == ["oxalpha", "openai_compat", "cohere"]
    assert chain[0]["model"] == "stealth/ox-alpha"


def test_chain_legacy_default_order_preserved():
    s = _settings(openrouter_api_key="k", llm_base_url="http://x/v1",
                  llm_api_key="k2", cohere_api_key="k3")
    with patch("app.agent.orchestrator.get_settings", return_value=s):
        chain = _provider_chain()
    # No explicit hint: existing behavior first (openai_compat), then cohere,
    # ox-alpha as last-resort failover.
    assert [c["name"] for c in chain] == ["openai_compat", "cohere", "oxalpha"]


def test_chain_honors_per_agent_provider():
    s = _settings(openrouter_api_key="k", llm_base_url="http://x/v1", llm_api_key="k2")
    with patch("app.agent.orchestrator.get_settings", return_value=s):
        chain = _provider_chain({"provider": "oxalpha", "model": "stealth/ox-alpha"})
    assert chain[0]["name"] == "oxalpha"


def test_failover_skips_broken_provider():
    ok_resp = MagicMock(text="done", tool_calls=[], chat_history=[], usage={})

    def broken(*a, **k):
        raise RuntimeError("402: trial expired")

    chain = [{"name": "oxalpha", "chat": broken, "model": "ox"},
             {"name": "openai_compat", "chat": MagicMock(return_value=ok_resp), "model": "auto"}]

    resp, used, failovers = _chat_with_failover(chain, [SYSTEM, USER], TOOLS, None, None)
    assert resp.text == "done"
    assert used["name"] == "openai_compat"
    assert failovers == [{"provider": "oxalpha", "error": "402: trial expired"}]


def test_failover_raises_when_all_providers_fail():
    def broken(*a, **k):
        raise RuntimeError("down")

    chain = [{"name": "a", "chat": broken, "model": "m"},
             {"name": "b", "chat": broken, "model": "m"}]
    with pytest.raises(RuntimeError):
        _chat_with_failover(chain, [SYSTEM, USER], None, None, None)


def _fake_response(payload):
    fake = MagicMock()
    fake.json.return_value = payload
    fake.raise_for_status = lambda: None
    return fake


def test_oxalpha_chat_posts_pinned_model_and_parses_tool_calls():
    payload = {
        "choices": [{
            "message": {
                "content": "",
                "tool_calls": [{
                    "id": "call_1",
                    "function": {"name": "query_service_health",
                                 "arguments": '{"service": "checkout-api"}'},
                }],
            }
        }],
        "usage": {"prompt_tokens": 9, "completion_tokens": 4},
    }
    fake_settings = _settings(openrouter_api_key="sk-or-test")
    fake = _fake_response(payload)

    with patch("app.llm.oxalpha.get_settings", return_value=fake_settings), \
         patch("httpx.Client") as mock_client:
        client_mock = mock_client.return_value.__enter__.return_value
        client_mock.post.return_value = fake
        from app.llm.oxalpha import chat as oxalpha_chat
        resp = oxalpha_chat([SYSTEM, USER], tools=TOOLS)

    posted = client_mock.post.call_args
    assert posted.args[0] == "https://openrouter.ai/api/v1/chat/completions"
    body = posted.kwargs["json"]
    assert body["model"] == "stealth/ox-alpha"
    assert body["messages"][0]["role"] == "system"
    assert body["tools"][0]["function"]["name"] == "query_service_health"

    assert resp.tool_calls[0] == {
        "name": "query_service_health",
        "arguments": {"service": "checkout-api"},
        "id": "call_1",
    }
    # Running conversation echoed back for the next turn.
    assert resp.chat_history[-1]["role"] == "assistant"
    assert resp.chat_history[-1]["tool_calls"][0]["id"] == "call_1"


def test_oxalpha_chat_requires_api_key():
    with patch("app.llm.oxalpha.get_settings", return_value=_settings()):
        from app.llm.oxalpha import chat as oxalpha_chat
        with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
            oxalpha_chat([SYSTEM, USER])


def test_oxalpha_http_error_propagates_for_failover():
    fake_settings = _settings(openrouter_api_key="sk-or-test")
    with patch("app.llm.oxalpha.get_settings", return_value=fake_settings), \
         patch("httpx.Client") as mock_client:
        client_mock = mock_client.return_value.__enter__.return_value
        client_mock.post.side_effect = httpx.HTTPStatusError(
            "402 Payment Required", request=MagicMock(), response=MagicMock()
        )
        from app.llm.oxalpha import chat as oxalpha_chat
        with pytest.raises(httpx.HTTPStatusError):
            oxalpha_chat([SYSTEM, USER])
