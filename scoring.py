# scoring.py – points calculation, group tables & full scoring engine

from matches import get_group_matches, MATCHES
from players import POSITION_POINTS, player_position

# ── New scoring constants ─────────────────────────────────────────────────────
PTS_CORRECT_WINNER  = 10
PTS_EXACT_SCORE     = 15
PTS_GROUP_PLACEMENT = 4       # per correct team-in-position
PTS_CHAMPION        = 200
PTS_UNDERDOG_WIN    = 15
PTS_UNDERDOG_DRAW   = 10
JOKER_MULTIPLIER    = 2
CASINO_MULTIPLIER   = 3
CASINO_PENALTY      = -5
STARTEAM_MULTIPLIER = 2


def result_type(home, away):
    if home > away:  return "home"
    if away > home:  return "away"
    return "draw"


def base_match_points(pred_h, pred_a, actual_h, actual_a):
    """Base points for one match (without modifiers)."""
    if pred_h is None or pred_a is None:
        return 0
    if pred_h == actual_h and pred_a == actual_a:
        return PTS_EXACT_SCORE
    if result_type(pred_h, pred_a) == result_type(actual_h, actual_a):
        return PTS_CORRECT_WINNER
    return 0


def score_match(pred_h, pred_a, actual_h, actual_a, *,
                is_joker=False, is_casino=False, is_starteam=False):
    """Final points for one match including modifiers."""
    base = base_match_points(pred_h, pred_a, actual_h, actual_a)
    correct = base > 0

    if is_casino:
        return CASINO_MULTIPLIER * base if correct else CASINO_PENALTY

    pts = base
    if is_joker:    pts *= JOKER_MULTIPLIER
    if is_starteam: pts *= STARTEAM_MULTIPLIER
    return pts


# ── Group standings (used for predicted standings in app) ────────────────────
def calculate_group_table(group, predictions):
    matches = get_group_matches(group)
    teams = {}
    for m in matches:
        for team in (m["home"], m["away"]):
            if team not in teams:
                teams[team] = {"team": team, "pts": 0, "w": 0, "d": 0, "l": 0,
                               "gf": 0, "ga": 0, "gd": 0, "played": 0}

    for m in matches:
        pred = predictions.get(m["id"])
        if not pred:
            continue
        h, a = pred.get("home"), pred.get("away")
        if h is None or a is None:
            continue

        ht, at = teams[m["home"]], teams[m["away"]]
        ht["played"] += 1; at["played"] += 1
        ht["gf"] += h;  ht["ga"] += a
        at["gf"] += a;  at["ga"] += h
        if h > a:   ht["pts"] += 3; ht["w"] += 1; at["l"] += 1
        elif a > h: at["pts"] += 3; at["w"] += 1; ht["l"] += 1
        else:       ht["pts"] += 1; at["pts"] += 1; ht["d"] += 1; at["d"] += 1

    for t in teams.values():
        t["gd"] = t["gf"] - t["ga"]

    return sorted(teams.values(),
                  key=lambda t: (t["pts"], t["gd"], t["gf"]),
                  reverse=True)


# ── Full submission scoring (used by calculate_scores.py) ────────────────────
def score_full_submission(submission, actual_results, actual_group_standings,
                          actual_champion=None, goals_by_player=None):
    """
    submission: dict from JSON export
    actual_results: {match_id: (home, away)} for matches that have been played
    actual_group_standings: {group_letter: [team1, team2, team3, team4]}
                            (ordered final placement). Pass partial = ignored.
    actual_champion: team name (or None)
    goals_by_player: {(country, player_name): goals_in_group_stage}
    """
    extras = submission.get("extras", {}) or {}
    joker_ids   = set(extras.get("jokers", []) or [])
    casino_ids  = set(extras.get("casinos", []) or [])
    star_team   = extras.get("star_team", "")
    underdog    = extras.get("underdog", "")
    champion    = extras.get("champion", "")
    topscorers  = extras.get("topscorers", []) or []  # list of {"team":..,"name":..}

    # Map match_id -> match for star-team check
    match_map = {m["id"]: m for m in MATCHES}

    breakdown = {
        "matches": [],
        "group_placement": 0,
        "underdog": 0,
        "champion": 0,
        "topscorer": 0,
        "total": 0,
    }

    # ── Per-match points ─────────────────────────────────────────────────────
    for mid_str, pred in submission.get("voorspellingen", {}).items():
        mid = int(mid_str)
        if mid not in actual_results:
            continue
        ah, aa = actual_results[mid]
        ph = pred.get("score_thuis")
        pa = pred.get("score_uit")

        m = match_map[mid]
        is_joker  = mid in joker_ids
        is_casino = mid in casino_ids
        is_star   = star_team and star_team in (m["home"], m["away"])

        pts = score_match(ph, pa, ah, aa,
                          is_joker=is_joker, is_casino=is_casino,
                          is_starteam=is_star)

        breakdown["matches"].append({
            "id": mid,
            "label": f"{m['home']} vs {m['away']}",
            "pred": f"{ph}-{pa}" if ph is not None and pa is not None else "—",
            "actual": f"{ah}-{aa}",
            "modifiers": "".join(filter(None, [
                "🃏" if is_joker else "",
                "🎰" if is_casino else "",
                "⭐" if is_star else "",
            ])),
            "points": pts,
        })

    # ── Group placement points ───────────────────────────────────────────────
    pred_standings = {}
    pred_preds = {int(k): {"home": v["score_thuis"], "away": v["score_uit"]}
                  for k, v in submission.get("voorspellingen", {}).items()
                  if v.get("score_thuis") is not None and v.get("score_uit") is not None}

    for group, actual_order in actual_group_standings.items():
        pred_order = [t["team"] for t in calculate_group_table(group, pred_preds)]
        for i, actual_team in enumerate(actual_order):
            if i < len(pred_order) and pred_order[i] == actual_team:
                breakdown["group_placement"] += PTS_GROUP_PLACEMENT

    # ── Underdog points ──────────────────────────────────────────────────────
    if underdog:
        for mid, (ah, aa) in actual_results.items():
            m = match_map[mid]
            if underdog == m["home"]:
                if ah > aa:   breakdown["underdog"] += PTS_UNDERDOG_WIN
                elif ah == aa: breakdown["underdog"] += PTS_UNDERDOG_DRAW
            elif underdog == m["away"]:
                if aa > ah:   breakdown["underdog"] += PTS_UNDERDOG_WIN
                elif ah == aa: breakdown["underdog"] += PTS_UNDERDOG_DRAW

    # ── Champion ─────────────────────────────────────────────────────────────
    if actual_champion and champion == actual_champion:
        breakdown["champion"] = PTS_CHAMPION

    # ── Top scorer (6 picks) ─────────────────────────────────────────────────
    if goals_by_player:
        for pick in topscorers:
            team = pick.get("team", "")
            name = pick.get("name", "")
            if not team or not name:
                continue
            goals = goals_by_player.get((team, name), 0)
            pos = player_position(team, name)
            pts_per_goal = POSITION_POINTS.get(pos, 0)
            breakdown["topscorer"] += goals * pts_per_goal

    # ── Total ────────────────────────────────────────────────────────────────
    match_total = sum(m["points"] for m in breakdown["matches"])
    breakdown["match_total"] = match_total
    breakdown["total"] = (match_total
                          + breakdown["group_placement"]
                          + breakdown["underdog"]
                          + breakdown["champion"]
                          + breakdown["topscorer"])
    return breakdown