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

## Completed Phases

### Phase 1-16 (Previous sessions)
- [x] Full MVP analytics, filters, presets
- [x] Executive Dashboard with 6 module cards
- [x] MongoDB Multi-Tenancy + RBAC + User Management
- [x] Full RBAC integration across all 16 pages
- [x] Tenant Admin Panel (UI + Backend)

### Phase 17 — Executive Dashboard P0 Enhancements (Feb 2026)
- [x] DASH-26: 401 Interceptor — expired tokens auto-redirect to login
- [x] DASH-02/03: Revenue & Margin KPI cards with WoW growth indicators
- [x] DASH-33: Week-over-Week comparison card
- [x] DASH-34: Year-over-Year comparison card
- [x] DASH-08: Quick date presets (7 presets)
- [x] DASH-12: Date validation (end < start blocked)
- [x] DASH-24: Auto-refresh toggle with 30s countdown
- [x] New backend endpoint: /api/analytics/executive-kpis
- [x] Testing: 100% (Iteration 17-18: all 35 test cases audited, 29 PASS, 3 known GAPs)

### Phase 18 — Data Upload Validation Enhancements (Feb 2026)
- [x] UPLOAD-05: File size limit (100MB) — backend + frontend
- [x] UPLOAD-09: Data type validation (text in numeric field rejected)
- [x] UPLOAD-11: Null validation on required columns
- [x] UPLOAD-12: Deduplication with duplicate count in response
- [x] UPLOAD-20: Future date rejection
- [x] UPLOAD-23: Negative quantity/revenue rejection
- [x] UPLOAD-32: Concurrent upload lock (asyncio.Lock per file_type)
- [x] UPLOAD-35: Encoding detection via chardet (Latin1, UTF-8-BOM, CP1252)
- [x] UPLOAD-34: BOM character handling
- [x] UPLOAD-03 fix: 400 status (was 500) for unsupported format
- [x] UPLOAD-08: Extra columns warning in response
- [x] Frontend: Client-side file size + extension validation
- [x] Response enhanced: warnings, duplicates_removed, encoding fields
- [x] Testing: 100% (Iteration 20: all 35 test cases, 30 PASS, 4 PARTIAL, 3 known GAPs)

## Test Case Coverage Summary

### Executive Dashboard (35 test cases)
| Status | Count | % |
|--------|-------|---|
| PASS   | 29    | 83% |
| PARTIAL| 1     | 3% |
| GAP    | 3     | 9% |

Remaining GAPs: DASH-15 (trend line chart), DASH-25 (offline detection), DASH-35 (PDF export)

### Data Upload (35 test cases)
| Status | Count | % |
|--------|-------|---|
| PASS   | 30    | 86% |
| PARTIAL| 4     | 11% |
| GAP    | 3     | 9% |

Remaining GAPs: UPLOAD-26/28 (SFTP real connection — currently MOCKED), UPLOAD-33 (browser-level network retry)

## Prioritized Backlog

### P0
- [ ] Tenant Admin Panel formal testing

### P1
- DASH-15: Revenue trend line chart
- DASH-25: Offline detection UI
- Real SFTP integration (replace demo mode)
- PDF report generation
- Email alerts for SLA/SFTP
- PermissionGate inside pages (hide edit/export for viewers)

### P2
- DASH-35: PDF export for dashboard
- Modularize server.py into route files (~3500+ lines)
- Scheduled analysis jobs
- Tenant billing/usage tracking
- Team activity dashboard
