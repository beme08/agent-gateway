"""In-process rate limiting for the agent API.

Protects the expensive LLM/tool endpoints from abuse (bot crawls, scripted
hammering) without external dependencies. State is per-process, which is fine
for single-instance free tier; swap for Redis if scaling horizontally.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import DefaultDict, Deque

from fastapi import HTTPException, Request


class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: DefaultDict[str, Deque[float]] = defaultdict(deque)

    def _prune(self, key: str, now: float) -> None:
        q = self._hits[key]
        while q and q[0] <= now - self.window_seconds:
            q.popleft()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        self._prune(key, now)
        q = self._hits[key]
        if len(q) >= self.max_requests:
            return False
        q.append(now)
        return True

    def clear(self) -> None:
        self._hits.clear()


def client_key(request: Request) -> str:
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.client.host or "unknown"
    auth = request.headers.get("authorization", "")
    # Bind limits to caller identity when present so shared NAT IPs aren't the bottleneck.
    token_fp = ""
    if auth.lower().startswith("bearer "):
        token_fp = auth[7:].strip()[:24]
    return f"{ip}:{token_fp}"


# Chat is the expensive one (LLM + tool loop). Leave endpoints get a looser cap.
CHAT_LIMIT = SlidingWindowLimiter(max_requests=20, window_seconds=60)
GENERAL_LIMIT = SlidingWindowLimiter(max_requests=120, window_seconds=60)


def enforce_chat_limit(request: Request) -> None:
    if not CHAT_LIMIT.allow(client_key(request)):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait a moment and retry.")


def enforce_general_limit(request: Request) -> None:
    if not GENERAL_LIMIT.allow(client_key(request)):
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
