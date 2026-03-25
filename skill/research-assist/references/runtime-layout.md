# Runtime Layout

This skill now separates the **skill wrapper surface** from the **runtime artifact surface**.

## Wrapper Surface

Files that define how Codex should invoke the skill:

- `SKILL.md`
- `agents/openai.yaml`
- `scripts/skill_runner.py`
- `scripts/render_digest_cn.py`
- `references/*.md`

These files are the stable control surface for Codex.

## Runtime Surface

Generated or machine-local artifacts should live under `./runtime/` whenever possible:

- `runtime/reports/` — run summaries, retrieval manifests, candidate artifacts, and machine-facing digest outputs
- `runtime/state/` — seen-state or incremental retrieval state
- `runtime/semantic-search/` — local semantic index persistence

User-facing Chinese digest HTML is published to:

- `reports/generated/` — shallow, easy-to-open `digest-*.zh-CN.html` artifacts

The repo-local Python environment stays at `.venv/` because `uv sync` owns that path.

## Config Contract

The local config should point generated artifacts at runtime paths:

- `output_root = ./runtime/reports`
- `retrieval_defaults.state_path = ./runtime/state/arxiv_profile_seen.json`
- `semantic_search.persist_directory = ./runtime/semantic-search`

## Migration Rule

When legacy root-level runtime artifacts still exist:

- prefer migrating them into `runtime/`
- do not move tracked source resources such as `reports/schema/`
- do not rewrite packaged Python source files just to perform the move

The deterministic runner `scripts/skill_runner.py` is allowed to perform this migration for untracked runtime artifacts before a normal daily run.
