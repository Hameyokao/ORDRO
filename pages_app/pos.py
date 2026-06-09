import json
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from components.database import query_df, execute, next_order_no, get_setting
from components.theme import hero, COLORS
from components.ui import fixed_image
from components.activity import log


def _ensure_cart():
    if 'cart' not in st.session_state:
        st.session_state.cart = []


def _add_to_cart(row, qty):
    qty = int(qty)
    available = int(row['stock'])
    for item in st.session_state.cart:
        if int(item['id']) == int(row['id']):
            new_qty = item['qty'] + qty
            if new_qty > available:
                st.error(f"Only {available} in stock (already have {item['qty']} in cart).")
                return
            item['qty']      = new_qty
            item['subtotal'] = float(item['price']) * new_qty
            st.toast(f"Cart updated: {item['name']} × {new_qty}")
            return
    if qty > available:
        st.error(f"Only {available} in stock.")
        return
    st.session_state.cart.append({
        "id":       int(row['id']),
        "name":     row['name'],
        "price":    float(row['price']),
        "cost":     float(row['cost']),
        "qty":      qty,
        "image":    row.get('image_path') or '',
        "subtotal": float(row['price']) * qty,
    })
    st.toast(f"Added: {row['name']} × {qty}")


# ── Shared checkout body (called from both right column and dialog) ───────────
def _checkout_body(currency, tax_percent, ks="c"):
    """Render cart + checkout form. ks = key suffix avoids widget key conflicts."""
    cart = st.session_state.cart
    if not cart:
        st.info("Cart is empty — add products first.")
        return

    # Cart items
    for i, item in enumerate(cart):
        stock_df      = query_df("SELECT stock FROM products WHERE id=?", (int(item['id']),))
        available_now = 0 if stock_df.empty else int(stock_df.iloc[0]['stock'])
        with st.container(border=True):
            c1, c2 = st.columns([1, 2.2])
            with c1:
                fixed_image(item.get('image', ''), height=80)
            with c2:
                st.markdown(f"**{item['name']}**")
                if available_now < 1:
                    st.error("Out of stock!")
                else:
                    in_cart = min(int(item['qty']), available_now)
                    st.caption(f"Qty: **{in_cart}**  ·  {currency} {float(item['subtotal']):,.2f}")
                if st.button("✕ Remove", key=f"rm_{i}_{ks}", use_container_width=True):
                    st.session_state.cart.pop(i)
                    st.rerun()

    st.markdown("---")
    if st.button("🗑 Clear Cart", key=f"clr_{ks}", use_container_width=True):
        st.session_state.cart = []
        st.session_state.pos_fees = []
        st.rerun()

    cart_df  = pd.DataFrame(st.session_state.cart)
    subtotal = float(cart_df['subtotal'].sum())

    # ── Additional fees (added ABOVE the discount) ──────────────────
    if 'pos_fees' not in st.session_state:
        st.session_state.pos_fees = []
    st.markdown("##### 💵 Additional Fees")
    fc1, fc2, fc3 = st.columns([2, 1.1, 0.9])
    fee_type = fc1.selectbox(
        "Fee type",
        ["Shipping Charge", "Handling Fee", "Delivery Fee", "Service Charge", "Custom Fee"],
        key=f"feetype_{ks}", label_visibility="collapsed")
    fee_amt = fc2.number_input(
        "Amount", min_value=0.0, value=0.0, step=1.0,
        key=f"feeamt_{ks}", label_visibility="collapsed")
    if fc3.button("➕ Add", key=f"feeadd_{ks}", use_container_width=True):
        if fee_amt and fee_amt > 0:
            existing = next((f for f in st.session_state.pos_fees if f['type'] == fee_type), None)
            if existing:
                existing['amount'] = float(fee_amt)
            else:
                st.session_state.pos_fees.append({"type": fee_type, "amount": float(fee_amt)})
            st.rerun()
        else:
            st.toast("Enter a fee amount greater than 0.")
    for fidx, fee in enumerate(st.session_state.pos_fees):
        rc1, rc2, rc3 = st.columns([2, 1.1, 0.9])
        rc1.write(fee['type'])
        rc2.write(f"{currency} {float(fee['amount']):,.2f}")
        if rc3.button("✕", key=f"feerm_{fidx}_{ks}", use_container_width=True):
            st.session_state.pos_fees.pop(fidx)
            st.rerun()
    fees_total = float(sum(float(f['amount']) for f in st.session_state.pos_fees))

    discount = st.number_input("Discount", min_value=0.0, max_value=float(subtotal),
                               value=0.0, step=1.0, key=f"disc_{ks}")
    # Additional fees are part of the taxable base (fees are taxed)
    tax    = max(0, (subtotal - discount + fees_total) * tax_percent / 100)
    total  = subtotal - discount + fees_total + tax
    profit = float(((cart_df['price'] - cart_df['cost']) * cart_df['qty']).sum()
                   - discount + fees_total)
    if fees_total > 0:
        st.caption(
            f"Subtotal {currency} {subtotal:,.2f}  ·  Fees {currency} {fees_total:,.2f}"
            + (f"  ·  Discount −{currency} {discount:,.2f}" if discount > 0 else ""))
    st.markdown(f"### Total: {currency} {total:,.2f}")

    # ── Customer section ──────────────────────────────────────────────────
    customers     = query_df("SELECT * FROM customers ORDER BY name")
    customer_mode = st.radio("Customer", ["New Customer", "Existing Customer"],
                             horizontal=True, key=f"cmode_{ks}")
    customer_id   = None
    customer_name = phone = city = address = ""

    if customer_mode == "Existing Customer":
        if customers.empty:
            st.warning("No saved customers — filling as new.")
            customer_mode = "New Customer"
        else:
            opts   = ["— Select existing customer —"] + [
                f"{r['id']} | {r['name']} | {r.get('phone','')}"
                for _, r in customers.iterrows()
            ]
            chosen = st.selectbox("Select customer", opts, key=f"esel_{ks}")
            if chosen == "— Select existing customer —":
                st.info("Please select a customer from the list above.")
                customer_mode = "_unset_"
            else:
                customer_id    = int(chosen.split('|')[0].strip())
                prev_cid       = st.session_state.get(f"_prev_cid_{ks}")
                if prev_cid != customer_id:
                    for k in (f"exist_phone_{ks}", f"exist_city_{ks}", f"exist_addr_{ks}"):
                        st.session_state.pop(k, None)
                    st.session_state[f"_prev_cid_{ks}"] = customer_id
                c              = customers[customers.id == customer_id].iloc[0]
                customer_name  = c['name']
                original_phone = c.get('phone') or ''
                city           = c.get('city')  or ''
                address        = c.get('address') or ''
                phone_input    = st.text_input("Customer phone", value=original_phone,
                                               key=f"exist_phone_{ks}")
                city    = st.text_input("City / Island",   value=city,    key=f"exist_city_{ks}")
                address = st.text_area("Delivery address", value=address, key=f"exist_addr_{ks}")
                if phone_input.strip() and phone_input.strip() != original_phone:
                    conflict = query_df(
                        "SELECT * FROM customers WHERE phone=? AND id!=? AND phone!=''",
                        (phone_input.strip(), customer_id),
                    )
                    if not conflict.empty:
                        cr = conflict.iloc[0]
                        st.error(
                            f"⚠ Phone **{phone_input.strip()}** already belongs to "
                            f"**{cr['name']}** (ID {cr['id']}). "
                            "Select that customer directly instead."
                        )
                        phone = original_phone
                    else:
                        phone = phone_input.strip()
                else:
                    phone = phone_input.strip() or original_phone

    if customer_mode == "_unset_":
        st.stop()

    if customer_mode == "New Customer":
        phone_input = st.text_input("Phone number", key=f"new_phone_{ks}")
        phone       = phone_input.strip()
        if phone:
            matches = query_df(
                "SELECT * FROM customers WHERE phone=? AND phone!=''", (phone,))
            if not matches.empty:
                st.warning(
                    f"📋 Phone matched: **{matches.iloc[0]['name']}**. "
                    "Switch to 'Existing Customer' to avoid duplicates.")
                m = matches.iloc[0]
                if st.checkbox("Use this existing customer instead", key=f"use_ex_{ks}"):
                    customer_id   = int(m['id'])
                    customer_name = m['name']
                    city          = m.get('city')    or ''
                    address       = m.get('address') or ''
                    city    = st.text_input("City / Island",   value=city,    key=f"nc_city_{ks}")
                    address = st.text_area("Delivery address", value=address, key=f"nc_addr_{ks}")
                else:
                    customer_name = st.text_input("Customer name", key=f"nc_name_{ks}")
                    city    = st.text_input("City / Island",   key=f"nc_city2_{ks}")
                    address = st.text_area("Delivery address", key=f"nc_addr2_{ks}")
            else:
                customer_name = st.text_input("Customer name",  key=f"nc_name_{ks}")
                city    = st.text_input("City / Island",   key=f"nc_city_{ks}")
                address = st.text_area("Delivery address", key=f"nc_addr_{ks}")
                if customer_name and phone:
                    st.caption("✔ New customer will be saved on checkout.")
        else:
            customer_name = st.text_input("Customer name",  key=f"nc_name_{ks}")
            city    = st.text_input("City / Island",   key=f"nc_city_{ks}")
            address = st.text_area("Delivery address", key=f"nc_addr_{ks}")

    # ── Order details ─────────────────────────────────────────────────────
    order_type = st.selectbox("Order type", ["Delivery", "Pickup", "Walk-in"],
                              key=f"otype_{ks}")
    payment    = st.selectbox("Payment method",
                              ["Cash", "Card", "Bank Transfer", "Online Payment"],
                              key=f"pmeth_{ks}")
    assigned_to = ""
    if order_type == "Delivery":
        d_users  = query_df(
            "SELECT username, full_name FROM users WHERE role='Delivery' AND active=1")
        options  = ([f"{r['username']} | {r['full_name']}" for _, r in d_users.iterrows()]
                    or ["delivery | Delivery Team"])
        assigned_to = st.selectbox("Assign delivery", options,
                                   key=f"assign_{ks}").split('|')[0].strip()

    notes = st.text_area("Order notes", key=f"notes_{ks}")

    # ── Checkout button ───────────────────────────────────────────────────
    if st.button("✔ Complete Checkout", type="primary", use_container_width=True,
                 icon=":material/shopping_cart_checkout:", key=f"chk_{ks}"):
        # Stock validation
        for item in st.session_state.cart:
            avail = query_df("SELECT stock FROM products WHERE id=?", (int(item['id']),))
            avail = 0 if avail.empty else int(avail.iloc[0]['stock'])
            if int(item['qty']) > avail:
                st.error(f"'{item['name']}' only has {avail} in stock. Reduce qty.")
                st.stop()

        if not customer_name or not phone:
            st.error("Customer name and phone number are required.")
            st.stop()

        if customer_mode == "New Customer" and customer_id is None:
            customer_id = execute(
                "INSERT INTO customers (name,phone,city,address,created_at) VALUES (?,?,?,?,?)",
                (customer_name, phone, city, address, datetime.now().isoformat()),
            )

        order_no = next_order_no()
        status   = "Pending" if order_type == "Delivery" else "Ready"
        seller   = st.session_state.get("username", "")
        order_id = execute(
            """INSERT INTO orders
            (order_no,created_at,customer_id,customer_name,customer_phone,customer_city,
             customer_address,order_type,payment_method,payment_status,subtotal,discount,
             tax,total,profit,status,assigned_to,seller,payment_slip_no,notes,
             extra_fees,extra_fees_detail)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (order_no, datetime.now().isoformat(), customer_id, customer_name, phone,
             city, address, order_type, payment, "Unpaid", subtotal, discount, tax,
             total, profit, status, assigned_to, seller, f"PS-{order_no}", notes,
             fees_total, json.dumps(st.session_state.get("pos_fees", []))),
        )
        for item in st.session_state.cart:
            execute(
                """INSERT INTO order_items
                (order_id,product_id,product_name,product_image,qty,unit_price,unit_cost,line_total)
                VALUES (?,?,?,?,?,?,?,?)""",
                (order_id, item['id'], item['name'], item['image'],
                 item['qty'], item['price'], item['cost'], item['subtotal']),
            )
            execute("UPDATE products SET stock = stock - ? WHERE id=?",
                    (item['qty'], item['id']))

        st.session_state.cart = []
        st.session_state.pos_fees = []
        log("Completed checkout", entity="order", entity_id=order_id,
            detail=f"{order_no} · {customer_name} · {currency} {total:,.2f}")
        st.success(
            f"✅ Order **{order_no}** placed for **{customer_name}**  ·  "
            f"{currency} {total:,.2f}")
        st.balloons()
        st.rerun()


# ── Mobile cart dialog ────────────────────────────────────────────────────────
@st.dialog("🛒 Cart & Checkout", width="large")
def _cart_dialog(currency, tax_percent):
    _checkout_body(currency, tax_percent, ks="d")


# ─────────────────────────────────────────────────────────────────────────────
def render():
    _ensure_cart()
    hero("Point of Sale", "Fast checkout · phone-verified customers · live stock check.")
    currency    = get_setting("currency", "MVR")
    tax_percent = float(get_setting("tax_percent", "0") or 0)
    accent      = COLORS.get(get_setting("accent_color", "Royal Blue"), "#2563eb")

    products    = query_df(
        "SELECT * FROM products WHERE active=1 AND stock>0 ORDER BY category, name")
    cart_count  = len(st.session_state.cart)
    cart_total  = sum(i['subtotal'] for i in st.session_state.cart) if st.session_state.cart else 0.0

    # ── Floating cart button — fixed while scrolling, draggable ─────────
    st.markdown(f"""
<style>
div[data-testid="stButton"]:has(button[aria-label^="🛒 Cart"]) {{
    position: fixed !important;
    bottom: 28px !important;
    right: 28px !important;
    z-index: 99999 !important;
    width: auto !important;
}}
button[aria-label^="🛒 Cart"] {{
    border-radius: 40px !important;
    padding: 12px 22px !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    line-height: 1 !important;
    box-shadow: 0 6px 24px rgba(0,0,0,.32) !important;
    background: {accent} !important;
    color: #fff !important;
    border: none !important;
    cursor: grab !important;
    white-space: nowrap !important;
}}
button[aria-label^="🛒 Cart"]:active {{ cursor: grabbing !important; }}
</style>
""", unsafe_allow_html=True)

    fab_label = f"🛒 Cart {cart_count}" if cart_count else "🛒 Cart"
    if st.button(fab_label, key="pos_cart_fab", type="primary"):
        if cart_count > 0:
            _cart_dialog(currency, tax_percent)
        else:
            st.toast("Cart is empty — add products first.")

    # Make the floating cart button draggable; remember where it is dropped.
    components.html(
        """
        <script>
        (function(){
          var root = window.parent, pdoc = root.document, KEY = 'ordro_fab_pos';
          if(!root.__ordroFab){
            root.__ordroFab = {dragging:false, moved:false, el:null, sx:0, sy:0, ox:0, oy:0};
            function move(e){
              var S = root.__ordroFab; if(!S.dragging || !S.el) return;
              var pt = e.touches ? e.touches[0] : e, dx = pt.clientX-S.sx, dy = pt.clientY-S.sy, el = S.el;
              if(Math.abs(dx)+Math.abs(dy) > 4) S.moved = true;
              var nl = Math.max(4, Math.min(root.innerWidth  - el.offsetWidth  - 4, S.ox+dx));
              var nt = Math.max(4, Math.min(root.innerHeight - el.offsetHeight - 4, S.oy+dy));
              el.style.left = nl+'px'; el.style.top = nt+'px';
              if(S.moved && e.cancelable) e.preventDefault();
            }
            function up(){
              var S = root.__ordroFab; if(!S.dragging) return; S.dragging = false;
              if(S.moved && S.el){
                var r = S.el.getBoundingClientRect();
                try{ root.localStorage.setItem(KEY, JSON.stringify({left:r.left, top:r.top})); }catch(_){}
              }
            }
            pdoc.addEventListener('mousemove', move);
            pdoc.addEventListener('mouseup', up);
            pdoc.addEventListener('touchmove', move, {passive:false});
            pdoc.addEventListener('touchend', up);
          }
          function down(e){
            var S = root.__ordroFab, el = S.el; if(!el) return;
            var pt = e.touches ? e.touches[0] : e, r = el.getBoundingClientRect();
            S.dragging = true; S.moved = false; S.sx = pt.clientX; S.sy = pt.clientY; S.ox = r.left; S.oy = r.top;
            el.style.left = r.left+'px'; el.style.top = r.top+'px'; el.style.right = 'auto'; el.style.bottom = 'auto';
          }
          function applyPos(el){
            try{
              var s = JSON.parse(root.localStorage.getItem(KEY) || 'null');
              if(s && typeof s.left === 'number'){
                el.style.left = s.left+'px'; el.style.top = s.top+'px';
                el.style.right = 'auto'; el.style.bottom = 'auto';
              }
            }catch(e){}
          }
          function init(t){
            t = t || 0;
            var el = pdoc.querySelector('div[data-testid="stButton"]:has(button[aria-label^="🛒 Cart"])');
            if(!el){ if(t < 40) setTimeout(function(){ init(t+1); }, 120); return; }
            root.__ordroFab.el = el; applyPos(el);
            if(el.dataset.ordroDrag !== '1'){
              el.dataset.ordroDrag = '1';
              var btn = el.querySelector('button') || el;
              btn.addEventListener('mousedown', down);
              btn.addEventListener('touchstart', down, {passive:false});
              el.addEventListener('click', function(e){
                if(root.__ordroFab.moved){ e.stopPropagation(); e.preventDefault(); }
              }, true);
            }
          }
          init(0);
        })();
        </script>
        """,
        height=0, width=0,
    )

    # ── Main two-column layout ─────────────────────────────────────────────
    # Left: searchable product catalogue.  Right: cart + checkout (wide screens).
    left, right = st.columns([2, 1], gap="large")

    with left:
        st.markdown("### Products")
        search = st.text_input(
            "Search products",
            placeholder="Search by name, SKU or category — barcode/SKU scanner works here",
            key="pos_search",
            label_visibility="collapsed",
        )
        cats = ["All categories"]
        if not products.empty:
            cats += sorted(products["category"].dropna().unique().tolist())
        cat_filt = st.selectbox(
            "Category", cats, key="pos_cat", label_visibility="collapsed")

        filtered = products.copy()
        if not filtered.empty and search:
            s = search.lower()
            filtered = filtered[filtered.apply(
                lambda r: s in str(r.get('name') or '').lower()
                       or s in str(r.get('sku') or '').lower()
                       or s in str(r.get('category') or '').lower(), axis=1)]
        if not filtered.empty and cat_filt != "All categories":
            filtered = filtered[filtered['category'] == cat_filt]

        if products.empty:
            st.info("No products available to sell. Add stock in Inventory first.")
        elif filtered.empty:
            st.warning("No products match your search.")
        else:
            grid = st.columns(2)
            for i, (_, r) in enumerate(filtered.iterrows()):
                with grid[i % 2]:
                    with st.container(border=True):
                        fixed_image(r.get("image_path") or "", height=130)
                        st.markdown(f"**{r['name']}**")
                        stock_n = int(r['stock'])
                        stock_cls = "pill-green" if stock_n > int(r.get('reorder_level') or 5) else "pill-orange"
                        st.markdown(
                            f"<span class='pill pill-blue'>{r['category']}</span> "
                            f"<span class='pill {stock_cls}'>Stock {stock_n}</span>",
                            unsafe_allow_html=True,
                        )
                        if r.get("sku"):
                            st.caption(f"SKU: {r['sku']}")
                        st.write(f"**{currency} {float(r['price']):,.2f}**")
                        q_col, b_col = st.columns([1, 1.2])
                        qty = q_col.number_input(
                            "Qty", min_value=1, max_value=stock_n, value=1, step=1,
                            key=f"posqty_{r['id']}", label_visibility="collapsed",
                        )
                        if b_col.button(
                            "Add", key=f"posadd_{r['id']}",
                            use_container_width=True, icon=":material/add_shopping_cart:",
                        ):
                            _add_to_cart(r, qty)

    with right:
        # On wide screens this is the live cart/checkout panel.
        # On mobile it stacks below the products; the floating cart button
        # (FAB) opens the same checkout in a dialog for convenience.
        st.markdown(f"### 🛒 Cart  ·  {currency} {cart_total:,.2f}")
        _checkout_body(currency, tax_percent, ks="c")
