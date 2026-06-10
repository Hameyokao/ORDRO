import base64
from pathlib import Path
import streamlit as st
from .database import get_setting, UPLOAD_DIR

# ─── Background themes ───────────────────────────────────────────────────────
THEMES = {
    "Cloud White":      ("#ffffff", "#f8fafc", "#f1f5f9"),
    "Warm Ivory":       ("#fffdf7", "#fdf8ef", "#f9f4e8"),
    "Soft Slate":       ("#f8fafc", "#f1f5f9", "#e8edf5"),
    "Cool Mist":        ("#f5f9ff", "#eef4fd", "#e6f0fb"),
    "Pearl Grey":       ("#fafafa", "#f4f4f6", "#edeef2"),
    "Linen":            ("#fffbf5", "#fdf6ec", "#f8ede0"),
    "Ice Blue":         ("#f0f8ff", "#e8f2fc", "#deeef9"),
    "Mint Frost":       ("#f2fdf8", "#e8f9f2", "#ddf4ea"),
    "Blush":            ("#fff5f7", "#feeef2", "#fde6ec"),
    "Lavender Mist":    ("#f8f5ff", "#f0eaff", "#e8deff"),
    "Peach Cream":      ("#fff8f3", "#fff1e8", "#ffe8d8"),
    "Ocean Tint":       ("#f0faff", "#e0f4fd", "#cdeeff"),
    "Sage Whisper":     ("#f4faf4", "#ecf7ec", "#dff0df"),
    "Sunset Soft":      ("#fff9f0", "#fff2e0", "#ffe8c8"),
    "Charcoal Night":   ("#1a1d23", "#1e2128", "#22262f"),
    "Deep Navy":        ("#0f1623", "#131b2e", "#172040"),
    "Midnight Slate":   ("#12141a", "#16181f", "#1a1d25"),
}

# ─── Accent colours ──────────────────────────────────────────────────────────
COLORS = {
    "Midnight Blue":   "#1d4ed8",
    "Royal Blue":      "#2563eb",
    "Cobalt":          "#0ea5e9",
    "Teal":            "#0d9488",
    "Emerald":         "#059669",
    "Forest":          "#16a34a",
    "Violet":          "#7c3aed",
    "Grape":           "#9333ea",
    "Rose":            "#e11d48",
    "Crimson":         "#dc2626",
    "Amber":           "#d97706",
    "Coral":           "#f97316",
    "Fuchsia":         "#c026d3",
    "Indigo":          "#4f46e5",
    "Slate":           "#475569",
    "Charcoal":        "#334155",
    "Ink":             "#0f172a",
    "Gold":            "#b45309",
    "Sky":             "#0284c7",
    "Pink":            "#db2777",
}

# ─── Banner overlays ─────────────────────────────────────────────────────────
BANNER_THEMES = {
    "Solid Clean":            "none",
    "Corner Glow":            "radial-gradient(ellipse at 100% 0%, rgba(255,255,255,.22) 0%, transparent 55%)",
    "Soft Halo":              "radial-gradient(ellipse at 80% 50%, rgba(255,255,255,.18) 0%, transparent 60%)",
    "Diagonal Lines":         "repeating-linear-gradient(135deg, rgba(255,255,255,0) 0px, rgba(255,255,255,0) 18px, rgba(255,255,255,.08) 18px, rgba(255,255,255,.08) 19px)",
    "Dot Matrix":             "radial-gradient(rgba(255,255,255,.18) 1px, transparent 1px)",
    "Fine Grid":              "linear-gradient(rgba(255,255,255,.07) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.07) 1px, transparent 1px)",
    "Top Edge Light":         "linear-gradient(180deg, rgba(255,255,255,.18) 0%, transparent 60%)",
    "Left Fade":              "linear-gradient(90deg, rgba(255,255,255,.15) 0%, transparent 55%)",
    "Vertical Stripes":       "repeating-linear-gradient(90deg, rgba(255,255,255,0) 0px, rgba(255,255,255,0) 38px, rgba(255,255,255,.07) 38px, rgba(255,255,255,.07) 39px)",
    "Bottom Vignette":        "linear-gradient(0deg, rgba(0,0,0,.14) 0%, transparent 60%)",
    "Double Glow":            "radial-gradient(ellipse at 0% 100%, rgba(255,255,255,.18) 0%, transparent 50%), radial-gradient(ellipse at 100% 0%, rgba(255,255,255,.18) 0%, transparent 50%)",
    "Horizon Split":          "linear-gradient(180deg, rgba(255,255,255,.12) 0%, rgba(255,255,255,0) 50%, rgba(0,0,0,.08) 100%)",
    "Crosshatch":             "repeating-linear-gradient(45deg, rgba(255,255,255,.04) 0px, rgba(255,255,255,.04) 1px, transparent 1px, transparent 12px), repeating-linear-gradient(-45deg, rgba(255,255,255,.04) 0px, rgba(255,255,255,.04) 1px, transparent 1px, transparent 12px)",
    "Wave Shine":             "radial-gradient(ellipse at 50% 0%, rgba(255,255,255,.28) 0%, transparent 65%)",
    "Bokeh Glow":             "radial-gradient(circle at 20% 60%, rgba(255,255,255,.12) 0%, transparent 40%), radial-gradient(circle at 80% 30%, rgba(255,255,255,.10) 0%, transparent 35%)",
    "Neon Edge":              "linear-gradient(90deg, rgba(255,255,255,.0) 0%, rgba(255,255,255,.15) 50%, rgba(255,255,255,.0) 100%)",
    "Gold Shimmer":           "linear-gradient(135deg, rgba(255,215,0,.08) 0%, rgba(255,255,255,.12) 50%, rgba(255,215,0,.06) 100%)",
    "Prism":                  "linear-gradient(135deg, rgba(255,255,255,.14) 0%, transparent 30%, rgba(255,255,255,.08) 60%, transparent 100%)",
}

BANNER_SIZES = {
    "Dot Matrix":          "18px 18px",
    "Fine Grid":           "24px 24px",
    "Vertical Stripes":    "39px 100%",
    "Crosshatch":          "12px 12px",
}


def get_branding():
    return {
        "app_name":         "ORDRO",
        "business_name":    get_setting("business_name", "Your Business"),
        "business_logo":    get_setting("business_logo", ""),
        "theme_name":       get_setting("theme_name", "Cloud White"),
        "accent_color":     get_setting("accent_color", "Royal Blue"),
        "banner_theme":     get_setting("banner_theme", "Corner Glow"),
        "business_address": get_setting("business_address", ""),
        "business_phone":   get_setting("business_phone", ""),
        "business_email":   get_setting("business_email", ""),
        "business_website": get_setting("business_website", ""),
        "facebook_id":      get_setting("facebook_id", ""),
        "instagram_id":     get_setting("instagram_id", ""),
        "tiktok_id":        get_setting("tiktok_id", ""),
        "whatsapp_contact": get_setting("whatsapp_contact", ""),
        "viber_contact":    get_setting("viber_contact", ""),
    }


def logo_data_uri(filename: str):
    if not filename:
        return ""
    path = UPLOAD_DIR / filename
    if not path.exists():
        return ""
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("utf-8")


PALETTE_STYLES = {
    "Aurora": {
        "bg": "linear-gradient(135deg,#e0f7fa 0%,#f3e5f5 100%)",
        "card_bg": "rgba(255,255,255,0.85)",
        "card_shadow": "0 20px 40px rgba(0,191,165,0.15)",
        "input_bg": "rgba(255,255,255,0.6)",
        "input_border": "1px solid rgba(0,191,165,0.20)",
        "btn_bg": "#00bfa5",
        "btn_glow": "rgba(0,191,165,0.35)",
        "focus_ring": "#00bfa5",
        "focus_glow": "rgba(0,191,165,0.20)",
        "text_primary": "#1e293b",
        "text_secondary": "#64748b",
        "radius_card": "28px",
        "radius_input": "16px"
    },
    "Mint": {
        "bg": "linear-gradient(180deg,#e8f5e9 0%,#ffffff 100%)",
        "card_bg": "#ffffff",
        "card_shadow": "0 20px 40px rgba(0,200,83,0.12)",
        "input_bg": "#f1f8e9",
        "input_border": "1px solid rgba(0,200,83,0.20)",
        "btn_bg": "#00c853",
        "btn_glow": "rgba(0,200,83,0.30)",
        "focus_ring": "#00c853",
        "focus_glow": "rgba(0,200,83,0.20)",
        "text_primary": "#1b5e20",
        "text_secondary": "#4caf50",
        "radius_card": "24px",
        "radius_input": "14px"
    },
    "Lavender": {
        "bg": "linear-gradient(135deg,#f3e5f5 0%,#ede7f6 100%)",
        "card_bg": "rgba(255,255,255,0.9)",
        "card_shadow": "0 20px 40px rgba(124,77,255,0.15)",
        "input_bg": "#f8f5ff",
        "input_border": "1px solid rgba(124,77,255,0.20)",
        "btn_bg": "#7c4dff",
        "btn_glow": "rgba(124,77,255,0.35)",
        "focus_ring": "#7c4dff",
        "focus_glow": "rgba(124,77,255,0.20)",
        "text_primary": "#311b92",
        "text_secondary": "#7e57c2",
        "radius_card": "28px",
        "radius_input": "16px"
    },
    "Sunset": {
        "bg": "linear-gradient(135deg,#fff3e0 0%,#fce4ec 100%)",
        "card_bg": "rgba(255,255,255,0.9)",
        "card_shadow": "0 20px 40px rgba(255,82,82,0.15)",
        "input_bg": "#fff8f6",
        "input_border": "1px solid rgba(255,82,82,0.20)",
        "btn_bg": "#ff5252",
        "btn_glow": "rgba(255,82,82,0.35)",
        "focus_ring": "#ff5252",
        "focus_glow": "rgba(255,82,82,0.20)",
        "text_primary": "#bf360c",
        "text_secondary": "#ff7043",
        "radius_card": "28px",
        "radius_input": "16px"
    },
    "Ocean": {
        "bg": "linear-gradient(180deg,#e3f2fd 0%,#ffffff 100%)",
        "card_bg": "#ffffff",
        "card_shadow": "0 20px 40px rgba(41,121,255,0.12)",
        "input_bg": "#f0f7ff",
        "input_border": "1px solid rgba(41,121,255,0.20)",
        "btn_bg": "#2979ff",
        "btn_glow": "rgba(41,121,255,0.30)",
        "focus_ring": "#2979ff",
        "focus_glow": "rgba(41,121,255,0.20)",
        "text_primary": "#0d47a1",
        "text_secondary": "#42a5f5",
        "radius_card": "24px",
        "radius_input": "14px"
    },
    "Blossom": {
        "bg": "linear-gradient(135deg,#fce4ec 0%,#f8bbd0 100%)",
        "card_bg": "rgba(255,255,255,0.9)",
        "card_shadow": "0 20px 40px rgba(245,0,87,0.15)",
        "input_bg": "#fff0f5",
        "input_border": "1px solid rgba(245,0,87,0.20)",
        "btn_bg": "#f50057",
        "btn_glow": "rgba(245,0,87,0.35)",
        "focus_ring": "#f50057",
        "focus_glow": "rgba(245,0,87,0.20)",
        "text_primary": "#880e4f",
        "text_secondary": "#ec407a",
        "radius_card": "28px",
        "radius_input": "16px"
    },
    "Berry": {
        "bg": "linear-gradient(135deg,#f3e5f5 0%,#fce4ec 100%)",
        "card_bg": "rgba(255,255,255,0.9)",
        "card_shadow": "0 20px 40px rgba(224,64,251,0.15)",
        "input_bg": "#fdf5ff",
        "input_border": "1px solid rgba(224,64,251,0.20)",
        "btn_bg": "#e040fb",
        "btn_glow": "rgba(224,64,251,0.35)",
        "focus_ring": "#e040fb",
        "focus_glow": "rgba(224,64,251,0.20)",
        "text_primary": "#4a148c",
        "text_secondary": "#ba68c8",
        "radius_card": "28px",
        "radius_input": "16px"
    },
    "Sky": {
        "bg": "linear-gradient(180deg,#e1f5fe 0%,#b3e5fc 100%)",
        "card_bg": "rgba(255,255,255,0.85)",
        "card_shadow": "0 20px 40px rgba(0,176,255,0.15)",
        "input_bg": "rgba(255,255,255,0.6)",
        "input_border": "1px solid rgba(0,176,255,0.20)",
        "btn_bg": "#00b0ff",
        "btn_glow": "rgba(0,176,255,0.35)",
        "focus_ring": "#00b0ff",
        "focus_glow": "rgba(0,176,255,0.20)",
        "text_primary": "#01579b",
        "text_secondary": "#29b6f6",
        "radius_card": "28px",
        "radius_input": "16px"
    },
    "Emerald": {
        "bg": "linear-gradient(135deg,#e8f5e9 0%,#c8e6c9 100%)",
        "card_bg": "#ffffff",
        "card_shadow": "0 20px 40px rgba(0,191,165,0.15)",
        "input_bg": "#f1f8f4",
        "input_border": "1px solid rgba(0,191,165,0.20)",
        "btn_bg": "#00bfa5",
        "btn_glow": "rgba(0,191,165,0.35)",
        "focus_ring": "#00bfa5",
        "focus_glow": "rgba(0,191,165,0.20)",
        "text_primary": "#004d40",
        "text_secondary": "#26a69a",
        "radius_card": "24px",
        "radius_input": "14px"
    },
    "Indigo": {
        "bg": "linear-gradient(135deg,#e8eaf6 0%,#c5cae9 100%)",
        "card_bg": "#ffffff",
        "card_shadow": "0 20px 40px rgba(83,109,254,0.15)",
        "input_bg": "#f5f6ff",
        "input_border": "1px solid rgba(83,109,254,0.20)",
        "btn_bg": "#536dfe",
        "btn_glow": "rgba(83,109,254,0.35)",
        "focus_ring": "#536dfe",
        "focus_glow": "rgba(83,109,254,0.20)",
        "text_primary": "#1a237e",
        "text_secondary": "#5c6bc0",
        "radius_card": "24px",
        "radius_input": "14px"
    },
    "Candy": {
        "bg": "linear-gradient(135deg,#f8bbd0 0%,#e1bee7 100%)",
        "card_bg": "rgba(255,255,255,0.85)",
        "card_shadow": "0 20px 40px rgba(236,64,122,0.15)",
        "input_bg": "rgba(255,255,255,0.6)",
        "input_border": "1px solid rgba(236,64,122,0.20)",
        "btn_bg": "#ec407a",
        "btn_glow": "rgba(236,64,122,0.35)",
        "focus_ring": "#ec407a",
        "focus_glow": "rgba(236,64,122,0.20)",
        "text_primary": "#880e4f",
        "text_secondary": "#d81b60",
        "radius_card": "28px",
        "radius_input": "16px"
    },
    "Rose": {
        "bg": "linear-gradient(135deg,#ffebee 0%,#ffcdd2 100%)",
        "card_bg": "rgba(255,255,255,0.9)",
        "card_shadow": "0 20px 40px rgba(239,83,80,0.15)",
        "input_bg": "#fff5f5",
        "input_border": "1px solid rgba(239,83,80,0.20)",
        "btn_bg": "#ef5350",
        "btn_glow": "rgba(239,83,80,0.35)",
        "focus_ring": "#ef5350",
        "focus_glow": "rgba(239,83,80,0.20)",
        "text_primary": "#b71c1c",
        "text_secondary": "#e57373",
        "radius_card": "28px",
        "radius_input": "16px"
    },
    "Mist": {
        "bg": "linear-gradient(135deg,#f5f7fa 0%,#e4e8ec 100%)",
        "card_bg": "rgba(255,255,255,0.85)",
        "card_shadow": "0 20px 40px rgba(100,116,139,0.10)",
        "input_bg": "rgba(255,255,255,0.7)",
        "input_border": "1px solid rgba(100,116,139,0.20)",
        "btn_bg": "#64748b",
        "btn_glow": "rgba(100,116,139,0.30)",
        "focus_ring": "#64748b",
        "focus_glow": "rgba(100,116,139,0.20)",
        "text_primary": "#334155",
        "text_secondary": "#64748b",
        "radius_card": "24px",
        "radius_input": "14px"
    },
    "Fog": {
        "bg": "linear-gradient(180deg,#f8f9fa 0%,#e9ecef 100%)",
        "card_bg": "#ffffff",
        "card_shadow": "0 20px 40px rgba(148,163,184,0.12)",
        "input_bg": "#f8f9fa",
        "input_border": "1px solid rgba(148,163,184,0.25)",
        "btn_bg": "#94a3b8",
        "btn_glow": "rgba(148,163,184,0.30)",
        "focus_ring": "#94a3b8",
        "focus_glow": "rgba(148,163,184,0.20)",
        "text_primary": "#1e293b",
        "text_secondary": "#64748b",
        "radius_card": "28px",
        "radius_input": "16px"
    },
    "Silver": {
        "bg": "linear-gradient(135deg,#f1f5f9 0%,#e2e8f0 100%)",
        "card_bg": "rgba(255,255,255,0.9)",
        "card_shadow": "0 20px 40px rgba(71,85,105,0.12)",
        "input_bg": "#ffffff",
        "input_border": "1px solid rgba(71,85,105,0.20)",
        "btn_bg": "#475569",
        "btn_glow": "rgba(71,85,105,0.30)",
        "focus_ring": "#475569",
        "focus_glow": "rgba(71,85,105,0.20)",
        "text_primary": "#0f172a",
        "text_secondary": "#475569",
        "radius_card": "24px",
        "radius_input": "14px"
    },
    "Coral": {
        "bg": "linear-gradient(135deg,#fff3e0 0%,#ffe0b2 100%)",
        "card_bg": "rgba(255,255,255,0.9)",
        "card_shadow": "0 20px 40px rgba(255,110,64,0.15)",
        "input_bg": "#fff6f0",
        "input_border": "1px solid rgba(255,110,64,0.20)",
        "btn_bg": "#ff6e40",
        "btn_glow": "rgba(255,110,64,0.35)",
        "focus_ring": "#ff6e40",
        "focus_glow": "rgba(255,110,64,0.20)",
        "text_primary": "#bf360c",
        "text_secondary": "#ff8a65",
        "radius_card": "28px",
        "radius_input": "16px"
    },
    "Amber": {
        "bg": "linear-gradient(135deg,#fff8e1 0%,#ffecb3 100%)",
        "card_bg": "#ffffff",
        "card_shadow": "0 20px 40px rgba(255,160,0,0.15)",
        "input_bg": "#fffdf5",
        "input_border": "1px solid rgba(255,160,0,0.22)",
        "btn_bg": "#ff8f00",
        "btn_glow": "rgba(255,160,0,0.32)",
        "focus_ring": "#ff8f00",
        "focus_glow": "rgba(255,160,0,0.20)",
        "text_primary": "#e65100",
        "text_secondary": "#ffa726",
        "radius_card": "24px",
        "radius_input": "14px"
    },
    "Teal": {
        "bg": "linear-gradient(180deg,#e0f2f1 0%,#ffffff 100%)",
        "card_bg": "#ffffff",
        "card_shadow": "0 20px 40px rgba(0,150,136,0.14)",
        "input_bg": "#f0faf9",
        "input_border": "1px solid rgba(0,150,136,0.20)",
        "btn_bg": "#009688",
        "btn_glow": "rgba(0,150,136,0.30)",
        "focus_ring": "#009688",
        "focus_glow": "rgba(0,150,136,0.20)",
        "text_primary": "#004d40",
        "text_secondary": "#26a69a",
        "radius_card": "24px",
        "radius_input": "14px"
    },
    "Plum": {
        "bg": "linear-gradient(135deg,#f3e5f5 0%,#e1bee7 100%)",
        "card_bg": "rgba(255,255,255,0.9)",
        "card_shadow": "0 20px 40px rgba(142,36,170,0.15)",
        "input_bg": "#faf2fc",
        "input_border": "1px solid rgba(142,36,170,0.20)",
        "btn_bg": "#8e24aa",
        "btn_glow": "rgba(142,36,170,0.35)",
        "focus_ring": "#8e24aa",
        "focus_glow": "rgba(142,36,170,0.20)",
        "text_primary": "#4a148c",
        "text_secondary": "#ab47bc",
        "radius_card": "28px",
        "radius_input": "16px"
    },
    "Forest": {
        "bg": "linear-gradient(135deg,#e8f5e9 0%,#c8e6c9 100%)",
        "card_bg": "#ffffff",
        "card_shadow": "0 20px 40px rgba(46,125,50,0.15)",
        "input_bg": "#f1f8f1",
        "input_border": "1px solid rgba(46,125,50,0.20)",
        "btn_bg": "#2e7d32",
        "btn_glow": "rgba(46,125,50,0.30)",
        "focus_ring": "#2e7d32",
        "focus_glow": "rgba(46,125,50,0.20)",
        "text_primary": "#1b5e20",
        "text_secondary": "#43a047",
        "radius_card": "24px",
        "radius_input": "14px"
    },
    "Graphite": {
        "bg": "linear-gradient(135deg,#eceff1 0%,#cfd8dc 100%)",
        "card_bg": "rgba(255,255,255,0.9)",
        "card_shadow": "0 20px 40px rgba(55,71,79,0.14)",
        "input_bg": "#f7f9fa",
        "input_border": "1px solid rgba(55,71,79,0.18)",
        "btn_bg": "#37474f",
        "btn_glow": "rgba(55,71,79,0.30)",
        "focus_ring": "#37474f",
        "focus_glow": "rgba(55,71,79,0.20)",
        "text_primary": "#263238",
        "text_secondary": "#546e7a",
        "radius_card": "24px",
        "radius_input": "14px"
    },
    "Peach": {
        "bg": "linear-gradient(135deg,#fff3e0 0%,#ffccbc 100%)",
        "card_bg": "rgba(255,255,255,0.9)",
        "card_shadow": "0 20px 40px rgba(255,138,101,0.15)",
        "input_bg": "#fff7f2",
        "input_border": "1px solid rgba(255,138,101,0.20)",
        "btn_bg": "#ff8a65",
        "btn_glow": "rgba(255,138,101,0.32)",
        "focus_ring": "#ff8a65",
        "focus_glow": "rgba(255,138,101,0.20)",
        "text_primary": "#d84315",
        "text_secondary": "#ffab91",
        "radius_card": "28px",
        "radius_input": "16px"
    },
    "Cocoa": {
        "bg": "linear-gradient(135deg,#efebe9 0%,#d7ccc8 100%)",
        "card_bg": "#ffffff",
        "card_shadow": "0 20px 40px rgba(121,85,72,0.14)",
        "input_bg": "#f7f4f2",
        "input_border": "1px solid rgba(121,85,72,0.20)",
        "btn_bg": "#795548",
        "btn_glow": "rgba(121,85,72,0.30)",
        "focus_ring": "#795548",
        "focus_glow": "rgba(121,85,72,0.20)",
        "text_primary": "#4e342e",
        "text_secondary": "#8d6e63",
        "radius_card": "24px",
        "radius_input": "14px"
    }
}

_PALETTE_APP_TEMPLATE = "\n        <style>\n        :root {\n          --accent:{btn_bg} !important;\n          --accent-10:{btn_bg}1a !important;\n          --accent-20:{btn_bg}33 !important;\n          --accent-40:{btn_glow} !important;\n          --ink:{text_primary} !important;\n          --muted:{text_secondary} !important;\n          --card:{card_bg} !important;\n          --card-border:transparent !important;\n        }\n        html, body, .stApp, [data-testid=\"stApp\"] {\n          background:{bg} !important;\n          color:{text_primary} !important;\n        }\n        .block-container, .stApp p, .stApp span, .stApp label,\n        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 { color:{text_primary} !important; }\n        .muted, .metric-label, .metric-note { color:{text_secondary} !important; }\n        .soft-card, .info-card, .delivery-card, .metric-card,\n        div[data-testid=\"stMetric\"], div[data-testid=\"stExpander\"],\n        div[data-testid=\"stContainer\"][data-border=\"true\"] {\n          background:{card_bg} !important;\n          border:{input_border} !important;\n          border-radius:{radius_card} !important;\n          box-shadow:{card_shadow} !important;\n        }\n        .hero-block {\n          background:linear-gradient(135deg, {btn_bg} 0%, {btn_bg}cc 100%) !important;\n          border-radius:{radius_card} !important;\n          box-shadow:0 12px 30px {btn_glow} !important;\n        }\n        .metric-value, div[data-testid=\"stMetricValue\"] { color:{text_primary} !important; }\n        .stTextInput div[data-baseweb=\"input\"],\n        .stNumberInput div[data-baseweb=\"input\"],\n        .stDateInput div[data-baseweb=\"input\"],\n        .stTextArea textarea,\n        div[data-baseweb=\"select\"] > div:first-child {\n          background:{input_bg} !important;\n          border:{input_border} !important;\n          border-radius:{radius_input} !important;\n          box-shadow:none !important;\n          color:{text_primary} !important;\n        }\n        .stTextInput input, .stNumberInput input, .stDateInput input {\n          background:transparent !important; border:none !important; box-shadow:none !important;\n          color:{text_primary} !important;\n        }\n        .stTextInput div[data-baseweb=\"input\"]:focus-within,\n        .stNumberInput div[data-baseweb=\"input\"]:focus-within {\n          border-color:{focus_ring} !important;\n          box-shadow:0 0 0 4px {focus_glow} !important;\n        }\n        .stButton > button, .stDownloadButton > button,\n        div[data-testid=\"stFormSubmitButton\"] button { border-radius:{radius_input} !important; }\n        .stButton > button[kind=\"primary\"],\n        div[data-testid=\"stFormSubmitButton\"] button[kind=\"primary\"] {\n          background:{btn_bg} !important; color:#ffffff !important; border:none !important;\n          box-shadow:0 8px 20px {btn_glow} !important;\n        }\n        .stButton > button[kind=\"primary\"]:hover,\n        div[data-testid=\"stFormSubmitButton\"] button[kind=\"primary\"]:hover {\n          transform:translateY(-2px) !important; box-shadow:0 12px 24px {btn_glow} !important;\n        }\n        .stButton > button[kind=\"secondary\"] {\n          background:{input_bg} !important; color:{text_primary} !important; border:{input_border} !important;\n        }\n        section[data-testid=\"stSidebar\"] {\n          background:{card_bg} !important; border-right:{input_border} !important;\n        }\n        .sidebar-brand {\n          background:{input_bg} !important; border:{input_border} !important;\n          border-radius:{radius_card} !important; box-shadow:{card_shadow} !important;\n        }\n        .brand-name, .app-small { color:{text_primary} !important; }\n        section[data-testid=\"stSidebar\"] div[data-testid=\"stButton\"] button { border-radius:{radius_input} !important; }\n        section[data-testid=\"stSidebar\"] div[data-testid=\"stButton\"] button[kind=\"primary\"] {\n          background:{btn_bg} !important; color:#ffffff !important; box-shadow:0 6px 16px {btn_glow} !important;\n        }\n        section[data-testid=\"stSidebar\"] div[data-testid=\"stButton\"] button[kind=\"secondary\"] {\n          background:{input_bg} !important; color:{text_primary} !important;\n        }\n        div.stDataFrame { border:{input_border} !important; border-radius:{radius_input} !important; }\n        button[data-baseweb=\"tab\"][aria-selected=\"true\"] { color:{btn_bg} !important; }\n        </style>\n"

_PALETTE_LOGIN_TEMPLATE = "\n        <style>\n        html, body, [data-testid=\"stApp\"], .stApp { background:{bg} !important; }\n        div[data-testid=\"stForm\"] {\n          background:{card_bg} !important;\n          box-shadow:{card_shadow} !important;\n          border-radius:{radius_card} !important;\n          border:{input_border} !important;\n        }\n        div[data-testid=\"stTextInput\"] [data-baseweb=\"input\"] {\n          background:{input_bg} !important;\n          border:{input_border} !important;\n          box-shadow:none !important;\n          border-radius:{radius_input} !important;\n        }\n        div[data-testid=\"stTextInput\"] [data-baseweb=\"input\"]:focus-within {\n          border-color:{focus_ring} !important;\n          box-shadow:0 0 0 4px {focus_glow} !important;\n        }\n        div[data-testid=\"stTextInput\"] input { color:{text_primary} !important; background:transparent !important; }\n        div[data-testid=\"stFormSubmitButton\"] button {\n          background:{btn_bg} !important; color:#ffffff !important;\n          box-shadow:0 8px 20px {btn_glow} !important;\n          border-radius:{radius_input} !important;\n        }\n        .ordro-pw-pill {\n          background:{input_bg} !important; box-shadow:none !important;\n          border:{input_border} !important; color:{text_secondary} !important;\n        }\n        </style>\n"

def _fill_palette(tpl, p):
    out = tpl
    for k, v in p.items():
        out = out.replace('{' + k + '}', v)
    return out

def palette_app_css(p):
    return _fill_palette(_PALETTE_APP_TEMPLATE, p)

def palette_login_css(p):
    return _fill_palette(_PALETTE_LOGIN_TEMPLATE, p)


def apply_theme():
    brand    = get_branding()
    bg1, bg2, bg3 = THEMES.get(brand["theme_name"], THEMES["Cloud White"])
    accent   = COLORS.get(brand["accent_color"], COLORS["Royal Blue"])
    banner   = BANNER_THEMES.get(brand["banner_theme"], BANNER_THEMES["Corner Glow"])
    b_size   = BANNER_SIZES.get(brand["banner_theme"], "auto")

    dark = brand["theme_name"] in ("Charcoal Night", "Deep Navy", "Midnight Slate")
    card_bg    = "rgba(30,33,40,.92)"    if dark else "rgba(255,255,255,.97)"
    card_bdr   = "rgba(255,255,255,.08)" if dark else "rgba(220,228,240,.80)"
    text_ink   = "#e8edf5"              if dark else "#0f172a"
    text_muted = "#94a3b8"
    sidebar_bg = "rgba(18,22,32,.97)"   if dark else "rgba(255,255,255,.97)"
    app_bg     = f"linear-gradient(150deg, {bg1} 0%, {bg2} 50%, {bg3} 100%)"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=DM+Mono:wght@400;500&display=swap');

    :root {{
        --accent:         {accent};
        --accent-10:      {accent}1a;
        --accent-20:      {accent}33;
        --accent-40:      {accent}66;
        --ink:            {text_ink};
        --muted:          {text_muted};
        --card:           {card_bg};
        --card-border:    {card_bdr};
        --line:           {card_bdr};
        --green:          #059669;
        --orange:         #d97706;
        --red:            #dc2626;
        --violet:         #7c3aed;
        --radius-sm:      10px;
        --radius-md:      16px;
        --radius-lg:      22px;
        --radius-xl:      28px;
        --shadow-sm:      0 1px 3px rgba(0,0,0,.07);
        --shadow-md:      0 4px 14px rgba(0,0,0,.09);
        --shadow-lg:      0 12px 32px rgba(0,0,0,.11);
    }}

    html, body, [class*="css"] {{
        font-family: 'DM Sans', system-ui, -apple-system, sans-serif;
        color: var(--ink);
        -webkit-font-smoothing: antialiased;
    }}

    .stApp {{
        background: {app_bg};
        min-height: 100vh;
    }}

    .block-container {{
        padding-top: 1.5rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        max-width: 1440px;
    }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        border-right: 1px solid var(--card-border);
        box-shadow: 4px 0 24px rgba(0,0,0,.07);
    }}
    section[data-testid="stSidebar"] * {{
        color: var(--ink) !important;
    }}

    .sidebar-brand {{
        padding: 16px;
        border-radius: var(--radius-lg);
        background: var(--card);
        border: 1px solid var(--card-border);
        box-shadow: var(--shadow-sm);
        margin-bottom: 12px;
    }}
    .sidebar-logo {{
        width: 44px; height: 44px;
        object-fit: cover;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
        flex-shrink: 0;
    }}
    .sidebar-logo-placeholder {{
        width: 44px; height: 44px;
        border-radius: var(--radius-md);
        display: flex; align-items: center; justify-content: center;
        background: var(--accent);
        color: #fff !important;
        font-weight: 700; font-size: 20px; flex-shrink: 0;
        box-shadow: 0 4px 12px var(--accent-40);
    }}
    .brand-name {{
        font-size: 15px; font-weight: 700;
        letter-spacing: -.02em; line-height: 1.2;
    }}
    .app-small {{
        font-size: 10px; font-weight: 600;
        letter-spacing: .12em; text-transform: uppercase;
        color: var(--accent) !important; margin-top: 2px;
    }}

    /* sidebar nav buttons */
    section[data-testid="stSidebar"] div[data-testid="stButton"] button {{
        width: 100%;
        border-radius: var(--radius-md) !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        letter-spacing: -.01em;
        transition: all .15s ease !important;
        padding: 10px 14px !important;
        border: none !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] {{
        background: var(--accent) !important;
        color: #fff !important;
        box-shadow: 0 4px 14px var(--accent-40) !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="secondary"] {{
        background: var(--accent-10) !important;
        color: var(--accent) !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {{
        transform: translateX(3px) !important;
    }}

    /* ── Hero / page header ── */
    .hero-block {{
        background: linear-gradient(135deg, var(--accent) 0%, {accent}cc 100%);
        background-size: {b_size};
        background-image: linear-gradient(135deg, var(--accent) 0%, {accent}cc 100%), {banner};
        border-radius: var(--radius-xl);
        padding: 26px 32px 22px;
        margin-bottom: 24px;
        color: #fff;
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 32px var(--accent-40);
    }}
    .hero-title {{
        font-size: 26px; font-weight: 700;
        letter-spacing: -.04em; margin: 0 0 4px;
    }}
    .hero-sub {{
        font-size: 14px; opacity: .82; margin: 0; font-weight: 400;
    }}

    /* ── Cards ── */
    .soft-card {{
        background: var(--card);
        border: 1px solid var(--card-border);
        border-radius: var(--radius-lg);
        padding: 20px 22px;
        box-shadow: var(--shadow-md);
        margin-bottom: 14px;
    }}

    /* ── Info card (product grid, etc.) ── */
    .info-card {{
        background: var(--card);
        border: 1px solid var(--card-border);
        border-radius: var(--radius-md);
        padding: 14px;
        box-shadow: var(--shadow-sm);
        margin-bottom: 10px;
    }}

    /* ── Delivery / order cards ── */
    .delivery-card {{
        background: var(--card);
        border: 1.5px solid var(--card-border);
        border-radius: var(--radius-lg);
        padding: 20px 22px;
        box-shadow: var(--shadow-md);
        margin-bottom: 16px;
        transition: box-shadow .18s ease;
    }}
    .delivery-card:hover {{
        box-shadow: var(--shadow-lg);
    }}

    /* ── Metric card ── */
    .metric-card {{
        background: var(--card);
        border: 1px solid var(--card-border);
        border-radius: var(--radius-lg);
        padding: 18px 20px;
        box-shadow: var(--shadow-sm);
        text-align: center;
    }}
    .metric-value {{
        font-size: 28px; font-weight: 700;
        letter-spacing: -.04em; margin: 6px 0 4px;
    }}
    .metric-label {{
        font-size: 11px; font-weight: 600;
        text-transform: uppercase; letter-spacing: .08em;
        color: var(--muted);
    }}
    .metric-note {{
        font-size: 12px; color: var(--muted); margin-top: 2px;
    }}

    /* ── Pills ── */
    .pill {{
        display: inline-flex; align-items: center;
        padding: 3px 10px; border-radius: 999px;
        font-size: 11px; font-weight: 600;
    }}
    .pill-blue   {{ background: #eff6ff; color: #1d4ed8; }}
    .pill-green  {{ background: #f0fdf4; color: #15803d; }}
    .pill-orange {{ background: #fffbeb; color: #b45309; }}
    .pill-pink   {{ background: #fdf2f8; color: #9d174d; }}
    .pill-violet {{ background: #f5f3ff; color: #5b21b6; }}
    .pill-red    {{ background: #fef2f2; color: #b91c1c; }}
    .pill-gray   {{ background: #f1f5f9; color: #475569; }}

    /* ── Muted text ── */
    .muted {{ color: var(--muted); }}

    /* ── Login ── */
    .login-center-wrap {{
        min-height: 100vh;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
    }}

    /* ── Streamlit overrides ── */
    div[data-testid="stMetricValue"] {{
        font-size: 28px; font-weight: 700;
        letter-spacing: -.03em;
    }}
    div[data-testid="stMetric"] {{
        background: var(--card);
        border: 1px solid var(--card-border);
        border-radius: var(--radius-md);
        padding: 14px 16px;
        box-shadow: var(--shadow-sm);
    }}
    .stButton > button {{
        border-radius: var(--radius-md) !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        transition: all .15s ease !important;
    }}
    .stButton > button[kind="primary"] {{
        background: var(--accent) !important;
        border: none !important;
        color: #fff !important;
        box-shadow: 0 4px 14px var(--accent-40) !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px var(--accent-40) !important;
    }}
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {{
        border-radius: var(--radius-md) !important;
        border: 1.5px solid var(--card-border) !important;
        background: var(--card) !important;
        color: var(--ink) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
    }}
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-10) !important;
    }}
    div[data-testid="stExpander"] {{
        background: var(--card);
        border: 1px solid var(--card-border) !important;
        border-radius: var(--radius-lg) !important;
        box-shadow: var(--shadow-sm);
        margin-bottom: 10px;
    }}
    div[data-testid="stContainer"][data-border="true"] {{
        background: var(--card);
        border: 1px solid var(--card-border) !important;
        border-radius: var(--radius-lg) !important;
        box-shadow: var(--shadow-sm);
        padding: 16px 20px !important;
    }}
    div.stDataFrame {{
        border-radius: var(--radius-md);
        overflow: hidden;
        border: 1px solid var(--card-border);
    }}

    /* ── Beacon animation for alerts ── */
    @keyframes beacon {{
        0%   {{ box-shadow: 0 0 0 0 rgba(220,38,38,.6); }}
        70%  {{ box-shadow: 0 0 0 10px rgba(220,38,38,0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(220,38,38,0); }}
    }}
    @keyframes beacon-orange {{
        0%   {{ box-shadow: 0 0 0 0 rgba(217,119,6,.6); }}
        70%  {{ box-shadow: 0 0 0 10px rgba(217,119,6,0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(217,119,6,0); }}
    }}
    .beacon-dot {{
        display: inline-block; width: 10px; height: 10px;
        border-radius: 50%; background: #dc2626;
        animation: beacon 1.6s infinite;
        vertical-align: middle; margin-left: 6px;
    }}
    .beacon-dot-orange {{
        display: inline-block; width: 10px; height: 10px;
        border-radius: 50%; background: #d97706;
        animation: beacon-orange 1.6s infinite;
        vertical-align: middle; margin-left: 6px;
    }}

    @media (max-width: 640px) {{
        .hero-block {{ padding: 20px; }}
        .hero-title {{ font-size: 20px; }}
        .block-container {{ padding-left: .75rem; padding-right: .75rem; }}
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── Neomorphic Soft full-app skin (opt-in from Settings → App Style) ──
    if st.session_state.get("logged_in") and get_setting("ui_style", "Classic") == "Neomorphic Soft":
        st.markdown(f"""
        <style>
        :root {{
            --ink:#1e2a3a !important;
            --muted:#5a6e8a !important;
            --card:#e0e5ec !important;
            --card-border:transparent !important;
            --line:rgba(120,140,170,.18) !important;
            --neu-bg:#eef2f9;
            --neu-surface:#e0e5ec;
            --neu-d:#bcc6d6;
            --neu-l:#ffffff;
        }}

        html, body, .stApp, [data-testid="stApp"] {{
            background:#eef2f9 !important;
            color:#1e2a3a !important;
        }}
        .block-container, .stApp p, .stApp span, .stApp label,
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {{
            color:#1e2a3a !important;
        }}
        .muted, .metric-label, .metric-note, .stCaption, small {{ color:#5a6e8a !important; }}

        /* Raised soft surfaces */
        .soft-card, .info-card, .delivery-card, .metric-card,
        div[data-testid="stMetric"],
        div[data-testid="stExpander"],
        div[data-testid="stContainer"][data-border="true"] {{
            background:#e0e5ec !important;
            border:none !important;
            border-radius:24px !important;
            box-shadow:5px 5px 11px #bcc6d6, -5px -5px 11px #ffffff !important;
        }}
        .delivery-card:hover {{
            box-shadow:7px 7px 16px #bcc6d6, -7px -7px 16px #ffffff !important;
        }}

        /* Hero keeps the accent but softer + rounder */
        .hero-block {{
            border-radius:28px !important;
            box-shadow:5px 5px 14px #bcc6d6, -5px -5px 14px #ffffff !important;
        }}
        .metric-value, div[data-testid="stMetricValue"] {{ color:#1e2a3a !important; }}

        /* Inputs → inset pressed pills */
        .stTextInput div[data-baseweb="input"],
        .stNumberInput div[data-baseweb="input"],
        .stDateInput div[data-baseweb="input"],
        .stTextArea textarea,
        div[data-baseweb="select"] > div:first-child {{
            background:#e0e5ec !important;
            border:none !important;
            border-radius:14px !important;
            box-shadow:inset 3px 3px 6px #bcc6d6, inset -3px -3px 6px #ffffff !important;
            color:#1e2a3a !important;
        }}
        .stTextInput input, .stNumberInput input, .stDateInput input {{
            background:transparent !important;
            border:none !important;
            box-shadow:none !important;
            color:#1e2a3a !important;
        }}
        .stTextInput div[data-baseweb="input"]:focus-within,
        .stNumberInput div[data-baseweb="input"]:focus-within {{
            box-shadow:inset 4px 4px 8px #b0bacb, inset -4px -4px 8px #ffffff !important;
        }}

        /* Buttons → raised, press to inset */
        .stButton > button, .stDownloadButton > button,
        div[data-testid="stFormSubmitButton"] button {{
            background:#e0e5ec !important;
            border:none !important;
            border-radius:14px !important;
            color:#2c3e66 !important;
            box-shadow:4px 4px 8px #bcc6d6, -4px -4px 8px #ffffff !important;
        }}
        .stButton > button:active, .stDownloadButton > button:active,
        div[data-testid="stFormSubmitButton"] button:active {{
            box-shadow:inset 3px 3px 6px #bcc6d6, inset -3px -3px 6px #ffffff !important;
            transform:scale(.99) !important;
        }}
        .stButton > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] button[kind="primary"] {{
            background:{accent} !important;
            color:#fff !important;
            box-shadow:4px 4px 8px #bcc6d6, -4px -4px 8px #ffffff !important;
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background:#eef2f9 !important;
            border-right:none !important;
            box-shadow:none !important;
        }}
        .sidebar-brand {{
            background:#e0e5ec !important;
            border:none !important;
            border-radius:24px !important;
            box-shadow:5px 5px 11px #bcc6d6, -5px -5px 11px #ffffff !important;
        }}
        section[data-testid="stSidebar"] div[data-testid="stButton"] button {{
            border-radius:14px !important;
            box-shadow:4px 4px 8px #bcc6d6, -4px -4px 8px #ffffff !important;
        }}
        section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="secondary"] {{
            background:#e0e5ec !important;
            color:#2c3e66 !important;
        }}
        section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] {{
            background:{accent} !important;
            color:#fff !important;
        }}

        /* Tables */
        div.stDataFrame {{
            border:none !important;
            border-radius:18px !important;
            overflow:hidden !important;
            box-shadow:inset 3px 3px 6px #bcc6d6, inset -3px -3px 6px #ffffff !important;
        }}

        /* Expander header text stays readable */
        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary * {{ color:#1e2a3a !important; }}

        /* Tabs */
        button[data-baseweb="tab"] {{ color:#5a6e8a !important; }}
        button[data-baseweb="tab"][aria-selected="true"] {{ color:{accent} !important; }}
        </style>
        """, unsafe_allow_html=True)



    _ui = get_setting("ui_style", "Classic")
    if st.session_state.get("logged_in") and _ui in PALETTE_STYLES:
        st.markdown(palette_app_css(PALETTE_STYLES[_ui]), unsafe_allow_html=True)


def hero(title: str, subtitle: str = ""):
    sub_html = f'<p class="hero-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div class="hero-block">
        <div class="hero-title">{title}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def metric_card(label: str, value: str, note: str = "", pill_class: str = "pill-blue"):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {f'<div class="metric-note"><span class="pill {pill_class}">{note}</span></div>' if note else ''}
    </div>
    """, unsafe_allow_html=True)
