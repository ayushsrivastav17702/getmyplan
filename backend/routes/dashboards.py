"""
Dashboards API: Buy Plan Readiness + Forecast Accuracy.
"""
from fastapi import APIRouter, Depends, Request
from datetime import datetime, timezone
import logging

router = APIRouter(prefix="/dashboards", tags=["dashboards"])

_db_func = None
_get_current_user = None

logger = logging.getLogger(__name__)


def init_dashboards(get_db_func, get_current_user_func):
    global _db_func, _get_current_user
    _db_func = get_db_func
    _get_current_user = get_current_user_func


async def _dep_user(request: Request) -> dict:
    return await _get_current_user(request)


def _tenant_match(tenant_id: str) -> dict:
    return {"$or": [{"tenant_id": tenant_id}, {"tenant_id": {"$exists": False}}]}


# ──────────────────────────────────────────────
#  BUY PLAN READINESS
# ──────────────────────────────────────────────

@router.get("/readiness")
async def get_readiness(user: dict = Depends(_dep_user)):
    """Buy plan readiness audit — checks data completeness for buy planning."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    tmatch = _tenant_match(tenant_id)

    checks = []

    # Use estimated counts for large collections (instant, no full scan)
    sales_count = await db.daily_sales.estimated_document_count()

    # Get store and SKU counts from master tables (small, fast)
    total_stores = await db.store_master.estimated_document_count()
    if total_stores == 0:
        total_stores = len(await db.daily_sales.distinct("store_code"))

    total_skus = await db.sku_ean_master.estimated_document_count()
    if total_skus == 0:
        total_skus = len(await db.daily_sales.distinct("sku"))

    # 1. Store Wedge Classification
    store_wedge_count = await db.store_wedge_results.estimated_document_count()
    checks.append({
        "id": "store_wedge",
        "label": "Store Wedge Classification",
        "description": "Stores classified into A/B/C wedges by revenue",
        "current": store_wedge_count,
        "total": max(total_stores, store_wedge_count),
        "passed": store_wedge_count > 0,
        "weight": 20,
        "category": "classification",
    })

    # 2. Style Mix Tagging
    style_mix_count = await db.style_mix_results.estimated_document_count()
    checks.append({
        "id": "style_mix",
        "label": "Style Mix Tagging",
        "description": "SKUs tagged as Core/Fashion/Test",
        "current": style_mix_count,
        "total": max(total_skus, style_mix_count),
        "passed": style_mix_count > 0,
        "weight": 15,
        "category": "classification",
    })

    # 3. Daily Sales Data
    checks.append({
        "id": "daily_sales",
        "label": "Daily Sales Data",
        "description": "Historical sales transactions loaded",
        "current": sales_count,
        "total": sales_count,
        "passed": sales_count >= 100,
        "weight": 20,
        "category": "data",
    })

    # 4. SKU Master
    sku_count = await db.sku_ean_master.estimated_document_count()
    checks.append({
        "id": "sku_master",
        "label": "SKU Master",
        "description": "Product/SKU catalog uploaded",
        "current": sku_count,
        "total": sku_count,
        "passed": sku_count > 0,
        "weight": 10,
        "category": "data",
    })

    # 5. Sell-Through Config
    sell_cfg = await db.buy_plan_config.find_one({"type": "sell_through_targets"})
    checks.append({
        "id": "sell_through",
        "label": "Sell-Through Targets",
        "description": "Target sell-through % configured per wedge/mix",
        "current": 1 if sell_cfg else 0,
        "total": 1,
        "passed": sell_cfg is not None,
        "weight": 10,
        "category": "config",
    })

    # 6. Inventory Data
    inv_count = await db.store_inventory.estimated_document_count()
    checks.append({
        "id": "inventory",
        "label": "Store Inventory",
        "description": "Current SOH and in-transit inventory loaded",
        "current": inv_count,
        "total": inv_count,
        "passed": inv_count > 0,
        "weight": 15,
        "category": "data",
    })

    # 7. Display Minimums
    dm_count = await db.display_minimums.estimated_document_count()
    checks.append({
        "id": "display_minimums",
        "label": "Display Minimums",
        "description": "Minimum display quantities set per category/wedge",
        "current": dm_count,
        "total": dm_count,
        "passed": dm_count > 0,
        "weight": 5,
        "category": "config",
    })

    # 8. Promotions
    promo_count = await db.promotions.estimated_document_count()
    checks.append({
        "id": "promotions",
        "label": "Promotions Calendar",
        "description": "Active promotions with lift factors configured",
        "current": promo_count,
        "total": promo_count,
        "passed": promo_count > 0,
        "weight": 5,
        "category": "config",
    })

    # Calculate readiness score
    total_weight = sum(c["weight"] for c in checks)
    earned_weight = sum(c["weight"] for c in checks if c["passed"])
    readiness_score = round((earned_weight / total_weight * 100) if total_weight else 0)

    passed_count = sum(1 for c in checks if c["passed"])

    # Generate recommendations
    recommendations = []
    for c in checks:
        if not c["passed"]:
            if c["id"] == "store_wedge":
                recommendations.append({"priority": "high", "message": "Run Store Wedge classification to categorize stores into A/B/C tiers", "action_path": "/buy-planning"})
            elif c["id"] == "style_mix":
                recommendations.append({"priority": "high", "message": "Run Style Mix tagging to classify SKUs as Core/Fashion/Test", "action_path": "/buy-planning"})
            elif c["id"] == "daily_sales":
                recommendations.append({"priority": "high", "message": "Upload daily sales data (minimum 100 transactions recommended)", "action_path": "/upload"})
            elif c["id"] == "sku_master":
                recommendations.append({"priority": "high", "message": "Upload SKU/EAN master data", "action_path": "/upload"})
            elif c["id"] == "sell_through":
                recommendations.append({"priority": "medium", "message": "Configure sell-through targets in Buy Planning > Config tab", "action_path": "/buy-planning"})
            elif c["id"] == "inventory":
                recommendations.append({"priority": "medium", "message": "Upload store inventory data for safety stock calculations", "action_path": "/buy-planning"})
            elif c["id"] == "display_minimums":
                recommendations.append({"priority": "low", "message": "Set display minimums per category and wedge", "action_path": "/buy-planning"})
            elif c["id"] == "promotions":
                recommendations.append({"priority": "low", "message": "Add promotion calendar entries with lift factors", "action_path": "/buy-planning"})

    return {
        "readiness_score": readiness_score,
        "passed": passed_count,
        "total": len(checks),
        "checks": checks,
        "recommendations": recommendations,
    }


# ──────────────────────────────────────────────
#  FORECAST ACCURACY
# ──────────────────────────────────────────────

@router.get("/forecast-accuracy")
async def get_forecast_accuracy(user: dict = Depends(_dep_user)):
    """Compare forecast snapshots against actual sales to compute accuracy metrics."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    tmatch = _tenant_match(tenant_id)

    # Get all forecast snapshots (latest per category)
    snapshots = await db.forecast_snapshots.find(
        {}, {"_id": 0}
    ).sort("created_at", -1).to_list(200)

    if not snapshots:
        # Try without tenant filter (global snapshots)
        snapshots = await db.forecast_snapshots.find(
            {}, {"_id": 0}
        ).sort("created_at", -1).to_list(200)

    # Group by category — keep only latest per category
    latest_by_cat = {}
    for s in snapshots:
        cat = s.get("category", "All")
        if cat not in latest_by_cat:
            latest_by_cat[cat] = s

    # Aggregate actual revenue per month from daily_sales
    actuals_pipeline = [
        {"$match": tmatch},
        {"$addFields": {"month_key": {"$substr": ["$day", 0, 7]}}},
        {"$group": {
            "_id": "$month_key",
            "actual_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$revenue", 0]}}},
            "total_qty": {"$sum": {"$toInt": {"$ifNull": ["$quantity", 0]}}},
        }},
        {"$sort": {"_id": 1}},
    ]
    actuals_raw = await db.daily_sales.aggregate(actuals_pipeline).to_list(100)
    actuals_map = {a["_id"]: a["actual_revenue"] for a in actuals_raw}

    # Build monthly comparison for "All" category
    all_forecast = latest_by_cat.get("All", {})
    forecast_data = all_forecast.get("forecast_data", [])

    monthly_comparison = []
    total_abs_error = 0
    total_actual = 0
    total_bias = 0
    matched_months = 0

    for fd in forecast_data:
        month_key = fd.get("month_key", "")
        predicted = fd.get("predicted_revenue", 0)
        actual = actuals_map.get(month_key, None)

        entry = {
            "month_key": month_key,
            "predicted": round(predicted, 2),
            "actual": round(actual, 2) if actual is not None else None,
        }

        if actual is not None and actual > 0:
            error = abs(predicted - actual)
            pct_error = (error / actual) * 100
            bias = ((predicted - actual) / actual) * 100
            entry["error"] = round(error, 2)
            entry["mape"] = round(pct_error, 2)
            entry["bias"] = round(bias, 2)
            entry["accuracy"] = round(max(0, 100 - pct_error), 2)

            total_abs_error += error
            total_actual += actual
            total_bias += (predicted - actual)
            matched_months += 1
        else:
            entry["error"] = None
            entry["mape"] = None
            entry["bias"] = None
            entry["accuracy"] = None

        monthly_comparison.append(entry)

    # Overall metrics
    overall_mape = round((total_abs_error / total_actual * 100), 2) if total_actual > 0 else None
    overall_accuracy = round(100 - overall_mape, 2) if overall_mape is not None else None
    overall_bias = round((total_bias / total_actual * 100), 2) if total_actual > 0 else None

    # Category-level accuracy (from snapshots with matching actuals)
    # For categories that have both forecasts and actual data
    category_accuracy = []
    for cat, snap in latest_by_cat.items():
        if cat == "All":
            continue
        cat_data = snap.get("forecast_data", [])
        cat_abs_error = 0
        cat_actual = 0
        cat_months = 0
        for fd in cat_data:
            mk = fd.get("month_key", "")
            predicted = fd.get("predicted_revenue", 0)
            actual = actuals_map.get(mk)
            if actual and actual > 0:
                cat_abs_error += abs(predicted - actual)
                cat_actual += actual
                cat_months += 1
        if cat_actual > 0:
            cat_mape = (cat_abs_error / cat_actual) * 100
            category_accuracy.append({
                "category": cat,
                "mape": round(cat_mape, 2),
                "accuracy": round(max(0, 100 - cat_mape), 2),
                "months_compared": cat_months,
            })

    return {
        "overall": {
            "mape": overall_mape,
            "accuracy": overall_accuracy,
            "bias": overall_bias,
            "months_compared": matched_months,
            "confidence_score": all_forecast.get("confidence_score"),
        },
        "monthly_comparison": monthly_comparison,
        "category_accuracy": category_accuracy,
        "forecast_count": len(snapshots),
        "actual_months": len(actuals_map),
        "last_forecast_date": all_forecast.get("created_at"),
    }
