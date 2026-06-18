# Contributing

Thanks for your interest in the Secure Enterprise Agent Gateway. This project is a public demo of a multi-tenant agentic AI platform with HR workflow automation, Supabase RLS, and a deployed landing page.

## Repo layout

```
.
├── apps/
│   ├── web/        Next.js 14 (App Router) — landing, auth, dashboard, leave, audit, chat
│   └── api/        FastAPI Python 3.11+ — agent orchestrator, RAG, tool gateway
├── supabase/       SQL migrations + RLS + seed data
├── scripts/        Demo user creation, remote seed, demo reset
├── docs/           Architecture, demo guide, launch strategy, live demo
├── e2e/            Playwright-style walkthroughs
└── .github/        CI workflow (api tests + web build) + nightly demo reset
```

## Local setup

1. **Clone the repo** and `cd` into it.
2. **Create a Supabase project** at [supabase.com](https://supabase.com) (free tier is fine).
3. From the Supabase dashboard, copy your project URL and keys into the env files:
   - `apps/web/.env.local`
   - `apps/api/.env`
   - `scripts/.env`
4. **Run the migrations** in the Supabase SQL editor in this order:
   - `supabase/migrations/0001_init.sql`
   - `supabase/migrations/0002_rls.sql`
   - `supabase/migrations/0003_leave_functions.sql`
   - `supabase/migrations/0004_match_chunks.sql`
   - `supabase/migrations/0005_demo_reset.sql`
   - `supabase/migrations/0006_leave_manager.sql`
   - `supabase/migrations/0007_more_leave_types.sql`
5. **Run the seed**:
   ```bash
   cd scripts && npm install && npx tsx create_demo_users.ts
   ```
6. **Start the API** (terminal 1):
   ```bash
   cd apps/api && uvicorn app.main:app --reload --port 8000
   ```
7. **Start the web** (terminal 2):
   ```bash
   cd apps/web && npm run dev
   ```
8. Open [http://localhost:3000](http://localhost:3000) and click "Try as Employee" to walk the demo.

## Tests

```bash
# API tests (36 unit tests)
cd apps/api && pytest -q

# Web build
cd apps/web && npm run build

# E2E walkthroughs (requires Playwright + the live URL)
E2E_URL=https://agent-gateway-reqonacjn-beme08s-projects.vercel.app \
  node e2e/landing-and-roles.mjs
E2E_URL=https://agent-gateway-reqonacjn-beme08s-projects.vercel.app \
  node e2e/manager-approve.mjs
```

## PR conventions

- One feature or fix per PR
- Branch from `main` (or `codex/mvp` if working on a long-running feature branch)
- Commit messages in the imperative mood ("Add X", "Fix Y", "Refactor Z")
- Run `pytest` and `npm run build` locally before pushing
- Don't commit secrets. Use `.env.local` (gitignored). The pre-commit hook in `.githooks/` catches common mistakes.
- Don't commit `node_modules/`, `.next/`, `.venv/`, `*.egg-info/`, or any tracked `.env` file. The `.gitignore` covers all of these.

## Adding a new demo user

Edit `scripts/create_demo_users.ts`, add the user to the `USERS` array, then re-run `npx tsx create_demo_users.ts`. The seed script is idempotent — it upserts.

## Code style

- **TypeScript / React**: the web tier uses Next.js 14 App Router, no client-side state library (just `useState`). New components should follow the Intercom design system documented in `DESIGN.md` at the repo root.
- **Python**: the API uses FastAPI, Pydantic v2, and Supabase's Python client. Type hints required. Tests live in `apps/api/app/tests/`.
- **SQL**: migrations are one .sql file per change, named `NNNN_description.sql`. Migrations are append-only — never edit a committed migration.

## Questions?

Open a GitHub issue. For security issues, see `SECURITY.md`.
