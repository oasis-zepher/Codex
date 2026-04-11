#!/usr/bin/env bash

set -euo pipefail

SITE="${1:-}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -z "$SITE" ]]; then
  cat <<'EOF'
Usage:
  ./scripts/use_design_md.sh <site>

Examples:
  ./scripts/use_design_md.sh vercel
  ./scripts/use_design_md.sh voltagent
  ./scripts/use_design_md.sh ollama

This command replaces the root DESIGN.md using the official getdesign CLI.
EOF
  exit 1
fi

cd "$PROJECT_ROOT"

if [[ -f DESIGN.md ]]; then
  cp DESIGN.md "DESIGN.md.bak.$(date +%Y%m%d%H%M%S)"
fi

npx getdesign@latest add "$SITE"

echo "Updated DESIGN.md with preset: $SITE"
