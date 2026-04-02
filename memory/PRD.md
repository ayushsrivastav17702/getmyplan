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

### Phase 22 — Stock-Out Analysis Module (Feb 2026)
- **SO-01–35**: Period trends (WTD/MTD/QTD/YTD), heatmaps, moving averages, predictive analysis, reorder recommendations
- Testing: **100% (Iteration 24, 35/35 PASS)**

### Phase 23 — Replenishment Planner Module (Apr 2026)
- **REP-01–08**: Reorder Point Calculation — RP = (Avg Daily Sales × Lead Time) + Safety Stock, zero lead time, zero safety stock, high variability (z-score 1.65), seasonal dynamic safety (1.5x), new style category average fallback, manual override, trigger replenishment flag
- **REP-09–15**: Order Quantity — Order Qty = (Cover Days × Avg Sales) - Current Stock, MOQ rounding, pack size constraints, warehouse stock availability check, ROS-based multi-store allocation, A-class store priority
- **REP-16–21**: IST Inter-Store Transfer — overstocked (DOH > 30d), understocked (DOH < 7d), transfer qty = min(surplus, need), same-region prioritization, multiple source stores, approval workflow
- **REP-22–27**: Replenishment Run — algorithm generates orders, pre/post comparison, stock-out reduction %, fill rate improvement, DOH improvement, warehouse stock exhaustion alerts
- **REP-28–32**: Orders Dashboard — pending orders list, approve/reject, bulk approve, CSV export, auto-replenishment schedule (daily/weekly)
- New modular route file: `/backend/routes/replenishment.py`
- Testing: **100% (Iteration 25, 32/32 PASS)**

## Test Coverage Summary

| Module | Total | PASS | PARTIAL | GAP | % |
|--------|-------|------|---------|-----|---|
| Executive Dashboard | 35 | 29 | 1 | 3 | 83% |
| Data Upload | 35 | 30 | 4 | 3 | 86% |
| Configuration | 32 | 32 | 0 | 0 | **100%** |
| Core Logic | 35 | 35 | 0 | 0 | **100%** |
| Gap Analysis | 35 | 35 | 0 | 0 | **100%** |
| Stock-Out Analysis | 35 | 35 | 0 | 0 | **100%** |
| Replenishment Planner | 32 | 32 | 0 | 0 | **100%** |
| **Total** | **239** | **228** | **5** | **6** | **95%** |

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
- Modularize server.py (~4200 lines) — started with /backend/routes/core_logic.py and /backend/routes/replenishment.py
- Scheduled analysis jobs
- Tenant billing/usage tracking
