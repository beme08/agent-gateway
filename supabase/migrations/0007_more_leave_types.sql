-- 0007_more_leave_types.sql
-- Add pto, bereavement, parental, jury, unpaid to leave_policies and seed
-- leave_balances for the existing demo employees. This makes the
-- "Take time off" form useful for the broader set of reasons the
-- public demo promises (vacation, PTO, sick, bereavement, personal,
-- parental, jury duty, unpaid).

insert into public.leave_policies (tenant_id, leave_type, annual_allocation, requires_approval) values
  ('11111111-1111-1111-1111-111111111111', 'pto',         8, true),
  ('11111111-1111-1111-1111-111111111111', 'bereavement', 5, true),
  ('11111111-1111-1111-1111-111111111111', 'parental',   60, true),
  ('11111111-1111-1111-1111-111111111111', 'jury',        5, true),
  ('11111111-1111-1111-1111-111111111111', 'unpaid',     30, true),
  ('22222222-2222-2222-2222-222222222222', 'pto',         8, true),
  ('22222222-2222-2222-2222-222222222222', 'bereavement', 5, true),
  ('22222222-2222-2222-2222-222222222222', 'parental',   60, true),
  ('22222222-2222-2222-2222-222222222222', 'jury',        5, true),
  ('22222222-2222-2222-2222-222222222222', 'unpaid',     30, true)
on conflict do nothing;

-- Seed leave_balances for the two employee users in each tenant, for the
-- current year, for each of the new leave types. Uses the same per-tenant
-- annual allocation as the policy so remaining_days = allocated initially.
do $$
declare
  yr int := date_part('year', now());
  u  record;
begin
  for u in
    select m.user_id, m.tenant_id, p.leave_type, p.annual_allocation
    from public.tenant_memberships m
    join public.leave_policies p
      on p.tenant_id = m.tenant_id
    where m.role = 'employee'
      and p.leave_type in ('pto','bereavement','parental','jury','unpaid')
  loop
    insert into public.leave_balances
      (tenant_id, user_id, leave_type, year, allocated_days, used_days, pending_days)
    values
      (u.tenant_id, u.user_id, u.leave_type, yr, u.annual_allocation, 0, 0)
    on conflict (tenant_id, user_id, leave_type, year) do nothing;
  end loop;
end $$;
