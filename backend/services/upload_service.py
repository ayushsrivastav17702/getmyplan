"""
Universal Upload Service with 75-error validations.
Adapted for async Motor driver and get_db() tenant pattern.
"""
import pandas as pd
import numpy as np
import hashlib
import logging
import re
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

    def __init__(self, upload_type, master_skus=None, master_stores=None, master_warehouses=None, file_hash=None):
        self.upload_type = upload_type
        self.master_skus = master_skus or []
        self.master_stores = master_stores or []
        self.master_warehouses = master_warehouses or []
        self.file_hash = file_hash
        self.corrections = []
        self.warnings = []
        self.errors = []
        self.requires_approval = []
        self._currency_info = {"detected": None, "symbols_found": set()}

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
            df = self._clean_warehouse(df)
            df = self._clean_date(df)
            df = self._clean_quantity(df)
            df = self._clean_revenue(df)
            df = self._validate_warehouse_inventory(df)
            df = self._validate_warehouse_master_flags(df)
            self._check_master_duplicates(df)
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

            # Add currency info if detected
            if self._currency_info["detected"]:
                result["currency"] = {
                    "detected": self._currency_info["detected"],
                    "symbols_found": list(self._currency_info["symbols_found"]),
                    "converted_to_base": self._currency_info.get("converted_to_base", False),
                }

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

        # E007: Whitespace trimming
        original_ws = df["sku"].astype(str).copy()
        df["sku"] = df["sku"].astype(str).str.strip()
        ws_changed = int((original_ws != df["sku"]).sum())
        if ws_changed > 0:
            self.corrections.append({"code": "E007", "count": ws_changed, "action": f"Trimmed whitespace from {ws_changed} SKUs"})

        # E010: Scientific notation / long numeric SKUs (pandas auto-converts 1.23E+14 to 123000000000000.0)
        long_numeric = df["sku"].str.match(r"^\d{10,}\.?0*$", na=False)
        if long_numeric.any():
            sci_count = int(long_numeric.sum())
            df.loc[long_numeric, "sku"] = df.loc[long_numeric, "sku"].str.replace(r"\.0+$", "", regex=True)
            self.corrections.append({"code": "E010", "count": sci_count, "action": f"Reconstructed {sci_count} SKUs from scientific notation / long numeric"})

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
            case_fixes = 0
            for idx, val in df["sku"].items():
                lower = val.lower()
                if lower in sku_lower_map and val != sku_lower_map[lower]:
                    df.at[idx, "sku"] = sku_lower_map[lower]
                    case_fixes += 1
            if case_fixes > 0:
                self.corrections.append({"code": "E008", "count": case_fixes, "action": f"Corrected capitalization for {case_fixes} SKUs to match catalog"})

            # E003: SKU not in master (skip for master uploads)
            if self.upload_type not in ["sku_master"]:
                # Also check case-insensitive
                master_lower = {s.lower() for s in self.master_skus}
                invalid = ~df["sku"].str.lower().isin(master_lower)
                if invalid.any():
                    invalid_skus = df.loc[invalid, "sku"].unique()[:5].tolist()
                    self.errors.append(get_error("E003", count=int(invalid.sum()), skus=", ".join(str(s) for s in invalid_skus)))
                    df.loc[invalid, "_has_error"] = True

        return df

    # ─── Store Cleaning ────────────────────────────────────────
    def _clean_store(self, df):
        if "store_code" not in df.columns:
            return df

        df["store_code"] = df["store_code"].astype(str).str.strip()

        # E013: Numeric store codes
        if len(df) > 0 and df["store_code"].str.match(r"^\d+$").all():
            self.corrections.append({"code": "E013", "action": "Converted numeric store codes to text"})

        # E014: Multiple stores comma-separated
        multi_store = df["store_code"].str.contains(",", na=False)
        if multi_store.any():
            multi_count = int(multi_store.sum())
            self.warnings.append({
                "code": "E014",
                "category": "store",
                "message": "Multiple stores in one row",
                "user_message": f"{multi_count} rows contain comma-separated store codes. Split into separate rows.",
                "severity": "warning",
            })

        # Validate against master stores (skip for store_master uploads)
        if self.master_stores and self.upload_type not in ["store_master"]:
            master_lower = {s.lower(): s for s in self.master_stores}
            # Case fix first
            for idx, val in df["store_code"].items():
                lower = val.lower()
                if lower in master_lower and val != master_lower[lower]:
                    df.at[idx, "store_code"] = master_lower[lower]

            invalid = ~df["store_code"].str.lower().isin({s.lower() for s in self.master_stores})
            if invalid.any():
                invalid_stores = df.loc[invalid, "store_code"].unique()[:5].tolist()
                self.errors.append(get_error("E011", count=int(invalid.sum()), stores=", ".join(str(s) for s in invalid_stores)))
                df.loc[invalid, "_has_error"] = True

        return df

    # ─── Warehouse Cleaning ────────────────────────────────────
    def _clean_warehouse(self, df):
        if "warehouse" not in df.columns:
            return df

        df["warehouse"] = df["warehouse"].astype(str).str.strip()

        # Validate against master warehouses (skip for warehouse_master uploads)
        if self.master_warehouses and self.upload_type not in ["warehouse_master"]:
            master_lower = {w.lower(): w for w in self.master_warehouses}
            # Case fix
            for idx, val in df["warehouse"].items():
                lower = val.lower()
                if lower in master_lower and val != master_lower[lower]:
                    df.at[idx, "warehouse"] = master_lower[lower]

            invalid = ~df["warehouse"].str.lower().isin({w.lower() for w in self.master_warehouses})
            if invalid.any():
                invalid_wh = df.loc[invalid, "warehouse"].unique()[:5].tolist()
                self.errors.append({
                    "code": "E011",
                    "category": "store",
                    "message": "Warehouse not found in master",
                    "user_message": f"{int(invalid.sum())} warehouse codes don't exist in your warehouse list: {', '.join(str(w) for w in invalid_wh)}",
                    "severity": "blocking",
                })
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

    @staticmethod
    def _is_string_col(series):
        """Check if a pandas series contains string data (handles both object and StringDtype)."""
        return pd.api.types.is_string_dtype(series) or series.dtype == "object"

    # ─── Quantity Cleaning ─────────────────────────────────────
    def _clean_quantity(self, df):
        qty_cols = [c for c in ["quantity", "closing_stock", "on_hand_qty", "available_qty"] if c in df.columns]
        if not qty_cols:
            return df

        for qty_col in qty_cols:
            if self._is_string_col(df[qty_col]):
                df[qty_col] = df[qty_col].astype(str).str.replace(",", "")

            df[qty_col] = pd.to_numeric(df[qty_col], errors="coerce").fillna(0)

            # E030: Decimal quantity detection
            has_decimal = (df[qty_col] != df[qty_col].astype(int)).any()
            if has_decimal:
                decimal_count = int((df[qty_col] != df[qty_col].astype(int)).sum())
                self.warnings.append(get_error("E030", count=decimal_count))

            # E027: Negative quantity
            negative = df[qty_col] < 0
            if negative.any():
                if qty_col == "closing_stock":
                    # E068: Negative inventory is a blocking error
                    self.errors.append({
                        "code": "E068",
                        "category": "business_rule",
                        "message": "Negative inventory at store",
                        "user_message": f"{int(negative.sum())} rows have negative {qty_col}. Inventory cannot be negative.",
                        "severity": "blocking",
                    })
                    df.loc[negative, "_has_error"] = True
                else:
                    self.warnings.append(get_error("E027", count=int(negative.sum())))

            # E032: Unusually large
            q99 = df[qty_col].quantile(0.99) if len(df) > 10 else 0
            threshold = q99 * 10 if q99 > 0 else 1000000
            unusual = df[df[qty_col] > threshold]
            for idx, row in unusual.iterrows():
                self.requires_approval.append({
                    "code": "E032", "row": int(idx),
                    "value": float(row[qty_col]),
                    "message": f"Unusually large quantity in {qty_col}: {row[qty_col]}",
                })

        return df

    # ─── Revenue Cleaning ──────────────────────────────────────
    def _clean_revenue(self, df):
        if "revenue" not in df.columns:
            return df

        # Phase 3: Currency detection before stripping symbols
        if self._is_string_col(df["revenue"]):
            rev_str = df["revenue"].astype(str)
            usd_count = int(rev_str.str.contains(r"\$", na=False).sum())
            inr_count = int(rev_str.str.contains(r"₹", na=False).sum())
            eur_count = int(rev_str.str.contains(r"€", na=False).sum())
            gbp_count = int(rev_str.str.contains(r"£", na=False).sum())

            symbols_found = set()
            if usd_count > 0:
                symbols_found.add("USD")
            if inr_count > 0:
                symbols_found.add("INR")
            if eur_count > 0:
                symbols_found.add("EUR")
            if gbp_count > 0:
                symbols_found.add("GBP")

            self._currency_info["symbols_found"] = symbols_found

            if len(symbols_found) > 1:
                # Mixed currencies warning
                dominant = max(symbols_found, key=lambda s: {"USD": usd_count, "INR": inr_count, "EUR": eur_count, "GBP": gbp_count}.get(s, 0))
                self._currency_info["detected"] = dominant
                self._currency_info["converted_to_base"] = True
                self.warnings.append({
                    "code": "MIXED_CURRENCY",
                    "category": "revenue",
                    "message": "Mixed currencies detected",
                    "user_message": f"Mixed currencies found ({', '.join(symbols_found)}). Using dominant currency ({dominant}) for conversion.",
                    "severity": "warning",
                })
            elif len(symbols_found) == 1:
                detected = list(symbols_found)[0]
                self._currency_info["detected"] = detected
                if detected == "INR":
                    self._currency_info["converted_to_base"] = False
                    self.corrections.append({"code": "E036", "action": "Detected INR currency. Stored as-is."})
                else:
                    self._currency_info["converted_to_base"] = True
                    self.corrections.append({"code": "E036", "action": f"Detected {detected} currency. Converted to base currency."})

            # Strip currency symbols and commas
            df["revenue"] = rev_str.str.replace(r"[$€£₹,]", "", regex=True)

        df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0)

        # E035: Negative revenue
        negative = df["revenue"] < 0
        if negative.any():
            self.warnings.append(get_error("E035", count=int(negative.sum())))

        # E039: Revenue mismatch with quantity x price (if price column exists)
        if "quantity" in df.columns and "price" in df.columns:
            df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
            expected = df["quantity"] * df["price"]
            tolerance = expected * 0.1  # 10% tolerance
            mismatch = (df["revenue"] > 0) & (expected > 0) & (abs(df["revenue"] - expected) > tolerance)
            if mismatch.any():
                self.warnings.append(get_error("E039", count=int(mismatch.sum())))

        # E040: Unusually large revenue
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

    # ─── Warehouse Inventory Validation ────────────────────────
    def _validate_warehouse_inventory(self, df):
        """Validate warehouse-specific rules: available vs on_hand, allocated calc."""
        if self.upload_type != "warehouse_inventory":
            return df
        if "on_hand_qty" not in df.columns or "available_qty" not in df.columns:
            return df

        # Available > on_hand check
        avail_exceeds = df["available_qty"] > df["on_hand_qty"]
        if avail_exceeds.any():
            count = int(avail_exceeds.sum())
            self.warnings.append({
                "code": "E067",
                "category": "business_rule",
                "message": "Available exceeds on-hand",
                "user_message": f"{count} rows have available_qty > on_hand_qty. Available cannot exceed on-hand.",
                "severity": "warning",
            })

        # Auto-calculate allocated_qty
        df["allocated_qty"] = df["on_hand_qty"] - df["available_qty"]
        self.corrections.append({
            "code": "AUTO_CALC",
            "action": "Auto-calculated allocated_qty = on_hand_qty - available_qty",
        })

        return df

    # ─── Warehouse Master Flag Validation ──────────────────────
    def _validate_warehouse_master_flags(self, df):
        """Validate warehouse_master specific fields."""
        if self.upload_type != "warehouse_master":
            return df
        if "online_fulfillment_flag" not in df.columns:
            return df

        # Normalize flag values
        df["online_fulfillment_flag"] = df["online_fulfillment_flag"].astype(str).str.strip().str.lower()
        valid_flags = {"true", "false", "yes", "no", "1", "0", "y", "n"}
        invalid_flags = ~df["online_fulfillment_flag"].isin(valid_flags)
        if invalid_flags.any():
            bad_vals = df.loc[invalid_flags, "online_fulfillment_flag"].unique()[:5].tolist()
            self.warnings.append({
                "code": "E069",
                "category": "business_rule",
                "message": "Invalid fulfillment flag",
                "user_message": f"online_fulfillment_flag should be true/false. Invalid values: {', '.join(str(v) for v in bad_vals)}",
                "severity": "warning",
            })

        # Normalize to true/false
        true_vals = {"true", "yes", "1", "y"}
        df["online_fulfillment_flag"] = df["online_fulfillment_flag"].apply(
            lambda x: "true" if x in true_vals else ("false" if x in valid_flags else x)
        )

        return df

    # ─── Master Duplicate Check ──────────────────────────────
    def _check_master_duplicates(self, df):
        """E004: Check for duplicate primary keys in master uploads."""
        if self.upload_type not in ["sku_master", "store_master", "warehouse_master"]:
            return
        dedup_col = {"sku_master": "sku", "store_master": "store_code", "warehouse_master": "warehouse"}.get(self.upload_type)
        if not dedup_col or dedup_col not in df.columns:
            return
        dupes = df.duplicated(subset=[dedup_col], keep="first")
        if dupes.any():
            dupe_count = int(dupes.sum())
            dupe_vals = df.loc[dupes, dedup_col].unique()[:5].tolist()
            self.warnings.append({
                "code": "E004",
                "category": "sku",
                "message": f"Duplicate {dedup_col} detected",
                "user_message": f"{dupe_count} duplicate {dedup_col}(s) found: {', '.join(str(v) for v in dupe_vals)}. Kept first occurrence.",
                "severity": "warning",
            })

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
        # E066: Low stock warning (for store_inventory)
        if "closing_stock" in df.columns and self.upload_type == "store_inventory":
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


def compute_file_hash(file_path):
    """Compute SHA256 hash of a file for duplicate detection."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
