# Fashion Retail Gap Analysis Platform - PRD

## Original Problem Statement
Build a Fashion Retail Gap Analysis platform with React + FastAPI featuring CSV data uploading, multiple analytics dashboards, dynamic filtering with presets, Chart.js visualizations, GPT-5.2 FAQ Chatbot, multi-tenant architecture, and role-based access control.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme)
- **Backend**: FastAPI with Python/Pandas
- **Database**: MongoDB (multi-tenant: separate DB per tenant, shared registry in merch_shared)
- **AI**: GPT 5.2 via Emergent LLM Key
- **Charts**: Chart.js + react-chartjs-2 (NO Recharts)
- **Auth**: JWT with bcrypt, RBAC with 8 built-in roles + custom roles + permission overrides

## Completed Phases

### Phase 1-16 (Previous sessions)
- Full MVP analytics, filters, presets, 6 analytics modules
- Executive Dashboard with module cards
- MongoDB Multi-Tenancy + RBAC + User Management
- Full RBAC integration across all 16 pages
- Tenant Admin Panel

### Phase 17 — Executive Dashboard P0 (Feb 2026)
- 401 Interceptor, KPI cards (Revenue, Units, MRP Realisation), WoW/YoY, date presets, validation, auto-refresh
- Testing: 100% (Iterations 17-18, 29/35 PASS, 3 known P1/P2 GAPs)

### Phase 18 — Data Upload Validation (Feb 2026)
- File size limit, data type validation, null check, dedup, future date rejection, negative qty rejection, encoding detection, concurrent upload lock
- Testing: 100% (Iteration 20, 30/35 PASS, 3 known SFTP/browser GAPs)

### Phase 19 — Configuration Module (Feb 2026)
- **CONF-01–08**: 8 analysis parameters (PSA Benchmark, Cover Days, ROS Period, Ideal DOH, Topseller X Factor, Lead Time, Safety Days, Shelf Life) with full validation + persistence + analytics integration
- **CONF-09–14**: Module toggles (NOOS, ROS, Size Gap, Lifecycle, Replenishment) that control Gap Analysis tabs + sidebar nav
- **CONF-15–20**: Store Classification CRUD with priority ordering + filter integration
- **CONF-21–26**: Category Hierarchy CRUD with parent-child nesting + delete protection
- **CONF-27–29**: User role assign/change/remove
- **CONF-30**: Custom role creation with configurable permissions
- **CONF-31**: Role-based menu visibility verified
- **CONF-32**: Per-user permission override (add/remove specific permissions)
- Testing: **100% (Iteration 21, 32/32 PASS)**

## Test Coverage Summary

| Module | Total | PASS | PARTIAL | GAP | % |
|--------|-------|------|---------|-----|---|
| Executive Dashboard | 35 | 29 | 1 | 3 | 83% |
| Data Upload | 35 | 30 | 4 | 3 | 86% |
| Configuration | 32 | 32 | 0 | 0 | **100%** |
| **Total** | **102** | **91** | **5** | **6** | **89%** |

## Remaining Known Gaps
- DASH-15: Revenue trend line chart (P1)
- DASH-25: Offline detection UI (P1)
- DASH-35: PDF export (P2)
- UPLOAD-26/28: Real SFTP connection (MOCKED)
- UPLOAD-33: Browser-level network retry

## Prioritized Backlog

### P0
- [ ] Tenant Admin Panel formal testing

### P1
- Revenue trend line chart (DASH-15)
- Offline detection UI (DASH-25)
- Real SFTP integration
- PDF report generation
- Email alerts for SLA/SFTP

### P2
- PDF export (DASH-35)
- Modularize server.py (~3700+ lines)
- Scheduled analysis jobs
- Tenant billing/usage tracking
