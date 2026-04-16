"""Super Admin tenant & user management APIs."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
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
        # Run anomaly detection (fire-and-forget, never blocks)
        await _check_anomalies(shared, action, actor.get("email", ""), kwargs)
    except Exception:
        pass  # Audit logging never blocks the request


# ── Anomaly Detection Engine ──

_ANOMALY_RULES = {
    "excessive_impersonations": {
        "severity": "critical",
        "title": "Excessive impersonations",
        "description": "{actor} performed {count} impersonations in the last hour (threshold: 5)",
        "action": "impersonation_start",
        "window_hours": 1,
        "threshold": 5,
    },
    "role_flip_flop": {
        "severity": "warning",
        "title": "Role flip-flop detected",
        "description": "{target}'s role in {tenant} was changed {count} times in 24h (threshold: 3)",
        "action": "user_role_changed",
        "window_hours": 24,
        "threshold": 3,
    },
    "bulk_status_changes": {
        "severity": "warning",
        "title": "Bulk user deactivations",
        "description": "{actor} changed {count} user statuses in the last hour (threshold: 10)",
        "action": "user_status_changed",
        "window_hours": 1,
        "threshold": 10,
    },
    "off_hours_activity": {
        "severity": "warning",
        "title": "Off-hours admin activity",
        "description": "{actor} performed '{action_name}' at {time} UTC (outside 06:00–22:00)",
    },
    "rapid_password_resets": {
        "severity": "critical",
        "title": "Rapid password resets",
        "description": "{actor} reset {count} passwords in the last hour (threshold: 5)",
        "action": "user_password_reset",
        "window_hours": 1,
        "threshold": 5,
    },
}


async def _check_anomalies(shared, action: str, actor_email: str, details: dict):
    """Run anomaly detection rules against recent audit logs."""
    try:
        now = datetime.now(timezone.utc)

        # Rule 1: Excessive impersonations
        if action == "impersonation_start":
            await _check_count_rule(shared, "excessive_impersonations", actor_email, now, details)

        # Rule 2: Role flip-flop
        if action == "user_role_changed":
            await _check_role_flip_flop(shared, actor_email, now, details)

        # Rule 3: Bulk status changes
        if action == "user_status_changed":
            await _check_count_rule(shared, "bulk_status_changes", actor_email, now, details)

        # Rule 4: Off-hours activity
        if now.hour < 6 or now.hour >= 22:
            await _create_alert(shared, "off_hours_activity", "warning",
                _ANOMALY_RULES["off_hours_activity"]["title"],
                _ANOMALY_RULES["off_hours_activity"]["description"].format(
                    actor=actor_email, action_name=action, time=now.strftime("%H:%M")),
                actor_email, details)

        # Rule 5: Rapid password resets
        if action == "user_password_reset":
            await _check_count_rule(shared, "rapid_password_resets", actor_email, now, details)
    except Exception:
        pass


async def _check_count_rule(shared, rule_id: str, actor_email: str, now, details: dict):
    rule = _ANOMALY_RULES[rule_id]
    window_start = (now - timedelta(hours=rule["window_hours"])).isoformat()
    count = await shared.audit_logs.count_documents({
        "source": "super_admin",
        "action": rule["action"],
        "actor_email": actor_email,
        "timestamp": {"$gte": window_start},
    })
    if count >= rule["threshold"]:
        # Check if we already alerted for this rule + actor in the last hour
        existing = await shared.admin_alerts.find_one({
            "rule_id": rule_id,
            "actor_email": actor_email,
            "created_at": {"$gte": window_start},
            "status": {"$ne": "dismissed"},
        })
        if not existing:
            desc = rule["description"].format(actor=actor_email, count=count,
                target=details.get("target_email", ""), tenant=details.get("target_tenant_id", ""))
            await _create_alert(shared, rule_id, rule["severity"], rule["title"], desc, actor_email, details)


async def _check_role_flip_flop(shared, actor_email: str, now, details: dict):
    rule = _ANOMALY_RULES["role_flip_flop"]
    target_email = details.get("target_email", "")
    target_tenant = details.get("target_tenant_id", "")
    if not target_email or not target_tenant:
        return
    window_start = (now - timedelta(hours=rule["window_hours"])).isoformat()
    count = await shared.audit_logs.count_documents({
        "source": "super_admin",
        "action": "user_role_changed",
        "target_email": target_email,
        "target_tenant_id": target_tenant,
        "timestamp": {"$gte": window_start},
    })
    if count >= rule["threshold"]:
        existing = await shared.admin_alerts.find_one({
            "rule_id": "role_flip_flop",
            "details.target_email": target_email,
            "created_at": {"$gte": window_start},
            "status": {"$ne": "dismissed"},
        })
        if not existing:
            desc = rule["description"].format(target=target_email, tenant=target_tenant, count=count)
            await _create_alert(shared, "role_flip_flop", rule["severity"], rule["title"], desc, actor_email,
                {**details, "target_email": target_email, "target_tenant_id": target_tenant})


async def _create_alert(shared, rule_id: str, severity: str, title: str, description: str, actor_email: str, details: dict):
    await shared.admin_alerts.insert_one({
        "alert_id": str(uuid.uuid4()),
        "rule_id": rule_id,
        "severity": severity,
        "title": title,
        "description": description,
        "actor_email": actor_email,
        "details": {k: v for k, v in details.items() if v is not None},
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


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
async def create_tenant(body: CreateTenantReq, request: Request, user: dict = Depends(_dep_get_current_user)):
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

    # Check plan user limit
    from core.plan_access import check_plan_limit
    allowed, current, limit, plan = await check_plan_limit(shared, body.tenant_id, "users")
    if not allowed:
        raise HTTPException(400, f"User limit reached ({current}/{limit}) for {plan} plan. Upgrade to add more users.")

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


# ── Security Alerts ──

@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    user: dict = Depends(_dep_get_current_user),
):
    _super_admin_only(user)
    shared = _shared()
    query = {}
    if severity:
        query["severity"] = severity
    if status:
        query["status"] = status
    else:
        query["status"] = {"$ne": "dismissed"}

    total = await shared.admin_alerts.count_documents(query)
    alerts = []
    async for doc in shared.admin_alerts.find(query, {"_id": 0}).sort("created_at", -1).limit(limit):
        alerts.append(doc)
    return {"alerts": alerts, "total": total}


@router.get("/alerts/unread-count")
async def get_alerts_unread_count(user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()
    count = await shared.admin_alerts.count_documents({"status": "active"})
    return {"count": count}


@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()
    result = await shared.admin_alerts.update_one(
        {"alert_id": alert_id},
        {"$set": {"status": "acknowledged", "acknowledged_by": user.get("email"),
                  "acknowledged_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Alert not found")
    return {"success": True, "alert_id": alert_id, "status": "acknowledged"}


@router.put("/alerts/{alert_id}/dismiss")
async def dismiss_alert(alert_id: str, user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()
    result = await shared.admin_alerts.update_one(
        {"alert_id": alert_id},
        {"$set": {"status": "dismissed", "dismissed_by": user.get("email"),
                  "dismissed_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Alert not found")
    return {"success": True, "alert_id": alert_id, "status": "dismissed"}


# ── Platform Analytics ──

PLAN_MRR = {
    "trial": 0,
    "starter": 29000,
    "professional": 99000,
    "business": 199000,
    "enterprise": 249000,
}


@router.get("/analytics")
async def get_platform_analytics(user: dict = Depends(_dep_get_current_user)):
    """Platform-wide analytics: MRR, tenant health, active users, churn."""
    _super_admin_only(user)
    shared = _shared()

    # ── Tenant stats ──
    tenants = []
    async for t in shared.tenants.find({}, {"_id": 0}):
        tenants.append(t)

    total_tenants = len(tenants)
    active_tenants = sum(1 for t in tenants if t.get("status") == "active")
    trial_tenants = sum(1 for t in tenants if t.get("plan_type") == "trial" and t.get("status") == "active")
    suspended_tenants = sum(1 for t in tenants if t.get("status") in ("suspended", "trial_expired"))

    # Plan distribution
    plan_dist = {}
    for t in tenants:
        p = t.get("plan_type", "starter")
        plan_dist[p] = plan_dist.get(p, 0) + 1

    # MRR calculation (only active paying tenants)
    mrr = 0
    for t in tenants:
        if t.get("status") == "active" and t.get("plan_type") != "trial":
            mrr += PLAN_MRR.get(t.get("plan_type", "starter"), 0)

    # ── User stats ──
    total_users = await shared.user_tenants.count_documents({})
    active_users = await shared.user_tenants.count_documents({"is_active": True})

    # Users active in last 7 days
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_logins = await shared.users.count_documents({"last_login": {"$gte": week_ago}})

    # Users active in last 30 days
    month_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    monthly_active = await shared.users.count_documents({"last_login": {"$gte": month_ago}})

    # ── Tenant health breakdown ──
    tenant_health = []
    for t in tenants:
        tid = t.get("tenant_id", "")
        user_count = await shared.user_tenants.count_documents({"tenant_id": tid})
        status = t.get("status", "unknown")
        plan = t.get("plan_type", "starter")

        # Check trial expiration
        trial_days_left = None
        if plan == "trial" and t.get("trial_end"):
            try:
                trial_end = datetime.fromisoformat(t["trial_end"])
                if trial_end.tzinfo is None:
                    trial_end = trial_end.replace(tzinfo=timezone.utc)
                trial_days_left = max(0, (trial_end - datetime.now(timezone.utc)).days)
            except Exception:
                pass

        from core.plan_access import get_plan_limits
        limits = get_plan_limits(plan)

        tenant_health.append({
            "tenant_id": tid,
            "company_name": t.get("company_name", tid),
            "plan": plan,
            "status": status,
            "users": user_count,
            "max_users": limits.get("max_users", 999),
            "mrr": PLAN_MRR.get(plan, 0) if status == "active" and plan != "trial" else 0,
            "trial_days_left": trial_days_left,
            "created_at": t.get("created_at"),
        })

    # ── Signups over time (last 30 days) ──
    signup_trend = []
    for i in range(30, -1, -1):
        day = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
        count = sum(1 for t in tenants if t.get("created_at", "")[:10] == day)
        signup_trend.append({"date": day, "count": count})

    # ── Security alerts ──
    active_alerts = await shared.admin_alerts.count_documents({"status": "active"})

    return {
        "overview": {
            "total_tenants": total_tenants,
            "active_tenants": active_tenants,
            "trial_tenants": trial_tenants,
            "suspended_tenants": suspended_tenants,
            "mrr": mrr,
            "mrr_formatted": f"₹{mrr:,.0f}",
            "total_users": total_users,
            "active_users": active_users,
            "weekly_active_users": recent_logins,
            "monthly_active_users": monthly_active,
            "active_alerts": active_alerts,
        },
        "plan_distribution": plan_dist,
        "tenant_health": sorted(tenant_health, key=lambda x: x["mrr"], reverse=True),
        "signup_trend": signup_trend,
    }


# ── Feature Flags ──

class FeatureFlagReq(BaseModel):
    flag_key: str
    label: str
    description: str = ""
    default_enabled: bool = False


class FeatureFlagOverrideReq(BaseModel):
    tenant_id: str
    enabled: bool


@router.get("/feature-flags")
async def list_feature_flags(user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()
    flags = []
    async for f in shared.feature_flags.find({}, {"_id": 0}).sort("flag_key", 1):
        # Count overrides
        overrides = await shared.feature_flag_overrides.count_documents({"flag_key": f["flag_key"]})
        f["override_count"] = overrides
        flags.append(f)
    return {"flags": flags}


@router.post("/feature-flags")
async def create_feature_flag(body: FeatureFlagReq, request: Request, user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()
    existing = await shared.feature_flags.find_one({"flag_key": body.flag_key})
    if existing:
        raise HTTPException(400, f"Flag '{body.flag_key}' already exists")
    await shared.feature_flags.insert_one({
        "flag_key": body.flag_key,
        "label": body.label,
        "description": body.description,
        "default_enabled": body.default_enabled,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("email"),
    })
    await _log_admin_audit("feature_flag_created", user, request, flag_key=body.flag_key)
    return {"success": True, "flag_key": body.flag_key}


@router.put("/feature-flags/{flag_key}")
async def update_feature_flag(flag_key: str, body: FeatureFlagReq, request: Request, user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()
    result = await shared.feature_flags.update_one(
        {"flag_key": flag_key},
        {"$set": {
            "label": body.label,
            "description": body.description,
            "default_enabled": body.default_enabled,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Feature flag not found")
    await _log_admin_audit("feature_flag_updated", user, request, flag_key=flag_key)
    return {"success": True, "flag_key": flag_key}


@router.delete("/feature-flags/{flag_key}")
async def delete_feature_flag(flag_key: str, request: Request, user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()
    result = await shared.feature_flags.delete_one({"flag_key": flag_key})
    if result.deleted_count == 0:
        raise HTTPException(404, "Feature flag not found")
    await shared.feature_flag_overrides.delete_many({"flag_key": flag_key})
    await _log_admin_audit("feature_flag_deleted", user, request, flag_key=flag_key)
    return {"success": True, "flag_key": flag_key}


@router.get("/feature-flags/{flag_key}/overrides")
async def get_flag_overrides(flag_key: str, user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()
    overrides = []
    async for o in shared.feature_flag_overrides.find({"flag_key": flag_key}, {"_id": 0}):
        overrides.append(o)
    return {"flag_key": flag_key, "overrides": overrides}


@router.put("/feature-flags/{flag_key}/overrides")
async def set_flag_override(flag_key: str, body: FeatureFlagOverrideReq, request: Request, user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()
    flag = await shared.feature_flags.find_one({"flag_key": flag_key})
    if not flag:
        raise HTTPException(404, "Feature flag not found")
    tenant = await shared.tenants.find_one({"tenant_id": body.tenant_id})
    if not tenant:
        raise HTTPException(404, f"Tenant '{body.tenant_id}' not found")
    await shared.feature_flag_overrides.update_one(
        {"flag_key": flag_key, "tenant_id": body.tenant_id},
        {"$set": {
            "flag_key": flag_key,
            "tenant_id": body.tenant_id,
            "enabled": body.enabled,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user.get("email"),
        }},
        upsert=True,
    )
    await _log_admin_audit("feature_flag_override", user, request,
        flag_key=flag_key, target_tenant_id=body.tenant_id, enabled=body.enabled)
    return {"success": True, "flag_key": flag_key, "tenant_id": body.tenant_id, "enabled": body.enabled}


@router.delete("/feature-flags/{flag_key}/overrides/{tenant_id}")
async def delete_flag_override(flag_key: str, tenant_id: str, request: Request, user: dict = Depends(_dep_get_current_user)):
    _super_admin_only(user)
    shared = _shared()
    result = await shared.feature_flag_overrides.delete_one({"flag_key": flag_key, "tenant_id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Override not found")
    return {"success": True}


# Public endpoint: get flags for current tenant (used by frontend useFeatureFlag hook)
@router.get("/feature-flags/tenant/{tenant_id}")
async def get_tenant_flags(tenant_id: str, user: dict = Depends(_dep_get_current_user)):
    """Return resolved feature flags for a specific tenant."""
    shared = _shared()
    flags = {}
    async for f in shared.feature_flags.find({}, {"_id": 0}):
        flags[f["flag_key"]] = f.get("default_enabled", False)
    # Apply tenant overrides
    async for o in shared.feature_flag_overrides.find({"tenant_id": tenant_id}, {"_id": 0}):
        flags[o["flag_key"]] = o.get("enabled", False)
    return {"tenant_id": tenant_id, "flags": flags}
