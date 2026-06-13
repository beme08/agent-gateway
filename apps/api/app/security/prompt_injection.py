"""Prompt-injection detector.

This is one layer of defense-in-depth, not a guarantee. It catches obvious
patterns; sophisticated attacks are still possible. Treat the output as a
signal to wrap retrieved text in an UNTRUSTED block, log a security event,
or block the user input entirely.
"""
from __future__ import annotations

import base64
import re
from dataclasses import dataclass

# Patterns are intentionally conservative. False positives are logged but
# don't block the user input; retrieved-text matches add a [SUSPICIOUS CHUNK]
# prefix and are excluded from instruction-following.
PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("ignore_previous", re.compile(r"ignore (?:all )?previous instructions", re.I), "high"),
    ("reveal_system",   re.compile(r"(?:reveal|show|print|dump) (?:your )?system prompt", re.I), "high"),
    ("exfiltrate",      re.compile(r"\bexfiltrate\b|\bsend (?:this|the) (?:secret|token|key)\b", re.I), "high"),
    ("disable_security",re.compile(r"disable (?:security|safety|filters|guardrails)", re.I), "high"),
    ("role_override",   re.compile(r"you (?:are|act) now (?:a|an) ", re.I), "medium"),
    ("prompt_leak",     re.compile(r"(?:system prompt|hidden instructions|internal instructions)", re.I), "medium"),
    ("data_url",        re.compile(r"https?://[^\s]{50,}", re.I), "low"),
]

SUSPICIOUS_BLOB = re.compile(r"[A-Za-z0-9+/]{120,}={0,2}")


@dataclass
class Detection:
    is_suspicious: bool
    severity: str
    reasons: list[str]
    has_blob: bool


def detect(text: str) -> Detection:
    reasons: list[str] = []
    severity_rank = {"low": 1, "medium": 2, "high": 3}
    top = "low"
    for name, pat, sev in PATTERNS:
        if pat.search(text):
            reasons.append(name)
            if severity_rank[sev] > severity_rank[top]:
                top = sev

    has_blob = False
    for match in SUSPICIOUS_BLOB.findall(text):
        try:
            base64.b64decode(match, validate=True)
            has_blob = True
            reasons.append("base64_blob")
            top = "high"
            break
        except Exception:
            continue

    return Detection(
        is_suspicious=bool(reasons),
        severity=top,
        reasons=reasons,
        has_blob=has_blob,
    )


def looks_suspicious_for_corpus(text: str) -> bool:
    """Convenience: treat anything with a `high`-severity match as suspicious."""
    d = detect(text)
    return d.is_suspicious and d.severity in ("high", "medium")
