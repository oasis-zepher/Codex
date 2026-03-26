---
name: literature-report-ppt
description: Create Chinese-first literature-report PPT decks for a specific project module, not a generic digest. Use when Codex needs to explain how literature connects to one module inside a project, generate a module-focused PPTX for lab meetings, or turn a project/module brief plus selected papers into an editable presentation deck.
---

# Literature Report PPT

Use this skill when the user wants a literature deck anchored to:

- a project root
- one module, subsystem, feature slice, or research direction inside that project
- a small set of relevant papers that explain or support that module

Do not default to a full daily digest. The module is the center; papers are evidence around that module.

## Default Workflow

1. build a module brief JSON from a project root and module path
2. generate an editable PPTX from that brief

Commands:

```bash
cd ~/Bio/Codex/skill/literature-report-ppt
npm install
python3 scripts/build_module_brief.py \
  --project-root ~/Bio/Codex \
  --module skill/research-assist \
  --role "本地文献检索与摘要流水线" \
  --goal "说明该模块当前能力、缺口，以及需要关注的文献方向" \
  --summary ~/Bio/Codex/skill/research-assist/runtime/reports/<run>.run-summary.json \
  --out /tmp/module-brief.json

node scripts/build_deck.mjs \
  --brief-json /tmp/module-brief.json \
  --out ./output/module-literature-report.pptx
```

## Input Model

Preferred input is `--brief-json`, produced by `scripts/build_module_brief.py`.

The brief should describe:

- project name and root
- module name and relative path
- module role, goal, current state, key files, recent changes, open questions
- selected papers that matter to this module
- why each paper is relevant, what can be borrowed, and what the limitations are

`research-assist` summaries are optional helpers for selecting papers, not the primary framing.

## Output Expectations

The deck should read like a module briefing:

- what this module does in the project
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
