#!/usr/bin/env bash
# scripts/who-is-on-port.sh — show what is listening on common dev ports.
PORTS="3000 8000 9191 5173 8080"
echo "Port scan (LISTEN sockets only):"
for p in $PORTS; do
  out=$(lsof -nP -iTCP:$p -sTCP:LISTEN 2>/dev/null)
  if [ -n "$out" ]; then
    echo "  :$p → $(echo "$out" | tail -n +2 | awk '{print $1, $2, $9}')"
  else
    echo "  :$p → (free)"
  fi
done
