"""
standings_visual_pdf.py  –  visual standings PDF for WK 2026 Familiepoel.

Reads actual results from calculate_scores.py and all submissions from submissions/.
Run whenever you want a fresh standings PDF.

Usage:
    python standings_visual_pdf.py             # → stand.pdf
    python standings_visual_pdf.py output.pdf
"""

import os, shutil, subprocess, sys, tempfile
from datetime import date
from pathlib import Path

from scoring import score_full_submission
from calculate_scores import (
    ACTUAL_RESULTS, ACTUAL_GROUP_STANDINGS,
    ACTUAL_CHAMPION, GOALS_BY_PLAYER, load_submissions,
)
from matches import MATCHES


# ── Helpers ───────────────────────────────────────────────────────────────────
MAANDEN = ["januari","februari","maart","april","mei","juni",
           "juli","augustus","september","oktober","november","december"]

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def fmt(v, dash_zero=False):
    """Format a score: int if whole, 1 decimal otherwise; '—' for zero when dash_zero=True."""
    if v == 0 and dash_zero:
        return "—"
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    if isinstance(v, float):
        return f"{v:.1f}"
    return str(v)

def today_nl():
    d = date.today()
    return f"{d.day} {MAANDEN[d.month - 1]} {d.year}"


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
    font-size: 13px;
    color: #1e293b;
    line-height: 1.4;
}

.wrap { padding: 0.85cm 1cm; }

/* ── Page header ──────────────────────────────────────────────────────────── */
.page-header {
    padding-bottom: 0.65rem;
    border-bottom: 2px solid #b8cce8;
    margin-bottom: 1.2rem;
}
.page-title    { font-size: 1.5rem; font-weight: 900; color: #0f172a; letter-spacing: -0.02em; }
.page-subtitle { font-size: 0.75rem; color: #5a7898; margin-top: 3px; }

/* ── Standings table ──────────────────────────────────────────────────────── */
.st {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.09);
}

/* ── Header row ──────────────────────────────────────────────────────────── */
.st thead tr {
    background: #1e3a5f;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
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

/* ── Body rows ───────────────────────────────────────────────────────────── */
.st tbody tr:nth-child(odd)  td { background: #fff; }
.st tbody tr:nth-child(even) td { background: #f4f8ff; }
.st tbody td { border-bottom: 1px solid #dde8f8; }
.st tbody tr:last-child td { border-bottom: none; }

/* Medal row colour overrides */
.r1 td { background: #fefce8 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.r2 td { background: #f8fafc !important; }
.r3 td { background: #fff8f2 !important; }

/* ── Rank cell ───────────────────────────────────────────────────────────── */
.c-rank {
    width: 46px; min-width: 46px;
    text-align: center; vertical-align: middle;
    padding: 16px 4px;
    font-size: 18px; line-height: 1;
    border-right: 1px solid #dde8f8;
    border-left: 4px solid transparent;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.r1 .c-rank { border-left-color: #f59e0b; }
.r2 .c-rank { border-left-color: #94a3b8; }
.r3 .c-rank { border-left-color: #b87333; }
.rank-n { font-size: 14px; font-weight: 900; color: #64748b; }

/* ── Name cell ───────────────────────────────────────────────────────────── */
.c-name {
    text-align: left; vertical-align: middle;
    padding: 16px 14px;
    font-weight: 800; font-size: 15px; color: #0f172a;
    border-right: 2px solid #b8cce8;
}
.r1 .c-name { color: #78350f; }

/* ── Total cell ──────────────────────────────────────────────────────────── */
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

/* ── Breakdown cells ─────────────────────────────────────────────────────── */
.c-sc {
    width: 78px; min-width: 78px;
    text-align: center; vertical-align: middle;
    padding: 16px 6px;
    font-size: 13px; font-weight: 600; color: #64748b;
    border-right: 1px solid #dde8f8;
}
.c-sc:last-child { border-right: none; }
.sc-z { color: #d1d5db; font-weight: 400; font-size: 12px; }
"""


# ── HTML builder ──────────────────────────────────────────────────────────────
def build_html(rows):
    n_played = len(ACTUAL_RESULTS)
    n_total  = len(MATCHES)

    if n_played == 0:
        subtitle = f"Stand van {today_nl()}"
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

    # Unicode medal codepoints
    medals = {1: "&#129351;", 2: "&#129352;", 3: "&#129353;"}

    def rank_html(rank):
        return medals.get(rank, f'<span class="rank-n">{rank}</span>')

    def score_td(v):
        return f'<td class="c-sc">{fmt(v)}</td>'

    tr_rows = []
    for r, rank in zip(rows, ranks):
        row_cls = {1: " class=\"r1\"", 2: " class=\"r2\"", 3: " class=\"r3\""}.get(rank, "")
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

    thead = (
        '<thead><tr>'
        '<th></th>'
        '<th class="th-left">Deelnemer</th>'
        '<th>Totaal</th>'
        '<th>Wedstrijden</th>'
        '<th>Topscorers</th>'
        '<th>Underdog</th>'
        '</tr></thead>'
    )
    tbody = "<tbody>" + "".join(tr_rows) + "</tbody>"

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <title>WK 2026 Familiepoel &ndash; Stand</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap"
        rel="stylesheet">
  <style>{CSS}</style>
</head>
<body>
  <div class="wrap">
    <div class="page-header">
      <div class="page-title">&#127942; WK 2026 &ndash; Stand</div>
      <div class="page-subtitle">{esc(subtitle)}</div>
    </div>
    <table class="st">{thead}{tbody}</table>
  </div>
</body>
</html>"""


# ── Chrome/Edge headless PDF ───────────────────────────────────────────────────
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
    submissions = load_submissions()
    if not submissions:
        print("Geen inzendingen gevonden in submissions/")
        sys.exit(1)

    rows = []
    for sub in submissions:
        br = score_full_submission(
            sub, ACTUAL_RESULTS, ACTUAL_GROUP_STANDINGS,
            ACTUAL_CHAMPION, GOALS_BY_PLAYER,
        )
        rows.append({"name": sub.get("naam", "?"), **br})

    rows.sort(key=lambda r: (-r["total"], r["name"].lower()))

    print(f"{len(rows)} deelnemer(s), {len(ACTUAL_RESULTS)} resultaat/resultaten ingevoerd.")

    out      = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("stand.pdf")
    html     = build_html(rows)
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
