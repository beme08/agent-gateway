-- 0010_support_ops.sql
-- Support Operations environment: tickets, ticket timeline, gateway-level
-- human approvals, and remediation records. Reuses the existing tenant,
-- membership, ACL, and audit model — no new security primitives.

-- ============================================================
-- Support tickets (simulated ticketing system of record)
-- ============================================================

create table if not exists public.support_tickets (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  ticket_ref text not null,
  title text not null,
  body text not null default '',
  severity text not null default 'medium'
    check (severity in ('low', 'medium', 'high', 'critical')),
  category text not null default 'other'
    check (category in ('incident', 'bug', 'access', 'billing', 'question', 'other')),
  status text not null default 'open'
    check (status in ('open', 'triaged', 'in_progress', 'pending_approval',
                      'remediating', 'verifying', 'resolved', 'blocked', 'closed')),
  reporter_email text,
  affected_service text,
  created_by uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, ticket_ref)
);

create index if not exists idx_support_tickets_tenant
  on public.support_tickets(tenant_id, created_at desc);

create table if not exists public.ticket_events (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  ticket_id uuid not null references public.support_tickets(id) on delete cascade,
  event_type text not null,
  actor text not null default 'system'
    check (actor in ('agent', 'human', 'system')),
  detail jsonb not null default '{}'::jsonb,
  trace_id uuid references public.agent_traces(id) on delete set null,
  created_at timestamptz not null default now()
);

create index if not exists idx_ticket_events_ticket
  on public.ticket_events(ticket_id, created_at);

-- ============================================================
-- Gateway-level human approvals (risk-tiered actions)
-- ============================================================

create table if not exists public.action_approvals (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  trace_id uuid references public.agent_traces(id) on delete set null,
  requested_by uuid references public.users(id) on delete set null,
  tool_name text not null,
  arguments jsonb not null default '{}'::jsonb,
  risk_tier text not null default 'approval_required',
  reason text,
  status text not null default 'pending'
    check (status in ('pending', 'approved', 'rejected', 'executed', 'failed')),
  decided_by uuid references public.users(id) on delete set null,
  decision_note text,
  decided_at timestamptz,
  executed_at timestamptz,
  execution_result jsonb,
  context jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_action_approvals_tenant
  on public.action_approvals(tenant_id, status, created_at desc);

-- ============================================================
-- Remediation records (action + verification evidence)
-- ============================================================

create table if not exists public.remediation_actions (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  ticket_id uuid references public.support_tickets(id) on delete set null,
  trace_id uuid references public.agent_traces(id) on delete set null,
  tool_name text not null,
  arguments jsonb not null default '{}'::jsonb,
  outcome text not null
    check (outcome in ('executed', 'verification_failed', 'denied',
                       'failed', 'approval_pending')),
  verification jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_remediation_tenant
  on public.remediation_actions(tenant_id, created_at desc);

-- ============================================================
-- ACL: support knowledge-base tag
-- ============================================================

alter table public.documents drop constraint if exists documents_acl_tags_check;
alter table public.documents
  add constraint documents_acl_tags_check
  check (acl_tags <@ array['public', 'hr_policy', 'manager_only', 'executive', 'support_kb']);

create or replace function public.accessible_tags(p_role public.tenant_role)
returns text[]
language sql
immutable
as $$
  select case p_role
    when 'viewer'   then array['public']
    when 'employee' then array['public', 'hr_policy', 'support_kb']
    when 'manager'  then array['public', 'hr_policy', 'support_kb', 'manager_only']
    when 'admin'    then array['public', 'hr_policy', 'support_kb', 'manager_only', 'executive']
  end;
$$;

-- ============================================================
-- RLS
-- ============================================================

alter table public.support_tickets enable row level security;
alter table public.ticket_events enable row level security;
alter table public.action_approvals enable row level security;
alter table public.remediation_actions enable row level security;

drop policy if exists tenant_isolation on public.support_tickets;
create policy tenant_isolation on public.support_tickets
  for all using (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  ) with check (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  );

drop policy if exists tenant_read on public.ticket_events;
create policy tenant_read on public.ticket_events
  for select using (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  );
-- Writes go through the API (service role bypasses RLS); no client insert policy.

drop policy if exists tenant_read on public.action_approvals;
create policy tenant_read on public.action_approvals
  for select using (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  );
-- Approve/reject happens only through the authenticated API (service role);
-- clients can read but never mutate approvals directly.

drop policy if exists tenant_read on public.remediation_actions;
create policy tenant_read on public.remediation_actions
  for select using (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  );
