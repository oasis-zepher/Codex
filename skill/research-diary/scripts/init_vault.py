#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "templates"

DIRS = [
    "01 Projects",
    "02 Literature Notes",
    "03 Experiments",
    "05 Meetings",
    "06 Slides",
    "90 Assets",
    "99 Templates",
]


def copy_template(name: str, destination: Path) -> None:
    destination.write_text((TEMPLATE_ROOT / name).read_text(encoding="utf-8"), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize an Obsidian-compatible research diary vault.")
    parser.add_argument("--vault", required=True, type=Path, help="Target vault path")
    args = parser.parse_args()

    vault = args.vault.expanduser().resolve()
    vault.mkdir(parents=True, exist_ok=True)

    for relative in DIRS:
        (vault / relative).mkdir(parents=True, exist_ok=True)

    template_targets = {
        "daily-note.md": vault / "99 Templates" / "daily-note.md",
        "literature-note.md": vault / "99 Templates" / "literature-note.md",
    }
    for template_name, destination in template_targets.items():
        if not destination.exists():
            copy_template(template_name, destination)

    print(vault.as_posix())


if __name__ == "__main__":
    main()
