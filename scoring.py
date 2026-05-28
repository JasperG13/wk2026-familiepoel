# scoring.py – final rules

from matches import get_group_matches, MATCHES
from players import POSITION_POINTS, player_position

# ── Scoring constants ─────────────────────────────────────────────────────────
PTS_CORRECT_WINNER  = 10
PTS_EXACT_SCORE     = 15
PTS_GROUP_PLACEMENT = 2          # per correct top-2 team
PTS_CHAMPION        = 150
PTS_UNDERDOG_WIN    = 30
PTS_UNDERDOG_DRAW   = 20

JOKER_MULTIPLIER    = 1.5
CASINO_MULTIPLIER   = 2.5
CASINO_PENALTY      = -5
STARTEAM_MULTIPLIER = 2


def result_type(h, a):
    if h is None or a is None: return None
    if h > a: return "home"
    if a > h: return "away"
    return "draw"


def base_match_points(ph, pa, ah, aa):
    """Base toto/exact points for one match (without modifiers)."""
    if ph is None or pa is None:
        return 0
    if ph == ah and pa == aa:
        return PTS_EXACT_SCORE
    if result_type(ph, pa) == result_type(ah, aa):
        return PTS_CORRECT_WINNER
    return 0


def compute_match_modifiers(ph, pa, ah, aa, is_joker, is_casino, is_star):
    """
    Compute final match-toto points AND the multiplier for any topscorer goals
    scored in this same match.

    Returns (match_points, topscorer_multiplier).
    Bonuses stack except Joker+Casino (UI prevents that, so we don't enforce here).
    """
    base = base_match_points(ph, pa, ah, aa)
    toto_correct = base > 0

    # ── Topscorer multiplier for goals in this match ─────────────────────────
    ts_mult = 1.0
    if is_joker:
        ts_mult *= JOKER_MULTIPLIER
    if is_casino and toto_correct:
        ts_mult *= CASINO_MULTIPLIER
    if is_star:
        ts_mult *= STARTEAM_MULTIPLIER

    # ── Match (toto) points ──────────────────────────────────────────────────
    if is_casino:
        if toto_correct:
            mult = CASINO_MULTIPLIER * (STARTEAM_MULTIPLIER if is_star else 1)
            match_pts = base * mult
        else:
            match_pts = CASINO_PENALTY    # flat, no star-team multiplier on penalty
    else:
        mult = 1.0
        if is_joker:  mult *= JOKER_MULTIPLIER
        if is_star:   mult *= STARTEAM_MULTIPLIER
        match_pts = base * mult

    return match_pts, ts_mult


# ── Group standings (used for predicted standings in app) ────────────────────
def calculate_group_table(group, predictions):
    matches = get_group_matches(group)
    teams = {}
    for m in matches:
        for t in (m["home"], m["away"]):
            if t not in teams:
                teams[t] = {"team": t, "pts": 0, "w": 0, "d": 0, "l": 0,
                            "gf": 0, "ga": 0, "gd": 0, "played": 0}

    for m in matches:
        pred = predictions.get(m["id"])
        if not pred: continue
        h, a = pred.get("home"), pred.get("away")
        if h is None or a is None: continue
        ht, at = teams[m["home"]], teams[m["away"]]
        ht["played"] += 1; at["played"] += 1
        ht["gf"] += h; ht["ga"] += a
        at["gf"] += a; at["ga"] += h
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
    actual_results: {match_id: (home, away)}
    actual_group_standings: {group_letter: [team_1st, team_2nd, team_3rd, team_4th]}
    actual_champion: team name or None
    goals_by_player: {(team, player_name): {match_id: goals_in_that_match}}
    """
    extras     = submission.get("extras", {}) or {}
    joker_ids  = set(extras.get("jokers", []) or [])
    casino_ids = set(extras.get("casinos", []) or [])
    star_team  = extras.get("star_team", "")
    underdog   = extras.get("underdog", "")
    champion   = extras.get("champion", "")
    topscorers = extras.get("topscorers", []) or []
    goals_by_player = goals_by_player or {}

    match_map = {m["id"]: m for m in MATCHES}
    voorspel  = submission.get("voorspellingen", {})

    breakdown = {
        "matches": [],
        "group_placement": 0,
        "underdog":        0,
        "champion":        0,
        "topscorer":       0,
        "match_total":     0,
        "total":           0,
    }

    # Cache topscorer-multipliers per match so we reuse them for the topscorer section
    ts_mult_by_match = {}

    # ── Per-match points ─────────────────────────────────────────────────────
    for mid_str, pred in voorspel.items():
        mid = int(mid_str)
        if mid not in actual_results:
            continue
        ah, aa = actual_results[mid]
        ph, pa = pred.get("score_thuis"), pred.get("score_uit")
        m = match_map[mid]

        is_joker  = mid in joker_ids
        is_casino = mid in casino_ids
        is_star   = bool(star_team) and star_team in (m["home"], m["away"])

        match_pts, ts_mult = compute_match_modifiers(
            ph, pa, ah, aa, is_joker, is_casino, is_star)

        ts_mult_by_match[mid] = ts_mult

        breakdown["matches"].append({
            "id":   mid,
            "label": f"{m['home']} vs {m['away']}",
            "pred":  f"{ph}-{pa}" if ph is not None and pa is not None else "—",
            "actual": f"{ah}-{aa}",
            "modifiers": "".join(filter(None, [
                "🃏" if is_joker else "",
                "🎰" if is_casino else "",
                "⭐" if is_star else "",
            ])),
            "points": match_pts,
        })

    breakdown["match_total"] = sum(m["points"] for m in breakdown["matches"])

    # ── Group placement (top 2 only) ─────────────────────────────────────────
    pred_preds = {
        int(k): {"home": v.get("score_thuis"), "away": v.get("score_uit")}
        for k, v in voorspel.items()
        if v.get("score_thuis") is not None and v.get("score_uit") is not None
    }
    for group, actual_order in actual_group_standings.items():
        if len(actual_order) < 2:
            continue
        actual_top2 = set(actual_order[:2])
        pred_order  = [t["team"] for t in calculate_group_table(group, pred_preds)]
        pred_top2   = set(pred_order[:2])
        breakdown["group_placement"] += len(actual_top2 & pred_top2) * PTS_GROUP_PLACEMENT

    # ── Underdog ─────────────────────────────────────────────────────────────
    if underdog:
        for mid, (ah, aa) in actual_results.items():
            m = match_map[mid]
            if underdog == m["home"]:
                if ah > aa:    breakdown["underdog"] += PTS_UNDERDOG_WIN
                elif ah == aa: breakdown["underdog"] += PTS_UNDERDOG_DRAW
            elif underdog == m["away"]:
                if aa > ah:    breakdown["underdog"] += PTS_UNDERDOG_WIN
                elif ah == aa: breakdown["underdog"] += PTS_UNDERDOG_DRAW

    # ── Champion ─────────────────────────────────────────────────────────────
    if actual_champion and champion == actual_champion:
        breakdown["champion"] = PTS_CHAMPION

    # ── Top scorer goals (per match, with multipliers) ───────────────────────
    for pick in topscorers:
        team = pick.get("team", "")
        name = pick.get("name", "")
        if not team or not name:
            continue
        pos = player_position(team, name)
        base_per_goal = POSITION_POINTS.get(pos, 0)
        if base_per_goal == 0:
            continue

        goals_per_match = goals_by_player.get((team, name), {})
        for mid, goals in goals_per_match.items():
            ts_mult = ts_mult_by_match.get(mid, 1.0)
            # If the match wasn't in actual_results, fall back to no modifiers
            if mid not in ts_mult_by_match:
                m = match_map.get(mid)
                is_star = bool(star_team) and m and star_team in (m["home"], m["away"])
                is_joker = mid in joker_ids
                # No casino multiplier if we don't know correctness, default just joker+star
                ts_mult = 1.0
                if is_joker: ts_mult *= JOKER_MULTIPLIER
                if is_star:  ts_mult *= STARTEAM_MULTIPLIER
            breakdown["topscorer"] += goals * base_per_goal * ts_mult

    breakdown["total"] = (breakdown["match_total"]
                          + breakdown["group_placement"]
                          + breakdown["underdog"]
                          + breakdown["champion"]
                          + breakdown["topscorer"])
    return breakdown