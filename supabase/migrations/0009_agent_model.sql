-- 0009_agent_model.sql
-- Per-agent LLM provider/model routing + gateway risk-tier columns.
--
-- agents.provider / agents.model  -> per-agent LLM routing (Support Ops runs
--                                    ox-alpha; HR agents keep the default).
-- agent_traces.llm_provider       -> which provider actually served the run
--                                    (failover evidence).
-- tool_calls.risk_tier            -> auto | approval_required | prohibited.
-- security_event_type             -> new gateway events.

alter table public.agents
  add column if not exists provider text,
  add column if not exists model text;

comment on column public.agents.provider is
  'Preferred LLM provider: oxalpha | openai_compat | cohere. Null = gateway default chain.';
comment on column public.agents.model is
  'Model override for the preferred provider. Null = provider default.';

alter table public.agent_traces
  add column if not exists llm_provider text;

alter table public.tool_calls
  add column if not exists risk_tier text;

-- New gateway event types (idempotent; ALTER TYPE ADD VALUE cannot run inside
-- a transaction block, so guard via DO + exception swallow is not possible —
-- run each statement standalone).
alter type public.security_event_type add value if not exists 'approval_requested';
alter type public.security_event_type add value if not exists 'prohibited_action_attempt';
alter type public.security_event_type add value if not exists 'provider_failover';
alter type public.security_event_type add value if not exists 'approval_blocked_by_policy';
