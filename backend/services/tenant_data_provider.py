"""
TenantDataProvider — Single Source of Truth for tenant-uploaded data.

Works with the existing `get_cached_data(file_type)` and `get_db()` pattern.
Data comes ONLY from uploaded CSV files stored in `uploaded_files` collection.
No hardcoded mock data; returns empty lists / 0 when no data is available.
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
    """Provides tenant-specific data from uploaded CSVs only."""

    def __init__(self):
        self._cache: Dict[str, object] = {}

    # ── Helper to load a DataFrame from cached upload ────────
    async def _get_df(self, file_type: str) -> Optional[pd.DataFrame]:
        df = await _get_cached_data(file_type)
        return df

    # ══════════════════════════════════════════════════════════
    #  MASTER DATA  (from uploaded CSV files)
    # ══════════════════════════════════════════════════════════

    async def get_categories(self) -> List[str]:
        """Categories from style_master upload."""
        if "categories" in self._cache:
            return self._cache["categories"]
        df = await self._get_df("style_master")
        if df is None or "category" not in df.columns:
            return []
        cats = sorted(df["category"].dropna().unique().tolist())
        self._cache["categories"] = cats
        return cats

    async def get_subcategories(self, category: str = None) -> List[str]:
        df = await self._get_df("style_master")
        if df is None or "subcategory" not in df.columns:
            return []
        if category:
            df = df[df["category"] == category]
        return sorted(df["subcategory"].dropna().unique().tolist())

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
        """Stores from store_master upload."""
        if "stores" in self._cache:
            return self._cache["stores"]
        df = await self._get_df("store_master")
        if df is None:
            return []
        stores = df.to_dict("records")
        self._cache["stores"] = stores
        return stores

    async def get_store_codes(self) -> List[str]:
        stores = await self.get_stores()
        return [s.get("store_code", s.get("store", "")) for s in stores]

    async def get_channels(self) -> List[str]:
        """Unique channel values from store_master."""
        if "channels" in self._cache:
            return self._cache["channels"]
        df = await self._get_df("store_master")
        if df is None or "channel" not in df.columns:
            # Fallback to daily_sales channel column
            sales_df = await self._get_df("daily_sales")
            if sales_df is not None and "channel" in sales_df.columns:
                chans = sorted(sales_df["channel"].dropna().unique().tolist())
                self._cache["channels"] = chans
                return chans
            return []
        chans = sorted(df["channel"].dropna().unique().tolist())
        self._cache["channels"] = chans
        return chans

    async def get_regions(self) -> List[str]:
        df = await self._get_df("store_master")
        if df is None or "region" not in df.columns:
            return []
        return sorted(df["region"].dropna().unique().tolist())

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
        merged = sales_df.merge(sku_df[["ean", "style"]], left_on="sku", right_on="ean", how="left")
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
        """Check what data has been uploaded."""
        style_df = await self._get_df("style_master")
        store_df = await self._get_df("store_master")
        sales_range = await self.get_historical_sales_range()
        has_styles = style_df is not None and len(style_df) > 0
        has_stores = store_df is not None and len(store_df) > 0

        missing = []
        if not has_styles:
            missing.append("Style Master")
        if not has_stores:
            missing.append("Store Master")
        if not sales_range["has_data"]:
            missing.append("Daily Sales data")

        return {
            "has_style_master": has_styles,
            "has_store_master": has_stores,
            "has_sales_data": sales_range["has_data"],
            "sales_months_available": sales_range["months_available"],
            "is_ready": has_styles and has_stores and sales_range["has_data"],
            "missing": missing,
        }


async def get_tenant_provider() -> TenantDataProvider:
    """FastAPI-compatible dependency (works within tenant middleware context)."""
    return TenantDataProvider()
