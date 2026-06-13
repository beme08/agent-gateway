#!/usr/bin/env bash
# scripts/setup-supabase-mcp.sh
# Registers the Supabase MCP server with Codex and walks you through OAuth.
# Run this in your terminal (not from inside Codex's sandbox).
#
# After it succeeds, type /mcp in Codex to verify, and the Supabase tools
# (list_tables, execute_sql, apply_migration, etc.) will appear.

set -e

PROJECT_REF="dabksbszhwqnpglattvb"
FEATURES="docs%2Caccount%2Cdatabase%2Cdebugging%2Cdevelopment%2Cfunctions%2Cbranching"
URL="https://mcp.supabase.com/mcp?project_ref=${PROJECT_REF}&features=${FEATURES}"

echo "→ Registering Supabase MCP server with Codex …"
if codex mcp add supabase --url "$URL"; then
  echo "✓ Registered."
else
  echo "✗ codex mcp add failed. Make sure codex CLI is on PATH and ~/.codex/ is writable by you."
  exit 1
fi

echo ""
echo "→ Authenticating (opens your browser to grant Codex access to your Supabase project) …"
codex mcp login supabase
echo "✓ Login flow launched. Complete the OAuth consent in the browser."

echo ""
echo "→ Verifying …"
echo "  In Codex, type:  /mcp"
echo "  You should see 'supabase' listed as authenticated with the project ref above."
