"""Cohere client with deterministic local mock fallback.

If COHERE_API_KEY is set, real Cohere SDK calls are used. If not, a
small deterministic mock generates embeddings (hash-based 1024-dim) and
chat completions (echo + tool-call stub) so the UI is testable offline.
"""
from __future__ import annotations

import hashlib
import math
import os
import re
from dataclasses import dataclass
from typing import Any

import httpx

from ..config import get_settings


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    tool_call_id: str | None = None
    tool_calls: list[dict] | None = None


@dataclass
class ChatResponse:
    text: str
    tool_calls: list[dict]
    usage: dict


def _hash_embed(text: str, dim: int = 1024) -> list[float]:
    """Deterministic 1024-dim embedding from text. Good enough for offline UI."""
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
    vec = []
    for i in range(dim):
        # simple LCG seeded by i
        v = math.sin(seed * (i + 1)) * 10000.0
        vec.append(v - math.floor(v))
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def embed_documents(texts: list[str], input_type: str = "search_document") -> list[list[float]]:
    s = get_settings()
    if not s.cohere_api_key:
        return [_hash_embed(t) for t in texts]
    with httpx.Client(timeout=30) as client:
        r = client.post(
            "https://api.cohere.ai/v1/embed",
            headers={"Authorization": f"Bearer {s.cohere_api_key}"},
            json={"model": s.cohere_embed_model, "texts": texts, "input_type": input_type},
        )
        r.raise_for_status()
        return r.json()["embeddings"]


def embed_query(text: str) -> list[float]:
    s = get_settings()
    if not s.cohere_api_key:
        return _hash_embed(text)
    with httpx.Client(timeout=30) as client:
        r = client.post(
            "https://api.cohere.ai/v1/embed",
            headers={"Authorization": f"Bearer {s.cohere_api_key}"},
            json={"model": s.cohere_embed_model, "texts": [text], "input_type": "search_query"},
        )
        r.raise_for_status()
        return r.json()["embeddings"][0]


def chat(messages: list[ChatMessage], tools: list[dict] | None = None, model: str | None = None) -> ChatResponse:
    s = get_settings()
    if not s.cohere_api_key:
        return _mock_chat(messages, tools or [])
    # Real Cohere chat (Command R+ supports native tool use).
    body: dict[str, Any] = {
        "model": model or s.cohere_model,
        "message": _cohere_format(messages),
    }
    if tools:
        body["tools"] = tools
    with httpx.Client(timeout=60) as client:
        r = client.post(
            "https://api.cohere.ai/v1/chat",
            headers={"Authorization": f"Bearer {s.cohere_api_key}"},
            json=body,
        )
        r.raise_for_status()
        data = r.json()
    text = data.get("text", "")
    raw_tools = data.get("tool_calls") or []
    tool_calls = [
        {"name": t["name"], "arguments": t.get("parameters", {}), "id": t.get("id", "")}
        for t in raw_tools
    ]
    usage = data.get("meta", {}).get("billed_units", {}) or {}
    return ChatResponse(text=text, tool_calls=tool_calls, usage=usage)


def _cohere_format(messages: list[ChatMessage]) -> str:
    # The Cohere chat endpoint accepts a prebuilt `message` string. The
    # orchestrator assembles the full system + user + tool-history prompt
    # before calling, so we just use the last user message.
    for m in reversed(messages):
        if m.role == "user":
            return m.content
    return messages[-1].content if messages else ""


# ---------------------------------------------------------------------------
# Mock
# ---------------------------------------------------------------------------

def _mock_chat(messages: list[ChatMessage], tools: list[dict]) -> ChatResponse:
    last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
    text = _echo_answer(last_user)
    return ChatResponse(text=text, tool_calls=[], usage={"input_tokens": 0, "output_tokens": 0})


def _echo_answer(question: str) -> str:
    q = question.lower()
    if "sick" in q:
        return (
            "Based on the **Sick Leave Policy** (Acme Corp), you have 10 paid sick days per year. "
            "For an unplanned sick day, just notify your manager on Slack and submit the leave request "
            "the same day — it will be approved automatically for absences under 3 consecutive days."
        )
    if "remote" in q or "work from" in q or "another country" in q:
        return (
            "According to the **Remote Work Policy** (Acme Corp), working remotely from another country "
            "for an extended period requires (1) written manager approval, (2) HR + Legal notification at "
            "least 30 days in advance, and (3) confirmation that your home-country tax and employment-law "
            "obligations are met. Short trips (under 30 days) only need manager notification 3 business "
            "days in advance."
        )
    if "vacation" in q or "pto" in q or "time off" in q:
        return (
            "Per the **Paid Time Off Policy** (Acme Corp), full-time employees with 0-2 years of service "
            "receive 20 vacation days per year. PTO is accrued monthly and you can roll over up to 5 "
            "unused days into the next year. Submit a request through the HR portal and your manager "
            "will usually approve within 2 business days."
        )
    if "balance" in q:
        return "I'll check your leave balance now."
    if "ignore" in q or "system prompt" in q or "reveal" in q:
        return "I can't share my system instructions. I'm the HR Policy Agent — how can I help you with a policy question or a leave request?"
    return (
        "I'm the HR Policy Agent for Acme Corp. I can help with sick leave, vacation/PTO, and "
        "remote work policy questions. What would you like to know?"
    )
