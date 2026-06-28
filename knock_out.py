# knock_out.py – Streamlit knock-out stage prediction app for WK 2026

import json
import streamlit as st
from datetime import date
from players import PLAYERS
from utils import send_predictions_email, flag_img, encode_predictions, decode_predictions

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROUND_NAME = "Ronde van 32"

MATCHES_KO = [
    {"id":  1, "home": "Zuid-Afrika",        "away": "Canada",              "date": "28 jun", "time": "21:00"},
    {"id":  2, "home": "Brazilië",            "away": "Japan",               "date": "29 jun", "time": "19:00"},
    {"id":  3, "home": "Duitsland",           "away": "Paraguay",            "date": "29 jun", "time": "22:30"},
    {"id":  4, "home": "Nederland",           "away": "Marokko",             "date": "30 jun", "time": "03:00"},
    {"id":  5, "home": "Ivoorkust",           "away": "Noorwegen",           "date": "30 jun", "time": "19:00"},
    {"id":  6, "home": "Frankrijk",           "away": "Zweden",              "date": "30 jun", "time": "23:00"},
    {"id":  7, "home": "Mexico",              "away": "Ecuador",             "date": "1 jul",  "time": "03:00"},
    {"id":  8, "home": "Engeland",            "away": "DR Congo",            "date": "1 jul",  "time": "18:00"},
    {"id":  9, "home": "België",              "away": "Senegal",             "date": "1 jul",  "time": "22:00"},
    {"id": 10, "home": "USA",                 "away": "Bosnië-Herzegovina",  "date": "2 jul",  "time": "02:00"},
    {"id": 11, "home": "Spanje",              "away": "Oostenrijk",          "date": "2 jul",  "time": "21:00"},
    {"id": 12, "home": "Portugal",            "away": "Kroatië",             "date": "3 jul",  "time": "01:00"},
    {"id": 13, "home": "Zwitserland",         "away": "Algerije",            "date": "3 jul",  "time": "05:00"},
    {"id": 14, "home": "Australië",           "away": "Egypte",              "date": "3 jul",  "time": "20:00"},
    {"id": 15, "home": "Argentinië",          "away": "Kaapverdië",          "date": "4 jul",  "time": "00:00"},
    {"id": 16, "home": "Colombia",            "away": "Ghana",               "date": "4 jul",  "time": "03:30"},
]

TOPSCORER_SLOTS = 4
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# ── Config ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"WK 2026 – {ROUND_NAME}",
    page_icon="⚽",
    layout="wide",
)


# ── CSS (same design language as World_Championship.py) ───────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Bebas+Neue&display=swap" rel="stylesheet">
<style>
    :root {
        --bg-1: #0b1220;
        --bg-2: #111a2e;
        --card: rgba(255,255,255,0.04);
        --card-border: rgba(255,255,255,0.08);
        --text: #e6ebf5;
        --muted: #8893a8;
        --gold: #f5b841;
        --gold-2: #fbcf6c;
        --emerald: #34d399;
        --crimson: #ef4444;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }

    .stApp {
        background:
            radial-gradient(1100px 600px at 12% -10%, rgba(245,184,65,0.08), transparent 60%),
            radial-gradient(900px 500px at 110% 5%, rgba(52,211,153,0.07), transparent 60%),
            radial-gradient(700px 400px at 50% 110%, rgba(99,102,241,0.06), transparent 60%),
            linear-gradient(180deg, #0a1020 0%, #0d1628 60%, #0a1020 100%);
        background-attachment: fixed;
    }

    .block-container { padding-top: 1.5rem; max-width: 1280px; }

    p, span, label, li { color: var(--text); }
    h1, h2, h3, h4 { color: #ffffff !important; letter-spacing: -0.01em; }
    h2 { font-weight: 700; }
    .stCaption p { color: var(--muted) !important; font-size: 0.78rem; }

    .stTextInput input {
        background: #ffffff !important;
        color: #0a1020 !important;
        -webkit-text-fill-color: #0a1020 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
    }
    .stTextInput input::placeholder { color: #8893a8 !important; }
    .stTextInput div[data-baseweb="input"] {
        background: #ffffff !important;
        border-radius: 10px !important;
    }
    .stTextInput label { color: #cdd5e3 !important; font-weight: 500 !important; }
    .stTextInput input[aria-label="thuis"],
    .stTextInput input[aria-label="uit"] {
        background: #0d1628 !important;
        color: #f5b841 !important;
        -webkit-text-fill-color: #f5b841 !important;
        border: 2px solid rgba(245,184,65,0.35) !important;
        border-radius: 10px !important;
        text-align: center !important;
        font-weight: 800 !important;
        font-size: 1.4rem !important;
        padding: 0.35rem 0.2rem !important;
        letter-spacing: 0.04em !important;
    }
    .stTextInput input[aria-label="thuis"]:focus,
    .stTextInput input[aria-label="uit"]:focus {
        border-color: rgba(245,184,65,0.8) !important;
        box-shadow: 0 0 0 3px rgba(245,184,65,0.15) !important;
    }
    .stTextInput div[data-baseweb="input"]:has(input[aria-label="thuis"]),
    .stTextInput div[data-baseweb="input"]:has(input[aria-label="uit"]) {
        background: #0d1628 !important;
        border-radius: 10px !important;
    }

    .stSelectbox label { color: #cdd5e3 !important; font-weight: 500 !important; }
    .stSelectbox div[data-baseweb="select"] > div {
        background: #ffffff !important;
        color: #0a1020 !important;
        border-radius: 10px !important;
    }
    .stSelectbox div[data-baseweb="select"] span {
        color: #0a1020 !important;
        -webkit-text-fill-color: #0a1020 !important;
    }

    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent) !important;
        margin: 1.6rem 0 !important;
    }

    .hero { text-align: center; padding: 1.8rem 1rem 0.6rem; }
    .hero-badge {
        display: inline-block;
        padding: 0.3rem 0.9rem;
        background: rgba(245,184,65,0.1);
        border: 1px solid rgba(245,184,65,0.3);
        border-radius: 999px;
        color: var(--gold-2) !important;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        margin-bottom: 0.9rem;
    }
    .hero h1 {
        font-family: 'Bebas Neue', 'Inter', sans-serif !important;
        font-size: 4.2rem !important;
        font-weight: 900 !important;
        letter-spacing: 0.02em !important;
        margin: 0.2rem 0 0.4rem !important;
        background: linear-gradient(135deg, #fff 0%, #f5b841 50%, #fff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-size: 200% 200%;
        animation: shine 8s ease-in-out infinite;
    }
    @keyframes shine {
        0%, 100% { background-position: 0% 50%; }
        50%       { background-position: 100% 50%; }
    }
    .hero-sub {
        color: var(--muted) !important;
        font-size: 0.95rem;
        margin-top: 0.2rem;
        letter-spacing: 0.02em;
    }
    .hero-sub strong { color: #cdd5e3 !important; font-weight: 600; }

    .welcome-card {
        background: var(--card); border: 1px solid var(--card-border);
        border-radius: 14px; padding: 1rem 1.2rem;
        margin: 0.4rem 0 0.8rem; backdrop-filter: blur(8px);
    }
    .welcome-card h3 { margin: 0 !important; font-size: 1.15rem; }

    .ko-match-card {
        border-radius: 16px;
        padding: 0.85rem 1.1rem 0.6rem;
        margin-bottom: 0.5rem;
        backdrop-filter: blur(8px);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .ko-match-card:hover { transform: translateY(-3px); }
    .ko-match-label {
        display: inline-block;
        font-size: 0.64rem; font-weight: 800; letter-spacing: 0.16em;
        text-transform: uppercase;
        padding: 0.2rem 0.75rem;
        border-radius: 999px;
        margin-bottom: 0.7rem;
    }
    .ko-team {
        font-size: 1.05rem; font-weight: 700; color: #f1f5f9 !important;
        display: flex; align-items: center; gap: 7px;
    }
    .ko-score-sep {
        text-align: center; padding-top: 8px;
        font-weight: 900; font-size: 1.4rem;
        text-shadow: 0 0 12px currentColor;
    }

    .progress-card {
        background: var(--card); border: 1px solid var(--card-border);
        border-radius: 14px; padding: 1rem 1.3rem;
        backdrop-filter: blur(8px); text-align: center; margin-bottom: 1rem;
    }
    .progress-bar {
        height: 8px; background: rgba(255,255,255,0.06);
        border-radius: 999px; overflow: hidden; margin-top: 0.6rem;
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--gold), var(--emerald));
        border-radius: 999px; transition: width 0.5s ease;
    }

    .stButton > button {
        border-radius: 12px; font-weight: 600;
        padding: 0.65rem 1.2rem; transition: all 0.2s ease;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--gold) 0%, #e8a52e 100%);
        color: #1a1a1a !important; border: none;
        box-shadow: 0 4px 16px rgba(245,184,65,0.3);
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 22px rgba(245,184,65,0.45);
    }
    .stDownloadButton > button {
        border-radius: 12px; font-weight: 600;
        padding: 0.65rem 1.2rem;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.15);
        color: #fff; transition: all 0.2s ease;
    }
    .stDownloadButton > button:hover {
        background: rgba(255,255,255,0.12);
        border-color: rgba(245,184,65,0.4);
        transform: translateY(-2px);
    }

    .stAlert { border-radius: 12px; backdrop-filter: blur(6px); border: 1px solid rgba(255,255,255,0.08); }

    .footer {
        text-align: center; padding: 2.5rem 0 1.5rem;
        color: #3a4a5c; font-size: 0.78rem; letter-spacing: 0.04em;
    }
    .footer .heart { color: #ef4444; }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Load saved state from URL ──────────────────────────────────────────────────
params = st.query_params
saved_raw = params.get("d", "")
saved_name, saved_preds, saved_extras = decode_predictions(saved_raw) if saved_raw else ("", {}, {})

if "_ko_init_done" not in st.session_state:
    st.session_state["_ko_init_done"] = True
    for mid, pred in saved_preds.items():
        if pred.get("home") is not None:
            st.session_state[f"ko{mid}_home"] = str(pred["home"])
        if pred.get("away") is not None:
            st.session_state[f"ko{mid}_away"] = str(pred["away"])

if "ko_extras" not in st.session_state:
    ts = saved_extras.get("topscorers") or []
    if not isinstance(ts, list):
        ts = []
    ts = (ts + [{"team": "", "name": ""} for _ in range(TOPSCORER_SLOTS)])[:TOPSCORER_SLOTS]
    st.session_state["ko_extras"] = {"topscorers": ts}

if "ko_loaded_name" not in st.session_state:
    st.session_state["ko_loaded_name"] = saved_name


# ── Helpers ────────────────────────────────────────────────────────────────────
def parse_score(raw):
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or not s.lstrip("-").isdigit():
        return None
    try:
        n = int(s)
        return n if 0 <= n <= 20 else None
    except ValueError:
        return None

def get_predictions():
    preds = {}
    for match in MATCHES_KO:
        mid = match["id"]
        h = parse_score(st.session_state.get(f"ko{mid}_home"))
        a = parse_score(st.session_state.get(f"ko{mid}_away"))
        if h is not None or a is not None:
            preds[mid] = {"home": h, "away": a}
    return preds

def build_ko_export(name, preds, topscorers):
    payload = {
        "naam":  name,
        "ronde": ROUND_NAME,
        "datum": str(date.today()),
        "topscorers": topscorers,
        "voorspellingen": {},
    }
    for m in MATCHES_KO:
        mid  = m["id"]
        pred = preds.get(mid, {})
        payload["voorspellingen"][str(mid)] = {
            "thuis":       m["home"],
            "uit":         m["away"],
            "score_thuis": pred.get("home"),
            "score_uit":   pred.get("away"),
        }
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class='hero'>
    <div class='hero-badge'>⚽ FIFA World Cup · 2026 · Knock-out</div>
    <h1>WK 2026 Familiepoel</h1>
    <p class='hero-sub'>
        🏆 <strong>{ROUND_NAME}</strong> &nbsp;·&nbsp; 28 juni – 4 juli
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()


# ── Name ───────────────────────────────────────────────────────────────────────
col_name, _ = st.columns([2, 3])
with col_name:
    name = st.text_input(
        "👤 Jouw naam",
        value=st.session_state["ko_loaded_name"],
        placeholder="Bijv. Jan",
        key="player_name",
    )

if not name.strip():
    st.info("✏️ Voer eerst je naam in om te beginnen met voorspellen.")
    st.stop()

st.markdown(f"""
<div class='welcome-card'>
    <h3>👋 Hallo <span style='color:#f5b841'>{name.strip()}</span>!</h3>
    <p style='color:#8893a8;font-size:0.88rem;margin-top:0.3rem'>
        Voorspel de uitslag van elke wedstrijd <strong style='color:#cdd5e3'>na 90 minuten</strong>.
        Bij gelijke stand gaat een wedstrijd door naar verlenging en eventueel strafschoppen —
        maar jij voorspelt alleen de reguliere 90 minuten.<br>
        <strong style='color:#f5b841'>Exacte uitslag = 15 pt &nbsp;·&nbsp; Juiste winnaar = 10 pt</strong>
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()


# ── Match grid (2 matches per row) ─────────────────────────────────────────────
st.markdown("## 🏆 Wedstrijden")

PAIR_COLORS = [
    ("#f5b841", "#78350f"),
    ("#34d399", "#064e3b"),
    ("#60a5fa", "#1e3a8a"),
    ("#f472b6", "#831843"),
    ("#a78bfa", "#3b0764"),
    ("#fb923c", "#7c2d12"),
    ("#38bdf8", "#0c4a6e"),
    ("#4ade80", "#14532d"),
]

for i in range(0, len(MATCHES_KO), 2):
    accent, accent_dark = PAIR_COLORS[(i // 2) % len(PAIR_COLORS)]
    left_col, right_col = st.columns(2, gap="medium")

    for col, match in zip([left_col, right_col], MATCHES_KO[i:i+2]):
        mid  = match["id"]
        home = match["home"]
        away = match["away"]

        with col:
            st.markdown(f"""
            <div class='ko-match-card' style='
                background: linear-gradient(135deg, {accent}14 0%, {accent}06 100%);
                border: 1px solid {accent}40;
                border-left: 4px solid {accent};
                box-shadow: 0 4px 20px {accent}18;
            '>
                <div class='ko-match-label' style='background:{accent}22; color:{accent};'>
                    ⚽ {match['date']} · {match['time']} CEST
                </div>
            </div>
            """, unsafe_allow_html=True)

            c_home, c_score, c_away = st.columns([3, 2, 3])

            with c_home:
                st.markdown(
                    f"<div class='ko-team' style='justify-content:flex-end'>"
                    f"{flag_img(home)}&nbsp;<span>{home}</span></div>",
                    unsafe_allow_html=True,
                )

            with c_score:
                s1, sep, s2 = st.columns([1, 0.2, 1])
                with s1:
                    st.text_input(
                        "thuis", key=f"ko{mid}_home",
                        label_visibility="collapsed",
                        max_chars=2, placeholder="–",
                    )
                with sep:
                    st.markdown(
                        f"<div class='ko-score-sep' style='color:{accent}'>:</div>",
                        unsafe_allow_html=True,
                    )
                with s2:
                    st.text_input(
                        "uit", key=f"ko{mid}_away",
                        label_visibility="collapsed",
                        max_chars=2, placeholder="–",
                    )

            with c_away:
                st.markdown(
                    f"<div class='ko-team'>"
                    f"<span>{away}</span>&nbsp;{flag_img(away)}</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)


# ── Topscorer picks ────────────────────────────────────────────────────────────
st.divider()
st.markdown("## ⚽ Topscorers (kies 4)")
st.caption("Kies 4 spelers waarvan jij denkt dat ze het meest scoren in de knock-outfase.")

ko_extras = st.session_state["ko_extras"]
saved_ts = ko_extras.get("topscorers") or []
saved_ts = (saved_ts + [{"team": "", "name": ""} for _ in range(TOPSCORER_SLOTS)])[:TOPSCORER_SLOTS]

countries = ["— kies land —"] + sorted(PLAYERS.keys())
new_topscorers = []
for i in range(TOPSCORER_SLOTS):
    saved = saved_ts[i] if i < len(saved_ts) else {"team": "", "name": ""}
    if not isinstance(saved, dict):
        saved = {"team": "", "name": ""}
    c1, c2 = st.columns(2)
    with c1:
        c_idx = countries.index(saved["team"]) if saved["team"] in countries else 0
        country = st.selectbox(
            f"Topscorer {i+1} — Land",
            options=countries, index=c_idx,
            key=f"ko_ts_country_{i}",
        )
    with c2:
        if country and country != "— kies land —" and PLAYERS.get(country):
            player_opts = ["— kies speler —"] + [
                f"{p['name']} ({p['position']})" for p in PLAYERS[country]
            ]
            saved_label = next(
                (f"{p['name']} ({p['position']})"
                 for p in PLAYERS[country] if p["name"] == saved["name"]),
                "— kies speler —",
            )
            p_idx = player_opts.index(saved_label) if saved_label in player_opts else 0
            picked = st.selectbox(
                f"Topscorer {i+1} — Naam",
                options=player_opts, index=p_idx,
                key=f"ko_ts_player_{i}",
            )
            player_name = picked.rsplit(" (", 1)[0] if picked != "— kies speler —" else ""
        else:
            st.selectbox(
                f"Topscorer {i+1} — Naam",
                options=["— kies eerst een land —"],
                disabled=True, key=f"ko_ts_player_{i}_dis",
            )
            player_name = ""
    new_topscorers.append({
        "team": country if country != "— kies land —" else "",
        "name": player_name,
    })

st.session_state["ko_extras"] = {"topscorers": new_topscorers}


# ── Progress ───────────────────────────────────────────────────────────────────
st.divider()

current_preds = get_predictions()
filled  = sum(
    1 for p in current_preds.values()
    if p.get("home") is not None and p.get("away") is not None
)
total      = len(MATCHES_KO)
percentage = int((filled / total) * 100) if total > 0 else 0

st.markdown(f"""
<div class='progress-card'>
    <div style='font-size:0.85rem;color:#8893a8;letter-spacing:0.06em;text-transform:uppercase'>Voortgang</div>
    <div style='font-size:1.8rem;font-weight:800;color:#fff;margin-top:0.25rem'>
        <span style='color:#f5b841'>{filled}</span>
        <span style='color:#8893a8;font-weight:500;font-size:1.1rem'>/ {total} wedstrijden</span>
    </div>
    <div class='progress-bar'>
        <div class='progress-fill' style='width:{percentage}%'></div>
    </div>
    <div style='color:#8893a8;font-size:0.78rem;margin-top:0.4rem'>{percentage}% ingevuld</div>
</div>
""", unsafe_allow_html=True)

if filled < total:
    st.warning("⚠️ Nog niet alle wedstrijden ingevuld. Je kunt al wel tussentijds opslaan.")


# ── Auto-save to URL ───────────────────────────────────────────────────────────
ko_extras_now = st.session_state["ko_extras"]
if name.strip():
    encoded = encode_predictions(name.strip(), current_preds, ko_extras_now)
    if encoded != st.session_state.get("_ko_last_encoded"):
        st.session_state["_ko_last_encoded"] = encoded
        st.query_params["d"] = encoded


# ── Save / Download / Submit ───────────────────────────────────────────────────
col_save, col_export, col_submit = st.columns(3)
json_str = build_ko_export(name.strip(), current_preds, new_topscorers)

with col_save:
    if st.button("🔖 Sla op", type="secondary", use_container_width=True):
        encoded = encode_predictions(name.strip(), current_preds, ko_extras_now)
        st.query_params["d"] = encoded
        st.success("✅ Opgeslagen! Bookmark de URL.")

with col_export:
    st.download_button(
        label="📤 Download (.json)",
        data=json_str,
        file_name=f"knockout_r32_{name.strip().replace(' ', '_')}.json",
        mime="application/json",
        use_container_width=True,
    )

with col_submit:
    already_sent = st.session_state.get("ko_submitted", False)
    if already_sent:
        st.button("✅ Reeds ingestuurd", disabled=True, use_container_width=True, key="ko_submit_done")
    else:
        if st.button("📩 Definitief insturen", type="primary", use_container_width=True):
            if filled < total:
                st.warning(f"⚠️ Je hebt pas {filled}/{total} wedstrijden ingevuld. Inzending wordt nu verstuurd.")
            try:
                with st.spinner("Bezig met versturen..."):
                    send_predictions_email(name.strip(), json_str)
                st.session_state["ko_submitted"] = True
                st.success(f"🎉 Bedankt **{name.strip()}**! Je knock-out voorspellingen zijn verstuurd.")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Versturen mislukt: {e}")
                st.info("Gebruik de **Download (.json)** knop en stuur het bestand handmatig op.")

st.caption(
    "💡 **Sla op** = bewaren via URL · "
    "**Download** = bestand voor jezelf · "
    "**Definitief insturen** = mail naar de organisator"
)

st.markdown("""
<div class='footer'>
    WK 2026 Familiepoel · Knock-out stage · Gemaakt met <span class='heart'>♥</span> · Veel succes! ⚽🏆
</div>
""", unsafe_allow_html=True)
