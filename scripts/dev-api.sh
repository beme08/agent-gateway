#!/usr/bin/env bash
# scripts/dev-api.sh — start the FastAPI agent + tool gateway on :8000.
# Creates a venv on first run and installs the API in editable mode.
set -e
cd "$(dirname "$0")/.."
API="apps/api"

if [ ! -d "$API/.venv" ]; then
  echo "→ Creating venv at $API/.venv"
  python3 -m venv "$API/.venv"
fi
# shellcheck disable=SC1091
source "$API/.venv/bin/activate"

if ! python -c "import fastapi" 2>/dev/null; then
  echo "→ Installing API dependencies (this can take 1-2 minutes) …"
  pip install --quiet --upgrade pip
  pip install --quiet -e ".[dev]"
fi

if [ ! -f "$API/.env" ]; then
  echo "✗ Missing $API/.env. Run:  bash scripts/supabase-bootstrap.sh"
  exit 1
fi

echo ""
echo "→ Starting FastAPI on http://localhost:8000"
echo "  (Ctrl-C to stop. Re-run this script any time.)"
echo ""
cd "$API" && exec uvicorn app.main:app --reload --port 8000
