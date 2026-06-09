"""Chart.js-based finance charts for Reports & Dashboard (reads the live DB)."""
import json
from datetime import date, timedelta
import streamlit as st
import streamlit.components.v1 as components
from components.database import query_df

BLUE = "#2563eb"; GREEN = "#16a34a"; ORANGE = "#f97316"; SLATE = "#64748b"
VIOLET = "#8b5cf6"; TEAL = "#0ea5a4"; AMBER = "#f59e0b"; RED = "#ef4444"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _sat_week(today=None):
    today = today or date.today()
    diff = (today.weekday() - 5) % 7
    start = today - timedelta(days=diff)
    return start, start + timedelta(days=6)


def _period_range(period):
    t = date.today()
    if period == "week":
        s, e = _sat_week(t); return s.isoformat(), e.isoformat()
    if period == "year":
        return date(t.year, 1, 1).isoformat(), date(t.year, 12, 31).isoformat()
    return t.replace(day=1).isoformat(), t.isoformat()


def _render(cfg, height=360):
    js = json.dumps(cfg)
    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<script src='https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js'></script>"
        "<style>html,body{margin:0;font-family:Segoe UI,system-ui,sans-serif;}"
        "#wrap{height:" + str(height - 10) + "px;padding:4px 2px;}</style></head>"
        "<body><div id='wrap'><canvas id='c'></canvas></div><script>"
        "var cfg=" + js + ";"
        "cfg.options=cfg.options||{};cfg.options.responsive=true;cfg.options.maintainAspectRatio=false;"
        "cfg.options.plugins=cfg.options.plugins||{};"
        "cfg.options.plugins.legend=Object.assign({labels:{font:{size:10},boxWidth:11,boxHeight:11,padding:7}},cfg.options.plugins.legend||{});"
        "if(cfg.options.scales){for(var k in cfg.options.scales){cfg.options.scales[k].ticks=Object.assign({font:{size:10}},cfg.options.scales[k].ticks||{});}}"
        "new Chart(document.getElementById('c'),cfg);</script></body></html>"
    )
    components.html(html, height=height)


def _sp_cfg(labels, sales, profit, style):
    if style == "line":
        ds = [
            {"label": "Sales", "data": sales, "borderColor": BLUE, "borderWidth": 2, "fill": False, "tension": 0.25, "pointRadius": 2},
            {"label": "Profit", "data": profit, "borderColor": GREEN, "borderWidth": 2, "fill": False, "tension": 0.25, "pointRadius": 2},
        ]
        t = "line"
    else:
        ds = [
            {"label": "Sales", "data": sales, "backgroundColor": BLUE, "borderRadius": 5},
            {"label": "Profit", "data": profit, "backgroundColor": GREEN, "borderRadius": 5},
        ]
        t = "bar"
    return {"type": t, "data": {"labels": labels, "datasets": ds}, "options": {}}


def _hbar(labels, data, label, color, pct=False):
    opts = {"indexAxis": "y", "plugins": {"legend": {"display": False}}}
    if pct:
        opts["scales"] = {"x": {"ticks": {}}}
    return {"type": "bar", "data": {"labels": labels,
            "datasets": [{"label": label, "data": data, "backgroundColor": color, "borderRadius": 5}]},
            "options": opts}


# ── individual report builders: return (title, cfg, insight) ─────────────────
def _b_sp_weekly(style, period):
    s, e = _sat_week()
    df = query_df("SELECT date(created_at) d, COALESCE(SUM(total),0) s, COALESCE(SUM(profit),0) p "
                  "FROM orders WHERE date(created_at) BETWEEN ? AND ? AND status!='Cancelled' GROUP BY date(created_at)",
                  (s.isoformat(), e.isoformat()))
    m = {str(r["d"]): (float(r["s"]), float(r["p"])) for _, r in df.iterrows()}
    labels = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]; sales = []; profit = []
    for i in range(7):
        sv, pv = m.get((s + timedelta(days=i)).isoformat(), (0, 0))
        sales.append(round(sv, 2)); profit.append(round(pv, 2))
    title = f"Sales & Profit — This week ({s.strftime('%d %b')} – {e.strftime('%d %b')})"
    ins = f"Week total: sales {sum(sales):,.0f}, profit {sum(profit):,.0f}."
    return title, _sp_cfg(labels, sales, profit, style), ins


def _b_sp_monthly(style, period):
    t = date.today(); ym = t.strftime("%Y-%m")
    import calendar
    ndays = calendar.monthrange(t.year, t.month)[1]
    df = query_df("SELECT CAST(strftime('%d', created_at) AS INTEGER) d, COALESCE(SUM(total),0) s, COALESCE(SUM(profit),0) p "
                  "FROM orders WHERE strftime('%Y-%m', created_at)=? AND status!='Cancelled' GROUP BY d", (ym,))
    m = {int(r["d"]): (float(r["s"]), float(r["p"])) for _, r in df.iterrows()}
    labels = [str(i) for i in range(1, ndays + 1)]
    sales = [round(m.get(i, (0, 0))[0], 2) for i in range(1, ndays + 1)]
    profit = [round(m.get(i, (0, 0))[1], 2) for i in range(1, ndays + 1)]
    title = f"Sales & Profit — {t.strftime('%B %Y')} (daily)"
    ins = f"Month total: sales {sum(sales):,.0f}, profit {sum(profit):,.0f}."
    return title, _sp_cfg(labels, sales, profit, style), ins


def _b_sp_yearly(style, period):
    t = date.today()
    df = query_df("SELECT CAST(strftime('%m', created_at) AS INTEGER) m, COALESCE(SUM(total),0) s, COALESCE(SUM(profit),0) p "
                  "FROM orders WHERE strftime('%Y', created_at)=? AND status!='Cancelled' GROUP BY m", (str(t.year),))
    mp = {int(r["m"]): (float(r["s"]), float(r["p"])) for _, r in df.iterrows()}
    sales = [round(mp.get(i, (0, 0))[0], 2) for i in range(1, 13)]
    profit = [round(mp.get(i, (0, 0))[1], 2) for i in range(1, 13)]
    title = f"Sales & Profit — {t.year} (monthly)"
    ins = f"Year to date: sales {sum(sales):,.0f}, profit {sum(profit):,.0f}."
    return title, _sp_cfg(MONTHS, sales, profit, style), ins


def _monthly_series(year):
    rev = query_df("SELECT CAST(strftime('%m', created_at) AS INTEGER) m, COALESCE(SUM(total),0) v "
                   "FROM orders WHERE strftime('%Y', created_at)=? AND status!='Cancelled' GROUP BY m", (str(year),))
    cost = query_df("SELECT CAST(strftime('%m', o.created_at) AS INTEGER) m, COALESCE(SUM(oi.qty*oi.unit_cost),0) v "
                    "FROM order_items oi JOIN orders o ON oi.order_id=o.id "
                    "WHERE strftime('%Y', o.created_at)=? AND o.status!='Cancelled' GROUP BY m", (str(year),))
    prof = query_df("SELECT CAST(strftime('%m', created_at) AS INTEGER) m, COALESCE(SUM(profit),0) v "
                    "FROM orders WHERE strftime('%Y', created_at)=? AND status!='Cancelled' GROUP BY m", (str(year),))
    exp = query_df("SELECT CAST(strftime('%m', date) AS INTEGER) m, COALESCE(SUM(amount),0) v "
                   "FROM expenses WHERE strftime('%Y', date)=? GROUP BY m", (str(year),))
    items = query_df("SELECT CAST(strftime('%m', o.created_at) AS INTEGER) m, COALESCE(SUM(oi.qty),0) v "
                     "FROM order_items oi JOIN orders o ON oi.order_id=o.id "
                     "WHERE strftime('%Y', o.created_at)=? AND o.status!='Cancelled' GROUP BY m", (str(year),))
    def arr(df):
        d = {int(r["m"]): float(r["v"]) for _, r in df.iterrows()}
        return [round(d.get(i, 0), 2) for i in range(1, 13)]
    return arr(rev), arr(cost), arr(prof), arr(exp), arr(items)


def _b_rcn(style, period):
    t = date.today()
    rev, cost, prof, exp, items = _monthly_series(t.year)
    net = [round(rev[i] - cost[i] - exp[i], 2) for i in range(12)]
    cfg = {"type": "line", "data": {"labels": MONTHS, "datasets": [
        {"label": "Revenue", "data": rev, "borderColor": BLUE, "borderWidth": 2, "fill": False, "tension": 0.25},
        {"label": "Cost of Goods", "data": cost, "borderColor": SLATE, "borderWidth": 2, "fill": False, "tension": 0.25},
        {"label": "Net Profit", "data": net, "borderColor": GREEN, "borderWidth": 2, "fill": False, "tension": 0.25},
    ]}, "options": {}}
    return (f"Revenue vs Cost of Goods vs Net Profit — {t.year}", cfg,
            f"Net = Revenue − Cost − Expenses. Year net profit {sum(net):,.0f}.")


def _b_items_rev(style, period):
    t = date.today()
    rev, cost, prof, exp, items = _monthly_series(t.year)
    cfg = {"data": {"labels": MONTHS, "datasets": [
        {"type": "bar", "label": "Items sold", "data": [int(x) for x in items], "backgroundColor": AMBER, "borderRadius": 5, "yAxisID": "y"},
        {"type": "line", "label": "Revenue", "data": rev, "borderColor": BLUE, "borderWidth": 2, "tension": 0.25, "yAxisID": "y1"},
    ]}, "type": "bar", "options": {"scales": {
        "y": {"position": "left", "title": {"display": True, "text": "Items"}},
        "y1": {"position": "right", "grid": {"drawOnChartArea": False}, "title": {"display": True, "text": "Revenue"}}}}}
    return (f"Number of Items vs Revenue — {t.year}", cfg,
            "Compares units sold against revenue each month.")


def _b_category(style, period):
    df = query_df("SELECT COALESCE(p.category,'Uncategorised') cat, COALESCE(SUM(oi.line_total),0) sales, "
                  "COALESCE(SUM(oi.qty*(oi.unit_price-oi.unit_cost)),0) profit "
                  "FROM order_items oi JOIN orders o ON oi.order_id=o.id LEFT JOIN products p ON oi.product_id=p.id "
                  "WHERE o.status!='Cancelled' GROUP BY cat ORDER BY sales DESC LIMIT 12")
    labels = df["cat"].astype(str).tolist()
    sales = [round(float(x), 2) for x in df["sales"]]
    profit = [round(float(x), 2) for x in df["profit"]]
    return ("Sales & Profit by Category", _sp_cfg(labels, sales, profit, style),
            f"Top category: {labels[0] if labels else '—'}.")


def _b_product(style, period):
    df = query_df("SELECT oi.product_name pn, COALESCE(SUM(oi.line_total),0) sales, "
                  "COALESCE(SUM(oi.qty*(oi.unit_price-oi.unit_cost)),0) profit "
                  "FROM order_items oi JOIN orders o ON oi.order_id=o.id "
                  "WHERE o.status!='Cancelled' GROUP BY oi.product_name ORDER BY sales DESC LIMIT 12")
    labels = df["pn"].astype(str).tolist()
    sales = [round(float(x), 2) for x in df["sales"]]
    profit = [round(float(x), 2) for x in df["profit"]]
    return ("Sales & Profit by Product", _sp_cfg(labels, sales, profit, style),
            f"Best-selling product: {labels[0] if labels else '—'}.")


def _top_query(period):
    s, e = _period_range(period)
    return query_df("SELECT oi.product_name pn, COALESCE(SUM(oi.line_total),0) rev, "
                    "COALESCE(SUM(oi.qty*(oi.unit_price-oi.unit_cost)),0) prof, COALESCE(SUM(oi.qty),0) vol "
                    "FROM order_items oi JOIN orders o ON oi.order_id=o.id "
                    "WHERE o.status!='Cancelled' AND date(o.created_at) BETWEEN ? AND ? "
                    "GROUP BY oi.product_name", (s, e))


def _top(metric, period):
    df = _top_query(period)
    rows = []
    for _, r in df.iterrows():
        rev = float(r["rev"]); prof = float(r["prof"]); vol = float(r["vol"])
        pct = (prof / rev * 100) if rev > 0 else 0
        rows.append((str(r["pn"]), rev, prof, pct, vol))
    pname = {"revenue": "Revenue", "profit": "Profit", "profit_pct": "Profit %", "volume": "Units sold"}[metric]
    idx = {"revenue": 1, "profit": 2, "profit_pct": 3, "volume": 4}[metric]
    rows.sort(key=lambda x: x[idx], reverse=True)
    rows = rows[:8]
    labels = [r[0] for r in rows]
    data = [round(r[idx], 1 if metric == "profit_pct" else 2) for r in rows]
    color = {"revenue": BLUE, "profit": GREEN, "profit_pct": VIOLET, "volume": TEAL}[metric]
    cfg = _hbar(labels, data, pname, color, pct=(metric == "profit_pct"))
    return (f"Top Products — by {pname} ({period})", cfg,
            f"Leader: {labels[0] if labels else '—'}.")


def _b_top_rev(style, period): return _top("revenue", period)
def _b_top_profit(style, period): return _top("profit", period)
def _b_top_pct(style, period): return _top("profit_pct", period)
def _b_top_vol(style, period): return _top("volume", period)


def _b_expenses(style, period):
    df = query_df("SELECT category, COALESCE(SUM(amount),0) a FROM expenses GROUP BY category ORDER BY a DESC LIMIT 12")
    labels = df["category"].astype(str).tolist()
    data = [round(float(x), 2) for x in df["a"]]
    return ("Expenses by Category", _hbar(labels, data, "Expense", ORANGE),
            f"Largest cost: {labels[0] if labels else '—'}.")


def _b_projection(style, period):
    # use available monthly history, project 6 months at the average MoM growth
    df = query_df("SELECT strftime('%Y-%m', created_at) ym, COALESCE(SUM(total),0) rev, COALESCE(SUM(profit),0) prof "
                  "FROM orders WHERE status!='Cancelled' GROUP BY ym ORDER BY ym")
    if df.empty:
        return ("Revenue & Profit Growth Projection", {"type": "line", "data": {"labels": [], "datasets": []}, "options": {}},
                "Not enough history yet to project.")
    labels = df["ym"].astype(str).tolist()
    rev = [round(float(x), 2) for x in df["rev"]]
    prof = [round(float(x), 2) for x in df["prof"]]
    g = 0.06 / 12
    if len(rev) >= 2 and rev[-2] > 0:
        g = max(min((rev[-1] - rev[-2]) / rev[-2], 0.5), -0.2)
    lr, lp = rev[-1], prof[-1]
    for i in range(1, 7):
        lr = lr * (1 + g); lp = lp * (1 + g)
        rev.append(round(lr, 2)); prof.append(round(lp, 2)); labels.append(f"+{i}")
    cfg = {"type": "line", "data": {"labels": labels, "datasets": [
        {"label": "Revenue", "data": rev, "borderColor": BLUE, "backgroundColor": "rgba(37,99,235,.07)", "fill": True, "tension": 0.3, "pointRadius": 1},
        {"label": "Profit", "data": prof, "borderColor": GREEN, "backgroundColor": "rgba(22,163,74,.07)", "fill": True, "tension": 0.3, "pointRadius": 1},
    ]}, "options": {}}
    return ("Revenue & Profit Growth Projection (from past records)", cfg,
            f"Projected next-period revenue ~{rev[-1]:,.0f}, profit ~{prof[-1]:,.0f}.")


BUILDERS = {
    "sp_week": _b_sp_weekly, "sp_month": _b_sp_monthly, "sp_year": _b_sp_yearly,
    "rcn": _b_rcn, "items_rev": _b_items_rev, "cat": _b_category, "prod": _b_product,
    "top_rev": _b_top_rev, "top_profit": _b_top_profit, "top_pct": _b_top_pct,
    "top_vol": _b_top_vol, "exp": _b_expenses, "proj": _b_projection,
}
STYLE_REPORTS = {"sp_week", "sp_month", "sp_year", "cat", "prod"}
PERIOD_REPORTS = {"top_rev", "top_profit", "top_pct", "top_vol"}


def render_report(key, style="bar", period="month", height=360, show_title=True):
    title, cfg, insight = BUILDERS[key](style, period)
    if show_title:
        st.markdown(f"#### {title}")
    _render(cfg, height=height)
    if insight:
        st.markdown(
            f"<div style='background:#eef2ff;border-left:4px solid #2563eb;border-radius:10px;"
            f"padding:8px 12px;margin-top:6px;font-size:13px;color:#1e3a8a;'>{insight}</div>",
            unsafe_allow_html=True)
