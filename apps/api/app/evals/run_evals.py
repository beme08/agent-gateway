"""Eval runner: executes all scenarios and emits a markdown results report.

Usage:
    python -m app.evals.run_evals            # prints table + writes docs report
    python -m app.evals.run_evals --out path # custom report path
"""
from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from .scenarios import SCENARIOS


def run_all() -> tuple[int, list[dict]]:
    results = []
    for scenario in SCENARIOS:
        name, checks = scenario()
        passed = sum(1 for _, ok in checks if ok)
        results.append({
            "scenario": name,
            "passed": passed,
            "total": len(checks),
            "ok": passed == len(checks),
            "checks": checks,
        })
    return sum(1 for r in results if r["ok"]), results


def to_markdown(total_ok: int, results: list[dict]) -> str:
    lines = [
        "# Support Operations — Deterministic Evaluation Results",
        "",
        (
            f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')} · "
            f"Suite: {len(results)} scenarios · "
            f"Result: **{total_ok}/{len(results)} scenarios passed** "
            f"({sum(r['passed'] for r in results)}/{sum(r['total'] for r in results)} assertions)"
        ),
        "",
        "| # | Scenario | Assertions | Status |",
        "|---|----------|------------|--------|",
    ]
    for i, r in enumerate(results, 1):
        status = "PASS" if r["ok"] else "FAIL"
        lines.append(f"| {i} | `{r['scenario']}` | {r['passed']}/{r['total']} | {status} |")
    lines += ["", "## Assertion detail", ""]
    for r in results:
        lines.append(f"### `{r['scenario']}` — {'PASS' if r['ok'] else 'FAIL'}")
        for desc, ok in r["checks"]:
            lines.append(f"- {'[x]' if ok else '[ ]'} {desc}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None, help="markdown report output path")
    args = parser.parse_args()

    total_ok, results = run_all()
    print(to_markdown(total_ok, results))
    out = args.out or Path(__file__).resolve().parents[4] / "docs" / "support-ops" / "EVAL_RESULTS.md"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(to_markdown(total_ok, results))
    print(f"\nreport written to {out}", file=sys.stderr)
    return 0 if total_ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
