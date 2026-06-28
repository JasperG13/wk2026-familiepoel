# calculate_scores.py – compute standings from submitted JSONs

import json, glob, os
from pathlib import Path
from datetime import date

from scoring import score_full_submission
from matches import MATCHES

SUBMISSIONS_DIR = "submissions"

# ── Fill these in as the tournament progresses ────────────────────────────────
ACTUAL_RESULTS = {
    1:  (2, 0),  # Mexico - Zuid-Afrika
    2:  (2, 1),  # Zuid-Korea - Tsjechië
    7:  (1, 1),  # Canada - Bosnië-Herzegovina
    8:  (1, 1),  # Qatar - Zwitserland
    13: (1, 1),  # Brazilië - Marokko
    14: (0, 1),  # Haïti - Schotland
    19: (4, 1),  # USA - Paraguay
    20: (2, 0),  # Australië - Turkije
    25: (7, 1),  # Duitsland - Curaçao
    26: (1, 0),  # Ivoorkust - Ecuador
    31: (2, 2),  # Nederland - Japan
    32: (5, 1),  # Zweden - Tunesië
    37: (1, 1),  # België - Egypte
    38: (2, 2),  # Iran - Nieuw-Zeeland
    43: (0, 0),  # Spanje - Kaapverdië
    44: (1, 1),  # Saudi-Arabië - Uruguay
    49: (3, 1),  # Frankrijk - Senegal
    50: (1, 4),  # Irak - Noorwegen
    55: (3, 0),  # Argentinië - Algerije
    56: (3, 1),  # Oostenrijk - Jordanië
    3:  (1, 1),  # Tsjechië - Zuid-Afrika
    4:  (1, 0),  # Mexico - Zuid-Korea
    9:  (4, 1),  # Zwitserland - Bosnië-Herzegovina
    10: (6, 0),  # Canada - Qatar
    61: (1, 1),  # Portugal - DR Congo
    62: (1, 3),  # Oezbekistan - Colombia
    67: (4, 2),  # Engeland - Kroatië
    68: (1, 0),  # Ghana - Panama
    21: (2, 0),  # USA - Australië
    15: (0, 1),  # Schotland - Marokko
    16: (3, 0),  # Brazilië - Haïti
    22: (0, 1),  # Turkije - Paraguay
    33: (5, 1),  # Nederland - Zweden
    27: (2, 1),  # Duitsland - Ivoorkust
    28: (0, 0),  # Ecuador - Curaçao
    34: (0, 4),  # Tunesië - Japan
    45: (4, 0),  # Spanje - Saudi-Arabië
    39: (0, 0),  # België - Iran
    40: (1, 3),  # Nieuw-Zeeland - Egypte
    46: (2, 2),  # Uruguay - Kaapverdië
    57: (2, 0),  # Argentinië - Oostenrijk
    51: (3, 0),  # Frankrijk - Irak
    52: (3, 2),  # Noorwegen - Senegal
    58: (1, 2),  # Jordanië - Algerije
    63: (5, 0),  # Portugal - Oezbekistan
    69: (0, 0),  # Engeland - Ghana
    70: (0, 1),  # Panama - Kroatië
    64: (1, 0),  # Colombia - DR Congo
    11: (2, 1),  # Zwitserland - Canada
    12: (3, 1),  # Bosnië-Herzegovina - Qatar
    17: (4, 2),  # Marokko - Haïti
    18: (0, 3),  # Schotland - Brazilië
    6:  (0, 3),  # Tsjechië - Mexico
    5:  (1, 0),  # Zuid-Afrika - Zuid-Korea
    29: (0, 2),  # Curaçao - Ivoorkust
    30: (2, 1),  # Ecuador - Duitsland
    35: (1, 3),  # Tunesië - Nederland
    36: (1, 1),  # Japan - Zweden
    23: (3, 2),  # Turkije - USA
    24: (0, 0),  # Paraguay - Australië
}

ACTUAL_GROUP_STANDINGS = {
    # "A": ["Mexico", "Zuid-Korea", "Tsjechië", "Zuid-Afrika"],
}

ACTUAL_CHAMPION = None

# Goals per player per match (group stage only)
# Format: (team, player_name): {match_id: goals_in_that_match}
GOALS_BY_PLAYER = {
    ("Mexico",              "Julián Quiñones"):   {1: 1, 6: 1},
    ("Mexico",              "Raúl Jiménez"):       {1: 1},
    ("Tsjechië",            "Ladislav Krejčí"):    {2: 1},
    ("Zuid-Korea",          "Hwang In-beom"):      {2: 1},
    ("Zuid-Korea",          "Oh Hyeon-gyu"):       {2: 1},
    ("Canada",              "Cyle Larin"):         {7: 1, 10: 1},
    ("Bosnië-Herzegovina",  "Jovo Lukic"):         {7: 1},
    ("Qatar",               "Boualem Khoukhi"):   {8: 1},
    ("Zwitserland",         "Breel Embolo"):       {8: 1},
    ("Brazilië",            "Vinicius Jr."):       {13: 1, 16: 1, 18: 2},
    ("Brazilië",            "Matheus Cunha"):      {16: 2, 18: 1},
    ("Marokko",             "Ismael Saibari"):     {13: 1, 15: 1, 17: 1},
    ("Schotland",           "John McGinn"):        {14: 1},
    ("USA",                 "Folarin Balogun"):    {19: 2},
    ("USA",                 "Alex Freeman"):       {21: 1},
    ("USA",                 "Giovanni Reyna"):     {19: 1},
    ("Paraguay",            "Maurício Magalhães"): {19: 1},
    ("Paraguay",            "Matías Galarza"):     {22: 1},
    ("Australië",           "Nestory Irankunda"):  {20: 1},
    ("Australië",           "Connor Metcalfe"):    {20: 1},
    ("Duitsland",           "Felix Nmecha"):        {25: 1},
    ("Duitsland",           "Nico Schlotterbeck"): {25: 1},
    ("Duitsland",           "Kai Havertz"):         {25: 2},
    ("Duitsland",           "Jamal Musiala"):       {25: 1},
    ("Duitsland",           "Nathaniel Brown"):     {25: 1},
    ("Duitsland",           "Deniz Undav"):         {25: 1, 27: 2},
    ("Curaçao",             "Livano Comenencia"):   {25: 1},
    ("Ivoorkust",           "Amad Diallo"):         {26: 1},
    ("Ivoorkust",           "Franck Kessié"):       {27: 1},
    ("Spanje",              "Lamine Yamal"):        {45: 1},
    ("Spanje",              "Mikel Oyarzabal"):     {45: 2},
    ("Kaapverdië",          "Kevin Pina"):          {46: 1},
    ("Kaapverdië",          "Helio Varela"):        {46: 1},
    ("Nederland",           "Virgil van Dijk"):     {31: 1},
    ("Nederland",           "Crysencio Summerville"): {31: 1, 33: 1},
    ("Nederland",           "Brian Brobbey"):        {33: 2, 35: 1},
    ("Nederland",           "Cody Gakpo"):           {33: 2},
    ("Japan",               "Keito Nakamura"):      {31: 1},
    ("Japan",               "Daichi Kamada"):       {31: 1, 34: 1},
    ("Japan",               "Ayase Ueda"):          {34: 2},
    ("Japan",               "Junya Ito"):           {34: 1},
    ("Zweden",              "Yasin Ayari"):         {32: 2},
    ("Zweden",              "Alexander Isak"):      {32: 1},
    ("Zweden",              "Viktor Gyökeres"):     {32: 1},
    ("Zweden",              "Mattias Svanberg"):    {32: 1},
    ("Zweden",              "Anthony Elanga"):      {33: 1, 36: 1},
    ("Tunesië",             "Omar Rekik"):          {32: 1},
    ("Egypte",              "Emam Ashour"):         {37: 1},
    ("Egypte",              "Mostafa Ziko"):        {40: 1},
    ("Egypte",              "Mohamed Salah"):       {40: 1},
    ("Egypte",              "Mahmoud Trézéguet"):   {40: 1},
    ("Iran",                "Ramin Rezaiyan"):      {38: 1},
    ("Iran",                "Mohammed Mohebbi"):    {38: 1},
    ("Nieuw-Zeeland",       "Eli Just"):             {38: 2},
    ("Nieuw-Zeeland",       "Finn Surman"):          {40: 1},
    ("Saudi-Arabië",        "Abdulelah Al Amri"):   {44: 1},
    ("Uruguay",             "Maximiliano Araújo"):  {44: 1, 46: 1},
    ("Uruguay",             "Agustín Canobbio"):    {46: 1},
    ("Frankrijk",           "Kylian Mbappé"):       {49: 2, 51: 2},
    ("Frankrijk",           "Bradley Barcola"):     {49: 1},
    ("Frankrijk",           "Ousmane Dembélé"):     {51: 1},
    ("Senegal",             "Ibrahim Mbaye"):       {49: 1},
    ("Senegal",             "Ismaïla Sarr"):        {52: 2},
    ("Noorwegen",           "Erling Haaland"):      {50: 2, 52: 2},
    ("Noorwegen",           "Marcus Holmgren Pedersen"): {52: 1},
    ("Noorwegen",           "Leo Skiri Østigård"):  {50: 1},
    ("Noorwegen",           "Kristian Thorstvedt"):{50: 1},
    ("Irak",                "Aymen Hussein"):       {50: 1},
    ("Argentinië",          "Lionel Messi"):        {55: 3, 57: 2},
    ("Oostenrijk",          "Romano Schmid"):       {56: 1},
    ("Oostenrijk",          "Marko Arnautovic"):    {56: 1},
    ("Jordanië",            "Ali Olwan"):           {56: 1},
    ("Jordanië",            "Nizar Al Rashdan"):    {58: 1},
    ("Algerije",            "Nadir Benbouali"):     {58: 1},
    ("Algerije",            "Amine Gouiri"):        {58: 1},
    ("Tsjechië",            "Michal Sadílek"):      {3: 1},
    ("Zuid-Afrika",         "Teboho Mokoena"):      {3: 1},
    ("Mexico",              "Luis Romo"):            {4: 1},
    ("Zwitserland",         "Johan Manzambi"):      {9: 2, 11: 1},
    ("Zwitserland",         "Ruben Vargas"):         {9: 1, 11: 1},
    ("Zwitserland",         "Granit Xhaka"):         {9: 1},
    ("Bosnië-Herzegovina",  "Ermin Mahmic"):         {9: 1, 12: 1},
    ("Canada",              "Jonathan David"):       {10: 3},
    ("Canada",              "Nathan Saliba"):        {10: 1},
    ("Portugal",            "João Neves"):          {61: 1},
    ("DR Congo",            "Yoane Wissa"):         {61: 1},
    ("Colombia",            "Daniel Muñoz"):        {62: 1, 64: 1},
    ("Colombia",            "Luis Díaz"):           {62: 1},
    ("Colombia",            "Jaminton Campaz"):     {62: 1},
    ("Oezbekistan",         "Abbosbek Fayzullaev"):{62: 1},
    ("Engeland",            "Harry Kane"):          {67: 2},
    ("Engeland",            "Jude Bellingham"):     {67: 1},
    ("Engeland",            "Marcus Rashford"):     {67: 1},
    ("Kroatië",             "Martin Baturina"):     {67: 1},
    ("Ghana",               "Caleb Yirenkyi"):      {68: 1},
    ("Portugal",            "Cristiano Ronaldo"):   {63: 2},
    ("Portugal",            "Nuno Mendes"):         {63: 1},
    ("Portugal",            "Rafael Leão"):         {63: 1},
    ("Kroatië",             "Ante Budimir"):        {70: 1},
    ("Canada",              "Promise David"):       {11: 1},
    ("Bosnië-Herzegovina",  "Kerim Alajbegovic"):   {12: 1},
    ("Qatar",               "Hassan Al-Haydos"):    {12: 1},
    ("Marokko",             "Achraf Hakimi"):       {17: 1},
    ("Marokko",             "Soufiane Rahimi"):     {17: 1},
    ("Marokko",             "Gessime Yassine"):     {17: 1},
    ("Haïti",               "Wilson Isidor"):       {17: 1},
    ("Mexico",              "Mateo Chávez"):        {6: 1},
    ("Mexico",              "Álvaro Fidalgo"):      {6: 1},
    ("Zuid-Afrika",         "Thapelo Maseko"):      {5: 1},
    ("Ivoorkust",           "Nicolas Pépé"):        {29: 2},
    ("Ecuador",             "Gonzalo Plata"):       {30: 1},
    ("Ecuador",             "Nilson Angulo"):       {30: 1},
    ("Duitsland",           "Leroy Sané"):          {30: 1},
    ("Nederland",           "Jan Paul van Hecke"):  {35: 1},
    ("Tunesië",             "Hazem Mastouri"):      {35: 1},
    ("Japan",               "Daizen Maeda"):        {36: 1},
    ("Turkije",             "Arda Güler"):          {23: 1},
    ("Turkije",             "Barış Alper Yılmaz"):  {23: 1},
    ("Turkije",             "Kaan Ayhan"):          {23: 1},
    ("USA",                 "Auston Trusty"):       {23: 1},
    ("USA",                 "Sebastian Berhalter"): {23: 1},
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