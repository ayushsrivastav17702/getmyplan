"""
Tenant identification middleware.
Resolves tenant from: X-Tenant-ID header > JWT token > default demo tenant.
Sets tenant_context ContextVar for the duration of the request.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Optional
import jwt as pyjwt
import os
import logging

from .tenant_db import (
    tenant_context,
    TenantContext,
    resolve_tenant,
    resolve_tenant_by_subdomain,
    get_shared_db,
    get_mongo_client,
)

logger = logging.getLogger(__name__)

# Paths that should bypass tenant resolution entirely
PUBLIC_PATHS = {
    "/api/health",
    "/api/tenants/create",
    "/api/tenants/check-subdomain",
    "/docs",
    "/openapi.json",
}

JWT_SECRET = os.environ.get("JWT_SECRET", "merch-saas-secret-change-me")
JWT_ALGORITHM = "HS256"


class TenantMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip tenant resolution for public endpoints
        if path in PUBLIC_PATHS or not path.startswith("/api"):
            return await call_next(request)

        tenant_id = await self._resolve_tenant_id(request)

        if not tenant_id:
            return JSONResponse(
                status_code=400,
                content={"detail": "Tenant identification required. Provide X-Tenant-ID header or authenticate."},
            )

        tenant_doc = await resolve_tenant(tenant_id)
        if not tenant_doc:
            return JSONResponse(status_code=403, content={"detail": f"Tenant '{tenant_id}' not found or inactive."})

        ctx = TenantContext(
            tenant_id=tenant_doc["tenant_id"],
            db_name=tenant_doc["db_name"],
            company_name=tenant_doc["company_name"],
            plan_type=tenant_doc["plan_type"],
        )
        token = tenant_context.set(ctx)
        request.state.tenant = ctx

        try:
            response = await call_next(request)
        finally:
            tenant_context.reset(token)

        return response

    # ------------------------------------------------------------------

    async def _resolve_tenant_id(self, request: Request) -> Optional[str]:
        # 1. Explicit header
        tid = request.headers.get("X-Tenant-ID")
        if tid:
            return tid

        # 2. JWT bearer token
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            try:
                payload = pyjwt.decode(auth[7:], JWT_SECRET, algorithms=[JWT_ALGORITHM])
                return payload.get("tenant_id")
            except Exception:
                pass

        # 3. Subdomain (tenant.domain.com)
        host = request.headers.get("host", "")
        parts = host.split(".")
        if len(parts) >= 3:
            subdomain = parts[0]
            skip = {"www", "app", "api"}
            if subdomain not in skip:
                doc = await resolve_tenant_by_subdomain(subdomain)
                if doc:
                    return doc["tenant_id"]

        # 4. Fallback to "demo" tenant (backward compat / development)
        demo = await resolve_tenant("demo")
        if demo:
            return "demo"

        return None
