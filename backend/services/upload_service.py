"""
Universal Upload Service with 75-error validations.
Adapted for async Motor driver and get_db() tenant pattern.
"""
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from utils.upload_errors import get_error

logger = logging.getLogger(__name__)


class UniversalUploadService:
    """Processes uploaded files with comprehensive validation."""

    REQUIRED_COLUMNS = {
        "daily_sales": ["sku", "store_code", "day", "quantity", "revenue"],
        "store_inventory": ["store_code", "sku", "closing_stock"],
        "warehouse_inventory": ["warehouse", "sku", "on_hand_qty", "available_qty"],
        "sku_master": ["sku", "product_name", "category"],
        "store_master": ["store_code", "store_name"],
        "warehouse_master": ["warehouse", "warehouse_name", "online_fulfillment_flag"],
        # Existing file types from v1
        "style_master": ["style_code", "season", "category", "subcategory", "gender", "brand"],
        "sku_ean_master": ["ean", "style", "size", "mrp"],
    }

    DEDUP_KEYS = {
        "daily_sales": ["sku", "store_code", "day"],
        "store_inventory": ["store_code", "sku"],
        "warehouse_inventory": ["warehouse", "sku"],
        "sku_master": ["sku"],
        "store_master": ["store_code"],
        "warehouse_master": ["warehouse"],
        "style_master": ["style_code"],
        "sku_ean_master": ["ean"],
    }

    def __init__(self, upload_type, master_skus=None, master_stores=None):
        self.upload_type = upload_type
        self.master_skus = master_skus or []
        self.master_stores = master_stores or []
        self.corrections = []
        self.warnings = []
        self.errors = []
        self.requires_approval = []

    def process_file(self, file_path, file_name):
        """Main entry point — processes file, returns complete validation result."""
        result = {
            "success": False,
            "file_name": file_name,
            "total_rows": 0,
            "valid_rows": 0,
            "corrections": [],
            "warnings": [],
            "errors": [],
            "requires_approval": False,
            "approval_items": [],
            "data": None,
            "preview": None,
        }

        try:
            df = self._read_file(file_path, file_name)
            result["total_rows"] = len(df)

            if len(df) == 0:
                result["errors"].append(get_error("E045"))
                return result

            # Normalize column names
            df.columns = [c.lower().strip() for c in df.columns]

            # Validate required columns
            df, col_errors = self._validate_columns(df)
            if col_errors:
                result["errors"].extend(col_errors)
                return result

            # Tag rows for error tracking
            df["_has_error"] = False

            # Run validations
            df = self._clean_sku(df)
            df = self._clean_store(df)
            df = self._clean_date(df)
            df = self._clean_quantity(df)
            df = self._clean_revenue(df)
            self._check_duplicates_in_file(df)
            self._check_business_rules(df)

            # Assemble result
            error_count = int(df["_has_error"].sum()) if "_has_error" in df.columns else 0
            result["success"] = len(self.errors) == 0
            result["corrections"] = self.corrections
            result["warnings"] = self.warnings
            result["errors"] = self.errors
            result["requires_approval"] = len(self.requires_approval) > 0
            result["approval_items"] = self.requires_approval[:10]
            result["valid_rows"] = len(df) - error_count

            # Strip internal columns for data output
            data_cols = [c for c in df.columns if not c.startswith("_")]
            # Convert timestamps to ISO strings for JSON serialization
            out_df = df[data_cols].copy()
            for col in out_df.select_dtypes(include=["datetime64", "datetimetz"]).columns:
                out_df[col] = out_df[col].dt.strftime("%Y-%m-%d").fillna("")
            result["data"] = out_df.fillna("").to_dict("records")
            result["preview"] = out_df.head(5).fillna("").to_dict("records")

        except Exception as e:
            logger.error(f"Upload processing error: {e}", exc_info=True)
            result["errors"].append({"code": "FATAL", "message": str(e), "severity": "blocking"})

        return result

    # ─── File Reading ──────────────────────────────────────────
    def _read_file(self, file_path, file_name):
        fname = file_name.lower()
        if fname.endswith(".xlsx") or fname.endswith(".xls"):
            return pd.read_excel(file_path)

        # CSV — try multiple encodings
        for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(file_path, encoding=enc)
                if "\ufffd" not in df.astype(str).iloc[:10].to_string():
                    return df
            except Exception:
                continue
        return pd.read_csv(file_path, encoding="utf-8", errors="ignore")

    # ─── Column Validation ─────────────────────────────────────
    def _validate_columns(self, df):
        required = self.REQUIRED_COLUMNS.get(self.upload_type, [])
        missing = [c for c in required if c not in df.columns]

        if missing:
            return df, [get_error("E043", columns=", ".join(missing))]

        extra = [c for c in df.columns if c not in required and not c.startswith("_")]
        if extra:
            self.warnings.append(get_error("E044", columns=", ".join(extra[:5])))

        # Keep required + extra (don't drop extra — they may be useful)
        return df, []

    # ─── SKU Cleaning ──────────────────────────────────────────
    def _clean_sku(self, df):
        if "sku" not in df.columns:
            return df

        df["sku"] = df["sku"].astype(str).str.strip()

        # E006: Remove special characters
        original = df["sku"].copy()
        df["sku"] = df["sku"].str.replace(r"[^\w\-]", "", regex=True)
        changed = int((original != df["sku"]).sum())
        if changed > 0:
            self.corrections.append({"code": "E006", "count": changed, "action": f"Removed special characters from {changed} SKUs"})

        # E001/E002: Numeric SKUs
        if df["sku"].str.match(r"^\d+\.?0*$").all():
            df["sku"] = df["sku"].str.replace(r"\.0+$", "", regex=True)
            self.corrections.append({"code": "E001", "action": "Converted numeric SKUs to text"})

        # E008: Case mismatch against master
        if self.master_skus:
            sku_lower_map = {s.lower(): s for s in self.master_skus}
            for idx, val in df["sku"].items():
                lower = val.lower()
                if lower in sku_lower_map and val != sku_lower_map[lower]:
                    df.at[idx, "sku"] = sku_lower_map[lower]

            # E003: SKU not in master
            invalid = ~df["sku"].isin(self.master_skus)
            if invalid.any():
                invalid_skus = df.loc[invalid, "sku"].unique()[:5].tolist()
                self.errors.append(get_error("E003", count=int(invalid.sum()), skus=", ".join(invalid_skus)))
                df.loc[invalid, "_has_error"] = True

        return df

    # ─── Store Cleaning ────────────────────────────────────────
    def _clean_store(self, df):
        if "store_code" not in df.columns:
            return df

        df["store_code"] = df["store_code"].astype(str).str.strip()

        # E013: Numeric store codes
        if df["store_code"].str.match(r"^\d+$").all():
            self.corrections.append({"code": "E013", "action": "Converted numeric store codes to text"})

        if self.master_stores:
            invalid = ~df["store_code"].isin(self.master_stores)
            if invalid.any():
                invalid_stores = df.loc[invalid, "store_code"].unique()[:5].tolist()
                self.errors.append(get_error("E011", count=int(invalid.sum()), stores=", ".join(invalid_stores)))
                df.loc[invalid, "_has_error"] = True

        return df

    # ─── Date Cleaning ─────────────────────────────────────────
    def _clean_date(self, df):
        date_col = "day" if "day" in df.columns else ("inventory_date" if "inventory_date" in df.columns else None)
        if not date_col:
            return df

        # E023: Text dates
        text_map = {
            "today": datetime.now(timezone.utc).date(),
            "yesterday": (datetime.now(timezone.utc) - timedelta(days=1)).date(),
        }
        for idx, val in df[date_col].items():
            s = str(val).lower().strip()
            if s in text_map:
                df.at[idx, date_col] = text_map[s]
                self.corrections.append({"code": "E023", "action": f"Converted '{s}' to {text_map[s]}"})

        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        failed = df[date_col].isna()
        if failed.any():
            self.errors.append(get_error("E019", count=int(failed.sum())))
            df.loc[failed, "_has_error"] = True

        # E020: Future dates
        now = pd.Timestamp(datetime.now(timezone.utc).date())
        future = df[date_col].notna() & (df[date_col] > now)
        if future.any():
            self.warnings.append(get_error("E020", count=int(future.sum())))

        return df

    # ─── Quantity Cleaning ─────────────────────────────────────
    def _clean_quantity(self, df):
        qty_col = None
        for col in ["quantity", "closing_stock", "on_hand_qty"]:
            if col in df.columns:
                qty_col = col
                break
        if not qty_col:
            return df

        if df[qty_col].dtype == "object":
            df[qty_col] = df[qty_col].astype(str).str.replace(",", "")

        df[qty_col] = pd.to_numeric(df[qty_col], errors="coerce").fillna(0)

        # E027: Negative
        negative = df[qty_col] < 0
        if negative.any():
            self.warnings.append(get_error("E027", count=int(negative.sum())))

        # E032: Unusually large
        q99 = df[qty_col].quantile(0.99) if len(df) > 10 else 0
        if q99 > 0:
            unusual = df[df[qty_col] > q99 * 10]
            for idx, row in unusual.iterrows():
                self.requires_approval.append({
                    "code": "E032", "row": int(idx),
                    "value": float(row[qty_col]),
                    "message": f"Unusually large quantity: {row[qty_col]}",
                })

        return df

    # ─── Revenue Cleaning ──────────────────────────────────────
    def _clean_revenue(self, df):
        if "revenue" not in df.columns:
            return df

        if df["revenue"].dtype == "object":
            df["revenue"] = df["revenue"].astype(str).str.replace(r"[$\u20ac\u00a3\u20b9,]", "", regex=True)

        df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0)

        negative = df["revenue"] < 0
        if negative.any():
            self.warnings.append(get_error("E035", count=int(negative.sum())))

        q99 = df["revenue"].quantile(0.99) if len(df) > 10 else 0
        if q99 > 0:
            unusual = df[df["revenue"] > q99 * 10]
            for idx, row in unusual.iterrows():
                self.requires_approval.append({
                    "code": "E040", "row": int(idx),
                    "value": float(row["revenue"]),
                    "message": f"Unusually large revenue: {row['revenue']:,.2f}",
                })

        return df

    # ─── Duplicate Check ───────────────────────────────────────
    def _check_duplicates_in_file(self, df):
        dedup_cols = self.DEDUP_KEYS.get(self.upload_type)
        if not dedup_cols:
            return
        valid_cols = [c for c in dedup_cols if c in df.columns]
        if not valid_cols:
            return
        dupes = df.duplicated(subset=valid_cols, keep="first")
        if dupes.any():
            self.warnings.append(get_error("E050", count=int(dupes.sum())))

    # ─── Business Rules ────────────────────────────────────────
    def _check_business_rules(self, df):
        # E066: Low stock warning
        if "closing_stock" in df.columns:
            low_stock = df[df["closing_stock"] < 10]
            if len(low_stock) > 0:
                self.warnings.append(get_error("E066", count=len(low_stock)))

        # E070: Test data detection
        for col in ["sku", "store_code", "warehouse"]:
            if col in df.columns:
                test_rows = df[df[col].astype(str).str.lower().isin(["test", "demo", "sample"])]
                if len(test_rows) > 0:
                    self.warnings.append(get_error("E070"))
                    break

        # E041: Zero revenue with positive quantity
        if "revenue" in df.columns and "quantity" in df.columns:
            zero_rev = (df["quantity"] > 0) & (df["revenue"] == 0)
            if zero_rev.any():
                self.warnings.append(get_error("E041", count=int(zero_rev.sum())))
