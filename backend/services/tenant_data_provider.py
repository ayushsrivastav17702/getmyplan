"""
TenantDataProvider — Single Source of Truth for tenant data.

Works with the existing `get_cached_data(file_type)` and `get_db()` pattern.
Primary data comes from uploaded CSV files stored in `uploaded_files` collection.
Onboarding wizard data (ob_categories, ob_stores, ob_marketplaces) serves as
fallback when CSV data is unavailable — CSV always takes precedence.
"""
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# Module-level references (set by init_tenant_provider)
_get_cached_data = None
_get_db = None


def init_tenant_provider(get_cached_data_func, get_db_func):
    """Called once at startup from server.py to inject dependencies."""
    global _get_cached_data, _get_db
    _get_cached_data = get_cached_data_func
    _get_db = get_db_func


class TenantDataProvider:
    """Provides tenant-specific data from uploaded CSVs, with onboarding data as fallback."""

    def __init__(self):
        self._cache: Dict[str, object] = {}

    # ── Helper to load a DataFrame from cached upload ────────
    async def _get_df(self, file_type: str) -> Optional[pd.DataFrame]:
        df = await _get_cached_data(file_type)
        return df

    # ── Onboarding fallback helpers ──────────────────────────
    async def _ob_categories(self) -> List[str]:
        """Get root-level category names from onboarding wizard."""
        db = _get_db()
        cats = await db.ob_categories.find({"is_active": True, "level": 1}, {"_id": 0, "name": 1}).to_list(200)
        return sorted(set(c["name"] for c in cats if c.get("name")))

    async def _ob_subcategories(self, category: str = None) -> List[str]:
        """Get level-2+ category names from onboarding wizard."""
        db = _get_db()
        query = {"is_active": True, "level": {"$gte": 2}}
        if category:
            parent = await db.ob_categories.find_one(
                {"is_active": True, "name": category}, {"_id": 0, "category_id": 1}
            )
            if parent:
                query["parent_id"] = parent["category_id"]
        cats = await db.ob_categories.find(query, {"_id": 0, "name": 1}).to_list(500)
        return sorted(set(c["name"] for c in cats if c.get("name")))

    async def _ob_channels(self) -> List[str]:
        """Get marketplace names from onboarding wizard as channel fallback."""
        db = _get_db()
        mps = await db.ob_marketplaces.find({"is_active": True}, {"_id": 0, "name": 1}).to_list(200)
        return sorted(set(m["name"] for m in mps if m.get("name")))

    async def _ob_regions(self) -> List[str]:
        """Get unique states from onboarding stores as region fallback."""
        db = _get_db()
        stores = await db.ob_stores.find({"is_active": True}, {"_id": 0, "state": 1}).to_list(500)
        return sorted(set(s["state"] for s in stores if s.get("state")))

    async def _ob_stores(self) -> List[Dict]:
        """Get stores from onboarding wizard."""
        db = _get_db()
        return await db.ob_stores.find({"is_active": True}, {"_id": 0}).to_list(500)

    async def _ob_store_codes(self) -> List[str]:
        stores = await self._ob_stores()
        return [s.get("store_code", "") for s in stores if s.get("store_code")]

    # ══════════════════════════════════════════════════════════
    #  MASTER DATA  (from uploaded CSV files)
    # ══════════════════════════════════════════════════════════

    async def get_categories(self) -> List[str]:
        """Categories: onboarding categories override CSV when present."""
        if "categories" in self._cache:
            return self._cache["categories"]
        # Onboarding categories are the authoritative config
        ob_cats = await self._ob_categories()
        if ob_cats:
            self._cache["categories"] = ob_cats
            return ob_cats
        # No onboarding categories — use CSV data
        df = await self._get_df("style_master")
        if df is not None and "category" in df.columns:
            cats = sorted(df["category"].dropna().unique().tolist())
            self._cache["categories"] = cats
            return cats
        return []

    async def get_subcategories(self, category: str = None) -> List[str]:
        # Onboarding subcategories override CSV when present
        ob_subs = await self._ob_subcategories(category)
        if ob_subs:
            return ob_subs
        df = await self._get_df("style_master")
        if df is not None and "subcategory" in df.columns:
            filtered = df[df["category"] == category] if category else df
            return sorted(filtered["subcategory"].dropna().unique().tolist())
        return []

    async def get_brands(self) -> List[str]:
        df = await self._get_df("style_master")
        if df is None or "brand" not in df.columns:
            return []
        return sorted(df["brand"].dropna().unique().tolist())

    async def get_genders(self) -> List[str]:
        df = await self._get_df("style_master")
        if df is None or "gender" not in df.columns:
            return []
        return sorted(df["gender"].dropna().unique().tolist())

    async def get_seasons(self) -> List[str]:
        df = await self._get_df("style_master")
        if df is None or "season" not in df.columns:
            return []
        return sorted(df["season"].dropna().unique().tolist())

    async def get_styles(self, category: str = None) -> List[Dict]:
        """Return list of style dicts from style_master."""
        df = await self._get_df("style_master")
        if df is None:
            return []
        if category and "category" in df.columns:
            df = df[df["category"] == category]
        return df.to_dict("records")

    # ── Stores ───────────────────────────────────────────────

    async def get_stores(self) -> List[Dict]:
        """Stores: onboarding stores override CSV when present."""
        if "stores" in self._cache:
            return self._cache["stores"]
        ob_stores = await self._ob_stores()
        if ob_stores:
            self._cache["stores"] = ob_stores
            return ob_stores
        df = await self._get_df("store_master")
        if df is not None and len(df) > 0:
            stores = df.to_dict("records")
            self._cache["stores"] = stores
            return stores
        return []

    async def get_store_codes(self) -> List[str]:
        stores = await self.get_stores()
        codes = [s.get("store_code", s.get("store", "")) for s in stores]
        return sorted(set(c for c in codes if c))

    async def get_channels(self) -> List[str]:
        """Channels: onboarding marketplaces override CSV when present."""
        if "channels" in self._cache:
            return self._cache["channels"]
        ob_chans = await self._ob_channels()
        if ob_chans:
            self._cache["channels"] = ob_chans
            return ob_chans
        csv_chans = []
        df = await self._get_df("store_master")
        if df is not None and "channel" in df.columns:
            csv_chans = df["channel"].dropna().unique().tolist()
        if not csv_chans:
            sales_df = await self._get_df("daily_sales")
            if sales_df is not None and "channel" in sales_df.columns:
                csv_chans = sales_df["channel"].dropna().unique().tolist()
        merged = sorted(csv_chans)
        self._cache["channels"] = merged
        return merged

    async def get_regions(self) -> List[str]:
        ob_regions = await self._ob_regions()
        if ob_regions:
            return ob_regions
        df = await self._get_df("store_master")
        if df is not None and "region" in df.columns:
            return sorted(df["region"].dropna().unique().tolist())
        return []

    async def get_warehouses(self) -> List[Dict]:
        df = await self._get_df("warehouse_master")
        if df is None:
            return []
        return df.to_dict("records")

    # ══════════════════════════════════════════════════════════
    #  SALES DATA  (from uploaded daily_sales)
    # ══════════════════════════════════════════════════════════

    async def get_sales_df(self, category: str = None, channel: str = None,
                           start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """Get filtered sales DataFrame."""
        df = await self._get_df("daily_sales")
        if df is None:
            return None
        df = df.copy()
        if "day" in df.columns:
            df["day"] = pd.to_datetime(df["day"], errors="coerce")
        if start_date and "day" in df.columns:
            df = df[df["day"] >= pd.to_datetime(start_date)]
        if end_date and "day" in df.columns:
            df = df[df["day"] <= pd.to_datetime(end_date)]

        # Category requires joining with style_master (sales have sku, not category)
        if category:
            style_df = await self._get_df("style_master")
            if style_df is not None and "style_code" in style_df.columns:
                cat_styles = style_df[style_df["category"] == category]["style_code"].tolist()
                if "style" in df.columns:
                    df = df[df["style"].isin(cat_styles)]
                elif "sku" in df.columns:
                    sku_df = await self._get_df("sku_ean_master")
                    if sku_df is not None:
                        cat_skus = sku_df[sku_df["style"].isin(cat_styles)]["ean"].tolist()
                        df = df[df["sku"].isin(cat_skus)]

        if channel and "channel" in df.columns:
            df = df[df["channel"] == channel]
        return df

    async def get_historical_sales_range(self) -> Dict:
        """Date range of uploaded sales data."""
        df = await self._get_df("daily_sales")
        if df is None or "day" not in df.columns or len(df) == 0:
            return {"oldest_date": None, "newest_date": None, "months_available": 0, "has_data": False}
        dates = pd.to_datetime(df["day"], errors="coerce").dropna()
        if dates.empty:
            return {"oldest_date": None, "newest_date": None, "months_available": 0, "has_data": False}
        oldest = dates.min()
        newest = dates.max()
        months = max(1, int((newest - oldest).days / 30))
        return {
            "oldest_date": oldest.isoformat(),
            "newest_date": newest.isoformat(),
            "months_available": months,
            "has_data": True,
        }

    async def get_revenue_by_category(self, days: int = 90) -> Dict[str, float]:
        """Revenue grouped by category from real sales."""
        sales_df = await self._get_df("daily_sales")
        style_df = await self._get_df("style_master")
        sku_df = await self._get_df("sku_ean_master")
        if sales_df is None or style_df is None or sku_df is None:
            return {}
        sales_df = sales_df.copy()
        sales_df["day"] = pd.to_datetime(sales_df["day"], errors="coerce")
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
        sales_df = sales_df[sales_df["day"] >= cutoff]
        # Join: sales.sku → sku_ean.ean → sku_ean.style → style.style_code → style.category
        merged = sales_df.merge(sku_df[["ean", "style"]], left_on="sku", right_on="ean", how="left")
        merged = merged.merge(style_df[["style_code", "category"]], left_on="style", right_on="style_code", how="left")
        if "category" not in merged.columns:
            return {}
        result = merged.groupby("category")["revenue"].sum()
        return {k: round(v, 2) for k, v in result.items() if pd.notna(k)}

    async def get_revenue_by_channel(self, days: int = 90) -> Dict[str, float]:
        """Revenue grouped by channel."""
        df = await self._get_df("daily_sales")
        if df is None or "channel" not in df.columns:
            return {}
        df = df.copy()
        df["day"] = pd.to_datetime(df["day"], errors="coerce")
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
        df = df[df["day"] >= cutoff]
        result = df.groupby("channel")["revenue"].sum()
        return {k: round(v, 2) for k, v in result.items()}

    async def get_asp_by_category(self) -> Dict[str, float]:
        """Average selling price per category from real data."""
        sales_df = await self._get_df("daily_sales")
        style_df = await self._get_df("style_master")
        sku_df = await self._get_df("sku_ean_master")
        if sales_df is None or sku_df is None or style_df is None:
            return {}
        # Required columns — skip gracefully if a tenant's upload is missing any.
        if not {"sku", "revenue", "quantity"}.issubset(sales_df.columns):
            return {}
        if not {"ean", "style"}.issubset(sku_df.columns):
            return {}
        if not {"style_code", "category"}.issubset(style_df.columns):
            return {}
        # If sales_df already has a "style" column (pre-denormalised by some uploaders)
        # the merge below would rename into style_x/style_y and break line 289. Drop it
        # so `sku_df.style` wins and becomes the merge key.
        if "style" in sales_df.columns:
            sales_df = sales_df.drop(columns=["style"])
        merged = sales_df.merge(sku_df[["ean", "style"]], left_on="sku", right_on="ean", how="left")
        if "style" not in merged.columns:  # defensive: upstream merge produced no style col
            return {}
        merged = merged.merge(style_df[["style_code", "category"]], left_on="style", right_on="style_code", how="left")
        merged["asp"] = merged["revenue"] / merged["quantity"].replace(0, 1)
        result = merged.groupby("category")["asp"].mean()
        return {k: round(v, 2) for k, v in result.items() if pd.notna(k)}

    async def get_channel_splits(self, days: int = 365) -> Dict[str, float]:
        """Revenue share per channel from real sales."""
        rev = await self.get_revenue_by_channel(days)
        total = sum(rev.values())
        if total == 0:
            return {}
        return {k: round(v / total, 4) for k, v in rev.items()}

    async def get_seasonality_factors(self) -> Dict[int, float]:
        """Monthly seasonality index from real sales."""
        df = await self._get_df("daily_sales")
        if df is None or "day" not in df.columns:
            return {m: 1.0 for m in range(1, 13)}
        df = df.copy()
        df["day"] = pd.to_datetime(df["day"], errors="coerce")
        df["month"] = df["day"].dt.month
        monthly = df.groupby("month")["revenue"].sum()
        if monthly.empty:
            return {m: 1.0 for m in range(1, 13)}
        avg = monthly.mean()
        if avg == 0:
            return {m: 1.0 for m in range(1, 13)}
        factors = {}
        for m in range(1, 13):
            factors[m] = round(monthly.get(m, avg) / avg, 2)
        return factors

    # ══════════════════════════════════════════════════════════
    #  INVENTORY DATA  (from uploaded store_inventory)
    # ══════════════════════════════════════════════════════════

    async def get_inventory_df(self, channel: str = None, store_code: str = None) -> Optional[pd.DataFrame]:
        df = await self._get_df("store_inventory")
        if df is None:
            return None
        df = df.copy()
        if channel and "channel" in df.columns:
            df = df[df["channel"] == channel]
        if store_code and "store_code" in df.columns:
            df = df[df["store_code"] == store_code]
        return df

    async def get_current_inventory_by_channel(self, channel: str) -> int:
        """Total inventory for a specific channel."""
        df = await self.get_inventory_df(channel=channel)
        if df is None or "quantity" not in df.columns:
            return 0
        return int(df["quantity"].sum())

    # ══════════════════════════════════════════════════════════
    #  DATA AVAILABILITY CHECK
    # ══════════════════════════════════════════════════════════

    async def validate_data_availability(self) -> Dict:
        """Check what data has been uploaded and what comes from onboarding."""
        style_df = await self._get_df("style_master")
        store_df = await self._get_df("store_master")
        sales_range = await self.get_historical_sales_range()
        has_styles = style_df is not None and len(style_df) > 0
        has_stores = store_df is not None and len(store_df) > 0

        # Check onboarding data availability
        ob_cats = await self._ob_categories()
        ob_stores = await self._ob_store_codes()
        ob_channels = await self._ob_channels()
        has_ob_cats = len(ob_cats) > 0
        has_ob_stores = len(ob_stores) > 0
        has_ob_channels = len(ob_channels) > 0

        missing = []
        if not has_styles and not has_ob_cats:
            missing.append("Style Master")
        if not has_stores and not has_ob_stores:
            missing.append("Store Master")
        if not sales_range["has_data"]:
            missing.append("Daily Sales data")

        csv_ready = has_styles and has_stores and sales_range["has_data"]

        return {
            "has_style_master": has_styles,
            "has_store_master": has_stores,
            "has_sales_data": sales_range["has_data"],
            "sales_months_available": sales_range["months_available"],
            "is_ready": csv_ready,
            "has_onboarding_data": has_ob_cats or has_ob_stores or has_ob_channels,
            "onboarding_contributing": {
                "categories": has_ob_cats,
                "stores": has_ob_stores,
                "channels": has_ob_channels,
            },
            "missing": missing,
        }


    async def get_analytics_options(self) -> Dict:
        """Unified options for all analytics modules."""
        categories = await self.get_categories()
        subcategories = await self.get_subcategories()
        channels = await self.get_channels()
        regions = await self.get_regions()
        brands = await self.get_brands()
        genders = await self.get_genders()
        seasons = await self.get_seasons()
        data_status = await self.validate_data_availability()
        sales_range = await self.get_historical_sales_range()

        return {
            "has_data": data_status["is_ready"],
            "data_status": data_status,
            "sales_range": sales_range,
            "categories": categories,
            "subcategories": subcategories,
            "channels": channels,
            "regions": regions,
            "brands": brands,
            "genders": genders,
            "seasons": seasons,
        }


async def get_tenant_provider() -> TenantDataProvider:
    """FastAPI-compatible dependency (works within tenant middleware context)."""
    return TenantDataProvider()
