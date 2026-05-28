# matches.py – all WK 2026 group stage data

GROUP_COLORS = {
    "A": "#e74c3c", "B": "#e67e22", "C": "#f1c40f",
    "D": "#2ecc71", "E": "#1abc9c", "F": "#3498db",
    "G": "#9b59b6", "H": "#e91e63", "I": "#00bcd4",
    "J": "#8bc34a", "K": "#ff5722", "L": "#607d8b",
}

FLAG_CODES = {
    "Mexico":             "mx",
    "Zuid-Afrika":        "za",
    "Zuid-Korea":         "kr",
    "Tsjechië":           "cz",
    "Canada":             "ca",
    "Bosnië-Herzegovina": "ba",
    "Qatar":              "qa",
    "Zwitserland":        "ch",
    "Brazilië":           "br",
    "Marokko":            "ma",
    "Haïti":              "ht",
    "Schotland":          "gb-sct",
    "USA":                "us",
    "Paraguay":           "py",
    "Australië":          "au",
    "Turkije":            "tr",
    "Duitsland":          "de",
    "Curaçao":            "cw",
    "Ivoorkust":          "ci",
    "Ecuador":            "ec",
    "Nederland":          "nl",
    "Japan":              "jp",
    "Tunesië":            "tn",
    "Zweden":             "se",
    "België":             "be",
    "Egypte":             "eg",
    "Iran":               "ir",
    "Nieuw-Zeeland":      "nz",
    "Spanje":             "es",
    "Kaapverdië":         "cv",
    "Saudi-Arabië":       "sa",
    "Uruguay":            "uy",
    "Frankrijk":          "fr",
    "Senegal":            "sn",
    "Noorwegen":          "no",
    "Irak":               "iq",
    "Argentinië":         "ar",
    "Algerije":           "dz",
    "Oostenrijk":         "at",
    "Jordanië":           "jo",
    "Portugal":           "pt",
    "DR Congo":           "cd",
    "Oezbekistan":        "uz",
    "Colombia":           "co",
    "Engeland":           "gb-eng",
    "Kroatië":            "hr",
    "Ghana":              "gh",
    "Panama":             "pa",
}

# Bottom-12 FIFA-ranked teams in the WC2026 field — edit to taste
UNDERDOG_TEAMS = [
    "Curaçao", "Kaapverdië", "Haïti", "Nieuw-Zeeland",
    "Oezbekistan", "Jordanië", "Saudi-Arabië", "Qatar",
    "Zuid-Afrika", "DR Congo", "Irak", "Panama",
]

MATCHES = [
    # Group A
    {"id": 1,  "group": "A", "date": "11 jun", "home": "Mexico",             "away": "Zuid-Afrika",         "venue": "Estadio Azteca",          "city": "Mexico City"},
    {"id": 2,  "group": "A", "date": "12 jun", "home": "Zuid-Korea",         "away": "Tsjechië",             "venue": "Estadio Akron",           "city": "Guadalajara"},
    {"id": 3,  "group": "A", "date": "18 jun", "home": "Tsjechië",           "away": "Zuid-Afrika",          "venue": "Mercedes-Benz Stadium",   "city": "Atlanta"},
    {"id": 4,  "group": "A", "date": "19 jun", "home": "Mexico",             "away": "Zuid-Korea",           "venue": "Estadio Akron",           "city": "Guadalajara"},
    {"id": 5,  "group": "A", "date": "25 jun", "home": "Zuid-Afrika",        "away": "Zuid-Korea",           "venue": "Estadio BBVA",            "city": "Monterrey"},
    {"id": 6,  "group": "A", "date": "25 jun", "home": "Tsjechië",           "away": "Mexico",               "venue": "Estadio Azteca",          "city": "Mexico City"},
    # Group B
    {"id": 7,  "group": "B", "date": "12 jun", "home": "Canada",             "away": "Bosnië-Herzegovina",   "venue": "BMO Field",               "city": "Toronto"},
    {"id": 8,  "group": "B", "date": "13 jun", "home": "Qatar",              "away": "Zwitserland",          "venue": "Levi's Stadium",          "city": "San Francisco"},
    {"id": 9,  "group": "B", "date": "18 jun", "home": "Zwitserland",        "away": "Bosnië-Herzegovina",   "venue": "SoFi Stadium",            "city": "Los Angeles"},
    {"id": 10, "group": "B", "date": "18 jun", "home": "Canada",             "away": "Qatar",                "venue": "BC Place",                "city": "Vancouver"},
    {"id": 11, "group": "B", "date": "24 jun", "home": "Zwitserland",        "away": "Canada",               "venue": "BC Place",                "city": "Vancouver"},
    {"id": 12, "group": "B", "date": "24 jun", "home": "Bosnië-Herzegovina", "away": "Qatar",                "venue": "Lumen Field",             "city": "Seattle"},
    # Group C
    {"id": 13, "group": "C", "date": "13 jun", "home": "Brazilië",           "away": "Marokko",              "venue": "MetLife Stadium",         "city": "New York/New Jersey"},
    {"id": 14, "group": "C", "date": "14 jun", "home": "Haïti",              "away": "Schotland",            "venue": "Gillette Stadium",        "city": "Boston"},
    {"id": 15, "group": "C", "date": "19 jun", "home": "Schotland",          "away": "Marokko",              "venue": "Gillette Stadium",        "city": "Boston"},
    {"id": 16, "group": "C", "date": "20 jun", "home": "Brazilië",           "away": "Haïti",                "venue": "Lincoln Financial Field", "city": "Philadelphia"},
    {"id": 17, "group": "C", "date": "24 jun", "home": "Marokko",            "away": "Haïti",                "venue": "Mercedes-Benz Stadium",   "city": "Atlanta"},
    {"id": 18, "group": "C", "date": "24 jun", "home": "Schotland",          "away": "Brazilië",             "venue": "Hard Rock Stadium",       "city": "Miami"},
    # Group D
    {"id": 19, "group": "D", "date": "13 jun", "home": "USA",                "away": "Paraguay",             "venue": "SoFi Stadium",            "city": "Los Angeles"},
    {"id": 20, "group": "D", "date": "14 jun", "home": "Australië",          "away": "Turkije",              "venue": "BC Place",                "city": "Vancouver"},
    {"id": 21, "group": "D", "date": "19 jun", "home": "USA",                "away": "Australië",            "venue": "Lumen Field",             "city": "Seattle"},
    {"id": 22, "group": "D", "date": "20 jun", "home": "Turkije",            "away": "Paraguay",             "venue": "Levi's Stadium",          "city": "San Francisco"},
    {"id": 23, "group": "D", "date": "26 jun", "home": "Turkije",            "away": "USA",                  "venue": "SoFi Stadium",            "city": "Los Angeles"},
    {"id": 24, "group": "D", "date": "26 jun", "home": "Paraguay",           "away": "Australië",            "venue": "Levi's Stadium",          "city": "San Francisco"},
    # Group E
    {"id": 25, "group": "E", "date": "14 jun", "home": "Duitsland",          "away": "Curaçao",              "venue": "NRG Stadium",             "city": "Houston"},
    {"id": 26, "group": "E", "date": "15 jun", "home": "Ivoorkust",          "away": "Ecuador",              "venue": "Lincoln Financial Field", "city": "Philadelphia"},
    {"id": 27, "group": "E", "date": "20 jun", "home": "Duitsland",          "away": "Ivoorkust",            "venue": "BMO Field",               "city": "Toronto"},
    {"id": 28, "group": "E", "date": "21 jun", "home": "Ecuador",            "away": "Curaçao",              "venue": "Arrowhead Stadium",       "city": "Kansas City"},
    {"id": 29, "group": "E", "date": "25 jun", "home": "Curaçao",            "away": "Ivoorkust",            "venue": "Lincoln Financial Field", "city": "Philadelphia"},
    {"id": 30, "group": "E", "date": "25 jun", "home": "Ecuador",            "away": "Duitsland",            "venue": "MetLife Stadium",         "city": "New York/New Jersey"},
    # Group F
    {"id": 31, "group": "F", "date": "14 jun", "home": "Nederland",          "away": "Japan",                "venue": "AT&T Stadium",            "city": "Dallas"},
    {"id": 32, "group": "F", "date": "15 jun", "home": "Zweden",             "away": "Tunesië",              "venue": "Estadio BBVA",            "city": "Monterrey"},
    {"id": 33, "group": "F", "date": "20 jun", "home": "Nederland",          "away": "Zweden",               "venue": "NRG Stadium",             "city": "Houston"},
    {"id": 34, "group": "F", "date": "21 jun", "home": "Tunesië",            "away": "Japan",                "venue": "Estadio BBVA",            "city": "Monterrey"},
    {"id": 35, "group": "F", "date": "26 jun", "home": "Tunesië",            "away": "Nederland",            "venue": "Arrowhead Stadium",       "city": "Kansas City"},
    {"id": 36, "group": "F", "date": "26 jun", "home": "Japan",              "away": "Zweden",               "venue": "AT&T Stadium",            "city": "Dallas"},
    # Group G
    {"id": 37, "group": "G", "date": "15 jun", "home": "België",             "away": "Egypte",               "venue": "Lumen Field",             "city": "Seattle"},
    {"id": 38, "group": "G", "date": "16 jun", "home": "Iran",               "away": "Nieuw-Zeeland",        "venue": "SoFi Stadium",            "city": "Los Angeles"},
    {"id": 39, "group": "G", "date": "21 jun", "home": "België",             "away": "Iran",                 "venue": "SoFi Stadium",            "city": "Los Angeles"},
    {"id": 40, "group": "G", "date": "22 jun", "home": "Nieuw-Zeeland",      "away": "Egypte",               "venue": "BC Place",                "city": "Vancouver"},
    {"id": 41, "group": "G", "date": "27 jun", "home": "Nieuw-Zeeland",      "away": "België",               "venue": "BC Place",                "city": "Vancouver"},
    {"id": 42, "group": "G", "date": "27 jun", "home": "Egypte",             "away": "Iran",                 "venue": "Lumen Field",             "city": "Seattle"},
    # Group H
    {"id": 43, "group": "H", "date": "15 jun", "home": "Spanje",             "away": "Kaapverdië",           "venue": "Mercedes-Benz Stadium",   "city": "Atlanta"},
    {"id": 44, "group": "H", "date": "15 jun", "home": "Saudi-Arabië",       "away": "Uruguay",              "venue": "Hard Rock Stadium",       "city": "Miami"},
    {"id": 45, "group": "H", "date": "21 jun", "home": "Spanje",             "away": "Saudi-Arabië",         "venue": "Mercedes-Benz Stadium",   "city": "Atlanta"},
    {"id": 46, "group": "H", "date": "21 jun", "home": "Uruguay",            "away": "Kaapverdië",           "venue": "Hard Rock Stadium",       "city": "Miami"},
    {"id": 47, "group": "H", "date": "27 jun", "home": "Kaapverdië",         "away": "Saudi-Arabië",         "venue": "NRG Stadium",             "city": "Houston"},
    {"id": 48, "group": "H", "date": "27 jun", "home": "Uruguay",            "away": "Spanje",               "venue": "Estadio Akron",           "city": "Guadalajara"},
    # Group I
    {"id": 49, "group": "I", "date": "16 jun", "home": "Frankrijk",          "away": "Senegal",              "venue": "MetLife Stadium",         "city": "New York/New Jersey"},
    {"id": 50, "group": "I", "date": "16 jun", "home": "Irak",               "away": "Noorwegen",            "venue": "Gillette Stadium",        "city": "Boston"},
    {"id": 51, "group": "I", "date": "22 jun", "home": "Frankrijk",          "away": "Irak",                 "venue": "Lincoln Financial Field", "city": "Philadelphia"},
    {"id": 52, "group": "I", "date": "23 jun", "home": "Noorwegen",          "away": "Senegal",              "venue": "BMO Field",               "city": "Toronto"},
    {"id": 53, "group": "I", "date": "26 jun", "home": "Noorwegen",          "away": "Frankrijk",            "venue": "Gillette Stadium",        "city": "Boston"},
    {"id": 54, "group": "I", "date": "26 jun", "home": "Senegal",            "away": "Irak",                 "venue": "BMO Field",               "city": "Toronto"},
    # Group J
    {"id": 55, "group": "J", "date": "17 jun", "home": "Argentinië",         "away": "Algerije",             "venue": "Arrowhead Stadium",       "city": "Kansas City"},
    {"id": 56, "group": "J", "date": "17 jun", "home": "Oostenrijk",         "away": "Jordanië",             "venue": "Levi's Stadium",          "city": "San Francisco"},
    {"id": 57, "group": "J", "date": "22 jun", "home": "Argentinië",         "away": "Oostenrijk",           "venue": "AT&T Stadium",            "city": "Dallas"},
    {"id": 58, "group": "J", "date": "23 jun", "home": "Jordanië",           "away": "Algerije",             "venue": "Arrowhead Stadium",       "city": "Kansas City"},
    {"id": 59, "group": "J", "date": "28 jun", "home": "Algerije",           "away": "Oostenrijk",           "venue": "Arrowhead Stadium",       "city": "Kansas City"},
    {"id": 60, "group": "J", "date": "28 jun", "home": "Jordanië",           "away": "Argentinië",           "venue": "AT&T Stadium",            "city": "Dallas"},
    # Group K
    {"id": 61, "group": "K", "date": "17 jun", "home": "Portugal",           "away": "DR Congo",             "venue": "NRG Stadium",             "city": "Houston"},
    {"id": 62, "group": "K", "date": "18 jun", "home": "Oezbekistan",        "away": "Colombia",             "venue": "Estadio Azteca",          "city": "Mexico City"},
    {"id": 63, "group": "K", "date": "23 jun", "home": "Portugal",           "away": "Oezbekistan",          "venue": "NRG Stadium",             "city": "Houston"},
    {"id": 64, "group": "K", "date": "24 jun", "home": "Colombia",           "away": "DR Congo",             "venue": "Estadio Akron",           "city": "Guadalajara"},
    {"id": 65, "group": "K", "date": "28 jun", "home": "Colombia",           "away": "Portugal",             "venue": "Hard Rock Stadium",       "city": "Miami"},
    {"id": 66, "group": "K", "date": "28 jun", "home": "DR Congo",           "away": "Oezbekistan",          "venue": "Mercedes-Benz Stadium",   "city": "Atlanta"},
    # Group L
    {"id": 67, "group": "L", "date": "17 jun", "home": "Engeland",           "away": "Kroatië",              "venue": "AT&T Stadium",            "city": "Dallas"},
    {"id": 68, "group": "L", "date": "18 jun", "home": "Ghana",              "away": "Panama",               "venue": "BMO Field",               "city": "Toronto"},
    {"id": 69, "group": "L", "date": "23 jun", "home": "Engeland",           "away": "Ghana",                "venue": "Gillette Stadium",        "city": "Boston"},
    {"id": 70, "group": "L", "date": "24 jun", "home": "Panama",             "away": "Kroatië",              "venue": "Gillette Stadium",        "city": "Boston"},
    {"id": 71, "group": "L", "date": "27 jun", "home": "Panama",             "away": "Engeland",             "venue": "MetLife Stadium",         "city": "New York/New Jersey"},
    {"id": 72, "group": "L", "date": "27 jun", "home": "Kroatië",            "away": "Ghana",                "venue": "Lincoln Financial Field", "city": "Philadelphia"},
]

def get_groups():
    return sorted(set(m["group"] for m in MATCHES))

def get_group_matches(group):
    return [m for m in MATCHES if m["group"] == group]

def get_group_teams(group):
    teams = set()
    for m in get_group_matches(group):
        teams.add(m["home"])
        teams.add(m["away"])
    return sorted(teams)