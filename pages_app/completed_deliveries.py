import streamlit as st
from components.database import query_df, get_setting
from components.theme import hero
from pages_app.delivery import render_order_card, order_summary_row, section_header


def render():
    hero("Completed Orders", "Delivered & completed orders — awaiting payment shown first.")
    currency = get_setting("currency", "MVR")
    role     = st.session_state.get("view_role") or st.session_state.get("role")
    username = st.session_state.get("username")

    if role == "Delivery":
        # A delivery user only sees the DELIVERY orders THEY delivered.
        # Non-delivery orders never appear here (keeps business data private).
        orders = query_df(
            "SELECT * FROM orders WHERE status IN ('Delivered','Completed') "
            "AND order_type='Delivery' AND assigned_to=? ORDER BY created_at DESC",
            (username,))
    else:
        # Staff / Admin / Administrator see every completed order.
        orders = query_df(
            "SELECT * FROM orders WHERE status IN ('Delivered','Completed') "
            "ORDER BY created_at DESC")

    if orders.empty:
        st.success("✓ No completed orders to show.")
        return

    counts = query_df("SELECT order_id, SUM(qty) AS n FROM order_items GROUP BY order_id")
    cmap = ({int(r["order_id"]): int(r["n"] or 0) for _, r in counts.iterrows()}
            if not counts.empty else {})

    unpaid = orders[orders["payment_status"].fillna("Unpaid") != "Paid"]
    paid   = orders[orders["payment_status"].fillna("Unpaid") == "Paid"]
    if not unpaid.empty:
        st.warning(f"⚠ {len(unpaid)} completed order(s) still awaiting payment — shown first.")
    st.caption(f"{len(orders)} completed order(s)")

    for label, color, grp in [("Awaiting payment", "#dc2626", unpaid),
                              ("Paid", "#16a34a", paid)]:
        if grp.empty:
            continue
        st.markdown(section_header(color, label, len(grp)), unsafe_allow_html=True)
        for _, o in grp.iterrows():
            order_summary_row(o, currency, cmap.get(int(o["id"]), 0), color)
            with st.expander("Manage order"):
                render_order_card(o, mode="completed")
