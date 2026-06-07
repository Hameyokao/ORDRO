from datetime import datetime
import streamlit as st
from components.database import query_df, execute, get_setting
from components.theme import hero, metric_card
from components.auth import has_access
from components.activity import log

EXPENSE_CATEGORIES = [
    "Shipping costs", "Ad expenses", "Salaries", "Delivery expenses", "Phone bills", "Electricity Bills",
    "Internet bills", "Rent", "Packaging", "Fuel", "Maintenance", "Bank charges", "Office supplies", "Other expenses"
]


def render():
    hero("Expenses", "Track shipping, ads, salaries, bills and other costs — flag recurring monthly expenses.")
    if not has_access("Staff"):
        st.warning("Only Staff and Admin can add expenses.")
        return
    currency = get_setting("currency", "MVR")
    total = query_df("SELECT COALESCE(SUM(amount),0) AS total FROM expenses")['total'][0]
    today = query_df("SELECT COALESCE(SUM(amount),0) AS total FROM expenses WHERE date(date)=date('now')")['total'][0]
    recurring = query_df("SELECT COALESCE(SUM(amount),0) AS total FROM expenses WHERE recurring=1")['total'][0]
    c1, c2, c3 = st.columns(3)
    with c1: metric_card("Total expenses", f"{currency} {float(total):,.2f}", "All time", "pill-red")
    with c2: metric_card("Today", f"{currency} {float(today):,.2f}", "Today", "pill-orange")
    with c3: metric_card("Recurring", f"{currency} {float(recurring):,.2f}", "Marked recurring", "pill-violet")

    with st.expander("Add expense", expanded=True):
        with st.form("expense_form_main", clear_on_submit=True):
            c1, c2 = st.columns(2)
            category = c1.selectbox("Expense category", EXPENSE_CATEGORIES)
            custom_category = c2.text_input("Other category", placeholder="Use only if category is Other expenses")
            description = st.text_input("Description")
            c3, c4 = st.columns(2)
            amount = c3.number_input("Amount", min_value=0.0, step=1.0)
            is_recurring = c4.checkbox("Recurring monthly expense")
            if st.form_submit_button("Save expense", type="primary", icon=":material/add:"):
                final_category = custom_category.strip() if category == "Other expenses" and custom_category.strip() else category
                eid = execute(
                    "INSERT INTO expenses (date,category,description,amount,recurring,created_by) VALUES (?,?,?,?,?,?)",
                    (datetime.now().isoformat(), final_category, description, amount,
                     1 if is_recurring else 0, st.session_state.get('username', '')),
                )
                log("Created expense", entity="expense", entity_id=eid,
                    detail=f"{final_category} · {currency} {amount:,.2f}")
                st.success("Expense saved.")
                st.rerun()

    exp = query_df("SELECT * FROM expenses ORDER BY date DESC")
    if exp.empty:
        st.info("No expenses recorded yet.")
        return
    st.markdown("### Recent expenses")
    cols = st.columns(3)
    for i, e in exp.head(30).iterrows():
        with cols[i % 3]:
            rec = "<span class='pill pill-violet'>Recurring</span>" if int(e.get('recurring') or 0) else ""
            st.markdown(
                f"<div class='info-card'><b>{e['category']}</b> {rec}<br>"
                f"<span class='muted'>{e['description'] or ''}</span><br>"
                f"<span class='pill pill-red'>{currency} {float(e['amount']):,.2f}</span><br>"
                f"<span class='muted'>By: {e.get('created_by') or '-'} · {str(e['date'])[:10]}</span></div>",
                unsafe_allow_html=True,
            )
            if has_access("Admin"):
                if st.button("Delete", key=f"expdel_{e['id']}", icon=":material/delete:"):
                    execute("DELETE FROM expenses WHERE id=?", (int(e['id']),))
                    log("Deleted expense", entity="expense", entity_id=int(e['id']),
                        detail=f"{e['category']} · {currency} {float(e['amount']):,.2f}")
                    st.success("Expense deleted.")
                    st.rerun()
