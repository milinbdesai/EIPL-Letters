"""Companies master — CRUD with logo upload."""
import streamlit as st
from lib.auth import require_login
from lib.repo import list_companies, get_company, upsert_company, delete_company
from lib.db import upload_bytes, delete_object_by_url

require_login()
st.set_page_config(page_title="Companies", page_icon="🏢", layout="wide")
st.title("🏢 Companies")

companies = list_companies(active_only=False)
left, right = st.columns([1, 2])

with left:
    st.subheader("All companies")
    options = ["➕ New company"] + [f"{c['name']}" for c in companies]
    ids = [None] + [c["id"] for c in companies]
    idx = st.radio("Select", options, label_visibility="collapsed", index=0)
    selected_id = ids[options.index(idx)]

with right:
    company = get_company(selected_id) if selected_id else {}
    is_new = not selected_id
    st.subheader("New company" if is_new else f"Edit: {company.get('name')}")

    with st.form("company_form", clear_on_submit=False):
        name = st.text_input("Name *", value=company.get("name", ""))
        legal_name = st.text_input("Legal name", value=company.get("legal_name", ""))

        c1, c2 = st.columns(2)
        with c1:
            address = st.text_area("Address", value=company.get("address", ""))
            city = st.text_input("City", value=company.get("city", ""))
            state = st.text_input("State", value=company.get("state", ""))
            pincode = st.text_input("Pincode", value=company.get("pincode", ""))
            country = st.text_input("Country", value=company.get("country") or "India")
        with c2:
            phone = st.text_input("Phone", value=company.get("phone", ""))
            email = st.text_input("Email", value=company.get("email", ""))
            website = st.text_input("Website", value=company.get("website", ""))
            registration_no = st.text_input("CIN / Registration No", value=company.get("registration_no", ""))
            pan = st.text_input("PAN", value=company.get("pan", ""))
            gstin = st.text_input("GSTIN", value=company.get("gstin", ""))

        st.markdown("**Authorized Signatory**")
        s1, s2, s3 = st.columns(3)
        signatory_name = s1.text_input("Name", value=company.get("signatory_name", ""))
        signatory_designation = s2.text_input("Designation", value=company.get("signatory_designation", ""))
        signatory_department = s3.text_input("Department", value=company.get("signatory_department", ""))

        letterhead_footer = st.text_area("Letterhead footer (optional)", value=company.get("letterhead_footer", ""))

        st.markdown("**Logo**")
        if company.get("logo_url"):
            st.image(company["logo_url"], width=120)
        logo_file = st.file_uploader("Upload new logo (PNG/JPG)", type=["png", "jpg", "jpeg"])

        is_active = st.checkbox("Active", value=bool(company.get("is_active", True)))

        col_a, col_b = st.columns([1, 1])
        save = col_a.form_submit_button("💾 Save", type="primary", use_container_width=True)
        del_ = col_b.form_submit_button("🗑️ Delete", use_container_width=True, disabled=is_new)

    if save:
        if not name.strip():
            st.error("Name is required.")
        else:
            data = {
                "name": name.strip(), "legal_name": legal_name or None,
                "address": address or None, "city": city or None, "state": state or None,
                "pincode": pincode or None, "country": country or None,
                "phone": phone or None, "email": email or None, "website": website or None,
                "registration_no": registration_no or None, "pan": pan or None, "gstin": gstin or None,
                "signatory_name": signatory_name or None,
                "signatory_designation": signatory_designation or None,
                "signatory_department": signatory_department or None,
                "letterhead_footer": letterhead_footer or None,
                "is_active": is_active,
            }
            if not is_new:
                data["id"] = selected_id
            if logo_file is not None:
                if company.get("logo_url"):
                    delete_object_by_url(company["logo_url"])
                data["logo_url"] = upload_bytes("logos", logo_file.name, logo_file.read(), logo_file.type)
            saved = upsert_company(data)
            st.success(f"Saved: {saved['name']}")
            st.rerun()

    if del_ and not is_new:
        if company.get("logo_url"):
            delete_object_by_url(company["logo_url"])
        delete_company(selected_id)
        st.success("Deleted.")
        st.rerun()
