#!/usr/bin/env python3
"""Generate the profile header and project card SVGs in assets/.

Usage:  python3 scripts/gen_assets.py <fonts-dir>
Needs:  pip install fonttools brotli   (used to measure text and read woff2)

<fonts-dir> must hold bric400.woff2, bric600.woff2, bric800.woff2 (Bricolage
Grotesque) and jb700.woff2 (JetBrains Mono Bold), subset to printable ASCII.
Brand icons are lifted from assets/stack-<theme>.svg, so keep those files.

To add a project: append a dict to PROJECTS, run the script, then add one <td>
to the table in README.md. Chips are listed in data-flow order.
"""
import base64
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

THEMES = {
    "dark": dict(bg="#0C1424", panel="#131E33", line="#2A3B5A", text="#EAF0FA", muted="#93A3BD",
                 signal="#FFB020", on_signal="#0C1424", data="#35C2B0",
                 tile="#EEF2F8", tile_ink="#0C1424"),
    "light": dict(bg="#FFFFFF", panel="#F3F6FB", line="#CBD5E5", text="#0F1B33", muted="#55637C",
                  signal="#FFB020", on_signal="#0C1424", data="#0E8F80",
                  tile="#0F1B33", tile_ink="#F3F6FB"),
}

PROJECTS = [
    dict(slug="smart-knowledge-hub", name="smart-knowledge-hub-backend",
         url="https://github.com/tqha1011/smart-knowledge-hub-backend",
         desc=["AI knowledge base: ask your documents,", "get answers with sources."],
         flow=["NestJS", "Redis", "pgvector", "Gemini"]),
    dict(slug="fitwork", name="FitworkBE-Nestjs",
         url="https://github.com/tqha1011/FitworkBE-Nestjs",
         desc=["Recruitment platform backend with AI", "resume evaluation and cited evidence."],
         flow=["NestJS", "Prisma", "PostgreSQL", "Redis"]),
    dict(slug="shoestore", name="ShoeStore",
         url="https://github.com/tqha1011/ShoeStore",
         desc=["Shoe e-commerce: Android app and", "ASP.NET Core API, optimistic locking."],
         flow=["Kotlin", "Jetpack Compose", "ASP.NET Core", "Docker"]),
]

# flow label -> icon key inside stack-<theme>.svg
ICON_KEYS = {"NestJS": "NestJS", "pgvector": "pgvector", "Redis": "Redis", "Gemini": "Gemini",
             "Prisma": "Prisma", "PostgreSQL": "PostgreSQL", "Docker": "Docker",
             "Jetpack Compose": "Jetpack Compose", "TypeScript": "TypeScript"}
CUSTOM_ICONS = {
    "Kotlin": '<path d="M0 24V0h24L12 12 24 24z" fill="#7F52FF"/>',
    "ASP.NET Core": '<rect x="1" y="1" width="22" height="22" rx="5" fill="#512BD4"/>'
                    '<path d="M7 17V7l10 10V7" fill="none" stroke="#fff" stroke-width="2.2" '
                    'stroke-linejoin="round"/>',
}

FONT_FILES = {"r": "bric400.woff2", "b": "bric600.woff2", "x": "bric800.woff2", "m": "jb700.woff2"}
_metrics = {}


def width(text, font, size):
    """Advance width of text in px for one of the embedded fonts (kerning ignored)."""
    if font not in _metrics:
        t = TTFont(FONTS / FONT_FILES[font])
        _metrics[font] = (t.getBestCmap(), t["hmtx"], t["head"].unitsPerEm)
    cmap, hmtx, upm = _metrics[font]
    return sum(hmtx[cmap[ord(ch)]][0] for ch in text) * size / upm


def font_css():
    def face(fam, wt, name):
        b = base64.b64encode((FONTS / name).read_bytes()).decode()
        return (f"@font-face {{ font-family: '{fam}'; font-weight: {wt}; "
                f"src: url(data:font/woff2;base64,{b}) format('woff2'); }}\n")
    return (face("Bric", 400, "bric400.woff2") + face("Bric", 600, "bric600.woff2")
            + face("Bric", 800, "bric800.woff2") + face("JB", 700, "jb700.woff2")
            + "text { font-family: 'Bric', ui-sans-serif, system-ui, 'Segoe UI', Helvetica, Arial, sans-serif; "
              "text-rendering: geometricPrecision; }\n"
            + ".m { font-family: 'JB', ui-monospace, 'SF Mono', Menlo, Consolas, monospace; font-weight: 700; }\n")


def load_icons(theme):
    s = (ASSETS / f"stack-{theme}.svg").read_text()
    icons = {}
    for m in re.finditer(r'<g class="ico"[^>]*>(<svg.*?</svg>)</g><text[^>]*>([^<]+)</text>', s):
        inner = re.sub(r'^<svg[^>]*>', '', m.group(1))
        view = re.search(r'viewBox="([^"]+)"', m.group(1)).group(1)
        icons[m.group(2)] = (view, inner[:-len("</svg>")])
    return icons


def icon_svg(label, icons, cx, cy, size=16):
    if label in CUSTOM_ICONS:
        view, inner = "0 0 24 24", CUSTOM_ICONS[label]
    else:
        view, inner = icons[ICON_KEYS[label]]
    return (f'<svg x="{cx - size/2:.1f}" y="{cy - size/2:.1f}" width="{size}" height="{size}" '
            f'viewBox="{view}">{inner}</svg>')


def svg_open(w, h, extra_css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img">\n<style>{font_css()}{extra_css}</style>\n')


# --------------------------------------------------------------------------- header
def header(theme):
    c = THEMES[theme]
    W, H = 800, 168
    tx, ty, tw, th = 44, 32, 118, 104
    bar_w, bar_h = 10, 54
    bx1, bx2 = tx + 16, tx + 16 + 38
    by = ty + 25
    mid = by + bar_h / 2
    run = bx2 - bx1 - bar_w - 10
    css = ("@keyframes hop { from { transform: translateX(0); } to { transform: translateX(%.1fpx); } }\n"
           ".pkt { animation: hop 1.8s cubic-bezier(.65,0,.35,1) infinite alternate; }\n"
           "@media (prefers-reduced-motion: reduce) { .pkt { animation: none !important; "
           "transform: translateX(%.1fpx); } }\n") % (run, run / 2)
    o = [svg_open(W, H, css)]
    o.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="14" fill="{c["bg"]}" stroke="{c["line"]}"/>')
    # logo tile: H = two queue lanes joined by a link a packet travels along, then "a"
    o.append(f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="22" fill="{c["tile"]}"/>')
    o.append(f'<rect x="{bx1}" y="{by}" width="{bar_w}" height="{bar_h}" rx="3" fill="{c["tile_ink"]}"/>')
    o.append(f'<rect x="{bx2}" y="{by}" width="{bar_w}" height="{bar_h}" rx="3" fill="{c["tile_ink"]}"/>')
    o.append(f'<rect x="{bx1+bar_w}" y="{mid-2:.1f}" width="{bx2-bx1-bar_w}" height="4" fill="{c["tile_ink"]}"/>')
    o.append(f'<circle class="pkt" cx="{bx1+bar_w+5}" cy="{mid:.1f}" r="5" fill="{c["signal"]}"/>')
    o.append(f'<text x="{bx2+bar_w+8}" y="{by+bar_h}" font-size="68" font-weight="800" '
             f'letter-spacing="-1" fill="{c["tile_ink"]}">a</text>')
    # text block
    x = tx + tw + 34
    o.append(f'<text x="{x}" y="76" font-size="38" font-weight="800" letter-spacing="-.8" '
             f'fill="{c["text"]}">Tran Quang Ha</text>')
    o.append(f'<text x="{x}" y="102" font-size="14" fill="{c["muted"]}">'
             f'Backend engineer building AI-integrated systems: RAG, queues, real-time.</text>')
    pill = "Open to backend / full-stack internships"
    pw = width(pill, "b", 12) + 36
    o.append(f'<rect x="{x}" y="114" width="{pw:.1f}" height="24" rx="12" fill="{c["panel"]}" stroke="{c["line"]}"/>'
             f'<circle cx="{x+14}" cy="126" r="3.5" fill="{c["data"]}"/>'
             f'<text x="{x+25}" y="130.5" font-size="12" font-weight="600" fill="{c["text"]}">{escape(pill)}</text>')
    o.append("</svg>\n")
    return "".join(o)


# --------------------------------------------------------------------------- cards
CW, CH = 392, 200
PAD = 20


def frame(c, body, dashed=False):
    dash = ' stroke-dasharray="5 4"' if dashed else ""
    return (svg_open(CW, CH)
            + f'<rect x=".5" y=".5" width="{CW-1}" height="{CH-1}" rx="12" fill="{c["bg"]}" '
              f'stroke="{c["line"]}"{dash}/>\n' + body + "</svg>\n")


def button(c, label, y, outline=False):
    w = width(label, "b", 12.5) + 20 + 22
    h = 28
    if outline:
        box = f'<rect x="{PAD}" y="{y}" width="{w:.1f}" height="{h}" rx="7" fill="none" stroke="{c["muted"]}"/>'
        ink = c["text"]
    else:
        box = f'<rect x="{PAD}" y="{y}" width="{w:.1f}" height="{h}" rx="7" fill="{c["signal"]}"/>'
        ink = c["on_signal"]
    cx = PAD + w - 14
    return (box + f'<text x="{PAD+12}" y="{y+18.5}" font-size="12.5" font-weight="600" fill="{ink}">{escape(label)}</text>'
            f'<path d="M{cx-2:.1f} {y+9.5} l4.5 4.5 -4.5 4.5" fill="none" stroke="{ink}" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def project_card(p, theme, icons):
    c = THEMES[theme]
    b = [f'<text class="m" x="{PAD}" y="38" font-size="15" fill="{c["text"]}">{escape(p["name"])}</text>']
    for i, ln in enumerate(p["desc"]):
        assert width(ln, "r", 13) < CW - 2 * PAD, (p["name"], ln)
        b.append(f'<text x="{PAD}" y="{62 + i*19}" font-size="13" fill="{c["muted"]}">{escape(ln)}</text>')
    n, r, cy = len(p["flow"]), 14, 111
    x0, x1 = PAD + r, CW - PAD - r
    step = (x1 - x0) / (n - 1)
    for i in range(n - 1):
        ax, bx = x0 + i * step + r + 3, x0 + (i + 1) * step - r - 3
        b.append(f'<line x1="{ax:.1f}" y1="{cy}" x2="{bx-4:.1f}" y2="{cy}" stroke="{c["data"]}" stroke-width="1.5"/>'
                 f'<path d="M{bx-5:.1f} {cy-3.5} l4 3.5 -4 3.5" fill="none" stroke="{c["data"]}" '
                 f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>')
    for i, label in enumerate(p["flow"]):
        cx = x0 + i * step
        b.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="{r}" fill="{c["panel"]}" stroke="{c["line"]}"/>')
        b.append(icon_svg(label, icons, cx, cy))
        anchor, lx = "middle", cx
        if i == 0:
            anchor, lx = "start", PAD
        elif i == n - 1:
            anchor, lx = "end", CW - PAD
        b.append(f'<text x="{lx:.1f}" y="{cy+r+16}" text-anchor="{anchor}" font-size="11" '
                 f'fill="{c["muted"]}">{escape(label)}</text>')
    b.append(button(c, "Explore repository", 156))
    return frame(c, "\n".join(b))


def more_card(theme):
    c = THEMES[theme]
    b = [f'<text x="{PAD}" y="38" font-size="17" font-weight="800" fill="{c["text"]}">More projects</text>',
         f'<text x="{PAD}" y="62" font-size="13" fill="{c["muted"]}">Smaller experiments, templates and</text>',
         f'<text x="{PAD}" y="81" font-size="13" fill="{c["muted"]}">coursework live on GitHub.</text>',
         button(c, "View all repositories", 156, outline=True)]
    return frame(c, "\n".join(b), dashed=True)


def main():
    for theme in THEMES:
        icons = load_icons(theme)
        (ASSETS / f"header-{theme}.svg").write_text(header(theme))
        for p in PROJECTS:
            (ASSETS / f"project-{p['slug']}-{theme}.svg").write_text(project_card(p, theme, icons))
        (ASSETS / f"project-more-{theme}.svg").write_text(more_card(theme))
    print("ok")


if __name__ == "__main__":
    FONTS = Path(sys.argv[1])
    main()
