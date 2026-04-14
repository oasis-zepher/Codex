#!/bin/zsh

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: check_codex_balance.sh [--json] [--open]

Checks how Codex CLI is authenticated and prints the official place to view
remaining Codex usage / credits.

Options:
  --json   Print machine-readable JSON
  --open   Open the suggested page(s) on macOS
  -h       Show this help
EOF
}

json_mode=0
open_mode=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json)
      json_mode=1
      shift
      ;;
    --open)
      open_mode=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

login_output="$(codex login status 2>&1 || true)"
login_clean="$(printf '%s\n' "$login_output" | sed '/^WARNING: proceeding, even though we could not update PATH:/d')"

auth_mode="unknown"
summary=""
primary_url=""
secondary_url=""

if printf '%s' "$login_clean" | rg -qi 'Logged in using ChatGPT'; then
  auth_mode="chatgpt"
  summary="No official Codex CLI/API currently exposes remaining ChatGPT Codex balance as a number. View it in Codex Settings -> Usage Dashboard."
  primary_url="https://chatgpt.com/codex"
  secondary_url="https://help.openai.com/en/articles/12642688-using-credits-for-flexible-usage-in-chatgpt-freegopluspro-sora"
elif printf '%s' "$login_clean" | rg -qi 'API key|OPENAI_API_KEY'; then
  auth_mode="api_key"
  summary="API-backed usage is tracked in the OpenAI platform dashboard."
  primary_url="https://platform.openai.com/usage"
  secondary_url="https://platform.openai.com/settings/organization/billing/credit-grants"
elif printf '%s' "$login_clean" | rg -qi 'Not logged in|logged out|No active login'; then
  auth_mode="logged_out"
  summary="Codex CLI is not logged in. If you use ChatGPT billing, sign in and then check Codex Settings -> Usage Dashboard. If you use API billing, check the platform usage dashboard."
  primary_url="https://chatgpt.com/codex"
  secondary_url="https://platform.openai.com/usage"
else
  auth_mode="unknown"
  summary="Could not determine the billing mode from codex login status. Check ChatGPT Codex Usage Dashboard for subscription usage, or the OpenAI platform dashboard for API usage."
  primary_url="https://chatgpt.com/codex"
  secondary_url="https://platform.openai.com/usage"
fi

if [[ "$json_mode" -eq 1 ]]; then
  printf '{\n'
  printf '  "auth_mode": "%s",\n' "$auth_mode"
  printf '  "supports_direct_numeric_query": false,\n'
  printf '  "summary": "%s",\n' "$summary"
  printf '  "primary_url": "%s",\n' "$primary_url"
  printf '  "secondary_url": "%s"\n' "$secondary_url"
  printf '}\n'
else
  printf 'Auth mode: %s\n' "$auth_mode"
  printf '%s\n' "$summary"
  printf 'Primary: %s\n' "$primary_url"
  printf 'Secondary: %s\n' "$secondary_url"
fi

if [[ "$open_mode" -eq 1 ]]; then
  open "$primary_url"
  open "$secondary_url"
fi
