#!/usr/bin/env bash
# Preflight for demo docker one-click: require .env + one LLM key.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${AX_ENV_FILE:-$ROOT/.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  echo "Run: cp .env.example .env  # then fill at least one LLM API key" >&2
  exit 1
fi

get_key() {
  local name="$1"
  # last assignment wins; strip export, quotes, CR
  local line
  line="$(grep -E "^[[:space:]]*(export[[:space:]]+)?${name}=" "$ENV_FILE" | tail -n 1 || true)"
  [[ -z "$line" ]] && { echo ""; return; }
  local val="${line#*=}"
  val="${val%$'\r'}"
  val="${val#\"}"
  val="${val%\"}"
  val="${val#\'}"
  val="${val%\'}"
  # trim whitespace
  val="$(printf '%s' "$val" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  printf '%s' "$val"
}

if [[ -z "$(get_key DEEPSEEK_API_KEY)" \
   && -z "$(get_key DASHSCOPE_CN_API_KEY)" \
   && -z "$(get_key MOONSHOT_API_KEY)" ]]; then
  echo "No LLM API key found in $ENV_FILE" >&2
  echo "Set at least one of: DEEPSEEK_API_KEY, DASHSCOPE_CN_API_KEY, MOONSHOT_API_KEY" >&2
  exit 1
fi

exit 0
