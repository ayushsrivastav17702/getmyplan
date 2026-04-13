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
| `/api/config` | N/A (no Pandas) | N/A |

### Key Technical Decisions
- `_has_tenant_id()` — auto-detects whether collection uses tenant_id field (handles both shared DB and tenant-specific DBs)
- `_tenant_match()` — conditional match builder, empty dict for tenant DBs without tenant_id
- `_tid_cache` — per-db:collection caching of tenant_id detection
- Cache flush endpoint: `POST /api/admin/cache/flush` — clears stale Redis entries after migration
- `get_cached_data()` — streaming batch load (10K/batch) with 300K doc cap

### Key Files
- `/app/backend/core/mongo_aggregations.py` — All aggregation pipelines
- `/app/backend/server.py` — Endpoints using aggregations
- `/app/backend/routes/stock_out.py` — Stock-out (MongoDB)

## All Implemented Features
- Multi-tenant RBAC, JWT + MFA (TOTP + Email OTP)
- Invoice generation, Backup/Restore, User Funnel Analytics (super admin only)
- Email Drip Campaigns (super admin only), SFTP scheduling, Chunked uploads
- 42 SEO blogs (14 Original + 7 Saudi + 7 UAE + 7 SA + 7 USA)
- Puppeteer pre-rendering, dynamic meta, sitemaps, RSS

## Remaining Backlog
- Phase 4: Warehouse, Planogram aggregation migration (low priority — less traffic)
