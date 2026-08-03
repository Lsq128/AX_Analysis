#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "${1:-}" == "--volumes" ]]; then
  docker compose down --volumes
  echo "Stopped stack and removed volumes."
else
  docker compose down
  echo "Stopped stack (volumes kept). Use ./scripts/down.sh --volumes to wipe data."
fi
