import math
from datetime import datetime
import streamlit as st
import pandas as pd
from components.database import query_df, execute, UPLOAD_DIR, get_setting
from components.theme import hero, metric_card
from components.auth import has_access
from components.ui import fixed_image
from components.activity import log


def save_upload(uploaded):
    if not uploaded:
        return ""
    safe = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded.name}".replace(" ", "_")
    path = UPLOAD_DIR / safe
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    return safe


def _supplier_options():
    sup = query_df("SELECT id, name FROM suppliers ORDER BY name")
    options = {0: "— None —"}
    for _, s in sup.iterrows():
        options[int(s["id"])] = s["name"]
    return options


def _safe_supplier_id(val):
    """Convert pandas supplier_id (may be NaN/None/float) to int key for selectbox."""
    try:
        if val is None:
            return 0
        if isinstance(val, float) and math.isnan(val):
            return 0
        return int(val)
    except Exception:
        return 0


def render():
    hero("Inventory", "Products, prices, stock levels and supplier links — with live alerts.")
    currency = get_setting("currency", "MVR")

    products = query_df("SELECT * FROM products WHERE active=1 ORDER BY (stock<=0), category, name")

    # ── Summary metrics ───────────────────────────────────────────────────
    if not products.empty:
        retail_value = float((products["price"] * products["stock"]).sum())
        out_of_stock = int((products["stock"] <= 0).sum())
        low_stock    = int(((products["stock"] > 0) & (products["stock"] <= products["reorder_level"])).sum())
        if has_access("Admin"):
            cost_value = float((products["cost"] * products["stock"]).sum())
            m1, m2, m3, m4 = st.columns(4)
            with m1: metric_card("Stock Value (Cost)",   f"{currency} {cost_value:,.2f}",   "Admin only",    "pill-violet")
            with m2: metric_card("Stock Value (Retail)", f"{currency} {retail_value:,.2f}", "Selling price", "pill-blue")
            with m3: metric_card("Low Stock",            f"{low_stock}",                    "Needs reorder", "pill-orange")
            with m4: metric_card("Out of Stock",         f"{out_of_stock}",                 "Unavailable",   "pill-red")
        else:
            m1, m2, m3 = st.columns(3)
            with m1: metric_card("Stock Value (Retail)", f"{currency} {retail_value:,.2f}", "Selling price", "pill-blue")
            with m2: metric_card("Low Stock",            f"{low_stock}",                    "Needs reorder", "pill-orange")
            with m3: metric_card("Out of Stock",         f"{out_of_stock}",                 "Unavailable",   "pill-red")

    supplier_options = _supplier_options()

    # ── Add product ───────────────────────────────────────────────────────
    if has_access("Staff"):
        with st.expander("➕ Add New Product", expanded=False):
            with st.form("product_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                name     = c1.text_input("Product Name")
                category = c2.text_input("Category", value="General")
                sku      = c3.text_input("SKU / Barcode")
                c4, c5, c6 = st.columns(3)
                cost     = c4.number_input("Cost Price",    min_value=0.0, step=1.0)
                price    = c5.number_input("Selling Price", min_value=0.0, step=1.0)
                stock    = c6.number_input("Stock",         min_value=0,   step=1)
                c7, c8 = st.columns(2)
                reorder     = c7.number_input("Reorder Alert Level", min_value=0, value=5, step=1)
                supplier_id = c8.selectbox(
                    "Supplier", list(supplier_options.keys()),
                    format_func=lambda k: supplier_options[k],
                )
                image = st.file_uploader("Product Photo", type=["png", "jpg", "jpeg", "webp"])
                if st.form_submit_button("Save Product", type="primary", icon=":material/add:"):
                    if not name or price <= 0:
                        st.error("Product name and selling price are required.")
                    else:
                        img = save_upload(image)
                        pid = execute(
                            """INSERT INTO products
                            (name,category,sku,cost,price,stock,reorder_level,image_path,supplier_id,created_at)
                            VALUES (?,?,?,?,?,?,?,?,?,?)""",
                            (name, category, sku, cost, price, stock, reorder, img,
                             supplier_id or None, datetime.now().isoformat()),
                        )
                        log("Created product", entity="product", entity_id=pid,
                            detail=f"{name} · stock {int(stock)} · {currency} {price:,.2f}")
                        st.success("Product saved.")
                        st.rerun()

    # ── Product catalogue ─────────────────────────────────────────────────
    st.markdown("### Product Catalogue")

    # Filter bar
    fc1, fc2 = st.columns([2, 1])
    search   = fc1.text_input("Search", placeholder="Name, SKU or category", label_visibility="collapsed")
    cats     = ["All categories"] + sorted(products["category"].dropna().unique().tolist()) if not products.empty else ["All categories"]
    cat_filt = fc2.selectbox("Category", cats, label_visibility="collapsed")

    if products.empty:
        st.info("No products yet. Add one above.")
        return

    filtered = products.copy()
    if search:
        s = search.lower()
        filtered = filtered[filtered.apply(
            lambda r: s in str(r['name']).lower()
                   or s in str(r['sku']).lower()
                   or s in str(r['category']).lower(), axis=1)]
    if cat_filt != "All categories":
        filtered = filtered[filtered['category'] == cat_filt]

    if filtered.empty:
        st.warning("No products match your search.")
        return

    # Split into in-stock and zero-stock for separate display
    filtered_in  = filtered[filtered['stock'] > 0]
    filtered_out = filtered[filtered['stock'] <= 0]

    def _render_product_card(r, key_suffix=""):
        """Render a single product card with edit controls."""
        with st.container(border=True):
            img_col, detail_col = st.columns([1, 1.45])
            with img_col:
                fixed_image(r.get("image_path") or "", height=160, fallback_logo=True)
            with detail_col:
                st.markdown(f"### {r['name']}")
                if int(r["stock"]) <= 0:
                    s_cls, s_lbl = "pill-red",    "Out of Stock"
                elif int(r["stock"]) <= int(r["reorder_level"]):
                    s_cls, s_lbl = "pill-orange", f"Low · {r['stock']}"
                else:
                    s_cls, s_lbl = "pill-green",  f"Stock {r['stock']}"
                st.markdown(
                    f"<span class='pill pill-blue'>{r['category']}</span> "
                    f"<span class='pill {s_cls}'>{s_lbl}</span>",
                    unsafe_allow_html=True,
                )
                if r.get("sku"):
                    st.caption(f"SKU: {r['sku']}")
                st.write(f"**{currency} {float(r['price']):,.2f}**")
                if has_access("Admin"):
                    st.caption(
                        f"Cost: {currency} {float(r['cost']):,.2f} · "
                        f"Margin: {((float(r['price'])-float(r['cost']))/float(r['price'])*100):.0f}% · "
                        f"Reorder at {r['reorder_level']}"
                        if float(r["price"]) > 0 else
                        f"Cost: {currency} {float(r['cost']):,.2f}"
                    )
                sup_id = _safe_supplier_id(r.get("supplier_id"))
                if sup_id and sup_id in supplier_options:
                    st.caption(f"Supplier: {supplier_options[sup_id]}")

            if has_access("Admin"):
                with st.expander("✏ Edit Product"):
                    e_name     = st.text_input("Name",     r["name"],          key=f"pn_{r['id']}{key_suffix}")
                    e_category = st.text_input("Category", r["category"],      key=f"pc_{r['id']}{key_suffix}")
                    e_sku      = st.text_input("SKU",      r.get("sku") or "", key=f"ps_{r['id']}{key_suffix}")
                    cc1, cc2, cc3 = st.columns(3)
                    e_cost  = cc1.number_input("Cost",  value=float(r["cost"]),  min_value=0.0, step=1.0, key=f"pct_{r['id']}{key_suffix}")
                    e_price = cc2.number_input("Price", value=float(r["price"]), min_value=0.0, step=1.0, key=f"pp_{r['id']}{key_suffix}")
                    e_stock = cc3.number_input("Stock", value=int(r["stock"]),   min_value=0,   step=1,   key=f"pst_{r['id']}{key_suffix}")
                    e_reorder = st.number_input("Reorder Level", value=int(r["reorder_level"]), min_value=0, step=1, key=f"pr_{r['id']}{key_suffix}")
                    cur_sup = _safe_supplier_id(r.get("supplier_id"))
                    if cur_sup not in supplier_options:
                        cur_sup = 0
                    e_sup = st.selectbox(
                        "Supplier", list(supplier_options.keys()),
                        index=list(supplier_options.keys()).index(cur_sup),
                        format_func=lambda k: supplier_options[k],
                        key=f"psup_{r['id']}{key_suffix}",
                    )
                    e_image  = st.file_uploader("New Photo (optional)", type=["png","jpg","jpeg","webp"], key=f"pimg_{r['id']}{key_suffix}")
                    e_active = st.checkbox("Active", value=bool(r["active"]), key=f"pa_{r['id']}{key_suffix}")
                    if st.button("Save", key=f"savep_{r['id']}{key_suffix}", type="primary", icon=":material/save:"):
                        new_img = save_upload(e_image) if e_image else (r.get("image_path") or "")
                        execute(
                            """UPDATE products
                            SET name=?, category=?, sku=?, cost=?, price=?, stock=?,
                                reorder_level=?, supplier_id=?, active=?, image_path=?
                            WHERE id=?""",
                            (e_name, e_category, e_sku, e_cost, e_price, e_stock,
                             e_reorder, e_sup or None, int(e_active), new_img, int(r["id"])),
                        )
                        log("Updated product", entity="product", entity_id=int(r["id"]),
                            detail=f"{e_name} · stock {int(e_stock)}")
                        st.success("Product updated.")
                        st.rerun()

                    st.markdown("---")
                    st.caption("⚠ Danger zone — permanently removes this product.")
                    confirm_del = st.checkbox(
                        "Confirm permanent delete",
                        key=f"pdelchk_{r['id']}{key_suffix}",
                    )
                    if st.button(
                        "Delete Product", key=f"pdel_{r['id']}{key_suffix}",
                        disabled=not confirm_del, icon=":material/delete:",
                    ):
                        execute("DELETE FROM products WHERE id=?", (int(r["id"]),))
                        log("Deleted product", entity="product", entity_id=int(r["id"]),
                            detail=r["name"])
                        st.success("Product deleted.")
                        st.rerun()

            elif has_access("Staff"):
                with st.expander("📦 Update Stock"):
                    new_stock = st.number_input(
                        "Stock", value=int(r["stock"]), min_value=0, step=1,
                        key=f"staff_st_{r['id']}{key_suffix}",
                    )
                    if st.button("Save Stock", key=f"sst_{r['id']}{key_suffix}", type="primary", icon=":material/save:"):
                        execute("UPDATE products SET stock=? WHERE id=?", (new_stock, int(r["id"])))
                        log("Updated stock", entity="product", entity_id=int(r["id"]),
                            detail=f"{r['name']} → {int(new_stock)}")
                        st.success("Stock updated.")
                        st.rerun()

    # ── IN-STOCK PRODUCTS ─────────────────────────────────────────────────
    if not filtered_in.empty:
        cols = st.columns(2)
        for i, (_, r) in enumerate(filtered_in.iterrows()):
            with cols[i % 2]:
                _render_product_card(r)

    # ── OUT-OF-STOCK PRODUCTS (shown separately for easy restocking) ──────
    if not filtered_out.empty:
        st.markdown("---")
        st.markdown(
            "<div style='background:#fef2f2;border-left:5px solid #dc2626;border-radius:10px;"
            "padding:10px 18px;margin-bottom:14px;'>"
            "<b style='color:#dc2626;font-size:15px;'>⚠ Out of Stock</b>"
            " <span style='color:#94a3b8;font-size:13px;'>— Items below need restocking</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        cols_oos = st.columns(2)
        for i, (_, r) in enumerate(filtered_out.iterrows()):
            with cols_oos[i % 2]:
                _render_product_card(r, key_suffix="_oos")

    # ── Stock alerts ──────────────────────────────────────────────────────
    alerts = products[products["stock"] <= products["reorder_level"]]
    if not alerts.empty:
        st.markdown("---")
        st.markdown("### ⚠ Stock Alerts")
        cols2 = st.columns(3)
        for j, (_, a) in enumerate(alerts.iterrows()):
            with cols2[j % 3]:
                out   = int(a["stock"]) <= 0
                pill  = "pill-red" if out else "pill-orange"
                label = "Out of stock" if out else f"Low stock: {a['stock']}"
                st.markdown(
                    f"<div class='info-card'><b>{a['name']}</b><br>"
                    f"<span class='pill {pill}'>{label}</span><br>"
                    f"<span class='muted'>Reorder at: {a['reorder_level']}</span></div>",
                    unsafe_allow_html=True,
                )
