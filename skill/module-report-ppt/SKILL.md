---
name: module-report-ppt
description: Create Chinese-first module-report PPT decks and editable PPTX files for a specific project area. Use when the user asks for a 模块汇报, 模块相关性分析, PartA/PartB 汇报 PPT, or wants slides explaining one module's role, supporting literature, current gaps, and next steps inside a project.
---

# Module Report PPT

Use this skill when the user wants a module deck anchored to:

- a project root
- one module, subsystem, feature slice, or research direction inside that project
- one analysis scope such as `模块相关性分析`, `PartA`, or `PartB`

Do not default to a generic literature digest. The module is the center; papers are evidence around that module.

## Default Workflow

1. build a module brief JSON from a project root and module path
2. generate an editable PPTX from that brief

Commands:

```bash
cd ~/Bio/Codex/skill/module-report-ppt
npm install
python3 scripts/build_module_brief.py \
  --project-root ~/Bio/Codex \
  --module skill/research-assist \
  --analysis-title "模块相关性分析" \
  --part "PartB" \
  --role "本地文献检索与摘要流水线" \
  --goal "说明该模块当前能力、缺口，以及需要关注的文献方向" \
  --summary ~/Bio/Codex/skill/research-assist/runtime/reports/<run>.run-summary.json \
  --out /tmp/module-brief.json

node scripts/build_deck.mjs \
  --brief-json /tmp/module-brief.json \
  --out ./output/module-report-partb.pptx
```

## Input Model

Preferred input is `--brief-json`, produced by `scripts/build_module_brief.py`.

The brief should describe:

- project name and root
- module name and relative path
- analysis title and optional `PartA` / `PartB`
- module role, goal, current state, key files, recent changes, open questions
- selected papers that matter to this module
- why each paper is relevant, what can be borrowed, and what the limitations are

`research-assist` summaries are optional helpers for selecting papers, not the primary framing.

## Output Expectations

The deck should read like a module briefing:

- what this module does in the project
- which analysis slice this deck belongs to, such as `模块相关性分析 PartB`
- why literature matters for this module now
- which papers are worth discussing
- what those papers imply for implementation or next steps

Keep the language concise and technical. Prefer Chinese slide labels and lab-meeting phrasing over generic business presentation language.

## References

- Read `references/workflow.md` for the brief schema and deck layout.

## Boundary Notes

- Prefer the bundled scripts over manually assembling slides.
- Treat `.pptx` as the main deliverable; write a Markdown outline as a secondary artifact.
- If the user already has a project brief JSON, skip scanning and build the deck directly from it.
