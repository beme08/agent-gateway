"""Slack adapter (mock): deterministic notification posting."""
from __future__ import annotations

import threading
from typing import Protocol


class SlackAdapter(Protocol):
    def post_message(self, channel: str, text: str) -> dict: ...
    def list_messages(self) -> list[dict]: ...


class MockSlack:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._messages: list[dict] = []
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self._messages = []

    def post_message(self, channel: str, text: str) -> dict:
        if not channel or not text:
            raise ValueError("channel and text are required")
        with self._lock:
            ts = f"1758.{len(self._messages) + 1:06d}"
            msg = {"channel": channel, "text": text[:2000], "ts": ts, "posted": True}
            self._messages.append(msg)
            return msg

    def list_messages(self) -> list[dict]:
        with self._lock:
            return list(self._messages)


_singleton: MockSlack | None = None


def get_slack() -> MockSlack:
    global _singleton
    if _singleton is None:
        _singleton = MockSlack()
    return _singleton
