# Support Operations — Deployment Guide

> Demonstrates taking the same governed agent infrastructure from the HR
> environment into a second operational environment: configuration, tool
> registration, data/source configuration, policy configuration, agent
> behavior configuration, and the deployment process.

## Principle

The Support Operations environment is **configuration, not a new system**.
The orchestrator, tool gateway, policy engine, approval mechanism, RAG,
auth, audit, and observability are unchanged. What's new:

- 1 migration (`supabase/migrations/0010_support_ops.sql`)
- 1 seed file (`supabase/seed/support_ops_seed.sql`)
- 5 integration adapters (`apps/api/app/integrations/`)
- 12 tool definitions (`apps/api/app/agent/tools/support_tools.py`)
- risk-tier + argument-constraint fields on the existing registry/policy engine
- 3 web pages + 2 client/action modules

## 1. Database migration

```bash
supabase db push          # applies 0009 (provider routing) + 0010 (support ops)
psql "$DATABASE_URL" -f supabase/seed/support_ops_seed.sql
```

Migration 0010 creates `support_tickets`, `ticket_events`, `action_approvals`,
`remediation_actions` — all tenant-scoped with RLS identical to the HR tables —
and extends the ACL model with the `support_kb` tag (employee and above).

## 2. Tool registration

Tools are declared in `support_tools.py` and registered into the **shared**
registry in `definitions.py::build_registry()`. One gateway serves both
environments; each agent sees only its `allowed_tools`.

Registration = declaring a `ToolSchema` (name, description, required_role,
parameters, **risk_tier**, **constraints**) plus an async handler. Example:

```python
restart_service_schema = ToolSchema(
    name="restart_service",
    description="Restart a service instance ...",
    required_role="manager",
    parameters={...},
    constraints={
        "service": {"enum": ["checkout-api", "payments-api", ...]},
        "environment": {"enum": ["staging", "production"]},
    },
    risk_tier="auto",
)
```

## 3. Data / source configuration

- Knowledge base: runbooks, incident history, and the automation policy are
  seeded as documents tagged `support_kb`; embeddings are generated at API
  boot by the existing `seed_ingest` worker.
- Integrations: adapters initialize deterministically (`reset_support_world()`).
  Replacing a mock with a real client means implementing the Protocol and
  swapping the accessor in `app/integrations/__init__.py`.

## 4. Policy configuration

Policy is data on the tool schema, enforced by the shared engine
(`tools/policy.py`) in a fixed order:

```
identity → authorization → prohibited gate → scope rules →
argument validation (required/enum/bounds/pattern) → quota →
[approval if required] → execution → verification
```

To change the risk posture of an environment, edit the tier or constraints on
a schema — no engine changes.

## 5. Agent behavior configuration

The Support Ops agent is a row in `agents` (seeded):

- `system_prompt`: workflow + security rules (untrusted ticket bodies,
  tier discipline, verification requirement)
- `allowed_tools`: the 12 support tools — including `delete_production_data`,
  which the agent can *see* but the gateway will never execute
- `provider`: `oxalpha` (per-agent LLM routing; HR agents keep their default)

## 6. LLM provider configuration

Provider chain: `oxalpha → openai_compat → cohere → offline mock`. The
default is ox-alpha because it is currently the only model serving free on
this OpenRouter key (the shared free-tier bucket for other models is
exhausted → 403). Same gateway, same guardrails, same eval suite regardless
of which model answers.

```bash
# .env — current deployed default
LLM_PROVIDER=oxalpha
OPENROUTER_API_KEY=sk-or-...
OXALPHA_MODEL=stealth/ox-alpha
```

**Fast-path recipe (one-line change when quota headroom exists):** measured
against the real gateway payload, ox-alpha is ~15–26s per round trip from a
fast host (and ~82s from Render free-tier egress) while
`google/gemini-2.5-flash` answers in ~0.4s:

```bash
LLM_PROVIDER=openai_compat
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=google/gemini-2.5-flash
```

- `LLM_API_KEY` is optional: it falls back to `OPENROUTER_API_KEY`, so only
  `LLM_PROVIDER` + `LLM_MODEL` need editing when the fast bucket refills.
- FreeLLMAPI/cerebras: targeted but currently blocked (model not in the
  local catalog under the tested id; Cerebras blocks raw clients with
  Cloudflare 1010 — FreeLLMAPI's own adapter is the sanctioned path once a
  provider has headroom).
- Failover is automatic: if the primary errors (quota, 402, timeout), the
  request falls through the chain and the trace records which provider
  served it (`agent_traces.llm_provider`).
- Per-agent override: `agents.provider` / `agents.model` columns route a
  single agent without touching global config.

Same infrastructure as the HR environment:

## 7. Deployment process

| Component | Target | Notes |
|---|---|---|
| API | Render/Fly.io (Dockerfile) | env vars above |
| Web | Vercel | new `/support/*` routes ship with the app |
| DB | Supabase | migrations + seeds |

CI runs `pytest -q` (unit tests) and the deterministic evaluation suite
(`app/evals/`) on every PR — no API keys required.

## 8. Verification after deploy

```bash
curl -s $API/healthz
# run the pipeline on the seeded incident ticket (JWT of a manager)
curl -X POST "$API/v1/support/tickets/$TICKET_ID/run" -H "Authorization: Bearer $JWT"
# review what the agent wants to do that requires a human
curl "$API/v1/approvals?status=pending" -H "Authorization: Bearer $MANAGER_JWT"
```
