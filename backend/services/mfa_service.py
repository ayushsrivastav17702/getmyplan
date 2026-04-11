"""
MFA service: TOTP (Authenticator App) + Email OTP.
Uses pyotp for TOTP, segno for QR codes, and existing SMTP service for emails.
"""
import pyotp
import segno
import io
import secrets
import hashlib
import logging
from base64 import b64encode
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# ── TOTP Service ──

TOTP_ISSUER = "GetMyPlan"
TOTP_WINDOW = 1  # Accept ±1 time step (30s each side)
OTP_LENGTH = 6
OTP_EXPIRY_SECONDS = 600  # 10 minutes
MFA_TOKEN_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5


def generate_totp_secret() -> str:
    """Generate a random base32 TOTP secret."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    """Generate otpauth:// URI for authenticator app provisioning."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=TOTP_ISSUER)


def generate_qr_base64(uri: str) -> str:
    """Generate QR code as base64 data URI for embedding in frontend."""
    qr = segno.make(uri)
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=6, border=2)
    buf.seek(0)
    return f"data:image/png;base64,{b64encode(buf.getvalue()).decode()}"


def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code against the secret with a ±1 window."""
    if not secret or not code:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=TOTP_WINDOW)


# ── Email OTP Service ──

def generate_otp(length: int = OTP_LENGTH) -> str:
    """Generate a random numeric OTP code."""
    return "".join([str(secrets.randbelow(10)) for _ in range(length)])


def hash_otp(otp: str) -> str:
    """SHA-256 hash for secure OTP storage."""
    return hashlib.sha256(otp.encode()).hexdigest()


def verify_otp_hash(otp: str, otp_hash: str) -> bool:
    """Verify OTP against stored hash."""
    return hashlib.sha256(otp.encode()).hexdigest() == otp_hash


def send_mfa_otp_email(email_service, to_email: str, otp_code: str, user_name: str = "User") -> bool:
    """Send MFA OTP email using the existing SMTP service."""
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;margin:0;padding:0;background:#f3f4f6;">
<div style="max-width:600px;margin:20px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
  <div style="padding:28px 24px;background:#0176D3;text-align:center;">
    <h1 style="margin:0;color:#fff;font-size:22px;">GetMyPlan</h1>
  </div>
  <div style="padding:32px 28px;">
    <h2 style="margin:0 0 12px;color:#1e293b;">Your Login Verification Code</h2>
    <p style="color:#475569;line-height:1.6;">Hi {user_name},</p>
    <p style="color:#475569;line-height:1.6;">Use the code below to complete your sign-in:</p>
    <div style="text-align:center;margin:24px 0;">
      <div style="display:inline-block;padding:16px 40px;background:#f0f4ff;border:2px dashed #0176D3;border-radius:8px;font-size:32px;font-weight:700;letter-spacing:8px;color:#0176D3;">
        {otp_code}
      </div>
    </div>
    <p style="color:#64748b;font-size:13px;">This code expires in 10 minutes. If you didn't request this, please ignore this email.</p>
    <div style="margin:20px 0;padding:14px;background:#fef3c7;border-radius:6px;">
      <p style="margin:0;color:#92400e;font-size:13px;">Never share this code with anyone. GetMyPlan will never ask for it.</p>
    </div>
  </div>
  <div style="padding:16px;text-align:center;background:#f8fafc;font-size:12px;color:#94a3b8;">
    GetMyPlan &mdash; AI-powered retail analytics
  </div>
</div>
</body></html>"""
    return email_service.send_email(to_email, "Your GetMyPlan verification code", html)
