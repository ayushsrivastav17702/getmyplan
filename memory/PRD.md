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
- CORE-01–35: ROS, Healthy Size Set, TrueROS, Attribute Grouping, Store-Style Ranking
- New modular route file: `/backend/routes/core_logic.py`
- Testing: **100% (Iteration 22)**

### Phase 21 — Gap Analysis Module (Feb 2026)
- GAP-01–35: ROS Gap, Size Set Gap, NOOS Analysis, Dashboard
- Testing: **100% (Iteration 23, 35/35 PASS)**

### Phase 22 — Stock-Out Analysis Module (Feb 2026)
- SO-01–35: Period trends, heatmaps, moving averages, predictive analysis, reorder recommendations
- Testing: **100% (Iteration 24, 35/35 PASS)**

### Phase 23 — Replenishment Planner Module (Apr 2026)
- REP-01–32: Reorder Point Calculation, Order Quantity, IST Inter-Store Transfer, Replenishment Run, Orders Dashboard
- New modular route file: `/backend/routes/replenishment.py`
- Testing: **100% (Iteration 25, 32/32 PASS)**

### Phase 24 — DOH Analysis Module (Apr 2026)
- **DOH-01–08**: DOH Calculation — store-SKU DOH = Inventory/ROS, zero inv (STOCKED_OUT), zero ROS (NO_SALES/9999), weighted avg DOH, channel-level DOH aggregation, category-level DOH, WH stock toggle (include_wh), store-only mode
- **DOH-09–15**: Classification — Optimal (±20% ideal), Overstocked (>120%), Understocked (<80%), Stocked Out, ideal_doh=9d default, category-specific ideal DOH (CRUD), topseller additional cover (multiplier)
- **DOH-16–21**: Heatmap — store grid color-coded by status, category grid, click drill-down with status % and detail, region filter, store class filter, heatmap export
- **DOH-22–27**: DOH vs Stock-Out Correlation — negative correlation (high DOH -> low stock-outs), trendline visualization, Pearson correlation coefficient, optimal DOH range identification via bucket analysis, store-level correlation
- **DOH-28–35**: Recommendations — low DOH (increase replenishment), high DOH (reduce orders), stocked out (expedite), bulk low DOH, category-wide issues, store-wide issues (>30% SO or >50% understocked), seasonal adjustment, DOH target setting suggestion
- New modular route file: `/backend/routes/doh_analysis.py`
- Testing: **100% (Iteration 26, 35/35 PASS)**

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
| DOH Analysis | 35 | 35 | 0 | 0 | **100%** |
| **Total** | **274** | **263** | **5** | **6** | **96%** |

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
- Modularize server.py (~4200 lines) — partially done with core_logic.py, replenishment.py, doh_analysis.py
- Scheduled analysis jobs
- Tenant billing/usage tracking
