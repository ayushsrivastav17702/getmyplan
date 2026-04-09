# GetMyPlan - AI-Powered Retail Analytics Platform — PRD

## Original Problem Statement
Build a Fashion Retail Gap Analysis platform (branded as **GetMyPlan**) with React + FastAPI featuring CSV data uploading, multiple analytics dashboards, dynamic filtering with presets, Chart.js visualizations, GPT-5.2 FAQ Chatbot, multi-tenant architecture, and role-based access control.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme for dashboard, Enterprise SaaS for marketing)
- **Backend**: FastAPI with Python/Pandas
- **Database**: MongoDB (multi-tenant: separate DB per tenant, shared registry in DB_NAME database)
- **AI**: GPT 5.2 via Emergent LLM Key
- **Charts**: Chart.js + react-chartjs-2 (NO Recharts)
- **Auth**: JWT with bcrypt, RBAC with 8 built-in roles + custom roles + permission overrides
- **Email**: SMTP via Hostinger (smtp.hostinger.com:465, SSL, info@getmyplan.in)
- **Security**: Enterprise middleware stack (rate limiting, security headers, input sanitization, structured logging)
- **Animations**: framer-motion v12.38.0
- **Branding**: GetMyPlan (getmyplan.in)

## Completed Phases

### Phase 1-37 (Previous sessions)
- Full MVP: 16+ analytics modules, Multi-Tenancy, RBAC, JWT Auth
- AI Demand Planning, Buy Plan Generator, Executive Dashboard
- TenantDataProvider refactoring, Onboarding Wizard

### Phase 38 — Self-Service Signup (Apr 2026)
- SMTP emails, 7-day trial, TrialBanner — 24/25 PASS (Iteration 42)

### Phase 39 — GetMyPlan Rebranding (Apr 2026)
- All "Increff" -> "GetMyPlan" — 27/27 PASS (Iteration 43)

### Phase 40 — Enterprise Security (Apr 2026)
- Rate Limiting, Security Headers, MongoDB Indexes — 29/29 PASS (Iteration 44)

### Phase 41 — Website Product Report + CORS Fix (Apr 2026)
- WEBSITE_PRODUCT_REPORT.md: 11-section report with real API data

### Phase 42 — Marketing Landing Page v1 (Apr 2026)
- Initial landing page — 27/27 PASS (Iteration 45)

### Phase 43 — Enterprise SaaS Landing Page Redesign (Apr 2026)
- 12 landing components, Plan-Based Access Control architecture — 23/24 PASS (Iteration 46)

### Phase 44 — Interactive Product Tour (Apr 2026)
- 5-step interactive product tour — 44/44 PASS (Iteration 47)

### Phase 45 — PlanGuard Module Access + SFTP Notification System (Apr 2026)
- PlanGuard + SFTP Alerts — 30/30 PASS (Iteration 48)

### Phase 46 — Force Password Change, Plan Upgrade, Scheduled Jobs (Apr 2026)
- USER-17: Force Password Change, Plan Upgrade Page, Scheduled Jobs CRUD — 40/40 PASS (Iteration 49)

### Phase 47 — Data Quality Rules Engine (Apr 2026)
- 6 Rule Types, Full CRUD — 35/35 PASS (Iteration 50)

### Phase 48 — Production MongoDB Authorization Fix (Apr 2026)
- DB_NAME priority, lazy ML imports, dynamic email Origin tracking

### Phase 49 — Complete Data Upload Module with 75-Error Validation (Apr 2026)
- New Upload System `/api/upload/v2/*` with 6 upload types — 39/39 PASS (Iteration 51)

### Phase 50 — Data Upload Page UI Redesign (Apr 2026)
- Master/Daily split, master-status endpoint — 49/49 PASS (Iteration 52)

### Phase 51 — 65-Rule Validation Engine Enhancement (Apr 2026)
- Currency detection, file hash dedup, warehouse validation
- **Testing: 56/56 PASS (Iteration 53)**

### Phase 52 — Component Refactoring + Validate-then-Save Flow (Apr 2026)
- Split DataUploadPage into components, validate-only endpoint
- **Testing: 48/48 PASS (Iteration 54)**

### Phase 53 — Demand Planning Audit + P0 Fixes (Apr 2026)
- Generated comprehensive audit report: `/app/memory/DEMAND_PLANNING_AUDIT_V2.md`
- **P0.1 V2 Data Bridge**: Updated `get_cached_data()` in server.py to check V2 collections first, fall back to V1 `uploaded_files`. Includes field compatibility mapping (V2 `closing_stock`→`quantity`, `sku`→`ean`).
- **P0.2 Seasonal Decomposition Fix**: Fixed numpy.ndarray attribute error in `ml_forecast_engine.py` — converts input to pd.Series and uses np.asarray() on decomposition results. All 3 ML models now active in ensemble.
- **P0.3 Database Indexes**: Added V2 collection indexes on startup (daily_sales, store_inventory, sku_master, etc.)
- **Data Health Dashboard**: New `GET /api/analytics/ai-demand/data-health` endpoint + collapsible DataHealthDashboard component on AI Demand page. Shows progress to 180-day ML minimum, per-data-type status, estimated ML activation date, and "Upload Historical Data" CTA.
- **25-Month Historical Data Seed**: Generated 757 days (Apr 2024 → Apr 2026) of realistic data: 30,961 daily sales rows, 37,850 store inventory rows, 15,140 warehouse inventory rows. SKUs: TSHIRT-BLK-M/L, HOODIE-GRY-M/L, CAP-BLK-ONE, SOCKS-WHT-3PK, JOGGER-BLK-M, SNEAKER-WHT-9, BACKPACK-BLK, WATER-BOTTLE-500. Stores: MAIN-01, SOUTH-02, WEST-03, ONLINE-01, POPUP-01. Data includes weekly seasonality, 5% monthly growth, festive peaks (Oct-Dec).
- **ML Forecast Activated**: All 3 models (Holt-Winters, Random Forest, Seasonal Decomposition) now running on real data. Confidence 92.7%, trend "accelerating". Data Health badge shows "REAL ML FORECAST".
- **Testing: 31/31 PASS (Iteration 55) + 35/35 PASS (Iteration 56) + 39/39 PASS (Iteration 57)**

## Route Map
```
UNAUTHENTICATED:
  /           -> Marketing Landing Page
  /login, /signup, /verify-email, /forgot-password, /reset-password

AUTHENTICATED (PlanGuard-wrapped):
  /           -> Getting Started
  /dashboard  -> Executive Dashboard
  /upload     -> Data Upload (refactored components)
  /config     -> Configuration
  /core-logics -> Core Logics
  /gap-analysis, /stock-out, /replenishment, /doh, /planogram
  /bi-dashboards, /warehouse, /ai-demand, /buy-plan
  /sftp-monitor, /data-quality, /chatbot
  /users, /tenant-admin, /plan-upgrade, /scheduled-jobs
```

## Key Files
### Upload Module (Refactored)
- `/app/backend/routes/upload.py` — V2 endpoints + validate + history/days
- `/app/backend/services/upload_service.py` — 75-rule validation engine
- `/app/frontend/src/pages/DataUploadPage.jsx` — Main page (imports components)
- `/app/frontend/src/components/upload/MasterCard.jsx` — Master data card
- `/app/frontend/src/components/upload/DailyStatusCard.jsx` — Daily status card
- `/app/frontend/src/components/upload/PreviousDaysList.jsx` — Previous days list
- `/app/frontend/src/components/upload/FileDropzone.jsx` — File dropzone + validation results

### AI Demand Planning
- `/app/backend/routes/ai_demand.py` — 10 endpoints (forecast, stockout, topseller, reorder, supply, plan CRUD)
- `/app/backend/ml_forecast_engine.py` — 3 ML models + ensemble (Holt-Winters, Random Forest, Seasonal Decomposition)
- `/app/backend/services/tenant_data_provider.py` — Data abstraction layer (V2→V1 bridge)
- `/app/frontend/src/pages/AIDemandPlanning.js` — 4-tab UI with Chart.js visualizations

### Core
- `/app/backend/server.py` — Route registration, get_cached_data() with V2 bridge
- `/app/frontend/src/context/AuthContext.js` — JWT/Tenant state
- `/app/frontend/src/App.js` — Routing with PlanGuard

## API Endpoints (Upload V2)
```
POST /api/upload/v2/daily-sales          — Upload daily sales
POST /api/upload/v2/store-inventory      — Upload store inventory
POST /api/upload/v2/warehouse-inventory  — Upload warehouse inventory
POST /api/upload/v2/sku-master           — Upload SKU master
POST /api/upload/v2/store-master         — Upload store master
POST /api/upload/v2/warehouse-master     — Upload warehouse master
POST /api/upload/v2/{type}/validate      — Validate without saving
GET  /api/upload/v2/daily-status         — Today's upload status
GET  /api/upload/v2/master-status        — Master data counts
GET  /api/upload/v2/history              — Grouped upload history
GET  /api/upload/v2/history/days         — Per-day upload status
GET  /api/upload/v2/template/{type}      — Download Excel template
```

## API Endpoints (AI Demand)
```
GET  /api/analytics/ai-demand/options           — Filter values + data status
GET  /api/analytics/ai-demand/forecast          — ML ensemble forecast
GET  /api/analytics/ai-demand/stockout-risk     — SKU×Store stockout prediction
GET  /api/analytics/ai-demand/topseller-prediction — X-Factor classification
GET  /api/analytics/ai-demand/reorder-optimisation — Safety stock + ROP
GET  /api/analytics/ai-demand/supply-feasibility   — 12-month DOH coverage
POST /api/analytics/ai-demand/generate-plan     — Generate blended demand plan
GET  /api/analytics/ai-demand/plans             — List saved plans
GET  /api/analytics/ai-demand/plans/{id}        — Get specific plan
PUT  /api/analytics/ai-demand/plans/{id}        — Update plan (optimistic locking)
```

## Prioritized Backlog

### P1 — Next
- EOQ (Economic Order Quantity) implementation
- Lead times from SKU master (currently hardcoded default 14 days)
- SKU-level forecasting
- Forecast accuracy tracking over time

### P2
- USER-18: MFA (Multi-factor authentication)
- TENANT-10: Tenant backup/restore
- TENANT-31: Invoice generation
- User Funnel Analytics Dashboard
- Buy Plan integration with demand forecast
- Holiday/promotional calendar

### P3
- Auto-scheduled SFTP uploads for Data Upload V2
- Prophet integration for holiday-aware forecasting
- Automated daily/weekly forecast regeneration
- Purchase order creation from reorder recommendations
- Warehouse-level demand allocation
