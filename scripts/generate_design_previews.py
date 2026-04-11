#!/usr/bin/env python3

from __future__ import annotations

import html
import re
from pathlib import Path


ROOT = Path("/Users/zephyr/Bio/Codex")
PRESETS_DIR = ROOT / "design-presets"
INDEX_PATH = PRESETS_DIR / "index.html"

HEX_RE = re.compile(r"`(#[0-9a-fA-F]{3,8})`")
TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
FONT_RE = re.compile(r"- \*\*(?:Primary|Display|Body)\*\*: `([^`]+)`")
CHARACTERISTICS_RE = re.compile(
    r"\*\*Key Characteristics:\*\*\n(?P<body>(?:- .+\n)+)", re.MULTILINE
)


def clean_text(text: str) -> str:
    return " ".join(text.strip().split())


def first_paragraph(md: str) -> str:
    parts = md.split("\n\n")
    for part in parts:
        stripped = part.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("##"):
            continue
        if stripped.startswith("**Key Characteristics:**"):
            continue
        return clean_text(stripped)
    return ""


def extract_palette(md: str) -> list[str]:
    colors: list[str] = []
    seen: set[str] = set()
    for match in HEX_RE.findall(md):
        value = match.lower()
        if value not in seen:
            colors.append(value)
            seen.add(value)
        if len(colors) == 6:
            break
    fallback = ["#111111", "#f5f5f5", "#2563eb", "#ef4444", "#10b981", "#a855f7"]
    for color in fallback:
        if len(colors) == 6:
            break
        if color not in seen:
            colors.append(color)
            seen.add(color)
    return colors


def pick_font(md: str) -> str:
    match = FONT_RE.search(md)
    if not match:
        return "System UI"
    return clean_text(match.group(1).split(",")[0])


def extract_bullets(md: str) -> list[str]:
    match = CHARACTERISTICS_RE.search(md)
    if not match:
        return []
    bullets = []
    for line in match.group("body").splitlines():
        if line.startswith("- "):
            bullets.append(clean_text(line[2:]))
        if len(bullets) == 3:
            break
    return bullets


def contrast_color(hex_color: str) -> str:
    value = hex_color.lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) < 6:
        return "#111111"
    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#111111" if luminance > 0.65 else "#f8fafc"


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def svg_preview(site: str, title: str, summary: str, font: str, colors: list[str], bullets: list[str]) -> str:
    bg = colors[0]
    surface = colors[1]
    accent = colors[2]
    accent_two = colors[3]
    text = contrast_color(bg)
    muted = "#d4d4d8" if text == "#f8fafc" else "#52525b"
    surface_text = contrast_color(surface)

    bullet_markup = []
    y = 410
    for bullet in bullets[:3]:
        bullet_markup.append(
            f'<circle cx="72" cy="{y - 5}" r="4" fill="{accent}"/>'
            f'<text x="88" y="{y}" fill="{surface_text}" font-size="20">{html.escape(truncate(bullet, 52))}</text>'
        )
        y += 38

    swatches = []
    for idx, color in enumerate(colors[:5]):
        swatches.append(
            f'<rect x="{64 + idx * 72}" y="520" width="56" height="56" rx="16" fill="{color}" />'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720" role="img" aria-label="{html.escape(site)} design preview">
  <defs>
    <linearGradient id="bg" x1="0%" x2="100%" y1="0%" y2="100%">
      <stop offset="0%" stop-color="{bg}" />
      <stop offset="100%" stop-color="{accent_two}" />
    </linearGradient>
    <linearGradient id="glow" x1="0%" x2="100%" y1="0%" y2="0%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.92" />
      <stop offset="100%" stop-color="{accent_two}" stop-opacity="0.92" />
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="20" stdDeviation="28" flood-color="#000000" flood-opacity="0.18"/>
    </filter>
  </defs>
  <rect width="1200" height="720" fill="url(#bg)" />
  <circle cx="1030" cy="110" r="180" fill="{accent}" fill-opacity="0.18" />
  <circle cx="170" cy="640" r="220" fill="{accent_two}" fill-opacity="0.20" />
  <rect x="44" y="44" width="1112" height="632" rx="32" fill="#ffffff" fill-opacity="0.08" stroke="#ffffff" stroke-opacity="0.16"/>
  <text x="64" y="92" fill="{text}" font-size="22" letter-spacing="2.8">DESIGN PRESET</text>
  <text x="64" y="164" fill="{text}" font-size="60" font-weight="700">{html.escape(site)}</text>
  <text x="64" y="208" fill="{muted}" font-size="26">{html.escape(truncate(title, 52))}</text>
  <text x="64" y="260" fill="{text}" font-size="22">Primary font: {html.escape(font)}</text>
  <text x="64" y="320" fill="{text}" font-size="24">{html.escape(truncate(summary, 86))}</text>
  <rect x="64" y="360" width="490" height="248" rx="28" fill="{surface}" filter="url(#shadow)"/>
  <rect x="64" y="360" width="490" height="10" rx="10" fill="url(#glow)"/>
  <text x="72" y="400" fill="{surface_text}" font-size="24" font-weight="700">Key Characteristics</text>
  {''.join(bullet_markup)}
  <rect x="610" y="120" width="504" height="212" rx="28" fill="#ffffff" fill-opacity="0.10" stroke="#ffffff" stroke-opacity="0.18"/>
  <text x="648" y="172" fill="{text}" font-size="18" letter-spacing="2">PALETTE</text>
  {''.join(swatches)}
  <rect x="648" y="230" width="378" height="14" rx="7" fill="{accent}" />
  <rect x="648" y="262" width="290" height="14" rx="7" fill="{accent_two}" />
  <rect x="648" y="294" width="334" height="14" rx="7" fill="{surface}" />
  <rect x="610" y="372" width="504" height="236" rx="28" fill="#111111" fill-opacity="0.16" stroke="#ffffff" stroke-opacity="0.12"/>
  <text x="648" y="424" fill="{text}" font-size="18" letter-spacing="2">STYLE SIGNAL</text>
  <text x="648" y="484" fill="{text}" font-size="44" font-weight="700">{html.escape(truncate(site.upper(), 16))}</text>
  <text x="648" y="530" fill="{muted}" font-size="24">{html.escape(truncate(summary, 40))}</text>
  <rect x="648" y="560" width="172" height="18" rx="9" fill="{accent}" />
  <rect x="836" y="560" width="118" height="18" rx="9" fill="{accent_two}" />
  <rect x="970" y="560" width="86" height="18" rx="9" fill="{surface}" />
</svg>
"""


def build_index(cards: list[dict[str, str]]) -> str:
    card_markup = []
    for card in cards:
        card_markup.append(
            f"""
<article class="card">
  <img src="./{card['site']}/preview.svg" alt="{html.escape(card['site'])} preview" loading="lazy" />
  <div class="body">
    <h2>{html.escape(card['site'])}</h2>
    <p>{html.escape(card['summary'])}</p>
    <div class="links">
      <a href="./{card['site']}/DESIGN.md">DESIGN.md</a>
      <a href="./{card['site']}/preview.svg">preview.svg</a>
    </div>
  </div>
</article>
"""
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Design Presets Gallery</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f3f5f7;
      --panel: #ffffff;
      --text: #121417;
      --muted: #5b6470;
      --line: #d9e0e7;
      --link: #0f62fe;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(15, 98, 254, 0.10), transparent 22rem),
        linear-gradient(180deg, #fcfdff, var(--bg));
      color: var(--text);
    }}
    .wrap {{
      max-width: 1480px;
      margin: 0 auto;
      padding: 40px 24px 64px;
    }}
    h1 {{
      margin: 0 0 12px;
      font-size: 40px;
      line-height: 1.05;
    }}
    .intro {{
      max-width: 860px;
      margin: 0 0 32px;
      color: var(--muted);
      font-size: 18px;
      line-height: 1.6;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      gap: 20px;
    }}
    .card {{
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 22px;
      background: var(--panel);
      box-shadow: 0 12px 36px rgba(16, 24, 40, 0.08);
    }}
    img {{
      display: block;
      width: 100%;
      height: auto;
      background: #eef2f6;
    }}
    .body {{
      padding: 18px 18px 20px;
    }}
    h2 {{
      margin: 0 0 8px;
      font-size: 22px;
    }}
    p {{
      margin: 0 0 14px;
      color: var(--muted);
      line-height: 1.55;
      min-height: 4.6em;
    }}
    .links {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }}
    a {{
      color: var(--link);
      text-decoration: none;
      font-weight: 600;
    }}
    a:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <main class="wrap">
    <h1>Design Presets Gallery</h1>
    <p class="intro">Local offline gallery for the archived DESIGN.md presets. Each preview is generated from the saved markdown file and lives next to it as <code>preview.svg</code>.</p>
    <section class="grid">
      {''.join(card_markup)}
    </section>
  </main>
</body>
</html>
"""


def main() -> None:
    cards: list[dict[str, str]] = []

    for preset_dir in sorted(path for path in PRESETS_DIR.iterdir() if path.is_dir()):
        md_path = preset_dir / "DESIGN.md"
        if not md_path.exists():
            continue

        md = md_path.read_text(encoding="utf-8")
        title_match = TITLE_RE.search(md)
        title = clean_text(title_match.group(1)) if title_match else preset_dir.name
        summary = truncate(first_paragraph(md), 140)
        font = pick_font(md)
        colors = extract_palette(md)
        bullets = extract_bullets(md)

        svg = svg_preview(
            site=preset_dir.name,
            title=title,
            summary=summary,
            font=font,
            colors=colors,
            bullets=bullets,
        )
        (preset_dir / "preview.svg").write_text(svg, encoding="utf-8")
        cards.append({"site": preset_dir.name, "summary": summary})

    INDEX_PATH.write_text(build_index(cards), encoding="utf-8")


if __name__ == "__main__":
    main()
