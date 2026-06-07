import streamlit as st
from .database import query_df, get_setting, verify_password, execute, hash_password, is_hashed, record_activity
from .theme import logo_data_uri, COLORS

ROLE_ORDER = {"Delivery": 1, "Staff": 2, "Admin": 3, "Super Admin": 4}


def current_role():
    return st.session_state.get("view_role") or st.session_state.get("role")


def has_access(required_role: str) -> bool:
    role = current_role()
    return ROLE_ORDER.get(role, 0) >= ROLE_ORDER.get(required_role, 0)


def login_box():
    business = get_setting("business_name", "Your Business Name")
    accent   = COLORS.get(get_setting("accent_color", "Royal Blue"), "#2563eb")
    logo     = logo_data_uri(get_setting("business_logo", ""))

    if logo:
        logo_html = (
            f'<img src="{logo}" style="width:68px;height:68px;object-fit:cover;'
            f'border-radius:14px;box-shadow:0 4px 14px rgba(0,0,0,.18);flex-shrink:0;">'
        )
    else:
        first = (business[:1] or "O").upper()
        logo_html = (
            f'<div style="width:68px;height:68px;border-radius:14px;background:{accent};'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:28px;font-weight:800;color:#fff;flex-shrink:0;">{first}</div>'
        )

    # ── CSS ───────────────────────────────────────────────────────────────
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [data-testid="stApp"] {{
        font-family:'Inter',system-ui,sans-serif !important;
        background:linear-gradient(145deg,#0f2040 0%,#1a3a6e 45%,#0e2d55 100%) !important;
        min-height:100vh;
    }}

    /* hide chrome */
    header[data-testid="stHeader"],
    [data-testid="stDecoration"],
    [data-testid="stToolbar"],
    section[data-testid="stSidebar"] {{ display:none !important; }}

    /* vertically center main area */
    .main .block-container {{
        padding:0 !important;
        max-width:100% !important;
        min-height:100vh;
        display:flex;
        align-items:center;
        justify-content:center;
    }}
    section[data-testid="stMain"] > div:first-child {{
        width:100%;
    }}

    /* form */
    div[data-testid="stForm"] {{
        border:none !important;padding:0 !important;
        background:transparent !important;box-shadow:none !important;
    }}

    /* inputs */
    div[data-testid="stTextInput"] input {{
        border:1.5px solid #e2e8f0 !important;border-radius:10px !important;
        padding:11px 14px !important;font-size:14px !important;
        font-family:'Inter',system-ui,sans-serif !important;
        background:#f8fafc !important;color:#0f172a !important;
        transition:border-color .2s,box-shadow .2s !important;
    }}
    div[data-testid="stTextInput"] input:focus {{
        border-color:{accent} !important;background:#fff !important;
        box-shadow:0 0 0 3px {accent}22 !important;
    }}
    div[data-testid="stTextInput"] label {{
        font-size:12px !important;font-weight:600 !important;
        color:#374151 !important;font-family:'Inter',system-ui,sans-serif !important;
    }}

    /* submit */
    div[data-testid="stFormSubmitButton"] button {{
        width:100% !important;padding:13px !important;
        background:{accent} !important;color:#fff !important;
        border:none !important;border-radius:12px !important;
        font-size:15px !important;font-weight:700 !important;
        font-family:'Inter',system-ui,sans-serif !important;
        cursor:pointer !important;transition:opacity .15s,transform .12s !important;
    }}
    div[data-testid="stFormSubmitButton"] button:hover {{
        opacity:.9 !important;transform:translateY(-1px) !important;
    }}

    /* remove default column gap / padding */
    [data-testid="column"] {{ padding:0 !important; }}

    /* Tighten gap between form fields (username → password) */
    div[data-testid="stForm"] [data-testid="stVerticalBlock"] > div {{
        gap:6px !important;
    }}
    div[data-testid="stForm"] [data-testid="stVerticalBlockBorderWrapper"] > div > div {{
        gap:6px !important;
    }}
    /* Reduce label bottom margin */
    div[data-testid="stTextInput"] label {{
        margin-bottom:2px !important;
    }}

    /* alerts */
    div[data-testid="stAlert"] {{
        border-radius:10px !important;
        font-family:'Inter',system-ui,sans-serif !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── Centered single column containing brand + form ─────────────────────
    _, col, _ = st.columns([1, 1.05, 1])
    with col:
        # Brand card (top section only — no centering wrapper)
        st.markdown(f"""
        <div style="background:#fff;border-radius:22px 22px 0 0;overflow:hidden;
                    box-shadow:0 8px 32px rgba(0,0,0,.28);border:1px solid rgba(255,255,255,.12);
                    border-bottom:none;">
            <div style="height:5px;background:linear-gradient(90deg,{accent},{accent}88);"></div>
            <div style="padding:28px 32px 20px;">
                <div style="display:flex;align-items:center;gap:14px;margin-bottom:18px;">
                    {logo_html}
                    <div>
                        <div style="font-size:17px;font-weight:800;color:#0f172a;
                                    letter-spacing:-.02em;line-height:1.2;">{business}</div>
                        <div style="font-size:10px;font-weight:700;letter-spacing:.14em;
                                    text-transform:uppercase;color:{accent};margin-top:2px;">
                            ORDRO · Management System</div>
                    </div>
                </div>
                <div style="font-size:20px;font-weight:800;color:#0f172a;
                            letter-spacing:-.03em;margin-bottom:2px;">Welcome back</div>
                <div style="font-size:13px;color:#64748b;line-height:1.4;margin-bottom:0;">
                    Sign in to manage your business</div>
            </div>
        </div>
        <div style="background:#fff;border-radius:0 0 22px 22px;
                    box-shadow:0 8px 32px rgba(0,0,0,.28);border:1px solid rgba(255,255,255,.12);
                    border-top:1px solid #f1f5f9;padding:20px 32px 24px;">
        """, unsafe_allow_html=True)

        # Streamlit form inside the white card bottom section
        with st.form("login_form", border=False):
            username  = st.text_input("Username", placeholder="Enter your username")
            password  = st.text_input("Password", type="password",
                                      placeholder="Enter your password")
            submitted = st.form_submit_button(
                "Sign In →", use_container_width=True, type="primary")

            if submitted:
                user = query_df(
                    "SELECT * FROM users WHERE username=? AND active=1",
                    (username.strip(),),
                )
                if user.empty or not verify_password(user.iloc[0]["password"], password):
                    st.error("Invalid username or password.")
                    record_activity(
                        username.strip() or "unknown", "", "", "Failed login attempt"
                    )
                else:
                    row = user.iloc[0]
                    if not is_hashed(row["password"]):
                        execute(
                            "UPDATE users SET password=? WHERE id=?",
                            (hash_password(password), int(row["id"])),
                        )
                    st.session_state.logged_in = True
                    st.session_state.username  = row["username"]
                    st.session_state.role      = row["role"]
                    st.session_state.view_role = row["role"]
                    st.session_state.full_name = row["full_name"]
                    record_activity(
                        row["username"], row["full_name"], row["role"], "Signed in"
                    )
                    st.rerun()

        st.markdown(
            "<div style='text-align:center;font-size:11px;color:#94a3b8;"
            "padding:8px 0 0;'>Powered by ORDRO · Secure login</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)


def logout_button():
    if st.sidebar.button("Log out", use_container_width=True, icon=":material/logout:"):
        record_activity(
            st.session_state.get("username", "system"),
            st.session_state.get("full_name", ""),
            st.session_state.get("role", ""),
            "Signed out",
        )
        for key in ["logged_in", "username", "role", "view_role", "full_name", "cart", "page"]:
            st.session_state.pop(key, None)
        st.rerun()
