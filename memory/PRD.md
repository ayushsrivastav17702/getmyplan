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

## Completed Phases

### Phase 1-16 (Previous sessions)
- Full MVP analytics, filters, presets, 6 analytics modules
- Executive Dashboard with module cards
- MongoDB Multi-Tenancy + RBAC + User Management
- Full RBAC integration across all 16 pages
- Tenant Admin Panel

### Phase 17 — Executive Dashboard P0 (Feb 2026)
- 401 Interceptor, KPI cards (Revenue, Units, MRP Realisation), WoW/YoY, date presets, validation, auto-refresh
- Testing: 100% (Iterations 17-18)

### Phase 18 — Data Upload Validation (Feb 2026)
- File size limit, data type validation, null check, dedup, future date rejection, negative qty rejection, encoding detection, concurrent upload lock
- Testing: 100% (Iteration 20)

### Phase 19 — Configuration Module (Feb 2026)
- CONF-01–32: Analysis parameters, module toggles, store classes, category hierarchies, custom roles, permission overrides
- Testing: **100% (Iteration 21)**

### Phase 20 — Core Logic Module (Feb 2026)
- CORE-01–35: ROS, Healthy Size Set, TrueROS, Attribute Grouping, Store-Style Ranking
- New modular route file: `/backend/routes/core_logic.py`
- Testing: **100% (Iteration 22)**

### Phase 21 — Gap Analysis Module (Feb 2026)
- GAP-01–35: ROS Gap, Size Set Gap, NOOS Analysis, Dashboard
- Testing: **100% (Iteration 23, 35/35 PASS)**

### Phase 22 — Stock-Out Analysis Module (Feb 2026)
- SO-01–35: Period trends, heatmaps, moving averages, predictive analysis, reorder recommendations
- Testing: **100% (Iteration 24, 35/35 PASS)**

### Phase 23 — Replenishment Planner Module (Apr 2026)
- REP-01–32: Reorder Point Calculation, Order Quantity, IST Inter-Store Transfer, Replenishment Run, Orders Dashboard
- New modular route file: `/backend/routes/replenishment.py`
- Testing: **100% (Iteration 25, 32/32 PASS)**

### Phase 24 — DOH Analysis Module (Apr 2026)
- DOH-01–35: DOH Calculation, Classification, Heatmap, DOH vs Stock-Out Correlation, Recommendations
- New modular route file: `/backend/routes/doh_analysis.py`
- Testing: **100% (Iteration 26, 35/35 PASS)**

### Phase 25 — Planogram Fill Rate Module (Apr 2026)
- PLAN-01–32: Fill Rate Calculation, Store Performance, Category Performance, Gap Analysis, Dashboard
- New modular route file: `/backend/routes/planogram.py`
- Testing: **100% (Iteration 27, 32/32 PASS)**

### Phase 26 — BI Dashboards Module (Apr 2026)
- BI-01–35: Revenue Analytics, Category Analytics, Store Analytics, Trend Analysis, Custom Dashboards
- New modular route file: `/backend/routes/bi_dashboard.py`
- Testing: **100% (Iteration 27, 35/35 PASS)**

### Phase 27 — SFTP Monitor Enhancement (Apr 2026)
- **19 gap test cases resolved**:
  - SFTP-03: Connection timeout with retry backoff (exponential backoff, configurable max_retries/base_delay/max_delay)
  - SFTP-04: Network interruption auto-reconnect (connection pool with automatic recovery)
  - SFTP-07: Connection pool (thread-safe pool with max_size, acquire/release, stats tracking)
  - SFTP-08: SSL/TLS verification (auto/strict/reject modes via config)
  - SFTP-09: Upload file to SFTP (single file upload with progress, hash, speed)
  - SFTP-10: Download file from SFTP (with progress tracking)
  - SFTP-11: Large file transfer with progress indicator (chunked transfer, TransferTracker)
  - SFTP-12: Partial transfer resume (byte offset resume for downloads)
  - SFTP-14: File overwrite protection (auto-versioning with timestamp suffix)
  - SFTP-15: Batch file upload (multi-file upload with aggregate results)
  - SFTP-16: Scheduled transfer (enhanced scheduler with demo/real mode)
  - SFTP-20: Malformed file detection -> failed folder (Pandas validation, archive_path)
  - SFTP-22: Duplicate file handling (SHA-256 hash-based dedup)
  - SFTP-23: File archive after processing (/archive/processed/ and /archive/failed/)
  - SFTP-25: Filter logs by date range (start_date, end_date params)
  - SFTP-29: Download error log as CSV
  - SFTP-30: Transfer speed metrics (avg/max/min speed, daily breakdown)
  - SFTP-35: Daily summary report (files, success rate, store coverage, top errors, by type)
- New route file: `/backend/routes/sftp_routes.py`
- Enhanced: `/backend/sftp/sftp_service.py` (ConnectionPool, TransferTracker, full file ops)
- Enhanced: `/backend/sftp/sftp_scheduler.py` (real scheduled transfer support)
- Enhanced: `/backend/server.py` (status with pool/SSL/retry, logs with date filter, stats with speed/malformed/dup)
- Frontend: Complete rewrite of SFTPMonitor.js with 5 tabs (Overview, Transfers, Logs, Speed Metrics, Daily Summary)
- Testing: **100% (Iteration 28, 25/25 PASS)**
- Note: All SFTP operations run in **DEMO MODE** (MOCKED) — no real SFTP server connected

## Test Coverage Summary

| Module | Total | PASS | PARTIAL | GAP | % |
|--------|-------|------|---------|-----|---|
| Executive Dashboard | 35 | 29 | 1 | 3 | 83% |
| Data Upload | 35 | 30 | 4 | 3 | 86% |
| Configuration | 32 | 32 | 0 | 0 | **100%** |
| Core Logic | 35 | 35 | 0 | 0 | **100%** |
| Gap Analysis | 35 | 35 | 0 | 0 | **100%** |
| Stock-Out Analysis | 35 | 35 | 0 | 0 | **100%** |
| Replenishment Planner | 32 | 32 | 0 | 0 | **100%** |
| DOH Analysis | 35 | 35 | 0 | 0 | **100%** |
| Planogram Fill Rate | 32 | 32 | 0 | 0 | **100%** |
| BI Dashboards | 35 | 35 | 0 | 0 | **100%** |
| SFTP Monitor | 35 | 27 | 6 | 2 | **94%** |
| **Total** | **396** | **357** | **11** | **8** | **96%** |

## Remaining Known Gaps
- DASH-15: Revenue trend line chart (P0)
- DASH-25: Offline detection UI (P1)
- DASH-35: PDF export (P2)
- SFTP-31/32/33/34: Email/Slack alerts, dashboard notifications, alert thresholds (P1-P2)
- SFTP-05/06: Host unreachable/permission denied messages (PARTIAL — generic errors)
- Warehouse Module: 24 gaps out of 30 test cases

## Prioritized Backlog

### P0
- DASH-15: Revenue trend line chart
- Warehouse Module (30 test cases — 24 gaps)

### P1
- DASH-25: Offline detection UI
- SFTP alert/notification system (SFTP-31 to SFTP-34)
- Modularize server.py — move Gap Analysis & Stock-Out endpoints to routes/

### P2
- DASH-35: PDF export
- Scheduled analysis jobs
- Tenant billing/usage tracking
