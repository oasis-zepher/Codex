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
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) {
      continue;
    }
    const key = token.slice(2);
    const value = argv[index + 1] && !argv[index + 1].startsWith("--") ? argv[++index] : "true";
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

function compact(text, limit = 220) {
  const normalized = String(text || "").replace(/\s+/g, " ").trim();
  if (normalized.length <= limit) {
    return normalized;
  }
  return `${normalized.slice(0, limit - 1).trim()}...`;
}

function asList(value) {
  return Array.isArray(value) ? value : value ? [value] : [];
}

function formatAuthors(authors) {
  const names = asList(authors).filter(Boolean);
  if (names.length <= 4) {
    return names.join(", ");
  }
  return `${names.slice(0, 4).join(", ")} et al.`;
}

function deckDate(brief) {
  const generatedAt = String(brief.generated_at || "");
  return generatedAt ? generatedAt.slice(0, 10) : new Date().toISOString().slice(0, 10);
}

function buildOutline(brief, deckTitle, subtitle, dateText) {
  const project = brief.project || {};
  const report = brief.report || {};
  const module = brief.module || {};
  const literature = brief.literature || {};
  const lines = [
    `# ${deckTitle}`,
    "",
    `- 日期：${dateText}`,
    `- 项目：${project.name || "Unknown project"}`,
    `- 模块：${module.name || module.path || "Unknown module"}`,
    `- 分析：${compact(report.analysis_title || "模块汇报", 80)} ${compact(report.part || "", 20)}`.trim(),
    `- 场景：${subtitle || "项目模块文献汇报"}`,
    "",
    "## 模块定位",
    `- 角色：${compact(module.role || "", 140)}`,
    `- 目标：${compact(module.goal || "", 140)}`,
    `- 当前状态：${compact(module.current_state || "", 160)}`,
    ""
  ];
  asList(literature.papers).forEach((paper, index) => {
    lines.push(`## ${index + 1}. ${paper.title || "Untitled"}`);
    lines.push(`- 相关性：${compact(paper.relevance_to_module || "", 140)}`);
    lines.push(`- 可借用点：${compact(paper.takeaway || "", 140)}`);
    lines.push(`- 风险：${compact(paper.limitations || "", 120)}`);
    lines.push("");
  });
  return `${lines.join("\n").trim()}\n`;
}

function addTextBox(slide, text, options) {
  slide.addText(text, {
    margin: 0.06,
    breakLine: false,
    fit: "shrink",
    ...options
  });
}

function addBullets(slide, items, options) {
  const lines = items.length > 0
    ? items.map((item) => ({ text: compact(item, options.compactLimit || 120), options: { bullet: { indent: 12 } } }))
    : [{ text: options.emptyText || "暂无补充。", options: { bullet: { indent: 12 } } }];
  slide.addText(lines, {
    x: options.x,
    y: options.y,
    w: options.w,
    h: options.h,
    fontFace: options.fontFace,
    fontSize: options.fontSize,
    color: options.color,
    margin: 0.04,
    fit: "shrink",
    valign: "top"
  });
}

function addTitleSlide(pptx, theme, brief, deckTitle, subtitle, dateText) {
  const slide = pptx.addSlide();
  const project = brief.project || {};
  const report = brief.report || {};
  const module = brief.module || {};
  slide.background = { color: theme.colors.bg };
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.35, fill: { color: theme.colors.accent } });
  addTextBox(slide, deckTitle, {
    x: 0.65, y: 0.95, w: 11.9, h: 0.9,
    fontFace: theme.fonts.title, fontSize: 24, bold: true, color: theme.colors.ink
  });
  addTextBox(slide, subtitle || "围绕项目模块组织文献、问题与行动建议", {
    x: 0.65, y: 1.95, w: 9.8, h: 0.45,
    fontFace: theme.fonts.body, fontSize: 14, color: theme.colors.muted
  });
  addTextBox(slide, `项目：${project.name || "Unknown"} | 模块：${module.name || module.path || "Unknown"} | 日期：${dateText}`, {
    x: 0.65, y: 2.55, w: 10.8, h: 0.35,
    fontFace: theme.fonts.body, fontSize: 11, color: theme.colors.muted
  });
  addTextBox(slide, `${report.analysis_title || "模块汇报"} ${report.part || ""}`.trim(), {
    x: 0.65, y: 3.0, w: 6.0, h: 0.35,
    fontFace: theme.fonts.body, fontSize: 12.5, bold: true, color: theme.colors.accent
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 9.6, y: 1.0, w: 2.5, h: 1.05,
    rectRadius: 0.08, fill: { color: theme.colors.accentSoft }, line: { color: theme.colors.accentSoft }
  });
  addTextBox(slide, "模块优先", {
    x: 10.0, y: 1.34, w: 1.7, h: 0.28,
    fontFace: theme.fonts.body, fontSize: 13, bold: true, color: theme.colors.accent, align: "center"
  });
}

function addModuleContextSlide(pptx, theme, brief) {
  const slide = pptx.addSlide();
  const module = brief.module || {};
  slide.background = { color: "FFFFFF" };
  addTextBox(slide, "模块定位与当前状态", {
    x: 0.55, y: 0.42, w: 5.8, h: 0.4,
    fontFace: theme.fonts.title, fontSize: 21, bold: true, color: theme.colors.ink
  });

  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.55, y: 1.0, w: 6.1, h: 2.25,
    rectRadius: 0.05, fill: { color: "F8FAFC" }, line: { color: theme.colors.line, pt: 1 }
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 6.9, y: 1.0, w: 5.9, h: 2.25,
    rectRadius: 0.05, fill: { color: "FCFCFD" }, line: { color: theme.colors.line, pt: 1 }
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.55, y: 3.55, w: 12.25, h: 2.65,
    rectRadius: 0.05, fill: { color: "FFFFFF" }, line: { color: theme.colors.line, pt: 1 }
  });

  addTextBox(slide, "角色 / Goal", {
    x: 0.8, y: 1.22, w: 2.2, h: 0.2,
    fontFace: theme.fonts.body, fontSize: 12, bold: true, color: theme.colors.ink
  });
  addTextBox(slide, `角色：${compact(module.role || "未提供", 180)}\n\n目标：${compact(module.goal || "未提供", 180)}`, {
    x: 0.8, y: 1.55, w: 5.55, h: 1.45,
    fontFace: theme.fonts.body, fontSize: 11, color: theme.colors.ink, valign: "top"
  });

  addTextBox(slide, "当前状态 / Open Questions", {
    x: 7.15, y: 1.22, w: 3.0, h: 0.2,
    fontFace: theme.fonts.body, fontSize: 12, bold: true, color: theme.colors.ink
  });
  addBullets(slide, asList(module.open_questions).slice(0, 4), {
    x: 7.15, y: 1.58, w: 5.2, h: 1.25,
    fontFace: theme.fonts.body, fontSize: 11, color: theme.colors.ink,
    emptyText: compact(module.current_state || "未提供当前状态。", 180)
  });

  addTextBox(slide, "关键文件 / Recent Changes", {
    x: 0.8, y: 3.78, w: 3.2, h: 0.2,
    fontFace: theme.fonts.body, fontSize: 12, bold: true, color: theme.colors.ink
  });
  addBullets(slide, asList(module.key_files).slice(0, 6), {
    x: 0.8, y: 4.1, w: 5.55, h: 1.7,
    fontFace: theme.fonts.body, fontSize: 10.5, color: theme.colors.ink,
    compactLimit: 80,
    emptyText: "未收集到关键文件。"
  });
  addBullets(slide, [...asList(module.recent_commits).slice(0, 3), ...asList(module.worktree_changes).slice(0, 3)], {
    x: 6.95, y: 4.1, w: 5.45, h: 1.7,
    fontFace: theme.fonts.body, fontSize: 10.5, color: theme.colors.muted,
    compactLimit: 90,
    emptyText: "未检测到最近 commit 或工作区改动。"
  });
}

function addLiteratureNeedSlide(pptx, theme, brief) {
  const slide = pptx.addSlide();
  const module = brief.module || {};
  const literature = brief.literature || {};
  const report = brief.report || {};
  slide.background = { color: "FFFFFF" };
  addTextBox(slide, `为什么现在要做这部分${report.analysis_title || "模块汇报"}`, {
    x: 0.55, y: 0.42, w: 6.8, h: 0.4,
    fontFace: theme.fonts.title, fontSize: 21, bold: true, color: theme.colors.ink
  });
  addTextBox(slide, compact(module.goal || "未提供目标。", 300), {
    x: 0.8, y: 1.25, w: 11.8, h: 0.5,
    fontFace: theme.fonts.body, fontSize: 14, color: theme.colors.ink
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.75, y: 2.0, w: 12.0, h: 3.6,
    rectRadius: 0.05, fill: { color: "F8FAFC" }, line: { color: theme.colors.line, pt: 1 }
  });
  addTextBox(slide, `文献主题：${compact(literature.theme || `${module.name || module.path || "该模块"} 相关方法`, 160)}`, {
    x: 1.0, y: 2.3, w: 10.8, h: 0.3,
    fontFace: theme.fonts.body, fontSize: 13, bold: true, color: theme.colors.accent
  });
  addBullets(slide, [
    `当前状态：${compact(module.current_state || "未提供当前状态。", 100)}`,
    `待解问题：${compact(asList(module.open_questions)[0] || "未提供问题。", 100)}`,
    `计划重点：从 paper 中提炼可借用的方法、实验设计和工程边界。`
  ], {
    x: 1.0, y: 2.8, w: 10.9, h: 1.4,
    fontFace: theme.fonts.body, fontSize: 12, color: theme.colors.ink,
    compactLimit: 120
  });
  addBullets(slide, asList(literature.papers).slice(0, 4).map((paper) => `${paper.title}：${compact(paper.relevance_to_module || paper.takeaway || "", 90)}`), {
    x: 1.0, y: 4.35, w: 10.9, h: 1.0,
    fontFace: theme.fonts.body, fontSize: 11, color: theme.colors.muted,
    compactLimit: 120,
    emptyText: "当前 brief 尚未附带 paper 列表。"
  });
}

function addPaperSlide(pptx, theme, paper, index) {
  const slide = pptx.addSlide();
  slide.background = { color: "FFFFFF" };
  addTextBox(slide, `${index + 1}. ${compact(paper.title || "Untitled", 90)}`, {
    x: 0.55, y: 0.42, w: 10.4, h: 0.5,
    fontFace: theme.fonts.title, fontSize: 20, bold: true, color: theme.colors.ink
  });
  addTextBox(slide, `${formatAuthors(paper.authors)} | ${paper.year || "n.d."}`, {
    x: 0.55, y: 0.95, w: 9.0, h: 0.25,
    fontFace: theme.fonts.body, fontSize: 10.5, color: theme.colors.muted
  });
  addTextBox(slide, compact(paper.url || "", 90), {
    x: 9.0, y: 0.95, w: 3.2, h: 0.25,
    fontFace: theme.fonts.body, fontSize: 9.5, color: theme.colors.accent, align: "right"
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

  addTextBox(slide, "对模块的启发", {
    x: 0.8, y: 1.55, w: 2.5, h: 0.2,
    fontFace: theme.fonts.body, fontSize: 12, bold: true, color: theme.colors.ink
  });
  addTextBox(slide, compact(paper.relevance_to_module || "未提供相关性说明。", 280), {
    x: 0.8, y: 1.9, w: 5.35, h: 1.15,
    fontFace: theme.fonts.body, fontSize: 11, color: theme.colors.ink, valign: "top"
  });

  addTextBox(slide, "可借用点", {
    x: 7.0, y: 1.55, w: 2.5, h: 0.2,
    fontFace: theme.fonts.body, fontSize: 12, bold: true, color: theme.colors.ink
  });
  addBullets(slide, asList(paper.takeaway || "").filter(Boolean), {
    x: 7.0, y: 1.86, w: 5.35, h: 1.2,
    fontFace: theme.fonts.body, fontSize: 11, color: theme.colors.ink,
    emptyText: compact(paper.takeaway || "未提供 takeaways。", 180)
  });

  addTextBox(slide, "限制 / 下一步", {
    x: 0.8, y: 3.85, w: 2.5, h: 0.2,
    fontFace: theme.fonts.body, fontSize: 12, bold: true, color: theme.colors.ink
  });
  addTextBox(slide, [
    `限制：${compact(paper.limitations || "未提供限制说明。", 220)}`,
    "",
    `下一步：${compact(paper.next_use || "结合模块需求，评估是否值得落到 PoC。", 220)}`
  ].join("\n"), {
    x: 0.8, y: 4.18, w: 11.5, h: 1.8,
    fontFace: theme.fonts.body, fontSize: 10.8, color: theme.colors.ink, valign: "top"
  });
}

function addActionSlide(pptx, theme, brief) {
  const slide = pptx.addSlide();
  const module = brief.module || {};
  const literature = brief.literature || {};
  slide.background = { color: "FFFFFF" };
  addTextBox(slide, "汇报后建议动作", {
    x: 0.55, y: 0.42, w: 5.0, h: 0.4,
    fontFace: theme.fonts.title, fontSize: 21, bold: true, color: theme.colors.ink
  });
  addBullets(slide, [
    `把最相关的 1-2 篇 paper 映射到模块的 open questions：${compact(asList(module.open_questions)[0] || "待补充", 80)}`,
    `针对关键文件建立 PoC 或 refactor 计划：${compact(asList(module.key_files)[0] || "待补充", 80)}`,
    `把文献里可借用的方法、评价指标和限制写回模块设计文档。`
  ], {
    x: 0.8, y: 1.3, w: 11.5, h: 2.0,
    fontFace: theme.fonts.body, fontSize: 16, color: theme.colors.ink,
    compactLimit: 140
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.8, y: 4.15, w: 11.5, h: 1.25,
    rectRadius: 0.05, fill: { color: theme.colors.accentSoft }, line: { color: theme.colors.accentSoft }
  });
  addTextBox(slide, `建议结尾：把“模块目标 - 当前缺口 - paper 启发 - 下一步实验”串成一条线。当前纳入 papers：${asList(literature.papers).length} 篇。`, {
    x: 1.0, y: 4.55, w: 11.1, h: 0.35,
    fontFace: theme.fonts.body, fontSize: 13, bold: true, color: theme.colors.accent, align: "center"
  });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args["brief-json"]) {
    throw new Error("Provide --brief-json <module-brief.json>.");
  }

  const briefPath = resolveInput(args["brief-json"]);
  const brief = readJson(briefPath);
  const theme = readJson(path.join(SKILL_ROOT, "assets", "deck-theme.json"));
  const report = brief.report || {};
  const module = brief.module || {};
  const project = brief.project || {};
  const dateText = deckDate(brief);
  const defaultAnalysisTitle = `${report.analysis_title || "模块汇报"}${report.part ? ` ${report.part}` : ""}`.trim();
  const deckTitle = args.title || `${project.name || "Project"} / ${module.name || module.path || "Module"} ${defaultAnalysisTitle}`;
  const subtitle = args.subtitle || "围绕单个项目模块组织问题、文献证据与实现建议";
  const outPath = resolveInput(args.out || path.join(process.cwd(), "output", `${String(module.name || "module").replace(/\s+/g, "-").toLowerCase()}-${String(report.part || "report").toLowerCase()}-module-report.pptx`));
  const outDir = path.dirname(outPath);
  ensureDir(outDir);

  const pptx = new PptxGenJS();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Codex";
  pptx.company = "Codex";
  pptx.subject = "Module literature report";
  pptx.title = deckTitle;
  pptx.lang = "zh-CN";
  pptx.theme = {
    headFontFace: theme.fonts.title,
    bodyFontFace: theme.fonts.body,
    lang: "zh-CN"
  };

  addTitleSlide(pptx, theme, brief, deckTitle, subtitle, dateText);
  addModuleContextSlide(pptx, theme, brief);
  addLiteratureNeedSlide(pptx, theme, brief);
  asList(brief?.literature?.papers).forEach((paper, index) => addPaperSlide(pptx, theme, paper, index));
  addActionSlide(pptx, theme, brief);

  const outlinePath = outPath.replace(/\.pptx$/i, ".md");
  fs.writeFileSync(outlinePath, buildOutline(brief, deckTitle, subtitle, dateText), "utf8");
  await pptx.writeFile({ fileName: outPath });
  process.stdout.write(`${outPath}\n${outlinePath}\n`);
}

main().catch((error) => {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exit(1);
});
