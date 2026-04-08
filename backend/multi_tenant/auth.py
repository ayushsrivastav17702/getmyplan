"""
JWT Authentication routes for multi-tenant platform.
Users are stored in shared DB users collection, mapped to tenants via user_tenants.
"""
from fastapi import APIRouter, HTTPException, Request, Depends, status
from pydantic import BaseModel, EmailStr, Field
from pymongo.errors import OperationFailure
from typing import Optional
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt as pyjwt
import os
import logging

from .tenant_db import get_shared_db, tenant_context

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])

JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

def _refresh_jwt_secret():
    """Re-read JWT_SECRET after load_dotenv has been called."""
    global JWT_SECRET
    JWT_SECRET = os.environ.get("JWT_SECRET", "")
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET environment variable is not set")


# ---------- models ----------

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# ---------- helpers ----------

def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def _create_token(payload: dict) -> str:
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload["iat"] = datetime.now(timezone.utc)
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    return pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


async def _safe_db_op(coro, fallback=None, op_name="db_op"):
    """Execute a DB operation, handling MongoDB permission errors gracefully."""
    try:
        return await coro
    except OperationFailure as e:
        if e.code == 13:  # Unauthorized
            logger.error(f"MongoDB permission denied during {op_name}: {e.details.get('errmsg', str(e))}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable. Please try again later.",
            )
        raise


async def _log_audit_safe(shared, action: str, **kwargs):
    """Log audit event — fails silently if unauthorized."""
    try:
        await shared.audit_logs.insert_one({
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        })
    except OperationFailure as e:
        if e.code == 13:
            logger.warning(f"Audit log skipped (unauthorized): {action}")
        else:
            logger.error(f"Audit log failed: {e}")
    except Exception as e:
        logger.error(f"Audit log unexpected error: {e}")


async def get_current_user(request: Request) -> dict:
    """Dependency: extract and validate user from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(auth[7:])
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


# ---------- routes ----------

@auth_router.post("/register")
async def register(body: RegisterRequest, request: Request):
    """Register a new user for the current tenant."""
    ctx = tenant_context.get()
    if not ctx:
        raise HTTPException(status_code=400, detail="Tenant context required")

    shared = get_shared_db()

    existing = await _safe_db_op(
        shared.users.find_one({"email": body.email}),
        op_name="register_find_user",
    )
    if existing:
        mapping = await _safe_db_op(
            shared.user_tenants.find_one({"email": body.email, "tenant_id": ctx.tenant_id}),
            op_name="register_find_mapping",
        )
        if mapping:
            raise HTTPException(status_code=400, detail="User already registered for this tenant")
        user_id = str(existing["_id"])
    else:
        result = await _safe_db_op(
            shared.users.insert_one({
                "email": body.email,
                "username": body.username,
                "hashed_password": _hash_password(body.password),
                "full_name": body.full_name or body.username,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }),
            op_name="register_insert_user",
        )
        user_id = str(result.inserted_id)

    await _safe_db_op(
        shared.user_tenants.update_one(
            {"email": body.email, "tenant_id": ctx.tenant_id},
            {"$set": {
                "email": body.email,
                "user_id": user_id,
                "tenant_id": ctx.tenant_id,
                "role": "viewer",
                "is_active": True,
                "assigned_at": datetime.now(timezone.utc).isoformat(),
            }},
            upsert=True,
        ),
        op_name="register_upsert_mapping",
    )

    token = _create_token({
        "user_id": user_id,
        "email": body.email,
        "tenant_id": ctx.tenant_id,
        "role": "viewer",
    })

    return TokenResponse(
        access_token=token,
        user={
            "email": body.email,
            "username": body.username,
            "full_name": body.full_name or body.username,
            "role": "viewer",
            "tenant_id": ctx.tenant_id,
        },
    )


@auth_router.post("/login")
async def login(body: LoginRequest, request: Request):
    """Login user — auto-resolves tenant from email. Handles MongoDB permission errors gracefully."""
    shared = get_shared_db()

    try:
        # ── STEP 1: Find User ──
        try:
            user = await shared.users.find_one({"email": body.email})
        except OperationFailure as e:
            if e.code == 13:
                logger.error(f"MongoDB permission denied reading users: {e.details.get('errmsg', str(e))}")
                await _log_audit_safe(shared, "login_error", error_type="database_permission", email=body.email)
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                    detail="Service temporarily unavailable. Please try again later.")
            raise

        if not user:
            await _log_audit_safe(shared, "login_failed", error_type="user_not_found", email=body.email)
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not _verify_password(body.password, user["hashed_password"]):
            await _log_audit_safe(shared, "login_failed", error_type="invalid_password", email=body.email)
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # ── STEP 2: Check Email Verification ──
        if user.get("email_verified") is False:
            await _log_audit_safe(shared, "login_failed", error_type="email_unverified", email=body.email)
            raise HTTPException(status_code=403,
                                detail="Please verify your email before logging in. Check your inbox for the verification link.")

        # ── STEP 3: Resolve Tenant ──
        ctx = tenant_context.get(None)
        if ctx:
            resolved_tenant_id = ctx.tenant_id
        else:
            try:
                mapping = await shared.user_tenants.find_one(
                    {"email": body.email, "is_active": True},
                    {"_id": 0, "tenant_id": 1},
                )
            except OperationFailure as e:
                if e.code == 13:
                    logger.error(f"MongoDB permission denied reading user_tenants: {e.details.get('errmsg', str(e))}")
                    await _log_audit_safe(shared, "login_error", error_type="database_permission", email=body.email)
                    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                        detail="Service temporarily unavailable. Please try again later.")
                raise
            if not mapping:
                await _log_audit_safe(shared, "login_failed", error_type="no_active_workspace", email=body.email)
                raise HTTPException(status_code=401, detail="No active workspace found for this email")
            resolved_tenant_id = mapping["tenant_id"]

        # ── STEP 4: Verify Tenant Membership ──
        try:
            mapping = await shared.user_tenants.find_one({
                "email": body.email,
                "tenant_id": resolved_tenant_id,
                "is_active": True,
            })
        except OperationFailure as e:
            if e.code == 13:
                logger.error(f"MongoDB permission denied verifying membership: {e.details.get('errmsg', str(e))}")
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                    detail="Service temporarily unavailable. Please try again later.")
            raise

        if not mapping:
            await _log_audit_safe(shared, "login_failed", error_type="user_not_in_tenant",
                                  email=body.email, tenant_id=resolved_tenant_id)
            raise HTTPException(status_code=401, detail="User not authorized for this workspace")

        # ── STEP 5: Check Tenant Status ──
        try:
            tenant_doc = await shared.tenants.find_one({"tenant_id": resolved_tenant_id})
        except OperationFailure as e:
            if e.code == 13:
                logger.error(f"MongoDB permission denied reading tenants: {e.details.get('errmsg', str(e))}")
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                    detail="Service temporarily unavailable. Please try again later.")
            raise

        if tenant_doc:
            tenant_status = tenant_doc.get("status", "active")
            if tenant_status == "pending_verification":
                await _log_audit_safe(shared, "login_failed", error_type="tenant_pending_verification",
                                      email=body.email, tenant_id=resolved_tenant_id)
                raise HTTPException(status_code=403,
                                    detail="Please verify your workspace email before logging in. Check your inbox.")
            if tenant_status == "suspended":
                await _log_audit_safe(shared, "login_failed", error_type="tenant_suspended",
                                      email=body.email, tenant_id=resolved_tenant_id)
                raise HTTPException(status_code=403, detail="This workspace has been suspended. Please contact support.")

        # ── STEP 6: Trial Checking ──
        trial_info = None
        if tenant_doc and tenant_doc.get("plan_type") == "trial" and tenant_doc.get("trial_end"):
            trial_end_str = tenant_doc["trial_end"]
            trial_end = datetime.fromisoformat(trial_end_str) if isinstance(trial_end_str, str) else trial_end_str
            if trial_end.tzinfo is None:
                trial_end = trial_end.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            days_remaining = (trial_end - now).days
            if days_remaining <= 0:
                grace_end = trial_end + timedelta(days=3)
                if now > grace_end:
                    raise HTTPException(status_code=403, detail="Trial expired. Please upgrade your plan.")
            trial_info = {
                "days_remaining": max(0, days_remaining),
                "trial_end": trial_end.isoformat(),
                "is_trial_active": days_remaining > 0,
                "plan_type": "trial",
            }

        # ── STEP 7: Build Response ──
        role = mapping.get("role", "viewer")
        must_change_pw = user.get("must_change_password", False)

        token = _create_token({
            "user_id": str(user["_id"]),
            "email": user["email"],
            "tenant_id": resolved_tenant_id,
            "role": role,
        })

        from .rbac import resolve_permissions
        perms = resolve_permissions(role)

        from core.plan_access import get_plan_info
        plan_type = tenant_doc.get("plan_type", "starter") if tenant_doc else "starter"
        plan_info = get_plan_info(plan_type)

        # Update last login (non-critical)
        try:
            await shared.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}},
            )
        except Exception:
            pass

        # Log success
        await _log_audit_safe(shared, "login_success", email=body.email,
                              tenant_id=resolved_tenant_id, role=role)

        response = {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "email": user["email"],
                "username": user.get("username", ""),
                "full_name": user.get("full_name", ""),
                "role": role,
                "tenant_id": resolved_tenant_id,
                "permissions": perms,
            },
            "tenant_id": resolved_tenant_id,
            "plan_info": plan_info,
            "plan_type": plan_type,
        }
        if trial_info:
            response["trial_info"] = trial_info
        if must_change_pw:
            response["must_change_password"] = True

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected login error for {body.email}: {e}")
        await _log_audit_safe(shared, "login_error", error_type="system_error",
                              email=body.email, error_message=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="An unexpected error occurred. Please try again.")


@auth_router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "tenant_id": user.get("tenant_id"),
        "role": user.get("role"),
    }


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


@auth_router.post("/change-password")
async def change_password(body: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    """Authenticated user changes their own password. Also clears must_change_password flag."""
    shared = get_shared_db()
    try:
        user = await shared.users.find_one({"email": current_user["email"]})
    except OperationFailure as e:
        if e.code == 13:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail="Service temporarily unavailable. Please try again later.")
        raise

    if not user:
        raise HTTPException(404, "User not found")

    if not _verify_password(body.current_password, user["hashed_password"]):
        raise HTTPException(400, "Current password is incorrect")

    if body.current_password == body.new_password:
        raise HTTPException(400, "New password must be different from current password")

    try:
        await shared.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "hashed_password": _hash_password(body.new_password),
                    "password_updated_at": datetime.now(timezone.utc).isoformat(),
                },
                "$unset": {"must_change_password": ""},
            },
        )
    except OperationFailure as e:
        if e.code == 13:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail="Service temporarily unavailable. Please try again later.")
        raise

    return {"success": True, "message": "Password changed successfully"}
