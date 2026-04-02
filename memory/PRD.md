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
- [x] Verified: admin=16 nav items, merchandiser=15, store_manager=6
- [x] Verified: direct URL access to denied pages shows Access Denied
- [x] PermissionGate component available for in-page conditional rendering
- [x] Testing: 100% (Iteration 16: 11 backend + all frontend)

## Prioritized Backlog
### P1
- Real SFTP integration
- PDF report generation
- Email alerts for SLA/SFTP
- PermissionGate usage inside pages (hide edit/export buttons for viewers)

### P2
- Scheduled analysis jobs
- Modularize server.py into route files (~3200+ lines)
- Tenant billing/usage tracking
- Team activity dashboard
