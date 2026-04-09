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
- CORS lockdown + query projection fix

### Phase 42 — Marketing Landing Page v1 (Apr 2026)
- Initial landing page — 27/27 PASS (Iteration 45)

### Phase 43 — Enterprise SaaS Landing Page Redesign (Apr 2026)
- 12 landing components, Plan-Based Access Control architecture
- **Testing: 23/24 PASS (Iteration 46)**

### Phase 44 — Interactive Product Tour (Apr 2026)
- 5-step interactive product tour (Upload, Dashboard, Forecast, Stock-Out, Buy Plan)
- Auto-play, keyboard nav, sessionStorage resume
- **Testing: 44/44 PASS (Iteration 47)**

### Phase 45 — PlanGuard Module Access + SFTP Notification System (Apr 2026)
- PlanGuard applied to 13 routes with Starter/Professional/Enterprise tiers
- SFTP Alert/Notification System with email + Slack webhooks
- **Testing: 30/30 PASS (Iteration 48)**

### Phase 46 — P2 Features: Force Password Change, Plan Upgrade, Scheduled Jobs (Apr 2026)
- USER-17: Force Password Change on First Login
- Plan Upgrade Page with usage stats + plan comparison
- Scheduled Analysis Jobs — full CRUD with daily/weekly/monthly frequencies
- **Testing: 40/40 PASS (Iteration 49)** — Backend 23/23, Frontend 17/17

### Phase 47 — Data Quality Rules Engine (Apr 2026)
- **6 Rule Types**: threshold, null_check, pattern, uniqueness, cross_reference, range
- **Backend**: Full CRUD at `/api/quality/rules/` with evaluate, toggle, file-columns endpoints
- **Frontend**: "Custom Rules" tab in Data Quality page
- **Testing: 35/35 PASS (Iteration 50)** — Backend 20/20, Frontend 15/15

### Phase 48 — Production MongoDB Authorization Fix (Apr 2026)
- Critical Fix: DB_NAME priority over SHARED_DB_NAME
- OperationFailure handling, lazy ML imports, dynamic email Origin tracking

### Phase 49 — Complete Data Upload Module with 75-Error Validation (Apr 2026)
- **New Upload System** at `/api/upload/v2/*` with 6 upload types
- **75-Error Validation Engine**: E001-E075 across 10 categories
- **Upload History**, **Daily Status Widget**, **Template Download**
- **Testing: 39/39 PASS (Iteration 51)**

### Phase 50 — Data Upload Page UI Redesign (Apr 2026)
- Redesigned DataUploadPage.jsx to explicitly separate "Master Data" (Setup Once) from "Daily Transactional Data"
- New `/api/upload/v2/master-status` endpoint returning counts and last_updated for sku_master, store_master, warehouse_master
- Master Data section: 3 cards with count, last_updated, download/upload buttons
- Today's Status section: 3 daily cards with Uploaded/Not Uploaded badges
- Upload New Data section: 6-option dropdown + react-dropzone
- Previous Days section: Grouped upload history
- **Testing: 49/49 PASS (Iteration 52)** — Backend 30/30, Frontend 19/19

## Route Map
```
UNAUTHENTICATED:
  /           -> Marketing Landing Page (12 sections + Product Tour)
  /login      -> Login Page
  /signup     -> Signup Page (2-step wizard, uses native fetch)
  /verify-email -> Email Verification
  /forgot-password -> Forgot Password
  /reset-password -> Reset Password

FORCE PASSWORD CHANGE (blocks all other routes):
  /*          -> ChangePassword (when mustChangePassword=true)

AUTHENTICATED (All routes PlanGuard-wrapped):
  /           -> Getting Started (Dashboard Home)
  /dashboard  -> Executive Dashboard [PlanGuard: dashboard]
  /upload     -> Data Upload [PlanGuard: data_upload]
  /config     -> Configuration [PlanGuard: config]
  /core-logics -> Core Logics [PlanGuard: topseller]
  /gap-analysis -> Gap Analysis [PlanGuard: gap_analysis]
  /stock-out  -> Stock-Out Analysis [PlanGuard: stock_out]
  /replenishment -> Replenishment [PlanGuard: replenishment]
  /doh        -> DOH Analysis [PlanGuard: doh_analysis]
  /planogram  -> Planogram Fill Rate [PlanGuard: planogram]
  /bi-dashboards -> BI Dashboards [PlanGuard: multi_channel]
  /warehouse  -> Warehouse [PlanGuard: warehouse]
  /ai-demand  -> AI Demand Planning [PlanGuard: ai_forecasting]
  /buy-plan   -> Buy Plan Generator [PlanGuard: buy_plan]
  /sftp-monitor -> SFTP Monitor (no PlanGuard)
  /data-quality -> Data Quality & SLA (with Custom Rules tab)
  /chatbot    -> FAQ Chatbot (no PlanGuard)
  /users      -> User Management (RBAC only)
  /tenant-admin -> Tenant Admin (RBAC only)
  /plan-upgrade -> Plan & Billing (all users)
  /scheduled-jobs -> Scheduled Jobs (all users)
```

## Key Files
- `/app/backend/multi_tenant/tenant_db.py` — DB resolution (DB_NAME-first priority)
- `/app/backend/routes/upload.py` — V2 upload endpoints + master-status + daily-status
- `/app/backend/services/upload_service.py` — 75-rule validation engine
- `/app/frontend/src/pages/DataUploadPage.jsx` — Redesigned upload page (Master/Daily split)
- `/app/backend/routes/data_quality_rules.py` — Rules Engine CRUD + evaluate
- `/app/frontend/src/components/DataQualityRules.jsx` — Rules Engine UI component
- `/app/backend/routes/scheduled_jobs.py` — Scheduled jobs CRUD
- `/app/frontend/src/pages/ScheduledJobs.jsx` — Scheduled jobs management
- `/app/frontend/src/context/AuthContext.js` — JWT/Tenant state + mustChangePassword
- `/app/frontend/src/App.js` — Routing with PlanGuard + force password redirect

## Prioritized Backlog

### P2
- USER-18: MFA (Multi-factor authentication)
- TENANT-10: Tenant backup/restore
- TENANT-31: Invoice generation
- User Funnel Analytics Dashboard

### P3
- Auto-scheduled SFTP uploads for Data Upload V2
