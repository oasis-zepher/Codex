# Codex Settings Mirror

This directory stores a repository-side copy of the Codex settings that matter for repeatable setup.

Included:
- `config.toml`
- `rules/`
- third-party installed skills from `~/.codex/skills/`

Excluded:
- authentication and credentials
- chat history and sessions
- logs, caches, sqlite state, shell snapshots
- local project skills that already live in `/Users/zephyr/Bio/Codex/skill/`

Refresh this mirror with:

```sh
/Users/zephyr/Bio/Codex/scripts/sync_codex_settings.sh
```
