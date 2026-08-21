"""OpenAI-compatible chat client for the agent tool loop.

Mirrors the interface of cohere.py so the orchestrator can call either
provider without knowing which backend is active:

    ChatMessage(role, content, tool_call_id=None, tool_calls=None)
    ChatResponse(text, tool_calls, usage, chat_history)

The backend is any OpenAI-compatible ``/v1/chat/completions`` endpoint
(FreeLLMAPI, OpenRouter, Groq, ...). It implements the same two-phase tool
loop that the orchestrator already drives:

  * Turn 1: system + user message, ``tools`` list.
  * Turn N: previous OpenAI messages (assistant ``tool_calls`` echoed) plus
    ``tool`` role messages produced from ``tool_results``.

``chat_history`` returned by this client is a list of OpenAI message dicts
that the orchestrator echoes back on the next turn — the same contract as the
Cohere v1 client, just serialized differently.
"""
from __future__ import annotations

import json
from typing import Any

import httpx

from ..config import get_settings
from .cohere import ChatMessage, ChatResponse

OPENAI_TOOL_SCHEMA = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}


def _openai_tools(cohere_tools: list[dict]) -> list[dict]:
    """Convert registry's Cohere-style tool defs to OpenAI function tools.

    Cohere tool shape (from ``ToolRegistry.as_cohere_tools()``):
        {"name", "description", "parameter_definitions": {name: {type, description, required}}}
    OpenAI tool shape:
        {"type": "function", "function": {"name", "description", "parameters": {...}}}
    """
    out: list[dict] = []
    for t in cohere_tools or []:
        params = t.get("parameter_definitions") or {}
        properties = {
            name: {
                "type": spec.get("type", "string"),
                "description": spec.get("description", ""),
            }
            for name, spec in params.items()
        }
        required = [name for name, spec in params.items() if spec.get("required")]
        schema: dict[str, Any] = {
            "type": "object",
            "properties": properties,
            "additionalProperties": False,
        }
        if required:
            schema["required"] = required
        out.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": schema,
            },
        })
    return out


def _openai_messages(history: list[ChatMessage]) -> list[dict]:
    """Turn-1 conversion: system + user messages to OpenAI format."""
    msgs: list[dict] = []
    for m in history:
        if m.role == "system":
            msgs.append({"role": "system", "content": m.content})
        elif m.role == "user":
            msgs.append({"role": "user", "content": m.content})
    return msgs


def _apply_tool_results(messages: list[dict], tool_results: list[dict]) -> list[dict]:
    """Append ``tool`` role messages from Cohere-style tool_results.

    The orchestrator produces tool_results as
        {"call": {"name", "parameters"}, "outputs": [...]}
    OpenAI needs, after the assistant's tool_calls, one ``tool`` message per
    call with the matching tool_call_id. We pair by position with the last
    assistant message's tool_calls (the orchestrator always emits results in
    the same order it received the calls).
    """
    msgs = list(messages)
    last_asst = None
    for m in reversed(msgs):
        if m.get("role") == "assistant" and m.get("tool_calls"):
            last_asst = m
            break
    if last_asst is None:
        raise ValueError("tool_results provided but no assistant tool_calls in history")

    calls = last_asst["tool_calls"]
    for call, result in zip(calls, tool_results):
        outputs = result.get("outputs") or []
        content = json.dumps(outputs[0] if outputs else {})
        msgs.append({
            "role": "tool",
            "tool_call_id": call["id"],
            "content": content,
        })
    return msgs


def _parse_tool_calls(message: dict) -> list[dict]:
    """Normalize OpenAI tool_calls to the orchestrator's expected shape:
    [{"name", "arguments" (dict), "id"}]."""
    out: list[dict] = []
    for tc in message.get("tool_calls") or []:
        fn = tc.get("function", {})
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except (ValueError, TypeError):
            args = {}
        out.append({
            "name": fn.get("name", ""),
            "arguments": args,
            "id": tc.get("id", ""),
        })
    return out


def chat(
    messages: list[ChatMessage],
    tools: list[dict] | None = None,
    model: str | None = None,
    *,
    tool_results: list[dict] | None = None,
    chat_history: list[dict] | None = None,
) -> ChatResponse:
    """Call an OpenAI-compatible chat endpoint with the tool loop.

    ``chat_history`` is the running OpenAI messages array; the orchestrator
    passes back whatever we returned last turn. When ``tool_results`` is given
    we append ``tool`` messages and continue; otherwise it is turn 1.
    """
    s = get_settings()
    if not s.llm_base_url or not s.llm_api_key:
        raise RuntimeError(
            "OpenAI-compatible provider not configured: set LLM_BASE_URL and LLM_API_KEY"
        )

    if chat_history:
        openai_msgs = [dict(m) for m in chat_history]
    else:
        openai_msgs = _openai_messages(messages)

    if tool_results:
        openai_msgs = _apply_tool_results(openai_msgs, tool_results)

    body: dict[str, Any] = {
        "model": model or s.llm_model or "auto",
        "messages": openai_msgs,
    }
    oai_tools = _openai_tools(tools)
    if oai_tools:
        body["tools"] = oai_tools
        body["tool_choice"] = "auto"

    base = s.llm_base_url.rstrip("/")
    with httpx.Client(timeout=s.oai_timeout_s) as client:
        r = client.post(
            f"{base}/chat/completions",
            headers={
                "Authorization": f"Bearer {s.llm_api_key}",
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

    # Extend the running conversation: append the assistant turn so the next
    # iteration can pair tool_results against these tool_calls.
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
