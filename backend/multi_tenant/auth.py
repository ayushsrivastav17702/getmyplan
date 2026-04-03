"""
JWT Authentication routes for multi-tenant platform.
Users are stored in merch_shared.users, mapped to tenants via user_tenants.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr, Field
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

    existing = await shared.users.find_one({"email": body.email})
    if existing:
        # Check if already mapped to this tenant
        mapping = await shared.user_tenants.find_one({
            "email": body.email,
            "tenant_id": ctx.tenant_id,
        })
        if mapping:
            raise HTTPException(status_code=400, detail="User already registered for this tenant")
        user_id = str(existing["_id"])
    else:
        result = await shared.users.insert_one({
            "email": body.email,
            "username": body.username,
            "hashed_password": _hash_password(body.password),
            "full_name": body.full_name or body.username,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        user_id = str(result.inserted_id)

    # Map user to tenant
    await shared.user_tenants.update_one(
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


@auth_router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request):
    """Login user to the current tenant."""
    ctx = tenant_context.get()
    if not ctx:
        raise HTTPException(status_code=400, detail="Tenant context required")

    shared = get_shared_db()
    user = await shared.users.find_one({"email": body.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not _verify_password(body.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check tenant membership
    mapping = await shared.user_tenants.find_one({
        "email": body.email,
        "tenant_id": ctx.tenant_id,
        "is_active": True,
    })
    if not mapping:
        raise HTTPException(status_code=401, detail="User not authorized for this tenant")

    role = mapping.get("role", "viewer")
    token = _create_token({
        "user_id": str(user["_id"]),
        "email": user["email"],
        "tenant_id": ctx.tenant_id,
        "role": role,
    })

    # Resolve permissions for this role
    from .rbac import resolve_permissions
    perms = resolve_permissions(role)

    return TokenResponse(
        access_token=token,
        user={
            "email": user["email"],
            "username": user.get("username", ""),
            "full_name": user.get("full_name", ""),
            "role": role,
            "tenant_id": ctx.tenant_id,
            "permissions": perms,
        },
    )


@auth_router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "tenant_id": user.get("tenant_id"),
        "role": user.get("role"),
    }
