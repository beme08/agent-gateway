-- 0003_leave_functions.sql
-- Centralized leave transition logic. The only place that mutates balance
-- columns and the only path through which the UI route and the agent tool
-- can create / approve / reject / cancel requests.

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
begin
  if p_end_date < p_start_date then
    raise exception 'end_date must be on or after start_date';
  end if;

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

  insert into public.leave_requests (
    tenant_id, user_id, leave_type, start_date, end_date, total_days, reason, status
  ) values (
    p_tenant_id, p_user_id, p_leave_type, p_start_date, p_end_date, v_total_days, p_reason, 'pending'
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

create or replace function public.approve_leave_request(
  p_request_id uuid,
  p_manager_user_id uuid,
  p_note text
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_req public.leave_requests%rowtype;
  v_is_admin boolean;
begin
  select * into v_req from public.leave_requests where id = p_request_id for update;
  if not found then raise exception 'request not found'; end if;
  if v_req.status <> 'pending' then raise exception 'request is not pending (status=%)', v_req.status; end if;

  select exists (
    select 1 from public.tenant_memberships
    where tenant_id = v_req.tenant_id and user_id = p_manager_user_id and role = 'admin'
  ) into v_is_admin;

  if not v_is_admin and v_req.manager_user_id is distinct from p_manager_user_id then
    raise exception 'manager % is not authorized to approve this request', p_manager_user_id;
  end if;

  update public.leave_requests
  set status = 'approved',
      approved_by = p_manager_user_id,
      approved_at = now(),
      manager_note = coalesce(p_note, manager_note)
  where id = p_request_id;

  update public.leave_balances
  set pending_days = greatest(0, pending_days - v_req.total_days),
      used_days = used_days + v_req.total_days
  where tenant_id = v_req.tenant_id
    and user_id = v_req.user_id
    and leave_type = v_req.leave_type
    and year = extract(year from v_req.start_date)::int;

  insert into public.leave_request_events (tenant_id, request_id, actor_user_id, event_type, notes)
  values (v_req.tenant_id, p_request_id, p_manager_user_id, 'approved', p_note);

  insert into public.audit_logs (tenant_id, user_id, action, target_table, target_id, details)
  values (v_req.tenant_id, p_manager_user_id, 'leave.approve', 'leave_requests', p_request_id,
          jsonb_build_object('total_days', v_req.total_days, 'note', p_note));
end $$;

create or replace function public.reject_leave_request(
  p_request_id uuid,
  p_manager_user_id uuid,
  p_reason text
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_req public.leave_requests%rowtype;
  v_is_admin boolean;
begin
  if p_reason is null or length(trim(p_reason)) = 0 then
    raise exception 'rejection reason is required';
  end if;

  select * into v_req from public.leave_requests where id = p_request_id for update;
  if not found then raise exception 'request not found'; end if;
  if v_req.status <> 'pending' then raise exception 'request is not pending (status=%)', v_req.status; end if;

  select exists (
    select 1 from public.tenant_memberships
    where tenant_id = v_req.tenant_id and user_id = p_manager_user_id and role = 'admin'
  ) into v_is_admin;

  if not v_is_admin and v_req.manager_user_id is distinct from p_manager_user_id then
    raise exception 'manager % is not authorized to reject this request', p_manager_user_id;
  end if;

  update public.leave_requests
  set status = 'rejected',
      rejected_by = p_manager_user_id,
      rejected_at = now(),
      manager_note = p_reason
  where id = p_request_id;

  update public.leave_balances
  set pending_days = greatest(0, pending_days - v_req.total_days)
  where tenant_id = v_req.tenant_id
    and user_id = v_req.user_id
    and leave_type = v_req.leave_type
    and year = extract(year from v_req.start_date)::int;

  insert into public.leave_request_events (tenant_id, request_id, actor_user_id, event_type, notes)
  values (v_req.tenant_id, p_request_id, p_manager_user_id, 'rejected', p_reason);

  insert into public.audit_logs (tenant_id, user_id, action, target_table, target_id, details)
  values (v_req.tenant_id, p_manager_user_id, 'leave.reject', 'leave_requests', p_request_id,
          jsonb_build_object('reason', p_reason));
end $$;

create or replace function public.cancel_leave_request(
  p_request_id uuid,
  p_user_id uuid
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_req public.leave_requests%rowtype;
begin
  select * into v_req from public.leave_requests where id = p_request_id for update;
  if not found then raise exception 'request not found'; end if;
  if v_req.user_id <> p_user_id then raise exception 'only the requester can cancel'; end if;
  if v_req.status <> 'pending' then raise exception 'request is not pending (status=%)', v_req.status; end if;

  update public.leave_requests
  set status = 'cancelled',
      cancelled_at = now()
  where id = p_request_id;

  update public.leave_balances
  set pending_days = greatest(0, pending_days - v_req.total_days)
  where tenant_id = v_req.tenant_id
    and user_id = v_req.user_id
    and leave_type = v_req.leave_type
    and year = extract(year from v_req.start_date)::int;

  insert into public.leave_request_events (tenant_id, request_id, actor_user_id, event_type, notes)
  values (v_req.tenant_id, p_request_id, p_user_id, 'cancelled', null);

  insert into public.audit_logs (tenant_id, user_id, action, target_table, target_id, details)
  values (v_req.tenant_id, p_user_id, 'leave.cancel', 'leave_requests', p_request_id, '{}'::jsonb);
end $$;
