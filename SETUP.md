# HR Letters App — Setup Guide

A Streamlit web app to generate Offer / Appointment / Confirmation / custom letters for multiple companies, with employee masters, configurable salary structures, and DOCX + PDF output.

---

## 1. Create Supabase project (free, ~3 min)

1. Go to https://supabase.com → **Sign in** (GitHub login is easiest).
2. **New Project**
   - Name: `hr-letters` (anything)
   - Database password: **save it** somewhere — you'll need it
   - Region: pick closest (Mumbai/Singapore for India)
   - Plan: Free
3. Wait ~2 min for provisioning.

## 2. Run the database schema

1. In Supabase dashboard → left sidebar → **SQL Editor** → **New query**.
2. Open `db/schema.sql` from this project, copy entire contents, paste into SQL editor.
3. Click **Run**. You should see "Success".

## 3. Create storage bucket for logos

1. Supabase → **Storage** → **New bucket**
   - Name: `company-assets`
   - Public bucket: **Yes** (so logos render in the app)
2. Click **Create**.

## 4. Get your API credentials

1. Supabase → **Project Settings** (gear icon) → **API**
2. Copy these two values:
   - **Project URL** (e.g. `https://xxxxx.supabase.co`)
   - **anon public key** (long string starting with `eyJ...`)
3. Also get the **service_role** key from the same page (keep secret — server-side only).

## 5. Configure local secrets

1. Copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml`
2. Paste your Supabase URL and keys.
3. Set an initial admin email + password (you'll log in with this).

## 6. Install & run locally

```bash
cd app
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Visit http://localhost:8501

## 7. Deploy to Streamlit Community Cloud (when ready)

1. Push this `app/` folder to a **private** GitHub repo.
2. Go to https://share.streamlit.io → **New app** → pick the repo.
3. In **Advanced settings → Secrets**, paste the same TOML content from `secrets.toml`.
4. Deploy. You'll get a public `*.streamlit.app` URL.

> **Note on PDF generation:** Streamlit Cloud's Linux image supports LibreOffice via `packages.txt` (already included). DOCX → PDF conversion uses `libreoffice --headless`.

---

## First-run checklist

- [ ] Log in with admin credentials from `secrets.toml`
- [ ] **Masters → Companies** → add your first company (BNS) with logo
- [ ] **Masters → Salary Components** → add Basic / HRA / etc. for that company
- [ ] **Masters → Templates** → create Offer Letter template (paste existing BNS letter text, replace names with `{{placeholders}}`)
- [ ] **Employees** → add one test employee
- [ ] **Generate Letter** → pick company, template, employee → download DOCX + PDF
