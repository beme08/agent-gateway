#!/usr/bin/env bash
# scripts/dev.sh — one-shot local dev launcher.
# Installs web deps (idempotent), starts the Next.js dev server on :3000,
# and prints clear next steps. Safe to re-run.

set -e
cd "$(dirname "$0")/.."
WEB="apps/web"

echo "→ Checking $WEB/node_modules/next …"
if [ ! -f "$WEB/node_modules/next/package.json" ]; then
  echo "→ Installing web dependencies (this can take 1-3 minutes) …"
  if command -v npm >/dev/null 2>&1; then
    (cd "$WEB" && npm install --no-audit --no-fund)
  elif command -v yarn >/dev/null 2>&1; then
    (cd "$WEB" && yarn install)
  elif command -v pnpm >/dev/null 2>&1; then
    (cd "$WEB" && pnpm install)
  else
    echo "✗ No package manager found. Install Node 18+ from https://nodejs.org"
    exit 1
  fi
else
  echo "✓ node_modules already present"
fi

echo ""
echo "→ Starting Next.js dev server on http://localhost:3000"
echo "  (Ctrl-C to stop. Re-run this script any time.)"
echo ""
cd "$WEB" && npm run dev
