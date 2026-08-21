# Testing Pyramid for Agents

> How testing is layered for this platform, from pure functions to live
> monitoring. Each layer has a different purpose, cost, and determinism
> profile. CI runs layers 1–4 on every push.

```
                    ▲  5. Online monitoring & error analysis
                   ▲▲   audit dashboard · analyze_traces.py · replay.py
                  ▲▲▲
                 ▲▲▲▲   4. Live end-to-end demo suite
                ▲▲▲▲▲   scripts/demo_tests.sh (real API, real DB, real LLM)
               ▲▲▲▲▲▲
              ▲▲▲▲▲▲▲   3. Deterministic agent evaluation
             ▲▲▲▲▲▲▲▲   app/evals/ — 16 scenarios, 59 assertions (CI)
            ▲▲▲▲▲▲▲▲▲
           ▲▲▲▲▲▲▲▲▲▲   2. Component contracts
          ▲▲▲▲▲▲▲▲▲▲▲   provider tool-loops, failover chains, approval lifecycle
         ▲▲▲▲▲▲▲▲▲▲▲▲
        ▲▲▲▲▲▲▲▲▲▲▲▲▲   1. Unit — policy engine, schemas, validators
       ▲▲▲▲▲▲▲▲▲▲▲▲▲▲   fastest, most deterministic, runs everywhere
```

## Layer details

### 1. Unit — decision logic (`app/tests/`)
Policy engine (roles, tiers, constraints), prompt-injection patterns, ACL
tags, leave transitions. Pure functions; milliseconds; zero I/O.

### 2. Component contracts (`app/tests/test_*_tool_loop.py`)
Each LLM provider's request/response contract, message serialization, and
the orchestrator's failover chain. Mocked HTTP; locks the interfaces the
gateway depends on so providers can be swapped safely.

### 3. Deterministic agent evaluation (`app/evals/`)
The full loop — orchestrator → policy → tools → adapters — against fake
persistence and a scripted LLM. Functional + adversarial scenarios assert
**gateway outcomes** (decisions, approvals, verification post-conditions),
never model wording. This is the layer that makes agent behavior a
regression-testable artifact. Also includes:
- `retrieval_eval.py` — golden-set retrieval quality (hit@k, MRR) vs live DB
- `replay.py` — re-decides historical production tool calls under current policy

### 4. Live demo suite (`scripts/demo_tests.sh`)
Real API + real Supabase + real ox-alpha. Proves wiring, auth, and that the
whole system behaves under a real model. Assertions still target gateway
behavior; either guardrail layer (model refusal or gateway denial) counts.

### 5. Online monitoring & error analysis
Production traces auto-classified into a failure taxonomy
(`agent_traces.failure_class`). `scripts/analyze_traces.py` groups failures,
supports human relabeling (open → axial coding), and emits test-case
candidates — closing the loop **from error analysis back into layer 3**.

## The improvement loop

```
traffic/demo ──▶ traces ──▶ analyze_traces.py ──▶ failure taxonomy
                                   │                        │
                                   ▼                        ▼
                        new/relabelled scenarios      replay.py regression check
                                   │                        │
                                   ▼                        ▼
                          app/evals (CI, forever)     guardrail changes verified
```

Example from this repo: `retrieval_eval.py` measured hit@3 = 0.25, exposed
the offline embedder as the cause, the fix was verified by re-running the
same golden set (hit@3 = 1.0, MRR 0.94).

## What is deliberately NOT tested

- Exact LLM wording (non-deterministic; asserted only at gateway boundaries)
- Real upstream vendor behavior (adapters are Protocol-mocked; contracts are)
- Load/performance (free-tier demo scope)
