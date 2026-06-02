"""Employees master per company."""
import streamlit as st
import pandas as pd
from datetime import date
from dateutil.parser import parse as dtparse
from lib.auth import require_login
from lib.repo import list_companies, list_employees, get_employee, upsert_employee, delete_employee

require_login()
st.set_page_config(page_title="Employees", page_icon="👤", layout="wide")
st.title("👤 Employees")

companies = list_companies()
if not companies:
    st.info("Add a company first."); st.stop()
cmap = {c["name"]: c["id"] for c in companies}
sel_company = st.selectbox("Company", list(cmap.keys()))
company_id = cmap[sel_company]

employees = list_employees(company_id=company_id, active_only=False)

with st.expander(f"All employees ({len(employees)})", expanded=True):
    if employees:
        df = pd.DataFrame([{
            "Code": e.get("employee_code"),
            "Name": e["full_name"],
            "Designation": e.get("designation"),
            "Department": e.get("department"),
            "DOJ": e.get("date_of_joining"),
            "CTC": e.get("ctc_annual"),
            "Active": e.get("is_active"),
        } for e in employees])
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.caption("No employees yet.")

st.divider()
left, right = st.columns([1, 2])
with left:
    st.subheader("Pick employee")
    options = ["➕ New employee"] + [f"{e['full_name']}" for e in employees]
    ids = [None] + [e["id"] for e in employees]
    idx = st.radio("Select", options, label_visibility="collapsed")
    selected_id = ids[options.index(idx)]

with right:
    emp = get_employee(selected_id) if selected_id else {}
    is_new = not selected_id
    st.subheader("New employee" if is_new else f"Edit: {emp['full_name']}")

    def _date_val(key, default=None):
        v = emp.get(key)
        if isinstance(v, str):
            try: return dtparse(v).date()
            except: return default
        return v or default

    with st.form("emp_form"):
        c1, c2 = st.columns(2)
        with c1:
            employee_code = st.text_input("Employee code", value=emp.get("employee_code", "") or "")
            full_name = st.text_input("Full name *", value=emp.get("full_name", ""))
            email = st.text_input("Email", value=emp.get("email", "") or "")
            phone = st.text_input("Phone", value=emp.get("phone", "") or "")
            gender = st.selectbox("Gender", ["", "Male", "Female", "Other"],
                                  index=["","Male","Female","Other"].index(emp.get("gender") or ""))
            date_of_birth = st.date_input("Date of birth", value=_date_val("date_of_birth"),
                                          min_value=date(1950,1,1), max_value=date.today())
            address = st.text_area("Address", value=emp.get("address", "") or "")
        with c2:
            designation = st.text_input("Designation", value=emp.get("designation", "") or "")
            department = st.text_input("Department", value=emp.get("department", "") or "")
            reporting_to = st.text_input("Reporting to", value=emp.get("reporting_to", "") or "")
            work_location = st.text_input("Work location", value=emp.get("work_location", "") or "")
            date_of_joining = st.date_input("Date of joining",
                                            value=_date_val("date_of_joining", date.today()))
            etype_opts = ["", "permanent", "contract", "intern"]
            employment_type = st.selectbox("Employment type", etype_opts,
                                           index=etype_opts.index(emp.get("employment_type") or ""))
            probation_months = st.number_input("Probation months", value=int(emp.get("probation_months") or 6), step=1)
            ctc_annual = st.number_input("Annual CTC (₹)", value=float(emp.get("ctc_annual") or 0), step=10000.0)
        notes = st.text_area("Notes", value=emp.get("notes", "") or "")
        is_active = st.checkbox("Active", value=bool(emp.get("is_active", True)))

        cc1, cc2 = st.columns(2)
        save = cc1.form_submit_button("💾 Save", type="primary", use_container_width=True)
        del_ = cc2.form_submit_button("🗑️ Delete", use_container_width=True, disabled=is_new)

    if save:
        if not full_name.strip():
            st.error("Full name required.")
        else:
            data = {
                "company_id": company_id,
                "employee_code": employee_code or None,
                "full_name": full_name.strip(),
                "email": email or None, "phone": phone or None,
                "date_of_birth": date_of_birth.isoformat() if date_of_birth else None,
                "gender": gender or None, "address": address or None,
                "designation": designation or None, "department": department or None,
                "reporting_to": reporting_to or None, "work_location": work_location or None,
                "date_of_joining": date_of_joining.isoformat() if date_of_joining else None,
                "employment_type": employment_type or None,
                "probation_months": int(probation_months),
                "ctc_annual": float(ctc_annual) if ctc_annual else None,
                "notes": notes or None, "is_active": is_active,
            }
            if not is_new: data["id"] = selected_id
            upsert_employee(data); st.success("Saved."); st.rerun()

    if del_ and not is_new:
        delete_employee(selected_id); st.success("Deleted."); st.rerun()
