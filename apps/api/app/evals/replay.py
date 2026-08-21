"""Sandboxed replay of production traces.

Given a trace id, fetch its recorded tool calls and re-run each proposed
action through the CURRENT policy engine in a sandbox (no adapters touched,
no LLM, no writes). Produces a diff: what the gateway decided then vs. what
it would decide now.

Use cases:
  * guardrail regression detection: did a policy change flip any historical
    decision?
  * "would we still allow this?" audits after risk-tier/constraint changes
  * evidence for incident reviews

Usage:
  python -m app.evals.replay <trace_id>            # replay one trace
  python -m app.evals.replay --last 20             # replay recent traces
Exit code 0 = all decisions stable; 1 = at least one flipped.
"""
from __future__ import annotations

import argparse

from ..agent.tools.definitions import build_registry
from ..agent.tools.policy import check as policy_check
from ..db import service_client


def fetch_trace(trace_id: str) -> dict | None:
    res = (
        service_client()
        .table("agent_traces")
        .select("id, tenant_id, user_id, user_message, final_status, llm_provider, created_at")
        .eq("id", trace_id)
        .single()
        .execute()
    )
    return res.data or None


def fetch_calls(trace_id: str) -> list[dict]:
    res = (
        service_client()
        .table("tool_calls")
        .select("tool_name, arguments, status, caller_role, policy_decision, policy_reason")
        .eq("trace_id", trace_id)
        .order("created_at")
        .execute()
    )
    return res.data or []


def role_rank(role: str | None) -> int:
    return {"viewer": 0, "employee": 1, "manager": 2, "admin": 3}.get(role or "viewer", 0)


def replay_trace(trace_id: str, registry=None) -> dict:
    registry = registry or build_registry()
    trace = fetch_trace(trace_id)
    if not trace:
        return {"trace_id": trace_id, "error": "not found"}

    caller = {
        "user_id": trace["user_id"],
        "tenant_id": trace["tenant_id"],
        # Replay uses the recorded caller role: we are auditing decisions,
        # not re-authorizing a live user.
        "role": None,
    }
    rows = fetch_calls(trace_id)
    results = []
    flips = 0
    for row in rows:
        caller["role"] = row.get("caller_role") or "viewer"
        verdict = policy_check(registry, caller, row["tool_name"], row.get("arguments") or {})
        then_allowed = row.get("policy_decision", "").startswith("allow")
        now_allowed = verdict.allow
        stable = then_allowed == now_allowed
        if not stable:
            flips += 1
        results.append({
            "tool": row["tool_name"],
            "then": f"{row.get('policy_decision')} ({(row.get('policy_reason') or '')[:60]})",
            "now": f"{'allow' if now_allowed else 'deny'} ({verdict.reason[:60]})",
            "stable": stable,
        })
    return {
        "trace_id": trace_id,
        "user_message": (trace.get("user_message") or "")[:80],
        "provider": trace.get("llm_provider"),
        "decisions": results,
        "flips": flips,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("trace_id", nargs="?", help="a single trace id to replay")
    ap.add_argument("--last", type=int, default=0, help="replay the N most recent traces")
    args = ap.parse_args()

    sb = service_client()
    ids: list[str] = []
    if args.trace_id:
        ids = [args.trace_id]
    elif args.last:
        rows = (
            sb.table("agent_traces")
            .select("id")
            .order("created_at", desc=True)
            .limit(args.last)
            .execute()
        )
        ids = [r["id"] for r in rows.data or []]
    else:
        ap.error("provide a TRACE_ID or --last N")

    total_flips = 0
    for tid in ids:
        out = replay_trace(tid)
        if "error" in out:
            print(f"{tid}: {out['error']}")
            continue
        print(f"\ntrace {tid[:8]}… provider={out['provider']} “{out['user_message']}”")
        for d in out["decisions"]:
            mark = "  ok  " if d["stable"] else " FLIP "
            print(f"  {mark} {d['tool']:<26} then: {d['then']}")
            if not d["stable"]:
                print(f"           {'':<26} now : {d['now']}")
        total_flips += out["flips"]

    print(f"\nreplayed {len(ids)} trace(s); decision flips: {total_flips}")
    return 1 if total_flips else 0


if __name__ == "__main__":
    raise SystemExit(main())
