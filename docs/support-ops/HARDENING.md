# Support Operations — Production Hardening

> Evidence that the deployment is hardened: authentication, authorization,
> failure handling, retries/timeouts, auditability, observability, guardrails,
> human approval, verification, and deterministic behavior. Each section maps
> to code and to evaluation scenarios.

## The control model

Every action — whether proposed by the LLM, requested by a user, or revived
by an approval — passes through the same chain, enforced in the gateway:

```
Identity → Authorization → Validation → Policy/Risk → Approval → Execution → Verification → Audit
```

**Policy enforcement occurs in the gateway/executor layer and cannot be
bypassed by the LLM, the system prompt, the caller's role, or the approval
flow.** The model's output is treated as a *proposal*, never as permission.

## Identity & authentication

- Every request carries a Supabase JWT verified server-side (ES256/RS256 via
  project JWKS; HS256 legacy fallback) — `app/auth.py`.
- Tenant and role are derived from `tenant_memberships` in the database;
  client-supplied tenant/role flags are never trusted.
- Rate limits per token (`ratelimit.py`) on chat and pipeline endpoints.

## Authorization (independent of risk tier)

- Role rank check per tool (`required_role`), plus scope rules and manager
  scope checks — `tools/policy.py`.
- Evaluated *before* tier logic for normal tools, but **after** the
  prohibited gate: no role unlocks a prohibited tool.
- Evidence: evals `role_authorization_enforced` (employee denied restart),
  `prohibited_blocked_for_admin` (admin denied deletion).

## Argument validation (before any adapter is touched)

- Required-argument checks against the tool schema.
- Declared constraints enforced by the policy engine: enum membership
  (service allowlist, environment whitelist), numeric bounds
  (replicas 2–12), string patterns (version format), length caps.
- Malformed or malicious arguments die in the gateway; adapters re-check
  defensively as a second layer.
- Evidence: eval `invalid_arguments_rejected` (`service="*"` rejected, state
  unchanged).

## Guardrails: risk tiers

| Tier | Enforcement |
|---|---|
| `auto` | Executes within constraints; every call audited |
| `approval_required` | Orchestrator creates an approval record instead of executing; the LLM receives "pending_approval" |
| `prohibited` | Denied unconditionally before authorization is even considered; high-severity security event |

The tiers live on `ToolSchema.risk_tier` — configuration, not prompts.

## Human approval (that cannot bypass policy)

- Approval records capture tool, arguments, requester, trace, and ticket
  context (`action_approvals`).
- On approve, the gateway **re-runs the full policy check with the original
  requester's context** before executing. If anything changed — role,
  quota, arguments — or if the tool is prohibited, the approval is rejected
  with the policy reason.
- Clients can read approvals but never mutate them directly (RLS: select-only);
  decisions flow only through the authenticated API.
- Evidence: eval `approval_cannot_bypass_policy` (crafted approval row for a
  prohibited tool is blocked at approve time).

## Failure handling, retries, timeouts

- Tool execution is wrapped in an `{ok, data, error}` envelope — adapter
  exceptions become structured errors the agent can reason about, never 500s.
- LLM calls carry configurable timeouts (`OAI_TIMEOUT_S`); provider failover
  chain degrades gracefully when ox-alpha is unavailable (trial expiry,
  4xx/5xx, timeout), recording each skip on the trace.
- Audit writes are best-effort by design: logging failures never break the
  request path.
- Evidence: evals `adapter_failure_recovery`, provider-failover unit tests.

## Verification gate

A remediation is not successful until verification confirms the expected
post-condition:

- Mutating adapters return a `verification` block with their own
  post-condition check (`post_condition_met`).
- `remediation_actions.outcome` is `executed` only when the post-condition
  holds; otherwise `verification_failed`.
- The runbook and system prompt require `verify_service_health` after any
  remediation; the eval proves the failure path leaves the ticket unresolved.
- Evidence: evals `low_risk_auto_remediation_verified`,
  `verification_gate_enforced`.

## Auditability & observability

- `agent_traces`: retrieval chunk ids + safety status, input safety, model +
  provider actually used, loop count, latency, final status, error/failover
  notes.
- `tool_calls`: every call — allowed, denied, pending_approval, error — with
  arguments, results, policy decision/reason, risk tier, latency.
- `security_events`: suspicious prompts/chunks, policy denials, prohibited
  attempts, approval requests/blocks, provider failovers.
- `ticket_events` + `remediation_actions`: human-readable timeline and
  machine-readable evidence per ticket.
- Admin API + web audit dashboard expose all of the above, tenant-scoped.

## Untrusted-content defenses (prompt injection)

1. Ticket bodies and retrieved chunks are wrapped in
   `UNTRUSTED_DOCUMENT_BLOCK`; system prompts treat them as data.
2. Pattern-based injection detector runs on user input (high severity ⇒
   refusal before the LLM runs) and on every retrieved chunk (flagged,
   security event).
3. ACL-filtered retrieval keeps restricted content out of the prompt entirely.
4. Even a successful manipulation cannot produce an unsafe action: the
   gateway re-derives every decision from the DB.
- Evidence: evals `prompt_injection_via_ticket_blocked`,
  `kb_injection_flagged`.

## Deterministic behavior where it matters

- Governance is deterministic: same inputs to the policy engine always yield
  the same decision, regardless of model output.
- Mock adapters are deterministic state machines; the evaluation suite runs
  offline with zero API keys and produces reproducible results
  (`EVAL_RESULTS.md`).
- Provider selection and failover order are explicit configuration.

## Known limitations (honesty section)

- Adapters are mocks; real integrations must add their own retry/backoff and
  credential management.
- Injection detection is pattern-based; production would layer semantic
  detection.
- Approvals do not expire; a TTL sweep is straightforward follow-up work.
