# players.py – squads & position points

POSITION_POINTS = {
    "Verdediger":   24,
    "Middenvelder": 12,
    "Aanvaller":     6,
}

# Each player: {"name": "...", "position": "Aanvaller" | "Middenvelder" | "Verdediger"}
# Fill in once squads are announced.
PLAYERS = {
    "Mexico":             [],
    "Zuid-Afrika":        [],
    "Zuid-Korea":         [],
    "Tsjechië":           [],
    "Canada":             [],
    "Bosnië-Herzegovina": [],
    "Qatar":              [],
    "Zwitserland":        [],
    "Brazilië": [
        # Example format — delete once you have the real squad
        {"name": "Vinicius Jr.",   "position": "Aanvaller"},
        {"name": "Rodrygo",        "position": "Aanvaller"},
        {"name": "Bruno Guimarães","position": "Middenvelder"},
        {"name": "Marquinhos",     "position": "Verdediger"},
    ],
    "Marokko":            [],
    "Haïti":              [],
    "Schotland":          [],
    "USA":                [],
    "Paraguay":           [],
    "Australië":          [],
    "Turkije":            [],
    "Duitsland":          [],
    "Curaçao":            [],
    "Ivoorkust":          [],
    "Ecuador":            [],
    "Nederland":          [],
    "Japan":              [],
    "Tunesië":            [],
    "Zweden":             [],
    "België":             [],
    "Egypte":             [],
    "Iran":               [],
    "Nieuw-Zeeland":      [],
    "Spanje":             [],
    "Kaapverdië":         [],
    "Saudi-Arabië":       [],
    "Uruguay":            [],
    "Frankrijk":          [],
    "Senegal":            [],
    "Noorwegen":          [],
    "Irak":               [],
    "Argentinië":         [],
    "Algerije":           [],
    "Oostenrijk":         [],
    "Jordanië":           [],
    "Portugal":           [],
    "Jamaica":            [],
    "Oezbekistan":        [],
    "Colombia":           [],
    "Engeland":           [],
    "Kroatië":            [],
    "Ghana":              [],
    "Panama":             [],
}


def get_team_players(team):
    return PLAYERS.get(team, [])


def player_position(team, player_name):
    for p in PLAYERS.get(team, []):
        if p["name"] == player_name:
            return p["position"]
    return None