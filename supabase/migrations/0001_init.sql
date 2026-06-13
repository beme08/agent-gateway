-- 0001_init.sql
-- Core schema for Secure Enterprise Agent Gateway.
-- Run in the Supabase SQL editor as the first migration.

create extension if not exists pgcrypto;
create extension if not exists vector;

-- ============================================================
-- Tenants
-- ============================================================

create table if not exists public.tenants (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null unique,
  plan text not null default 'demo' check (plan in ('demo', 'free', 'pro', 'enterprise')),
  max_users int not null default 25,
  max_documents int not null default 50,
  max_agents int not null default 5,
  max_messages_per_month int not null default 2000,
  max_storage_mb int not null default 200,
  monthly_message_count int not null default 0,
  monthly_tool_call_count int not null default 0,
  document_count int not null default 0,
  storage_used_mb int not null default 0,
  agent_count int not null default 0,
  usage_period_start timestamptz not null default date_trunc('month', now()),
  created_at timestamptz not null default now()
);

-- ============================================================
-- Users (mirrors auth.users)
-- ============================================================

create table if not exists public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null unique,
  full_name text,
  created_at timestamptz not null default now()
);

-- ============================================================
-- Tenant memberships
-- ============================================================

do $$ begin
  create type public.tenant_role as enum ('admin', 'manager', 'employee', 'viewer');
exception when duplicate_object then null; end $$;

create table if not exists public.tenant_memberships (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  role public.tenant_role not null,
  manager_user_id uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now(),
  unique (tenant_id, user_id)
);

create index if not exists idx_memberships_user on public.tenant_memberships(user_id);
create index if not exists idx_memberships_tenant on public.tenant_memberships(tenant_id);
create index if not exists idx_memberships_manager on public.tenant_memberships(manager_user_id);

-- ============================================================
-- Accessible tags (single source of truth for role -> ACL)
-- ============================================================

create or replace function public.accessible_tags(p_role public.tenant_role)
returns text[]
language sql
immutable
as $$
  select case p_role
    when 'viewer'   then array['public']
    when 'employee' then array['public', 'hr_policy']
    when 'manager'  then array['public', 'hr_policy', 'manager_only']
    when 'admin'    then array['public', 'hr_policy', 'manager_only', 'executive']
  end;
$$;

-- ============================================================
-- Documents & chunks (RAG)
-- ============================================================

create table if not exists public.documents (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  title text not null,
  source text,
  acl_tags text[] not null check (acl_tags <@ array['public', 'hr_policy', 'manager_only', 'executive']),
  uploaded_by uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists public.document_chunks (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  document_id uuid not null references public.documents(id) on delete cascade,
  chunk_index int not null,
  content text not null,
  embedding vector(1024),
  acl_tags text[] not null,
  page int,
  section text,
  created_at timestamptz not null default now(),
  unique (document_id, chunk_index)
);

create index if not exists idx_chunks_tenant on public.document_chunks(tenant_id);
create index if not exists idx_chunks_document on public.document_chunks(document_id);
create index if not exists idx_chunks_embedding on public.document_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create table if not exists public.retrieval_logs (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  user_id uuid references public.users(id) on delete set null,
  agent_id uuid,
  query text not null,
  retrieved_chunk_ids uuid[] not null default '{}',
  created_at timestamptz not null default now()
);

-- ============================================================
-- Agents
-- ============================================================

create table if not exists public.agents (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  name text not null,
  description text,
  system_prompt text not null,
  allowed_tools text[] not null default '{}',
  created_at timestamptz not null default now()
);

create table if not exists public.agent_sessions (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  agent_id uuid not null references public.agents(id) on delete cascade,
  created_at timestamptz not null default now()
);

create table if not exists public.agent_messages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.agent_sessions(id) on delete cascade,
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  role text not null check (role in ('user', 'assistant', 'tool', 'system')),
  content text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.agent_traces (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  agent_id uuid not null references public.agents(id) on delete cascade,
  session_id uuid not null references public.agent_sessions(id) on delete cascade,
  user_message text not null,
  retrieval_query text,
  retrieved_chunk_ids uuid[] not null default '{}',
  retrieval_safety_status text not null default 'clean',
  input_safety_status text not null default 'clean',
  model_name text,
  embedding_model text,
  tool_loop_count int not null default 0,
  final_status text not null default 'ok',
  error_message text,
  latency_ms int,
  estimated_tokens int,
  created_at timestamptz not null default now()
);

-- ============================================================
-- Tool calls + security events + audit
-- ============================================================

create table if not exists public.tool_calls (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  trace_id uuid references public.agent_traces(id) on delete set null,
  user_id uuid references public.users(id) on delete set null,
  tool_name text not null,
  arguments jsonb not null default '{}'::jsonb,
  result jsonb,
  status text not null check (status in ('allowed', 'denied', 'error')),
  required_role public.tenant_role,
  caller_role public.tenant_role,
  policy_decision text not null,
  policy_reason text,
  latency_ms int,
  created_at timestamptz not null default now()
);

create index if not exists idx_tool_calls_tenant on public.tool_calls(tenant_id, created_at desc);
create index if not exists idx_tool_calls_trace on public.tool_calls(trace_id);

do $$ begin
  create type public.security_event_type as enum (
    'blocked_retrieval', 'blocked_tool_call', 'suspicious_prompt',
    'suspicious_chunk', 'rate_limit_exceeded', 'policy_denial'
  );
exception when duplicate_object then null; end $$;

create table if not exists public.security_events (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references public.tenants(id) on delete cascade,
  user_id uuid references public.users(id) on delete set null,
  event_type public.security_event_type not null,
  severity text not null default 'medium' check (severity in ('low', 'medium', 'high')),
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_security_events_tenant on public.security_events(tenant_id, created_at desc);

create table if not exists public.audit_logs (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  user_id uuid references public.users(id) on delete set null,
  action text not null,
  target_table text,
  target_id uuid,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_audit_tenant on public.audit_logs(tenant_id, created_at desc);

-- ============================================================
-- HR: leave policies, balances, requests, events
-- ============================================================

create table if not exists public.leave_policies (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  leave_type text not null check (leave_type in ('vacation', 'sick', 'personal', 'unpaid', 'parental', 'bereavement')),
  annual_allocation int not null default 0,
  requires_approval boolean not null default true,
  unique (tenant_id, leave_type)
);

create table if not exists public.leave_balances (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  leave_type text not null check (leave_type in ('vacation', 'sick', 'personal', 'unpaid', 'parental', 'bereavement')),
  year int not null,
  allocated_days int not null default 0,
  used_days int not null default 0,
  pending_days int not null default 0,
  remaining_days int not null default 0,
  unique (tenant_id, user_id, leave_type, year)
);

create or replace function public.leave_balances_derive_remaining()
returns trigger language plpgsql as $$
begin
  new.remaining_days := new.allocated_days - new.used_days - new.pending_days;
  if new.remaining_days < 0 then
    new.remaining_days := 0;
  end if;
  return new;
end $$;

drop trigger if exists trg_leave_balances_derive on public.leave_balances;
create trigger trg_leave_balances_derive
  before insert or update on public.leave_balances
  for each row execute function public.leave_balances_derive_remaining();

do $$ begin
  create type public.leave_status as enum ('pending', 'approved', 'rejected', 'cancelled');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.leave_event_type as enum ('created', 'submitted', 'approved', 'rejected', 'cancelled', 'updated');
exception when duplicate_object then null; end $$;

create table if not exists public.leave_requests (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  manager_user_id uuid references public.users(id) on delete set null,
  leave_type text not null check (leave_type in ('vacation', 'sick', 'personal', 'unpaid', 'parental', 'bereavement')),
  start_date date not null,
  end_date date not null,
  total_days int not null,
  status public.leave_status not null default 'pending',
  reason text,
  manager_note text,
  approved_by uuid references public.users(id) on delete set null,
  approved_at timestamptz,
  rejected_by uuid references public.users(id) on delete set null,
  rejected_at timestamptz,
  cancelled_at timestamptz,
  created_at timestamptz not null default now(),
  check (end_date >= start_date),
  check (total_days >= 0)
);

create index if not exists idx_leave_requests_tenant on public.leave_requests(tenant_id, created_at desc);
create index if not exists idx_leave_requests_user on public.leave_requests(user_id, created_at desc);
create index if not exists idx_leave_requests_manager on public.leave_requests(manager_user_id, status);
create index if not exists idx_leave_requests_status on public.leave_requests(tenant_id, status);

create table if not exists public.leave_request_events (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  request_id uuid not null references public.leave_requests(id) on delete cascade,
  actor_user_id uuid references public.users(id) on delete set null,
  event_type public.leave_event_type not null,
  notes text,
  created_at timestamptz not null default now()
);

create index if not exists idx_leave_events_request on public.leave_request_events(request_id, created_at);

-- ============================================================
-- Waitlist
-- ============================================================

create table if not exists public.waitlist_signups (
  id uuid primary key default gen_random_uuid(),
  email text not null,
  company text,
  role text,
  created_at timestamptz not null default now(),
  unique (email)
);
