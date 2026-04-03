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
- TenantDataProvider now merges onboarding data as fallback when CSV data is missing
- **CSV always takes precedence** — onboarding data fills gaps only
- Fallback mapping:
  - `ob_categories` (level 1) → `get_categories()` 
  - `ob_categories` (level 2+) → `get_subcategories()`
  - `ob_marketplaces` names → `get_channels()`
  - `ob_stores` states → `get_regions()`
  - `ob_stores` → `get_stores()` / `get_store_codes()`
- `validate_data_availability()` includes `onboarding_fallback` and `has_onboarding_data` fields
- Both `/filter-options` and `/ai-demand/options` endpoints benefit from fallback
- Testing: **100% (Iteration 39, 15/15 PASS)**

### Phase 37 — Deployment Health Check (Apr 2026)
- Security fix: Removed hardcoded JWT_SECRET fallback, added `_refresh_jwt_secret()` startup validation
- Deployment agent: All checks passed (compilation, env, CORS, DB, supervisor, ports)
- Full system verified: Backend API + Frontend UI + MongoDB all operational

## Key API Endpoints

### Onboarding
- `GET /api/onboarding/status` — Progress, current step, is_onboarded
- `POST/GET/DELETE /api/onboarding/marketplaces` — Marketplace CRUD
- `POST/GET/DELETE /api/onboarding/stores` — Store CRUD with marketplace mapping
- `POST/GET/DELETE /api/onboarding/categories` — Category taxonomy CRUD (nested tree)
- `POST /api/onboarding/skip`, `/complete`, `/reset`

### Analytics Options (TenantDataProvider-powered with onboarding fallback)
- `GET /api/analytics/ai-demand/options`
- `GET /api/analytics/filter-options`
- `GET /api/buy-plan/options`

## Prioritized Backlog

### P1
- SFTP alert/notification system (SFTP-31 to SFTP-34)

### P2
- USER-17: Force password change on first login
- Scheduled analysis jobs
- Tenant billing/usage tracking

### P3
- USER-18: MFA
- TENANT-10: Tenant backup/restore
- TENANT-31: Invoice generation
- Data Quality Rules Engine (custom tenant-specific validation)
