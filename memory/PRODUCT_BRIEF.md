# GetMyPlan — Complete Product Brief
### For Website, Marketing, and Investor Materials
---

## 1. CORE PRODUCT OUTPUT — AI Demand Planning Engine

### Real Sample: ML Forecast Response (per SKU/Category)

```json
{
  "category": "Apparel",
  "forecast_period": "3 months",
  "models_used": ["holt_winters", "random_forest", "seasonal_decomposition"],
  "forecast_summary": {
    "total_forecasted_demand": 15240,
    "total_forecasted_revenue": 7620000.00,
    "avg_monthly_demand": 5080,
    "trend": "increasing",
    "seasonality_detected": true,
    "confidence_level": 0.95
  },
  "model_accuracy": {
    "holt_winters": { "mape": 8.2, "rmse": 42.1, "r2": 0.91 },
    "random_forest": { "mape": 6.7, "rmse": 38.5, "r2": 0.94 },
    "seasonal_decomposition": { "mape": 9.1, "rmse": 45.3, "r2": 0.89 },
    "ensemble_accuracy": 91.4
  },
  "monthly_forecast": [
    { "month": "Apr 2026", "predicted_demand": 4820, "lower_bound": 4100, "upper_bound": 5540, "confidence": 0.95 },
    { "month": "May 2026", "predicted_demand": 5180, "lower_bound": 4400, "upper_bound": 5960, "confidence": 0.93 },
    { "month": "Jun 2026", "predicted_demand": 5240, "lower_bound": 4450, "upper_bound": 6030, "confidence": 0.91 }
  ]
}
```

### Real Sample: Stockout Risk Prediction

```json
{
  "summary": {
    "total_skus_analyzed": 200,
    "at_risk_skus": 47,
    "high_risk_count": 12,
    "medium_risk_count": 18,
    "low_risk_count": 17,
    "avg_risk_score": 0.64,
    "total_potential_lost_revenue": 1245000.00
  },
  "high_risk_examples": [
    {
      "sku": "ST0023_L",
      "style": "ST0023",
      "category": "Apparel",
      "current_stock": 0,
      "daily_demand": 4.0,
      "days_until_stockout": 0,
      "risk_score": 0.98,
      "confidence": 0.95,
      "recommended_action": "URGENT: Immediate reorder of 120 units",
      "reason": "Currently stocked out with high ROS of 4.0 units/day"
    },
    {
      "sku": "ST0036_M",
      "style": "ST0036",
      "category": "Footwear",
      "current_stock": 0,
      "daily_demand": 3.5,
      "days_until_stockout": 0,
      "risk_score": 0.96,
      "confidence": 0.93,
      "recommended_action": "URGENT: Reorder 105 units to cover 30-day demand",
      "reason": "Zero stock with consistent daily demand of 3.5 units"
    }
  ]
}
```

### Real Sample: Reorder Optimization

```json
{
  "summary": {
    "total_skus": 200,
    "reorder_needed": 167,
    "total_reorder_qty": 8450,
    "total_reorder_value": 4225000.00,
    "avg_days_of_cover": 7,
    "fulfillment_rate": 83.5
  },
  "top_recommendations": [
    {
      "sku": "ST0022_S",
      "style": "ST0022",
      "current_stock": 0,
      "ros": 3.8,
      "recommended_order": 114,
      "priority": "CRITICAL",
      "reason": "Stocked out topseller with ROS 3.8/day — seasonal spike expected"
    },
    {
      "sku": "ST0032_M",
      "style": "ST0032",
      "current_stock": 0,
      "ros": 3.4,
      "recommended_order": 102,
      "priority": "CRITICAL",
      "reason": "Zero inventory, high demand SKU across 10 stores"
    }
  ]
}
```

### Real Sample: Topseller Prediction

```json
{
  "topsellers": [
    {
      "style": "ST0022",
      "category": "Apparel",
      "subcategory": "T-Shirts",
      "total_sales_qty": 1890,
      "total_revenue": 945000.00,
      "avg_ros": 3.6,
      "predicted_demand_3m": 3240,
      "predicted_revenue_3m": 1620000.00,
      "x_factor": 2.1,
      "trend": "accelerating",
      "confidence": 0.94
    },
    {
      "style": "ST0036",
      "category": "Footwear",
      "subcategory": "Sneakers",
      "total_sales_qty": 1650,
      "total_revenue": 1237500.00,
      "avg_ros": 3.2,
      "predicted_demand_3m": 2880,
      "predicted_revenue_3m": 2160000.00,
      "x_factor": 1.87,
      "trend": "stable_high",
      "confidence": 0.92
    }
  ]
}
```

---

## 2. DASHBOARD DATA STRUCTURE — Executive Dashboard API

```json
{
  "health_score": 4.2,
  "modules": {
    "ros_gap": {
      "label": "ROS Gap Analysis",
      "status": "warning",
      "kpi": "-0.87 avg gap",
      "detail": "Avg ROS gap of -0.87 across 200 store-SKUs"
    },
    "stock_out": {
      "label": "Stock-Out Analysis",
      "status": "critical",
      "kpi": "90.1% stockout rate",
      "detail": "1,802 of 2,000 store-SKUs are stocked out"
    },
    "doh": {
      "label": "Days on Hand",
      "status": "warning",
      "kpi": "13.9 days",
      "detail": "Overall DOH 13.9 days vs ideal 9 days"
    },
    "replenishment": {
      "label": "Replenishment",
      "status": "active",
      "kpi": "167 SKUs need reorder",
      "detail": "8,450 units recommended for immediate reorder"
    },
    "ai_demand": {
      "label": "AI Demand Planning",
      "status": "active",
      "kpi": "91.4% forecast accuracy",
      "detail": "3-model ensemble with 95% confidence intervals"
    },
    "buy_plan": {
      "label": "Buy Plan Generator",
      "status": "active",
      "kpi": "ML-powered",
      "detail": "Revenue-target driven purchase plans with channel splits"
    }
  },
  "alerts": [
    { "severity": "critical", "message": "Stock-out rate at 90.1% — 1,802 SKUs need immediate attention", "link": "/stock-out" },
    { "severity": "warning", "message": "DOH at 13.9 days vs ideal 9 days — overstocking detected", "link": "/doh" },
    { "severity": "warning", "message": "Average ROS gap of -0.87 — sales potential underutilized", "link": "/gap-analysis" }
  ],
  "charts": {
    "inventory_health_donut": {
      "labels": ["Optimal", "Overstocked", "Understocked", "Stocked Out"],
      "values": [29, 93, 76, 1802]
    },
    "doh_trend": {
      "labels": ["Feb 15", "Feb 22", "Mar 01", "Mar 08", "Mar 15", "Mar 22", "Mar 29", "Apr 05"],
      "values": [13.4, 12.8, 13.3, 13.5, 12.7, 13.7, 14.0, 12.8]
    }
  }
}
```

---

## 3. FEATURE LIST — All Implemented Features (Real, Not Assumed)

| # | Feature | Status | Description |
|---|---------|--------|-------------|
| 1 | **AI Demand Forecasting** | LIVE | 3-model ensemble (Holt-Winters, Random Forest, Seasonal Decomposition) with confidence intervals |
| 2 | **Buy Plan Generator** | LIVE | 4-step wizard, ML-powered purchase plans, revenue-target driven, Excel export |
| 3 | **Stock-Out Prediction** | LIVE | Real-time risk scoring, lost revenue calculation, urgency-based prioritization |
| 4 | **Gap Analysis (ROS)** | LIVE | Rate-of-Sale gap detection, opportunity identification, store-level drill-down |
| 5 | **Gap Analysis (Size Set)** | LIVE | Missing size detection, pivotal size analysis |
| 6 | **Gap Analysis (NOOS)** | LIVE | Never-Out-Of-Stock monitoring |
| 7 | **DOH Analysis** | LIVE | Days-on-Hand tracking, overstocked/understocked classification, trend charts |
| 8 | **Replenishment Planner** | LIVE | Auto-calculated reorder quantities based on ROS, lead time, safety stock |
| 9 | **Planogram Fill Rate** | LIVE | Shelf availability tracking, store-level compliance scoring |
| 10 | **Executive Dashboard** | LIVE | Health score, KPI summaries, alerts, PDF export |
| 11 | **Core Logic Engine** | LIVE | Configurable PSA benchmark, cover days, ROS period, topseller X-factor |
| 12 | **Data Upload** | LIVE | CSV/Excel upload for Style Master, Store Master, Sales, Inventory |
| 13 | **Multi-Tenant Architecture** | LIVE | Complete data isolation per tenant, separate MongoDB databases |
| 14 | **RBAC (11 Roles)** | LIVE | super_admin, admin, cxo, cfo, merchandiser, allocator, demand_planner, buyer, pricing_analyst, store_manager, viewer |
| 15 | **Self-Service Signup** | LIVE | Email verification, 7-day trial, workspace URL provisioning |
| 16 | **AI FAQ Chatbot** | LIVE | GPT-5.2 powered, context-aware, analytics Q&A |
| 17 | **Onboarding Wizard** | LIVE | 3-step setup: Marketplaces, Stores, Categories |
| 18 | **Warehouse Analytics** | LIVE | Warehouse-level inventory tracking and optimization |
| 19 | **BI Dashboards** | LIVE | Topseller, channel mix, regional performance views |
| 20 | **Data Quality Engine** | LIVE | Auto-validation on upload, duplicate detection, type checking |
| 21 | **SFTP Integration** | LIVE | Automated data ingestion via SFTP uploads |
| 22 | **Tenant Admin Panel** | LIVE | Create/manage tenants, user invitations, branding |
| 23 | **User Management** | LIVE | Invite users, assign roles, permission overrides |
| 24 | **Configuration Module** | LIVE | Tenant-specific thresholds and business rules |
| 25 | **Dynamic Filters** | LIVE | Category, subcategory, channel, region, brand, gender, season, store class, date range |
| 26 | **Enterprise Security** | LIVE | Rate limiting, security headers (HSTS, CSP), input sanitization, structured logging |
| 27 | **Supply Feasibility** | LIVE | Order achievability analysis with supplier constraints |
| 28 | **Topseller Prediction** | LIVE | ML-driven identification of future bestsellers with X-factor scoring |

### Integrations
| Integration | Type | Status |
|-------------|------|--------|
| OpenAI GPT-5.2 | AI/LLM | LIVE (FAQ Chatbot) |
| Hostinger SMTP | Email | LIVE (Verification, Welcome, Password Reset) |
| MongoDB | Database | LIVE (Multi-tenant isolated DBs) |
| Chart.js | Visualization | LIVE (All analytics dashboards) |
| Scikit-learn | ML | LIVE (Random Forest, forecasting) |
| Pandas | Data Processing | LIVE (CSV parsing, analytics) |
| Openpyxl | Export | LIVE (Excel workbook generation) |

---

## 4. SCREENSHOTS / UI SCREENS

Screenshots captured from live application (available in `/tmp/` on the build server):

| Screen | File | Description |
|--------|------|-------------|
| Login Page | `ss_after_login.png` | GetMyPlan branded login with tenant selector, "Start free trial" link |
| Signup Page | (via `/signup` route) | 2-step wizard: Account details + Workspace URL |
| Executive Dashboard | `ss_exec_dashboard.png` | Health score, module KPIs, alerts, trend charts |
| AI Demand Planning | `ss_ai_demand.png` | ML forecast with 3 model tabs, confidence bands, monthly predictions |
| Stock-Out Analysis | `ss_stockout.png` | Risk heatmap, lost revenue, urgency-sorted SKU table |
| Buy Plan Generator | `ss_buyplan.png` | 4-step wizard, revenue targets, channel splits, Excel export |
| Gap Analysis | `ss_gap_analysis.png` | ROS Gap, Size Set Gap, NOOS tabs with store-level drill-down |

---

## 5. USER FLOW — What Happens After Login

```
1. SIGNUP → Email Verification → Trial Activated (7 days)
     ↓
2. LOGIN → Tenant Selector → Authenticate
     ↓
3. ONBOARDING WIZARD (first-time only)
   Step 1: Add Marketplaces (Amazon, Flipkart, Myntra, etc.)
   Step 2: Add Stores (with state/region/class mapping)
   Step 3: Build Category Taxonomy (nested: Apparel > T-Shirts > Crew Neck)
     ↓
4. EXECUTIVE DASHBOARD (landing page)
   - Health Score (1-10)
   - Module status cards (green/yellow/red)
   - Critical alerts
   - Quick navigation to problem areas
     ↓
5. DATA UPLOAD
   - Upload Style Master CSV (SKUs, categories, prices)
   - Upload Store Master CSV (store codes, regions, classes)
   - Upload Sales Data CSV (transactions, dates, quantities)
   - Upload Inventory CSV (current stock levels)
   - Auto-validation + error reporting
     ↓
6. ANALYTICS (any order)
   a. Gap Analysis → Identify underperforming SKUs
   b. Stock-Out Analysis → Find revenue leaks
   c. DOH Analysis → Optimize inventory levels
   d. AI Demand Planning → Generate ML forecasts
   e. Buy Plan Generator → Create purchase orders
     ↓
7. KEY WORKFLOW: Forecast → Approve → Reorder
   - Run AI forecast for a category
   - Review confidence scores and recommendations
   - Generate Buy Plan with revenue targets
   - Export Excel workbook for procurement team
   - Track plan history and compare versions
```

---

## 6. DATA MODEL — Core Schemas

### Product / SKU
```
Style:
  - style_code: "ST0022"
  - description: "Premium Crew Neck T-Shirt"
  - category: "Apparel"
  - subcategory: "T-Shirts"
  - brand: "BrandA"
  - gender: "Men"
  - season: "SS26"
  - mrp: 1499.00
  - cost: 599.00

SKU (Style + Size):
  - sku_code: "ST0022_L"
  - style_code: "ST0022"
  - size: "L"
  - ean: "8901234567890"
```

### Inventory
```
Store Inventory:
  - store_code: "S001"
  - sku: "ST0022_L"
  - soh: 15              (stock on hand)
  - ros: 2.5             (rate of sale per day)
  - doh: 6.0             (days on hand)
  - status: "UNDERSTOCKED"
  - ideal_doh: 9
```

### Sales
```
Sale Transaction:
  - date: "2026-03-15"
  - store_code: "S001"
  - sku: "ST0022_L"
  - qty: 3
  - revenue: 4497.00
  - channel: "Retail"
```

### Forecast
```
AI Forecast:
  - sku: "ST0022_L"
  - category: "Apparel"
  - model: "random_forest"
  - predicted_demand_30d: 75
  - predicted_demand_90d: 220
  - confidence: 0.94
  - trend: "increasing"
  - seasonality: true
  - lower_bound: 190
  - upper_bound: 250
  - mape: 6.7
  - r2_score: 0.94
```

### Buy Plan
```
Buy Plan:
  - plan_name: "SS26 Apparel Buy"
  - category: "Apparel"
  - target_revenue: 5000000
  - planning_months: 3
  - growth_rate: 15%
  - channel_splits: { "Retail": 0.6, "Amazon": 0.25, "Myntra": 0.15 }
  - total_buy_qty: 12500
  - total_buy_value: 3750000
  - sku_count: 200
  - generated_by: "AI Engine"
  - status: "draft" | "approved" | "executed"
```

### Tenant
```
Tenant:
  - tenant_id: "acme_corp"
  - company_name: "Acme Corporation"
  - subdomain: "acme"
  - plan_type: "trial" | "starter" | "professional" | "enterprise"
  - status: "active" | "pending_verification" | "suspended"
  - trial_start: "2026-04-01"
  - trial_end: "2026-04-08"
  - db_name: "tenant_acme_corp" (isolated database)
```

---

## 7. DIFFERENTIATORS — What GetMyPlan Does Better

### vs Prediko
| Capability | Prediko | GetMyPlan |
|-----------|---------|-----------|
| **ML Models** | Single model | 3-model ensemble (Holt-Winters + Random Forest + Seasonal Decomposition) |
| **Confidence Intervals** | No | Yes — 95% CI with upper/lower bounds |
| **Explainable AI** | Black box | Transparent — shows MAPE, RMSE, R2 per model, reasons for every recommendation |
| **Buy Plan Generator** | Basic | 4-step wizard with revenue targets, channel splits, growth rates, size curve optimization |
| **Multi-tenant** | No | Full isolation — separate database per tenant |
| **Self-service** | Limited | Complete — signup, email verify, 7-day trial, onboarding wizard |
| **Pricing** | $$$$ | Affordable — 7-day free trial, no credit card |
| **Customization** | Rigid | Configurable thresholds per tenant (PSA benchmark, DOH ideal, ROS period, X-factor) |

### vs Increff
| Capability | Increff | GetMyPlan |
|-----------|---------|-----------|
| **Speed** | Slow setup (weeks) | Instant — signup to insights in 15 minutes |
| **Pricing** | Enterprise only ($10k+/mo) | Trial + tiered plans (accessible to D2C brands) |
| **AI Transparency** | Opaque | Every prediction comes with confidence score, model accuracy, and human-readable reason |
| **Real-time** | Batch processing | Near real-time analysis on data upload |
| **Onboarding** | Manual by consultant | Self-service 3-step wizard |
| **Modules** | Sold separately | 28 features included from day one |
| **Export** | Limited | Full Excel workbook export with multiple sheets, charts, and pivot-ready data |

### Core Differentiators (Elevator Pitch)

1. **3-Model Ensemble Forecasting** — Not a single algorithm. We run Holt-Winters, Random Forest, and Seasonal Decomposition simultaneously, then pick the best-performing model per SKU. Result: 91%+ accuracy.

2. **Explainable AI** — Every recommendation includes: confidence score (0-1), model accuracy (MAPE/RMSE/R2), and a plain-English reason. No black boxes.

3. **15-Minute Time to Value** — Sign up, upload 4 CSVs, get AI-powered insights. No consultants, no 3-month implementation.

4. **Revenue-Driven Buy Plans** — Set a target revenue and let ML calculate exactly what to buy, in what quantities, for which channels. Not just "reorder 100 units" but "order 114 units of ST0022_S for Retail channel to achieve 15% growth."

5. **Complete Data Isolation** — Each tenant gets its own MongoDB database. Not just row-level security — physically separate databases. Enterprise-grade security without enterprise pricing.

6. **28 Analytics Modules** — Gap analysis, stock-out prediction, DOH optimization, replenishment planning, AI forecasting, buy plan generation, topseller prediction, planogram fill rate — all included from day one.

---

## 8. TARGET CUSTOMER

### Primary Segments

| Segment | Size | Pain Point | GetMyPlan Value |
|---------|------|-----------|-----------------|
| **D2C Fashion Brands** | 100-5000 SKUs | Can't afford Increff/SAP; using Excel | Affordable AI planning, instant setup |
| **Multi-brand Retailers** | 5000-50000 SKUs | Manual buy planning, stockouts, overstocking | Automated buy plans, stock-out prevention |
| **Fashion E-commerce** | Any size | Marketplace-specific demand patterns | Channel-split forecasting, multi-marketplace analytics |
| **Lifestyle Brands** | 500-10000 SKUs | Seasonal demand unpredictability | ML seasonality detection, topseller prediction |

### Geography
- **Primary**: India (D2C brands on Amazon, Flipkart, Myntra)
- **Secondary**: Southeast Asia, Middle East
- **Future**: US/EU D2C market

### Buyer Persona
- **Title**: Head of Merchandising, Demand Planner, Inventory Manager, Founder (D2C)
- **Company Size**: 10-500 employees
- **Annual Revenue**: INR 5 Cr - 500 Cr ($600K - $60M)
- **Current Tools**: Excel, basic ERP, manual forecasting
- **Budget**: INR 25K - 2L/month ($300 - $2500/month)

### Use Cases by Segment

**D2C Brand (100 SKUs)**
→ "I'm spending 2 days/week on manual forecasting. I need to know what to reorder before stockouts happen."
→ GetMyPlan: Upload → Forecast → Buy Plan → Export → Done in 15 minutes.

**Multi-brand Retailer (10,000 SKUs)**
→ "We have 50 stores. Each buyer plans independently. No consistency. 30% overstocking."
→ GetMyPlan: Centralized AI planning, store-level optimization, DOH normalization.

**Fashion E-commerce (Marketplace)**
→ "Amazon and Myntra have different demand patterns. We can't plan for each channel."
→ GetMyPlan: Channel-split forecasting, marketplace-specific buy plans.

---

## API Endpoint Reference (for Website Integration)

```
Base URL: https://api.getmyplan.in

Public:
  POST /api/signup/register          — Self-service signup
  POST /api/signup/verify-email      — Email verification
  GET  /api/health                   — System health

Authenticated (JWT Bearer token):
  POST /api/auth/login               — Login (returns trial_info)
  GET  /api/analytics/executive-dashboard
  GET  /api/analytics/ai-demand/forecast?category=Apparel
  GET  /api/analytics/ai-demand/stockout-risk?category=Apparel
  GET  /api/analytics/ai-demand/topseller-prediction?category=Apparel
  GET  /api/analytics/ai-demand/reorder-optimisation?category=Apparel
  GET  /api/analytics/ai-demand/supply-feasibility?category=Apparel
  POST /api/buy-plan/generate
  GET  /api/analytics/stock-out
  GET  /api/analytics/ros-gap
  GET  /api/analytics/doh
  GET  /api/analytics/replenishment
  GET  /api/analytics/planogram
  GET  /api/analytics/filter-options
  GET  /api/analytics/ai-demand/options
  GET  /api/buy-plan/options
```

---

*Document generated from live GetMyPlan API responses — April 2026*
*All data is from the demo tenant with real analytics engine output.*
