"""Salary components master — per company, configurable formula."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import streamlit as st
import pandas as pd
from lib.auth import require_login
from lib.repo import list_companies, list_components, upsert_component, delete_component
from lib.salary import compute_breakup, format_inr

require_login()
st.set_page_config(page_title="Salary Components", page_icon="💰", layout="wide")
st.title("💰 Salary Components")

companies = list_companies()
if not companies:
    st.info("Add a company first."); st.stop()

cmap = {c["name"]: c["id"] for c in companies}
sel = st.selectbox("Company", list(cmap.keys()))
company_id = cmap[sel]
components = list_components(company_id)

left, right = st.columns([2, 1])
with left:
    st.subheader("Components")
    if components:
        df = pd.DataFrame([{
            "Name": c["name"], "Type": c["component_type"], "Calc": c["calc_type"],
            "Value": c.get("calc_value"), "Formula": c.get("formula_expr"),
            "Order": c["display_order"],
        } for c in components])
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("No components yet. Add one on the right →")

    st.subheader("Edit / Delete")
    options = ["—"] + [c["name"] for c in components]
    pick = st.selectbox("Pick a component", options)
    if pick != "—":
        comp = next(c for c in components if c["name"] == pick)
        with st.form("edit_comp"):
            name = st.text_input("Name", value=comp["name"])
            ctype = st.selectbox("Type", ["earning", "deduction"], index=0 if comp["component_type"] == "earning" else 1)
            calc = st.selectbox("Calc type", ["percent_of_ctc","percent_of_basic","fixed","formula"],
                                index=["percent_of_ctc","percent_of_basic","fixed","formula"].index(comp["calc_type"]))
            val = st.number_input("Value", value=float(comp.get("calc_value") or 0))
            formula = st.text_input("Formula (uses 'ctc')", value=comp.get("formula_expr") or "")
            order = st.number_input("Display order", value=int(comp.get("display_order") or 0), step=1)
            c1, c2 = st.columns(2)
            do_save = c1.form_submit_button("💾 Update", type="primary", use_container_width=True)
            do_del = c2.form_submit_button("🗑️ Delete", use_container_width=True)
        if do_save:
            upsert_component({
                "id": comp["id"], "name": name, "component_type": ctype,
                "calc_type": calc, "calc_value": val,
                "formula_expr": formula or None, "display_order": int(order),
            })
            st.success("Updated."); st.rerun()
        if do_del:
            delete_component(comp["id"]); st.success("Deleted."); st.rerun()

with right:
    st.subheader("Add new")
    with st.form("new_comp", clear_on_submit=True):
        name = st.text_input("Name *", placeholder="Basic / HRA / PF")
        ctype = st.selectbox("Type", ["earning", "deduction"])
        calc = st.selectbox("Calc type", ["percent_of_ctc","percent_of_basic","fixed","formula"])
        val = st.number_input("Value", value=0.0)
        formula = st.text_input("Formula (uses 'ctc')", placeholder="ctc * 0.5 - 50000")
        order = st.number_input("Display order", value=len(components), step=1)
        if st.form_submit_button("➕ Add", type="primary", use_container_width=True):
            if not name.strip():
                st.error("Name required.")
            else:
                upsert_component({
                    "company_id": company_id, "name": name.strip(),
                    "component_type": ctype, "calc_type": calc,
                    "calc_value": val, "formula_expr": formula or None,
                    "display_order": int(order),
                })
                st.success("Added."); st.rerun()

    st.divider()
    st.subheader("Preview at sample CTC")
    sample = st.number_input("Sample annual CTC", value=1200000, step=10000)
    if components:
        bk = compute_breakup(components, sample)
        rows = []
        for a, m in zip(bk["annual"], bk["monthly"]):
            rows.append({"Component": a["name"] + ("" if a["type"]=="earning" else " (D)"),
                         "Monthly": format_inr(m["amount"]),
                         "Annual": format_inr(a["amount"])})
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        t = bk["totals"]
        st.caption(f"Gross: ₹{format_inr(t['gross_annual'])}  •  "
                   f"Deductions: ₹{format_inr(t['deductions_annual'])}  •  "
                   f"Net: ₹{format_inr(t['net_annual'])}")
