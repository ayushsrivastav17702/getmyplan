"""
User management API — list, invite, update role, remove, audit log.
All endpoints are tenant-scoped via the middleware context.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import secrets
import logging

from .tenant_db import get_shared_db, tenant_context
from .auth import get_current_user, _hash_password, _create_token
from .rbac import require_role, resolve_permissions, ROLES

logger = logging.getLogger(__name__)

user_router = APIRouter(prefix="/api/users", tags=["User Management"])


# ──────────── Models ────────────

class InviteRequest(BaseModel):
    email: EmailStr
    role: str = Field(..., min_length=2)
    full_name: Optional[str] = None

class UpdateRoleRequest(BaseModel):
    role: str

class AcceptInviteRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


# ──────────── Helpers ────────────

async def _log_audit(user_id: str, tenant_id: str, action: str, detail: dict = None):
    shared = get_shared_db()
    await shared.audit_logs.insert_one({
        "user_id": user_id,
        "tenant_id": tenant_id,
        "action": action,
        "detail": detail or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


# ──────────── Routes ────────────

@user_router.get("/roles")
async def list_roles(current_user: dict = Depends(require_role(["admin", "super_admin"]))):
    """Return all assignable roles (exclude super_admin for tenant admins)."""
    roles = ROLES
    if current_user["role"] != "super_admin":
        roles = [r for r in roles if r["role_name"] != "super_admin"]
    return {"roles": [{"role_name": r["role_name"], "display_name": r["display_name"], "description": r["description"]} for r in roles]}


@user_router.get("/list")
async def list_users(current_user: dict = Depends(require_role(["admin", "super_admin"]))):
    """List all users in the current tenant."""
    ctx = tenant_context.get()
    if not ctx:
        raise HTTPException(400, "Tenant context required")
    shared = get_shared_db()

    mappings = await shared.user_tenants.find({"tenant_id": ctx.tenant_id, "is_active": True}).to_list(500)
    users = []
    for m in mappings:
        user = await shared.users.find_one({"email": m["email"]}, {"_id": 0, "hashed_password": 0})
        if user:
            users.append({
                "email": user["email"],
                "username": user.get("username", ""),
                "full_name": user.get("full_name", ""),
                "role": m.get("role", "viewer"),
                "is_active": m.get("is_active", True),
                "assigned_at": m.get("assigned_at"),
            })
    return {"users": users, "total": len(users)}


@user_router.post("/invite")
async def invite_user(body: InviteRequest, current_user: dict = Depends(require_role(["admin", "super_admin"]))):
    """Invite a user to the current tenant. Creates an invitation token."""
    ctx = tenant_context.get()
    if not ctx:
        raise HTTPException(400, "Tenant context required")
    shared = get_shared_db()

    # Check role is valid
    valid_roles = {r["role_name"] for r in ROLES}
    if body.role not in valid_roles:
        raise HTTPException(400, f"Invalid role: {body.role}")

    # Check if already a member
    existing = await shared.user_tenants.find_one({"email": body.email, "tenant_id": ctx.tenant_id, "is_active": True})
    if existing:
        raise HTTPException(400, "User is already a member of this tenant")

    token = secrets.token_urlsafe(32)
    await shared.invitations.insert_one({
        "email": body.email,
        "tenant_id": ctx.tenant_id,
        "role": body.role,
        "full_name": body.full_name,
        "invited_by": current_user["email"],
        "token": token,
        "status": "pending",
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    await _log_audit(current_user["email"], ctx.tenant_id, "INVITE_USER", {"email": body.email, "role": body.role})

    return {"message": f"Invitation sent to {body.email}", "invite_token": token}


@user_router.get("/invitations")
async def list_invitations(current_user: dict = Depends(require_role(["admin", "super_admin"]))):
    """List pending invitations for the current tenant."""
    ctx = tenant_context.get()
    shared = get_shared_db()
    invites = await shared.invitations.find(
        {"tenant_id": ctx.tenant_id, "status": "pending"},
        {"_id": 0, "token": 0},
    ).to_list(200)
    return {"invitations": invites}


@user_router.post("/accept-invite")
async def accept_invite(body: AcceptInviteRequest):
    """Accept an invitation and create/link user account."""
    shared = get_shared_db()
    invite = await shared.invitations.find_one({"token": body.token, "status": "pending"})
    if not invite:
        raise HTTPException(400, "Invalid or expired invitation")

    expires = invite.get("expires_at", "")
    if expires and datetime.fromisoformat(expires) < datetime.now(timezone.utc):
        raise HTTPException(400, "Invitation has expired")

    # Get or create user
    existing = await shared.users.find_one({"email": invite["email"]})
    if existing:
        user_id = str(existing["_id"])
    else:
        res = await shared.users.insert_one({
            "email": invite["email"],
            "username": invite["email"].split("@")[0],
            "hashed_password": _hash_password(body.password),
            "full_name": body.full_name or invite.get("full_name") or invite["email"].split("@")[0],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        user_id = str(res.inserted_id)

    # Map to tenant
    await shared.user_tenants.update_one(
        {"email": invite["email"], "tenant_id": invite["tenant_id"]},
        {"$set": {
            "email": invite["email"],
            "user_id": user_id,
            "tenant_id": invite["tenant_id"],
            "role": invite["role"],
            "is_active": True,
            "assigned_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )

    # Mark accepted
    await shared.invitations.update_one({"token": body.token}, {"$set": {"status": "accepted", "accepted_at": datetime.now(timezone.utc).isoformat()}})

    token = _create_token({
        "user_id": user_id,
        "email": invite["email"],
        "tenant_id": invite["tenant_id"],
        "role": invite["role"],
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": invite["email"],
            "role": invite["role"],
            "tenant_id": invite["tenant_id"],
            "full_name": body.full_name or invite.get("full_name", ""),
        },
    }


@user_router.put("/{user_email}/role")
async def update_user_role(user_email: str, body: UpdateRoleRequest, current_user: dict = Depends(require_role(["admin", "super_admin"]))):
    """Change a user's role in the current tenant."""
    ctx = tenant_context.get()
    shared = get_shared_db()

    if user_email == current_user["email"]:
        raise HTTPException(400, "Cannot change your own role")

    valid_roles = {r["role_name"] for r in ROLES}
    if body.role not in valid_roles:
        raise HTTPException(400, f"Invalid role: {body.role}")

    result = await shared.user_tenants.update_one(
        {"email": user_email, "tenant_id": ctx.tenant_id, "is_active": True},
        {"$set": {"role": body.role, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "User not found in this tenant")

    await _log_audit(current_user["email"], ctx.tenant_id, "UPDATE_ROLE", {"email": user_email, "new_role": body.role})

    return {"message": f"{user_email} role updated to {body.role}"}


@user_router.delete("/{user_email}")
async def remove_user(user_email: str, current_user: dict = Depends(require_role(["admin", "super_admin"]))):
    """Remove a user from the current tenant (soft-delete)."""
    ctx = tenant_context.get()
    shared = get_shared_db()

    if user_email == current_user["email"]:
        raise HTTPException(400, "Cannot remove yourself")

    result = await shared.user_tenants.update_one(
        {"email": user_email, "tenant_id": ctx.tenant_id},
        {"$set": {"is_active": False, "removed_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "User not found in this tenant")

    await _log_audit(current_user["email"], ctx.tenant_id, "REMOVE_USER", {"email": user_email})

    return {"message": f"{user_email} removed from tenant"}


@user_router.get("/me/permissions")
async def my_permissions(current_user: dict = Depends(get_current_user)):
    """Return the full list of permissions for the current user's role."""
    perms = resolve_permissions(current_user["role"])
    return {
        "email": current_user["email"],
        "role": current_user["role"],
        "permissions": perms,
    }


@user_router.get("/audit-log")
async def get_audit_log(limit: int = 50, current_user: dict = Depends(require_role(["admin", "super_admin"]))):
    """Return recent audit log entries for the current tenant."""
    ctx = tenant_context.get()
    shared = get_shared_db()
    logs = await shared.audit_logs.find(
        {"tenant_id": ctx.tenant_id},
        {"_id": 0},
    ).sort("created_at", -1).to_list(limit)
    return {"logs": logs}



# ──────────── Custom Role Creation (CONF-30) ────────────

class CreateRoleRequest(BaseModel):
    role_name: str = Field(..., min_length=2, max_length=50)
    display_name: str = Field(..., min_length=2)
    description: str = ""
    permissions: List[str] = []  # e.g. ["dashboard.executive.view", "analytics.stockout.view"]

@user_router.post("/roles/create")
async def create_custom_role(body: CreateRoleRequest, current_user: dict = Depends(require_role(["super_admin", "admin"]))):
    """Create a custom role with selected permissions."""
    shared = get_shared_db()
    role_name = body.role_name.lower().replace(" ", "_")

    existing = await shared.roles.find_one({"role_name": role_name})
    if existing:
        raise HTTPException(400, f"Role '{role_name}' already exists")

    await shared.roles.insert_one({
        "role_name": role_name,
        "display_name": body.display_name,
        "description": body.description,
        "priority": 50,
        "is_system": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    # Store custom role permissions
    await shared.role_permissions.update_one(
        {"role_name": role_name},
        {"$set": {"role_name": role_name, "permissions": body.permissions,
                  "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )

    # Register in ROLE_PERMISSIONS runtime cache
    from .rbac import ROLE_PERMISSIONS
    ROLE_PERMISSIONS[role_name] = body.permissions

    return {"message": f"Role '{body.display_name}' created", "role_name": role_name, "permissions": body.permissions}


# ──────────── Permission Override (CONF-32) ────────────

class PermissionOverrideRequest(BaseModel):
    add_permissions: List[str] = []     # permissions to grant
    remove_permissions: List[str] = []  # permissions to revoke

@user_router.put("/{email}/permissions")
async def override_user_permissions(email: str, body: PermissionOverrideRequest,
                                    current_user: dict = Depends(require_role(["super_admin", "admin"]))):
    """Override specific permissions for a user without changing their role."""
    ctx = tenant_context.get()
    shared = get_shared_db()

    user_tenant = await shared.user_tenants.find_one({
        "email": email.lower(), "tenant_id": ctx.tenant_id, "is_active": True
    })
    if not user_tenant:
        raise HTTPException(404, f"User '{email}' not found in tenant")

    await shared.permission_overrides.update_one(
        {"email": email.lower(), "tenant_id": ctx.tenant_id},
        {"$set": {
            "email": email.lower(),
            "tenant_id": ctx.tenant_id,
            "add_permissions": body.add_permissions,
            "remove_permissions": body.remove_permissions,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )
    return {"message": f"Permission overrides saved for {email}"}

@user_router.get("/{email}/permissions")
async def get_user_permissions(email: str, current_user: dict = Depends(require_role(["super_admin", "admin"]))):
    """Get effective permissions for a user (role + overrides)."""
    ctx = tenant_context.get()
    shared = get_shared_db()

    user_tenant = await shared.user_tenants.find_one({
        "email": email.lower(), "tenant_id": ctx.tenant_id, "is_active": True
    })
    if not user_tenant:
        raise HTTPException(404, f"User '{email}' not found in tenant")

    role_perms = set(resolve_permissions(user_tenant["role"]))

    overrides = await shared.permission_overrides.find_one({
        "email": email.lower(), "tenant_id": ctx.tenant_id
    }, {"_id": 0})

    if overrides:
        role_perms.update(overrides.get("add_permissions", []))
        role_perms -= set(overrides.get("remove_permissions", []))

    return {
        "email": email,
        "role": user_tenant["role"],
        "role_permissions": sorted(resolve_permissions(user_tenant["role"])),
        "overrides": overrides or {},
        "effective_permissions": sorted(role_perms),
    }
