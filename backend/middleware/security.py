"""
Enterprise Security Middleware for GetMyPlan.
Provides: rate limiting, security headers, request size limits,
structured logging, global error handling, and input sanitization.
"""
import time
import uuid
import re
import logging
import json
import traceback
from datetime import datetime, timezone
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


# K8s probe paths that every middleware must pass through untouched — kept in
# sync with `HEALTH_PROBE_PATHS` in server.py. See the comment there for why.
HEALTH_PROBE_PATHS = frozenset({"/health", "/healthz", "/readyz", "/livez"})


# ─── 1. Rate Limiter (per IP + per tenant) ───

def _get_rate_limit_key(request: Request) -> str:
    """Composite key: real client IP + tenant for per-tenant rate limiting."""
    # In K8s, use X-Forwarded-For to get real client IP
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = get_remote_address(request)
    tenant = request.headers.get("x-tenant-id", "anon")
    return f"{ip}:{tenant}"


limiter = Limiter(
    key_func=_get_rate_limit_key,
    default_limits=["200/minute"],
    storage_uri="memory://",
)

# Endpoint-specific limits (applied via decorators or in middleware)
AUTH_RATE_LIMIT = "30/minute"      # Login/signup: prevent brute force
UPLOAD_RATE_LIMIT = "20/minute"    # File uploads: prevent abuse
GENERAL_RATE_LIMIT = "200/minute"  # General API calls


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom 429 response for rate limit violations."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please slow down.",
            "retry_after": str(exc.detail).split("per")[0].strip() if exc.detail else "60 seconds",
        },
        headers={"Retry-After": "60"},
    )


# ─── 2. Security Headers Middleware ───

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds enterprise-grade security headers to every response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # K8s probes — pass through untouched, no header injection needed
        if request.url.path in HEALTH_PROBE_PATHS:
            return await call_next(request)
        response = await call_next(request)

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Enable XSS filter
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # HSTS (Strict Transport Security) — 1 year
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Permissions policy
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        # Content Security Policy (relaxed for API)
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
        # Remove server header
        if "server" in response.headers:
            del response.headers["server"]
        # Cache control for API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        return response


# ─── 3. Request Size Limit Middleware ───

MAX_BODY_SIZE = 50 * 1024 * 1024  # 50 MB for file uploads
MAX_JSON_SIZE = 1 * 1024 * 1024   # 1 MB for JSON payloads


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject oversized request bodies to prevent resource exhaustion."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in HEALTH_PROBE_PATHS:
            return await call_next(request)
        content_length = request.headers.get("content-length")
        if content_length:
            size = int(content_length)
            content_type = request.headers.get("content-type", "")

            if "multipart/form-data" in content_type:
                if size > MAX_BODY_SIZE:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": f"File too large. Maximum size is {MAX_BODY_SIZE // (1024*1024)}MB."},
                    )
            else:
                if size > MAX_JSON_SIZE:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": f"Request body too large. Maximum size is {MAX_JSON_SIZE // (1024*1024)}MB."},
                    )

        return await call_next(request)


# ─── 4. Structured Logging with Correlation IDs ───

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Adds correlation IDs to every request for traceability.
    Logs request/response metadata in structured JSON format.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in HEALTH_PROBE_PATHS:
            return await call_next(request)
        correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4())[:8])
        tenant_id = request.headers.get("x-tenant-id", "-")

        request.state.correlation_id = correlation_id
        start_time = time.time()

        response = await call_next(request)

        duration_ms = round((time.time() - start_time) * 1000, 1)

        # Add correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-Duration"] = f"{duration_ms}ms"

        # Structured log (skip health checks & static assets to reduce noise)
        path = request.url.path
        if path not in ("/api/health", "/api/", "/favicon.ico") and not path.startswith("/static"):
            log_data = {
                "type": "request",
                "correlation_id": correlation_id,
                "method": request.method,
                "path": path,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "tenant": tenant_id,
                "ip": get_remote_address(request),
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            if response.status_code >= 500:
                logging.getLogger("audit").error(json.dumps(log_data))
            elif response.status_code >= 400:
                logging.getLogger("audit").warning(json.dumps(log_data))
            else:
                logging.getLogger("audit").info(json.dumps(log_data))

        return response


# ─── 5. Global Error Handler (no stack traces in production) ───

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Catches unhandled exceptions and returns clean JSON errors.
    Never leaks stack traces or internal details to clients.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in HEALTH_PROBE_PATHS:
            return await call_next(request)
        try:
            return await call_next(request)
        except Exception as exc:
            correlation_id = getattr(request.state, "correlation_id", "unknown")

            # Log the full traceback internally
            logging.getLogger("error").error(
                "Unhandled exception [%s] %s %s: %s\n%s",
                correlation_id,
                request.method,
                request.url.path,
                str(exc),
                traceback.format_exc(),
            )

            # Return a clean error to the client — NO stack traces
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "An internal error occurred. Please try again later.",
                    "correlation_id": correlation_id,
                },
                headers={"X-Correlation-ID": correlation_id},
            )


# ─── 6. Input Sanitization Utilities ───

# Patterns that indicate potential injection attacks
_NOSQL_INJECTION_PATTERNS = re.compile(r'(\$where|\$gt|\$lt|\$ne|\$regex|\$exists|\$or|\$and)')
_XSS_PATTERNS = re.compile(r'<script|javascript:|on\w+\s*=', re.IGNORECASE)
_PATH_TRAVERSAL = re.compile(r'\.\./|\.\.\\')


def sanitize_string(value: str) -> str:
    """Remove potentially dangerous characters from user input."""
    if not isinstance(value, str):
        return value
    # Strip null bytes
    value = value.replace('\x00', '')
    # Trim excessive whitespace
    value = ' '.join(value.split())
    return value


def check_nosql_injection(data: dict) -> bool:
    """Check if a dictionary contains NoSQL injection patterns."""
    def _scan(obj):
        if isinstance(obj, str):
            return bool(_NOSQL_INJECTION_PATTERNS.search(obj))
        if isinstance(obj, dict):
            for k, v in obj.items():
                if _NOSQL_INJECTION_PATTERNS.search(k) or _scan(v):
                    return True
        if isinstance(obj, list):
            return any(_scan(item) for item in obj)
        return False
    return _scan(data)


def check_xss(value: str) -> bool:
    """Check if a string contains XSS patterns."""
    if not isinstance(value, str):
        return False
    return bool(_XSS_PATTERNS.search(value))


def check_path_traversal(value: str) -> bool:
    """Check if a string contains path traversal patterns."""
    if not isinstance(value, str):
        return False
    return bool(_PATH_TRAVERSAL.search(value))


def validate_input(data: dict) -> list:
    """
    Validate a dictionary for injection attacks.
    Returns list of issues found (empty = clean).
    """
    issues = []
    if check_nosql_injection(data):
        issues.append("Potential NoSQL injection detected")
    for key, value in data.items():
        if isinstance(value, str):
            if check_xss(value):
                issues.append(f"Potential XSS detected in field: {key}")
            if check_path_traversal(value):
                issues.append(f"Potential path traversal in field: {key}")
    return issues
