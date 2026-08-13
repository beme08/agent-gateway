# Agilyti AIOps Engineer — Interview Prep

> **Purpose**: interview-preparation notes for the **Agilyti AI Operations Engineer
> (AIOps Engineer)** role — 30-minute recruiter screen **Fri 2026-08-14 14:00
> Europe/Budapest**, and the technical ammunition for later rounds.
>
> Interviewer at screen level: Dorina Nishevci (TA, Agilyti) 
~70%  overlap with `PREP_PACK.md` + `INTERVIEW_DEEP_DIVE.md`. 
This doc adds the  deltas: **Governor**, **Azure** (concept mapping — we have not used Azure),
> and **predictive-on-observability + AI ticketing**.
>
> ⚠️ This is the **technical-round** backing. For Friday keep it conversational
> (see §9).

---

## 1. The through-line: Build → Observe → Guard → Evaluate → Operate

Your story is a pipeline, and each project is one stage. Use this every time
someone asks "tell me about yourself" or "what have you built."

| Stage | Project | What it proves |
|---|---|---|
| **Build** | **Agent Gateway** | Agent + RAG + tools + approvals + audit, deployed multi-tenant with security-by-design |
| **Observe** | **Agent0Waste** | Metrics for AI systems: tokens, cost, execution waste, resource usage — observability tooling |
| **Guard** | **Governor** | The control plane: policy, permissions, prompt-injection, secrets, **bounded autonomy, fail-closed** |
| **Evaluate** | **agentb** | "The agent produced an answer" ≠ "the agent worked" — 60-task benchmark, rubrics |
| **Operate** | **the role** | Detect → diagnose → remediate → verify on enterprise support |

One line: **"I've built the build→observe→guard→evaluate stack around LLM
agents, and this role is the 'operate' layer — running that stack over a global
support organization."**

---

## 2. The centerpiece architecture (rehearse until you can draw it)

```text
Observability
metrics / logs / traces
          ↓
   Detection / Prediction
          ↓
    Incident / Ticket
          ↓
       AI Agent
     ↙    ↓     ↘
  RAG   Tools   History
          ↓
       Governor
          ↓
   ┌──────┼──────┐
   ↓      ↓      ↓
 Auto   Human   Block
          ↓
      Remediation
          ↓
       Verify
          ↓
   Audit + Evaluation
```

**The closing line** (say this — it's the whole point):

> "The important part isn't just putting an LLM in the middle. The operational
> system needs detection, context, controlled action, verification,
> observability, and a feedback/evaluation loop."

**Every box, backed by a project:**

- **Detection/Prediction** — anomaly detection on metrics/logs/traces. Evidence:
  Agent0Waste (I build observability tooling for agents) + the "cost doubled"
  investigation answer (§7).
- **Incident/Ticket** — event → issue/ticket, correlated, deduplicated.
- **AI Agent** — the triage/diagnose loop. Evidence: Agent Gateway orchestrator
  (`orchestrator.py` — max-5-turn loop, `{ok,data,error}` tool envelope).
- **RAG** — diagnose against KB + runbooks. Evidence: Agent Gateway
  ACL-filtered retrieval; failure modes (reranking, staleness) in the deep-dive.
- **Tools** — resolve against real systems. Evidence: tool gateway, policy
  engine, two-tier approval.
- **Governor → Auto/Human/Block** — the guardrails. Evidence: Governor
  (low=auto, medium=human, high=block) + Agent Gateway policy engine. Frame it
  as: "the interesting part of autonomous remediation isn't executing an action
  — it's deciding when it's allowed, under what constraints, and what happens
  when those constraints fail."
- **Verify** — did the remediation actually fix it? Evidence: agentb
  ("resolved" ≠ "fixed"; verification step people skip).
- **Audit + Evaluation** — every decision traced. Evidence: Agent Gateway
  `agent_traces`/`tool_calls`/`security_events`; feedback loop → eval → improve.

---

## 3. Governor — the "within guardrails" answer (honest framing only)

**The phrase in the job spec**: "auto-remediate **within defined safety
parameters**." Governor is your direct evidence for that phrase.

**Elevator version (gated-autonomy framing — lead with this):**

> "I've been building a governance layer around autonomous agents. The idea is
> that the agent doesn't get unrestricted authority — actions are gated by
> policy, risk, scope, and approval requirements. The system fails closed when
> something goes wrong, maintains an audit trail, and autonomy can be demoted
> rather than the agent promoting itself."

**The Remediate hook** (ties Governor directly to their role — their system is
Detect → Diagnose → Remediate → Verify, and Governor sits around *Remediate*):

> "The interesting part of autonomous remediation isn't getting an agent to
> execute an action. It's deciding when it's allowed to execute that action,
> under what constraints, and what happens when those constraints fail."

**If asked how far you've taken it:**

> "I've been exploring a governance model for progressively increasing agent
> autonomy — a bounded L0–L10 ladder where every level requires evidence, the
> system never promotes itself, demotion is automatic, and promotion to a
> higher rung requires a founder sign-off."

**If asked whether it runs enterprise production workloads:**

> "No — the governance layer and tests are implemented, but production runtime
> enforcement is intentionally a separate authorization step."

**The concrete pieces (know the names):**

- **Risk-tiered action policy** — low-risk = auto, medium-risk = human
  approval, high-risk/blocklist = hard block. (Same philosophy as the Agent
  Gateway `dangerous`-tool scaffold.)
- **Incident gate** — fail-closed lifecycle: self-check failure sets
  `system_blocked=1` → all autonomous work stops → recovery is human-only, no
  auto-unblock. *This is an AIOps incident lifecycle applied to agents.*
- **Scope containment** — child/subagent scope ⊆ parent scope, no widening.
- **Guardrail code** — `policy_filter.py` (allowed/forbidden ops gate before
  tool calls, audit-logged), `secret_detect.py` (blocks externalization of
  keys/tokens), `prompt_inject.py`, `audit.py`.
- **Bounded autonomy model (L0–L10)** — "100% autonomy ≠ unrestricted
  autonomy"; every level requires evidence, the system never promotes itself,
  demotion is automatic, uncertainty fails closed.

**Why it's credible**: you didn't just write rules — you wrote the control
plane + guardrail modules + a test-frozen RC1 baseline. And the honest framing
is the point: fail-closed governance is a *feature*, not an excuse.

---

## 4. Azure — concept-transfer map (we have NOT used Azure)

> Honest opening: **"I haven't shipped this exact stack, but I understand what
> it does, and here's exactly how it maps to systems I've built."**
> Role lists: Azure AI Foundry, Azure OpenAI, AKS, Azure Monitor, Azure
> DevOps, Docker, Grafana.

**Terminology update (2026 docs)**: Azure AI Foundry → now **Microsoft Foundry**
(portal `ai.azure.com`). One resource = projects; unified RBAC, networking,
policies; built-in observability and evals.

| Microsoft / Azure service | What it is | Your equivalent |
|---|---|---|
| **Foundry Agent Service** | Managed agent platform: **prompt agents** (declarative) + **hosted agents** (your code as a container: Agent Framework, LangGraph, OpenAI Agents SDK); **Responses API** as single entry point; tool catalog (web/file search, code interpreter, MCP servers); versioning/publishing; agent **identity (Entra, OBO)** | Your FastAPI orchestrator + tool registry; "model proposes, your code executes" |
| **Azure OpenAI (function/tool calling)** | `tools` + `tool_choice`; model returns JSON args + `tool_call_id`; you execute and feed results back with `role: "tool"` | **The exact loop we just fixed** in `cohere.py` (multi-step tool use). You can say: "I've implemented this pattern end to end — model proposes → I execute → result fed back via tool call id." |
| **Azure AI Search** | Vector/hybrid search; **agentic retrieval** (knowledge bases, query planning, sub-queries, semantic reranking); integrated vectorization | pgvector + `match_document_chunks`; your documented RAG gap = reranking, which AI Search's agentic retrieval does |
| **Azure Monitor / Application Insights** | Unified telemetry: **Log Analytics (KQL)** for logs/traces, **Azure Monitor workspaces (PromQL)** for metrics; **Application Insights** = OpenTelemetry APM; **built-in AI agent observability dashboards** (token, latency, error, quality); **AIOps**: dynamic-threshold alerts, smart detection, alert correlation → "issues" | `agent_traces` + `tool_calls` rows; Agent0Waste |
| **Azure Copilot Observability Agent** | Runs autonomously on alerts: correlates alerts into incidents, runs deep investigation, creates issues with findings + next steps, **humans stay in control** | This is literally the role — say so: "what I'd build, and it's what this role does" |
| **AKS + Docker** | Managed Kubernetes, containerized services/agents, autoscale | Deployment of your FastAPI/agent services |
| **Azure DevOps** | Pipelines / CI-CD, repos, boards | Your GitHub Actions + runbooks |
| **Grafana** | Dashboards on metrics | Familiarity: metrics/alerting concepts; Agent0Waste output is a scan report |

**Best 30-second Azure answer if asked directly:**

> "I haven't deployed this stack, but I know exactly what each piece does and
> how it maps to what I've built. My agent loop uses the same tool-calling
> contract as Azure OpenAI's function calling. My retrieval layer is the same
> pattern as AI Search. My traces are the same shape as Application Insights.
> The part I'd need to ramp on is Azure's operational surface — governance,
> networking, IAM — and that's a fast ramp because the concepts are the ones I
> already operate."

---

## 5. Predictive-on-observability + AI ticketing (bounded, vocabulary-ready)

### Predictive / anomaly detection (metrics, logs, traces)
- **Baseline vs anomaly**: dynamic thresholds, z-score, EWMA, seasonality
  decomposition (weekly/daily patterns matter for support traffic).
- **Unsupervised**: isolation forest on metric/feature vectors.
- **Correlation**: alert dedup + correlation into a single incident (this is
  what Azure Monitor "issues" and the Observability Agent do).
- **RCA / dependency mapping**: service maps, call graphs, transaction traces —
  "find the component behind the business transaction" (role explicitly asks
  for this).
- **AIOps best practices vocab**: event correlation, automated root cause
  analysis, noise reduction, runbook automation.
- **The "cost doubled" investigation** (from earlier prep) is your anomaly
  answer: metrics → identify workload → token/model/retry/loop/context growth →
  regression → mitigate → verify.

### AI ticketing (clustering, similarity, drafting)
All of this is **the same machinery as Agent Gateway RAG** — say that:
- **Similarity / duplicate detection** — embeddings + vector search ("is this a
  known issue?").
- **Clustering** — group tickets by text/embedding similarity (tf-idf or
  embeddings + k-means/HDBSCAN) to surface recurring patterns → convert to
  runbooks (ties to "convert repetitive patterns into automated remediation").
- **Generative drafting** — LLM summarization of ticket context + suggested
  resolution within guardrails (Governor).
- **ServiceNow Predictive Intelligence / Now Assist** — the ITSM native AI
  layer; the concepts are the same (predict, classify, cluster, assist).

### SQL / KQL
Comfort answer: SQL is your thing; observability SQL = **KQL** (Log Analytics)
and **PromQL** (metrics). KQL example shape you can speak to:
`customEvents | where timestamp > ago(1h) | summarize count() by operation_Id`
→ tracing latency/errors per transaction.

---

## 6. Answer skeletons (technical round)

**"Design an AIOps system that triages, diagnoses, and auto-remediates tickets."**
→ §2, whole answer. End with the closing line.

**"What's the biggest risk in auto-remediation?"**
→ Uncontrolled autonomy: an agent resolving the wrong thing or taking a
side-effect action. Mitigation: Governor (risk tiers, human approval for
medium/high, incident gate fail-closed) + verification step (fix actually
worked?) + audit.

**"How do you evaluate whether the agent worked?"**
→ Operational signals (traces, latency, tool success) ≠ task success. Need
golden datasets, groundedness checks, human review, regression evals (agentb
is the evidence I think this way).

**"How would you detect an issue before it becomes an incident?"**
→ Baseline the metrics (tokens, latency, error rate, tool failures, loop
count) → dynamic thresholds/anomaly detection → correlate into a single
incident → agent investigates with RAG over runbooks + tool access → propose,
human-in-the-loop for action.

**"Tell me about Azure"** → §4 honest transfer line; mention the Observability
Agent + function-calling loop as the exact matches to what you've built.

**"Something you found wrong in your own system."** → Tool-loop bug + ACL
overlap leak (deep-dive §4). Now even better: the tool-loop bug is literally
the Azure function-calling loop — "I found my multi-step tool loop wasn't
sending results back to the model; fixed it to the documented contract; that's
the same pattern Azure OpenAI's tool calling uses."

**"Why you for an AIOps role with no enterprise ops history?"** → "I'm the
person who builds the systems this role operates — agents, observability,
guardrails, evaluation. Operating them at global scale is the step I'm
positioned for."

---

## 7. Friday — 30-minute recruiter screen (conversational)

**Posture**: Dorina is TA, not a technical round. Be warm, concise, no
architecture dump. Let her guide. Your job: sound like the obvious fit and
find out what the role really is.

**60-second positioning** (no jargon):

> "I'm an AI systems engineer. I build the infrastructure around LLM agents —
> how they run, how they're observed, how they're kept safe, how they're
> evaluated. I built a multi-tenant agent gateway with RAG and approved tool
> actions, an observability tool for AI systems, and a governance layer for
> bounded autonomy. So the 'AI that helps support teams prevent problems
> instead of reacting' framing is exactly the direction I've been working."

**Discovery questions (recruiter screen — get signal):**

1. **"Is this role part of Agilyti's engineering organization, or would I be
   embedded directly with the client's AIOps team?"** ← your key question; it
   changes how to evaluate the opportunity.
2. "What does the client's support org look like — size, global footprint,
   what ticketing/observability stack?"
3. "Is the team building on Azure AI Foundry today, or is this a new platform
   being stood up?"
4. "What's the team's current AI maturity — existing agents/models, or greenfield?"
5. "What would success look like in the first six months?"
6. "Where is the team based, and is this remote-friendly?"

**If she asks technical questions anyway** (some TA screens include a light
technical screen): use §6 — keep answers 30–45s, conversational, no whiteboard.

---

## 8. Honesty guardrails

- **Azure**: "I haven't shipped on this stack" — always. Map concepts, never
  imply deployed experience.
- **Governor**: production enforcement is *not authorized* — that's the design.
  Say the honest two lines from §3.
- **Governor novelty — do NOT say "nobody else has built this."** Say
  "I've been exploring a governance model for progressively increasing agent
  autonomy." Internal context only: the parts are industry-standard primitives
  (NIST RMF, ISO 42001, OWASP, AAGMM; Claude Code/Copilot-class harnesses stop
  at PR-draft; CSA calls the self-modifying level a research question) — no
  documented operational L0→L10 evidence-docketed ladder exists, which makes
  yours a first-documented instance *if* it completes. Your edge is
  evidence-bundle + audit discipline (ODTA's Action-Evidence Bundle is a 2026
  research construct). L9–L10 claims will draw scrutiny precisely because the
  controls are the open frontier — your oracle-test + founder-gate + demotion
  design is the structure reviewers want to see.
- **agentb**: benchmark/rubric project; don't overclaim deployment scale.
- **Predictive models on observability**: adjacent — you build observability
  tooling and designed the detection layer; say "I've been working on" not
  "I've shipped to enterprise".
- Only Agent Gateway (deployed Vercel + live Supabase) and the local AI stack
  have real shipped claims.

---

## 9. Rehearsal order (if time is short, in order)

1. §2 centerpiece + closing line — 5 min.
2. §3 Governor elevator (gated-autonomy framing) + the honest production line
   + the Remediate hook — 5 min.
3. §4 Azure transfer line + the two "this is literally my work" hooks
   (function-calling loop, Observability Agent) — 5 min.
4. §7 recruiter script + discovery questions — 5 min.
5. §6 "found something wrong" answer (tool loop + ACL) — 3 min.

---

## 10. ML/LLM fundamentals — study priority (do NOT become an ML researcher)

This role hires an **AI systems engineer**, not an ML researcher. Questions are
far more likely to be operational: "How would you use embeddings to find
similar incidents?", "How would you build an agent that diagnoses a ticket?",
"How would you safely let it remediate?", "How would you detect anomalies from
observability data?", "How would you evaluate whether the agent actually
resolved the incident?", "How would you monitor an AI agent in production?"

**Study order (everything before the ⚪ is higher value than any ML internals):**

1. **AIOps architecture** — detect → diagnose → remediate → verify (§2)
2. **Agents** — tool/function calling, orchestration loops, memory
3. **Observability** — tokens, latency, errors, loops, cost
4. **RAG/retrieval** — embeddings, chunking, grounding, reranking
5. **Incident correlation** — alert dedup, anomaly detection, RCA
6. **Guardrails / Governor** — policy, risk tiers, fail-closed (§3)
7. **Evaluation** — "resolved ≠ fixed", rubrics, regression detection
8. **Reliability** — fallbacks, retries, circuit breakers, 502s
9. **Python / SQL (KQL, PromQL)**
10. **Azure concepts** — §4 map
11. **LLM fundamentals** — what they are and how you use them in systems

**LLM/ML topic buckets for reference:**

- 🟢 **Know well**: Transformers (high-level: attention relates tokens/context);
  RAG ⭐⭐⭐⭐⭐; GPT/LLMs (what they are, how you use them in systems); MoE
  (different experts handle different inputs → cost/efficiency); RLHF (aligning
  behavior with human preferences).
- 🟡 **Know conceptually only**: LoRA (efficient fine-tuning, few extra
  parameters); PEFT (category LoRA belongs to); BERT (encoder vs generative
  LLM; representations/classification); LLaMA (Meta's open-weight family);
  RoPE (positional encoding); InstructGPT (instruction tuning/alignment).
- 🔴 **Very low priority**: ViT, VAE, GANs, Diffusion Models — no mapping to
  metrics/logs/traces + agents + predictive + ticketing + GenAI.

**The test for studying anything**: does it help you answer the six
operational questions above? If not, don't cram it for Friday.
