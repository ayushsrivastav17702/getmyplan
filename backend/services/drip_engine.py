"""
Drip Campaign Engine.
Detects users stuck at each funnel stage and sends escalating nudge emails.
Drip sequence: Day 1, Day 3, Day 7 per stage.
"""
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

ACTIVE_THRESHOLD_DAYS = 30

# Default campaign definitions
DEFAULT_CAMPAIGNS = [
    {
        "campaign_id": "not_verified",
        "name": "Email Not Verified",
        "description": "Nudge users who signed up but haven't verified their email",
        "stage_from": "signed_up",
        "stage_to": "email_verified",
        "enabled": True,
        "drip_days": [1, 3, 7],
    },
    {
        "campaign_id": "not_onboarded",
        "name": "Onboarding Incomplete",
        "description": "Nudge users who verified email but haven't completed onboarding",
        "stage_from": "email_verified",
        "stage_to": "onboarding_complete",
        "enabled": True,
        "drip_days": [1, 3, 7],
    },
    {
        "campaign_id": "no_upload",
        "name": "No Data Uploaded",
        "description": "Nudge users who completed onboarding but haven't uploaded data",
        "stage_from": "onboarding_complete",
        "stage_to": "first_upload",
        "enabled": True,
        "drip_days": [1, 3, 7],
    },
    {
        "campaign_id": "inactive",
        "name": "Inactive User",
        "description": "Re-engage users who uploaded data but haven't logged in recently",
        "stage_from": "first_upload",
        "stage_to": "active_user",
        "enabled": True,
        "drip_days": [1, 3, 7],
    },
]


# ── Email Templates ──

def _get_email_html(campaign_id: str, drip_day: int, user_name: str, app_url: str) -> dict:
    """Return subject and HTML body for each campaign + drip step."""
    templates = {
        "not_verified": {
            1: {
                "subject": "Verify your email to get started",
                "body": f"""
                <h2 style="margin:0 0 12px;color:#1e293b;">Almost there, {user_name}!</h2>
                <p style="color:#475569;line-height:1.6;">You signed up for GetMyPlan but haven't verified your email yet. Verify now to start your free trial.</p>
                <div style="text-align:center;margin:24px 0;">
                  <a href="{app_url}/login" style="display:inline-block;padding:12px 32px;background:#0176D3;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;">Verify & Get Started</a>
                </div>
                """,
            },
            3: {
                "subject": "Don't miss out — verify your email",
                "body": f"""
                <h2 style="margin:0 0 12px;color:#1e293b;">Hey {user_name}, still waiting for you!</h2>
                <p style="color:#475569;line-height:1.6;">Your GetMyPlan account is ready — just verify your email to unlock AI-powered demand forecasting, analytics dashboards, and more.</p>
                <div style="text-align:center;margin:24px 0;">
                  <a href="{app_url}/login" style="display:inline-block;padding:12px 32px;background:#0176D3;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;">Verify Now</a>
                </div>
                <p style="color:#64748b;font-size:13px;">Your verification link expires soon. Don't let your free trial go to waste.</p>
                """,
            },
            7: {
                "subject": "Last chance to activate your account",
                "body": f"""
                <h2 style="margin:0 0 12px;color:#1e293b;">Final reminder, {user_name}</h2>
                <p style="color:#475569;line-height:1.6;">It's been a week since you signed up. Your GetMyPlan account is still waiting to be verified. After this, we won't send more reminders.</p>
                <div style="text-align:center;margin:24px 0;">
                  <a href="{app_url}/login" style="display:inline-block;padding:12px 32px;background:#ef4444;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;">Activate My Account</a>
                </div>
                """,
            },
        },
        "not_onboarded": {
            1: {
                "subject": "Complete your setup in 5 minutes",
                "body": f"""
                <h2 style="margin:0 0 12px;color:#1e293b;">Welcome aboard, {user_name}!</h2>
                <p style="color:#475569;line-height:1.6;">Your email is verified. Now complete the quick onboarding wizard to configure your workspace — it takes less than 5 minutes.</p>
                <div style="text-align:center;margin:24px 0;">
                  <a href="{app_url}/onboarding" style="display:inline-block;padding:12px 32px;background:#10b981;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;">Start Setup Wizard</a>
                </div>
                """,
            },
            3: {
                "subject": "Your workspace is 80% ready",
                "body": f"""
                <h2 style="margin:0 0 12px;color:#1e293b;">{user_name}, you're almost there!</h2>
                <p style="color:#475569;line-height:1.6;">Just a few more steps to complete your workspace setup. Once done, you'll unlock AI demand forecasting, buy plan generation, and 15+ analytics dashboards.</p>
                <div style="text-align:center;margin:24px 0;">
                  <a href="{app_url}/onboarding" style="display:inline-block;padding:12px 32px;background:#10b981;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;">Continue Setup</a>
                </div>
                """,
            },
            7: {
                "subject": "Need help setting up? We're here",
                "body": f"""
                <h2 style="margin:0 0 12px;color:#1e293b;">Hi {user_name},</h2>
                <p style="color:#475569;line-height:1.6;">We noticed you haven't completed your workspace setup yet. If you're stuck or need help, just reply to this email — our team is happy to assist.</p>
                <div style="text-align:center;margin:24px 0;">
                  <a href="{app_url}/onboarding" style="display:inline-block;padding:12px 32px;background:#0176D3;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;">Resume Setup</a>
                </div>
                """,
            },
        },
        "no_upload": {
            1: {
                "subject": "Upload your first data file",
                "body": f"""
                <h2 style="margin:0 0 12px;color:#1e293b;">Great progress, {user_name}!</h2>
                <p style="color:#475569;line-height:1.6;">Your workspace is set up. Now upload your first data file (Style Master, Store Master, or Daily Sales) to start generating insights.</p>
                <div style="text-align:center;margin:24px 0;">
                  <a href="{app_url}/upload" style="display:inline-block;padding:12px 32px;background:#f59e0b;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;">Upload Data</a>
                </div>
                """,
            },
            3: {
                "subject": "Your analytics dashboards are waiting",
                "body": f"""
                <h2 style="margin:0 0 12px;color:#1e293b;">{user_name}, unlock your insights</h2>
                <p style="color:#475569;line-height:1.6;">Upload a CSV or Excel file with your sales, inventory, or product data. GetMyPlan will automatically generate AI-powered forecasts and analytics.</p>
                <div style="text-align:center;margin:24px 0;">
                  <a href="{app_url}/upload" style="display:inline-block;padding:12px 32px;background:#f59e0b;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;">Upload Now</a>
                </div>
                """,
            },
            7: {
                "subject": "Try with sample data — see GetMyPlan in action",
                "body": f"""
                <h2 style="margin:0 0 12px;color:#1e293b;">Hi {user_name},</h2>
                <p style="color:#475569;line-height:1.6;">Not ready with your own data? No problem — try our sample data templates to see how GetMyPlan's AI forecasting and analytics work.</p>
                <div style="text-align:center;margin:24px 0;">
                  <a href="{app_url}/upload" style="display:inline-block;padding:12px 32px;background:#0176D3;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;">Explore with Sample Data</a>
                </div>
                """,
            },
        },
        "inactive": {
            1: {
                "subject": "Your analytics are waiting for you",
                "body": f"""
                <h2 style="margin:0 0 12px;color:#1e293b;">Welcome back, {user_name}!</h2>
                <p style="color:#475569;line-height:1.6;">It's been a while since you logged in. Your dashboards have been updated with the latest data — come check them out.</p>
                <div style="text-align:center;margin:24px 0;">
                  <a href="{app_url}/dashboard" style="display:inline-block;padding:12px 32px;background:#0176D3;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;">View Dashboard</a>
                </div>
                """,
            },
            3: {
                "subject": "New features since your last visit",
                "body": f"""
                <h2 style="margin:0 0 12px;color:#1e293b;">{user_name}, we've been busy!</h2>
                <p style="color:#475569;line-height:1.6;">We've added new AI forecasting models, improved dashboards, and more. Log in to explore what's new.</p>
                <div style="text-align:center;margin:24px 0;">
                  <a href="{app_url}/dashboard" style="display:inline-block;padding:12px 32px;background:#6366f1;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;">See What's New</a>
                </div>
                """,
            },
            7: {
                "subject": "We miss you — here's what you're missing",
                "body": f"""
                <h2 style="margin:0 0 12px;color:#1e293b;">Hi {user_name},</h2>
                <p style="color:#475569;line-height:1.6;">Your GetMyPlan workspace is ready and waiting. If there's anything we can improve, just reply to this email — we read every response.</p>
                <div style="text-align:center;margin:24px 0;">
                  <a href="{app_url}/dashboard" style="display:inline-block;padding:12px 32px;background:#0176D3;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;">Log In Now</a>
                </div>
                """,
            },
        },
    }

    t = templates.get(campaign_id, {}).get(drip_day)
    if not t:
        return None
    return {
        "subject": t["subject"],
        "html": _wrap_email(t["body"]),
    }


def _wrap_email(body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;margin:0;padding:0;background:#f3f4f6;">
<div style="max-width:600px;margin:20px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
  <div style="padding:28px 24px;background:#0176D3;text-align:center;">
    <h1 style="margin:0;color:#fff;font-size:22px;">GetMyPlan</h1>
  </div>
  <div style="padding:32px 28px;">
    {body_html}
  </div>
  <div style="padding:16px;text-align:center;background:#f8fafc;font-size:12px;color:#94a3b8;">
    GetMyPlan &mdash; AI-powered retail analytics<br>
    <a href="{{app_url}}" style="color:#94a3b8;">Unsubscribe</a>
  </div>
</div>
</body></html>"""


def _parse_iso(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.replace(tzinfo=timezone.utc) if val.tzinfo is None else val
    try:
        dt = datetime.fromisoformat(str(val))
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    except Exception:
        return None


async def get_campaigns(shared_db) -> list:
    """Get campaign configs from DB, seeding defaults if needed."""
    existing = []
    async for doc in shared_db.drip_campaigns.find({}, {"_id": 0}):
        existing.append(doc)

    if not existing:
        for c in DEFAULT_CAMPAIGNS:
            c["created_at"] = datetime.now(timezone.utc).isoformat()
            c["updated_at"] = datetime.now(timezone.utc).isoformat()
        await shared_db.drip_campaigns.insert_many([dict(c) for c in DEFAULT_CAMPAIGNS])
        return DEFAULT_CAMPAIGNS

    return existing


async def run_drip_check(shared_db, email_service) -> dict:
    """
    Core engine: check all users against funnel stages,
    determine which drip emails to send, and send them.
    Returns summary of actions taken.
    """
    import os
    app_url = os.environ.get("APP_URL", "")
    now = datetime.now(timezone.utc)
    active_cutoff = now - timedelta(days=ACTIVE_THRESHOLD_DAYS)

    campaigns = await get_campaigns(shared_db)
    enabled_campaigns = {c["campaign_id"]: c for c in campaigns if c.get("enabled")}

    if not enabled_campaigns:
        return {"sent": 0, "skipped": 0, "errors": 0, "details": [], "message": "All campaigns are disabled"}

    # Gather user data
    all_users = []
    async for u in shared_db.users.find({}, {"_id": 0, "hashed_password": 0, "totp_secret": 0}):
        all_users.append(u)

    # Tenant memberships
    user_tenant_map = {}
    async for ut in shared_db.user_tenants.find({}, {"_id": 0}):
        email = ut.get("email")
        if email:
            user_tenant_map[email] = ut

    # Onboarding status
    onboarding_map = {}
    async for ob in shared_db.onboarding_status.find({}, {"_id": 0}):
        onboarding_map[ob.get("tenant_id")] = ob

    # Upload check — tenants with data
    upload_tenants = set()
    async for t in shared_db.tenants.find({"status": "active"}, {"_id": 0, "tenant_id": 1}):
        has_data = await shared_db.daily_sales.find_one({"tenant_id": t["tenant_id"]})
        if has_data:
            upload_tenants.add(t["tenant_id"])

    # Tenant map
    tenant_map = {}
    async for t in shared_db.tenants.find({}, {"_id": 0, "tenant_id": 1, "status": 1}):
        tenant_map[t["tenant_id"]] = t

    # Existing drip logs
    recent_logs = {}
    async for log in shared_db.drip_logs.find(
        {"sent_at": {"$gte": (now - timedelta(days=30)).isoformat()}},
        {"_id": 0},
    ):
        key = f"{log['email']}:{log['campaign_id']}:{log['drip_day']}"
        recent_logs[key] = log

    sent = 0
    skipped = 0
    errors = 0
    details = []

    for u in all_users:
        email = u.get("email", "")
        created = _parse_iso(u.get("created_at"))
        if not created:
            continue

        last_login = _parse_iso(u.get("last_login"))
        email_verified = u.get("email_verified", False)
        mapping = user_tenant_map.get(email, {})
        user_tid = mapping.get("tenant_id")
        user_name = u.get("full_name", u.get("username", email.split("@")[0]))

        # Legacy users without email_verified field
        if not email_verified and user_tid and tenant_map.get(user_tid, {}).get("status") == "active":
            email_verified = True

        ob = onboarding_map.get(user_tid, {})
        is_onboarded = ob.get("is_onboarded", False)
        has_uploaded = user_tid and user_tid in upload_tenants
        is_active = last_login is not None and last_login >= active_cutoff

        # Determine current stage
        current_stage = "signed_up"
        if email_verified:
            current_stage = "email_verified"
        if email_verified and is_onboarded:
            current_stage = "onboarding_complete"
        if email_verified and is_onboarded and has_uploaded:
            current_stage = "first_upload"
        if email_verified and is_onboarded and has_uploaded and is_active:
            current_stage = "active_user"

        # Determine the reference timestamp for "stuck at stage"
        # For each campaign, check if user is stuck at the expected stage
        stage_to_campaign = {
            "signed_up": "not_verified",
            "email_verified": "not_onboarded",
            "onboarding_complete": "no_upload",
            "first_upload": "inactive",
        }

        campaign_id = stage_to_campaign.get(current_stage)
        if not campaign_id or campaign_id not in enabled_campaigns:
            continue

        campaign = enabled_campaigns[campaign_id]
        days_stuck = (now - created).days

        # For inactive users, use last_login as reference
        if campaign_id == "inactive" and last_login:
            days_stuck = (now - last_login).days

        # Determine which drip day to send
        drip_days = campaign.get("drip_days", [1, 3, 7])
        target_drip_day = None
        for dd in sorted(drip_days, reverse=True):
            if days_stuck >= dd:
                target_drip_day = dd
                break

        if not target_drip_day:
            continue

        # Check if already sent this drip
        log_key = f"{email}:{campaign_id}:{target_drip_day}"
        if log_key in recent_logs:
            skipped += 1
            continue

        # Send the email
        template = _get_email_html(campaign_id, target_drip_day, user_name, app_url)
        if not template:
            skipped += 1
            continue

        success = email_service.send_email(email, template["subject"], template["html"])

        if success:
            sent += 1
            await shared_db.drip_logs.insert_one({
                "email": email,
                "campaign_id": campaign_id,
                "campaign_name": campaign["name"],
                "drip_day": target_drip_day,
                "subject": template["subject"],
                "sent_at": now.isoformat(),
                "current_stage": current_stage,
            })
            details.append({
                "email": email,
                "campaign": campaign["name"],
                "drip_day": target_drip_day,
                "status": "sent",
            })
        else:
            errors += 1
            details.append({
                "email": email,
                "campaign": campaign["name"],
                "drip_day": target_drip_day,
                "status": "failed",
            })

    return {
        "sent": sent,
        "skipped": skipped,
        "errors": errors,
        "details": details,
        "run_at": now.isoformat(),
        "message": f"Drip check complete: {sent} sent, {skipped} skipped, {errors} errors",
    }
