"""
periodical_overview_qf_pdf.py – Kwartfinale update PDF for WK 2026 Familiepoel.

Usage:
    python periodical_overview_qf_pdf.py          # -> kwartfinale_overzicht.pdf
    python periodical_overview_qf_pdf.py out.pdf
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

from periodical_overview_pdf import (
    ab, esc, MONTH_NL, prefetch_flags, flag, html_to_pdf, CSS,
)
from calculate_qf_scores import (
    R16_STANDINGS, ACTUAL_RESULTS_QF, score_qf_submission,
    canonical_name,
)

SUBMISSIONS_DIR = Path("submissions_quarter_finals")

MATCHES_QF = [
    {"id": 1, "home": "Frankrijk",  "away": "Marokko",     "date": "9 jul",  "time": "22:00"},
    {"id": 2, "home": "Spanje",     "away": "België",      "date": "10 jul", "time": "21:00"},
    {"id": 3, "home": "Noorwegen",  "away": "Engeland",    "date": "11 jul", "time": "23:00"},
    {"id": 4, "home": "Argentinië", "away": "Zwitserland", "date": "12 jul", "time": "03:00"},
]

PAIR_COLORS = [
    "#f5b841", "#34d399", "#60a5fa", "#f472b6",
]

MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni",
           "juli", "augustus", "september", "oktober", "november", "december"]

EXTRA_CSS = """
.ts-pick { display:flex; align-items:center; justify-content:center; gap:6px; font-weight:700; font-size:12px; }
.ts-pick img { width:22px; height:16px; border-radius:3px; object-fit:cover; }
.ts-empty { color:#94a3b8; font-weight:300; font-size:16px; }
"""

TOPSCORER_SLOTS = 2


# ── Helpers ───────────────────────────────────────────────────────────────────
def result_dir(h, a):
    if h > a: return "home"
    if a > h: return "away"
    return "draw"

def match_to_date(m):
    day, mon = m["date"].strip().split()
    return date(2026, MONTH_NL[mon.lower()], int(day))

def date_range_str(matches):
    if not matches:
        return ""
    dates = [match_to_date(m) for m in matches]
    fmt_d = (lambda d: d.strftime("%#d %b")) if os.name == "nt" else (lambda d: d.strftime("%-d %b"))
    first, last = fmt_d(min(dates)), fmt_d(max(dates))
    return first if first == last else f"{first} – {last}"

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

def match_color(m):
    return PAIR_COLORS[(m["id"] - 1) % len(PAIR_COLORS)]

def get_upcoming_qf():
    future = [m for m in MATCHES_QF if m["id"] not in ACTUAL_RESULTS_QF]
    future.sort(key=lambda m: (match_to_date(m), m["id"]))
    return future

def get_past_qf():
    past = [m for m in MATCHES_QF if m["id"] in ACTUAL_RESULTS_QF]
    past.sort(key=lambda m: (match_to_date(m), m["id"]))
    return past

def load_qf_submissions():
    subs = []
    for f in sorted(SUBMISSIONS_DIR.glob("*.json")):
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception:
            continue
        if data.get("ronde") == "Kwartfinale":
            subs.append(data)
    subs.sort(key=lambda s: s.get("naam", "").lower())
    return subs


# ── Section builders ──────────────────────────────────────────────────────────
def build_qf_standings_section(submissions):
    sub_by_canon = {canonical_name(s.get("naam", "")): s for s in submissions}
    rows = []
    for name, r16_pts in R16_STANDINGS.items():
        sub = sub_by_canon.get(name)
        if sub:
            qf = score_qf_submission(sub)
        else:
            qf = {"match_total": 0, "topscorer": 0.0, "total": 0.0}
        combined = r16_pts + qf["total"]
        rows.append({
            "name":      name,
            "r16":       r16_pts,
            "qf_match":  qf["match_total"],
            "qf_topsc":  qf["topscorer"],
            "total":     combined,
        })
    rows.sort(key=lambda r: (-r["total"], r["name"].lower()))

    ranks = []
    for i, r in enumerate(rows):
        if i == 0 or r["total"] != rows[i - 1]["total"]:
            ranks.append(i + 1)
        else:
            ranks.append(ranks[-1])

    n_played = len(ACTUAL_RESULTS_QF)
    subtitle = f"Stand van {today_nl()} · {n_played} kwartfinale wedstrijd(en) gespeeld"

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
            f'{score_td(r["r16"])}'
            f'{score_td(r["qf_match"])}'
            f'{score_td(r["qf_topsc"])}'
            f'</tr>'
        )

    thead = ('<thead><tr><th></th>'
             '<th class="th-left">Deelnemer</th>'
             '<th>Totaal</th><th>t/m 1/8</th>'
             '<th>QF Wedstr.</th><th>QF Topsc.</th>'
             '</tr></thead>')
    tbody = "<tbody>" + "".join(tr_rows) + "</tbody>"

    return (f'<div class="page-header">'
            f'<div class="page-title">&#127942; WK 2026 &ndash; Kwartfinale Stand</div>'
            f'<div class="page-subtitle">{esc(subtitle)}</div>'
            f'</div>'
            f'<table class="st">{thead}{tbody}</table>')


def build_pred_table_qf(matches, submissions):
    match_headers = []
    for m in matches:
        color = match_color(m)
        match_headers.append(
            f'<th class="match-th" style="background:{color}">'
            f'<div class="match-th-inner">'
            f'<div class="match-group-date">{esc(m["date"])} &middot; {esc(m["time"])}</div>'
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
        name   = esc(sub.get("naam", "?"))
        voorsp = sub.get("voorspellingen", {}) or {}
        cells  = [f'<td class="col-name">{name}</td>']
        for m in matches:
            pred = voorsp.get(str(m["id"]), {})
            sh, sa = pred.get("score_thuis"), pred.get("score_uit")
            if sh is not None and sa is not None:
                score_html = (f'<div class="score-row"><div class="sc">{sh}</div>'
                              f'<span class="sc-sep">&#8211;</span>'
                              f'<div class="sc">{sa}</div></div>')
            else:
                score_html = '<div class="score-row"><div class="sc empty">&#8211;</div></div>'
            cells.append(f'<td class="pred-cell">{score_html}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")

    tbody = "<tbody>" + "".join(rows) + "</tbody>"
    return f'<table class="pred-table">{thead}{tbody}</table>'


def build_lookback_table_qf(matches, submissions):
    match_headers = []
    for m in matches:
        color  = match_color(m)
        actual = ACTUAL_RESULTS_QF.get(m["id"])
        if actual is not None:
            ah, aa = actual
            result_html = (f'<div class="actual-result">'
                           f'<div class="actual-sc">{ah}</div>'
                           f'<span class="actual-sep">&#8211;</span>'
                           f'<div class="actual-sc">{aa}</div>'
                           f'</div>')
        else:
            result_html = ('<div class="actual-result">'
                           '<div class="actual-sc pending">&#8211;</div>'
                           '</div>')
        match_headers.append(
            f'<th class="match-th" style="background:{color}">'
            f'<div class="match-th-inner">'
            f'<div class="match-group-date">{esc(m["date"])} &middot; {esc(m["time"])}</div>'
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
        name   = esc(sub.get("naam", "?"))
        voorsp = sub.get("voorspellingen", {}) or {}
        cells  = [f'<td class="col-name">{name}</td>']
        for m in matches:
            pred   = voorsp.get(str(m["id"]), {})
            sh, sa = pred.get("score_thuis"), pred.get("score_uit")
            actual = ACTUAL_RESULTS_QF.get(m["id"])

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
            cells.append(f'<td class="pred-cell{lb_cls}">{score_html}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")

    tbody = "<tbody>" + "".join(rows) + "</tbody>"
    return f'<table class="pred-table">{thead}{tbody}</table>'


def build_topscorer_section(submissions):
    head_cells = "".join(
        f'<th class="match-th" style="background:#1e3a5f">'
        f'<div class="match-th-inner"><div class="match-group-date">Topscorer {i + 1}</div></div></th>'
        for i in range(TOPSCORER_SLOTS)
    )
    thead = f'<thead><tr><th class="col-name">Deelnemer</th>{head_cells}</tr></thead>'

    rows = []
    for sub in submissions:
        name = esc(sub.get("naam", "?"))
        ts = sub.get("topscorers") or []
        ts = (list(ts) + [{}] * TOPSCORER_SLOTS)[:TOPSCORER_SLOTS]
        cells = [f'<td class="col-name">{name}</td>']
        for t in ts:
            team  = t.get("team", "") if isinstance(t, dict) else ""
            pname = t.get("name", "") if isinstance(t, dict) else ""
            if pname:
                cell = f'<div class="ts-pick">{flag(team)}<span>{esc(pname)}</span></div>'
            else:
                cell = '<div class="ts-pick ts-empty">&#8211;</div>'
            cells.append(f'<td class="pred-cell">{cell}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")

    tbody = "<tbody>" + "".join(rows) + "</tbody>"
    return (f'<div class="page-header">'
            f'<div class="page-title">&#9917; Topscorer-keuzes</div>'
            f'<div class="page-subtitle">Kwartfinale &middot; {len(submissions)} inzending(en)</div>'
            f'</div>'
            f'<table class="pred-table">{thead}{tbody}</table>')


def _pred_page(chunk, submissions, title, subtitle):
    table = build_pred_table_qf(chunk, submissions)
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
                f'<div class="lb-empty">Nog geen gespeelde kwartfinale wedstrijden om op terug te kijken.</div>')
    table = build_lookback_table_qf(chunk, submissions)
    return (f'<div class="page-header">'
            f'<div class="page-title">{title}</div>'
            f'<div class="page-subtitle">{esc(subtitle)}</div>'
            f'</div>'
            f'<div class="table-block">{table}</div>')


def build_html(upcoming, past, submissions):
    def chunks_of_4(lst):
        if not lst:
            return []
        return [lst[i:i + 4] for i in range(0, len(lst), 4)]

    up_chunks = chunks_of_4(upcoming)
    lb_chunks = chunks_of_4(past)
    up_range  = date_range_str(upcoming)
    lb_range  = date_range_str(past)

    pages = [build_qf_standings_section(submissions)]

    if up_chunks:
        for i, chunk in enumerate(up_chunks):
            suffix = " (vervolg)" if i > 0 else ""
            pages.append(_pred_page(chunk, submissions,
                                    f"&#128197; Komende kwartfinale wedstrijden{suffix}", up_range))

    for i, chunk in enumerate(lb_chunks):
        suffix = f" ({i + 1}/{len(lb_chunks)})" if len(lb_chunks) > 1 else ""
        pages.append(_lookback_page(chunk, submissions,
                                    f"&#128269; Terugblik Kwartfinale{suffix}", lb_range or ""))

    pages.append(build_topscorer_section(submissions))
    pages_html = "".join(
        f'<div class="page"><div class="wrap">{p}</div></div>' for p in pages
    )

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <title>WK 2026 &ndash; Kwartfinale overzicht</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap"
        rel="stylesheet">
  <style>{CSS}{EXTRA_CSS}</style>
</head>
<body>{pages_html}</body>
</html>"""


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    prefetch_flags()

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out  = Path(args[0]) if args else Path("kwartfinale_overzicht.pdf")

    upcoming    = get_upcoming_qf()
    past        = get_past_qf()
    submissions = load_qf_submissions()

    print(f"{len(submissions)} inzending(en) | "
          f"{len(upcoming)} komende | {len(past)} gespeelde kwartfinale wedstrijden.")

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
