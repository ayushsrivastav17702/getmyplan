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
- CONF-01–32: Analysis parameters, module toggles, store classes, category hierarchies, custom roles, permission overrides
- Testing: **100% (Iteration 21, 32/32 PASS)**

### Phase 20 — Core Logic Module (Feb 2026)
- **CORE-01–08**: ROS Calculation — configurable period, exclude returns, exclude promo spikes, per-store independence, closed day exclusion
- **CORE-09–14**: Healthy Size Set — per-store-style size availability vs PSA threshold, style-specific total sizes
- **CORE-15–21**: TrueROS — weighted recent/historical ROS with configurable weights, promo exclusion, weekend/weekday weighting
- **CORE-22–27**: Attribute Grouping — group by color/size/fit/nested multi-attribute, null→Unknown handling
- **CORE-28–35**: Store-Style Ranking — sort by revenue/ROS/DOH, tie-breaking, pagination, Top/Bottom N, CSV export, filter-before-rank
- Testing: **100% (Iteration 22, 35/35 PASS)**

## Test Coverage Summary

| Module | Total | PASS | PARTIAL | GAP | % |
|--------|-------|------|---------|-----|---|
| Executive Dashboard | 35 | 29 | 1 | 3 | 83% |
| Data Upload | 35 | 30 | 4 | 3 | 86% |
| Configuration | 32 | 32 | 0 | 0 | **100%** |
| Core Logic | 35 | 35 | 0 | 0 | **100%** |
| **Total** | **137** | **126** | **5** | **6** | **92%** |

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
- Modularize server.py (~3700+ lines) — started with /backend/routes/core_logic.py
- Scheduled analysis jobs
- Tenant billing/usage tracking
