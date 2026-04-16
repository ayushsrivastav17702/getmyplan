"""
JWT Authentication routes for multi-tenant platform.
Users are stored in shared DB users collection, mapped to tenants via user_tenants.
Supports MFA: TOTP (Authenticator App) + Email OTP.
"""
from fastapi import APIRouter, HTTPException, Request, Depends, status
from pydantic import BaseModel, EmailStr, Field
from pymongo.errors import OperationFailure
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt as pyjwt
import os
import logging
import secrets

from .tenant_db import get_shared_db, tenant_context
from services.mfa_service import (
    generate_totp_secret, get_totp_uri, generate_qr_base64,
    verify_totp, generate_otp, hash_otp, verify_otp_hash,
    send_mfa_otp_email, MFA_TOKEN_EXPIRY_MINUTES, OTP_EXPIRY_SECONDS, MAX_OTP_ATTEMPTS,
)

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])

JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24
MFA_JWT_EXPIRE_MINUTES = 5

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

def _create_mfa_token(payload: dict) -> str:
    """Short-lived JWT for MFA challenge (5 min). token_type='mfa'."""
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=MFA_JWT_EXPIRE_MINUTES)
    payload["iat"] = datetime.now(timezone.utc)
    payload["token_type"] = "mfa"
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def _decode_mfa_token(token: str) -> dict:
    """Decode and verify an MFA-only token."""
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="MFA session expired. Please login again.")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid MFA token")
    if payload.get("token_type") != "mfa":
        raise HTTPException(status_code=401, detail="Invalid token type for MFA verification")
    return payload


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

    # Check plan user limit
    from core.plan_access import check_plan_limit
    allowed, current, limit, plan = await check_plan_limit(shared, ctx.tenant_id, "users")
    if not allowed:
        raise HTTPException(status_code=400, detail=f"User limit reached ({current}/{limit}) for {plan} plan. Please upgrade to add more users.")

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

        # ── STEP 7: MFA Check ──
        role = mapping.get("role", "viewer")
        user_mfa_enabled = user.get("mfa_enabled", False)
        user_totp_verified = user.get("totp_verified", False)

        # Check tenant-level MFA enforcement
        tenant_mfa_enforced = False
        if tenant_doc:
            tenant_mfa_enforced = tenant_doc.get("mfa_enforced", False)

        if user_mfa_enabled and user_totp_verified:
            # User has MFA set up — issue MFA challenge token
            mfa_token = _create_mfa_token({
                "user_id": str(user["_id"]),
                "email": user["email"],
                "tenant_id": resolved_tenant_id,
                "role": role,
            })
            await _log_audit_safe(shared, "mfa_challenge_issued", email=body.email,
                                  tenant_id=resolved_tenant_id)
            return {
                "mfa_required": True,
                "mfa_token": mfa_token,
                "mfa_methods": ["totp", "email_otp"],
                "expires_in": MFA_JWT_EXPIRE_MINUTES * 60,
            }

        # ── STEP 8: Build Full Response ──
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
            "mfa_enforced": tenant_mfa_enforced and not user_mfa_enabled,
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


# ═══════════════════════════════════════════════════════════
# MFA ENDPOINTS
# ═══════════════════════════════════════════════════════════

# -- MFA request / response models --

class MFAVerifyLoginRequest(BaseModel):
    mfa_token: str
    totp_code: str = Field(..., min_length=6, max_length=6)

class MFAEmailOTPRequest(BaseModel):
    mfa_token: str

class MFAEmailOTPVerifyRequest(BaseModel):
    mfa_token: str
    otp_code: str = Field(..., min_length=6, max_length=6)

class MFASetupVerifyRequest(BaseModel):
    totp_code: str = Field(..., min_length=6, max_length=6)
    setup_token: str

class MFADisableRequest(BaseModel):
    password: str


async def _complete_mfa_login(payload: dict, shared):
    """Shared helper: issue full access token after MFA verification."""
    from .rbac import resolve_permissions
    from core.plan_access import get_plan_info

    user = await shared.users.find_one({"email": payload["email"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    tenant_id = payload["tenant_id"]
    role = payload["role"]

    token = _create_token({
        "user_id": payload["user_id"],
        "email": payload["email"],
        "tenant_id": tenant_id,
        "role": role,
    })

    perms = resolve_permissions(role)

    tenant_doc = await shared.tenants.find_one({"tenant_id": tenant_id})
    plan_type = tenant_doc.get("plan_type", "starter") if tenant_doc else "starter"
    plan_info = get_plan_info(plan_type)

    # Update last login
    try:
        await shared.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}},
        )
    except Exception:
        pass

    trial_info = None
    if tenant_doc and tenant_doc.get("plan_type") == "trial" and tenant_doc.get("trial_end"):
        trial_end_str = tenant_doc["trial_end"]
        trial_end = datetime.fromisoformat(trial_end_str) if isinstance(trial_end_str, str) else trial_end_str
        if trial_end.tzinfo is None:
            trial_end = trial_end.replace(tzinfo=timezone.utc)
        days_remaining = (trial_end - datetime.now(timezone.utc)).days
        trial_info = {
            "days_remaining": max(0, days_remaining),
            "trial_end": trial_end.isoformat(),
            "is_trial_active": days_remaining > 0,
            "plan_type": "trial",
        }

    await _log_audit_safe(shared, "login_success_mfa", email=payload["email"],
                          tenant_id=tenant_id, role=role)

    response = {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": user["email"],
            "username": user.get("username", ""),
            "full_name": user.get("full_name", ""),
            "role": role,
            "tenant_id": tenant_id,
            "permissions": perms,
        },
        "tenant_id": tenant_id,
        "plan_info": plan_info,
        "plan_type": plan_type,
    }
    if trial_info:
        response["trial_info"] = trial_info
    if user.get("must_change_password"):
        response["must_change_password"] = True
    return response


# ── MFA Login Verification: TOTP ──

@auth_router.post("/mfa/verify-totp")
async def mfa_verify_totp(body: MFAVerifyLoginRequest):
    """Verify TOTP code during login. Exchanges mfa_token + valid TOTP for full access token."""
    payload = _decode_mfa_token(body.mfa_token)
    shared = get_shared_db()

    user = await shared.users.find_one({"email": payload["email"]})
    if not user or not user.get("totp_verified"):
        raise HTTPException(status_code=401, detail="TOTP not configured")

    if not verify_totp(user["totp_secret"], body.totp_code):
        await _log_audit_safe(shared, "mfa_totp_failed", email=payload["email"])
        raise HTTPException(status_code=401, detail="Invalid authenticator code. Please try again.")

    return await _complete_mfa_login(payload, shared)


# ── MFA Login Verification: Email OTP ──

@auth_router.post("/mfa/send-email-otp")
async def mfa_send_email_otp(body: MFAEmailOTPRequest):
    """Send a one-time email code as an alternative to TOTP during login."""
    payload = _decode_mfa_token(body.mfa_token)
    shared = get_shared_db()

    user = await shared.users.find_one({"email": payload["email"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Rate limit: check for recent OTP
    existing = await shared.mfa_sessions.find_one({
        "email": payload["email"],
        "type": "email_otp",
        "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()},
    })
    if existing:
        created = datetime.fromisoformat(existing["created_at"])
        if (datetime.now(timezone.utc) - created).total_seconds() < 60:
            raise HTTPException(status_code=429, detail="Please wait before requesting another code.")

    otp_code = generate_otp()
    otp_hashed = hash_otp(otp_code)

    from services.smtp_email_service import email_service
    sent = send_mfa_otp_email(email_service, user["email"], otp_code,
                               user.get("full_name", user.get("username", "User")))
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send verification email. Please try again.")

    # Store session
    await shared.mfa_sessions.delete_many({"email": payload["email"], "type": "email_otp"})
    await shared.mfa_sessions.insert_one({
        "email": payload["email"],
        "type": "email_otp",
        "otp_hash": otp_hashed,
        "attempts": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=OTP_EXPIRY_SECONDS)).isoformat(),
    })

    await _log_audit_safe(shared, "mfa_email_otp_sent", email=payload["email"])
    return {"message": "Verification code sent to your email", "expires_in": OTP_EXPIRY_SECONDS}


@auth_router.post("/mfa/verify-email-otp")
async def mfa_verify_email_otp(body: MFAEmailOTPVerifyRequest):
    """Verify email OTP during login. Exchanges mfa_token + valid OTP for full access token."""
    payload = _decode_mfa_token(body.mfa_token)
    shared = get_shared_db()

    session = await shared.mfa_sessions.find_one({
        "email": payload["email"],
        "type": "email_otp",
    })
    if not session:
        raise HTTPException(status_code=401, detail="No active email code. Please request a new one.")

    # Check expiry
    if datetime.now(timezone.utc).isoformat() > session["expires_at"]:
        await shared.mfa_sessions.delete_one({"_id": session["_id"]})
        raise HTTPException(status_code=401, detail="Code expired. Please request a new one.")

    # Check attempt limit
    if session.get("attempts", 0) >= MAX_OTP_ATTEMPTS:
        await shared.mfa_sessions.delete_one({"_id": session["_id"]})
        raise HTTPException(status_code=429, detail="Too many attempts. Please request a new code.")

    if not verify_otp_hash(body.otp_code, session["otp_hash"]):
        await shared.mfa_sessions.update_one(
            {"_id": session["_id"]},
            {"$inc": {"attempts": 1}},
        )
        await _log_audit_safe(shared, "mfa_email_otp_failed", email=payload["email"])
        raise HTTPException(status_code=401, detail="Invalid code. Please try again.")

    await shared.mfa_sessions.delete_one({"_id": session["_id"]})
    return await _complete_mfa_login(payload, shared)


# ── MFA Setup: TOTP ──

@auth_router.post("/mfa/setup-totp")
async def mfa_setup_totp(current_user: dict = Depends(get_current_user)):
    """Generate TOTP secret + QR code for authenticator app setup."""
    shared = get_shared_db()
    user = await shared.users.find_one({"email": current_user["email"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("mfa_enabled") and user.get("totp_verified"):
        raise HTTPException(status_code=400, detail="MFA is already enabled. Disable it first to re-configure.")

    secret = generate_totp_secret()
    uri = get_totp_uri(secret, user["email"])
    qr_code = generate_qr_base64(uri)

    setup_token = secrets.token_urlsafe(32)

    # Store pending setup
    await shared.mfa_sessions.delete_many({"email": user["email"], "type": "totp_setup"})
    await shared.mfa_sessions.insert_one({
        "email": user["email"],
        "type": "totp_setup",
        "totp_secret": secret,
        "setup_token": setup_token,
        "attempts": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
    })

    return {
        "qr_code": qr_code,
        "secret": secret,
        "setup_token": setup_token,
    }


@auth_router.post("/mfa/verify-setup")
async def mfa_verify_setup(body: MFASetupVerifyRequest, current_user: dict = Depends(get_current_user)):
    """Verify TOTP code to confirm authenticator app setup. Enables MFA on the user account."""
    shared = get_shared_db()

    session = await shared.mfa_sessions.find_one({
        "email": current_user["email"],
        "type": "totp_setup",
        "setup_token": body.setup_token,
    })
    if not session:
        raise HTTPException(status_code=400, detail="No pending TOTP setup. Please start setup again.")

    if datetime.now(timezone.utc).isoformat() > session["expires_at"]:
        await shared.mfa_sessions.delete_one({"_id": session["_id"]})
        raise HTTPException(status_code=400, detail="Setup session expired. Please start again.")

    if session.get("attempts", 0) >= 5:
        await shared.mfa_sessions.delete_one({"_id": session["_id"]})
        raise HTTPException(status_code=429, detail="Too many attempts. Please restart setup.")

    if not verify_totp(session["totp_secret"], body.totp_code):
        await shared.mfa_sessions.update_one(
            {"_id": session["_id"]},
            {"$inc": {"attempts": 1}},
        )
        raise HTTPException(status_code=400, detail="Invalid code. Please check your authenticator app and try again.")

    # Enable MFA on user
    await shared.users.update_one(
        {"email": current_user["email"]},
        {"$set": {
            "mfa_enabled": True,
            "totp_secret": session["totp_secret"],
            "totp_verified": True,
            "mfa_updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    await shared.mfa_sessions.delete_one({"_id": session["_id"]})
    await _log_audit_safe(shared, "mfa_enabled", email=current_user["email"])

    return {"success": True, "message": "Two-factor authentication enabled successfully"}


# ── MFA Disable ──

@auth_router.post("/mfa/disable")
async def mfa_disable(body: MFADisableRequest, current_user: dict = Depends(get_current_user)):
    """Disable MFA. Requires current password for security."""
    shared = get_shared_db()
    user = await shared.users.find_one({"email": current_user["email"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.get("mfa_enabled"):
        raise HTTPException(status_code=400, detail="MFA is not currently enabled")

    if not _verify_password(body.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect password")

    # Check tenant enforcement
    tenant_id = current_user.get("tenant_id")
    if tenant_id:
        tenant_doc = await shared.tenants.find_one({"tenant_id": tenant_id})
        if tenant_doc and tenant_doc.get("mfa_enforced"):
            raise HTTPException(status_code=403,
                                detail="Your workspace requires MFA. Contact your admin to change this policy.")

    await shared.users.update_one(
        {"email": current_user["email"]},
        {"$set": {
            "mfa_enabled": False,
            "totp_secret": None,
            "totp_verified": False,
            "mfa_updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    await _log_audit_safe(shared, "mfa_disabled", email=current_user["email"])
    return {"success": True, "message": "Two-factor authentication has been disabled"}


# ── MFA Status ──

@auth_router.get("/mfa/status")
async def mfa_status(current_user: dict = Depends(get_current_user)):
    """Get MFA status for the current user."""
    shared = get_shared_db()
    user = await shared.users.find_one({"email": current_user["email"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    tenant_id = current_user.get("tenant_id")
    tenant_mfa_enforced = False
    if tenant_id:
        tenant_doc = await shared.tenants.find_one({"tenant_id": tenant_id})
        if tenant_doc:
            tenant_mfa_enforced = tenant_doc.get("mfa_enforced", False)

    return {
        "mfa_enabled": user.get("mfa_enabled", False),
        "totp_verified": user.get("totp_verified", False),
        "mfa_updated_at": user.get("mfa_updated_at"),
        "tenant_mfa_enforced": tenant_mfa_enforced,
    }


# ── Tenant MFA Enforcement (Admin only) ──

class TenantMFAEnforceRequest(BaseModel):
    enforce: bool

@auth_router.post("/mfa/tenant-enforce")
async def mfa_tenant_enforce(body: TenantMFAEnforceRequest, current_user: dict = Depends(get_current_user)):
    """Tenant admin: enable/disable MFA enforcement for all users in the workspace."""
    if current_user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Only admins can change MFA enforcement policy")

    shared = get_shared_db()
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")

    await shared.tenants.update_one(
        {"tenant_id": tenant_id},
        {"$set": {"mfa_enforced": body.enforce}},
    )
    action = "mfa_enforcement_enabled" if body.enforce else "mfa_enforcement_disabled"
    await _log_audit_safe(shared, action, email=current_user["email"], tenant_id=tenant_id)
    return {"success": True, "mfa_enforced": body.enforce}
