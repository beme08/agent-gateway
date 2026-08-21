"""Observability adapter (mock): deterministic service health signals.

Stands in for a monitoring system (Datadog/Librium-style). The gateway's
diagnosis and verification tools read from here; the deployment adapter
mutates it, so act -> verify causality is real inside the simulated world.
"""
from __future__ import annotations

import threading
from typing import Protocol

from .base import KNOWN_SERVICES, AdapterError


class ObservabilityAdapter(Protocol):
    def get_service_health(self, service: str) -> dict: ...
    def get_metrics(self, service: str) -> dict: ...


_INITIAL_STATE: dict[str, dict] = {
    "checkout-api": {"status": "degraded", "error_rate": 0.31, "p99_latency_ms": 950,
                     "version": "v1.8.4", "uptime_pct": 99.12},
    # payments-api starts latency-degraded to match seeded ticket TKT-1003
    # (p99 regression after the 08:15 UTC deploy of v1.9.1).
    "payments-api": {"status": "degraded", "error_rate": 0.012, "p99_latency_ms": 700,
                     "version": "v1.9.1", "uptime_pct": 99.98},
    "search-api": {"status": "healthy", "error_rate": 0.005, "p99_latency_ms": 140,
                   "version": "v2.1.0", "uptime_pct": 99.99},
    "web-frontend": {"status": "healthy", "error_rate": 0.002, "p99_latency_ms": 310,
                     "version": "v3.4.1", "uptime_pct": 99.97},
    "analytics": {"status": "healthy", "error_rate": 0.01, "p99_latency_ms": 400,
                  "version": "v0.9.7", "uptime_pct": 99.90},
}


class MockObservability:
    """Deterministic in-memory observability backend."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state: dict[str, dict] = {}
        self._unreachable: set[str] = set()
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self._state = {s: dict(v) for s, v in _INITIAL_STATE.items()}
            self._unreachable = set()

    def set_unreachable(self, service: str | None = None) -> None:
        """Simulate upstream failure for one service (or all when None)."""
        with self._lock:
            if service is None:
                self._unreachable.update(self._state.keys())
            else:
                self._ensure_known(service)
                self._unreachable.add(service)

    def set_health(self, service: str, **fields) -> None:
        with self._lock:
            self._ensure_known(service)
            self._state[service].update(fields)

    def get_service_health(self, service: str) -> dict:
        with self._lock:
            self._ensure_known(service)
            if service in self._unreachable:
                raise AdapterError(f"observability upstream unreachable for '{service}'")
            return {
                "service": service,
                **self._state[service],
                "checked_at": "deterministic-mock",
            }

    def get_metrics(self, service: str) -> dict:
        health = self.get_service_health(service)
        return {
            "service": service,
            "error_rate_5m": health["error_rate"],
            "p99_latency_ms_5m": health["p99_latency_ms"],
            "version": health["version"],
        }

    @staticmethod
    def _ensure_known(service: str) -> None:
        if service not in KNOWN_SERVICES:
            raise AdapterError(f"unknown service '{service}'")


_singleton: MockObservability | None = None


def get_observability() -> MockObservability:
    global _singleton
    if _singleton is None:
        _singleton = MockObservability()
    return _singleton
