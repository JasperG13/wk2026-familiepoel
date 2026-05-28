# calculate_scores.py – compute standings from submitted JSONs

import json, glob, os
from pathlib import Path
from datetime import date

from scoring import score_full_submission
from matches import MATCHES

SUBMISSIONS_DIR = "submissions"

# ── Fill these in as the tournament progresses ────────────────────────────────
ACTUAL_RESULTS = {
    # 1: (2, 1),
}

ACTUAL_GROUP_STANDINGS = {
    # "A": ["Mexico", "Zuid-Korea", "Tsjechië", "Zuid-Afrika"],
}

ACTUAL_CHAMPION = None

# Goals per player per match (group stage only)
# Format: (team, player_name): {match_id: goals_in_that_match}
GOALS_BY_PLAYER = {
    # ("Brazilië", "Vinicius Jr."): {13: 1, 16: 2},
}


def load_submissions():
    Path(SUBMISSIONS_DIR).mkdir(exist_ok=True)
    out = []
    for path in glob.glob(f"{SUBMISSIONS_DIR}/*.json"):
        with open(path, encoding="utf-8") as f:
            try:
                out.append(json.load(f))
            except Exception as e:
                print(f"⚠️ {path}: {e}")
    return out


def main():
    subs = load_submissions()
    if not subs:
        print(f"No submissions in '{SUBMISSIONS_DIR}/'")
        return

    rows = []
    for sub in subs:
        br = score_full_submission(sub, ACTUAL_RESULTS, ACTUAL_GROUP_STANDINGS,
                                   ACTUAL_CHAMPION, GOALS_BY_PLAYER)
        rows.append({"name": sub.get("naam", "?"), **br})

    rows.sort(key=lambda r: r["total"], reverse=True)

    # ── Print leaderboard ────────────────────────────────────────────────────
    print(f"\n🏆 WK 2026 FAMILIEPOEL — STAND ({date.today()})")
    print("=" * 70)
    print(f"{'#':<3}{'Naam':<16}{'Wed.':>6}{'Plts':>6}{'Und.':>6}{'Kamp':>6}{'TopS':>6}{'TOT':>8}")
    print("-" * 70)
    for i, r in enumerate(rows, 1):
        m = {1:"🥇", 2:"🥈", 3:"🥉"}.get(i, f"{i}.")
        print(f"{m:<3}{r['name']:<16}"
              f"{r['match_total']:>6}{r['group_placement']:>6}"
              f"{r['underdog']:>6}{r['champion']:>6}"
              f"{r['topscorer']:>6}{r['total']:>8}")

    # ── WhatsApp message ─────────────────────────────────────────────────────
    msg = ["🏆 *WK 2026 FAMILIEPOEL*", f"_Stand van {date.today().strftime('%d %B')}_", "", "```"]
    msg.append(f"{'#':<3}{'Naam':<14}{'Pts':>5}")
    msg.append("-" * 22)
    for i, r in enumerate(rows, 1):
        m = {1:"🥇",2:"🥈",3:"🥉"}.get(i, f"{i}.")
        msg.append(f"{m:<3}{r['name'][:12]:<14}{r['total']:>5}")
    msg += ["```", ""]
    if rows:
        msg.append(f"👑 Aan kop: *{rows[0]['name']}* met *{rows[0]['total']} punten*")

    with open("whatsapp_update.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(msg))
    print("\n📱 whatsapp_update.txt saved")

    # ── Per-player breakdown messages (optional, paste individually) ─────────
    with open("per_player.txt", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(f"\n=== {r['name']} — {r['total']} pts ===\n")
            f.write(f"Wedstrijden: {r['match_total']} · Plaatsingen: {r['group_placement']}\n")
            f.write(f"Underdog: {r['underdog']} · Kampioen: {r['champion']} · Topscorer: {r['topscorer']}\n")
            for m in r["matches"]:
                if m["points"] != 0:
                    f.write(f"  {m['label']}: voorsp. {m['pred']} | echt {m['actual']} "
                            f"{m['modifiers']} = {m['points']} pt\n")
    print("📄 per_player.txt saved (one section per player, easy to copy-paste)")


if __name__ == "__main__":
    main()