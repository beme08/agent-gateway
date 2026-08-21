"""Adapter base: shared error type and constants."""
from __future__ import annotations


class AdapterError(Exception):
    """Raised by adapters on invalid input or simulated upstream failure."""


# Services known to the mock deployment/observability world. Argument
# validation in the policy engine enforces this allowlist BEFORE an adapter
# is ever called; adapters re-check defensively.
KNOWN_SERVICES = ("checkout-api", "payments-api", "search-api", "web-frontend", "analytics")
KNOWN_ENVIRONMENTS = ("staging", "production")
