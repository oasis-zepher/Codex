# Design.md Setup

This repository has been configured to use `DESIGN.md` in the project root.

## What Was Added

- `DESIGN.md`
  - Active default preset: `vercel`
- `awesome-design-md/`
  - Local clone of the upstream index repository
- `design-presets/`
  - Local backup of all currently downloadable presets
- `scripts/use_design_md.sh`
  - Helper script to switch the root `DESIGN.md` preset
- `scripts/fetch_all_design_presets.sh`
  - Helper script to refresh the full local preset archive
- `scripts/generate_design_previews.py`
  - Generates a `preview.svg` for each preset plus a gallery page

## How To Use

Ask your coding agent to read `DESIGN.md` before generating UI.

Example prompts:

- `Read DESIGN.md and build the landing page in that style.`
- `Use DESIGN.md as the visual system for this dashboard.`
- `Keep the existing behavior, but restyle the page to match DESIGN.md.`

## Switch To Another Preset

Run:

```bash
./scripts/use_design_md.sh vercel
./scripts/use_design_md.sh voltagent
./scripts/use_design_md.sh ollama
```

The script keeps a timestamped backup like `DESIGN.md.bak.20260412153000` before replacing the active file.

## Refresh The Full Local Archive

Run:

```bash
./scripts/fetch_all_design_presets.sh
```

This saves every currently available preset under `design-presets/<site>/DESIGN.md`.
Use those files as your offline backup if the upstream index repo or website changes later.
It also regenerates:

- `design-presets/<site>/preview.svg`
- `design-presets/index.html`

## Notes About The Upstream Repo

The upstream `awesome-design-md` repository is now mainly an index of available presets.
The actual `DESIGN.md` content is delivered by the official `getdesign` CLI and `getdesign.md`.
