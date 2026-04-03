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
  - `get_categories()`, `get_channels()`, `get_asp_by_category()`, `get_seasonality_factors()`, `get_channel_splits()`, `get_revenue_by_category/channel()`, `validate_data_availability()`, `get_analytics_options()`
  - Initialised in `server.py` via `init_tenant_provider(get_cached_data, get_db)`
- **Phase 2: Buy Plan Generator Refactored** — Replaced ALL hardcoded data with TenantDataProvider
  - New `GET /api/buy-plan/options` endpoint
  - `data_source` field in responses
  - Frontend data-source-indicator banner
- **Phase 3: AI Demand Planning Refactored** (Apr 2026)
  - New `GET /api/analytics/ai-demand/options` endpoint — dynamic categories, subcategories, channels, regions, brands, genders, seasons from TenantDataProvider
  - `data_source` field added to ALL 6 AI Demand endpoints (forecast, stockout-risk, topseller, reorder, supply-feasibility, generate-plan)
  - Frontend: AIDemandPlanning.js now fetches from `/ai-demand/options`, shows data-source-indicator banner (green=uploaded, amber=demo)
- **Phase 4: Gap Analysis Refactored** (Apr 2026)
  - `data_source` field added to ROS, ROS Gap, Size Gap, NOOS endpoints
- **Phase 5: Remaining Analytics Refactored** (Apr 2026)
  - `data_source` field added to Stock-Out, Planogram, DOH, Replenishment, BI Dashboard endpoints
  - `GET /api/analytics/filter-options` refactored to use TenantDataProvider — now returns subcategories, brands, genders, seasons, has_data, data_status
- Testing: **100% (Iteration 37, 36/36 PASS)**

## Key API Endpoints

### TenantDataProvider-Powered
- `GET /api/analytics/ai-demand/options` — Dynamic options for AI Demand filters
- `GET /api/analytics/filter-options` — Unified filter options (TenantDataProvider-powered)
- `GET /api/buy-plan/options` — Dynamic categories, channels, ASP for Buy Plan wizard

### AI Demand
- `GET /api/analytics/ai-demand/forecast` — ML ensemble forecast (data_source field)
- `GET /api/analytics/ai-demand/stockout-risk` — Stockout risk prediction
- `GET /api/analytics/ai-demand/topseller-prediction` — Topseller with X-Factor
- `GET /api/analytics/ai-demand/reorder-optimisation` — Reorder points
- `GET /api/analytics/ai-demand/supply-feasibility` — DOH-based feasibility
- `POST /api/analytics/ai-demand/generate-plan` — Generate demand plan

### Buy Plan
- `POST /api/buy-plan/generate` — Generate buy plan
- `POST /api/buy-plan/export-excel` — Export multi-sheet Excel
- `POST /api/buy-plan/upload-edited-plan` — Upload overrides
- `GET /api/buy-plan/history` — Plan history

## Incremental Refactoring Roadmap (TenantDataProvider)
- [x] Phase 1: Core Infrastructure (TenantDataProvider)
- [x] Phase 2: Buy Plan Generator
- [x] Phase 3: AI Demand Planning
- [x] Phase 4: Gap Analysis
- [x] Phase 5: Stock-Out, DOH, Replenishment, Planogram, BI Dashboards

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
