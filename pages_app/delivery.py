from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
from components.database import query_df, execute, get_setting, fmt_date
from components.theme import hero
from components.auth import has_access
from components.ui import fixed_image, save_uploaded_file
from components.payments import (
    clean, add_payment_verification, render_verification_previews,
    payment_slip_html, delivery_sticker_html,
)
from components.activity import log


@st.dialog("Payment slip", width="large")
def _slip_dialog(order, items, currency):
    components.html(payment_slip_html(order, items, currency), height=900, scrolling=True)


@st.dialog("Delivery sticker", width="large")
def _sticker_dialog(order, items, currency):
    components.html(delivery_sticker_html(order, items, currency), height=640, scrolling=True)

STATUSES = ["Pending", "Preparing", "Ready", "Out for Delivery", "Delivered", "Completed", "Cancelled"]
PAYMENTS = ["Unpaid", "Paid", "Partially Paid"]
STATUS_COLOR = {
    "Pending": "#f97316", "Preparing": "#8b5cf6", "Ready": "#3b82f6",
    "Out for Delivery": "#ec4899", "Delivered": "#16a34a",
    "Completed": "#16a34a", "Cancelled": "#ef4444",
}


def restore_inventory(order_id: int):
    rows = query_df("SELECT product_id, qty FROM order_items WHERE order_id=?", (order_id,))
    for _, it in rows.iterrows():
        execute("UPDATE products SET stock = stock + ? WHERE id=?",
                (int(it["qty"]), int(it["product_id"])))


def render_order_card(order, mode="delivery"):
    """
    mode: 'delivery' | 'orders' | 'completed'
    """
    currency       = get_setting("currency", "MVR")
    order_id       = int(order["id"])
    status         = order.get("status") or "Pending"
    payment_status = order.get("payment_status") or "Unpaid"
    urgent         = "urgent" in str(order.get("notes") or "").lower()
    unpaid_alert   = (payment_status != "Paid") and status in ("Delivered", "Completed")

    border = "#ef4444" if unpaid_alert else ("#f97316" if urgent else "#e2e8f0")
    s_col  = STATUS_COLOR.get(status, "#64748b")
    p_col  = "#16a34a" if payment_status == "Paid" else "#dc2626"
    p_bg   = "#f0fdf4" if payment_status == "Paid" else "#fef2f2"

    items = query_df("SELECT * FROM order_items WHERE order_id=?", (order_id,))

    delivered_str = fmt_date(order.get("delivered_at"))
    delivered_html = (
        f"<span style='color:#15803d;font-weight:700;'>🕐 Delivered: {delivered_str}</span> &nbsp;·&nbsp; "
        if delivered_str != "—" else ""
    )

    # Pre-compute badge HTML to avoid complex expressions inside the f-string
    badge_urgent = (
        "<span style='background:#fff7ed;color:#c2410c;border:1px solid #fed7aa;"
        "border-radius:6px;padding:2px 10px;font-size:11px;font-weight:700;'>⚡ URGENT</span>"
        if urgent else ""
    )
    badge_payment = (
        "<span style='background:#fef2f2;color:#dc2626;border:1px solid #fecaca;"
        "border-radius:6px;padding:2px 10px;font-size:11px;font-weight:700;'>💳 PAYMENT PENDING</span>"
        if unpaid_alert else ""
    )
    notes_html = (
        "<div><div style='font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;"
        "letter-spacing:.1em;margin-bottom:4px;'>Notes</div>"
        f"<div style='font-size:13px;color:#475569;'>📝 {str(order.get('notes',''))}</div></div>"
        if order.get('notes') else "<div></div>"
    )

    # ── Open card ─────────────────────────────────────────────────────────
    st.markdown(
        f"""<div style="border:2px solid {border};border-radius:20px;background:#fff;box-shadow:0 2px 18px rgba(0,0,0,.07);margin-bottom:8px;padding:20px 24px 16px;">
<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;">{badge_urgent}{badge_payment}</div>
<div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:14px;">
<div>
<div style="font-size:22px;font-weight:800;color:#0f172a;letter-spacing:-.02em;">📦 {order['order_no']}</div>
<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:5px;">
<span style="background:{s_col};color:#fff;border-radius:7px;padding:2px 12px;font-size:12px;font-weight:700;">{status}</span>
<span style="background:#f1f5f9;color:#475569;border-radius:7px;padding:2px 10px;font-size:12px;">{order.get('order_type') or 'Delivery'}</span>
<span style="background:{p_bg};color:{p_col};border-radius:7px;padding:2px 10px;font-size:12px;font-weight:700;">{payment_status}</span>
</div>
<div style="font-size:12px;color:#64748b;margin-top:5px;">{delivered_html}📅 {fmt_date(order.get('created_at'))}</div>
</div>
<div style="text-align:right;">
<div style="font-size:24px;font-weight:800;color:#0f172a;">{currency} {float(order.get('total',0)):,.2f}</div>
<div style="font-size:12px;color:#64748b;margin-top:2px;">{clean(order.get('payment_method'))} &nbsp;·&nbsp; Seller: {clean(order.get('seller'))}</div>
<div style="font-size:12px;color:#64748b;">👤 {clean(order.get('assigned_to'))}</div>
</div>
</div>
<div style="border-top:1px solid #f1f5f9;padding-top:12px;display:grid;grid-template-columns:1fr 1fr;gap:8px;">
<div>
<div style="font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px;">Customer</div>
<div style="font-size:15px;font-weight:700;color:#0f172a;">{clean(order.get('customer_name'))}</div>
<div style="font-size:13px;color:#475569;">📱 {clean(order.get('customer_phone'))}</div>
<div style="font-size:13px;color:#475569;">📍 {clean(order.get('customer_city'))}</div>
<div style="font-size:13px;color:#475569;">🏠 {clean(order.get('customer_address'))}</div>
</div>
{notes_html}
</div>
</div>""",
        unsafe_allow_html=True,
    )

    # ── Controls + Product images (Streamlit widgets) ──────────────────────
    ctrl_col, img_col = st.columns([1, 2])

    with ctrl_col:
        if has_access("Delivery") and mode in ("delivery", "orders"):
            new_status = st.selectbox(
                "Update Status", STATUSES,
                index=STATUSES.index(status) if status in STATUSES else 0,
                key=f"st_{order_id}_{mode}")
            new_payment = st.selectbox(
                "Update Payment", PAYMENTS,
                index=PAYMENTS.index(payment_status) if payment_status in PAYMENTS else 0,
                key=f"pay_{order_id}_{mode}")
            verify_file = None
            if new_payment == "Paid":
                verify_file = st.file_uploader(
                    "Payment proof", type=["png","jpg","jpeg","webp"],
                    key=f"verify_{order_id}_{mode}")
            if st.button("💾 Save", key=f"save_{order_id}_{mode}",
                         type="primary", use_container_width=True):
                saved_file   = order.get("payment_verification_image") or ""
                delivered_at = order.get("delivered_at") or ""
                if verify_file:
                    saved_file = save_uploaded_file(verify_file, prefix=f"pay_{order['order_no']}")
                    add_payment_verification(order_id, saved_file,
                                             st.session_state.get("username","user"))
                update_pay = new_payment
                if new_status == "Cancelled" and status != "Cancelled":
                    restore_inventory(order_id)
                    update_pay = ""
                if new_status in ("Delivered","Completed") and not delivered_at:
                    delivered_at = datetime.now().isoformat(timespec="seconds")
                execute(
                    "UPDATE orders SET status=?,payment_status=?,payment_verification_image=?,"
                    "payment_slip_no=?,delivered_at=? WHERE id=?",
                    (new_status, update_pay, saved_file,
                     order.get("payment_slip_no") or f"PS-{order['order_no']}",
                     delivered_at, order_id),
                )
                log("Updated order", entity="order", entity_id=order_id,
                    detail=f"{order['order_no']} → {new_status} / {update_pay or 'n/a'}")
                st.success("Saved.")
                st.rerun()

            if has_access("Admin") and mode == "orders":
                with st.expander("⚠ Delete order (Admin)"):
                    st.caption("Permanently removes this order. Stock from non-cancelled "
                               "orders is returned to inventory.")
                    confirm_del = st.checkbox(
                        "Confirm permanent delete", key=f"odelchk_{order_id}_{mode}")
                    if st.button(
                        "Delete order", key=f"odel_{order_id}_{mode}",
                        disabled=not confirm_del, icon=":material/delete:",
                        use_container_width=True,
                    ):
                        if status != "Cancelled":
                            restore_inventory(order_id)
                        execute("DELETE FROM order_items WHERE order_id=?", (order_id,))
                        execute("DELETE FROM payment_verifications WHERE order_id=?", (order_id,))
                        execute("DELETE FROM orders WHERE id=?", (order_id,))
                        log("Deleted order", entity="order", entity_id=order_id,
                            detail=order.get("order_no") or "")
                        st.success("Order deleted.")
                        st.rerun()

            if st.session_state.get("role") == "Super Admin":
                with st.expander("✎ Edit order number (Administrator)"):
                    new_no = st.text_input(
                        "Order number", value=order.get("order_no") or "",
                        key=f"onum_{order_id}_{mode}")
                    if st.button("Save number", key=f"onsave_{order_id}_{mode}",
                                 icon=":material/save:"):
                        nn = (new_no or "").strip()
                        if not nn:
                            st.error("Order number cannot be empty.")
                        else:
                            dup = query_df(
                                "SELECT id FROM orders WHERE order_no=? AND id!=?",
                                (nn, order_id))
                            if not dup.empty:
                                st.error("That order number is already used by another order.")
                            else:
                                execute("UPDATE orders SET order_no=? WHERE id=?", (nn, order_id))
                                log("Edited order number", entity="order",
                                    entity_id=order_id, detail=nn)
                                st.success("Order number updated.")
                                st.rerun()

        elif has_access("Delivery") and mode == "completed":
            new_pay = st.selectbox(
                "Update Payment", PAYMENTS, key=f"cpay_{order_id}_{mode}",
                index=PAYMENTS.index(payment_status) if payment_status in PAYMENTS else 0)
            proof = st.file_uploader("Payment proof", type=["png","jpg","jpeg","webp"],
                                      key=f"cproof_{order_id}_{mode}")
            if st.button("💾 Save Payment", key=f"csave_{order_id}_{mode}",
                         type="primary", use_container_width=True):
                saved_file = order.get("payment_verification_image") or ""
                if proof:
                    saved_file = save_uploaded_file(proof, prefix=f"pay_{order['order_no']}")
                    add_payment_verification(order_id, saved_file,
                                             st.session_state.get("username","user"))
                execute("UPDATE orders SET payment_status=?,payment_verification_image=? WHERE id=?",
                        (new_pay, saved_file, order_id))
                log("Updated payment", entity="order", entity_id=order_id,
                    detail=f"{order['order_no']} → {new_pay}")
                st.success("Saved.")
                st.rerun()

    # ── Product image boxes ────────────────────────────────────────────────
    with img_col:
        if not items.empty:
            st.markdown(
                "<div style='font-size:10px;font-weight:700;color:#94a3b8;"
                "text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px;'>"
                "Items</div>",
                unsafe_allow_html=True)
            n_cols = min(len(items), 5)
            icols  = st.columns(n_cols)
            for idx, (_, it) in enumerate(items.head(5).iterrows()):
                with icols[idx]:
                    with st.container(border=True):
                        fixed_image(it.get("product_image") or "", height=84)
                        st.markdown(
                            f"<div style='font-size:12px;font-weight:700;color:#0f172a;"
                            f"line-height:1.3;'>{str(it['product_name'])[:20]}</div>"
                            f"<div style='font-size:11px;color:#64748b;'>"
                            f"×{int(it['qty'])} · {currency} {float(it['line_total']):,.2f}</div>",
                            unsafe_allow_html=True)

    # ── Payment verification & downloads ──────────────────────────────────
    render_verification_previews(order_id)

    if not items.empty:
        da, db = st.columns(2)
        with da:
            if st.button("🧾 Payment Slip", key=f"slip_{order_id}_{mode}",
                         use_container_width=True):
                _slip_dialog(order, items, currency)
        with db:
            if st.button("📦 Delivery Sticker", key=f"stk_{order_id}_{mode}",
                         use_container_width=True):
                _sticker_dialog(order, items, currency)

    st.markdown("<div style='margin-bottom:24px;'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
def render():
    hero("Delivery Board", "Active delivery orders — urgent orders flagged on top.")
    role     = st.session_state.get("view_role") or st.session_state.get("role")
    username = st.session_state.get("username")

    base   = ("SELECT * FROM orders WHERE order_type='Delivery' "
              "AND status NOT IN ('Delivered','Completed','Cancelled')")
    params = ()
    # Delivery users see ALL active delivery orders (every driver), not only
    # the ones assigned to them.

    orders = query_df(
        base + " ORDER BY CASE WHEN LOWER(COALESCE(notes,'')) LIKE '%urgent%' THEN 0 "
               "ELSE 1 END, created_at DESC",
        params,
    )

    if orders.empty:
        st.success("✓ No active delivery orders right now.")
        return

    st.caption(f"{len(orders)} active order(s)")
    for _, order in orders.iterrows():
        render_order_card(order, mode="delivery")
