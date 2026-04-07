"""
SFTP Notification / Alert System
- Creates notifications on upload failures, processing errors, SLA misses
- Email alerts for critical issues
- Slack webhook integration (optional)
- Daily summary notifications
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import logging
import os
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])

_get_db = None
_email_service = None


def init_notification_routes(get_db_func, email_svc=None):
    global _get_db, _email_service
    _get_db = get_db_func
    _email_service = email_svc


def get_db():
    return _get_db()


# ── Notification Types ───────────────────────────────────────────
SEVERITY_LEVELS = {"critical": 1, "warning": 2, "info": 3}

NOTIFICATION_TYPES = {
    "sftp_upload_failure": {"severity": "critical", "title": "SFTP Upload Failed"},
    "sftp_processing_error": {"severity": "critical", "title": "Processing Error"},
    "sftp_malformed_file": {"severity": "warning", "title": "Malformed File Detected"},
    "sftp_sla_miss": {"severity": "warning", "title": "SLA Deadline Missed"},
    "sftp_daily_summary": {"severity": "info", "title": "Daily SFTP Summary"},
    "sftp_duplicate_file": {"severity": "info", "title": "Duplicate File Skipped"},
}


# ── Create Notification ──────────────────────────────────────────
async def create_notification(
    notification_type: str,
    message: str,
    details: Dict[str, Any] = None,
    send_email: bool = False,
    email_to: str = None,
):
    """Create a notification and optionally send email/Slack alerts."""
    type_config = NOTIFICATION_TYPES.get(notification_type, {
        "severity": "info", "title": notification_type
    })

    notification = {
        "type": notification_type,
        "severity": type_config["severity"],
        "title": type_config["title"],
        "message": message,
        "details": details or {},
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    await get_db().notifications.insert_one(notification)
    # Remove _id before any further use
    notification.pop("_id", None)

    # Send email for critical/warning if configured
    if send_email and email_to and _email_service:
        try:
            severity_color = {"critical": "#dc2626", "warning": "#f59e0b", "info": "#3b82f6"}
            color = severity_color.get(type_config["severity"], "#3b82f6")
            html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: {color}; color: white; padding: 16px 24px; border-radius: 8px 8px 0 0;">
                    <h2 style="margin: 0; font-size: 18px;">{type_config['title']}</h2>
                </div>
                <div style="border: 1px solid #e5e7eb; border-top: none; padding: 24px; border-radius: 0 0 8px 8px;">
                    <p style="color: #374151; margin: 0 0 16px;">{message}</p>
                    {_build_details_html(details) if details else ""}
                    <p style="color: #9ca3af; font-size: 12px; margin: 16px 0 0;">
                        GetMyPlan SFTP Alert System — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
                    </p>
                </div>
            </div>
            """
            _email_service.send_email(email_to, f"[{type_config['severity'].upper()}] {type_config['title']}", html)
        except Exception as e:
            logger.error(f"Failed to send notification email: {e}")

    # Slack webhook
    slack_url = os.environ.get("SLACK_WEBHOOK_URL")
    if slack_url and type_config["severity"] in ("critical", "warning"):
        try:
            emoji = {"critical": ":red_circle:", "warning": ":warning:"}.get(type_config["severity"], ":information_source:")
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(slack_url, json={
                    "text": f"{emoji} *{type_config['title']}*\n{message}",
                })
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    return notification


def _build_details_html(details: dict) -> str:
    rows = ""
    for k, v in details.items():
        label = k.replace("_", " ").title()
        rows += f"<tr><td style='padding: 4px 8px; color: #6b7280; font-size: 13px;'>{label}</td><td style='padding: 4px 8px; font-size: 13px; font-weight: 600;'>{v}</td></tr>"
    return f"<table style='width: 100%; border-collapse: collapse; margin-top: 8px;'>{rows}</table>"


# ── SFTP Alert Triggers ──────────────────────────────────────────
async def alert_upload_failure(filename: str, error: str, transfer_id: str = "", admin_email: str = None):
    """Trigger alert for SFTP upload failure."""
    return await create_notification(
        "sftp_upload_failure",
        f"File '{filename}' failed to upload: {error}",
        {"filename": filename, "error": error, "transfer_id": transfer_id},
        send_email=True,
        email_to=admin_email,
    )


async def alert_processing_error(filename: str, error: str, admin_email: str = None):
    """Trigger alert for processing/validation error."""
    return await create_notification(
        "sftp_processing_error",
        f"Processing error for '{filename}': {error}",
        {"filename": filename, "error": error},
        send_email=True,
        email_to=admin_email,
    )


async def alert_malformed_file(filename: str, error: str):
    """Trigger alert for malformed file detection."""
    return await create_notification(
        "sftp_malformed_file",
        f"File '{filename}' is malformed and was rejected: {error}",
        {"filename": filename, "validation_error": error},
    )


async def alert_sla_miss(expected_time: str, file_type: str, admin_email: str = None):
    """Trigger alert when SLA deadline is missed."""
    return await create_notification(
        "sftp_sla_miss",
        f"SLA deadline missed for {file_type}. Expected by {expected_time}.",
        {"file_type": file_type, "expected_by": expected_time},
        send_email=True,
        email_to=admin_email,
    )


async def create_daily_summary_notification(summary: dict, admin_email: str = None):
    """Create a daily summary notification from SFTP processing data."""
    success_rate = summary.get("success_rate", 0)
    severity = "critical" if success_rate < 80 else "warning" if success_rate < 95 else "info"

    msg = (
        f"Date: {summary.get('date', 'N/A')} — "
        f"{summary.get('success', 0)}/{summary.get('total_files', 0)} files processed successfully "
        f"({success_rate}% rate). "
        f"Failed: {summary.get('failed', 0)}, Malformed: {summary.get('malformed', 0)}"
    )

    return await create_notification(
        "sftp_daily_summary",
        msg,
        {
            "date": summary.get("date"),
            "total_files": summary.get("total_files", 0),
            "success": summary.get("success", 0),
            "failed": summary.get("failed", 0),
            "malformed": summary.get("malformed", 0),
            "success_rate": f"{success_rate}%",
            "missing_stores": ", ".join(summary.get("store_coverage", {}).get("missing_stores", [])) or "None",
        },
        send_email=severity != "info",
        email_to=admin_email,
    )


# ── API Routes ───────────────────────────────────────────────────

@router.get("")
async def get_notifications(
    unread_only: bool = False,
    severity: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
):
    """Get notifications with optional filters."""
    query: Dict[str, Any] = {}
    if unread_only:
        query["read"] = False
    if severity:
        query["severity"] = severity

    total = await get_db().notifications.count_documents(query)
    notifications = await get_db().notifications.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    unread_count = await get_db().notifications.count_documents({"read": False})

    return {
        "notifications": notifications,
        "total": total,
        "unread_count": unread_count,
    }


@router.get("/unread-count")
async def get_unread_count():
    """Quick endpoint for notification badge count."""
    count = await get_db().notifications.count_documents({"read": False})
    return {"unread_count": count}


@router.put("/mark-read")
async def mark_notifications_read(notification_type: Optional[str] = None):
    """Mark notifications as read. If type provided, mark only that type."""
    query: Dict[str, Any] = {"read": False}
    if notification_type:
        query["type"] = notification_type
    result = await get_db().notifications.update_many(query, {"$set": {"read": True}})
    return {"marked_read": result.modified_count}


@router.put("/mark-all-read")
async def mark_all_read():
    """Mark all notifications as read."""
    result = await get_db().notifications.update_many({"read": False}, {"$set": {"read": True}})
    return {"marked_read": result.modified_count}


@router.delete("/clear")
async def clear_old_notifications(days: int = Query(30, ge=1)):
    """Delete notifications older than N days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    result = await get_db().notifications.delete_many({"created_at": {"$lt": cutoff}})
    return {"deleted": result.deleted_count}


@router.post("/trigger-daily-summary")
async def trigger_daily_summary(date: Optional[str] = None):
    """Manually trigger daily summary notification (also called by scheduler)."""
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Get SFTP daily summary data
    logs = await get_db().sftp_logs.find(
        {"processed_at": {"$regex": f"^{date}"}}, {"_id": 0}
    ).to_list(2000)

    total = len(logs)
    success = sum(1 for entry in logs if entry.get("status") == "success")
    failed = sum(1 for entry in logs if entry.get("status") == "error")
    malformed = sum(1 for entry in logs if entry.get("status") == "malformed")

    stores_seen = set(entry.get("store_code") for entry in logs if entry.get("store_code"))
    expected = {"ST001", "ST002", "ST003", "ST004", "ST005", "ST006", "ST007", "ST008", "ST009", "ST010"}
    missing = sorted(expected - stores_seen)

    summary = {
        "date": date,
        "total_files": total,
        "success": success,
        "failed": failed,
        "malformed": malformed,
        "success_rate": round((success / max(total, 1)) * 100, 1),
        "store_coverage": {"missing_stores": missing},
    }

    notification = await create_daily_summary_notification(summary)
    return {"summary": summary, "notification": notification}
