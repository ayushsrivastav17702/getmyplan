"""
Reporting APIs: Planner Performance, Category Health, ROI Dashboard.
"""
from fastapi import APIRouter, Depends, Request
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Dict
import logging

router = APIRouter(prefix="/reports", tags=["reports"])

_db_func = None
_get_current_user = None

logger = logging.getLogger(__name__)


def init_reports(get_db_func, get_current_user_func):
    global _db_func, _get_current_user
    _db_func = get_db_func
    _get_current_user = get_current_user_func


async def _dep_user(request: Request) -> dict:
    return await _get_current_user(request)


def _tmatch(tenant_id: str) -> dict:
    return {"$or": [{"tenant_id": tenant_id}, {"tenant_id": {"$exists": False}}]}


# ──────────────────────────────────────────────
#  PLANNER PERFORMANCE LEADERBOARD
# ──────────────────────────────────────────────

@router.get("/planner-performance")
async def planner_performance(user: dict = Depends(_dep_user)):
    """Planner leaderboard based on buy plan activity and approval rates."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")

    # Get all buy plans
    plans = await db.buy_plans.find(
        _tmatch(tenant_id),
        {"_id": 0, "generated_by": 1, "status": 1, "totals": 1,
         "sku_count": 1, "generated_at": 1, "approved_at": 1}
    ).to_list(500)

    # Get approval audit entries
    audits = await db.buy_planning_approval_audit.find(
        _tmatch(tenant_id),
        {"_id": 0, "performed_by": 1, "action": 1, "role": 1, "performed_at": 1}
    ).to_list(1000)

    # Aggregate per planner
    planner_stats = {}
    for p in plans:
        email = p.get("generated_by") or "system"
        if email not in planner_stats:
            planner_stats[email] = {
                "email": email,
                "plans_created": 0,
                "plans_approved": 0,
                "plans_rejected": 0,
                "total_units": 0,
                "total_value": 0,
            }
        s = planner_stats[email]
        s["plans_created"] += 1
        totals = p.get("totals", {})
        s["total_units"] += totals.get("total_units", 0)
        s["total_value"] += totals.get("total_value", 0)
        status = p.get("status", "")
        if status in ("ordered", "approved", "head_approved"):
            s["plans_approved"] += 1
        elif status == "rejected":
            s["plans_rejected"] += 1

    # Approval actions per user
    for a in audits:
        email = a.get("performed_by", "")
        if email not in planner_stats:
            planner_stats[email] = {
                "email": email,
                "plans_created": 0,
                "plans_approved": 0,
                "plans_rejected": 0,
                "total_units": 0,
                "total_value": 0,
            }
        act = a.get("action", "")
        if "approve" in act:
            planner_stats[email]["approvals_given"] = planner_stats[email].get("approvals_given", 0) + 1
        elif act in ("reject", "rejected"):
            planner_stats[email]["rejections_given"] = planner_stats[email].get("rejections_given", 0) + 1

    # Build leaderboard sorted by plans_approved desc, then plans_created desc
    leaderboard = sorted(
        planner_stats.values(),
        key=lambda x: (x["plans_approved"], x["plans_created"], x["total_value"]),
        reverse=True,
    )

    # Add rank and approval rate
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1
        created = entry["plans_created"]
        entry["approval_rate"] = round(
            (entry["plans_approved"] / created * 100) if created > 0 else 0, 1
        )

    return {
        "leaderboard": leaderboard,
        "total_plans": len(plans),
        "total_planners": len(leaderboard),
    }


# ──────────────────────────────────────────────
#  CATEGORY HEALTH SCORECARD
# ──────────────────────────────────────────────

@router.get("/category-health")
async def category_health(user: dict = Depends(_dep_user)):
    """Category-level health metrics: stock health, fill rate, topseller availability, DOH.

    ## Definitions (SOH-driven, not plan-driven)
      - `stock_health`   = pct of SKUs in the category with SOH > 0
      - `fill_rate`      = units_in_stock / (units_in_stock + units_lost_to_stockouts)
                           simplified: pct of SKU-stores with SOH > 0
      - `topseller_availability` = pct of top-20% revenue SKUs that have SOH > 0
      - `doh`            = total_soh / daily_sales_rate (days of supply)

    ## Field-name note
    The canonical inventory quantity field in `store_inventory` is `closing_stock`
    (NOT `soh`). See `mongo_aggregations.py` L597 and the Transfer Optimizer
    repository for the same convention. A prior version of this route aggregated
    `$soh` and always got 0, which — combined with the active/total bug below —
    made every KPI show 100%.
    """
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    tmatch = _tmatch(tenant_id)

    # 1. Style catalogue → category mapping
    styles = await db.style_master.find(
        tmatch, {"_id": 0, "style_code": 1, "category": 1},
    ).to_list(500)
    style_cat_map = {s["style_code"]: s.get("category") or "Other" for s in styles}

    # 2. Full SKU list from sku_master, with style→category back-reference
    skus = await db.sku_master.find(
        tmatch, {"_id": 0, "sku": 1, "style": 1},
    ).to_list(5000)

    # Fallback: if sku_master is empty, derive from distinct inventory rows
    if not skus:
        async for doc in db.store_inventory.aggregate([
            {"$match": tmatch},
            {"$group": {"_id": "$sku", "style": {"$first": "$style"}}},
        ]):
            skus.append({"sku": doc["_id"], "style": doc.get("style")})

    sku_cat_map: Dict[str, str] = {
        s["sku"]: style_cat_map.get(s.get("style"), "Other") for s in skus
    }

    # 3. Latest SOH per SKU-store (canonical field: closing_stock)
    inv_pipeline = [
        {"$match": tmatch},
        {"$sort": {"uploaded_at": -1}},
        {"$group": {
            "_id": {"sku": "$sku", "store": "$store_code"},
            "soh": {"$first": {"$toInt": {"$ifNull": ["$closing_stock", 0]}}},
        }},
    ]
    soh_rows = await db.store_inventory.aggregate(inv_pipeline).to_list(None)
    # Roll SOH up to SKU level and count in-stock SKU-stores for fill-rate
    sku_soh: Dict[str, int] = defaultdict(int)
    sku_store_total: Dict[str, int] = defaultdict(int)
    sku_store_instock: Dict[str, int] = defaultdict(int)
    for row in soh_rows:
        sku = row["_id"]["sku"]
        qty = row.get("soh") or 0
        sku_soh[sku] += qty
        sku_store_total[sku] += 1
        if qty > 0:
            sku_store_instock[sku] += 1

    # 4. 30-day sales per SKU → revenue, units, and top-20% flag
    cutoff_30d = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    sales_pipeline = [
        {"$match": {**tmatch, "day": {"$gte": cutoff_30d}}},
        {"$group": {
            "_id": "$sku",
            "revenue": {"$sum": {"$toDouble": {"$ifNull": ["$revenue", 0]}}},
            "units": {"$sum": {"$toInt": {"$ifNull": ["$quantity", 0]}}},
        }},
    ]
    sku_sales = {doc["_id"]: doc async for doc in db.daily_sales.aggregate(sales_pipeline)}

    # Top-20% revenue SKUs = "topsellers"
    revenues = sorted((s.get("revenue", 0) for s in sku_sales.values()), reverse=True)
    topseller_threshold = revenues[max(0, len(revenues) // 5 - 1)] if revenues else 0
    topseller_skus = {
        sku for sku, s in sku_sales.items()
        if s.get("revenue", 0) >= topseller_threshold and topseller_threshold > 0
    }

    # 5. Bucket everything per category
    categories = sorted({c for c in sku_cat_map.values() if c})
    if not categories:
        categories = ["Apparel", "Footwear", "Accessories"]

    results = []
    for cat in categories:
        cat_skus = [s for s, c in sku_cat_map.items() if c == cat]
        if not cat_skus:
            continue

        total_skus = len(cat_skus)
        in_stock_skus = sum(1 for s in cat_skus if sku_soh.get(s, 0) > 0)
        total_store_cells = sum(sku_store_total.get(s, 0) for s in cat_skus)
        instock_store_cells = sum(sku_store_instock.get(s, 0) for s in cat_skus)
        total_soh = sum(sku_soh.get(s, 0) for s in cat_skus)
        revenue_30d = sum(sku_sales.get(s, {}).get("revenue", 0) for s in cat_skus)
        qty_30d = sum(sku_sales.get(s, {}).get("units", 0) for s in cat_skus)

        cat_topsellers = [s for s in cat_skus if s in topseller_skus]
        top_in_stock = sum(1 for s in cat_topsellers if sku_soh.get(s, 0) > 0)

        # KPIs — every one is SOH-driven; when SOH=0 anywhere, the metric is 0
        stock_health = round(in_stock_skus / total_skus * 100, 1) if total_skus else 0.0
        fill_rate = (
            round(instock_store_cells / total_store_cells * 100, 1)
            if total_store_cells else 0.0
        )
        topseller_availability = (
            round(top_in_stock / len(cat_topsellers) * 100, 1)
            if cat_topsellers else 0.0
        )
        daily_rate = qty_30d / 30 if qty_30d else 0
        doh = round(total_soh / daily_rate) if daily_rate > 0 else 0

        results.append({
            "category": cat,
            "total_skus": total_skus,
            "in_stock_skus": in_stock_skus,
            "stock_health": stock_health,
            "fill_rate": fill_rate,
            "topseller_availability": topseller_availability,
            "topseller_count": len(cat_topsellers),
            "doh": doh,
            "revenue_30d": round(revenue_30d, 2),
            "qty_30d": qty_30d,
            "soh": total_soh,
        })

    results.sort(key=lambda x: x["revenue_30d"], reverse=True)
    return {"categories": results, "period": "last_30_days"}


# ──────────────────────────────────────────────
#  ROI DASHBOARD
# ──────────────────────────────────────────────

@router.get("/roi")
async def roi_dashboard(user: dict = Depends(_dep_user)):
    """System ROI metrics: plan efficiency, stockout reduction estimates, time savings."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    tmatch = _tmatch(tenant_id)

    # Buy plan stats
    plans = await db.buy_plans.find(
        tmatch, {"_id": 0, "status": 1, "totals": 1, "generated_at": 1, "sku_count": 1}
    ).to_list(500)

    total_plans = len(plans)
    approved_plans = sum(1 for p in plans if p.get("status") in ("ordered", "approved", "head_approved", "senior_approved", "category_approved"))
    rejected_plans = sum(1 for p in plans if p.get("status") == "rejected")
    total_plan_value = sum(p.get("totals", {}).get("total_value", 0) for p in plans)
    total_plan_units = sum(p.get("totals", {}).get("total_units", 0) for p in plans)

    # Monthly revenue trend (last 6 months)
    six_months_ago = (datetime.now(timezone.utc) - timedelta(days=180)).strftime("%Y-%m-%d")
    revenue_pipeline = [
        {"$match": {**tmatch, "day": {"$gte": six_months_ago}}},
        {"$addFields": {"month_key": {"$substr": ["$day", 0, 7]}}},
        {"$group": {
            "_id": "$month_key",
            "revenue": {"$sum": {"$toDouble": {"$ifNull": ["$revenue", 0]}}},
            "qty": {"$sum": {"$toInt": {"$ifNull": ["$quantity", 0]}}},
            "transactions": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    monthly_revenue = await db.daily_sales.aggregate(revenue_pipeline).to_list(12)

    # Inventory stats — use estimated counts (instant)
    inv_count = await db.store_inventory.estimated_document_count()
    total_stores = await db.store_master.estimated_document_count()
    total_skus = await db.sku_ean_master.estimated_document_count()

    # Approval efficiency (avg time from draft to approved)
    approval_audits = await db.buy_planning_approval_audit.find(
        tmatch, {"_id": 0, "plan_id": 1, "action": 1, "performed_at": 1}
    ).to_list(500)

    # Estimated KPIs
    plan_approval_rate = round((approved_plans / total_plans * 100) if total_plans > 0 else 0, 1)
    avg_skus_per_plan = round(sum(p.get("sku_count", 0) for p in plans) / total_plans) if total_plans > 0 else 0

    # Time saved estimate: assume 2 hrs manual per plan vs 5 min automated
    time_saved_hrs = round(total_plans * 1.92, 1)  # ~1.92 hrs saved per plan

    return {
        "kpis": {
            "total_plans": total_plans,
            "approved_plans": approved_plans,
            "rejected_plans": rejected_plans,
            "plan_approval_rate": plan_approval_rate,
            "total_plan_value": round(total_plan_value, 2),
            "total_plan_units": total_plan_units,
            "avg_skus_per_plan": avg_skus_per_plan,
            "time_saved_hrs": time_saved_hrs,
            "inventory_records": inv_count,
            "total_stores": total_stores,
            "total_skus": total_skus,
        },
        "monthly_revenue": [
            {
                "month": m["_id"],
                "revenue": round(m["revenue"], 2),
                "qty": m["qty"],
                "transactions": m["transactions"],
            }
            for m in monthly_revenue
        ],
        "approval_activity": len(approval_audits),
    }
