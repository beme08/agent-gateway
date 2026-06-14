# Live Public Demo

**Production URL**: https://agent-gateway-qdauk3e09-beme08s-projects.vercel.app

This is a deployed, public, recruiter-safe demo. No login is required to see the landing page or to try the waitlist. To walk the full HR workflow, click any **"Try as …"** button on the landing page — that signs you in as a seeded demo user and routes you to the right dashboard.

## What's live and verified

- ✅ **Public landing page** — Demo banner, four "Try as" role buttons, architecture highlights, waitlist form. Renders at the production URL above.
- ✅ **HR workflow UI** (employee → manager → admin) — fully working through the live Vercel deployment.
  - Try as Employee → see balances, request time off, see own requests
  - Try as Manager → see team's pending requests, approve/reject
  - Try as Admin → audit dashboard with tenant usage counters, traces, tool calls, security events
- ✅ **Database-backed state machine** — Manager "Approve" click in the live UI writes to the `leave_requests` table via the `approve_leave_request` Postgres function. Verified end-to-end on 2026-06-14.
- ✅ **Supabase RLS** — every tenant-scoped table has RLS enabled. Cross-tenant reads are blocked at the database level.
- ✅ **Waitlist API** — `POST /api/waitlist` writes to `waitlist_signups` table and returns `{"ok": true}`.
- ✅ **Screenshots** — `e2e/shots/01-landing.png`, `05-approvals.png`, `chat-01-employee-agent.png`, `07-audit.png` in the repo (after `npx playwright install chromium` then `node e2e/landing-and-roles.mjs`).

## What's not yet live

- 🟡 **Agent chat** — the chat UI loads, the demo question chips appear, but pressing Send returns an error because the FastAPI service is not deployed yet. See "Deployment status" below.

## How to walk the demo in 60 seconds

1. Open the [production URL](https://agent-gateway-qdauk3e09-beme08s-projects.vercel.app).
2. Click **"Try as Employee"**. You land on the leave page for `employee@acme.test` in Acme Corp.
3. (Optional) Request time off. Or skip — there's usually a pending request already from the seed.
4. From the same browser, click **"Try as Manager"**. You see the team queue with the pending request.
5. Click **Approve** on a row. The row disappears; the balance is updated server-side.
6. Click **"Try as Admin"**. You see the audit dashboard with the demo data reset button and tenant usage counters.

## Demo credentials

| Role | Email | Password |
|---|---|---|
| Admin | `admin@acme.test` | `demo1234` |
| Manager | `manager@acme.test` | `demo1234` |
| Employee | `employee@acme.test` | `demo1234` |
| Employee 2 | `employee2@acme.test` | `demo1234` |
| Viewer | `viewer@acme.test` | `demo1234` |

Same set with `@globex.test` for the second seeded tenant.

## Deployment status

| Tier | Host | Status |
|---|---|---|
| Web (Next.js 14) | Vercel — `beme08s-projects/agent-gateway` | ✅ Live, all 5 env vars set, production deployment is `5b9dfc2` |
| API (FastAPI) | Render or Fly.io | 🟡 Dockerfile is committed at `apps/api/Dockerfile`; deploy command documented in `docs/deployment.md` step 3. Needs the Supabase JWT secret pasted into Render env vars. |
| Database | Supabase (hosted) | ✅ 7 migrations applied, 10 demo users, 2 seeded tenants, full RLS |

The "Agent chat" UI works (renders, accepts input, shows demo questions) but the chat endpoint currently 502s because `AGENT_API_URL` on Vercel points to a placeholder. After the API is deployed, update the Vercel env var with the real URL.
