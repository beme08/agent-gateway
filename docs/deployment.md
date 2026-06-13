# Deployment

## Prerequisites

- A Supabase project (free tier is fine).
- A Vercel account.
- A Render or Fly.io account.
- (Optional) A Cohere API key. Without one, the API falls back to a deterministic local mock so the UI still works.

## 1. Supabase

1. Create a new project at https://supabase.com.
2. In the SQL editor, run each file in `supabase/migrations/` in order, then `supabase/seed/seed.sql`.
3. Copy the project URL, anon key, and service-role key from Settings → API.
4. Copy the JWT secret from Settings → API → JWT Settings.

## 2. Create demo users

```bash
cd scripts
cp .env.example .env   # fill in SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
npm install
npx tsx create_demo_users.ts
```

This writes `docs/demo_credentials.md` with the 10 demo users and seeds the leave balances for the current year.

## 3. Deploy the API (Render or Fly.io)

The Dockerfile in `apps/api/` builds and runs the FastAPI app. Recommended (Render):

1. New → Web Service → Connect repo.
2. Root directory: `apps/api`.
3. Environment: Docker.
4. Add env vars from `apps/api/.env.example`:
   - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
   - `COHERE_API_KEY` (optional)
   - `AGENT_API_KEY` (any random string)
5. Deploy. Note the public URL (e.g. `https://agent-gateway-api.onrender.com`).

On first boot, the API runs `seed_ingest.py` to embed the four HR documents with ACL tags. The first request can take ~10s while this runs.

## 4. Deploy the web (Vercel)

1. New Project → import the repo.
2. Root directory: leave at the repo root (Next.js 14 will detect `apps/web` via `vercel.json`).
3. Add env vars:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `AGENT_API_URL` (the Render URL from step 3, no trailing slash)
   - `ENABLE_PUBLIC_UPLOAD=false`
4. Deploy.

## 5. Optional: nightly reset

The `.github/workflows/reset-demo.yml` workflow calls `reset_demo_tenant()` for both seeded tenants once a day. Configure the secrets `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in your GitHub repo.

## Verifying the deployment

Visit the Vercel URL. You should see the public landing page with four "Try as…" buttons and the demo disclaimer. Click "Try as Employee" — you'll be signed in as `employee@acme.test` and routed to the leave page. From there, follow [`docs/demo.md`](docs/demo.md).
