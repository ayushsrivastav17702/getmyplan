"""
Assortment-Matrix domain module.

Endpoint owned:
  GET /assortment-matrix   Wedge × Style-Mix assortment matrix

Pure rule: which style-mixes reach which wedges?
  A-Stores: Core + Fashion + Test  ("Full")
  B-Stores: Core + Fashion         ("Standard")
  C-Stores: Core only              ("Efficiency / NOS")

This is the *inverse* view of `attribution.WEDGE_RULES`: here we fix the wedge
and ask "which mixes land here?", where the attribution module fixes the mix
and asks "which wedges does it reach?". Both are derived from the same truth.
"""

from typing import List

from .attribution import WEDGE_RULES


_WEDGE_LABELS = {
    "A": "Full (Core + Fashion + Test)",
    "B": "Standard (Core + Fashion)",
    "C": "Efficiency (Core NOS only)",
}


def mixes_eligible_for_wedge(wedge: str) -> List[str]:
    """Inverse lookup: given a wedge, which mixes ship there?"""
    return [mix for mix, rules in WEDGE_RULES.items() if rules.get(wedge)]


def build_matrix(wedge_counts: dict, mix_to_styles: dict) -> dict:
    """
    Build the Wedge × Mix assortment matrix.

    wedge_counts:   {"A": {"count": int, "stores": [...]}, ...}
    mix_to_styles:  {"Core": ["S1", "S2"], "Fashion": [...], "Test": [...]}
    """
    matrix: dict = {}
    for wedge in ("A", "B", "C"):
        eligible_mixes = mixes_eligible_for_wedge(wedge)
        breakdown = {m: len(mix_to_styles.get(m, [])) for m in eligible_mixes}
        matrix[wedge] = {
            "stores": wedge_counts.get(wedge, {}).get("count", 0),
            "assortment": _WEDGE_LABELS[wedge],
            "styles": sum(breakdown.values()),
            "style_breakdown": breakdown,
        }
    return matrix


# ═════════════════════════════════════════════════════════════════
# Repository
# ═════════════════════════════════════════════════════════════════

def _tenant_match(tenant_id: str) -> dict:
    return {"$or": [{"tenant_id": tenant_id}, {"tenant_id": {"$exists": False}}]}


class AssortmentMatrixRepository:
    def __init__(self, db):
        self._db = db

    async def aggregate_wedges_with_stores(self, tenant_id: str) -> dict:
        out: dict = {}
        async for doc in self._db.store_master.aggregate([
            {"$match": _tenant_match(tenant_id)},
            {"$group": {
                "_id": "$wedge_class",
                "count": {"$sum": 1},
                "stores": {"$push": "$store_code"},
            }},
        ]):
            out[doc["_id"]] = {"count": doc["count"], "stores": doc["stores"]}
        return out

    async def aggregate_styles_by_mix(self) -> dict:
        out: dict = {}
        async for doc in self._db.sku_ean_master.aggregate([
            {"$match": {"style_mix": {"$exists": True}}},
            {"$group": {"_id": "$style_mix", "styles": {"$addToSet": "$style"}}},
        ]):
            out[doc["_id"]] = list(set(doc["styles"]))
        return out


# ═════════════════════════════════════════════════════════════════
# Service
# ═════════════════════════════════════════════════════════════════

class AssortmentMatrixService:
    def __init__(self, repo: AssortmentMatrixRepository):
        self._repo = repo

    async def get_matrix(self, tenant_id: str) -> dict:
        wedge_counts = await self._repo.aggregate_wedges_with_stores(tenant_id)
        mix_to_styles = await self._repo.aggregate_styles_by_mix()
        return {
            "matrix": build_matrix(wedge_counts, mix_to_styles),
            "core_styles": mix_to_styles.get("Core", []),
            "fashion_styles": mix_to_styles.get("Fashion", []),
            "test_styles": mix_to_styles.get("Test", []),
        }
