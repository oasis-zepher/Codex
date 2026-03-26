# Vault Layout

The vault is organized around projects and modules, not only by date:

- `01 Projects/<project>/<module>/Daily/` — one daily note per day for that module
- `01 Projects/<project>/<module>/Context.md` — stable module context
- `02 Literature Notes/` — per-paper reading notes
- `03 Experiments/` — experiment logs and code runs
- `05 Meetings/` — lab meeting / mentor meeting notes
- `06 Slides/` — links to exported PPTX and talk outlines
- `90 Assets/` — figures or attachments
- `99 Templates/` — Markdown templates used by the scripts

## Daily Note Expectations

Each module daily note should answer:

- what this module was supposed to achieve today
- what code / docs changed
- what decisions were made
- what is currently blocked
- what should happen next

## Automatic Module Update

`append_module_update.py` appends:

- project root and module path
- current worktree changes for that module
- recent commits touching that module

This is scaffolding. The actual reasoning and conclusions should still be written by the agent or user.
