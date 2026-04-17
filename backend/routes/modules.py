"""
Tenant Admin - Module Configuration API
Enables tenant admins to manage module access, features, and usage for their organization.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
import uuid

router = APIRouter(prefix="/tenant-admin/modules", tags=["tenant-admin-modules"])

_get_current_user = None
_get_shared_db = None
_tenant_context = None

logger = logging.getLogger(__name__)


def init_modules(get_current_user_func, get_shared_db_func, tenant_context_var):
    global _get_current_user, _get_shared_db, _tenant_context
    _get_current_user = get_current_user_func
    _get_shared_db = get_shared_db_func
    _tenant_context = tenant_context_var


async def _dep_user(request: Request) -> dict:
    return await _get_current_user(request)


def _shared():
    return _get_shared_db()


def _get_tenant_id(user: dict) -> str:
    ctx = _tenant_context.get()
    if ctx:
        return ctx.tenant_id
    return user.get("tenant_id", "")


# ── Models ──

class ModuleToggleRequest(BaseModel):
    enabled: bool


class FeatureToggleRequest(BaseModel):
    feature_id: str
    enabled: bool


# ── Helpers ──

async def _get_tenant_doc(tenant_id: str) -> dict:
    shared = _shared()
    tenant = await shared.tenants.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(404, f"Tenant '{tenant_id}' not found")
    return tenant


async def _audit_log(tenant_id: str, actor_email: str, entity_type: str,
                     entity_id: str, action: str, new_value: dict = None):
    shared = _shared()
    await shared.audit_logs.insert_one({
        "audit_id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "new_value": new_value or {},
        "actor_email": actor_email,
        "source": "module_config",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ── Endpoints ──

@router.get("")
async def get_modules(user: dict = Depends(_dep_user)):
    """Get all modules with their enabled status and features for this tenant."""
    tenant_id = _get_tenant_id(user)
    if not tenant_id:
        raise HTTPException(400, "Tenant context required")

    shared = _shared()

    # Get module definitions
    module_defs = await shared.module_definitions.find(
        {}, {"_id": 0}
    ).sort("order", 1).to_list(100)

    # Get tenant's module configuration
    tenant = await _get_tenant_doc(tenant_id)
    tenant_modules = tenant.get("modules", {})

    modules = []
    for md in module_defs:
        mid = md["module_id"]
        tenant_cfg = tenant_modules.get(mid, {})

        # Count users with access to this module
        user_count = 0
        try:
            mappings = await shared.user_tenants.find(
                {"tenant_id": tenant_id, "is_active": True}
            ).to_list(500)
            emails = [m["email"] for m in mappings]
            if emails:
                user_count = await shared.users.count_documents({
                    "email": {"$in": emails},
                    f"module_access.{mid}.access": {"$ne": "none"}
                })
        except Exception:
            pass

        modules.append({
            "module_id": mid,
            "module_name": md["module_name"],
            "description": md["description"],
            "category": md["category"],
            "icon": md.get("icon", "Settings"),
            "is_core": md.get("is_core", False),
            "is_paid": md.get("is_paid", False),
            "order": md.get("order", 999),
            "enabled": tenant_cfg.get("enabled", md.get("is_core", False)),
            "features": [
                {
                    "feature_id": f["feature_id"],
                    "name": f["name"],
                    "description": f["description"],
                    "is_core": f.get("is_core", False),
                    "enabled": f["feature_id"] in tenant_cfg.get("features", []),
                }
                for f in md.get("features", [])
            ],
            "usage_stats": {
                "active_users": user_count,
            },
        })

    return {"success": True, "modules": modules}


@router.put("/{module_id}/toggle")
async def toggle_module(module_id: str, body: ModuleToggleRequest,
                        user: dict = Depends(_dep_user)):
    """Enable or disable a module for the entire tenant."""
    tenant_id = _get_tenant_id(user)
    if not tenant_id:
        raise HTTPException(400, "Tenant context required")

    # Only admins can toggle modules
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(403, "Only admins can toggle modules")

    shared = _shared()

    # Validate module exists
    md = await shared.module_definitions.find_one({"module_id": module_id}, {"_id": 0})
    if not md:
        raise HTTPException(404, f"Module '{module_id}' not found")

    # Core modules cannot be disabled
    if md.get("is_core") and not body.enabled:
        raise HTTPException(400, f"Module '{md['module_name']}' is a core module and cannot be disabled")

    # Get current tenant config
    tenant = await _get_tenant_doc(tenant_id)
    current_modules = tenant.get("modules", {})
    current_cfg = current_modules.get(module_id, {})

    # If enabling, auto-enable core features
    features = current_cfg.get("features", [])
    if body.enabled and not features:
        features = [f["feature_id"] for f in md.get("features", []) if f.get("is_core")]

    await shared.tenants.update_one(
        {"tenant_id": tenant_id},
        {"$set": {
            f"modules.{module_id}": {
                "enabled": body.enabled,
                "features": features,
            },
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }}
    )

    await _audit_log(tenant_id, user.get("email", ""), "module", module_id,
                     "enabled" if body.enabled else "disabled",
                     {"enabled": body.enabled})

    return {
        "success": True,
        "message": f"Module '{md['module_name']}' {'enabled' if body.enabled else 'disabled'} successfully",
    }


@router.put("/{module_id}/features/{feature_id}/toggle")
async def toggle_feature(module_id: str, feature_id: str, body: FeatureToggleRequest,
                         user: dict = Depends(_dep_user)):
    """Enable or disable a specific feature within a module."""
    tenant_id = _get_tenant_id(user)
    if not tenant_id:
        raise HTTPException(400, "Tenant context required")

    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(403, "Only admins can toggle features")

    shared = _shared()

    # Validate module + feature
    md = await shared.module_definitions.find_one({"module_id": module_id}, {"_id": 0})
    if not md:
        raise HTTPException(404, f"Module '{module_id}' not found")

    feature_def = next((f for f in md.get("features", []) if f["feature_id"] == feature_id), None)
    if not feature_def:
        raise HTTPException(404, f"Feature '{feature_id}' not found in module '{module_id}'")

    # Core features cannot be disabled
    if feature_def.get("is_core") and not body.enabled:
        raise HTTPException(400, f"Feature '{feature_def['name']}' is a core feature and cannot be disabled")

    # Get current config
    tenant = await _get_tenant_doc(tenant_id)
    current_modules = tenant.get("modules", {})
    current_cfg = current_modules.get(module_id, {"enabled": True, "features": []})
    features = list(current_cfg.get("features", []))

    if body.enabled and feature_id not in features:
        features.append(feature_id)
    elif not body.enabled and feature_id in features:
        features.remove(feature_id)

    await shared.tenants.update_one(
        {"tenant_id": tenant_id},
        {"$set": {
            f"modules.{module_id}.features": features,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }}
    )

    await _audit_log(tenant_id, user.get("email", ""), "feature",
                     f"{module_id}.{feature_id}",
                     "enabled" if body.enabled else "disabled",
                     {"enabled": body.enabled})

    return {
        "success": True,
        "message": f"Feature '{feature_def['name']}' {'enabled' if body.enabled else 'disabled'} successfully",
    }


@router.get("/usage")
async def get_module_usage(user: dict = Depends(_dep_user)):
    """Get module usage statistics and resource limits."""
    tenant_id = _get_tenant_id(user)
    if not tenant_id:
        raise HTTPException(400, "Tenant context required")

    shared = _shared()
    tenant = await _get_tenant_doc(tenant_id)

    limits = tenant.get("limits", {})
    usage = tenant.get("usage", {})
    subscription = tenant.get("subscription", {})

    # Convert datetime fields to ISO strings for JSON serialization
    for key in ("start_date", "end_date"):
        if key in subscription and hasattr(subscription[key], "isoformat"):
            subscription[key] = subscription[key].isoformat()
    if "last_updated" in usage and hasattr(usage["last_updated"], "isoformat"):
        usage["last_updated"] = usage["last_updated"].isoformat()

    # Count active users for this tenant
    mappings = await shared.user_tenants.find(
        {"tenant_id": tenant_id, "is_active": True}
    ).to_list(500)
    usage["current_users"] = len(mappings)

    return {
        "success": True,
        "limits": limits,
        "current_usage": usage,
        "subscription": subscription,
    }
