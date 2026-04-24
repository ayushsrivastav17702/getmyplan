"""
Size Curve Optimization domain module.

## What it does
For each (store, category), computes the observed size-mix % based on recent
sales velocity and compares it against the tenant-wide "corporate curve".
Stores whose curve deviates materially from the corporate average are surfaced
for rebalancing — typical actions are: buy more Ls at stores where L is
over-indexing, phase out XXL at stores where it never moves.

## Inputs
- SKU dimension (sku → style, size, category)  ← reuses attribute_grouping repo
- daily_sales (sku, store_code, quantity) over a lookback window

## Pipeline
1. Bucket units by (store_code, category, size)
2. Normalise inside each (store, category) → pct_by_size
3. Compute corporate curve = weighted avg across all stores for the category
4. Flag stores whose curve deviates from corporate by > `deviation_threshold`
   (default 10pp absolute on any size)

## Non-goals for v1
- Unisex size de-duplication (we treat every raw size label as distinct —
  downstream sellers can normalise via a mapping layer)
- Forecast-based curves (v1 is look-backward only; v2 could weight recent
  weeks more heavily via exponential smoothing)
- Curve *allocation* (i.e. split a buy-plan quantity by the recommended mix)
  — exposed as a follow-up endpoint once the recommend step is live
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

# Note: we depend on `AttributeGroupingRepository` at runtime, but import it
# lazily inside `SizeCurveRepository.__init__` so that this module remains
# importable from any Python path (pytest runs from /app, the server from
# /app/backend — the two contexts see different module names).


# ═════════════════════════════════════════════════════════════════
# 1. Pure helpers — no I/O.
# ═════════════════════════════════════════════════════════════════

def normalize_distribution(counts: Dict[str, float]) -> Dict[str, float]:
    """Turn raw unit counts into percentages (0-100) summing to ~100."""
    total = sum(counts.values())
    if total <= 0:
        return {k: 0.0 for k in counts}
    return {k: round(v / total * 100, 2) for k, v in counts.items()}


def build_store_category_curves(
    enriched_skus: List[Dict[str, Any]],
    sales_by_store_sku: Dict[tuple, float],
    category_key: str = "category",
) -> Dict[tuple, Dict[str, Any]]:
    """
    Roll up units by (store_code, category, size).

    sales_by_store_sku: {(store_code, sku): units}
    Returns {(store_code, category): {total_units, sizes: {size: units}}}
    """
    buckets: Dict[tuple, Dict[str, Any]] = defaultdict(
        lambda: {"total_units": 0, "sizes": defaultdict(int)}
    )
    sku_lookup = {s.get("sku"): s for s in enriched_skus if s.get("sku")}

    for (store, sku), units in sales_by_store_sku.items():
        meta = sku_lookup.get(sku)
        if not meta:
            continue
        cat = meta.get(category_key)
        size = meta.get("size")
        if not cat or not size:
            continue
        b = buckets[(store, cat)]
        b["total_units"] += units
        b["sizes"][size] += units
    return buckets


def compute_corporate_curve(
    store_category_curves: Dict[tuple, Dict[str, Any]],
    category: str,
) -> Dict[str, float]:
    """
    Tenant-wide distribution for a single category = sum of units across all
    stores, normalised.
    """
    combined: Dict[str, float] = defaultdict(float)
    for (store, cat), rec in store_category_curves.items():
        if cat != category:
            continue
        for size, units in rec["sizes"].items():
            combined[size] += units
    return normalize_distribution(combined)


def compute_deviations(
    store_curve: Dict[str, float],
    corporate_curve: Dict[str, float],
) -> List[Dict[str, Any]]:
    """
    Per-size absolute deviation of the store's % from the corporate %.

    Returns rows sorted by |delta| desc so the biggest outliers are first.
    """
    all_sizes = set(store_curve) | set(corporate_curve)
    rows: List[Dict[str, Any]] = []
    for size in all_sizes:
        sp = store_curve.get(size, 0.0)
        cp = corporate_curve.get(size, 0.0)
        delta = round(sp - cp, 2)
        rows.append({
            "size": size,
            "store_pct": sp, "corporate_pct": cp,
            "delta_pp": delta,
            "direction": "over" if delta > 0 else ("under" if delta < 0 else "flat"),
        })
    rows.sort(key=lambda r: abs(r["delta_pp"]), reverse=True)
    return rows


def classify_stores(
    store_category_curves: Dict[tuple, Dict[str, Any]],
    category: str,
    corporate_curve: Dict[str, float],
    deviation_threshold_pp: float = 10.0,
    min_units: int = 50,
) -> Dict[str, Any]:
    """
    For every store carrying the target category, compute the deviation from
    the corporate curve and bucket the store as `outlier` if any size deviates
    by more than `deviation_threshold_pp` points (absolute).

    Returns {stores: [...], outlier_count, aligned_count}.
    """
    rows: List[Dict[str, Any]] = []
    for (store, cat), rec in store_category_curves.items():
        if cat != category:
            continue
        if rec["total_units"] < min_units:
            # Too little signal — skip (would overfit on noise)
            continue
        store_curve = normalize_distribution(dict(rec["sizes"]))
        deviations = compute_deviations(store_curve, corporate_curve)
        max_abs = max((abs(d["delta_pp"]) for d in deviations), default=0)
        is_outlier = max_abs > deviation_threshold_pp
        rows.append({
            "store_code": store,
            "total_units": rec["total_units"],
            "curve": store_curve,
            "deviations": deviations,
            "max_abs_delta_pp": round(max_abs, 2),
            "is_outlier": is_outlier,
            "top_size": max(store_curve, key=store_curve.get) if store_curve else None,
        })
    rows.sort(key=lambda r: r["max_abs_delta_pp"], reverse=True)
    return {
        "stores": rows,
        "outlier_count": sum(1 for r in rows if r["is_outlier"]),
        "aligned_count": sum(1 for r in rows if not r["is_outlier"]),
    }


def allocate_by_curve(
    total_qty: int, curve: Dict[str, float],
) -> Dict[str, int]:
    """
    Split a buy quantity across sizes according to the given curve.

    Uses the largest-remainder method so the sum always equals `total_qty`.
    """
    if total_qty <= 0 or not curve:
        return {}
    # Exact fractional allocation
    raw = {size: total_qty * (pct / 100.0) for size, pct in curve.items()}
    floors = {size: int(v) for size, v in raw.items()}
    assigned = sum(floors.values())
    # Distribute the remaining units to sizes with the largest remainders
    remainders = sorted(
        ((size, raw[size] - floors[size]) for size in raw),
        key=lambda x: x[1], reverse=True,
    )
    leftover = total_qty - assigned
    i = 0
    while leftover > 0 and remainders:
        floors[remainders[i % len(remainders)][0]] += 1
        leftover -= 1
        i += 1
    return floors


# ═════════════════════════════════════════════════════════════════
# 2. Repository — reuses attribute_grouping's plumbing.
# ═════════════════════════════════════════════════════════════════


class SizeCurveRepository:
    """
    Wraps `AttributeGroupingRepository` to expose the two reads we need:

      - `load_enriched_skus(tenant_id)`  (inherited behaviour)
      - `aggregate_sales_by_store_sku()` — the one new primitive here
    """

    def __init__(self, db):
        self._db = db
        # Lazy import to work from both `/app` (pytest) and `/app/backend` (server).
        try:
            from domains.analytics.attribute_grouping import AttributeGroupingRepository
        except ModuleNotFoundError:  # pragma: no cover
            from backend.domains.analytics.attribute_grouping import AttributeGroupingRepository
        self._inner = AttributeGroupingRepository(db)

    async def load_enriched_skus(self, tenant_id: str) -> List[Dict[str, Any]]:
        return await self._inner.load_enriched_skus(tenant_id)

    async def aggregate_sales_by_store_sku(
        self, tenant_id: str, start_day: str,
    ) -> Dict[tuple, float]:
        """Sum units per (store_code, sku) over the window."""
        tmatch = self._inner._tenant_match(tenant_id)
        pipeline = [
            {"$match": {**tmatch, "day": {"$gte": start_day}}},
            {"$group": {
                "_id": {"store": "$store_code", "sku": "$sku"},
                "units": {"$sum": {"$toInt": {"$ifNull": ["$quantity", 0]}}},
            }},
        ]
        out: Dict[tuple, float] = {}
        async for doc in self._db.daily_sales.aggregate(pipeline):
            out[(doc["_id"]["store"], doc["_id"]["sku"])] = doc.get("units", 0)
        return out


# ═════════════════════════════════════════════════════════════════
# 3. Service — orchestration.
# ═════════════════════════════════════════════════════════════════


class ValidationError(Exception):
    """Raised on bad input."""


def _window_start(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")


class SizeCurveService:
    def __init__(self, repo: SizeCurveRepository):
        self._repo = repo

    async def list_categories(self, *, tenant_id: str) -> Dict[str, Any]:
        """Categories that have at least one SKU with a size attribute."""
        skus = await self._repo.load_enriched_skus(tenant_id)
        by_cat: Dict[str, int] = defaultdict(int)
        for s in skus:
            if s.get("category") and s.get("size"):
                by_cat[s["category"]] += 1
        categories = [
            {"name": c, "sku_count": n}
            for c, n in sorted(by_cat.items(), key=lambda x: x[1], reverse=True)
        ]
        return {"categories": categories, "total_categories": len(categories)}

    async def corporate_curve(
        self, *, tenant_id: str, category: str, days: int = 90,
    ) -> Dict[str, Any]:
        if days < 1 or days > 365:
            raise ValidationError("days must be 1..365")
        skus = await self._repo.load_enriched_skus(tenant_id)
        sales = await self._repo.aggregate_sales_by_store_sku(
            tenant_id, _window_start(days),
        )
        curves = build_store_category_curves(skus, sales)
        corp = compute_corporate_curve(curves, category)
        if not corp:
            raise ValidationError(
                f"No sales data found for category '{category}' in the last {days} days",
            )
        return {
            "category": category, "days": days,
            "curve": corp,
            "sizes": sorted(corp, key=lambda s: corp[s], reverse=True),
        }

    async def recommend(
        self, *, tenant_id: str, category: str,
        days: int = 90,
        deviation_threshold_pp: float = 10.0,
        min_units: int = 50,
    ) -> Dict[str, Any]:
        if days < 1 or days > 365:
            raise ValidationError("days must be 1..365")
        skus = await self._repo.load_enriched_skus(tenant_id)
        sales = await self._repo.aggregate_sales_by_store_sku(
            tenant_id, _window_start(days),
        )
        curves = build_store_category_curves(skus, sales)
        corp = compute_corporate_curve(curves, category)
        if not corp:
            raise ValidationError(
                f"No sales data for category '{category}' in the last {days} days",
            )
        classified = classify_stores(
            curves, category, corp,
            deviation_threshold_pp=deviation_threshold_pp,
            min_units=min_units,
        )
        return {
            "category": category, "days": days,
            "corporate_curve": corp,
            "deviation_threshold_pp": deviation_threshold_pp,
            "min_units": min_units,
            **classified,
        }

    async def allocate(
        self, *, tenant_id: str, category: str,
        store_code: Optional[str] = None,
        total_qty: int = 0, days: int = 90,
    ) -> Dict[str, Any]:
        """
        Split `total_qty` across sizes using either the corporate curve
        (when `store_code` is None) or the specific store's curve.
        """
        if total_qty <= 0:
            raise ValidationError("total_qty must be > 0")
        skus = await self._repo.load_enriched_skus(tenant_id)
        sales = await self._repo.aggregate_sales_by_store_sku(
            tenant_id, _window_start(days),
        )
        curves = build_store_category_curves(skus, sales)
        corp = compute_corporate_curve(curves, category)
        if not corp:
            raise ValidationError(
                f"No sales data for category '{category}' in the last {days} days",
            )
        if store_code:
            rec = curves.get((store_code, category))
            if not rec:
                raise ValidationError(
                    f"No sales for store '{store_code}' in category '{category}'",
                )
            curve = normalize_distribution(dict(rec["sizes"]))
            curve_source = f"store:{store_code}"
        else:
            curve = corp
            curve_source = "corporate"
        allocation = allocate_by_curve(total_qty, curve)
        return {
            "category": category, "store_code": store_code,
            "curve_source": curve_source,
            "curve": curve,
            "total_qty": total_qty,
            "allocation": allocation,
        }
