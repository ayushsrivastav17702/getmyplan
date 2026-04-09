# DEMAND PLANNING MODULE — COMPLETE AUDIT REPORT

**Date**: April 9, 2026  
**Application**: GetMyPlan (zip-improved)  
**Auditor**: E1 Agent  

---

## EXECUTIVE SUMMARY

The demand planning module is a **moderately mature** implementation with a solid ML ensemble engine (Holt-Winters, Random Forest, Seasonal Decomposition) and 7 API endpoints covering forecast generation, stockout risk, topseller prediction, reorder optimization, supply feasibility, and demand plan CRUD with optimistic locking. However, it currently runs **entirely on demo data** for forecasting because the V1 `uploaded_files` collection only contains 1 day of sales history (Jan 1, 2026 — 13,618 rows), far below the 6-month minimum required by the forecast engine.

The **critical gap** is the disconnection between the V2 upload system (which the user actively uploads to) and the AI demand module (which reads exclusively from the V1 `uploaded_files` collection). Stockout risk, topseller prediction, and reorder optimization DO work with real uploaded data, but the core ML forecast always falls back to demo mode. Additionally, there is no mechanism to ingest 12-18 months of historical sales data — the primary requirement for meaningful demand planning.

The frontend (876 lines) is well-built with 6 collapsible sections, Chart.js visualizations, editable demand plans, and confidence meters. The infrastructure is production-ready with rate limiting (50 req/min), RBAC enforcement, lazy ML imports (to prevent K8s startup crashes), and error fallbacks to demo data.

---

## PART 1: CURRENT IMPLEMENTATION ANALYSIS

### 1. FORECASTING METHODS

| # | Algorithm | File | Line | Min Data Required | Status |
|---|-----------|------|------|-------------------|--------|
| 1 | **Holt-Winters (Exponential Smoothing)** | `ml_forecast_engine.py` | L41 | 24 months (2x seasonal_periods) | Working but requires 24+ months |
| 2 | **Random Forest Regressor** | `ml_forecast_engine.py` | L76 | 24 months | Working (100 trees, max_depth=10, lag features 1/2/3/6/12) |
| 3 | **Seasonal Decomposition + Linear Regression** | `ml_forecast_engine.py` | L136 | 24 months (2x seasonal_periods) | Working |
| 4 | **Ensemble (Weighted Average of above)** | `ml_forecast_engine.py` | L172 | 6 months (uses subset of models if data partial) | Working — equal-weight average of available models |
| 5 | **Moving Average (Fallback)** | `ml_forecast_engine.py` | L187 | 1 month | Used when no model succeeds (last-12-month mean) |

**Feature engineering (Random Forest)**:
- Lag features: 1, 2, 3, 6, 12 months
- Rolling mean (3-month, 6-month)
- Rolling std (3-month)
- Month-of-year, quarter cyclic features
- Recursive multi-step prediction

### 2. DATA INPUTS

| Data Source | Collection | Used By | Schema (key fields) |
|-------------|------------|---------|---------------------|
| **Daily Sales** | `uploaded_files` (file_type='daily_sales') | Forecast, Stockout, Topseller, Reorder, Supply | `{sku, store_code, day, quantity, revenue, channel}` |
| **Store Inventory** | `uploaded_files` (file_type='store_inventory') | Stockout, Reorder, Supply | `{store_code, ean, day, quantity}` |
| **SKU-EAN Master** | `uploaded_files` (file_type='sku_ean_master') | All (SKU resolution) | `{ean, style, size, mrp}` |
| **Style Master** | `uploaded_files` (file_type='style_master') | Forecast, Topseller (category grouping) | `{style_code, season, category, subcategory, gender}` |
| **V2 daily_sales** | `daily_sales` collection | **NOT USED** by AI | `{sku, store_code, day, quantity, revenue, tenant_id}` |

**Minimum historical data for each endpoint:**

| Endpoint | Minimum Data | Ideal Data | Current Data | Status |
|----------|-------------|------------|--------------|--------|
| ML Forecast | 6 months | 18-24 months | 1 day | INSUFFICIENT (uses demo) |
| Stockout Risk | 7 days | 30+ days | 1 day | WORKS (limited accuracy) |
| Topseller | 2 months | 6+ months | 1 day | WORKS (limited accuracy) |
| Reorder Optimization | 14 days | 60+ days | 1 day | WORKS (limited accuracy) |
| Supply Feasibility | 7 days | 30+ days | 1 day | WORKS (limited accuracy) |
| Generate Demand Plan | 6 months | 18-24 months | 1 day | WORKS but uses demo forecast |

### 3. FORECAST OUTPUTS

| Feature | Supported | Details |
|---------|-----------|---------|
| Forecast horizons | 1-24 months (default 12) | Configurable via `forecast_horizon` query param |
| MAPE (Mean Absolute % Error) | Yes | Calculated in `_accuracy()` |
| RMSE (Root Mean Square Error) | Yes | Via sklearn.metrics |
| R-squared | Yes | Via sklearn.metrics |
| Confidence Intervals | Yes | 95% CI (1.96 * std) from ensemble model disagreement |
| Confidence Score | Yes | 50-95 scale based on model agreement |
| Seasonality Factors | Yes | Monthly factors (12 months) relative to average |
| Growth Trend | Yes | avg_monthly_growth %, trend: accelerating/stable/declining |

### 4. REORDER LOGIC

| Feature | Implemented | Formula | Location |
|---------|-------------|---------|----------|
| **Reorder Point** | Yes | `avg_daily_demand * lead_time + safety_stock` | ai_demand.py L407 |
| **Safety Stock** | Yes | `Z * std_daily * sqrt(lead_time)` | ai_demand.py L406 |
| **Service Level Z-scores** | Yes | 80%=0.84, 85%=1.04, 90%=1.28, 95%=1.645, 99%=2.33, 99.9%=3.09 | ai_demand.py L404 |
| **Days Until Reorder** | Yes | `(current_stock - reorder_point) / avg_daily_demand` | ai_demand.py L413 |
| **Recommended Order Qty** | Yes | `reorder_point * 1.5 - current_stock` (if reorder needed) | ai_demand.py L415 |
| **EOQ (Economic Order Quantity)** | NO | Not implemented | — |
| **Lead Time from SKU Master** | NO | Hardcoded as query param (default 14 days) | — |
| **DOH Classification** | Yes | Achievable (>120%), At Risk (80-120%), Unachievable (<80%) | ai_demand.py L104-117 |

### 5. SEASONALITY & TRENDS

| Feature | Implemented | Details |
|---------|-------------|---------|
| **Seasonality Detection** | Yes | Monthly factors from last 12 months, normalized to mean=1.0 |
| **Seasonal Decomposition** | Yes | Additive model via statsmodels, extrapolated trend |
| **Trend Detection** | Yes | Growth rate classification: accelerating (>5%), stable, declining (<-5%) |
| **Promotional Events** | NO | Not implemented |
| **Holiday Calendar** | NO | Not implemented |

### 6. AGGREGATION LEVELS

| Level | Supported | How |
|-------|-----------|-----|
| **Category level** | Yes | `?category=Apparel` filter on all endpoints |
| **Subcategory level** | Yes | `?subcategory=Shirts` on forecast/plan endpoints |
| **All Categories (aggregate)** | Yes | Default when no category filter |
| **SKU level** | Partial | Stockout and reorder work at SKU level; forecast is category-level only |
| **Store level** | Partial | Stockout works at store+SKU level; others are aggregate |
| **Warehouse level** | NO | Not implemented |

---

## PART 2: TECHNICAL IMPLEMENTATION DETAILS

### 7. CODE STRUCTURE

| File | Lines | Role |
|------|-------|------|
| `/app/backend/routes/ai_demand.py` | 790 | Main API controller — 7 endpoints, rate limiting, RBAC, demo fallbacks |
| `/app/backend/ml_forecast_engine.py` | 237 | ML engine — 3 models + ensemble + accuracy metrics |
| `/app/frontend/src/pages/AIDemandPlanning.js` | 876 | Frontend — 6 sections, charts, editable plans, KPIs |
| `/app/backend/services/tenant_data_provider.py` | 418 | Data layer — reads from V1 `uploaded_files` collection |
| **Total** | **2,321** | |

**Scheduled Jobs**: The `scheduled_jobs.py` has `"ai_demand"` as a registered job type, but there is NO automated forecast regeneration. Demand plans are generated on-demand only.

### 8. DEPENDENCIES

| Library | Used For | Import Style |
|---------|----------|-------------|
| `scikit-learn` | RandomForestRegressor, LinearRegression, metrics | **Lazy** (try/except at module level) |
| `statsmodels` | Holt-Winters, Seasonal Decomposition | **Lazy** (try/except at module level) |
| `pandas` | Data manipulation, groupby, merge | Direct import |
| `numpy` | Math, array operations | Direct import |
| `Prophet` | NOT used | Not installed |
| **External APIs** | NONE | All computation is local |

### 9. DATABASE SCHEMA

**Collections used by demand planning:**

```
uploaded_files (V1 — PRIMARY DATA SOURCE)
├── file_type: "daily_sales" | "store_inventory" | "sku_ean_master" | "style_master"
├── data: [{ sku, store_code, day, quantity, revenue, channel, ... }]
└── Indexes: _id only (NO compound indexes)

demand_plans (DEMAND PLAN CRUD)
├── category: str
├── annual_target: float
├── total_planned: float
├── variance: float, variance_pct: float
├── subcategories: [{ name, monthly_plan: [12 floats], forecast_values, total, confidence }]
├── status: "draft" | "approved" | "archived"
├── version: int (optimistic locking)
├── created_by, updated_by: str
├── created_at, updated_at: ISO datetime
└── Indexes: _id only

daily_sales (V2 — NOT READ BY AI MODULE)
├── sku, store_code, day, quantity, revenue
├── tenant_id, uploaded_at, uploaded_by
└── Indexes: _id only
```

### 10. API ENDPOINTS

| # | Method | Endpoint | Auth | Purpose |
|---|--------|----------|------|---------|
| 1 | GET | `/api/analytics/ai-demand/options` | All | Dynamic filter values (categories, subcategories) |
| 2 | GET | `/api/analytics/ai-demand/forecast` | All | ML ensemble forecast (12-month default) |
| 3 | GET | `/api/analytics/ai-demand/stockout-risk` | admin/merchandiser/allocator/viewer | SKU-level stockout prediction |
| 4 | GET | `/api/analytics/ai-demand/topseller-prediction` | admin/merchandiser/viewer | X-Factor topseller classification |
| 5 | GET | `/api/analytics/ai-demand/reorder-optimisation` | admin/allocator/merchandiser/viewer | Safety stock + reorder point calc |
| 6 | GET | `/api/analytics/ai-demand/supply-feasibility` | admin/allocator/merchandiser/viewer | DOH-based 12-month supply coverage |
| 7 | POST | `/api/analytics/ai-demand/generate-plan` | admin/merchandiser | Generate demand plan with blended forecast |
| 8 | GET | `/api/analytics/ai-demand/plans` | All | List saved demand plans |
| 9 | GET | `/api/analytics/ai-demand/plans/{id}` | All | Get specific plan |
| 10 | PUT | `/api/analytics/ai-demand/plans/{id}` | admin/merchandiser | Update plan (optimistic locking) |

**Batch/Bulk endpoints**: None

---

## PART 3: WHAT'S WORKING CORRECTLY

| Feature | Status | Notes |
|---------|--------|-------|
| Ensemble forecast generation | WORKING | Falls back to demo data (insufficient history) |
| Confidence intervals (95% CI) | WORKING | Based on inter-model disagreement |
| Stockout risk prediction (SKU x Store) | WORKING | Uses real uploaded V1 data |
| Topseller prediction with X-Factor | WORKING | Uses real V1 data |
| Reorder point + Safety stock | WORKING | Correct formula with configurable Z-score |
| Supply feasibility (DOH) | WORKING | 12-month monthly breakdown |
| Demand plan CRUD with optimistic locking | WORKING | Create, list, get, update with version control |
| Rate limiting (50 req/min) | WORKING | Per-IP bucket |
| RBAC enforcement | WORKING | Role-based access per endpoint |
| Demo fallback | WORKING | All endpoints gracefully fall back to realistic demo data |
| Frontend visualizations | WORKING | Line charts, bar charts, KPIs, editable tables |
| Seasonality factors | WORKING | Monthly factors calculated from historical data |
| Growth trend detection | WORKING | Accelerating/stable/declining classification |

---

## PART 4: GAPS & MISSING FEATURES

### 12. MISSING FEATURES

| # | Feature | Priority | Effort | Notes |
|---|---------|----------|--------|-------|
| 1 | **V2 data bridge** — AI module reads from V1 `uploaded_files`, not V2 `daily_sales` | P0 | 2h | Users upload to V2 but AI doesn't see it |
| 2 | **Historical bulk upload** — No way to upload 12-18 months of past sales at once | P0 | 4h | Required for ML forecast to work on real data |
| 3 | **SKU-level forecast** — Forecast is category-level only | P1 | 8h | Need per-SKU time series |
| 4 | **Store-level forecast** — No store-level breakdown | P1 | 6h | Need per-store demand view |
| 5 | **EOQ (Economic Order Quantity)** — Not implemented | P1 | 4h | `sqrt(2 * demand * ordering_cost / holding_cost)` |
| 6 | **Lead time from SKU master** — Hardcoded as query param | P1 | 2h | Should read from master data |
| 7 | **Promotional/Holiday calendar** — No event-based adjustments | P2 | 12h | Retail events significantly impact demand |
| 8 | **Warehouse-level aggregation** — Not supported | P2 | 6h | Need warehouse demand allocation |
| 9 | **Automated forecast refresh** — No scheduled regeneration | P2 | 4h | Should auto-regenerate daily/weekly |
| 10 | **Forecast accuracy tracking over time** — No historical accuracy log | P2 | 6h | MAPE trend dashboard |
| 11 | **Purchase order integration** — Reorder doesn't create POs | P2 | 12h | Need PO creation workflow |
| 12 | **Prophet integration** — Industry-standard time series model | P3 | 8h | Better holiday/event handling |

### 13. BUGS & ISSUES

| # | Issue | Severity | Location |
|---|-------|----------|----------|
| 1 | **Forecast ALWAYS uses demo data** — V1 daily_sales has only 1 day of history | HIGH | ai_demand.py L162-165 |
| 2 | **V2 upload data invisible to AI** — `_get_cached_data()` reads from `uploaded_files` only | HIGH | server.py L382 |
| 3 | **No indexes on demand-related collections** — Full collection scans | MEDIUM | MongoDB |
| 4 | **Supply feasibility uses naive depletion model** — `supply -= demand * i * 0.3` (arbitrary 30% factor) | LOW | ai_demand.py L671 |
| 5 | **Holt-Winters initialization warning** — statsmodels convergence warnings suppressed | LOW | ml_forecast_engine.py L24 |
| 6 | **New products (zero sales)** — No cold-start handling for new SKUs | LOW | All endpoints |

### 14. DATA GAPS

| Data | Required | Available | Gap |
|------|----------|-----------|-----|
| 12-18 month sales history | YES (for ML) | 1 day (Jan 1, 2026) | CRITICAL |
| Lead time per SKU | YES (for reorder) | Not in SKU master | MISSING |
| Ordering cost per SKU | YES (for EOQ) | Not stored | MISSING |
| Holding cost per SKU | YES (for EOQ) | Not stored | MISSING |
| Promotional calendar | Ideal | Not stored | MISSING |
| Historical stock snapshots | Ideal | Only latest snapshot | PARTIAL |

### 15. INTEGRATION GAPS

| Integration | Connected | Notes |
|-------------|-----------|-------|
| Executive Dashboard | YES | Dashboard shows stockout alerts |
| V2 Upload Module | **NO** | AI reads V1 only |
| Purchase Orders | NO | No PO creation |
| Inventory Alerts | PARTIAL | Stockout risk calculated but no push notifications |
| Scheduled Jobs | PARTIAL | Job type registered but no auto-execution |
| Buy Plan Generator | NO | Separate module, not connected to demand forecast |

---

## PART 5: RECOMMENDED ENHANCEMENTS

### P0 — Immediate (This Week)

1. **Bridge V2 uploads to AI module** — Update `get_cached_data()` to read from V2 `daily_sales` collection when available, falling back to V1 `uploaded_files`
2. **Add historical bulk upload endpoint** — New `/api/upload/v2/historical-sales` that accepts 12-18 months of data in a single CSV, writes to both V1 and V2 collections
3. **Add indexes** — `daily_sales(tenant_id, day)`, `uploaded_files(file_type)`, `demand_plans(category, status)`

### P1 — Short-Term (This Month)

4. Add `lead_time_days` field to SKU master schema and read it in reorder calculation
5. SKU-level forecast endpoint
6. EOQ calculation with ordering/holding cost from config
7. Forecast accuracy dashboard (track MAPE over time)
8. Connect reorder recommendations to Buy Plan generator

### P2 — Long-Term (Next Quarter)

9. Prophet integration for holiday-aware forecasting
10. Automated daily/weekly forecast regeneration via scheduled jobs
11. Promotional calendar module
12. Purchase order creation from reorder recommendations
13. Warehouse-level demand allocation
14. Multi-scenario planning (optimistic/pessimistic/base)

---

## PART 6: SAMPLE OUTPUT VERIFICATION

### Test Run: ML Forecast (Category: All)

```
Endpoint: GET /api/analytics/ai-demand/forecast?forecast_horizon=12
Data Source: DEMO (insufficient real data — only 1 day available, need 6+ months)

Models Used: Holt-Winters, Random Forest
Confidence Score: 50 (capped due to insufficient data)

Forecast (monthly revenue, next 12 months):
  Apr 2026: 462,141    Jul 2026: 526,375    Oct 2026: 648,345
  May 2026: 475,270    Aug 2026: 554,498    Nov 2026: 719,988
  Jun 2026: 505,050    Sep 2026: 570,027    Dec 2026: 679,749
  (Full 12-month forecast with confidence bands available)

Seasonality: Peak in Nov (1.3x), Trough in Feb (0.75x)
Growth Trend: 5.0% avg monthly, "accelerating"
```

### Test Run: Stockout Risk (Real Data)

```
Data Source: UPLOADED (real V1 data)
Total SKU x Store combos: 2,000
  Critical (<=3 days): 1,835 (91.8%)
  High (3-7 days): 42
  Medium (7-14 days): 64
  Low (14-30 days): 59
  Healthy (30+ days): 0

DOH Summary: Achievable=41, At Risk=43, Unachievable=1,916
Note: High critical count is because inventory snapshot is from March 31 (stale)
```

### Test Run: Reorder Optimization (Real Data)

```
Data Source: UPLOADED
Lead Time: 14 days, Service Level: 95% (Z=1.645)
Total SKUs: 200
  Reorder Needed: 181 (90.5%)
  Healthy: 19

Sample: SKU ST0009_M
  Avg Daily Demand: 4.2 units
  Std Daily: 1.8
  Safety Stock: 11.1 units (1.645 * 1.8 * sqrt(14))
  Reorder Point: 69.9 units (4.2 * 14 + 11.1)
  Current Stock: 12
  Days Until Reorder: -13.8 (already past reorder point)
  Recommended Order: 93 units
```

---

## GAP ANALYSIS TABLE

| Feature | Status | Priority | Effort | Impact |
|---------|--------|----------|--------|--------|
| V2 data bridge for AI | MISSING | P0 | 2h | Unlocks real data for AI |
| Historical sales bulk upload | MISSING | P0 | 4h | Enables ML forecasting |
| Database indexes | MISSING | P0 | 1h | Performance on large datasets |
| Lead time from SKU master | MISSING | P1 | 2h | Accurate reorder points |
| SKU-level forecast | MISSING | P1 | 8h | Granular demand planning |
| EOQ calculation | MISSING | P1 | 4h | Optimal order quantities |
| Forecast accuracy tracking | MISSING | P1 | 6h | Model improvement over time |
| Buy Plan integration | MISSING | P1 | 8h | End-to-end planning |
| Prophet model | MISSING | P2 | 8h | Holiday-aware forecasting |
| Auto forecast refresh | MISSING | P2 | 4h | Always-fresh forecasts |
| Promotional calendar | MISSING | P2 | 12h | Event-driven adjustments |
| PO creation workflow | MISSING | P2 | 12h | Actionable recommendations |
| Warehouse allocation | MISSING | P2 | 6h | Multi-warehouse planning |

---

## RECOMMENDED NEXT STEPS

1. **IMMEDIATE**: Bridge V2 → AI data pipeline (2h) — make `get_cached_data('daily_sales')` also read from V2 `daily_sales` collection
2. **IMMEDIATE**: Build historical sales upload flow — accept 12-18 month CSV, populate both V1 and V2 collections
3. **THIS WEEK**: Add MongoDB indexes for demand collections
4. **THIS MONTH**: SKU-level forecast, lead time from master, EOQ
5. **NEXT MONTH**: Forecast accuracy dashboard, Buy Plan integration, auto-refresh
