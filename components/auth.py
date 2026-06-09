import streamlit as st
import streamlit.components.v1 as components
# ORDRO v13 — neomorphic login
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

    # The logo tile shows the uploaded image from Settings if present,
    # otherwise it falls back to the first letter of the business name.
    if logo:
        logo_html = (
            f'<img src="{logo}" style="width:72px;height:72px;object-fit:cover;'
            f'border-radius:32px;flex-shrink:0;'
            f'box-shadow:inset 2px 2px 5px #b8c0ce, inset -3px -3px 7px #ffffff;">'
        )
    else:
        first = (business[:1] or "O").upper()
        logo_html = (
            f'<div style="width:72px;height:72px;border-radius:32px;background:#e0e5ec;'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:2.2rem;font-weight:800;color:#1e3a5f;flex-shrink:0;'
            f'box-shadow:inset 2px 2px 5px #b8c0ce, inset -3px -3px 7px #ffffff;">{first}</div>'
        )

    # -- Neomorphic CSS ------------------------------------------------------
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [data-testid="stApp"], .stApp {
        font-family:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif !important;
        background:#eef2f9 !important;
        min-height:100vh;
    }

    /* hide chrome */
    header[data-testid="stHeader"],
    [data-testid="stDecoration"],
    [data-testid="stToolbar"],
    section[data-testid="stSidebar"] { display:none !important; }

    /* vertically center main area */
    .main .block-container, .block-container {
        padding:2rem 1rem !important;
        max-width:100% !important;
        min-height:100vh;
        display:flex;
        align-items:center;
        justify-content:center;
    }
    section[data-testid="stMain"] > div:first-child { width:100%; }
    [data-testid="column"] { padding:0 !important; }

    /* -- The form IS the neomorphic card -- */
    div[data-testid="stForm"] {
        background:#e0e5ec !important;
        border:none !important;
        border-radius:48px !important;
        padding:2.5rem 2.2rem 2rem !important;
        box-shadow:9px 9px 16px #a3b1c6, -9px -9px 16px #ffffff !important;
        max-width:500px !important;
        margin:0 auto !important;
    }

    /* neomorphic inputs — single clean inset pill (outer wrapper only) */
    div[data-testid="stTextInput"] div[data-baseweb="input"] {
        border:none !important;
        border-radius:60px !important;
        background:#e0e5ec !important;
        box-shadow:inset 4px 4px 8px #b8c0ce, inset -4px -4px 8px #ffffff !important;
        padding:0 !important;
        overflow:hidden !important;
        position:relative !important;
        min-height:0 !important;
    }
    /* inner wrapper stays a transparent pass-through (no second shadow/border) */
    div[data-testid="stTextInput"] div[data-baseweb="base-input"] {
        border:none !important;
        background:transparent !important;
        box-shadow:none !important;
        padding:0 !important;
    }
    div[data-testid="stTextInput"] input {
        border:none !important;
        background:transparent !important;
        box-shadow:none !important;
        padding:0.9rem 1.2rem !important;
        font-size:0.95rem !important;
        line-height:1.2 !important;
        font-family:'Inter',system-ui,sans-serif !important;
        color:#1e2a3a !important;
    }
    div[data-testid="stTextInput"] input::placeholder { color:#8a99b0 !important; }
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
        box-shadow:inset 5px 5px 10px #b0b8c8, inset -5px -5px 10px #ffffff !important;
    }
    /* hide Streamlit's native password reveal — replaced by neomorphic pill */
    div[data-testid="stTextInput"] button { display:none !important; }
    div[data-testid="stTextInput"] label {
        font-size:0.8rem !important;
        font-weight:600 !important;
        color:#2d3748 !important;
        padding-left:0.5rem !important;
        margin-bottom:0.4rem !important;
        font-family:'Inter',system-ui,sans-serif !important;
    }
    div[data-testid="stTextInput"] { margin-bottom:0.4rem !important; }

    /* neomorphic Show/Hide password pill */
    .ordro-pw-pill {
        position:absolute; right:10px; top:50%; transform:translateY(-50%);
        display:flex; align-items:center; gap:0.3rem;
        background:#e0e5ec; padding:0.25rem 0.65rem; border-radius:30px;
        cursor:pointer; font-size:0.7rem; font-weight:600; color:#4a5b7a;
        user-select:none; z-index:20; font-family:'Inter',system-ui,sans-serif;
        box-shadow:inset 1px 1px 2px #b8c0ce, inset -1px -1px 2px #ffffff;
    }

    /* neomorphic submit button */
    div[data-testid="stFormSubmitButton"] button {
        width:100% !important;
        padding:0.9rem !important;
        background:#2c3e66 !important;
        color:#fff !important;
        border:none !important;
        border-radius:60px !important;
        font-size:0.95rem !important;
        font-weight:600 !important;
        font-family:'Inter',system-ui,sans-serif !important;
        box-shadow:4px 4px 8px #b8c0ce, -2px -2px 6px #ffffff !important;
        cursor:pointer !important;
        margin-top:0.8rem !important;
        transition:all .1s !important;
        display:block !important;
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        background:#324573 !important;
    }
    div[data-testid="stFormSubmitButton"] button:active {
        transform:scale(0.98) !important;
        box-shadow:inset 2px 2px 4px #1f2c48, inset -1px -1px 3px #395084 !important;
    }

    /* tighten field spacing inside the card */
    div[data-testid="stForm"] [data-testid="stVerticalBlock"] > div { gap:0.4rem !important; }

    /* alerts */
    div[data-testid="stAlert"] {
        border-radius:18px !important;
        font-family:'Inter',system-ui,sans-serif !important;
        box-shadow:inset 2px 2px 5px #b8c0ce, inset -2px -2px 5px #ffffff !important;
        background:#e0e5ec !important;
        border:none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # -- Centered single column holding the neomorphic card -----------------
    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        # Everything lives INSIDE the form so the neomorphic card wraps it all
        with st.form("login_form", border=False):
            # Business header: logo left, name + crimson "ordro app" wordmark right
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:1.2rem;margin-bottom:2rem;">
                {logo_html}
                <div style="display:flex;flex-direction:column;gap:0.2rem;">
                    <div style="font-weight:800;font-size:1.9rem;letter-spacing:-0.5px;
                                color:#1e2a3a;line-height:1.1;">{business}</div>
                    <div style="font-weight:800;font-size:1.1rem;color:#dc143c;
                                letter-spacing:-0.2px;">ordro app</div>
                </div>
            </div>
            <div style="margin-bottom:1.4rem;">
                <div style="font-size:1.4rem;font-weight:700;color:#1e2a3a;
                            margin-bottom:0.4rem;">Welcome back</div>
                <div style="font-size:0.85rem;color:#5a6e8a;">Sign in to manage your business</div>
            </div>
            """, unsafe_allow_html=True)

            username  = st.text_input("Username", placeholder="Enter your username")
            password  = st.text_input("Password", type="password",
                                      placeholder="Enter your password")
            submitted = st.form_submit_button(
                "Sign In  →", use_container_width=True, type="primary")

            # Status badge + footer
            st.markdown("""
            <div style="text-align:center;">
                <div style="display:inline-flex;align-items:center;gap:0.4rem;
                            padding:0.4rem 0.9rem;background:#e0e5ec;
                            box-shadow:inset 2px 2px 4px #b8c0ce, inset -2px -2px 4px #ffffff;
                            border-radius:20px;font-size:0.7rem;color:#2d5a3d;
                            margin-top:1.2rem;font-weight:500;">
                    <span style="width:8px;height:8px;background:#48bb78;border-radius:50%;
                                 box-shadow:0 0 6px rgba(72,187,120,0.6);"></span>
                    <span>System online</span>
                </div>
            </div>
            <div style="text-align:center;margin-top:1.6rem;font-size:0.7rem;
                        font-weight:500;color:#5a6e8a;letter-spacing:0.3px;">
                Powered by ORDRO &middot; Secure login</div>
            """, unsafe_allow_html=True)

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

    # -- Inject the neomorphic Show/Hide pill into the password field --------
    components.html(
        """
        <script>
        (function () {
            var pdoc = window.parent.document;
            function init(tries) {
                tries = tries || 0;
                var inputs = pdoc.querySelectorAll(
                    'div[data-testid="stForm"] div[data-testid="stTextInput"]');
                if (inputs.length < 2) {
                    if (tries < 40) setTimeout(function(){ init(tries+1); }, 120);
                    return;
                }
                var pwWrap = inputs[1];
                if (pwWrap.querySelector('.ordro-pw-pill')) return;
                var input = pwWrap.querySelector('input');
                if (!input) {
                    if (tries < 40) setTimeout(function(){ init(tries+1); }, 120);
                    return;
                }
                var box = pwWrap.querySelector('div[data-baseweb="input"]')
                          || input.parentElement;
                box.style.position = 'relative';
                input.style.paddingRight = '4.6rem';
                var pill = pdoc.createElement('div');
                pill.className = 'ordro-pw-pill';
                pill.innerHTML = '<span>Show</span>';
                pill.addEventListener('click', function () {
                    if (input.type === 'password') {
                        input.type = 'text';
                        pill.innerHTML = '<span>Hide</span>';
                    } else {
                        input.type = 'password';
                        pill.innerHTML = '<span>Show</span>';
                    }
                });
                box.appendChild(pill);
            }
            init(0);
        })();
        </script>
        """,
        height=0, width=0,
    )


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
