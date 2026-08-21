"""Ox-alpha chat client (OpenRouter, OpenAI-compatible protocol).

Pinned to the ox-alpha model behind an OpenRouter-compatible
``/chat/completions`` endpoint. Implements the exact same contract as
``cohere.py`` / ``openai_compat.py`` so the orchestrator can treat it as a
drop-in provider and failover between providers transparently:

    ChatMessage(role, content, tool_call_id=None, tool_calls=None)
    ChatResponse(text, tool_calls, usage, chat_history)

Configuration:
    OPENROUTER_API_KEY   required
    OPENROUTER_BASE_URL  optional (default https://openrouter.ai/api/v1)
    OXALPHA_MODEL        optional (default stealth/ox-alpha)

The message serialization is identical to openai_compat.py; the difference
is the pinned base URL + model and the provider label used in traces.
"""
from __future__ import annotations

from typing import Any

import httpx

from ..config import get_settings
from .cohere import ChatMessage, ChatResponse
from .openai_compat import (
    _apply_tool_results,
    _openai_messages,
    _openai_tools,
    _parse_tool_calls,
)

PROVIDER_NAME = "oxalpha"


def chat(
    messages: list[ChatMessage],
    tools: list[dict] | None = None,
    model: str | None = None,
    *,
    tool_results: list[dict] | None = None,
    chat_history: list[dict] | None = None,
) -> ChatResponse:
    """Call ox-alpha via OpenRouter with the two-phase tool loop.

    Same loop contract as openai_compat.chat: turn 1 sends system + user +
    tools; tool turns append ``tool`` messages keyed by tool_call id.
    """
    s = get_settings()
    if not s.openrouter_api_key:
        raise RuntimeError(
            "ox-alpha provider not configured: set OPENROUTER_API_KEY"
        )

    if chat_history:
        openai_msgs = [dict(m) for m in chat_history]
    else:
        openai_msgs = _openai_messages(messages)

    if tool_results:
        openai_msgs = _apply_tool_results(openai_msgs, tool_results)

    body: dict[str, Any] = {
        "model": model or s.oxalpha_model,
        "messages": openai_msgs,
    }
    oai_tools = _openai_tools(tools)
    if oai_tools:
        body["tools"] = oai_tools
        body["tool_choice"] = "auto"

    base = s.openrouter_base_url.rstrip("/")
    with httpx.Client(timeout=s.oai_timeout_s) as client:
        r = client.post(
            f"{base}/chat/completions",
            headers={
                "Authorization": f"Bearer {s.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json=body,
        )
        r.raise_for_status()
        data = r.json()

    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    text = message.get("content") or ""
    tool_calls = _parse_tool_calls(message)
    usage = data.get("usage") or {}

    next_history = [dict(m) for m in openai_msgs]
    assistant_turn: dict[str, Any] = {"role": "assistant", "content": text}
    if message.get("tool_calls"):
        assistant_turn["tool_calls"] = message["tool_calls"]
    next_history.append(assistant_turn)

    return ChatResponse(
        text=text,
        tool_calls=tool_calls,
        usage=usage,
        chat_history=next_history,
    )
