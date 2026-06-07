from datetime import datetime, timedelta
import streamlit as st
from components.database import query_df, today_iso, fmt_date
from components.theme import hero, metric_card
from components.auth import has_access, current_role

ACTION_PILL = {
    "Signed in": "pill-green", "Signed out": "pill-blue",
    "Failed login attempt": "pill-red",
}


def _pill_for(action: str) -> str:
    a = (action or "").lower()
    if "fail" in a or "delete" in a or "cancel" in a:
        return "pill-red"
    if "creat" in a or "sign in" in a or "signed in" in a or "checkout" in a:
        return "pill-green"
    if "updat" in a or "edit" in a or "status" in a or "payment" in a:
        return "pill-blue"
    if "sign" in a or "log out" in a or "signed out" in a:
        return "pill-violet"
    return "pill-blue"


def render():
    hero("Activity Log", "Full audit trail — who signed in, and who created, edited or deleted records.")
    if not has_access("Admin"):
        st.warning("Only Admin can view the activity log.")
        return

    today_str = today_iso()  # ← FIX: local date, not SQLite UTC date('now')

    # Admins may not see the Administrator's (Super Admin) activity; the
    # Administrator sees everything. Applied to every query below.
    restrict_sa = current_role() != "Super Admin"
    sa_clause   = " AND (role IS NULL OR role != 'Super Admin')" if restrict_sa else ""

    total  = query_df(f"SELECT COUNT(*) AS n FROM activity_log WHERE 1=1{sa_clause}")["n"][0]
    today  = query_df(
        f"SELECT COUNT(*) AS n FROM activity_log WHERE date(ts)=?{sa_clause}", (today_str,)
    )["n"][0]
    failed = query_df(
        f"SELECT COUNT(*) AS n FROM activity_log WHERE action='Failed login attempt'{sa_clause}"
    )["n"][0]

    c1, c2, c3 = st.columns(3)
    with c1: metric_card("Total Events", f"{int(total):,}", "All time", "pill-blue")
    with c2: metric_card("Today", f"{int(today):,}", f"Events on {today_str}", "pill-green")
    with c3: metric_card("Failed Logins", f"{int(failed):,}", "All time", "pill-red")

    st.markdown("---")
    users     = query_df(
        "SELECT DISTINCT username FROM activity_log WHERE username IS NOT NULL"
        + sa_clause + " ORDER BY username")
    user_opts = ["All users"] + users["username"].dropna().tolist()

    f1, f2, f3 = st.columns([1, 1, 1.4])
    with f1:
        who    = st.selectbox("Filter by user", user_opts)
    with f2:
        period = st.selectbox("Period", ["Today", "Last 7 days", "Last 30 days", "All time"])
    with f3:
        search = st.text_input("Search action / detail", placeholder="e.g. product, order, sign in")

    where, params = ["1=1"], []
    if who != "All users":
        where.append("username=?"); params.append(who)
    if period == "Today":
        where.append("date(ts)=?"); params.append(today_str)
    elif period == "Last 7 days":
        where.append("date(ts) >= ?")
        params.append((datetime.now().date() - timedelta(days=6)).isoformat())
    elif period == "Last 30 days":
        where.append("date(ts) >= ?")
        params.append((datetime.now().date() - timedelta(days=29)).isoformat())
    if search.strip():
        like = f"%{search.strip().lower()}%"
        where.append("(LOWER(action) LIKE ? OR LOWER(detail) LIKE ? OR LOWER(entity) LIKE ?)")
        params += [like, like, like]
    if restrict_sa:
        where.append("(role IS NULL OR role != 'Super Admin')")

    sql = (
        "SELECT ts, full_name, username, role, action, entity, detail "
        "FROM activity_log WHERE " + " AND ".join(where)
        + " ORDER BY ts DESC LIMIT 500"
    )
    df = query_df(sql, tuple(params))

    if df.empty:
        st.info("No activity recorded for this filter.")
        return

    col_export, _ = st.columns([1, 3])
    with col_export:
        st.download_button(
            "⬇ Export to CSV",
            data=df.to_csv(index=False).encode(),
            file_name="ordro_activity_log.csv",
            mime="text/csv",
            icon=":material/download:",
        )

    st.caption(f"{len(df)} event(s) found")
    st.markdown("### Recent Activity")

    display = df.copy()
    display.columns = ["When", "Name", "Username", "Role", "Action", "Area", "Details"]
    st.dataframe(display, use_container_width=True, hide_index=True, height=520)

    # Per-user summary
    if who == "All users" and not df.empty:
        st.markdown("### Activity by User")
        by_user = query_df(
            "SELECT full_name, username, role, COUNT(*) AS events "
            "FROM activity_log WHERE " + " AND ".join(where)
            + " GROUP BY username ORDER BY events DESC",
            tuple(params),
        )
        if not by_user.empty:
            by_user.columns = ["Name", "Username", "Role", "Events"]
            st.dataframe(by_user, use_container_width=True, hide_index=True)
