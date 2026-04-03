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

### Phase 18 — Data Upload Validation (Feb 2026)
- File size limit, data type validation, null check, dedup, future date rejection, negative qty rejection, encoding detection, concurrent upload lock

### Phase 19 — Configuration Module (Feb 2026)
- CONF-01–32: Analysis parameters, module toggles, store classes, category hierarchies, custom roles, permission overrides

### Phase 20 — Core Logic Module (Feb 2026)
- CORE-01–35: ROS, Healthy Size Set, TrueROS, Attribute Grouping, Store-Style Ranking

### Phase 21 — Gap Analysis Module (Feb 2026)
- GAP-01–35: ROS Gap, Size Set Gap, NOOS Analysis, Dashboard

### Phase 22 — Stock-Out Analysis Module (Feb 2026)
- SO-01–35: Period trends, heatmaps, moving averages, predictive analysis, reorder recommendations

### Phase 23 — Replenishment Planner Module (Apr 2026)
- REP-01–32: Reorder Point Calculation, Order Quantity, IST Inter-Store Transfer

### Phase 24 — DOH Analysis Module (Apr 2026)
- DOH-01–35: DOH Calculation, Classification, Heatmap, Correlation, Recommendations

### Phase 25 — Planogram Fill Rate Module (Apr 2026)
- PLAN-01–32: Fill Rate Calculation, Store/Category Performance, Gap Analysis

### Phase 26 — BI Dashboards Module (Apr 2026)
- BI-01–35: Revenue Analytics, Category Analytics, Store Analytics, Trend Analysis

### Phase 27 — SFTP Monitor Enhancement (Apr 2026)
- 19 gap test cases: Connection pool, retry, SSL/TLS, batch upload, malformed detection (DEMO MODE)

### Phase 28 — Warehouse Module (Apr 2026)
- 30/30: Stock, Movements, Transfers, Performance, Dashboard

### Phase 29 — DASH-15 & DASH-25 (Apr 2026)
- Revenue Trend Line Chart, Offline Detection UI

### Phase 30 — 51-Gap Fix (Apr 2026)
- Data Quality (17), FAQ Chatbot (4), User Management (16), Tenant Management (14)

### Phase 31 — AI Demand Planning System (Apr 2026)
- ML Forecast Engine (Holt-Winters, Random Forest, Seasonal Decomposition)
- Stockout Prediction, Reorder Optimization, Demand Plan Generation
- 25-Point Design Compliance

### Phase 32 — DASH-35 & TENANT-20 (Apr 2026)
- DASH-35: PDF Export for Executive Dashboard (html2canvas + jsPDF)
- TENANT-20: Tenant Branding (Logo, Colors) with dynamic sidebar theming

### Phase 33 — AI Buy Plan Generator (Apr 2026)
- **4-step Configuration Wizard**: Revenue Target → Categories → Channels → Parameters
- **ML-powered Plan Generation**: Revenue-to-units conversion, seasonal phasing, channel splits, dynamic safety stock calculation
- **Interactive Results Dashboard**: KPI cards, Line chart (monthly forecast by category), Bar charts (required vs buy, channel breakdown)
- **Expandable Category Table**: ASP, contribution, required units, buy qty with channel/monthly drilldown
- **Editable Excel Workbook**: 5-sheet export (Executive Summary, Category, Monthly Plan, Buy Plan Editable, Instructions), upload with user overrides
- **Plan History**: Saved plans with timestamps, audit trail
- **Backend**: 5 endpoints (/generate, /export-excel, /upload-edited-plan, /history, /summary) with auth, rate limiting, tenant isolation
- Testing: **100% (Iteration 35, 28/28 PASS)**

## Key API Endpoints (Buy Plan)
- `POST /api/buy-plan/generate` — Generate complete buy plan
- `POST /api/buy-plan/export-excel` — Export as multi-sheet Excel
- `POST /api/buy-plan/upload-edited-plan` — Upload edited Excel with overrides
- `GET /api/buy-plan/history` — Get saved plan history
- `GET /api/buy-plan/summary` — Get categories, channels, defaults

## Prioritized Backlog

### P1
- SFTP alert/notification system (SFTP-31 to SFTP-34)

### P2
- USER-05: Email change, USER-17: Force password change
- Scheduled analysis jobs
- Tenant billing/usage tracking

### P3
- USER-18: MFA
- TENANT-10: Tenant backup/restore
- TENANT-31: Invoice generation
