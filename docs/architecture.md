# Architecture

## System diagram

```mermaid
flowchart TB
  Visitor[Public visitor] --> Landing[Landing page<br/>Try as… buttons]
  Landing -->|signInAsDemoUser| SupabaseAuth[Supabase Auth]
  Landing --> Waitlist[waitlist_signups table]

  Browser[Authenticated browser] --> Web[Next.js on Vercel]
  Web -->|server actions| Postgres[(Supabase Postgres + pgvector<br/>RLS-enforced)]
  Web -->|/api/agent/chat| API[FastAPI on Render/Fly.io]

  API --> CohereEmbed[Cohere embed-english-v3.0]
  API --> CohereChat[Cohere command-r-plus]
  API --> ToolGateway[Tool Gateway<br/>Registry + PolicyEngine + Executor + Audit]
  API --> Injection[Prompt-Injection Detector]
  API --> Quota[Quota / rate-limit helper]
  ToolGateway --> LeaveService[LeaveService]
  LeaveService --> Postgres
  Injection --> SecurityEvents[(security_events)]
  ToolGateway --> ToolCalls[(tool_calls)]
  API --> AgentTraces[(agent_traces)]
  API --> AuditLogs[(audit_logs)]

  Cron[GitHub Actions cron<br/>nightly] -->|reset_demo_tenant| Postgres
```

## Agent flow (one request)

```
User message
  ↓
Authenticated session (Supabase JWT verified server-side)
  ↓
Agent orchestrator (FastAPI)
  ↓
Prompt-injection detector on user input  →  security_events on block
  ↓
Embed query (Cohere) → match_document_chunks(filter_tenant, filter_tags=accessible_tags(role))
  ↓
Prompt-injection detector on retrieved text  →  mark suspicious chunks
  ↓
Build prompt with UNTRUSTED_DOCUMENT_BLOCK fence (retrieved text is data, not instructions)
  ↓
Cohere command-r-plus proposes tool call(s)
  ↓
Tool Gateway validates (auth, tenant, role, agent perms, schema, rate limit)
  ↓
Tool executes through shared LeaveService / RAG function (Postgres)
  ↓
tool_calls row written (allow or deny), audit_logs row written for sensitive actions
  ↓
Model receives structured {ok, data, error} result
  ↓
agent_traces row written (retrieval, tool calls, blocked events, latencies, tokens)
  ↓
Final answer streamed to browser
```

## Defense-in-depth (prompt injection)

1. Retrieved text wrapped in `UNTRUSTED_DOCUMENT_BLOCK`; system prompt treats it as data, not commands.
2. ACL-filtered retrieval — restricted tags never enter the prompt.
3. Suspicious-pattern detector on user input and retrieved chunks.
4. All tool inputs Pydantic-validated.
5. All tool calls server-authorized by tenant/role/scope.
6. Sensitive actions logged to `audit_logs` + `security_events`.
7. Model output is never trusted as authorization — every decision is re-derived from the DB.

## Two-tier approval (kept separate)

- **Tool-execution authorization** (always enforced server-side by the gateway).
- **Business workflow approval** (manager approves a `pending` leave request).

`create_time_off_request` is workflow-pending, not tool-blocked. The `dangerous` tool flag is superseded by explicit risk tiers (below).

## Support Operations environment (second deployment)

The same gateway serves a second operational environment. Differences are
configuration, not architecture:

```mermaid
flowchart TB
  T[Support Ticket] -->|POST /v1/support/tickets/{id}/run| Orch[Same orchestrator]
  Orch --> Inj2[Prompt-injection detector on ticket body]
  Orch --> RAG2[support_kb ACL-filtered retrieval]
  Orch --> LLM[ox-alpha via OpenRouter<br/>provider chain + failover]
  LLM --> GW[Tool Gateway: policy + risk tiers + constraints]
  GW -->|auto| Act[restart_service / notify_slack / github_issue]
  GW -->|approval_required| App[action_approvals → human → policy re-check → execute]
  GW -->|prohibited| Deny[denied unconditionally + security_event]
  Act --> Ver[verify_service_health post-condition gate]
  Ver --> Rem[(remediation_actions)]
  App --> Adapters[Mock adapters: ticketing / observability / deployment / github / slack]
```

Control model for every action:
`identity → authorization → prohibited gate → argument validation → risk policy → approval if required → execution → verification → audit`.

Details: [`docs/support-ops/`](support-ops/DISCOVERY.md).
