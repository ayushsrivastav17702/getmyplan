"""
Self-service signup routes: register, verify-email, resend-verification.
These are PUBLIC endpoints (no tenant context required).
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime, timezone, timedelta
import secrets
import re
import os
import logging

from multi_tenant.tenant_db import get_shared_db, get_mongo_client, clear_tenant_cache
from multi_tenant.auth import _hash_password
from services.smtp_email_service import email_service
from middleware.security import limiter, AUTH_RATE_LIMIT, validate_input

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/signup", tags=["Signup"])


# ────────── Models ──────────

class SignupRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    subdomain: str = Field(..., min_length=3, max_length=50)

    @field_validator("subdomain")
    @classmethod
    def validate_subdomain(cls, v):
        v = v.lower()
        if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", v) and len(v) >= 3:
            if not re.match(r"^[a-z0-9-]+$", v):
                raise ValueError("Subdomain can only contain lowercase letters, numbers, and hyphens")
        reserved = {"www", "api", "app", "admin", "mail", "ftp", "localhost", "demo", "test"}
        if v in reserved:
            raise ValueError("Subdomain is reserved")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


# ────────── Helpers ──────────

def _trial_days() -> int:
    return int(os.environ.get("TRIAL_DAYS", "7"))


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# ────────── Routes ──────────

@router.post("/register")
@limiter.limit(AUTH_RATE_LIMIT)
async def register(body: SignupRequest, request: Request, background_tasks: BackgroundTasks):
    """Self-service registration: create user + tenant, send verification email."""
    # Input sanitization check
    input_issues = validate_input(body.model_dump())
    if input_issues:
        raise HTTPException(400, f"Invalid input: {'; '.join(input_issues)}")

    shared = get_shared_db()

    # Uniqueness checks
    if await shared.users.find_one({"email": body.email}):
        raise HTTPException(400, "Email already registered. Please sign in instead.")
    existing_tenant = await shared.tenants.find_one({"subdomain": body.subdomain})
    if existing_tenant:
        raise HTTPException(400, f"This workspace already exists. Ask your admin to invite you from the User Management page, or choose a different workspace URL.")

    tenant_id = _slug(body.company_name)
    # Ensure tenant_id is unique (handle collisions)
    base_id = tenant_id
    counter = 1
    while await shared.tenants.find_one({"tenant_id": tenant_id}):
        tenant_id = f"{base_id}_{counter}"
        counter += 1

    db_name = f"tenant_{tenant_id}"
    client = get_mongo_client()

    # Create tenant database with default config
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

    # Create user
    verification_token = secrets.token_urlsafe(32)
    verification_expiry = datetime.now(timezone.utc) + timedelta(hours=24)
    now_iso = datetime.now(timezone.utc).isoformat()

    user_result = await shared.users.insert_one({
        "email": body.email,
        "username": body.email.split("@")[0],
        "hashed_password": _hash_password(body.password),
        "full_name": body.company_name,
        "email_verified": False,
        "verification_token": verification_token,
        "verification_token_expiry": verification_expiry,
        "is_active": False,
        "created_at": now_iso,
    })
    user_id = str(user_result.inserted_id)

    # Create tenant
    trial_days = _trial_days()
    trial_start = datetime.now(timezone.utc)
    trial_end = trial_start + timedelta(days=trial_days)

    await shared.tenants.insert_one({
        "tenant_id": tenant_id,
        "company_name": body.company_name,
        "db_name": db_name,
        "subdomain": body.subdomain,
        "plan_type": "trial",
        "status": "pending_verification",
        "trial_start": trial_start.isoformat(),
        "trial_end": trial_end.isoformat(),
        "admin_user_id": user_id,
        "created_at": now_iso,
        "updated_at": now_iso,
    })

    # User-tenant mapping
    await shared.user_tenants.insert_one({
        "email": body.email,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "role": "admin",
        "is_active": False,
        "assigned_at": now_iso,
    })

    clear_tenant_cache()

    # Send verification email in background
    background_tasks.add_task(
        email_service.send_verification_email,
        to_email=body.email,
        company_name=body.company_name,
        token=verification_token,
    )

    return {
        "success": True,
        "message": "Registration successful! Please check your email to verify your account.",
        "email": body.email,
        "subdomain": body.subdomain,
        "tenant_id": tenant_id,
        "trial_days": trial_days,
    }


@router.post("/verify-email")
@limiter.limit(AUTH_RATE_LIMIT)
async def verify_email(body: VerifyEmailRequest, request: Request, background_tasks: BackgroundTasks):
    """Verify email token and activate account + tenant."""
    shared = get_shared_db()

    user = await shared.users.find_one({
        "verification_token": body.token,
        "verification_token_expiry": {"$gt": datetime.now(timezone.utc)},
    })
    if not user:
        raise HTTPException(400, "Invalid or expired verification token")

    if user.get("email_verified"):
        raise HTTPException(400, "Email already verified")

    # Activate user
    await shared.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "email_verified": True,
                "is_active": True,
                "verified_at": datetime.now(timezone.utc).isoformat(),
            },
            "$unset": {"verification_token": "", "verification_token_expiry": ""},
        },
    )

    # Find and activate tenant
    mapping = await shared.user_tenants.find_one({"user_id": str(user["_id"])})
    tenant = None
    if mapping:
        tenant = await shared.tenants.find_one({"tenant_id": mapping["tenant_id"]})
        if tenant:
            await shared.tenants.update_one(
                {"_id": tenant["_id"]},
                {"$set": {"status": "active", "updated_at": datetime.now(timezone.utc).isoformat()}},
            )
            await shared.user_tenants.update_one(
                {"user_id": str(user["_id"]), "tenant_id": tenant["tenant_id"]},
                {"$set": {"is_active": True}},
            )
            clear_tenant_cache(tenant["tenant_id"])

            # Send welcome email
            background_tasks.add_task(
                email_service.send_welcome_email,
                to_email=user["email"],
                company_name=tenant["company_name"],
            )

    return {
        "success": True,
        "message": "Email verified successfully! You can now log in.",
        "tenant_id": tenant["tenant_id"] if tenant else None,
        "subdomain": tenant["subdomain"] if tenant else None,
    }


@router.post("/resend-verification")
@limiter.limit("3/minute")
async def resend_verification(body: ResendVerificationRequest, request: Request, background_tasks: BackgroundTasks):
    """Resend verification email with rate limiting."""
    shared = get_shared_db()

    user = await shared.users.find_one({"email": body.email})
    if not user:
        raise HTTPException(404, "User not found")

    if user.get("email_verified"):
        raise HTTPException(400, "Email already verified")

    # Rate limit: 60 seconds
    last_resend = user.get("last_verification_resend")
    if last_resend:
        if isinstance(last_resend, str):
            last_resend = datetime.fromisoformat(last_resend)
        elif not last_resend.tzinfo:
            last_resend = last_resend.replace(tzinfo=timezone.utc)
        elapsed = (datetime.now(timezone.utc) - last_resend).total_seconds()
        if elapsed < 60:
            raise HTTPException(429, "Please wait 60 seconds before requesting again")

    # New token
    new_token = secrets.token_urlsafe(32)
    new_expiry = datetime.now(timezone.utc) + timedelta(hours=24)

    await shared.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "verification_token": new_token,
            "verification_token_expiry": new_expiry,
            "last_verification_resend": datetime.now(timezone.utc).isoformat(),
        }},
    )

    # Get tenant for company name
    mapping = await shared.user_tenants.find_one({"user_id": str(user["_id"])})
    company_name = "Your Company"
    if mapping:
        tenant = await shared.tenants.find_one({"tenant_id": mapping["tenant_id"]})
        if tenant:
            company_name = tenant["company_name"]

    background_tasks.add_task(
        email_service.send_verification_email,
        to_email=body.email,
        company_name=company_name,
        token=new_token,
    )

    return {"success": True, "message": "Verification email resent"}
