---
name: research-assist
description: Use for local Zotero-driven literature retrieval, semantic-index-backed daily digests, Chinese HTML digest delivery, and non-destructive Zotero feedback planning in the local macOS Bio workspace.
---

# Research Assist

Use this skill when the user wants any of the following:

- a local Zotero-driven literature search
- a semantic-index-backed daily digest
- a Chinese HTML digest report
- a top-3 paper recommendation based on the latest local digest
- a non-destructive Zotero feedback plan

Do not use this skill for unrelated coding, generic writing, or non-literature tasks.

## Runtime Snapshot

- repo root: `~/Bio/Codex/skill/research-assist`
- config: `./config.json`
- environment: repo-local `.venv/` managed by `uv sync`
- runtime artifacts: `./runtime/`

Do not assume `~/.openclaw/...` global deployment paths for this local setup.

## Default Entry

For `$research-assist` or `$research-assist daily`, do not manually reconstruct the workflow.
Run the deterministic runner instead:

```bash
uv run python scripts/skill_runner.py daily --config ./config.json
```

That runner is the canonical local path for:

1. preflight
2. semantic-index rebuild
3. digest execution
4. fallback handling
5. Chinese HTML generation

Treat the generated `*.zh-CN.html` file as the default user-facing deliverable.

## Quick Options

### Main Pick

- `$research-assist`
- `$research-assist daily`

Both mean: run the deterministic daily runner.

### Extra Picks

- `$research-assist top3`
  Use:
  ```bash
  uv run python scripts/skill_runner.py top3 --config ./config.json
  ```

- `$research-assist feedback`
  Prepare a dry-run Zotero feedback plan. Use the bundled MCP and always keep the first pass non-destructive.

## Hard Rules

- Prefer `scripts/skill_runner.py` over hand-assembled shell chains.
- Prefer the existing `./config.json`; do not reopen setup unless config is missing or broken.
- Keep daily output generation in the scripts layer; do not edit packaged Python source files just to localize the digest.
- Keep Zotero writeback dry-run first, then ask before any real apply.
- Use runtime paths under `./runtime/` for generated artifacts whenever possible.

## Fallback Policy

The runner should prefer this exact order:

1. normal digest with semantic search
2. retry with semantic search disabled
3. reuse the latest successful run summary and regenerate the Chinese HTML

If all three fail, report the failure clearly instead of silently improvising.

## Reference Routing

Read only what the current task needs:

- `references/daily-runner.md`
  Read for `daily`, `top3`, preflight, fallback, or artifact-path questions.

- `references/runtime-layout.md`
  Read for wrapper-vs-runtime separation, path cleanup, and config path conventions.

- `references/setup-routing.md`
  Read only for installation, config repair, or reconfiguration.

- `references/workflow.md`
  Read for stage order and controller boundary.

- `references/review-generation.md`
  Read for digest card wording, review patch expectations, and fallback review behavior.

- `references/profile-map-generation.md`
  Read when the task is about rebuilding or refining the research-interest map itself.

- `references/zotero-mcp.md`
  Read for live Zotero reads or semantic-search operations.

- `references/zotero-feedback.md`
  Read for dry-run feedback planning and allowed writeback actions.

## Boundary Notes

- `daily` and `top3` should stay deterministic and script-driven.
- `feedback` stays read/plan first and write later only with explicit confirmation.
- Search, digest, semantic ranking, and Chinese HTML delivery belong to this skill.
- General frontend edits, repo refactors unrelated to literature workflow, and unrelated automation do not.
