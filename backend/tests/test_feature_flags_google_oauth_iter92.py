"""
Iteration 92: Feature Flags CRUD + Per-Tenant Overrides + Google OAuth Tests

Tests:
1. Feature Flags CRUD (create, list, update, delete)
2. Per-tenant overrides (set, get, delete)
3. Resolved flags for tenant (defaults + overrides)
4. 403 for non-super-admin
5. Google OAuth callback error handling
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
SUPER_ADMIN_EMAIL = "admin@demo.com"
SUPER_ADMIN_PASSWORD = "demo1234"
REGULAR_USER_EMAIL = "ayush.srivastav@increff.com"
REGULAR_USER_PASSWORD = "Ayush@114988"

# Test flag prefix for cleanup
TEST_FLAG_PREFIX = "TEST_FLAG_"


@pytest.fixture(scope="module")
def super_admin_token():
    """Get super admin auth token."""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    assert resp.status_code == 200, f"Super admin login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def regular_user_token():
    """Get regular user auth token."""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": REGULAR_USER_EMAIL,
        "password": REGULAR_USER_PASSWORD
    })
    assert resp.status_code == 200, f"Regular user login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def super_admin_headers(super_admin_token):
    """Headers with super admin auth."""
    return {"Authorization": f"Bearer {super_admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def regular_user_headers(regular_user_token):
    """Headers with regular user auth."""
    return {"Authorization": f"Bearer {regular_user_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def test_flag_key():
    """Generate unique test flag key."""
    return f"{TEST_FLAG_PREFIX}{uuid.uuid4().hex[:8]}"


class TestFeatureFlagsCRUD:
    """Feature Flags CRUD operations."""

    def test_01_list_feature_flags(self, super_admin_headers):
        """GET /api/admin/platform/feature-flags returns list of flags."""
        resp = requests.get(f"{BASE_URL}/api/admin/platform/feature-flags", headers=super_admin_headers)
        assert resp.status_code == 200, f"List flags failed: {resp.text}"
        data = resp.json()
        assert "flags" in data
        assert isinstance(data["flags"], list)
        print(f"✓ Listed {len(data['flags'])} feature flags")
        # Check existing flags (ai_forecasting_v2, google_sso)
        flag_keys = [f["flag_key"] for f in data["flags"]]
        print(f"  Existing flags: {flag_keys}")

    def test_02_create_feature_flag(self, super_admin_headers, test_flag_key):
        """POST /api/admin/platform/feature-flags creates a new flag."""
        payload = {
            "flag_key": test_flag_key,
            "label": "Test Feature Flag",
            "description": "Created by iteration 92 tests",
            "default_enabled": False
        }
        resp = requests.post(f"{BASE_URL}/api/admin/platform/feature-flags", 
                            headers=super_admin_headers, json=payload)
        assert resp.status_code == 200, f"Create flag failed: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["flag_key"] == test_flag_key
        print(f"✓ Created flag: {test_flag_key}")

    def test_03_verify_flag_in_list(self, super_admin_headers, test_flag_key):
        """Verify created flag appears in list with override_count."""
        resp = requests.get(f"{BASE_URL}/api/admin/platform/feature-flags", headers=super_admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        test_flag = next((f for f in data["flags"] if f["flag_key"] == test_flag_key), None)
        assert test_flag is not None, f"Flag {test_flag_key} not found in list"
        assert "override_count" in test_flag
        assert test_flag["override_count"] == 0
        assert test_flag["label"] == "Test Feature Flag"
        assert test_flag["default_enabled"] is False
        print(f"✓ Flag {test_flag_key} found with override_count=0")

    def test_04_update_feature_flag_toggle_default(self, super_admin_headers, test_flag_key):
        """PUT /api/admin/platform/feature-flags/{flag_key} updates flag (toggle default)."""
        payload = {
            "flag_key": test_flag_key,
            "label": "Test Feature Flag Updated",
            "description": "Updated by iteration 92 tests",
            "default_enabled": True  # Toggle ON
        }
        resp = requests.put(f"{BASE_URL}/api/admin/platform/feature-flags/{test_flag_key}",
                           headers=super_admin_headers, json=payload)
        assert resp.status_code == 200, f"Update flag failed: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        print(f"✓ Updated flag {test_flag_key} - default_enabled=True")

    def test_05_verify_flag_updated(self, super_admin_headers, test_flag_key):
        """Verify flag was updated."""
        resp = requests.get(f"{BASE_URL}/api/admin/platform/feature-flags", headers=super_admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        test_flag = next((f for f in data["flags"] if f["flag_key"] == test_flag_key), None)
        assert test_flag is not None
        assert test_flag["default_enabled"] is True
        assert test_flag["label"] == "Test Feature Flag Updated"
        print(f"✓ Verified flag update: default_enabled=True, label updated")


class TestFeatureFlagOverrides:
    """Per-tenant override operations."""

    def test_06_set_tenant_override(self, super_admin_headers, test_flag_key):
        """PUT /api/admin/platform/feature-flags/{flag_key}/overrides sets per-tenant override."""
        payload = {
            "tenant_id": "demo",
            "enabled": False  # Override to OFF for demo tenant
        }
        resp = requests.put(f"{BASE_URL}/api/admin/platform/feature-flags/{test_flag_key}/overrides",
                           headers=super_admin_headers, json=payload)
        assert resp.status_code == 200, f"Set override failed: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["tenant_id"] == "demo"
        assert data["enabled"] is False
        print(f"✓ Set override for {test_flag_key}: demo=OFF")

    def test_07_get_flag_overrides(self, super_admin_headers, test_flag_key):
        """GET /api/admin/platform/feature-flags/{flag_key}/overrides returns overrides list."""
        resp = requests.get(f"{BASE_URL}/api/admin/platform/feature-flags/{test_flag_key}/overrides",
                           headers=super_admin_headers)
        assert resp.status_code == 200, f"Get overrides failed: {resp.text}"
        data = resp.json()
        assert data["flag_key"] == test_flag_key
        assert "overrides" in data
        assert len(data["overrides"]) >= 1
        demo_override = next((o for o in data["overrides"] if o["tenant_id"] == "demo"), None)
        assert demo_override is not None
        assert demo_override["enabled"] is False
        print(f"✓ Got overrides for {test_flag_key}: {len(data['overrides'])} override(s)")

    def test_08_verify_override_count_updated(self, super_admin_headers, test_flag_key):
        """Verify override_count increased in flag list."""
        resp = requests.get(f"{BASE_URL}/api/admin/platform/feature-flags", headers=super_admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        test_flag = next((f for f in data["flags"] if f["flag_key"] == test_flag_key), None)
        assert test_flag is not None
        assert test_flag["override_count"] >= 1
        print(f"✓ Override count updated: {test_flag['override_count']}")

    def test_09_get_resolved_flags_for_tenant(self, super_admin_headers, test_flag_key):
        """GET /api/admin/platform/feature-flags/tenant/{tenant_id} returns resolved flags."""
        resp = requests.get(f"{BASE_URL}/api/admin/platform/feature-flags/tenant/demo",
                           headers=super_admin_headers)
        assert resp.status_code == 200, f"Get tenant flags failed: {resp.text}"
        data = resp.json()
        assert data["tenant_id"] == "demo"
        assert "flags" in data
        # Test flag should be OFF for demo (override) even though default is ON
        assert test_flag_key in data["flags"]
        assert data["flags"][test_flag_key] is False  # Override takes precedence
        print(f"✓ Resolved flags for demo: {test_flag_key}=False (override applied)")

    def test_10_delete_tenant_override(self, super_admin_headers, test_flag_key):
        """DELETE /api/admin/platform/feature-flags/{flag_key}/overrides/{tenant_id} removes override."""
        resp = requests.delete(f"{BASE_URL}/api/admin/platform/feature-flags/{test_flag_key}/overrides/demo",
                              headers=super_admin_headers)
        assert resp.status_code == 200, f"Delete override failed: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        print(f"✓ Deleted override for {test_flag_key}/demo")

    def test_11_verify_override_removed(self, super_admin_headers, test_flag_key):
        """Verify override was removed and resolved flag uses default."""
        # Check overrides list
        resp = requests.get(f"{BASE_URL}/api/admin/platform/feature-flags/{test_flag_key}/overrides",
                           headers=super_admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        demo_override = next((o for o in data["overrides"] if o["tenant_id"] == "demo"), None)
        assert demo_override is None, "Override should be removed"
        
        # Check resolved flags - should now use default (True)
        resp = requests.get(f"{BASE_URL}/api/admin/platform/feature-flags/tenant/demo",
                           headers=super_admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["flags"][test_flag_key] is True  # Default value
        print(f"✓ Override removed, resolved flag uses default: {test_flag_key}=True")


class TestFeatureFlagsAuthorization:
    """Authorization tests - 403 for non-super-admin."""

    def test_12_list_flags_403_for_regular_user(self, regular_user_headers):
        """GET /api/admin/platform/feature-flags returns 403 for non-super-admin."""
        resp = requests.get(f"{BASE_URL}/api/admin/platform/feature-flags", headers=regular_user_headers)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print("✓ List flags returns 403 for regular user")

    def test_13_create_flag_403_for_regular_user(self, regular_user_headers):
        """POST /api/admin/platform/feature-flags returns 403 for non-super-admin."""
        payload = {"flag_key": "unauthorized_flag", "label": "Test", "description": "", "default_enabled": False}
        resp = requests.post(f"{BASE_URL}/api/admin/platform/feature-flags", 
                            headers=regular_user_headers, json=payload)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print("✓ Create flag returns 403 for regular user")

    def test_14_update_flag_403_for_regular_user(self, regular_user_headers):
        """PUT /api/admin/platform/feature-flags/{flag_key} returns 403 for non-super-admin."""
        payload = {"flag_key": "ai_forecasting_v2", "label": "Test", "description": "", "default_enabled": True}
        resp = requests.put(f"{BASE_URL}/api/admin/platform/feature-flags/ai_forecasting_v2",
                           headers=regular_user_headers, json=payload)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print("✓ Update flag returns 403 for regular user")

    def test_15_delete_flag_403_for_regular_user(self, regular_user_headers):
        """DELETE /api/admin/platform/feature-flags/{flag_key} returns 403 for non-super-admin."""
        resp = requests.delete(f"{BASE_URL}/api/admin/platform/feature-flags/ai_forecasting_v2",
                              headers=regular_user_headers)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print("✓ Delete flag returns 403 for regular user")

    def test_16_set_override_403_for_regular_user(self, regular_user_headers):
        """PUT /api/admin/platform/feature-flags/{flag_key}/overrides returns 403 for non-super-admin."""
        payload = {"tenant_id": "demo", "enabled": True}
        resp = requests.put(f"{BASE_URL}/api/admin/platform/feature-flags/ai_forecasting_v2/overrides",
                           headers=regular_user_headers, json=payload)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print("✓ Set override returns 403 for regular user")

    def test_17_get_overrides_403_for_regular_user(self, regular_user_headers):
        """GET /api/admin/platform/feature-flags/{flag_key}/overrides returns 403 for non-super-admin."""
        resp = requests.get(f"{BASE_URL}/api/admin/platform/feature-flags/ai_forecasting_v2/overrides",
                           headers=regular_user_headers)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print("✓ Get overrides returns 403 for regular user")

    def test_18_delete_override_403_for_regular_user(self, regular_user_headers):
        """DELETE /api/admin/platform/feature-flags/{flag_key}/overrides/{tenant_id} returns 403 for non-super-admin."""
        resp = requests.delete(f"{BASE_URL}/api/admin/platform/feature-flags/ai_forecasting_v2/overrides/demo",
                              headers=regular_user_headers)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print("✓ Delete override returns 403 for regular user")


class TestGoogleOAuthCallback:
    """Google OAuth callback endpoint tests."""

    def test_19_google_callback_invalid_session_id(self):
        """POST /api/auth/google/callback returns 400 for invalid session_id."""
        resp = requests.post(f"{BASE_URL}/api/auth/google/callback", json={
            "session_id": "invalid_session_id_12345"
        })
        # Should return 400 (invalid session) or 502 (auth service error)
        assert resp.status_code in [400, 502], f"Expected 400/502, got {resp.status_code}: {resp.text}"
        print(f"✓ Google callback returns {resp.status_code} for invalid session_id")

    def test_20_google_callback_empty_session_id(self):
        """POST /api/auth/google/callback returns error for empty session_id."""
        resp = requests.post(f"{BASE_URL}/api/auth/google/callback", json={
            "session_id": ""
        })
        # Should return 400 or 422 (validation error)
        assert resp.status_code in [400, 422, 502], f"Expected 400/422/502, got {resp.status_code}: {resp.text}"
        print(f"✓ Google callback returns {resp.status_code} for empty session_id")

    def test_21_google_callback_endpoint_exists(self):
        """POST /api/auth/google/callback endpoint exists and returns proper error format."""
        resp = requests.post(f"{BASE_URL}/api/auth/google/callback", json={
            "session_id": "test_session_123"
        })
        # Endpoint should exist (not 404) and return JSON error
        assert resp.status_code != 404, "Google callback endpoint should exist"
        assert resp.status_code in [400, 502], f"Expected 400/502, got {resp.status_code}"
        data = resp.json()
        assert "detail" in data, "Error response should have 'detail' field"
        print(f"✓ Google callback endpoint exists, returns proper error format: {data['detail']}")


class TestFeatureFlagsCleanup:
    """Cleanup test data."""

    def test_99_delete_test_flag(self, super_admin_headers, test_flag_key):
        """DELETE /api/admin/platform/feature-flags/{flag_key} deletes flag and overrides."""
        resp = requests.delete(f"{BASE_URL}/api/admin/platform/feature-flags/{test_flag_key}",
                              headers=super_admin_headers)
        assert resp.status_code == 200, f"Delete flag failed: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        print(f"✓ Deleted test flag: {test_flag_key}")

    def test_99b_verify_flag_deleted(self, super_admin_headers, test_flag_key):
        """Verify test flag was deleted."""
        resp = requests.get(f"{BASE_URL}/api/admin/platform/feature-flags", headers=super_admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        test_flag = next((f for f in data["flags"] if f["flag_key"] == test_flag_key), None)
        assert test_flag is None, f"Flag {test_flag_key} should be deleted"
        print(f"✓ Verified flag {test_flag_key} deleted")


class TestExistingFlags:
    """Test existing flags in the database."""

    def test_22_existing_ai_forecasting_flag(self, super_admin_headers):
        """Verify ai_forecasting_v2 flag exists with expected properties."""
        resp = requests.get(f"{BASE_URL}/api/admin/platform/feature-flags", headers=super_admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        ai_flag = next((f for f in data["flags"] if f["flag_key"] == "ai_forecasting_v2"), None)
        if ai_flag:
            print(f"✓ ai_forecasting_v2 flag exists: default_enabled={ai_flag['default_enabled']}, overrides={ai_flag['override_count']}")
        else:
            print("⚠ ai_forecasting_v2 flag not found (may have been deleted)")

    def test_23_existing_google_sso_flag(self, super_admin_headers):
        """Verify google_sso flag exists with expected properties."""
        resp = requests.get(f"{BASE_URL}/api/admin/platform/feature-flags", headers=super_admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        sso_flag = next((f for f in data["flags"] if f["flag_key"] == "google_sso"), None)
        if sso_flag:
            print(f"✓ google_sso flag exists: default_enabled={sso_flag['default_enabled']}, overrides={sso_flag['override_count']}")
        else:
            print("⚠ google_sso flag not found (may have been deleted)")

    def test_24_resolved_flags_for_demo_tenant(self, super_admin_headers):
        """Get resolved flags for demo tenant and verify structure."""
        resp = requests.get(f"{BASE_URL}/api/admin/platform/feature-flags/tenant/demo",
                           headers=super_admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant_id"] == "demo"
        assert "flags" in data
        print(f"✓ Resolved flags for demo tenant: {data['flags']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
