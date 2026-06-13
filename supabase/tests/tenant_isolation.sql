-- tenant_isolation.sql — manual regression test for RLS.
-- Run this in the Supabase SQL editor AFTER create_demo_users.ts has run and
-- the seed has been applied. The script sets up two synthetic users via
-- the auth.users table and asserts they cannot see each other's tenant rows.

-- This test is a reference implementation; full CI coverage lives in
-- apps/api/app/tests/test_rls.py once the API is wired up.

begin;

-- Reset any prior run
delete from auth.users where email in ('rls-tester-a@acme.test', 'rls-tester-b@globex.test');

-- Two synthetic users
insert into auth.users (id, email, raw_user_meta_data, role) values
  ('99999999-9999-9999-9999-99999999999a', 'rls-tester-a@acme.test', '{}'::jsonb, 'authenticated'),
  ('99999999-9999-9999-9999-99999999999b', 'rls-tester-b@globex.test', '{}'::jsonb, 'authenticated')
on conflict (id) do nothing;

insert into public.users (id, email) values
  ('99999999-9999-9999-9999-99999999999a', 'rls-tester-a@acme.test'),
  ('99999999-9999-9999-9999-99999999999b', 'rls-tester-b@globex.test')
on conflict (id) do nothing;

insert into public.tenant_memberships (tenant_id, user_id, role) values
  ('11111111-1111-1111-1111-111111111111', '99999999-9999-9999-9999-99999999999a', 'admin'),
  ('22222222-2222-2222-2222-222222222222', '99999999-9999-9999-9999-99999999999b', 'admin')
on conflict do nothing;

-- Simulate user A's session and try to read Globex tenant
set local role authenticated;
set local request.jwt.claim.sub to '99999999-9999-9999-9999-99999999999a';
set local role authenticated;

-- Acme admin SHOULD be able to see Acme tenant
do $$
declare
  v_count int;
begin
  select count(*) into v_count from public.tenants where slug = 'acme';
  if v_count = 0 then raise exception 'FAIL: Acme admin could not see Acme tenant'; end if;
  raise notice 'PASS: Acme admin sees Acme tenant';
end $$;

-- Acme admin should NOT be able to see Globex tenant
do $$
declare
  v_count int;
begin
  select count(*) into v_count from public.tenants where slug = 'globex';
  if v_count <> 0 then raise exception 'FAIL: Acme admin could see Globex tenant (count=%)', v_count; end if;
  raise notice 'PASS: Acme admin cannot see Globex tenant';
end $$;

rollback;
