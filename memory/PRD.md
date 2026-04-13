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

### P0 Bug Fix: Stock-Out ₹0 Lost Sales (Apr 13 2026)
**Root Cause:** `agg_stock_out` in `mongo_aggregations.py` returned simplified response shape after migration (flat `data[]` + `daily_revenue_loss` in summary), but the frontend expected `total_lost_sales`, `top_skus[]`, `top_stores[]`, `category_impact[]`, `store_heatmap[]`, `high_risk_skus[]`, `reorder_recommendations[]`, `alternative_suggestions[]`.
**Fix:** Enhanced `agg_stock_out` to compute all aggregated views server-side from stockout data, including SKU→style and style→category lookups.
**Verification:** 31/31 tests passed (16 backend + 15 frontend). KPI shows ₹1.6L (was ₹0).

### Key Technical Decisions
- `_has_tenant_id()` — auto-detects whether collection uses tenant_id field
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
- Stock-Out daily_trend data (currently returns empty arrays — needs historical inventory snapshots)
- Monitor production for remaining OOM patterns
