#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


TEXT_EXTENSIONS = {".md", ".txt", ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".toml", ".yaml", ".yml"}


def compact(text: str, limit: int = 240) -> str:
    normalized = " ".join(str(text or "").split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_first_paragraph(module_dir: Path) -> str:
    for candidate in (module_dir / "README.md", module_dir / "README.zh-CN.md", module_dir / "SKILL.md"):
        if candidate.exists():
            text = candidate.read_text(encoding="utf-8", errors="ignore")
            blocks = [block.strip() for block in text.split("\n\n") if block.strip()]
            for block in blocks:
                if block.startswith("#") or block.startswith("---") or block.startswith("|") or block.startswith(">"):
                    continue
                cleaned = re.sub(r"<[^>]+>", " ", block)
                cleaned = re.sub(r"\s+", " ", cleaned).strip(" -")
                if len(cleaned) >= 20:
                    return compact(cleaned, limit=260)
    return ""


def list_key_files(module_dir: Path, limit: int = 8) -> list[str]:
    files: list[Path] = []
    for path in module_dir.rglob("*"):
        relative = path.relative_to(module_dir) if path.exists() else path
        if any(part.startswith(".") for part in relative.parts):
            continue
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS and ".git" not in path.parts:
            files.append(path)
    files.sort(key=lambda item: (len(item.relative_to(module_dir).parts), item.as_posix()))
    return [path.relative_to(module_dir).as_posix() for path in files[:limit]]


def git_lines(project_root: Path, *args: str) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "-C", project_root.as_posix(), *args],
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return []
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def recent_commits(project_root: Path, module_rel: str, limit: int = 5) -> list[str]:
    return git_lines(project_root, "log", "--oneline", f"-n{limit}", "--", module_rel)


def worktree_changes(project_root: Path, module_rel: str) -> list[str]:
    return git_lines(project_root, "status", "--short", "--", module_rel)


def summary_papers(summary_path: Path, top_n: int) -> list[dict[str, Any]]:
    summary = read_json(summary_path)
    papers: list[dict[str, Any]] = []
    for candidate_path in list(summary.get("artifacts", {}).get("candidate_paths") or [])[:top_n]:
        candidate = read_json(Path(candidate_path))
        paper = candidate.get("paper", {})
        review = candidate.get("review", {})
        papers.append(
            {
                "title": str(paper.get("title") or "Untitled"),
                "authors": list(paper.get("authors") or []),
                "year": paper.get("year"),
                "url": str((paper.get("identifiers") or {}).get("url") or (paper.get("source_links") or [""])[0] or ""),
                "takeaway": compact("；".join(str(item) for item in list(review.get("quick_takeaways") or [])[:3]) or review.get("reviewer_summary") or ""),
                "relevance_to_module": compact(str(review.get("why_it_matters") or review.get("reviewer_summary") or "")),
                "limitations": compact("；".join(str(item) for item in list(review.get("caveats") or [])[:3])),
                "next_use": compact(str(review.get("why_it_matters") or "")),
            }
        )
    return papers


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a project/module-centric literature brief JSON.")
    parser.add_argument("--project-root", required=True, type=Path, help="Project root directory")
    parser.add_argument("--module", required=True, help="Module path relative to project root")
    parser.add_argument("--project-name", default=None, help="Optional override for project name")
    parser.add_argument("--module-name", default=None, help="Optional override for module name")
    parser.add_argument("--analysis-title", default="模块汇报", help="Analysis title, e.g. 模块相关性分析")
    parser.add_argument("--part", default="", help="Optional section label such as PartA or PartB")
    parser.add_argument("--role", default="", help="Role of this module inside the project")
    parser.add_argument("--goal", default="", help="What this literature report should help answer")
    parser.add_argument("--theme", default="", help="Literature theme for this module")
    parser.add_argument("--question", action="append", default=[], help="Open question; repeatable")
    parser.add_argument("--summary", type=Path, default=None, help="Optional research-assist run summary to source candidate papers")
    parser.add_argument("--top", type=int, default=4, help="Top papers to include from summary")
    parser.add_argument("--out", type=Path, required=True, help="Output JSON path")
    args = parser.parse_args()

    project_root = args.project_root.expanduser().resolve()
    module_rel = args.module.strip().strip("/")
    module_dir = (project_root / module_rel).resolve()
    if not module_dir.exists():
        raise SystemExit(f"Module path does not exist: {module_dir}")

    brief = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project": {
            "name": args.project_name or project_root.name,
            "root": project_root.as_posix(),
        },
        "report": {
            "analysis_title": args.analysis_title,
            "part": args.part,
        },
        "module": {
            "name": args.module_name or Path(module_rel).name,
            "path": module_rel,
            "role": args.role or read_first_paragraph(module_dir) or "请补充该模块在项目中的角色。",
            "goal": args.goal or "说明这个模块当前为什么需要做文献梳理。",
            "current_state": read_first_paragraph(module_dir) or "未提取到 README 摘要，建议人工补充当前状态。",
            "key_files": list_key_files(module_dir),
            "recent_commits": recent_commits(project_root, module_rel),
            "worktree_changes": worktree_changes(project_root, module_rel),
            "open_questions": args.question or ["这个模块最值得借鉴哪类方法或实验设计？"],
        },
        "literature": {
            "theme": args.theme or f"{Path(module_rel).name} 相关方法、架构与实验设计",
            "papers": summary_papers(args.summary.expanduser().resolve(), args.top) if args.summary else [],
        },
    }

    out_path = args.out.expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out_path.as_posix())


if __name__ == "__main__":
    main()
