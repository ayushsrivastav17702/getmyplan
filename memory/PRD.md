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
- DOH-01–35: DOH Calculation, Classification, Heatmap, DOH vs Stock-Out Correlation, Recommendations
- New modular route file: `/backend/routes/doh_analysis.py`
- Testing: **100% (Iteration 26, 35/35 PASS)**

### Phase 25 — Planogram Fill Rate Module (Apr 2026)
- PLAN-01–32: Fill Rate Calculation, Store Performance, Category Performance, Gap Analysis, Dashboard
- New modular route file: `/backend/routes/planogram.py`
- Testing: **100% (Iteration 27, 32/32 PASS)**

### Phase 26 — BI Dashboards Module (Apr 2026)
- BI-01–35: Revenue Analytics, Category Analytics, Store Analytics, Trend Analysis, Custom Dashboards
- New modular route file: `/backend/routes/bi_dashboard.py`
- Testing: **100% (Iteration 27, 35/35 PASS)**

### Phase 27 — SFTP Monitor Enhancement (Apr 2026)
- 19 gap test cases resolved: Connection pool, retry backoff, SSL/TLS, upload/download, batch upload, malformed detection, duplicate handling, file archive, date filtering, error log CSV, speed metrics, daily summary
- New route file: `/backend/routes/sftp_routes.py`
- Enhanced: sftp_service.py (ConnectionPool, TransferTracker), sftp_scheduler.py
- Frontend: 5-tab layout (Overview, Transfers, Logs, Speed Metrics, Daily Summary)
- Testing: **100% (Iteration 28, 25/25 PASS)**
- Note: SFTP operations in **DEMO MODE** (MOCKED)

### Phase 28 — Warehouse Module (Apr 2026)
- **30/30 test cases PASS**:
  - **WH-01..08 Stock**: View stock levels, filter by warehouse/category, search by SKU/style, stock value calculation (Qty x MRP), low stock alert (<50 units), out of stock (=0), overstock (>500)
  - **WH-09..14 Movements**: Inbound/outbound tracking with timeline, daily stock change (opening vs closing), stock reconciliation (system vs physical), stock adjustment log (who changed what)
  - **WH-15..20 Transfers**: Create transfer order, allocate stock, multi-step approval workflow, track in-transit inventory, receive transfer, transfer history audit trail
  - **WH-21..25 Performance**: Order fulfillment rate (%), avg dispatch time (hours), warehouse turnover (COGS/Avg Inv), storage utilization (% capacity), slow-moving stock (90+ days no sales)
  - **WH-26..30 Dashboard**: KPI cards (Total Stock, Stock Value, SKUs, Warehouses), stock by category chart, stock movement trend (inbound/outbound), CSV export, multi-warehouse comparison table
- New route file: `/backend/routes/warehouse.py`
- Frontend: 5-tab layout (Dashboard, Stock, Movements, Transfers, Performance)
- Testing: **100% (Iteration 29, 30/30 PASS)**

## Test Coverage Summary

| Module | Total | PASS | % |
|--------|-------|------|---|
| Executive Dashboard | 35 | 29 | 83% |
| Data Upload | 35 | 30 | 86% |
| Configuration | 32 | 32 | **100%** |
| Core Logic | 35 | 35 | **100%** |
| Gap Analysis | 35 | 35 | **100%** |
| Stock-Out Analysis | 35 | 35 | **100%** |
| Replenishment Planner | 32 | 32 | **100%** |
| DOH Analysis | 35 | 35 | **100%** |
| Planogram Fill Rate | 32 | 32 | **100%** |
| BI Dashboards | 35 | 35 | **100%** |
| SFTP Monitor | 35 | 27 | 94% |
| Warehouse | 30 | 30 | **100%** |
| **Total** | **426** | **387** | **91%** |

## Remaining Known Gaps
- DASH-15: Revenue trend line chart (P0)
- DASH-25: Offline detection UI (P1)
- DASH-35: PDF export (P2)
- SFTP-31/32/33/34: Email/Slack alerts, dashboard notifications, alert thresholds (P1-P2)

## Prioritized Backlog

### P0
- DASH-15: Revenue trend line chart

### P1
- DASH-25: Offline detection UI
- SFTP alert/notification system (SFTP-31 to SFTP-34)
- Modularize server.py — move Gap Analysis & Stock-Out endpoints to routes/

### P2
- DASH-35: PDF export
- Scheduled analysis jobs
- Tenant billing/usage tracking
