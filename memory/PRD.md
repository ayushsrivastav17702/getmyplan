# GetMyPlan - AI-Powered Retail Demand Planning Platform

## Product Requirements Document

### Original Problem Statement
Multi-tenant demand planning system with comprehensive V2 data pipelines, UI dashboards, ML forecasting, scalable sample data onboarding, Redis caching, email alerts, contextual data upload guidance, guided onboarding wizard, and Technical SEO optimizations.

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
│   ├── routes/ (ai_demand.py, bi_dashboard.py, doh_analysis.py, gap_analysis.py, stock_out.py, replenishment.py, upload.py, signup.py, warehouse.py, core_logic.py, planogram.py, onboarding.py)
│   ├── services/ (cache_service.py, smtp_email_service.py, upload_service.py, tenant_data_provider.py)
│   ├── multi_tenant/ (tenant_db.py, rbac.py)
│   └── server.py (main FastAPI app, analytics endpoints)
├── frontend/
│   ├── src/pages/ (DataUploadPage.jsx, GapAnalysis.js, AIDemandPlanning.jsx, OnboardingWizard.js, NotFound.jsx, etc.)
│   ├── src/components/ (Sidebar.jsx, ReturnUserBanner.jsx, upload/DataRequirementsPanel.jsx, upload/FileDropzone.jsx, etc.)
│   └── src/context/ (AuthContext.js)
```

---

## Completed Features

### Previous Sessions
- Full multi-tenant platform with auth, RBAC, 10 upload types
- Executive Dashboard, BI Dashboard, Gap Analysis, DOH Analysis, Stock-Out Analysis
- Replenishment Planner, Planogram Fill Rate, AI Demand Forecasting
- Admin signup email notifications (SMTP)
- Forecast Accuracy Tracking with MAPE calculation
- Collapsible sidebar with categories and keyboard shortcuts
- Data Upload Page with preview modals and data summary cards
- Enterprise-scale sample data generation (~380k rows, 30 stores, 100 SKUs)

### Session: Apr 10, 2026

#### Redis Caching Implementation (P0)
- `cache_service.py`: cache_get, cache_set, invalidate_for_upload, invalidate_tenant
- TTLs: 1h (DOH/stockout/replenishment/planogram), 6h (executive/BI/gap), 24h (topseller), 7d (AI forecast)
- 11 analytics endpoints wrapped with caching
- Performance: 3-10x speedup (exec dashboard: 3.65s -> 0.35s)
- **Test Report**: iteration_67.json -- 24/24 PASS

#### Data Requirements Panel
- `DataRequirementsPanel.jsx`: Dynamic panel for all 10 upload types
- Backend `GET /api/upload/v2/data-days` endpoint
- **Test Report**: iteration_68.json -- 19/19 PASS

#### Guided Onboarding Wizard
- `OnboardingWizard.js`: 4-step wizard (Sample Data -> Master Data -> Transactional -> Dashboard)
- Backend `GET /api/onboarding/status` with data-driven step detection
- **Test Report**: iteration_69.json -- 29/30 PASS

#### SEO Technical Audit (Steps 1-3)
- SEO static files: `robots.txt`, `llms.txt`, `sitemap.xml`
- 5 Schema.org JSON-LD blocks hardcoded in `public/index.html`
- 3 public SEO pages: `/vs/anaplan`, `/vs/blue-yonder`, `/ai-demand-planning`
- Footer links to all SEO pages

#### SEO Fixes 3, 4, 5 (P0)
- **Fix 3**: Created proper `NotFound.jsx` 404 page with SEO meta (noindex), helpful links, and internal site navigation. Wired to catch-all routes for both authenticated and unauthenticated users.
- **Fix 4**: Ensured exactly 1 H1 per page. Fixed: OnboardingWizard (2 H1s -> 1 H1 + 1 H2), PlanUpgrade (missing H1 added), VerifyEmail (sr-only H1 added).
- **Fix 5**: Reduced main JS bundle from **2.3MB to 340KB** (85% reduction) via React.lazy code splitting for all 30+ route-level components with Suspense fallback.
- **Test Report**: iteration_70.json -- 11/11 PASS

---

## Pending / Backlog

### P1 -- Next Up
- Executive Dashboard & Configuration Page UX Fixes:
  - KPI labels, unique keys, compact INR formatting, filter dropdown wiring
  - Configuration page: typos, save button, numeric inputs

### P2 -- Future
- USER-18: Multi-factor authentication (MFA)
- TENANT-10: Tenant backup/restore
- TENANT-31: Invoice generation
- User Funnel Analytics Dashboard

### P3 -- Backlog
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
