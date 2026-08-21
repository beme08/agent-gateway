# agent-gateway API — Deploy Runbook (Render)

Why this exists: the web tier is live on Vercel, but the agent chat 502s because
`AGENT_API_URL` points to a placeholder. Deploying this FastAPI service is the
only missing piece to make the full demo — and the interview story — real.

## Prerequisites (5 min)

1. **Supabase project keys** — from the dashboard at
   `https://supabase.com/dashboard/project/dabksbszhwqnpglattvb/settings/api`
   - Project URL: `https://dabksbszhwqnpglattvb.supabase.co`
   - `SUPABASE_ANON_KEY` (anon public)
   - `SUPABASE_SERVICE_ROLE_KEY` (service_role)
   - `SUPABASE_JWT_SECRET` (Settings → API → JWT Settings)
   > The service-role key currently in `~/.env.local` belongs to a *different*
   > Supabase project — it returns "Invalid API key" against this project.

2. **Render account** — create at render.com (free tier is enough), then
   authorize GitHub access. No CLI needed — everything below is dashboard-only.

3. **Vercel access** — you'll update one env var in the dashboard and redeploy.

## Deploy the API on Render (one-time, ~10 min)

1. Render dashboard → **New** → **Web Service**.
2. **Connect a repository** → pick `beme08/agent-gateway` (authorize the repo).
3. Set the service values:
   - **Name**: `agent-gateway-api`
   - **Root directory**: `apps/api`
   - **Environment**: `Docker` (Render reads `Dockerfile`)
   - **Region**: any (free tier is single-region; `frankfurt` is fine)
   - **Branch**: `main`
4. **Environment variables** — add each:
   | Key | Value |
   |---|---|
   | `SUPABASE_URL` | `https://dabksbszhwqnpglattvb.supabase.co` |
   | `SUPABASE_ANON_KEY` | anon key from dashboard |
   | `SUPABASE_SERVICE_ROLE_KEY` | service_role key from dashboard |
   | `SUPABASE_JWT_SECRET` | JWT secret from dashboard |
   | `AGENT_API_KEY` | any random string (e.g. `openssl rand -hex 16`) |
   | `COHERE_API_KEY` | optional — omit to use the built-in mock |
   | `ENABLE_PUBLIC_UPLOAD` | `false` |
5. **Deploy Web Service**. First boot may take ~10s while `seed_ingest`
   embeds the HR documents (non-fatal if it fails).
6. When healthy, note the public URL, e.g. `https://governor-chk2.onrender.com`.

> Note: `render.yaml` at the repo root is a Blueprint with the same settings —
> you can also deploy via **New → Blueprint** and it will fill most fields,
> prompting you for the secret values (`sync: false`).

## Verify the API

```bash
curl https://governor-chk2.onrender.com/healthz   # expect {"ok":true}
```

## Wire the web tier (Vercel dashboard)

1. Open the agent-gateway project in Vercel → **Settings → Environment Variables**.
2. Set `AGENT_API_URL` = `https://governor-chk2.onrender.com` (no trailing slash).
   If the deployed app uses `NEXT_PUBLIC_AGENT_API_URL`, set that too with the same value.
   `apps/web/lib/agent-client.ts` reads `NEXT_PUBLIC_AGENT_API_URL` first — for client-side
   code the value is baked in at build time, so set it and redeploy.
3. **Deployments → Redeploy** the latest production deployment.
4. Git author email must match a verified email on the Vercel account (Hobby plan) or
   GitHub auto-deploys stay blocked (`TEAM_ACCESS_REQUIRED`). Check with `git config user.email`.
## Full end-to-end verification (the interview demo)

1. `https://web-nine-roan-66.vercel.app`
2. Click **Try as Employee** → land on `/leave` as `employee@acme.test`
3. Open the agent chat, ask: *"I'm sick today, can you request sick leave for me?"*
4. Expect: cited sick-leave policy + a tool-call badge → pending leave request appears
5. Click **Try as Manager** → approve the request → balance updates + audit event
6. Click **Try as Admin** → audit dashboard → open the trace → see retrieval → tool calls → answer

## If demo users are missing (e.g. Supabase free-tier paused/reset)

```bash
cd ~/Desktop/agent-gateway/scripts
cp .env.example .env   # fill SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY
npm install
npx tsx create_demo_users.ts
```
Idempotent — safe to re-run.
