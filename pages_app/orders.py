from datetime import datetime, timedelta
import streamlit as st
from components.database import query_df, execute, get_setting, fmt_date
from components.theme import hero
from components.auth import has_access
from pages_app.delivery import render_order_card, restore_inventory
from components.activity import log


def _date_filter_sql(mode, month_value=None, year_value=None, week_value=None):
    today = datetime.now().date()
    if mode == "Last 7 days":
        return "date(created_at) >= ?", ((today - timedelta(days=6)).isoformat(),)
    if mode == "This month":
        return "strftime('%Y-%m', created_at)=?", (today.strftime("%Y-%m"),)
    if mode == "Previous month":
        first = today.replace(day=1)
        prev  = first - timedelta(days=1)
        return "strftime('%Y-%m', created_at)=?", (prev.strftime("%Y-%m"),)
    if mode == "Select month" and month_value:
        return "strftime('%Y-%m', created_at)=?", (month_value,)
    if mode == "Select week" and week_value:
        return "strftime('%Y-%W', created_at)=?", (week_value,)
    if mode == "Select year" and year_value:
        return "strftime('%Y', created_at)=?", (str(year_value),)
    return "1=1", ()


def render():
    hero("Orders", "All orders — manage status, payment and fulfilment.")
    currency = get_setting("currency", "MVR")

    f1, f2, f3 = st.columns([1.1, 1.1, 1.1])
    with f1:
        view = st.selectbox("Group", [
            "Active Orders", "Pending Payment", "Completed Orders",
            "Cancelled Orders", "All Orders",
        ])
    with f2:
        date_mode = st.selectbox("Period", [
            "Last 7 days", "This month", "Previous month",
            "Select month", "Select week", "Select year", "All time",
        ])
    month_value = week_value = year_value = None
    with f3:
        if date_mode == "Select month":
            months = query_df("SELECT DISTINCT strftime('%Y-%m', created_at) AS m "
                              "FROM orders ORDER BY m DESC")
            opts = months["m"].dropna().tolist() or [datetime.now().strftime("%Y-%m")]
            month_value = st.selectbox("Month", opts)
        elif date_mode == "Select week":
            weeks = query_df("SELECT DISTINCT strftime('%Y-%W', created_at) AS w "
                             "FROM orders ORDER BY w DESC")
            opts = weeks["w"].dropna().tolist() or [datetime.now().strftime("%Y-%W")]
            week_value = st.selectbox("Year-week", opts)
        elif date_mode == "Select year":
            years = query_df("SELECT DISTINCT strftime('%Y', created_at) AS y "
                             "FROM orders ORDER BY y DESC")
            opts = years["y"].dropna().tolist() or [str(datetime.now().year)]
            year_value = st.selectbox("Year", opts)
        else:
            st.caption("Select a period above.")

    date_sql, date_params = _date_filter_sql(date_mode, month_value, year_value, week_value)
    where  = [date_sql]
    params = list(date_params)

    if view == "Active Orders":
        where.append("status NOT IN ('Delivered','Completed','Cancelled')")
    elif view == "Pending Payment":
        where.append("status NOT IN ('Cancelled')")
        where.append("COALESCE(payment_status,'Unpaid') != 'Paid'")
    elif view == "Completed Orders":
        where.append("status IN ('Delivered','Completed')")
    elif view == "Cancelled Orders":
        where.append("status = 'Cancelled'")

    sql = (
        f"SELECT * FROM orders WHERE {' AND '.join(where)} ORDER BY "
        "CASE WHEN status IN ('Delivered','Completed') AND "
        "COALESCE(payment_status,'Unpaid')!='Paid' THEN 0 ELSE 1 END, created_at DESC"
    )
    orders = query_df(sql, tuple(params))

    if orders.empty:
        st.info("No orders found for this filter.")
        return

    k1, k2, k3 = st.columns(3)
    k1.metric("Orders", len(orders))
    k2.metric("Total Value", f"{currency} {orders['total'].sum():,.2f}")
    k3.metric("Pending Payment",
              int(((orders["status"] != "Cancelled") &
                   (orders["payment_status"].fillna("Unpaid") != "Paid")).sum()))

    st.markdown("---")
    for _, order in orders.iterrows():
        render_order_card(order, mode="orders")
