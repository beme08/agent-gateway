# Supabase setup (5 minutes)

There is no Supabase MCP available in this Codex environment, so this is the manual path. It is short.

## 1. Create a project

Go to https://supabase.com/dashboard and click **New project**. Pick any name, a region near you, and a strong database password. Free tier is fine. Wait ~1 minute for it to provision.

## 2. Copy your credentials

In the project dashboard, go to **Settings → API**:

- **Project URL** — looks like `https://abcdefg.supabase.co`
- **anon public key** — JWT starting with `eyJ...`
- **service_role key** — JWT starting with `eyJ...` (server-side only; never expose to the browser)
- **JWT Secret** — under **Settings → API → JWT Settings**

## 3. Run the bootstrap script

From the repo root:

```bash
bash scripts/supabase-bootstrap.sh
```

It will prompt for the four values, write:
- `apps/web/.env.local`
- `apps/api/.env`
- `scripts/.env`

All with the right keys. (Or pass them as flags — see the script header.)

## 4. Run the migrations

In the Supabase dashboard, open **SQL Editor → New query** and run each file in this exact order. Open each, copy, paste, run:

1. `supabase/migrations/0001_init.sql`
2. `supabase/migrations/0002_rls.sql`
3. `supabase/migrations/0003_leave_functions.sql`
4. `supabase/migrations/0004_match_chunks.sql`
5. `supabase/migrations/0005_demo_reset.sql`
6. `supabase/seed/seed.sql`

You should see "Success. No rows returned" for each.

## 5. Seed demo users

```bash
cd scripts
npm install
npx tsx create_demo_users.ts
```

This creates 10 auth users (5 per tenant), mirrors them into `public.users`, sets up `tenant_memberships` with `manager_user_id` links, and seeds `leave_balances` for the current year. It prints the credentials table to stdout and writes `docs/demo_credentials.md`.

## 6. Start the dev servers

In one terminal:
```bash
bash scripts/dev.sh
```
Web on http://localhost:3000.

In another terminal:
```bash
bash scripts/dev-api.sh
```
API on http://localhost:8000.

## 7. Walk the demo

Open http://localhost:3000. Click **Try as Employee**. You should land on the leave page. Go to the chat, ask "I'm sick today, can you request sick leave for me?" — the agent will retrieve the sick-leave policy, check your balance, and create a `pending` request. Sign out, **Try as Manager**, approve the request. Sign out, **Try as Admin**, open the audit trace.

## Troubleshooting

- **`Invalid API key`** — the anon or service-role key was copied wrong. Re-copy from Settings → API.
- **`permission denied for table tenants`** — RLS is enabled but you're using the anon key from a server context. Use the service-role key for the API.
- **`relation "agents" does not exist`** — migrations ran out of order. Drop the schema and re-run them in the order above.
- **Demo users can't sign in** — `create_demo_users.ts` errors. Run it with `npx tsx create_demo_users.ts` and read the error.
