# calculate_r16_scores.py – compute standings for Achtste Finale (Round of 16)

import json
from pathlib import Path

from players import player_position, POSITION_POINTS

SUBMISSIONS_DIR = "submissions_8th_finals"

# Submission "naam" fields that differ from R32_STANDINGS keys
NAME_MAP = {
    "Bart de beste":     "Bart",
    "Caroline":          "Caroline Vernooij",
    "Jacqueline Vernooij": "Jacqueline",
    "Kirsten":           "Kirsten Mekes",
}

# ── Hardcoded final R32 standings ─────────────────────────────────────────────
R32_STANDINGS = {
    "Caroline Vernooij": 1032.0,
    "Karlijn":           979.5,
    "Kirsten Mekes":     975.0,
    "Jacqueline":        904.5,
    "Hans":              900.5,
    "Thijs":             879.0,
    "Jasper":            852.0,
    "wouter":            812.0,
    "Carlijne":          810.0,
    "Inez":              793.0,
    "Bart":              780.0,
}

# ── R16 scoring constants (×1.5 vs R32, ×3 vs group stage) ───────────────────
PTS_R16_CORRECT = 30
PTS_R16_EXACT   = 45

# Topscorer points per goal = ×1.5 vs R32
R16_POSITION_POINTS = {pos: int(pts * 1.5) for pos, pts in {
    "Aanvaller":   12,
    "Middenvelder": 24,
    "Verdediger":  48,
}.items()}
# → Aanvaller: 18 pt, Middenvelder: 36 pt, Verdediger: 72 pt

# ── Fill these in as the Achtste Finale progresses ────────────────────────────
ACTUAL_RESULTS_R16 = {
    1: (0, 3),  # Canada – Marokko
    2: (0, 1),  # Paraguay – Frankrijk
    3: (1, 2),  # Brazilië – Noorwegen
    4: (2, 3),  # Mexico – Engeland
    5: (0, 1),  # Portugal – Spanje
    6: (1, 4),  # USA – België
    7: (3, 2),  # Argentinië – Egypte
    8: (0, 0),  # Zwitserland – Colombia (Zwitserland wint pen.)
}

GOALS_BY_PLAYER_R16 = {
    # Match 1 – Canada 0-3 Marokko
    ("Marokko",    "Azzedine Ounahi"):   {1: 2},
    ("Marokko",    "Soufiane Rahimi"):   {1: 1},
    # Match 2 – Paraguay 0-1 Frankrijk
    ("Frankrijk",  "Kylian Mbappé"):     {2: 1},
    # Match 3 – Brazilië 1-2 Noorwegen
    ("Noorwegen",  "Erling Haaland"):    {3: 2},
    ("Brazilië",   "Neymar"):            {3: 1},
    # Match 4 – Mexico 2-3 Engeland
    ("Engeland",   "Jude Bellingham"):   {4: 2},
    ("Engeland",   "Harry Kane"):        {4: 1},
    ("Mexico",     "Julián Quiñones"):   {4: 1},
    ("Mexico",     "Raúl Jiménez"):      {4: 1},
    # Match 5 – Portugal 0-1 Spanje
    ("Spanje",     "Mikel Merino"):      {5: 1},
    # Match 6 – USA 1-4 België
    ("België",     "Charles De Ketelaere"): {6: 2},
    ("België",     "Hans Vanaken"):      {6: 1},
    ("België",     "Romelu Lukaku"):     {6: 1},
    ("USA",        "Malik Tillman"):     {6: 1},
    # Match 7 – Argentinië 3-2 Egypte — Enzo Fernández not in players.py, skipped
    ("Argentinië", "Cristian Romero"):   {7: 1},
    ("Argentinië", "Lionel Messi"):      {7: 1},
    ("Egypte",     "Yasser Ibrahim"):    {7: 1},
    # Match 8 – Zwitserland 0-0 Colombia (pen.) — no goals
}


def score_r16_submission(sub):
    """
    Returns dict with match_total, topscorer, total (R16 points only).
    No bonuses — clean scoring only.
    """
    voorspel   = sub.get("voorspellingen", {}) or {}
    topscorers = sub.get("topscorers") or []

    match_points = 0
    for mid_str, pred in voorspel.items():
        mid = int(mid_str)
        if mid not in ACTUAL_RESULTS_R16:
            continue
        ah, aa = ACTUAL_RESULTS_R16[mid]
        ph = pred.get("score_thuis")
        pa = pred.get("score_uit")
        if ph is None or pa is None:
            continue
        if ph == ah and pa == aa:
            match_points += PTS_R16_EXACT
        elif (ph > pa) == (ah > aa) and (ph == pa) == (ah == aa):
            match_points += PTS_R16_CORRECT

    topscorer_points = 0.0
    for pick in topscorers:
        team = pick.get("team", "") if isinstance(pick, dict) else ""
        name = pick.get("name", "") if isinstance(pick, dict) else ""
        if not team or not name:
            continue
        pos = player_position(team, name)
        pts_per_goal = R16_POSITION_POINTS.get(pos, 0)
        if pts_per_goal == 0:
            continue
        goals_map = GOALS_BY_PLAYER_R16.get((team, name), {})
        for mid, goals in goals_map.items():
            topscorer_points += goals * pts_per_goal

    return {
        "match_total": match_points,
        "topscorer":   topscorer_points,
        "total":       match_points + topscorer_points,
    }


def canonical_name(raw):
    return NAME_MAP.get(raw, raw)


def load_r16_submissions():
    subs = []
    for f in sorted(Path(SUBMISSIONS_DIR).glob("*.json")):
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception:
            continue
        if data.get("ronde") == "Achtste Finale":
            subs.append(data)
    subs.sort(key=lambda s: s.get("naam", "").lower())
    return subs


def main():
    submissions = load_r16_submissions()
    print(f"{'Deelnemer':<16}  {'R32':>7}  {'R16 wedstr':>10}  {'R16 topsc':>9}  {'R16 totaal':>10}  {'Eindstand':>10}")
    print("-" * 72)

    rows = []
    for sub in submissions:
        raw_name = sub.get("naam", "?")
        name     = canonical_name(raw_name)
        r16      = score_r16_submission(sub)
        r32_pts  = R32_STANDINGS.get(name, 0.0)
        combined = r32_pts + r16["total"]
        rows.append((name, r32_pts, r16["match_total"], r16["topscorer"], r16["total"], combined))

    submitted_names = {r[0] for r in rows}
    for name, r32_pts in R32_STANDINGS.items():
        if name not in submitted_names:
            rows.append((name, r32_pts, 0, 0.0, 0.0, r32_pts))


    rows.sort(key=lambda r: r[5], reverse=True)
    for rank, (name, r32, r16_match, r16_ts, r16_total, combined) in enumerate(rows, 1):
        print(f"{rank:>2}. {name:<14}  {r32:>7.1f}  {r16_match:>10.1f}  {r16_ts:>9.1f}  {r16_total:>10.1f}  {combined:>10.1f}")


if __name__ == "__main__":
    main()
