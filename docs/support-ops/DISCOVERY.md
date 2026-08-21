# Support Operations — Discovery & Architecture

> Forward-deployed engagement artifact. This document records the discovery →
> architecture phase: the business problem, the existing workflow and its
> bottleneck, the proposed AI workflow, system boundaries, integration points,
> risk model, and success metrics.

## Honest framing

There are no external users or customers. Agent Gateway is a
**production-oriented enterprise deployment prototype / reference
implementation**. The "enterprise systems" it integrates with (ticketing,
observability, deployment, GitHub, Slack) are **deterministic mock adapters
behind clean Protocol interfaces** — swappable for real integrations without
touching the agent, tools, or gateway.

## Business problem

Support operations teams drown in tickets that follow a small number of
repeating patterns: a service degrades with a known failure signature, a bad
deploy regresses latency, a customer asks for something policy forbids.
Human triage of these tickets is slow; meanwhile production incidents burn
revenue. Teams want automation, but unrestricted automation in production is
unacceptable: one wrong action (deleting data, rolling back the wrong thing)
costs more than the toil it saves.

## Existing (manual) workflow

```
Ticket arrives (queue unwatched at night)
  → human triages severity/category          [minutes–hours]
  → engineer greps runbooks / incident history  [minutes]
  → engineer checks dashboards               [minutes]
  → diagnosis by memory or tribal knowledge  [variable]
  → change request / approval meeting        [hours]
  → remediation executed manually            [minutes]
  → verification often skipped ("it looks fine now")
  → audit trail: whatever someone remembered to write down
```

## Bottleneck

The bottleneck is not any single step — it is that every step requires a
human to move the ticket forward, while the *guardrails* exist only as
documentation and tribal memory. Low-risk actions wait behind high-risk
process; prohibited actions are prevented only by people remembering the
rules.

## Proposed AI workflow

```
Support Ticket
      ↓
Triage Agent (severity / category)
      ↓
Context / Knowledge Retrieval (ACL-filtered RAG over runbooks + incident history)
      ↓
Diagnosis (live observability signals)
      ↓
Policy / Risk Evaluation (gateway-enforced risk tiers)
      ↓
 ┌────┴─────────────┐
 │                  │
Auto Action      Approval (human decides; policy re-checked)
 │                  │
 └───────┬──────────┘
         ↓
     Remediation
         ↓
     Verification (post-condition gate)
         ↓
   Audit / Trace (every decision, action, and evidence item)
```

The agent moves tickets through the same pipeline humans do — but the
*gateway*, not the model, decides what the agent may execute.

## System boundaries

| Boundary | Interface | Prototype implementation |
|---|---|---|
| Ticketing system | `TicketingAdapter` | DB-backed mock (`support_tickets` / `ticket_events`) |
| Monitoring / observability | `ObservabilityAdapter` | Deterministic state machine (`app/integrations/observability.py`) |
| Deployment system | `DeploymentAdapter` | Mock with real post-conditions (`deployment.py`) |
| GitHub | `GitHubAdapter` | Deterministic issue tracker mock |
| Slack | `SlackAdapter` | Deterministic message log mock |
| Knowledge base | RAG (`search_knowledge`) | Existing pgvector retrieval, new `support_kb` ACL tag |
| LLM | provider chain (`oxalpha` → fallbacks) | OpenRouter-hosted ox-alpha; failover to other configured providers |

Each adapter is a `Protocol` in `apps/api/app/integrations/`. Real
integrations replace the mocks at the boundary; nothing above the boundary
changes.

## Integration points

- **Ingestion:** `POST /v1/support/tickets` creates tickets;
  `POST /v1/support/tickets/{id}/run` starts the pipeline.
- **Human control:** `GET /v1/approvals`, `POST /v1/approvals/{id}/approve|reject`.
- **Audit:** every tool call lands in `tool_calls`, every run in
  `agent_traces`, security-relevant events in `security_events`, remediation
  evidence in `remediation_actions`, ticket history in `ticket_events`.

## Risk model

Every tool carries a gateway-enforced tier (`ToolSchema.risk_tier`):

| Tier | Semantics | Examples |
|---|---|---|
| `auto` | Executes within argument constraints; fully audited | restart_service, notify_slack, create_github_issue, read/diagnostic tools |
| `approval_required` | Agent may propose only; human approves; policy re-evaluated before execution | scale_service, rollback_deployment |
| `prohibited` | Denied unconditionally — no role, ticket, or approval can authorize it | delete_production_data |

Authorization is independent of tier: an employee cannot restart production
even though `restart_service` is auto-tiered for managers.

## Success metrics

Measured by the deterministic evaluation suite (`docs/support-ops/EVAL_RESULTS.md`):

1. Correct triage / retrieval / diagnosis / tool selection (functional).
2. Auto-remediation succeeds **only** when post-condition verification passes.
3. Approval-required actions are never executed without a human decision.
4. Prohibited actions are blocked for every role, including via crafted approvals.
5. Injection attempts through tickets or retrieved content never produce unsafe actions.
6. Adapter failures degrade gracefully (structured errors, escalation, no destructive fallback).
7. Every scenario produces a complete audit trail.
