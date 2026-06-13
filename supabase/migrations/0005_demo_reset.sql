-- 0005_demo_reset.sql
-- Resets a demo tenant back to a clean seeded state. Called by the nightly
-- GitHub Actions cron and from the admin "Reset demo data" button.

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
