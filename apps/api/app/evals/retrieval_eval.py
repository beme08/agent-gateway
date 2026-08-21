"""Retrieval evaluation against the live knowledge base.

Golden set of (query -> expected document title) pairs covering both
environments (HR policy + support KB). For each query we run the SAME
retrieval path production uses (embed -> match_document_chunks with the
caller role's ACL tags) and report hit@k, MRR, and per-query detail.

Deterministic for a fixed embedding space; safe to run in CI when Supabase
credentials are present (skipped otherwise).

Usage:
    python -m app.evals.retrieval_eval            # table + summary
    python -m app.evals.retrieval_eval --k 5      # evaluate top-5
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

GOLDEN = [
    # (query, expected document title substring, caller role)
    ("how many sick days do I get", "Sick Leave Policy", "employee"),
    ("can I work from another country", "Remote Work Policy", "employee"),
    ("how much vacation time accrue", "PTO Policy", "employee"),
    ("executive compensation structure", "Executive Compensation", "admin"),
    ("checkout-api returning 503 restart procedure", "Remediation Runbook", "manager"),
    ("payments-api latency regression rollback approval", "Runbook", "manager"),
    ("what actions can the agent execute automatically", "Support Operations Policy", "manager"),
    ("incident history connection pool exhaustion", "Incident History", "manager"),
]


def _load_env() -> None:
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        return
    env_file = Path(__file__).resolve().parents[3] / ".env"
    alt = Path(__file__).resolve().parents[4] / "apps" / "api" / ".env"
    for f in (alt, env_file):
        if f.exists():
            for line in f.read_text().splitlines():
                if line.startswith("SUPABASE_URL="):
                    os.environ.setdefault("SUPABASE_URL", line.split("=", 1)[1].strip())
                if line.startswith("SUPABASE_SERVICE_ROLE_KEY="):
                    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", line.split("=", 1)[1].strip())


def run(k: int = 3) -> dict:
    _load_env()
    if not (os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY")):
        return {"skipped": True}

    from ..db import service_client
    from ..llm import cohere
    from ..rag.retrieve import accessible_tags

    sb = service_client()
    docs = {
        d["id"]: d["title"]
        for d in sb.table("documents").select("id, title").execute().data or []
    }

    results = []
    hits = 0
    rr_sum = 0.0
    for query, expected, role in GOLDEN:
        embedding = cohere.embed_query(query)
        res = (
            sb.rpc("match_document_chunks", {
                "query_embedding": embedding,
                "filter_tenant": "11111111-1111-1111-1111-111111111111",
                "filter_tags": accessible_tags(role),
                "match_count": k,
            }).execute()
        )
        ranked_titles = [docs.get(c["document_id"], "?") for c in (res.data or [])]
        rank = next((i + 1 for i, t in enumerate(ranked_titles) if expected in t), None)
        hit = rank is not None
        hits += hit
        rr_sum += (1.0 / rank) if rank else 0.0
        results.append({
            "query": query,
            "expected": expected,
            "role": role,
            "rank": rank,
            "top_titles": ranked_titles[:k],
        })

    n = len(GOLDEN)
    return {
        "skipped": False,
        "k": k,
        "n": n,
        "hit_at_k": round(hits / n, 3),
        "mrr": round(rr_sum / n, 3),
        "results": results,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=3)
    args = ap.parse_args()

    out = run(k=args.k)
    if out.get("skipped"):
        print("skipped: Supabase credentials not configured")
        return 0

    print(f"retrieval eval — {out['n']} golden queries, top-{out['k']}, ACL-filtered\n")
    print(f"{'query':<52} {'role':<9} {'rank':<5} expected")
    print("-" * 100)
    for r in out["results"]:
        rank = r["rank"] if r["rank"] else "-"
        mark = "✓" if r["rank"] else "✗"
        print(f"{r['query']:<52} {r['role']:<9} {mark}{rank!s:<4} {r['expected']}")
    print(f"\nhit@{out['k']}: {out['hit_at_k']}   MRR: {out['mrr']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
