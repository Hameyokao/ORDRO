from datetime import datetime
import streamlit as st
from components.database import query_df, execute, get_setting, fmt_date
from components.theme import hero
from components.auth import has_access
from components.activity import log


def _customer_card(r, currency, key_suffix=""):
    """Render a full customer card with stats, history, edit."""
    with st.container(border=True):
        c_top, c_phone = st.columns([2, 1])
        with c_top:
            st.markdown(f"### :material/person: {r['name']}")
        with c_phone:
            phone_val = r.get('phone') or '—'
            st.markdown(
                f"<div style='text-align:right;padding-top:8px;'>"
                f"<a href='tel:{phone_val}' style='text-decoration:none;color:#2563eb;font-weight:600;font-size:14px;'>"
                f"📞 {phone_val}</a></div>",
                unsafe_allow_html=True,
            )

        col_a, col_b = st.columns(2)
        with col_a:
            st.write(f"**City:** {r.get('city') or '—'}")
        with col_b:
            st.write(f"**Email:** {r.get('email') or '—'}")
        if r.get('address'):
            st.caption(f"📍 {r['address']}")
        if r.get('notes'):
            st.caption(f"💬 {r['notes']}")

        stats = query_df(
            """SELECT COUNT(*) AS orders,
                      COALESCE(SUM(CASE WHEN status!='Cancelled' THEN total ELSE 0 END),0) AS spent,
                      COALESCE(SUM(CASE WHEN status!='Cancelled'
                                        AND COALESCE(payment_status,'Unpaid')!='Paid'
                                        THEN total ELSE 0 END),0) AS outstanding,
                      MAX(created_at) AS last_order
               FROM orders WHERE customer_id=?""",
            (int(r['id']),),
        )
        n_orders    = int(stats['orders'][0])
        spent       = float(stats['spent'][0])
        outstanding = float(stats['outstanding'][0])
        last_order  = stats['last_order'][0]

        pills = (
            f"<span class='pill pill-blue'>{n_orders} orders</span> "
            f"<span class='pill pill-green'>Spent {currency} {spent:,.0f}</span>"
        )
        if outstanding > 0:
            pills += f" <span class='pill pill-red'>Owes {currency} {outstanding:,.0f}</span>"
        if last_order:
            pills += f" <span class='pill pill-violet'>Last: {fmt_date(last_order, show_time=False)}</span>"
        st.markdown(pills, unsafe_allow_html=True)

        with st.expander("📋 Purchase history"):
            hist = query_df(
                """SELECT order_no, created_at, status, payment_status, total
                   FROM orders WHERE customer_id=? ORDER BY created_at DESC LIMIT 25""",
                (int(r['id']),),
            )
            if hist.empty:
                st.caption("No orders yet.")
            else:
                view = hist.copy()
                view['created_at'] = view['created_at'].apply(lambda v: fmt_date(str(v)[:19]))
                view['total'] = view['total'].apply(lambda v: f"{currency} {float(v):,.2f}")
                view.columns = ["Order", "Date", "Status", "Payment", "Total"]
                st.dataframe(view, use_container_width=True, hide_index=True)

        if has_access("Staff"):
            with st.expander("✏ Edit customer"):
                ename    = st.text_input("Name",    r['name'],            key=f"cn_{r['id']}{key_suffix}")
                ephone   = st.text_input("Phone",   r.get('phone') or '', key=f"cp_{r['id']}{key_suffix}")
                eemail   = st.text_input("Email",   r.get('email') or '', key=f"ce_{r['id']}{key_suffix}")
                ecity    = st.text_input("City",    r.get('city') or '',  key=f"cc_{r['id']}{key_suffix}")
                eaddress = st.text_area("Address",  r.get('address') or '',key=f"ca_{r['id']}{key_suffix}")
                enotes   = st.text_area("Notes",    r.get('notes') or '',  key=f"ct_{r['id']}{key_suffix}")
                if st.button("Save", key=f"cs_{r['id']}{key_suffix}", type="primary", icon=":material/save:"):
                    execute(
                        "UPDATE customers SET name=?, phone=?, email=?, city=?, address=?, notes=? WHERE id=?",
                        (ename, ephone, eemail, ecity, eaddress, enotes, int(r['id'])),
                    )
                    log("Updated customer", entity="customer", entity_id=int(r['id']), detail=ename)
                    st.success("Customer updated.")
                    st.rerun()

                if has_access("Admin"):
                    st.markdown("---")
                    st.caption("⚠ Danger zone — removes the customer. Past orders are kept "
                               "(their saved name/phone stays on the order).")
                    confirm_del = st.checkbox(
                        "Confirm permanent delete", key=f"cdelchk_{r['id']}{key_suffix}")
                    if st.button(
                        "Delete customer", key=f"cdel_{r['id']}{key_suffix}",
                        disabled=not confirm_del, icon=":material/delete:",
                    ):
                        execute("UPDATE orders SET customer_id=NULL WHERE customer_id=?", (int(r['id']),))
                        execute("DELETE FROM customers WHERE id=?", (int(r['id']),))
                        log("Deleted customer", entity="customer", entity_id=int(r['id']), detail=r['name'])
                        st.success("Customer deleted.")
                        st.rerun()


def render():
    hero("Customers", "Latest purchasers · full customer directory · purchase history")
    currency = get_setting("currency", "MVR")

    if has_access("Staff"):
        with st.expander("➕ Add customer", expanded=False):
            with st.form("customer_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                name  = c1.text_input("Full name")
                phone = c2.text_input("Phone number")
                c3, c4 = st.columns(2)
                email = c3.text_input("Email")
                city  = c4.text_input("City / Island")
                address = st.text_area("Address")
                notes   = st.text_area("Notes")
                if st.form_submit_button("Save customer", type="primary", icon=":material/add:"):
                    if name:
                        cid = execute(
                            "INSERT INTO customers (name,phone,email,city,address,notes,created_at) VALUES (?,?,?,?,?,?,?)",
                            (name, phone, email, city, address, notes, datetime.now().isoformat()),
                        )
                        log("Created customer", entity="customer", entity_id=cid, detail=name)
                        st.success("Customer saved.")
                        st.rerun()
                    else:
                        st.error("Name is required.")

    # ── Load customers with last-order info ───────────────────────────────
    customers = query_df("""
        SELECT c.*,
               MAX(o.created_at) AS last_order_at
        FROM customers c
        LEFT JOIN orders o ON o.customer_id = c.id AND o.status != 'Cancelled'
        GROUP BY c.id
        ORDER BY last_order_at DESC NULLS LAST, c.name ASC
    """)

    if customers.empty:
        st.info("No customers yet.")
        return

    # Search / filter bar
    search = st.text_input("🔍 Search customers", placeholder="Name, phone, city…",
                           label_visibility="collapsed")
    if search:
        s = search.lower()
        customers = customers[customers.apply(
            lambda r: s in str(r.get('name') or '').lower()
                   or s in str(r.get('phone') or '').lower()
                   or s in str(r.get('city') or '').lower(), axis=1)]

    if customers.empty:
        st.warning("No customers match your search.")
        return

    # Split: recently active (last 30 days) vs rest
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    recent = customers[customers['last_order_at'].notna() & (customers['last_order_at'] >= cutoff)]
    others = customers[~customers.index.isin(recent.index)]

    # ── SECTION 1: Latest Purchase Customers ─────────────────────────────
    if not recent.empty:
        st.markdown(
            "<div style='background:linear-gradient(135deg,#eff6ff,#f0fdf4);"
            "border-left:5px solid #2563eb;border-radius:10px;"
            "padding:10px 18px;margin-bottom:14px;'>"
            f"<b style='color:#1d4ed8;font-size:15px;'>🕐 Recent Customers</b>"
            f" <span style='color:#64748b;font-size:13px;'>— Purchased in the last 30 days "
            f"({len(recent)} customer{'s' if len(recent)!=1 else ''})</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        cols = st.columns(3)
        for i, (_, r) in enumerate(recent.iterrows()):
            with cols[i % 3]:
                _customer_card(r, currency, key_suffix="_r")

    # ── SECTION 2: All Customers ──────────────────────────────────────────
    st.markdown("---")
    label = "All Customers" if recent.empty else "Other Customers"
    st.markdown(
        f"<div style='background:#f8faff;border-left:5px solid #64748b;border-radius:10px;"
        f"padding:10px 18px;margin-bottom:14px;'>"
        f"<b style='color:#334155;font-size:15px;'>👥 {label}</b>"
        f" <span style='color:#94a3b8;font-size:13px;'>({len(others)} customer{'s' if len(others)!=1 else ''})</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    if others.empty:
        st.info("All customers have purchased in the last 30 days.")
    else:
        cols2 = st.columns(3)
        for i, (_, r) in enumerate(others.iterrows()):
            with cols2[i % 3]:
                _customer_card(r, currency, key_suffix="_o")
