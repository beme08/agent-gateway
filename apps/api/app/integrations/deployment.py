"""Deployment adapter (mock): restart / scale / rollback with post-conditions.

Mutates the observability world so that remediation has a real, checkable
effect: restart_service repairs a degraded service UNLESS
simulate_restart_failure is set — in which case the action "executes" but
the post-condition check fails, exercising the verification gate.

Every method returns {ok, output, verification} where ``verification`` is
the adapter's own post-condition check. The tool layer records this as
remediation evidence: a remediation is not successful until verification
confirms the expected state.
"""
from __future__ import annotations

import threading
from typing import Protocol

from .base import KNOWN_ENVIRONMENTS, KNOWN_SERVICES, AdapterError
from .observability import get_observability

MAX_REPLICAS = 12
MIN_REPLICAS = 2


class DeploymentAdapter(Protocol):
    def restart_service(self, service: str, environment: str) -> dict: ...
    def scale_service(self, service: str, environment: str, replicas: int) -> dict: ...
    def rollback_deployment(self, service: str, environment: str, to_version: str) -> dict: ...
    def get_recent_deployments(self, service: str) -> dict: ...


class MockDeployment:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._deploy_log: list[dict] = []
        self._unreachable: bool = False
        self.simulate_restart_failure: bool = False
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self._deploy_log = [
                {"service": "checkout-api", "version": "v1.8.4", "deployed_at": "2026-08-19T08:00:00Z",
                 "by": "ci", "status": "current"},
                {"service": "payments-api", "version": "v1.9.1", "deployed_at": "2026-08-21T08:15:00Z",
                 "by": "ci", "status": "current"},
                {"service": "payments-api", "version": "v1.9.0", "deployed_at": "2026-08-14T10:00:00Z",
                 "by": "ci", "status": "previous"},
            ]
            self._unreachable = False
            self.simulate_restart_failure = False

    def set_unreachable(self) -> None:
        self._unreachable = True

    # ----- actions ----------------------------------------------------------

    def restart_service(self, service: str, environment: str) -> dict:
        self._guard(service, environment)
        obs = get_observability()
        with self._lock:
            if self.simulate_restart_failure:
                # Action performed, but the fault persists — verification must
                # catch this and the remediation must be marked failed.
                verification = obs.get_service_health(service)
                verification["post_condition_met"] = verification["status"] == "healthy"
                return self._record(service, "restart", {"environment": environment},
                                    ok=True, verification=verification)
            obs.set_health(service, status="healthy", error_rate=0.004, p99_latency_ms=180)
            verification = obs.get_service_health(service)
            verification["post_condition_met"] = verification["status"] == "healthy"
            return self._record(service, "restart", {"environment": environment},
                                ok=True, verification=verification)

    def scale_service(self, service: str, environment: str, replicas: int) -> dict:
        self._guard(service, environment)
        if not (MIN_REPLICAS <= replicas <= MAX_REPLICAS):
            raise AdapterError(f"replicas must be between {MIN_REPLICAS} and {MAX_REPLICAS}")
        obs = get_observability()
        obs.set_health(service, p99_latency_ms=max(120, obs.get_service_health(service)["p99_latency_ms"] - 100))
        verification = obs.get_service_health(service)
        verification["post_condition_met"] = verification["p99_latency_ms"] < 900
        return self._record(service, "scale",
                            {"environment": environment, "replicas": replicas},
                            ok=True, verification=verification)

    def rollback_deployment(self, service: str, environment: str, to_version: str) -> dict:
        self._guard(service, environment)
        if not to_version or not str(to_version).startswith("v"):
            raise AdapterError("to_version must look like 'v1.2.3'")
        obs = get_observability()
        obs.set_health(service, version=to_version, status="healthy",
                       error_rate=0.008, p99_latency_ms=225)
        verification = obs.get_service_health(service)
        verification["post_condition_met"] = (
            verification["version"] == to_version and verification["status"] == "healthy"
        )
        return self._record(service, "rollback",
                            {"environment": environment, "to_version": to_version},
                            ok=True, verification=verification)

    def get_recent_deployments(self, service: str) -> dict:
        if service not in KNOWN_SERVICES:
            raise AdapterError(f"unknown service '{service}'")
        if self._unreachable:
            raise AdapterError("deployment upstream unreachable")
        return {"service": service,
                "deployments": [d for d in self._deploy_log if d["service"] == service]}

    # ----- helpers ----------------------------------------------------------

    def _guard(self, service: str, environment: str) -> None:
        if self._unreachable:
            raise AdapterError("deployment upstream unreachable")
        if service not in KNOWN_SERVICES:
            raise AdapterError(f"unknown service '{service}'")
        if environment not in KNOWN_ENVIRONMENTS:
            raise AdapterError(f"unknown environment '{environment}'")

    def _record(self, service: str, action: str, params: dict, ok: bool, verification: dict) -> dict:
        entry = {"service": service, "action": action, **params,
                 "acted_at": "deterministic-mock", "status": "current" if ok else "failed"}
        with self._lock:
            self._deploy_log.insert(0, entry)
        return {
            "ok": ok,
            "output": {"performed": action, "service": service, **params},
            "verification": verification,
        }


_singleton: MockDeployment | None = None


def get_deployment() -> MockDeployment:
    global _singleton
    if _singleton is None:
        _singleton = MockDeployment()
    return _singleton
