"""HR Letters — Streamlit multi-page app entry point.

Run:  streamlit run app.py
"""
from __future__ import annotations
import streamlit as st

from lib.auth import login, current_user, logout, ensure_initial_admin
from lib.repo import list_companies, list_letters, list_employees


st.set_page_config(
    page_title=st.secrets.get("app", {}).get("app_title", "HR Letters"),
    page_icon="📄",
    layout="wide",
)


def _login_view():
    st.title("📄 HR Letters")
    st.caption("Generate offer, appointment, confirmation & custom letters.")
    with st.form("login"):
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        ok = st.form_submit_button("Log in", use_container_width=True)
    if ok:
        try:
            ensure_initial_admin()
        except Exception as e:
            st.error(f"Could not reach database: {e}")
            st.stop()
        user = login(email, pw)
        if user:
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error("Invalid email or password.")


def _dashboard():
    user = current_user()
    with st.sidebar:
        st.markdown(f"**{user['full_name'] or user['email']}**")
        st.caption(user["role"].upper())
        if st.button("Log out", use_container_width=True):
            logout(); st.rerun()
        st.divider()
        st.page_link("app.py", label="🏠 Dashboard")
        st.page_link("pages/1_Companies.py", label="🏢 Companies")
        st.page_link("pages/2_Salary_Components.py", label="💰 Salary Components")
        st.page_link("pages/3_Templates.py", label="📝 Templates")
        st.page_link("pages/4_Employees.py", label="👤 Employees")
        st.page_link("pages/5_Generate_Letter.py", label="✨ Generate Letter")
        st.page_link("pages/6_Letter_History.py", label="📚 Letter History")
        if user["role"] == "admin":
            st.page_link("pages/7_Users.py", label="🔐 Users")

    st.title("Dashboard")
    try:
        companies = list_companies()
        letters = list_letters(limit=500)
        employees = list_employees()
    except Exception as e:
        st.error(f"Database error: {e}")
        st.info("Did you run db/schema.sql in Supabase and set secrets correctly?")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Companies", len(companies))
    c2.metric("Employees", len(employees))
    c3.metric("Letters issued", len(letters))

    st.subheader("Recent letters")
    if not letters:
        st.info("No letters yet. Go to **Generate Letter** to create one.")
        return
    import pandas as pd
    df = pd.DataFrame([{
        "Date": l["issue_date"],
        "Ref No": l.get("reference_no"),
        "Type": l["letter_type"].title(),
        "Company": (l.get("companies") or {}).get("name"),
        "Employee": (l.get("employees") or {}).get("full_name"),
        "Status": l.get("status"),
    } for l in letters[:25]])
    st.dataframe(df, hide_index=True, use_container_width=True)


if current_user():
    _dashboard()
else:
    _login_view()
