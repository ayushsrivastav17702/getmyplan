# GetMyPlan PRD — AI-Powered Demand Planning Platform

## Original Problem Statement
Multi-tenant SaaS demand planning platform.

## Architecture
- React 19 + Tailwind + Chart.js | FastAPI + MongoDB + Redis | JWT + MFA

## Critical Fix: MongoDB Aggregation Migration (Apr 2026)
**Problem:** Analytics endpoints causing 503/520 OOM crashes on production (Pandas loading 500MB+ DataFrames)
**Fix:** Replaced ALL high-traffic Pandas endpoints with native MongoDB aggregation pipelines

### Migrated Endpoints (Phase 1-3 COMPLETE)
| Endpoint | Before (Pandas) | After (MongoDB) |
|---|---|---|
| `/api/analytics/executive-kpis` | ~500MB RAM | ~5MB RAM |
| `/api/analytics/executive-revenue-trend` | ~500MB RAM | ~5MB RAM |
| `/api/analytics/doh` | ~800MB RAM | ~10MB RAM |
| `/api/analytics/stock-out` | ~600MB RAM | ~8MB RAM |
| `/api/analytics/replenishment` | ~700MB RAM | ~10MB RAM |
| `/api/analytics/executive-dashboard` | ~1GB RAM | ~15MB RAM |

### P0 Bug Fix: Stock-Out Lost Sales = 0 (Apr 13 2026)
Enhanced `agg_stock_out` to return complete response shape with all aggregated views.
**Verification:** 31/31 tests passed. KPI shows correct values.

### 503/520 Resilience Layer (Apr 13 2026)
- **Axios Retry Interceptor** (`axiosRetry.js`): Auto-retries GET on 503/520 with exponential backoff + sonner toast
- **Health Endpoints** (`health.py`): `/api/health/memory`, `/api/health/ready`, `/api/health/live`

### Resilience Fixes I-03, I-04, I-05 (Apr 13 2026)
- **I-03**: Upload status localStorage cache fallback — sidebar shows last known count when backend down
- **I-04**: Sidebar counts `s.uploaded` (not `s.uploaded && s.valid`) — COGS no longer shows false negative
- **I-05**: AI onboarding banner (red/amber/green) when no plan exists — guides users based on data availability

### Key Technical Decisions
- `_has_tenant_id()` — auto-detects whether collection uses tenant_id field
- `_tenant_match()` — conditional match builder
- Cache flush: `POST /api/admin/cache/flush`
- Retry interceptor only retries GET requests (safe idempotent)

### Key Files
- `/app/backend/core/mongo_aggregations.py` — All aggregation pipelines
- `/app/backend/routes/health.py` — Health endpoints
- `/app/frontend/src/utils/axiosRetry.js` — Retry interceptor
- `/app/frontend/src/pages/AIDemandPlanning.js` — AI onboarding banner

## All Implemented Features
- Multi-tenant RBAC, JWT + MFA (TOTP + Email OTP)
- Invoice generation, Backup/Restore, User Funnel Analytics (super admin only)
- Email Drip Campaigns (super admin only), SFTP scheduling, Chunked uploads
- 42 SEO blogs (14 Original + 7 Saudi + 7 UAE + 7 SA + 7 USA)
- Puppeteer pre-rendering, dynamic meta, sitemaps, RSS
- Axios retry interceptor for 503/520 resilience
- Health check endpoints for Kubernetes probes
- Upload status localStorage cache fallback
- AI onboarding banner for data readiness guidance

## Remaining Backlog
- Phase 4: Warehouse, Planogram aggregation migration (low priority)
- Stock-Out daily_trend data (needs historical inventory snapshots)
- Monitor production for OOM patterns
