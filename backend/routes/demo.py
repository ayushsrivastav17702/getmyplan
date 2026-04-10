"""
Demo request endpoint — stores lead in MongoDB and sends notification email.
Public (no auth required).
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os, logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "getmyplan")


class DemoRequest(BaseModel):
    name: str
    email: EmailStr
    company: str
    heard_from: str
    goals: str


@router.post("/request")
async def submit_demo_request(body: DemoRequest):
    """Save lead to shared DB and email the admin."""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    doc = {
        "name": body.name,
        "email": body.email,
        "company": body.company,
        "heard_from": body.heard_from,
        "goals": body.goals,
        "status": "new",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.demo_requests.insert_one(doc)

    # Send notification email (fire-and-forget, don't block the response)
    try:
        from services.smtp_email_service import email_service
        html = f"""
        <div style="font-family:system-ui,sans-serif;max-width:560px;margin:0 auto;padding:24px;">
            <h2 style="color:#1e293b;margin:0 0 16px;">New Demo Request</h2>
            <table style="width:100%;border-collapse:collapse;font-size:14px;">
                <tr><td style="padding:8px 12px;color:#64748b;border-bottom:1px solid #f1f5f9;width:130px;">Name</td><td style="padding:8px 12px;color:#1e293b;border-bottom:1px solid #f1f5f9;font-weight:500;">{body.name}</td></tr>
                <tr><td style="padding:8px 12px;color:#64748b;border-bottom:1px solid #f1f5f9;">Email</td><td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;"><a href="mailto:{body.email}" style="color:#2563eb;">{body.email}</a></td></tr>
                <tr><td style="padding:8px 12px;color:#64748b;border-bottom:1px solid #f1f5f9;">Company</td><td style="padding:8px 12px;color:#1e293b;border-bottom:1px solid #f1f5f9;font-weight:500;">{body.company}</td></tr>
                <tr><td style="padding:8px 12px;color:#64748b;border-bottom:1px solid #f1f5f9;">Source</td><td style="padding:8px 12px;color:#1e293b;border-bottom:1px solid #f1f5f9;">{body.heard_from}</td></tr>
                <tr><td style="padding:8px 12px;color:#64748b;vertical-align:top;">Goals</td><td style="padding:8px 12px;color:#1e293b;">{body.goals}</td></tr>
            </table>
            <p style="margin:20px 0 0;font-size:12px;color:#94a3b8;">This is an automated notification from GetMyPlan.</p>
        </div>
        """
        admin_email = "info@getmyplan.in"
        email_service.send_email(admin_email, f"Demo Request: {body.company} ({body.name})", html)
    except Exception as e:
        logger.warning("Failed to send demo notification email: %s", e)

    return {"status": "ok", "message": "Demo request submitted successfully"}


@router.get("/requests")
async def list_demo_requests():
    """Admin endpoint — list all demo requests (newest first)."""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    cursor = db.demo_requests.find({}, {"_id": 0}).sort("created_at", -1).limit(100)
    return {"requests": await cursor.to_list(length=100)}
