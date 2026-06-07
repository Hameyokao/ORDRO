from datetime import datetime
import streamlit as st
from components.database import query_df, execute
from components.theme import hero
from components.auth import has_access
from components.activity import log


def render():
    hero("Suppliers", "Keep vendor contacts in one place and link them to the products you buy.")
    if not has_access("Staff"):
        st.warning("Only Staff and Admin can manage suppliers.")
        return

    with st.expander("Add supplier", expanded=False):
        with st.form("supplier_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Supplier / company name")
            contact = c2.text_input("Contact person")
            c3, c4 = st.columns(2)
            phone = c3.text_input("Phone")
            email = c4.text_input("Email")
            address = st.text_area("Address")
            notes = st.text_area("Notes")
            if st.form_submit_button("Save supplier", type="primary", icon=":material/add:"):
                if not name.strip():
                    st.error("Supplier name is required.")
                else:
                    sid = execute(
                        "INSERT INTO suppliers (name,contact_person,phone,email,address,notes,created_at) VALUES (?,?,?,?,?,?,?)",
                        (name.strip(), contact.strip(), phone.strip(), email.strip(), address.strip(), notes.strip(),
                         datetime.now().isoformat()),
                    )
                    log("Created supplier", entity="supplier", entity_id=sid, detail=name.strip())
                    st.success("Supplier saved.")
                    st.rerun()

    suppliers = query_df("SELECT * FROM suppliers ORDER BY name")
    st.markdown("### Supplier directory")
    if suppliers.empty:
        st.info("No suppliers yet.")
        return

    cols = st.columns(3)
    for i, r in suppliers.iterrows():
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"#### :material/local_shipping: {r['name']}")
                if r.get('contact_person'):
                    st.caption(f"Contact: {r['contact_person']}")
                st.write(f"**Phone:** {r.get('phone') or '-'}")
                st.write(f"**Email:** {r.get('email') or '-'}")
                if r.get('address'):
                    st.write(f"**Address:** {r['address']}")
                if r.get('notes'):
                    st.caption(r['notes'])

                linked = query_df("SELECT COUNT(*) AS n FROM products WHERE supplier_id=? AND active=1", (int(r['id']),))['n'][0]
                st.caption(f"Linked products: {int(linked)}")

                if has_access("Admin"):
                    with st.expander("Edit supplier"):
                        nm = st.text_input("Name", r['name'], key=f"sn_{r['id']}")
                        cp = st.text_input("Contact person", r.get('contact_person') or '', key=f"scp_{r['id']}")
                        ph = st.text_input("Phone", r.get('phone') or '', key=f"sph_{r['id']}")
                        em = st.text_input("Email", r.get('email') or '', key=f"sem_{r['id']}")
                        ad = st.text_area("Address", r.get('address') or '', key=f"sad_{r['id']}")
                        nt = st.text_area("Notes", r.get('notes') or '', key=f"snt_{r['id']}")
                        cc1, cc2 = st.columns(2)
                        if cc1.button("Save", key=f"ssave_{r['id']}", type="primary", icon=":material/save:"):
                            execute(
                                "UPDATE suppliers SET name=?, contact_person=?, phone=?, email=?, address=?, notes=? WHERE id=?",
                                (nm, cp, ph, em, ad, nt, int(r['id'])),
                            )
                            log("Updated supplier", entity="supplier", entity_id=int(r['id']), detail=nm)
                            st.success("Supplier updated.")
                            st.rerun()
                        if cc2.button("Delete", key=f"sdel_{r['id']}", icon=":material/delete:"):
                            execute("UPDATE products SET supplier_id=NULL WHERE supplier_id=?", (int(r['id']),))
                            execute("DELETE FROM suppliers WHERE id=?", (int(r['id']),))
                            log("Deleted supplier", entity="supplier", entity_id=int(r['id']), detail=r['name'])
                            st.success("Supplier deleted.")
                            st.rerun()
