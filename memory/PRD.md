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
- **Email**: SMTP via Hostinger (smtp.hostinger.com:465, SSL)
- **Service Layer**: TenantDataProvider (`/backend/services/tenant_data_provider.py`) — single source of truth for tenant data with onboarding fallback

## Completed Phases

### Phase 1-32 (Previous sessions)
- Full MVP analytics, filters, presets, 16+ analytics modules
- MongoDB Multi-Tenancy + RBAC + User Management
- Executive Dashboard, Data Upload, Configuration, Core Logics, Gap Analysis, Stock-Out, Replenishment, DOH, Planogram, BI Dashboards, Warehouse, SFTP, Data Quality, FAQ Chatbot
- AI Demand Planning System (ML Forecast Engine)
- DASH-35 PDF Export, TENANT-20 Tenant Branding

### Phase 33 — AI Buy Plan Generator (Apr 2026)
- 4-step Wizard, ML-powered Plan Generation, Charts, Tables, Excel Workbook, History
- Testing: **100% (Iteration 35, 28/28 PASS)**

### Phase 34 — TenantDataProvider Refactoring (Apr 2026)
- Phase 1-5: Core service, Buy Plan, AI Demand, Gap Analysis, remaining modules refactored
- `data_source` field in all analytics responses
- Testing: **100% (Iteration 37, 36/36 PASS)**

### Phase 35 — Onboarding Wizard (Apr 2026)
- 3-step wizard: Marketplaces → Stores → Category Taxonomy
- Full CRUD APIs: `ob_marketplaces`, `ob_stores`, `ob_categories` collections
- Auto-onboarding for existing tenants with uploaded data
- RequireOnboarding guard for non-onboarded tenants
- Testing: **100% (Iteration 38, 31/31 PASS)**

### Phase 36 — Onboarding-to-Analytics Integration (Apr 2026)
- TenantDataProvider merges onboarding data as fallback
- Testing: **100% (Iteration 39, 15/15 PASS)**

### Phase 37 — Deployment Health Check (Apr 2026)
- Security fix: Removed hardcoded JWT_SECRET fallback
- Deployment agent: All checks passed

### Phase 38 — Self-Service Signup with Email Verification & Trial (Apr 2026)
- **Backend**: `/api/signup/register`, `/verify-email`, `/resend-verification`
- **SMTP Email Service**: Hostinger SMTP with verification & welcome emails, mock fallback
- **Trial System**: 7-day trial, 3-day grace period, trial_info in login response
- **Frontend**: 2-step Signup wizard, VerifyEmail page, TrialBanner, "Start free trial" link
- **Coexistence**: Existing tenants (demo, acme_corp) unaffected, no trial_info returned
- Testing: **96% (Iteration 42, 24/25 PASS, 1 PARTIAL expected)**

## Key API Endpoints

### Signup (PUBLIC — no tenant context required)
- `POST /api/signup/register` — Create user + tenant, send verification email
- `POST /api/signup/verify-email` — Verify token, activate user + tenant
- `POST /api/signup/resend-verification` — Resend email (60s rate limit)

### Onboarding
- `GET /api/onboarding/status` — Progress, current step, is_onboarded
- `POST/GET/DELETE /api/onboarding/marketplaces` — Marketplace CRUD
- `POST/GET/DELETE /api/onboarding/stores` — Store CRUD with marketplace mapping
- `POST/GET/DELETE /api/onboarding/categories` — Category taxonomy CRUD (nested tree)
- `POST /api/onboarding/skip`, `/complete`, `/reset`

### Auth (Enhanced)
- `POST /api/auth/login` — Login with trial checking (returns trial_info for trial tenants)

### Analytics Options (TenantDataProvider-powered with onboarding fallback)
- `GET /api/analytics/ai-demand/options`
- `GET /api/analytics/filter-options`
- `GET /api/buy-plan/options`

## Key DB Collections (New)
- `merch_shared.users` — Added: `email_verified`, `verification_token`, `verification_token_expiry`, `is_active`
- `merch_shared.tenants` — Added: `plan_type: "trial"`, `status: "pending_verification"`, `trial_start`, `trial_end`, `admin_user_id`

## Prioritized Backlog

### P1
- SFTP alert/notification system (SFTP-31 to SFTP-34)

### P2
- USER-17: Force password change on first login
- Scheduled analysis jobs
- Tenant billing/usage tracking
- Plan upgrade page for trial users

### P3
- USER-18: MFA
- TENANT-10: Tenant backup/restore
- TENANT-31: Invoice generation
- Data Quality Rules Engine (custom tenant-specific validation)
