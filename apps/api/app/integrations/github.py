"""GitHub adapter (mock): deterministic issue creation."""
from __future__ import annotations

import threading
from typing import Protocol


class GitHubAdapter(Protocol):
    def create_issue(self, title: str, body: str, labels: list[str] | None = None) -> dict: ...
    def list_issues(self) -> list[dict]: ...


class MockGitHub:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._next_issue = 1200
        self._issues: list[dict] = []
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self._next_issue = 1200
            self._issues = []

    def create_issue(self, title: str, body: str, labels: list[str] | None = None) -> dict:
        with self._lock:
            number = self._next_issue
            self._next_issue += 1
            issue = {
                "number": number,
                "title": title,
                "labels": labels or [],
                "url": f"https://github.com/acme/ops/issues/{number}",
                "created": True,
            }
            self._issues.append(issue)
            return issue

    def list_issues(self) -> list[dict]:
        with self._lock:
            return list(self._issues)


_singleton: MockGitHub | None = None


def get_github() -> MockGitHub:
    global _singleton
    if _singleton is None:
        _singleton = MockGitHub()
    return _singleton
