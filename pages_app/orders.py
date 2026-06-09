from datetime import datetime, timedelta
import streamlit as st
from components.database import query_df, execute, get_setting, fmt_date
from components.theme import hero
from components.auth import has_access
from pages_app.delivery import render_order_card, restore_inventory
from components.activity import log


def _e(v):
    s = "" if v is None else str(v)
    if s.strip().lower() == "nan":
        s = ""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _date_filter_sql(mode, month_value=None, year_value=None, week_value=None):
    today = datetime.now().date()
    if mode == "Last 7 days":
        return "date(created_at) >= ?", ((today - timedelta(days=6)).isoformat(),)
    if mode == "This month":
        return "strftime('%Y-%m', created_at)=?", (today.strftime("%Y-%m"),)
    if mode == "Previous month":
        first = today.replace(day=1)
        prev = first - timedelta(days=1)
        return "strftime('%Y-%m', created_at)=?", (prev.strftime("%Y-%m"),)
    if mode == "Select month" and month_value:
        return "strftime('%Y-%m', created_at)=?", (month_value,)
    if mode == "Select week" and week_value:
        return "strftime('%Y-%W', created_at)=?", (week_value,)
    if mode == "Select year" and year_value:
        return "strftime('%Y', created_at)=?", (str(year_value),)
    return "1=1", ()


_PAY_PILL = {
    "Paid":           ("#f0fdf4", "#15803d"),
    "Unpaid":         ("#fef2f2", "#b91c1c"),
    "Partially Paid": ("#fffbeb", "#b45309"),
}
_STATUS_PILL = {
    "Pending":          ("#eff6ff", "#1d4ed8"),
    "Preparing":        ("#f5f3ff", "#6d28d9"),
    "Ready":            ("#eff6ff", "#1d4ed8"),
    "Out for Delivery": ("#fdf2f8", "#9d174d"),
    "Delivered":        ("#f0fdf4", "#15803d"),
    "Completed":        ("#f0fdf4", "#15803d"),
    "Cancelled":        ("#f1f5f9", "#475569"),
}


def _summary_row(o, currency, n_items, strip):
    pay = str(o.get("payment_status") or "Unpaid")
    pbg, pfg = _PAY_PILL.get(pay, ("#f1f5f9", "#475569"))
    status = o.get("status") or "Pending"
    sbg, sfg = _STATUS_PILL.get(status, ("#f1f5f9", "#475569"))
    name = _e(o.get("customer_name")) or "&mdash;"
    phone = _e(o.get("customer_phone"))
    tel = "".join(c for c in str(o.get("customer_phone") or "") if c.isdigit() or c == "+")
    phone_html = (
        f'<a href="tel:{tel}" style="display:inline-flex;align-items:center;gap:5px;'
        f'font-size:16px;font-weight:700;color:#2563eb;text-decoration:none;margin-top:3px;">'
        f'&#128222; {phone}</a>'
    ) if phone else ""
    foot = [fmt_date(o.get("created_at"), show_time=False), f"{n_items} item(s)",
            _e(o.get("order_type")) or "&mdash;"]
    seller = _e(o.get("seller"))
    if seller:
        foot.append(f"Seller: {seller}")
    foot_html = " &middot; ".join(b for b in foot if b)

    st.markdown(f"""
<div style="display:flex;background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden;margin-top:2px;">
  <div style="width:5px;background:{strip};"></div>
  <div style="flex:1;padding:12px 16px;">
    <div style="display:flex;justify-content:space-between;align-items:baseline;">
      <span style="font-size:14px;font-weight:700;color:#475569;">{_e(o.get('order_no'))}</span>
      <span style="font-size:16px;font-weight:800;color:#0f172a;">{currency} {float(o.get('total') or 0):,.2f}</span>
    </div>
    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;flex-wrap:wrap;margin-top:6px;">
      <div><div style="font-size:18px;font-weight:800;color:#0f172a;line-height:1.2;">{name}</div>{phone_html}</div>
      <div style="display:flex;gap:6px;padding-top:2px;">
        <span style="font-size:11px;font-weight:700;padding:3px 9px;border-radius:7px;background:{pbg};color:{pfg};">{_e(pay)}</span>
        <span style="font-size:11px;font-weight:700;padding:3px 9px;border-radius:7px;background:{sbg};color:{sfg};">{_e(status)}</span>
      </div>
    </div>
    <div style="font-size:12px;color:#94a3b8;margin-top:10px;padding-top:8px;border-top:1px solid #f1f5f9;">{foot_html}</div>
  </div>
</div>
""", unsafe_allow_html=True)


def render():
    hero("Pending Orders", "All orders — grouped by status, easy to scan.")
    currency = get_setting("currency", "MVR")
    role = st.session_state.get("view_role") or st.session_state.get("role")
    is_delivery = role == "Delivery" and st.session_state.get("role") != "Admin"

    period_opts = ["Last 7 days", "This month", "Previous month",
                   "Select month", "Select week", "Select year", "All time"]
    f1, f2 = st.columns([1, 1])
    with f1:
        date_mode = st.selectbox(
            "Period", period_opts,
            index=period_opts.index("All time") if is_delivery else 0)
    month_value = week_value = year_value = None
    with f2:
        if date_mode == "Select month":
            months = query_df("SELECT DISTINCT strftime('%Y-%m', created_at) AS m FROM orders ORDER BY m DESC")
            opts = months["m"].dropna().tolist() or [datetime.now().strftime("%Y-%m")]
            month_value = st.selectbox("Month", opts)
        elif date_mode == "Select week":
            weeks = query_df("SELECT DISTINCT strftime('%Y-%W', created_at) AS w FROM orders ORDER BY w DESC")
            opts = weeks["w"].dropna().tolist() or [datetime.now().strftime("%Y-%W")]
            week_value = st.selectbox("Year-week", opts)
        elif date_mode == "Select year":
            years = query_df("SELECT DISTINCT strftime('%Y', created_at) AS y FROM orders ORDER BY y DESC")
            opts = years["y"].dropna().tolist() or [str(datetime.now().year)]
            year_value = st.selectbox("Year", opts)
        else:
            st.caption("Filter orders by time period.")

    date_sql, date_params = _date_filter_sql(date_mode, month_value, year_value, week_value)
    orders = query_df(
        f"SELECT * FROM orders WHERE {date_sql} ORDER BY created_at DESC",
        tuple(date_params))

    if orders.empty:
        st.info("No orders found for this period.")
        return

    k1, k2, k3 = st.columns(3)
    k1.metric("Orders", len(orders))
    k2.metric("Total Value", f"{currency} {orders['total'].sum():,.2f}")
    k3.metric("Pending Payment",
              int(((orders["status"] != "Cancelled") &
                   (orders["payment_status"].fillna("Unpaid") != "Paid")).sum()))

    counts = query_df("SELECT order_id, SUM(qty) AS n FROM order_items GROUP BY order_id")
    cmap = ({int(r["order_id"]): int(r["n"] or 0) for _, r in counts.iterrows()}
            if not counts.empty else {})

    buckets = {"Needs payment": [], "In progress": [], "Completed": [], "Cancelled": []}
    for _, o in orders.iterrows():
        status = o.get("status") or "Pending"
        paid = str(o.get("payment_status") or "Unpaid") == "Paid"
        if status == "Cancelled":
            buckets["Cancelled"].append(o)
        elif not paid:
            buckets["Needs payment"].append(o)
        elif status in ("Delivered", "Completed"):
            buckets["Completed"].append(o)
        else:
            buckets["In progress"].append(o)

    buckets["Needs payment"].sort(
        key=lambda o: 0 if (o.get("status") in ("Delivered", "Completed")) else 1)

    colors = {"Needs payment": "#dc2626", "In progress": "#3b82f6",
              "Completed": "#16a34a", "Cancelled": "#94a3b8"}

    for key in ["Needs payment", "In progress", "Completed", "Cancelled"]:
        rows = buckets[key]
        if not rows:
            continue
        color = colors[key]
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:8px;margin:20px 0 6px;'>"
            f"<span style='width:10px;height:10px;border-radius:50%;background:{color};'></span>"
            f"<span style='font-size:15px;font-weight:700;color:#0f172a;'>{key}</span>"
            f"<span style='font-size:12px;color:#64748b;'>{len(rows)} order(s)</span></div>",
            unsafe_allow_html=True)
        for o in rows:
            _summary_row(o, currency, cmap.get(int(o["id"]), 0), color)
            with st.expander("Manage order"):
                render_order_card(o, mode="orders")
