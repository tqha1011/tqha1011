#!/usr/bin/env python3
"""Generate the profile header, project cards and stack card SVGs in assets/.

Usage:  python3 scripts/gen_assets.py
Needs:  pip install fonttools brotli   (used only to measure text widths)

Fonts live in scripts/fonts (Syne Bold for display, Instrument Sans for text, both
subset to printable ASCII) and are embedded into every SVG as base64, so the
images render identically on GitHub. Brand icons live in scripts/icons.json.

To add a project: append a dict to PROJECTS (and an illustration in ART), run
the script, then add one <td> to the table in README.md.
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

# Palette: five flat colours used as identity colours, plus ink for text.
COBALT, TANGERINE, MINT, LEMON, LILAC = "#3438E8", "#FF6A2B", "#19C39B", "#FFD23F", "#B9A8FF"
INK, WHITE = "#15142B", "#FFFFFF"

# Only the stack card and the "more" card change with the GitHub theme.
THEMES = {
    "light": dict(surface="#EEF0FB", line="#D5D9F2", text=INK, muted="#4B4A6B",
                  chip="#FFFFFF", chip_line="#D5D9F2", chip_ink=INK, icons="light"),
    "dark": dict(surface="#1B1A36", line="#34335C", text="#F1F1FA", muted="#A9A8CC",
                 chip="#26254A", chip_line="#3C3B66", chip_ink="#F1F1FA", icons="dark"),
}

PROJECTS = [
    dict(slug="smart-knowledge-hub", name="smart-knowledge-hub-backend",
         url="https://github.com/tqha1011/smart-knowledge-hub-backend",
         desc=["AI knowledge base: ask your documents,", "get answers with sources."],
         tech=["NestJS", "Redis", "pgvector", "Gemini"],
         bg=COBALT, fg=WHITE, fg2="#E3E4FF", btn=WHITE, btn_ink=INK),
    dict(slug="fitwork", name="FitworkBE-Nestjs",
         url="https://github.com/tqha1011/FitworkBE-Nestjs",
         desc=["Recruitment platform backend with AI", "resume evaluation and cited evidence."],
         tech=["NestJS", "Prisma", "PostgreSQL", "Redis"],
         bg=TANGERINE, fg=INK, fg2="#3A1A12", btn=INK, btn_ink=WHITE),
    dict(slug="shoestore", name="ShoeStore",
         url="https://github.com/tqha1011/ShoeStore",
         desc=["Shoe e-commerce: Android app and", "ASP.NET Core API, optimistic locking."],
         tech=["Kotlin", "Compose", "ASP.NET", "Docker"],
         bg=MINT, fg=INK, fg2="#0B3A31", btn=INK, btn_ink=WHITE),
]

STACK = [  # (group, colour, items)
    ("Backend", COBALT, ["Java", "Spring Boot", "TypeScript", "NestJS"]),
    ("Data", TANGERINE, ["PostgreSQL", "pgvector", "Prisma", "Redis"]),
    ("Async & AI", MINT, ["BullMQ", "Socket.IO", "Gemini", "RAG"]),
    ("Infra", LILAC, ["Docker", "Azure", "Cloudflare", "Vercel", "GitHub Actions"]),
    ("Learning", LEMON, ["React", "Jetpack Compose"]),
]

ICON_ALIAS = {"Compose": "Jetpack Compose"}
CUSTOM_ICONS = {
    "Kotlin": '<path d="M0 24V0h24L12 12 24 24z" fill="#7F52FF"/>',
    "ASP.NET": '<rect x="1" y="1" width="22" height="22" rx="5" fill="#512BD4"/>'
               '<path d="M7 17V7l10 10V7" fill="none" stroke="#fff" stroke-width="2.2" '
               'stroke-linejoin="round"/>',
}

FONT_FILES = {"d": ("Syne", 700, "syne-700.woff2"),
              "r": ("Inst", 400, "instrument-sans-400.woff2"), "b": ("Inst", 600, "instrument-sans-600.woff2")}
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
            ".d { font-family: 'Syne', 'Inst', ui-sans-serif, system-ui, sans-serif; font-weight: 700; }\n"
            ".b { font-weight: 600; }\n")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img">\n<style>{css}{extra_css}</style>\n')


def icon_svg(label, theme_icons, cx, cy, size=14):
    if label in CUSTOM_ICONS:
        view, inner = "0 0 24 24", CUSTOM_ICONS[label]
    else:
        view, inner = theme_icons[ICON_ALIAS.get(label, label)]
    return (f'<svg x="{cx - size/2:.1f}" y="{cy - size/2:.1f}" width="{size}" height="{size}" '
            f'viewBox="{view}">{inner}</svg>')


def chip(label, x, y, h, size, fill, ink, icons, stroke=None, dash=False):
    """Pill with brand icon + label; returns (svg, width)."""
    pad_l, isz, gap, pad_r = h * 0.32, h * 0.54, 6, h * 0.42
    w = pad_l + isz + gap + width(label, "b", size) + pad_r + 1
    edge = ""
    if stroke:
        edge = f' stroke="{stroke}"' + (' stroke-dasharray="4 3"' if dash else "")
    return (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h/2}" fill="{fill}"{edge}/>'
            + icon_svg(label, icons, x + pad_l + isz / 2, y + h / 2, isz)
            + f'<text class="b" x="{x + pad_l + isz + gap:.1f}" y="{y + h/2 + size*0.35:.1f}" '
              f'font-size="{size}" fill="{ink}">{escape(label)}</text>', w)


def arrow(cx, cy, ink):
    return (f'<path d="M{cx-4.5} {cy+4.5} L{cx+4.5} {cy-4.5} M{cx-3} {cy-4.5} H{cx+4.5} V{cy+3}" fill="none" '
            f'stroke="{ink}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')


# --------------------------------------------------------------------------- header
def header():
    W, H, R = 800, 216, 26
    bars = [(LILAC, 40, 150), (LEMON, 8, 186), (MINT, 56, 130), (TANGERINE, 22, 170)]  # colour, x-offset, length
    ax, ay, bh, gap = 566, 31, 28, 14
    anim = "".join(f".j{i} {{ animation-delay: {i*0.55:.2f}s; }}\n" for i in range(4))
    css = ("@keyframes run { 0% { transform: translateX(0); opacity: 0; } 12% { opacity: 1; } "
           "80% { opacity: 1; } 100% { transform: translateX(96px); opacity: 0; } }\n"
           ".job { animation: run 3.4s cubic-bezier(.45,0,.35,1) infinite; }\n" + anim +
           "@media (prefers-reduced-motion: reduce) { .job { animation: none !important; "
           "opacity: 1; transform: translateX(38px); } }\n")
    o = [svg_open(W, H, ["d", "r", "b"], css),
         f'<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="{R}"/></clipPath></defs>',
         f'<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="{COBALT}"/>']
    for i, (col, dx, ln) in enumerate(bars):
        y = ay + i * (bh + gap)
        o.append(f'<rect x="{ax+dx}" y="{y}" width="{ln+80}" height="{bh}" rx="{bh/2}" fill="{col}"/>')
        o.append(f'<circle class="job j{i}" cx="{ax+dx+bh/2}" cy="{y+bh/2}" r="8.5" fill="{INK}"/>')
    o.append("</g>")
    x, name, ns = 44, "Tran Quang Ha", 46
    # Syne is wide: keep the name clear of the bars (a 24px gutter).
    assert x + width(name, "d", ns) - len(name) < ax + min(b[1] for b in bars) - 24, "name overlaps bars"
    o.append(f'<text class="d" x="{x}" y="88" font-size="{ns}" letter-spacing="-1" fill="{WHITE}">{name}</text>')
    o.append(f'<text x="{x}" y="123" font-size="16" fill="#E3E4FF">Backend engineer building AI-integrated systems:</text>')
    o.append(f'<text x="{x}" y="145" font-size="16" fill="#E3E4FF">RAG, queues, real-time.</text>')
    pill = "Open to backend / full-stack internships"
    pw = width(pill, "b", 13) + 44
    o.append(f'<rect x="{x}" y="165" width="{pw:.1f}" height="30" rx="15" fill="{LEMON}"/>'
             f'<circle cx="{x+16}" cy="180" r="4" fill="{INK}"/>'
             f'<text class="b" x="{x+30}" y="184.5" font-size="13" fill="{INK}">{escape(pill)}</text>')
    o.append("</svg>\n")
    return "".join(o)


# --------------------------------------------------------------------------- cards
CW, CH, PAD, CR = 392, 200, 20, 22
ART_X, ART_Y = 278, 58
CHIP_H, CHIP_SIZE = 26, 11.5


def art_hub(ox, oy):
    return (f'<rect x="{ox+22}" y="{oy}" width="60" height="74" rx="8" fill="#fff" opacity=".35"/>'
            f'<rect x="{ox+11}" y="{oy+6}" width="60" height="70" rx="8" fill="#fff" opacity=".6"/>'
            f'<rect x="{ox}" y="{oy+12}" width="62" height="66" rx="8" fill="#fff"/>'
            f'<rect x="{ox+10}" y="{oy+24}" width="34" height="5" rx="2.5" fill="{INK}" opacity=".25"/>'
            f'<rect x="{ox+6}" y="{oy+36}" width="50" height="11" rx="5.5" fill="{LEMON}"/>'
            f'<rect x="{ox+11}" y="{oy+39.5}" width="34" height="4" rx="2" fill="{INK}"/>'
            f'<rect x="{ox+10}" y="{oy+54}" width="40" height="5" rx="2.5" fill="{INK}" opacity=".25"/>'
            f'<rect x="{ox+10}" y="{oy+64}" width="24" height="5" rx="2.5" fill="{INK}" opacity=".25"/>'
            f'<circle cx="{ox+62}" cy="{oy+42}" r="9" fill="{INK}"/>'
            f'<text class="d" x="{ox+62}" y="{oy+45.5}" font-size="10" text-anchor="middle" fill="#fff">1</text>')


def art_resume(ox, oy):
    return (f'<rect x="{ox+6}" y="{oy+2}" width="64" height="76" rx="8" fill="#fff"/>'
            f'<circle cx="{ox+22}" cy="{oy+20}" r="8" fill="{INK}" opacity=".85"/>'
            f'<rect x="{ox+36}" y="{oy+14}" width="26" height="5" rx="2.5" fill="{INK}" opacity=".3"/>'
            f'<rect x="{ox+36}" y="{oy+23}" width="18" height="4" rx="2" fill="{INK}" opacity=".2"/>'
            f'<rect x="{ox+14}" y="{oy+40}" width="48" height="5" rx="2.5" fill="{INK}" opacity=".22"/>'
            f'<rect x="{ox+14}" y="{oy+51}" width="40" height="5" rx="2.5" fill="{INK}" opacity=".22"/>'
            f'<rect x="{ox+14}" y="{oy+62}" width="44" height="5" rx="2.5" fill="{INK}" opacity=".22"/>'
            f'<circle cx="{ox+78}" cy="{oy+60}" r="16" fill="{INK}" stroke="{TANGERINE}" stroke-width="3"/>'
            f'<path d="M{ox+71} {oy+60.5} l5 5 l9 -10" fill="none" stroke="#fff" stroke-width="3" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def art_shoe(ox, oy):
    oy += 8
    return (f'<path d="M4 50 V24 Q4 18 11 18 H30 Q34 32 48 34 L80 40 Q96 43 96 50 Z" '
            f'transform="translate({ox} {oy})" fill="#fff"/>'
            f'<rect x="{ox}" y="{oy+50}" width="100" height="13" rx="6.5" fill="{INK}"/>'
            f'<path d="M{ox+16} {oy+44} Q{ox+44} {oy+30} {ox+84} {oy+44}" fill="none" '
            f'stroke="{INK}" stroke-width="3.5" stroke-linecap="round"/>'
            f'<rect x="{ox+56}" y="{oy-6}" width="38" height="22" rx="11" fill="{INK}"/>'
            f'<text class="d" x="{ox+75}" y="{oy+9.5}" font-size="12" text-anchor="middle" fill="#fff">v2</text>')


ART = {"smart-knowledge-hub": art_hub, "fitwork": art_resume, "shoestore": art_shoe}


def _title_size():
    """One title size for every card: the largest at which the longest repo name still fits."""
    size = 20.0
    while any(width(p["name"], "b", size) > CW - 2 * PAD - 48 for p in PROJECTS):
        size -= 0.5
    return size


TITLE = _title_size()


def project_card(p):
    icons = ICONS["light"]  # chips are white on every theme
    b = [f'<rect width="{CW}" height="{CH}" rx="{CR}" fill="{p["bg"]}"/>']
    b.append(f'<circle cx="{CW-PAD-17}" cy="{PAD+17}" r="17" fill="{p["btn"]}"/>' + arrow(CW - PAD - 17, PAD + 17, p["btn_ink"]))
    b.append(f'<text class="b" x="{PAD}" y="{PAD+25}" font-size="{TITLE}" fill="{p["fg"]}">{escape(p["name"])}</text>')
    for i, ln in enumerate(p["desc"]):
        assert width(ln, "r", 13.5) < ART_X - PAD - 6, (p["name"], ln)
        b.append(f'<text x="{PAD}" y="{74 + i*20}" font-size="13.5" fill="{p["fg2"]}">{escape(ln)}</text>')
    b.append(ART[p["slug"]](ART_X, ART_Y))
    # tech chips, wrapped; bottom-anchored
    rows, row, rw = [], [], 0
    for t in p["tech"]:
        cw = chip(t, 0, 0, CHIP_H, CHIP_SIZE, "#fff", INK, icons)[1]
        if row and rw + cw > CW - 2 * PAD + 1:
            rows.append(row); row, rw = [], 0
        row.append((t, cw)); rw += cw + 5
    rows.append(row)
    assert len(rows) == 1, (p["name"], "tech chips wrap")
    y = CH - PAD - CHIP_H - (len(rows) - 1) * 34
    for row in rows:
        x = PAD
        for t, _ in row:
            svg, w = chip(t, x, y, CHIP_H, CHIP_SIZE, "#fff", INK, icons)
            b.append(svg); x += w + 5
        y += 34
    return svg_open(CW, CH, ["d", "r", "b"]) + "\n".join(b) + "</svg>\n"


def more_card(theme):
    c = THEMES[theme]
    b = [f'<rect x="1" y="1" width="{CW-2}" height="{CH-2}" rx="{CR-1}" fill="{c["surface"]}" '
         f'stroke="{COBALT}" stroke-width="2" stroke-dasharray="7 6"/>']
    b.append(f'<circle cx="{CW-PAD-17}" cy="{PAD+17}" r="17" fill="{COBALT}"/>' + arrow(CW - PAD - 17, PAD + 17, "#fff"))
    b.append(f'<text class="b" x="{PAD}" y="{PAD+25}" font-size="{TITLE}" fill="{c["text"]}">More projects</text>')
    b.append(f'<text x="{PAD}" y="74" font-size="13.5" fill="{c["muted"]}">Smaller experiments, templates and</text>')
    b.append(f'<text x="{PAD}" y="94" font-size="13.5" fill="{c["muted"]}">coursework live on GitHub.</text>')
    # tiles: three filled, one waiting
    x, y, s = PAD, CH - PAD - 40, 40
    for i, col in enumerate([COBALT, TANGERINE, MINT]):
        b.append(f'<rect x="{x + i*(s+10)}" y="{y}" width="{s}" height="{s}" rx="11" fill="{col}"/>')
    px = x + 3 * (s + 10)
    b.append(f'<rect x="{px+1}" y="{y+1}" width="{s-2}" height="{s-2}" rx="10" fill="none" stroke="{c["muted"]}" '
             f'stroke-width="2" stroke-dasharray="4 4"/>'
             f'<path d="M{px+s/2} {y+13} v14 M{px+s/2-7} {y+20} h14" stroke="{c["muted"]}" stroke-width="2.2" stroke-linecap="round"/>')
    b.append(f'<text class="b" x="{CW-PAD}" y="{CH-PAD-4}" font-size="13" text-anchor="end" fill="{c["text"]}">View all repositories</text>')
    return svg_open(CW, CH, ["d", "r", "b"]) + "\n".join(b) + "</svg>\n"


# --------------------------------------------------------------------------- stack
def stack(theme):
    c = THEMES[theme]
    icons = ICONS[c["icons"]]
    W, padx, label_w, row, ch = 800, 28, 156, 46, 30
    H = 2 * 26 + row * len(STACK) - (row - ch)
    o = [svg_open(W, H, ["d", "r", "b"]),
         f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="26" fill="{c["surface"]}" stroke="{c["line"]}"/>']
    y = 26
    for group, col, items in STACK:
        o.append(f'<circle cx="{padx+7}" cy="{y+ch/2}" r="7" fill="{col}"/>')
        o.append(f'<text class="d" x="{padx+24}" y="{y+ch/2+5.5}" font-size="16" fill="{c["text"]}">{escape(group)}</text>')
        x = padx + label_w
        learning = group == "Learning"
        for it in items:
            svg, w = chip(it, x, y, ch, 13, "none" if learning else c["chip"], c["chip_ink"], icons,
                          stroke=c["muted"] if learning else c["chip_line"], dash=learning)
            o.append(svg); x += w + 8
        assert x < W - padx, group
        y += row
    o.append("</svg>\n")
    return "".join(o)


def main():
    (ASSETS / "header.svg").write_text(header())
    for p in PROJECTS:
        (ASSETS / f"project-{p['slug']}.svg").write_text(project_card(p))
    for theme in THEMES:
        (ASSETS / f"project-more-{theme}.svg").write_text(more_card(theme))
        (ASSETS / f"stack-{theme}.svg").write_text(stack(theme))
    print("ok")


if __name__ == "__main__":
    main()
