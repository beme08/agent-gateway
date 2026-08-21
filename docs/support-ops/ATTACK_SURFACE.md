# Agent Attack Surface & Red-Team Coverage

> Every input channel an attacker can influence, what the gateway does about
> it, and where the red-team suite proves it. Complements
> `EVAL_RESULTS.md` (deterministic proof) and `HARDENING.md` (control model).

## Attack surface matrix

| # | Surface | Example attack | Defense layer | Proven by |
|---|---------|----------------|---------------|-----------|
| 1 | User chat message | "ignore previous instructions…" | injection detector → refusal before LLM runs | eval `prompt_injection_via_ticket_blocked` |
| 2 | Ticket body (indirect) | ticket text instructs the agent to call destructive tools | untrusted-content framing + detector on composed message | same eval; live: ox-alpha refused |
| 3 | Knowledge-base content (poisoned RAG) | KB chunk contains agent instructions | chunk-level detector + `UNTRUSTED_DOCUMENT_BLOCK` + ACL filtering | eval `kb_injection_flagged` |
| 4 | Tool arguments | `service="*"`, `replicas=99999`, bad version string | constraint validation in gateway before adapters | eval `invalid_arguments_rejected` |
| 5 | Risk-tier bypass via approval | crafted/hand-edited approval row for a prohibited tool | approve endpoint re-runs full policy check with original context | eval `approval_cannot_bypass_policy` |
| 6 | Privilege escalation | employee/admin attempts out-of-role or prohibited actions | role authorization independent of tier; prohibited gate before roles | evals `role_authorization_enforced`, `prohibited_blocked_for_admin` |
| 7 | Multi-turn coercion | benign first turn, destructive second turn | per-call policy evaluation — no conversation-level trust accrual | eval `multi_step_coercion_blocked` |
| 8 | Cross-tenant access | guess another tenant's resource ids | tenant scoping in every tool handler + RLS | eval `cross_tenant_isolation_enforced` |
| 9 | Provider compromise / misbehaving model | model emits arbitrary tool calls | every call re-authorized server-side; model output is a proposal only | whole-suite design; control chain |
| 10 | Adapter responses (compromised upstream) | observability returns hostile content | adapter outputs are data; recorded as evidence; verification gates actions | adapter_failure + verification evals |
| 11 | Approval flow abuse | approve own request / approve without role | manager/admin gate on endpoint; requester≠approver allowed but policy re-check binds to requester's context | approvals tests + live demo 2b |

## Red-team methodology

1. **Enumerate surfaces** (table above) — anything that carries text, ids,
   or arguments into the loop.
2. **Write the attack as a deterministic scenario** — scripted LLM performs
   the attack exactly; assertions check the *gateway outcome*, not wording.
3. **Assert the security post-condition**, not the mechanism:
   nothing destructive executed, no cross-tenant payload leaked, denial
   recorded with evidence (`tool_calls`, `security_events`).
4. **Accept either blocking layer**: model-layer refusal and gateway-layer
   denial both satisfy the post-condition (mirrors `demo_tests.sh`).
5. **Re-run on every push** (CI) and after any guardrail change
   (`replay.py` re-decides historical actions against current policy).

## Known gaps (honesty section)

- Injection detection is pattern-based; semantic/jailbreak detection is future work.
- No automated adversarial fuzzing of argument shapes beyond declared constraints.
- Red team currently covers single-agent flows; multi-agent delegation would add surface.
