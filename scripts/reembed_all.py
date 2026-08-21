#!/usr/bin/env python3
"""Recompute embeddings for every document_chunk with the current embedder.

Run after changing the offline embedding function (or to migrate to/from
Cohere semantic embeddings). Idempotent; safe to re-run.

Usage: apps/api/.venv/bin/python scripts/reembed_all.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api"))

_env = Path(__file__).resolve().parent.parent / "apps" / "api" / ".env"
if _env.exists():
    for line in _env.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from app.db import service_client  # noqa: E402
from app.llm import cohere  # noqa: E402


def main() -> int:
    sb = service_client()
    rows = (
        sb.table("document_chunks")
        .select("id, content")
        .order("created_at")
        .limit(1000)
        .execute()
        .data
        or []
    )
    if not rows:
        print("no chunks found")
        return 0
    embeddings = cohere.embed_documents([r["content"] for r in rows])
    for row, emb in zip(rows, embeddings):
        sb.table("document_chunks").update({"embedding": emb}).eq("id", row["id"]).execute()
    print(f"re-embedded {len(rows)} chunks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
