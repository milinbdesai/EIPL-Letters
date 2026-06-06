"""Thin data-access helpers around Supabase tables."""
from __future__ import annotations
from lib.db import sb


# ---- Companies ----
def list_companies(active_only: bool = True) -> list[dict]:
    q = sb().table("companies").select("*").order("name")
    if active_only:
        q = q.eq("is_active", True)
    return q.execute().data or []

def get_company(cid: str) -> dict | None:
    r = sb().table("companies").select("*").eq("id", cid).limit(1).execute().data
    return r[0] if r else None

def upsert_company(data: dict) -> dict:
    if data.get("id"):
        cid = data.pop("id")
        return sb().table("companies").update(data).eq("id", cid).execute().data[0]
    return sb().table("companies").insert(data).execute().data[0]

def delete_company(cid: str) -> None:
    sb().table("companies").delete().eq("id", cid).execute()


# ---- Salary components ----
def list_components(company_id: str) -> list[dict]:
    return sb().table("salary_components").select("*")\
        .eq("company_id", company_id).eq("is_active", True)\
        .order("display_order").execute().data or []

def upsert_component(data: dict) -> dict:
    if data.get("id"):
        cid = data.pop("id")
        return sb().table("salary_components").update(data).eq("id", cid).execute().data[0]
    return sb().table("salary_components").insert(data).execute().data[0]

def delete_component(cid: str) -> None:
    sb().table("salary_components").delete().eq("id", cid).execute()


# ---- Templates ----
def list_templates(company_id: str | None = None, letter_type: str | None = None,
                   active_only: bool = True) -> list[dict]:
    q = sb().table("letter_templates").select("*").order("display_name")
    if company_id: q = q.eq("company_id", company_id)
    if letter_type: q = q.eq("letter_type", letter_type)
    if active_only: q = q.eq("is_active", True)
    return q.execute().data or []

def get_template(tid: str) -> dict | None:
    r = sb().table("letter_templates").select("*").eq("id", tid).limit(1).execute().data
    return r[0] if r else None

def upsert_template(data: dict) -> dict:
    if data.get("id"):
        tid = data.pop("id")
        return sb().table("letter_templates").update(data).eq("id", tid).execute().data[0]
    return sb().table("letter_templates").insert(data).execute().data[0]

def delete_template(tid: str) -> None:
    sb().table("letter_templates").delete().eq("id", tid).execute()


# ---- Employees ----
def list_employees(company_id: str | None = None, active_only: bool = True) -> list[dict]:
    q = sb().table("employees").select("*").order("full_name")
    if company_id: q = q.eq("company_id", company_id)
    if active_only: q = q.eq("is_active", True)
    return q.execute().data or []

def get_employee(eid: str) -> dict | None:
    r = sb().table("employees").select("*").eq("id", eid).limit(1).execute().data
    return r[0] if r else None

def upsert_employee(data: dict) -> dict:
    if data.get("id"):
        eid = data.pop("id")
        return sb().table("employees").update(data).eq("id", eid).execute().data[0]
    return sb().table("employees").insert(data).execute().data[0]

def delete_employee(eid: str) -> None:
    sb().table("employees").delete().eq("id", eid).execute()


# ---- Letters (history) ----
def list_letters(company_id: str | None = None, employee_id: str | None = None,
                 limit: int = 200) -> list[dict]:
    q = sb().table("letters").select("*, companies(name), employees(full_name)")\
        .order("issue_date", desc=True).limit(limit)
    if company_id: q = q.eq("company_id", company_id)
    if employee_id: q = q.eq("employee_id", employee_id)
    return q.execute().data or []

def insert_letter(data: dict) -> dict:
    return sb().table("letters").insert(data).execute().data[0]

def next_reference_no(company: dict, letter_type: str) -> str:
    """Generate sequential ref no like 'BNS/OL/2026/0001'."""
    from datetime import date
    prefix_map = {"offer": "OL", "appointment": "AL", "confirmation": "CL"}
    short = (company.get("name") or "CO").split()[0][:4].upper()
    code = prefix_map.get(letter_type, letter_type[:2].upper())
    year = date.today().year
    pattern = f"{short}/{code}/{year}/"
    rows = sb().table("letters").select("reference_no")\
        .eq("company_id", company["id"]).eq("letter_type", letter_type)\
        .like("reference_no", f"{pattern}%").execute().data or []
    n = 0
    for r in rows:
        try:
            n = max(n, int((r.get("reference_no") or "").split("/")[-1]))
        except Exception:
            pass
    return f"{pattern}{n+1:04d}"
