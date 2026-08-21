#!/usr/bin/env python3
"""Agent error analysis: read traces, group by failure taxonomy, propose test cases.

Agent-in-the-loop workflow this enables:
  1. OBSERVE   run the agent (demo suite / public traffic)
  2. ANALYZE   this script groups finished traces by failure class
  3. CODE      review free-text notes; relabel with --label (open -> axial coding)
  4. PROPAGATE accepted labels become eval-scenario candidates (from error
               analysis to test cases); confirmed regressions go into
               app/evals/scenarios.py and run in CI forever after.

Usage:
  python3 scripts/analyze_traces.py                 # last 50 traces, grouped report
  python3 scripts/analyze_traces.py -n 200          # wider window
  python3 scripts/analyze_traces.py --label <trace_id> retrieval_miss --note "query had no KB overlap"
  python3 scripts/analyze_traces.py --candidates    # only the test-case proposals

Reads SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY from apps/api/.env or env.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

TAXONOMY = [
    "none", "injection_blocked", "policy_denied", "argument_error",
    "retrieval_miss", "verification_failed", "provider_error",
    "tool_error", "loop_exhausted",
]

CANDIDATE_TEMPLATE = {
    "injection_blocked": "Adversarial: craft input that should be refused (assert blocked=True).",
    "policy_denied": "Guardrail: assert gateway denies '{tools}' for this caller role/tier.",
    "argument_error": "Validation: assert constraint rejection for args the model produced.",
    "retrieval_miss": "Retrieval: query phrasing returned no chunks — add golden query to retrieval_eval.",
    "verification_failed": "Verification: post-condition failed — assert remediation outcome is verification_failed.",
    "provider_error": "Reliability: provider failed — assert failover chain engaged and trace records it.",
    "tool_error": "Adapter: {tools} errored — add adapter-failure scenario or fix adapter.",
    "loop_exhausted": "Scaffolding: agent ran out of turns — consider tool-result summarization.",
    "none": "",
}


def load_env() -> tuple[str, str]:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if url and key:
        return url, key
    env_file = Path(__file__).resolve().parent.parent / "apps" / "api" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("SUPABASE_URL="):
                url = line.split("=", 1)[1].strip()
            if line.startswith("SUPABASE_SERVICE_ROLE_KEY="):
                key = line.split("=", 1)[1].strip()
    if not (url and key):
        sys.exit("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not found (env or apps/api/.env)")
    return url, key


def client():
    url, key = load_env()
    from supabase import create_client
    return create_client(url, key)


def fetch_traces(sb, limit: int) -> list[dict]:
    res = (
        sb.table("agent_traces")
        .select("id, user_message, final_status, failure_class, failure_notes, "
                "tool_loop_count, latency_ms, llm_provider, model_name, "
                "input_safety_status, retrieval_safety_status, error_message, created_at")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def tool_summary(sb, trace_ids: list[str]) -> dict[str, list[dict]]:
    if not trace_ids:
        return {}
    res = (
        sb.table("tool_calls")
        .select("trace_id, tool_name, status, risk_tier, policy_reason")
        .in_("trace_id", trace_ids)
        .execute()
    )
    out: dict[str, list[dict]] = defaultdict(list)
    for row in res.data or []:
        out[row["trace_id"]].append(row)
    return out


def report(traces: list[dict], tools_by_trace: dict) -> None:
    by_class: dict[str, list[dict]] = defaultdict(list)
    for t in traces:
        by_class[t.get("failure_class") or "unclassified"].append(t)

    print(f"traces analyzed: {len(traces)}\n")
    print(f"{'failure_class':<20} {'count':>6}  {'providers':<22} example")
    print("-" * 100)
    for cls, rows in sorted(by_class.items(), key=lambda kv: -len(kv[1])):
        providers = Counter(r.get("llm_provider") or "?" for r in rows)
        ex = rows[0]
        example = (ex.get("user_message") or "")[:48].replace("\n", " ")
        print(f"{cls:<20} {len(rows):>6}  {','.join(f'{p}:{c}' for p, c in providers.most_common(3)):<22} {example}")

    print("\n--- per-class detail (most recent 3) ---")
    for cls, rows in sorted(by_class.items()):
        if cls == "none":
            continue
        print(f"\n[{cls}]")
        for r in rows[:3]:
            tools = tools_by_trace.get(r["id"], [])
            tool_str = ", ".join(f"{t['tool_name']}:{t['status']}" for t in tools) or "no tools"
            notes = json.dumps(r.get("failure_notes") or {})[:120]
            print(f"  {r['id'][:8]}… {(r.get('user_message') or '')[:60].replace(chr(10), ' ')}")
            print(f"      tools: {tool_str}")
            if notes != "{}":
                print(f"      notes: {notes}")


def candidates(traces: list[dict]) -> int:
    proposals = []
    for t in traces:
        cls = t.get("failure_class")
        if not cls or cls == "none":
            continue
        template = CANDIDATE_TEMPLATE.get(cls, "")
        if not template:
            continue
        tools = []
        if "{tools}" in template:
            notes = t.get("failure_notes") or {}
            tools = ",".join(notes.get("tools") or notes.get("denied_tools") or [])
        proposals.append((t["id"], cls, template.format(tools=tools)))
    if not proposals:
        print("no test-case candidates — every trace classified 'none'")
        return 0
    print(f"{len(proposals)} test-case candidate(s) from error analysis:\n")
    for tid, cls, desc in proposals:
        print(f"  [{cls}] {desc}")
        print(f"        source trace: {tid}")
    return len(proposals)


def label(sb, trace_id: str, failure_class: str, note: str | None) -> None:
    if failure_class not in TAXONOMY:
        sys.exit(f"invalid class '{failure_class}'; choose from: {', '.join(TAXONOMY)}")
    update: dict = {"failure_class": failure_class}
    if note:
        res = sb.table("agent_traces").select("failure_notes").eq("id", trace_id).single().execute()
        notes = res.data.get("failure_notes") or {}
        notes.setdefault("human_labels", []).append({"class": failure_class, "note": note})
        update["failure_notes"] = notes
    sb.table("agent_traces").update(update).eq("id", trace_id).execute()
    print(f"labeled {trace_id} -> {failure_class}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=50)
    ap.add_argument("--candidates", action="store_true", help="only print test-case proposals")
    ap.add_argument("--label", nargs=2, metavar=("TRACE_ID", "CLASS"), help="human relabel a trace")
    ap.add_argument("--note", default=None, help="optional note stored with --label")
    args = ap.parse_args()

    sb = client()

    if args.label:
        label(sb, args.label[0], args.label[1], args.note)
        return 0

    traces = fetch_traces(sb, args.n)
    if not traces:
        print("no traces found")
        return 0
    tools_by_trace = tool_summary(sb, [t["id"] for t in traces])

    if args.candidates:
        n = candidates(traces)
        return 0
    report(traces, tools_by_trace)
    print()
    candidates(traces)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
