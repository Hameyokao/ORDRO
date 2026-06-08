import streamlit as st
from components.database import query_df, get_setting
from components.theme import hero
from pages_app.delivery import render_order_card


def render():
    hero("Completed Deliveries", "Delivered orders · unpaid orders appear first.")
    role     = st.session_state.get("view_role") or st.session_state.get("role")
    username = st.session_state.get("username")
    currency = get_setting("currency", "MVR")

    base   = ("SELECT * FROM orders WHERE order_type='Delivery' "
              "AND status IN ('Delivered','Completed')")
    params = ()
    # Delivery users see ALL completed delivery orders (every date, every driver) —
    # nothing is hidden by age or assignment.

    orders = query_df(
        base + " ORDER BY CASE WHEN COALESCE(payment_status,'Unpaid')!='Paid' "
               "THEN 0 ELSE 1 END, created_at DESC",
        params,
    )

    if orders.empty:
        st.success("✓ No completed deliveries to show.")
        return

    pending = int((orders["payment_status"].fillna("Unpaid") != "Paid").sum())
    if pending:
        st.warning(f"⚠ {pending} order(s) still awaiting payment — shown first.")
    st.caption(f"{len(orders)} completed order(s) · {pending} unpaid")

    for _, order in orders.iterrows():
        render_order_card(order, mode="completed")
