"""Scripted LLM provider for deterministic evals.

Plays the role of ox-alpha with a pre-recorded tool-call script per
scenario. Same chat() contract as the real providers.
"""
from __future__ import annotations

from app.llm.cohere import ChatResponse


class ScriptExhausted(Exception):
    pass


class ScriptedLLM:
    def __init__(self, steps: list[dict]) -> None:
        self.steps = list(steps)
        self.turn = 0
        self.calls: list[list[dict]] = []

    def chat(self, messages, tools=None, model=None, *,
             tool_results=None, chat_history=None) -> ChatResponse:
        if not self.steps:
            raise ScriptExhausted("script ran out of turns — add a final {'text': ...} step")
        step = self.steps.pop(0)
        self.turn += 1
        if "text" in step:
            return ChatResponse(text=step["text"], tool_calls=[], usage={},
                                chat_history=[{"role": "assistant", "content": step["text"]}])
        calls = []
        for i, tc in enumerate(step.get("tools", []), start=1):
            calls.append({
                "name": tc["name"],
                "arguments": tc.get("arguments", {}),
                "id": f"call_{self.turn}_{i}",
            })
        self.calls.append(calls)
        assistant_turn = {"role": "assistant", "content": "", "tool_calls": [
            {"id": c["id"], "function": {"name": c["name"], "arguments": _json(c["arguments"])}}
            for c in calls
        ]}
        return ChatResponse(text="", tool_calls=calls, usage={},
                            chat_history=[assistant_turn])


def _json(value) -> str:
    import json
    return json.dumps(value)
