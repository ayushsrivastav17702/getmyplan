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
- V2 Data Bridge, Seasonal Decomposition Fix, Data Health Dashboard, 25-month seed data
- **Testing: 43/43 PASS (Iteration 58)**

### Phase 54 — P1 Enterprise Features (Apr 2026)
- EOQ, Per-SKU Lead Times, SKU-level Forecasting
- **Testing: 43/43 PASS (Iteration 58)**

### Phase 55 — Technical Audit Documents (Apr 2026)
- `CORE_ALGORITHMS_AUDIT.md` — Parts 4-9: Core Algorithms, Backend Architecture, Frontend, Scalability, Gaps
- `DATA_INFRASTRUCTURE_AUDIT.md` — Parts 1-3: Data Upload Infrastructure, Master Data Management, Transactional Data

## Audit Documents
- `/app/memory/CORE_ALGORITHMS_AUDIT.md` — Parts 4-9 (204 lines)
- `/app/memory/DATA_INFRASTRUCTURE_AUDIT.md` — Parts 1-3 (168 lines)
- `/app/memory/DEMAND_PLANNING_AUDIT_V2.md` — Original demand planning audit

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

## Prioritized Backlog

### P1 — Next
- Forecast accuracy tracking over time (MAPE trend)
- Holiday/promotional calendar integration
- Address gaps identified in audit (COGS/margin, PO tracking, planogram management)

### P2
- USER-18: MFA (Multi-factor authentication)
- TENANT-10: Tenant backup/restore
- TENANT-31: Invoice generation
- User Funnel Analytics Dashboard
- Buy Plan integration with demand forecast
- Custom validation rules per tenant (wire Data Quality Rules into upload pipeline)

### P3
- Auto-scheduled SFTP uploads for Data Upload V2
- Prophet integration for holiday-aware forecasting
- Automated daily/weekly forecast regeneration
- Purchase order creation from reorder recommendations
- Warehouse-level demand allocation
- Chunked file uploads for >50MB files
- Async upload processing with job queues
- Pre-computed aggregation tables for analytics performance
