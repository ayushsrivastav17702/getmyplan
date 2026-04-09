# DEMAND PLANNING MODULE — COMPLETE AUDIT REPORT V2

**Date**: April 9, 2026
**Application**: GetMyPlan (zip-improved)
**Auditor**: E1 Agent (Live API + Code Analysis)

---

## 1. FILE INVENTORY

| # | File Path | Lines | Primary Purpose |
|---|-----------|-------|-----------------|
| 1 | `/app/backend/routes/ai_demand.py` | 790 | Main API controller — 10 endpoints (forecast, stockout, topseller, reorder, supply feasibility, demand plan CRUD), rate limiting (50 req/min), RBAC, demo fallbacks |
| 2 | `/app/backend/ml_forecast_engine.py` | 237 | ML engine — Holt-Winters, Random Forest, Seasonal Decomposition, Ensemble averaging, accuracy metrics (MAPE, RMSE, R2) |
| 3 | `/app/backend/services/tenant_data_provider.py` | 418 | Data abstraction layer — reads from V1 `uploaded_files` collection, provides sales/inventory/master DataFrames to all analytics modules, onboarding data fallback |
| 4 | `/app/frontend/src/pages/AIDemandPlanning.js` | 876 | Full frontend — 4 tabs (Demand Planning, Supply Feasibility, Replenishment, AI Insights), Chart.js visualizations, editable demand plan grid, confidence meters, KPI cards |
| **TOTAL** | | **2,321** | |

### Supporting Files (data pipeline)
| File | Lines | Role |
|------|-------|------|
| `/app/backend/server.py` (L379-405) | ~27 | `get_cached_data()` — the function ALL analytics modules call to read data. Currently reads ONLY from V1 `uploaded_files` collection |
| `/app/backend/routes/upload.py` | 545 | V2 Upload module — writes to individual MongoDB collections (`daily_sales`, `sku_master`, etc.) |
| `/app/frontend/src/components/Charts.jsx` | ~150 | Shared Chart.js wrapper (LineChart, BarChart) used by demand planning |

---

## 2. FORECASTING ALGORITHMS

### Model 1: Holt-Winters (Exponential Smoothing)
- **File**: `ml_forecast_engine.py` → `MLForecastEngine.holt_winters_forecast()` (Line 41)
- **Minimum data**: 24 months (2x `seasonal_periods`, where `seasonal_periods=12`)
- **Parameters**: `trend='add'`, `seasonal='add'`, `initialization_method='estimated'`, `optimized=True`
- **Output**: Forecast values + 95% CI (1.96 * residual std) + accuracy metrics
- **Library**: `statsmodels.tsa.holtwinters.ExponentialSmoothing` (lazy import)

### Model 2: Random Forest Regressor
- **File**: `ml_forecast_engine.py` → `MLForecastEngine.random_forest_forecast()` (Line 76)
- **Minimum data**: 24 months (needs 12+ rows after feature engineering)
- **Parameters**: `n_estimators=100`, `max_depth=10`, `random_state=42`, `n_jobs=1`
- **Features**: Lag (1,2,3,6,12), rolling mean (3,6), rolling std (3), month-of-year, quarter
- **Prediction**: Recursive multi-step (each step feeds back as input)
- **Validation**: 80/20 train/val split, MAPE + RMSE + R2 on validation set
- **Library**: `sklearn.ensemble.RandomForestRegressor` (lazy import)

### Model 3: Seasonal Decomposition + Linear Regression
- **File**: `ml_forecast_engine.py` → `MLForecastEngine.seasonal_decomposition_forecast()` (Line 136)
- **Minimum data**: 24 months (2x `seasonal_periods`)
- **Method**: Additive decomposition → extrapolate trend with LinearRegression → re-add seasonal component
- **Library**: `statsmodels.tsa.seasonal.seasonal_decompose` + `sklearn.linear_model.LinearRegression`
- **Known Bug**: Line in logs: `'numpy.ndarray' object has no attribute 'values'` — this model always fails in current version (statsmodels API change)

### Model 4: Ensemble (Weighted Average)
- **File**: `ml_forecast_engine.py` → `MLForecastEngine.ensemble_forecast()` (Line 172)
- **Method**: Equal-weight average of all successful models
- **Confidence**: `max(50, min(95, 100 - mean_std/mean_forecast * 100))` — based on inter-model disagreement
- **CI**: 95% (1.96 * cross-model std deviation)

### Model 5: Moving Average (Fallback)
- **File**: `ml_forecast_engine.py` → `ensemble_forecast()` (Line 187-196)
- **Trigger**: When ALL three models fail
- **Method**: Simple mean of last 12 months, repeated for horizon
- **Confidence**: Fixed at 50

### Currently Active (from live API test):
Only **Holt-Winters** and **Random Forest** run (Seasonal Decomposition crashes with numpy error). The forecast uses demo data because real uploaded data has only ~3 months (90 days) which is below the 6-month minimum.

---

## 3. DATA INPUTS

### Collections Queried

| Source | Collection | Query Method | Fields Used |
|--------|-----------|-------------|-------------|
| V1 Daily Sales | `uploaded_files` (file_type='daily_sales') | `get_cached_data('daily_sales')` | `sku`, `store_code`, `day`, `quantity`, `revenue`, `channel` |
| V1 Store Inventory | `uploaded_files` (file_type='store_inventory') | `get_cached_data('store_inventory')` | `store_code`, `ean`, `day`, `quantity` |
| V1 SKU-EAN Master | `uploaded_files` (file_type='sku_ean_master') | `get_cached_data('sku_ean_master')` | `ean`, `style`, `size`, `mrp` |
| V1 Style Master | `uploaded_files` (file_type='style_master') | `get_cached_data('style_master')` | `style_code`, `category`, `subcategory`, `gender`, `brand`, `season` |
| V1 Store Master | `uploaded_files` (file_type='store_master') | `get_cached_data('store_master')` | `store_code`, `channel`, `city`, `region` |
| V1 Warehouse Inv | `uploaded_files` (file_type='warehouse_inventory') | `get_cached_data('warehouse_inventory')` | `sku`, `warehouse`, `quantity`, `day` |
| **V2 daily_sales** | `daily_sales` collection | **NOT USED by AI module** | `sku`, `store_code`, `day`, `quantity`, `revenue` |
| **V2 sku_master** | `sku_master` collection | **NOT USED by AI module** | `sku`, `product_name`, `category` |

### Caching Mechanism
- **`get_cached_data(file_type)`** in `server.py` (L379):
  ```python
  doc = await tdb.uploaded_files.find_one({"file_type": file_type})
  return pd.DataFrame(doc['data'])  # entire CSV stored as array in single doc
  ```
- **No in-memory cache** — every API call re-queries MongoDB
- **V1 architecture**: Entire CSV stored as a JSON array inside one MongoDB document (`uploaded_files.data[]`). This limits scalability and prevents incremental appends.

### Current Data State (from live DB inspection)

| Database | Collection | Records | Notes |
|----------|-----------|---------|-------|
| `test_database` | `uploaded_files` (V1) | 7 docs (daily_sales=13,618 rows, store_inv=18,000, sku=200, styles=50, stores=10, wh_inv=400, wh_master=2) | This is where AI reads from (no tenant context) |
| `test_database` | `daily_sales` (V2) | 4 docs | Minimal V2 test data |
| `tenant_demo` | `uploaded_files` | 0 | Empty — tenant-specific DB has NO V1 data |
| `tenant_demo` | `daily_sales` (V2) | 0 | Empty — no V2 uploads for this tenant yet |
| `tenant_increff` | All collections | 0 | Empty |

**Critical Finding**: The AI module currently works ONLY because authenticated requests from `admin@demo.com` fall back to `test_database` (the default DB) when tenant context doesn't resolve properly. If proper tenant isolation is enforced, all AI demand endpoints would return demo/fallback data.

---

## 4. REORDER LOGIC

### Reorder Point (ROP) Formula
**File**: `ai_demand.py` L407
```
reorder_point = avg_daily_demand * lead_time_days + safety_stock
```

### Safety Stock Formula
**File**: `ai_demand.py` L406
```
safety_stock = Z * std_daily_demand * sqrt(lead_time_days)
```
Where Z-scores map to service levels:
| Service Level | Z-Score |
|---------------|---------|
| 80% | 0.84 |
| 85% | 1.04 |
| 90% | 1.28 |
| 95% | 1.645 |
| 97.5% | 1.96 |
| 99% | 2.33 |
| 99.9% | 3.09 |

### Days Until Reorder
```
days_until_reorder = (current_stock - reorder_point) / avg_daily_demand
```
Negative values = already past reorder point (stock below ROP).

### Recommended Order Quantity
```
IF status == 'reorder_needed':
    recommended_order = reorder_point * 1.5 - current_stock
    (clipped to minimum 0)
ELSE:
    recommended_order = 0
```

### EOQ (Economic Order Quantity)
**Status: NOT IMPLEMENTED**
The classic formula `sqrt(2 * annual_demand * ordering_cost / holding_cost)` is not present. The `recommended_order = reorder_point * 1.5 - current_stock` is a simplified heuristic, not EOQ.

### Lead Time
**Source**: Hardcoded as query parameter `lead_time_days` (default: 14 days, range: 1-90)
**Not read from SKU master** — there is no `lead_time_days` field in the SKU/style master schema.

### DOH (Days on Hand) Classification
**File**: `ai_demand.py` L104-117
```
coverage_pct = (stock_on_hand / (avg_daily_demand * lead_time)) * 100
- Achievable: coverage > 120%
- At Risk: 80% <= coverage <= 120%
- Unachievable: coverage < 80%
```

### Live Test Results (Reorder):
```
Total SKUs: 200
Reorder needed: 181 (90.5%)
Healthy: 19
DOH: Achievable=19, At Risk=39, Unachievable=142

Sample: SKU ST0031_S
  avg_daily=3.36, std_daily=2.64, safety_stock=16.3
  reorder_point=63.4, current_stock=0, days_until_reorder=-18.9
  recommended_order=95 units
```

---

## 5. API ENDPOINTS

| # | Method | Path | Auth | Parameters | Purpose |
|---|--------|------|------|------------|---------|
| 1 | GET | `/api/analytics/ai-demand/options` | All authenticated | — | Dynamic filter values (categories, subcategories, channels, data status) |
| 2 | GET | `/api/analytics/ai-demand/forecast` | All authenticated | `category`, `subcategory`, `forecast_horizon` (1-24, default 12) | ML ensemble forecast with confidence intervals |
| 3 | GET | `/api/analytics/ai-demand/stockout-risk` | admin/merchandiser/allocator/viewer | `category`, `limit` (1-100, default 20) | SKU x Store stockout prediction with DOH |
| 4 | GET | `/api/analytics/ai-demand/topseller-prediction` | admin/merchandiser/viewer | `category`, `x_factor` (1.0-5.0, default 2.0), `limit` (1-50, default 10) | X-Factor topseller classification |
| 5 | GET | `/api/analytics/ai-demand/reorder-optimisation` | admin/allocator/merchandiser/viewer | `limit` (1-50, default 15), `lead_time_days` (1-90, default 14), `service_level` (80-99.9, default 95) | Safety stock + reorder point calculation |
| 6 | GET | `/api/analytics/ai-demand/supply-feasibility` | admin/allocator/merchandiser/viewer | `plan_id`, `lead_time_days` (1-90, default 14) | DOH-based 12-month supply coverage |
| 7 | POST | `/api/analytics/ai-demand/generate-plan` | admin/merchandiser | `category`, `annual_target` (default 10,000,000) | Generate blended demand plan (60% forecast + 40% target) |
| 8 | GET | `/api/analytics/ai-demand/plans` | All authenticated | — | List saved demand plans (newest first, max 50) |
| 9 | GET | `/api/analytics/ai-demand/plans/{plan_id}` | All authenticated | — | Get specific demand plan by ID |
| 10 | PUT | `/api/analytics/ai-demand/plans/{plan_id}` | admin/merchandiser | `expected_version` (required), body: `{subcategories, annual_target, status}` | Update plan with optimistic locking |

### Sample Responses

**Forecast** (abbreviated):
```json
{
  "category": "All", "subcategory": "All", "forecast_horizon": 12,
  "months": [{"month": 4, "year": 2026, "label": "Apr 2026"}, ...],
  "forecast": [462141.29, 464280.61, 511448.04, ...],
  "confidence_intervals": {"lower": [460480.33, ...], "upper": [463802.25, ...]},
  "models_used": ["Holt-Winters", "Random Forest"],
  "confidence_score": 50,
  "seasonality_factors": {"1": 0.71, "2": 0.72, ..., "10": 1.34, "11": 1.24},
  "growth_trend": {"avg_monthly_growth": 5.0, "trend": "accelerating"},
  "insufficient_data": true,
  "data_source": "demo"
}
```

**Stockout Risk** (abbreviated):
```json
{
  "summary": {"critical": 1835, "high": 42, "medium": 64, "low": 59, "healthy": 0, "total": 2000, "snapshot_date": "2026-03-31"},
  "items": [{"sku": "ST0001_L", "store_code": "S001", "soh": 0, "ros": 2.5, "days_until_stockout": 0, "risk": "critical"}],
  "data_source": "uploaded"
}
```

---

## 6. DATABASE SCHEMA

### `demand_plans` Collection
```json
{
  "category": "Accessories",
  "annual_target": 10000000.0,
  "total_planned": 10000000.2,
  "variance": -0.2,
  "variance_pct": -0.0,
  "subcategories": [
    {
      "name": "Dresses",
      "monthly_plan": [166666.67, 166666.67, ...],  // 12 float values
      "forecast_values": [166666.67, ...],           // 12 float values
      "total": 2000000.04,
      "confidence": 50
    }
  ],
  "status": "draft",           // "draft" | "approved" | "archived"
  "version": 1,                // Optimistic locking counter
  "created_by": "admin@demo.com",
  "updated_by": "admin@demo.com",
  "created_at": "2026-04-09T09:13:08.123Z",
  "updated_at": "2026-04-09T09:13:08.123Z",
  "data_source": "demo"        // "demo" | "uploaded"
}
```

### `uploaded_files` Collection (V1 — current data source)
```json
{
  "file_type": "daily_sales",
  "data": [                           // Entire CSV as JSON array (max ~20K rows)
    {"sku": "ST0001_L", "store_code": "S001", "day": "2026-01-01", "quantity": 3, "revenue": 1350.0, "channel": "online"},
    ...
  ],
  "columns": ["channel", "store_code", "sku", "day", "online", "quantity", "discount_value", "revenue"],
  "rows": 13618,
  "validation": {...},
  "uploaded_at": "2026-04-07T..."
}
```

### V2 Collections (NOT used by AI module — separate docs per row)
```
daily_sales:        {sku, store_code, day, quantity, revenue, tenant_id, uploaded_at, uploaded_by}
store_inventory:    {store_code, sku, closing_stock, tenant_id, uploaded_at, uploaded_by}
sku_master:         {sku, product_name, category, tenant_id, uploaded_at, uploaded_by}
store_master:       {store_code, store_name, tenant_id, uploaded_at, uploaded_by}
warehouse_master:   {warehouse, warehouse_name, online_fulfillment_flag, tenant_id, uploaded_at, uploaded_by}
warehouse_inventory:{warehouse, sku, on_hand_qty, available_qty, allocated_qty, tenant_id, uploaded_at, uploaded_by}
```

**Note**: There is NO dedicated `demand_forecasts` or `reorder_recommendations` collection. Forecasts are computed on-the-fly per request. Only demand plans are persisted.

---

## 7. GAP ANALYSIS TABLE

| Feature | Status | Notes |
|---------|--------|-------|
| Simple Moving Average | ✅ Implemented | Fallback in `ensemble_forecast()` when all models fail (L187) |
| Weighted Moving Average | ❌ Missing | Not implemented (ensemble uses equal weights) |
| Exponential Smoothing | ✅ Implemented | Holt-Winters with additive trend + seasonality |
| Holt-Winters (Seasonal) | ✅ Implemented | `ml_forecast_engine.py` L41, needs 24 months data |
| ARIMA / SARIMA | ❌ Missing | Not implemented |
| Prophet (Facebook) | ❌ Missing | Not installed, not implemented |
| Safety Stock Calculation | ✅ Implemented | `Z * std_daily * sqrt(lead_time)` with configurable Z-scores |
| EOQ Calculation | ❌ Missing | No ordering_cost/holding_cost fields exist |
| Reorder Point Formula | ✅ Implemented | `avg_daily * lead_time + safety_stock` |
| Lead Time from SKU Master | ❌ Missing | Hardcoded as query param (default 14 days) |
| Seasonality Detection | ✅ Implemented | Monthly factors normalized to mean=1.0 |
| Trend Detection | ✅ Implemented | Growth rate: accelerating (>5%), stable, declining (<-5%) |
| Holiday/Promotion Adjustment | ❌ Missing | No calendar or event system |
| Forecast Accuracy (MAPE/MAE) | ✅ Implemented | MAPE, RMSE, R2 via sklearn.metrics |
| Confidence Intervals | ✅ Implemented | 95% CI from inter-model disagreement (1.96 * std) |
| SKU-level Forecasting | ⚠️ Partial | Stockout + reorder work at SKU level; forecast is category-level only |
| Store-level Forecasting | ⚠️ Partial | Stockout works at store+SKU level; others are aggregate |
| Category-level Aggregation | ✅ Implemented | Filter by `?category=` on all endpoints |
| Stockout Risk Prediction | ✅ Implemented | SKU x Store with DOH classification, 5-tier risk levels |
| Top Seller Prediction | ✅ Implemented | X-Factor classification with linear regression prediction |
| Supply Feasibility Check | ✅ Implemented | 12-month DOH-based supply vs demand coverage |
| Purchase Order Generation | ❌ Missing | Reorder recommendations exist but no PO creation workflow |
| V2 Data Bridge | ❌ Missing | AI module reads from V1 `uploaded_files` only, ignoring V2 collections |
| Warehouse-level Aggregation | ❌ Missing | No warehouse-level demand view |
| Forecast Caching/Persistence | ❌ Missing | Forecasts computed on-the-fly, never cached |
| Automated Forecast Refresh | ❌ Missing | No scheduled regeneration (job type registered but not implemented) |

---

## 8. SAMPLE OUTPUT (Live API Test)

### Forecast Test (Category: All, Horizon: 12)
```
Data Source: DEMO (insufficient real data — 90 days available, need 180+ days)
Models Used: Holt-Winters, Random Forest (Seasonal Decomposition CRASHED)
Confidence Score: 50 (capped due to insufficient data)

Monthly Forecast (next 12 months, revenue):
  Apr 2026: 462,141     Jul 2026: 618,633     Oct 2026: 648,345
  May 2026: 464,281     Aug 2026: 679,749     Nov 2026: 703,522
  Jun 2026: 511,448     Sep 2026: 551,291     Dec 2026: 701,325
                                                Jan 2027: 522,829
                                                Feb 2027: 540,413
                                                Mar 2027: 679,110

Seasonality: Peak in Oct (1.34x), Trough in Jan (0.71x)
Growth Trend: 5.0% avg monthly, "accelerating"
```

### Stockout Risk Test (Real V1 Data)
```
Data Source: UPLOADED (from V1 uploaded_files)
Total SKU x Store combos: 2,000
  Critical (<=3 days): 1,835 (91.8%)
  High (3-7 days): 42
  Medium (7-14 days): 64
  Low (14-30 days): 59
  Healthy (30+ days): 0

Snapshot Date: 2026-03-31 (stale — inventory from same upload day)
```

### Reorder Optimization Test (Real V1 Data)
```
Data Source: UPLOADED
Lead Time: 14 days, Service Level: 95% (Z=1.645)
Total SKUs: 200
  Reorder Needed: 181 (90.5%)
  Healthy: 19

Top Item: SKU ST0031_S
  Avg Daily Demand: 3.36 units
  Std Daily: 2.64
  Safety Stock: 16.3 units
  Reorder Point: 63.4 units
  Current Stock: 0
  Days Until Reorder: -18.9 (past due)
  Recommended Order: 95 units
```

### Topseller Prediction Test (Real V1 Data)
```
Data Source: UPLOADED
Category Average Revenue: 618,246.92
X-Factor Threshold: 2.0

Top Style: ST0012
  Current Monthly Avg: 774,541
  Growth Rate: 53.8%
  Predicted Revenue (3m): 3,842,792
  X-Factor: 1.25 (NOT topseller — below 2.0 threshold)
```

### Supply Feasibility Test (Real V1 Data)
```
Data Source: UPLOADED
Total SKUs: 133
  Achievable: 19, At Risk: 39, Unachievable: 75
  All 12 months: UNACHIEVABLE (supply runs out by month 2)

Month 1 (Apr 2026): Demand=13,560, Supply=4,853, Coverage=35.8%
Month 2 (May 2026): Demand=13,560, Supply=785, Coverage=5.8%
Month 3+ : Supply = 0
```

**NOTE**: No SKU-level forecast test is possible because forecasting only operates at category level. Individual SKU forecasting is not implemented.

---

## 9. KNOWN ISSUES

### Bugs
| # | Issue | Severity | Location | Details |
|---|-------|----------|----------|---------|
| 1 | **Seasonal Decomposition model always crashes** | HIGH | `ml_forecast_engine.py` L136 | Error: `'numpy.ndarray' object has no attribute 'values'` — statsmodels API changed, `.values` is called on numpy array instead of pandas Series |
| 2 | **Forecast ALWAYS uses demo data** | HIGH | `ai_demand.py` L162-165 | V1 `uploaded_files` has only 90 days (3 months) of sales; forecast requires 6+ months (180 days) |
| 3 | **V2 upload data invisible to AI** | HIGH | `server.py` L379 | `get_cached_data()` reads ONLY from `uploaded_files` collection, ignoring V2 `daily_sales`, `sku_master`, etc. |
| 4 | **Tenant isolation broken** | HIGH | `server.py` L96 | When tenant context fails to resolve, falls back to `test_database` (shared DB). All tenants see the same demo data. |
| 5 | **Supply feasibility uses arbitrary depletion** | MEDIUM | `ai_demand.py` L671 | `supply -= demand * i * 0.3` — the 30% factor is hardcoded with no business justification |
| 6 | **No MongoDB indexes** on demand collections | MEDIUM | MongoDB | Full collection scans on `uploaded_files`, `demand_plans`, V2 collections |

### Performance Concerns
| Concern | Impact | Location |
|---------|--------|----------|
| V1 `uploaded_files` loads entire CSV into memory per request | High memory for large datasets (13K+ rows) | `server.py` L382 |
| No caching of forecast results | Recomputes ML models on every API call (~1.1s per request) | `ai_demand.py` |
| Random Forest trains from scratch on every request | CPU-intensive for large datasets | `ml_forecast_engine.py` L103 |
| Sequential model execution (not parallel) | 3x latency if all models run | `ml_forecast_engine.py` L177-185 |

### Hardcoded Values That Should Be Configurable
| Value | Current | Location | Should Be |
|-------|---------|----------|-----------|
| Lead time | 14 days (query param default) | `ai_demand.py` L381 | Read from SKU/style master |
| Rate limit | 50 req/min | `ai_demand.py` L42 | Configurable per tenant/plan |
| Forecast confidence cap | 50 when insufficient data | `ai_demand.py` L177 | Configurable threshold |
| Annual target default | 10,000,000 | `ai_demand.py` L454 | Should come from tenant config |
| Plan blend ratio | 60% forecast / 40% target | `ai_demand.py` L491 | Configurable per plan |
| Recommended order multiplier | 1.5x reorder point | `ai_demand.py` L415 | Should be configurable or use EOQ |
| Supply depletion factor | 0.3 per month | `ai_demand.py` L671 | Should use actual demand forecast |
| Min months for forecast | 6 months | `ai_demand.py` L163 | Should be configurable |
| Seasonal periods | 12 (monthly) | `ml_forecast_engine.py` | Could support weekly (52) |
| Random Forest trees | 100 | `ml_forecast_engine.py` L103 | Configurable for accuracy vs speed |

---

## SUMMARY TABLE

| Area | Score | Status |
|------|-------|--------|
| Forecasting Models | 7/10 | 3 models + ensemble, but one is broken and data pipeline disconnected |
| Reorder Logic | 6/10 | ROP + Safety Stock implemented, but no EOQ, hardcoded lead time |
| Data Pipeline | 3/10 | V2 upload system exists but AI doesn't read from it |
| Frontend | 8/10 | Well-built UI with 4 tabs, charts, editable plans, confidence indicators |
| API Design | 8/10 | Clean REST endpoints with rate limiting, RBAC, optimistic locking |
| Performance | 4/10 | No caching, no indexes, models retrained on every request |
| Production Readiness | 4/10 | Demo data fallbacks mask real issues; tenant isolation broken |
