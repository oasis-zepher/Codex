#!/usr/bin/env python3
"""Render a Chinese-localized digest HTML from structured candidate artifacts."""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent

RESEARCH_LINE_RULES = [
    {
        "label": "AI + Biomarker",
        "zh": "AI + 生物标志物",
        "keywords": (
            "alzheimer",
            "neurodegeneration",
            "huntington",
            "multimodal",
            "llm",
            "tabular",
            "brain network",
            "biomarker learning",
        ),
    },
    {
        "label": "Multiomics + Disease",
        "zh": "多组学 + 疾病",
        "keywords": (
            "multiomics",
            "multi-omic",
            "proteomics",
            "protein",
            "transcriptome",
            "omics",
            "disease stratification",
        ),
    },
    {
        "label": "EV + Ocular",
        "zh": "EV + 眼科",
        "keywords": (
            "extracellular vesicle",
            "ev ",
            "tear",
            "ocular",
            "ophthalm",
            "retina",
            "cornea",
        ),
    },
    {
        "label": "Spatial Proteomics",
        "zh": "空间蛋白组",
        "keywords": (
            "spatial",
            "proteomics",
            "histopathology",
            "pathology",
            "tumor microenvironment",
            "spatio-temporal",
        ),
    },
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_repo_path(raw_path: str | None) -> Path | None:
    if not raw_path:
        return None

    candidate = Path(raw_path).expanduser()
    if candidate.exists():
        return candidate.resolve()

    normalized = raw_path.lstrip("./")
    runtime_aliases = {
        "reports/": "runtime/reports/",
        ".state/": "runtime/state/",
        ".semantic-search/": "runtime/semantic-search/",
    }
    for legacy_prefix, runtime_prefix in runtime_aliases.items():
        if normalized.startswith(legacy_prefix):
            remapped = (REPO_ROOT / (runtime_prefix + normalized[len(legacy_prefix) :])).resolve()
            if remapped.exists():
                return remapped

    markers = [
        "/Bio/Codex/skill/research-assist/",
        "/Bio/research-assist/",
    ]
    for marker in markers:
        if marker in raw_path:
            suffix = raw_path.split(marker, 1)[1]
            remapped = (REPO_ROOT / suffix).resolve()
            if remapped.exists():
                return remapped
            for legacy_prefix, runtime_prefix in runtime_aliases.items():
                if suffix.startswith(legacy_prefix):
                    runtime_remapped = (REPO_ROOT / (runtime_prefix + suffix[len(legacy_prefix) :])).resolve()
                    if runtime_remapped.exists():
                        return runtime_remapped

    remapped = (REPO_ROOT / raw_path.lstrip("./")).resolve()
    if remapped.exists():
        return remapped
    return candidate.resolve()


def sentence_split(text: str, limit: int = 2) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    cleaned = [chunk.strip() for chunk in chunks if chunk.strip()]
    return cleaned[:limit]


def short_authors(authors: list[str], limit: int = 4) -> str:
    if not authors:
        return "Unknown authors"
    if len(authors) <= limit:
        return ", ".join(authors)
    return ", ".join(authors[:limit]) + ", et al."


def normalize_text(text: str, limit: int = 260) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "..."


def has_keyword(haystack: str, keyword: str) -> bool:
    normalized = keyword.strip().lower()
    if not normalized:
        return False
    if re.fullmatch(r"[a-z0-9.+\- ]+", normalized):
        pattern = r"(?<!\w)" + re.escape(normalized).replace(r"\ ", r"\s+") + r"(?!\w)"
        return re.search(pattern, haystack) is not None
    return normalized in haystack


def localize_label(label: str) -> str:
    for rule in RESEARCH_LINE_RULES:
        if label == rule["label"]:
            return str(rule["zh"])
    return label


def localize_labels(labels: list[str]) -> list[str]:
    localized: list[str] = []
    for item in labels:
        label = localize_label(str(item))
        if label not in localized:
            localized.append(label)
    return localized


def join_labels(labels: list[str], limit: int = 2) -> str:
    cleaned = [str(item).strip() for item in labels if str(item).strip()]
    if not cleaned:
        return ""
    return "、".join(cleaned[:limit])


def infer_research_lines(title: str, abstract: str) -> list[str]:
    haystack = f"{title} {abstract}".lower()
    matched: list[str] = []
    for rule in RESEARCH_LINE_RULES:
        if any(has_keyword(haystack, str(keyword)) for keyword in rule["keywords"]):
            matched.append(str(rule["zh"]))
    return matched


def short_paper_ref(title: str, limit: int = 42) -> str:
    compact = " ".join((title or "").split())
    if ":" in compact:
        tail = compact.split(":")[-1].strip()
        if 3 <= len(tail) <= 22:
            return tail
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "..."


def semantic_anchor_title(candidate: dict[str, Any]) -> str | None:
    scores = candidate.get("_scores", {})
    if not isinstance(scores, dict):
        return None
    if not scores.get("semantic_available", True):
        return None
    title = str(scores.get("semantic_top_title") or "").strip()
    if not title:
        neighbors = scores.get("semantic_neighbors") or []
        if neighbors:
            title = str((neighbors[0] or {}).get("title") or "").strip()
    return title or None


def paper_focus(title: str, abstract: str) -> tuple[str, str]:
    haystack = f"{title} {abstract}".lower()
    rules = [
        (
            ("llm", "language model", "tabular", "few-shot", "interpretable"),
            "把表格型模型用于小样本、多模态的生物标志物预测",
            "适合重点参考小样本表型建模、缺失值处理和可解释输出的组织方式。",
        ),
        (
            ("brain network", "graph", "network mining"),
            "用图或网络表示去组织疾病表型与进展信号",
            "适合拿来比较 disease representation、节点传播和疾病分层的分析框架。",
        ),
        (
            ("spatial", "histopathology", "pathology"),
            "把空间统计和组织结构信息引入病理分析",
            "适合参考空间组学、数字病理和局部微环境量化之间的连接方式。",
        ),
        (
            ("proteomics", "multiomics", "multi-omic", "omics"),
            "整合蛋白组或多组学信号去做疾病分型和标志物筛选",
            "适合参考多层数据整合、疾病分层和候选标志物收敛的分析思路。",
        ),
        (
            ("mortality", "cohort", "screening", "association", "risk"),
            "在临床队列里做结局关联和风险分层",
            "更适合借鉴 cohort-based association、终点定义和风险建模的写法。",
        ),
        (
            ("speech", "asr", "audio", "voice"),
            "把数字行为或语音信号转成疾病表型",
            "适合作为数字生物标志物支线阅读，补足非组学模态的建模视角。",
        ),
    ]
    for keywords, focus, value in rules:
        if any(has_keyword(haystack, str(keyword)) for keyword in keywords):
            return focus, value
    first_sentence = sentence_split(abstract, limit=1)
    if first_sentence:
        return "围绕一个较具体的疾病或分析问题展开方法验证", f"摘要首句已经把切口说得很清楚：{first_sentence[0]}"
    return "围绕一个较具体的疾病问题组织分析流程", "更适合作为结构参照，而不是直接照搬结论。"


def keyword_core_module(title: str, abstract: str) -> tuple[str, str]:
    haystack = f"{title} {abstract}".lower()
    rules = [
        (
            ("spatial", "histopathology", "pathology"),
            "空间分析模块",
            "用来刻画组织或细胞在空间维度上的分布、邻域关系和局部互作，适合连接空间组学与数字病理。",
        ),
        (
            ("proteomics", "protein", "multiomics", "multi-omic", "omics"),
            "多组学整合模块",
            "用来整合蛋白组或多组学信号，提炼与疾病分型、机制解释或生物标志物筛选相关的稳定模式。",
        ),
        (
            ("alzheimer", "neurodegeneration", "huntington", "brain network"),
            "神经疾病生物标志物模块",
            "用来把疾病相关表型、脑网络或生物标志物信号组织成可比较的诊断与分层分析框架。",
        ),
        (
            ("llm", "language model", "tabular"),
            "表格智能建模模块",
            "用来处理小样本、多模态表型或缺失值较多的表格数据，适合做可解释预测与变量贡献分析。",
        ),
        (
            ("extracellular vesicle", "ev ", "tear", "ocular", "ophthalm"),
            "眼科与囊泡标志物模块",
            "用来连接眼表样本、囊泡载荷和疾病表型，适合做可转化的液体活检式探索。",
        ),
        (
            ("network", "graph"),
            "网络挖掘模块",
            "用来把变量之间的相关性或传播关系组织成网络结构，适合发现关键模块与桥接节点。",
        ),
    ]
    for keywords, label, description in rules:
        if any(has_keyword(haystack, str(keyword)) for keyword in keywords):
            return label, description
    return (
        "方法整合模块",
        "用来把论文里的核心分析流程压缩成一个可复用的阅读切口，方便快速判断它更偏方法、资源还是应用。",
    )


def chinese_overview(candidate: dict[str, Any]) -> str:
    paper = candidate.get("paper", {})
    triage = candidate.get("triage", {})
    title = str(paper.get("title") or "该论文")
    abstract = str(paper.get("abstract") or "")
    matched = localize_labels(triage.get("matched_interest_labels") or [])
    inferred = infer_research_lines(title, abstract)
    anchor = semantic_anchor_title(candidate)
    focus, value = paper_focus(title, abstract)
    line_text = join_labels(inferred or matched)

    if inferred:
        if anchor:
            return normalize_text(
                f"这篇更适合放在“{line_text}”这条线上看。它的核心是{focus}，"
                f"和你库里的《{short_paper_ref(anchor)}》放在一起看会更有参照感；{value}",
                limit=260,
            )
        return normalize_text(
            f"这篇更适合放在“{line_text}”这条线上看。它的核心是{focus}；{value}",
            limit=260,
        )
    if anchor:
        return normalize_text(
            f"这篇不一定在你的主线正中央，但和你库里的《{short_paper_ref(anchor)}》相对更近。"
            f"它的核心是{focus}；{value}",
            limit=260,
        )
    if matched:
        return normalize_text(
            f"这篇和“{join_labels(matched)}”存在一定交叉，但更适合当作边界扩展来读。"
            f"它的核心是{focus}；{value}",
            limit=260,
        )
    module_label, module_desc = keyword_core_module(title, abstract)
    return normalize_text(f"{title} 更接近{module_label}。它的核心是{focus}；{module_desc}", limit=260)


def english_overview(candidate: dict[str, Any]) -> str:
    review = candidate.get("review", {})
    reviewer_summary = str(review.get("reviewer_summary") or "").strip()
    if reviewer_summary:
        return normalize_text(reviewer_summary, limit=280)
    abstract = str(candidate.get("paper", {}).get("abstract") or "")
    summary = " ".join(sentence_split(abstract, limit=2))
    return normalize_text(summary or "No abstract summary available.", limit=280)


def relevance_text(candidate: dict[str, Any]) -> str:
    paper = candidate.get("paper", {})
    triage = candidate.get("triage", {})
    title = str(paper.get("title") or "")
    abstract = str(paper.get("abstract") or "")
    matched = localize_labels(triage.get("matched_interest_labels") or [])
    inferred = infer_research_lines(title, abstract)
    anchor = semantic_anchor_title(candidate)
    focus, _value = paper_focus(title, abstract)

    if inferred:
        line_text = join_labels(inferred)
        if anchor:
            return normalize_text(
                f"主线相关度较高。更建议放在“{line_text}”里优先看，并和《{short_paper_ref(anchor)}》做并排比较，重点看它如何实现“{focus}”这一步。",
                limit=220,
            )
        return normalize_text(
            f"主线相关度较高。更建议放在“{line_text}”里看，重点参考它如何实现“{focus}”这一步。",
            limit=220,
        )
    if anchor:
        return normalize_text(
            f"主题不算正面重合，但和《{short_paper_ref(anchor)}》在问题设定或分析框架上有邻近性，适合作为旁线参考。",
            limit=220,
        )
    if matched:
        return normalize_text(
            f"和当前研究模块“{join_labels(matched)}”有交叉，但更适合快速浏览它的分析框架，而不是优先精读。",
            limit=220,
        )
    return "和当前 Zotero 研究地图存在一定方法邻近性，适合作为补充阅读。"


def recommendation_badge(candidate: dict[str, Any]) -> str:
    review = candidate.get("review", {})
    recommendation = str(review.get("recommendation") or "unset").strip().lower()
    mapping = {
        "read_first": "优先读",
        "skim": "快速看",
        "watch": "持续跟踪",
        "watchlist": "加入观察",
        "archive": "归档参考",
        "skip_for_now": "暂缓",
        "unset": "候选",
    }
    return mapping.get(recommendation, recommendation.replace("_", " ").title())


def copy_chip(label: str, value: str, link: str | None = None) -> str:
    action = ""
    if link:
        action = (
            f'<a class="locator-open" href="{html.escape(link)}" target="_blank" rel="noreferrer" '
            f'aria-label="查看 {html.escape(label)} 页面">'
            '<span>查看</span><span class="locator-open-icon">↗</span></a>'
        )
    return (
        '<div class="locator-token">'
        '<button class="locator-chip" type="button" '
        f'data-copy="{html.escape(value)}" aria-label="Copy {html.escape(label)}">'
        f'<span class="locator-label">{html.escape(label)}</span>'
        f'<span class="locator-value">{html.escape(value)}</span>'
        "</button>"
        f"{action}"
        "</div>"
    )


def digest_issue_date(path: Path) -> str:
    match = re.search(r"digest-(\d{4}-\d{2}-\d{2})\.zh-CN\.html$", path.name)
    if match:
        return match.group(1)
    return path.stem


def digest_navigation(output_path: Path) -> dict[str, Any]:
    reports = sorted(output_path.parent.glob("digest-*.zh-CN.html"))
    if output_path not in reports:
        reports.append(output_path)
        reports = sorted(reports)

    current_index = reports.index(output_path)
    previous_report = reports[current_index - 1] if current_index > 0 else None
    next_report = reports[current_index + 1] if current_index + 1 < len(reports) else None
    archive = reports

    return {
        "previous": previous_report,
        "next": next_report,
        "archive": archive,
        "issue_index": current_index + 1,
        "issue_count": len(reports),
    }


def load_candidates(summary_path: Path) -> list[dict[str, Any]]:
    summary = load_json(summary_path)
    candidate_paths = summary.get("artifacts", {}).get("candidate_paths") or []
    resolved = []
    for raw_path in candidate_paths:
        path = resolve_repo_path(raw_path)
        if path and path.exists():
            resolved.append(load_json(path))
    return resolved


def profile_labels(profile_path: Path | None) -> list[str]:
    if profile_path is None or not profile_path.exists():
        return []
    payload = load_json(profile_path)
    return [str(item.get("label")) for item in payload.get("interests", []) if item.get("enabled", True)]


def format_date(date_text: str | None) -> str:
    if not date_text:
        return datetime.now().strftime("%Y-%m-%d")
    try:
        return datetime.fromisoformat(date_text.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except ValueError:
        return date_text[:10]


def render_card(candidate: dict[str, Any], index: int, *, lead: bool = False) -> str:
    paper = candidate.get("paper", {})
    review = candidate.get("review", {})
    identifiers = paper.get("identifiers", {}) if isinstance(paper.get("identifiers"), dict) else {}
    arxiv_id = identifiers.get("arxiv_id")
    doi = identifiers.get("doi")
    display_url = identifiers.get("url") or (paper.get("source_links") or [None])[0]
    locator_html = ""
    if arxiv_id:
        locator_html += copy_chip("arXiv", str(arxiv_id), str(display_url or ""))
    if doi:
        locator_html += copy_chip("DOI", str(doi), f"https://doi.org/{doi}")

    takeaways = review.get("quick_takeaways") or []
    takeaway_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in takeaways[:4])
    module_label, module_desc = keyword_core_module(str(paper.get("title") or ""), str(paper.get("abstract") or ""))

    card_class = "paper-card lead-card" if lead else "paper-card"
    return f"""
    <article class="{card_class}">
      <div class="story-number">稿件 {index:02d}</div>
      <div class="card-head">
        <span class="badge">{html.escape(recommendation_badge(candidate))}</span>
        <span class="meta">{html.escape(format_date(paper.get("published_at")))} · {html.escape(str(paper.get("year") or "n/a"))}</span>
      </div>
      <h2>{html.escape(str(paper.get("title") or "Untitled"))}</h2>
      <p class="authors">{html.escape(short_authors(paper.get("authors") or []))}</p>
      <div class="locator-row">{locator_html or '<span class="locator-empty">No arXiv / DOI identifier</span>'}</div>
      <section class="block">
        <h3>论文概述 / Paper Overview</h3>
        <p><strong>中文：</strong>{html.escape(chinese_overview(candidate))}</p>
        <p><strong>English:</strong> {html.escape(english_overview(candidate))}</p>
      </section>
      <section class="block">
        <h3>核心模块 / Core Module</h3>
        <p><strong>{html.escape(module_label)}</strong>：{html.escape(module_desc)}</p>
      </section>
      <section class="block">
        <h3>为何相关 / Relevance</h3>
        <p>{html.escape(relevance_text(candidate))}</p>
      </section>
      {f'<section class="block"><h3>快速要点 / Quick Takeaways</h3><ul class="takeaways">{takeaway_html}</ul></section>' if takeaway_html else ''}
      <details class="abstract-block">
        <summary>Original Abstract</summary>
        <p>{html.escape(str(paper.get("abstract") or "No abstract available."))}</p>
      </details>
    </article>
    """


def render_html(summary_path: Path, output_path: Path) -> None:
    summary = load_json(summary_path)
    run = summary.get("run", {})
    generated_at = str(run.get("generated_at") or "")
    profile_path = resolve_repo_path(run.get("profile_path"))
    labels = profile_labels(profile_path)
    candidates = load_candidates(summary_path)
    date_str = format_date(generated_at)
    lead_count = min(2, len(candidates))
    lead_cards = "\n".join(
        render_card(candidate, index, lead=True)
        for index, candidate in enumerate(candidates[:lead_count], start=1)
    )
    body_cards = "\n".join(
        render_card(candidate, index)
        for index, candidate in enumerate(candidates[lead_count:], start=lead_count + 1)
    )
    modules_text = " · ".join(labels) if labels else "No active modules detected"
    navigation = digest_navigation(output_path)
    previous_report = navigation["previous"]
    next_report = navigation["next"]
    archive_reports = navigation["archive"]
    archive_links = "".join(
        (
            f'<a class="issue-link{" is-current" if report == output_path else ""}" '
            f'href="{html.escape(report.name)}">{html.escape(digest_issue_date(report))}</a>'
        )
        for report in archive_reports
    )
    archive_html = (
        '<div class="issue-track-head">日期时间线'
        '<span class="issue-track-note">从左到右按时间推进</span></div>'
        f'<div class="issue-track-links">{archive_links}</div>'
    )
    previous_html = (
        f'<a class="edge-nav edge-left" href="{html.escape(previous_report.name)}" aria-label="上一期报告">'
        '<span class="edge-arrow">‹</span><span class="edge-copy">上一期</span></a>'
        if previous_report
        else ""
    )
    next_html = (
        f'<a class="edge-nav edge-right" href="{html.escape(next_report.name)}" aria-label="下一期报告">'
        '<span class="edge-copy">下一期</span><span class="edge-arrow">›</span></a>'
        if next_report
        else ""
    )
    archive_note = (
        f"当前为第 {navigation['issue_index']} 期，共 {navigation['issue_count']} 期。"
        if navigation["issue_count"] > 0
        else "当前仅有一期报告。"
    )

    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>文献检索简报 - {html.escape(date_str)}</title>
  <style>
    :root {{
      --bg: #f2eadf;
      --paper: rgba(255, 252, 246, 0.97);
      --paper-soft: rgba(245, 237, 226, 0.92);
      --ink: #2d251f;
      --ink-soft: #5f5045;
      --muted: #8f7867;
      --line: rgba(92, 63, 42, 0.16);
      --line-strong: rgba(92, 63, 42, 0.28);
      --accent: #7f3b22;
      --accent-soft: rgba(127, 59, 34, 0.10);
      --olive: #67715a;
      --olive-soft: rgba(103, 113, 90, 0.14);
      --shadow: 0 24px 60px rgba(92, 63, 42, 0.10);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      background:
        linear-gradient(rgba(255,255,255,0.22) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.18) 1px, transparent 1px),
        linear-gradient(180deg, #f7f0e6 0%, #efe4d5 100%);
      background-size: 28px 28px, 28px 28px, 100% 100%;
      color: var(--ink);
      padding: 22px 16px 48px;
    }}
    .page-shell {{
      width: min(1380px, 100%);
      margin: 0 auto;
    }}
    .hero {{
      padding: 30px 30px 24px;
      border-radius: 18px;
      background:
        linear-gradient(180deg, rgba(255, 252, 248, 0.98), rgba(247, 238, 228, 0.95));
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
      margin-bottom: 14px;
      position: relative;
      overflow: hidden;
    }}
    .hero::before,
    .hero::after {{
      content: "";
      position: absolute;
      left: 30px;
      right: 30px;
      height: 1px;
      background: var(--line-strong);
    }}
    .hero::before {{
      top: 18px;
    }}
    .hero::after {{
      bottom: 18px;
    }}
    .eyebrow {{
      display: inline-flex;
      padding: 0;
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      margin: 10px 0 14px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(38px, 6.4vw, 68px);
      line-height: 0.98;
      letter-spacing: -0.05em;
      font-family: "Iowan Old Style", Georgia, serif;
      font-weight: 600;
    }}
    .hero-deck {{
      max-width: 920px;
      font-size: 15px;
      line-height: 1.82;
      color: var(--ink-soft);
      margin-top: 8px;
    }}
    .hero-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }}
    .pill {{
      display: inline-flex;
      gap: 8px;
      align-items: center;
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: rgba(255, 252, 248, 0.82);
      color: var(--ink-soft);
      font-size: 12px;
    }}
    .issue-strip {{
      display: grid;
      grid-template-columns: 240px minmax(0, 1fr);
      gap: 14px;
      margin-bottom: 18px;
    }}
    .issue-panel {{
      border-radius: 14px;
      padding: 18px 18px 16px;
      background: var(--paper-soft);
      border: 1px solid var(--line);
      box-shadow: 0 10px 24px rgba(92, 63, 42, 0.06);
    }}
    .issue-kicker {{
      font-size: 11px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.14em;
      font-weight: 700;
      margin-bottom: 8px;
    }}
    .issue-main {{
      font-family: "Iowan Old Style", Georgia, serif;
      font-size: 30px;
      line-height: 1;
      margin-bottom: 8px;
    }}
    .issue-copy {{
      color: var(--ink-soft);
      font-size: 13px;
      line-height: 1.6;
    }}
    .issue-archive {{
      display: block;
    }}
    .issue-track-head {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
      color: var(--ink-soft);
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .issue-track-note {{
      color: var(--muted);
      font-size: 11px;
      letter-spacing: 0.06em;
      text-transform: none;
      font-weight: 500;
    }}
    .issue-track-links {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }}
    .issue-link {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 132px;
      padding: 11px 14px;
      border-radius: 10px;
      border: 1px solid var(--line);
      background: rgba(255, 252, 248, 0.94);
      color: var(--ink-soft);
      font-size: 13px;
      text-decoration: none;
      transition: transform 140ms ease, border-color 140ms ease, color 140ms ease;
    }}
    .issue-link:hover {{
      transform: translateY(-1px);
      border-color: var(--line-strong);
      color: var(--ink);
    }}
    .issue-link.is-current {{
      color: var(--accent);
      border-color: rgba(127, 59, 34, 0.26);
      background: rgba(127, 59, 34, 0.10);
      font-weight: 700;
    }}
    .overview-band {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .overview-card {{
      border-radius: 18px;
      padding: 14px 16px;
      background: var(--paper-soft);
      border: 1px solid var(--line);
      box-shadow: 0 12px 28px rgba(98, 69, 46, 0.07);
    }}
    .overview-label {{
      font-size: 11px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 700;
      margin-bottom: 6px;
    }}
    .overview-value {{
      font-size: clamp(24px, 3vw, 34px);
      line-height: 1;
      font-family: "Iowan Old Style", Georgia, serif;
      margin-bottom: 6px;
    }}
    .overview-copy {{
      font-size: 12px;
      color: var(--ink-soft);
      line-height: 1.45;
    }}
    .front-page {{
      margin-bottom: 18px;
    }}
    .section-header {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 12px;
      margin: 0 0 12px;
      padding: 0 2px;
    }}
    .section-kicker {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      font-weight: 700;
    }}
    .lead-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
      align-items: start;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
      align-items: start;
    }}
    .paper-card {{
      width: 100%;
      border-radius: 10px;
      padding: 24px 22px 20px;
      background: var(--paper);
      border: 1px solid var(--line);
      box-shadow: 0 12px 28px rgba(92, 63, 42, 0.06);
      position: relative;
    }}
    .paper-card::before {{
      content: "";
      position: absolute;
      left: 22px;
      right: 22px;
      top: 13px;
      height: 1px;
      background: rgba(92, 63, 42, 0.10);
    }}
    .lead-card {{
      margin-bottom: 0;
      box-shadow: 0 16px 34px rgba(92, 63, 42, 0.08);
      border-color: rgba(92, 63, 42, 0.20);
    }}
    .lead-card h2 {{
      font-size: 33px;
      line-height: 1.12;
    }}
    .story-number {{
      margin-bottom: 12px;
      color: var(--muted);
      font-size: 11px;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      font-weight: 700;
    }}
    .card-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
    }}
    .badge {{
      display: inline-flex;
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--olive-soft);
      color: var(--olive);
      font-size: 12px;
      font-weight: 700;
    }}
    .meta, .authors {{
      color: var(--muted);
      font-size: 13px;
    }}
    h2 {{
      margin: 0 0 8px;
      font-size: 29px;
      line-height: 1.16;
      font-family: "Iowan Old Style", Georgia, serif;
      letter-spacing: -0.02em;
    }}
    .locator-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin: 16px 0 4px;
      align-items: center;
    }}
    .locator-token {{
      display: inline-flex;
      align-items: stretch;
      border-radius: 16px;
      overflow: hidden;
      border: 1px solid var(--line);
      background: rgba(255, 252, 248, 0.94);
      box-shadow: 0 8px 20px rgba(92, 63, 42, 0.06);
    }}
    .locator-chip {{
      display: inline-flex;
      flex-direction: column;
      gap: 4px;
      min-width: 0;
      padding: 10px 12px;
      border: 0;
      background: transparent;
      cursor: pointer;
      color: inherit;
      text-align: left;
    }}
    .locator-chip:hover {{
      background: rgba(127, 59, 34, 0.05);
    }}
    .locator-label {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      font-weight: 700;
    }}
    .locator-value {{
      font-size: 13px;
      font-weight: 700;
      color: var(--accent);
      word-break: break-all;
    }}
    .locator-open {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 0 14px;
      border-left: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(127, 59, 34, 0.10), rgba(127, 59, 34, 0.06));
      color: var(--accent);
      text-decoration: none;
      font-size: 13px;
      font-weight: 700;
      transition: background 140ms ease, color 140ms ease;
    }}
    .locator-open:hover {{
      background: linear-gradient(180deg, rgba(127, 59, 34, 0.16), rgba(127, 59, 34, 0.10));
      color: #66311d;
    }}
    .locator-open-icon {{
      display: inline-flex;
      width: 20px;
      height: 20px;
      align-items: center;
      justify-content: center;
      border-radius: 999px;
      background: rgba(127, 59, 34, 0.12);
      font-size: 12px;
      line-height: 1;
    }}
    .locator-empty {{
      color: var(--muted);
      font-size: 13px;
    }}
    .block {{
      margin-top: 16px;
      padding-top: 14px;
      border-top: 1px solid var(--line);
    }}
    .block h3 {{
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin: 0 0 8px;
    }}
    .block p {{
      margin: 0;
      color: var(--ink-soft);
      line-height: 1.82;
      font-size: 15px;
      text-align: justify;
    }}
    .block p + p {{
      margin-top: 10px;
    }}
    .takeaways {{
      margin: 0;
      padding-left: 18px;
      color: var(--ink-soft);
    }}
    .takeaways li + li {{
      margin-top: 6px;
    }}
    .abstract-block {{
      margin-top: 16px;
      border-top: 1px solid var(--line);
      padding-top: 14px;
    }}
    .abstract-block summary {{
      cursor: pointer;
      color: var(--accent);
      font-weight: 700;
      list-style: none;
    }}
    .abstract-block summary::-webkit-details-marker {{
      display: none;
    }}
    .abstract-block p {{
      margin-top: 12px;
      color: var(--ink-soft);
      font-size: 14px;
      line-height: 1.82;
      text-align: justify;
    }}
    .footer {{
      margin-top: 22px;
      text-align: center;
      color: var(--muted);
      font-size: 13px;
    }}
    .edge-nav {{
      position: fixed;
      top: 50%;
      transform: translateY(-50%);
      z-index: 12;
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 14px 16px;
      border-radius: 999px;
      text-decoration: none;
      color: var(--ink);
      border: 1px solid var(--line);
      background: rgba(255, 252, 248, 0.94);
      box-shadow: 0 12px 26px rgba(92, 63, 42, 0.10);
      backdrop-filter: blur(8px);
    }}
    .edge-nav:hover {{
      border-color: var(--line-strong);
    }}
    .edge-left {{
      left: 14px;
    }}
    .edge-right {{
      right: 14px;
    }}
    .edge-arrow {{
      font-family: "Iowan Old Style", Georgia, serif;
      font-size: 28px;
      line-height: 1;
      color: var(--accent);
    }}
    .edge-copy {{
      font-size: 12px;
      color: var(--ink-soft);
      letter-spacing: 0.08em;
      text-transform: uppercase;
      font-weight: 700;
    }}
    @media (max-width: 960px) {{
      body {{
        padding-left: 12px;
        padding-right: 12px;
      }}
      .lead-grid,
      .issue-strip,
      .overview-band,
      .cards {{
        grid-template-columns: 1fr;
      }}
      .edge-nav {{
        top: auto;
        bottom: 14px;
        transform: none;
        padding: 12px 14px;
      }}
      .edge-left {{
        left: 12px;
      }}
      .edge-right {{
        right: 12px;
      }}
    }}
    @media (max-width: 720px) {{
      .hero {{
        padding: 24px 20px 20px;
      }}
      .hero::before,
      .hero::after {{
        left: 20px;
        right: 20px;
      }}
      .paper-card {{
        padding: 20px;
      }}
      .locator-row {{
        flex-direction: column;
        align-items: stretch;
      }}
      .locator-token {{
        width: 100%;
      }}
      .locator-open {{
        justify-content: center;
      }}
      .issue-link {{
        min-width: 0;
        width: calc(50% - 5px);
      }}
    }}
  </style>
</head>
<body>
  {previous_html}
  {next_html}
  <div class="page-shell">
    <header class="hero">
      <div class="eyebrow">Research Assist 文献简报</div>
      <h1>文献检索简报</h1>
      <p class="hero-deck">以本地 Zotero 兴趣图谱为底稿，把当日筛出的重点论文整理成一张可连续翻阅的研究版面。左右侧可切换到其他日期的报告，适合按时间线追踪候选论文的变化。</p>
      <div class="hero-meta">
        <span class="pill">日期 · {html.escape(date_str)}</span>
        <span class="pill">入选 · {len(candidates)}</span>
        <span class="pill">模块 · {len(labels)}</span>
      </div>
    </header>
    <section class="issue-strip">
      <div class="issue-panel">
        <div class="issue-kicker">Issue</div>
        <div class="issue-main">{html.escape(date_str)}</div>
        <div class="issue-copy">{html.escape(archive_note)}</div>
      </div>
      <div class="issue-panel issue-archive">
        {archive_html}
      </div>
    </section>
    <section class="overview-band">
      <div class="overview-card">
        <div class="overview-label">模块</div>
        <div class="overview-value">{len(labels)}</div>
        <div class="overview-copy">{html.escape(modules_text)}</div>
      </div>
      <div class="overview-card">
        <div class="overview-label">本轮产出</div>
        <div class="overview-value">{len(candidates)}</div>
        <div class="overview-copy">本轮 digest 中被最终选中的重点论文卡片数。</div>
      </div>
    </section>
    {(
      f'<section class="front-page"><div class="section-header"><div class="section-kicker">头版重点</div></div><div class="lead-grid">{lead_cards}</div></section>'
      if lead_cards else ''
    )}
    {(
      f'<section><div class="section-header"><div class="section-kicker">后续稿件</div></div><div class="cards">{body_cards}</div></section>'
      if body_cards else ''
    )}
    {(
      '<article class="paper-card"><h2>今天没有新增匹配论文</h2><p class="authors">可以稍后重跑 daily，或先检查检索源与 profile 是否更新。</p></article>'
      if not lead_cards and not body_cards else ''
    )}
    <div class="footer">Created by Zephyr</div>
  </div>
  <script>
    async function copyText(value) {{
      if (navigator.clipboard && navigator.clipboard.writeText) {{
        await navigator.clipboard.writeText(value);
        return;
      }}
      const area = document.createElement("textarea");
      area.value = value;
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.focus();
      area.select();
      document.execCommand("copy");
      document.body.removeChild(area);
    }}
    document.querySelectorAll(".locator-chip").forEach((chip) => {{
      chip.addEventListener("click", async () => {{
        const value = chip.dataset.copy || "";
        if (!value) return;
        const original = chip.querySelector(".locator-label").textContent;
        try {{
          await copyText(value);
          chip.querySelector(".locator-label").textContent = "已复制";
          setTimeout(() => {{
            chip.querySelector(".locator-label").textContent = original;
          }}, 1000);
        }} catch (_error) {{}}
      }});
    }});
    const previousHref = {json.dumps(previous_report.name if previous_report else "")};
    const nextHref = {json.dumps(next_report.name if next_report else "")};
    document.addEventListener("keydown", (event) => {{
      if (event.key === "ArrowLeft" && previousHref) {{
        window.location.href = previousHref;
      }}
      if (event.key === "ArrowRight" && nextHref) {{
        window.location.href = nextHref;
      }}
    }});
  </script>
</body>
</html>
"""
    output_path.write_text(html_doc, encoding="utf-8")


def default_output_path(summary_path: Path, summary: dict[str, Any]) -> Path:
    run = summary.get("run", {})
    date_str = format_date(str(run.get("generated_at") or ""))
    return summary_path.parent / f"digest-{date_str}.zh-CN.html"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Chinese-localized digest HTML")
    parser.add_argument("--summary", required=True, type=Path, help="Path to a digest run summary JSON")
    parser.add_argument("--output", type=Path, default=None, help="Optional output HTML path")
    args = parser.parse_args()

    summary_path = args.summary.expanduser().resolve()
    summary = load_json(summary_path)
    if args.output is not None:
        output_path = args.output.expanduser().resolve()
    else:
        output_path = default_output_path(summary_path, summary)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    render_html(summary_path, output_path)
    print(output_path.as_posix())


if __name__ == "__main__":
    main()
