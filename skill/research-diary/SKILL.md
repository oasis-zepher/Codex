---
name: research-diary
description: Create and maintain a Chinese-first daily research diary in an Obsidian-compatible vault. Use when Codex needs to initialize a local research vault, create today's diary page, append `research-assist` digest highlights, or keep structured records of papers, experiments, blockers, and next steps.
---

# Research Diary

Use this skill for local Markdown-based research journaling, especially when the user wants:

- today's scientific worklog
- a reusable Obsidian vault layout
- automatic diary entries from `research-assist` outputs
- a daily note that is easy to reuse for weekly reports or slide preparation

## Default Workflow

1. initialize the vault once
2. create today's note
3. append today's digest highlights when available

Commands:

```bash
cd ~/Bio/Codex/skill/research-diary
python3 scripts/init_vault.py --vault ~/Bio/Research-Diary
python3 scripts/new_daily_note.py --vault ~/Bio/Research-Diary
python3 scripts/append_digest_entry.py --vault ~/Bio/Research-Diary
```

## References

- Read `references/vault-layout.md` for the directory design and note conventions.

## Boundary Notes

- Keep everything plain Markdown and Obsidian-compatible.
- Do not require the Obsidian GUI to create or update notes.
- Prefer concise, structured entries over long narrative diary text.
