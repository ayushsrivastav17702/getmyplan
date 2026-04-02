# Fashion Retail Gap Analysis Platform - PRD

## Original Problem Statement
Build a Fashion Retail Gap Analysis platform with React + FastAPI featuring CSV data uploading, multiple analytics dashboards with PRD formulas, dynamic filtering with presets, Chart.js visualizations, GPT-5.2 FAQ Chatbot, multi-tenant architecture, and role-based access control.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme)
- **Backend**: FastAPI with Python/Pandas
- **Database**: MongoDB (multi-tenant: separate DB per tenant, shared registry in merch_shared)
- **AI**: GPT 5.2 via Emergent LLM Key
- **Charts**: Chart.js + react-chartjs-2 (NO Recharts)
- **Auth**: JWT with bcrypt, tenant-scoped tokens, RBAC

## Multi-Tenant Architecture
```
MongoDB
├── merch_shared (shared DB)
│   ├── tenants (registry)
│   ├── users (shared authentication)
│   ├── user_tenants (user-tenant-role mapping)
│   ├── roles (8 system roles)
│   ├── permissions (21 permissions)
│   ├── invitations (pending user invites)
│   └── audit_logs (action history)
├── test_database (demo tenant DB)
│   └── uploaded_files, filter_presets, analysis_config...
└── tenant_{name} (each new tenant gets isolated DB)
```

## RBAC System
### Roles (8)
| Role | Priority | Description |
|------|----------|-------------|
| super_admin | 100 | Full platform access |
| admin | 90 | Full tenant access |
| cxo | 80 | High-level dashboards |
| merchandiser | 70 | Product mix, categories, data upload |
| allocator | 65 | Stock distribution |
| demand_planner | 60 | Forecasting & replenishment |
| store_manager | 40 | Store-level access |
| viewer | 30 | Read-only dashboards |

### Permissions (21) across modules: dashboard, analytics, data, users, settings, chatbot

## Pages & Routes (16 + Login)
| Route | Page | Admin Only |
|-------|------|-----------|
| (login) | Login/Register | No |
| / | Getting Started | No |
| /dashboard | Executive Dashboard | No |
| /upload | Data Upload | No |
| /config | Configuration | No |
| /core-logics | Core Logics | No |
| /gap-analysis | Gap Analysis | No |
| /stock-out | Stock-Out Analysis | No |
| /replenishment | Replenishment Planner | No |
| /doh | DOH Analysis | No |
| /planogram | Planogram Fill Rate | No |
| /bi-dashboards | BI Dashboards | No |
| /warehouse | Warehouse | No |
| /sftp-monitor | SFTP Monitor | No |
| /data-quality | Data Quality | No |
| /chatbot | FAQ Chatbot | No |
| /users | User Management | Yes |

## Completed Phases

### Phase 1-7 (Previous sessions)
- [x] Full MVP, dynamic filters + presets, Chart.js migration, SFTP Monitor + Data Quality

### Phase 8-12 (Analytics Modules)
- [x] ROS Gap, Stock-Out, Replenishment, DOH, Planogram Fill Rate (all 100%)

### Phase 13 — Executive Dashboard (Feb 2026)
- [x] Aggregated CXO dashboard, Testing: 100% (Iteration 13)

### Phase 14 — Multi-Tenant Architecture (Feb 2026)
- [x] MongoDB database-per-tenant isolation, tenant middleware, JWT auth
- [x] Testing: 100% (Iteration 14)

### Phase 15 — RBAC & User Management (Feb 2026)
- [x] 8 system roles, 21 permissions seeded at startup
- [x] require_role() and require_permission() decorators
- [x] User management API: list, invite, accept-invite, update role, remove
- [x] Invitation flow with tokens (7-day expiry)
- [x] Audit logging for all user actions
- [x] Frontend: UserManagement page with tabs (Team Members, Invitations, Audit Log)
- [x] Frontend: Invite modal, role editing, user removal
- [x] Frontend: AuthContext with hasRole(), hasPermission(), permissions state
- [x] Frontend: PermissionGate component for conditional rendering
- [x] Frontend: Admin-only nav filtering
- [x] Testing: 100% (Iteration 15: 30 backend + all frontend)

## Prioritized Backlog
### P1
- Real SFTP integration
- PDF report generation
- Email alerts for SLA/SFTP
- Permission-based page access (use PermissionGate on routes)

### P2
- Scheduled analysis jobs
- Product lifecycle timeline
- Preset sharing via URL
- Modularize server.py into route files (~3200+ lines)
- Tenant billing/usage tracking
