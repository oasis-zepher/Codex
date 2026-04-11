#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_ROOT="$PROJECT_ROOT/awesome-design-md/design-md"
OUTPUT_ROOT="$PROJECT_ROOT/design-presets"
TMP_ROOT="${TMPDIR:-/tmp}/codex-design-presets"
FAILURES_FILE="$OUTPUT_ROOT/_failures.txt"
PREVIEW_SCRIPT="$PROJECT_ROOT/scripts/generate_design_previews.py"

if [[ ! -d "$SOURCE_ROOT" ]]; then
  echo "Missing source directory: $SOURCE_ROOT" >&2
  exit 1
fi

mkdir -p "$OUTPUT_ROOT"
mkdir -p "$TMP_ROOT"

get_cli_sites() {
  local output

  if ! output="$(cd "$TMP_ROOT" && npx getdesign@latest add __codex_invalid__ 2>&1 || true)"; then
    return 1
  fi

  printf '%s\n' "$output" | awk '
    /^Available brands:/ {
      sub(/^Available brands: /, "", $0)
      gsub(/, /, "\n", $0)
      print
    }
  '
}

SITES_RAW="$(get_cli_sites)"

if [[ -z "$SITES_RAW" ]]; then
  SITES_RAW="$(find "$SOURCE_ROOT" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort)"
fi

if [[ -z "$SITES_RAW" ]]; then
  echo "No presets found under $SOURCE_ROOT" >&2
  exit 1
fi

site_count=0
failure_count=0

: > "$FAILURES_FILE"

while IFS= read -r site; do
  [[ -z "$site" ]] && continue
  site_count=$((site_count + 1))
  workdir="$TMP_ROOT/$site"
  target_dir="$OUTPUT_ROOT/$site"

  rm -rf "$workdir"
  mkdir -p "$workdir" "$target_dir"

  if ! (
    cd "$workdir"
    npx getdesign@latest add "$site" >/dev/null
  ); then
    failure_count=$((failure_count + 1))
    echo "$site" >> "$FAILURES_FILE"
    rm -rf "$target_dir"
    echo "Failed $site"
    continue
  fi

  cp "$workdir/DESIGN.md" "$target_dir/DESIGN.md"
  printf '%s\n' "$site" > "$target_dir/site.txt"
  echo "Saved $site -> $target_dir/DESIGN.md"
done <<EOF
$SITES_RAW
EOF

if [[ "$failure_count" -eq 0 ]]; then
  rm -f "$FAILURES_FILE"
fi

if [[ -f "$PREVIEW_SCRIPT" ]]; then
  python3 "$PREVIEW_SCRIPT"
fi

echo "Fetched $site_count design presets into $OUTPUT_ROOT"
echo "Failures: $failure_count"
