#!/usr/bin/env python3
"""Generate the profile header and project card SVGs in assets/.

Usage:  python3 scripts/gen_assets.py <fonts-dir>

<fonts-dir> must hold neon400.woff2, neon700.woff2, xenon700.woff2
(Monaspace Neon/Xenon, subset to printable ASCII + a few symbols).
Brand icons are lifted from assets/stack-<theme>.svg, so keep that file.

To add a project: append a dict to PROJECTS, run the script, and add one <td>
to the table in README.md.
"""
import base64
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

THEMES = {
    "dark": dict(bg="#0d1117", panel="#161b22", chip="#1c2330", border="#30363d",
                 text="#e6edf3", muted="#8b949e", green="#3fb950", blue="#79c0ff"),
    "light": dict(bg="#ffffff", panel="#f6f8fa", chip="#eaeef2", border="#d0d7de",
                  text="#1f2328", muted="#59636e", green="#1a7f37", blue="#0969da"),
}

PROJECTS = [
    dict(slug="smart-knowledge-hub", name="smart-knowledge-hub-backend", lang="TypeScript",
         url="https://github.com/tqha1011/smart-knowledge-hub-backend",
         desc="AI knowledge base: ask your documents, get answers with sources.",
         chips=["NestJS", "pgvector", "Redis", "Gemini"]),
    dict(slug="fitwork", name="FitworkBE-Nestjs", lang="TypeScript",
         url="https://github.com/tqha1011/FitworkBE-Nestjs",
         desc="Recruitment platform backend with AI resume evaluation and cited evidence.",
         chips=["NestJS", "Prisma", "PostgreSQL", "Redis"]),
    dict(slug="shoestore", name="ShoeStore", lang="Kotlin",
         url="https://github.com/tqha1011/ShoeStore",
         desc="Shoe e-commerce: Android app and ASP.NET Core API, optimistic locking on stock.",
         chips=["Kotlin", "Compose", "ASP.NET", "Docker"]),
]
MORE_URL = "https://github.com/tqha1011?tab=repositories"

# chip label -> key of the icon inside stack-<theme>.svg (None = custom / no icon)
ICON_KEYS = {"NestJS": "NestJS", "pgvector": "pgvector", "Redis": "Redis", "Gemini": "Gemini",
             "Prisma": "Prisma", "PostgreSQL": "PostgreSQL", "Docker": "Docker",
             "Compose": "Jetpack Compose", "TypeScript": "TypeScript"}
CUSTOM_ICONS = {
    "Kotlin": '<path d="M0 24V0h24L12 12 24 24z" fill="#7F52FF"/>',
    "ASP.NET": '<rect x="1" y="1" width="22" height="22" rx="5" fill="#512BD4"/>'
               '<path d="M7 17V7l10 10V7" fill="none" stroke="#fff" stroke-width="2.2" '
               'stroke-linejoin="round"/>',
}

CHAR_W = 0.6  # Monaspace advance width in em


def font_css(fonts: Path) -> str:
    def b64(name):
        return base64.b64encode((fonts / name).read_bytes()).decode()
    return (
        "@font-face { font-family: 'MNeon'; font-weight: 400; src: url(data:font/woff2;base64,"
        f"{b64('neon400.woff2')}) format('woff2'); }}\n"
        "@font-face { font-family: 'MNeon'; font-weight: 700; src: url(data:font/woff2;base64,"
        f"{b64('neon700.woff2')}) format('woff2'); }}\n"
        "@font-face { font-family: 'MXenon'; font-weight: 700; src: url(data:font/woff2;base64,"
        f"{b64('xenon700.woff2')}) format('woff2'); }}\n"
        "text { font-family: 'MNeon', ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, "
        "'DejaVu Sans Mono', monospace; text-rendering: geometricPrecision; }\n"
        ".d { font-family: 'MXenon', 'MNeon', ui-monospace, 'SF Mono', Menlo, Consolas, monospace; "
        "font-weight: 700; }\n"
    )


def load_icons(theme: str) -> dict:
    s = (ASSETS / f"stack-{theme}.svg").read_text()
    icons = {}
    for m in re.finditer(r'<g class="ico"[^>]*>(<svg.*?</svg>)</g><text[^>]*>([^<]+)</text>', s):
        inner = re.sub(r'^<svg[^>]*>', '', m.group(1))
        view = re.search(r'viewBox="([^"]+)"', m.group(1)).group(1)
        icons[m.group(2)] = (view, inner[:-len("</svg>")])
    return icons


def icon_svg(label, icons, x, y, size=14):
    if label in CUSTOM_ICONS:
        view, inner = "0 0 24 24", CUSTOM_ICONS[label]
    elif label in ICON_KEYS and ICON_KEYS[label] in icons:
        view, inner = icons[ICON_KEYS[label]]
    else:
        return ""
    return f'<svg x="{x:.1f}" y="{y:.1f}" width="{size}" height="{size}" viewBox="{view}">{inner}</svg>'


def has_icon(label, icons):
    return label in CUSTOM_ICONS or (label in ICON_KEYS and ICON_KEYS[label] in icons)


def wrap(text, width):
    lines, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    lines.append(cur)
    return lines


def svg_open(w, h, css, extra_css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img">\n<style>{css}{extra_css}</style>\n')


# --------------------------------------------------------------------------- header
def header(theme, fonts):
    c = THEMES[theme]
    W, H = 800, 176
    css = font_css(fonts) + (
        "@keyframes blink { 50% { opacity: 0; } }\n"
        ".cur { animation: blink 1.2s steps(1) infinite; }\n"
        "@media (prefers-reduced-motion: reduce) { .cur { animation: none !important; } }\n")
    tx, ty, ts = 44, 38, 100          # logo tile
    out = [svg_open(W, H, css)]
    out.append(
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{c["green"]}"/><stop offset="1" stop-color="{c["blue"]}"/>'
        f'</linearGradient>'
        f'<radialGradient id="glow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" '
        f'stop-color="{c["green"]}" stop-opacity=".22"/><stop offset="1" stop-color="{c["green"]}" '
        f'stop-opacity="0"/></radialGradient>'
        f'<pattern id="dots" width="16" height="16" patternUnits="userSpaceOnUse">'
        f'<circle cx="1" cy="1" r="1" fill="{c["border"]}"/></pattern>'
        f'<clipPath id="r"><rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12"/></clipPath></defs>\n')
    out.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="{c["bg"]}"/>')
    out.append(f'<g clip-path="url(#r)"><rect x="440" y="0" width="360" height="{H}" fill="url(#dots)" opacity=".55"/>'
               f'<rect x="440" y="0" width="120" height="{H}" fill="{c["bg"]}" opacity=".0"/>'
               f'<circle cx="{tx+ts/2}" cy="{ty+ts/2}" r="96" fill="url(#glow)"/></g>')
    out.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{c["border"]}"/>')
    # chip pins
    for off in (25, 50, 75):
        for (x1, y1, x2, y2) in ((tx - 9, ty + off, tx, ty + off), (tx + ts, ty + off, tx + ts + 9, ty + off),
                                 (tx + off, ty - 9, tx + off, ty), (tx + off, ty + ts, tx + off, ty + ts + 9)):
            out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c["green"]}" '
                       f'stroke-width="2" stroke-linecap="round" opacity=".6"/>')
    out.append(f'<rect x="{tx}" y="{ty}" width="{ts}" height="{ts}" rx="22" fill="{c["panel"]}" '
               f'stroke="url(#g)" stroke-width="2.5"/>')
    out.append(f'<rect x="{tx+8}" y="{ty+8}" width="{ts-16}" height="{ts-16}" rx="15" fill="none" '
               f'stroke="{c["border"]}" stroke-dasharray="2 5" stroke-linecap="round"/>')
    out.append(f'<circle cx="{tx+14}" cy="{ty+14}" r="2.5" fill="{c["green"]}"/>')
    out.append(f'<text class="d" x="{tx+ts/2-6}" y="{ty+ts/2+16}" text-anchor="middle" font-size="50" '
               f'fill="{c["text"]}">H<tspan fill="{c["green"]}">a</tspan></text>')
    out.append(f'<rect class="cur" x="{tx+ts/2+2}" y="{ty+ts/2+23}" width="24" height="4" rx="2" fill="{c["green"]}"/>')
    # text block
    x = 188
    out.append(f'<text class="d" x="{x}" y="74" font-size="32" fill="{c["text"]}">Tran Quang Ha</text>')
    out.append(f'<text x="{x}" y="102" font-size="12.5" fill="{c["muted"]}">'
               f'Backend engineer building AI-integrated systems: RAG, queues, real-time.</text>')
    pill = "Open to backend / full-stack internships"
    pw = len(pill) * 11 * CHAR_W + 40
    out.append(f'<rect x="{x}" y="118" width="{pw:.1f}" height="26" rx="13" fill="{c["green"]}" '
               f'fill-opacity=".12" stroke="{c["green"]}" stroke-opacity=".55"/>'
               f'<circle cx="{x+15}" cy="131" r="3.5" fill="{c["green"]}"/>'
               f'<text x="{x+27}" y="135" font-size="11" fill="{c["green"]}" font-weight="700">{escape(pill)}</text>')
    out.append("</svg>\n")
    return "".join(out)


# --------------------------------------------------------------------------- cards
CW, CH = 392, 176


def card_frame(c, fonts, body, dashed=False):
    css = font_css(fonts)
    dash = ' stroke-dasharray="5 4"' if dashed else ""
    top = "" if dashed else (
        f'<g clip-path="url(#r)"><rect x="0" y="0" width="{CW}" height="3" fill="url(#g)"/></g>')
    return (svg_open(CW, CH, css)
            + f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0">'
              f'<stop offset="0" stop-color="{c["green"]}"/><stop offset="1" stop-color="{c["blue"]}"/>'
              f'</linearGradient><clipPath id="r"><rect x=".5" y=".5" width="{CW-1}" height="{CH-1}" rx="12"/>'
              f'</clipPath></defs>\n'
            + f'<rect x=".5" y=".5" width="{CW-1}" height="{CH-1}" rx="12" fill="{c["bg"]}" '
              f'stroke="{c["border"]}"{dash}/>\n' + top + body + "</svg>\n")


def explore_link(c, label, y=158):
    return (f'<line x1="18" y1="{y-22}" x2="{CW-18}" y2="{y-22}" stroke="{c["border"]}"/>'
            f'<text x="18" y="{y}" font-size="12.5" font-weight="700" fill="{c["green"]}">{escape(label)}</text>'
            f'<text x="{CW-18}" y="{y}" text-anchor="end" font-size="14" font-weight="700" '
            f'fill="{c["green"]}">→</text>')


def project_card(p, theme, fonts, icons):
    c = THEMES[theme]
    b = [f'<text class="d" x="18" y="38" font-size="16" fill="{c["text"]}">{escape(p["name"])}</text>',
         f'<text x="{CW-18}" y="37" text-anchor="end" font-size="10.5" fill="{c["muted"]}">{escape(p["lang"])}</text>']
    lines = wrap(p["desc"], 46)
    assert len(lines) <= 2, (p["name"], lines)
    for i, ln in enumerate(lines):
        b.append(f'<text x="18" y="{62 + i*19}" font-size="12.5" fill="{c["muted"]}">{escape(ln)}</text>')
    x, y, fs = 18.0, 100.0, 11
    for label in p["chips"]:
        ic = has_icon(label, icons)
        w = len(label) * fs * CHAR_W + 18 + (19 if ic else 0)
        b.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="24" rx="6" fill="{c["chip"]}"/>')
        tx = x + 9
        if ic:
            b.append(icon_svg(label, icons, tx, y + 5))
            tx += 19
        b.append(f'<text x="{tx:.1f}" y="{y+16}" font-size="{fs}" fill="{c["text"]}">{escape(label)}</text>')
        x += w + 6
    assert x - 6 <= CW - 18 + 0.5, (p["name"], x)
    b.append(explore_link(c, "Explore repository"))
    return card_frame(c, fonts, "\n".join(b))


def more_card(theme, fonts):
    c = THEMES[theme]
    b = [f'<text class="d" x="18" y="38" font-size="16" fill="{c["text"]}">More projects</text>',
         f'<text x="18" y="62" font-size="12.5" fill="{c["muted"]}">Smaller experiments, templates and</text>',
         f'<text x="18" y="81" font-size="12.5" fill="{c["muted"]}">coursework live on GitHub.</text>']
    x = 18.0
    for label in ("React", "Flutter", "Python"):
        w = len(label) * 11 * CHAR_W + 18
        b.append(f'<rect x="{x:.1f}" y="100" width="{w:.1f}" height="24" rx="6" fill="{c["chip"]}"/>'
                 f'<text x="{x+9:.1f}" y="116" font-size="11" fill="{c["text"]}">{label}</text>')
        x += w + 6
    b.append(f'<text x="{x+2:.1f}" y="116" font-size="11" fill="{c["muted"]}">…</text>')
    b.append(explore_link(c, "View all repositories"))
    return card_frame(c, fonts, "\n".join(b), dashed=True)


def main():
    fonts = Path(sys.argv[1])
    for theme in THEMES:
        icons = load_icons(theme)
        (ASSETS / f"header-{theme}.svg").write_text(header(theme, fonts))
        for p in PROJECTS:
            (ASSETS / f"project-{p['slug']}-{theme}.svg").write_text(project_card(p, theme, fonts, icons))
        (ASSETS / f"project-more-{theme}.svg").write_text(more_card(theme, fonts))
    print("ok")


if __name__ == "__main__":
    main()
