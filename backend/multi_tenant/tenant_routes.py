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

    branding = tenant.get("branding", {})

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
        "branding": {
            "primary_color": branding.get("primary_color", "#0176D3"),
            "secondary_color": branding.get("secondary_color", "#0161B0"),
            "logo_url": branding.get("logo_url", ""),
        },
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


# ──────────── TENANT-20: Branding (Logo, Colors) ────────────

@tenant_router.put("/{tenant_id}/branding")
async def update_tenant_branding(tenant_id: str, body: dict, current_user: dict = Depends(require_role(["admin", "super_admin"]))):
    """Update tenant branding: primary_color, secondary_color, logo_url."""
    shared = get_shared_db()
    branding = {}
    if "primary_color" in body:
        pc = body["primary_color"]
        if not (isinstance(pc, str) and len(pc) == 7 and pc.startswith("#")):
            raise HTTPException(400, "primary_color must be a valid hex color (e.g. #0176D3)")
        branding["primary_color"] = pc
    if "secondary_color" in body:
        sc = body["secondary_color"]
        if not (isinstance(sc, str) and len(sc) == 7 and sc.startswith("#")):
            raise HTTPException(400, "secondary_color must be a valid hex color (e.g. #0161B0)")
        branding["secondary_color"] = sc
    if "logo_url" in body:
        branding["logo_url"] = body["logo_url"][:500]  # cap length

    if not branding:
        raise HTTPException(400, "No branding fields provided")

    result = await shared.tenants.update_one(
        {"tenant_id": tenant_id},
        {"$set": {f"branding.{k}": v for k, v in branding.items()} | {"updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Tenant not found")
    clear_tenant_cache(tenant_id)
    return {"message": "Branding updated", "branding": branding}


@tenant_router.get("/{tenant_id}/branding")
async def get_tenant_branding(tenant_id: str):
    """Get tenant branding info (public for rendering)."""
    shared = get_shared_db()
    tenant = await shared.tenants.find_one({"tenant_id": tenant_id}, {"_id": 0, "branding": 1, "company_name": 1})
    if not tenant:
        raise HTTPException(404, "Tenant not found")
    branding = tenant.get("branding", {})
    return {
        "company_name": tenant.get("company_name", ""),
        "primary_color": branding.get("primary_color", "#0176D3"),
        "secondary_color": branding.get("secondary_color", "#0161B0"),
        "logo_url": branding.get("logo_url", ""),
    }


# ──────────── TENANT-06/27/28: Plan Management ────────────

PLAN_LIMITS = {
    "starter": {"max_users": 5, "storage_gb": 10, "api_calls": 1000},
    "professional": {"max_users": 20, "storage_gb": 50, "api_calls": 10000},
    "enterprise": {"max_users": 999, "storage_gb": 100, "api_calls": 100000},
}

@tenant_router.put("/{tenant_id}/plan")
async def update_tenant_plan(tenant_id: str, body: dict, current_user: dict = Depends(require_role(["admin", "super_admin"]))):
    """Upgrade or downgrade tenant plan."""
    new_plan = body.get("plan_type", "")
    if new_plan not in PLAN_LIMITS:
        raise HTTPException(400, f"Invalid plan. Must be one of: {list(PLAN_LIMITS.keys())}")

    shared = get_shared_db()
    tenant = await shared.tenants.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(404, "Tenant not found")

    old_plan = tenant.get("plan_type", "starter")
    is_downgrade = list(PLAN_LIMITS.keys()).index(new_plan) < list(PLAN_LIMITS.keys()).index(old_plan)

    # TENANT-29: Enforce limits on downgrade
    if is_downgrade:
        active_users = await shared.user_tenants.count_documents({"tenant_id": tenant_id, "is_active": True})
        if active_users > PLAN_LIMITS[new_plan]["max_users"]:
            raise HTTPException(400, f"Cannot downgrade: {active_users} active users exceed {new_plan} limit of {PLAN_LIMITS[new_plan]['max_users']}")

    await shared.tenants.update_one(
        {"tenant_id": tenant_id},
        {"$set": {"plan_type": new_plan, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    clear_tenant_cache(tenant_id)

    direction = "downgraded" if is_downgrade else "upgraded"
    return {"message": f"Plan {direction} from {old_plan} to {new_plan}", "plan": new_plan, "limits": PLAN_LIMITS[new_plan]}


# ──────────── TENANT-23: Currency Setting ────────────

@tenant_router.put("/{tenant_id}/currency")
async def update_tenant_currency(tenant_id: str, body: dict, current_user: dict = Depends(require_role(["admin", "super_admin"]))):
    """Set tenant currency."""
    currency = body.get("currency", "INR")
    valid = ["INR", "USD", "EUR", "GBP", "AED", "SGD", "AUD"]
    if currency not in valid:
        raise HTTPException(400, f"Invalid currency. Must be one of: {valid}")

    shared = get_shared_db()
    result = await shared.tenants.update_one(
        {"tenant_id": tenant_id},
        {"$set": {"currency": currency, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Tenant not found")
    return {"message": f"Currency set to {currency}"}


# ──────────── TENANT-34: Filter Tenants ────────────

@tenant_router.get("/filtered")
async def list_tenants_filtered(
    status: Optional[str] = None,
    plan_type: Optional[str] = None,
    search: Optional[str] = None,
):
    """List tenants with optional filters."""
    shared = get_shared_db()
    query: dict = {"status": {"$ne": "deleted"}}
    if status:
        query["status"] = status
    if plan_type:
        query["plan_type"] = plan_type

    tenants = await shared.tenants.find(query, {"_id": 0, "api_key_hash": 0}).to_list(500)

    if search:
        search_lower = search.lower()
        tenants = [t for t in tenants if search_lower in t.get("company_name", "").lower() or search_lower in t.get("tenant_id", "").lower()]

    return {"tenants": tenants, "total": len(tenants)}


# ──────────── TENANT-35: Export Tenant List ────────────

@tenant_router.get("/export")
async def export_tenants():
    """Export all tenants as CSV."""
    import io
    import pandas as pd
    from fastapi.responses import StreamingResponse

    shared = get_shared_db()
    tenants = await shared.tenants.find({"status": {"$ne": "deleted"}}, {"_id": 0, "api_key_hash": 0}).to_list(500)

    if not tenants:
        raise HTTPException(404, "No tenants found")

    df = pd.DataFrame(tenants)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tenants_export.csv"},
    )
