# World_Championship.py – main Streamlit app

import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from players import PLAYERS, POSITION_POINTS
from utils import send_predictions_email

from matches import (
    MATCHES, GROUP_COLORS, FLAG_CODES, UNDERDOG_TEAMS,
    get_groups, get_group_matches,
)
from scoring import calculate_group_table
from utils import flag_img, encode_predictions, decode_predictions, build_export_payload

# ── Config ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WK 2026 – Poule de Goetzee! (+ meer)",
    page_icon="⚽",
    layout="wide",
)

# ── Constants ──────────────────────────────────────────────────────────────────
DEADLINE = datetime(2026, 6, 10, 23, 59, 59, tzinfo=timezone.utc)
MATCHES_BY_ID = {m["id"]: m for m in MATCHES}

JOKER_LIMIT  = 7
CASINO_LIMIT = 5
TOPSCORER_SLOTS = 3

def is_past_deadline():
    return datetime.now(timezone.utc) > DEADLINE

def deadline_str():
    return DEADLINE.strftime("%d %B %Y om %H:%M").lstrip("0")

def match_label(mid):
    m = MATCHES_BY_ID[mid]
    return f"#{mid:02d} · {m['home']} – {m['away']} · {m['date']} (Groep {m['group']})"


# ── CSS / Design ───────────────────────────────────────────────────────────────
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

    /* Background — deep stadium night with soft glows */
    .stApp {
        background:
            radial-gradient(1100px 600px at 12% -10%, rgba(245,184,65,0.08), transparent 60%),
            radial-gradient(900px 500px at 110% 5%, rgba(52,211,153,0.07), transparent 60%),
            radial-gradient(700px 400px at 50% 110%, rgba(99,102,241,0.06), transparent 60%),
            linear-gradient(180deg, #0a1020 0%, #0d1628 60%, #0a1020 100%);
        background-attachment: fixed;
    }

    .block-container {
        padding-top: 1.5rem;
        max-width: 1280px;
    }

    /* Typography */
    p, span, label, li { color: var(--text); }
    h1, h2, h3, h4 { color: #ffffff !important; letter-spacing: -0.01em; }
    h2 { font-weight: 700; }
    .stCaption p { color: var(--muted) !important; font-size: 0.78rem; }

    /* ── Text input (general — used for name & topscorer) ────────────────── */
    .stTextInput input,
    [data-testid="stTextInput"] input {
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

    /* ── Score inputs (text_inputs with aria-label "thuis" / "uit") ──────── */
    .stTextInput input[aria-label="thuis"],
    .stTextInput input[aria-label="uit"] {
        text-align: center !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 0.4rem 0.3rem !important;
    }

    /* ── Selectbox + Multiselect ────────────────────────────────────────── */
    .stSelectbox label,
    .stMultiSelect label { color: #cdd5e3 !important; font-weight: 500 !important; }
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        background: #ffffff !important;
        color: #0a1020 !important;
        border-radius: 10px !important;
    }
    .stSelectbox div[data-baseweb="select"] span,
    .stMultiSelect div[data-baseweb="select"] span {
        color: #0a1020 !important;
        -webkit-text-fill-color: #0a1020 !important;
    }
    /* Multiselect chips */
    .stMultiSelect [data-baseweb="tag"] {
        background: #f5b841 !important;
        color: #1a1a1a !important;
        border-radius: 6px !important;
    }
    .stMultiSelect [data-baseweb="tag"] span {
        color: #1a1a1a !important;
        -webkit-text-fill-color: #1a1a1a !important;
    }

    /* ── Dataframe ──────────────────────────────────────────────────────── */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--card-border);
        background: var(--card);
        backdrop-filter: blur(8px);
    }
    .stDataFrame [data-testid="stDataFrameResizable"] * {
        color: #0a1020 !important;
    }
    .stDataFrame [role="columnheader"] {
        background: #1a2540 !important;
    }
    .stDataFrame [role="columnheader"] * {
        color: #f5b841 !important;
        font-weight: 700 !important;
    }

    /* Divider */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent) !important;
        margin: 1.6rem 0 !important;
    }

    /* Hero header */
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
        50% { background-position: 100% 50%; }
    }
    .hero-sub {
        color: var(--muted) !important;
        font-size: 0.95rem;
        margin-top: 0.2rem;
        letter-spacing: 0.02em;
    }
    .hero-sub strong { color: #cdd5e3 !important; font-weight: 600; }

    /* Countdown / Deadline */
    .deadline-banner {
        background: linear-gradient(135deg, rgba(239,68,68,0.18), rgba(220,38,38,0.10));
        border: 1px solid rgba(239,68,68,0.4);
        color: #fecaca !important;
        padding: 0.8rem 1.2rem;
        border-radius: 14px;
        text-align: center;
        font-weight: 600;
        margin: 0.8rem auto 1rem;
        max-width: 720px;
        backdrop-filter: blur(6px);
    }
    .countdown {
        display: flex;
        justify-content: center;
        gap: 0.6rem;
        flex-wrap: wrap;
        max-width: 720px;
        margin: 0.6rem auto 0.4rem;
    }
    .countdown-pill {
        background: rgba(245,184,65,0.08);
        border: 1px solid rgba(245,184,65,0.25);
        padding: 0.45rem 0.9rem;
        border-radius: 12px;
        color: var(--gold-2) !important;
        font-size: 0.82rem;
        font-weight: 600;
        backdrop-filter: blur(6px);
    }
    .countdown-pill .num {
        color: #fff !important;
        font-weight: 700;
        font-size: 1rem;
        margin-right: 4px;
    }
    .countdown-label {
        text-align: center;
        color: var(--muted) !important;
        font-size: 0.75rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-top: 0.4rem;
    }

    /* Welcome card */
    .welcome-card {
        background: var(--card);
        border: 1px solid var(--card-border);
        border-radius: 14px;
        padding: 1rem 1.2rem;
        margin: 0.4rem 0 0.8rem;
        backdrop-filter: blur(8px);
    }
    .welcome-card h3 { margin: 0 !important; font-size: 1.15rem; }

    /* Group header card */
    .group-header {
        padding: 0.85rem 1.2rem;
        border-radius: 14px 14px 0 0;
        margin-bottom: 0.5rem;
        font-weight: 700;
        font-size: 1.1rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        backdrop-filter: blur(6px);
        border: 1px solid var(--card-border);
        border-bottom: none;
        display: flex;
        align-items: center;
        gap: 0.7rem;
    }
    .group-letter {
        width: 36px; height: 36px;
        border-radius: 10px;
        display: inline-flex; align-items: center; justify-content: center;
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.5rem;
        color: #fff;
        box-shadow: 0 4px 14px rgba(0,0,0,0.25);
    }
    .group-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.5rem;
        letter-spacing: 0.06em;
        color: #fff !important;
    }

    /* Bonus section card */
    .bonus-section {
        background: var(--card);
        border: 1px solid var(--card-border);
        border-radius: 14px;
        padding: 1rem 1.2rem;
        margin: 0.6rem 0 1rem;
        backdrop-filter: blur(8px);
    }
    .bonus-section h4 {
        margin: 0 0 0.5rem !important;
        font-size: 1rem !important;
        color: var(--gold-2) !important;
    }
    .bonus-summary {
        background: linear-gradient(135deg, rgba(245,184,65,0.10), rgba(52,211,153,0.06));
        border: 1px solid rgba(245,184,65,0.25);
        border-radius: 14px;
        padding: 0.9rem 1.2rem;
        margin: 0.4rem 0 1rem;
        font-size: 0.92rem;
        line-height: 1.7;
        color: #e6ebf5 !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 12px;
        font-weight: 600;
        padding: 0.65rem 1.2rem;
        transition: all 0.2s ease;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--gold) 0%, #e8a52e 100%);
        color: #1a1a1a !important;
        border: none;
        box-shadow: 0 4px 16px rgba(245,184,65,0.3);
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 22px rgba(245,184,65,0.45);
    }
    .stDownloadButton > button {
        border-radius: 12px;
        font-weight: 600;
        padding: 0.65rem 1.2rem;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.15);
        color: #fff;
        transition: all 0.2s ease;
    }
    .stDownloadButton > button:hover {
        background: rgba(255,255,255,0.12);
        border-color: rgba(245,184,65,0.4);
        transform: translateY(-2px);
    }

    /* Alerts */
    .stAlert {
        border-radius: 12px;
        backdrop-filter: blur(6px);
        border: 1px solid rgba(255,255,255,0.08);
    }

    /* Progress section */
    .progress-card {
        background: var(--card);
        border: 1px solid var(--card-border);
        border-radius: 14px;
        padding: 1rem 1.3rem;
        backdrop-filter: blur(8px);
        text-align: center;
        margin-bottom: 1rem;
    }
    .progress-bar {
        height: 8px;
        background: rgba(255,255,255,0.06);
        border-radius: 999px;
        overflow: hidden;
        margin-top: 0.6rem;
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--gold), var(--emerald));
        border-radius: 999px;
        transition: width 0.5s ease;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 2.5rem 0 1.5rem;
        color: #3a4a5c;
        font-size: 0.78rem;
        letter-spacing: 0.04em;
    }
    .footer .heart { color: #ef4444; }

    /* Hide streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Load saved predictions from URL ───────────────────────────────────────────
params = st.query_params
saved_raw = params.get("d", "")
saved_name, saved_preds, saved_extras = "", {}, {}
if saved_raw:
    saved_name, saved_preds, saved_extras = decode_predictions(saved_raw)

# One-time init: copy saved values into widget state keys (as STRINGS).
if "_init_done" not in st.session_state:
    st.session_state["_init_done"] = True
    for mid, pred in saved_preds.items():
        if pred.get("home") is not None:
            st.session_state[f"m{mid}_home"] = str(pred["home"])
        if pred.get("away") is not None:
            st.session_state[f"m{mid}_away"] = str(pred["away"])

# Initialize extras with all required keys
def _default_extras():
    return {
        "champion":   "",
        "topscorers": ["", "", ""],
        "jokers":     [],
        "casinos":    [],
        "star_team":  "",
        "underdog":   "",
    }

if "extras" not in st.session_state:
    base = _default_extras()
    if saved_extras:
        base.update({k: v for k, v in saved_extras.items() if v is not None})
        # make sure topscorers always 3 long
        ts = list(base.get("topscorers") or [])
        base["topscorers"] = (ts + ["", "", ""])[:3]
    st.session_state.extras = base

if "loaded_name" not in st.session_state:
    st.session_state.loaded_name = saved_name

# Star-team lock: if previously saved, lock it permanently for this session
if "star_locked" not in st.session_state:
    st.session_state.star_locked = bool(saved_extras.get("star_team"))


# ── Helpers ──────────────────────────────────────────────────────────────────
def parse_score(raw):
    """Parse a text-input value into an int in [0, 20], else None."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    if not s.lstrip("-").isdigit():
        return None
    try:
        n = int(s)
    except ValueError:
        return None
    if 0 <= n <= 20:
        return n
    return None


def get_predictions():
    """Single source of truth: read all match scores straight from widget state."""
    preds = {}
    for match in MATCHES:
        mid = match["id"]
        h = parse_score(st.session_state.get(f"m{mid}_home"))
        a = parse_score(st.session_state.get(f"m{mid}_away"))
        if h is not None or a is not None:
            preds[mid] = {"home": h, "away": a}
    return preds


past_deadline = is_past_deadline()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='hero'>
    <div class='hero-badge'>⚽ FIFA World Cup · 2026</div>
    <h1>WK 2026 Familiepoel</h1>
    <p class='hero-sub'>
        🇺🇸 <strong>USA</strong> &nbsp;·&nbsp; 🇨🇦 <strong>Canada</strong> &nbsp;·&nbsp; 🇲🇽 <strong>Mexico</strong>
        &nbsp;&nbsp;|&nbsp;&nbsp; 11 juni – 27 juni 2026
    </p>
</div>
""", unsafe_allow_html=True)

# Deadline banner / countdown
if past_deadline:
    st.markdown("""
    <div class='deadline-banner'>
        🔒 De deadline is verstreken — voorspellingen zijn gesloten.
    </div>
    """, unsafe_allow_html=True)
else:
    now = datetime.now(timezone.utc)
    diff = DEADLINE - now
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes = remainder // 60
    st.markdown(f"""
    <div class='countdown-label'>⏰ Deadline · {deadline_str()} UTC</div>
    <div class='countdown'>
        <div class='countdown-pill'><span class='num'>{days}</span>dagen</div>
        <div class='countdown-pill'><span class='num'>{hours}</span>uur</div>
        <div class='countdown-pill'><span class='num'>{minutes}</span>min</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── Name input ─────────────────────────────────────────────────────────────────
col_name, _ = st.columns([2, 3])
with col_name:
    name = st.text_input(
        "👤 Jouw naam",
        value=st.session_state.loaded_name,
        placeholder="Bijv. Jan",
        key="player_name",
        disabled=past_deadline,
    )

if not name.strip():
    st.info("✏️ Voer eerst je naam in om te beginnen met voorspellen.")
    st.stop()

# ── Intro / welcome ────────────────────────────────────────────────────────────
INTRO_TEXT = """
Welkom bij de WK 2026 poule de Goetzee! 🏆

Hier vul je je voorspellingen in voor alle wedstrijden van de groepsfase. Updates omtrent de stand en puntenscores worden
in de groepschat op Whatsapp gepost. Je wordt aan deze groep toegevoegd zodra je je scores bij mij (jasper) hebt ingeleverd!

De site werkt als volgt: Je kunt je scores invullen door in de cellen een getal in te vullen (dit spreekt redelijk voor zich). 
Ook zijn er bonuspunten te verdienen. De scoring daarvan staat een stukje verderop uitgelegd. Voor de uitleg per bonuspunt categorie
kun je in het uitleg bestand kijken!

**Punten voor wedstrijden**
- Exacte uitslag: **10 punten**
- Juiste winnaar / gelijkspel: **5 punt**

**Bonusvoorspellingen**
- 🃏 7× Joker-wedstrijd → punten voor die wedstrijd ×1.5
- 🎰 5× Casino-wedstrijd → ×2.5 als goed, −3 als fout (juiste winnaar / gelijkspel, niet exacte uitslag) 
- ⭐ 1× STAR-team → ×2.5 op alle correcte voorspellingen met dit team
- 🐴 1× Underdog → +5 per gewonnen wedstrijd, +3 voor gelijk
- 🥅 +1 per team dat je correct bij de top-2 van de groep voorspelt
- 🥇 Wereldkampioen: +30 als correct
- ⚽ 3× Topscorer-kans: +15 als één van je namen klopt

Veel succes en plezier! ⚽
"""

if saved_preds:
    st.markdown(f"""
    <div class='welcome-card'>
        ✅ Welkom terug <strong style='color:#f5b841'>{name.strip()}</strong>!
        Je vorige voorspellingen zijn automatisch geladen.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class='welcome-card'>
        <h3>👋 Hallo <span style='color:#f5b841'>{name.strip()}</span>!</h3>
    </div>
    """, unsafe_allow_html=True)

intro_html = INTRO_TEXT.strip().replace("\n", "<br>")
st.markdown(f"""
<div style='background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-left: 4px solid #f5b841;
            border-radius: 12px;
            padding: 1.1rem 1.3rem;
            margin: 0.6rem 0 1rem;
            backdrop-filter: blur(8px);
            line-height: 1.65;
            color: #cdd5e3;
            font-size: 0.95rem;'>
    {intro_html}
</div>
""", unsafe_allow_html=True)

st.divider()


# ── Group table helper ─────────────────────────────────────────────────────────
def render_group_table(group, predictions):
    standing = calculate_group_table(group, predictions)
    rows = []
    for t in standing:
        gd = f"+{t['gd']}" if t['gd'] > 0 else str(t['gd'])
        rows.append({
            "Vlag": f"https://flagcdn.com/48x36/{FLAG_CODES.get(t['team'], 'un')}.png",
            "Team": t["team"],
            "Pts":  t["pts"],
            "+/-":  gd,
            "DV":   t["gf"],
            "G":    t["played"],
        })

    df = pd.DataFrame(rows)

    def highlight_rows(row):
        if row.name < 2:
            return ["background-color: #a7f3d0; color: #0a1020; font-weight: 600;"] * len(row)
        return ["background-color: #f1f5f9; color: #0a1020;"] * len(row)

    styled = df.style.apply(highlight_rows, axis=1)

    st.caption(f"📊 **Stand Groep {group}**")
    st.dataframe(
        styled,
        hide_index=True,
        use_container_width=True,
        height=178,
        column_config={
            "Vlag": st.column_config.ImageColumn("", width="small"),
            "Team": st.column_config.TextColumn("Team"),
            "Pts":  st.column_config.NumberColumn("Pts", help="Punten"),
            "+/-":  st.column_config.TextColumn("+/-",  help="Doelsaldo"),
            "DV":   st.column_config.NumberColumn("DV",  help="Doelpunten voor"),
            "G":    st.column_config.NumberColumn("G",   help="Gespeeld"),
        }
    )
    st.caption("🟢 Top 2 = doorgekwalificeerd naar de knock-outs")


# ── Render each group ──────────────────────────────────────────────────────────
def render_group(group):
    group_matches = get_group_matches(group)
    color = GROUP_COLORS[group]
    ex = st.session_state.extras

    st.markdown(f"""
    <div class='group-header' style='background:linear-gradient(90deg, {color}26, {color}08 60%, transparent);
         border-left: 4px solid {color};'>
        <span class='group-letter' style='background:linear-gradient(135deg, {color}, {color}aa);'>{group}</span>
        <span class='group-title'>Groep {group}</span>
    </div>
    """, unsafe_allow_html=True)

    col_matches, col_table = st.columns([2.6, 2])

    with col_matches:
        for match in group_matches:
            mid = match["id"]
            c_date, c_home, c_score, c_away = st.columns([1.1, 3.0, 1.8, 3.0])

            # Build badges (joker / casino / star)
            badges = ""
            if mid in ex.get("jokers", []):  badges += "🃏"
            if mid in ex.get("casinos", []): badges += "🎰"
            star = ex.get("star_team", "")
            if star and star in (match["home"], match["away"]):
                badges += "⭐"
            badges_html = (
                f"<div style='font-size:0.95rem;margin-top:3px;letter-spacing:2px'>{badges}</div>"
                if badges else ""
            )

            with c_date:
                st.markdown(
                    f"<div style='color:#8893a8;font-size:0.78rem;padding-top:8px;line-height:1.35'>"
                    f"<span style='color:#cdd5e3;font-weight:600'>{match['date']}</span><br>"
                    f"<span style='font-size:0.68rem'>📍 {match['city']}</span>"
                    f"{badges_html}</div>",
                    unsafe_allow_html=True
                )
            with c_home:
                st.markdown(
                    f"<div style='text-align:right;padding-top:6px;font-size:0.95rem;font-weight:600;color:#e6ebf5'>"
                    f"{match['home']} {flag_img(match['home'], '48x36')}</div>",
                    unsafe_allow_html=True
                )
            with c_score:
                s1, s2, s3 = st.columns([1, 0.25, 1])
                with s1:
                    st.text_input(
                        "thuis",
                        key=f"m{mid}_home",
                        label_visibility="collapsed",
                        max_chars=2,
                        placeholder="–",
                        disabled=past_deadline,
                    )
                with s2:
                    st.markdown(
                        "<div style='text-align:center;padding-top:8px;font-weight:800;color:#f5b841;font-size:1.1rem'>:</div>",
                        unsafe_allow_html=True
                    )
                with s3:
                    st.text_input(
                        "uit",
                        key=f"m{mid}_away",
                        label_visibility="collapsed",
                        max_chars=2,
                        placeholder="–",
                        disabled=past_deadline,
                    )
            with c_away:
                st.markdown(
                    f"<div style='padding-top:6px;font-size:0.95rem;font-weight:600;color:#e6ebf5'>"
                    f"{flag_img(match['away'], '48x36')} {match['away']}</div>",
                    unsafe_allow_html=True
                )

    with col_table:
        render_group_table(group, get_predictions())

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)


for group in get_groups():
    render_group(group)


# ── Bonus predictions / Power-ups ─────────────────────────────────────────────
st.divider()
st.markdown("## 🎮 Power-ups & Bonusvoorspellingen")

all_teams = sorted(set(m["home"] for m in MATCHES) | set(m["away"] for m in MATCHES))
match_options = [m["id"] for m in MATCHES]
def match_label(mid):
    m = next(x for x in MATCHES if x["id"] == mid)
    return f"{m['date']} · {m['home']} vs {m['away']} (Gr. {m['group']})"

# Initialise extras keys
extras = st.session_state.extras
extras.setdefault("jokers",     [])
extras.setdefault("casinos",    [])
extras.setdefault("star_team",  "")
extras.setdefault("underdog",   "")
extras.setdefault("champion",   "")
# Reset if it's the wrong type (e.g. legacy data)
ts = extras.get("topscorers")
if not isinstance(ts, list) or not all(isinstance(x, dict) for x in ts):
    extras["topscorers"] = [{"team": "", "name": ""} for _ in range(6)]

# ── Jokers ────────────────────────────────────────────────────────────────────
st.markdown("#### 🃏 Joker-wedstrijden (kies 4) — punten × 1.5")
jokers = st.multiselect(
    "Joker matches",
    options=match_options,
    default=[mid for mid in extras["jokers"] if mid in match_options],
    format_func=match_label,
    max_selections=4,
    key="ui_jokers",
    label_visibility="collapsed",
    disabled=past_deadline,
)

# ── Casinos ───────────────────────────────────────────────────────────────────
st.markdown("#### 🎰 Casino-wedstrijden (kies 4) — × 2.5 als correct, −5 als fout (kan niet samen met Joker)")
casinos = st.multiselect(
    "Casino matches",
    options=[mid for mid in match_options if mid not in jokers],
    default=[mid for mid in extras["casinos"] if mid in match_options and mid not in jokers],
    format_func=match_label,
    max_selections=4,
    key="ui_casinos",
    label_visibility="collapsed",
    disabled=past_deadline,
)

overlap = set(jokers) & set(casinos)
if overlap:
    st.error("❌ Een wedstrijd kan niet tegelijk Joker én Casino zijn. "
             "Pas een van beide aan.")

# ── Star team & Underdog ──────────────────────────────────────────────────────
col_star, col_under = st.columns(2)
with col_star:
    st.markdown("#### ⭐ Star-Team — × 2 op al hun groepswedstrijden")
    team_options = ["— kies team —"] + all_teams
    star_idx = team_options.index(extras["star_team"]) if extras["star_team"] in team_options else 0
    star_team = st.selectbox("Star team", options=team_options, index=star_idx,
                             key="ui_star", label_visibility="collapsed",
                             disabled=past_deadline)

with col_under:
    st.markdown("#### 🐺 Underdog — +30 per zege, +20 per gelijkspel")
    underdog_options = ["— kies team —"] + sorted(UNDERDOG_TEAMS)
    under_idx = underdog_options.index(extras["underdog"]) if extras["underdog"] in underdog_options else 0
    underdog = st.selectbox("Underdog", options=underdog_options, index=under_idx,
                            key="ui_under", label_visibility="collapsed",
                            disabled=past_deadline)

# ── Champion ──────────────────────────────────────────────────────────────────
st.markdown("#### 🏆 Wereldkampioen — +150 als correct")
champ_options = ["— kies team —"] + all_teams
champ_idx = champ_options.index(extras["champion"]) if extras["champion"] in champ_options else 0
champion = st.selectbox("Champion", options=champ_options, index=champ_idx,
                        key="ui_champion", label_visibility="collapsed",
                        disabled=past_deadline)

# ── Top scorer picks (6 players) ──────────────────────────────────────────────
st.markdown("#### ⚽ Topscorer-spelers (kies 6)")
st.caption(
    f"Punten per doelpunt in de groepsfase — "
    f"Verdediger: {POSITION_POINTS['Verdediger']} · "
    f"Middenvelder: {POSITION_POINTS['Middenvelder']} · "
    f"Aanvaller: {POSITION_POINTS['Aanvaller']}  ·  "
    f"Multipliers van 🃏/🎰/⭐ wedstrijden tellen ook door op deze punten."
)

countries = ["— kies land —"] + sorted(PLAYERS.keys())
new_topscorers = []
for i in range(6):
    saved = {"team": "", "name": ""}
    if i < len(extras["topscorers"]):
        item = extras["topscorers"][i]
        if isinstance(item, dict):
            saved = {"team": item.get("team", ""), "name": item.get("name", "")}
    c1, c2 = st.columns(2)
    with c1:
        c_idx = countries.index(saved["team"]) if saved["team"] in countries else 0
        country = st.selectbox(f"Speler {i+1} — Land",
                               options=countries, index=c_idx,
                               key=f"ts_country_{i}",
                               disabled=past_deadline)
    with c2:
        if country and country != "— kies land —" and PLAYERS.get(country):
            player_opts = ["— kies speler —"] + [
                f"{p['name']} ({p['position']})" for p in PLAYERS[country]
            ]
            # Find saved name in options
            saved_label = next(
                (f"{p['name']} ({p['position']})"
                 for p in PLAYERS[country] if p["name"] == saved["name"]),
                "— kies speler —"
            )
            p_idx = player_opts.index(saved_label) if saved_label in player_opts else 0
            picked = st.selectbox(f"Speler {i+1} — Naam",
                                  options=player_opts, index=p_idx,
                                  key=f"ts_player_{i}",
                                  disabled=past_deadline)
            player_name = picked.rsplit(" (", 1)[0] if picked != "— kies speler —" else ""
        else:
            st.selectbox(f"Speler {i+1} — Naam",
                         options=["— kies eerst een land —"],
                         disabled=True, key=f"ts_player_{i}_dis")
            player_name = ""
    new_topscorers.append({
        "team":  country if country != "— kies land —" else "",
        "name":  player_name,
    })

# Persist all bonus selections
if not past_deadline:
    st.session_state.extras = {
        "jokers":     jokers,
        "casinos":    casinos,
        "star_team":  star_team if star_team != "— kies team —" else "",
        "underdog":   underdog  if underdog  != "— kies team —" else "",
        "champion":   champion  if champion  != "— kies team —" else "",
        "topscorers": new_topscorers,
    }
# ── Bonus summary card ────────────────────────────────────────────────────
ex_now = st.session_state.extras
st.markdown(f"""
<div class='bonus-summary'>
🃏 Jokers: <strong>{len(ex_now['jokers'])}/{JOKER_LIMIT}</strong> &nbsp;·&nbsp;
🎰 Casino: <strong>{len(ex_now['casinos'])}/{CASINO_LIMIT}</strong> &nbsp;·&nbsp;
⭐ STAR: <strong>{ex_now['star_team'] or '—'}</strong> &nbsp;·&nbsp;
🐴 Underdog: <strong>{ex_now['underdog'] or '—'}</strong> &nbsp;·&nbsp;
🥇 Kampioen: <strong>{ex_now['champion'] or '—'}</strong> &nbsp;·&nbsp;
⚽ Topscorers: <strong>{sum(1 for t in ex_now['topscorers'] if t) }/{TOPSCORER_SLOTS}</strong>
</div>
""", unsafe_allow_html=True)


# ── Progress, save & export ──────────────────────────────────────────────────
st.divider()

current_preds = get_predictions()
filled = sum(
    1 for sc in current_preds.values()
    if sc.get("home") is not None and sc.get("away") is not None
)
total = len(MATCHES)
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

if not past_deadline and filled < total:
    st.warning("⚠️ Nog niet alle wedstrijden ingevuld. Je kunt al wel tussentijds opslaan.")

# Auto-save to URL (only when something actually changed)
if name.strip() and not past_deadline:
    encoded = encode_predictions(name.strip(), current_preds, st.session_state.extras)
    if encoded != st.session_state.get("_last_encoded"):
        st.session_state["_last_encoded"] = encoded
        st.query_params["d"] = encoded

# ── Save, Export, Submit ─────────────────────────────────────────────────────
col_save, col_export, col_submit = st.columns(3)

with col_save:
    if not past_deadline:
        if st.button("🔖 Sla op", type="secondary", use_container_width=True):
            encoded = encode_predictions(name.strip(), current_preds, st.session_state.extras)
            st.query_params["d"] = encoded
            st.success("✅ Opgeslagen! Bookmark de URL.")
    else:
        st.button("🔒 Deadline verstreken", disabled=True, use_container_width=True)

with col_export:
    json_str = build_export_payload(name.strip(), current_preds, MATCHES, st.session_state.extras)
    st.download_button(
        label="📤 Download (.json)",
        data=json_str,
        file_name=f"voorspelling_{name.strip().replace(' ', '_')}.json",
        mime="application/json",
        use_container_width=True,
    )

with col_submit:
    already_sent = st.session_state.get("submitted", False)
    if past_deadline:
        st.button("🔒 Deadline verstreken", disabled=True, use_container_width=True, key="submit_locked")
    elif already_sent:
        st.button("✅ Reeds ingestuurd", disabled=True, use_container_width=True, key="submit_done")
    else:
        if st.button("📩 Definitief insturen", type="primary", use_container_width=True):
            if filled < total:
                # Warn but still allow
                st.warning(f"⚠️ Je hebt pas {filled}/{total} wedstrijden ingevuld. "
                           f"Je inzending wordt nu zo verstuurd. Je kan later opnieuw insturen om te updaten.")
            try:
                with st.spinner("Bezig met versturen..."):
                    send_predictions_email(name.strip(), json_str)
                st.session_state["submitted"] = True
                st.success(f"🎉 Bedankt **{name.strip()}**! Je inzending is verstuurd naar de organisator.")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Versturen mislukt: {e}")
                st.info("Geen zorgen — gebruik de **Download (.json)** knop en stuur het bestand handmatig op.")
                
if not past_deadline:
    st.caption(
        "💡 **Sla op** = tussentijds bewaren via URL · "
        "**Download** = bestand voor jezelf · "
        "**Definitief insturen** = mail naar de organisator (kan maar 1× per sessie)."
    )
    
st.markdown("""
<div class='footer'>
    WK 2026 Familiepoel · Gemaakt met <span class='heart'>♥</span> · Veel plezier en succes! ⚽🏆
</div>
""", unsafe_allow_html=True)