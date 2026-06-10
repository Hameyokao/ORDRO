from datetime import date, timedelta
import streamlit as st
from components.database import query_df, get_setting, scalar
from components.theme import hero
from components.auth import has_access
import components.charts as charts

REPORTS = [
    ("sp_week",    "Sales & Profit — Weekly"),
    ("sp_month",   "Sales & Profit — Monthly"),
    ("sp_year",    "Sales & Profit — Yearly"),
    ("rcn",        "Revenue vs Cost of Goods vs Net Profit"),
    ("items_rev",  "Number of Items vs Revenue"),
    ("cat",        "Sales & Profit by Category"),
    ("prod",       "Sales & Profit by Product"),
    ("top_rev",    "Top Products — by Revenue"),
    ("top_profit", "Top Products — by Profit (amount)"),
    ("top_pct",    "Top Products — by Profit %"),
    ("top_vol",    "Top Products — by Volume"),
    ("exp",        "Expenses by Category"),
    ("proj",       "Revenue & Profit Growth Projection"),
]
_LABELS = [l for _, l in REPORTS]
_KEYS = {l: k for k, l in REPORTS}


def _delta(curr, prev):
    curr = float(curr or 0); prev = float(prev or 0)
    if prev == 0:
        return ("&#9650; new", "#059669") if curr > 0 else ("&bull; —", "#94a3b8")
    pct = (curr - prev) / prev * 100
    if pct > 0:
        return f"&#9650; {abs(pct):.0f}%", "#059669"
    if pct < 0:
        return f"&#9660; {abs(pct):.0f}%", "#dc2626"
    return "&bull; 0%", "#94a3b8"


def _kpis(currency):
    t = date.today()
    ym = t.strftime("%Y-%m")
    pm = (t.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    rev = lambda m: float(scalar("SELECT COALESCE(SUM(total),0) FROM orders WHERE strftime('%Y-%m',created_at)=? AND status!='Cancelled'", (m,)))
    prof = lambda m: float(scalar("SELECT COALESCE(SUM(profit),0) FROM orders WHERE strftime('%Y-%m',created_at)=? AND status!='Cancelled'", (m,)))
    exp = lambda m: float(scalar("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE strftime('%Y-%m',date)=?", (m,)))
    fee = lambda m: float(scalar("SELECT COALESCE(SUM(extra_fees),0) FROM orders WHERE strftime('%Y-%m',created_at)=? AND status!='Cancelled'", (m,)))
    r, rp = rev(ym), rev(pm)
    g, gp = prof(ym), prof(pm)
    e, ep = exp(ym), exp(pm)
    fz, fzp = fee(ym), fee(pm)
    net, netp = g - e, gp - ep
    margin = (g / r * 100) if r else 0
    marginp = (gp / rp * 100) if rp else 0
    cards = [
        ("Revenue (MTD)",  f"{currency} {r:,.0f}",   _delta(r, rp)),
        ("Gross Profit",   f"{currency} {g:,.0f}",   _delta(g, gp)),
        ("Expenses",       f"{currency} {e:,.0f}",   _delta(e, ep)),
        ("Net Profit",     f"{currency} {net:,.0f}", _delta(net, netp)),
        ("Profit Margin",  f"{margin:.0f}%",         _delta(margin, marginp)),
        ("Fees Revenue",   f"{currency} {fz:,.0f}",  _delta(fz, fzp)),
    ]
    html = "<div style='display:grid;grid-template-columns:repeat(6,1fr);gap:.7rem;margin-bottom:1rem;'>"
    for label, val, (dtxt, dcol) in cards:
        html += (f"<div style='background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:.8rem .9rem;'>"
                 f"<div style='font-size:1.25rem;font-weight:800;color:#0f172a;'>{val}</div>"
                 f"<div style='font-size:.62rem;text-transform:uppercase;letter-spacing:.04em;color:#4b6a8b;margin-top:3px;'>{label}</div>"
                 f"<div style='font-size:.7rem;font-weight:700;margin-top:3px;color:{dcol};'>{dtxt}</div></div>")
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render():
    hero("Reports & Analysis", "Finance reports — sales, profit, products and expenses.")
    if not has_access("Staff"):
        st.warning("Only Staff and Admin can view reports.")
        return
    currency = get_setting("currency", "MVR")

    _kpis(currency)

    c1, c2, c3 = st.columns([2.4, 1, 1])
    label = c1.selectbox("Report", _LABELS)
    key = _KEYS[label]

    style = "bar"
    if key in charts.STYLE_REPORTS:
        style = "line" if c2.radio("Style", ["Bars", "Lines"], horizontal=True,
                                   key="rep_style") == "Lines" else "bar"
    period = "month"
    if key in charts.PERIOD_REPORTS:
        period = {"Weekly": "week", "Monthly": "month", "Yearly": "year"}[
            c3.selectbox("Period", ["Weekly", "Monthly", "Yearly"], index=1, key="rep_period")]

    charts.render_report(key, style=style, period=period, height=400)
