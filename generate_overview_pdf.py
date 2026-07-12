"""
generate_overview_pdf.py  –  generates a PDF overview of a player's submission.

Uses Chrome/Edge headless for clean PDF output (no browser headers/footers).

Usage:
    python generate_overview_pdf.py submissions/voorspelling_jan.json
    python generate_overview_pdf.py submissions/    # batch: all JSONs in folder
"""

import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from matches import get_groups, get_group_matches, FLAG_CODES, GROUP_COLORS
from scoring import calculate_group_table

ABBR = {
    "Mexico": "MEX", "Zuid-Afrika": "ZAF", "Zuid-Korea": "KOR",
    "Tsjechië": "CZE", "Canada": "CAN", "Bosnië-Herzegovina": "BIH",
    "Qatar": "QAT", "Zwitserland": "SUI", "Brazilië": "BRA",
    "Marokko": "MAR", "Haïti": "HAI", "Schotland": "SCO",
    "USA": "USA", "Paraguay": "PAR", "Australië": "AUS",
    "Turkije": "TUR", "Duitsland": "GER", "Curaçao": "CUW",
    "Ivoorkust": "CIV", "Ecuador": "ECU", "Nederland": "NED",
    "Japan": "JPN", "Tunesië": "TUN", "Zweden": "SWE",
    "België": "BEL", "Egypte": "EGY", "Iran": "IRI",
    "Nieuw-Zeeland": "NZL", "Spanje": "ESP", "Kaapverdië": "CPV",
    "Saudi-Arabië": "KSA", "Uruguay": "URU", "Frankrijk": "FRA",
    "Senegal": "SEN", "Noorwegen": "NOR", "Irak": "IRQ",
    "Argentinië": "ARG", "Algerije": "ALG", "Oostenrijk": "AUT",
    "Jordanië": "JOR", "Portugal": "POR", "DR Congo": "COD",
    "Oezbekistan": "UZB", "Colombia": "COL", "Engeland": "ENG",
    "Kroatië": "CRO", "Ghana": "GHA", "Panama": "PAN",
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# Module-level cache: flag code → base64 data URI (populated by prefetch_flags)
FLAG_CACHE: dict = {}

def prefetch_flags():
    """Fetch all flag images in parallel and store as base64 data URIs."""
    codes = list(set(FLAG_CODES.values()))
    print(f"Vlaggen ophalen ({len(codes)} landen)...", end=" ", flush=True)

    def fetch_one(code):
        try:
            url = f"https://flagcdn.com/48x36/{code}.png"
            with urllib.request.urlopen(url, timeout=8) as r:
                data = r.read()
            return code, "data:image/png;base64," + base64.b64encode(data).decode()
        except Exception:
            return code, None

    with ThreadPoolExecutor(max_workers=15) as ex:
        for code, data in ex.map(fetch_one, codes):
            if data:
                FLAG_CACHE[code] = data
    print(f"{len(FLAG_CACHE)}/{len(codes)} opgehaald.")

def flag(team, size="40x30", cls="flag"):
    code = FLAG_CODES.get(team, "un")
    # Use embedded base64 when available so headless Chrome can render without network access
    src  = FLAG_CACHE.get(code) or f"https://flagcdn.com/{size}/{code}.png"
    return (f'<img src="{src}" class="{cls}" alt="{esc(team)}" '
            f'onerror="this.style.visibility=\'hidden\'">')

def ab(team):
    return ABBR.get(team, team[:3].upper())

def hex_to_rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


# ── Headless PDF ──────────────────────────────────────────────────────────────
def find_browser():
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return shutil.which("chrome") or shutil.which("msedge") or shutil.which("google-chrome")

def html_to_pdf(html_content, pdf_path):
    browser = find_browser()
    if not browser:
        return False, "Chrome/Edge niet gevonden"
    with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", encoding="utf-8", delete=False) as f:
        f.write(html_content)
        tmp = f.name
    try:
        subprocess.run([
            browser,
            "--headless=new", "--no-sandbox", "--disable-gpu",
            "--disable-extensions",
            "--run-all-compositor-stages-before-draw",
            "--print-to-pdf-no-header",
            f"--print-to-pdf={os.path.abspath(str(pdf_path))}",
            f"file:///{Path(tmp).as_posix()}",
        ], check=True, capture_output=True, timeout=30)
        return True, ""
    except Exception as e:
        return False, str(e)
    finally:
        os.unlink(tmp)


# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

@page { size: A4; margin: 0; }

html, body {
    background: #eaf0fb;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}

body {
    color: #1e293b;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 12px;
    line-height: 1.4;
}

/* Page padding replaces @page margins */
.wrap { padding: 0.9cm 1.1cm; }

/* ── Page header ──────────────────────────────────────────────────────────── */
.page-header {
    padding-bottom: 0.7rem;
    border-bottom: 2px solid #b8cce8;
    margin-bottom: 0.9rem;
}
.page-header-by   { font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.14em; color: #4a6888; margin-bottom: 0.15rem; }
.page-header-name { font-size: 1.7rem; font-weight: 900; color: #0f172a; letter-spacing: -0.02em; }

/* ── Section titles ───────────────────────────────────────────────────────── */
.sec-title {
    font-size: 0.62rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.12em; color: #3d5a7a; margin-bottom: 0.5rem;
}

/* ── Bonus section (no forced page break — flows into groups) ─────────────── */
.bonus-section { margin-bottom: 1rem; }

.bonus-row { display: grid; grid-template-columns: repeat(3,1fr); gap: 0.6rem; margin-bottom: 0.9rem; }

.bonus-card {
    background: #fff; border: 1px solid #b8cce8;
    border-top: 3px solid #3b82f6; border-radius: 9px; padding: 0.65rem 0.8rem;
}
.bonus-card-lbl { font-size: 0.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #334155; margin-bottom: 0.35rem; }
.bonus-card-val { font-size: 0.9rem; font-weight: 700; color: #0f172a; display: flex; align-items: center; gap: 7px; }
.bonus-card-val img { width: 28px; height: 21px; border-radius: 3px; }

/* ── Topscorers ───────────────────────────────────────────────────────────── */
.ts-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 6px; }

.ts-card {
    background: #fff; border: 1px solid #b8cce8; border-radius: 8px;
    padding: 6px 9px; display: flex; align-items: center; gap: 7px;
}
.ts-card.empty { opacity: 0.35; }
.ts-num {
    width: 18px; height: 18px; border-radius: 50%; background: #dde8f8;
    display: flex; align-items: center; justify-content: center;
    font-size: 9px; font-weight: 700; color: #334155; flex-shrink: 0;
}
.ts-card img { width: 24px; height: 18px; border-radius: 2px; object-fit: cover; flex-shrink: 0; }
.ts-name    { font-size: 0.75rem; font-weight: 700; color: #0f172a; }
.ts-country { font-size: 0.6rem; color: #4a6888; font-weight: 600; }

/* ── Group divider ────────────────────────────────────────────────────────── */
.groups-list { display: block; }

/* ── Group card: full width, header + side-by-side body ──────────────────── */
.group-card {
    border-radius: 10px; overflow: hidden;
    border: 1px solid #b8cce8;
    margin-bottom: 0.6rem;
    break-inside: avoid; page-break-inside: avoid;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
}

.group-hdr {
    display: flex; align-items: center; gap: 8px;
    padding: 6px 11px; color: #fff;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.group-badge {
    width: 24px; height: 24px; border-radius: 5px;
    background: rgba(255,255,255,0.28);
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 900;
}
.group-label { font-size: 0.82rem; font-weight: 800; }

/* Body splits into matches (left) + standings (right) */
.group-body {
    display: grid;
    grid-template-columns: 3fr 2fr;
    gap: 0;
}

.matches-col { padding: 5px 6px; }
.standings-col {
    padding: 5px 6px;
    border-left: 1px solid rgba(0,0,0,0.07);
    background: rgba(255,255,255,0.35);
}

/* ── Match rows ───────────────────────────────────────────────────────────── */
.match-row {
    display: grid;
    grid-template-columns: 1fr 80px 1fr 62px;
    align-items: center; gap: 3px;
    padding: 4px 5px; border-radius: 6px; margin-bottom: 2px;
    background: rgba(255,255,255,0.6);
    border-left: 3px solid transparent;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.match-row.is-joker   { background: #dbeafe; border-left-color: #2563eb; }
.match-row.is-casino  { background: #ffe4e6; border-left-color: #e11d48; }
.match-row.is-star    { background: #fef9c3; border-left-color: #ca8a04; }
.match-row.is-underdog{ background: #dcfce7; border-left-color: #16a34a; }

.t-left  { display: flex; align-items: center; justify-content: flex-end;  gap: 4px; }
.t-right { display: flex; align-items: center; justify-content: flex-start; gap: 4px; }
.flag    { width: 26px; height: 19px; border-radius: 2px; object-fit: cover; flex-shrink: 0; }

.t-ab             { font-weight: 800; font-size: 10.5px; letter-spacing: 0.06em; color: #1e293b; }
.t-ab.is-star-team{ color: #92400e; }
.t-ab.is-dog-team { color: #14532d; }
.team-mark        { font-size: 8px; }

.score-wrap { display: flex; align-items: center; justify-content: center; gap: 2px; }

.sc {
    background: #2563eb; border-radius: 5px; width: 25px; height: 25px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 12px; color: #fff; flex-shrink: 0;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.sc.empty { background: #e2e8f0; color: #94a3b8; border: 1px dashed #cbd5e1; }
.sc-sep   { color: #94a3b8; font-weight: 700; font-size: 9px; }

/* Bonus pill badges */
.badge-col { display: flex; flex-direction: column; gap: 2px; align-items: flex-start; }
.bp {
    font-size: 7.5px; font-weight: 800; border-radius: 3px;
    padding: 1px 4px; display: block; white-space: nowrap;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.bp-j { background: #bfdbfe; color: #1e40af; }
.bp-c { background: #fecdd3; color: #9f1239; }
.bp-s { background: #fef08a; color: #854d0e; }
.bp-u { background: #bbf7d0; color: #14532d; }

/* ── Standings (right column) ─────────────────────────────────────────────── */
.standings { border-radius: 0; }

.s-hdr, .s-row {
    display: grid;
    grid-template-columns: 14px 1fr 22px 24px 22px;
    align-items: center; gap: 2px; padding: 3px 5px;
}
.s-hdr {
    font-size: 7px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.06em; color: #64748b; background: rgba(0,0,0,0.06);
    border-radius: 4px; margin-bottom: 1px;
}
.s-row { font-size: 9.5px; color: #334155; border-bottom: 1px solid rgba(0,0,0,0.05); }
.s-row.qual {
    background: #bbf7d0; border-radius: 3px;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.s-row:last-child { border-bottom: none; }
.s-pos  { color: #94a3b8; font-weight: 600; text-align: center; }
.s-team { display: flex; align-items: center; gap: 4px; font-weight: 700; color: #0f172a; }
.s-team img { width: 17px; height: 13px; border-radius: 2px; object-fit: cover; }
.s-pts  { font-weight: 800; color: #b45309; text-align: center; }
.s-num  { text-align: center; color: #64748b; font-size: 9px; }

@media (max-width: 600px) {
    .bonus-row, .ts-grid { grid-template-columns: 1fr; }
    .group-body { grid-template-columns: 1fr; }
    .standings-col { border-left: none; border-top: 1px solid rgba(0,0,0,0.07); }
}
"""


# ── HTML builder ─────────────────────────────────────────────────────────────
def build_html(submission):
    name   = esc(submission.get("naam", "Onbekend"))
    extras = submission.get("extras", {}) or {}

    preds = {}
    for k, v in (submission.get("voorspellingen") or {}).items():
        sh = v.get("score_thuis")
        sa = v.get("score_uit")
        if sh is not None and sa is not None:
            preds[int(k)] = {"home": sh, "away": sa}

    joker_ids  = set(extras.get("jokers")  or [])
    casino_ids = set(extras.get("casinos") or [])
    star_team  = extras.get("star_team") or ""
    underdog   = extras.get("underdog")  or ""
    champion   = extras.get("champion")  or ""
    topscorers = extras.get("topscorers") or []

    # ── Header ───────────────────────────────────────────────────────────────
    header = f"""<div class="page-header">
  <div class="page-header-by">Inzending van</div>
  <div class="page-header-name">{name}</div>
</div>"""

    # ── Bonus cards ───────────────────────────────────────────────────────────
    def val_card(label, emoji, team):
        inner = f'{flag(team, "28x21")} {esc(team)}' if team else '&#8212;'
        return (f'<div class="bonus-card"><div class="bonus-card-lbl">{emoji} {label}</div>'
                f'<div class="bonus-card-val">{inner}</div></div>')

    ts_cards = []
    for i in range(1, 7):
        p    = topscorers[i - 1] if i <= len(topscorers) else {}
        team = (p.get("team") if isinstance(p, dict) else "") or ""
        nm   = (p.get("name") if isinstance(p, dict) else "") or ""
        if nm:
            ts_cards.append(
                f'<div class="ts-card"><div class="ts-num">{i}</div>'
                f'{flag(team, "24x18")}'
                f'<div><div class="ts-name">{esc(nm)}</div>'
                f'<div class="ts-country">{ab(team)}</div></div></div>'
            )
        else:
            ts_cards.append(
                f'<div class="ts-card empty"><div class="ts-num">{i}</div>'
                f'<div><div class="ts-name">&#8212;</div></div></div>'
            )

    bonus_section = f"""<div class="bonus-section">
  {header}
  <div class="sec-title">&#127918; Bonusvoorspellingen</div>
  <div class="bonus-row">
    {val_card("Wereldkampioen (+150)", "&#127942;", champion)}
    {val_card("Star-Team (&times;2)", "&#11088;", star_team)}
    {val_card("Underdog", "&#128058;", underdog)}
  </div>
  <div class="sec-title">&#9917; Topscorer-keuzes</div>
  <div class="ts-grid">{''.join(ts_cards)}</div>
</div>"""

    # ── Groups ────────────────────────────────────────────────────────────────
    def score_box(val):
        return f'<div class="sc">{val}</div>' if val is not None else '<div class="sc empty">&ndash;</div>'

    def team_cell(team, side):
        is_s  = star_team == team
        is_u  = underdog  == team
        cls   = "t-ab" + (" is-star-team" if is_s else " is-dog-team" if is_u else "")
        mark  = (' <span class="team-mark">&#11088;</span>' if is_s
                 else ' <span class="team-mark">&#128058;</span>' if is_u else "")
        if side == "left":
            return f'<div class="t-left"><span class="{cls}">{ab(team)}{mark}</span>{flag(team, "26x19")}</div>'
        return f'<div class="t-right">{flag(team, "26x19")}<span class="{cls}">{mark}{ab(team)}</span></div>'

    def match_row(m):
        mid  = m["id"]
        home, away = m["home"], m["away"]
        pred = preds.get(mid)
        h_sc = pred["home"] if pred else None
        a_sc = pred["away"] if pred else None

        is_j = mid in joker_ids
        is_c = mid in casino_ids
        is_s = bool(star_team) and star_team in (home, away)
        is_u = bool(underdog)  and underdog  in (home, away)

        cls = "match-row"
        if is_j:   cls += " is-joker"
        elif is_c: cls += " is-casino"
        elif is_s: cls += " is-star"
        elif is_u: cls += " is-underdog"

        badges = []
        if is_j: badges.append('<span class="bp bp-j">&#127183; JOKER</span>')
        if is_c: badges.append('<span class="bp bp-c">&#127920; CASINO</span>')
        if is_s: badges.append('<span class="bp bp-s">&#11088; STAR</span>')
        if is_u: badges.append('<span class="bp bp-u">&#128058; UNDERDOG</span>')

        return (f'<div class="{cls}">'
                f'{team_cell(home, "left")}'
                f'<div class="score-wrap">{score_box(h_sc)}'
                f'<span class="sc-sep">&ndash;</span>{score_box(a_sc)}</div>'
                f'{team_cell(away, "right")}'
                f'<div class="badge-col">{"".join(badges)}</div>'
                f'</div>')

    def standings_col(group):
        standing = calculate_group_table(group, preds)
        rows = ['<div class="standings">',
                '<div class="s-hdr"><span></span><span>Team</span>'
                '<span class="s-num">G</span>'
                '<span class="s-pts">Pts</span>'
                '<span class="s-num">+/-</span></div>']
        for i, t in enumerate(standing, 1):
            gd  = f"+{t['gd']}" if t['gd'] > 0 else str(t['gd'])
            cls = "s-row qual" if i <= 2 else "s-row"
            rows.append(
                f'<div class="{cls}">'
                f'<span class="s-pos">{i}</span>'
                f'<span class="s-team">{flag(t["team"], "17x13")} {ab(t["team"])}</span>'
                f'<span class="s-num">{t["played"]}</span>'
                f'<span class="s-pts">{t["pts"]}</span>'
                f'<span class="s-num">{gd}</span>'
                f'</div>'
            )
        rows.append('</div>')
        return "\n".join(rows)

    def group_card(group):
        color   = GROUP_COLORS.get(group, "#607d8b")
        r, g, b = hex_to_rgb(color)
        m_html  = "".join(match_row(m) for m in get_group_matches(group))
        return (f'<div class="group-card" style="'
                f'background:rgba({r},{g},{b},0.07);border-color:rgba({r},{g},{b},0.28)">'
                f'<div class="group-hdr" style="background:{color}">'
                f'<div class="group-badge">{group}</div>'
                f'<span class="group-label">Groep {group}</span></div>'
                f'<div class="group-body">'
                f'<div class="matches-col">{m_html}</div>'
                f'<div class="standings-col">{standings_col(group)}</div>'
                f'</div></div>')

    groups_html = "".join(group_card(g) for g in get_groups())

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>WK 2026 - {name}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap"
        rel="stylesheet">
  <style>{CSS}</style>
</head>
<body>
  <div class="wrap">
    {bonus_section}
    <div class="sec-title" style="margin-top:0.8rem">&#9917; Groepsfase</div>
    <div class="groups-list">{groups_html}</div>
  </div>
</body>
</html>"""


# ── Entry point ───────────────────────────────────────────────────────────────
def process(json_path, out_path):
    with open(json_path, encoding="utf-8") as f:
        sub = json.load(f)
    html    = build_html(sub)
    pdf_path = out_path.with_suffix(".pdf")
    ok, err  = html_to_pdf(html, pdf_path)
    if ok:
        print(f"Opgeslagen: {pdf_path}")
    else:
        html_path = out_path.with_suffix(".html")
        html_path.write_text(html, encoding="utf-8")
        print(f"PDF mislukt ({err}) — HTML opgeslagen: {html_path}")


def main():
    prefetch_flags()

    if len(sys.argv) < 2:
        print("Gebruik:")
        print("  python generate_overview_pdf.py <submission.json>")
        print("  python generate_overview_pdf.py <map/>    # batch")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"FOUT: niet gevonden: {input_path}")
        sys.exit(1)

    if input_path.is_dir():
        files = sorted(input_path.glob("*.json"))
        if not files:
            print(f"Geen JSON-bestanden in {input_path}")
            return
        out_dir = input_path / "pdfs"
        out_dir.mkdir(exist_ok=True)
        for jf in files:
            process(jf, out_dir / jf.stem)
    else:
        out = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_suffix(".pdf")
        process(input_path, out)


if __name__ == "__main__":
    main()
