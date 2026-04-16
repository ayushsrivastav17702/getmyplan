"""
Super Admin Panel API Tests - Iteration 86
Tests for tenant management, user management, and impersonation endpoints.
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@demo.com"
SUPER_ADMIN_PASSWORD = "demo1234"
REGULAR_USER_EMAIL = "ayush.srivastav@increff.com"
REGULAR_USER_PASSWORD = "Ayush@114988"


@pytest.fixture(scope="module")
def super_admin_token():
    """Get super admin JWT token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Super admin login failed: {response.text}"
    data = response.json()
    assert data.get("user", {}).get("role") == "super_admin", "User is not super_admin"
    return data["access_token"]


@pytest.fixture(scope="module")
def regular_user_token():
    """Get regular user JWT token (non-super-admin)"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": REGULAR_USER_EMAIL,
        "password": REGULAR_USER_PASSWORD
    })
    assert response.status_code == 200, f"Regular user login failed: {response.text}"
    data = response.json()
    assert data.get("user", {}).get("role") != "super_admin", "User should not be super_admin"
    return data["access_token"]


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


# ═══════════════════════════════════════════════════════════
# TENANT ENDPOINTS TESTS
# ═══════════════════════════════════════════════════════════

class TestTenantEndpoints:
    """Tests for /api/admin/platform/tenants endpoints"""

    def test_list_tenants_success(self, api_client, super_admin_token):
        """GET /api/admin/platform/tenants - returns list of tenants with user_count"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/platform/tenants",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "tenants" in data, "Response should contain 'tenants' key"
        assert isinstance(data["tenants"], list), "tenants should be a list"
        assert len(data["tenants"]) > 0, "Should have at least one tenant"
        
        # Verify tenant structure
        tenant = data["tenants"][0]
        assert "tenant_id" in tenant, "Tenant should have tenant_id"
        assert "user_count" in tenant, "Tenant should have user_count"
        assert isinstance(tenant["user_count"], int), "user_count should be integer"
        print(f"Found {len(data['tenants'])} tenants")

    def test_list_tenants_403_for_non_super_admin(self, api_client, regular_user_token):
        """GET /api/admin/platform/tenants - returns 403 for non-super-admin"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/platform/tenants",
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        assert "Super Admin" in response.json().get("detail", ""), "Should mention Super Admin"

    def test_create_tenant_success(self, api_client, super_admin_token):
        """POST /api/admin/platform/tenants - creates new tenant with admin user"""
        unique_id = str(uuid.uuid4())[:8]
        tenant_id = f"test_{unique_id}"
        
        response = api_client.post(
            f"{BASE_URL}/api/admin/platform/tenants",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={
                "tenant_id": tenant_id,
                "company_name": f"Test Company {unique_id}",
                "admin_email": f"admin_{unique_id}@test.com",
                "admin_name": f"Test Admin {unique_id}",
                "plan": "professional"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Response should indicate success"
        assert data.get("tenant_id") == tenant_id, "Should return created tenant_id"
        assert "temp_password" in data, "Should return temp_password"
        assert len(data["temp_password"]) > 0, "temp_password should not be empty"
        print(f"Created tenant: {tenant_id} with temp password")

    def test_create_tenant_duplicate_fails(self, api_client, super_admin_token):
        """POST /api/admin/platform/tenants - fails for duplicate tenant_id"""
        response = api_client.post(
            f"{BASE_URL}/api/admin/platform/tenants",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={
                "tenant_id": "demo",  # Already exists
                "company_name": "Duplicate Demo",
                "admin_email": "dup@test.com",
                "admin_name": "Dup Admin",
                "plan": "starter"
            }
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "already exists" in response.json().get("detail", "").lower()

    def test_create_tenant_403_for_non_super_admin(self, api_client, regular_user_token):
        """POST /api/admin/platform/tenants - returns 403 for non-super-admin"""
        response = api_client.post(
            f"{BASE_URL}/api/admin/platform/tenants",
            headers={"Authorization": f"Bearer {regular_user_token}"},
            json={
                "tenant_id": "unauthorized_tenant",
                "company_name": "Unauthorized",
                "admin_email": "unauth@test.com",
                "admin_name": "Unauth Admin",
                "plan": "starter"
            }
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    def test_update_tenant_status_suspend(self, api_client, super_admin_token):
        """PUT /api/admin/platform/tenants/{id}/status - suspends tenant"""
        # First create a test tenant
        unique_id = str(uuid.uuid4())[:8]
        tenant_id = f"suspend_test_{unique_id}"
        
        create_resp = api_client.post(
            f"{BASE_URL}/api/admin/platform/tenants",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={
                "tenant_id": tenant_id,
                "company_name": f"Suspend Test {unique_id}",
                "admin_email": f"suspend_{unique_id}@test.com",
                "admin_name": "Suspend Admin",
                "plan": "starter"
            }
        )
        assert create_resp.status_code == 200, f"Failed to create test tenant: {create_resp.text}"
        
        # Now suspend it
        response = api_client.put(
            f"{BASE_URL}/api/admin/platform/tenants/{tenant_id}/status",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"status": "suspended"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert data.get("status") == "suspended"
        print(f"Suspended tenant: {tenant_id}")

    def test_update_tenant_status_activate(self, api_client, super_admin_token):
        """PUT /api/admin/platform/tenants/{id}/status - activates tenant"""
        # Use an existing suspended tenant or create one
        unique_id = str(uuid.uuid4())[:8]
        tenant_id = f"activate_test_{unique_id}"
        
        # Create and suspend
        api_client.post(
            f"{BASE_URL}/api/admin/platform/tenants",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={
                "tenant_id": tenant_id,
                "company_name": f"Activate Test {unique_id}",
                "admin_email": f"activate_{unique_id}@test.com",
                "admin_name": "Activate Admin",
                "plan": "starter"
            }
        )
        api_client.put(
            f"{BASE_URL}/api/admin/platform/tenants/{tenant_id}/status",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"status": "suspended"}
        )
        
        # Now activate
        response = api_client.put(
            f"{BASE_URL}/api/admin/platform/tenants/{tenant_id}/status",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"status": "active"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json().get("status") == "active"

    def test_update_tenant_status_404_not_found(self, api_client, super_admin_token):
        """PUT /api/admin/platform/tenants/{id}/status - returns 404 for non-existent tenant"""
        response = api_client.put(
            f"{BASE_URL}/api/admin/platform/tenants/nonexistent_tenant_xyz/status",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"status": "suspended"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    def test_delete_tenant_success(self, api_client, super_admin_token):
        """DELETE /api/admin/platform/tenants/{id} - deletes tenant"""
        # Create a tenant to delete
        unique_id = str(uuid.uuid4())[:8]
        tenant_id = f"delete_test_{unique_id}"
        
        api_client.post(
            f"{BASE_URL}/api/admin/platform/tenants",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={
                "tenant_id": tenant_id,
                "company_name": f"Delete Test {unique_id}",
                "admin_email": f"delete_{unique_id}@test.com",
                "admin_name": "Delete Admin",
                "plan": "starter"
            }
        )
        
        # Delete it
        response = api_client.delete(
            f"{BASE_URL}/api/admin/platform/tenants/{tenant_id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.json().get("success") == True
        print(f"Deleted tenant: {tenant_id}")

    def test_delete_demo_tenant_fails(self, api_client, super_admin_token):
        """DELETE /api/admin/platform/tenants/demo - cannot delete demo tenant"""
        response = api_client.delete(
            f"{BASE_URL}/api/admin/platform/tenants/demo",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "demo" in response.json().get("detail", "").lower()


# ═══════════════════════════════════════════════════════════
# USER ENDPOINTS TESTS
# ═══════════════════════════════════════════════════════════

class TestUserEndpoints:
    """Tests for /api/admin/platform/users endpoints"""

    def test_list_all_users_success(self, api_client, super_admin_token):
        """GET /api/admin/platform/users - returns all users across tenants"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/platform/users",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "users" in data, "Response should contain 'users' key"
        assert isinstance(data["users"], list), "users should be a list"
        assert len(data["users"]) > 0, "Should have at least one user"
        
        # Verify user structure
        user = data["users"][0]
        assert "email" in user, "User should have email"
        assert "tenant_id" in user, "User should have tenant_id"
        assert "role" in user, "User should have role"
        print(f"Found {len(data['users'])} users")

    def test_list_users_filter_by_tenant(self, api_client, super_admin_token):
        """GET /api/admin/platform/users?tenant_id=demo - filters by tenant"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/platform/users?tenant_id=demo",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        for user in data["users"]:
            assert user["tenant_id"] == "demo", f"User {user['email']} should be in demo tenant"

    def test_list_users_403_for_non_super_admin(self, api_client, regular_user_token):
        """GET /api/admin/platform/users - returns 403 for non-super-admin"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/platform/users",
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    def test_create_user_success(self, api_client, super_admin_token):
        """POST /api/admin/platform/users - creates user and maps to tenant"""
        unique_id = str(uuid.uuid4())[:8]
        
        response = api_client.post(
            f"{BASE_URL}/api/admin/platform/users",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={
                "email": f"newuser_{unique_id}@test.com",
                "name": f"New User {unique_id}",
                "tenant_id": "demo",  # Use existing tenant
                "role": "viewer"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "temp_password" in data, "Should return temp_password"
        assert len(data["temp_password"]) > 0
        print(f"Created user: newuser_{unique_id}@test.com")

    def test_create_user_invalid_tenant_fails(self, api_client, super_admin_token):
        """POST /api/admin/platform/users - fails for non-existent tenant"""
        response = api_client.post(
            f"{BASE_URL}/api/admin/platform/users",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={
                "email": "invalid_tenant_user@test.com",
                "name": "Invalid Tenant User",
                "tenant_id": "nonexistent_tenant_xyz",
                "role": "viewer"
            }
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        assert "not found" in response.json().get("detail", "").lower()

    def test_create_user_403_for_non_super_admin(self, api_client, regular_user_token):
        """POST /api/admin/platform/users - returns 403 for non-super-admin"""
        response = api_client.post(
            f"{BASE_URL}/api/admin/platform/users",
            headers={"Authorization": f"Bearer {regular_user_token}"},
            json={
                "email": "unauthorized_user@test.com",
                "name": "Unauthorized User",
                "tenant_id": "demo",
                "role": "viewer"
            }
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"


# ═══════════════════════════════════════════════════════════
# IMPERSONATION ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════

class TestImpersonationEndpoint:
    """Tests for /api/admin/platform/impersonate/{tenant_id} endpoint"""

    def test_impersonate_success(self, api_client, super_admin_token):
        """POST /api/admin/platform/impersonate/{id} - returns JWT for tenant impersonation"""
        response = api_client.post(
            f"{BASE_URL}/api/admin/platform/impersonate/increff",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "access_token" in data, "Should return access_token"
        assert data.get("tenant_id") == "increff"
        assert "email" in data, "Should return impersonated user email"
        print(f"Impersonated tenant: increff as {data['email']}")

    def test_impersonate_404_for_nonexistent_tenant(self, api_client, super_admin_token):
        """POST /api/admin/platform/impersonate/{id} - returns 404 for non-existent tenant"""
        response = api_client.post(
            f"{BASE_URL}/api/admin/platform/impersonate/nonexistent_tenant_xyz",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    def test_impersonate_403_for_non_super_admin(self, api_client, regular_user_token):
        """POST /api/admin/platform/impersonate/{id} - returns 403 for non-super-admin"""
        response = api_client.post(
            f"{BASE_URL}/api/admin/platform/impersonate/demo",
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"


# ═══════════════════════════════════════════════════════════
# AUTHENTICATION TESTS
# ═══════════════════════════════════════════════════════════

class TestAuthentication:
    """Tests for authentication requirements on admin endpoints"""

    def test_tenants_401_without_token(self, api_client):
        """GET /api/admin/platform/tenants - returns 401 without token"""
        response = api_client.get(f"{BASE_URL}/api/admin/platform/tenants")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    def test_users_401_without_token(self, api_client):
        """GET /api/admin/platform/users - returns 401 without token"""
        response = api_client.get(f"{BASE_URL}/api/admin/platform/users")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    def test_impersonate_401_without_token(self, api_client):
        """POST /api/admin/platform/impersonate/{id} - returns 401 without token"""
        response = api_client.post(f"{BASE_URL}/api/admin/platform/impersonate/demo")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
