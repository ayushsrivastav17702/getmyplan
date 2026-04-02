"""
RBAC: Role definitions, permission definitions, seeding, and access-control decorators.
All data lives in the merch_shared database.
"""
from fastapi import HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
import logging

from .tenant_db import get_shared_db
from .auth import get_current_user

logger = logging.getLogger(__name__)

# ──────────────── Role & Permission Definitions ────────────────

ROLES = [
    {"role_name": "super_admin",    "display_name": "Super Admin",     "description": "Full platform access",          "priority": 100, "is_system": True},
    {"role_name": "admin",          "display_name": "Tenant Admin",    "description": "Full tenant access",            "priority": 90,  "is_system": True},
    {"role_name": "cxo",            "display_name": "CXO / Executive", "description": "High-level dashboards",         "priority": 80,  "is_system": True},
    {"role_name": "merchandiser",   "display_name": "Merchandiser",    "description": "Product mix, categories",       "priority": 70,  "is_system": True},
    {"role_name": "allocator",      "display_name": "Allocator",       "description": "Stock distribution",            "priority": 65,  "is_system": True},
    {"role_name": "demand_planner", "display_name": "Demand Planner",  "description": "Forecasting & replenishment",   "priority": 60,  "is_system": True},
    {"role_name": "store_manager",  "display_name": "Store Manager",   "description": "Store-level access",            "priority": 40,  "is_system": True},
    {"role_name": "viewer",         "display_name": "Viewer",          "description": "Read-only access to dashboards", "priority": 30,  "is_system": True},
]

PERMISSIONS = [
    # Dashboards
    {"module": "dashboard", "resource": "executive",     "action": "view"},
    {"module": "dashboard", "resource": "bi",            "action": "view"},
    {"module": "dashboard", "resource": "warehouse",     "action": "view"},
    # Analytics
    {"module": "analytics", "resource": "gap",           "action": "view"},
    {"module": "analytics", "resource": "stockout",      "action": "view"},
    {"module": "analytics", "resource": "replenishment", "action": "view"},
    {"module": "analytics", "resource": "doh",           "action": "view"},
    {"module": "analytics", "resource": "planogram",     "action": "view"},
    {"module": "analytics", "resource": "core_logics",   "action": "view"},
    # Data
    {"module": "data", "resource": "upload",    "action": "manage"},
    {"module": "data", "resource": "config",    "action": "manage"},
    {"module": "data", "resource": "export",    "action": "execute"},
    {"module": "data", "resource": "sftp",      "action": "view"},
    {"module": "data", "resource": "quality",   "action": "view"},
    # Users
    {"module": "users", "resource": "list",   "action": "view"},
    {"module": "users", "resource": "invite", "action": "create"},
    {"module": "users", "resource": "roles",  "action": "manage"},
    {"module": "users", "resource": "remove", "action": "delete"},
    # Settings
    {"module": "settings", "resource": "tenant", "action": "view"},
    {"module": "settings", "resource": "tenant", "action": "edit"},
    # Chatbot
    {"module": "chatbot", "resource": "faq", "action": "view"},
]

# role_name → list of "module.resource.action" patterns  (* = wildcard)
ROLE_PERMISSIONS = {
    "super_admin":    ["*"],
    "admin":          ["*"],
    "cxo":            ["dashboard.*.view", "analytics.*.view", "data.export.execute", "chatbot.faq.view"],
    "merchandiser":   ["dashboard.*.view", "analytics.*.view", "data.upload.manage", "data.config.manage", "data.export.execute", "data.sftp.view", "data.quality.view", "chatbot.faq.view"],
    "allocator":      ["dashboard.*.view", "analytics.*.view", "data.upload.manage", "data.export.execute", "chatbot.faq.view"],
    "demand_planner": ["dashboard.*.view", "analytics.replenishment.view", "analytics.doh.view", "analytics.stockout.view", "data.export.execute", "chatbot.faq.view"],
    "store_manager":  ["dashboard.executive.view", "analytics.stockout.view", "analytics.planogram.view", "data.quality.view", "chatbot.faq.view"],
    "viewer":         ["dashboard.*.view", "analytics.*.view", "chatbot.faq.view"],
}


def _perm_key(p: dict) -> str:
    return f"{p['module']}.{p['resource']}.{p['action']}"


def _matches(pattern: str, perm_key: str) -> bool:
    """Check if a wildcard pattern matches a permission key."""
    if pattern == "*":
        return True
    pp = pattern.split(".")
    pk = perm_key.split(".")
    if len(pp) != 3 or len(pk) != 3:
        return pattern == perm_key
    return all(a == "*" or a == b for a, b in zip(pp, pk))


def resolve_permissions(role_name: str) -> List[str]:
    """Return the concrete list of permission keys for a role."""
    patterns = ROLE_PERMISSIONS.get(role_name, [])
    all_keys = [_perm_key(p) for p in PERMISSIONS]
    result = set()
    for pat in patterns:
        for key in all_keys:
            if _matches(pat, key):
                result.add(key)
    return sorted(result)


# ──────────────── Seed function (call at startup) ────────────────

async def seed_rbac():
    """Upsert roles and permissions into merch_shared."""
    shared = get_shared_db()

    for role in ROLES:
        await shared.roles.update_one(
            {"role_name": role["role_name"]},
            {"$set": {**role, "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
    logger.info("Seeded %d roles", len(ROLES))

    for perm in PERMISSIONS:
        await shared.permissions.update_one(
            {"module": perm["module"], "resource": perm["resource"], "action": perm["action"]},
            {"$set": {**perm, "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
    logger.info("Seeded %d permissions", len(PERMISSIONS))


# ──────────────── Access-control dependencies ────────────────

def require_role(allowed_roles: List[str]):
    """FastAPI dependency — verifies the caller has one of the allowed roles."""
    async def _dep(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                403,
                f"Role '{current_user['role']}' not authorised. Required: {', '.join(allowed_roles)}",
            )
        return current_user
    return _dep


def require_permission(module: str, resource: str, action: str):
    """FastAPI dependency — verifies the caller's role grants a specific permission.
    Also checks per-user permission overrides from merch_shared.permission_overrides."""
    needed = f"{module}.{resource}.{action}"

    async def _dep(current_user: dict = Depends(get_current_user)):
        perms = set(resolve_permissions(current_user["role"]))
        # Check custom role permissions from DB
        shared = get_shared_db()
        custom_rp = await shared.role_permissions.find_one({"role_name": current_user["role"]}, {"_id": 0})
        if custom_rp and custom_rp.get("permissions"):
            from .rbac import _matches, PERMISSIONS, _perm_key
            for pat in custom_rp["permissions"]:
                for p in PERMISSIONS:
                    if _matches(pat, _perm_key(p)):
                        perms.add(_perm_key(p))
        # Check per-user overrides
        overrides = await shared.permission_overrides.find_one({
            "email": current_user["email"],
            "tenant_id": current_user.get("tenant_id", "")
        }, {"_id": 0})
        if overrides:
            perms.update(overrides.get("add_permissions", []))
            perms -= set(overrides.get("remove_permissions", []))
        if needed not in perms:
            raise HTTPException(403, f"Permission denied: {needed}")
        return current_user
    return _dep
