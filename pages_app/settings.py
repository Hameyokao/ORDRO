from datetime import datetime
import sqlite3
import streamlit as st
from components.database import query_df, execute, get_setting, set_setting, UPLOAD_DIR, hash_password
from components.theme import hero, THEMES, COLORS, BANNER_THEMES
from components.auth import has_access
from components.activity import log


def save_logo(uploaded):
    if not uploaded:
        return get_setting("business_logo", "")
    safe = f"logo_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded.name}".replace(" ", "_")
    path = UPLOAD_DIR / safe
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    return safe


def _section(title):
    st.markdown(f"### {title}")


def render():
    hero("Settings", "Business details, branding, theme, contact info, and user management.")
    if not has_access("Admin"):
        st.warning("Only Admin can access settings.")
        return

    current_user_role = st.session_state.get("role", "")
    is_super_admin    = current_user_role == "Super Admin"

    # ─── Business branding ───────────────────────────────────────────────
    with st.container(border=True):
        _section("Business Branding")
        with st.form("branding_form"):
            c1, c2 = st.columns(2)
            business_name = c1.text_input(
                "Shop / Business Name",
                value=get_setting("business_name", "Your Business Name"),
            )
            currency = c2.text_input("Currency Symbol", value=get_setting("currency", "MVR"))
            c3, c4 = st.columns(2)
            tax = c3.number_input(
                "Tax Percent (%)", min_value=0.0, max_value=100.0,
                value=float(get_setting("tax_percent", "0") or 0), step=0.5,
            )
            logo = c4.file_uploader("Business Logo / Icon", type=["png", "jpg", "jpeg", "webp"])
            if st.form_submit_button("Save Branding", type="primary", icon=":material/save:"):
                set_setting("business_name", business_name or "Your Business Name")
                set_setting("currency", currency or "MVR")
                set_setting("tax_percent", str(tax))
                if logo:
                    set_setting("business_logo", save_logo(logo))
                log("Updated branding", entity="settings", detail=business_name)
                st.success("Branding saved.")
                st.rerun()

    # ─── Contact details ─────────────────────────────────────────────────
    with st.container(border=True):
        _section("Business Contact Details")
        st.caption("These appear on payment slips and receipts.")
        with st.form("contact_form"):
            c1, c2 = st.columns(2)
            biz_address = c1.text_input("Business Address", value=get_setting("business_address", ""))
            biz_phone   = c2.text_input("Phone / Contact Number", value=get_setting("business_phone", ""))
            c3, c4 = st.columns(2)
            biz_email   = c3.text_input("Email Address", value=get_setting("business_email", ""))
            biz_website = c4.text_input("Website URL", value=get_setting("business_website", ""))

            st.caption("Social Media & Messaging (shown at bottom of receipts)")
            r1c1, r1c2, r1c3 = st.columns(3)
            fb_id    = r1c1.text_input("Facebook Page ID / Username", value=get_setting("facebook_id", ""))
            ig_id    = r1c2.text_input("Instagram Username", value=get_setting("instagram_id", ""))
            tt_id    = r1c3.text_input("TikTok Username", value=get_setting("tiktok_id", ""))
            r2c1, r2c2 = st.columns(2)
            wa_no    = r2c1.text_input("WhatsApp Number", value=get_setting("whatsapp_contact", ""))
            viber_no = r2c2.text_input("Viber Number", value=get_setting("viber_contact", ""))

            if st.form_submit_button("Save Contact Details", type="primary", icon=":material/save:"):
                set_setting("business_address",  biz_address)
                set_setting("business_phone",    biz_phone)
                set_setting("business_email",    biz_email)
                set_setting("business_website",  biz_website)
                set_setting("facebook_id",       fb_id)
                set_setting("instagram_id",      ig_id)
                set_setting("tiktok_id",         tt_id)
                set_setting("whatsapp_contact",  wa_no)
                set_setting("viber_contact",     viber_no)
                log("Updated contact details", entity="settings")
                st.success("Contact details saved.")

    # ─── Theme ───────────────────────────────────────────────────────────
    with st.container(border=True):
        _section("Theme, Colour & Banner")
        with st.form("theme_form"):
            ui_style_opts = ["Classic", "Neomorphic Soft"]
            cur_ui_style = get_setting("ui_style", "Classic")
            ui_style = st.selectbox(
                "App Style",
                ui_style_opts,
                index=ui_style_opts.index(cur_ui_style) if cur_ui_style in ui_style_opts else 0,
                help="Neomorphic Soft applies a soft, light 3D look across the whole app. "
                     "It uses your Accent Colour; background themes and dark modes are "
                     "overridden while it is active.",
            )
            c1, c2, c3 = st.columns(3)
            theme_name = c1.selectbox(
                "App Background Theme", list(THEMES.keys()),
                index=list(THEMES.keys()).index(get_setting("theme_name", "Cloud White"))
                if get_setting("theme_name", "Cloud White") in THEMES else 0,
            )
            accent_color = c2.selectbox(
                "Accent Colour", list(COLORS.keys()),
                index=list(COLORS.keys()).index(get_setting("accent_color", "Royal Blue"))
                if get_setting("accent_color", "Royal Blue") in COLORS else 0,
            )
            banner_theme = c3.selectbox(
                "Banner Style", list(BANNER_THEMES.keys()),
                index=list(BANNER_THEMES.keys()).index(get_setting("banner_theme", "Corner Glow"))
                if get_setting("banner_theme", "Corner Glow") in BANNER_THEMES else 0,
            )
            st.markdown(
                f"<div class='soft-card' style='padding:10px 14px;'>"
                f"<b>Preview</b> · "
                f"<span class='pill pill-blue'>{theme_name}</span> "
                f"<span class='pill pill-green'>{accent_color}</span> "
                f"<span class='pill pill-violet'>{banner_theme}</span></div>",
                unsafe_allow_html=True,
            )
            if st.form_submit_button("Apply Design", type="primary", icon=":material/palette:"):
                set_setting("ui_style",     ui_style)
                set_setting("theme_name",   theme_name)
                set_setting("accent_color", accent_color)
                set_setting("banner_theme", banner_theme)
                log("Updated theme", entity="settings",
                    detail=f"{ui_style} / {theme_name} / {accent_color}")
                st.success("Theme updated.")
                st.rerun()

    # ─── Create user ─────────────────────────────────────────────────────
    with st.container(border=True):
        _section("Create New User")
        # Only Super Admin can create Admin users
        if is_super_admin:
            role_choices = ["Admin", "Staff", "Delivery"]
        else:
            role_choices = ["Staff", "Delivery"]
        with st.form("create_user_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            full_name = c1.text_input("Full Name")
            username  = c2.text_input("Username")
            c3, c4 = st.columns(2)
            password  = c3.text_input("Password", type="password")
            role      = c4.selectbox("Role", role_choices)
            if st.form_submit_button("Create User", type="primary", icon=":material/person_add:"):
                if not full_name or not username or not password:
                    st.error("Full name, username, and password are all required.")
                elif username.strip() == "Administrator":
                    st.error("The username 'Administrator' is reserved for Super Admin.")
                else:
                    try:
                        uid = execute(
                            "INSERT INTO users (username,password,role,full_name,active) VALUES (?,?,?,?,1)",
                            (username.strip(), hash_password(password), role, full_name.strip()),
                        )
                        log("Created user", entity="user", entity_id=uid,
                            detail=f"{full_name.strip()} ({role})")
                        st.success(f"User '{username.strip()}' created as {role}.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Username already exists. Choose a different username.")

    # ─── User management ─────────────────────────────────────────────────
    with st.container(border=True):
        _section("User Management")
        users = query_df(
            "SELECT id, username, role, full_name, active FROM users "
            "ORDER BY CASE role WHEN 'Super Admin' THEN 0 WHEN 'Admin' THEN 1 WHEN 'Staff' THEN 2 ELSE 3 END, full_name"
        )
        st.caption(f"{len(users)} user(s) registered")
        cols = st.columns(3)
        for i, r in users.iterrows():
            with cols[i % 3]:
                with st.container(border=True):
                    is_sa_row    = r["role"] == "Super Admin"
                    active_label = "Active" if int(r["active"]) else "Inactive"
                    a_pill   = "pill-green" if int(r["active"]) else "pill-red"
                    role_pill = {
                        "Super Admin": "pill-violet",
                        "Admin": "pill-red",
                        "Staff": "pill-blue",
                        "Delivery": "pill-orange",
                    }.get(r["role"], "pill-gray")
                    crown = "👑 " if is_sa_row else ""
                    st.markdown(f"#### :material/account_circle: {crown}{r['full_name']}")
                    st.markdown(
                        f"<span class='pill {role_pill}'>{r['role']}</span> "
                        f"<span class='pill {a_pill}'>{active_label}</span>",
                        unsafe_allow_html=True,
                    )
                    st.caption(f"@{r['username']}")

                    # ── Administrator (Super Admin) row — name + password only ──
                    if is_sa_row:
                        if is_super_admin:
                            with st.expander("Edit Administrator"):
                                sa_name = st.text_input(
                                    "Full Name", value=r["full_name"] or "",
                                    key=f"saname_{r['id']}")
                                sa_pw = st.text_input(
                                    "New Password (leave blank to keep)", value="",
                                    type="password", key=f"sapw_{r['id']}")
                                if st.button("Save", key=f"sasv_{r['id']}", type="primary",
                                             icon=":material/save:"):
                                    execute("UPDATE users SET full_name=? WHERE id=?",
                                            (sa_name.strip() or r["full_name"], int(r["id"])))
                                    if sa_pw:
                                        execute("UPDATE users SET password=? WHERE id=?",
                                                (hash_password(sa_pw), int(r["id"])))
                                    log("Updated Administrator account", entity="user",
                                        entity_id=int(r["id"]))
                                    st.success("Administrator updated.")
                                    st.rerun()
                                st.caption("The Administrator username is reserved and cannot be changed.")
                        else:
                            st.caption("Only the Administrator can edit this account.")

                    # ── Other users — editable by Admin / Administrator ──
                    else:
                        # A regular Admin manages Staff & Delivery only;
                        # Admin accounts are managed by the Administrator alone.
                        can_edit = is_super_admin or (r["role"] not in ("Admin", "Super Admin"))
                        if not can_edit:
                            st.caption("Only the Administrator can edit Admin accounts.")
                        else:
                            is_self   = r["username"] == st.session_state.get("username")
                            role_opts = (["Admin", "Staff", "Delivery"] if is_super_admin
                                         else ["Staff", "Delivery"])
                            with st.expander("Edit user"):
                                e_name = st.text_input(
                                    "Full Name", value=r["full_name"] or "",
                                    key=f"uname_{r['id']}")
                                e_user = st.text_input(
                                    "Username", value=r["username"] or "",
                                    key=f"uuser_{r['id']}")
                                e_pw = st.text_input(
                                    "New Password (leave blank to keep)", value="",
                                    type="password", key=f"upw_{r['id']}")
                                cur_role = r["role"] if r["role"] in role_opts else role_opts[-1]
                                e_role = st.selectbox(
                                    "Role", role_opts, index=role_opts.index(cur_role),
                                    key=f"urole_{r['id']}")
                                e_active = st.checkbox(
                                    "Active", value=bool(int(r["active"])),
                                    key=f"uact_{r['id']}", disabled=is_self)
                                if is_self:
                                    st.caption("You cannot deactivate or delete your own account.")
                                cc1, cc2 = st.columns(2)
                                if cc1.button("Save", key=f"usv_{r['id']}", type="primary",
                                              icon=":material/save:"):
                                    new_user = e_user.strip()
                                    if not new_user or not e_name.strip():
                                        st.error("Full name and username are required.")
                                    elif new_user == "Administrator":
                                        st.error("The username 'Administrator' is reserved.")
                                    else:
                                        try:
                                            execute(
                                                "UPDATE users SET full_name=?, username=?, role=?, active=? "
                                                "WHERE id=?",
                                                (e_name.strip(), new_user, e_role,
                                                 1 if (e_active or is_self) else 0, int(r["id"])))
                                            if e_pw:
                                                execute("UPDATE users SET password=? WHERE id=?",
                                                        (hash_password(e_pw), int(r["id"])))
                                            log("Updated user", entity="user",
                                                entity_id=int(r["id"]),
                                                detail=f"{e_name.strip()} ({e_role})")
                                            st.success("User updated.")
                                            st.rerun()
                                        except sqlite3.IntegrityError:
                                            st.error("That username is already taken.")
                                confirm_del = cc2.checkbox(
                                    "Confirm delete", key=f"udelchk_{r['id']}",
                                    disabled=is_self)
                                if st.button("Delete user", key=f"udel_{r['id']}",
                                             icon=":material/delete:",
                                             disabled=is_self or not confirm_del):
                                    execute("DELETE FROM users WHERE id=?", (int(r["id"]),))
                                    log("Deleted user", entity="user", entity_id=int(r["id"]),
                                        detail=f"{r['full_name']} ({r['role']})")
                                    st.success("User deleted.")
                                    st.rerun()
