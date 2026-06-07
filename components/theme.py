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
