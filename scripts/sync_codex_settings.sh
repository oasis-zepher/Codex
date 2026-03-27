#!/bin/zsh
set -euo pipefail

HOME_CODEX="${HOME}/.codex"
REPO_CODEX="/Users/zephyr/Bio/Codex/.codex"

mkdir -p "${REPO_CODEX}/rules" "${REPO_CODEX}/skills"

if [[ -f "${HOME_CODEX}/config.toml" ]]; then
  cp -f "${HOME_CODEX}/config.toml" "${REPO_CODEX}/config.toml"
fi

if [[ -d "${HOME_CODEX}/rules" ]]; then
  rsync -a --delete "${HOME_CODEX}/rules/" "${REPO_CODEX}/rules/"
fi

while IFS= read -r skill_dir; do
  skill_name="${skill_dir:t}"
  case "${skill_name}" in
    .system|research-assist|research-diary)
      continue
      ;;
  esac

  mkdir -p "${REPO_CODEX}/skills/${skill_name}"
  rsync -a --delete "${HOME_CODEX}/skills/${skill_name}/" "${REPO_CODEX}/skills/${skill_name}/"
done < <(find -L "${HOME_CODEX}/skills" -maxdepth 1 -mindepth 1 -type d | sort)

{
  echo "research-assist -> /Users/zephyr/Bio/Codex/skill/research-assist"
  echo "research-diary -> /Users/zephyr/Bio/Codex/skill/research-diary"
} > "${REPO_CODEX}/skills/local-links.txt"

printf 'Synced Codex settings to %s\n' "${REPO_CODEX}"
