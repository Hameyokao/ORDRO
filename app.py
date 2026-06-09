import streamlit as st
import streamlit.components.v1 as components
from components.database import init_db, get_setting
from components.theme import apply_theme, logo_data_uri
from components.auth import login_box, logout_button, has_access, current_role
from components.icons import NAV_ICONS
from pages_app import (
    dashboard, pos, inventory, customers, suppliers, delivery, reports,
    settings, expenses, orders, completed_deliveries, activity_log,
)

st.set_page_config(page_title="ORDRO", page_icon="◆", layout="wide", initial_sidebar_state="auto")
init_db()
apply_theme()

if not st.session_state.get("logged_in"):
    login_box()
    st.stop()

real_role     = st.session_state.get("role", "Delivery")
role          = current_role()
full_name     = st.session_state.get("full_name", "User")
business_name = get_setting("business_name", "Your Business")
logo          = logo_data_uri(get_setting("business_logo", ""))
logo_html     = f'<img class="sidebar-logo" src="{logo}">' if logo else '<div class="sidebar-logo-placeholder">O</div>'

st.sidebar.markdown(f"""
<div class="sidebar-brand">
    <div style="display:flex;align-items:center;gap:10px;">
        {logo_html}
        <div>
            <div class="brand-name">{business_name}</div>
            <div class="app-small">ORDRO</div>
        </div>
    </div>
    <div style="margin-top:10px;font-size:13px;">
        <span style="font-weight:600;">{full_name}</span>
        <span class="muted" style="display:block;font-size:11px;margin-top:2px;">{real_role}{' · viewing as ' + role if role != real_role else ''}</span>
    </div>
</div>
""", unsafe_allow_html=True)

if real_role in ("Admin", "Super Admin"):
    view_opts = ["Super Admin", "Admin", "Staff", "Delivery"] if real_role == "Super Admin" else ["Admin", "Staff", "Delivery"]
    selected_view = st.sidebar.selectbox(
        "Role view",
        view_opts,
        index=view_opts.index(role) if role in view_opts else 0,
        label_visibility="collapsed",
    )
    if selected_view != st.session_state.get("view_role"):
        st.session_state.view_role = selected_view
        st.session_state.page = None
        st.rerun()

# Delivery role sees only their 3 pages — no other business data exposed
if role == "Delivery" and real_role not in ("Admin", "Super Admin"):
    # Delivery users can ONLY see their dashboard and the two delivery pages.
    menu = ["Dashboard", "Pending Deliveries", "Completed Orders"]
else:
    menu = ["Dashboard"]
    if has_access("Staff"):
        menu += ["Point of Sale", "Inventory", "Pending Orders"]
    if has_access("Delivery"):
        menu += ["Pending Deliveries", "Completed Orders"]
    if has_access("Staff"):
        menu += ["Expenses", "Reports", "Customers", "Suppliers"]
    if real_role in ("Admin", "Super Admin") and role in ("Admin", "Super Admin"):
        menu += ["Activity Log", "Settings"]
    seen = set()
    menu = [x for x in menu if not (x in seen or seen.add(x))]

if "page" not in st.session_state or st.session_state.page not in menu:
    st.session_state.page = menu[0]

st.sidebar.markdown(
    "<div class='muted' style='font-size:10px;font-weight:700;letter-spacing:.12em;"
    "text-transform:uppercase;padding:10px 2px 4px;'>NAVIGATION</div>",
    unsafe_allow_html=True,
)
for item in menu:
    is_active = item == st.session_state.page
    if st.sidebar.button(
        item,
        key=f"nav_{item}",
        use_container_width=True,
        icon=NAV_ICONS.get(item),
        type="primary" if is_active else "secondary",
    ):
        st.session_state.page = item
        st.rerun()

st.sidebar.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
logout_button()

choice = st.session_state.page
if   choice == "Dashboard":             dashboard.render()
elif choice == "Point of Sale":         pos.render()
elif choice == "Inventory":             inventory.render()
elif choice == "Customers":             customers.render()
elif choice == "Suppliers":             suppliers.render()
elif choice == "Pending Deliveries":    delivery.render()
elif choice == "Completed Orders":      completed_deliveries.render()
elif choice == "Reports":               reports.render()
elif choice == "Expenses":              expenses.render()
elif choice == "Pending Orders":        orders.render()
elif choice == "Activity Log":          activity_log.render()
elif choice == "Settings":              settings.render()# ── Mobile menu auto-hide (installed into the MAIN page so it survives reloads) ─
# A throw-away component frame gets deleted by Streamlit on every rerun, which
# would kill any listener bound inside it. So instead we inject a small script
# into the top page document itself, bound exactly once. On phones (< 768px) the
# side menu closes the instant any menu button is tapped and starts closed after
# sign-in. Desktop is never touched. Applies to every signed-in user & role.
components.html(
    """
    <script>
    (function () {
        var root = window.parent;
        if (!root || root.__ordroBootstrapped) return;
        root.__ordroBootstrapped = true;
        function ordroSetup() {
            if (window.__ordroNavBound) return;
            window.__ordroNavBound = true;
            var doc = document;
            function mobile() { return (window.innerWidth || 0) < 768; }
            function sidebar() { return doc.querySelector('section[data-testid="stSidebar"]'); }
            function isOpen() {
                var sb = sidebar();
                if (!sb) return false;
                var ae = sb.getAttribute('aria-expanded');
                if (ae === 'true') return true;
                if (ae === 'false') return false;
                var r = sb.getBoundingClientRect();
                return r.width > 100 && r.right > 0;
            }
            function clickCollapse() {
                var sels = [
                    'div[data-testid="stSidebarCollapseButton"] button',
                    'button[data-testid="stSidebarCollapseButton"]',
                    'div[data-testid="stSidebarHeader"] button',
                    'button[aria-label="Close sidebar"]',
                    'button[aria-label="Collapse sidebar"]',
                    'button[kind="headerNoPadding"]'
                ];
                for (var i = 0; i < sels.length; i++) {
                    var el = doc.querySelector(sels[i]);
                    if (el) { el.click(); return true; }
                }
                return false;
            }
            function closeNow() { if (mobile() && isOpen()) clickCollapse(); }
            doc.addEventListener('click', function (e) {
                if (!mobile()) return;
                var sb = sidebar();
                if (!sb || !sb.contains(e.target)) return;
                var btn = e.target.closest('button');
                if (!btn) return;
                if (btn.closest('[data-testid="stSidebarCollapseButton"]')) return;
                setTimeout(closeNow, 0);
            }, true);
            var tries = 0;
            function initClose() {
                if (!mobile()) return;
                var sb = sidebar();
                if (!sb) { if (tries++ < 30) setTimeout(initClose, 100); return; }
                if (isOpen()) closeNow();
            }
            setTimeout(initClose, 150);
        }
        var s = root.document.createElement("script");
        s.textContent = "(" + ordroSetup.toString() + ")();";
        root.document.body.appendChild(s);
    })();
    </script>
    """,
    height=0, width=0,
)
