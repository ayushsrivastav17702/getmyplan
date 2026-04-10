# GetMyPlan - AI-Powered Retail Demand Planning Platform

## Product Requirements Document

### Original Problem Statement
Multi-tenant demand planning system with comprehensive V2 data pipelines, UI dashboards, ML forecasting, scalable sample data onboarding, Redis caching, email alerts, and contextual data upload guidance.

### Tech Stack
- **Frontend**: React 18, Chart.js (react-chartjs-2), Shadcn/UI, TailwindCSS
- **Backend**: FastAPI (Python 3.11), Motor (async MongoDB)
- **Database**: MongoDB (multi-tenant with shared + tenant-specific DBs)
- **Cache**: Redis Cloud (non-SSL)
- **Auth**: JWT-based multi-tenant auth with RBAC
- **AI/ML**: Holt-Winters, Random Forest, Seasonal Decomposition (3-model ensemble)
- **Email**: Hostinger SMTP
- **LLM**: OpenAI GPT-5.2 via Emergent LLM Key (FAQ Chatbot)

### Architecture
```
/app
├── backend/
│   ├── routes/ (ai_demand.py, bi_dashboard.py, doh_analysis.py, gap_analysis.py, stock_out.py, replenishment.py, upload.py, signup.py, warehouse.py, core_logic.py, planogram.py)
│   ├── services/ (cache_service.py, smtp_email_service.py, upload_service.py, tenant_data_provider.py)
│   ├── multi_tenant/ (tenant_db.py, rbac.py)
│   └── server.py (main FastAPI app, analytics endpoints)
├── frontend/
│   ├── src/pages/ (DataUploadPage.jsx, GapAnalysis.js, AIDemandPlanning.jsx, etc.)
│   ├── src/components/ (Sidebar.jsx, upload/DataRequirementsPanel.jsx, upload/FileDropzone.jsx, etc.)
│   └── src/context/ (AuthContext.js)
```

### Key DB Schema
- `forecast_snapshots`: tenant_id, snapshot_id, created_at, forecast_data, metadata
- `daily_sales`: day, store_code, sku, quantity, revenue, tenant_id
- Redis keys: `module:tenant_id:date:extra` (e.g., `executive_kpis:increff:2026-04-10:all`)

---

## Completed Features

### Session 1 (Previous)
- Full multi-tenant platform with auth, RBAC, 10 upload types
- Executive Dashboard, BI Dashboard, Gap Analysis, DOH Analysis, Stock-Out Analysis
- Replenishment Planner, Planogram Fill Rate, AI Demand Forecasting
- Admin signup email notifications (SMTP)
- Forecast Accuracy Tracking with MAPE calculation
- Collapsible sidebar with categories and keyboard shortcuts
- Data Upload Page with preview modals and data summary cards
- Enterprise-scale sample data generation (~380k rows, 30 stores, 100 SKUs)

### Session 2 (Current — Apr 10, 2026)

#### Redis Caching Implementation (P0) ✅
- Created `/app/backend/services/cache_service.py` with `cache_get`, `cache_set`, `invalidate_for_upload`, `invalidate_tenant`
- TTLs: 1h (DOH/stockout/replenishment/planogram), 6h (executive/BI/gap), 24h (topseller), 7d (AI forecast)
- Wired caching to 11 analytics endpoints in server.py and route files
- Cache invalidation on successful uploads (type-specific) and sample data loads (full tenant clear)
- Performance: executive-kpis 3s→0.37s, exec-dashboard 3.65s→0.35s, BI overview 1.09s→0.34s, forecast 1.63s→0.34s
- **Test Report**: iteration_67.json — 24/24 PASS

#### Data Requirements Panel (P1) ✅
- Created `/app/frontend/src/components/upload/DataRequirementsPanel.jsx`
- Panel appears above dropzone for every upload type with dynamic content
- Sections: Required Date Range (min/recommended/AI), Date Format, Important Rules, Date Range Impact Table
- Data days indicator: "Your current data: X days" with color-coded status
- Master data types show simplified panel (When to Upload + tip)
- Expected date range hint below dropzone for transactional types
- Backend endpoint `GET /api/upload/v2/data-days` returns distinct day count
- **Test Report**: iteration_68.json — 19/19 PASS

---

## Pending / Backlog

### P1 — Next Up
- Executive Dashboard & Configuration Page UX Fixes (from message 152):
  - KPI labels, unique keys, compact INR formatting, filter dropdown wiring
  - Configuration page: typos, save button, numeric inputs

### P2 — Future
- USER-18: Multi-factor authentication (MFA)
- TENANT-10: Tenant backup/restore
- TENANT-31: Invoice generation
- User Funnel Analytics Dashboard

### P3 — Backlog
- Auto-scheduled SFTP uploads for Data Upload V2
- Chunked uploads & async processing
- MongoDB pipeline migration (replace in-memory Pandas aggregation)

---

## 3rd Party Integrations
| Service | Status | Key Source |
|---------|--------|-----------|
| OpenAI GPT-5.2 | Active | Emergent LLM Key |
| Hostinger SMTP | Active | .env credentials |
| Redis Cloud | Active | .env credentials |

## Test Credentials
- Increff Admin: ayush.srivastav@increff.com / Ayush@114988
- Demo Admin: admin@demo.com / demo1234
