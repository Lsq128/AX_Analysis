#!/usr/bin/env bash
# Local dev: Postgres + Redis + API + Worker + Web
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export DATABASE_URL="${DATABASE_URL:-postgresql://ax:ax@localhost:5432/ax_analysis}"

if [[ "${1:-}" == "--memory" ]]; then
  unset DATABASE_URL
  export AX_JOB_STORE=memory
  echo "Memory job store (no Postgres)"
  shift
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  export AX_JOB_STORE="${AX_JOB_STORE:-memory}"
else
  docker compose up -d postgres redis
  echo "Postgres: ${DATABASE_URL}"
  echo "Redis: ${REDIS_URL}"
fi

if [[ "${AX_JOB_STORE:-redis}" != "memory" ]]; then
  docker compose up -d redis 2>/dev/null || true
fi

if [[ ! -x .venv/bin/ax-api ]]; then
  echo "Run: python -m venv .venv && .venv/bin/pip install -e '.[dev]'"
  exit 1
fi

case "${1:-}" in
  web)
    cd apps/web && npm install && npm run dev
    ;;
  *)
    echo "Start services in separate terminals:"
    echo "  .venv/bin/ax-worker"
    echo "  .venv/bin/ax-api"
    echo "  ./scripts/dev_stack.sh web"
    ;;
esac
