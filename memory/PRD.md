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
- **PlanGuard Applied to All Routes**:
  - 13 routes wrapped with `<PlanGuard module="...">` in App.js
  - Sidebar nav shows lock icons (locked modules) and "View" badges (view-only)
  - Starter: 7 full, 3 view-only, 3 locked | Professional/Enterprise: all full
  - PlanGuard reads planInfo from AuthContext automatically
- **SFTP Alert/Notification System**:
  - Backend: `/api/notifications` CRUD routes (get, unread-count, mark-read, mark-all-read, clear, trigger-daily-summary)
  - Alert triggers: upload failures, malformed files, processing errors, SLA misses, daily summary
  - Email alerts for critical/warning severity (via Hostinger SMTP)
  - Slack webhook integration (optional, via SLACK_WEBHOOK_URL env var)
  - Frontend: `NotificationBell` component with badge count, dropdown panel, mark-all-read
  - Polls unread count every 30 seconds
- **Tour Resume**: ProductTour saves progress to sessionStorage, resumes on reopen
- **Testing: 30/30 PASS (Iteration 48)** — Backend 12/12, Frontend 18/18

## Route Map
```
UNAUTHENTICATED:
  /           -> Marketing Landing Page (12 sections + Product Tour)
  /login      -> Login Page
  /signup     -> Signup Page (2-step wizard)
  /verify-email -> Email Verification

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
```

## Key Files
- `/app/frontend/src/components/landing/*` — 13 landing page components (incl. ProductTour)
- `/app/frontend/src/components/PlanGuard.jsx` — Plan-based module access guard + NAV_PLAN_MODULE_MAP
- `/app/frontend/src/components/NotificationBell.jsx` — Dashboard notification bell + panel
- `/app/frontend/src/App.js` — Routing with PlanGuard wrapping + NotificationBell
- `/app/backend/routes/notification_routes.py` — Notification CRUD + alert triggers
- `/app/backend/core/plan_access.py` — Plan-based module access definitions
- `/app/backend/routes/sftp_routes.py` — SFTP routes with notification triggers

## Prioritized Backlog

### P2
- USER-17: Force password change on first login
- Plan upgrade page for trial users
- Scheduled analysis jobs

### P3
- USER-18: MFA
- TENANT-10: Tenant backup/restore
- TENANT-31: Invoice generation
- Data Quality Rules Engine
