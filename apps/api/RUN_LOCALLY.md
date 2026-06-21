# Running the FastAPI gateway locally

The Python FastAPI side (`apps/api/`) is **not deployed** anywhere.
It is code-complete and intended to be run on a developer laptop for
local exploration and e2e tests. There is no public host for it yet.

## Prerequisites

- macOS or Linux
- Python 3.11+ (the repo's `apps/api/.venv` is Python 3.11.15)
- The existing venv at `apps/api/.venv` already has all dependencies
  installed (fastapi, uvicorn, supabase, cohere, pydantic, etc.). If
  it is missing, recreate it:
  ```bash
  cd apps/api
  python3.11 -m venv .venv
  .venv/bin/pip install -e ".[dev]"
  ```

## Start the server

From the repo root:

```bash
cd apps/api
./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

The server is now reachable at `http://localhost:8000`.

## Verify it works

```bash
curl http://localhost:8000/healthz
# → {"ok":true}

# Interactive API docs (Swagger UI):
open http://localhost:8000/docs

# OpenAPI spec:
curl http://localhost:8000/openapi.json
```

## What works without any env vars

- `GET /healthz`
- `GET /docs` (Swagger UI listing all 12 routes)
- `GET /openapi.json`

## What needs env vars

Authenticated and LLM-backed endpoints need real values. The defaults
in `app/config.py` are placeholders and will fail at request time.

Create `apps/api/.env` (gitignored) with:

```env
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=<anon>
SUPABASE_SERVICE_ROLE_KEY=<service-role>   # required for leave/audit/agent
SUPABASE_JWT_SECRET=<jwt-secret>           # for verifying Supabase auth tokens

AGENT_API_KEY=<random 32+ char string>      # HMAC for service-to-service calls
COHERE_API_KEY=<cohere-key>                 # for embeddings + chat
COHERE_MODEL=command-r-plus
COHERE_EMBED_MODEL=embed-english-v3.0
```

Restart uvicorn after editing `.env` (or use `--reload`).

## Pointing the web app at the local API

The Next.js web app reads `NEXT_PUBLIC_AGENT_API_URL` and falls back
to `http://localhost:8000` when unset. To make `npm run dev` in
`apps/web/` talk to your local FastAPI, just leave the env var unset.

For the **deployed** Vercel demo to talk to a real API, the API has
to be hosted somewhere publicly reachable (Fly.io, Render, etc.).
That is intentionally **not done yet** — there are no customers and
no public demo of the chat agent is offered today.

## Running the e2e scripts against local API

The Playwright scripts in `e2e/*.mjs` only touch the web app, not
FastAPI directly. The web app in turn talks to FastAPI when the
chat step runs. To exercise the full stack locally:

```bash
# Terminal 1 — API
cd apps/api && ./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Web
cd apps/web && npm run dev

# Terminal 3 — e2e (against the local web dev server)
E2E_URL=http://localhost:3000 node e2e/manager-approve.mjs
```

## When to host FastAPI publicly

Only when one of these becomes true:

- A real user (customer, demo partner, blog reader) needs to see the
  chat agent working end-to-end.
- CI needs to run the chat step of the e2e suite on every PR.
- A second engineer joins and needs a shared dev environment.

Until then, `localhost:8000` is the right answer.
