#!/usr/bin/env bash
# scripts/supabase-bootstrap.sh
# Wires .env files for the web and api apps from a Supabase project's
# credentials. Idempotent: if the .env already has real keys, it does nothing.
#
# Usage:
#   bash scripts/supabase-bootstrap.sh
#   bash scripts/supabase-bootstrap.sh --url https://xxx.supabase.co \
#                                     --anon eyJ... \
#                                     --service eyJ... \
#                                     --jwt-secret xxx
#
# Or run without args and answer the prompts.

set -e
cd "$(dirname "$0")/.."

WEB_ENV="apps/web/.env.local"
API_ENV="apps/api/.env"

is_placeholder() {
  # Detect the unedited .env.example (URL is "your-project.supabase.co")
  grep -q "your-project.supabase.co" "$1" 2>/dev/null
}

# -- gather credentials --------------------------------------------------------

if [ "$1" != "--url" ]; then
  echo "→ Supabase project bootstrap"
  echo "  (find these at https://supabase.com/dashboard → your project → Settings → API)"
  echo ""
  read -r -p "  Project URL        : " URL
  read -r -p "  Anon public key    : " ANON
  read -r -s -p "  Service-role key   : " SERVICE; echo
  read -r -s -p "  JWT secret         : " JWT; echo
else
  while [ $# -gt 0 ]; do
    case "$1" in
      --url)         URL="$2"; shift 2 ;;
      --anon)        ANON="$2"; shift 2 ;;
      --service)     SERVICE="$2"; shift 2 ;;
      --jwt-secret)  JWT="$2"; shift 2 ;;
      *) shift ;;
    esac
  done
fi

if [ -z "$URL" ] || [ -z "$ANON" ] || [ -z "$SERVICE" ] || [ -z "$JWT" ]; then
  echo "✗ All four values are required."
  exit 1
fi

# -- write apps/web/.env.local -------------------------------------------------

cat > "$WEB_ENV" <<EENV
NEXT_PUBLIC_SUPABASE_URL=$URL
NEXT_PUBLIC_SUPABASE_ANON_KEY=$ANON
SUPABASE_SERVICE_ROLE_KEY=$SERVICE
AGENT_API_URL=http://localhost:8000
ENABLE_PUBLIC_UPLOAD=false
EENV
echo "✓ wrote $WEB_ENV"

# -- write apps/api/.env -------------------------------------------------------

cat > "$API_ENV" <<EENV
SUPABASE_URL=$URL
SUPABASE_ANON_KEY=$ANON
SUPABASE_SERVICE_ROLE_KEY=$SERVICE
SUPABASE_JWT_SECRET=$JWT
AGENT_API_KEY=local-dev-shared-secret
COHERE_API_KEY=
COHERE_MODEL=command-r-plus
COHERE_EMBED_MODEL=embed-english-v3.0
ENABLE_PUBLIC_UPLOAD=false
LOG_LEVEL=info
EENV
echo "✓ wrote $API_ENV"

# -- write scripts/.env --------------------------------------------------------

cat > "scripts/.env" <<EENV
SUPABASE_URL=$URL
SUPABASE_SERVICE_ROLE_KEY=$SERVICE
EENV
echo "✓ wrote scripts/.env"

echo ""
echo "→ Next steps:"
echo "  1. Open the Supabase SQL editor and run the migrations in this order:"
echo "       supabase/migrations/0001_init.sql"
echo "       supabase/migrations/0002_rls.sql"
echo "       supabase/migrations/0003_leave_functions.sql"
echo "       supabase/migrations/0004_match_chunks.sql"
echo "       supabase/migrations/0005_demo_reset.sql"
echo "       supabase/seed/seed.sql"
echo "  2. From the repo root, install scripts deps and seed users:"
echo "       cd scripts && npm install && npx tsx create_demo_users.ts"
echo "  3. Restart the dev servers:"
echo "       bash scripts/dev.sh                  (web on :3000)"
echo "       bash scripts/dev-api.sh              (api on :8000)"
