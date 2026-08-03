#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

bash "$ROOT/scripts/check_demo_env.sh"

echo "Building and starting demo stack (postgres redis api worker web)..."
docker compose up --build -d postgres redis api worker web

echo "Waiting for API health..."
deadline=$((SECONDS + 180))
until curl -fsS "http://127.0.0.1:8000/health" >/dev/null 2>&1; do
  if (( SECONDS >= deadline )); then
    echo "Timed out waiting for API. Check: docker compose logs api worker" >&2
    exit 1
  fi
  sleep 2
done

echo ""
echo "Demo stack is up:"
echo "  Web  http://localhost:3000"
echo "  API  http://localhost:8000/health"
echo ""
echo "Stop with: ./scripts/down.sh"
