-- 0006_leave_manager.sql
-- Backfill leave_requests.manager_user_id from tenant_memberships, and update
-- the create_leave_request function to populate it on insert.

-- 1. Backfill any existing rows where manager_user_id is null.
update public.leave_requests r
set manager_user_id = tm.manager_user_id
from public.tenant_memberships tm
where tm.tenant_id = r.tenant_id
  and tm.user_id = r.user_id
  and r.manager_user_id is null
  and tm.manager_user_id is not null;

-- 2. Replace create_leave_request to populate manager_user_id from the membership.
create or replace function public.create_leave_request(
  p_tenant_id uuid,
  p_user_id uuid,
  p_leave_type text,
  p_start_date date,
  p_end_date date,
  p_reason text
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_request_id uuid;
  v_total_days int;
  v_balance public.leave_balances%rowtype;
  v_year int;
  v_manager_id uuid;
begin
  if p_end_date < p_start_date then
    raise exception 'end_date must be on or after start_date';
  end if;

  v_total_days := (p_start_date - p_end_date);  -- placeholder; overwritten below
  v_total_days := (p_end_date - p_start_date) + 1;
  v_year := extract(year from p_start_date)::int;

  select * into v_balance
  from public.leave_balances
  where tenant_id = p_tenant_id
    and user_id = p_user_id
    and leave_type = p_leave_type
    and year = v_year;

  if not found then
    raise exception 'no leave balance configured for type % in year %', p_leave_type, v_year;
  end if;

  if v_balance.remaining_days < v_total_days then
    raise exception 'insufficient balance: have % days, need %', v_balance.remaining_days, v_total_days;
  end if;

  -- Look up the employee's manager from tenant_memberships so the request
  -- can be approved by the right person.
  select manager_user_id into v_manager_id
  from public.tenant_memberships
  where tenant_id = p_tenant_id and user_id = p_user_id;

  insert into public.leave_requests (
    tenant_id, user_id, manager_user_id, leave_type, start_date, end_date, total_days, reason, status
  ) values (
    p_tenant_id, p_user_id, v_manager_id, p_leave_type, p_start_date, p_end_date, v_total_days, p_reason, 'pending'
  )
  returning id into v_request_id;

  update public.leave_balances
  set pending_days = pending_days + v_total_days
  where id = v_balance.id;

  insert into public.leave_request_events (tenant_id, request_id, actor_user_id, event_type, notes)
  values (p_tenant_id, v_request_id, p_user_id, 'created', null),
         (p_tenant_id, v_request_id, p_user_id, 'submitted', null);

  insert into public.audit_logs (tenant_id, user_id, action, target_table, target_id, details)
  values (p_tenant_id, p_user_id, 'leave.create', 'leave_requests', v_request_id,
          jsonb_build_object('leave_type', p_leave_type, 'total_days', v_total_days));

  return v_request_id;
end $$;
