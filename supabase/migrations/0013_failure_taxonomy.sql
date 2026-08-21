-- 0013_failure_taxonomy.sql
-- Failure taxonomy for error analysis. The orchestrator auto-classifies every
-- finished trace; humans can re-label via analyze_traces.py (open coding ->
-- axial coding: free-text review groups into these fixed classes).

alter table public.agent_traces
  add column if not exists failure_class text
    check (failure_class is null or failure_class in (
      'none',                  -- completed as intended
      'injection_blocked',     -- guardrail refused suspicious input
      'policy_denied',         -- gateway denied a proposed action (expected for prohibited)
      'argument_error',        -- tool calls failed argument validation
      'retrieval_miss',        -- no relevant chunks retrieved
      'verification_failed',   -- remediation post-condition not met
      'provider_error',        -- LLM/provider chain failure incl. failover
      'tool_error',            -- adapter/execution error surfaced
      'loop_exhausted'         -- hit max tool-loop turns without final answer
    )),
  add column if not exists failure_notes jsonb
    default '{}'::jsonb;

create index if not exists idx_traces_failure_class
  on public.agent_traces(tenant_id, failure_class, created_at desc);
