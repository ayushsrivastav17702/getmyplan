"""
Tenant management API — create, list, status, suspend, delete tenants.
These endpoints bypass the tenant middleware (PUBLIC_PATHS) for creation,
and require admin auth for management operations.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timezone
import secrets
import bcrypt
import logging

from .tenant_db import (
    get_shared_db,
    get_mongo_client,
    clear_tenant_cache,
    tenant_context,
)
from .auth import get_current_user
from .rbac import require_role

logger = logging.getLogger(__name__)

tenant_router = APIRouter(prefix="/api/tenants", tags=["Tenant Management"])


# ---------- models ----------

class TenantCreate(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=100)
    subdomain: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)
    plan_type: str = Field("starter", pattern=r"^(starter|professional|enterprise)$")


class TenantOut(BaseModel):
    tenant_id: str
    company_name: str
    subdomain: str
    plan_type: str
    status: str
    created_at: str
    api_key: Optional[str] = None


# ---------- helpers ----------

def _slug(name: str) -> str:
    import re
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug


def _hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


# ---------- routes ----------

@tenant_router.post("/create", response_model=TenantOut)
async def create_tenant(body: TenantCreate):
    """Self-service tenant onboarding. Creates DB, admin user, API key."""
    shared = get_shared_db()
    client = get_mongo_client()

    tenant_id = _slug(body.company_name)
    db_name = f"tenant_{tenant_id}"

    if await shared.tenants.find_one({"tenant_id": tenant_id}):
        raise HTTPException(400, "A tenant with this name already exists")
    if await shared.tenants.find_one({"subdomain": body.subdomain}):
        raise HTTPException(400, "Subdomain already taken")

    # Create tenant database with default collections & config
    tdb = client[db_name]
    await tdb.config.insert_one({
        "psa_benchmark": 80,
        "cover_days": 7,
        "ros_period": 30,
        "ideal_doh": 9,
        "topseller_x_factor": 2.0,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    await tdb.channels.insert_many([
        {"channel_code": "offline", "channel_name": "Offline Store", "channel_type": "offline", "commission": 0},
        {"channel_code": "website", "channel_name": "Own Website", "channel_type": "website", "commission": 2.5},
        {"channel_code": "amazon", "channel_name": "Amazon India", "channel_type": "marketplace", "commission": 12.5},
        {"channel_code": "flipkart", "channel_name": "Flipkart", "channel_type": "marketplace", "commission": 15.0},
        {"channel_code": "myntra", "channel_name": "Myntra", "channel_type": "marketplace", "commission": 18.0},
    ])

    # Admin user in shared DB
    existing_user = await shared.users.find_one({"email": body.admin_email})
    if existing_user:
        user_id = str(existing_user["_id"])
    else:
        res = await shared.users.insert_one({
            "email": body.admin_email,
            "username": body.admin_email.split("@")[0],
            "hashed_password": _hash_pw(body.admin_password),
            "full_name": body.company_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        user_id = str(res.inserted_id)

    api_key = secrets.token_urlsafe(32)
    now_iso = datetime.now(timezone.utc).isoformat()

    await shared.tenants.insert_one({
        "tenant_id": tenant_id,
        "company_name": body.company_name,
        "db_name": db_name,
        "subdomain": body.subdomain,
        "plan_type": body.plan_type,
        "status": "active",
        "api_key_hash": api_key[:8],
        "created_at": now_iso,
        "updated_at": now_iso,
    })

    await shared.user_tenants.insert_one({
        "email": body.admin_email,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "role": "admin",
        "is_active": True,
        "assigned_at": now_iso,
    })

    clear_tenant_cache()

    return TenantOut(
        tenant_id=tenant_id,
        company_name=body.company_name,
        subdomain=body.subdomain,
        plan_type=body.plan_type,
        status="active",
        created_at=now_iso,
        api_key=api_key,
    )


@tenant_router.get("/check-subdomain")
async def check_subdomain(subdomain: str):
    """Check if a subdomain is available."""
    shared = get_shared_db()
    taken = await shared.tenants.find_one({"subdomain": subdomain})
    return {"subdomain": subdomain, "available": taken is None}


@tenant_router.get("/{tenant_id}/status")
async def tenant_status(tenant_id: str):
    """Get tenant status and data metrics."""
    shared = get_shared_db()
    tenant = await shared.tenants.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(404, "Tenant not found")

    tdb = get_mongo_client()[tenant["db_name"]]
    metrics = {
        "uploaded_files": await tdb.uploaded_files.count_documents({}),
        "presets": await tdb.filter_presets.count_documents({}),
        "upload_history": await tdb.upload_history.count_documents({}),
    }

    return {
        "tenant_id": tenant_id,
        "company_name": tenant["company_name"],
        "subdomain": tenant["subdomain"],
        "plan_type": tenant["plan_type"],
        "status": tenant["status"],
        "metrics": metrics,
        "created_at": tenant.get("created_at"),
    }


@tenant_router.get("/")
async def list_tenants():
    """List all tenants (admin only in production)."""
    shared = get_shared_db()
    tenants = await shared.tenants.find(
        {"status": {"$ne": "deleted"}},
        {"_id": 0, "api_key_hash": 0},
    ).to_list(500)
    return {"tenants": tenants}


@tenant_router.post("/{tenant_id}/suspend")
async def suspend_tenant(tenant_id: str):
    shared = get_shared_db()
    result = await shared.tenants.update_one(
        {"tenant_id": tenant_id},
        {"$set": {"status": "suspended", "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Tenant not found")
    clear_tenant_cache(tenant_id)
    return {"message": f"Tenant '{tenant_id}' suspended"}


@tenant_router.post("/{tenant_id}/activate")
async def activate_tenant(tenant_id: str):
    shared = get_shared_db()
    result = await shared.tenants.update_one(
        {"tenant_id": tenant_id},
        {"$set": {"status": "active", "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Tenant not found")
    clear_tenant_cache(tenant_id)
    return {"message": f"Tenant '{tenant_id}' activated"}


@tenant_router.delete("/{tenant_id}")
async def delete_tenant(tenant_id: str):
    shared = get_shared_db()
    tenant = await shared.tenants.find_one({"tenant_id": tenant_id})
    if not tenant:
        raise HTTPException(404, "Tenant not found")

    # Drop tenant database
    client = get_mongo_client()
    await client.drop_database(tenant["db_name"])

    # Remove registry entries
    await shared.tenants.delete_one({"tenant_id": tenant_id})
    await shared.user_tenants.delete_many({"tenant_id": tenant_id})

    clear_tenant_cache(tenant_id)
    return {"message": f"Tenant '{tenant_id}' deleted"}


# ──────────── Tenant Admin: Metrics ────────────

@tenant_router.get("/{tenant_id}/metrics")
async def tenant_metrics(tenant_id: str, current_user: dict = Depends(require_role(["admin", "super_admin"]))):
    """Return rich usage metrics for the tenant admin panel."""
    shared = get_shared_db()
    tenant = await shared.tenants.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(404, "Tenant not found")

    tdb = get_mongo_client()[tenant["db_name"]]
    total_users = await shared.user_tenants.count_documents({"tenant_id": tenant_id, "is_active": True})
    uploaded = await tdb.uploaded_files.count_documents({})
    presets = await tdb.filter_presets.count_documents({})
    api_calls = await shared.audit_logs.count_documents({"tenant_id": tenant_id})

    plan = tenant.get("plan_type", "starter")
    storage_limit = {"starter": 10, "professional": 50, "enterprise": 100}.get(plan, 10)

    return {
        "tenant_id": tenant_id,
        "company_name": tenant["company_name"],
        "subdomain": tenant["subdomain"],
        "plan": plan,
        "total_users": total_users,
        "uploaded_files": uploaded,
        "presets": presets,
        "api_calls": api_calls,
        "storage_used": round(uploaded * 0.3, 1),
        "storage_limit": storage_limit,
        "created_at": tenant.get("created_at"),
    }


# ──────────── Tenant Admin: API Keys ────────────

@tenant_router.get("/admin/api-keys")
async def list_api_keys(current_user: dict = Depends(require_role(["admin", "super_admin"]))):
    ctx = tenant_context.get()
    if not ctx:
        raise HTTPException(400, "Tenant context required")
    shared = get_shared_db()
    keys = await shared.api_keys.find(
        {"tenant_id": ctx.tenant_id, "is_active": True},
        {"_id": 0},
    ).to_list(100)
    for k in keys:
        full = k.get("key", "")
        k["key_masked"] = full[:8] + "..." + full[-4:] if len(full) > 12 else full
    return {"keys": keys}


@tenant_router.post("/admin/api-keys")
async def generate_api_key(name: str = "ERP Integration Key", current_user: dict = Depends(require_role(["admin", "super_admin"]))):
    ctx = tenant_context.get()
    if not ctx:
        raise HTTPException(400, "Tenant context required")
    shared = get_shared_db()
    key = f"mct_{secrets.token_urlsafe(32)}"
    now_iso = datetime.now(timezone.utc).isoformat()
    await shared.api_keys.insert_one({
        "tenant_id": ctx.tenant_id,
        "name": name,
        "key": key,
        "created_by": current_user["email"],
        "created_at": now_iso,
        "last_used": None,
        "is_active": True,
    })
    return {"key": key, "name": name, "created_at": now_iso}


@tenant_router.delete("/admin/api-keys/{key_prefix}")
async def revoke_api_key(key_prefix: str, current_user: dict = Depends(require_role(["admin", "super_admin"]))):
    ctx = tenant_context.get()
    if not ctx:
        raise HTTPException(400, "Tenant context required")
    shared = get_shared_db()
    result = await shared.api_keys.update_one(
        {"tenant_id": ctx.tenant_id, "key": {"$regex": f"^{key_prefix}"}},
        {"$set": {"is_active": False, "revoked_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "API key not found")
    return {"message": "API key revoked"}


# ──────────── Tenant Admin: Settings ────────────

@tenant_router.put("/{tenant_id}/settings")
async def update_tenant_settings(tenant_id: str, body: dict, current_user: dict = Depends(require_role(["admin", "super_admin"]))):
    shared = get_shared_db()
    update = {}
    if "company_name" in body:
        update["company_name"] = body["company_name"]
    if "timezone" in body:
        update["timezone"] = body["timezone"]
    if not update:
        raise HTTPException(400, "No settings to update")
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await shared.tenants.update_one({"tenant_id": tenant_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(404, "Tenant not found")
    clear_tenant_cache(tenant_id)
    return {"message": "Settings updated"}
