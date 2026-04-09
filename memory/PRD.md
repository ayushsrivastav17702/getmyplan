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
- Implemented comprehensive validation rules: E003, E004, E006, E007, E008, E010, E011, E020, E027, E030, E039, E041, E043, E045, E049, E054, E066, E067, E068, E069, MIXED_CURRENCY, AUTO_CALC
- Currency detection (USD/INR/EUR/GBP) with mixed currency warnings
- File size check (E049), duplicate file hash detection (E054)
- Warehouse inventory validation: available>on_hand (E067), allocated_qty auto-calc
- Warehouse master flag validation (E069)
- Master data cross-validation against v2 collections
- **Testing: 56/56 PASS (Iteration 53)** — Backend 40/40, Frontend 16/16

### Phase 52 — Component Refactoring + Validate-then-Save Flow (Apr 2026)
- Split DataUploadPage into separate components: MasterCard, DailyStatusCard, PreviousDaysList, FileDropzone
- New `/api/upload/v2/{upload_type}/validate` endpoint for validate-only mode
- New `/api/upload/v2/history/days` endpoint for per-day upload status
- Two-step upload flow: Validate File -> Proceed to Save -> Save confirmation
- **Testing: 48/48 PASS (Iteration 54)** — Backend 28/28, Frontend 20/20

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
- `/app/frontend/src/components/upload/FileDropzone.jsx` — File dropzone + validation results + save confirm

### Core
- `/app/backend/server.py` — Route registration, MONGODB_URI sync
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

## Prioritized Backlog

### P2
- USER-18: MFA (Multi-factor authentication)
- TENANT-10: Tenant backup/restore
- TENANT-31: Invoice generation
- User Funnel Analytics Dashboard

### P3
- Auto-scheduled SFTP uploads for Data Upload V2
