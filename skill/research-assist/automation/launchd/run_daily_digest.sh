#!/bin/zsh
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export UV_CACHE_DIR="/tmp/uv-cache"

REPO_ROOT="/Users/zephyr/Bio/Codex/skill/research-assist"
LOG_DIR="$REPO_ROOT/automation/logs"

mkdir -p "$LOG_DIR"
cd "$REPO_ROOT"

printf '[%s] Starting scheduled digest run\n' "$(date '+%Y-%m-%d %H:%M:%S')"
/opt/homebrew/bin/uv run research-assist --action digest --config ./config.json
printf '[%s] Scheduled digest run finished\n' "$(date '+%Y-%m-%d %H:%M:%S')"
