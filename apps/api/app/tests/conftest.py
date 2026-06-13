"""Shared pytest fixtures. Disable the Supabase quota lookup for policy tests."""
from app.agent.tools import policy as policy_module


def pytest_collection_modifyitems(config, items):
    # Always set a no-op quota provider for unit tests so we don't need a
    # real Supabase connection.
    policy_module.quota_provider = lambda _tenant_id: None
