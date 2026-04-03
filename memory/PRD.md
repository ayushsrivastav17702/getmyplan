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
- **Service Layer**: TenantDataProvider (`/backend/services/tenant_data_provider.py`) — single source of truth for tenant-uploaded data

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
- **Phase 1: Core Infrastructure** — Created `TenantDataProvider` service layer
- **Phase 2: Buy Plan Generator Refactored** — data_source field, `/buy-plan/options` endpoint
- **Phase 3: AI Demand Planning Refactored** — `/ai-demand/options` endpoint, data_source in all 6 endpoints
- **Phase 4: Gap Analysis Refactored** — data_source in ROS, ROS Gap, Size Gap, NOOS
- **Phase 5: Remaining Analytics** — data_source in Stock-Out, Planogram, DOH, Replenishment, BI Dashboard, filter-options
- Testing: **100% (Iteration 37, 36/36 PASS)**

### Phase 35 — Onboarding Wizard (Apr 2026)
- **3-step wizard**: Marketplaces → Stores → Category Taxonomy
- **Backend**: Full CRUD for marketplaces (ob_marketplaces), stores (ob_stores), categories (ob_categories)
  - `POST/GET/DELETE /api/onboarding/marketplaces` with currency, tax, commission, type
  - `POST/GET/DELETE /api/onboarding/stores` with marketplace mapping
  - `POST/GET/DELETE /api/onboarding/categories` with nested parent-child tree
  - `GET /api/onboarding/status` — progress %, current step, is_onboarded
  - `POST /api/onboarding/skip` — skip individual steps
  - `POST /api/onboarding/complete` — validates all 3 steps done, marks onboarded
  - `POST /api/onboarding/reset` — clears all onboarding data
- **Auto-onboarding**: Existing tenants with uploaded data are auto-marked as onboarded
- **Frontend**: Full wizard UI with progress bar, skip, back/next, add/delete forms
- **RequireOnboarding guard**: Non-onboarded tenants see full-page wizard before accessing app
- **Nav item**: "Setup Wizard" in sidebar for admin reconfiguration
- Testing: **100% (Iteration 38, 31/31 PASS)**

## Key API Endpoints

### Onboarding
- `GET /api/onboarding/status` — Onboarding progress, current step, is_onboarded
- `POST/GET/DELETE /api/onboarding/marketplaces` — Marketplace CRUD
- `POST/GET/DELETE /api/onboarding/stores` — Store CRUD with marketplace mapping
- `POST/GET/DELETE /api/onboarding/categories` — Category taxonomy CRUD (nested tree)
- `POST /api/onboarding/skip?step=N` — Skip a step
- `POST /api/onboarding/complete` — Complete onboarding
- `POST /api/onboarding/reset` — Reset onboarding

### TenantDataProvider-Powered
- `GET /api/analytics/ai-demand/options` — Dynamic filter options
- `GET /api/analytics/filter-options` — Unified filter options
- `GET /api/buy-plan/options` — Buy Plan dynamic options

### AI Demand
- `GET /api/analytics/ai-demand/forecast` + stockout-risk, topseller, reorder, supply-feasibility
- `POST /api/analytics/ai-demand/generate-plan`

### Buy Plan
- `POST /api/buy-plan/generate`, `/export-excel`, `/upload-edited-plan`

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
