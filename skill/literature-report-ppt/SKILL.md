---
name: literature-report-ppt
description: Create Chinese-first literature briefing slide decks and editable PPTX files from research digests, paper metadata JSON, or structured notes. Use when Codex needs to turn `research-assist` run summaries, candidate paper JSON files, or manual paper briefs into lab-meeting slides, journal club decks, or concise literature-report presentations.
---

# Literature Report PPT

Use the local script instead of hand-building slides when the user wants a deck from:

- `research-assist` `*.run-summary.json`
- `research-assist` candidate paper JSON files
- a short manual paper brief that can be converted into the expected JSON fields

## Default Workflow

For a daily literature briefing deck from `research-assist`, run:

```bash
cd ~/Bio/Codex/skill/literature-report-ppt
npm install
node scripts/build_deck.mjs \
  --summary ~/Bio/Codex/skill/research-assist/runtime/reports/<run>.run-summary.json \
  --out ./output/literature-briefing.pptx
```

The script also writes a sibling Markdown outline for quick review.

## Inputs

Choose one input mode:

- `--summary <path>`: preferred; builds an overview slide plus one slide per top paper
- `--paper-json <path>`: single-paper briefing mode

Optional arguments:

- `--top <n>`: number of papers to include from a summary, default `5`
- `--title <text>`: override the deck title
- `--subtitle <text>`: short lab-meeting context line
- `--out <path>`: output `.pptx` path

## Output Expectations

The generated deck should stay pragmatic and lab-facing:

- title slide with date + context
- one overview slide summarizing the top papers
- one paper slide per selected paper
- one final slide with concrete next-step suggestions

Keep the wording compact. Prefer Chinese section labels and plain technical language over promotional prose.

## References

- Read `references/workflow.md` for deck structure, field mapping, and local limitations.

## Boundary Notes

- Prefer the bundled `scripts/build_deck.mjs` over ad hoc slide generation.
- Treat the output as editable PPTX, not a screenshot or static PDF workflow.
- If the user needs heavy brand styling or an existing corporate slide master, ask for the template file and adapt the script.
