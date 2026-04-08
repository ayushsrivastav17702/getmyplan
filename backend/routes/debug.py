"""
Temporary debug endpoints for production MongoDB configuration diagnostics.
REMOVE THIS FILE after debugging is complete.
"""
from fastapi import APIRouter, Request
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/config")
async def debug_config():
    """Shows environment variable resolution for database configuration."""
    mongo_url = os.getenv("MONGO_URL", "")
    return {
        "environment": {
            "SHARED_DB_NAME": os.getenv("SHARED_DB_NAME", "NOT_SET"),
            "DB_NAME": os.getenv("DB_NAME", "NOT_SET"),
            "MONGO_URL_prefix": (mongo_url[:30] + "...") if mongo_url else "NOT_SET",
            "SHARED_DB_NAME_RAW": repr(os.getenv("SHARED_DB_NAME")),
            "IS_MERCH_SHARED": os.getenv("SHARED_DB_NAME") == "merch_shared",
        },
        "resolved": {
            "get_shared_db_name_result": _get_resolved_name(),
        }
    }


@router.get("/database")
async def debug_database():
    """Check actual database being used and connection status."""
    from multi_tenant.tenant_db import get_shared_db, get_mongo_client
    try:
        shared = get_shared_db()
        db_name = shared.name

        # Try listing collections to verify read access
        try:
            collections = await shared.list_collection_names()
            read_access = True
        except Exception as e:
            collections = []
            read_access = False

        # Try connectionStatus command
        conn_status = {}
        try:
            client = get_mongo_client()
            status = await client.admin.command("connectionStatus")
            conn_status = status.get("authInfo", {})
        except Exception as e:
            conn_status = {"error": str(e)}

        return {
            "current_shared_db_name": db_name,
            "read_access": read_access,
            "collections_found": collections,
            "connection_status": conn_status,
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/db-permission-test")
async def debug_db_permission_test():
    """Test read/write access to the resolved shared DB and merch_shared separately."""
    from multi_tenant.tenant_db import get_mongo_client, get_shared_db_name

    client = get_mongo_client()
    resolved_name = get_shared_db_name()
    results = {}

    # Test resolved DB
    for db_name in [resolved_name, "merch_shared"]:
        test_db = client[db_name]
        entry = {"db_name": db_name}
        try:
            count = await test_db.users.count_documents({})
            entry["read_access"] = True
            entry["users_count"] = count
        except Exception as e:
            entry["read_access"] = False
            entry["error"] = str(e)
        results[db_name] = entry

    return {
        "resolved_shared_db": resolved_name,
        "permission_tests": results,
    }


@router.get("/email-config")
async def debug_email_config():
    """Shows SMTP configuration (password masked)."""
    password = os.getenv("SMTP_PASSWORD", "")
    return {
        "smtp": {
            "SMTP_HOST": os.getenv("SMTP_HOST", "NOT_SET"),
            "SMTP_PORT": os.getenv("SMTP_PORT", "NOT_SET"),
            "SMTP_USER": os.getenv("SMTP_USER", "NOT_SET"),
            "SMTP_PASSWORD": f"{'*' * (len(password) - 3)}{password[-3:]}" if len(password) > 3 else ("SET" if password else "NOT_SET"),
            "SMTP_USE_SSL": os.getenv("SMTP_USE_SSL", "NOT_SET"),
            "FROM_EMAIL": os.getenv("FROM_EMAIL", "NOT_SET"),
            "FROM_NAME": os.getenv("FROM_NAME", "NOT_SET"),
            "APP_URL": os.getenv("APP_URL", "NOT_SET"),
        },
        "status": {
            "credentials_present": bool(os.getenv("SMTP_USER")) and bool(os.getenv("SMTP_PASSWORD")),
            "will_mock_emails": not (os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD")),
        }
    }


@router.get("/email-test")
async def debug_email_test():
    """Tests SMTP connectivity and attempts to send a test email to the configured FROM_EMAIL."""
    import smtplib
    import socket

    host = os.getenv("SMTP_HOST", "smtp.hostinger.com")
    port = int(os.getenv("SMTP_PORT", "465"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    use_ssl = os.getenv("SMTP_USE_SSL", "true").lower() == "true"
    from_email = os.getenv("FROM_EMAIL", "")

    results = {
        "config": {"host": host, "port": port, "user": user, "ssl": use_ssl},
        "steps": [],
    }

    if not user or not password:
        results["steps"].append({"step": "credentials_check", "status": "FAIL", "error": "SMTP_USER or SMTP_PASSWORD not set — emails are in MOCK mode"})
        results["overall"] = "FAIL"
        return results

    results["steps"].append({"step": "credentials_check", "status": "PASS"})

    # Step 1: DNS resolution
    try:
        ip = socket.getaddrinfo(host, port, socket.AF_INET)
        results["steps"].append({"step": "dns_resolution", "status": "PASS", "resolved_ip": ip[0][4][0]})
    except Exception as e:
        results["steps"].append({"step": "dns_resolution", "status": "FAIL", "error": str(e)})
        results["overall"] = "FAIL"
        return results

    # Step 2: TCP connection
    try:
        sock = socket.create_connection((host, port), timeout=10)
        sock.close()
        results["steps"].append({"step": "tcp_connection", "status": "PASS", "detail": f"Connected to {host}:{port}"})
    except Exception as e:
        results["steps"].append({"step": "tcp_connection", "status": "FAIL", "error": str(e), "hint": f"Firewall may be blocking outbound traffic on port {port}. Check Kubernetes egress rules."})
        results["overall"] = "FAIL"
        return results

    # Step 3: SMTP handshake + auth
    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=15)
        else:
            server = smtplib.SMTP(host, port, timeout=15)
            server.starttls()
        results["steps"].append({"step": "smtp_handshake", "status": "PASS"})
    except Exception as e:
        results["steps"].append({"step": "smtp_handshake", "status": "FAIL", "error": str(e)})
        results["overall"] = "FAIL"
        return results

    try:
        server.login(user, password)
        results["steps"].append({"step": "smtp_auth", "status": "PASS"})
    except smtplib.SMTPAuthenticationError as e:
        results["steps"].append({"step": "smtp_auth", "status": "FAIL", "error": f"Authentication failed: {e}", "hint": "Check SMTP_USER and SMTP_PASSWORD. Special chars like @ in password may need escaping."})
        server.quit()
        results["overall"] = "FAIL"
        return results
    except Exception as e:
        results["steps"].append({"step": "smtp_auth", "status": "FAIL", "error": str(e)})
        server.quit()
        results["overall"] = "FAIL"
        return results

    # Step 4: Send test email
    try:
        from email.mime.text import MIMEText
        msg = MIMEText("This is a test email from GetMyPlan debug endpoint. If you see this, SMTP is working.")
        msg["Subject"] = "[GetMyPlan] SMTP Test - Email Working"
        msg["From"] = f"GetMyPlan <{from_email}>"
        msg["To"] = from_email  # send to self
        server.send_message(msg)
        results["steps"].append({"step": "send_test_email", "status": "PASS", "detail": f"Test email sent to {from_email}"})
    except Exception as e:
        results["steps"].append({"step": "send_test_email", "status": "FAIL", "error": str(e)})
        results["overall"] = "FAIL"
        server.quit()
        return results

    server.quit()
    results["overall"] = "PASS"
    results["message"] = f"All SMTP tests passed. Test email sent to {from_email}."
    return results


def _get_resolved_name():
    try:
        from multi_tenant.tenant_db import get_shared_db_name
        return get_shared_db_name()
    except Exception as e:
        return f"ERROR: {e}"
