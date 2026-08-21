-- 0011_support_reset.sql
-- Extend the nightly demo reset to the Support Operations tables so the
-- public demo comes back to a clean, seeded state every night.
-- Idempotent: recreates the function wholesale.

create or replace function public.reset_demo_tenant(p_tenant_id uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  delete from public.leave_request_events where tenant_id = p_tenant_id;
  delete from public.leave_requests where tenant_id = p_tenant_id;
  delete from public.tool_calls where tenant_id = p_tenant_id;
  delete from public.security_events where tenant_id = p_tenant_id;
  delete from public.audit_logs where tenant_id = p_tenant_id;
  delete from public.retrieval_logs where tenant_id = p_tenant_id;
  delete from public.agent_traces where tenant_id = p_tenant_id;
  delete from public.agent_messages where tenant_id = p_tenant_id;
  delete from public.agent_sessions where tenant_id = p_tenant_id;

  -- Support Operations environment
  delete from public.ticket_events where tenant_id = p_tenant_id;
  delete from public.action_approvals where tenant_id = p_tenant_id;
  delete from public.remediation_actions where tenant_id = p_tenant_id;
  delete from public.support_tickets where tenant_id = p_tenant_id;

  update public.leave_balances
  set used_days = 0, pending_days = 0
  where tenant_id = p_tenant_id;

  update public.tenants
  set monthly_message_count = 0,
      monthly_tool_call_count = 0
  where id = p_tenant_id;

  insert into public.audit_logs (tenant_id, user_id, action, details)
  values (p_tenant_id, null, 'demo.reset', jsonb_build_object('at', now()));
end $$;
