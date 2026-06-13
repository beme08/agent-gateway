-- 0002_rls.sql
-- Row-Level Security policies. Enable RLS on every tenant-scoped table and
-- gate reads/writes by tenant membership. Admin-only tables are additionally
-- gated by role.

alter table public.tenants enable row level security;
alter table public.users enable row level security;
alter table public.tenant_memberships enable row level security;
alter table public.documents enable row level security;
alter table public.document_chunks enable row level security;
alter table public.retrieval_logs enable row level security;
alter table public.agents enable row level security;
alter table public.agent_sessions enable row level security;
alter table public.agent_messages enable row level security;
alter table public.agent_traces enable row level security;
alter table public.tool_calls enable row level security;
alter table public.security_events enable row level security;
alter table public.audit_logs enable row level security;
alter table public.leave_policies enable row level security;
alter table public.leave_balances enable row level security;
alter table public.leave_requests enable row level security;
alter table public.leave_request_events enable row level security;
alter table public.waitlist_signups enable row level security;

-- ============================================================
-- Helper: is the current user an admin of this tenant?
-- ============================================================

create or replace function public.is_tenant_admin(p_tenant_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.tenant_memberships
    where tenant_id = p_tenant_id
      and user_id = auth.uid()
      and role = 'admin'
  );
$$;

-- ============================================================
-- Generic tenant-isolation policies
-- ============================================================

drop policy if exists tenant_isolation on public.tenant_memberships;
create policy tenant_isolation on public.tenant_memberships
  for all using (
    user_id = auth.uid()
    or public.is_tenant_admin(tenant_id)
  ) with check (
    user_id = auth.uid()
    or public.is_tenant_admin(tenant_id)
  );

drop policy if exists tenant_isolation on public.users;
create policy tenant_isolation on public.users
  for all using (id = auth.uid()) with check (id = auth.uid());

drop policy if exists tenant_isolation on public.tenants;
create policy tenant_isolation on public.tenants
  for select using (
    id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  );

drop policy if exists tenant_isolation on public.documents;
create policy tenant_isolation on public.documents
  for all using (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  ) with check (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  );

drop policy if exists tenant_isolation on public.document_chunks;
create policy tenant_isolation on public.document_chunks
  for all using (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  ) with check (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  );

drop policy if exists tenant_isolation on public.retrieval_logs;
create policy tenant_isolation on public.retrieval_logs
  for all using (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  ) with check (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  );

drop policy if exists tenant_isolation on public.agents;
create policy tenant_isolation on public.agents
  for all using (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  ) with check (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  );

drop policy if exists tenant_isolation on public.agent_sessions;
create policy tenant_isolation on public.agent_sessions
  for all using (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  ) with check (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  );

drop policy if exists tenant_isolation on public.agent_messages;
create policy tenant_isolation on public.agent_messages
  for all using (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  ) with check (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  );

drop policy if exists tenant_isolation on public.agent_traces;
create policy tenant_isolation on public.agent_traces
  for all using (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  ) with check (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  );

drop policy if exists tenant_isolation on public.tool_calls;
create policy tenant_isolation on public.tool_calls
  for all using (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  ) with check (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  );

drop policy if exists tenant_isolation on public.leave_policies;
create policy tenant_isolation on public.leave_policies
  for all using (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  ) with check (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  );

drop policy if exists tenant_isolation on public.leave_balances;
create policy tenant_isolation on public.leave_balances
  for all using (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  ) with check (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  );

drop policy if exists tenant_isolation on public.leave_requests;
create policy tenant_isolation on public.leave_requests
  for all using (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  ) with check (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  );

drop policy if exists tenant_isolation on public.leave_request_events;
create policy tenant_isolation on public.leave_request_events
  for all using (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  ) with check (
    tenant_id in (select tenant_id from public.tenant_memberships where user_id = auth.uid())
  );

-- ============================================================
-- Admin-only tables
-- ============================================================

drop policy if exists admin_only on public.audit_logs;
create policy admin_only on public.audit_logs
  for all using (public.is_tenant_admin(tenant_id)) with check (public.is_tenant_admin(tenant_id));

drop policy if exists admin_only on public.security_events;
create policy admin_only on public.security_events
  for all using (public.is_tenant_admin(tenant_id)) with check (public.is_tenant_admin(tenant_id));

-- ============================================================
-- Waitlist: anyone can insert, no one can read (admin uses service role)
-- ============================================================

drop policy if exists waitlist_insert on public.waitlist_signups;
create policy waitlist_insert on public.waitlist_signups
  for insert with check (true);
