"""
Onboarding Wizard Routes — 3-step setup: Marketplaces → Stores → Categories.
Uses the same init_* dependency-injection pattern as other route modules.
"""
from fastapi import APIRouter, HTTPException, Query, Body, Request
from typing import List, Optional
from datetime import datetime, timezone
import logging

from models.onboarding_models import Marketplace, StoreMapping, CategoryNode

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
    """Authenticate the request and return the user dict."""
    if _get_current_user:
        return await _get_current_user(request)
    return {}


async def _update_status(db, tenant_id: str):
    """Recalculate and persist onboarding status from live collection counts."""
    mp_count = await db.ob_marketplaces.count_documents({"is_active": True})
    st_count = await db.ob_stores.count_documents({"is_active": True})
    cat_count = await db.ob_categories.count_documents({"is_active": True})

    await db.onboarding_status.update_one(
        {"tenant_id": tenant_id},
        {"$set": {
            "tenant_id": tenant_id,
            "step_1_marketplaces_complete": mp_count >= 1,
            "step_1_marketplaces_count": mp_count,
            "step_2_stores_complete": st_count >= 1,
            "step_2_stores_count": st_count,
            "step_3_taxonomy_complete": cat_count >= 3,
            "step_3_categories_count": cat_count,
            "last_activity": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )


# ═══════════════════════════════════════════════════════════════
# STEP 1 — MARKETPLACES
# ═══════════════════════════════════════════════════════════════

@router.post("/onboarding/marketplaces")
async def add_marketplace(marketplace: Marketplace, request: Request):
    user = await _auth(request)
    tenant_id = user.get("tenant_id", "demo")
    db = _get_db()

    if not marketplace.marketplace_id:
        marketplace.marketplace_id = marketplace.name.lower().replace(" ", "_").replace("-", "_")

    existing = await db.ob_marketplaces.find_one({"marketplace_id": marketplace.marketplace_id})
    if existing:
        raise HTTPException(400, "Marketplace already exists")

    doc = marketplace.dict()
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.ob_marketplaces.insert_one(doc)
    await _update_status(db, tenant_id)

    return {"success": True, "message": f"Marketplace {marketplace.name} added", "marketplace_id": marketplace.marketplace_id}


@router.get("/onboarding/marketplaces")
async def get_marketplaces(request: Request):
    await _auth(request)
    db = _get_db()
    items = await db.ob_marketplaces.find({"is_active": True}, {"_id": 0}).to_list(200)
    return items


@router.delete("/onboarding/marketplaces/{marketplace_id}")
async def delete_marketplace(marketplace_id: str, request: Request):
    user = await _auth(request)
    db = _get_db()
    result = await db.ob_marketplaces.delete_one({"marketplace_id": marketplace_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Marketplace not found")
    await _update_status(db, user.get("tenant_id", "demo"))
    return {"success": True, "message": "Marketplace deleted"}


# ═══════════════════════════════════════════════════════════════
# STEP 2 — STORES
# ═══════════════════════════════════════════════════════════════

@router.post("/onboarding/stores")
async def add_store(store: StoreMapping, request: Request):
    user = await _auth(request)
    db = _get_db()

    existing = await db.ob_stores.find_one({"store_code": store.store_code})
    if existing:
        raise HTTPException(400, "Store code already exists")

    doc = store.dict()
    doc["location"] = f"{store.city}, {store.state}"
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.ob_stores.insert_one(doc)
    await _update_status(db, user.get("tenant_id", "demo"))

    return {"success": True, "message": f"Store {store.store_name} added"}


@router.get("/onboarding/stores")
async def get_stores(request: Request):
    await _auth(request)
    db = _get_db()
    items = await db.ob_stores.find({"is_active": True}, {"_id": 0}).to_list(500)
    return items


@router.put("/onboarding/stores/{store_code}/marketplaces")
async def update_store_marketplaces(store_code: str, request: Request, marketplaces: List[str] = Body(...)):
    await _auth(request)
    db = _get_db()
    result = await db.ob_stores.update_one(
        {"store_code": store_code},
        {"$set": {"marketplaces": marketplaces, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Store not found")
    return {"success": True, "message": f"Store {store_code} marketplaces updated"}


@router.delete("/onboarding/stores/{store_code}")
async def delete_store(store_code: str, request: Request):
    user = await _auth(request)
    db = _get_db()
    result = await db.ob_stores.delete_one({"store_code": store_code})
    if result.deleted_count == 0:
        raise HTTPException(404, "Store not found")
    await _update_status(db, user.get("tenant_id", "demo"))
    return {"success": True, "message": "Store deleted"}


# ═══════════════════════════════════════════════════════════════
# STEP 3 — CATEGORY TAXONOMY
# ═══════════════════════════════════════════════════════════════

@router.post("/onboarding/categories")
async def add_category(category: CategoryNode, request: Request):
    user = await _auth(request)
    db = _get_db()

    if not category.category_id:
        category.category_id = category.name.lower().replace(" ", "_").replace("-", "_")

    existing = await db.ob_categories.find_one({"category_id": category.category_id})
    if existing:
        raise HTTPException(400, "Category already exists")

    if category.parent_id:
        parent = await db.ob_categories.find_one({"category_id": category.parent_id})
        if not parent:
            raise HTTPException(400, "Parent category not found")
        category.level = parent.get("level", 0) + 1

    doc = category.dict()
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.ob_categories.insert_one(doc)
    await _update_status(db, user.get("tenant_id", "demo"))

    return {"success": True, "message": f"Category {category.name} added", "category_id": category.category_id}


@router.get("/onboarding/categories/tree")
async def get_category_tree(request: Request):
    await _auth(request)
    db = _get_db()
    cats = await db.ob_categories.find({"is_active": True}, {"_id": 0}).to_list(500)

    cat_map = {c["category_id"]: c for c in cats}
    roots = []
    for cat in cats:
        pid = cat.get("parent_id")
        if pid and pid in cat_map:
            parent = cat_map[pid]
            parent.setdefault("children", []).append(cat)
        else:
            roots.append(cat)
    return roots


@router.delete("/onboarding/categories/{category_id}")
async def delete_category(category_id: str, request: Request):
    user = await _auth(request)
    db = _get_db()

    # Collect IDs to delete (the target + descendants)
    to_delete = [category_id]
    all_cats = await db.ob_categories.find({}, {"_id": 0, "category_id": 1, "parent_id": 1}).to_list(500)
    changed = True
    while changed:
        changed = False
        for c in all_cats:
            if c.get("parent_id") in to_delete and c["category_id"] not in to_delete:
                to_delete.append(c["category_id"])
                changed = True

    result = await db.ob_categories.delete_many({"category_id": {"$in": to_delete}})
    if result.deleted_count == 0:
        raise HTTPException(404, "Category not found")
    await _update_status(db, user.get("tenant_id", "demo"))
    return {"success": True, "message": f"Deleted {result.deleted_count} categories"}


# ═══════════════════════════════════════════════════════════════
# ONBOARDING STATUS
# ═══════════════════════════════════════════════════════════════

@router.get("/onboarding/status")
async def get_onboarding_status(request: Request):
    user = await _auth(request)
    tenant_id = user.get("tenant_id", "demo")
    db = _get_db()

    # Auto-onboard existing tenants that already have uploaded data
    status = await db.onboarding_status.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not status:
        has_data = await db.uploaded_files.count_documents({}) > 0
        if has_data:
            auto_doc = {
                "tenant_id": tenant_id,
                "step_1_marketplaces_complete": True,
                "step_1_marketplaces_count": 0,
                "step_2_stores_complete": True,
                "step_2_stores_count": 0,
                "step_3_taxonomy_complete": True,
                "step_3_categories_count": 0,
                "step_4_data_upload_complete": True,
                "is_onboarded": True,
                "last_activity": datetime.now(timezone.utc).isoformat(),
            }
            await db.onboarding_status.insert_one(auto_doc)
            auto_doc.pop("_id", None)
            auto_doc["current_step"] = 4
            auto_doc["progress_percentage"] = 100
            return auto_doc
        # Truly new tenant
        return {
            "tenant_id": tenant_id,
            "step_1_marketplaces_complete": False, "step_1_marketplaces_count": 0,
            "step_2_stores_complete": False, "step_2_stores_count": 0,
            "step_3_taxonomy_complete": False, "step_3_categories_count": 0,
            "step_4_data_upload_complete": False,
            "is_onboarded": False, "current_step": 1, "progress_percentage": 0,
        }

    # Calculate derived fields
    steps = sum([
        status.get("step_1_marketplaces_complete", False),
        status.get("step_2_stores_complete", False),
        status.get("step_3_taxonomy_complete", False),
        status.get("step_4_data_upload_complete", False),
    ])
    status["progress_percentage"] = int((steps / 4) * 100)
    if not status.get("step_1_marketplaces_complete"):
        status["current_step"] = 1
    elif not status.get("step_2_stores_complete"):
        status["current_step"] = 2
    elif not status.get("step_3_taxonomy_complete"):
        status["current_step"] = 3
    else:
        status["current_step"] = 4
    return status


@router.post("/onboarding/skip")
async def skip_step(request: Request, step: int = Query(..., ge=1, le=3)):
    user = await _auth(request)
    tenant_id = user.get("tenant_id", "demo")
    db = _get_db()

    field_map = {1: "step_1_marketplaces_complete", 2: "step_2_stores_complete", 3: "step_3_taxonomy_complete"}
    await db.onboarding_status.update_one(
        {"tenant_id": tenant_id},
        {"$set": {field_map[step]: True, "last_activity": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return {"success": True, "message": f"Step {step} skipped"}


@router.post("/onboarding/complete")
async def complete_onboarding(request: Request):
    user = await _auth(request)
    tenant_id = user.get("tenant_id", "demo")
    db = _get_db()

    status = await db.onboarding_status.find_one({"tenant_id": tenant_id})
    if not status:
        raise HTTPException(400, "Start onboarding first")

    missing = []
    if not status.get("step_1_marketplaces_complete"):
        missing.append("Add marketplaces")
    if not status.get("step_2_stores_complete"):
        missing.append("Add stores")
    if not status.get("step_3_taxonomy_complete"):
        missing.append("Build category tree (min 3)")

    if missing:
        raise HTTPException(400, f"Please complete: {', '.join(missing)}")

    await db.onboarding_status.update_one(
        {"tenant_id": tenant_id},
        {"$set": {
            "is_onboarded": True,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
        }},
    )
    return {"success": True, "message": "Onboarding complete! You can now upload data."}


@router.post("/onboarding/reset")
async def reset_onboarding(request: Request):
    user = await _auth(request)
    tenant_id = user.get("tenant_id", "demo")
    db = _get_db()

    await db.ob_marketplaces.delete_many({})
    await db.ob_stores.delete_many({})
    await db.ob_categories.delete_many({})
    await db.onboarding_status.delete_many({"tenant_id": tenant_id})
    return {"success": True, "message": "Onboarding reset"}
