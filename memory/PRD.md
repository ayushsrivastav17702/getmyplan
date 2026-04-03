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
- **Phase 1: Core Infrastructure** — Created `TenantDataProvider` service layer (`/backend/services/tenant_data_provider.py`)
  - `get_categories()`, `get_channels()`, `get_asp_by_category()`, `get_seasonality_factors()`, `get_channel_splits()`, `get_revenue_by_category/channel()`, `validate_data_availability()`
  - Initialised in `server.py` via `init_tenant_provider(get_cached_data, get_db)`
- **Phase 2: Buy Plan Generator Refactored** — Replaced ALL hardcoded data with TenantDataProvider
  - New `GET /api/buy-plan/options` endpoint: returns dynamic categories, channels, ASP, seasonality, channel splits from uploaded CSV data
  - `POST /api/buy-plan/generate`: `data_source` field shows "uploaded" vs "defaults"; version bumped to 1.1
  - Frontend: data-source-indicator banner (green=uploaded data, amber=defaults), dynamic categoriesList/channelsList props in wizard steps
  - Old hardcoded values (Jeans/Shirts/STORE_A/AMAZON) only used as fallback when no data exists
- Testing: **100% (Iteration 36, 30/30 PASS)**

## Key API Endpoints (Buy Plan — Refactored)
- `GET /api/buy-plan/options` — Dynamic categories, channels, ASP from uploaded data
- `POST /api/buy-plan/generate` — Generate buy plan (uses TenantDataProvider)
- `POST /api/buy-plan/export-excel` — Export multi-sheet Excel
- `POST /api/buy-plan/upload-edited-plan` — Upload edited plan with overrides
- `GET /api/buy-plan/history` — Saved plan history
- `GET /api/buy-plan/summary` — Dynamic summary with data status

## Incremental Refactoring Roadmap (TenantDataProvider)
- [x] Phase 1: Core Infrastructure (TenantDataProvider)
- [x] Phase 2: Buy Plan Generator
- [ ] Phase 3: AI Demand Planning
- [ ] Phase 4: Gap Analysis
- [ ] Phase 5: Stock-Out, DOH, Replenishment, Planogram, BI Dashboards

## Prioritized Backlog

### P1
- Phase 3-5: Continue TenantDataProvider refactoring (AI Demand → Gap Analysis → remaining modules)
- SFTP alert/notification system (SFTP-31 to SFTP-34)

### P2
- USER-17: Force password change on first login
- Scheduled analysis jobs
- Tenant billing/usage tracking

### P3
- USER-18: MFA
- TENANT-10: Tenant backup/restore
- TENANT-31: Invoice generation
