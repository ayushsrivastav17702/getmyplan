"""
Onboarding Wizard Routes — 4-step data-driven setup:
  Step 1: Load Sample Data (or skip)
  Step 2: Master Data (SKU, Store, Style, Warehouse)
  Step 3: Transactional Data (Sales, Inventory, COGS, Orders)
  Step 4: Explore Dashboard
"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["onboarding"])

_client = None
_get_db = None
_get_current_user = None


def init_onboarding(mongo_client, get_db_func, get_current_user_func=None):
    global _client, _get_db, _get_current_user
    _client = mongo_client
    _get_db = get_db_func
    _get_current_user = get_current_user_func


async def _auth(request: Request):
    if _get_current_user:
        return await _get_current_user(request)
    return {}


async def _collection_count(db, name):
    """Count docs in a V2 collection, fallback to V1 uploaded_files."""
    count = await db[name].count_documents({})
    if count == 0:
        v1 = await db.uploaded_files.find_one({"file_type": name}, {"_id": 0, "data": 0})
        if v1:
            count = v1.get("row_count", 1)
    return count


@router.get("/onboarding/status")
async def get_onboarding_status(request: Request):
    user = await _auth(request)
    tenant_id = user.get("tenant_id", "")
    db = _get_db()

    # Check master data collections
    sku_count = await _collection_count(db, "sku_ean_master")
    store_count = await _collection_count(db, "store_master")
    style_count = await _collection_count(db, "style_master")
    wh_count = await _collection_count(db, "warehouse_master")

    # Check transactional data collections
    sales_count = await _collection_count(db, "daily_sales")
    inv_count = await _collection_count(db, "store_inventory")
    cogs_count = await _collection_count(db, "cogs")
    orders_count = await _collection_count(db, "open_orders")

    # Data days for sales
    sales_days = 0
    try:
        days_list = await db.daily_sales.distinct("day")
        if not days_list:
            v1 = await db.uploaded_files.find_one({"file_type": "daily_sales"}, {"_id": 0, "data": 1})
            if v1 and "data" in v1:
                day_set = set()
                for r in v1["data"]:
                    d = r.get("day") or r.get("date")
                    if d:
                        day_set.add(str(d))
                sales_days = len(day_set)
        else:
            sales_days = len(days_list)
    except Exception:
        pass

    # Step completion logic
    #
    # NB: we intentionally ignore system-seeded demo data when deciding if a
    # tenant is "really" onboarded. Demo data is marked with
    # `uploaded_by = 'system'` in upload_history; a tenant is only considered
    # onboarded once at least one *human* upload has landed. This keeps the
    # `/onboarding` wizard from being skipped for brand-new tenants that
    # received sample data via `_ensure_default_tenant()`.
    try:
        real_uploads_count = await db.upload_history.count_documents({
            "tenant_id": tenant_id,
            "uploaded_by": {"$nin": [None, "", "system"]},
        })
    except Exception:
        real_uploads_count = 0
    has_real_uploads = real_uploads_count > 0

    has_any_data = (sku_count + store_count + sales_count + inv_count) > 0
    master_complete = sku_count > 0 and store_count > 0
    master_all = sku_count > 0 and store_count > 0 and style_count > 0 and wh_count > 0
    transactional_has_sales = sales_count > 0
    # "all_ready" = data exists AND a real user has uploaded at least once.
    all_ready = master_complete and transactional_has_sales and has_real_uploads

    master_uploaded = sum(1 for c in [sku_count, store_count, style_count, wh_count] if c > 0)
    trans_uploaded = sum(1 for c in [sales_count, inv_count, cogs_count, orders_count] if c > 0)

    # Determine current step
    if not has_any_data:
        current_step = 1
    elif not master_complete:
        current_step = 2
    elif not transactional_has_sales:
        current_step = 3
    else:
        current_step = 4

    steps_done = sum([has_any_data, master_complete, transactional_has_sales, all_ready])

    return {
        "tenant_id": tenant_id,
        "is_onboarded": all_ready,
        "current_step": current_step,
        "progress_percentage": int((steps_done / 4) * 100),
        "sample_data_loaded": has_any_data,
        # True when data exists in collections (seeded or uploaded).
        # False when the workspace is literally empty.
        "has_data": has_any_data,
        # True only when a real user (not "system") has uploaded at least once.
        # Used by the dashboard to decide whether to show the "demo data" banner.
        "has_real_uploads": has_real_uploads,
        "real_uploads_count": real_uploads_count,
        "master_data": {
            "sku_master": {"uploaded": sku_count > 0, "count": sku_count},
            "store_master": {"uploaded": store_count > 0, "count": store_count},
            "style_master": {"uploaded": style_count > 0, "count": style_count},
            "warehouse_master": {"uploaded": wh_count > 0, "count": wh_count},
            "total_uploaded": master_uploaded,
            "complete": master_complete,
            "all_complete": master_all,
        },
        "transactional_data": {
            "daily_sales": {"uploaded": sales_count > 0, "count": sales_count, "days": sales_days},
            "store_inventory": {"uploaded": inv_count > 0, "count": inv_count},
            "cogs": {"uploaded": cogs_count > 0, "count": cogs_count},
            "open_orders": {"uploaded": orders_count > 0, "count": orders_count},
            "total_uploaded": trans_uploaded,
            "complete": transactional_has_sales,
        },
    }


@router.post("/onboarding/skip")
async def skip_onboarding(request: Request):
    user = await _auth(request)
    tenant_id = user.get("tenant_id", "")
    db = _get_db()
    await db.onboarding_status.update_one(
        {"tenant_id": tenant_id},
        {"$set": {
            "tenant_id": tenant_id,
            "is_onboarded": True,
            "skipped": True,
            "skipped_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )
    return {"success": True, "message": "Onboarding skipped"}


@router.post("/onboarding/complete")
async def complete_onboarding(request: Request):
    user = await _auth(request)
    tenant_id = user.get("tenant_id", "")
    db = _get_db()
    await db.onboarding_status.update_one(
        {"tenant_id": tenant_id},
        {"$set": {
            "tenant_id": tenant_id,
            "is_onboarded": True,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )
    return {"success": True, "message": "Onboarding complete!"}


@router.post("/onboarding/reset")
async def reset_onboarding(request: Request):
    user = await _auth(request)
    tenant_id = user.get("tenant_id", "")
    db = _get_db()
    await db.onboarding_status.delete_many({"tenant_id": tenant_id})
    return {"success": True, "message": "Onboarding reset"}
