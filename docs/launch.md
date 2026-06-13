# Launch Strategy

## MVP launch mode: public demo, not real SaaS

The MVP is deployed publicly as a **live demo with seeded data**, not as a real public SaaS. It does not support unrestricted self-serve signup or real company data at first.

### Public demo includes

- Seeded **Acme Corp** and **Globex Corp** tenants (`tenants.plan = 'demo'`).
- **Demo role buttons on the public landing page** that sign visitors in as pre-seeded users:
  - "Try as Employee"
  - "Try as Manager"
  - "Try as Admin"
  - "Try as Viewer"
- Fake HR policies (remote work, sick leave, PTO, executive comp).
- Fake leave balances seeded for the current year.
- Fake sick leave / PTO workflows demonstrated end-to-end.
- **Resettable demo data** — nightly cron calls `reset_demo_tenant()` for both tenants; admin can trigger a manual reset from the audit page.
- **No arbitrary public document uploads in MVP** — documents are seed-script only; `ENABLE_PUBLIC_UPLOAD=false` by default.
- **Demo disclaimer banner** on every page: *"Demo environment — do not upload sensitive or real company data. Data is reset periodically."*
- **Optional waitlist CTA** ("Join the private beta") that writes to `waitlist_signups` with rate-limiting.
- Per-IP and per-tenant rate limits on `/api/agent/chat` and tool calls.

This keeps the project safe, cheap to run, and recruiter-friendly while still showing a deployed, production-style system.

## SaaS-ready architecture

`tenants` carries the columns needed for plans and limits:

- `plan text default 'demo'` — values: `demo` / `free` / `pro` / `enterprise`.
- `max_users int`, `max_documents int`, `max_agents int`, `max_messages_per_month int`, `max_storage_mb int`.

Per-tenant usage counters (also on `tenants`):

- `monthly_message_count int default 0`
- `monthly_tool_call_count int default 0`
- `document_count int default 0`
- `storage_used_mb int default 0`
- `agent_count int default 0`
- `usage_period_start timestamptz`

The ToolPolicyEngine and FastAPI request handlers are structured to consult these limits before executing. Flipping a tenant from `plan='demo'` to `plan='pro'` (with higher caps) requires no code change, only a data update. The `enforce_tenant_quota()` helper is scaffolded in the gateway so adding real enforcement in MVP 2 is a small change.

## Deferred SaaS features (do not build in MVP)

- Public self-serve signup
- Billing / Stripe
- SSO / SAML
- Real customer onboarding flows
- Public arbitrary file uploads
- Workspace deletion / export flows
- Full customer support / admin tooling
- Legal docs, privacy policy, terms of service beyond the demo disclaimer
