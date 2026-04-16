"""
Iteration 90: Anomaly Detection & Alert Management Testing
Tests for:
- Alert endpoints (GET /alerts, GET /alerts/unread-count, PUT /alerts/{id}/acknowledge, PUT /alerts/{id}/dismiss)
- Alert filtering by severity and status
- Authorization (403 for non-super-admin)
- Anomaly detection rules (excessive_impersonations, role_flip_flop)
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@demo.com"
SUPER_ADMIN_PASSWORD = "demo1234"
REGULAR_USER_EMAIL = "ayush.srivastav@increff.com"
REGULAR_USER_PASSWORD = "Ayush@114988"
TEST_TARGET_EMAIL = "merch@demo.com"


@pytest.fixture(scope="module")
def super_admin_token():
    """Get super admin token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD,
        "tenant_id": "demo"
    })
    assert response.status_code == 200, f"Super admin login failed: {response.text}"
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def regular_user_token():
    """Get regular user token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": REGULAR_USER_EMAIL,
        "password": REGULAR_USER_PASSWORD,
        "tenant_id": "increff"
    })
    assert response.status_code == 200, f"Regular user login failed: {response.text}"
    return response.json().get("access_token")


class TestAlertEndpoints:
    """Test GET /api/admin/platform/alerts and related endpoints"""

    def test_01_get_alerts_returns_200(self, super_admin_token):
        """GET /alerts returns 200 with alerts list and total count"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "total" in data
        assert isinstance(data["alerts"], list)
        assert isinstance(data["total"], int)
        print(f"✓ GET /alerts returned {data['total']} total alerts, {len(data['alerts'])} in response")
        
        # Verify alert structure if alerts exist
        if data["alerts"]:
            alert = data["alerts"][0]
            assert "alert_id" in alert, "Missing alert_id"
            assert "rule_id" in alert, "Missing rule_id"
            assert "severity" in alert, "Missing severity"
            assert "title" in alert, "Missing title"
            assert "description" in alert, "Missing description"
            assert "status" in alert, "Missing status"
            assert "created_at" in alert, "Missing created_at"
            print(f"✓ Alert structure verified: {list(alert.keys())}")

    def test_02_get_alerts_filter_by_severity_critical(self, super_admin_token):
        """GET /alerts?severity=critical filters by severity"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts?severity=critical",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # All returned alerts should have severity=critical
        for alert in data["alerts"]:
            assert alert["severity"] == "critical", f"Expected severity=critical, got {alert['severity']}"
        print(f"✓ Filter by severity=critical works: {len(data['alerts'])} critical alerts")

    def test_03_get_alerts_filter_by_severity_warning(self, super_admin_token):
        """GET /alerts?severity=warning filters by severity"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts?severity=warning",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # All returned alerts should have severity=warning
        for alert in data["alerts"]:
            assert alert["severity"] == "warning", f"Expected severity=warning, got {alert['severity']}"
        print(f"✓ Filter by severity=warning works: {len(data['alerts'])} warning alerts")

    def test_04_get_alerts_filter_by_status_active(self, super_admin_token):
        """GET /alerts?status=active filters by status"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts?status=active",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # All returned alerts should have status=active
        for alert in data["alerts"]:
            assert alert["status"] == "active", f"Expected status=active, got {alert['status']}"
        print(f"✓ Filter by status=active works: {len(data['alerts'])} active alerts")

    def test_05_get_alerts_filter_by_status_acknowledged(self, super_admin_token):
        """GET /alerts?status=acknowledged filters by status"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts?status=acknowledged",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # All returned alerts should have status=acknowledged
        for alert in data["alerts"]:
            assert alert["status"] == "acknowledged", f"Expected status=acknowledged, got {alert['status']}"
        print(f"✓ Filter by status=acknowledged works: {len(data['alerts'])} acknowledged alerts")

    def test_06_get_alerts_default_excludes_dismissed(self, super_admin_token):
        """GET /alerts (no status param) excludes dismissed alerts by default"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # No returned alerts should have status=dismissed
        for alert in data["alerts"]:
            assert alert["status"] != "dismissed", f"Dismissed alert should not be returned by default"
        print(f"✓ Default query excludes dismissed alerts: {len(data['alerts'])} non-dismissed alerts")

    def test_07_get_alerts_401_without_token(self):
        """GET /alerts returns 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/admin/platform/alerts")
        assert response.status_code == 401
        print("✓ GET /alerts returns 401 without token")

    def test_08_get_alerts_403_for_regular_user(self, regular_user_token):
        """GET /alerts returns 403 for non-super-admin"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts",
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        assert response.status_code == 403
        print("✓ GET /alerts returns 403 for regular user")


class TestAlertUnreadCount:
    """Test GET /api/admin/platform/alerts/unread-count"""

    def test_09_get_unread_count_returns_200(self, super_admin_token):
        """GET /alerts/unread-count returns count of active alerts"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts/unread-count",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert isinstance(data["count"], int)
        assert data["count"] >= 0
        print(f"✓ GET /alerts/unread-count returned count: {data['count']}")

    def test_10_get_unread_count_401_without_token(self):
        """GET /alerts/unread-count returns 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/admin/platform/alerts/unread-count")
        assert response.status_code == 401
        print("✓ GET /alerts/unread-count returns 401 without token")

    def test_11_get_unread_count_403_for_regular_user(self, regular_user_token):
        """GET /alerts/unread-count returns 403 for non-super-admin"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts/unread-count",
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        assert response.status_code == 403
        print("✓ GET /alerts/unread-count returns 403 for regular user")


class TestAlertAcknowledge:
    """Test PUT /api/admin/platform/alerts/{alert_id}/acknowledge"""

    def test_12_acknowledge_alert_changes_status(self, super_admin_token):
        """PUT /alerts/{alert_id}/acknowledge changes status to acknowledged"""
        # First get an active alert
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts?status=active",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        alerts = response.json().get("alerts", [])
        
        if not alerts:
            pytest.skip("No active alerts to acknowledge")
        
        alert_id = alerts[0]["alert_id"]
        
        # Acknowledge the alert
        ack_response = requests.put(
            f"{BASE_URL}/api/admin/platform/alerts/{alert_id}/acknowledge",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert ack_response.status_code == 200
        data = ack_response.json()
        assert data["success"] == True
        assert data["alert_id"] == alert_id
        assert data["status"] == "acknowledged"
        print(f"✓ Alert {alert_id} acknowledged successfully")
        
        # Verify the alert status changed
        verify_response = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts?status=acknowledged",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        acknowledged_ids = [a["alert_id"] for a in verify_response.json().get("alerts", [])]
        assert alert_id in acknowledged_ids, "Alert should now be in acknowledged list"
        print(f"✓ Alert status verified as acknowledged")

    def test_13_acknowledge_nonexistent_alert_returns_404(self, super_admin_token):
        """PUT /alerts/{alert_id}/acknowledge returns 404 for nonexistent alert"""
        fake_id = str(uuid.uuid4())
        response = requests.put(
            f"{BASE_URL}/api/admin/platform/alerts/{fake_id}/acknowledge",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 404
        print("✓ Acknowledge nonexistent alert returns 404")

    def test_14_acknowledge_alert_401_without_token(self):
        """PUT /alerts/{alert_id}/acknowledge returns 401 without auth"""
        response = requests.put(f"{BASE_URL}/api/admin/platform/alerts/test-id/acknowledge")
        assert response.status_code == 401
        print("✓ Acknowledge alert returns 401 without token")

    def test_15_acknowledge_alert_403_for_regular_user(self, regular_user_token):
        """PUT /alerts/{alert_id}/acknowledge returns 403 for non-super-admin"""
        response = requests.put(
            f"{BASE_URL}/api/admin/platform/alerts/test-id/acknowledge",
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        assert response.status_code == 403
        print("✓ Acknowledge alert returns 403 for regular user")


class TestAlertDismiss:
    """Test PUT /api/admin/platform/alerts/{alert_id}/dismiss"""

    def test_16_dismiss_alert_changes_status(self, super_admin_token):
        """PUT /alerts/{alert_id}/dismiss changes status to dismissed"""
        # First get any non-dismissed alert
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        alerts = response.json().get("alerts", [])
        
        if not alerts:
            pytest.skip("No alerts to dismiss")
        
        alert_id = alerts[0]["alert_id"]
        
        # Dismiss the alert
        dismiss_response = requests.put(
            f"{BASE_URL}/api/admin/platform/alerts/{alert_id}/dismiss",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert dismiss_response.status_code == 200
        data = dismiss_response.json()
        assert data["success"] == True
        assert data["alert_id"] == alert_id
        assert data["status"] == "dismissed"
        print(f"✓ Alert {alert_id} dismissed successfully")
        
        # Verify the alert is no longer in default list
        verify_response = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        default_ids = [a["alert_id"] for a in verify_response.json().get("alerts", [])]
        assert alert_id not in default_ids, "Dismissed alert should not be in default list"
        print(f"✓ Dismissed alert no longer in default list")

    def test_17_dismiss_nonexistent_alert_returns_404(self, super_admin_token):
        """PUT /alerts/{alert_id}/dismiss returns 404 for nonexistent alert"""
        fake_id = str(uuid.uuid4())
        response = requests.put(
            f"{BASE_URL}/api/admin/platform/alerts/{fake_id}/dismiss",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 404
        print("✓ Dismiss nonexistent alert returns 404")

    def test_18_dismiss_alert_401_without_token(self):
        """PUT /alerts/{alert_id}/dismiss returns 401 without auth"""
        response = requests.put(f"{BASE_URL}/api/admin/platform/alerts/test-id/dismiss")
        assert response.status_code == 401
        print("✓ Dismiss alert returns 401 without token")

    def test_19_dismiss_alert_403_for_regular_user(self, regular_user_token):
        """PUT /alerts/{alert_id}/dismiss returns 403 for non-super-admin"""
        response = requests.put(
            f"{BASE_URL}/api/admin/platform/alerts/test-id/dismiss",
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        assert response.status_code == 403
        print("✓ Dismiss alert returns 403 for regular user")


class TestAnomalyDetectionRules:
    """Test anomaly detection rules trigger alerts"""

    def test_20_role_flip_flop_rule_structure(self, super_admin_token):
        """Verify role_flip_flop alerts have correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts?status=active",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        # Also check acknowledged alerts
        response2 = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts?status=acknowledged",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        
        all_alerts = response.json().get("alerts", []) + response2.json().get("alerts", [])
        role_flip_flop_alerts = [a for a in all_alerts if a.get("rule_id") == "role_flip_flop"]
        
        if role_flip_flop_alerts:
            alert = role_flip_flop_alerts[0]
            assert alert["severity"] == "warning", "role_flip_flop should be warning severity"
            assert "role" in alert["title"].lower() or "flip" in alert["title"].lower()
            print(f"✓ role_flip_flop alert found with correct structure: {alert['title']}")
        else:
            print("⚠ No role_flip_flop alerts found (may need to trigger by changing roles 4+ times)")

    def test_21_excessive_impersonations_rule_structure(self, super_admin_token):
        """Verify excessive_impersonations alerts have correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts?status=active",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        response2 = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts?status=acknowledged",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        
        all_alerts = response.json().get("alerts", []) + response2.json().get("alerts", [])
        excessive_imp_alerts = [a for a in all_alerts if a.get("rule_id") == "excessive_impersonations"]
        
        if excessive_imp_alerts:
            alert = excessive_imp_alerts[0]
            assert alert["severity"] == "critical", "excessive_impersonations should be critical severity"
            assert "impersonation" in alert["title"].lower()
            print(f"✓ excessive_impersonations alert found with correct structure: {alert['title']}")
        else:
            print("⚠ No excessive_impersonations alerts found (may need to trigger by doing 6+ impersonations)")

    def test_22_alert_has_actor_email(self, super_admin_token):
        """Verify alerts have actor_email field"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        alerts = response.json().get("alerts", [])
        
        if alerts:
            for alert in alerts[:3]:  # Check first 3
                assert "actor_email" in alert, "Alert should have actor_email"
                print(f"✓ Alert has actor_email: {alert.get('actor_email')}")
        else:
            print("⚠ No alerts to verify actor_email field")

    def test_23_alert_has_details_field(self, super_admin_token):
        """Verify alerts have details field with context"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/alerts",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        alerts = response.json().get("alerts", [])
        
        if alerts:
            for alert in alerts[:3]:  # Check first 3
                assert "details" in alert, "Alert should have details field"
                print(f"✓ Alert has details: {alert.get('details')}")
        else:
            print("⚠ No alerts to verify details field")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
