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
- Testing: 100% (Iterations 17-18)

### Phase 18 — Data Upload Validation (Feb 2026)
- File size limit, data type validation, null check, dedup, future date rejection, negative qty rejection, encoding detection, concurrent upload lock
- Testing: 100% (Iteration 20)

### Phase 19 — Configuration Module (Feb 2026)
- CONF-01–32: Analysis parameters, module toggles, store classes, category hierarchies, custom roles, permission overrides
- Testing: **100% (Iteration 21)**

### Phase 20 — Core Logic Module (Feb 2026)
- CORE-01–35: ROS Calculation, Healthy Size Set, TrueROS, Attribute Grouping, Store-Style Ranking
- New modular route file: `/backend/routes/core_logic.py`
- Testing: **100% (Iteration 22)**

### Phase 21 — Gap Analysis Module (Feb 2026)
- **GAP-01–10**: ROS Gap Analysis — gap = healthy_ros - raw_ros, brand/store filters, sort by gap_size, weekly trend
- **GAP-11–19**: Size Set Gap — healthy size sets (PSA threshold), sales loss estimation, store comparison, category/gender breakdown, weekly trend
- **GAP-20–28**: NOOS Analysis — candidate identification (avail>=80% + sales>=80%), new-style exclusion (<30 days), seasonal exclusion, low-stock alerts, recovery plans, bulk NOOS export
- **GAP-29–35**: Dashboard — 3 tabs (ROS Gap, Size Set, NOOS), KPI summary cards on all tabs, drill-down panels, chart interactivity, combined export of all gaps
- Testing: **100% (Iteration 23, 35/35 PASS)**

## Test Coverage Summary

| Module | Total | PASS | PARTIAL | GAP | % |
|--------|-------|------|---------|-----|---|
| Executive Dashboard | 35 | 29 | 1 | 3 | 83% |
| Data Upload | 35 | 30 | 4 | 3 | 86% |
| Configuration | 32 | 32 | 0 | 0 | **100%** |
| Core Logic | 35 | 35 | 0 | 0 | **100%** |
| Gap Analysis | 35 | 35 | 0 | 0 | **100%** |
| **Total** | **172** | **161** | **5** | **6** | **94%** |

## Remaining Known Gaps
- DASH-15: Revenue trend line chart (P1)
- DASH-25: Offline detection UI (P1)
- DASH-35: PDF export (P2)
- UPLOAD-26/28: Real SFTP connection (MOCKED)
- UPLOAD-33: Browser-level network retry

## Prioritized Backlog

### P0
- None critical outstanding

### P1
- Revenue trend line chart (DASH-15)
- Offline detection UI (DASH-25)
- Real SFTP integration
- PDF report generation

### P2
- PDF export (DASH-35)
- Modularize server.py (~3900+ lines) — started with /backend/routes/core_logic.py
- Scheduled analysis jobs
- Tenant billing/usage tracking
