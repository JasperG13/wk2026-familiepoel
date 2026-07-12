"""
periodical_overview_pdf.py  –  weekly update PDF for WK 2026 Familiepoel.

Generates a 5-page PDF:
  Page 1   : Current standings
  Pages 2-3: Predictions for the upcoming 6 matches  (3 per page)
  Pages 4-5: Lookback at the previous 6 matches      (3 per page)

Usage:
    python periodical_overview_pdf.py                   # → komende_wedstrijden.pdf
    python periodical_overview_pdf.py [output.pdf]
    python periodical_overview_pdf.py out.pdf --upcoming=8 --lookback=6
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
from datetime import date
from pathlib import Path

from matches import MATCHES, FLAG_CODES, GROUP_COLORS
from scoring import score_full_submission
from calculate_scores import (
    ACTUAL_RESULTS, ACTUAL_GROUP_STANDINGS,
    ACTUAL_CHAMPION, GOALS_BY_PLAYER,
)

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

MONTH_NL = {
    "jan": 1, "feb": 2, "mrt": 3, "apr": 4, "mei": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "okt": 10, "nov": 11, "dec": 12,
}

MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni",
           "juli", "augustus", "september", "oktober", "november", "december"]

PRIORITY_NAMES = ["Inez", "Jacqueline", "Hans", "Wouter"]


# ── Helpers ───────────────────────────────────────────────────────────────────
def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def ab(team):
    return ABBR.get(team, team[:3].upper())

def match_to_date(m):
    day, mon = m["date"].strip().split()
    return date(2026, MONTH_NL[mon.lower()], int(day))

def result_dir(h, a):
    if h > a: return "home"
    if a > h: return "away"
    return "draw"

def today_nl():
    d = date.today()
    return f"{d.day} {MAANDEN[d.month - 1]} {d.year}"

def fmt(v):
    if v == 0:
        return "0"
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    if isinstance(v, float):
        return f"{v:.1f}"
    return str(v)

def date_range_str(matches):
    if not matches:
        return ""
    dates = [match_to_date(m) for m in matches]
    first = min(dates).strftime("%-d %b") if os.name != "nt" else min(dates).strftime("%#d %b")
    last  = max(dates).strftime("%-d %b") if os.name != "nt" else max(dates).strftime("%#d %b")
    return first if first == last else f"{first} – {last}"

def get_upcoming(n=6):
    today = date.today()
    future = [m for m in MATCHES
              if m["id"] not in ACTUAL_RESULTS and match_to_date(m) >= today]
    future.sort(key=lambda m: (match_to_date(m), m["id"]))
    return future[:n]

def get_previous(n=6):
    past = [m for m in MATCHES if m["id"] in ACTUAL_RESULTS]
    past.sort(key=lambda m: (match_to_date(m), m["id"]), reverse=True)
    return past[:n]

def load_submissions():
    sub_dir = Path("submissions")
    if not sub_dir.exists():
        return []
    subs = []
    for f in sorted(sub_dir.glob("*.json")):
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception:
            continue
        if data.get("ronde"):
            continue  # knockout-phase submission, not group stage
        subs.append(data)

    def sort_key(s):
        naam = s.get("naam", "")
        try:
            return (PRIORITY_NAMES.index(naam), "")
        except ValueError:
            return (len(PRIORITY_NAMES), naam.lower())

    return sorted(subs, key=sort_key)


# ── Flag cache ────────────────────────────────────────────────────────────────
FLAG_CACHE: dict = {}

def prefetch_flags():
    codes = list(set(FLAG_CODES.values()))
    print(f"Vlaggen ophalen ({len(codes)} landen)...", end=" ", flush=True)

    def fetch_one(code):
        try:
            with urllib.request.urlopen(
                    f"https://flagcdn.com/48x36/{code}.png", timeout=8) as r:
                data = r.read()
            return code, "data:image/png;base64," + base64.b64encode(data).decode()
        except Exception:
            return code, None

    with ThreadPoolExecutor(max_workers=15) as ex:
        for code, data in ex.map(fetch_one, codes):
            if data:
                FLAG_CACHE[code] = data
    print(f"{len(FLAG_CACHE)}/{len(codes)} opgehaald.")

def flag(team, cls="flag"):
    code = FLAG_CODES.get(team, "un")
    src  = FLAG_CACHE.get(code) or f"https://flagcdn.com/48x36/{code}.png"
    return f'<img src="{src}" class="{cls}" alt="{esc(team)}" onerror="this.style.visibility=\'hidden\'">'


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
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 14px;
    color: #1e293b;
    line-height: 1.4;
}

.page { break-after: page; }
.wrap { padding: 0.85cm 1cm; }

/* ── Shared page header ──────────────────────────────────────────────────── */
.page-header {
    padding-bottom: 0.65rem;
    border-bottom: 2px solid #b8cce8;
    margin-bottom: 1rem;
}
.page-title    { font-size: 1.5rem; font-weight: 900; color: #0f172a; letter-spacing: -0.02em; }
.page-subtitle { font-size: 0.75rem; color: #5a7898; margin-top: 2px; }

/* ════════════════════════════════════════════════════════════════════════════
   STANDINGS (page 1)
════════════════════════════════════════════════════════════════════════════ */
.st {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.09);
}
.st thead tr {
    background: #1e3a5f;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.st thead th {
    color: rgba(255,255,255,0.7);
    font-size: 9px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.1em;
    padding: 10px 8px; text-align: center;
    border-right: 1px solid rgba(255,255,255,0.1);
}
.st thead th:last-child { border-right: none; }
.th-left { text-align: left !important; padding-left: 14px !important; }

.st tbody tr:nth-child(odd)  td { background: #fff; }
.st tbody tr:nth-child(even) td { background: #f4f8ff; }
.st tbody td { border-bottom: 1px solid #dde8f8; }
.st tbody tr:last-child td { border-bottom: none; }

.r1 td { background: #fefce8 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.r2 td { background: #f8fafc !important; }
.r3 td { background: #fff8f2 !important; }

.c-rank {
    width: 46px; min-width: 46px;
    text-align: center; vertical-align: middle;
    padding: 16px 4px; font-size: 18px; line-height: 1;
    border-right: 1px solid #dde8f8;
    border-left: 4px solid transparent;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.r1 .c-rank { border-left-color: #f59e0b; }
.r2 .c-rank { border-left-color: #94a3b8; }
.r3 .c-rank { border-left-color: #b87333; }
.rank-n { font-size: 14px; font-weight: 900; color: #64748b; }

.c-name {
    text-align: left; vertical-align: middle;
    padding: 16px 14px;
    font-weight: 800; font-size: 15px; color: #0f172a;
    border-right: 2px solid #b8cce8;
}
.r1 .c-name { color: #78350f; }

.c-total {
    width: 110px; min-width: 110px;
    text-align: center; vertical-align: middle;
    padding: 16px 10px;
    font-size: 26px; font-weight: 900; color: #1d4ed8;
    border-right: 2px solid #b8cce8;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.r1 .c-total { color: #b45309; }
.r2 .c-total { color: #374151; }

.c-sc {
    width: 78px; min-width: 78px;
    text-align: center; vertical-align: middle;
    padding: 16px 6px;
    font-size: 13px; font-weight: 600; color: #64748b;
    border-right: 1px solid #dde8f8;
}
.c-sc:last-child { border-right: none; }
.sc-z { color: #d1d5db; font-weight: 400; font-size: 12px; }

/* ════════════════════════════════════════════════════════════════════════════
   PREDICTIONS & LOOKBACK TABLES (pages 2-5, shared structure)
════════════════════════════════════════════════════════════════════════════ */
.table-block { margin-bottom: 1.2rem; }

.pred-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0 2px;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

/* ── Name column ─────────────────────────────────────────────────────────── */
.col-name {
    width: 115px; min-width: 115px;
    text-align: left; padding: 0 10px;
    font-weight: 800; font-size: 13px; color: #0f172a;
    background: #fff;
    border-right: 2px solid #ccdaef;
    vertical-align: middle;
}
th.col-name {
    font-size: 0.6rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; color: #6a8aaa;
    border-bottom: 1px solid rgba(255,255,255,0.2);
    padding: 7px 10px; background: #dde8f8;
}

/* ── Match header cells ───────────────────────────────────────────────────── */
.match-th {
    text-align: center; vertical-align: middle;
    border-bottom: 1px solid rgba(255,255,255,0.2);
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.match-th-inner { padding: 8px 6px; }

.match-group-date {
    font-size: 9px; font-weight: 700; letter-spacing: 0.08em;
    color: rgba(255,255,255,0.85); margin-bottom: 5px;
    text-transform: uppercase;
}
.match-teams {
    display: flex; align-items: center; justify-content: center; gap: 5px;
}
.match-teams img {
    width: 28px; height: 21px; border-radius: 3px; object-fit: cover;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.match-team-ab { font-weight: 900; font-size: 14px; color: #fff; letter-spacing: 0.04em; }
.match-vs { font-size: 10px; color: rgba(255,255,255,0.55); font-weight: 600; margin: 0 1px; }

/* ── Alternating row backgrounds ─────────────────────────────────────────── */
.pred-table tbody tr:nth-child(even) .col-name,
.pred-table tbody tr:nth-child(even) .pred-cell { background: #f4f8ff; }
.pred-table tbody tr:nth-child(odd)  .col-name,
.pred-table tbody tr:nth-child(odd)  .pred-cell { background: #fff; }

/* ── Prediction cells ─────────────────────────────────────────────────────── */
.pred-cell {
    text-align: center; vertical-align: middle;
    padding: 6px 6px;
    border-left: 1px solid #dde8f8;
    border-bottom: 1px solid #dde8f8;
}

/* Bonus-type cell tints (upcoming only) */
.pred-cell.is-joker   { background: #eff6ff !important; }
.pred-cell.is-casino  { background: #fff1f2 !important; }
.pred-cell.is-star    { background: #fefce8 !important; }
.pred-cell.is-underdog{ background: #f0fdf4 !important; }

/* ── Score boxes ─────────────────────────────────────────────────────────── */
.score-row { display: flex; align-items: center; justify-content: center; gap: 4px; margin-bottom: 4px; }

.sc {
    background: #2563eb; border-radius: 6px;
    width: 30px; height: 30px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 14px; color: #fff;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.sc.empty { background: #e2e8f0; color: #94a3b8; font-size: 16px; font-weight: 300; }
.sc-sep   { color: #94a3b8; font-size: 11px; font-weight: 700; }

/* ── Bonus badge pills ───────────────────────────────────────────────────── */
.bonus-row { display: flex; gap: 3px; justify-content: center; flex-wrap: wrap; min-height: 14px; }
.bp {
    font-size: 9px; font-weight: 800; border-radius: 4px;
    padding: 2px 5px; white-space: nowrap;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.bp-j { background: #bfdbfe; color: #1e40af; }
.bp-c { background: #fecdd3; color: #9f1239; }
.bp-s { background: #fef08a; color: #854d0e; }
.bp-u { background: #bbf7d0; color: #14532d; }

/* ════════════════════════════════════════════════════════════════════════════
   LOOKBACK ADDITIONS (pages 4-5)
════════════════════════════════════════════════════════════════════════════ */

/* Actual result block inside match header */
.actual-result {
    display: flex; align-items: center; justify-content: center; gap: 3px;
    margin-top: 5px;
}
.actual-sc {
    background: rgba(255,255,255,0.92); color: #1e293b;
    border-radius: 4px; width: 22px; height: 22px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 12px;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.actual-sc.pending {
    background: rgba(255,255,255,0.2); color: rgba(255,255,255,0.35);
    font-size: 18px; font-weight: 300;
}
.actual-sep { color: rgba(255,255,255,0.55); font-size: 11px; font-weight: 700; }

/* Result accuracy cell backgrounds */
.lb-exact   { background: #dcfce7 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.lb-correct { background: #fef9c3 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.lb-wrong   { background: #fee2e2 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }

/* Score box colour follows result accuracy */
.lb-exact   .sc { background: #16a34a; }
.lb-correct .sc { background: #d97706; }
.lb-wrong   .sc { background: #dc2626; }

/* Empty lookback placeholder */
.lb-empty {
    text-align: center; padding: 3rem 1rem;
    color: #94a3b8; font-size: 1rem; font-style: italic;
}
"""


# ── Section builders ──────────────────────────────────────────────────────────

MANUAL_BONUS = {
    "Inez": {"match_total": 100, "total": 100},
}

def build_standings_section(submissions):
    """Returns the standings page content (header + table HTML)."""
    rows = []
    for sub in submissions:
        br = score_full_submission(
            sub, ACTUAL_RESULTS, ACTUAL_GROUP_STANDINGS,
            ACTUAL_CHAMPION, GOALS_BY_PLAYER,
        )
        name = sub.get("naam", "?")
        bonus = MANUAL_BONUS.get(name, {})
        for k, v in bonus.items():
            br[k] = br.get(k, 0) + v
        rows.append({"name": name, **br})
    rows.sort(key=lambda r: (-r["total"], r["name"].lower()))

    n_played = len(ACTUAL_RESULTS)
    n_total  = len(MATCHES)
    if n_played == 0:
        subtitle = f"Stand van {today_nl()} · Toernooi nog niet begonnen"
    elif n_played == n_total:
        subtitle = f"Stand van {today_nl()} · Alle {n_total} wedstrijden gespeeld"
    else:
        subtitle = f"Stand van {today_nl()} · {n_played} van de {n_total} wedstrijden gespeeld"

    # Competition-style ranking: 1, 2, 2, 4, ...
    ranks = []
    for i, r in enumerate(rows):
        if i == 0 or r["total"] != rows[i - 1]["total"]:
            ranks.append(i + 1)
        else:
            ranks.append(ranks[-1])

    medals = {1: "&#129351;", 2: "&#129352;", 3: "&#129353;"}

    def rank_html(rank):
        return medals.get(rank, f'<span class="rank-n">{rank}</span>')

    def score_td(v):
        return f'<td class="c-sc">{fmt(v)}</td>'

    tr_rows = []
    for r, rank in zip(rows, ranks):
        row_cls = {1: ' class="r1"', 2: ' class="r2"', 3: ' class="r3"'}.get(rank, "")
        tr_rows.append(
            f'<tr{row_cls}>'
            f'<td class="c-rank">{rank_html(rank)}</td>'
            f'<td class="c-name">{esc(r["name"])}</td>'
            f'<td class="c-total">{fmt(r["total"])}</td>'
            f'{score_td(r["match_total"])}'
            f'{score_td(r["topscorer"])}'
            f'{score_td(r["underdog"])}'
            f'</tr>'
        )

    thead = ('<thead><tr><th></th>'
             '<th class="th-left">Deelnemer</th>'
             '<th>Totaal</th><th>Wedstrijden</th>'
             '<th>Topscorers</th><th>Underdog</th>'
             '</tr></thead>')
    tbody  = "<tbody>" + "".join(tr_rows) + "</tbody>"

    return (f'<div class="page-header">'
            f'<div class="page-title">&#127942; WK 2026 &ndash; Stand</div>'
            f'<div class="page-subtitle">{esc(subtitle)}</div>'
            f'</div>'
            f'<table class="st">{thead}{tbody}</table>')


def build_pred_table(matches, submissions):
    """One predictions table for a list of upcoming matches."""
    match_headers = []
    for m in matches:
        color = GROUP_COLORS.get(m["group"], "#607d8b")
        match_headers.append(
            f'<th class="match-th" style="background:{color}">'
            f'<div class="match-th-inner">'
            f'<div class="match-group-date">GR. {m["group"]} &middot; {esc(m["date"])}</div>'
            f'<div class="match-teams">'
            f'{flag(m["home"])}<span class="match-team-ab">{ab(m["home"])}</span>'
            f'<span class="match-vs">vs</span>'
            f'<span class="match-team-ab">{ab(m["away"])}</span>{flag(m["away"])}'
            f'</div></div></th>'
        )

    thead = ('<thead><tr><th class="col-name">Deelnemer</th>'
             + "".join(match_headers) + '</tr></thead>')

    rows = []
    for sub in submissions:
        name       = esc(sub.get("naam", "?"))
        extras     = sub.get("extras", {}) or {}
        voorsp     = sub.get("voorspellingen", {}) or {}
        joker_ids  = set(extras.get("jokers")  or [])
        casino_ids = set(extras.get("casinos") or [])
        star_team  = extras.get("star_team") or ""
        underdog   = extras.get("underdog")  or ""

        cells = [f'<td class="col-name">{name}</td>']
        for m in matches:
            mid  = str(m["id"])
            pred = voorsp.get(mid, {})
            sh, sa = pred.get("score_thuis"), pred.get("score_uit")

            is_j = m["id"] in joker_ids
            is_c = m["id"] in casino_ids
            is_s = bool(star_team) and star_team in (m["home"], m["away"])
            is_u = bool(underdog)  and underdog  in (m["home"], m["away"])

            cell_cls = "pred-cell"
            if is_j:   cell_cls += " is-joker"
            elif is_c: cell_cls += " is-casino"
            elif is_s: cell_cls += " is-star"
            elif is_u: cell_cls += " is-underdog"

            if sh is not None and sa is not None:
                score_html = (f'<div class="score-row"><div class="sc">{sh}</div>'
                              f'<span class="sc-sep">&#8211;</span>'
                              f'<div class="sc">{sa}</div></div>')
            else:
                score_html = '<div class="score-row"><div class="sc empty">&#8211;</div></div>'

            badges = []
            if is_j: badges.append('<span class="bp bp-j">&#127183; JOKER</span>')
            if is_c: badges.append('<span class="bp bp-c">&#127920; CASINO</span>')
            if is_s: badges.append(f'<span class="bp bp-s">&#11088; {ab(star_team)}</span>')
            if is_u: badges.append(f'<span class="bp bp-u">&#128058; {ab(underdog)}</span>')

            cells.append(f'<td class="{cell_cls}">{score_html}'
                         f'<div class="bonus-row">{"".join(badges)}</div></td>')

        rows.append("<tr>" + "".join(cells) + "</tr>")

    tbody = "<tbody>" + "".join(rows) + "</tbody>"
    return f'<table class="pred-table">{thead}{tbody}</table>'


def build_lookback_table(matches, submissions):
    """One lookback table for a list of past matches, with actual result display."""
    match_headers = []
    for m in matches:
        color  = GROUP_COLORS.get(m["group"], "#607d8b")
        actual = ACTUAL_RESULTS.get(m["id"])

        if actual is not None:
            ah, aa = actual
            result_html = (f'<div class="actual-result">'
                           f'<div class="actual-sc">{ah}</div>'
                           f'<span class="actual-sep">&#8211;</span>'
                           f'<div class="actual-sc">{aa}</div>'
                           f'</div>')
        else:
            result_html = (f'<div class="actual-result">'
                           f'<div class="actual-sc pending">&#8211;</div>'
                           f'</div>')

        match_headers.append(
            f'<th class="match-th" style="background:{color}">'
            f'<div class="match-th-inner">'
            f'<div class="match-group-date">GR. {m["group"]} &middot; {esc(m["date"])}</div>'
            f'<div class="match-teams">'
            f'{flag(m["home"])}<span class="match-team-ab">{ab(m["home"])}</span>'
            f'<span class="match-vs">vs</span>'
            f'<span class="match-team-ab">{ab(m["away"])}</span>{flag(m["away"])}'
            f'</div>'
            f'{result_html}'
            f'</div></th>'
        )

    thead = ('<thead><tr><th class="col-name">Deelnemer</th>'
             + "".join(match_headers) + '</tr></thead>')

    rows = []
    for sub in submissions:
        name       = esc(sub.get("naam", "?"))
        extras     = sub.get("extras", {}) or {}
        voorsp     = sub.get("voorspellingen", {}) or {}
        joker_ids  = set(extras.get("jokers")  or [])
        casino_ids = set(extras.get("casinos") or [])
        star_team  = extras.get("star_team") or ""
        underdog   = extras.get("underdog")  or ""

        cells = [f'<td class="col-name">{name}</td>']
        for m in matches:
            mid    = str(m["id"])
            pred   = voorsp.get(mid, {})
            sh, sa = pred.get("score_thuis"), pred.get("score_uit")
            actual = ACTUAL_RESULTS.get(m["id"])

            # Result accuracy
            lb_cls = ""
            if actual is not None and sh is not None and sa is not None:
                ah, aa = actual
                if (ah, aa) == (sh, sa):
                    lb_cls = " lb-exact"
                elif result_dir(ah, aa) == result_dir(sh, sa):
                    lb_cls = " lb-correct"
                else:
                    lb_cls = " lb-wrong"

            if sh is not None and sa is not None:
                score_html = (f'<div class="score-row"><div class="sc">{sh}</div>'
                              f'<span class="sc-sep">&#8211;</span>'
                              f'<div class="sc">{sa}</div></div>')
            else:
                score_html = '<div class="score-row"><div class="sc empty">&#8211;</div></div>'

            # Badges still shown so people know what bonuses were at stake
            is_j = m["id"] in joker_ids
            is_c = m["id"] in casino_ids
            is_s = bool(star_team) and star_team in (m["home"], m["away"])
            is_u = bool(underdog)  and underdog  in (m["home"], m["away"])
            badges = []
            if is_j: badges.append('<span class="bp bp-j">&#127183; JOKER</span>')
            if is_c: badges.append('<span class="bp bp-c">&#127920; CASINO</span>')
            if is_s: badges.append(f'<span class="bp bp-s">&#11088; {ab(star_team)}</span>')
            if is_u: badges.append(f'<span class="bp bp-u">&#128058; {ab(underdog)}</span>')

            cells.append(f'<td class="pred-cell{lb_cls}">{score_html}'
                         f'<div class="bonus-row">{"".join(badges)}</div></td>')

        rows.append("<tr>" + "".join(cells) + "</tr>")

    tbody = "<tbody>" + "".join(rows) + "</tbody>"
    return f'<table class="pred-table">{thead}{tbody}</table>'


def _pred_page(chunk, submissions, title, subtitle):
    table = build_pred_table(chunk, submissions)
    return (f'<div class="page-header">'
            f'<div class="page-title">{title}</div>'
            f'<div class="page-subtitle">{esc(subtitle)}</div>'
            f'</div>'
            f'<div class="table-block">{table}</div>')


def _lookback_page(chunk, submissions, title, subtitle):
    if not chunk:
        return (f'<div class="page-header">'
                f'<div class="page-title">{title}</div>'
                f'<div class="page-subtitle">{esc(subtitle)}</div>'
                f'</div>'
                f'<div class="lb-empty">Nog geen gespeelde wedstrijden om op terug te kijken.</div>')
    table = build_lookback_table(chunk, submissions)
    return (f'<div class="page-header">'
            f'<div class="page-title">{title}</div>'
            f'<div class="page-subtitle">{esc(subtitle)}</div>'
            f'</div>'
            f'<div class="table-block">{table}</div>')


def build_html(upcoming, past, submissions):
    # Split each section into pages of 4 matches; pad to exactly 2 pages each
    def chunks_of_4(lst):
        pages = [lst[i:i+4] for i in range(0, max(len(lst), 1), 4)]
        while len(pages) < 2:
            pages.append([])
        return pages[:2]

    up_chunks  = chunks_of_4(upcoming)
    lb_chunks  = chunks_of_4(past)
    up_range   = date_range_str(upcoming)
    lb_range   = date_range_str(past)

    pages = [
        build_standings_section(submissions),
        _pred_page(up_chunks[0], submissions,
                   "&#128197; Komende wedstrijden", up_range),
        _pred_page(up_chunks[1], submissions,
                   "&#128197; Komende wedstrijden (vervolg)",
                   up_range if up_chunks[1] else ""),
        _lookback_page(lb_chunks[0], submissions,
                       "&#128269; Terugblik", lb_range or "Nog geen gespeelde wedstrijden"),
        _lookback_page(lb_chunks[1], submissions,
                       "&#128269; Terugblik (vervolg)",
                       lb_range if lb_chunks[1] else ""),
    ]

    pages_html = "".join(
        f'<div class="page"><div class="wrap">{p}</div></div>'
        for p in pages
    )

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <title>WK 2026 &ndash; Weekoverzicht</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap"
        rel="stylesheet">
  <style>{CSS}</style>
</head>
<body>{pages_html}</body>
</html>"""


# ── Chrome headless ───────────────────────────────────────────────────────────
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


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    prefetch_flags()

    args     = [a for a in sys.argv[1:] if not a.startswith("--")]
    n_up_arg = next((a.split("=")[1] for a in sys.argv[1:] if a.startswith("--upcoming=")), None)
    n_lb_arg = next((a.split("=")[1] for a in sys.argv[1:] if a.startswith("--lookback=")), None)
    n_up     = int(n_up_arg) if n_up_arg else 8
    n_lb     = int(n_lb_arg) if n_lb_arg else 8
    out      = Path(args[0]) if args else Path("komende_wedstrijden.pdf")

    upcoming    = get_upcoming(n_up)
    past        = get_previous(n_lb)
    submissions = load_submissions()

    print(f"{len(submissions)} inzending(en) | "
          f"{len(upcoming)} aankomende | {len(past)} vorige wedstrijden.")

    html     = build_html(upcoming, past, submissions)
    pdf_path = out.with_suffix(".pdf")
    ok, err  = html_to_pdf(html, pdf_path)

    if ok:
        print(f"Opgeslagen: {pdf_path}")
    else:
        html_path = out.with_suffix(".html")
        Path(html_path).write_text(html, encoding="utf-8")
        print(f"PDF mislukt ({err}) — HTML opgeslagen: {html_path}")


if __name__ == "__main__":
    main()
