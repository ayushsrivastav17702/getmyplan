# Fashion Retail Gap Analysis Platform - PRD

## Original Problem Statement
Build a Fashion Retail Gap Analysis platform with React + FastAPI featuring CSV data uploading, multiple analytics dashboards with PRD formulas, dynamic filtering with presets, Chart.js visualizations, GPT-5.2 FAQ Chatbot, multi-tenant architecture, and role-based access control integrated across all pages.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme)
- **Backend**: FastAPI with Python/Pandas
- **Database**: MongoDB (multi-tenant: separate DB per tenant, shared registry in merch_shared)
- **AI**: GPT 5.2 via Emergent LLM Key
- **Charts**: Chart.js + react-chartjs-2 (NO Recharts)
- **Auth**: JWT with bcrypt, tenant-scoped tokens, RBAC with permission-guarded routes

## RBAC System
### 8 Roles with permission counts
| Role | Priority | Permissions | Description |
|------|----------|------------|-------------|
| super_admin | 100 | 21 (all) | Full platform access |
| admin | 90 | 21 (all) | Full tenant access |
| cxo | 80 | 10 | Dashboards + analytics + export |
| merchandiser | 70 | 15 | All analytics + data management |
| allocator | 65 | 11 | Analytics + data upload + export |
| demand_planner | 60 | 6 | Replenishment + DOH + stock-out |
| store_manager | 40 | 5 | Exec dashboard + store-level analytics |
| viewer | 30 | 10 | Read-only dashboards + analytics |

### Role vs Page Access Matrix
| Page | Admin | CXO | Merch | Alloc | Demand | Store | Viewer |
|------|-------|-----|-------|-------|--------|-------|--------|
| Getting Started | Y | Y | Y | Y | Y | Y | Y |
| Exec Dashboard | Y | Y | Y | Y | Y | Y | Y |
| Data Upload | Y | - | Y | Y | - | - | - |
| Configuration | Y | - | Y | - | - | - | - |
| Core Logics | Y | Y | Y | Y | - | - | Y |
| Gap Analysis | Y | Y | Y | Y | - | - | Y |
| Stock-Out | Y | Y | Y | Y | Y | Y | Y |
| Replenishment | Y | Y | Y | Y | Y | - | Y |
| DOH Analysis | Y | Y | Y | Y | Y | - | Y |
| Planogram | Y | Y | Y | Y | - | Y | Y |
| BI Dashboards | Y | Y | Y | Y | Y | - | Y |
| Warehouse | Y | Y | Y | Y | - | - | Y |
| SFTP Monitor | Y | - | Y | - | - | - | - |
| Data Quality | Y | - | Y | - | - | Y | - |
| FAQ Chatbot | Y | Y | Y | Y | Y | Y | Y |
| User Management | Y | - | - | - | - | - | - |

## Completed Phases

### Phase 1-12 (Previous sessions)
- [x] Full MVP, filters, presets, analytics modules (all 100%)

### Phase 13 — Executive Dashboard
- [x] Testing: 100% (Iteration 13)

### Phase 14 — Multi-Tenant Architecture
- [x] Testing: 100% (Iteration 14)

### Phase 15 — RBAC & User Management
- [x] Testing: 100% (Iteration 15)

### Phase 16 — Full RBAC Integration with All Pages (Feb 2026)
- [x] Permission-keyed navItems in App.js (16 routes mapped to 15 permission keys)
- [x] ProtectedRoute component wraps each Route with permission check
- [x] Sidebar nav filtering — only shows pages the user has permission for
- [x] Unauthorized page with role display and "Back to Home" button
- [x] Testing: 100% (Iteration 16: 11 backend + all frontend)

### Phase 17 — Executive Dashboard P0 Enhancements (Feb 2026)
- [x] DASH-26: 401 Interceptor — expired tokens auto-redirect to login with "Session expired" message
- [x] DASH-02/03: Revenue & Margin KPI cards (₹9.3Cr, 33K units, 100% MRP Realisation, Health Score)
- [x] DASH-33: Week-over-Week comparison card (+8.3% revenue, +5.5% units)
- [x] DASH-34: Year-over-Year comparison card (with fallback for missing prior-year data)
- [x] DASH-08: Quick date presets (Last 7d, 30d, 90d, This Month, Last Month, Quarter, YTD)
- [x] DASH-12: Date validation (end < start blocked with error message)
- [x] DASH-24: Auto-refresh toggle with 30s countdown
- [x] New backend endpoint: /api/analytics/executive-kpis
- [x] Testing: 100% (Iteration 17: 19 backend + all frontend)

### Tenant Admin Panel (Implemented, Testing Pending from Phase 16)
- [x] Implementation complete: Metrics, API Keys, Audit Logs, Settings tabs
- [ ] Formal testing via testing_agent_v3_fork

## Executive Dashboard Test Case Audit (35 cases)
| Status   | Count | Percentage |
|----------|-------|------------|
| PASS     | 30    | 86%        |
| PARTIAL  | 3     | 9%         |
| GAP      | 2     | 6%         |
| **Total**| **35**| **100%**   |

### Remaining P1 Gaps
- DASH-15: Revenue trend line chart (time-series)
- DASH-25: Offline detection / network error UI
- DASH-13: Explicit "No matching results" empty state for filters

### Remaining P2 Gaps
- DASH-35: PDF export of dashboard
- DASH-06: Negative revenue validation
- DASH-29: Timezone-aware date display

## Prioritized Backlog
### P0
- [x] Executive Dashboard P0 test cases (DONE)
- [ ] Tenant Admin Panel formal testing

### P1
- Real SFTP integration
- Revenue trend line chart (DASH-15)
- Offline detection (DASH-25)
- PDF report generation
- Email alerts for SLA/SFTP
- PermissionGate usage inside pages (hide edit/export buttons for viewers)

### P2
- PDF export for dashboard (DASH-35)
- Scheduled analysis jobs
- Modularize server.py into route files (~3200+ lines)
- Tenant billing/usage tracking
- Team activity dashboard
