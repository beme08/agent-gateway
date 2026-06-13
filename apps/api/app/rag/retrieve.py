"""ACL-filtered retrieval over pgvector."""
from __future__ import annotations

from typing import Iterable

from ..db import service_client
from ..llm import cohere

ROLE_TAGS: dict[str, list[str]] = {
    "viewer":   ["public"],
    "employee": ["public", "hr_policy"],
    "manager":  ["public", "hr_policy", "manager_only"],
    "admin":    ["public", "hr_policy", "manager_only", "executive"],
}


def accessible_tags(role: str) -> list[str]:
    return ROLE_TAGS.get(role, ["public"])


def search(
    tenant_id: str,
    role: str,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    embedding = cohere.embed_query(query)
    res = (
        service_client()
        .rpc(
            "match_document_chunks",
            {
                "query_embedding": embedding,
                "filter_tenant": tenant_id,
                "filter_tags": accessible_tags(role),
                "match_count": top_k,
            },
        )
        .execute()
    )
    return res.data or []
