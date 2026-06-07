import html
import calendar
from datetime import date, timedelta
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from components.database import query_df, scalar, get_setting, today_iso
from components.theme import hero, metric_card
from components.auth import has_access, current_role
from components.icons import svg

STATUS_CLASS = {
    "Pending":          "pill-orange",
    "Preparing":        "pill-violet",
    "Ready":            "pill-blue",
    "Out for Delivery": "pill-pink",
    "Delivered":        "pill-green",
    "Completed":        "pill-green",
    "Cancelled":        "pill-red",
}


def esc(v):
    return "" if v is None else html.escape(str(v))


def money(v, cur):
    try:
        return f"{cur} {float(v):,.2f}"
    except Exception:
        return f"{cur} 0.00"


def fully_completed_condition():
    return "status IN ('Delivered','Completed') AND COALESCE(payment_status,'Unpaid')='Paid'"


def open_orders_where(extra=""):
    base = f"status!='Cancelled' AND NOT ({fully_completed_condition()})"
    return f"{base} AND {extra}" if extra else base


def order_card_html(row, currency):
    status         = row.get("status") or "Pending"
    payment_status = row.get("payment_status") or "Unpaid"
    s_cls  = STATUS_CLASS.get(status, "pill-blue")
    p_cls  = "pill-red" if payment_status != "Paid" else "pill-green"
    cust   = f"{row.get('customer_name') or '—'}  ·  {row.get('customer_phone') or '—'}"
    addr   = f"{row.get('customer_city') or ''} {row.get('customer_address') or ''}".strip() or "No address"
    asgn   = row.get("assigned_to") or "—"
    date_s = str(row.get("created_at") or "")[:16].replace("T", " ")
    needs_action = status != "Cancelled" and not (
        status in ["Delivered", "Completed"] and payment_status == "Paid"
    )
    na_tag = '<span class="pill pill-red">Needs action</span>' if needs_action else ""
    na_cls = " needs-action" if needs_action else ""
    return f"""
    <div class="order-card{na_cls}">
        <div class="order-no">{esc(row.get('order_no', '—'))}</div>
        <div class="order-meta">{esc(cust)}</div>
        <div class="order-meta">{esc(addr)}</div>
        <div class="order-meta" style="color:#94a3b8;font-size:11.5px;">{esc(date_s)}</div>
        <div class="pill-row">
            <span class="pill {s_cls}">{esc(status)}</span>
            <span class="pill pill-blue">{esc(money(row.get('total', 0), currency))}</span>
            <span class="pill {p_cls}">{esc(payment_status)}</span>
            {na_tag}
        </div>
        <div class="order-meta assigned">Assigned: {esc(asgn)}</div>
    </div>
    """


def orders_html(title, where_sql, currency, params=(), empty_text="No orders found.", warning=False):
    df = query_df(f"""
        SELECT order_no, customer_name, customer_phone, customer_city, customer_address,
               status, total, assigned_to, payment_status, created_at, order_type
        FROM orders WHERE {where_sql}
        ORDER BY
            CASE WHEN status IN ('Delivered','Completed')
                 AND COALESCE(payment_status,'Unpaid')!='Paid' THEN 0 ELSE 1 END,
            created_at DESC
        LIMIT 80
    """, params)
    warn_html = ""
    if warning:
        unpaid = scalar(f"""SELECT COUNT(*) FROM orders
            WHERE {where_sql} AND status IN ('Delivered','Completed')
            AND COALESCE(payment_status,'Unpaid')!='Paid'""", params)
        if unpaid and int(unpaid) > 0:
            warn_html = f'<div class="warning-box">⚠ {int(unpaid)} delivered but unpaid — payment still outstanding.</div>'
    if df.empty:
        body = f"<div class='empty-box'>{esc(empty_text)}</div>"
    else:
        body = "<div class='orders-grid'>" + "".join(
            order_card_html(r, currency) for _, r in df.iterrows()
        ) + "</div>"
    return f"<div class='detail-heading'>{esc(title)}</div>{warn_html}{body}"


def low_stock_html():
    low = query_df("""
        SELECT name, category, sku, stock, reorder_level
        FROM products WHERE active=1 AND stock <= reorder_level
        ORDER BY stock ASC, name ASC LIMIT 80
    """)
    if low.empty:
        return "<div class='detail-heading'>Low Stock Items</div><div class='empty-box'>✓ All items well stocked.</div>"
    cards = "".join(f"""
        <div class="order-card needs-action">
            <div class="order-no">{esc(r.get('name'))}</div>
            <div class="order-meta">{esc(r.get('category') or 'General')} · SKU: {esc(r.get('sku') or '—')}</div>
            <div class="pill-row">
                <span class="pill pill-red">Stock: {int(r.get('stock') or 0)}</span>
                <span class="pill pill-orange">Reorder at: {int(r.get('reorder_level') or 0)}</span>
            </div>
        </div>
    """ for _, r in low.iterrows())
    return f"<div class='detail-heading'>Low Stock Items</div><div class='orders-grid'>{cards}</div>"


def card_html(tab_id, title, value, note, card_class, icon, has_beacon=False, beacon_type="red"):
    beacon = ""
    if has_beacon and value not in ("0", "0.00"):
        beacon = f'<span class="beacon-dot{"" if beacon_type=="red" else "-orange"}"></span>'
    return f"""
    <label class="dash-card {card_class}" for="{tab_id}">
        <div class="dash-icon">{icon}</div>
        <div class="dash-title">{esc(title)}{beacon}</div>
        <div class="dash-value">{esc(value)}</div>
        <div class="dash-note">{esc(note)}</div>
    </label>
    """


def dashboard_css(tab_ids):
    selectors, active = [], []
    for tid in tab_ids:
        pid = "detail_" + tid.replace("dash_", "")
        selectors.append(
            f"#{tid}:checked ~ .dashboard-details #{pid}{{display:block;}}"
        )
        active.append(
            f"#{tid}:checked ~ .dashboard-grid label[for='{tid}']"
            f"{{outline:2px solid rgba(37,99,235,.30);transform:translateY(-4px);"
            f"box-shadow:0 16px 40px rgba(0,0,0,.14);}}"
        )
    return f"""
    <style>
    *{{box-sizing:border-box;}}
    body{{margin:0;padding:0;background:transparent;
          font-family:'DM Sans',system-ui,sans-serif;color:#0f172a;
          overflow-x:hidden;-webkit-font-smoothing:antialiased;}}
    .dashboard-root{{padding:2px 2px 10px;width:100%;}}
    input[type='radio']{{position:absolute;opacity:0;width:0;height:0;pointer-events:none;}}

    /* metric cards */
    .dashboard-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-bottom:14px;}}
    .dash-card{{display:block;width:100%;min-height:160px;padding:20px 18px 16px;
               border-radius:20px;background:rgba(255,255,255,.97);
               border:1px solid rgba(220,228,240,.80);
               box-shadow:0 4px 14px rgba(0,0,0,.07);
               transition:all .18s ease;cursor:pointer;user-select:none;
               position:relative;overflow:hidden;}}
    .dash-card:hover{{transform:translateY(-4px);box-shadow:0 14px 36px rgba(0,0,0,.12);
                      border-color:rgba(37,99,235,.30);}}
    .dash-icon{{position:absolute;top:16px;right:16px;width:36px;height:36px;border-radius:11px;
               display:flex;align-items:center;justify-content:center;font-size:17px;
               background:rgba(255,255,255,.80);border:1px solid rgba(220,228,240,.80);}}
    .dash-title{{font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;
                color:#64748b;margin-bottom:10px;padding-right:46px;}}
    .dash-value{{font-size:30px;font-weight:700;letter-spacing:-.04em;line-height:1;
                margin-bottom:8px;word-break:break-word;}}
    .dash-note{{font-size:11.5px;color:#94a3b8;font-weight:500;}}

    /* beacon animations */
    @keyframes beacon{{0%{{box-shadow:0 0 0 0 rgba(220,38,38,.6);}}
                       70%{{box-shadow:0 0 0 10px rgba(220,38,38,0);}}
                       100%{{box-shadow:0 0 0 0 rgba(220,38,38,0);}}}}
    @keyframes beacon-orange{{0%{{box-shadow:0 0 0 0 rgba(217,119,6,.6);}}
                              70%{{box-shadow:0 0 0 10px rgba(217,119,6,0);}}
                              100%{{box-shadow:0 0 0 0 rgba(217,119,6,0);}}}}
    .beacon-dot{{display:inline-block;width:9px;height:9px;border-radius:50%;
                background:#dc2626;animation:beacon 1.6s infinite;
                vertical-align:middle;margin-left:5px;}}
    .beacon-dot-orange{{display:inline-block;width:9px;height:9px;border-radius:50%;
                       background:#d97706;animation:beacon-orange 1.6s infinite;
                       vertical-align:middle;margin-left:5px;}}

    /* card colours */
    .sales-card{{background:linear-gradient(135deg,#fff,#f0fdf4);border-color:rgba(5,150,105,.22);}}
    .sales-card .dash-value{{color:#065f46;}}.sales-card .dash-icon{{color:#059669;border-color:rgba(5,150,105,.22);}}
    .open-card{{background:linear-gradient(135deg,#fff,#eff6ff);border-color:rgba(37,99,235,.22);}}
    .open-card .dash-value{{color:#1d4ed8;}}.open-card .dash-icon{{color:#2563eb;border-color:rgba(37,99,235,.20);}}
    .danger-card{{background:linear-gradient(135deg,#fff,#fef2f2);border-color:rgba(220,38,38,.22);}}
    .danger-card .dash-value{{color:#b91c1c;}}.danger-card .dash-icon{{color:#dc2626;border-color:rgba(220,38,38,.20);}}
    .low-stock-card{{background:linear-gradient(135deg,#fff,#fffbeb);border-color:rgba(217,119,6,.22);}}
    .low-stock-card .dash-value{{color:#92400e;}}.low-stock-card .dash-icon{{color:#d97706;border-color:rgba(217,119,6,.20);}}

    /* detail panels */
    .dashboard-details{{margin-top:4px;}}
    .dashboard-detail-panel{{display:none;margin-top:4px;}}
    {"".join(selectors)}
    {"".join(active)}
    .detail-heading{{font-size:19px;font-weight:700;letter-spacing:-.03em;
                    margin:6px 0 12px;color:#0f172a;}}
    .orders-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:14px;}}
    .order-card{{background:#fff;border:1.5px solid rgba(220,228,240,.80);
               border-radius:16px;box-shadow:0 2px 8px rgba(0,0,0,.05);padding:14px;}}
    .order-card.needs-action{{border-color:rgba(220,38,38,.28);
                             background:linear-gradient(135deg,#fff,rgba(254,242,242,.70));}}
    .order-no{{font-weight:700;font-size:14.5px;margin-bottom:4px;color:#0f172a;}}
    .order-meta{{color:#64748b;font-size:12px;font-weight:500;margin-bottom:4px;line-height:1.45;}}
    .assigned{{margin-top:6px;color:#94a3b8;}}
    .pill-row{{display:flex;flex-wrap:wrap;gap:4px;margin-top:5px;}}
    .pill{{display:inline-flex;align-items:center;padding:2px 8px;border-radius:999px;
          font-size:10.5px;font-weight:600;}}
    .pill-blue{{background:#eff6ff;color:#1d4ed8;}}.pill-green{{background:#f0fdf4;color:#15803d;}}
    .pill-orange{{background:#fffbeb;color:#b45309;}}.pill-pink{{background:#fdf2f8;color:#9d174d;}}
    .pill-violet{{background:#f5f3ff;color:#5b21b6;}}.pill-red{{background:#fef2f2;color:#b91c1c;}}
    .warning-box{{background:linear-gradient(135deg,#fff,rgba(254,242,242,.80));
                 border:1px solid rgba(220,38,38,.28);color:#991b1b;
                 border-radius:14px;padding:12px 14px;margin-bottom:10px;
                 font-weight:600;font-size:13px;}}
    .empty-box{{background:#fff;border:1px solid rgba(220,228,240,.80);
               border-radius:14px;padding:14px;color:#94a3b8;font-size:14px;font-weight:500;}}

    @media(max-width:1000px){{.dashboard-grid,.orders-grid{{grid-template-columns:repeat(2,minmax(0,1fr));}}}}
    @media(max-width:640px){{
        .dashboard-grid{{grid-template-columns:1fr;gap:8px;}}
        .orders-grid{{grid-template-columns:1fr;gap:8px;}}
        .dash-card{{min-height:130px;padding:16px;border-radius:16px;}}
        .dash-value{{font-size:26px;}}
    }}
    </style>
    """


def render_dashboard_component(cards_html, panels_html, radio_inputs, tab_ids, height=920):
    scroll_js = """
    <script>
    (function() {
      // When any radio changes (card clicked), scroll the detail panel into view
      // and notify parent window to scroll down
      function onCardClick() {
        setTimeout(function() {
          var panel = document.querySelector('.dashboard-detail-panel[style*="block"], .dashboard-detail-panel:not([style*="none"])');
          // Find actually visible panel
          var panels = document.querySelectorAll('.dashboard-detail-panel');
          for (var p of panels) {
            if (p.style.display !== 'none' && p.offsetParent !== null) {
              p.scrollIntoView({behavior: 'smooth', block: 'start'});
              break;
            }
          }
          // Ask parent page to scroll down to show details
          try {
            window.parent.postMessage({type: 'ordro_scroll_down'}, '*');
          } catch(e) {}
        }, 80);
      }

      var radios = document.querySelectorAll('input[type="radio"]');
      radios.forEach(function(r) {
        r.addEventListener('change', onCardClick);
      });

      // Also handle label clicks (since labels trigger radio change)
      var labels = document.querySelectorAll('.dash-card');
      labels.forEach(function(lbl) {
        lbl.addEventListener('click', onCardClick);
      });
    })();
    </script>
    """
    html_doc = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
    <link href='https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap' rel='stylesheet'>
    {dashboard_css(tab_ids)}</head><body>
    <div class='dashboard-root'>{radio_inputs}
    <div class='dashboard-grid'>{cards_html}</div>
    <div class='dashboard-details' id='dash-details'>{panels_html}</div>
    </div>{scroll_js}</body></html>"""
    components.html(html_doc, height=height, scrolling=True)

    # Listen for scroll-down message from the iframe
    st.markdown("""
    <script>
    window.addEventListener('message', function(e) {
      if (e.data && e.data.type === 'ordro_scroll_down') {
        // Find the iframe and scroll so its bottom is visible
        var iframes = document.querySelectorAll('iframe');
        for (var iframe of iframes) {
          var rect = iframe.getBoundingClientRect();
          if (rect.top < window.innerHeight && rect.bottom > 0) {
            // Scroll so detail panels are visible (~60% down the iframe)
            window.scrollBy({top: Math.max(rect.top + rect.height * 0.38, 200), behavior: 'smooth'});
            break;
          }
        }
      }
    });
    </script>
    """, unsafe_allow_html=True)


def _saturday_week_range(today=None):
    today = today or date.today()
    days_since_saturday = (today.weekday() - 5) % 7
    start = today - timedelta(days=days_since_saturday)
    return start, start + timedelta(days=6)


def _small_bar_value(value):
    try:
        value = float(value or 0)
    except Exception:
        value = 0.0
    return value if value > 0 else 0.001


def render_sales_chart(currency):
    today = date.today()

    view_options = [
        "This Week", "This Month", "This Year",
        "Previous Week", "Previous Month",
        "Custom Period",
    ]
    view = st.selectbox("Sales chart period", view_options, key="dashboard_sales_chart_view")

    labels, display_values, actual_values, title = [], [], [], ""

    if view == "This Week":
        start, end = _saturday_week_range(today)
        sales = query_df("""
            SELECT date(created_at) AS period, COALESCE(SUM(total),0) AS revenue
            FROM orders WHERE status!='Cancelled'
              AND date(created_at) BETWEEN ? AND ?
            GROUP BY date(created_at)
        """, (start.isoformat(), end.isoformat()))
        lookup = {str(r["period"]): float(r["revenue"] or 0) for _, r in sales.iterrows()}
        for i in range(7):
            d = start + timedelta(days=i)
            rev = lookup.get(d.isoformat(), 0.0)
            labels.append(d.strftime("%a %d"))
            actual_values.append(rev)
            display_values.append(_small_bar_value(rev))
        title = f"This Week  ({start.strftime('%d %b')} – {end.strftime('%d %b %Y')})"

    elif view == "Previous Week":
        start, _ = _saturday_week_range(today)
        prev_end = start - timedelta(days=1)
        prev_start, _ = _saturday_week_range(prev_end)
        sales = query_df("""
            SELECT date(created_at) AS period, COALESCE(SUM(total),0) AS revenue
            FROM orders WHERE status!='Cancelled'
              AND date(created_at) BETWEEN ? AND ?
            GROUP BY date(created_at)
        """, (prev_start.isoformat(), prev_end.isoformat()))
        lookup = {str(r["period"]): float(r["revenue"] or 0) for _, r in sales.iterrows()}
        for i in range(7):
            d = prev_start + timedelta(days=i)
            rev = lookup.get(d.isoformat(), 0.0)
            labels.append(d.strftime("%a %d"))
            actual_values.append(rev)
            display_values.append(_small_bar_value(rev))
        title = f"Previous Week  ({prev_start.strftime('%d %b')} – {prev_end.strftime('%d %b %Y')})"

    elif view == "This Month":
        month_start = today.replace(day=1)
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        ym = today.strftime("%Y-%m")
        sales = query_df("""
            SELECT date(created_at) AS period, COALESCE(SUM(total),0) AS revenue
            FROM orders WHERE status!='Cancelled' AND strftime('%Y-%m', created_at)=?
            GROUP BY date(created_at)
        """, (ym,))
        lookup = {str(r["period"]): float(r["revenue"] or 0) for _, r in sales.iterrows()}
        for day in range(1, days_in_month + 1):
            d = month_start.replace(day=day)
            rev = lookup.get(d.isoformat(), 0.0)
            labels.append(str(day))
            actual_values.append(rev)
            display_values.append(_small_bar_value(rev))
        title = f"This Month  ({today.strftime('%B %Y')})"

    elif view == "Previous Month":
        first = today.replace(day=1)
        prev_last = first - timedelta(days=1)
        ym = prev_last.strftime("%Y-%m")
        days_in_month = calendar.monthrange(prev_last.year, prev_last.month)[1]
        month_start = prev_last.replace(day=1)
        sales = query_df("""
            SELECT date(created_at) AS period, COALESCE(SUM(total),0) AS revenue
            FROM orders WHERE status!='Cancelled' AND strftime('%Y-%m', created_at)=?
            GROUP BY date(created_at)
        """, (ym,))
        lookup = {str(r["period"]): float(r["revenue"] or 0) for _, r in sales.iterrows()}
        for day in range(1, days_in_month + 1):
            d = month_start.replace(day=day)
            rev = lookup.get(d.isoformat(), 0.0)
            labels.append(str(day))
            actual_values.append(rev)
            display_values.append(_small_bar_value(rev))
        title = f"Previous Month  ({prev_last.strftime('%B %Y')})"

    elif view == "This Year":
        sales = query_df("""
            SELECT strftime('%m', created_at) AS period, COALESCE(SUM(total),0) AS revenue
            FROM orders WHERE status!='Cancelled' AND strftime('%Y', created_at)=?
            GROUP BY strftime('%m', created_at)
        """, (str(today.year),))
        lookup = {str(r["period"]): float(r["revenue"] or 0) for _, r in sales.iterrows()}
        for month in range(1, 13):
            key = f"{month:02d}"
            rev = lookup.get(key, 0.0)
            labels.append(calendar.month_abbr[month])
            actual_values.append(rev)
            display_values.append(_small_bar_value(rev))
        title = f"This Year  ({today.year})"

    elif view == "Custom Period":
        c1, c2 = st.columns(2)
        start_d = c1.date_input("From", value=today - timedelta(days=29), key="chart_custom_start")
        end_d   = c2.date_input("To",   value=today, key="chart_custom_end")
        if start_d > end_d:
            st.warning("Start date must be before end date.")
            return
        sales = query_df("""
            SELECT date(created_at) AS period, COALESCE(SUM(total),0) AS revenue
            FROM orders WHERE status!='Cancelled'
              AND date(created_at) BETWEEN ? AND ?
            GROUP BY date(created_at)
        """, (start_d.isoformat(), end_d.isoformat()))
        lookup = {str(r["period"]): float(r["revenue"] or 0) for _, r in sales.iterrows()}
        delta = (end_d - start_d).days + 1
        for i in range(delta):
            d = start_d + timedelta(days=i)
            rev = lookup.get(d.isoformat(), 0.0)
            labels.append(d.strftime("%d %b"))
            actual_values.append(rev)
            display_values.append(_small_bar_value(rev))
        title = f"Custom Period  ({start_d.strftime('%d %b %Y')} – {end_d.strftime('%d %b %Y')})"

    if not labels:
        st.info("No sales data for this period.")
        return

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels,
        y=display_values,
        customdata=actual_values,
        name="Revenue",
        marker_color="#2563eb",
        marker_line_width=0,
        hovertemplate=f"%{{x}}<br>Revenue: {currency} %{{customdata:,.2f}}<extra></extra>",
    ))
    fig.update_layout(
        height=320,
        margin=dict(l=0, r=0, t=44, b=0),
        title=dict(text=title, font=dict(size=16, family="DM Sans")),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, title="", tickfont=dict(size=11, family="DM Sans")),
        yaxis=dict(gridcolor="rgba(0,0,0,.06)", title=f"Revenue ({currency})",
                   tickfont=dict(size=11, family="DM Sans")),
        font=dict(family="DM Sans, system-ui"),
        showlegend=False,
        bargap=0.3,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_admin_staff_dashboard(currency):
    today_str = today_iso()  # ← FIX: use local date, not SQLite UTC date('now')

    today_sales  = scalar("SELECT COALESCE(SUM(total),0) FROM orders WHERE date(created_at)=? AND status!='Cancelled'", (today_str,))
    week_s, week_e = _saturday_week_range()
    week_sales   = scalar("SELECT COALESCE(SUM(total),0) FROM orders WHERE date(created_at) BETWEEN ? AND ? AND status!='Cancelled'",
                          (week_s.isoformat(), week_e.isoformat()))
    month_sales  = scalar("SELECT COALESCE(SUM(total),0) FROM orders WHERE strftime('%Y-%m', created_at)=? AND status!='Cancelled'",
                          (date.today().strftime("%Y-%m"),))
    open_orders  = scalar(f"SELECT COUNT(*) FROM orders WHERE {open_orders_where()}")
    needs_action = scalar(f"SELECT COUNT(*) FROM orders WHERE {open_orders_where()} AND (status NOT IN ('Delivered','Completed') OR COALESCE(payment_status,'Unpaid')!='Paid')")
    low_stock    = scalar("SELECT COUNT(*) FROM products WHERE active=1 AND stock <= reorder_level")

    tab_ids = ["dash_open_orders", "dash_today_sales", "dash_week_sales",
               "dash_month_sales", "dash_needs_action", "dash_low_stock"]
    radios  = "".join(
        f"<input type='radio' name='ordro_dash' id='{t}'{' checked' if i == 0 else ''}>"
        for i, t in enumerate(tab_ids)
    )

    needs_beacon = int(needs_action) > 0
    low_beacon   = int(low_stock) > 0

    cards = "".join([
        card_html("dash_today_sales",  "Today's Sales",   money(today_sales, currency),  "Tap to view today's orders",        "sales-card",     svg("trending-up")),
        card_html("dash_week_sales",   "Weekly Sales",    money(week_sales,  currency),   "Tap to view this week's orders",    "sales-card",     svg("bar-chart")),
        card_html("dash_month_sales",  "Monthly Sales",   money(month_sales, currency),   "Tap to view this month's orders",   "sales-card",     svg("calendar")),
        card_html("dash_open_orders",  "Open Orders",     f"{int(open_orders):,}",         "Tap to view open orders",           "open-card",      svg("clipboard")),
        card_html("dash_needs_action", "Needs Action",    f"{int(needs_action):,}",        "Tap to review",                     "danger-card",    svg("alert"),   has_beacon=needs_beacon, beacon_type="red"),
        card_html("dash_low_stock",    "Low Stock",       f"{int(low_stock):,}",           "Tap to view low-stock items",       "low-stock-card", svg("package"), has_beacon=low_beacon,   beacon_type="orange"),
    ])

    panels = f"""
    <div class='dashboard-detail-panel' id='detail_today_sales'>
        {orders_html("Today's Orders", "date(created_at)=? AND status!='Cancelled'", currency, (today_str,))}
    </div>
    <div class='dashboard-detail-panel' id='detail_week_sales'>
        {orders_html("This Week's Orders", "date(created_at) BETWEEN ? AND ? AND status!='Cancelled'", currency, (week_s.isoformat(), week_e.isoformat()))}
    </div>
    <div class='dashboard-detail-panel' id='detail_month_sales'>
        {orders_html("This Month's Orders", "strftime('%Y-%m', created_at)=? AND status!='Cancelled'", currency, (date.today().strftime('%Y-%m'),))}
    </div>
    <div class='dashboard-detail-panel' id='detail_open_orders'>
        {orders_html("Open Orders", open_orders_where(), currency)}
    </div>
    <div class='dashboard-detail-panel' id='detail_needs_action'>
        {orders_html("Needs Action", f"{open_orders_where()} AND (status NOT IN ('Delivered','Completed') OR COALESCE(payment_status,'Unpaid')!='Paid')", currency, warning=True)}
    </div>
    <div class='dashboard-detail-panel' id='detail_low_stock'>
        {low_stock_html()}
    </div>
    """
    # CSS to kill Streamlit's padding below the iframe component
    st.markdown(
        '<style>div[data-testid="stCustomComponentV1"]{margin-bottom:-2rem!important;}iframe{display:block;}</style>',
        unsafe_allow_html=True,
    )
    render_dashboard_component(cards, panels, radios, tab_ids, height=960)
    render_sales_chart(currency)

    if has_access("Admin"):
        st.markdown("---")
        st.markdown("#### Admin Snapshot")
        profit = scalar("SELECT COALESCE(SUM(profit),0) FROM orders WHERE status!='Cancelled'")
        cost   = scalar("SELECT COALESCE(SUM(qty*unit_cost),0) FROM order_items")
        c1, c2 = st.columns(2)
        with c1:
            metric_card("Total Profit (All Time)", money(profit, currency), "Admin only", "pill-green")
        with c2:
            metric_card("Approx. Cost of Sales", money(cost, currency), "Admin only", "pill-violet")


def render_delivery_dashboard(currency):
    today_str = today_iso()
    delivery_extra  = "order_type='Delivery'"
    open_deliveries = scalar(f"SELECT COUNT(*) FROM orders WHERE {open_orders_where(delivery_extra)}")
    needs_action    = scalar(f"SELECT COUNT(*) FROM orders WHERE {open_orders_where(delivery_extra)} AND (status NOT IN ('Delivered','Completed') OR COALESCE(payment_status,'Unpaid')!='Paid')")
    completed_today = scalar(
        "SELECT COUNT(*) FROM orders WHERE order_type='Delivery' AND status IN ('Delivered','Completed') AND COALESCE(payment_status,'Unpaid')='Paid' AND date(created_at)=?",
        (today_str,),
    )

    tab_ids = ["dash_delivery_open", "dash_delivery_needs_action", "dash_delivery_completed_today"]
    radios  = "".join(
        f"<input type='radio' name='ordro_dash' id='{t}'{' checked' if i == 0 else ''}>"
        for i, t in enumerate(tab_ids)
    )
    needs_beacon = int(needs_action) > 0
    cards = "".join([
        card_html("dash_delivery_open",            "Open Deliveries",  f"{int(open_deliveries):,}", "Tap to view",           "open-card",    svg("truck")),
        card_html("dash_delivery_needs_action",    "Needs Action",     f"{int(needs_action):,}",    "Tap to review",         "danger-card",  svg("alert"),        has_beacon=needs_beacon),
        card_html("dash_delivery_completed_today", "Completed Today",  f"{int(completed_today):,}", "Deliveries done today", "sales-card",   svg("check-circle")),
    ])
    panels = f"""
    <div class='dashboard-detail-panel' id='detail_delivery_open'>
        {orders_html("Open Delivery Orders", open_orders_where(delivery_extra), currency)}
    </div>
    <div class='dashboard-detail-panel' id='detail_delivery_needs_action'>
        {orders_html("Needs Action", f"{open_orders_where(delivery_extra)} AND (status NOT IN ('Delivered','Completed') OR COALESCE(payment_status,'Unpaid')!='Paid')", currency, warning=True)}
    </div>
    <div class='dashboard-detail-panel' id='detail_delivery_completed_today'>
        {orders_html("Completed Today", "order_type='Delivery' AND status IN ('Delivered','Completed') AND COALESCE(payment_status,'Unpaid')='Paid' AND date(created_at)=?", currency, (today_str,))}
    </div>
    """
    render_dashboard_component(cards, panels, radios, tab_ids, height=800)


def render():
    role     = current_role()
    currency = get_setting("currency", "MVR")
    hero("Dashboard", "Live sales overview · open orders · action alerts · inventory health")
    if role == "Delivery":
        render_delivery_dashboard(currency)
    else:
        render_admin_staff_dashboard(currency)
