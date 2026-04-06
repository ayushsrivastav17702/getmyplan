# GetMyPlan - AI-Powered Retail Analytics Platform — PRD

## Original Problem Statement
Build a Fashion Retail Gap Analysis platform (now branded as **GetMyPlan**) with React + FastAPI featuring CSV data uploading, multiple analytics dashboards, dynamic filtering with presets, Chart.js visualizations, GPT-5.2 FAQ Chatbot, multi-tenant architecture, and role-based access control.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme)
- **Backend**: FastAPI with Python/Pandas
- **Database**: MongoDB (multi-tenant: separate DB per tenant, shared registry in merch_shared)
- **AI**: GPT 5.2 via Emergent LLM Key
- **Charts**: Chart.js + react-chartjs-2 (NO Recharts)
- **Auth**: JWT with bcrypt, RBAC with 8 built-in roles + custom roles + permission overrides
- **Email**: SMTP via Hostinger (smtp.hostinger.com:465, SSL, info@getmyplan.in)
- **Branding**: GetMyPlan (getmyplan.in)

## Completed Phases

### Phase 1-32 (Previous sessions)
- Full MVP analytics, filters, presets, 16+ analytics modules
- MongoDB Multi-Tenancy + RBAC + User Management
- Executive Dashboard, Data Upload, Configuration, Core Logics, Gap Analysis, Stock-Out, Replenishment, DOH, Planogram, BI Dashboards, Warehouse, SFTP, Data Quality, FAQ Chatbot
- AI Demand Planning System (ML Forecast Engine)
- DASH-35 PDF Export, TENANT-20 Tenant Branding

### Phase 33 — AI Buy Plan Generator (Apr 2026)
- 4-step Wizard, ML-powered Plan Generation, Charts, Tables, Excel Workbook, History

### Phase 34 — TenantDataProvider Refactoring (Apr 2026)
- Core service for all analytics, `data_source` field in responses

### Phase 35 — Onboarding Wizard (Apr 2026)
- 3-step wizard: Marketplaces → Stores → Category Taxonomy

### Phase 36 — Onboarding-to-Analytics Integration (Apr 2026)
- TenantDataProvider merges onboarding data as fallback

### Phase 37 — Deployment Health Check (Apr 2026)
- Security fix for JWT_SECRET, all checks passed

### Phase 38 — Self-Service Signup with Email Verification & Trial (Apr 2026)
- `/api/signup/register`, `/verify-email`, `/resend-verification`
- SMTP email service with verification & welcome emails
- 7-day trial, 3-day grace period, trial_info in login response
- Signup wizard, VerifyEmail page, TrialBanner
- Testing: **96% (Iteration 42, 24/25 PASS)**

### Phase 39 — GetMyPlan Rebranding (Apr 2026)
- Replaced ALL "Increff Analytics" / "Merchandising Tool" with "GetMyPlan"
- Updated: LoginPage, Signup, CoreLogics, OnboardingWizard, ExecutiveDashboard, App.js sidebar, index.html, server.py, email templates, .env
- Added password reset email template
- Testing: **100% (Iteration 43, 27/27 PASS)**

## Key API Endpoints

### Signup (PUBLIC)
- `POST /api/signup/register`, `/verify-email`, `/resend-verification`

### Auth (Enhanced with trial checking)
- `POST /api/auth/login` — returns `trial_info` for trial tenants

### Onboarding
- `GET /api/onboarding/status`, CRUD for marketplaces/stores/categories

### Analytics
- `GET /api/analytics/ai-demand/options`, `/filter-options`, `/buy-plan/options`

## Prioritized Backlog

### P1
- SFTP alert/notification system (SFTP-31 to SFTP-34)

### P2
- USER-17: Force password change on first login
- Plan upgrade page for trial users
- Scheduled analysis jobs

### P3
- USER-18: MFA
- TENANT-10: Tenant backup/restore
- TENANT-31: Invoice generation
- Data Quality Rules Engine
