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

### P0 Bug Fix: Stock-Out ₹0 Lost Sales (Apr 13 2026)
**Root Cause:** `agg_stock_out` returned simplified response shape after migration, but frontend expected complete aggregated views.
**Fix:** Enhanced `agg_stock_out` to compute top_skus, top_stores, category_impact, store_heatmap, category_heatmap, high_risk_skus, reorder_recommendations, alternative_suggestions server-side.
**Verification:** 31/31 tests passed. KPI shows ₹1.6L (was ₹0).

### 503/520 Resilience Layer (Apr 13 2026)
- **Axios Retry Interceptor** (`/app/frontend/src/utils/axiosRetry.js`): Auto-retries GET requests on 503/520 with exponential backoff (2s→4s→8s, max 3 retries). Shows "Reconnecting..." toast via sonner.
- **Health Check Endpoints** (`/app/backend/routes/health.py`):
  - `GET /api/health` — Existing enterprise health (DB + uptime)
  - `GET /api/health/memory` — Memory usage monitoring (psutil)
  - `GET /api/health/ready` — Kubernetes readiness probe (MongoDB ping)
  - `GET /api/health/live` — Kubernetes liveness probe

### Key Technical Decisions
- `_has_tenant_id()` — auto-detects whether collection uses tenant_id field
- `_tenant_match()` — conditional match builder
- Cache flush endpoint: `POST /api/admin/cache/flush` — clears stale Redis entries
- Retry interceptor only retries GET requests (safe idempotent operations)

### Key Files
- `/app/backend/core/mongo_aggregations.py` — All aggregation pipelines
- `/app/backend/routes/health.py` — Health/readiness/liveness endpoints
- `/app/frontend/src/utils/axiosRetry.js` — Axios retry interceptor with toast

## All Implemented Features
- Multi-tenant RBAC, JWT + MFA (TOTP + Email OTP)
- Invoice generation, Backup/Restore, User Funnel Analytics (super admin only)
- Email Drip Campaigns (super admin only), SFTP scheduling, Chunked uploads
- 42 SEO blogs (14 Original + 7 Saudi + 7 UAE + 7 SA + 7 USA)
- Puppeteer pre-rendering, dynamic meta, sitemaps, RSS
- Axios retry interceptor for 503/520 resilience
- Health check endpoints for Kubernetes probes

## Remaining Backlog
- Phase 4: Warehouse, Planogram aggregation migration (low priority — less traffic)
- Stock-Out daily_trend data (currently empty arrays — needs historical inventory snapshots)
- Monitor production for remaining OOM patterns
