"""Super Admin tenant & user management APIs."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import secrets
import bcrypt
import uuid
import io
import csv

router = APIRouter(prefix="/admin/platform", tags=["super-admin"])

_client = None
_get_current_user = None
_require_role = None


def init_super_admin(mongo_client, get_current_user_func, require_role_func):
    global _client, _get_current_user, _require_role
    _client = mongo_client
    _get_current_user = get_current_user_func
    _require_role = require_role_func


async def _dep_get_current_user(request: Request) -> dict:
    """Properly typed dependency wrapper for FastAPI injection."""
    return await _get_current_user(request)


async def _log_admin_audit(action: str, actor: dict, request: Request = None, **kwargs):
    """Log an admin action to the audit_logs collection."""
    try:
        shared = _shared()
        entry = {
            "audit_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "actor_email": actor.get("email", ""),
            "actor_role": actor.get("role", ""),
            "impersonated_by": actor.get("impersonated_by"),
            "source": "super_admin",
            **kwargs,
        }
        if request:
            entry["ip_address"] = request.headers.get("x-forwarded-for", request.client.host if request.client else "")
            entry["user_agent"] = request.headers.get("user-agent", "")[:200]
        await shared.audit_logs.insert_one(entry)
    except Exception:
        pass  # Audit logging never blocks the request


def _shared():
    import os
    return _client[os.environ["DB_NAME"]]


def _super_admin_only(user: dict):
    if user.get("role") != "super_admin":
        raise HTTPException(403, "Super Admin access required")


class CreateTenantReq(BaseModel):
    tenant_id: str
    company_name: str
    admin_email: str
    admin_name: str
    plan: str = "professional"


class CreateUserReq(BaseModel):
    email: str
    name: str
    tenant_id: str
    role: str = "viewer"


# ── Tenant CRUD ──

@router.get("/tenants")
async def list_tenants(user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()
    tenants = []
    async for t in shared.tenants.find({}, {"_id": 0}):
        t["user_count"] = await shared.user_tenants.count_documents({"tenant_id": t["tenant_id"]})
        tenants.append(t)
    return {"tenants": tenants}


@router.post("/tenants")
async def create_tenant(body: CreateTenantReq, user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()

    existing = await shared.tenants.find_one({"tenant_id": body.tenant_id})
    if existing:
        raise HTTPException(400, f"Tenant '{body.tenant_id}' already exists")

    # Create tenant record
    await shared.tenants.insert_one({
        "tenant_id": body.tenant_id,
        "company_name": body.company_name,
        "subdomain": body.tenant_id,  # Use tenant_id as subdomain to avoid unique index violation
        "db_name": f"tenant_{body.tenant_id}",
        "plan": body.plan,
        "plan_type": body.plan,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("email"),
    })

    # Create admin user
    temp_password = secrets.token_urlsafe(12)
    hashed = bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt()).decode()

    existing_user = await shared.users.find_one({"email": body.admin_email})
    if not existing_user:
        result = await shared.users.insert_one({
            "email": body.admin_email,
            "full_name": body.admin_name,
            "username": body.admin_name.lower().replace(" ", "_"),
            "hashed_password": hashed,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "must_change_password": True,
        })
        user_id = str(result.inserted_id)
    else:
        user_id = str(existing_user["_id"])

    # Map user to tenant
    await shared.user_tenants.update_one(
        {"email": body.admin_email, "tenant_id": body.tenant_id},
        {"$set": {
            "email": body.admin_email,
            "user_id": user_id,
            "tenant_id": body.tenant_id,
            "role": "admin",
            "is_active": True,
            "assigned_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )

    # Create tenant database with basic indexes
    import os
    db_name = f"merch_{body.tenant_id}"
    tdb = _client[db_name]
    for coll in ["daily_sales", "store_inventory", "sku_master", "style_master", "store_master"]:
        await tdb[coll].create_index("tenant_id", sparse=True)

    await _log_admin_audit("tenant_created", user, request,
        target_tenant_id=body.tenant_id, company_name=body.company_name,
        admin_email=body.admin_email, plan=body.plan)

    return {
        "success": True,
        "tenant_id": body.tenant_id,
        "admin_email": body.admin_email,
        "temp_password": temp_password,
        "message": f"Tenant created. Share credentials with admin: {body.admin_email} / {temp_password}",
    }


@router.put("/tenants/{tenant_id}/status")
async def update_tenant_status(tenant_id: str, body: dict, request: Request, user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()
    status = body.get("status", "active")
    result = await shared.tenants.update_one({"tenant_id": tenant_id}, {"$set": {"status": status}})
    if result.matched_count == 0:
        raise HTTPException(404, "Tenant not found")
    await _log_admin_audit("tenant_status_changed", user, request,
        target_tenant_id=tenant_id, new_status=status)
    return {"success": True, "tenant_id": tenant_id, "status": status}


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str, request: Request, user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    if tenant_id == "demo":
        raise HTTPException(400, "Cannot delete the demo tenant")
    shared = _shared()
    await shared.tenants.delete_one({"tenant_id": tenant_id})
    await shared.user_tenants.delete_many({"tenant_id": tenant_id})
    await _log_admin_audit("tenant_deleted", user, request, target_tenant_id=tenant_id)
    return {"success": True, "message": f"Tenant '{tenant_id}' deleted"}


# ── User management across tenants ──

@router.get("/users")
async def list_all_users(tenant_id: Optional[str] = None, user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()
    query = {"tenant_id": tenant_id} if tenant_id else {}
    mappings = []
    async for m in shared.user_tenants.find(query, {"_id": 0}):
        u = await shared.users.find_one({"email": m["email"]}, {"_id": 0, "hashed_password": 0, "password": 0, "totp_secret": 0})
        mappings.append({
            **m,
            "full_name": u.get("full_name", u.get("name", "")) if u else "",
            "username": u.get("username", "") if u else "",
            "last_login": u.get("last_login") if u else None,
            "mfa_enabled": u.get("mfa_enabled", False) if u else False,
            "created_at": u.get("created_at") if u else m.get("assigned_at"),
            "user_exists": u is not None,
        })
    return {"users": mappings}


class UpdateUserRoleReq(BaseModel):
    tenant_id: str
    role: str


@router.put("/users/{email}/role")
async def update_user_role(email: str, body: UpdateUserRoleReq, request: Request, user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()
    old = await shared.user_tenants.find_one({"email": email, "tenant_id": body.tenant_id}, {"_id": 0, "role": 1})
    result = await shared.user_tenants.update_one(
        {"email": email, "tenant_id": body.tenant_id},
        {"$set": {"role": body.role}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "User-tenant mapping not found")
    await _log_admin_audit("user_role_changed", user, request,
        target_email=email, target_tenant_id=body.tenant_id,
        old_role=old.get("role") if old else None, new_role=body.role)
    return {"success": True, "email": email, "tenant_id": body.tenant_id, "role": body.role}


class UpdateUserStatusReq(BaseModel):
    tenant_id: str
    is_active: bool


@router.put("/users/{email}/status")
async def update_user_status(email: str, body: UpdateUserStatusReq, request: Request, user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()
    result = await shared.user_tenants.update_one(
        {"email": email, "tenant_id": body.tenant_id},
        {"$set": {"is_active": body.is_active}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "User-tenant mapping not found")
    await _log_admin_audit("user_status_changed", user, request,
        target_email=email, target_tenant_id=body.tenant_id,
        new_status="active" if body.is_active else "inactive")
    return {"success": True, "email": email, "tenant_id": body.tenant_id, "is_active": body.is_active}


@router.post("/users/{email}/reset-password")
async def reset_user_password(email: str, request: Request, user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()
    existing = await shared.users.find_one({"email": email})
    if not existing:
        raise HTTPException(404, "User not found")
    temp_password = secrets.token_urlsafe(12)
    hashed = bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt()).decode()
    await shared.users.update_one(
        {"email": email},
        {"$set": {"hashed_password": hashed, "must_change_password": True}},
    )
    return {"success": True, "email": email, "temp_password": temp_password}


@router.post("/users")
async def create_user(body: CreateUserReq, request: Request, user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()

    # Verify tenant exists
    tenant = await shared.tenants.find_one({"tenant_id": body.tenant_id})
    if not tenant:
        raise HTTPException(404, f"Tenant '{body.tenant_id}' not found")

    temp_password = secrets.token_urlsafe(12)
    hashed = bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt()).decode()

    existing_user = await shared.users.find_one({"email": body.email})
    if not existing_user:
        result = await shared.users.insert_one({
            "email": body.email,
            "full_name": body.name,
            "username": body.name.lower().replace(" ", "_"),
            "hashed_password": hashed,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "must_change_password": True,
        })
        user_id = str(result.inserted_id)
    else:
        user_id = str(existing_user["_id"])

    await shared.user_tenants.update_one(
        {"email": body.email, "tenant_id": body.tenant_id},
        {"$set": {
            "email": body.email,
            "user_id": user_id,
            "tenant_id": body.tenant_id,
            "role": body.role,
            "is_active": True,
            "assigned_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )

    await _log_admin_audit("user_created", user, request,
        target_email=body.email, target_tenant_id=body.tenant_id, role=body.role)

    return {"success": True, "email": body.email, "temp_password": temp_password}


# ── Impersonation ──
# NOTE: /impersonate/end MUST be defined BEFORE /impersonate/{tenant_id}
# to avoid the path parameter matching "end" as a tenant_id

@router.post("/impersonate/end")
async def impersonation_end(request: Request, user: dict = Depends(_dep_get_current_user)):
    """Log that a super admin stopped impersonating."""
    impersonated_by = user.get("impersonated_by")
    if not impersonated_by:
        return {"success": True, "message": "Not in impersonation session"}
    await _log_admin_audit("impersonation_end", user, request,
        target_tenant_id=user.get("tenant_id"),
        impersonated_by=impersonated_by)
    return {"success": True}


@router.post("/impersonate/{tenant_id}")
async def impersonate(tenant_id: str, request: Request, user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()

    tenant = await shared.tenants.find_one({"tenant_id": tenant_id})
    if not tenant:
        raise HTTPException(404, "Tenant not found")

    # Find an admin user for this tenant
    mapping = await shared.user_tenants.find_one({"tenant_id": tenant_id, "role": "admin"})
    if not mapping:
        mapping = await shared.user_tenants.find_one({"tenant_id": tenant_id})
    if not mapping:
        raise HTTPException(404, "No users found for this tenant")

    target_user = await shared.users.find_one({"email": mapping["email"]}, {"_id": 0, "password": 0})
    if not target_user:
        raise HTTPException(404, "Target user not found")

    from multi_tenant.auth import _create_token
    token = _create_token({
        "user_id": mapping.get("user_id", ""),
        "email": mapping["email"],
        "tenant_id": tenant_id,
        "role": mapping.get("role", "admin"),
        "impersonated_by": user.get("email"),
    })

    from multi_tenant.rbac import resolve_permissions
    perms = resolve_permissions(mapping.get("role", "admin"))

    await _log_admin_audit("impersonation_start", user, request,
        target_tenant_id=tenant_id,
        target_email=mapping["email"],
        company_name=tenant.get("company_name", tenant_id))

    return {
        "success": True,
        "access_token": token,
        "tenant_id": tenant_id,
        "user": {
            "email": mapping["email"],
            "username": target_user.get("username", ""),
            "full_name": target_user.get("full_name", ""),
            "role": mapping.get("role", "admin"),
            "tenant_id": tenant_id,
            "permissions": perms,
        },
        "impersonated_by": user.get("email"),
        "company_name": tenant.get("company_name", tenant_id),
    }


# ── Audit Log Viewer ──

@router.get("/audit-logs")
async def get_audit_logs(
    action: Optional[str] = None,
    actor_email: Optional[str] = None,
    target_tenant_id: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    user: dict = Depends(_dep_get_current_user),
):
    _super_admin_only(user)
    shared = _shared()

    query = {"source": "super_admin"}
    if action:
        query["action"] = action
    if actor_email:
        query["actor_email"] = {"$regex": actor_email, "$options": "i"}
    if target_tenant_id:
        query["target_tenant_id"] = target_tenant_id

    total = await shared.audit_logs.count_documents(query)
    logs = []
    cursor = shared.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit)
    async for doc in cursor:
        logs.append(doc)

    return {"logs": logs, "total": total, "limit": limit, "skip": skip}


@router.get("/audit-logs/export/csv")
async def export_audit_logs_csv(
    action: Optional[str] = None,
    actor_email: Optional[str] = None,
    target_tenant_id: Optional[str] = None,
    user: dict = Depends(_dep_get_current_user),
):
    _super_admin_only(user)
    shared = _shared()

    query = {"source": "super_admin"}
    if action:
        query["action"] = action
    if actor_email:
        query["actor_email"] = {"$regex": actor_email, "$options": "i"}
    if target_tenant_id:
        query["target_tenant_id"] = target_tenant_id

    logs = []
    async for doc in shared.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).limit(5000):
        logs.append(doc)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Timestamp", "Action", "Actor", "Target Tenant", "Target User", "Impersonated By", "IP Address", "Details"])
    for log in logs:
        details = {k: v for k, v in log.items() if k not in (
            "audit_id", "timestamp", "action", "actor_email", "actor_role",
            "target_tenant_id", "target_email", "impersonated_by", "ip_address",
            "user_agent", "source",
        )}
        writer.writerow([
            log.get("timestamp", ""),
            log.get("action", ""),
            log.get("actor_email", ""),
            log.get("target_tenant_id", ""),
            log.get("target_email", ""),
            log.get("impersonated_by", ""),
            log.get("ip_address", ""),
            str(details) if details else "",
        ])

    buf.seek(0)
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
    )


@router.get("/audit-logs/actions")
async def get_audit_action_types(user: dict = Depends(_dep_get_current_user)):
    """Return distinct action types for filter dropdown."""
    _super_admin_only(user)
    shared = _shared()
    actions = await shared.audit_logs.distinct("action", {"source": "super_admin"})
    return {"actions": sorted(actions)}
