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

### Phase 1-52 (Previous sessions)
- Full MVP: 16+ analytics modules, Multi-Tenancy, RBAC, JWT Auth
- AI Demand Planning, Buy Plan Generator, Executive Dashboard
- Self-Service Signup, GetMyPlan Rebranding, Enterprise Security
- Marketing Landing Page, Interactive Product Tour, PlanGuard
- Data Quality Rules Engine, V2 Upload System with 75-Rule Validation
- Component Refactoring, Validate-then-Save Flow

### Phase 53 — Demand Planning P0 Fixes (Apr 2026)
- V2 Data Bridge, Seasonal Decomposition Fix, Data Health Dashboard, 25-month seed data
- **Testing: 43/43 PASS (Iteration 58)**

### Phase 54 — P1 Enterprise Features (Apr 2026)
- EOQ, Per-SKU Lead Times, SKU-level Forecasting
- **Testing: 43/43 PASS (Iteration 58)**

### Phase 55 — Technical Audit Documents (Apr 2026)
- `CORE_ALGORITHMS_AUDIT.md` — Parts 4-9: Core Algorithms, Backend Architecture, Frontend, Scalability, Gaps
- `DATA_INFRASTRUCTURE_AUDIT.md` — Parts 1-3: Data Upload Infrastructure, Master Data Management, Transactional Data
- `E2E_DATA_FLOW_AUDIT.md` — Complete end-to-end data flow verification

### Phase 56 — V2 Bridge Migration for 5 Modules (Apr 2026)
- Updated `core_logic.py`, `doh_analysis.py`, `bi_dashboard.py`, `planogram.py`, `replenishment.py` to use server.py's `get_cached_data()` V2→V1 bridge
- All 11 data flows now working (previously only 4/9 modules were V2-compatible)
- **Testing: 22/22 PASS (Iteration 59)** — 17 backend + 5 frontend

## Audit Documents
- `/app/memory/CORE_ALGORITHMS_AUDIT.md` — Parts 4-9 (204 lines)
- `/app/memory/DATA_INFRASTRUCTURE_AUDIT.md` — Parts 1-3 (168 lines)
- `/app/memory/E2E_DATA_FLOW_AUDIT.md` — End-to-end data flow verification with gap report

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

## V2 Data Bridge Architecture (Post Phase 56)
All 9 analytics modules now use `get_cached_data()` from server.py:
1. Checks V2 collections first (`daily_sales`, `store_inventory`, etc.)
2. Falls back to V1 `uploaded_files` collection if V2 is empty
3. Applies field renames for backward compatibility (`closing_stock` → `quantity`, etc.)

| Module | V2 Bridge Status |
|--------|-----------------|
| ai_demand.py | ✅ (Phase 53) |
| gap_analysis.py | ✅ (Phase 53) |
| stock_out.py | ✅ (Phase 53) |
| server.py (executive) | ✅ (Phase 53) |
| warehouse.py | ✅ Direct V2 |
| core_logic.py | ✅ (Phase 56) |
| doh_analysis.py | ✅ (Phase 56) |
| bi_dashboard.py | ✅ (Phase 56) |
| planogram.py | ✅ (Phase 56) |
| replenishment.py | ✅ (Phase 56) |

## Key Files
### Upload Module
- `/app/backend/routes/upload.py` — V2 endpoints + validate + history/days
- `/app/backend/services/upload_service.py` — 75-rule validation engine
- `/app/frontend/src/pages/DataUploadPage.jsx` — Main page

### Analytics Modules (all V2 bridge compatible)
- `/app/backend/routes/ai_demand.py` — AI Demand (Forecast, Stockout, Reorder, Data Health)
- `/app/backend/routes/core_logic.py` — ROS, TrueROS, Size Set, Attribute Grouping
- `/app/backend/routes/doh_analysis.py` — DOH Classification, Heatmaps, Correlation
- `/app/backend/routes/bi_dashboard.py` — KPI Overview, Trends, Category/Channel/Store
- `/app/backend/routes/planogram.py` — Fill Rate, Compliance, Lost Sales
- `/app/backend/routes/replenishment.py` — Order Qty, IST, Reorder Points, Priority
- `/app/backend/routes/gap_analysis.py` — ROS Gap, Size Gap, NOOS
- `/app/backend/routes/stock_out.py` — Stockout Detection, Risk, Duration
- `/app/backend/routes/warehouse.py` — Stock Flow, Transfers, Reconciliation

## Prioritized Backlog

### P0 — Gaps from E2E Audit (Next Priority)
- **Style Master V2**: Migrate to V2 upload (currently V1 only, `_V2_MAP` maps to `None`)
- **COGS Upload**: New collection + endpoint (unlocks real margin calculation)
- **Planogram Upload**: New collection + endpoint (unlocks manual norm allocation)
- **Open Orders Upload**: New collection + endpoint (unlocks supply pipeline deduction)
- **Frontend Upload Types**: Add style_master, planogram, cogs, open_orders to DataUploadPage.jsx

### P1
- Forecast accuracy tracking over time (MAPE trend)
- Holiday/promotional calendar integration
- Wire COGS into executive KPIs for true margin

### P2
- USER-18: MFA (Multi-factor authentication)
- TENANT-10: Tenant backup/restore
- TENANT-31: Invoice generation
- User Funnel Analytics Dashboard
- Buy Plan integration with demand forecast
- Custom validation rules per tenant

### P3
- Auto-scheduled SFTP uploads for Data Upload V2
- Prophet integration for holiday-aware forecasting
- Chunked file uploads for >50MB files
- Async upload processing with job queues
- Pre-computed aggregation tables for analytics performance
