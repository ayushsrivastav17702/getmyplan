"""
Iteration 89: Audit Trail for Impersonation - SOC2 Compliance Testing
Tests for:
- Audit log endpoints (GET /audit-logs, GET /audit-logs/actions, GET /audit-logs/export/csv)
- Audit logging for impersonation (start/end)
- Audit logging for tenant CRUD operations
- Audit logging for user CRUD operations
- Impersonation middleware auto-logging mutating requests
- Authorization (403 for non-super-admin)
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


class TestAuditLogEndpoints:
    """Test GET /api/admin/platform/audit-logs and related endpoints"""

    def test_01_get_audit_logs_returns_200(self, super_admin_token):
        """GET /audit-logs returns 200 with logs and total count"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data
        assert isinstance(data["logs"], list)
        assert isinstance(data["total"], int)
        print(f"✓ GET /audit-logs returned {data['total']} total logs")

    def test_02_get_audit_logs_with_pagination(self, super_admin_token):
        """GET /audit-logs supports limit and skip params"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs?limit=5&skip=0",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) <= 5
        assert data["limit"] == 5
        assert data["skip"] == 0
        print(f"✓ Pagination works: returned {len(data['logs'])} logs with limit=5")

    def test_03_get_audit_logs_filter_by_action(self, super_admin_token):
        """GET /audit-logs?action=X filters by action type"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs?action=impersonation_start",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # All returned logs should have action=impersonation_start
        for log in data["logs"]:
            assert log["action"] == "impersonation_start"
        print(f"✓ Filter by action works: {len(data['logs'])} impersonation_start logs")

    def test_04_get_audit_logs_filter_by_actor_email(self, super_admin_token):
        """GET /audit-logs?actor_email=X filters by actor email (regex)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs?actor_email=admin",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # All returned logs should have actor_email containing 'admin'
        for log in data["logs"]:
            assert "admin" in log.get("actor_email", "").lower()
        print(f"✓ Filter by actor_email works: {len(data['logs'])} logs from admin")

    def test_05_get_audit_logs_filter_by_tenant(self, super_admin_token):
        """GET /audit-logs?target_tenant_id=X filters by target tenant"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs?target_tenant_id=demo",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # All returned logs should have target_tenant_id=demo
        for log in data["logs"]:
            assert log.get("target_tenant_id") == "demo"
        print(f"✓ Filter by target_tenant_id works: {len(data['logs'])} logs for demo tenant")

    def test_06_get_audit_logs_401_without_token(self):
        """GET /audit-logs returns 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/admin/platform/audit-logs")
        assert response.status_code == 401
        print("✓ GET /audit-logs returns 401 without token")

    def test_07_get_audit_logs_403_for_regular_user(self, regular_user_token):
        """GET /audit-logs returns 403 for non-super-admin"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs",
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        assert response.status_code == 403
        print("✓ GET /audit-logs returns 403 for regular user")


class TestAuditLogActions:
    """Test GET /api/admin/platform/audit-logs/actions"""

    def test_08_get_action_types_returns_200(self, super_admin_token):
        """GET /audit-logs/actions returns distinct action types"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs/actions",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "actions" in data
        assert isinstance(data["actions"], list)
        print(f"✓ GET /audit-logs/actions returned {len(data['actions'])} action types: {data['actions']}")

    def test_09_get_action_types_401_without_token(self):
        """GET /audit-logs/actions returns 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/admin/platform/audit-logs/actions")
        assert response.status_code == 401
        print("✓ GET /audit-logs/actions returns 401 without token")

    def test_10_get_action_types_403_for_regular_user(self, regular_user_token):
        """GET /audit-logs/actions returns 403 for non-super-admin"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs/actions",
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        assert response.status_code == 403
        print("✓ GET /audit-logs/actions returns 403 for regular user")


class TestAuditLogExport:
    """Test GET /api/admin/platform/audit-logs/export/csv"""

    def test_11_export_csv_returns_csv_file(self, super_admin_token):
        """GET /audit-logs/export/csv returns CSV download"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs/export/csv",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        assert "attachment" in response.headers.get("content-disposition", "")
        # Check CSV has header row
        content = response.text
        assert "Timestamp" in content
        assert "Action" in content
        assert "Actor" in content
        print(f"✓ CSV export works: {len(content)} bytes, headers present")

    def test_12_export_csv_with_filters(self, super_admin_token):
        """GET /audit-logs/export/csv supports filter params"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs/export/csv?action=impersonation_start",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        print("✓ CSV export with filters works")

    def test_13_export_csv_401_without_token(self):
        """GET /audit-logs/export/csv returns 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/admin/platform/audit-logs/export/csv")
        assert response.status_code == 401
        print("✓ CSV export returns 401 without token")

    def test_14_export_csv_403_for_regular_user(self, regular_user_token):
        """GET /audit-logs/export/csv returns 403 for non-super-admin"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs/export/csv",
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        assert response.status_code == 403
        print("✓ CSV export returns 403 for regular user")


class TestImpersonationAuditLogging:
    """Test that impersonation start/end logs to audit_logs"""

    def test_15_impersonation_start_logs_audit_event(self, super_admin_token):
        """POST /impersonate/{tenant_id} logs 'impersonation_start' event"""
        # Get initial count of impersonation_start logs
        initial_response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs?action=impersonation_start&limit=100",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        initial_count = initial_response.json().get("total", 0)

        # Perform impersonation
        impersonate_response = requests.post(
            f"{BASE_URL}/api/admin/platform/impersonate/demo",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert impersonate_response.status_code == 200
        impersonation_token = impersonate_response.json().get("access_token")
        assert impersonation_token is not None

        # Wait a moment for async logging
        time.sleep(0.5)

        # Check audit log count increased
        after_response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs?action=impersonation_start&limit=100",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        after_count = after_response.json().get("total", 0)
        assert after_count > initial_count, f"Expected audit log count to increase: {initial_count} -> {after_count}"
        
        # Verify latest log has correct fields
        logs = after_response.json().get("logs", [])
        if logs:
            latest = logs[0]
            assert latest["action"] == "impersonation_start"
            assert latest["actor_email"] == SUPER_ADMIN_EMAIL
            assert "target_tenant_id" in latest
        print(f"✓ Impersonation start logged: count {initial_count} -> {after_count}")

    def test_16_impersonation_end_logs_audit_event(self, super_admin_token):
        """POST /impersonate/end logs 'impersonation_end' event"""
        # First impersonate to get impersonation token
        impersonate_response = requests.post(
            f"{BASE_URL}/api/admin/platform/impersonate/demo",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert impersonate_response.status_code == 200
        impersonation_token = impersonate_response.json().get("access_token")

        # Get initial count of impersonation_end logs
        initial_response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs?action=impersonation_end&limit=100",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        initial_count = initial_response.json().get("total", 0)

        # End impersonation using the impersonation token
        end_response = requests.post(
            f"{BASE_URL}/api/admin/platform/impersonate/end",
            headers={"Authorization": f"Bearer {impersonation_token}"}
        )
        assert end_response.status_code == 200

        # Wait a moment for async logging
        time.sleep(0.5)

        # Check audit log count increased
        after_response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs?action=impersonation_end&limit=100",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        after_count = after_response.json().get("total", 0)
        assert after_count > initial_count, f"Expected audit log count to increase: {initial_count} -> {after_count}"
        print(f"✓ Impersonation end logged: count {initial_count} -> {after_count}")


class TestUserOperationsAuditLogging:
    """Test that user CRUD operations log to audit_logs"""

    def test_17_user_role_change_logs_audit_event(self, super_admin_token):
        """PUT /users/{email}/role logs 'user_role_changed' event"""
        # Get initial count
        initial_response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs?action=user_role_changed&limit=100",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        initial_count = initial_response.json().get("total", 0)

        # Change role (toggle between admin and viewer)
        role_response = requests.put(
            f"{BASE_URL}/api/admin/platform/users/{TEST_TARGET_EMAIL}/role",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"tenant_id": "demo", "role": "viewer"}
        )
        assert role_response.status_code == 200

        time.sleep(0.5)

        # Check audit log
        after_response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs?action=user_role_changed&limit=100",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        after_count = after_response.json().get("total", 0)
        assert after_count > initial_count
        
        # Restore original role
        requests.put(
            f"{BASE_URL}/api/admin/platform/users/{TEST_TARGET_EMAIL}/role",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"tenant_id": "demo", "role": "admin"}
        )
        print(f"✓ User role change logged: count {initial_count} -> {after_count}")

    def test_18_user_status_change_logs_audit_event(self, super_admin_token):
        """PUT /users/{email}/status logs 'user_status_changed' event"""
        # Get initial count
        initial_response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs?action=user_status_changed&limit=100",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        initial_count = initial_response.json().get("total", 0)

        # Toggle status
        status_response = requests.put(
            f"{BASE_URL}/api/admin/platform/users/{TEST_TARGET_EMAIL}/status",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"tenant_id": "demo", "is_active": False}
        )
        assert status_response.status_code == 200

        time.sleep(0.5)

        # Check audit log
        after_response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs?action=user_status_changed&limit=100",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        after_count = after_response.json().get("total", 0)
        assert after_count > initial_count

        # Restore status
        requests.put(
            f"{BASE_URL}/api/admin/platform/users/{TEST_TARGET_EMAIL}/status",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"tenant_id": "demo", "is_active": True}
        )
        print(f"✓ User status change logged: count {initial_count} -> {after_count}")


class TestImpersonationMiddlewareAutoLogging:
    """Test that impersonation middleware auto-logs mutating requests"""

    def test_19_impersonated_request_auto_logged(self, super_admin_token):
        """Mutating requests during impersonation log 'impersonated_request' event"""
        # Get impersonation token
        impersonate_response = requests.post(
            f"{BASE_URL}/api/admin/platform/impersonate/demo",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert impersonate_response.status_code == 200
        impersonation_token = impersonate_response.json().get("access_token")

        # Get initial count of impersonated_request logs
        initial_response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs?action=impersonated_request&limit=100",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        initial_count = initial_response.json().get("total", 0)

        # Make a mutating request using impersonation token (POST /api/config)
        config_response = requests.post(
            f"{BASE_URL}/api/config",
            headers={"Authorization": f"Bearer {impersonation_token}"},
            json={
                "noos_enabled": True,
                "ros_enabled": True,
                "size_gap_enabled": True,
                "lifecycle_enabled": True,
                "replenishment_enabled": True,
                "min_shelf_life_days": 30,
                "pivotal_size_threshold": 75,
                "cover_days": 7,
                "ros_period": 30,
                "ideal_doh": 9,
                "topseller_x_factor": 2.0,
                "lead_time_days": 14,
                "safety_days": 7,
                "true_ros_recent_weight": 0.7,
                "true_ros_historical_weight": 0.3,
                "selected_seasons": []
            }
        )
        assert config_response.status_code == 200

        time.sleep(0.5)

        # Check audit log count increased
        after_response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs?action=impersonated_request&limit=100",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        after_count = after_response.json().get("total", 0)
        assert after_count > initial_count, f"Expected impersonated_request log: {initial_count} -> {after_count}"

        # Verify latest log has correct fields
        logs = after_response.json().get("logs", [])
        if logs:
            latest = logs[0]
            assert latest["action"] == "impersonated_request"
            assert "impersonated_by" in latest
            assert latest["impersonated_by"] == SUPER_ADMIN_EMAIL
            assert "method" in latest
            assert "path" in latest
        print(f"✓ Impersonated request auto-logged: count {initial_count} -> {after_count}")


class TestAuditLogDataStructure:
    """Test audit log data structure and fields"""

    def test_20_audit_log_has_required_fields(self, super_admin_token):
        """Audit logs contain required SOC2 fields"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/audit-logs?limit=10",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        logs = response.json().get("logs", [])
        
        if logs:
            log = logs[0]
            # Required fields for SOC2 compliance
            assert "audit_id" in log, "Missing audit_id"
            assert "timestamp" in log, "Missing timestamp"
            assert "action" in log, "Missing action"
            assert "actor_email" in log, "Missing actor_email"
            assert "source" in log, "Missing source"
            assert log["source"] == "super_admin", "Source should be 'super_admin'"
            print(f"✓ Audit log has required fields: {list(log.keys())}")
        else:
            print("⚠ No audit logs found to verify structure")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
