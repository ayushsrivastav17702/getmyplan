"""
SMTP email service for sending verification and welcome emails.
Uses Hostinger SMTP. Falls back to mock/log mode when credentials are missing.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logger = logging.getLogger(__name__)


class SMTPEmailService:
    """Lazy-reads env vars so it works after load_dotenv is called."""

    @property
    def _cfg(self):
        return {
            "host": os.environ.get("SMTP_HOST", "smtp.hostinger.com"),
            "port": int(os.environ.get("SMTP_PORT", "465")),
            "user": os.environ.get("SMTP_USER", ""),
            "password": os.environ.get("SMTP_PASSWORD", ""),
            "from_email": os.environ.get("FROM_EMAIL", ""),
            "from_name": os.environ.get("FROM_NAME", "GetMyPlan"),
            "use_ssl": os.environ.get("SMTP_USE_SSL", "true").lower() == "true",
            "app_url": os.environ.get("APP_URL", ""),
            "trial_days": int(os.environ.get("TRIAL_DAYS", "7")),
        }

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        cfg = self._cfg
        if not cfg["user"] or not cfg["password"]:
            logger.info("[MOCK] Email to %s: %s", to_email, subject)
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{cfg['from_name']} <{cfg['from_email']}>"
            msg["To"] = to_email
            msg.attach(MIMEText(html_content, "html"))

            if cfg["use_ssl"]:
                server = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=30)
            else:
                server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=30)
                server.starttls()

            server.login(cfg["user"], cfg["password"])
            server.send_message(msg)
            server.quit()
            logger.info("Email sent to %s: %s", to_email, subject)
            return True
        except Exception as e:
            logger.error("Failed to send email to %s: %s", to_email, e)
            return False

    def send_verification_email(self, to_email: str, company_name: str, token: str, app_url: str = None) -> bool:
        cfg = self._cfg
        base_url = app_url or cfg['app_url']
        verify_url = f"{base_url}/verify-email?token={token}"
        trial_days = cfg["trial_days"]

        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;margin:0;padding:0;background:#f3f4f6;">
<div style="max-width:600px;margin:20px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
  <div style="padding:28px 24px;background:#0176D3;text-align:center;">
    <h1 style="margin:0;color:#fff;font-size:22px;">GetMyPlan</h1>
  </div>
  <div style="padding:32px 28px;">
    <h2 style="margin:0 0 12px;color:#1e293b;">Welcome to {company_name}!</h2>
    <p style="color:#475569;line-height:1.6;">Please verify your email address to activate your <strong>{trial_days}-day free trial</strong>.</p>
    <div style="text-align:center;margin:28px 0;">
      <a href="{verify_url}" style="display:inline-block;padding:12px 32px;background:#0176D3;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;">Verify Email Address</a>
    </div>
    <p style="color:#64748b;font-size:13px;">Or copy this link:<br><code style="word-break:break-all;color:#0176D3;">{verify_url}</code></p>
    <div style="margin:24px 0;padding:16px;background:#fef3c7;border-radius:6px;">
      <p style="margin:0;color:#92400e;font-size:13px;"><strong>Important:</strong></p>
      <ul style="margin:8px 0 0;padding-left:20px;color:#92400e;font-size:13px;">
        <li>This link expires in 24 hours</li>
        <li>Your {trial_days}-day trial starts after verification</li>
      </ul>
    </div>
  </div>
  <div style="padding:16px;text-align:center;background:#f8fafc;font-size:12px;color:#94a3b8;">
    GetMyPlan &mdash; AI-powered retail analytics
  </div>
</div>
</body></html>"""

        return self.send_email(to_email, f"Verify your email - {company_name}", html)

    def send_welcome_email(self, to_email: str, company_name: str, app_url: str = None) -> bool:
        cfg = self._cfg
        dashboard_url = app_url or cfg["app_url"]
        trial_days = cfg["trial_days"]

        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;margin:0;padding:0;background:#f3f4f6;">
<div style="max-width:600px;margin:20px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
  <div style="padding:28px 24px;background:#10b981;text-align:center;">
    <h1 style="margin:0;color:#fff;font-size:22px;">Welcome to GetMyPlan!</h1>
  </div>
  <div style="padding:32px 28px;">
    <h2 style="margin:0 0 12px;color:#1e293b;">Your account is ready!</h2>
    <p style="color:#475569;line-height:1.6;">Your email has been verified and your <strong>{trial_days}-day free trial</strong> has started.</p>
    <div style="text-align:center;margin:28px 0;">
      <a href="{dashboard_url}" style="display:inline-block;padding:12px 32px;background:#10b981;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;">Go to Dashboard</a>
    </div>
    <h3 style="color:#1e293b;margin:24px 0 8px;">Next steps:</h3>
    <ul style="color:#475569;line-height:1.8;">
      <li>Complete the onboarding wizard</li>
      <li>Upload your data (Style Master, Store Master)</li>
      <li>Generate AI insights and forecasts</li>
      <li>Explore analytics dashboards</li>
    </ul>
    <p style="color:#475569;"><strong>Trial ends in {trial_days} days.</strong> Upgrade anytime to continue.</p>
  </div>
  <div style="padding:16px;text-align:center;background:#f8fafc;font-size:12px;color:#94a3b8;">
    GetMyPlan &mdash; AI-powered retail analytics
  </div>
</div>
</body></html>"""

        return self.send_email(to_email, f"Welcome to {company_name}!", html)

    def send_admin_signup_notification(self, tenant_email: str, company_name: str,
                                        subdomain: str, plan_type: str, tenant_id: str) -> bool:
        """Notify admin (info@getmyplan.in) about a new tenant registration."""
        from datetime import datetime, timezone
        admin_email = "info@getmyplan.in"
        registered_at = datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p UTC")

        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;margin:0;padding:0;background:#f3f4f6;">
<div style="max-width:600px;margin:20px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
  <div style="padding:28px 24px;background:#6366f1;text-align:center;">
    <h1 style="margin:0;color:#fff;font-size:22px;">New Signup Alert</h1>
  </div>
  <div style="padding:32px 28px;">
    <h2 style="margin:0 0 16px;color:#1e293b;">A new tenant just registered!</h2>
    <table style="width:100%;border-collapse:collapse;">
      <tr><td style="padding:8px 0;color:#64748b;width:140px;">Company</td><td style="padding:8px 0;color:#1e293b;font-weight:600;">{company_name}</td></tr>
      <tr><td style="padding:8px 0;color:#64748b;">Email</td><td style="padding:8px 0;color:#1e293b;">{tenant_email}</td></tr>
      <tr><td style="padding:8px 0;color:#64748b;">Subdomain</td><td style="padding:8px 0;color:#1e293b;">{subdomain}</td></tr>
      <tr><td style="padding:8px 0;color:#64748b;">Tenant ID</td><td style="padding:8px 0;color:#1e293b;">{tenant_id}</td></tr>
      <tr><td style="padding:8px 0;color:#64748b;">Plan</td><td style="padding:8px 0;color:#1e293b;">{plan_type}</td></tr>
      <tr><td style="padding:8px 0;color:#64748b;">Registered At</td><td style="padding:8px 0;color:#1e293b;">{registered_at}</td></tr>
    </table>
  </div>
  <div style="padding:16px;text-align:center;background:#f8fafc;font-size:12px;color:#94a3b8;">
    GetMyPlan Admin Notification
  </div>
</div>
</body></html>"""

        return self.send_email(admin_email, f"New Signup: {company_name} ({tenant_email})", html)

    def send_password_reset_email(self, to_email: str, token: str, app_url: str = None) -> bool:
        cfg = self._cfg
        base_url = app_url or cfg['app_url']
        reset_url = f"{base_url}/reset-password?token={token}"

        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;margin:0;padding:0;background:#f3f4f6;">
<div style="max-width:600px;margin:20px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
  <div style="padding:28px 24px;background:#0176D3;text-align:center;">
    <h1 style="margin:0;color:#fff;font-size:22px;">GetMyPlan</h1>
  </div>
  <div style="padding:32px 28px;">
    <h2 style="margin:0 0 12px;color:#1e293b;">Reset Your Password</h2>
    <p style="color:#475569;line-height:1.6;">Click the button below to reset your password. This link expires in 1 hour.</p>
    <div style="text-align:center;margin:28px 0;">
      <a href="{reset_url}" style="display:inline-block;padding:12px 32px;background:#0176D3;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;">Reset Password</a>
    </div>
    <p style="color:#64748b;font-size:13px;">If you didn't request this, you can safely ignore this email.</p>
  </div>
  <div style="padding:16px;text-align:center;background:#f8fafc;font-size:12px;color:#94a3b8;">
    GetMyPlan &mdash; AI-powered retail analytics
  </div>
</div>
</body></html>"""

        return self.send_email(to_email, "Reset your password - GetMyPlan", html)


email_service = SMTPEmailService()
