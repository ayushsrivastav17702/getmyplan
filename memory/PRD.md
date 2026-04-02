# Fashion Retail Gap Analysis Platform - PRD

## Original Problem Statement
Build a Fashion Retail Gap Analysis platform with React + FastAPI featuring CSV data uploading, multiple analytics dashboards with PRD formulas, dynamic filtering with presets, Chart.js visualizations, GPT-5.2 FAQ Chatbot, and multi-tenant architecture.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme)
- **Backend**: FastAPI with Python/Pandas
- **Database**: MongoDB (multi-tenant: separate DB per tenant, shared registry)
- **AI**: GPT 5.2 via Emergent LLM Key
- **Charts**: Chart.js + react-chartjs-2 (NO Recharts)
- **Auth**: JWT with bcrypt, tenant-scoped tokens

## Multi-Tenant Architecture
```
MongoDB
├── merch_shared (shared DB)
│   ├── tenants (registry)
│   ├── users (shared authentication)
│   └── user_tenants (user-tenant mapping)
├── test_database (demo tenant DB)
│   ├── uploaded_files, filter_presets, analysis_config...
├── tenant_acme_corp (Acme Corp DB)
│   └── (isolated data)
└── tenant_{new_tenant} (each new tenant)
```

## Pages & Routes (15 total + Login)
| Route | Page | Description |
|-------|------|-------------|
| (login) | Login/Register | Multi-tenant auth gate |
| / | Getting Started | App overview |
| /dashboard | Executive Dashboard | Unified CXO view |
| /upload | Data Upload | Master vs Daily file upload |
| /config | Configuration | Analysis config |
| /core-logics | Core Logics | TrueROS + Store-Style |
| /gap-analysis | Gap Analysis | NOOS + Size Gap + ROS Gap |
| /stock-out | Stock-Out Analysis | PRD stock-out formulas |
| /replenishment | Replenishment Planner | PO suggestions |
| /doh | DOH Analysis | Days on Hand classification |
| /planogram | Planogram Fill Rate | Fill rate compliance |
| /bi-dashboards | BI Dashboards | Revenue/units analytics |
| /warehouse | Warehouse | Inventory/velocity |
| /sftp-monitor | SFTP Monitor | Data pipeline monitoring |
| /data-quality | Data Quality | Store SLA scorecards |
| /chatbot | FAQ Chatbot | GPT-5.2 Q&A |

## Completed Phases

### Phase 1-7 (Previous sessions)
- [x] Full MVP with 7-file CSV upload, GPT chatbot, Salesforce theme
- [x] Dynamic filters + Presets with import/export
- [x] Chart.js migration, Warehouse Analysis, Data Upload redesign
- [x] SFTP Monitor + Data Quality dashboards

### Phase 8-12 (Analytics Modules)
- [x] ROS Gap Analysis (100% - Iteration 8)
- [x] Stock-Out Analysis (100% - Iteration 9)
- [x] Replenishment Planner (100% - Iteration 10)
- [x] DOH Analysis (100% - Iteration 11)
- [x] Planogram Fill Rate (100% - Iteration 12)

### Phase 13 — Executive Dashboard (Feb 2026)
- [x] Aggregated CXO dashboard with Health Score, Alerts, Module Cards
- [x] Testing: 100% (Iteration 13)

### Phase 14 — Multi-Tenant Architecture (Feb 2026)
- [x] MongoDB-based multi-tenancy (database-per-tenant isolation)
- [x] Shared registry in merch_shared DB (tenants, users, user_tenants)
- [x] TenantMiddleware: X-Tenant-ID header > JWT token > demo fallback
- [x] Tenant management API: create, list, status, suspend, activate, delete
- [x] JWT authentication: login, register, me (tenant-scoped)
- [x] Frontend: Login page with Sign In / Create Tenant tabs
- [x] Frontend: AuthProvider context with localStorage persistence
- [x] Frontend: Sidebar tenant info bar + user bar with logout
- [x] Default "demo" tenant maps to existing data (backward compat)
- [x] All existing analytics endpoints are now tenant-aware via get_db()
- [x] Testing: 100% (Iteration 14: 27 backend + all frontend)

## Prioritized Backlog
### P1
- Real SFTP integration
- PDF report generation
- Email alerts for SLA/SFTP
- Role-based access control (admin/analyst/viewer permissions)

### P2
- Scheduled analysis jobs
- Product lifecycle timeline
- Preset sharing via URL
- Modularize server.py into route files (~3200+ lines)
- Tenant billing/usage tracking
