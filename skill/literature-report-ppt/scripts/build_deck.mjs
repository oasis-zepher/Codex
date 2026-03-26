#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import PptxGenJS from "pptxgenjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const SKILL_ROOT = path.resolve(__dirname, "..");

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) {
      continue;
    }
    const key = token.slice(2);
    const value = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : "true";
    args[key] = value;
  }
  return args;
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function resolveInput(inputPath, baseDir = process.cwd()) {
  return path.isAbsolute(inputPath) ? inputPath : path.resolve(baseDir, inputPath);
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function compact(text, max = 220) {
  const normalized = String(text || "").replace(/\s+/g, " ").trim();
  if (normalized.length <= max) {
    return normalized;
  }
  return `${normalized.slice(0, max - 1).trim()}...`;
}

function asList(value) {
  if (!value) {
    return [];
  }
  return Array.isArray(value) ? value : [value];
}

function recommendationLabel(raw) {
  const key = String(raw || "unset").toLowerCase();
  return {
    read_first: "优先精读",
    skim: "快速浏览",
    watch: "持续跟踪",
    watchlist: "加入观察",
    archive: "归档参考",
    skip_for_now: "暂缓处理",
    unset: "待判断"
  }[key] || key;
}

function firstSourceLink(paper) {
  const identifiers = paper.identifiers || {};
  return identifiers.url || asList(paper.source_links)[0] || "";
}

function formatAuthors(authors) {
  const names = asList(authors).filter(Boolean);
  if (names.length <= 4) {
    return names.join(", ");
  }
  return `${names.slice(0, 4).join(", ")} et al.`;
}

function pickTopCandidates(summaryPath, topN) {
  const summary = readJson(summaryPath);
  const paths = asList(summary?.artifacts?.candidate_paths).slice(0, topN);
  const baseDir = path.dirname(summaryPath);
  const candidates = paths.map((candidatePath) => {
    const resolved = resolveInput(candidatePath, baseDir);
    return readJson(resolved);
  });
  return { summary, candidates };
}

function deckDate(summary) {
  const generatedAt = String(summary?.run?.generated_at || "");
  return generatedAt ? generatedAt.slice(0, 10) : new Date().toISOString().slice(0, 10);
}

function defaultOutPath({ summaryPath, paperPath, dateText }) {
  const base = summaryPath
    ? path.join(process.cwd(), "output", `literature-briefing-${dateText}.pptx`)
    : path.join(process.cwd(), "output", `${path.basename(paperPath, ".json")}.pptx`);
  return base;
}

function buildOutline(deckTitle, subtitle, dateText, candidates) {
  const lines = [
    `# ${deckTitle}`,
    "",
    `- 日期：${dateText}`,
    `- 场景：${subtitle || "文献组会 / journal club"}`,
    ""
  ];
  candidates.forEach((candidate, index) => {
    const paper = candidate.paper || {};
    const review = candidate.review || {};
    lines.push(`## ${index + 1}. ${paper.title || "Untitled"}`);
    lines.push(`- 推荐级别：${recommendationLabel(review.recommendation)}`);
    lines.push(`- 相关性：${compact(review.why_it_matters || review.reviewer_summary || "", 120)}`);
    for (const takeaway of asList(review.quick_takeaways).slice(0, 3)) {
      lines.push(`- 要点：${compact(takeaway, 100)}`);
    }
    lines.push("");
  });
  return `${lines.join("\n").trim()}\n`;
}

function addTextBox(slide, text, options) {
  slide.addText(text, {
    margin: 0.08,
    breakLine: false,
    fit: "shrink",
    ...options
  });
}

function addTitleSlide(pptx, theme, deckTitle, subtitle, dateText) {
  const slide = pptx.addSlide();
  slide.background = { color: theme.colors.bg };
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.35, fill: { color: theme.colors.accent } });
  addTextBox(slide, deckTitle, {
    x: 0.7, y: 1.0, w: 11.8, h: 0.9,
    fontFace: theme.fonts.title, fontSize: 24, bold: true, color: theme.colors.ink
  });
  addTextBox(slide, subtitle || "面向组会 / journal club 的中文文献汇报", {
    x: 0.7, y: 2.0, w: 8.8, h: 0.5,
    fontFace: theme.fonts.body, fontSize: 14, color: theme.colors.muted
  });
  addTextBox(slide, `生成日期：${dateText}`, {
    x: 0.7, y: 6.3, w: 3.0, h: 0.3,
    fontFace: theme.fonts.body, fontSize: 11, color: theme.colors.muted
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 9.7, y: 1.2, w: 2.2, h: 1.0,
    rectRadius: 0.08,
    fill: { color: theme.colors.accentSoft },
    line: { color: theme.colors.accentSoft }
  });
  addTextBox(slide, "中国语境汇报模板", {
    x: 9.95, y: 1.55, w: 1.8, h: 0.25,
    fontFace: theme.fonts.body, fontSize: 12, bold: true, color: theme.colors.accent, align: "center"
  });
}

function addOverviewSlide(pptx, theme, candidates) {
  const slide = pptx.addSlide();
  slide.background = { color: "FFFFFF" };
  addTextBox(slide, "今日文献总览", {
    x: 0.6, y: 0.45, w: 4.5, h: 0.45,
    fontFace: theme.fonts.title, fontSize: 21, bold: true, color: theme.colors.ink
  });

  let y = 1.1;
  candidates.forEach((candidate, index) => {
    const paper = candidate.paper || {};
    const review = candidate.review || {};
    const triage = candidate.triage || {};
    const label = compact(asList(triage.matched_interest_labels).join(" / ") || "未标注方向", 26);
    slide.addShape(pptx.ShapeType.roundRect, {
      x: 0.7, y, w: 12.0, h: 0.9,
      rectRadius: 0.06,
      fill: { color: index % 2 === 0 ? "F8FAFC" : "F1F5F9" },
      line: { color: theme.colors.line, pt: 1 }
    });
    addTextBox(slide, `${index + 1}. ${compact(paper.title, 80)}`, {
      x: 0.95, y: y + 0.1, w: 7.6, h: 0.22,
      fontFace: theme.fonts.body, fontSize: 14, bold: true, color: theme.colors.ink
    });
    addTextBox(slide, compact(review.why_it_matters || review.reviewer_summary || "", 120), {
      x: 0.95, y: y + 0.38, w: 7.6, h: 0.28,
      fontFace: theme.fonts.body, fontSize: 10.5, color: theme.colors.muted
    });
    addTextBox(slide, recommendationLabel(review.recommendation), {
      x: 9.15, y: y + 0.12, w: 1.3, h: 0.2,
      fontFace: theme.fonts.body, fontSize: 11, bold: true, color: theme.colors.accent, align: "center"
    });
    addTextBox(slide, label, {
      x: 10.55, y: y + 0.12, w: 1.65, h: 0.2,
      fontFace: theme.fonts.body, fontSize: 10.5, color: theme.colors.warn, align: "center"
    });
    y += 1.0;
  });
}

function addPaperSlide(pptx, theme, candidate, index) {
  const slide = pptx.addSlide();
  const paper = candidate.paper || {};
  const review = candidate.review || {};
  const triage = candidate.triage || {};
  const identifiers = paper.identifiers || {};

  slide.background = { color: "FFFFFF" };
  addTextBox(slide, `${index + 1}. ${compact(paper.title, 90)}`, {
    x: 0.55, y: 0.4, w: 9.8, h: 0.5,
    fontFace: theme.fonts.title, fontSize: 20, bold: true, color: theme.colors.ink
  });
  addTextBox(slide, recommendationLabel(review.recommendation), {
    x: 10.65, y: 0.44, w: 1.9, h: 0.26,
    fontFace: theme.fonts.body, fontSize: 11.5, bold: true, color: theme.colors.accent, align: "center"
  });
  addTextBox(slide, `${formatAuthors(paper.authors)} | ${paper.year || "n.d."} | ${identifiers.arxiv_id || identifiers.doi || "no-id"}`, {
    x: 0.55, y: 0.95, w: 11.2, h: 0.25,
    fontFace: theme.fonts.body, fontSize: 10.5, color: theme.colors.muted
  });

  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.55, y: 1.35, w: 5.95, h: 2.05,
    rectRadius: 0.05, fill: { color: "F8FAFC" }, line: { color: theme.colors.line, pt: 1 }
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 6.75, y: 1.35, w: 6.0, h: 2.05,
    rectRadius: 0.05, fill: { color: "FCFCFD" }, line: { color: theme.colors.line, pt: 1 }
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.55, y: 3.65, w: 12.2, h: 2.7,
    rectRadius: 0.05, fill: { color: "FFFFFF" }, line: { color: theme.colors.line, pt: 1 }
  });

  addTextBox(slide, "为何值得汇报", {
    x: 0.8, y: 1.55, w: 2.5, h: 0.2,
    fontFace: theme.fonts.body, fontSize: 12, bold: true, color: theme.colors.ink
  });
  addTextBox(slide, compact(review.why_it_matters || review.reviewer_summary || "暂无自动摘要。", 300), {
    x: 0.8, y: 1.9, w: 5.35, h: 1.15,
    fontFace: theme.fonts.body, fontSize: 11, color: theme.colors.ink, valign: "top"
  });

  addTextBox(slide, "核心信息", {
    x: 7.0, y: 1.55, w: 2.5, h: 0.2,
    fontFace: theme.fonts.body, fontSize: 12, bold: true, color: theme.colors.ink
  });
  const takeawayLines = asList(review.quick_takeaways).slice(0, 4).map((item) => ({
    text: compact(item, 90),
    options: { bullet: { indent: 12 } }
  }));
  slide.addText(takeawayLines.length > 0 ? takeawayLines : [{ text: "暂无要点，建议回到摘要或原文补充。", options: { bullet: { indent: 12 } } }], {
    x: 7.0, y: 1.86, w: 5.35, h: 1.2,
    fontFace: theme.fonts.body, fontSize: 11, color: theme.colors.ink,
    breakLine: false, fit: "shrink", margin: 0.05
  });

  addTextBox(slide, "摘要与风险", {
    x: 0.8, y: 3.85, w: 2.5, h: 0.2,
    fontFace: theme.fonts.body, fontSize: 12, bold: true, color: theme.colors.ink
  });
  const matchedLabels = asList(triage.matched_interest_labels).join(" / ") || "未标注";
  const caveats = asList(review.caveats).slice(0, 3).map((item) => `- ${compact(item, 120)}`).join("\n");
  const abstractBlock = [
    `匹配方向：${matchedLabels}`,
    `来源链接：${firstSourceLink(paper) || "N/A"}`,
    "",
    `摘要：${compact(paper.abstract || "No abstract available.", 380)}`,
    "",
    `风险与注意：`,
    caveats || "- 暂无 caveat，建议在正式汇报前自行复核统计假设与实验边界。"
  ].join("\n");
  addTextBox(slide, abstractBlock, {
    x: 0.8, y: 4.18, w: 11.6, h: 1.85,
    fontFace: theme.fonts.body, fontSize: 10.5, color: theme.colors.ink, valign: "top"
  });
}

function addActionSlide(pptx, theme, candidates) {
  const slide = pptx.addSlide();
  slide.background = { color: "FFFFFF" };
  addTextBox(slide, "建议的下一步", {
    x: 0.6, y: 0.5, w: 4.0, h: 0.4,
    fontFace: theme.fonts.title, fontSize: 21, bold: true, color: theme.colors.ink
  });
  const actionLines = candidates.slice(0, 3).map((candidate, index) => {
    const paper = candidate.paper || {};
    const review = candidate.review || {};
    return {
      text: `${index + 1}. ${compact(paper.title, 60)}：${compact(review.why_it_matters || "可作为下一步重点阅读对象。", 95)}`,
      options: { bullet: { indent: 14 } }
    };
  });
  slide.addText(actionLines, {
    x: 0.8, y: 1.4, w: 11.4, h: 2.0,
    fontFace: theme.fonts.body, fontSize: 16, color: theme.colors.ink, margin: 0.08, fit: "shrink"
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.8, y: 4.2, w: 11.2, h: 1.3,
    rectRadius: 0.05, fill: { color: theme.colors.accentSoft }, line: { color: theme.colors.accentSoft }
  });
  addTextBox(slide, "汇报建议：先讲问题背景，再给出 3 篇最值得读的 paper，最后用“我们能借什么”收尾。", {
    x: 1.05, y: 4.6, w: 10.7, h: 0.32,
    fontFace: theme.fonts.body, fontSize: 13, bold: true, color: theme.colors.accent, align: "center"
  });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const theme = readJson(path.join(SKILL_ROOT, "assets", "deck-theme.json"));
  const topN = Math.max(1, Number.parseInt(args.top || "5", 10));

  let summaryPath = "";
  let paperPath = "";
  let summary = null;
  let candidates = [];

  if (args.summary) {
    summaryPath = resolveInput(args.summary);
    ({ summary, candidates } = pickTopCandidates(summaryPath, topN));
  } else if (args["paper-json"]) {
    paperPath = resolveInput(args["paper-json"]);
    candidates = [readJson(paperPath)];
    summary = { run: { generated_at: new Date().toISOString() } };
  } else {
    throw new Error("Provide either --summary <run-summary.json> or --paper-json <candidate.json>.");
  }

  if (candidates.length === 0) {
    throw new Error("No candidate papers found for deck generation.");
  }

  const dateText = deckDate(summary);
  const deckTitle = args.title || (candidates.length > 1 ? `文献汇报：${dateText} 今日精选` : compact(candidates[0]?.paper?.title || "单篇文献汇报", 48));
  const subtitle = args.subtitle || "基于 research-assist digest 自动生成";
  const outPath = resolveInput(args.out || defaultOutPath({ summaryPath, paperPath, dateText }));
  const outDir = path.dirname(outPath);
  ensureDir(outDir);

  const pptx = new PptxGenJS();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Codex";
  pptx.company = "Codex";
  pptx.subject = "Literature briefing";
  pptx.title = deckTitle;
  pptx.lang = "zh-CN";
  pptx.theme = {
    headFontFace: theme.fonts.title,
    bodyFontFace: theme.fonts.body,
    lang: "zh-CN"
  };

  addTitleSlide(pptx, theme, deckTitle, subtitle, dateText);
  addOverviewSlide(pptx, theme, candidates);
  candidates.forEach((candidate, index) => addPaperSlide(pptx, theme, candidate, index));
  addActionSlide(pptx, theme, candidates);

  const outlinePath = outPath.replace(/\.pptx$/i, ".md");
  fs.writeFileSync(outlinePath, buildOutline(deckTitle, subtitle, dateText, candidates), "utf8");
  await pptx.writeFile({ fileName: outPath });

  process.stdout.write(`${outPath}\n${outlinePath}\n`);
}

main().catch((error) => {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exit(1);
});
