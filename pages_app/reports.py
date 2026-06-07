from datetime import datetime, timedelta, date
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from components.database import query_df, scalar, get_setting, today_iso, fmt_date
from components.theme import hero, metric_card
from components.auth import has_access


def money(v, cur):
    try:
        return f"{cur} {float(v):,.2f}"
    except Exception:
        return f"{cur} 0.00"


def _period_sql(period, custom_start=None, custom_end=None):
    today = date.today()
    if period == "Today":
        return "date(created_at)=?", (today_iso(),)
    if period == "This week":
        start = today - timedelta(days=today.weekday())
        return "date(created_at) >= ?", (start.isoformat(),)
    if period == "This month":
        return "strftime('%Y-%m', created_at)=?", (today.strftime("%Y-%m"),)
    if period == "Last 30 days":
        return "date(created_at) >= ?", ((today - timedelta(days=29)).isoformat(),)
    if period == "Last 90 days":
        return "date(created_at) >= ?", ((today - timedelta(days=89)).isoformat(),)
    if period == "This year":
        return "strftime('%Y', created_at)=?", (str(today.year),)
    if period == "Custom" and custom_start and custom_end:
        return "date(created_at) BETWEEN ? AND ?", (custom_start.isoformat(), custom_end.isoformat())
    return "1=1", ()  # All time


def render():
    hero("Reports & Analytics", "Sales performance · profit · expenses · team · customers · inventory insights")
    currency = get_setting("currency", "MVR")

    # ── Period selector ───────────────────────────────────────────────────
    period_opts = ["Today", "This week", "This month", "Last 30 days", "Last 90 days", "This year", "All time", "Custom"]
    col_p, col_s, col_e = st.columns([1.5, 1, 1])
    with col_p:
        period = st.selectbox("Report period", period_opts, index=2)
    custom_start = custom_end = None
    if period == "Custom":
        with col_s:
            custom_start = st.date_input("From", value=date.today() - timedelta(days=29))
        with col_e:
            custom_end = st.date_input("To", value=date.today())

    p_sql, p_params = _period_sql(period, custom_start, custom_end)
    where_active = f"status!='Cancelled' AND {p_sql}"

    # ── Top-level KPIs ────────────────────────────────────────────────────
    revenue  = scalar(f"SELECT COALESCE(SUM(total),0) FROM orders WHERE {where_active}", p_params)
    orders_n = scalar(f"SELECT COUNT(*) FROM orders WHERE {where_active}", p_params)
    avg_val  = (float(revenue) / int(orders_n)) if int(orders_n) > 0 else 0
    delivered = scalar(f"SELECT COUNT(*) FROM orders WHERE {where_active} AND status IN ('Delivered','Completed')", p_params)
    cancelled = scalar(f"SELECT COUNT(*) FROM orders WHERE {p_sql} AND status='Cancelled'", p_params)

    k_cols = st.columns(5)
    with k_cols[0]: metric_card("Revenue", money(revenue, currency), period, "pill-blue")
    with k_cols[1]: metric_card("Orders", f"{int(orders_n):,}", "Excl. cancelled", "pill-violet")
    with k_cols[2]: metric_card("Avg Order Value", money(avg_val, currency), "Per order", "pill-blue")
    with k_cols[3]: metric_card("Delivered", f"{int(delivered):,}", "Completed", "pill-green")
    with k_cols[4]: metric_card("Cancelled", f"{int(cancelled):,}", period, "pill-red")

    if has_access("Admin"):
        profit   = scalar(f"SELECT COALESCE(SUM(profit),0) FROM orders WHERE {where_active}", p_params)
        expenses = scalar(f"SELECT COALESCE(SUM(amount),0) FROM expenses WHERE {p_sql.replace('created_at','date')}", p_params)
        net      = float(profit) - float(expenses)
        margin   = (float(profit) / float(revenue) * 100) if float(revenue) > 0 else 0
        a_cols = st.columns(4)
        with a_cols[0]: metric_card("Gross Profit", money(profit, currency), "Admin only", "pill-green")
        with a_cols[1]: metric_card("Expenses", money(expenses, currency), period, "pill-orange")
        with a_cols[2]: metric_card("Net Profit", money(net, currency), "Profit − Expenses", "pill-green" if net >= 0 else "pill-red")
        with a_cols[3]: metric_card("Profit Margin", f"{margin:.1f}%", "Gross margin", "pill-violet")

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────────
    # TAB LAYOUT
    # ─────────────────────────────────────────────────────────────────────
    tab_labels = ["📈 Sales Trend", "🏆 Best Sellers", "👥 Customers", "💳 Payments"]
    if has_access("Admin"):
        tab_labels += ["💰 Profit & Expenses", "👨‍💼 Team Performance", "📦 Inventory Value"]
    tabs = st.tabs(tab_labels)

    # ── Sales Trend ───────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown("#### Daily Revenue Trend")
        daily = query_df(
            f"SELECT date(created_at) AS day, COALESCE(SUM(total),0) AS revenue,"
            f"       COUNT(*) AS orders FROM orders WHERE {where_active} GROUP BY day ORDER BY day",
            p_params,
        )
        if not daily.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=daily["day"], y=daily["revenue"],
                name="Revenue", marker_color="#2563eb", marker_line_width=0,
                hovertemplate=f"%{{x}}<br>Revenue: {currency} %{{y:,.2f}}<extra></extra>",
            ))
            fig.add_trace(go.Scatter(
                x=daily["day"], y=daily["revenue"],
                mode="lines", name="Trend",
                line=dict(color="#059669", width=2, dash="dot"),
            ))
            fig.update_layout(height=320, margin=dict(l=0,r=0,t=10,b=0),
                              plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                              showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            # Running total
            daily_cum = daily.copy()
            daily_cum["cumulative"] = daily_cum["revenue"].cumsum()
            fig2 = px.line(daily_cum, x="day", y="cumulative",
                           title="Cumulative Revenue",
                           labels={"cumulative": f"Revenue ({currency})", "day": "Date"})
            fig2.update_traces(fill="tozeroy", line_color="#7c3aed")
            fig2.update_layout(height=240, margin=dict(l=0,r=0,t=36,b=0),
                               plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No sales data for this period.")

        # Revenue by order type
        st.markdown("#### Revenue by Order Type")
        by_type = query_df(
            f"SELECT COALESCE(order_type,'Unknown') AS type, COALESCE(SUM(total),0) AS revenue,"
            f"       COUNT(*) AS orders FROM orders WHERE {where_active} GROUP BY type",
            p_params,
        )
        if not by_type.empty:
            cc1, cc2 = st.columns(2)
            with cc1:
                fig = px.pie(by_type, values="revenue", names="type", hole=.45,
                             title="Revenue Split")
                fig.update_layout(height=280, margin=dict(l=0,r=0,t=36,b=0),
                                  paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
            with cc2:
                show = by_type.copy()
                show["revenue"] = show["revenue"].apply(lambda v: money(v, currency))
                show.columns = ["Order Type", "Revenue", "Orders"]
                st.dataframe(show, use_container_width=True, hide_index=True)

        # Revenue by category
        st.markdown("#### Revenue by Product Category")
        cat = query_df(
            "SELECT COALESCE(p.category,'Uncategorised') AS category,"
            "       COALESCE(SUM(oi.line_total),0) AS revenue,"
            "       SUM(oi.qty) AS units"
            " FROM order_items oi"
            " JOIN orders o ON oi.order_id=o.id"
            " LEFT JOIN products p ON p.id = oi.product_id"
            f" WHERE o.status!='Cancelled' AND {p_sql.replace('created_at', 'o.created_at')}"
            " GROUP BY category ORDER BY revenue DESC",
            p_params,
        )
        if not cat.empty:
            fig = px.bar(cat, x="category", y="revenue",
                         labels={"revenue": f"Revenue ({currency})", "category": "Category"})
            fig.update_traces(marker_color="#2563eb", marker_line_width=0)
            fig.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0),
                              plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        # Hourly heatmap
        st.markdown("#### Sales by Hour of Day")
        hourly = query_df(
            f"SELECT CAST(strftime('%H', created_at) AS INTEGER) AS hour,"
            f"       COUNT(*) AS orders, COALESCE(SUM(total),0) AS revenue"
            f" FROM orders WHERE {where_active} GROUP BY hour ORDER BY hour",
            p_params,
        )
        if not hourly.empty:
            fig = px.bar(hourly, x="hour", y="orders",
                         labels={"hour": "Hour of Day (0–23)", "orders": "# Orders"},
                         title="Peak hours")
            fig.update_traces(marker_color="#0d9488", marker_line_width=0)
            fig.update_layout(height=240, margin=dict(l=0,r=0,t=36,b=0),
                              plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    # ── Best Sellers ──────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown("#### Top Products by Units Sold")
        best = query_df(
            "SELECT oi.product_name AS Product,"
            "       SUM(oi.qty) AS Units,"
            "       COALESCE(SUM(oi.line_total),0) AS Revenue,"
            "       COALESCE(AVG(oi.unit_price),0) AS AvgPrice"
            " FROM order_items oi JOIN orders o ON oi.order_id=o.id"
            f" WHERE o.status!='Cancelled' AND {p_sql.replace('created_at', 'o.created_at')}"
            " GROUP BY oi.product_name ORDER BY Units DESC LIMIT 20",
            p_params,
        )
        if best.empty:
            st.info("No sales data yet.")
        else:
            cc1, cc2 = st.columns([1.3, 1])
            with cc1:
                fig = px.bar(best.head(10).sort_values("Units"), x="Units", y="Product",
                             orientation="h",
                             labels={"Units": "Units Sold", "Product": ""},
                             title="Top 10 Products")
                fig.update_traces(marker_color="#2563eb", marker_line_width=0)
                fig.update_layout(height=380, margin=dict(l=0,r=0,t=36,b=0),
                                  plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
            with cc2:
                show = best.head(10).copy()
                show["Revenue"]  = show["Revenue"].apply(lambda v: money(v, currency))
                show["AvgPrice"] = show["AvgPrice"].apply(lambda v: money(v, currency))
                show.columns = ["Product", "Units", "Revenue", "Avg Price"]
                st.dataframe(show, use_container_width=True, hide_index=True, height=380)

        st.markdown("#### Revenue by Product")
        best_rev = query_df(
            "SELECT oi.product_name AS Product,"
            "       COALESCE(SUM(oi.line_total),0) AS Revenue"
            " FROM order_items oi JOIN orders o ON oi.order_id=o.id"
            f" WHERE o.status!='Cancelled' AND {p_sql.replace('created_at', 'o.created_at')}"
            " GROUP BY oi.product_name ORDER BY Revenue DESC LIMIT 10",
            p_params,
        )
        if not best_rev.empty:
            fig = px.pie(best_rev, values="Revenue", names="Product", hole=.4)
            fig.update_layout(height=320, margin=dict(l=0,r=0,t=10,b=0),
                              paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    # ── Customer Analytics ────────────────────────────────────────────────
    with tabs[2]:
        st.markdown("#### Top Customers by Revenue")
        top_customers = query_df(
            f"SELECT customer_name AS Customer, customer_phone AS Phone,"
            f"       COUNT(*) AS Orders, COALESCE(SUM(total),0) AS Revenue,"
            f"       COALESCE(AVG(total),0) AS AvgOrder"
            f" FROM orders WHERE {where_active} AND customer_name IS NOT NULL"
            f" GROUP BY customer_name ORDER BY Revenue DESC LIMIT 20",
            p_params,
        )
        if top_customers.empty:
            st.info("No customer data.")
        else:
            show = top_customers.copy()
            show["Revenue"]  = show["Revenue"].apply(lambda v: money(v, currency))
            show["AvgOrder"] = show["AvgOrder"].apply(lambda v: money(v, currency))
            show.columns = ["Customer", "Phone", "Orders", "Revenue", "Avg Order Value"]
            st.dataframe(show, use_container_width=True, hide_index=True, height=400)

        st.markdown("#### New vs Returning Customer Orders")
        total_cust = scalar(f"SELECT COUNT(DISTINCT customer_id) FROM orders WHERE {where_active}", p_params)
        repeat     = scalar(
            f"SELECT COUNT(DISTINCT customer_id) FROM orders WHERE {where_active}"
            f" AND customer_id IN (SELECT customer_id FROM orders WHERE {where_active}"
            f" GROUP BY customer_id HAVING COUNT(*) > 1)",
            p_params + p_params,
        )
        one_time   = int(total_cust) - int(repeat)
        c_cols = st.columns(3)
        with c_cols[0]: metric_card("Unique Customers", f"{int(total_cust):,}", period, "pill-blue")
        with c_cols[1]: metric_card("Repeat Customers", f"{int(repeat):,}", "Ordered 2+", "pill-green")
        with c_cols[2]: metric_card("One-Time Customers", f"{int(one_time):,}", period, "pill-orange")

        st.markdown("#### Customer City / Island Distribution")
        by_city = query_df(
            f"SELECT COALESCE(NULLIF(customer_city,''),'Unknown') AS city,"
            f"       COUNT(*) AS orders, COALESCE(SUM(total),0) AS revenue"
            f" FROM orders WHERE {where_active}"
            f" GROUP BY city ORDER BY orders DESC LIMIT 15",
            p_params,
        )
        if not by_city.empty:
            fig = px.bar(by_city, x="city", y="orders",
                         labels={"city": "City / Island", "orders": "Orders"},
                         title="Orders by Location")
            fig.update_traces(marker_color="#0ea5e9", marker_line_width=0)
            fig.update_layout(height=280, margin=dict(l=0,r=0,t=36,b=0),
                              plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    # ── Payment Analytics ─────────────────────────────────────────────────
    with tabs[3]:
        st.markdown("#### Payment Method Breakdown")
        by_method = query_df(
            f"SELECT COALESCE(payment_method,'Unknown') AS method,"
            f"       COUNT(*) AS orders, COALESCE(SUM(total),0) AS revenue"
            f" FROM orders WHERE {where_active}"
            f" GROUP BY method ORDER BY revenue DESC",
            p_params,
        )
        if not by_method.empty:
            cc1, cc2 = st.columns(2)
            with cc1:
                fig = px.pie(by_method, values="revenue", names="method", hole=.4,
                             title="Revenue by Payment Method")
                fig.update_layout(height=280, margin=dict(l=0,r=0,t=36,b=0),
                                  paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
            with cc2:
                show = by_method.copy()
                show["revenue"] = show["revenue"].apply(lambda v: money(v, currency))
                show.columns = ["Method", "Orders", "Revenue"]
                st.dataframe(show, use_container_width=True, hide_index=True)

        st.markdown("#### Payment Status Summary")
        by_pay = query_df(
            f"SELECT COALESCE(payment_status,'Unpaid') AS status,"
            f"       COUNT(*) AS orders, COALESCE(SUM(total),0) AS amount"
            f" FROM orders WHERE {p_sql} AND status!='Cancelled'"
            f" GROUP BY payment_status ORDER BY amount DESC",
            p_params,
        )
        if not by_pay.empty:
            show = by_pay.copy()
            show["amount"] = show["amount"].apply(lambda v: money(v, currency))
            show.columns = ["Payment Status", "Orders", "Amount"]
            st.dataframe(show, use_container_width=True, hide_index=True)

        unpaid_total = scalar(
            f"SELECT COALESCE(SUM(total),0) FROM orders WHERE {p_sql}"
            f" AND status!='Cancelled' AND COALESCE(payment_status,'Unpaid')!='Paid'",
            p_params,
        )
        if float(unpaid_total) > 0:
            st.warning(f"⚠ {money(unpaid_total, currency)} in outstanding unpaid orders for this period.")

    # ── Admin: Profit & Expenses ──────────────────────────────────────────
    if has_access("Admin") and len(tabs) > 4:
        with tabs[4]:
            st.markdown("#### Profit vs Expenses Over Time")
            daily_profit = query_df(
                f"SELECT date(created_at) AS day, COALESCE(SUM(profit),0) AS profit,"
                f"       COALESCE(SUM(total),0) AS revenue"
                f" FROM orders WHERE {where_active} GROUP BY day ORDER BY day",
                p_params,
            )
            daily_expenses = query_df(
                f"SELECT date AS day, COALESCE(SUM(amount),0) AS expenses"
                f" FROM expenses WHERE {p_sql.replace('created_at','date')}"
                f" GROUP BY date ORDER BY date",
                p_params,
            )
            if not daily_profit.empty:
                merged = daily_profit.merge(daily_expenses, on="day", how="left").fillna(0)
                merged["net"] = merged["profit"] - merged["expenses"]
                fig = go.Figure()
                fig.add_trace(go.Bar(x=merged["day"], y=merged["revenue"], name="Revenue",
                                     marker_color="#2563eb"))
                fig.add_trace(go.Bar(x=merged["day"], y=merged["profit"], name="Gross Profit",
                                     marker_color="#059669"))
                fig.add_trace(go.Scatter(x=merged["day"], y=merged["expenses"],
                                         name="Expenses", line=dict(color="#dc2626", width=2)))
                fig.update_layout(barmode="overlay", height=340,
                                  margin=dict(l=0,r=0,t=10,b=0),
                                  plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### Expense Breakdown by Category")
            exp_cat = query_df(
                f"SELECT COALESCE(category,'Other') AS category,"
                f"       COALESCE(SUM(amount),0) AS amount, COUNT(*) AS entries"
                f" FROM expenses WHERE {p_sql.replace('created_at','date')}"
                f" GROUP BY category ORDER BY amount DESC",
                p_params,
            )
            if not exp_cat.empty:
                cc1, cc2 = st.columns(2)
                with cc1:
                    fig = px.pie(exp_cat, values="amount", names="category", hole=.4)
                    fig.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0),
                                      paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)
                with cc2:
                    show = exp_cat.copy()
                    show["amount"] = show["amount"].apply(lambda v: money(v, currency))
                    show.columns = ["Category", "Total", "Entries"]
                    st.dataframe(show, use_container_width=True, hide_index=True)
            else:
                st.info("No expenses recorded for this period.")

        # ── Team Performance ──────────────────────────────────────────────
        with tabs[5]:
            st.markdown("#### Sales by Team Member (Seller)")
            by_seller = query_df(
                f"SELECT COALESCE(NULLIF(seller,''),'Unassigned') AS Seller,"
                f"       COUNT(*) AS Orders, COALESCE(SUM(total),0) AS Revenue,"
                f"       COALESCE(SUM(profit),0) AS Profit"
                f" FROM orders WHERE {where_active}"
                f" GROUP BY Seller ORDER BY Revenue DESC",
                p_params,
            )
            if not by_seller.empty:
                cc1, cc2 = st.columns([1.3, 1])
                with cc1:
                    fig = px.bar(by_seller, x="Seller", y="Revenue",
                                 labels={"Revenue": f"Revenue ({currency})"},
                                 title="Revenue per Seller")
                    fig.update_traces(marker_color="#7c3aed", marker_line_width=0)
                    fig.update_layout(height=320, margin=dict(l=0,r=0,t=36,b=0),
                                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)
                with cc2:
                    show = by_seller.copy()
                    show["Revenue"] = show["Revenue"].apply(lambda v: money(v, currency))
                    show["Profit"]  = show["Profit"].apply(lambda v: money(v, currency))
                    st.dataframe(show, use_container_width=True, hide_index=True, height=320)
            else:
                st.info("No seller data for this period.")

            st.markdown("#### Deliveries by Assigned Staff")
            by_assigned = query_df(
                f"SELECT COALESCE(NULLIF(assigned_to,''),'Unassigned') AS Staff,"
                f"       COUNT(*) AS Orders, COALESCE(SUM(total),0) AS Value,"
                f"       SUM(CASE WHEN status IN ('Delivered','Completed') THEN 1 ELSE 0 END) AS Completed"
                f" FROM orders WHERE order_type='Delivery' AND {where_active}"
                f" GROUP BY Staff ORDER BY Orders DESC",
                p_params,
            )
            if not by_assigned.empty:
                show = by_assigned.copy()
                show["Value"] = show["Value"].apply(lambda v: money(v, currency))
                show.columns = ["Staff", "Orders", "Value", "Completed"]
                st.dataframe(show, use_container_width=True, hide_index=True)

        # ── Inventory Value ───────────────────────────────────────────────
        with tabs[6]:
            st.markdown("#### Current Inventory Value")
            products = query_df(
                "SELECT name, category, sku, cost, price, stock, reorder_level,"
                "       (cost*stock) AS cost_value, (price*stock) AS retail_value"
                " FROM products WHERE active=1 ORDER BY retail_value DESC"
            )
            if products.empty:
                st.info("No products found.")
            else:
                total_cost   = float((products["cost"]  * products["stock"]).sum())
                total_retail = float((products["price"] * products["stock"]).sum())
                potential    = total_retail - total_cost
                low_stock    = int((products["stock"] <= products["reorder_level"]).sum())
                out_of_stock = int((products["stock"] <= 0).sum())

                iv_cols = st.columns(4)
                with iv_cols[0]: metric_card("Stock Value (Cost)",   money(total_cost, currency),   "At purchase cost", "pill-violet")
                with iv_cols[1]: metric_card("Stock Value (Retail)", money(total_retail, currency), "At selling price", "pill-blue")
                with iv_cols[2]: metric_card("Potential Profit",     money(potential, currency),    "If all sold",      "pill-green")
                with iv_cols[3]: metric_card("Low / Out of Stock",   f"{low_stock} / {out_of_stock}", "Items", "pill-orange")

                st.markdown("#### Stock by Category")
                by_cat = query_df(
                    "SELECT COALESCE(category,'Uncategorised') AS category,"
                    "       SUM(stock) AS units, SUM(price*stock) AS retail_value"
                    " FROM products WHERE active=1 GROUP BY category ORDER BY retail_value DESC"
                )
                if not by_cat.empty:
                    fig = px.treemap(by_cat, path=["category"], values="retail_value",
                                     title="Inventory Value by Category (Retail)")
                    fig.update_layout(height=340, margin=dict(l=0,r=0,t=36,b=0))
                    st.plotly_chart(fig, use_container_width=True)

                st.markdown("#### Low Stock Alert")
                low = products[products["stock"] <= products["reorder_level"]]
                if low.empty:
                    st.success("✓ All products well stocked.")
                else:
                    show = low[["name", "category", "sku", "stock", "reorder_level",
                                "cost_value", "retail_value"]].copy()
                    show["cost_value"]   = show["cost_value"].apply(lambda v: money(v, currency))
                    show["retail_value"] = show["retail_value"].apply(lambda v: money(v, currency))
                    show.columns = ["Product", "Category", "SKU", "Stock", "Reorder At",
                                    "Cost Value", "Retail Value"]
                    st.dataframe(show, use_container_width=True, hide_index=True)
