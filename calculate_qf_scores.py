# calculate_qf_scores.py – compute standings for Kwartfinale

import json
from pathlib import Path

from players import player_position

SUBMISSIONS_DIR = "submissions_quarter_finals"

# Submission "naam" fields that differ from R16_STANDINGS keys
NAME_MAP = {
    "Kirsten":             "Kirsten Mekes",
    "Jacqueline Vernooij": "Jacqueline",
}

# ── Hardcoded final R16 standings ─────────────────────────────────────────────
R16_STANDINGS = {
    "Caroline Vernooij": 1236.0,
    "Karlijn":           1147.5,
    "Kirsten Mekes":     1143.0,
    "Jacqueline":        1090.5,
    "Hans":              1056.5,
    "Jasper":            1050.0,
    "Thijs":             1005.0,
    "Carlijne":           984.0,
    "Bart":               954.0,
    "Inez":               943.0,
    "wouter":             938.0,
}

# ── QF scoring constants (×2 vs R16) ─────────────────────────────────────────
PTS_QF_CORRECT = 60
PTS_QF_EXACT   = 90

# Topscorer points per goal = ×2 vs R16
QF_POSITION_POINTS = {
    "Aanvaller":    36,
    "Middenvelder": 72,
    "Verdediger":  144,
}

# ── Fill these in as the Kwartfinale progresses ───────────────────────────────
ACTUAL_RESULTS_QF = {
    1: (2, 0),  # Frankrijk – Marokko
    2: (2, 1),  # Spanje – België
    3: (1, 2),  # Noorwegen – Engeland (na verlenging)
    4: (3, 1),  # Argentinië – Zwitserland (na verlenging)
}

GOALS_BY_PLAYER_QF = {
    # Match 1 – Frankrijk 2-0 Marokko
    ("Frankrijk", "Kylian Mbappé"):    {1: 1},
    ("Frankrijk", "Ousmane Dembélé"):  {1: 1},

    # Match 2 – Spanje 2-1 België
    ("Spanje", "Fabián Ruiz"):           {2: 1},
    ("Spanje", "Mikel Merino"):          {2: 1},
    ("België", "Charles De Ketelaere"):  {2: 1},

    # Match 3 – Noorwegen 1-2 Engeland (na verlenging)
    ("Noorwegen", "Andreas Schjelderup"): {3: 1},
    ("Engeland", "Jude Bellingham"):      {3: 2},

    # Match 4 – Argentinië 3-1 Zwitserland (na verlenging)
    ("Argentinië", "Alexis Mac Allister"): {4: 1},
    ("Argentinië", "Julián Álvarez"):      {4: 1},
    ("Argentinië", "Lautaro Martinez"):    {4: 1},
    ("Zwitserland", "Dan Ndoye"):          {4: 1},
}


def canonical_name(raw):
    return NAME_MAP.get(raw, raw)


def score_qf_submission(sub):
    voorspel   = sub.get("voorspellingen", {}) or {}
    topscorers = sub.get("topscorers") or []

    match_points = 0
    for mid_str, pred in voorspel.items():
        mid = int(mid_str)
        if mid not in ACTUAL_RESULTS_QF:
            continue
        ah, aa = ACTUAL_RESULTS_QF[mid]
        ph = pred.get("score_thuis")
        pa = pred.get("score_uit")
        if ph is None or pa is None:
            continue
        if ph == ah and pa == aa:
            match_points += PTS_QF_EXACT
        elif (ph > pa) == (ah > aa) and (ph == pa) == (ah == aa):
            match_points += PTS_QF_CORRECT

    topscorer_points = 0.0
    for pick in topscorers:
        team = pick.get("team", "") if isinstance(pick, dict) else ""
        name = pick.get("name", "") if isinstance(pick, dict) else ""
        if not team or not name:
            continue
        pos = player_position(team, name)
        pts_per_goal = QF_POSITION_POINTS.get(pos, 0)
        if pts_per_goal == 0:
            continue
        goals_map = GOALS_BY_PLAYER_QF.get((team, name), {})
        for mid, goals in goals_map.items():
            topscorer_points += goals * pts_per_goal

    return {
        "match_total": match_points,
        "topscorer":   topscorer_points,
        "total":       match_points + topscorer_points,
    }


def load_qf_submissions():
    subs = []
    for f in sorted(Path(SUBMISSIONS_DIR).glob("*.json")):
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception:
            continue
        if data.get("ronde") == "Kwartfinale":
            subs.append(data)
    subs.sort(key=lambda s: s.get("naam", "").lower())
    return subs


def main():
    submissions = load_qf_submissions()
    print(f"{'Deelnemer':<16}  {'R16':>7}  {'QF wedstr':>10}  {'QF topsc':>9}  {'QF totaal':>10}  {'Eindstand':>10}")
    print("-" * 72)

    rows = []
    for sub in submissions:
        raw_name = sub.get("naam", "?")
        name     = canonical_name(raw_name)
        qf       = score_qf_submission(sub)
        r16_pts  = R16_STANDINGS.get(name, 0.0)
        combined = r16_pts + qf["total"]
        rows.append((name, r16_pts, qf["match_total"], qf["topscorer"], qf["total"], combined))

    submitted_names = {r[0] for r in rows}
    for name, r16_pts in R16_STANDINGS.items():
        if name not in submitted_names:
            rows.append((name, r16_pts, 0, 0.0, 0.0, r16_pts))

    rows.sort(key=lambda r: r[5], reverse=True)
    for rank, (name, r16, qf_match, qf_ts, qf_total, combined) in enumerate(rows, 1):
        print(f"{rank:>2}. {name:<14}  {r16:>7.1f}  {qf_match:>10.1f}  {qf_ts:>9.1f}  {qf_total:>10.1f}  {combined:>10.1f}")


if __name__ == "__main__":
    main()