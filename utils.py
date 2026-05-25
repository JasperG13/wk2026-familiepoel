# utils.py – serialization, flags, export

import base64
import gzip
import json
from datetime import datetime, timezone

from matches import FLAG_CODES

EXTRAS_KEYS = ("champion", "topscorers", "jokers", "casinos", "star_team", "underdog")


# ── Flag image helper ────────────────────────────────────────────────────────
def flag_img(team, size="48x36"):
    code = FLAG_CODES.get(team, "un")
    return (
        f"<img src='https://flagcdn.com/{size}/{code}.png' "
        f"style='vertical-align:middle;border-radius:3px;height:1.1em' alt='{team}'>"
    )


# ── URL-safe encode / decode (gzip + base64 + JSON) ──────────────────────────
def encode_predictions(name, preds, extras):
    """Encode (name, predictions, extras) into a compact URL-safe string."""
    payload = {
        "n": name,
        "p": {str(mid): [v.get("home"), v.get("away")] for mid, v in preds.items()},
        "e": {k: extras.get(k) for k in EXTRAS_KEYS if k in extras},
    }
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    compressed = gzip.compress(raw)
    return base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")


def decode_predictions(raw):
    """Decode a URL-safe string back to (name, predictions, extras)."""
    if not raw:
        return "", {}, _default_extras()

    try:
        padding = "=" * ((4 - len(raw) % 4) % 4)
        compressed = base64.urlsafe_b64decode(raw + padding)
        data = gzip.decompress(compressed)
        payload = json.loads(data)
    except Exception:
        return "", {}, _default_extras()

    # Name
    name = payload.get("n", "") or ""

    # Predictions
    preds = {}
    for k, v in (payload.get("p") or {}).items():
        try:
            mid = int(k)
            home = v[0] if len(v) > 0 else None
            away = v[1] if len(v) > 1 else None
            preds[mid] = {"home": home, "away": away}
        except (ValueError, IndexError, TypeError):
            continue

    # Extras + back-compat
    extras = payload.get("e") or {}

    # Migrate old single 'topscorer' → list of 3
    if "topscorer" in extras and "topscorers" not in extras:
        old = extras.pop("topscorer", "") or ""
        extras["topscorers"] = [old, "", ""]

    # Fill in defaults so downstream code never KeyErrors
    defaults = _default_extras()
    for k, v in defaults.items():
        extras.setdefault(k, v)

    # Sanitize types
    if not isinstance(extras.get("topscorers"), list):
        extras["topscorers"] = ["", "", ""]
    extras["topscorers"] = (extras["topscorers"] + ["", "", ""])[:3]

    if not isinstance(extras.get("jokers"), list):
        extras["jokers"] = []
    if not isinstance(extras.get("casinos"), list):
        extras["casinos"] = []
    extras["jokers"]  = [int(x) for x in extras["jokers"]  if str(x).lstrip("-").isdigit()]
    extras["casinos"] = [int(x) for x in extras["casinos"] if str(x).lstrip("-").isdigit()]

    return name, preds, extras


def _default_extras():
    return {
        "champion":   "",
        "topscorers": ["", "", ""],
        "jokers":     [],
        "casinos":    [],
        "star_team":  "",
        "underdog":   "",
    }


# ── Organizer export (pretty JSON, full match metadata) ──────────────────────
def build_export_payload(name, predictions, matches, extras=None):
    import json
    from datetime import date

    payload = {
        "naam":  name,
        "datum": str(date.today()),
        "extras": extras or {},
        "voorspellingen": {},
    }
    for match in matches:
        mid = match["id"]
        pred = predictions.get(mid, {})
        payload["voorspellingen"][str(mid)] = {
            "thuis":       match["home"],
            "uit":         match["away"],
            "groep":       match["group"],
            "score_thuis": pred.get("home"),
            "score_uit":   pred.get("away"),
        }
    return json.dumps(payload, ensure_ascii=False, indent=2)

def send_predictions_email(name, json_str):
    """Send the predictions JSON as an attachment to the organizer."""
    import smtplib, ssl
    from email.message import EmailMessage
    import streamlit as st

    cfg = st.secrets["email"]

    msg = EmailMessage()
    msg["Subject"] = f"⚽ WK 2026 Voorspelling — {name}"
    msg["From"] = cfg["sender"]
    msg["To"] = cfg["recipient"]
    msg.set_content(
        f"Nieuwe voorspelling binnen!\n\n"
        f"Naam: {name}\n\n"
        f"De volledige voorspelling zit als JSON-bijlage."
    )

    safe_name = name.replace(" ", "_")
    msg.add_attachment(
        json_str.encode("utf-8"),
        maintype="application",
        subtype="json",
        filename=f"voorspelling_{safe_name}.json",
    )

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(cfg["smtp_host"], int(cfg["smtp_port"]), context=context) as smtp:
        smtp.login(cfg["sender"], cfg["password"])
        smtp.send_message(msg)