-- HR Letters App — Supabase schema
-- Run this entire file in Supabase SQL Editor.

-- ============ Users (app login) ============
create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  password_hash text not null,
  full_name text,
  role text not null default 'hr' check (role in ('admin','hr')),
  created_at timestamptz default now()
);

-- ============ Companies (master) ============
create table if not exists companies (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  legal_name text,
  address text,
  city text,
  state text,
  pincode text,
  country text default 'India',
  phone text,
  email text,
  website text,
  registration_no text,        -- CIN / Reg No
  pan text,
  gstin text,
  logo_url text,               -- Supabase Storage public URL
  signatory_name text,
  signatory_designation text,
  signatory_department text,
  letterhead_footer text,      -- optional small footer text
  is_active boolean default true,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- ============ Salary components (per company) ============
create table if not exists salary_components (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id) on delete cascade,
  name text not null,                       -- "Basic", "HRA", "Special Allowance"
  component_type text not null check (component_type in ('earning','deduction')),
  calc_type text not null check (calc_type in ('percent_of_ctc','percent_of_basic','fixed','formula')),
  calc_value numeric,                       -- e.g. 40 for 40%
  formula_expr text,                        -- optional, when calc_type='formula'
  display_order int default 0,
  is_active boolean default true,
  created_at timestamptz default now()
);

-- ============ Letter templates (per company × letter type) ============
create table if not exists letter_templates (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id) on delete cascade,
  letter_type text not null,                -- 'offer','appointment','confirmation', or custom string
  display_name text not null,               -- "Offer Letter", "Confirmation Letter"
  source_type text not null check (source_type in ('rich_text','docx_upload')),
  body_html text,                           -- when source_type='rich_text'
  docx_url text,                            -- when source_type='docx_upload' (Supabase Storage)
  is_default boolean default false,
  version int default 1,
  is_active boolean default true,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists idx_templates_company on letter_templates(company_id, letter_type, is_active);

-- ============ Employees ============
create table if not exists employees (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id) on delete cascade,
  employee_code text,
  full_name text not null,
  email text,
  phone text,
  date_of_birth date,
  gender text,
  address text,
  designation text,
  department text,
  reporting_to text,
  work_location text,
  date_of_joining date,
  employment_type text,                     -- 'permanent','contract','intern'
  probation_months int default 6,
  ctc_annual numeric,                       -- annual CTC
  notes text,
  is_active boolean default true,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists idx_employees_company on employees(company_id, is_active);

-- ============ Issued letters (history) ============
create table if not exists letters (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id) on delete restrict,
  employee_id uuid references employees(id) on delete set null,
  template_id uuid references letter_templates(id) on delete set null,
  letter_type text not null,
  reference_no text,                        -- e.g. "BNS/OL/2026/001"
  issue_date date not null default current_date,
  subject text,
  rendered_data jsonb,                      -- frozen snapshot of placeholders used
  docx_url text,                            -- Supabase Storage URL
  pdf_url text,
  issued_by uuid references users(id) on delete set null,
  status text default 'issued' check (status in ('draft','issued','revoked')),
  notes text,
  created_at timestamptz default now()
);

create index if not exists idx_letters_employee on letters(employee_id);
create index if not exists idx_letters_company on letters(company_id, issue_date desc);

-- ============ Updated-at triggers ============
create or replace function set_updated_at()
returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end $$;

drop trigger if exists trg_companies_updated on companies;
create trigger trg_companies_updated before update on companies
  for each row execute function set_updated_at();

drop trigger if exists trg_templates_updated on letter_templates;
create trigger trg_templates_updated before update on letter_templates
  for each row execute function set_updated_at();

drop trigger if exists trg_employees_updated on employees;
create trigger trg_employees_updated before update on employees
  for each row execute function set_updated_at();
