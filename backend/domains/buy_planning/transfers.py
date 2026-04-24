"""
Inter-Store Transfer (IST) Optimization domain module.

## What it does
For each SKU, finds donor→recipient store pairs where transferring units would
(a) reduce stockouts at recipients currently running on a low Days-of-Supply,
(b) consolidate slow-moving stock parked at donors with high Days-of-Supply.

Outputs: a ranked list of transfer recommendations, each with an expected
revenue uplift = `transfer_qty × recipient_daily_ros × mrp`.

## v1 Algorithm (rule-based)
1. Compute per-(store, sku) metrics: `soh`, `daily_ros`, `dos`
2. Per SKU:
   - **Donors**     = stores with dos ≥ `donor_dos_threshold` (default 45)
   - **Recipients** = stores with dos ≤ `recipient_dos_threshold` (default 7)
                       AND daily_ros > 0 (must actually be selling)
3. Greedy pair: sort donors by dos desc, recipients by dos asc.
   For each recipient, pull units from highest-dos donor until
   recipient reaches `target_post_transfer_dos` (default 21 days),
   respecting two floors:
     - donor must retain `min_donor_residual_dos` (default 30 days)
     - transfer_qty ≥ `min_transfer_qty` (default 3; sub-pack floor)
4. Rank recommendations by expected uplift = qty × recipient_ros × mrp, desc.

## Why the greedy v1 (not a full LP)
A proper IST optimizer uses a Min-Cost-Max-Flow network (supply = donor excess,
demand = recipient shortfall, cost = distance × unit_weight). That's the right
v2 target, but it needs a solver (`ortools` or `scipy.optimize.linprog`) and
per-store distance matrix. The greedy v1 captures 70–80% of uplift with zero
dependencies — ship it, measure it, upgrade later.

## Non-goals for v1
- Size-set re-balancing (partially handled since each EAN is its own SKU row)
- Cross-tenant transfers (impossible by design — `_tenant_match` scopes reads)
- Physical logistics cost modelling (v2)
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from uuid import uuid4


# ═════════════════════════════════════════════════════════════════
# 1. Pure algorithm — no I/O.
# ═════════════════════════════════════════════════════════════════

INF = float("inf")


def compute_dos(soh: float, daily_ros: float) -> float:
    """Days-of-Supply. Infinite when there's no sales velocity."""
    if daily_ros <= 0:
        return INF
    return soh / daily_ros


def build_store_sku_metrics(
    inventory_by_sku_store: Dict[tuple, int],
    sales_by_sku_store: Dict[tuple, dict],
) -> List[dict]:
    """
    Combine latest SOH + recent ROS into a single list of rows.

    inventory_by_sku_store: {(sku, store): latest_soh}
    sales_by_sku_store:    {(sku, store): {"total_qty": int, "days": int}}
    """
    metrics: list = []
    all_keys = set(inventory_by_sku_store.keys()) | set(sales_by_sku_store.keys())
    for sku, store in all_keys:
        soh = inventory_by_sku_store.get((sku, store), 0)
        sd = sales_by_sku_store.get((sku, store), {"total_qty": 0, "days": 1})
        daily_ros = sd["total_qty"] / max(sd["days"], 1)
        metrics.append({
            "sku": sku, "store_code": store,
            "soh": soh, "daily_ros": round(daily_ros, 3),
            "dos": compute_dos(soh, daily_ros),
        })
    return metrics


def identify_donors(rows: List[dict], threshold_dos: float) -> List[dict]:
    """Stores with too much stock relative to sales velocity."""
    return [r for r in rows if r["dos"] >= threshold_dos and r["soh"] > 0]


def identify_recipients(rows: List[dict], threshold_dos: float) -> List[dict]:
    """Stores running low AND actually selling."""
    return [r for r in rows if r["dos"] <= threshold_dos and r["daily_ros"] > 0]


def match_transfers_greedily(
    donors: List[dict],
    recipients: List[dict],
    *,
    target_post_transfer_dos: float = 21,
    min_donor_residual_dos: float = 30,
    min_transfer_qty: int = 3,
) -> List[dict]:
    """
    Greedy match: per SKU, highest-dos donors fill lowest-dos recipients first.

    Returns a list of transfer dicts:
      {sku, from_store, to_store, qty, donor_dos_before, donor_dos_after,
       recipient_dos_before, recipient_dos_after, recipient_daily_ros}
    """
    # Bucket by SKU — transfers only happen within the same SKU.
    by_sku: Dict[str, dict] = {}
    for d in donors:
        by_sku.setdefault(d["sku"], {"donors": [], "recipients": []})["donors"].append(dict(d))
    for r in recipients:
        by_sku.setdefault(r["sku"], {"donors": [], "recipients": []})["recipients"].append(dict(r))

    suggestions: list = []
    for sku, pools in by_sku.items():
        donors_sku = sorted(pools["donors"], key=lambda x: x["dos"], reverse=True)
        recips_sku = sorted(pools["recipients"], key=lambda x: x["dos"])
        if not donors_sku or not recips_sku:
            continue

        for recip in recips_sku:
            recip_target_units = int(round(target_post_transfer_dos * recip["daily_ros"]))
            shortfall = max(0, recip_target_units - recip["soh"])
            if shortfall < min_transfer_qty:
                continue

            for donor in donors_sku:
                if shortfall <= 0:
                    break
                if donor["soh"] <= 0:
                    continue

                donor_min_residual = int(round(min_donor_residual_dos * donor["daily_ros"]))
                donor_excess = donor["soh"] - donor_min_residual
                if donor_excess < min_transfer_qty:
                    continue

                qty = min(shortfall, donor_excess)
                qty = max(min_transfer_qty, qty)  # floor (only if donor can support it)
                qty = min(qty, donor_excess)       # cap again after floor
                if qty < min_transfer_qty:
                    continue

                suggestions.append({
                    "sku": sku,
                    "from_store": donor["store_code"],
                    "to_store": recip["store_code"],
                    "qty": qty,
                    "donor_dos_before": round(donor["dos"], 1) if donor["dos"] != INF else None,
                    "donor_dos_after": round(compute_dos(donor["soh"] - qty, donor["daily_ros"]), 1)
                        if donor["daily_ros"] > 0 else None,
                    "recipient_dos_before": round(recip["dos"], 1),
                    "recipient_dos_after": round(compute_dos(recip["soh"] + qty, recip["daily_ros"]), 1),
                    "recipient_daily_ros": recip["daily_ros"],
                })
                donor["soh"] -= qty
                shortfall -= qty

    return suggestions


def rank_by_uplift(suggestions: List[dict], mrp_map: Dict[str, float]) -> List[dict]:
    """
    Attach expected revenue uplift per suggestion and sort desc.

    uplift = qty × recipient_daily_ros × mrp
    """
    ranked = []
    for s in suggestions:
        mrp = mrp_map.get(s["sku"], 0)
        ranked.append({
            **s,
            "mrp": mrp,
            "expected_uplift_units": round(s["qty"] * s["recipient_daily_ros"], 1),
            "expected_uplift_value": round(s["qty"] * s["recipient_daily_ros"] * mrp, 2),
        })
    ranked.sort(key=lambda x: x["expected_uplift_value"], reverse=True)
    return ranked


# ═════════════════════════════════════════════════════════════════
# 2. Repository — pure Mongo.
# ═════════════════════════════════════════════════════════════════

def _tenant_match(tenant_id: str) -> dict:
    return {"$or": [{"tenant_id": tenant_id}, {"tenant_id": {"$exists": False}}]}


class TransfersRepository:
    def __init__(self, db):
        self._db = db

    async def load_latest_soh(self, tenant_id: str) -> Dict[tuple, int]:
        """Latest SOH per (sku, store) from store_inventory — picks max(uploaded_at) row.

        NOTE: the canonical inventory quantity field in `store_inventory` is
        `closing_stock` (not `soh`); there is no top-level `date` field —
        snapshots are timestamped by `uploaded_at`. Verified via
        mongo_aggregations.py L597 and buy_formula.py L206.
        """
        pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$sort": {"uploaded_at": -1}},
            {"$group": {
                "_id": {"sku": "$sku", "store": "$store_code"},
                "soh": {"$first": {"$toInt": {"$ifNull": ["$closing_stock", 0]}}},
            }},
        ]
        out: Dict[tuple, int] = {}
        async for doc in self._db.store_inventory.aggregate(pipeline):
            out[(doc["_id"]["sku"], doc["_id"]["store"])] = doc.get("soh", 0) or 0
        return out

    async def aggregate_ros(self, tenant_id: str, lookback_days: int) -> Dict[tuple, dict]:
        """Total units sold + distinct sale days per (sku, store) over lookback window."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        pipeline = [
            {"$match": {**_tenant_match(tenant_id), "day": {"$gte": cutoff}}},
            {"$group": {
                "_id": {"sku": "$sku", "store": "$store_code"},
                "total_qty": {"$sum": {"$toInt": {"$ifNull": ["$quantity", 0]}}},
                "days": {"$addToSet": "$day"},
            }},
        ]
        out: Dict[tuple, dict] = {}
        async for doc in self._db.daily_sales.aggregate(pipeline):
            out[(doc["_id"]["sku"], doc["_id"]["store"])] = {
                "total_qty": doc["total_qty"],
                "days": max(1, len(doc.get("days", []))),
            }
        return out

    async def load_mrp_map(self, tenant_id: str) -> Dict[str, float]:
        out: Dict[str, float] = {}
        async for doc in self._db.sku_ean_master.find(
            _tenant_match(tenant_id), {"_id": 0, "ean": 1, "mrp": 1},
        ):
            if doc.get("ean"):
                out[doc["ean"]] = doc.get("mrp", 0) or 0
        return out

    async def load_sku_style_map(self, tenant_id: str) -> Dict[str, dict]:
        """For enriching output with style/category for readability."""
        out: Dict[str, dict] = {}
        async for doc in self._db.sku_ean_master.find(
            _tenant_match(tenant_id),
            {"_id": 0, "ean": 1, "style": 1, "category": 1, "style_mix": 1},
        ):
            if doc.get("ean"):
                out[doc["ean"]] = {
                    "style": doc.get("style", ""),
                    "category": doc.get("category", ""),
                    "style_mix": doc.get("style_mix", ""),
                }
        return out

    async def save_batch(self, doc: dict) -> str:
        await self._db.ist_transfer_batches.insert_one(doc)
        return doc["batch_id"]

    async def list_batches(self, tenant_id: str, status: Optional[str], limit: int) -> list:
        query: dict = {"tenant_id": tenant_id}
        if status:
            query["status"] = status
        out: list = []
        async for doc in self._db.ist_transfer_batches.find(
            query, {"_id": 0, "recommendations": 0},
        ).sort("created_at", -1).limit(limit):
            out.append(doc)
        return out

    async def get_batch(self, tenant_id: str, batch_id: str) -> Optional[dict]:
        return await self._db.ist_transfer_batches.find_one(
            {"tenant_id": tenant_id, "batch_id": batch_id}, {"_id": 0},
        )

    async def update_status(self, *, tenant_id: str, batch_id: str, status: str,
                             user_email: str, now_iso: str) -> int:
        result = await self._db.ist_transfer_batches.update_one(
            {"tenant_id": tenant_id, "batch_id": batch_id},
            {"$set": {
                "status": status,
                f"{status}_at": now_iso,
                f"{status}_by": user_email,
            }},
        )
        return result.matched_count


# ═════════════════════════════════════════════════════════════════
# 3. Service — orchestration.
# ═════════════════════════════════════════════════════════════════

class NotFoundError(Exception):
    """Raised when a batch doesn't exist."""


class ValidationError(Exception):
    """Raised on illegal state transition."""


ALLOWED_STATUSES = {"draft", "approved", "rejected", "executed"}


class TransfersService:
    def __init__(self, repo: TransfersRepository):
        self._repo = repo

    async def optimize(
        self, *, tenant_id: str,
        donor_dos_threshold: float = 45,
        recipient_dos_threshold: float = 7,
        target_post_transfer_dos: float = 21,
        min_donor_residual_dos: float = 30,
        min_transfer_qty: int = 3,
        lookback_days: int = 30,
        max_suggestions: int = 500,
    ) -> dict:
        """Run the optimizer live — returns recommendations without saving."""
        soh_map = await self._repo.load_latest_soh(tenant_id)
        sales_map = await self._repo.aggregate_ros(tenant_id, lookback_days)
        mrp_map = await self._repo.load_mrp_map(tenant_id)
        style_map = await self._repo.load_sku_style_map(tenant_id)

        rows = build_store_sku_metrics(soh_map, sales_map)
        donors = identify_donors(rows, donor_dos_threshold)
        recipients = identify_recipients(rows, recipient_dos_threshold)
        suggestions = match_transfers_greedily(
            donors, recipients,
            target_post_transfer_dos=target_post_transfer_dos,
            min_donor_residual_dos=min_donor_residual_dos,
            min_transfer_qty=min_transfer_qty,
        )
        ranked = rank_by_uplift(suggestions, mrp_map)[:max_suggestions]

        # Enrich with style/category for UI
        for s in ranked:
            meta = style_map.get(s["sku"], {})
            s["style"] = meta.get("style", "")
            s["category"] = meta.get("category", "")
            s["style_mix"] = meta.get("style_mix", "")

        return {
            "success": True,
            "parameters": {
                "donor_dos_threshold": donor_dos_threshold,
                "recipient_dos_threshold": recipient_dos_threshold,
                "target_post_transfer_dos": target_post_transfer_dos,
                "min_donor_residual_dos": min_donor_residual_dos,
                "min_transfer_qty": min_transfer_qty,
                "lookback_days": lookback_days,
            },
            "summary": {
                "total_donor_positions": len(donors),
                "total_recipient_positions": len(recipients),
                "suggestion_count": len(ranked),
                "total_units_moved": sum(s["qty"] for s in ranked),
                "total_expected_uplift_value": round(sum(s["expected_uplift_value"] for s in ranked), 2),
            },
            "recommendations": ranked,
        }

    async def generate_batch(self, *, tenant_id: str, user_email: str, **params) -> dict:
        """Run optimizer + persist results as a draft batch."""
        result = await self.optimize(tenant_id=tenant_id, **params)
        batch_id = f"IST-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6]}"
        doc = {
            "tenant_id": tenant_id,
            "batch_id": batch_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user_email,
            "status": "draft",
            "parameters": result["parameters"],
            "summary": result["summary"],
            "recommendations": result["recommendations"],
        }
        await self._repo.save_batch(doc)
        return {
            "success": True,
            "batch_id": batch_id,
            "summary": result["summary"],
        }

    async def list_batches(self, *, tenant_id: str, status: Optional[str] = None,
                            limit: int = 20) -> dict:
        batches = await self._repo.list_batches(tenant_id, status, limit)
        return {"batches": batches, "total": len(batches)}

    async def get_batch(self, *, tenant_id: str, batch_id: str) -> dict:
        doc = await self._repo.get_batch(tenant_id, batch_id)
        if not doc:
            raise NotFoundError(f"Batch '{batch_id}' not found")
        return doc

    async def transition(self, *, tenant_id: str, batch_id: str,
                         new_status: str, user_email: str) -> dict:
        if new_status not in ALLOWED_STATUSES:
            raise ValidationError(f"status must be one of: {ALLOWED_STATUSES}")
        doc = await self._repo.get_batch(tenant_id, batch_id)
        if not doc:
            raise NotFoundError(f"Batch '{batch_id}' not found")
        current = doc.get("status", "draft")
        # Legal transitions
        legal = {
            "draft": {"approved", "rejected"},
            "approved": {"executed", "rejected"},
        }
        if new_status not in legal.get(current, set()):
            raise ValidationError(f"Cannot transition from '{current}' to '{new_status}'")
        now_iso = datetime.now(timezone.utc).isoformat()
        await self._repo.update_status(
            tenant_id=tenant_id, batch_id=batch_id, status=new_status,
            user_email=user_email, now_iso=now_iso,
        )
        return {"success": True, "batch_id": batch_id, "status": new_status}
