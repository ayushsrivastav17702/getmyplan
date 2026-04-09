# CORE ALGORITHMS & BACKEND ARCHITECTURE — FULL AUDIT RESPONSE

**Date**: April 9, 2026 | **Application**: GetMyPlan | **Codebase**: ~10,200 lines backend logic

---

## 4.1 Rate of Sale (ROS) Calculation

| # | Question | Status | Details | Limitations | Scale |
|---|----------|--------|---------|-------------|-------|
| 4.1.1 | What ROS periods are supported? | **Implemented** | 7-day, 14-day, 30-day, Custom via `ros_period` query param. Default from tenant config `ros_period` (default 30). File: `core_logic.py` L121 | No auto-suggestion of optimal period | Per-query configurable |
| 4.1.2 | How do you handle zero sales days? | **Implemented** | CORE-02: `ROS = Total Qty / Live Days`. Zero sales → ROS=0. `fillna(0)` applied after division. L236-238 | Zero-sale days not distinguished from "store closed" days | Handles cleanly |
| 4.1.3 | Weighted ROS (70/30 split)? | **Implemented** | TrueROS endpoint (`/true-ros`): `TrueROS = recent_weight × recent_ROS + historical_weight × historical_ROS`. Default 70/30 split, configurable via `recent_weight`/`historical_weight` params. CORE-15 to CORE-21. L392-468 | Weights are global (not per-SKU or per-category) | User-configurable |
| 4.1.4 | Seasonality in ROS? | **Partial** | TrueROS uses day-level weighting (`day_weight` decays for older days). No explicit seasonal calendar or month-over-month adjustment. | No holiday/festive calendar. No YoY comparison | Only recency weighting |
| 4.1.5 | Store-level or cluster-level ROS? | **Store-level** | ROS computed at store×SKU level (L235-236). Style-level aggregation available. No cluster/region-level ROS fallback for low-sales stores. | Stores with <5 sales get noisy ROS | No cluster aggregation |
| 4.1.6 | Recalculation frequency? | **On-demand** | Calculated on each API call. No scheduled background recalculation. | No pre-computed cache | ~1-2s per request |
| 4.1.7 | Performance at 1M SKUs × 1000 stores? | **Not tested** | Uses Pandas in-memory. Current: 10 SKUs × 5 stores. At 1M×1K, would need Spark/Dask. | Single-node Pandas, no distributed compute | ~30K row tested |
| 4.1.8 | New products with no history? | **Handled** | ROS=0 for new products. CORE-18: Both recent and historical zero → TrueROS=0. | No "similar product" fallback, no category-average imputation | Returns 0 |
| 4.1.9 | Recent SKU ROS stored separately? | **No** | Computed on-the-fly. Recent ROS and Raw ROS both returned in API response but not persisted to DB. | No historical ROS tracking | API response only |

---

## 4.2 Days on Hand (DOH) Calculation

| # | Question | Status | Details | Limitations | Scale |
|---|----------|--------|---------|-------------|-------|
| 4.2.1 | How is Ideal DOH determined? | **Implemented** | From tenant config `ideal_doh` (default 9 days). Per-category override via `category_ideal_doh` config map. DOH-14. L109-110 | Must be manually configured per category | Configurable |
| 4.2.2 | Dynamic ideal DOH by season/promo? | **Not implemented** | Ideal DOH is static per category from config. No seasonal or promotional adjustment. | No season-aware DOH | Static only |
| 4.2.3 | Top seller multiplier for DOH? | **Implemented** | DOH-15: `ideal_doh × topseller_multiplier` (default 2.0×). Configurable via `topseller_multiplier` param. L92,112 | Same multiplier for all topsellers (not graduated) | Configurable |
| 4.2.4 | Classification thresholds? | **Implemented** | DOH-09 to DOH-13: Optimal=±20% of ideal, Overstocked=>120%, Understocked=<80%, Stocked Out=SOH=0. L104 | Fixed percentage bands, not configurable | 4 classifications |
| 4.2.5 | Warehouse stock in DOH? | **Implemented** | DOH-07/08: `include_wh` param. When true, adds warehouse stock to SOH before calculating DOH. L103,184 | All warehouse stock attributed to nearest store (no allocation logic) | Toggle param |
| 4.2.6 | Aggregate channel DOH? | **Implemented** | DOH-04/05: Weighted average `Sum(DOH×Inv)/Sum(Inv)` at channel and category level. L99-100 | Equal weighting assumption across stores in same channel | Aggregation done |
| 4.2.7 | DOH trend analysis (Pre vs Post)? | **Not implemented** | No pre/post comparison. DOH is a point-in-time snapshot. | No before/after IST or replenishment comparison | Not available |
| 4.2.8 | DOH for topsellers calculated differently? | **Implemented** | DOH-15: Topsellers get `ideal_doh × multiplier` as their target. Classification thresholds shift accordingly. | Binary topseller/non-topseller (no graduated tiers) | Multiplier-based |

---

## 4.3 Stockout Detection & Analysis

| # | Question | Status | Details | Limitations | Scale |
|---|----------|--------|---------|-------------|-------|
| 4.3.1 | Stockout definition? | **Implemented** | `SOH == 0 AND ROS > 0`. File: `stock_out.py` L125. Zero stock with zero sales is not a stockout (dead SKU). | No configurable threshold (e.g., SOH < safety_stock) | Standard definition |
| 4.3.2 | Stockout duration tracking? | **Implemented** | Counts consecutive zero-inventory days per store×SKU. `stockout_days` field in response. L140-142 | Duration from inventory snapshots (gaps in data = assumed continuous) | Consecutive days |
| 4.3.3 | Lost sales calculation? | **Implemented** | `daily_sales_loss = ROS × 1 day × ASP`. Total lost = `daily_loss × stockout_days`. Severity = `daily_loss × duration`. L134-135, 143 | Assumes ROS would have continued at pre-stockout rate. No demand elasticity. | Per-SKU per-store |
| 4.3.4 | NOOS tagging? | **Implemented** | Dedicated NOOS endpoint (`/analytics/noos`). Tags SKUs as NOOS based on availability %. Recovery plan generation. `gap_analysis.py` L479 | NOOS threshold hardcoded (availability check), no user tagging of "core styles" | Auto-detected |
| 4.3.5 | Partial stockouts (some sizes missing)? | **Partial** | Healthy Size Set analysis in `core_logic.py` L279 detects broken size curves. Not directly linked to stockout module. | Separate module, no unified "partial stockout" metric | Via size gap |
| 4.3.6 | Stockout rate at store/category/overall? | **Implemented** | Store-level: `top_stores` with stockout_count, avg_duration. Category-level: `category_breakdown`. Overall: `stockout_rate_pct`. L152-183 | No subcategory-level breakdown | 3 levels |
| 4.3.7 | Stockout trend (WTD, MTD, QTD, YTD)? | **Partial** | Daily stockout trend chart (`daily_trend` in response, L190-195). No WTD/MTD/QTD/YTD pre-computed aggregations. | Raw daily data only, no period rollups | Daily trend |
| 4.3.8 | Post-run stockout reduction? | **Not implemented** | No before/after comparison of stockout rates after replenishment run. | No simulation or what-if analysis | Not available |
| 4.3.9 | Stockout diagnosis / root cause? | **Partial** | `high_risk_list` shows SKUs approaching stockout with days-to-stockout prediction (L199-211). No root cause analysis (late PO, supplier delay, demand spike). | No root cause categorization | Risk prediction only |

---

## 4.4 Topseller Identification

| # | Question | Status | Details | Limitations | Scale |
|---|----------|--------|---------|-------------|-------|
| 4.4.1 | Topseller definition? | **Implemented** | X-Factor: `predicted_revenue / category_avg_revenue`. If X-Factor ≥ threshold, marked as topseller. `ai_demand.py` topseller-prediction endpoint. Also `config.topseller_x_factor` in DOH module. | Single metric (revenue-based), no quantity-based or top-X% option | X-Factor formula |
| 4.4.2 | Store-specific or global? | **Global** | Topseller classification is across all stores (aggregate revenue per style). Not per-store. | A style that's a topseller in ONLINE-01 but not in POPUP-01 still gets global topseller tag | Global only |
| 4.4.3 | Dynamic threshold (user-configurable)? | **Implemented** | `x_factor` query parameter (1.0-5.0, default 2.0). Also in tenant config `topseller_x_factor`. | Can only be changed per request or globally, not per-category | Configurable |
| 4.4.4 | Refresh frequency? | **On-demand** | Calculated on each API call. Not cached or scheduled. | No historical topseller tracking (was it a topseller last month?) | Per-request |
| 4.4.5 | New launch topsellers? | **Not implemented** | No special handling for first 30 days. New products start with limited data → unlikely to hit X-factor threshold. | No "emerging topseller" detection | Not available |
| 4.4.6 | Topseller availability %? | **Not directly** | DOH module applies topseller multiplier to cover_days. NOOS module tracks availability. But no unified "topseller availability %" metric. | Spread across modules | Indirect |
| 4.4.7 | Topseller risk levels (G/Y/R)? | **Partial** | Via DOH classification: topsellers with Understocked DOH = Red, Optimal = Green. Not a dedicated topseller risk dashboard. | Derived from DOH, not standalone | Via DOH |
| 4.4.8 | Bubble chart (DOH vs Availability vs Store Count)? | **Not implemented** | No bubble chart visualization. Frontend has bar charts and tables. | Would need frontend component + dedicated API | Not available |

---

## 4.5 Replenishment Algorithm

| # | Question | Status | Details | Limitations | Scale |
|---|----------|--------|---------|-------------|-------|
| 4.5.1 | Replenishment logic? | **Cover-days driven** | `requirement = avg_daily_sales × cover_days`. Cover days = lead_time + safety_days. Configurable. `replenishment.py` L468. Also EOQ in ai_demand reorder. | Not min-max or forecast-driven in main replenishment module (forecast-driven is in ai_demand only) | Cover-days based |
| 4.5.2 | IST (Inter-Store Transfer)? | **Implemented** | Dedicated IST endpoint (`/replenishment/ist`). Identifies surplus stores and deficit stores per SKU, generates transfer suggestions with quantities. L611-750 | No transfer cost optimization. Region-based cost heuristic only (same region=₹50, cross=₹100). | Store-to-store |
| 4.5.3 | Pullback (excess → warehouse)? | **Not implemented** | IST handles store-to-store only. No store-to-warehouse pullback recommendations. | Overstocked stores can only transfer to other stores | Not available |
| 4.5.4 | Replacement (alternate style)? | **Not implemented** | No substitute/alternate style recommendations. | Would need similarity matrix or category mapping | Not available |
| 4.5.5 | Supplier constraints (MOQ, Lead time)? | **Partial** | REP-11: MOQ rounding implemented (`round_up_to_moq`). Lead time from config (not from supplier master). No vendor capacity constraint. L474, 397 | No supplier/vendor master with capacity limits | MOQ only |
| 4.5.6 | Output format? | **Implemented** | PO suggestions (order quantities per SKU), IST Transfer suggestions (transfer_id, from_store, to_store, qty). `final_store_level_output` not as separate concept. | No PDF/Excel export of PO. API response only. | JSON API |
| 4.5.7 | Performance at 1M×1000? | **Not tested** | Pandas-based. Current scale: 10 SKUs × 5 stores. Would need distributed compute at scale. | Single-node limitation | ~30K rows |
| 4.5.8 | Batch replenishment? | **Implemented** | All stores processed in one API call. Results grouped by priority class. L552-577 | No "batch ID" or "batch scheduling" concept | Single batch |
| 4.5.9 | Priority-based (topsellers first)? | **Implemented** | Priority classification: Stock-Out > Critical > High > Medium > Low. Store class priority weighting (A>B>C). L532-577. Topsellers get higher allocation_score via ROS. | Priority is ROS-based, not explicitly "topseller first" | ROS + class based |
| 4.5.10 | final_qty_at_store calculated? | **Implemented** | `order_qty = max(0, requirement - current_soh)` per store×SKU. MOQ rounding applied. L468-475 | No warehouse-available check before generating order | Simple gap fill |

---

## 4.6 Gap Analysis & Sales vs Stock Mix

| # | Question | Status | Details | Limitations | Scale |
|---|----------|--------|---------|-------------|-------|
| 4.6.1 | Sales vs stock mix deviation? | **Implemented** | ROS Gap Analysis (`/analytics/ros-gap`): compares raw_ros vs healthy_ros (category median). `gap_analysis.py` L119. Size Gap (`/analytics/size-gap`): compares actual size distribution vs sales-based ideal. L321 | Mix comparison is within-category only, not cross-category | ROS gap + Size gap |
| 4.6.2 | Multiple baselines? | **Partial** | Compares against: (1) Historical sales mix for size distribution, (2) Healthy ROS (category median). No planogram mix, pre/post-SOH mix comparison. | Only 2 baselines: historical sales + category median | 2 baselines |
| 4.6.3 | Severity classification? | **Implemented** | Size gap: Overstock (gap > threshold), Understock (gap < -threshold), Optimal. Configurable thresholds. L384 | Only 3 levels, no "Medium" severity | 3 levels |
| 4.6.4 | Heat maps? | **Implemented (DOH only)** | DOH heatmap: store grid and category grid (`/analytics/doh/heatmap`). DOH-16/17. `doh_analysis.py` L498-570. No heat map for gap analysis specifically. | DOH heatmaps only, not deviation heatmaps | DOH heatmaps |
| 4.6.5 | Attribute-level deviation (color, size, fit)? | **Partial** | Size-level gap analysis implemented. No color/fit/material-level deviation. Attribute grouping available in core_logic (`/core/attribute-grouping`). L579 | Size only, not other attributes | Size level |
| 4.6.6 | Action recommendations from gap? | **Partial** | NOOS module generates recovery plans (L572). Size gap identifies overstock/understock. No automated IST/replenishment/planogram update triggers from gap results. | Manual interpretation needed | Recovery plans |
| 4.6.7 | NOOS detection? | **Implemented** | Dedicated `/analytics/noos` endpoint. Tracks availability %, identifies NOOS SKUs, generates recovery plans. L479-572 | NOOS threshold not user-configurable | Auto-detected |

---

## 4.7 Planogram Fill Rate

| # | Question | Status | Details | Limitations | Scale |
|---|----------|--------|---------|-------------|-------|
| 4.7.1 | Fill rate calculation? | **Implemented** | `fill_rate = (current_stock / norm_allocated) × 100`. PLAN-01. `planogram.py` L108 | Norm from historical max, not from actual planogram allocation | % calculation |
| 4.7.2 | Pre vs Post fill rate? | **Not implemented** | Point-in-time snapshot only. No before/after comparison. | No temporal comparison | Snapshot only |
| 4.7.3 | Compliance thresholds? | **Implemented** | Green ≥90%, Yellow 80-90%, Red <80%. `_classify()` function L70. Configurable via `target_fill_rate` param. | Fixed 3 tiers | Configurable target |
| 4.7.4 | Lost sales due to low fill rate? | **Implemented** | PLAN-21-25: `lost_sales = missing_facings × ROS × ASP`. L137 | Assumes linear relationship between facings and sales | Per-SKU per-store |
| 4.7.5 | Planogram breach for topsellers? | **Not implemented** | No topseller-specific planogram rules. Fill rate treated equally for all SKUs. | No priority flagging | Not available |
| 4.7.6 | Drill down to space planning? | **Not implemented** | No space planning / visual merchandising module. | Would need floor plan integration | Not available |

---

## 4.8 Stock Health

| # | Question | Status | Details | Limitations | Scale |
|---|----------|--------|---------|-------------|-------|
| 4.8.1 | Stock health % calculation? | **Implemented** | `healthy_pct = healthy_count / total_combos × 100` per store. Healthy = size set complete and DOH within optimal range. `gap_analysis.py` L416-419 | Health defined by size completeness + DOH, not inventory freshness/age | % per store |
| 4.8.2 | PSA benchmark? | **Partial** | No explicit "PSA benchmark" label. Configurable ideal_doh serves similar purpose. Store class (A/B/C) used for prioritization. | No "80% healthy stock" global target | Via DOH config |
| 4.8.3 | Category-specific benchmarks? | **Implemented** | `category_ideal_doh` config map allows per-category DOH targets. L105-106 in doh_analysis | Must be manually configured | Configurable |
| 4.8.4 | Improvement indicator? | **Not implemented** | No delta or trend tracking. Each calculation is independent snapshot. | No time-series health tracking | Not available |

---

## 4.9 Stock Flow Analysis

| # | Question | Status | Details | Limitations | Scale |
|---|----------|--------|---------|-------------|-------|
| 4.9.1 | Stock flow waterfall chart? | **Implemented** | WH-12: `opening_stock + change = closing_stock` per day. `warehouse.py` `/daily-stock-change` L194-215 | Warehouse level only, no store-level stock flow | Daily waterfall |
| 4.9.2 | Stock inward components? | **Partial** | Warehouse movements endpoint tracks inwards/outwards. No breakdown into In-Transit, Open Orders, Vendor-to-Store as separate categories. | Single "inwards" category | Simple tracking |
| 4.9.3 | Pre and post stock flow? | **Not implemented** | No before/after replenishment stock flow comparison. | Would need simulation engine | Not available |

---

## PART 5: BACKEND ARCHITECTURE

### 5.1 Processing Pipeline

| # | Question | Status | Details | Limitations | Scale |
|---|----------|--------|---------|-------------|-------|
| 5.1.1 | Processing framework? | **Pandas** | All computation via Pandas DataFrames in FastAPI async handlers. ML models via scikit-learn/statsmodels (lazy-loaded). | Single-node, in-memory | Pandas |
| 5.1.2 | Distributed computing? | **Not implemented** | No Spark/Dask/Ray. All processing on single container. | Memory-bound at ~100K rows per collection. Would fail at 100M+ rows. | Single node |
| 5.1.3 | Job orchestration? | **Custom** | `/api/scheduled-jobs` CRUD with custom scheduler. No Airflow/Prefect. Jobs stored in MongoDB with cron-like schedule. | No DAG, no dependency management, no retry with backoff | Custom cron |
| 5.1.4 | Job failure handling? | **Basic** | Try/catch in scheduled job execution. Error logged. No automatic retry or dead-letter queue. | No retry policy, no alerting on failure | Log-only |
| 5.1.5 | Incremental processing? | **Not implemented** | Each API call reprocesses full dataset from DB. No delta/CDC processing. | Full table scan on every request | Full reprocess |
| 5.1.6 | End-to-end latency (upload → dashboard)? | **~2-5 seconds** | Upload validates + saves to MongoDB. Next dashboard API call reads from DB. No async pipeline. | No real-time streaming | Near-instant |
| 5.1.7 | Checkpointing for long jobs? | **Not implemented** | No checkpointing. If ML forecast fails mid-computation, entire request fails. | No partial result recovery | Not available |
| 5.1.8 | Data backfills? | **Via re-upload** | User re-uploads corrected CSV. V2 upsert replaces existing data. No dedicated backfill API. | Manual process, no audit trail of corrections | Re-upload |

### 5.2 API Layer

| # | Question | Status | Details | Limitations | Scale |
|---|----------|--------|---------|-------------|-------|
| 5.2.1 | API framework? | **FastAPI** | Python 3.11, FastAPI with async/await, Uvicorn server. | Single worker (K8s pod scaling for horizontal) | FastAPI |
| 5.2.2 | REST APIs for upload? | **Implemented** | 6 upload endpoints (`/api/upload/v2/*`), validate endpoint, history, templates. 75-rule validation engine. | No bulk/streaming upload API. Max ~50MB per file (proxy limit). | 6 endpoints |
| 5.2.3 | APIs to trigger algorithms? | **Implemented** | Each algorithm has its own GET endpoint. "Generate Plan" POST endpoint triggers ML forecast + plan generation. | No unified "Run All" button that chains multiple algorithms | Per-module |
| 5.2.4 | APIs for KPI/dashboard? | **Implemented** | Executive Dashboard, BI Dashboards, DOH Analysis, Gap Analysis, Stockout, Planogram — each with dedicated endpoints. | No GraphQL for flexible queries | REST endpoints |
| 5.2.5 | Rate limiting strategy? | **Implemented** | SlowAPI middleware: per-IP rate limiting. AI Demand: 50 req/min custom limit. Chat: 10 req/min. Configurable in middleware. | Per-IP, not per-client/per-tenant. No tiered limits by plan. | IP-based |
| 5.2.6 | Async API with webhooks? | **Not implemented** | All APIs are synchronous request-response. No webhook callbacks for long-running jobs. | ML forecast takes ~1-3s; no async notification | Sync only |
| 5.2.7 | API versioning? | **Partial** | Upload module has `/v2/` prefix. Other modules unversioned. No global `/api/v1/`, `/api/v2/` separation. | Only upload module versioned | Upload only |
| 5.2.8 | Swagger/OpenAPI docs? | **Implemented** | FastAPI auto-generated at `/api/docs`. All endpoints documented with types, query params, response models. | No custom examples or detailed field descriptions | Auto-generated |

### 5.3 Database & Caching

| # | Question | Status | Details | Limitations | Scale |
|---|----------|--------|---------|-------------|-------|
| 5.3.1 | Primary database? | **MongoDB** | Motor async driver. Separate tenant databases for data isolation. Shared DB for user/tenant registry. | Document-oriented, no complex JOINs | MongoDB |
| 5.3.2 | Analytics database? | **Same MongoDB** | No separate OLAP database. Analytics queries run on same MongoDB instance as transactional data. | Mixed workload on single DB. No columnar storage for analytics. | Same DB |
| 5.3.3 | Caching layer? | **None** | No Redis/Memcached. `get_cached_data()` reads from MongoDB on every call. V2 bridge with V1 fallback but no in-memory cache. | Every API call hits MongoDB. Repeated queries re-read full collections. | No cache |
| 5.3.4 | Pre-computed aggregations? | **Not implemented** | All aggregations computed on-the-fly via Pandas. No materialized views or summary tables. | CPU-intensive for large datasets. No pre-computation. | On-the-fly |
| 5.3.5 | Read replicas? | **Not implemented** | Single MongoDB instance (localhost:27017). No replica set configured. | Single point of failure. No read scaling. | Single node |
| 5.3.6 | Connection pooling? | **Motor default** | Motor async client uses default pool (100 connections). No custom configuration. | Default settings, no per-tenant pool isolation | Default pool |
| 5.3.7 | Query timeouts? | **Not configured** | No explicit MongoDB query timeouts. FastAPI request timeout managed by reverse proxy (120s). | Slow queries can block worker thread | Proxy timeout |

### 5.4 Multi-Tenancy

| # | Question | Status | Details | Limitations | Scale |
|---|----------|--------|---------|-------------|-------|
| 5.4.1 | Data isolation? | **Separate DB** | Each tenant gets `tenant_{tenant_id}` database. Shared registry in main DB. `tenant_db.py` L3,84-86 | Full DB-level isolation. Cannot query across tenants. | DB-per-tenant |
| 5.4.2 | Max concurrent clients? | **No hard limit** | Limited by MongoDB connections (default pool 100) and container memory. Currently 3 tenants active. | Not load-tested beyond ~5 concurrent tenants | Pool-limited |
| 5.4.3 | Client-specific configs? | **Implemented** | Per-tenant config collection: `ideal_doh`, `ros_period`, `topseller_x_factor`, `safety_days`, `cover_days`, store classes, category thresholds. | Config must be set manually per tenant (no admin UI for all settings) | Per-tenant DB |
| 5.4.4 | Custom attributes? | **Partial** | Style master supports `attribute1` through `attribute9` custom fields. Attribute grouping module processes them. `core_logic.py` L579 | Fixed 9 attribute slots, not dynamic schema | 9 custom fields |
| 5.4.5 | Resource quota per client? | **Partial** | Plan-based access control (Starter/Professional/Enterprise) with feature gating and user limits. No storage/compute quotas. `core/plan_access.py` | No storage limits, no compute throttling per tenant | Feature-based |
| 5.4.6 | Client onboarding time? | **~5 minutes** | Onboarding Wizard: signup → email verification → tenant creation → config → first upload. Automated via API. | No bulk data migration tool. Manual CSV upload only. | Self-service |

---

## SUMMARY SCORECARD

| Area | Score | Key Strength | Key Gap |
|------|-------|-------------|---------|
| **ROS (4.1)** | 8/10 | Weighted TrueROS, configurable periods | No cluster fallback, no seasonal calendar |
| **DOH (4.2)** | 8/10 | Per-category ideal, topseller multiplier, WH toggle | No dynamic seasonal DOH, no pre/post comparison |
| **Stockout (4.3)** | 7/10 | Duration tracking, lost sales, NOOS, daily trend | No root cause analysis, no post-run comparison |
| **Topseller (4.4)** | 6/10 | X-Factor configurable, auto-detection | No per-store topseller, no bubble chart, no new-launch tracking |
| **Replenishment (4.5)** | 7/10 | Cover-days + IST + MOQ + priority-based | No pullback, no alternate style, no vendor capacity |
| **Gap Analysis (4.6)** | 7/10 | ROS gap, size gap, NOOS, store comparison | No cross-category mix analysis, limited baselines |
| **Planogram (4.7)** | 6/10 | Fill rate + lost sales + compliance tiers | No pre/post, no topseller breach, no space planning |
| **Stock Health (4.8)** | 5/10 | Per-store health %, category DOH config | No improvement tracking, no PSA benchmark |
| **Stock Flow (4.9)** | 4/10 | Daily opening/closing waterfall | No inward breakdown, no pre/post flow |
| **Processing (5.1)** | 4/10 | Fast for small datasets, custom scheduler | No distributed compute, no incremental processing |
| **API Layer (5.2)** | 8/10 | FastAPI, Swagger, rate limiting, RBAC | No async webhooks, limited versioning |
| **Database (5.3)** | 5/10 | V2 bridge, indexes on startup | No caching, no read replicas, no pre-computation |
| **Multi-Tenancy (5.4)** | 8/10 | DB-per-tenant isolation, plan-based access | No resource quotas, no load testing at scale |
