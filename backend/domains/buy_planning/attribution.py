"""
Attribution domain module.

Fourth vertical extracted from routes/buy_planning.py.

Scope:
  GET /attribution/matrix    SKU → Store cluster attribution (how many stores each style reaches)

Why this extraction matters:
The attribution rules (Core reaches A+B+C, Fashion reaches A+B, Test reaches A only)
were previously duplicated — once in `/attribution/matrix` and once inline as
`eligible_wedges` dict in `/buy-formula/calculate`. Both now share
`WEDGE_RULES` + `eligible_wedges_for_mix` as the single source of truth.

The business rule:
  Core    → ALL stores (A + B + C)
  Fashion → Top stores only (A + B)
  Test    → Flagship only (A)
"""

from typing import Dict, List, Literal

StyleMix = Literal["Core", "Fashion", "Test"]
Wedge = Literal["A", "B", "C"]


# ═════════════════════════════════════════════════════════════════
# 1. Canonical attribution rules — pure data, no I/O.
# ═════════════════════════════════════════════════════════════════

WEDGE_RULES: Dict[str, Dict[str, bool]] = {
    "Core":    {"A": True,  "B": True,  "C": True},
    "Fashion": {"A": True,  "B": True,  "C": False},
    "Test":    {"A": True,  "B": False, "C": False},
}


def eligible_wedges_for_mix(mix: str) -> List[str]:
    """
    Return the wedges a style with this mix can be shipped to.
    Unknown mix → Test rules (most conservative).
    """
    rules = WEDGE_RULES.get(mix, WEDGE_RULES["Test"])
    return [w for w in ("A", "B", "C") if rules.get(w)]


def compute_wedge_allocation(mix: str, wedge_counts: Dict[str, int]) -> dict:
    """
    Given a style mix and store counts per wedge, return per-wedge eligibility
    and the allocation percentage (store_share within eligible wedges).
    """
    rules = WEDGE_RULES.get(mix, WEDGE_RULES["Test"])
    eligible_stores = sum(wedge_counts.get(w, 0) for w in ("A", "B", "C") if rules.get(w))
    out: dict = {}
    for w in ("A", "B", "C"):
        if rules.get(w) and eligible_stores > 0:
            out[w] = {
                "eligible": True,
                "stores": wedge_counts.get(w, 0),
                "allocation_pct": round(wedge_counts.get(w, 0) / eligible_stores * 100, 1),
            }
        else:
            out[w] = {"eligible": False, "stores": 0, "allocation_pct": 0}
    return out


def build_attribution_row(
    style: str, mix: str, sku_count: int, wedge_counts: Dict[str, int],
) -> dict:
    """Assemble one row of the attribution matrix."""
    rules = WEDGE_RULES.get(mix, WEDGE_RULES["Test"])
    eligible_stores = sum(wedge_counts.get(w, 0) for w in ("A", "B", "C") if rules.get(w))
    total_stores = sum(wedge_counts.values())
    return {
        "style": style,
        "style_mix": mix,
        "sku_count": sku_count,
        "eligible_stores": eligible_stores,
        "total_stores": total_stores,
        "coverage_pct": round(eligible_stores / max(total_stores, 1) * 100, 1),
        "wedge_allocation": compute_wedge_allocation(mix, wedge_counts),
    }


# ═════════════════════════════════════════════════════════════════
# 2. Repository — pure Mongo.
# ═════════════════════════════════════════════════════════════════

def _tenant_match(tenant_id: str) -> dict:
    return {"$or": [{"tenant_id": tenant_id}, {"tenant_id": {"$exists": False}}]}


class AttributionRepository:
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

    async def aggregate_styles_with_mix(self, tenant_id: str) -> List[dict]:
        pipeline = [
            {"$match": {**_tenant_match(tenant_id), "style_mix": {"$exists": True}}},
            {"$group": {
                "_id": {"style": "$style", "mix": "$style_mix"},
                "sku_count": {"$sum": 1},
            }},
        ]
        out: list = []
        async for doc in self._db.sku_ean_master.aggregate(pipeline):
            out.append({
                "style": doc["_id"]["style"],
                "style_mix": doc["_id"]["mix"],
                "sku_count": doc["sku_count"],
            })
        return out


# ═════════════════════════════════════════════════════════════════
# 3. Service — orchestration.
# ═════════════════════════════════════════════════════════════════

class AttributionService:
    def __init__(self, repo: AttributionRepository):
        self._repo = repo

    async def get_matrix(self, tenant_id: str) -> dict:
        wedge_counts = await self._repo.aggregate_wedge_counts(tenant_id)
        styles = await self._repo.aggregate_styles_with_mix(tenant_id)
        rows = [
            build_attribution_row(
                style=s["style"], mix=s["style_mix"],
                sku_count=s["sku_count"], wedge_counts=wedge_counts,
            )
            for s in styles
        ]
        rows.sort(key=lambda x: x["coverage_pct"], reverse=True)
        return {
            "attributions": rows,
            "total_styles": len(rows),
            "store_counts": wedge_counts,
            "rules": WEDGE_RULES,
        }
