"""
User Funnel Analytics API.
Tracks: Signup → Email Verified → Onboarding Complete → First Upload → Active User.
Super admins see platform-wide; tenant admins see their tenant.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from multi_tenant.auth import get_current_user
from multi_tenant.tenant_db import get_shared_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics/funnel", tags=["Funnel Analytics"])

ACTIVE_THRESHOLD_DAYS = 30  # user is "active" if last_login within this window


def _parse_iso(val) -> Optional[datetime]:
    """Safely parse an ISO datetime string or return a datetime as-is."""
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val
    try:
        dt = datetime.fromisoformat(str(val))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


@router.get("")
async def get_funnel_data(
    days: Optional[int] = Query(None, ge=1, le=365),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    """
    Get user funnel analytics.
    Restricted to super admins only.
    """
    role = user.get("role", "viewer")
    tenant_id = user.get("tenant_id")
    if role != "super_admin" and tenant_id != "demo":
        raise HTTPException(status_code=403, detail="Only super admins can access funnel analytics")
    is_platform_wide = role in ("super_admin",) or tenant_id == "demo"

    shared = get_shared_db()
    now = datetime.now(timezone.utc)

    # Time range
    range_start = None
    range_end = now
    if start_date:
        range_start = _parse_iso(start_date)
    if end_date:
        range_end = _parse_iso(end_date) or now
    if days and not start_date:
        range_start = now - timedelta(days=days)

    # ── Gather all users ──
    user_query = {}
    if range_start:
        user_query["created_at"] = {"$gte": range_start.isoformat()}

    all_users = []
    async for u in shared.users.find({}, {"_id": 0, "hashed_password": 0, "totp_secret": 0, "reset_token": 0}):
        created = _parse_iso(u.get("created_at"))
        if range_start and created and created < range_start:
            continue
        if range_end and created and created > range_end:
            continue
        all_users.append(u)

    # ── Gather user-tenant mappings ──
    ut_query = {}
    if not is_platform_wide:
        ut_query["tenant_id"] = tenant_id
    user_tenant_map = {}  # email -> list of tenant mappings
    async for ut in shared.user_tenants.find(ut_query, {"_id": 0}):
        email = ut.get("email")
        if email not in user_tenant_map:
            user_tenant_map[email] = []
        user_tenant_map[email].append(ut)

    # Filter users to those in scope
    if not is_platform_wide:
        all_users = [u for u in all_users if u.get("email") in user_tenant_map]

    # ── Gather onboarding status ──
    ob_query = {}
    if not is_platform_wide:
        ob_query["tenant_id"] = tenant_id
    onboarding_map = {}  # tenant_id -> doc
    async for ob in shared.onboarding_status.find(ob_query, {"_id": 0}):
        onboarding_map[ob.get("tenant_id")] = ob

    # ── Gather upload history ──
    upload_emails = set()
    # Check upload_history for uploaded_by field
    async for uh in shared.upload_history.find({"status": "success"}, {"_id": 0, "uploaded_by": 1, "uploaded_at": 1}):
        if uh.get("uploaded_by"):
            upload_emails.add(uh["uploaded_by"])

    # Also check uploaded_files collection
    async for uf in shared.uploaded_files.find({}, {"_id": 0, "uploaded_by": 1}):
        if uf.get("uploaded_by"):
            upload_emails.add(uf["uploaded_by"])

    # Check tenant-specific data collections for uploaded_by
    for col_name in ["daily_sales", "style_master", "store_inventory", "cogs"]:
        async for doc in shared[col_name].find(
            {"uploaded_by": {"$exists": True, "$nin": [None, "system"]}},
            {"_id": 0, "uploaded_by": 1},
        ).limit(100):
            if doc.get("uploaded_by") and doc["uploaded_by"] != "system":
                upload_emails.add(doc["uploaded_by"])

    # Fallback: if a tenant has upload_history records, consider all tenant members as having uploaded
    upload_tenants = set()
    if shared.upload_history.find_one({"status": "success"}):
        # Check which tenants have upload_history (no tenant_id on upload_history, so use onboarded tenants with data)
        async for t in shared.tenants.find({"status": "active"}, {"_id": 0, "tenant_id": 1}):
            tid = t["tenant_id"]
            has_data = await shared.daily_sales.find_one({"tenant_id": tid})
            if has_data:
                upload_tenants.add(tid)

    # ── Tenant info ──
    tenant_map = {}
    async for t in shared.tenants.find({}, {"_id": 0, "tenant_id": 1, "company_name": 1, "status": 1, "plan_type": 1}):
        tenant_map[t["tenant_id"]] = t

    # ── Compute funnel stages per user ──
    active_cutoff = now - timedelta(days=ACTIVE_THRESHOLD_DAYS)

    stage_counts = {
        "signed_up": 0,
        "email_verified": 0,
        "onboarding_complete": 0,
        "first_upload": 0,
        "active_user": 0,
    }

    user_details = []

    for u in all_users:
        email = u.get("email", "")
        created = _parse_iso(u.get("created_at"))
        last_login = _parse_iso(u.get("last_login"))
        email_verified = u.get("email_verified", False)
        mappings = user_tenant_map.get(email, [])
        user_tid = mappings[0].get("tenant_id") if mappings else None
        user_role = mappings[0].get("role", "viewer") if mappings else "viewer"

        # Determine tenant's onboarding status
        ob = onboarding_map.get(user_tid, {})
        is_onboarded = ob.get("is_onboarded", False)

        # Check if user has uploaded
        has_uploaded = email in upload_emails or (user_tid and user_tid in upload_tenants)

        # Check if active
        is_active = last_login is not None and last_login >= active_cutoff

        # Determine current stage (highest reached)
        current_stage = "signed_up"
        if email_verified or (u.get("email_verified") is not False and user_tid and tenant_map.get(user_tid, {}).get("status") == "active"):
            # If email_verified field exists and is True, or tenant is active (older users without the field)
            if email_verified:
                current_stage = "email_verified"
            elif user_tid and tenant_map.get(user_tid, {}).get("status") == "active":
                # Legacy users without email_verified field but active tenant
                current_stage = "email_verified"
                email_verified = True

        if current_stage == "email_verified" and is_onboarded:
            current_stage = "onboarding_complete"
        if current_stage == "onboarding_complete" and has_uploaded:
            current_stage = "first_upload"
        if current_stage == "first_upload" and is_active:
            current_stage = "active_user"

        # Count cumulative (each stage includes all users who reached that stage)
        stage_counts["signed_up"] += 1
        if email_verified:
            stage_counts["email_verified"] += 1
        if email_verified and is_onboarded:
            stage_counts["onboarding_complete"] += 1
        if email_verified and is_onboarded and has_uploaded:
            stage_counts["first_upload"] += 1
        if email_verified and is_onboarded and has_uploaded and is_active:
            stage_counts["active_user"] += 1

        company = tenant_map.get(user_tid, {}).get("company_name", user_tid or "—")
        user_details.append({
            "email": email,
            "full_name": u.get("full_name", u.get("username", "")),
            "tenant_id": user_tid,
            "company": company,
            "role": user_role,
            "current_stage": current_stage,
            "signed_up_at": u.get("created_at"),
            "email_verified": email_verified,
            "onboarding_complete": is_onboarded,
            "has_uploaded": has_uploaded,
            "is_active": is_active,
            "last_login": str(last_login) if last_login else None,
        })

    # ── Conversion rates ──
    stages_ordered = ["signed_up", "email_verified", "onboarding_complete", "first_upload", "active_user"]
    conversions = []
    for i in range(len(stages_ordered) - 1):
        from_stage = stages_ordered[i]
        to_stage = stages_ordered[i + 1]
        from_count = stage_counts[from_stage]
        to_count = stage_counts[to_stage]
        rate = round((to_count / from_count * 100), 1) if from_count > 0 else 0
        drop_off = from_count - to_count
        conversions.append({
            "from": from_stage,
            "to": to_stage,
            "from_count": from_count,
            "to_count": to_count,
            "conversion_rate": rate,
            "drop_off": drop_off,
        })

    overall_rate = round((stage_counts["active_user"] / stage_counts["signed_up"] * 100), 1) if stage_counts["signed_up"] > 0 else 0

    # ── Time series: signups per day ──
    signup_by_day = {}
    for u in all_users:
        created = _parse_iso(u.get("created_at"))
        if created:
            day_key = created.strftime("%Y-%m-%d")
            signup_by_day[day_key] = signup_by_day.get(day_key, 0) + 1

    # Fill in missing days
    if range_start:
        current_day = range_start.date()
        end_day = range_end.date()
        while current_day <= end_day:
            key = current_day.strftime("%Y-%m-%d")
            if key not in signup_by_day:
                signup_by_day[key] = 0
            current_day += timedelta(days=1)

    time_series = sorted([{"date": k, "signups": v} for k, v in signup_by_day.items()], key=lambda x: x["date"])

    # Sort user_details by created_at desc
    user_details.sort(key=lambda x: x.get("signed_up_at") or "", reverse=True)

    return {
        "funnel": {
            "stages": stage_counts,
            "conversions": conversions,
            "overall_conversion": overall_rate,
        },
        "time_series": time_series,
        "users": user_details,
        "total_users": len(all_users),
        "is_platform_wide": is_platform_wide,
        "date_range": {
            "start": range_start.isoformat() if range_start else None,
            "end": range_end.isoformat(),
        },
    }
