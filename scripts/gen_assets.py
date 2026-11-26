#!/usr/bin/env python3
"""Generate the profile header, project cards and stack card SVGs in assets/.

Usage:  python3 scripts/gen_assets.py
Needs:  pip install fonttools brotli   (used only to measure text widths)

Fonts live in scripts/fonts (Instrument Sans 400/600/700, subset to printable
ASCII) and are embedded into every SVG as base64, so the images render
identically on GitHub. Brand icons live in scripts/icons.json.

To add a project: append a dict to PROJECTS, run the script, then add one <td>
to the table in README.md.
"""
import base64
import json
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONTS = Path(__file__).resolve().parent / "fonts"
ICONS = json.loads((Path(__file__).resolve().parent / "icons.json").read_text())

# One accent colour on neutral surfaces; everything else is text colour.
ACCENT = "#3438E8"

THEMES = {
    "light": dict(surface="#F4F5FB", line="#D5D9F2", text="#15142B", muted="#4B4A6B", icons="light", dots="#B9BFE8", glow=".16"),
    "dark": dict(surface="#1B1A36", line="#34335C", text="#F1F1FA", muted="#A9A8CC", icons="dark", dots="#4A4A86", glow=".30"),
}

PROJECTS = [
    dict(slug="bidtix", name="BidTix",
         desc=["Concert ticketing backend: booking and", "live auctions, built to never oversell."],
         tech=["Java", "Spring Boot", "PostgreSQL", "Redis"]),
    dict(slug="smart-knowledge-hub", name="smart-knowledge-hub-backend",
         desc=["AI knowledge base: ask your documents,", "get answers with sources."],
         tech=["NestJS", "Redis", "pgvector", "Gemini"]),
    dict(slug="fitwork", name="FitworkBE-Nestjs",
         desc=["Recruitment platform backend with AI", "resume evaluation and cited evidence."],
         tech=["NestJS", "Prisma", "PostgreSQL", "Redis"]),
    dict(slug="shoestore", name="ShoeStore",
         desc=["Shoe e-commerce: Android app and", "ASP.NET Core API, optimistic locking."],
         tech=["Kotlin", "Compose", "ASP.NET", "Docker"]),
]

STACK = [  # (group, items)
    ("Backend", ["Java", "Spring Boot", "TypeScript", "NestJS"]),
    ("Data", ["PostgreSQL", "pgvector", "Prisma", "Redis"]),
    ("Async & AI", ["BullMQ", "Socket.IO", "Gemini", "RAG"]),
    ("Infra", ["Docker", "Azure", "Cloudflare", "Vercel", "GitHub Actions"]),
    ("Learning", ["React", "Jetpack Compose"]),
]

ICON_ALIAS = {"Compose": "Jetpack Compose"}
CUSTOM_ICONS = {
    "Kotlin": '<path d="M0 24V0h24L12 12 24 24z" fill="#7F52FF"/>',
    "ASP.NET": '<rect x="1" y="1" width="22" height="22" rx="5" fill="#512BD4"/>'
               '<path d="M7 17V7l10 10V7" fill="none" stroke="#fff" stroke-width="2.2" '
               'stroke-linejoin="round"/>',
}

FONT_FILES = {"r": ("Inst", 400, "instrument-sans-400.woff2"), "b": ("Inst", 600, "instrument-sans-600.woff2"),
              "x": ("Inst", 700, "instrument-sans-700.woff2")}
RADIUS = 20
_metrics = {}


def width(text, font, size):
    """Advance width of text in px for one of the embedded fonts (kerning ignored)."""
    if font not in _metrics:
        t = TTFont(FONTS / FONT_FILES[font][2])
        _metrics[font] = (t.getBestCmap(), t["hmtx"], t["head"].unitsPerEm)
    cmap, hmtx, upm = _metrics[font]
    return sum(hmtx[cmap[ord(ch)]][0] for ch in text) * size / upm


def svg_open(w, h, fonts, extra_css=""):
    css = ""
    for key in fonts:
        fam, wt, name = FONT_FILES[key]
        b64 = base64.b64encode((FONTS / name).read_bytes()).decode()
        css += (f"@font-face {{ font-family: '{fam}'; font-weight: {wt}; "
                f"src: url(data:font/woff2;base64,{b64}) format('woff2'); }}\n")
    css += ("text { font-family: 'Inst', ui-sans-serif, system-ui, 'Segoe UI', Helvetica, Arial, sans-serif; "
            "font-weight: 400; text-rendering: geometricPrecision; }\n"
            ".b { font-weight: 600; }\n.x { font-weight: 700; }\n")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img">\n<style>{css}{extra_css}</style>\n')


def icon_svg(label, theme_icons, cx, cy, size=14):
    if label in CUSTOM_ICONS:
        view, inner = "0 0 24 24", CUSTOM_ICONS[label]
    else:
        view, inner = theme_icons[ICON_ALIAS.get(label, label)]
    return (f'<svg x="{cx - size/2:.1f}" y="{cy - size/2:.1f}" width="{size}" height="{size}" '
            f'viewBox="{view}">{inner}</svg>')


def entry(label, x, cy, size, icons, ink, icon_size=16, opacity=1):
    """Brand icon + label, no box; returns (svg, width)."""
    gap = 7
    svg = (f'<g opacity="{opacity}">' + icon_svg(label, icons, x + icon_size / 2, cy, icon_size) + '</g>'
           f'<text x="{x + icon_size + gap:.1f}" y="{cy + size*0.35:.1f}" font-size="{size}" '
           f'fill="{ink}">{escape(label)}</text>')
    return svg, icon_size + gap + width(label, "r", size)


def arrow(cx, cy, ink):
    return (f'<path d="M{cx-4.5} {cy+4.5} L{cx+4.5} {cy-4.5} M{cx-3} {cy-4.5} H{cx+4.5} V{cy+3}" fill="none" '
            f'stroke="{ink}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')


# --------------------------------------------------------------------------- header
def header(theme):
    c = THEMES[theme]
    W, H = 800, 200
    bars = [(46, 190), (10, 226), (62, 160)]  # x-offset, length
    ax, ay, bh, gap = 580, 46, 30, 20
    # One orchestrated moment: bars slide in one after another, then each job runs
    # across its bar three times (there, back, there) and rests at the far end.
    anim = "".join(f".b{i} {{ animation-delay: {i*0.15:.2f}s; }}\n.j{i} {{ animation-delay: {0.9 + i*0.4:.2f}s; }}\n"
                   for i in range(len(bars)))
    css = ("@keyframes enter { from { transform: translateX(300px); } }\n"
           "@keyframes run { to { transform: translateX(96px); } }\n"
           ".bar { animation: enter .6s cubic-bezier(.2,.8,.2,1) backwards; }\n"
           ".job { animation: run 1.6s cubic-bezier(.45,0,.35,1) 3 alternate both; }\n" + anim +
           "@media (prefers-reduced-motion: reduce) { .bar { animation: none !important; } "
           ".job { animation: none !important; transform: translateX(96px); } }\n")
    o = [svg_open(W, H, ["r", "b", "x"], css),
         f'<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="{RADIUS}"/></clipPath>'
         # Backdrop: a dot grid and a soft glow, both fading out before they reach the name.
         f'<pattern id="dots" width="16" height="16" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.1" fill="{c["dots"]}"/></pattern>'
         f'<linearGradient id="fade" x1="0" x2="1"><stop offset=".32" stop-color="#fff" stop-opacity="0"/>'
         f'<stop offset=".72" stop-color="#fff" stop-opacity="1"/></linearGradient>'
         f'<mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>'
         f'<radialGradient id="glow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{ACCENT}" stop-opacity="{c["glow"]}"/>'
         f'<stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></radialGradient></defs>',
         f'<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="{c["surface"]}"/>'
         f'<ellipse cx="{ax+150}" cy="{ay+bh*1.5+gap}" rx="300" ry="150" fill="url(#glow)"/>'
         f'<rect width="{W}" height="{H}" fill="url(#dots)" mask="url(#m)"/>']
    for i, (dx, ln) in enumerate(bars):
        y = ay + i * (bh + gap)
        o.append(f'<g class="bar b{i}"><rect x="{ax+dx}" y="{y}" width="{ln+80}" height="{bh}" rx="{bh/2}" fill="{ACCENT}"/>'
                 f'<circle class="job j{i}" cx="{ax+dx+bh/2}" cy="{y+bh/2}" r="9" fill="#fff"/></g>')
    o.append("</g>")
    o.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="{RADIUS}" fill="none" stroke="{c["line"]}"/>')
    x, name, ns = 44, "Tran Quang Ha", 48
    assert x + width(name, "x", ns) < ax + min(b[0] for b in bars) - 24, "name overlaps bars"
    o.append(f'<text class="x" x="{x}" y="80" font-size="{ns}" letter-spacing="-1.2" fill="{c["text"]}">{name}</text>')
    o.append(f'<text x="{x}" y="112" font-size="16" fill="{c["muted"]}">Backend engineer building AI-integrated systems:</text>')
    o.append(f'<text x="{x}" y="134" font-size="16" fill="{c["muted"]}">RAG, queues, real-time.</text>')
    pill = "Open to backend / full-stack internships"
    pw = width(pill, "b", 13) + 44
    o.append(f'<rect x="{x+.5}" y="150.5" width="{pw:.1f}" height="29" rx="14.5" fill="none" stroke="{c["line"]}"/>'
             f'<circle cx="{x+16}" cy="165" r="4" fill="{ACCENT}"/>'
             f'<text class="b" x="{x+30}" y="169.5" font-size="13" fill="{c["text"]}">{escape(pill)}</text>')
    o.append("</svg>\n")
    return "".join(o)


# --------------------------------------------------------------------------- cards
CW, CH, PAD = 392, 168, 24
BTN = 16  # arrow button radius
TECH_SIZE = 12.5


def _title_size():
    """One title size for every card: the largest at which the longest repo name still fits."""
    size = 21.0
    while any(width(p["name"], "x", size) > CW - 2 * PAD - 2 * BTN - 12 for p in PROJECTS):
        size -= 0.5
    return size


TITLE = _title_size()


def card_base(c):
    bx, by = CW - PAD - BTN, PAD + BTN
    return (f'<rect x=".5" y=".5" width="{CW-1}" height="{CH-1}" rx="{RADIUS}" fill="{c["surface"]}" '
            f'stroke="{c["line"]}"/>'
            f'<circle cx="{bx}" cy="{by}" r="{BTN}" fill="{ACCENT}"/>' + arrow(bx, by, "#fff"))


def card_text(c, title, desc):
    b = [f'<text class="x" x="{PAD}" y="{PAD+BTN+7}" font-size="{TITLE}" fill="{c["text"]}">{escape(title)}</text>']
    for i, ln in enumerate(desc):
        assert width(ln, "r", 13.5) < CW - 2 * PAD, ln
        b.append(f'<text x="{PAD}" y="{78 + i*20}" font-size="13.5" fill="{c["muted"]}">{escape(ln)}</text>')
    return b


def project_card(p, theme):
    c = THEMES[theme]
    icons = ICONS[c["icons"]]
    b = [card_base(c)] + card_text(c, p["name"], p["desc"])
    x, cy = PAD, CH - PAD - 8
    for t in p["tech"]:
        svg, w = entry(t, x, cy, TECH_SIZE, icons, c["text"], icon_size=15)
        b.append(svg); x += w + 20
    assert x - 20 <= CW - PAD, (p["name"], "tech row overflows")
    return svg_open(CW, CH, ["r", "b", "x"]) + "\n".join(b) + "</svg>\n"


# --------------------------------------------------------------------------- stack
def stack(theme):
    c = THEMES[theme]
    icons = ICONS[c["icons"]]
    W, row, label_w = 800, 48, 150
    H = row * len(STACK)
    o = [svg_open(W, H, ["r", "b", "x"])]
    for i, (group, items) in enumerate(STACK):
        cy = i * row + row / 2
        quiet = group == "Learning"  # not yet in daily use: muted text and icons
        o.append(f'<text class="x" x="4" y="{cy+5:.1f}" font-size="15" fill="{c["muted" if quiet else "text"]}">{escape(group)}</text>')
        x = label_w
        for it in items:
            svg, w = entry(it, x, cy, 14, icons, c["muted" if quiet else "text"], icon_size=18,
                           opacity=.6 if quiet else 1)
            o.append(svg); x += w + 28
        assert x - 28 < W - 4, group
        if i < len(STACK) - 1:
            o.append(f'<line x1="0" y1="{(i+1)*row}" x2="{W}" y2="{(i+1)*row}" stroke="{c["line"]}"/>')
    o.append("</svg>\n")
    return "".join(o)


def main():
    for theme in THEMES:
        (ASSETS / f"header-{theme}.svg").write_text(header(theme))
        for p in PROJECTS:
            (ASSETS / f"project-{p['slug']}-{theme}.svg").write_text(project_card(p, theme))
        (ASSETS / f"stack-{theme}.svg").write_text(stack(theme))
    print("ok")


if __name__ == "__main__":
    main()
