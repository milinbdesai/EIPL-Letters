"""Generate a letter — pick company / template / employee, preview, download DOCX + PDF, save to history."""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import streamlit as st
import requests
from datetime import date
from lib.auth import require_login, current_user
from lib.repo import (
    list_companies, list_templates, list_employees,
    list_components, get_template, get_employee, get_company,
    insert_letter, next_reference_no,
)
from lib.salary import compute_breakup
from lib.render import build_context, render_richtext_to_docx, render_docx_template
from lib.pdf import docx_to_pdf
from lib.db import upload_bytes

user = require_login()
st.set_page_config(page_title="Generate Letter", page_icon="✨", layout="wide")
st.title("✨ Generate Letter")

companies = list_companies()
if not companies:
    st.info("Add a company first."); st.stop()

cmap = {c["name"]: c["id"] for c in companies}
sel_company = st.selectbox("Company", list(cmap.keys()))
company = get_company(cmap[sel_company])

templates = list_templates(company_id=company["id"])
if not templates:
    st.info("No templates for this company. Add one in **Templates**."); st.stop()

tmap = {f"{t['display_name']} ({t['letter_type']})": t["id"] for t in templates}
sel_template = st.selectbox("Template", list(tmap.keys()))
template = get_template(tmap[sel_template])

employees = list_employees(company_id=company["id"])
if not employees:
    st.info("No employees. Add one in **Employees**."); st.stop()
emap = {f"{e['full_name']}" + (f" ({e['employee_code']})" if e.get('employee_code') else ""): e["id"] for e in employees}
sel_emp = st.selectbox("Employee", list(emap.keys()))
employee = get_employee(emap[sel_emp])

# Salary breakup (used if template is appointment-style)
include_breakup = st.checkbox("Include salary breakup", value=(template["letter_type"] == "appointment"))
breakup = None
if include_breakup:
    components = list_components(company["id"])
    if not components:
        st.warning("No salary components defined for this company.")
    elif not employee.get("ctc_annual"):
        st.warning("Employee has no CTC set.")
    else:
        breakup = compute_breakup(components, employee["ctc_annual"])

st.subheader("Extras (optional)")
e1, e2 = st.columns(2)
ref_no = e1.text_input("Reference No (auto if blank)", value="")
issue_date = e2.date_input("Issue date", value=date.today())
extras_raw = st.text_area(
    "Extra placeholders (one per line, key=value)",
    placeholder="reporting_date=15 July 2026\noffer_validity=30 days",
)
extras = {}
for line in (extras_raw or "").splitlines():
    if "=" in line:
        k, v = line.split("=", 1)
        extras[k.strip()] = v.strip()

st.divider()

if st.button("🔧 Generate", type="primary"):
    ctx = build_context(company, employee, breakup, extras)
    ctx["issue_date"] = issue_date.strftime("%d %B %Y")
    if not ref_no.strip():
        ref_no = next_reference_no(company, template["letter_type"])
    ctx["reference_no"] = ref_no

    try:
        if template["source_type"] == "rich_text":
            docx_bytes = render_richtext_to_docx(
                template.get("body_html") or "",
                ctx, company.get("logo_url"), breakup,
                letter_title=None,  # template already has its own structure
            )
        else:
            # Pull template docx from storage
            if not template.get("docx_url"):
                st.error("This template has no DOCX uploaded."); st.stop()
            tpl_bytes = requests.get(template["docx_url"], timeout=15).content
            docx_bytes = render_docx_template(tpl_bytes, ctx, breakup)
    except Exception as e:
        st.error(f"Render failed: {e}"); st.stop()

    pdf_bytes = docx_to_pdf(docx_bytes)
    st.session_state["last_gen"] = {
        "docx": docx_bytes, "pdf": pdf_bytes, "ctx": ctx,
        "ref_no": ref_no, "issue_date": issue_date.isoformat(),
        "template_id": template["id"], "letter_type": template["letter_type"],
        "company_id": company["id"], "employee_id": employee["id"],
        "display_name": template["display_name"],
    }

# ----------- Preview / download / save -----------
gen = st.session_state.get("last_gen")
if gen:
    st.success(f"Generated — Ref No: **{gen['ref_no']}**")
    file_base = f"{gen['ctx'].get('employee_name','letter').replace(' ','_')}_{gen['letter_type']}_{gen['ref_no'].replace('/','-')}"

    c1, c2, c3 = st.columns(3)
    c1.download_button("⬇️ Download DOCX", data=gen["docx"],
                       file_name=f"{file_base}.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                       use_container_width=True)
    if gen["pdf"]:
        c2.download_button("⬇️ Download PDF", data=gen["pdf"],
                           file_name=f"{file_base}.pdf",
                           mime="application/pdf", use_container_width=True)
    else:
        c2.info("PDF unavailable here (LibreOffice not installed locally). On Streamlit Cloud it will work.")

    if c3.button("💾 Save to history", use_container_width=True):
        try:
            docx_url = upload_bytes("letters", f"{file_base}.docx", gen["docx"],
                                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            pdf_url = None
            if gen["pdf"]:
                pdf_url = upload_bytes("letters", f"{file_base}.pdf", gen["pdf"], "application/pdf")
            insert_letter({
                "company_id": gen["company_id"], "employee_id": gen["employee_id"],
                "template_id": gen["template_id"], "letter_type": gen["letter_type"],
                "reference_no": gen["ref_no"], "issue_date": gen["issue_date"],
                "subject": gen["display_name"], "rendered_data": gen["ctx"],
                "docx_url": docx_url, "pdf_url": pdf_url,
                "issued_by": user["id"], "status": "issued",
            })
            st.success("Saved to history.")
        except Exception as e:
            st.error(f"Save failed: {e}")
