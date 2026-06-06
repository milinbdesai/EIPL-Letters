"""Admin-only: add team members who can log in."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import streamlit as st
import pandas as pd
from lib.auth import require_login, create_user
from lib.db import sb

user = require_login()
if user["role"] != "admin":
    st.error("Admins only."); st.stop()

st.set_page_config(page_title="Users", page_icon="🔐", layout="wide")
st.title("🔐 Users")

rows = sb().table("users").select("id,email,full_name,role,created_at").order("created_at").execute().data or []
st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

st.subheader("Add user")
with st.form("new_user", clear_on_submit=True):
    email = st.text_input("Email *")
    full_name = st.text_input("Full name")
    role = st.selectbox("Role", ["hr", "admin"])
    pw = st.text_input("Initial password *", type="password")
    if st.form_submit_button("➕ Create", type="primary"):
        if not email or not pw:
            st.error("Email and password required.")
        else:
            try:
                create_user(email, pw, full_name or email.split("@")[0], role)
                st.success("Created."); st.rerun()
            except Exception as e:
                st.error(f"Could not create: {e}")
