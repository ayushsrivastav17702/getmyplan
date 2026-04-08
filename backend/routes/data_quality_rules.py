"""
Data Quality Rules Engine — tenant-specific custom validation rules.
Supports 6 rule types: threshold, null_check, pattern, uniqueness, cross_reference, range.
Rules are stored per-tenant and evaluated against uploaded data files.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import re
import pandas as pd
import numpy as np
import logging

from multi_tenant.tenant_db import get_mongo_client, tenant_context
from multi_tenant.auth import get_current_user
from multi_tenant.user_routes import require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quality/rules", tags=["Data Quality Rules"])

VALID_FILE_TYPES = ["daily_sales", "store_inventory", "sku_ean_master", "style_master", "store_master"]
VALID_RULE_TYPES = ["threshold", "null_check", "pattern", "uniqueness", "cross_reference", "range"]
VALID_OPERATORS = [">", ">=", "<", "<=", "==", "!="]
VALID_SEVERITIES = ["error", "warning", "info"]


class CreateRuleRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: str = Field("", max_length=500)
    file_type: str
    rule_type: str
    column: str = Field(..., min_length=1)
    operator: Optional[str] = None
    value: Optional[float] = None
    value_str: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    ref_file_type: Optional[str] = None
    ref_column: Optional[str] = None
    severity: str = "warning"
    threshold_pct: float = Field(95.0, ge=0, le=100)
    is_active: bool = True


class UpdateRuleRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[float] = None
    value_str: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    ref_file_type: Optional[str] = None
    ref_column: Optional[str] = None
    severity: Optional[str] = None
    threshold_pct: Optional[float] = None
    is_active: Optional[bool] = None


def _get_tenant_db():
    ctx = tenant_context.get()
    if not ctx:
        raise HTTPException(400, "Tenant context required")
    client = get_mongo_client()
    return client[f"tenant_{ctx.tenant_id}"]


async def _load_file(db, file_type: str) -> Optional[pd.DataFrame]:
    doc = await db.uploaded_files.find_one({"file_type": file_type})
    if doc and "data" in doc:
        return pd.DataFrame(doc["data"])
    return None


def _evaluate_single_rule(rule: dict, primary_df: pd.DataFrame, ref_df: Optional[pd.DataFrame] = None) -> dict:
    """Evaluate a single rule against a dataframe. Returns result dict."""
    col = rule["column"]
    rule_type = rule["rule_type"]
    total = len(primary_df)

    if total == 0:
        return {
            "status": "skip",
            "pass_count": 0, "fail_count": 0, "total": 0,
            "pass_pct": 0, "detail": "No data in file",
        }

    if col not in primary_df.columns:
        return {
            "status": "error",
            "pass_count": 0, "fail_count": total, "total": total,
            "pass_pct": 0, "detail": f"Column '{col}' not found in file",
        }

    try:
        if rule_type == "threshold":
            op = rule.get("operator", ">")
            val = rule.get("value", 0)
            series = pd.to_numeric(primary_df[col], errors="coerce")
            if op == ">":
                passed = series > val
            elif op == ">=":
                passed = series >= val
            elif op == "<":
                passed = series < val
            elif op == "<=":
                passed = series <= val
            elif op == "==":
                passed = series == val
            elif op == "!=":
                passed = series != val
            else:
                passed = pd.Series([True] * total)
            pass_count = int(passed.sum())
            fail_count = total - pass_count
            pass_pct = round(pass_count / total * 100, 1)
            detail = f"{pass_count}/{total} records pass ({col} {op} {val})"

        elif rule_type == "null_check":
            nulls = primary_df[col].isnull() | (primary_df[col].astype(str).str.strip() == "")
            null_count = int(nulls.sum())
            pass_count = total - null_count
            fail_count = null_count
            pass_pct = round(pass_count / total * 100, 1)
            detail = f"{null_count} null/empty values in '{col}' ({round(null_count/total*100, 1)}%)"

        elif rule_type == "pattern":
            pattern = rule.get("value_str", ".*")
            try:
                matched = primary_df[col].astype(str).str.match(pattern, na=False)
            except re.error:
                return {
                    "status": "error", "pass_count": 0, "fail_count": total,
                    "total": total, "pass_pct": 0, "detail": f"Invalid regex pattern: {pattern}",
                }
            pass_count = int(matched.sum())
            fail_count = total - pass_count
            pass_pct = round(pass_count / total * 100, 1)
            samples = primary_df[~matched][col].head(3).tolist() if fail_count > 0 else []
            detail = f"{pass_count}/{total} match pattern '{pattern}'"
            if samples:
                detail += f". Samples not matching: {samples}"

        elif rule_type == "uniqueness":
            dupes = primary_df[col].duplicated(keep=False)
            dupe_count = int(dupes.sum())
            pass_count = total - dupe_count
            fail_count = dupe_count
            pass_pct = round(pass_count / total * 100, 1)
            unique_dupes = int(primary_df[dupes][col].nunique())
            detail = f"{dupe_count} duplicate values across {unique_dupes} distinct values in '{col}'"

        elif rule_type == "cross_reference":
            ref_col = rule.get("ref_column", col)
            if ref_df is None:
                return {
                    "status": "error", "pass_count": 0, "fail_count": total,
                    "total": total, "pass_pct": 0,
                    "detail": f"Reference file '{rule.get('ref_file_type', '?')}' not uploaded",
                }
            if ref_col not in ref_df.columns:
                return {
                    "status": "error", "pass_count": 0, "fail_count": total,
                    "total": total, "pass_pct": 0,
                    "detail": f"Reference column '{ref_col}' not found in reference file",
                }
            ref_values = set(ref_df[ref_col].dropna().astype(str).unique())
            primary_values = primary_df[col].astype(str)
            matched = primary_values.isin(ref_values)
            pass_count = int(matched.sum())
            fail_count = total - pass_count
            pass_pct = round(pass_count / total * 100, 1)
            orphan_count = int((~matched).sum())
            orphan_samples = primary_df[~matched][col].unique()[:5].tolist() if orphan_count > 0 else []
            detail = f"{pass_count}/{total} values found in reference. {orphan_count} orphans"
            if orphan_samples:
                detail += f": {orphan_samples}"

        elif rule_type == "range":
            min_val = rule.get("min_value", float("-inf"))
            max_val = rule.get("max_value", float("inf"))
            series = pd.to_numeric(primary_df[col], errors="coerce")
            in_range = (series >= min_val) & (series <= max_val)
            pass_count = int(in_range.sum())
            fail_count = total - pass_count
            pass_pct = round(pass_count / total * 100, 1)
            detail = f"{pass_count}/{total} values in range [{min_val}, {max_val}]"

        else:
            return {
                "status": "error", "pass_count": 0, "fail_count": total,
                "total": total, "pass_pct": 0, "detail": f"Unknown rule type: {rule_type}",
            }

        threshold = rule.get("threshold_pct", 95)
        status = "pass" if pass_pct >= threshold else "warn" if pass_pct >= threshold * 0.8 else "fail"

        return {
            "status": status,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "total": total,
            "pass_pct": pass_pct,
            "detail": detail,
        }

    except Exception as e:
        logger.error(f"Rule evaluation error: {e}")
        return {
            "status": "error", "pass_count": 0, "fail_count": total,
            "total": total, "pass_pct": 0, "detail": f"Evaluation error: {str(e)}",
        }


# ──────── CRUD Endpoints ────────

@router.get("/")
async def list_rules(current_user: dict = Depends(get_current_user)):
    """List all custom data quality rules for the tenant."""
    tdb = _get_tenant_db()
    rules = await tdb.data_quality_rules.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"rules": rules}


@router.post("/")
async def create_rule(body: CreateRuleRequest, current_user: dict = Depends(require_role(["admin", "super_admin", "merchandiser"]))):
    """Create a new custom data quality rule."""
    if body.file_type not in VALID_FILE_TYPES:
        raise HTTPException(400, f"Invalid file_type. Must be one of: {VALID_FILE_TYPES}")
    if body.rule_type not in VALID_RULE_TYPES:
        raise HTTPException(400, f"Invalid rule_type. Must be one of: {VALID_RULE_TYPES}")
    if body.severity not in VALID_SEVERITIES:
        raise HTTPException(400, f"Invalid severity. Must be one of: {VALID_SEVERITIES}")
    if body.rule_type == "threshold" and body.operator and body.operator not in VALID_OPERATORS:
        raise HTTPException(400, f"Invalid operator. Must be one of: {VALID_OPERATORS}")
    if body.rule_type == "cross_reference" and not body.ref_file_type:
        raise HTTPException(400, "Cross-reference rules require ref_file_type")
    if body.rule_type == "range" and (body.min_value is None or body.max_value is None):
        raise HTTPException(400, "Range rules require both min_value and max_value")

    tdb = _get_tenant_db()
    now = datetime.now(timezone.utc).isoformat()
    rule = {
        "rule_id": str(uuid.uuid4())[:12],
        "name": body.name,
        "description": body.description,
        "file_type": body.file_type,
        "rule_type": body.rule_type,
        "column": body.column,
        "operator": body.operator,
        "value": body.value,
        "value_str": body.value_str,
        "min_value": body.min_value,
        "max_value": body.max_value,
        "ref_file_type": body.ref_file_type,
        "ref_column": body.ref_column,
        "severity": body.severity,
        "threshold_pct": body.threshold_pct,
        "is_active": body.is_active,
        "created_by": current_user["email"],
        "created_at": now,
        "updated_at": now,
        "last_evaluated": None,
        "last_status": None,
    }
    await tdb.data_quality_rules.insert_one(rule)
    rule.pop("_id", None)
    return {"message": "Rule created", "rule": rule}


@router.put("/{rule_id}")
async def update_rule(rule_id: str, body: UpdateRuleRequest, current_user: dict = Depends(require_role(["admin", "super_admin", "merchandiser"]))):
    """Update an existing rule."""
    tdb = _get_tenant_db()
    existing = await tdb.data_quality_rules.find_one({"rule_id": rule_id})
    if not existing:
        raise HTTPException(404, "Rule not found")

    updates = {}
    for field in ["name", "description", "operator", "value", "value_str", "min_value", "max_value",
                   "ref_file_type", "ref_column", "severity", "threshold_pct", "is_active"]:
        val = getattr(body, field)
        if val is not None:
            updates[field] = val

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await tdb.data_quality_rules.update_one({"rule_id": rule_id}, {"$set": updates})
    updated = await tdb.data_quality_rules.find_one({"rule_id": rule_id}, {"_id": 0})
    return {"message": "Rule updated", "rule": updated}


@router.delete("/{rule_id}")
async def delete_rule(rule_id: str, current_user: dict = Depends(require_role(["admin", "super_admin"]))):
    """Delete a rule."""
    tdb = _get_tenant_db()
    result = await tdb.data_quality_rules.delete_one({"rule_id": rule_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Rule not found")
    return {"message": "Rule deleted"}


@router.post("/{rule_id}/toggle")
async def toggle_rule(rule_id: str, current_user: dict = Depends(require_role(["admin", "super_admin", "merchandiser"]))):
    """Toggle a rule's active status."""
    tdb = _get_tenant_db()
    existing = await tdb.data_quality_rules.find_one({"rule_id": rule_id})
    if not existing:
        raise HTTPException(404, "Rule not found")
    new_active = not existing.get("is_active", True)
    await tdb.data_quality_rules.update_one(
        {"rule_id": rule_id},
        {"$set": {"is_active": new_active, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {"message": f"Rule {'activated' if new_active else 'deactivated'}", "is_active": new_active}


# ──────── Evaluation Endpoint ────────

@router.post("/evaluate")
async def evaluate_rules(current_user: dict = Depends(get_current_user)):
    """Evaluate all active custom rules against current data."""
    tdb = _get_tenant_db()
    rules = await tdb.data_quality_rules.find({"is_active": True}, {"_id": 0}).to_list(200)

    if not rules:
        return {"results": [], "summary": {"total": 0, "passed": 0, "warned": 0, "failed": 0, "errors": 0}}

    # Load all file types that rules reference
    file_cache = {}
    needed_files = set()
    for r in rules:
        needed_files.add(r["file_type"])
        if r.get("ref_file_type"):
            needed_files.add(r["ref_file_type"])

    for ft in needed_files:
        file_cache[ft] = await _load_file(tdb, ft)

    results = []
    now = datetime.now(timezone.utc).isoformat()

    for rule in rules:
        primary_df = file_cache.get(rule["file_type"])
        ref_df = file_cache.get(rule.get("ref_file_type")) if rule.get("ref_file_type") else None

        if primary_df is None:
            result = {
                "status": "skip",
                "pass_count": 0, "fail_count": 0, "total": 0,
                "pass_pct": 0, "detail": f"File '{rule['file_type']}' not uploaded",
            }
        else:
            result = _evaluate_single_rule(rule, primary_df, ref_df)

        # Update rule with last evaluation results
        await tdb.data_quality_rules.update_one(
            {"rule_id": rule["rule_id"]},
            {"$set": {"last_evaluated": now, "last_status": result["status"]}},
        )

        results.append({
            "rule_id": rule["rule_id"],
            "name": rule["name"],
            "description": rule.get("description", ""),
            "file_type": rule["file_type"],
            "rule_type": rule["rule_type"],
            "column": rule["column"],
            "severity": rule["severity"],
            "threshold_pct": rule["threshold_pct"],
            **result,
        })

    summary = {
        "total": len(results),
        "passed": sum(1 for r in results if r["status"] == "pass"),
        "warned": sum(1 for r in results if r["status"] == "warn"),
        "failed": sum(1 for r in results if r["status"] == "fail"),
        "errors": sum(1 for r in results if r["status"] in ("error", "skip")),
        "evaluated_at": now,
    }

    return {"results": results, "summary": summary}


@router.get("/file-columns/{file_type}")
async def get_file_columns(file_type: str, current_user: dict = Depends(get_current_user)):
    """Get available columns for a file type (helps rule builder UI)."""
    if file_type not in VALID_FILE_TYPES:
        raise HTTPException(400, f"Invalid file_type")
    tdb = _get_tenant_db()
    df = await _load_file(tdb, file_type)
    if df is None:
        return {"columns": [], "row_count": 0, "message": f"{file_type} not uploaded"}
    return {"columns": list(df.columns), "row_count": len(df)}


def init_data_quality_rules(app):
    """Initialize data quality rules router."""
    pass
