# Agent Gateway — Interview Deep-Dive (whiteboard story from the real code)

> **Purpose**: interview-preparation / engineering notes for the Genpact/XponentL
> AIOps role. This is **not** authoritative product architecture documentation.
> It is a reasoning map so you can whiteboard the system from memory, speak to
> the code precisely, and tell an honest story about your own critical review.
>
> Every claim below is verifiable in the repo. Code refs are `path:line`.

---

## 0. One-line elevator pitch

> "A multi-tenant agentic platform that answers HR policy questions with
> ACL-filtered RAG and executes role-gated time-off workflows — every decision
> (retrieval, tool call, denial, security event) is traced and auditable."

---

## 1. Whiteboard (draw this from memory)

```text
Browser (Next.js / Vercel)
   │  Supabase JWT in Authorization header
   ▼
FastAPI  /v1/agent/chat                          admin: /v1/audit/traces…
   │
   ├─auth.get_caller()    verify JWT (JWKS ES256 + HS256 fallback),
   │                      derive role from tenant_memberships (never trust client)
   │  + rate limit
   ▼
Agent orchestrator (run loop, max 5 turns)      apps/api/app/agent/orchestrator.py:87
   │
   ├─ 1. prompt-injection scan on user input  → security_events if high → refuse
   ├─ 2. embed query → pgvector RPC match_document_chunks(tenant, role-tags)   [ACL at DB]
   ├─ 3. scan retrieved chunks → flag suspicious → log security_event
   ├─ 4. build prompt: SYSTEM_PROMPT + <UNTRUSTED_DOCUMENT_BLOCK>retrieved chunks</block>
   ├─ 5. cohere.chat(tools=only agent's allowed tools)
   └─ 6. for each tool_calls → policy.check() → executor.execute() → tool_results
             │      (allow/deny recorded to tool_calls table + latency)
             └─ loop: echo chat_history + tool_results back to Cohere
   │
   └─ persist agent_traces (retrieval status, safety, latency, tool_loop_count)
                     ↓
Supabase Postgres: pgvector chunks, RLS, leave service (single mutation path),
                  agent_traces, tool_calls, security_events, audit_logs
```

**60-second script to say while drawing:**

1. Start at the browser: every request carries a Supabase JWT. We never trust
   client-supplied tenant/role — `get_caller` verifies the token server-side and
   looks up the membership to derive the role (`auth.py:109`).
2. The orchestrator runs the agent loop (`orchestrator.py:87`): scan user input
   for injection → retrieve with ACL filtering at the DB layer → scan retrieved
   text → wrap it in an `UNTRUSTED_DOCUMENT_BLOCK` so it's data, not
   instructions → call Cohere with only the tools that *agent row* allows.
3. When the model returns tool calls, each one goes through the policy engine
   before execution: role rank, scope rules, argument validation, tenant quota
   (`policy.py:50`). Every decision — allow or deny — is written to `tool_calls`
   with latency and reason.
4. Tool results go back to the model as `tool_results`, and the loop repeats up
   to 5 turns. The whole request — retrieval safety status, latencies, tool
   loop count — lands in `agent_traces`, which admins can replay.
5. The point: it's an *execution* system, not a chatbot. The model proposes,
   the gateway disposes, and everything is observable.

---

## 2. What makes it an "agent" and not an LLM wrapper

- **Tools + loop**: the model chooses and calls functions (`search_documents`,
  `get_leave_balance`, `create_time_off_request`, approvals…) and iterates on
  results up to 5 turns (`orchestrator.py:182`).
- **State**: `agent_messages`, `session_id`, and per-turn `chat_history`
  carried through the loop.
- **The control layer is the hard part, not the model**: tool registry
  (`tools/registry.py`), policy gate (`tools/policy.py`), executor envelope
  (`tools/executor.py`). The model is a proposer; authorization is always
  re-derived from the DB.
- **Deliberately bounded autonomy**: 5-turn cap, server-side approval for
  `dangerous` tools (scaffolded for `send_email` / `run_sql`), business-workflow
  approval via a manager (two-tier approval kept separate).

---

## 3. One request, end to end (with code refs)

| Step | Where |
|---|---|
| JWT verified, role derived from membership | `apps/api/app/auth.py:109` |
| Injection scan on user input; high-sev → refuse | `orchestrator.py:99-104`, `:152-158` |
| Trace row created up front (`final_status=running`) | `orchestrator.py:120-133` |
| ACL-filtered retrieval (role tags → pgvector RPC) | `rag/retrieve.py:21` + `0008_fix_acl_semantics.sql` |
| Injection scan on retrieved chunks | `orchestrator.py:139-149` |
| Prompt = system + `<UNTRUSTED_DOCUMENT_BLOCK>` | `orchestrator.py:164-170` |
| Cohere call with only the agent's allowed tools | `llm/cohere.py:77` |
| Policy gate per tool call (allow/deny + audit) | `tools/policy.py:50` |
| Executor returns `{ok, data, error, latency_ms}` | `tools/executor.py:11` |
| Tool results fed back as `tool_results` + echoed `chat_history` | `llm/cohere.py:129` |
| Persist assistant msg, finish trace | `orchestrator.py:236-243` |

---

## 4. The two things I found wrong in my own system

These are your strongest "show me something you discovered was wrong" answers.
They're now **fixed in the repo with regression tests** — say exactly that.

### 4a. The tool-loop bug (correctness)

- **What I found**: the orchestrator appended tool results to the message
  history, but the Cohere client sent only the *last user message* to the API
  (`llm/cohere.py`, old `_cohere_format`). Tool results never reached the model,
  so the agent could not actually iterate on tool output — the loop was
  effectively broken on the real-model path (only the keyword-based mock
  "worked", and it was heuristic).
- **Why it was a bug, not a nit**: an agent that can't see tool results will
  re-call tools or loop pointlessly, burn tokens, and produce answers grounded
  in nothing. It defeats the purpose of the architecture diagram.
- **The fix**: implemented the Cohere v1 multi-step contract — first turn sends
  `preamble` (system) + `message` (user) + `tools`; subsequent turns echo the
  API's `chat_history` and carry `tool_results` with `message=""` per the docs
  (`llm/cohere.py:77`, `:129`).
- **Regression test**: `app/tests/test_cohere_tool_loop.py` locks the request
  body for both turns.

### 4b. The ACL overlap leak (security)

- **What I found**: the pgvector match function used `acl_tags && filter_tags`
  — array **overlap**. A chunk tagged `{hr_policy, executive}` matched an
  employee whose grant was `{public, hr_policy}` because one tag overlapped →
  **executive content leaked to employees** (and any mixed-tag chunk leaks to
  the least-privileged matching role).
- **Why it's the real vulnerability in most RAG systems**: vector search is
  usually *not* a security boundary. Even if you filter later, an overlapping
  grant puts restricted text into the prompt where the model may echo it.
- **The fix**: containment semantics — a chunk is returned only when **every**
  tag it carries is within the caller's grant (`acl_tags <@ filter_tags`), plus
  a cardinality guard so untagged chunks can't implicitly be "public"
  (`supabase/migrations/0008_fix_acl_semantics.sql`). I also normalized the
  seed data, because the old redundant `{public, hr_policy}` tagging was only
  harmless *because* of the overlap bug (`seed_ingest.py:16`).
- **Regression test**: `app/tests/test_acl_semantics.py` (semantics + a
  migration-contract check so the SQL file itself can't drift back to `&&`).

**Bonus discovery** (also fixed): the prompt-injection detector missed padded
base64 blobs (`...AAA==`) because `b64decode(validate=True)` rejects a block
whose total length isn't a multiple of 4 — an evadable security detector. Fixed
by stripping padding before validation (`security/prompt_injection.py:27-63`);
the pre-existing failing test now passes.

**Framing**: *"I built a security-conscious agent gateway, instrumented it
heavily, then audited it critically enough to find where the implementation
didn't yet match the intended architecture — fixed the two correctness/security
ones, and documented the rest honestly as production hardening."*

---

## 5. The 502 incident (honest, still-open framing)

- Reality at interview time: web tier **200**, API **not deployed**
  (`agent-gateway-api.onrender.com/healthz` → 404 — NOTE: that hostname is NOT our service; the real API is governor-chk2.onrender.com). PREP_PACK's runbook exists,
  deployment is blocked on Supabase keys for the right project + Vercel re-auth.
- **Tell it as a diagnosis story, not a victory**:

> "The chat path 502'd though the landing page was healthy. I treated it as a
> boundary problem first: is it auth, the model, or the API itself? Tracing
> showed the frontend was pointing `AGENT_API_URL` at a placeholder — the
> FastAPI service was never actually deployed. That's a deployment topology
> mistake, not a code bug. I wrote the runbook, verified the web tier and
> Supabase are reachable, and the API deploy is the last blocking piece."

- Avoid: "I fixed it and it's live." Say: "diagnosed, runbook written, one
  deploy away — here's exactly what remains."

---

## 6. RAG pipeline + failure modes (tie to the code)

```text
documents → chunk (800/150) → embed (Cohere) → pgvector
query → embed → match_document_chunks(tenant + role-filtered) → top-5
→ UNTRUSTED_DOCUMENT_BLOCK → LLM → cited answer
```

Failure modes and what this system does / doesn't address:

| Failure mode | Status here |
|---|---|
| Bad chunking (splits mid-section) | Present — fixed 800/150 char split (`rag/chunk.py:5`), no section awareness |
| Irrelevant retrieval (no reranking) | Present — cosine top-5 only, no cross-encoder |
| Stale/missing documents | Partially — none tracked; no freshness/last-updated signal |
| Too much context / bloat | Capped (top_k 5), but no relevance threshold |
| Permission leakage | **Fixed** — now containment (`0008`); earlier was overlap bug |
| Hallucination despite retrieval | Guarded by citation rule in system prompt, not enforced by eval |
| Prompt injection via docs | Defense-in-depth (scan + untrusted block + ACL exclusion) |

---

## 7. Security model (defense-in-depth, in order)

1. AuthN: server-side JWT verification, JWKS (ES256/RS256) + legacy HS256
   fallback (`auth.py:68`).
2. AuthZ: membership-derived role; never client-supplied (`auth.py:109`).
3. Tenant/role isolation at the DB: RLS + tag-containment in the match function
   (`0002_rls.sql`, `0008_fix_acl_semantics.sql`).
4. Prompt injection: scan user input, short-circuit on high severity; scan
   retrieved text; `UNTRUSTED_DOCUMENT_BLOCK`; base64-blob detection
   (`security/prompt_injection.py:42`).
5. Tool execution gate: registry → policy check (role rank, scope, manager
   scope, arg validation, quota) → executor (`tools/policy.py:50`).
6. Dual authorization: tool-execution auth (server) vs business-workflow
   approval (manager approves `pending` request) — kept separate
   (`docs/architecture.md`).
7. Audit: `tool_calls` per decision, `security_events`, `audit_logs`,
   `agent_traces` replay (`main.py:216`).

---

## 8. Production gaps (documented honestly, by area)

**Reliability** — no model fallback, no retries/circuit breaker (fixed 60s
httpx timeout in `llm/cohere.py`), synchronous request path (no queue), no
idempotency key on tool calls (retry could double-create a leave request).
`tenacity` is a declared dep but unused.

**Observability** — per-request trace exists, but no token/cost per trace, no
sampling/retention policy, traces are Supabase RLS rows not a tracing backend,
no dashboards/alerts.

**Security** — `CORS allow_origins=["*"]` + `allow_credentials=True`
(`main.py:41-47`); blind `except Exception: pass` around audit writes
(`tools/policy.py:137`, `orchestrator.py:314`); audit failure is silent.

**Cost** — no caching of embeddings or answers, no model routing, no token
budget per trace, top_k=5 unconditional even when not needed.

**Evaluation** — no golden dataset / regression harness wired to this repo;
"trace status ok" ≠ "task succeeded". This is where `agentb` (dashboard's
evaluation story) connects: LLM-as-judge + human review + groundedness checks.

---

## 9. Answer skeletons (drill on these)

**"Why is this an agent, not an LLM wrapper?"** → Section 2. Emphasize: tool
selection + loop + state, and the control layer (policy / audit) being the real
engineering.

**"How does authorization work?"** → auth.py:109 (verify → derive role) →
policy.py:50 (5 checks in order) → tool_calls row for every decision; plus
business approval separate from tool authorization.

**"How do you know the agent is behaving correctly?"** → honest split:
operational signals (trace, latency, loop count, allow/deny) vs task-level
evaluation (groundedness, task success) — the latter is a gap I'd close with an
evaluation harness.

**"What's your biggest production risk?"** → the ACL fix shows I think DB-level
filters are the real security boundary; but candidly: no model-fallback layer +
synchronous path = single-model single-region dependency → availability risk.

**"Why isn't this production-ready?"** → Section 8, pick 2–3 honest gaps.

**"What happens if retrieved content contains a prompt injection?"** → scan →
flag/skip → UNTRUSTED block (content is data) → ACL already excluded what
wasn't granted; log security_event regardless.

**"How do you prevent an employee from retrieving executive documents?"**
→ tenant filter + tag containment in SQL (`0008`), not in the prompt; plus
`search_documents` tool result never contains what the DB didn't return.

**"How would you scale to 10× traffic?"** → stateless API (FastAPI is
stateless) → add queue + workers for the loop (synchronous LLM calls are the
bottleneck), connection pooling to Supabase, per-tenant rate limits already
exist; cache embeddings/answers; move to async-first with backpressure.

**"How would you reduce latency/cost?"** → smaller/faster model for
classification turns, cache retrieval, cap context (`top_k`), dedupe calls,
token budgets; route heavy turns to big model only (`Section` of prep doc).

**"Tell me about the 502."** → Section 5.

**"Show me something you discovered was wrong in your own system."**
→ Section 4 (tool loop + ACL leak + base64 detector). This is your home run.

---

## 10. Stats to have on hand

- **45 tests passing** (was 21 found / 1 pre-existing failure), including new
  regression suites for the tool-loop and ACL fixes.
- Deployed to Vercel with seeded two-tenant demo ("Try as…"), nightly demo
  reset cron, live Supabase `pgvector` + RLS.