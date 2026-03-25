# Daily Runner

The canonical local entrypoint is:

```bash
uv run python scripts/skill_runner.py daily --config ./config.json
```

## What `daily` Does

1. run preflight checks
2. ensure runtime directories exist
3. migrate legacy untracked runtime artifacts into `./runtime/` when safe
4. rebuild the local semantic index when semantic search is enabled and available
5. run the normal digest
6. render a Chinese-localized user-facing HTML under `./reports/generated/`

## Preflight Checks

The runner checks:

- `config.json`
- profile path
- runtime output path
- runtime state path
- semantic index directory
- Zotero SQLite path
- local embedding endpoint reachability

## Fallback Ladder

The daily runner should prefer this exact fallback order:

1. normal digest with semantic search
2. digest with semantic search disabled
3. reuse the latest successful run summary and regenerate the Chinese HTML

This keeps the skill deterministic and avoids silent drift between sessions.

The runner should also time-bound both:

- semantic index rebuild
- digest execution

Use config-driven timeout seconds instead of waiting indefinitely on blocked local services or blocked network access.

## Other Subcommands

### `top3`

```bash
uv run python scripts/skill_runner.py top3 --config ./config.json
```

Behavior:

- use the latest successful digest summary
- if no recent digest exists and freshness matters, run `daily` first
- print the top 3 recommendations with DOI / identifier and relevance notes

### `preflight`

```bash
uv run python scripts/skill_runner.py preflight --config ./config.json
```

Use this when debugging local runtime problems before a full digest.

## Output Artifacts

After a successful daily run, the key artifacts are:

- one latest `*.run-summary.json`
- one English digest HTML from the packaged pipeline
- one Chinese-localized `*.zh-CN.html` rendered by `scripts/render_digest_cn.py` under `./reports/generated/`

The Chinese HTML should be treated as the default user-facing deliverable.
