#!/usr/bin/env python3
"""Deterministic skill runner for the local research-assist workflow."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from render_digest_cn import (
    chinese_overview,
    default_output_path,
    load_candidates,
    load_json,
    recommendation_badge,
    render_html,
    resolve_repo_path,
    relevance_text,
)


REPO_ROOT = Path(__file__).resolve().parent.parent


def visible_abspath(path_value: str | Path, *, base_dir: Path | None = None) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_absolute() and base_dir is not None:
        path = base_dir / path
    return Path(os.path.abspath(os.fspath(path)))


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    severity: str = "error"


def resolve_path(config_path: Path, raw_path: str | None, *, default: str | None = None) -> Path | None:
    target = raw_path or default
    if not target:
        return None
    return visible_abspath(target, base_dir=REPO_ROOT)


def load_config(config_path: Path) -> dict[str, Any]:
    return json.loads(config_path.read_text(encoding="utf-8"))


def save_temp_config(payload: dict[str, Any]) -> Path:
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    with handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return Path(handle.name)


def ensure_directory(path: Path | None) -> None:
    if path is not None:
        path.mkdir(parents=True, exist_ok=True)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def socket_check(base_url: str) -> tuple[bool, str]:
    parsed = urlparse(base_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=2):
            return True, f"reachable at {host}:{port}"
    except OSError as exc:
        return False, f"unreachable at {host}:{port} ({exc})"


def skill_runtime_config(config: dict[str, Any]) -> dict[str, Any]:
    payload = config.get("skill_runtime", {})
    return payload if isinstance(payload, dict) else {}


def daily_config(config: dict[str, Any]) -> dict[str, Any]:
    payload = skill_runtime_config(config).get("daily", {})
    return payload if isinstance(payload, dict) else {}


def runtime_paths(config_path: Path, config: dict[str, Any]) -> dict[str, Path | None]:
    retrieval_defaults = config.get("retrieval_defaults", {})
    semantic_cfg = config.get("semantic_search", {})
    return {
        "profile_path": resolve_path(config_path, config.get("profile_path"), default="./profiles/research-interest.json"),
        "output_root": resolve_path(config_path, config.get("output_root"), default="./runtime/reports"),
        "state_path": resolve_path(
            config_path,
            retrieval_defaults.get("state_path") if isinstance(retrieval_defaults, dict) else None,
            default="./runtime/state/arxiv_profile_seen.json",
        ),
        "semantic_persist": resolve_path(
            config_path,
            semantic_cfg.get("persist_directory") if isinstance(semantic_cfg, dict) else None,
            default="./runtime/semantic-search",
        ),
        "zotero_db_path": resolve_path(
            config_path,
            semantic_cfg.get("zotero_db_path") if isinstance(semantic_cfg, dict) else None,
            default=None,
        ),
    }


def migrate_runtime_artifacts(paths: dict[str, Path | None]) -> list[str]:
    notes: list[str] = []

    output_root = paths.get("output_root")
    if output_root is not None:
        ensure_directory(output_root)
        legacy_reports = REPO_ROOT / "reports"
        legacy_items = list(legacy_reports.glob("*.run-summary.json")) + list(legacy_reports.glob("digest-*.html"))
        for item in legacy_items:
            target = output_root / item.name
            if item.exists() and not target.exists():
                item.rename(target)
                notes.append(f"moved {display_path(item)} -> {display_path(target)}")
        legacy_retrieval = legacy_reports / "retrieval"
        target_retrieval = output_root / "retrieval"
        if legacy_retrieval.exists() and not target_retrieval.exists():
            legacy_retrieval.rename(target_retrieval)
            notes.append("moved reports/retrieval -> runtime/reports/retrieval")

    state_path = paths.get("state_path")
    if state_path is not None:
        ensure_directory(state_path.parent)
        legacy_state = REPO_ROOT / ".state"
        if legacy_state.exists() and not any(state_path.parent.iterdir()):
            for item in legacy_state.iterdir():
                target = state_path.parent / item.name
                if not target.exists():
                    item.rename(target)
            try:
                legacy_state.rmdir()
            except OSError:
                pass
            notes.append("migrated .state contents -> runtime/state")

    semantic_persist = paths.get("semantic_persist")
    if semantic_persist is not None:
        ensure_directory(semantic_persist.parent)
        legacy_semantic = REPO_ROOT / ".semantic-search"
        if legacy_semantic.exists() and not semantic_persist.exists():
            legacy_semantic.rename(semantic_persist)
            notes.append("moved .semantic-search -> runtime/semantic-search")
        elif legacy_semantic.exists() and semantic_persist.exists():
            for item in legacy_semantic.iterdir():
                target = semantic_persist / item.name
                if not target.exists():
                    item.rename(target)
            try:
                legacy_semantic.rmdir()
            except OSError:
                pass
            notes.append("migrated .semantic-search contents -> runtime/semantic-search")

    return notes


def preflight(config_path: Path, config: dict[str, Any]) -> tuple[list[Check], dict[str, Path | None]]:
    paths = runtime_paths(config_path, config)
    checks: list[Check] = []

    profile_path = paths["profile_path"]
    output_root = paths["output_root"]
    state_path = paths["state_path"]
    semantic_persist = paths["semantic_persist"]
    zotero_db_path = paths["zotero_db_path"]

    checks.append(Check("config", config_path.exists(), config_path.as_posix()))
    checks.append(
        Check(
            "profile",
            bool(profile_path and profile_path.exists()),
            profile_path.as_posix() if profile_path else "missing profile path",
            severity="warn",
        )
    )

    for label, path in [("output_root", output_root), ("state_dir", state_path.parent if state_path else None), ("semantic_dir", semantic_persist)]:
        try:
            ensure_directory(path)
            checks.append(Check(label, True, path.as_posix() if path else "n/a"))
        except OSError as exc:
            checks.append(Check(label, False, str(exc)))

    semantic_cfg = config.get("semantic_search", {})
    semantic_enabled = bool(semantic_cfg.get("enabled", True)) if isinstance(semantic_cfg, dict) else True
    if semantic_enabled:
        checks.append(
            Check(
                "zotero_db",
                bool(zotero_db_path and zotero_db_path.exists()),
                zotero_db_path.as_posix() if zotero_db_path else "missing zotero_db_path",
            )
        )
        embedding_cfg = semantic_cfg.get("embedding_config", {}) if isinstance(semantic_cfg, dict) else {}
        base_url = str(embedding_cfg.get("base_url") or "http://localhost:11434/v1")
        reachable, detail = socket_check(base_url)
        checks.append(Check("embedding_endpoint", reachable, detail, severity="warn"))
        index_exists = bool(semantic_persist and semantic_persist.exists() and any(semantic_persist.iterdir()))
        checks.append(
            Check(
                "semantic_index",
                index_exists,
                semantic_persist.as_posix() if semantic_persist else "missing semantic path",
                severity="warn",
            )
        )

    return checks, paths


def can_use_semantic(checks: list[Check]) -> bool:
    lookup = {check.name: check for check in checks}
    required = ["zotero_db"]
    return all(lookup.get(name, Check(name, False, "")).ok for name in required)


def rebuild_semantic_index(config_path: Path, *, timeout_sec: int = 45) -> dict[str, Any]:
    script = (
        "from codex_research_assist.zotero_mcp.semantic_search import create_semantic_search; "
        f"search = create_semantic_search(config_path={config_path.as_posix()!r}); "
        "import json; "
        "print(json.dumps(search.update_database(force_rebuild=True), ensure_ascii=False))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=timeout_sec,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "semantic rebuild failed")
    stdout = completed.stdout.strip()
    if not stdout:
        return {"status": "ok", "detail": "semantic rebuild completed with empty stdout"}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {"status": "ok", "detail": stdout}


def digest_command(config_path: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "codex_research_assist",
        "--action",
        "digest",
        "--config",
        config_path.as_posix(),
    ]


def run_digest(config_path: Path, *, timeout_sec: int = 180) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            digest_command(config_path),
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            timeout=timeout_sec,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=digest_command(config_path),
            returncode=124,
            stdout="",
            stderr=f"digest timed out after {timeout_sec}s",
        )


def latest_summary(output_root: Path, *, require_candidates: bool = False) -> Path | None:
    summaries = sorted(output_root.glob("*.run-summary.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    for summary_path in summaries:
        if not require_candidates:
            return summary_path
        try:
            payload = load_json(summary_path)
        except Exception:
            continue
        candidate_count = payload.get("run", {}).get("candidate_count")
        candidate_paths = payload.get("artifacts", {}).get("candidate_paths") or []
        if (isinstance(candidate_count, int) and candidate_count > 0) or candidate_paths:
            return summary_path
    return None


def publish_latest_cn_alias(output_path: Path) -> Path | None:
    alias_path = output_path.parent / "latest.zh-CN.html"
    try:
        if alias_path.exists() or alias_path.is_symlink():
            alias_path.unlink()
        shutil.copyfile(output_path, alias_path)
    except OSError:
        return None
    return alias_path


def render_cn_digest(summary_path: Path) -> tuple[Path, Path | None]:
    summary = load_json(summary_path)
    output_path = default_output_path(summary_path, summary)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    render_html(summary_path, output_path)
    alias_path = publish_latest_cn_alias(output_path)
    return output_path, alias_path


def disable_semantic_in_config(config: dict[str, Any]) -> dict[str, Any]:
    patched = json.loads(json.dumps(config))
    semantic_cfg = patched.setdefault("semantic_search", {})
    if isinstance(semantic_cfg, dict):
        semantic_cfg["enabled"] = False
    return patched


def print_checks(checks: list[Check]) -> str:
    lines = ["# research-assist preflight", ""]
    for check in checks:
        prefix = "OK" if check.ok else ("WARN" if check.severity == "warn" else "FAIL")
        lines.append(f"- {prefix} `{check.name}`: {check.detail}")
    return "\n".join(lines)


def run_daily(config_path: Path, *, preflight_only: bool = False) -> int:
    config = load_config(config_path)
    paths = runtime_paths(config_path, config)
    migration_notes = migrate_runtime_artifacts(paths)
    checks, paths = preflight(config_path, config)
    print(print_checks(checks))
    if migration_notes:
        print("\n# runtime migration")
        for note in migration_notes:
            print(f"- {note}")
    if preflight_only:
        return 0

    output_root = paths["output_root"]
    runtime_daily = daily_config(config)
    semantic_enabled = bool(config.get("semantic_search", {}).get("enabled", True))
    semantic_allowed = semantic_enabled and can_use_semantic(checks)
    if semantic_enabled and semantic_allowed and runtime_daily.get("rebuild_semantic_index", True):
        print("\n# semantic rebuild")
        try:
            timeout_sec = int(runtime_daily.get("semantic_rebuild_timeout_sec", 45))
            result = rebuild_semantic_index(config_path, timeout_sec=timeout_sec)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as exc:  # pragma: no cover - defensive fallback
            semantic_allowed = False
            print(f"- semantic rebuild failed: {exc}")

    active_config_path = config_path
    temp_config_path: Path | None = None
    if semantic_enabled and not semantic_allowed and runtime_daily.get("fallback_disable_semantic", True):
        patched = disable_semantic_in_config(config)
        temp_config_path = save_temp_config(patched)
        active_config_path = temp_config_path
        print("\n# fallback")
        print("- semantic search unavailable; retrying digest with semantic disabled")

    print("\n# digest")
    digest_timeout_sec = int(runtime_daily.get("digest_timeout_sec", 180))
    result = run_digest(active_config_path, timeout_sec=digest_timeout_sec)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode != 0 and semantic_enabled and active_config_path == config_path and runtime_daily.get("fallback_disable_semantic", True):
        patched = disable_semantic_in_config(config)
        temp_config_path = save_temp_config(patched)
        active_config_path = temp_config_path
        print("- primary digest failed; retrying with semantic disabled")
        result = run_digest(active_config_path, timeout_sec=digest_timeout_sec)
        if result.stdout.strip():
            print(result.stdout.strip())

    if temp_config_path is not None and temp_config_path.exists():
        temp_config_path.unlink(missing_ok=True)

    summary_path = latest_summary(output_root) if output_root else None
    if result.returncode != 0:
        print(result.stderr.strip())
        fallback_summary = latest_summary(output_root, require_candidates=True) if output_root else None
        if runtime_daily.get("fallback_use_latest_successful_run", True) and fallback_summary is not None:
            zh_path, latest_zh_path = render_cn_digest(fallback_summary)
            print("\n# fallback artifact")
            print(f"- reused latest summary: {fallback_summary.as_posix()}")
            print(f"- chinese html: {zh_path.as_posix()}")
            if latest_zh_path is not None:
                print(f"- latest chinese html: {latest_zh_path.as_posix()}")
            return 0
        return result.returncode

    if summary_path is None:
        print("No digest run summary found after a successful digest run.")
        return 1

    zh_path, latest_zh_path = render_cn_digest(summary_path)
    print("\n# artifacts")
    print(f"- summary: {summary_path.as_posix()}")
    print(f"- chinese html: {zh_path.as_posix()}")
    if latest_zh_path is not None:
        print(f"- latest chinese html: {latest_zh_path.as_posix()}")
    return 0


def markdown_top3(summary_path: Path) -> str:
    candidates = load_candidates(summary_path)[:3]
    if not candidates:
        return "No ranked candidates available."
    lines = ["# 今日 Top 3 推荐", ""]
    for index, candidate in enumerate(candidates, start=1):
        paper = candidate.get("paper", {})
        identifiers = paper.get("identifiers", {}) if isinstance(paper.get("identifiers"), dict) else {}
        doi = identifiers.get("doi")
        arxiv_id = identifiers.get("arxiv_id")
        url = identifiers.get("url") or (paper.get("source_links") or [None])[0] or "N/A"
        if doi:
            identifier_text = f"DOI：{doi}"
        elif arxiv_id:
            identifier_text = f"arXiv：{arxiv_id}"
        else:
            identifier_text = "标识符：N/A"
        badge = recommendation_badge(candidate)
        lines.append(f"{index}. [{badge}] {paper.get('title', 'Untitled')}")
        lines.append(f"   - {identifier_text}")
        lines.append(f"   - 链接：{url}")
        lines.append(f"   - 推荐理由：{relevance_text(candidate)}")
        lines.append(f"   - 中文导读：{chinese_overview(candidate)}")
        lines.append("")
    return "\n".join(lines).strip()


def run_top3(config_path: Path, *, fresh: bool = False) -> int:
    config = load_config(config_path)
    output_root = runtime_paths(config_path, config)["output_root"]
    summary_path = latest_summary(output_root, require_candidates=True) if output_root else None
    if fresh or summary_path is None:
        exit_code = run_daily(config_path)
        if exit_code != 0:
            return exit_code
        summary_path = latest_summary(output_root, require_candidates=True) if output_root else None
    if summary_path is None:
        print("No digest summary available for top3 output.")
        return 1
    print(markdown_top3(summary_path))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Local skill runner for research-assist")
    subparsers = parser.add_subparsers(dest="command")

    daily = subparsers.add_parser("daily", help="Run preflight, digest, and Chinese HTML rendering")
    daily.add_argument("--config", type=Path, default=Path("./config.json"))
    daily.add_argument("--preflight-only", action="store_true")

    top3 = subparsers.add_parser("top3", help="Show the top 3 recommended papers from the latest run")
    top3.add_argument("--config", type=Path, default=Path("./config.json"))
    top3.add_argument("--fresh", action="store_true")

    preflight_parser = subparsers.add_parser("preflight", help="Run only preflight checks")
    preflight_parser.add_argument("--config", type=Path, default=Path("./config.json"))

    args = parser.parse_args()
    command = args.command or "daily"
    config_path = visible_abspath(args.config)

    if command == "daily":
        raise SystemExit(run_daily(config_path, preflight_only=args.preflight_only))
    if command == "top3":
        raise SystemExit(run_top3(config_path, fresh=args.fresh))
    if command == "preflight":
        config = load_config(config_path)
        checks, _paths = preflight(config_path, config)
        print(print_checks(checks))
        raise SystemExit(0)


if __name__ == "__main__":
    main()
