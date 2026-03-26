---
name: research-diary
description: Create and maintain a Chinese-first daily research diary for one project module in an Obsidian-compatible vault. Use when the user asks to `生成我的今日日记`, `记录今天这个模块做了什么`, `写一下今天 PartB 的工作日志`, or needs a module-scoped Markdown diary with today's changes, decisions, blockers, and next steps.
---

# Research Diary

Use this skill when the user wants a diary entry for:

- one project
- one module / subsystem / feature slice
- what was done today on that module
- natural prompts like `生成我的今日日记` or `记录今天这个模块做了什么`

Do not default to generic digest notes. The diary should answer: what changed in this module today, why, and what comes next.

If the module is already clear from the thread or current code context, use it directly. Only ask the user when the active module is genuinely ambiguous.

## Default Workflow

1. initialize the vault once
2. create a daily note for one project module
3. append module updates from the codebase

Commands:

```bash
cd ~/Bio/Codex/skill/research-diary
python3 scripts/init_vault.py --vault ~/Bio/Research-Diary
python3 scripts/new_daily_note.py \
  --vault ~/Bio/Research-Diary \
  --project Codex \
  --module skill/research-assist

python3 scripts/append_module_update.py \
  --vault ~/Bio/Research-Diary \
  --project-root ~/Bio/Codex \
  --project Codex \
  --module skill/research-assist
```

## References

- Read `references/vault-layout.md` for the project/module note layout and expected sections.

## Boundary Notes

- Keep everything plain Markdown and Obsidian-compatible.
- Prefer module-scoped daily notes over a single global diary page.
- Record concrete work: touched files, decisions, blockers, next steps.
