#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path


DEFAULT_SUMMARY_ROOT = Path("~/Bio/Codex/skill/research-assist/runtime/reports").expanduser()
DEFAULT_HTML = Path("~/Bio/Codex/skill/research-assist/reports/generated/latest.zh-CN.html").expanduser()


def latest_summary(summary_root: Path) -> Path:
    summaries = sorted(summary_root.glob("*.run-summary.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not summaries:
        raise FileNotFoundError(f"No run summary found under {summary_root}")
    return summaries[0]


def note_path(vault: Path, target_date: date) -> Path:
    return vault / "01 Daily Notes" / target_date.strftime("%Y") / target_date.strftime("%Y-%m") / f"{target_date.isoformat()}.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_note_exists(path: Path, target_date: date) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                f"date: {target_date.isoformat()}",
                "tags:",
                "  - research-diary",
                "  - daily-note",
                "---",
                "",
                f"# {target_date.isoformat()} 科研日记",
                "",
                "## 今日主线",
                "- ",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def digest_block(summary_path: Path, html_path: Path, top_n: int) -> str:
    summary = load_json(summary_path)
    candidate_paths = list(summary.get("artifacts", {}).get("candidate_paths") or [])[:top_n]
    lines = [
        "## 今日 digest 摘要",
        f"- run summary: `{summary_path.as_posix()}`",
        f"- zh html: `{html_path.as_posix()}`" if html_path.exists() else "- zh html: 未找到最新 HTML",
        "",
        "### Top papers",
    ]
    for index, candidate_path in enumerate(candidate_paths, start=1):
        candidate = load_json(Path(candidate_path))
        paper = candidate.get("paper", {})
        review = candidate.get("review", {})
        title = str(paper.get("title") or "Untitled")
        reason = str(review.get("why_it_matters") or review.get("reviewer_summary") or "").strip()
        recommendation = str(review.get("recommendation") or "unset").strip()
        lines.append(f"{index}. **{title}**")
        lines.append(f"   - recommendation: `{recommendation}`")
        lines.append(f"   - note: {reason[:180] + ('...' if len(reason) > 180 else '') if reason else '暂无摘要'}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Append the latest research-assist digest to today's diary note.")
    parser.add_argument("--vault", required=True, type=Path, help="Vault path")
    parser.add_argument("--summary", type=Path, default=None, help="Optional run summary path")
    parser.add_argument("--date", default=None, help="YYYY-MM-DD; defaults to today")
    parser.add_argument("--top", default="3", help="Top papers to append, default 3")
    args = parser.parse_args()

    target_date = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else date.today()
    vault = args.vault.expanduser().resolve()
    summary_path = args.summary.expanduser().resolve() if args.summary else latest_summary(DEFAULT_SUMMARY_ROOT)
    html_path = DEFAULT_HTML.resolve()
    daily_note = note_path(vault, target_date)
    ensure_note_exists(daily_note, target_date)

    content = daily_note.read_text(encoding="utf-8")
    marker = "## 今日 digest 摘要"
    if marker in content:
        content = content.split(marker, 1)[0].rstrip() + "\n\n"
    else:
        content = content.rstrip() + "\n\n"
    block = digest_block(summary_path, html_path, max(1, int(args.top)))
    daily_note.write_text(content + block + "\n", encoding="utf-8")
    print(daily_note.as_posix())


if __name__ == "__main__":
    main()
