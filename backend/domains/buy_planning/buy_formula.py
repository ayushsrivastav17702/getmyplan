"""
Buy-Formula domain module — the final composition layer.

This is the orchestrator that combines every other domain in this package to
answer one question: "given our stores, inventory, sales history and rules,
how many units should we buy for each SKU?"

Endpoints owned:
  POST /buy-formula/calculate     run the full formula + return full buy plan

Composition graph:
  attribution.eligible_wedges_for_mix  ← which wedges a mix can ship to
  safety_stock.*                       ← z-score, MAD-based safety
  sell_through.SellThroughRepository   ← tenant-tunable sell-through multipliers
  display_minimums                     ← category × wedge minimum facings
  exclusions                           ← SKUs deliberately kept out of plans
  promotions                           ← active lift factors

The canonical formula (preserved from legacy monolith + also present in
core/buy_formula.py as a pinned reference):

    buy_qty = MAX(
        (sell_through_target × forecasted_demand) - current_SOH,
        display_minimum_units × eligible_store_count,
        safety_stock_units
    )

  where `forecasted_demand = daily_ROS × cover_days × max_active_promo_lift`.

Binding factor = which of the three components drove the max.
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from .attribution import eligible_wedges_for_mix
from .safety_stock import Z_SCORES, DEFAULT_SAFETY_CONFIG
from .sell_through import DEFAULT_SELL_THROUGH, SellThroughRepository


# ═════════════════════════════════════════════════════════════════
# 1. Pure helpers — no I/O.
# ═════════════════════════════════════════════════════════════════

def compute_promo_lifts(active_promos: List[dict]) -> dict:
    """
    Flatten the list of active promos into a fast lookup dict:
      {"cat:<category>": max_lift, "sku:<sku>": max_lift}
    Taking MAX when multiple active promos overlap.
    """
    lifts: dict = {}
    for promo in active_promos:
        lf = promo.get("lift_factor", 1.0)
        for cat in promo.get("affected_categories", []) or []:
            lifts[f"cat:{cat}"] = max(lifts.get(f"cat:{cat}", 1.0), lf)
        for sku in promo.get("affected_skus", []) or []:
            lifts[f"sku:{sku}"] = max(lifts.get(f"sku:{sku}", 1.0), lf)
    return lifts


def best_lift_for(sku: str, category: str, promo_lifts: dict) -> float:
    """SKU-level lift beats category-level, but we take the max across both."""
    return max(
        promo_lifts.get(f"sku:{sku}", 1.0),
        promo_lifts.get(f"cat:{category}", 1.0),
    )


def compute_demand_buy(*, daily_ros: float, cover_days: int, lift: float,
                        sell_through_target: float, current_soh: int) -> tuple:
    """Return (forecasted_demand, demand_buy). Never negative."""
    forecasted = daily_ros * cover_days * lift
    demand_buy = max(0, (sell_through_target * forecasted) - current_soh)
    return forecasted, demand_buy


def compute_display_qty(*, mix: str, category: str,
                         disp_mins: dict, wedge_counts: dict) -> float:
    """Sum (display_min × store_count) across each eligible wedge."""
    total = 0.0
    for w in eligible_wedges_for_mix(mix):
        dm = disp_mins.get((category, w), disp_mins.get(("ALL", w), 4))
        total += dm * wedge_counts.get(w, 0)
    return total


def compute_safety_qty_statistical(*, daily_ros: float, safety_cfg: dict,
                                    lead_time_days: int = 14) -> float:
    """Classical z × MAD × sqrt(LT/RP), capped by max_safety_weeks × MAD."""
    z = Z_SCORES.get(safety_cfg.get("service_level", 0.95), 1.645)
    rp = safety_cfg.get("review_period_days", 7)
    max_weeks = safety_cfg.get("max_safety_weeks", 12)
    mad = daily_ros * 0.3 if daily_ros > 0 else 0.5
    raw = z * mad * math.sqrt(lead_time_days / max(rp, 1))
    return min(raw, max_weeks * mad)


def binding_factor(*, demand_buy: float, display_qty: float, safety_qty: float) -> str:
    """Which component drove the final buy_qty (the MAX)?"""
    if demand_buy >= max(display_qty, safety_qty):
        return "demand"
    if display_qty >= safety_qty:
        return "display_min"
    return "safety_stock"


def build_sku_row(*, sku: str, meta: dict, inputs: dict, cover_days: int,
                   sell_targets: dict, safety_cfg: dict) -> Optional[dict]:
    """
    Build one buy_plan row. Returns None if SKU is excluded
    (caller increments `excluded_skus` counter in that case).
    """
    if sku in inputs["excluded_skus"]:
        return None

    mix = meta["style_mix"]
    category = meta["category"]
    ros_data = inputs["ros_map"].get(sku, {"total_qty": 0, "daily_ros": 0, "revenue": 0})
    current_soh = inputs["soh_map"].get(sku, 0)

    daily_ros = ros_data["daily_ros"]
    lift = best_lift_for(sku, category, inputs["promo_lifts"])
    forecasted_demand, demand_buy = compute_demand_buy(
        daily_ros=daily_ros, cover_days=cover_days, lift=lift,
        sell_through_target=sell_targets.get(mix, 0.8),
        current_soh=current_soh,
    )
    display_qty = compute_display_qty(
        mix=mix, category=category,
        disp_mins=inputs["disp_mins"], wedge_counts=inputs["wedge_counts"],
    )
    safety_qty = compute_safety_qty_statistical(daily_ros=daily_ros, safety_cfg=safety_cfg)
    buy_qty = round(max(demand_buy, display_qty, safety_qty))
    bf = binding_factor(
        demand_buy=demand_buy, display_qty=display_qty, safety_qty=safety_qty,
    )
    buy_value = buy_qty * meta.get("mrp", 0)

    return {
        "sku": sku,
        "style": meta["style"],
        "category": category,
        "sub_category": meta["sub_category"],
        "style_mix": mix,
        "daily_ros": round(daily_ros, 2),
        "forecasted_demand": round(forecasted_demand),
        "sell_through_target": sell_targets.get(mix, 0.8),
        "demand_buy": round(demand_buy),
        "display_minimum": round(display_qty),
        "safety_stock": round(safety_qty),
        "safety_method": "statistical",
        "promo_lift": lift,
        "current_soh": current_soh,
        "buy_qty": buy_qty,
        "buy_value": round(buy_value, 2),
        "mrp": meta["mrp"],
        "binding_factor": bf,
        "binding_constraint": bf,  # legacy alias — do not remove
    }


# ═════════════════════════════════════════════════════════════════
# 2. Repository — pure Mongo.
# ═════════════════════════════════════════════════════════════════

def _tenant_match(tenant_id: str) -> dict:
    return {"$or": [{"tenant_id": tenant_id}, {"tenant_id": {"$exists": False}}]}


class BuyFormulaRepository:
    def __init__(self, db):
        self._db = db

    async def aggregate_wedge_counts(self, tenant_id: str) -> Dict[str, int]:
        counts = {"A": 0, "B": 0, "C": 0}
        async for doc in self._db.store_master.aggregate([
            {"$match": _tenant_match(tenant_id)},
            {"$group": {"_id": "$wedge_class", "count": {"$sum": 1}}},
        ]):
            if doc["_id"] in counts:
                counts[doc["_id"]] = doc["count"]
        return counts

    async def load_display_minimums(self) -> dict:
        out: dict = {}
        async for doc in self._db.display_minimums_config.find({}, {"_id": 0}):
            out[(doc["category"], doc["store_wedge"])] = doc.get("total_display_min_units", 4)
        return out

    async def aggregate_soh(self, tenant_id: str) -> dict:
        out: dict = {}
        async for doc in self._db.store_inventory.aggregate([
            {"$match": _tenant_match(tenant_id)},
            {"$group": {
                "_id": "$sku",
                "total_soh": {"$sum": {"$toInt": {"$ifNull": ["$closing_stock", 0]}}},
            }},
        ]):
            out[doc["_id"]] = doc["total_soh"]
        return out

    async def aggregate_ros(self, tenant_id: str, cover_days: int) -> dict:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=cover_days)).strftime("%Y-%m-%d")
        out: dict = {}
        async for doc in self._db.daily_sales.aggregate([
            {"$match": {**_tenant_match(tenant_id), "day": {"$gte": cutoff}}},
            {"$group": {
                "_id": "$sku",
                "total_qty": {"$sum": {"$toInt": {"$ifNull": ["$quantity", 0]}}},
                "total_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$revenue", 0]}}},
                "days": {"$addToSet": "$day"},
            }},
        ]):
            days = len(doc.get("days", []))
            out[doc["_id"]] = {
                "total_qty": doc["total_qty"],
                "daily_ros": doc["total_qty"] / max(days, 1),
                "revenue": doc["total_revenue"],
            }
        return out

    async def load_sku_meta(self, tenant_id: str) -> dict:
        out: dict = {}
        async for doc in self._db.sku_ean_master.find(_tenant_match(tenant_id), {"_id": 0}):
            out[doc.get("ean", "")] = {
                "style": doc.get("style", ""),
                "category": doc.get("category", ""),
                "sub_category": doc.get("sub_category", ""),
                "style_mix": doc.get("style_mix", "Test"),
                "mrp": doc.get("mrp", 0),
                "flow_rank": doc.get("flow_rank"),
                "lifecycle_stage": doc.get("lifecycle_stage", ""),
                "launch_date": doc.get("launch_date", ""),
            }
        return out

    async def load_excluded_skus(self, tenant_id: str) -> set:
        out: set = set()
        async for doc in self._db.buy_planning_exclusions.find(
            {"tenant_id": tenant_id}, {"_id": 0, "sku": 1},
        ):
            out.add(doc.get("sku"))
        return out

    async def load_active_promos(self, tenant_id: str) -> list:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        out: list = []
        async for doc in self._db.promotions.find({
            "tenant_id": tenant_id, "status": "active",
            "start_date": {"$lte": today}, "end_date": {"$gte": today},
        }, {"_id": 0, "affected_categories": 1, "affected_skus": 1, "lift_factor": 1}):
            out.append(doc)
        return out

    async def load_safety_cfg(self, tenant_id: str) -> dict:
        doc = await self._db.safety_stock_config.find_one({"tenant_id": tenant_id}, {"_id": 0})
        return doc or dict(DEFAULT_SAFETY_CONFIG)


# ═════════════════════════════════════════════════════════════════
# 3. Service — orchestration.
# ═════════════════════════════════════════════════════════════════

class BuyFormulaService:
    def __init__(self, repo: BuyFormulaRepository):
        self._repo = repo

    async def calculate(
        self, *, tenant_id: str, cover_days: int = 30, safety_days: int = 7,
        sell_through_targets: Optional[dict] = None,
    ) -> dict:
        """Compose every input and run the full formula across all SKUs."""
        # 1. Gather ALL inputs in parallel-friendly order (each is a single
        #    Mongo round-trip). Motor handles I/O concurrency at the driver.
        wedge_counts = await self._repo.aggregate_wedge_counts(tenant_id)
        disp_mins = await self._repo.load_display_minimums()
        soh_map = await self._repo.aggregate_soh(tenant_id)
        ros_map = await self._repo.aggregate_ros(tenant_id, cover_days)
        sku_meta = await self._repo.load_sku_meta(tenant_id)
        excluded_skus = await self._repo.load_excluded_skus(tenant_id)
        active_promos = await self._repo.load_active_promos(tenant_id)
        safety_cfg = await self._repo.load_safety_cfg(tenant_id)

        # Sell-through: explicit request body override > tenant-stored config > system default
        if sell_through_targets:
            sell_targets = sell_through_targets
        else:
            sell_targets = await SellThroughRepository(self._repo._db).get_targets()
        promo_lifts = compute_promo_lifts(active_promos)

        inputs = {
            "wedge_counts": wedge_counts,
            "disp_mins": disp_mins,
            "soh_map": soh_map,
            "ros_map": ros_map,
            "excluded_skus": excluded_skus,
            "promo_lifts": promo_lifts,
        }

        buy_plan: list = []
        totals = {
            "total_buy_qty": 0, "total_buy_value": 0,
            "total_display_qty": 0, "total_safety_qty": 0,
            "excluded_skus": 0,
        }

        for sku, meta in sku_meta.items():
            row = build_sku_row(
                sku=sku, meta=meta, inputs=inputs,
                cover_days=cover_days, sell_targets=sell_targets,
                safety_cfg=safety_cfg,
            )
            if row is None:
                totals["excluded_skus"] += 1
                continue
            totals["total_buy_qty"] += row["buy_qty"]
            totals["total_buy_value"] += row["buy_value"]
            totals["total_display_qty"] += row["display_minimum"]
            totals["total_safety_qty"] += row["safety_stock"]
            buy_plan.append(row)

        buy_plan.sort(key=lambda x: x["buy_value"], reverse=True)
        return {
            "success": True,
            "parameters": {
                "cover_days": cover_days,
                "safety_days": safety_days,
                "sell_through_targets": sell_targets,
                "store_counts": wedge_counts,
            },
            "totals": {k: round(v, 2) for k, v in totals.items()},
            "sku_count": len(buy_plan),
            "buy_plan": buy_plan,
        }

    def to_csv_rows(self, calc_result: dict, sku_meta: dict) -> List[dict]:
        """
        Convert a /buy-formula/calculate result into flattened CSV row dicts.
        Enriches with DNA fields from sku_meta (flow_rank, lifecycle, launch_date)
        that aren't in the regular response.
        """
        rows = []
        for r in calc_result.get("buy_plan", []):
            meta = sku_meta.get(r["sku"], {})
            rows.append({
                "SKU": r["sku"], "Style": r["style"], "Category": r["category"],
                "Sub Category": r["sub_category"], "Style Mix": r["style_mix"],
                "MRP": r["mrp"], "Daily ROS": r["daily_ros"],
                "Current SOH": r["current_soh"],
                "Forecasted Demand": r["forecasted_demand"],
                "Sell-Through Target": r["sell_through_target"],
                "Demand Buy": r["demand_buy"],
                "Display Minimum": r["display_minimum"],
                "Safety Stock": r["safety_stock"],
                "Buy Qty": r["buy_qty"], "Buy Value": r["buy_value"],
                "Binding Factor": r["binding_factor"],
                "Binding Constraint": r["binding_constraint"],
                "Flow Rank": meta.get("flow_rank"),
                "Lifecycle": meta.get("lifecycle_stage", ""),
                "Launch Date": meta.get("launch_date", ""),
            })
        return rows
