"""Email/password auth backed by `users` table. bcrypt hashes."""
from __future__ import annotations
import bcrypt
import streamlit as st
from .db import sb


def _hash(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def _check(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False


def ensure_initial_admin() -> None:
    """Seed the first admin user from secrets if `users` table is empty."""
    rows = sb().table("users").select("id").limit(1).execute().data
    if rows:
        return
    cfg = st.secrets.get("app", {})
    email = cfg.get("initial_admin_email")
    pw = cfg.get("initial_admin_password")
    name = cfg.get("initial_admin_name", "Admin")
    if not email or not pw:
        return
    sb().table("users").insert({
        "email": email.lower().strip(),
        "password_hash": _hash(pw),
        "full_name": name,
        "role": "admin",
    }).execute()


def login(email: str, password: str) -> dict | None:
    row = sb().table("users").select("*").eq("email", email.lower().strip()).limit(1).execute().data
    if not row:
        return None
    user = row[0]
    if not _check(password, user["password_hash"]):
        return None
    return {"id": user["id"], "email": user["email"], "full_name": user["full_name"], "role": user["role"]}


def current_user() -> dict | None:
    return st.session_state.get("user")


def require_login() -> dict:
    """Redirect to login if not authenticated. Returns user dict if logged in."""
    user = current_user()
    if not user:
        st.warning("Please log in to continue.")
        st.switch_page("app.py")
        st.stop()
    return user


def logout() -> None:
    st.session_state.pop("user", None)


def create_user(email: str, password: str, full_name: str, role: str = "hr") -> None:
    sb().table("users").insert({
        "email": email.lower().strip(),
        "password_hash": _hash(password),
        "full_name": full_name,
        "role": role,
    }).execute()
