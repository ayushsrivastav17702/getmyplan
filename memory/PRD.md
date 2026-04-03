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
- Testing: **100% (Iteration 25, 32/32 PASS)**

### Phase 24 — DOH Analysis Module (Apr 2026)
- DOH-01–35: DOH Calculation, Classification, Heatmap, DOH vs Stock-Out Correlation, Recommendations
- Testing: **100% (Iteration 26, 35/35 PASS)**

### Phase 25 — Planogram Fill Rate Module (Apr 2026)
- PLAN-01–32: Fill Rate Calculation, Store Performance, Category Performance, Gap Analysis, Dashboard
- Testing: **100% (Iteration 27, 32/32 PASS)**

### Phase 26 — BI Dashboards Module (Apr 2026)
- BI-01–35: Revenue Analytics, Category Analytics, Store Analytics, Trend Analysis, Custom Dashboards
- Testing: **100% (Iteration 27, 35/35 PASS)**

### Phase 27 — SFTP Monitor Enhancement (Apr 2026)
- 19 gap test cases resolved: Connection pool, retry backoff, SSL/TLS, upload/download, batch upload, malformed detection, duplicate handling, file archive, date filtering, error log CSV, speed metrics, daily summary
- Note: SFTP operations in **DEMO MODE** (MOCKED)
- Testing: **100% (Iteration 28, 25/25 PASS)**

### Phase 28 — Warehouse Module (Apr 2026)
- 30/30 test cases PASS: Stock, Movements, Transfers, Performance, Dashboard
- Testing: **100% (Iteration 29, 30/30 PASS)**

### Phase 29 — DASH-15 & DASH-25 (Apr 2026)
- DASH-15: Revenue Trend Line Chart, DASH-25: Offline Detection UI
- Testing: **100% (Iteration 30, 19/19 PASS)**

### Phase 30 — 51-Gap Fix (Apr 2026)
- Data Quality (17 gaps), FAQ Chatbot (4 gaps), User Management (16 gaps), Tenant Management (14 gaps)
- Testing: **100% (Iteration 31, 24/24 PASS)**

### Phase 31 — AI Demand Planning System (Apr 2026)
- ML Forecast Engine (Holt-Winters, Random Forest, Seasonal Decomposition)
- Stockout Prediction, Reorder Optimization, Demand Plan Generation
- 4-tab React workflow using Chart.js
- 25-Point Design Compliance: RBAC, Rate Limiting, Optimistic Locking, DOH, X-Factor
- Testing: **100% (Iterations 32-33)**

### Phase 32 — DASH-35 & TENANT-20 (Apr 2026)
- **DASH-35: PDF Export for Executive Dashboard**
  - `html2canvas` + `jsPDF` for client-side PDF generation
  - Export PDF button in dashboard header, disabled when no data
  - PDF includes header (title + timestamp), dashboard content, footer (confidential + page)
- **TENANT-20: Tenant Branding (Logo, Colors)**
  - Backend: `PUT/GET /api/tenants/{id}/branding` endpoints with hex validation
  - Frontend: New "Branding" tab in Tenant Admin Panel with color pickers, hex inputs, logo URL, live preview
  - Branding fetched during login and stored in AuthContext
  - Sidebar header, active nav items, tenant info bar use dynamic branding colors
  - Logo URL renders in sidebar header when set; company name shows when no logo
  - Metrics endpoint includes branding data
- Testing: **100% (Iteration 34, 20/20 PASS)**

## Test Coverage Summary

| Module | Total | PASS | % |
|--------|-------|------|---|
| Executive Dashboard | 35 | 35 | **100%** |
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
| Data Quality | 32 | 29 | **91%** |
| FAQ Chatbot | 35 | 31 | **89%** |
| User Management | 35 | 27 | **77%** |
| Tenant Management | 35 | 21 | **60%** |
| AI Demand Planning | 32 | 32 | **100%** |
| DASH-35 + TENANT-20 | 20 | 20 | **100%** |
| **Total** | **615** | **553** | **90%** |

## Remaining Known Gaps
- SFTP-31/32/33/34: Email/Slack alerts, dashboard notifications, alert thresholds (P1-P2)
- DQ-08: Completeness trend (basic, needs real historical data)
- CHAT-21: Message length limit, CHAT-23: Multi-language
- USER-05: Email change, USER-10: Profile image, USER-17: Force password change, USER-18: MFA, USER-34: IP whitelisting, USER-35: Session management
- TENANT-10: Restore from backup, TENANT-17/18: Backup isolation/resource limits, TENANT-24/25: Language, TENANT-31: Invoice generation

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
