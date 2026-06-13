"""First-boot ingestion. Reads the four seeded HR documents from
supabase/seed/documents, chunks them, embeds with Cohere (or the local mock),
and upserts into document_chunks. Idempotent: keyed on (tenant, document, chunk_index).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

from ..config import get_settings
from ..db import service_client
from ..llm import cohere
from ..rag.chunk import chunk_text

# Mapping of (tenant_slug) -> list of (filename, title, acl_tags)
SEED_DOCS: list[tuple[str, str, str, list[str]]] = [
    ("acme",   "remote-work.md", "Acme Remote Work Policy", ["public", "hr_policy"]),
    ("acme",   "sick-leave.md",  "Acme Sick Leave Policy",  ["public", "hr_policy"]),
    ("acme",   "pto.md",         "Acme PTO Policy",         ["public", "hr_policy"]),
    ("acme",   "exec-comp.md",   "Acme Executive Compensation", ["executive"]),
    ("globex", "remote-work.md", "Globex Remote Work Policy", ["public", "hr_policy"]),
    ("globex", "sick-leave.md",  "Globex Sick Leave Policy",  ["public", "hr_policy"]),
    ("globex", "pto.md",         "Globex PTO Policy",         ["public", "hr_policy"]),
    ("globex", "exec-comp.md",   "Globex Executive Compensation", ["executive"]),
]


def _tenant_id_for_slug(slug: str) -> str:
    res = service_client().table("tenants").select("id").eq("slug", slug).single().execute()
    return res.data["id"]


def _ensure_document(tenant_id: str, title: str, source: str, acl_tags: list[str]) -> str:
    existing = (
        service_client()
        .table("documents")
        .select("id")
        .eq("tenant_id", tenant_id)
        .eq("title", title)
        .limit(1)
        .execute()
    )
    if existing.data:
        return existing.data[0]["id"]
    res = (
        service_client()
        .table("documents")
        .insert({"tenant_id": tenant_id, "title": title, "source": source, "acl_tags": acl_tags})
        .execute()
    )
    return res.data[0]["id"]


def _delete_existing_chunks(document_id: str) -> None:
    service_client().table("document_chunks").delete().eq("document_id", document_id).execute()


def _insert_chunks(document_id: str, tenant_id: str, acl_tags: list[str], texts: list[str]) -> None:
    embeddings = cohere.embed_documents(texts, input_type="search_document")
    rows = []
    for i, (text, emb) in enumerate(zip(texts, embeddings)):
        rows.append({
            "document_id": document_id,
            "tenant_id": tenant_id,
            "chunk_index": i,
            "content": text,
            "embedding": emb,
            "acl_tags": acl_tags,
        })
    # batch insert in groups of 50
    for i in range(0, len(rows), 50):
        service_client().table("document_chunks").insert(rows[i : i + 50]).execute()


async def run_seed_ingest() -> None:
    settings = get_settings()
    docs_dir = Path(__file__).resolve().parents[3] / "supabase" / "seed" / "documents"
    if not docs_dir.exists():
        # Fallback for when running from apps/api
        alt = Path(os.environ.get("SEED_DOCS_DIR", "/app/supabase/seed/documents"))
        if alt.exists():
            docs_dir = alt
    if not docs_dir.exists():
        print(f"[seed_ingest] docs dir not found: {docs_dir}")
        return

    for slug, filename, title, acl_tags in SEED_DOCS:
        path = docs_dir / filename
        if not path.exists():
            print(f"[seed_ingest] missing {path}")
            continue
        text = path.read_text(encoding="utf-8")
        chunks = chunk_text(text, size=800, overlap=150)
        if not chunks:
            continue
        tenant_id = _tenant_id_for_slug(slug)
        doc_id = _ensure_document(tenant_id, title, str(path), acl_tags)
        _delete_existing_chunks(doc_id)
        _insert_chunks(doc_id, tenant_id, acl_tags, chunks)
        print(f"[seed_ingest] indexed {len(chunks)} chunks for {title} (tenant={slug})")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_seed_ingest())
