#!/usr/bin/env python3

from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
DAILY_TEMPLATE = SKILL_ROOT / "assets" / "templates" / "daily-note.md"


def note_path(vault: Path, project: str, module: str, target_date: date) -> Path:
    return (
        vault
        / "01 Projects"
        / project
        / module.replace("/", "__")
        / "Daily"
        / target_date.strftime("%Y")
        / target_date.strftime("%Y-%m")
        / f"{target_date.isoformat()}.md"
    )


def render_template(project: str, module: str, target_date: date) -> str:
    content = DAILY_TEMPLATE.read_text(encoding="utf-8")
    return (
        content.replace("{{date}}", target_date.isoformat())
        .replace("{{project}}", project)
        .replace("{{module}}", module)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Create today's project/module research diary note.")
    parser.add_argument("--vault", required=True, type=Path, help="Vault path")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--module", required=True, help="Module name or relative path")
    parser.add_argument("--date", default=None, help="YYYY-MM-DD; defaults to today")
    args = parser.parse_args()

    target_date = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else date.today()
    vault = args.vault.expanduser().resolve()
    daily_note = note_path(vault, args.project.strip(), args.module.strip(), target_date)
    daily_note.parent.mkdir(parents=True, exist_ok=True)

    if not daily_note.exists():
        daily_note.write_text(render_template(args.project.strip(), args.module.strip(), target_date), encoding="utf-8")

    print(daily_note.as_posix())


if __name__ == "__main__":
    main()
