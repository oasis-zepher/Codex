#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
from datetime import date, datetime
from pathlib import Path


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


def render_base_note(project: str, module: str, target_date: date) -> str:
    return "\n".join(
        [
            "---",
            f"date: {target_date.isoformat()}",
            f"project: {project}",
            f"module: {module}",
            "tags:",
            "  - research-diary",
            "  - module-note",
            "---",
            "",
            f"# {target_date.isoformat()} | {project} / {module}",
            "",
            "## 今日目标",
            "- ",
            "",
            "## 模块现状",
            "- ",
            "",
            "## 今日完成",
            "- ",
            "",
            "## 改动文件",
            "- ",
            "",
            "## 关键决策",
            "- ",
            "",
            "## Blockers",
            "- ",
            "",
            "## 下一步",
            "- ",
            "",
        ]
    ) + "\n"


def git_lines(project_root: Path, *args: str) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", project_root.as_posix(), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def module_block(project_root: Path, module: str) -> str:
    worktree = git_lines(project_root, "status", "--short", "--", module)
    commits = git_lines(project_root, "log", "--oneline", "-n5", "--", module)
    diffstat = git_lines(project_root, "diff", "--stat", "--", module)
    lines = [
        "## 模块自动更新",
        f"- project root: `{project_root.as_posix()}`",
        f"- module path: `{module}`",
        "",
        "### 工作区改动",
    ]
    if worktree:
        lines.extend(f"- `{item}`" for item in worktree[:8])
    else:
        lines.append("- 当前工作区没有检测到该模块的未提交改动。")

    lines.extend(["", "### 最近提交"])
    if commits:
        lines.extend(f"- `{item}`" for item in commits)
    else:
        lines.append("- 未检测到最近提交。")

    lines.extend(["", "### Diff Stat"])
    if diffstat:
        lines.extend(f"- {item}" for item in diffstat[:6])
    else:
        lines.append("- 当前没有可用 diff stat。")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Append project/module updates to today's diary note.")
    parser.add_argument("--vault", required=True, type=Path, help="Vault path")
    parser.add_argument("--project-root", required=True, type=Path, help="Project root path")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--module", required=True, help="Module path relative to project root")
    parser.add_argument("--date", default=None, help="YYYY-MM-DD; defaults to today")
    args = parser.parse_args()

    target_date = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else date.today()
    vault = args.vault.expanduser().resolve()
    project_root = args.project_root.expanduser().resolve()
    note = note_path(vault, args.project.strip(), args.module.strip(), target_date)
    note.parent.mkdir(parents=True, exist_ok=True)
    if not note.exists():
        note.write_text(render_base_note(args.project.strip(), args.module.strip(), target_date), encoding="utf-8")

    content = note.read_text(encoding="utf-8")
    marker = "## 模块自动更新"
    content = content.split(marker, 1)[0].rstrip() + "\n\n" if marker in content else content.rstrip() + "\n\n"
    note.write_text(content + module_block(project_root, args.module.strip()) + "\n", encoding="utf-8")
    print(note.as_posix())


if __name__ == "__main__":
    main()
