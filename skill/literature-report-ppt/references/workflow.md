# Workflow

## Main Use Case

Build a lab-meeting deck from a `research-assist` run summary:

```bash
node scripts/build_deck.mjs \
  --summary ~/Bio/Codex/skill/research-assist/runtime/reports/<run>.run-summary.json \
  --out ./output/literature-briefing.pptx
```

## Slide Structure

The bundled script generates:

1. title slide
2. daily overview slide
3. one slide per selected paper
4. final action slide

## Summary Field Mapping

When the input is a `research-assist` run summary:

- `artifacts.candidate_paths[]` -> selected paper JSON files
- `paper.title` -> slide title
- `paper.authors`, `paper.year`, `paper.identifiers` -> citation row
- `review.recommendation` -> badge / priority
- `review.why_it_matters` -> why relevant block
- `review.quick_takeaways[]` -> bullet list
- `review.caveats[]` -> risk / caveat block
- `triage.matched_interest_labels[]` -> topic tags

## Local Limitations

- The current environment can generate `.pptx` files, but does not have `soffice` or `pdftoppm`.
- That means the skill can create editable slides, but cannot fully render-check PDF exports or pixel previews locally.
- Keep layouts conservative enough to survive small font fallback differences.
