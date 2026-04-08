# GetMyPlan - AI-Powered Retail Analytics Platform — PRD

## Original Problem Statement
Build a Fashion Retail Gap Analysis platform (branded as **GetMyPlan**) with React + FastAPI featuring CSV data uploading, multiple analytics dashboards, dynamic filtering with presets, Chart.js visualizations, GPT-5.2 FAQ Chatbot, multi-tenant architecture, and role-based access control.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme for dashboard, Enterprise SaaS for marketing)
- **Backend**: FastAPI with Python/Pandas
- **Database**: MongoDB (multi-tenant: separate DB per tenant, shared registry in merch_shared)
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
- **USER-17: Force Password Change on First Login**:
  - Admin password reset sets `must_change_password: true` on user
  - Login response includes `must_change_password` flag
  - Frontend blocks all routes and shows `ChangePassword.jsx` page
  - POST `/api/auth/change-password` validates old password, sets new, clears flag
  - AuthContext tracks `mustChangePassword` state
- **Plan Upgrade Page**:
  - GET `/api/tenants/{id}/plan-usage` returns plan type, limits, usage stats
  - Frontend shows current plan banner, usage metrics, plan comparison cards
  - INR/USD currency toggle, upgrade request flow (MOCKED - no payment gateway)
- **Scheduled Analysis Jobs**:
  - Full CRUD: POST/GET/PUT/DELETE `/api/scheduled-jobs/`
  - Toggle active, run-now, execution history endpoints
  - 8 analysis types, 3 frequencies (daily/weekly/monthly)
  - Frontend: job list cards, create form with conditional fields, action buttons
- **Testing: 40/40 PASS (Iteration 49)** — Backend 23/23, Frontend 17/17

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
  /data-quality -> Data Quality (no PlanGuard)
  /chatbot    -> FAQ Chatbot (no PlanGuard)
  /users      -> User Management (RBAC only)
  /tenant-admin -> Tenant Admin (RBAC only)
  /plan-upgrade -> Plan & Billing (all users)
  /scheduled-jobs -> Scheduled Jobs (all users)
```

## Key Files
- `/app/frontend/src/components/landing/*` — 13 landing page components (incl. ProductTour)
- `/app/frontend/src/components/PlanGuard.jsx` — Plan-based module access guard
- `/app/frontend/src/components/NotificationBell.jsx` — Dashboard notification bell
- `/app/frontend/src/pages/ChangePassword.jsx` — Force password change page
- `/app/frontend/src/pages/PlanUpgrade.jsx` — Plan comparison + upgrade page
- `/app/frontend/src/pages/ScheduledJobs.jsx` — Scheduled jobs management
- `/app/frontend/src/context/AuthContext.js` — JWT/Tenant state + mustChangePassword
- `/app/frontend/src/App.js` — Routing with PlanGuard + force password redirect
- `/app/backend/multi_tenant/auth.py` — Login + change-password endpoint
- `/app/backend/multi_tenant/user_routes.py` — Admin password reset (sets flag)
- `/app/backend/multi_tenant/tenant_routes.py` — Plan usage endpoint
- `/app/backend/routes/scheduled_jobs.py` — Scheduled jobs CRUD
- `/app/backend/routes/notification_routes.py` — Notification CRUD + alert triggers
- `/app/backend/core/plan_access.py` — Plan-based module access definitions

## Prioritized Backlog

### P3
- USER-18: MFA (Multi-factor authentication)
- TENANT-10: Tenant backup/restore
- TENANT-31: Invoice generation
- Data Quality Rules Engine (Tenant-specific custom validation rules)
