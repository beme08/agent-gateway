#!/usr/bin/env bash
# scripts/seed_remote.sh
# Paste the contents of each migration and seed file into your Supabase
# project's SQL editor in this order. This script is a helper that prints
# instructions; we don't open a network connection.

set -euo pipefail
cat <<'NOTE'
Apply the following files in the Supabase SQL editor, in this order:

  1. supabase/migrations/0001_init.sql
  2. supabase/migrations/0002_rls.sql
  3. supabase/migrations/0003_leave_functions.sql
  4. supabase/migrations/0004_match_chunks.sql
  5. supabase/migrations/0005_demo_reset.sql
  6. supabase/seed/seed.sql
  7. supabase/tests/tenant_isolation.sql  (manual verification, end with ROLLBACK)

Then run scripts/create_demo_users.ts locally to create the 10 auth users.
NOTE
