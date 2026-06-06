"""Searchable history of issued letters with re-download links."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import streamlit as st
import pandas as pd
from lib.auth import require_login
from lib.repo import list_companies, list_letters

require_login()
st.set_page_config(page_title="Letter History", page_icon="📚", layout="wide")
st.title("📚 Letter History")

companies = list_companies(active_only=False)
cmap = {"All": None} | {c["name"]: c["id"] for c in companies}
sel = st.selectbox("Company filter", list(cmap.keys()))
letters = list_letters(company_id=cmap[sel], limit=500)

if not letters:
    st.info("No letters yet."); st.stop()

q = st.text_input("Search (name / ref no / type)", "")
def _match(l):
    if not q: return True
    s = (l.get("reference_no","") + " " + l.get("letter_type","") + " "
         + ((l.get("employees") or {}).get("full_name") or "")).lower()
    return q.lower() in s
filtered = [l for l in letters if _match(l)]

df = pd.DataFrame([{
    "Date": l["issue_date"],
    "Ref No": l.get("reference_no"),
    "Type": l["letter_type"].title(),
    "Company": (l.get("companies") or {}).get("name"),
    "Employee": (l.get("employees") or {}).get("full_name"),
    "Status": l.get("status"),
    "DOCX": l.get("docx_url") or "",
    "PDF": l.get("pdf_url") or "",
} for l in filtered])

st.dataframe(
    df, hide_index=True, use_container_width=True,
    column_config={
        "DOCX": st.column_config.LinkColumn("DOCX", display_text="open"),
        "PDF": st.column_config.LinkColumn("PDF", display_text="open"),
    },
)
