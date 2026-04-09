# END-TO-END DATA FLOW AUDIT REPORT

**Date**: April 10, 2026 | **Application**: GetMyPlan | **Audit Type**: Architecture Compliance

---

## PART 1: DATA UPLOAD HUB → MONGODB

### Upload Type Matrix

| # | Upload Type | V2 Endpoint | V2 Collection | V1 Collection | 75-Rule Validation | Currency Detection | Status |
|---|-------------|-------------|---------------|----------------|--------------------|--------------------|--------|
| 1 | Store Master | `POST /api/upload/v2/store-master` | `store_master` | `uploaded_files` (file_type=store_master) | Yes | Yes | ✅ Working |
| 2 | Style Master | **None (V2)** | **None** | `uploaded_files` (file_type=style_master) | V1 only (basic) | No | ⚠️ V1 Only |
| 3 | SKU Master | `POST /api/upload/v2/sku-master` | `sku_master` | `uploaded_files` (file_type=sku_ean_master) | Yes | Yes | ✅ Working |
| 4 | Planogram | **Not implemented** | **Does not exist** | **Does not exist** | N/A | N/A | ❌ Missing |
| 5 | Daily Sales | `POST /api/upload/v2/daily-sales` | `daily_sales` | `uploaded_files` (file_type=daily_sales) | Yes | Yes | ✅ Working |
| 6 | COGS | **Not implemented** | **Does not exist** | **Does not exist** | N/A | N/A | ❌ Missing |
| 7 | Store Inventory | `POST /api/upload/v2/store-inventory` | `store_inventory` | `uploaded_files` (file_type=store_inventory) | Yes | Yes | ✅ Working |
| 8 | Warehouse Inventory | `POST /api/upload/v2/warehouse-inventory` | `warehouse_inventory` | `uploaded_files` (file_type=warehouse_inventory) | Yes | Yes | ✅ Working |
| 9 | Open Orders & In-Transit | **Not implemented** | **Does not exist** | **Does not exist** | N/A | N/A | ❌ Missing |
| 10 | Warehouse Master | `POST /api/upload/v2/warehouse-master` | `warehouse_master` | `uploaded_files` (file_type=warehouse_master) | Yes | Yes | ✅ Working |

### Summary
- **✅ Working**: 6 out of 10 upload types (Store Master, SKU Master, Daily Sales, Store Inventory, Warehouse Inventory, Warehouse Master)
- **⚠️ Partial**: 1 (Style Master — V1 only, no V2 migration, no 75-rule validation)
- **❌ Missing**: 3 (Planogram, COGS, Open Orders/In-Transit)

### Current Upload Types in Frontend
The DataUploadPage.jsx (L226-231) shows 6 options: `daily_sales`, `store_inventory`, `warehouse_inventory`, `sku_master`, `store_master`, `warehouse_master`. Missing: `style_master`, `planogram`, `cogs`, `open_orders`.

---

## PART 2: SERVICE LAYER VERIFICATION

### Shared Utilities

| # | Utility | Status | File | Function/Line | Formula | Evidence |
|---|---------|--------|------|----------------|---------|----------|
| 1 | ROS Calculation (7/14/30 day) | ✅ | `core_logic.py` | `core_ros()` L114, `ros_period` param | `qty / live_days` | Configurable period, excl returns/promos |
| 2 | True ROS (70/30 weighted) | ✅ | `core_logic.py` | `core_true_ros()` L391 | `0.7×recent + 0.3×historical` | CORE-15 to CORE-18 |
| 3 | DOH Calculation (SOH/ROS) | ✅ | `doh_analysis.py` | `get_doh_analysis()` L82 | `inventory / daily_ros` | DOH-01 to DOH-15, zero handling |
| 4 | Lost Sales (ROS×days×ASP) | ✅ | `stock_out.py` L53-54, `planogram.py` L137 | Inline calc | `((ROS×1)-SOH)×ASP` / `missing_facings×ROS×ASP` | Two implementations (stockout + planogram) |
| 5 | Fill Rate (SOH/Norm) | ✅ | `planogram.py` | L108 | `(current_stock / norm_allocated) × 100` | PLAN-01 |
| 6 | Safety Stock (Z×σ×√LT) | ✅ | `ai_demand.py` | L680 | `z × std_daily × sqrt(lead_time)` | Z-table for service levels 90-99.9% |
| 7 | EOQ (√(2×D×S/H)) | ✅ | `ai_demand.py` | L687-688 | `sqrt(2 × annual_demand × ordering_cost / holding_cost)` | Parameterized ordering/holding costs |
| 8 | Margin (Revenue-COGS)/Revenue | ❌ | **Not implemented** | — | — | `margin_pct` returns MRP Realisation % (proxy), NOT true COGS margin |

### Module Services

| # | Module | File | Status | Key Functions | Data Source |
|---|--------|------|--------|---------------|-------------|
| 1 | DOH Analysis | `doh_analysis.py` | ⚠️ V1 ONLY | Classification (Optimal/Overstocked/Understocked/Stocked-Out), Heatmap grid, Category grid, Ideal DOH config, Topseller multiplier | Reads from `uploaded_files` (V1) |
| 2 | Stock-Out | `stock_out.py` | ✅ V2 Bridge | Duration, NOOS tagging (SOH=0 & ROS>0), Risk tiers, Lost sales, Severity scoring, Trend analysis, Alternatives | Uses injected `get_cached_data` (V2→V1) |
| 3 | Replenishment | `replenishment.py` | ⚠️ V1 ONLY | Cover-days calc, IST suggestions, Priority allocation (A/B/C class), MOQ rounding, Pack size, Warehouse availability | Reads from `uploaded_files` (V1) |
| 4 | Planogram | `planogram.py` | ⚠️ V1 ONLY | Fill Rate, 3-tier compliance (Green/Yellow/Red), Missing facings, Lost sales, Store/category aggregation | Reads from `uploaded_files` (V1) |
| 5 | Gap Analysis | `gap_analysis.py` | ✅ V2 Bridge | ROS gap, Healthy size set gap, Size gap depth, NOOS detection | Uses injected `get_cached_data` (V2→V1) |
| 6 | AI Demand | `ai_demand.py` | ✅ V2 Bridge | Holt-Winters, Random Forest, Seasonal Decomposition, Ensemble forecast, SKU-level forecast, Topseller prediction, Reorder optimization, Supply feasibility | Uses injected `get_cached_data` (V2→V1) |
| 7 | Warehouse | `warehouse.py` | ✅ Direct V2 | Stock levels, Movements, Daily change (opening/closing), Reconciliation, Adjustments, Transfer lifecycle (5 statuses), In-transit tracking, Performance metrics | Reads directly from V2 collections |
| 8 | Core Logic | `core_logic.py` | ⚠️ V1 ONLY | ROS (CORE-01 to CORE-08), Healthy Size Set, TrueROS (CORE-15 to CORE-21), Attribute Grouping, Store-Style Ranking | Reads from `uploaded_files` (V1) |
| 9 | BI Dashboard | `bi_dashboard.py` | ⚠️ V1 ONLY | KPI Overview (Revenue/Qty/ASP/Discount), Revenue Trend, Channel/Category/Regional Breakdown, Store Ranking, Export CSV | Reads from `uploaded_files` (V1) |

### Critical Architecture Gap: V2 Data Bridge

**Root Cause**: 5 out of 9 analytics modules read from the V1 `uploaded_files` collection directly, bypassing the V2→V1 data bridge in `server.py:get_cached_data()`.

| Module | Data Reader | V2 Compatible? |
|--------|------------|----------------|
| `ai_demand.py` | `_get_cached_data` (injected from server.py) | ✅ Yes |
| `gap_analysis.py` | `_get_cached_data` (injected from server.py) | ✅ Yes |
| `stock_out.py` | `_get_cached_data` (injected from server.py) | ✅ Yes |
| `server.py` (exec endpoints) | `get_cached_data` (own) | ✅ Yes |
| `warehouse.py` | Direct V2 collection reads | ✅ Yes |
| **`core_logic.py`** | `_cached()` → `uploaded_files` | ❌ V1 Only |
| **`doh_analysis.py`** | `_cached()` → `uploaded_files` | ❌ V1 Only |
| **`bi_dashboard.py`** | `_cached()` → `uploaded_files` | ❌ V1 Only |
| **`planogram.py`** | `_cached()` → `uploaded_files` | ❌ V1 Only |
| **`replenishment.py`** | `_cached()` → `uploaded_files` | ❌ V1 Only |

---

## PART 3: FRONTEND DASHBOARD VERIFICATION

### 1. Executive Dashboard (`ExecutiveDashboard.js`)
| Data Source | Required | Implemented | Notes |
|------------|----------|-------------|-------|
| daily_sales | ✅ | ✅ | Via `get_cached_data` (V2 bridge) |
| cogs | ❌ Required | ❌ Missing | **No COGS collection**. Margin uses MRP Realisation % as proxy |
| store_inv | ✅ | ✅ | Stock health from inventory data |
| stock_out | ✅ | ✅ | Stockout alerts from stock_out module |

| KPI | Implemented | Notes |
|-----|------------|-------|
| Revenue | ✅ | `executive-kpis` returns `revenue: 361306155.12` |
| Margin % | ⚠️ Proxy | Returns MRP Realisation % (90%), NOT true COGS-based margin |
| Units Sold | ✅ | `units_sold: 312045` |
| Stock Health | ✅ | Via executive-dashboard aggregation |
| Alerts (Stockout) | ✅ | Embedded in executive-dashboard response |
| Alerts (Low DOH) | ✅ | Embedded in executive-dashboard response |
| Alerts (High Risk) | ✅ | Embedded in executive-dashboard response |

### 2. BI Dashboards (`BIDashboards.js`)
| Feature | Implemented | Notes |
|---------|------------|-------|
| Revenue Trend | ✅ | `GET /api/analytics/bi/trend` |
| Category Mix | ✅ | `GET /api/analytics/bi/category-breakdown` |
| Channel Mix | ✅ | `GET /api/analytics/bi/channel-breakdown` |
| Store Ranking | ✅ | `GET /api/analytics/bi/store-ranking` |
| CSV Export | ✅ | `GET /api/analytics/bi/export/csv` |
| V2 Data | ⚠️ V1 Only | Module reads from `uploaded_files` |

### 3. Core Logics (`CoreLogics.js`)
| Feature | Implemented | Notes |
|---------|------------|-------|
| ROS Analysis | ✅ | `GET /api/analytics/core/ros` |
| Gap Analysis | ✅ | `GET /api/analytics/ros-gap` (via gap_analysis.py, V2 bridge) |
| Size Gap | ✅ | `GET /api/analytics/size-gap` |
| Attribute Grouping | ✅ | `GET /api/analytics/core/attribute-grouping` |
| V2 Data | ⚠️ Partial | core_logic reads V1. gap_analysis reads V2. |

### 4. AI Demand (`AIDemandPlanning.js`)
| Feature | Implemented | Evidence |
|---------|------------|----------|
| 12-Month Forecast | ✅ | Returns 12 months, 3 models + ensemble |
| Topseller ID | ✅ | X-factor calculation, revenue growth scoring |
| Reorder Recommendations | ✅ | EOQ-based, safety stock, per-SKU lead times |
| Stockout Risk | ✅ | Days-to-stockout, risk categorization |
| Data Health Dashboard | ✅ | Collection readiness scores |
| SKU-level Forecast | ✅ | `GET /api/analytics/ai-demand/forecast/sku/{sku}` |
| Confidence Score | ✅ | 91.6% (tested) |

### 5. DOH Analysis (`DOHAnalysis.js`)
| Feature | Implemented | Notes |
|---------|------------|-------|
| Heatmap Grid | ✅ | Store × Category heat grid |
| Store Grid | ✅ | Per-store DOH aggregation |
| Category Grid | ✅ | Per-category DOH aggregation |
| Drill-down | ✅ | Store → SKU level detail |
| Classification | ✅ | Optimal/Overstocked/Understocked/Stocked-Out |
| V2 Data | ⚠️ V1 Only | Module reads from `uploaded_files` |

### 6. Stockout (`StockOutAnalysis.js`)
| Feature | Implemented | Notes |
|---------|------------|-------|
| Daily Trend | ✅ | Stockout count over time |
| Lost Sales | ✅ | ROS × days × ASP calculation |
| High Risk List | ✅ | Severity-ranked stockout items |
| NOOS Recovery | ✅ | SOH=0 & ROS>0 detection |
| V2 Data | ✅ | Uses injected get_cached_data (V2 bridge) |

### 7. Replenishment (`ReplenishmentPlanner.js`)
| Feature | Implemented | Notes |
|---------|------------|-------|
| Order Qty | ✅ | Cover days × ROS - SOH |
| IST Transfer | ✅ | Surplus→Deficit store matching, region priority |
| Priority Rules | ✅ | A/B/C class allocation, ROS weighting |
| MOQ Rounding | ✅ | Min order qty + pack size rounding |
| open_orders integration | ❌ Missing | **No open_orders collection** — cannot deduct in-pipeline stock |
| V2 Data | ⚠️ V1 Only | Module reads from `uploaded_files` |

### 8. Data Upload (`DataUploadPage.jsx`)
| Feature | Implemented | Notes |
|---------|------------|-------|
| Upload Types | ⚠️ 6 of 10 | Missing: style_master, planogram, cogs, open_orders |
| 75-Rule Validation | ✅ | Full validation engine for all 6 V2 types |
| Templates | ✅ | `GET /api/upload/v2/template/{type}` |
| History | ✅ | `GET /api/upload/v2/history` + `/history/days` |
| Master Status | ✅ | Shows count + last_updated per master |
| Daily Status | ✅ | Shows upload status per day |

---

## PART 4: CROSS-MODULE DATA FLOW VERIFICATION

### Flow 1: Executive Dashboard KPI ⚠️ PARTIAL
```
daily_sales + cogs → Revenue/Margin KPI
```
- **Revenue**: ✅ WORKING — Returns `361,306,155.12`
- **Margin %**: ⚠️ PROXY — Returns `90.0` but this is MRP Realisation % (`Revenue / (Qty × MRP) × 100`), **NOT** true margin (`(Revenue - COGS) / Revenue × 100`)
- **COGS collection**: ❌ Does not exist. No upload endpoint, no schema, no collection.
- **WoW/YoY**: ✅ WORKING — Week-over-week and year-over-year comparisons active.

### Flow 2: BI Dashboards ✅ WORKING (for V1 tenants)
```
daily_sales + store_master → Revenue by Store
```
- **Tested (demo tenant)**: Revenue by store returns `361,306,155.12`, ASP `1157.87`
- **V2 tenants**: ⚠️ Returns empty — `bi_dashboard.py` reads from V1 `uploaded_files` only

### Flow 3: AI Demand Forecast ✅ WORKING
```
daily_sales (180+ days) → ML Forecast (3 models) → Reorder Recommendations
```
- **Tested**: 3 models returned (`Holt-Winters`, `Random Forest`, `Seasonal Decomposition`)
- **Forecast horizon**: 12 months
- **Confidence**: 91.6%
- **Data source**: V2 bridge (works for both V1 and V2 tenants)

### Flow 4: DOH Analysis ⚠️ V1 ONLY
```
store_inventory / ROS → Days on Hand → Classification
```
- **Logic**: ✅ Correct (`DOH = SOH / daily_ROS`)
- **Classification**: ✅ 4 tiers (Optimal, Overstocked, Understocked, Stocked-Out)
- **V2 tenants**: ❌ Returns empty — `doh_analysis.py` reads from V1 `uploaded_files` only

### Flow 5: Stockout Detection ✅ WORKING
```
store_inventory=0 AND ROS>0 → Stockout → Lost Sales
```
- **Tested**: Returns `stockouts: 0` (expected — seeded data has positive inventory)
- **Formula**: ✅ `daily_lost_sales = (ROS - SOH) × ASP`
- **Data source**: V2 bridge (works for both V1 and V2 tenants)

### Flow 6: Replenishment ⚠️ V1 ONLY
```
ROS × cover_days → Requirement - SOH → Order Quantity
```
- **Logic**: ✅ Correct with MOQ, pack size, warehouse availability check
- **V2 tenants**: ❌ Returns empty — `replenishment.py` reads from V1 `uploaded_files` only
- **open_orders**: ❌ NOT integrated — cannot deduct open orders from requirement

### Flow 7: IST Suggestions ⚠️ V1 ONLY
```
Surplus store → Deficit store → IST Suggestions
```
- **Logic**: ✅ Correct with DOH threshold, region priority, multi-source matching
- **V2 tenants**: ❌ Returns empty — uses same V1-only data reader
- **Transfer approval**: ✅ Workflow exists in warehouse.py (pending→allocated→approved→in_transit→delivered)

---

## PART 5: GAP REPORT

### ❌ MISSING FLOWS (Must Build)

| # | Gap | What's Missing | Files to Create/Modify | Effort |
|---|-----|---------------|----------------------|--------|
| 1 | **COGS Upload & Collection** | No `cogs` collection, no upload endpoint, no schema, no validation rules | `upload.py` (new endpoint), `upload_service.py` (new schema), `server.py` (V2 map) | **Medium** (2-3h) |
| 2 | **Planogram Upload & Collection** | No `planogram` collection, no upload endpoint. Norm is auto-derived from max inventory. | `upload.py` (new endpoint), `upload_service.py` (new schema), adjust `planogram.py` to read uploaded norms | **Medium** (2-3h) |
| 3 | **Open Orders Upload & Collection** | No `open_orders` collection, no upload endpoint. Replenishment can't deduct in-pipeline stock. | `upload.py` (new endpoint), `upload_service.py` (new schema), integrate into `replenishment.py` | **Medium** (2-3h) |
| 4 | **Style Master V2 Migration** | Style master stuck on V1 (`uploaded_files`). `_V2_MAP` maps it to `None`. No V2 upload endpoint. | `upload.py` (new endpoint), `server.py` (update V2_MAP), `upload_service.py` (schema exists) | **Small** (1-2h) |
| 5 | **True Margin Calculation** | Executive dashboard returns MRP Realisation % as proxy. Need COGS for real margin. | Depends on Gap #1 (COGS). Then update `server.py` executive-kpis endpoint. | **Small** (1h) after COGS |

### ⚠️ PARTIAL FLOWS (V2 Migration Required)

| # | Gap | What's Broken | Files to Modify | Effort |
|---|-----|--------------|----------------|--------|
| 6 | **Core Logic V2 Bridge** | `core_logic.py` L36-39: reads from `uploaded_files` (V1 only). Returns empty for V2-only tenants. | `core_logic.py`: Replace `_cached()` with injected `get_cached_data` from server.py, or replicate V2 bridge logic | **Small** (30min) |
| 7 | **DOH Analysis V2 Bridge** | `doh_analysis.py` L33-37: reads from `uploaded_files` (V1 only). | Same pattern as #6 | **Small** (30min) |
| 8 | **BI Dashboard V2 Bridge** | `bi_dashboard.py` L27-29: reads from `uploaded_files` (V1 only). | Same pattern as #6 | **Small** (30min) |
| 9 | **Planogram V2 Bridge** | `planogram.py` L28-29: reads from `uploaded_files` (V1 only). | Same pattern as #6 | **Small** (30min) |
| 10 | **Replenishment V2 Bridge** | `replenishment.py` L37-38: reads from `uploaded_files` (V1 only). | Same pattern as #6 | **Small** (30min) |
| 11 | **Frontend Upload Types** | DataUploadPage.jsx shows 6 types. Missing: style_master, planogram, cogs, open_orders. | `DataUploadPage.jsx` L226-231: Add 4 more SelectItem entries | **Small** (15min) per type |

### OVERALL ARCHITECTURE COMPLIANCE SCORE

| Component | Target | Current | Score |
|-----------|--------|---------|-------|
| Upload Types | 10 | 6 working + 1 V1-only | **65%** |
| V2 Data Bridge | 9 modules | 4 modules (+ 1 direct V2) | **56%** |
| Shared Utilities | 8 functions | 7 implemented (Margin missing) | **88%** |
| Frontend Dashboards | 8 modules | 8 exist, 5 partially broken for V2 | **62%** |
| Cross-Module Flows | 7 flows | 3 fully working, 4 V1-only | **43%** |

### RECOMMENDED PRIORITY ORDER

**Phase 1 — V2 Bridge Migration (Critical, ~2.5h):**
Fix the 5 modules reading from V1 `uploaded_files` to use the V2→V1 bridge. This immediately makes ALL existing features work for V2-only tenants.

**Phase 2 — New Upload Types (~6-9h):**
1. Style Master V2 (easiest — schema already exists)
2. COGS (unlocks true margin)
3. Planogram (unlocks manual norm allocation)
4. Open Orders (unlocks supply pipeline deduction)

**Phase 3 — Margin & Dashboard (~2h):**
Wire COGS into executive dashboard for real margin calculation.
