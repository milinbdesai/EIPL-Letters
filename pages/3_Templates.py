"""Letter templates — per company, per letter type. Rich text OR uploaded DOCX."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import streamlit as st
from lib.auth import require_login
from lib.repo import list_companies, list_templates, get_template, upsert_template, delete_template
from lib.db import upload_bytes, delete_object_by_url

require_login()
st.set_page_config(page_title="Templates", page_icon="📝", layout="wide")
st.title("📝 Letter Templates")

PRESET_TYPES = [
    ("offer", "Offer Letter"),
    ("appointment", "Appointment Letter"),
    ("confirmation", "Confirmation Letter"),
]

companies = list_companies()
if not companies:
    st.info("Add a company first."); st.stop()
cmap = {c["name"]: c["id"] for c in companies}
sel = st.selectbox("Company", list(cmap.keys()))
company_id = cmap[sel]

existing = list_templates(company_id=company_id, active_only=False)

with st.expander("📋 Placeholder reference", expanded=False):
    st.markdown("""
Use `{{placeholder}}` anywhere in the body.

**Company:** `{{company_name}}` `{{company_legal_name}}` `{{company_address}}` `{{company_city}}` `{{company_state}}` `{{company_pincode}}` `{{company_phone}}` `{{company_email}}` `{{company_website}}` `{{company_cin}}` `{{signatory_name}}` `{{signatory_designation}}` `{{signatory_department}}`

**Employee:** `{{employee_name}}` `{{employee_code}}` `{{employee_email}}` `{{employee_phone}}` `{{employee_address}}` `{{designation}}` `{{department}}` `{{reporting_to}}` `{{work_location}}` `{{date_of_joining}}` `{{date_of_birth}}` `{{probation_months}}` `{{employment_type}}`

**Comp:** `{{ctc_annual}}` `{{ctc_annual_words}}` `{{gross_annual}}` `{{gross_monthly}}` `{{net_annual}}` `{{net_monthly}}`

**Dates:** `{{issue_date}}` `{{today}}`

**Special block:** `{{salary_breakup_table}}` — auto-inserts the full salary table (appointment letters).
""")

st.divider()
left, right = st.columns([1, 2])

with left:
    st.subheader("Templates")
    options = ["➕ New template"] + [f"{t['display_name']} ({t['letter_type']})" for t in existing]
    ids = [None] + [t["id"] for t in existing]
    idx = st.radio("Select", options, label_visibility="collapsed", index=0)
    selected_id = ids[options.index(idx)]

with right:
    tpl = get_template(selected_id) if selected_id else {}
    is_new = not selected_id
    st.subheader("New template" if is_new else f"Edit: {tpl.get('display_name')}")

    type_options = [f"{k} — {v}" for k, v in PRESET_TYPES] + ["custom — Custom letter type"]
    if not is_new and tpl["letter_type"] not in [k for k, _ in PRESET_TYPES]:
        type_default_idx = len(type_options) - 1
    else:
        type_default_idx = [k for k, _ in PRESET_TYPES].index(tpl["letter_type"]) if not is_new else 0
    chosen = st.selectbox("Letter type", type_options, index=type_default_idx)
    if chosen.startswith("custom"):
        letter_type = st.text_input("Custom letter_type slug", value=tpl.get("letter_type", "") if not is_new else "")
    else:
        letter_type = chosen.split(" — ")[0]

    display_name = st.text_input("Display name", value=tpl.get("display_name", ""))

    source = st.radio("Template source", ["rich_text", "docx_upload"],
                      index=0 if (is_new or tpl.get("source_type") == "rich_text") else 1,
                      horizontal=True)

    body_html = tpl.get("body_html") or ""
    docx_file = None
    if source == "rich_text":
        try:
            from streamlit_quill import st_quill
            body_html = st_quill(value=body_html, html=True, key=f"quill_{selected_id or 'new'}")
        except Exception:
            st.warning("Rich editor unavailable — falling back to plain HTML textarea.")
            body_html = st.text_area("Body (HTML allowed)", value=body_html, height=500)
    else:
        if tpl.get("docx_url"):
            st.caption(f"Current: {tpl['docx_url']}")
        docx_file = st.file_uploader("Upload DOCX template (use Jinja: {{ employee_name }})", type=["docx"])
        st.caption("In DOCX templates use Jinja syntax: `{{ employee_name }}` with spaces. "
                   "For salary table loop: `{% for r in salary_annual %}{{ r.name }} - {{ r.amount }}{% endfor %}`")

    is_default = st.checkbox("Default template for this letter type", value=bool(tpl.get("is_default", False)))
    is_active = st.checkbox("Active", value=bool(tpl.get("is_active", True)))

    c1, c2 = st.columns(2)
    save = c1.button("💾 Save", type="primary", use_container_width=True)
    del_ = c2.button("🗑️ Delete", use_container_width=True, disabled=is_new)

    if save:
        if not letter_type.strip() or not display_name.strip():
            st.error("Letter type and display name required.")
        else:
            data = {
                "company_id": company_id,
                "letter_type": letter_type.strip(),
                "display_name": display_name.strip(),
                "source_type": source,
                "body_html": body_html if source == "rich_text" else None,
                "is_default": is_default,
                "is_active": is_active,
            }
            if not is_new:
                data["id"] = selected_id
                data["docx_url"] = tpl.get("docx_url")
            if source == "docx_upload" and docx_file is not None:
                if tpl.get("docx_url"):
                    delete_object_by_url(tpl["docx_url"])
                data["docx_url"] = upload_bytes("templates", docx_file.name, docx_file.read(), docx_file.type)
            upsert_template(data)
            st.success("Saved."); st.rerun()

    if del_ and not is_new:
        if tpl.get("docx_url"):
            delete_object_by_url(tpl["docx_url"])
        delete_template(selected_id)
        st.success("Deleted."); st.rerun()
