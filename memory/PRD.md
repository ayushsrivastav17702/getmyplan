# GetMyPlan PRD — AI-Powered Demand Planning Platform

## Original Problem Statement
Multi-tenant SaaS demand planning platform.

## Architecture
- React 19 + Tailwind + Chart.js | FastAPI + MongoDB + Redis | JWT + MFA

## MongoDB Aggregation Migration — COMPLETE (Apr 2026)
**All** high-traffic analytics endpoints migrated from Pandas to native MongoDB aggregation pipelines. Zero Pandas dependencies in analytics.

### Migrated Endpoints
| Phase | Endpoint | Status |
|---|---|---|
| 1 | `/api/analytics/executive-kpis` | Done |
| 1 | `/api/analytics/executive-revenue-trend` | Done |
| 2 | `/api/analytics/doh` | Done |
| 2 | `/api/analytics/stock-out` | Done (+ daily_trend charts) |
| 2 | `/api/analytics/replenishment` | Done |
| 3 | `/api/analytics/executive-dashboard` | Done |
| 4 | `/api/analytics/warehouse/*` (5 endpoints) | Done |
| 4 | `/api/analytics/planogram/*` (3 endpoints) | Done |

### Stock-Out Daily Trend (Task 3)
- Aggregates historical inventory snapshots to compute daily stockout counts
- Provides daily_trend, weekly_trend, monthly_trend, and 7-day moving_avg
- Frontend Trends tab now renders line charts

### Key Technical Decisions
- `_has_tenant_id()` — auto-detects whether collection uses tenant_id field
- Planogram uses `$ifNull` for ean/sku field compatibility
- Cache flush: `POST /api/admin/cache/flush`
- Health endpoints: `/api/health/memory`, `/api/health/ready`, `/api/health/live`

### Resilience Layer
- Axios retry interceptor (503/520 with exponential backoff + toast)
- localStorage cache for upload status (I-03)
- COGS upload count fix (I-04)
- AI onboarding banner (I-05)

### Key Files
- `/app/backend/core/mongo_aggregations.py` — Core aggregation pipelines
- `/app/backend/routes/warehouse.py` — Warehouse (MongoDB, no Pandas)
- `/app/backend/routes/planogram.py` — Planogram (MongoDB, no Pandas)
- `/app/backend/routes/health.py` — Health endpoints
- `/app/frontend/src/utils/axiosRetry.js` — Retry interceptor

## All Implemented Features
- Multi-tenant RBAC, JWT + MFA (TOTP + Email OTP)
- Invoice generation, Backup/Restore, User Funnel Analytics, Email Drip Campaigns
- SFTP scheduling, Chunked uploads
- 42 SEO blogs, Puppeteer pre-rendering, dynamic meta, sitemaps, RSS
- 503/520 resilience (retry + toast + health probes)
- Complete MongoDB aggregation migration (zero Pandas analytics)

## Remaining Backlog
- None — all user-requested features and migrations complete
