"""
Attribute Grouping domain module.

## What it does
For each SKU, treats one or more scalar fields as "attribute levels" and rolls
up sales by each level to answer questions like:

  - "Which colors are trending this quarter vs last?"
  - "How does Cotton compare to Polyester on avg units per SKU?"
  - "What's a reasonable demand forecast for a brand-new (Blue, Cotton, Slim) tee?"

## Why not a fixed 17-level schema
Retailers differ wildly in how they tag product attributes. Some upload only
`category + style + size`; others enrich with an `attributes` sub-object
(`attributes.color`, `attributes.fabric`, …). Hard-coding `level_1 = Category`
breaks the moment a tenant uses something different.

Instead we **discover** available attributes at runtime:
  1. Known base fields from sku_master joined with style_master
     (`category`, `style`, `size`).
  2. Derived fields parsed from dash-separated SKU codes
     (`TSHIRT-BLK-M` → `type=TSHIRT, color=BLK, size=M`).
  3. Any `attributes.*` sub-object fields if the tenant has uploaded them.

## Pipeline
load_sku_attributes → aggregate_sales_by_attribute → rank/compare/forecast
Each step is a pure function (once the two Mongo reads are done upstream).

## Non-goals for v1
- No per-tenant attribute schema editor (future: tenant config collection)
- No ML-trained similarity (forecast uses simple attribute-overlap heuristic)
- No attribute hierarchy (future: "T-Shirt" rolls up to "Apparel")
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ═════════════════════════════════════════════════════════════════
# 1. Pure helpers — no I/O.
# ═════════════════════════════════════════════════════════════════

# Base attribute levels that are guaranteed to exist in our SKU/style data.
# "field" is the flat JSON path inside the merged SKU dict produced by
# `merge_sku_and_style`; "source" is informational for the UI.
BASE_LEVELS: List[Dict[str, str]] = [
    {"key": "category", "name": "Category", "source": "style_master"},
    {"key": "style",    "name": "Style",    "source": "sku_master"},
    {"key": "size",     "name": "Size",     "source": "sku_master"},
]

# Extra levels parsed from the SKU code itself (dash-separated tokens).
# We assume the convention `TYPE-COLOR-SIZE` used by the demo seed data, but
# each derivation is independent so we simply attempt every position and only
# surface the level if at least one SKU has a non-empty value.
DERIVED_LEVELS: List[Dict[str, str]] = [
    {"key": "sku_type",  "name": "SKU Type",  "source": "derived.sku[0]"},
    {"key": "sku_color", "name": "SKU Color", "source": "derived.sku[1]"},
]


def parse_sku_tokens(sku: str) -> Dict[str, str]:
    """Derive type/color/size from a dash-separated SKU code.

    We support two common conventions:

      1. TYPE-COLOR-SIZE         → `TSHIRT-BLK-M`
      2. <prefix>-TYPE-CODE-COLOR-SIZE → `STYLE-TS-002-PNK-S`

    Heuristic: split by `-`, take last two tokens as (color, size), and the
    third-from-last (if it looks alphabetic) as the type. Any remaining
    tokens fold into the style/prefix and are ignored here (style is already
    carried on its own field).

    Examples:
        TSHIRT-BLK-M          → {sku_type: TSHIRT, sku_color: BLK}
        STYLE-TS-002-PNK-S    → {sku_type: TS,     sku_color: PNK}
        CAP-WHT-OS            → {sku_type: CAP,    sku_color: WHT}
        POLO                  → {sku_type: POLO}
    """
    if not sku or not isinstance(sku, str):
        return {}
    parts = [p for p in sku.split("-") if p]
    out: Dict[str, str] = {}
    if len(parts) == 1:
        out["sku_type"] = parts[0]
    elif len(parts) == 2:
        out["sku_type"] = parts[0]
        out["sku_color"] = parts[1]
    elif len(parts) == 3:
        out["sku_type"] = parts[0]
        out["sku_color"] = parts[1]
    else:
        # 4+ parts: `<prefix>-TYPE-CODE-COLOR-SIZE` — type is second position,
        # color is second-to-last.
        type_candidate = parts[1] if parts[1].isalpha() else parts[0]
        out["sku_type"] = type_candidate
        out["sku_color"] = parts[-2]
    return out


def merge_sku_and_style(
    sku_doc: Dict[str, Any],
    style_doc: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build a flat attribute dict for a single SKU.

    Pulls:
      - style/size/mrp/ean from sku_master (or store_inventory fallback)
      - EVERY scalar field from style_master (category, sub_category, brand,
        gender, season, fabric, …) — tenants enrich at the style level and we
        surface whatever they've uploaded.
      - parsed sku_type/sku_color from the SKU code
      - every key under `sku_doc.attributes` if present (future-proofing)
    """
    out: Dict[str, Any] = {
        "sku": sku_doc.get("sku") or sku_doc.get("ean"),
        "style": sku_doc.get("style"),
        "size": sku_doc.get("size"),
        "mrp": sku_doc.get("mrp"),
    }
    # Pull every scalar style-master field (skip internal metadata keys).
    if style_doc:
        _SKIP = {"_id", "tenant_id", "style_code", "style", "uploaded_at",
                 "uploaded_by", "created_at", "updated_at"}
        for k, v in style_doc.items():
            if k in _SKIP:
                continue
            if isinstance(v, (str, int, float, bool)) and v not in (None, ""):
                out[k] = v
    # Derived tokens
    out.update(parse_sku_tokens(out["sku"] or ""))
    # Tenant-provided sub-object (future extensibility)
    for k, v in (sku_doc.get("attributes") or {}).items():
        out[k] = v
    return out


def discover_levels(enriched_skus: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Inspect a collection of merged SKU dicts and return the *populated* levels.

    A level is surfaced only if at least one SKU carries a non-empty value
    for it — keeps the UI tidy.  Each entry carries sample `values` so the
    frontend can populate a dropdown without a second round-trip.
    """
    # Collect candidate keys from the known sets + anything new seen in the data
    known = {lv["key"]: lv for lv in (BASE_LEVELS + DERIVED_LEVELS)}
    seen_keys: set = set()
    values_by_key: Dict[str, set] = defaultdict(set)
    for sku in enriched_skus:
        for k, v in sku.items():
            if k in ("sku", "mrp"):
                continue
            if v is None or v == "":
                continue
            seen_keys.add(k)
            values_by_key[k].add(str(v))

    out: List[Dict[str, Any]] = []
    idx = 1
    # Emit base + derived first (stable order), then any extras found
    for lv_def in BASE_LEVELS + DERIVED_LEVELS:
        k = lv_def["key"]
        if k in seen_keys:
            out.append({
                "level": idx, "key": k, "name": lv_def["name"],
                "source": lv_def["source"],
                "values": sorted(values_by_key[k])[:100],
                "value_count": len(values_by_key[k]),
            })
            idx += 1
    for k in sorted(seen_keys):
        if k in known:
            continue
        out.append({
            "level": idx, "key": k,
            "name": k.replace("_", " ").title(), "source": "attributes.*",
            "values": sorted(values_by_key[k])[:100],
            "value_count": len(values_by_key[k]),
        })
        idx += 1
    return out


def group_sales_by_attribute(
    enriched_skus: List[Dict[str, Any]],
    sales_by_sku: Dict[str, Dict[str, float]],
    attribute_key: str,
) -> List[Dict[str, Any]]:
    """
    Aggregate sales over the given attribute.

    sales_by_sku: {sku: {"units": int, "value": float}}
    Returns a list sorted by `total_units` desc, each row carrying
    total_units, total_value, unique_skus, avg_units_per_sku, avg_value_per_sku.
    """
    buckets: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"total_units": 0, "total_value": 0.0, "sku_set": set()}
    )
    for sku in enriched_skus:
        v = sku.get(attribute_key)
        if v is None or v == "":
            continue
        sales = sales_by_sku.get(sku.get("sku") or "", {"units": 0, "value": 0.0})
        b = buckets[str(v)]
        b["total_units"] += sales.get("units", 0)
        b["total_value"] += sales.get("value", 0.0)
        b["sku_set"].add(sku.get("sku"))

    rows: List[Dict[str, Any]] = []
    for attr_value, b in buckets.items():
        n = len(b["sku_set"]) or 1
        rows.append({
            "attribute_value": attr_value,
            "total_units": b["total_units"],
            "total_value": round(b["total_value"], 2),
            "unique_skus": len(b["sku_set"]),
            "avg_units_per_sku": round(b["total_units"] / n, 2),
            "avg_value_per_sku": round(b["total_value"] / n, 2),
        })
    rows.sort(key=lambda r: r["total_units"], reverse=True)
    return rows


def compute_trend_split(
    enriched_skus: List[Dict[str, Any]],
    sales_recent: Dict[str, Dict[str, float]],
    sales_old: Dict[str, Dict[str, float]],
    attribute_key: str,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    For each attribute value, compare `recent` vs `old` period unit totals and
    rank by growth %. A growth of 100% means "doubled"; a new value with zero
    old sales is reported as +100% (infinite growth clipped).

    Returns {trending: [...], declining: [...]}.
    """
    by_attr: Dict[str, List[str]] = defaultdict(list)
    for sku in enriched_skus:
        v = sku.get(attribute_key)
        if v is None or v == "":
            continue
        by_attr[str(v)].append(sku.get("sku"))

    rows: List[Dict[str, Any]] = []
    for attr_value, skus in by_attr.items():
        old = sum(sales_old.get(s, {}).get("units", 0) for s in skus)
        recent = sum(sales_recent.get(s, {}).get("units", 0) for s in skus)
        if old > 0:
            growth = round(((recent - old) / old) * 100, 2)
        else:
            growth = 100.0 if recent > 0 else 0.0
        rows.append({
            "attribute_value": attr_value,
            "old_sales": old,
            "recent_sales": recent,
            "growth_pct": growth,
            "sku_count": len(skus),
        })

    trending = sorted(rows, key=lambda r: r["growth_pct"], reverse=True)[:limit]
    declining = sorted(rows, key=lambda r: r["growth_pct"])[:limit]
    return {"trending": trending, "declining": declining}


def compare_attribute_values(
    grouped_rows: List[Dict[str, Any]],
    values_to_compare: List[str],
) -> Dict[str, Any]:
    """
    Pick the requested subset out of a `group_sales_by_attribute` result and
    add a "best performer" + human-readable recommendations.
    """
    lookup = {r["attribute_value"]: r for r in grouped_rows}
    subset = [lookup[v] for v in values_to_compare if v in lookup]
    if not subset:
        return {"comparison": [], "best_performer": None, "recommendations": []}
    best = max(subset, key=lambda r: r["avg_units_per_sku"])
    recs: List[Dict[str, Any]] = []
    for r in subset:
        if r["attribute_value"] == best["attribute_value"]:
            continue
        ratio = (
            best["avg_units_per_sku"] / r["avg_units_per_sku"]
            if r["avg_units_per_sku"] > 0 else 0
        )
        if ratio >= 1.5:
            recs.append({
                "type": "buy_more",
                "attribute": best["attribute_value"],
                "vs": r["attribute_value"],
                "ratio": round(ratio, 1),
                "message": (
                    f"{best['attribute_value']} sells {round(ratio, 1)}× better "
                    f"per SKU than {r['attribute_value']}. "
                    f"Consider skewing future buys toward {best['attribute_value']}."
                ),
            })
    return {"comparison": subset, "best_performer": best, "recommendations": recs}


def forecast_new_combination(
    enriched_skus: List[Dict[str, Any]],
    sales_by_sku: Dict[str, Dict[str, float]],
    attribute_combination: Dict[str, str],
    min_similarity: float = 0.5,
    lookback_days: int = 90,
) -> Dict[str, Any]:
    """
    For a hypothetical new SKU described by an attribute dict, find SKUs that
    share at least `min_similarity` fraction of those attributes and average
    their daily units.

    Returns {similar_skus_found, avg_similarity, forecast_daily_units,
             forecast_monthly_units, forecast_quarterly_units}.
    """
    if not attribute_combination:
        return {"error": "attribute_combination must not be empty"}

    n_attrs = len(attribute_combination)
    similar: List[Tuple[Dict[str, Any], float]] = []
    for sku in enriched_skus:
        matches = sum(
            1 for k, v in attribute_combination.items()
            if sku.get(k) is not None and str(sku.get(k)) == str(v)
        )
        sim = matches / n_attrs
        if sim >= min_similarity:
            similar.append((sku, sim))

    if not similar:
        return {
            "similar_skus_found": 0, "avg_similarity": 0.0,
            "forecast_daily_units": 0.0,
            "forecast_monthly_units": 0.0,
            "forecast_quarterly_units": 0.0,
        }

    total_units = 0.0
    total_sim = 0.0
    for sku, sim in similar:
        s = sales_by_sku.get(sku.get("sku") or "", {"units": 0})
        total_units += s.get("units", 0)
        total_sim += sim
    # total_units is the sum over `lookback_days`; normalise to per-SKU-per-day
    avg_daily = total_units / len(similar) / max(lookback_days, 1)
    return {
        "similar_skus_found": len(similar),
        "avg_similarity": round(total_sim / len(similar), 2),
        "forecast_daily_units": round(avg_daily, 2),
        "forecast_monthly_units": round(avg_daily * 30, 0),
        "forecast_quarterly_units": round(avg_daily * 90, 0),
    }


# ═════════════════════════════════════════════════════════════════
# 2. Repository — pure Mongo.
# ═════════════════════════════════════════════════════════════════


class AttributeGroupingRepository:
    def __init__(self, db):
        self._db = db

    @staticmethod
    def _tenant_match(tenant_id: str) -> dict:
        """Match docs for the given tenant OR pre-multi-tenant seed data (no tenant_id).

        Matches the convention used by `routes/buy_planning/_shared.py::_tenant_match`.
        """
        return {"$or": [{"tenant_id": tenant_id}, {"tenant_id": {"$exists": False}}]}

    async def load_enriched_skus(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Produce a flat attribute dict per distinct SKU for the tenant.

        Prefers `sku_master` if populated (canonical). If empty (common in
        production-seed environments), falls back to distinct SKUs from
        `store_inventory` — which carries `sku`, `style`, `size`, `ean`.

        Every SKU is left-joined with `style_master` (rich category / brand /
        gender / season attributes bubble up), and the dash-separated SKU
        code is parsed for derived `sku_type` / `sku_color`.
        """
        tmatch = self._tenant_match(tenant_id)

        # Pull style_master (small) into a lookup dict — we keep ALL scalar
        # fields so they flow through as attribute levels for free.
        style_map: Dict[str, Dict[str, Any]] = {}
        async for doc in self._db.style_master.find(tmatch, {"_id": 0}):
            key = doc.get("style_code") or doc.get("style")
            if key:
                style_map[key] = doc

        # Primary path: sku_master.
        sku_master_docs = [
            doc async for doc in self._db.sku_master.find(tmatch, {"_id": 0})
        ]

        if sku_master_docs:
            return [
                merge_sku_and_style(sku, style_map.get(sku.get("style")))
                for sku in sku_master_docs
            ]

        # Fallback: build SKU dimension from store_inventory distinct rows.
        pipeline = [
            {"$match": tmatch},
            {"$group": {
                "_id": "$sku",
                "style": {"$first": "$style"},
                "size": {"$first": "$size"},
                "ean": {"$first": "$ean"},
                "mrp": {"$first": "$mrp"},
            }},
        ]
        out: List[Dict[str, Any]] = []
        async for doc in self._db.store_inventory.aggregate(pipeline):
            sku_doc = {
                "sku": doc["_id"], "style": doc.get("style"),
                "size": doc.get("size"), "ean": doc.get("ean"),
                "mrp": doc.get("mrp"),
            }
            out.append(merge_sku_and_style(sku_doc, style_map.get(sku_doc["style"])))
        return out

    async def aggregate_sales(
        self, tenant_id: str, start_day: str, end_day: Optional[str] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Sum units + revenue per SKU in the [start_day, end_day) window.

        Returns {sku: {"units": int, "value": float}}
        """
        match: Dict[str, Any] = {
            **self._tenant_match(tenant_id),
            "day": {"$gte": start_day},
        }
        if end_day:
            match["day"]["$lt"] = end_day
        pipeline = [
            {"$match": match},
            {"$group": {
                "_id": "$sku",
                "units": {"$sum": {"$toInt": {"$ifNull": ["$quantity", 0]}}},
                "value": {"$sum": {"$toDouble": {"$ifNull": ["$revenue", 0]}}},
            }},
        ]
        out: Dict[str, Dict[str, float]] = {}
        async for doc in self._db.daily_sales.aggregate(pipeline):
            out[doc["_id"]] = {"units": doc["units"], "value": doc["value"]}
        return out


# ═════════════════════════════════════════════════════════════════
# 3. Service — orchestration.
# ═════════════════════════════════════════════════════════════════


class ValidationError(Exception):
    """Raised on bad input (unknown level, invalid range, etc.)."""


def _window_start(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")


class AttributeGroupingService:
    def __init__(self, repo: AttributeGroupingRepository):
        self._repo = repo

    async def get_levels(self, *, tenant_id: str) -> Dict[str, Any]:
        skus = await self._repo.load_enriched_skus(tenant_id)
        levels = discover_levels(skus)
        return {"levels": levels, "sku_count": len(skus)}

    async def get_sales_by_level(
        self, *, tenant_id: str, level_key: str,
        days: int = 90, attribute_value: Optional[str] = None,
    ) -> Dict[str, Any]:
        if days < 1 or days > 365:
            raise ValidationError("days must be 1..365")
        skus = await self._repo.load_enriched_skus(tenant_id)
        if not any(sku.get(level_key) for sku in skus):
            raise ValidationError(f"Unknown or empty attribute key: '{level_key}'")
        start = _window_start(days)
        sales = await self._repo.aggregate_sales(tenant_id, start)
        rows = group_sales_by_attribute(skus, sales, level_key)
        if attribute_value:
            rows = [r for r in rows if r["attribute_value"] == attribute_value]
        return {
            "level_key": level_key, "days": days,
            "total_skus": len(skus),
            "data": rows,
        }

    async def get_trends(
        self, *, tenant_id: str, level_key: str,
        days: int = 90, limit: int = 10,
    ) -> Dict[str, Any]:
        if days < 2 or days > 365:
            raise ValidationError("days must be 2..365")
        if limit < 1 or limit > 50:
            raise ValidationError("limit must be 1..50")
        skus = await self._repo.load_enriched_skus(tenant_id)
        if not any(sku.get(level_key) for sku in skus):
            raise ValidationError(f"Unknown or empty attribute key: '{level_key}'")
        split_days = days // 2
        recent_start = _window_start(split_days)
        old_start = _window_start(days)
        recent_sales = await self._repo.aggregate_sales(tenant_id, recent_start)
        old_sales = await self._repo.aggregate_sales(
            tenant_id, old_start, end_day=recent_start,
        )
        split = compute_trend_split(skus, recent_sales, old_sales, level_key, limit)
        return {
            "level_key": level_key,
            "period_days": days, "period_split": split_days,
            **split,
        }

    async def compare(
        self, *, tenant_id: str, level_key: str,
        attribute_values: List[str], days: int = 90,
    ) -> Dict[str, Any]:
        if len(attribute_values) < 2:
            raise ValidationError("Need at least 2 attribute values to compare")
        full = await self.get_sales_by_level(
            tenant_id=tenant_id, level_key=level_key, days=days,
        )
        result = compare_attribute_values(full["data"], attribute_values)
        return {"level_key": level_key, "days": days, **result}

    async def forecast(
        self, *, tenant_id: str,
        attribute_combination: Dict[str, str], days: int = 90,
    ) -> Dict[str, Any]:
        if not attribute_combination:
            raise ValidationError("attribute_combination must not be empty")
        skus = await self._repo.load_enriched_skus(tenant_id)
        sales = await self._repo.aggregate_sales(tenant_id, _window_start(days))
        return forecast_new_combination(
            skus, sales, attribute_combination, lookback_days=days,
        )
