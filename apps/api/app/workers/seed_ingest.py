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
# Tags use containment semantics (`acl_tags <@ caller_tags`): a chunk is only
# returned when every tag it carries is in the caller's granted set. `public`
# is the widest grant (present in every role), so public-only tags are seen by
# all roles. Do not mix a broad tag with a restricted one on the same chunk.
SEED_DOCS: list[tuple[str, str, str, list[str]]] = [
    ("acme",   "remote-work.md", "Acme Remote Work Policy", ["public"]),
    ("acme",   "sick-leave.md",  "Acme Sick Leave Policy",  ["public"]),
    ("acme",   "pto.md",         "Acme PTO Policy",         ["public"]),
    ("acme",   "exec-comp.md",   "Acme Executive Compensation", ["executive"]),
    ("globex", "remote-work.md", "Globex Remote Work Policy", ["public"]),
    ("globex", "sick-leave.md",  "Globex Sick Leave Policy",  ["public"]),
    ("globex", "pto.md",         "Globex PTO Policy",         ["public"]),
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


def _backfill_chunk_embeddings() -> None:
    """Embed DB-seeded chunks that lack embeddings (e.g. support-KB seeds).

    Idempotent: only touches rows with embedding IS NULL. Uses the same
    embed_documents path as file ingestion (Cohere when keyed, deterministic
    local hash otherwise) so queries and chunks always share a vector space.
    """
    res = (
        service_client()
        .table("document_chunks")
        .select("id, content")
        .is_("embedding", "null")
        .limit(500)
        .execute()
    )
    rows = res.data or []
    if not rows:
        return
    embeddings = cohere.embed_documents([r["content"] for r in rows])
    for row, emb in zip(rows, embeddings):
        service_client().table("document_chunks").update({"embedding": emb}).eq("id", row["id"]).execute()
    print(f"[seed_ingest] backfilled {len(rows)} chunk embeddings")


async def run_seed_ingest() -> None:
    # Embedding backfill runs regardless of the docs dir: DB-seeded chunks
    # (e.g. support KB) need embeddings even when HR markdown files are absent.
    try:
        _backfill_chunk_embeddings()
    except Exception as e:
        print(f"[seed_ingest] embedding backfill failed (non-fatal): {e}")

    settings = get_settings()
    docs_dir = Path(__file__).resolve().parents[4] / "supabase" / "seed" / "documents"
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
