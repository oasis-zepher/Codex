# Workflow

## Main Use Case

Build a literature-report deck for one module inside a project:

```bash
python3 scripts/build_module_brief.py \
  --project-root ~/Bio/Codex \
  --module skill/research-assist \
  --role "本地文献检索与摘要流水线" \
  --goal "说明当前模块能力与文献方向" \
  --out /tmp/module-brief.json

node scripts/build_deck.mjs \
  --brief-json /tmp/module-brief.json \
  --out ./output/module-literature-report.pptx
```

## Brief Schema

The JSON brief should contain these top-level objects:

- `project`
  - `name`
  - `root`
- `module`
  - `name`
  - `path`
  - `role`
  - `goal`
  - `current_state`
  - `key_files[]`
  - `recent_commits[]`
  - `worktree_changes[]`
  - `open_questions[]`
- `literature`
  - `theme`
  - `papers[]`

Each paper should have:

- `title`
- `authors`
- `year`
- `url`
- `takeaway`
- `relevance_to_module`
- `limitations`
- `next_use`

## Deck Layout

The bundled script generates:

1. title slide
2. project/module context
3. why literature matters for the module now
4. one slide per selected paper
5. implementation next steps

## Local Limitations

- The current environment can generate `.pptx` files.
- It does not currently have `soffice` or `pdftoppm`, so full render QA is limited.
- Keep slide density conservative and use short bullet items.
