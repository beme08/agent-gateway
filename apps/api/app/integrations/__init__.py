"""Integration adapters for the Support Operations environment.

Every external system sits behind a Protocol interface so real
implementations (PagerDuty, Datadog, GitHub, Slack, ...) can replace the
deterministic mock adapters without touching the agent, tools, or gateway.

The mock world is a deterministic state machine:
  - checkout-api starts DEGRADED (error_rate 0.31) to match demo ticket
    TKT-1001; a successful restart flips it healthy — which is what
    verify_service_health then proves.
  - simulate_restart_failure forces the post-remediation verification to
    fail (eval: verification gate).
  - set_unreachable makes an adapter raise AdapterError (eval: failure
    handling).
"""
from __future__ import annotations

from .base import AdapterError
from .deployment import DeploymentAdapter, get_deployment
from .github import GitHubAdapter, get_github
from .observability import ObservabilityAdapter, get_observability
from .slack import SlackAdapter, get_slack
from .ticketing import TicketingAdapter, get_ticketing

__all__ = [
    "AdapterError",
    "DeploymentAdapter",
    "GitHubAdapter",
    "ObservabilityAdapter",
    "SlackAdapter",
    "TicketingAdapter",
    "get_deployment",
    "get_github",
    "get_observability",
    "get_slack",
    "get_ticketing",
]


def reset_support_world() -> None:
    """Reinitialize every mock adapter to its deterministic initial state."""
    get_observability().reset()
    get_deployment().reset()
    get_github().reset()
    get_slack().reset()
