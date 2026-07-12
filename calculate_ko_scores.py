# calculate_ko_scores.py – compute standings for Ronde van 32

import json
from pathlib import Path

from players import player_position, POSITION_POINTS

SUBMISSIONS_DIR = "submissions"

# ── Hardcoded final group-stage standings (including Inez +100 bonus) ─────────
POULE_STANDINGS = {
    "Karlijn":          727.5,
    "Caroline Vernooij":710.0,
    "Hans":             660.5,
    "Kirsten Mekes":    659.0,
    "Thijs":            637.0,
    "Jasper":           624.0,
    "Jacqueline":       616.5,
    "Carlijne":         552.0,
    "wouter":           532.0,
    "Bart":             524.0,
    "Inez":             485.0,
}

# ── KO scoring constants (2× group stage) ────────────────────────────────────
PTS_KO_CORRECT = 20
PTS_KO_EXACT   = 30

# KO topscorer points per goal = 2× group-stage POSITION_POINTS
KO_POSITION_POINTS = {pos: pts * 2 for pos, pts in POSITION_POINTS.items()}

# ── Fill these in as the Ronde van 32 progresses ──────────────────────────────
ACTUAL_RESULTS_KO = {
    # Scores after max 120 minutes (regular time + ET if applicable)
    1:  (0, 1),  # Zuid-Afrika – Canada
    2:  (2, 1),  # Brazilië – Japan
    3:  (1, 1),  # Duitsland – Paraguay      (Paraguay wint pen.)
    4:  (1, 1),  # Nederland – Marokko       (Marokko wint pen.)
    5:  (1, 2),  # Ivoorkust – Noorwegen
    6:  (3, 0),  # Frankrijk – Zweden
    7:  (2, 0),  # Mexico – Ecuador
    8:  (2, 1),  # Engeland – DR Congo
    9:  (3, 2),  # België – Senegal          (AET)
    10: (2, 0),  # USA – Bosnië-Herzegovina
    11: (3, 0),  # Spanje – Oostenrijk
    12: (2, 1),  # Portugal – Kroatië
    13: (2, 0),  # Zwitserland – Algerije
    14: (1, 1),  # Australië – Egypte        (Egypte wint pen.)
    15: (3, 2),  # Argentinië – Kaapverdië   (AET)
    16: (1, 0),  # Colombia – Ghana
}

GOALS_BY_PLAYER_KO = {
    # (team, player_name): {match_id: goals}
    # Match 1 – Zuid-Afrika 0-1 Canada
    ("Canada",      "Stephen Eustáquio"):  {1: 1},
    # Match 2 – Brazilië 2-1 Japan
    ("Brazilië",    "Casemiro"):           {2: 1},
    ("Brazilië",    "Gabriel Martinelli"): {2: 1},
    ("Japan",       "Kaishu Sano"):        {2: 1},
    # Match 3 – Duitsland 1-1 Paraguay (ET)
    ("Duitsland",   "Kai Havertz"):        {3: 1},
    ("Paraguay",    "Julio Enciso"):       {3: 1},
    # Match 4 – Nederland 1-1 Marokko (ET) — Issa Diop not in players.py, skipped
    ("Nederland",   "Cody Gakpo"):         {4: 1},
    # Match 5 – Ivoorkust 1-2 Noorwegen
    ("Noorwegen",   "Antonio Nusa"):       {5: 1},
    ("Ivoorkust",   "Amad Diallo"):        {5: 1},
    ("Noorwegen",   "Erling Haaland"):     {5: 1},
    # Match 6 – Frankrijk 3-0 Zweden
    ("Frankrijk",   "Kylian Mbappé"):      {6: 2},
    ("Frankrijk",   "Bradley Barcola"):    {6: 1},
    # Match 7 – Mexico 2-0 Ecuador
    ("Mexico",      "Julián Quiñones"):    {7: 1},
    ("Mexico",      "Raúl Jiménez"):       {7: 1},
    # Match 8 – Engeland 2-1 DR Congo
    ("Engeland",    "Harry Kane"):         {8: 2},
    ("DR Congo",    "Brian Cipenga"):      {8: 1},
    # Match 9 – België 3-2 Senegal (AET)
    ("België",      "Romelu Lukaku"):      {9: 1},
    ("België",      "Youri Tielemans"):    {9: 2},
    ("Senegal",     "Habib Diarra"):       {9: 1},
    ("Senegal",     "Ismaïla Sarr"):       {9: 1},
    # Match 10 – USA 2-0 Bosnië-Herzegovina
    ("USA",         "Folarin Balogun"):    {10: 1},
    ("USA",         "Malik Tillman"):      {10: 1},
    # Match 11 – Spanje 3-0 Oostenrijk
    ("Spanje",      "Mikel Oyarzabal"):    {11: 2},
    ("Spanje",      "Pedro Porro"):        {11: 1},
    # Match 12 – Portugal 2-1 Kroatië — Gonçalo Ramos not in players.py, skipped
    ("Portugal",    "Cristiano Ronaldo"):  {12: 1},
    ("Kroatië",     "Ivan Perisic"):       {12: 1},
    # Match 13 – Zwitserland 2-0 Algerije
    ("Zwitserland", "Breel Embolo"):       {13: 1},
    ("Zwitserland", "Dan Ndoye"):          {13: 1},
    # Match 14 – Australië 1-1 Egypte (ET) — Mohamed Hany OG skipped
    ("Egypte",      "Emam Ashour"):        {14: 1},
    # Match 15 – Argentinië 3-2 Kaapverdië (AET) — Diney Borges OG skipped
    ("Argentinië",  "Lionel Messi"):       {15: 1},
    ("Argentinië",  "Lisandro Martinez"):  {15: 1},
    ("Kaapverdië",  "Deroy Duarte"):       {15: 1},
    ("Kaapverdië",  "Sidny Cabral"):       {15: 1},
    # Match 16 – Colombia 1-0 Ghana
    ("Colombia",    "Jhon Arias"):         {16: 1},
}


def score_ko_submission(sub):
    """
    Returns dict with match_total, topscorer, and total (ko points only).
    No bonuses, jokers, casinos, star team, or underdog — KO round is clean scoring.
    """
    voorspel = sub.get("voorspellingen", {}) or {}
    topscorers = sub.get("topscorers") or []

    match_points = 0
    for mid_str, pred in voorspel.items():
        mid = int(mid_str)
        if mid not in ACTUAL_RESULTS_KO:
            continue
        ah, aa = ACTUAL_RESULTS_KO[mid]
        ph = pred.get("score_thuis")
        pa = pred.get("score_uit")
        if ph is None or pa is None:
            continue
        if ph == ah and pa == aa:
            match_points += PTS_KO_EXACT
        elif (ph > pa) == (ah > aa) and (ph == pa) == (ah == aa):
            match_points += PTS_KO_CORRECT

    topscorer_points = 0.0
    for pick in topscorers:
        team = pick.get("team", "") if isinstance(pick, dict) else ""
        name = pick.get("name", "") if isinstance(pick, dict) else ""
        if not team or not name:
            continue
        pos = player_position(team, name)
        pts_per_goal = KO_POSITION_POINTS.get(pos, 0)
        if pts_per_goal == 0:
            continue
        goals_map = GOALS_BY_PLAYER_KO.get((team, name), {})
        for mid, goals in goals_map.items():
            topscorer_points += goals * pts_per_goal

    return {
        "match_total":  match_points,
        "topscorer":    topscorer_points,
        "total":        match_points + topscorer_points,
    }


def load_ko_submissions():
    subs = []
    for f in sorted(Path(SUBMISSIONS_DIR).glob("*.json")):
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception:
            continue
        if data.get("ronde") == "Ronde van 32":
            subs.append(data)
    return subs


def main():
    submissions = load_ko_submissions()
    print(f"{'Deelnemer':<16}  {'Poule':>7}  {'KO wedstr':>10}  {'KO topsc':>9}  {'KO totaal':>10}  {'Eindstand':>10}")
    print("-" * 72)

    rows = []
    for sub in submissions:
        name = sub.get("naam", "?")
        ko   = score_ko_submission(sub)
        poule_pts = POULE_STANDINGS.get(name, 0.0)
        combined  = poule_pts + ko["total"]
        rows.append((name, poule_pts, ko["match_total"], ko["topscorer"], ko["total"], combined))

    # Also include participants who haven't submitted KO predictions yet
    submitted_names = {r[0] for r in rows}
    for name, poule_pts in POULE_STANDINGS.items():
        if name not in submitted_names:
            rows.append((name, poule_pts, 0, 0.0, 0.0, poule_pts))

    rows.sort(key=lambda r: r[5], reverse=True)
    for rank, (name, poule, ko_match, ko_ts, ko_total, combined) in enumerate(rows, 1):
        print(f"{rank:>2}. {name:<14}  {poule:>7.1f}  {ko_match:>10.1f}  {ko_ts:>9.1f}  {ko_total:>10.1f}  {combined:>10.1f}")


if __name__ == "__main__":
    main()
