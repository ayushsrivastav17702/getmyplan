"""
Iteration 88: User Management Admin Page Backend Tests
Tests for /api/admin/platform/users endpoints:
- GET /users - list all users with enriched data
- GET /users?tenant_id=demo - filter by tenant
- PUT /users/{email}/role - update user role
- PUT /users/{email}/status - toggle user status
- POST /users/{email}/reset-password - reset password
- POST /users - create new user
- Auth: 401 without token, 403 for non-super-admin
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@demo.com"
SUPER_ADMIN_PASSWORD = "demo1234"
REGULAR_USER_EMAIL = "ayush.srivastav@increff.com"
REGULAR_USER_PASSWORD = "Ayush@114988"

# Test target user for role/status updates
TEST_TARGET_EMAIL = "merch@demo.com"
TEST_TARGET_TENANT = "demo"


@pytest.fixture(scope="module")
def super_admin_token():
    """Get super admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Super admin login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def regular_user_token():
    """Get regular user auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": REGULAR_USER_EMAIL,
        "password": REGULAR_USER_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Regular user login failed: {response.status_code} - {response.text}")


class TestUserListEndpoint:
    """Tests for GET /api/admin/platform/users"""
    
    def test_01_list_users_returns_200(self, super_admin_token):
        """GET /users returns 200 for super admin"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/users",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "users" in data, "Response should contain 'users' key"
        print(f"✓ GET /users returned {len(data['users'])} users")
    
    def test_02_list_users_enriched_data(self, super_admin_token):
        """GET /users returns enriched user data (full_name, username, last_login, mfa_enabled, created_at)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/users",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        users = data.get("users", [])
        assert len(users) > 0, "Should have at least one user"
        
        # Check first user has enriched fields
        user = users[0]
        expected_fields = ["email", "tenant_id", "role", "is_active", "full_name", "username", "mfa_enabled", "created_at"]
        for field in expected_fields:
            assert field in user, f"User should have '{field}' field"
        
        # last_login can be None for users who never logged in
        assert "last_login" in user, "User should have 'last_login' field"
        print(f"✓ User data contains enriched fields: {list(user.keys())}")
    
    def test_03_filter_by_tenant(self, super_admin_token):
        """GET /users?tenant_id=demo filters by tenant"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/users?tenant_id=demo",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        users = data.get("users", [])
        
        # All returned users should be from demo tenant
        for user in users:
            assert user.get("tenant_id") == "demo", f"User {user.get('email')} should be from demo tenant"
        
        print(f"✓ Filter by tenant=demo returned {len(users)} users, all from demo tenant")
    
    def test_04_list_users_401_without_token(self):
        """GET /users returns 401 without auth token"""
        response = requests.get(f"{BASE_URL}/api/admin/platform/users")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /users returns 401 without token")
    
    def test_05_list_users_403_for_regular_user(self, regular_user_token):
        """GET /users returns 403 for non-super-admin"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/users",
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ GET /users returns 403 for regular user")


class TestUpdateUserRole:
    """Tests for PUT /api/admin/platform/users/{email}/role"""
    
    def test_06_update_role_returns_200(self, super_admin_token):
        """PUT /users/{email}/role updates user role"""
        # First get current role
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/users?tenant_id={TEST_TARGET_TENANT}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        users = response.json().get("users", [])
        target_user = next((u for u in users if u.get("email") == TEST_TARGET_EMAIL), None)
        
        if not target_user:
            pytest.skip(f"Test target user {TEST_TARGET_EMAIL} not found")
        
        original_role = target_user.get("role")
        new_role = "merchandiser" if original_role != "merchandiser" else "viewer"
        
        # Update role
        response = requests.put(
            f"{BASE_URL}/api/admin/platform/users/{TEST_TARGET_EMAIL}/role",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"tenant_id": TEST_TARGET_TENANT, "role": new_role}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert data.get("role") == new_role
        print(f"✓ Role updated from {original_role} to {new_role}")
        
        # Restore original role
        response = requests.put(
            f"{BASE_URL}/api/admin/platform/users/{TEST_TARGET_EMAIL}/role",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"tenant_id": TEST_TARGET_TENANT, "role": original_role}
        )
        assert response.status_code == 200
        print(f"✓ Role restored to {original_role}")
    
    def test_07_update_role_401_without_token(self):
        """PUT /users/{email}/role returns 401 without token"""
        response = requests.put(
            f"{BASE_URL}/api/admin/platform/users/{TEST_TARGET_EMAIL}/role",
            json={"tenant_id": TEST_TARGET_TENANT, "role": "viewer"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ PUT /users/{email}/role returns 401 without token")
    
    def test_08_update_role_403_for_regular_user(self, regular_user_token):
        """PUT /users/{email}/role returns 403 for non-super-admin"""
        response = requests.put(
            f"{BASE_URL}/api/admin/platform/users/{TEST_TARGET_EMAIL}/role",
            headers={"Authorization": f"Bearer {regular_user_token}"},
            json={"tenant_id": TEST_TARGET_TENANT, "role": "viewer"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ PUT /users/{email}/role returns 403 for regular user")
    
    def test_09_update_role_404_nonexistent_mapping(self, super_admin_token):
        """PUT /users/{email}/role returns 404 for non-existent user-tenant mapping"""
        response = requests.put(
            f"{BASE_URL}/api/admin/platform/users/nonexistent@test.com/role",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"tenant_id": "demo", "role": "viewer"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ PUT /users/{email}/role returns 404 for non-existent mapping")


class TestUpdateUserStatus:
    """Tests for PUT /api/admin/platform/users/{email}/status"""
    
    def test_10_toggle_status_returns_200(self, super_admin_token):
        """PUT /users/{email}/status toggles user active status"""
        # First get current status
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/users?tenant_id={TEST_TARGET_TENANT}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        users = response.json().get("users", [])
        target_user = next((u for u in users if u.get("email") == TEST_TARGET_EMAIL), None)
        
        if not target_user:
            pytest.skip(f"Test target user {TEST_TARGET_EMAIL} not found")
        
        original_status = target_user.get("is_active", True)
        new_status = not original_status
        
        # Toggle status
        response = requests.put(
            f"{BASE_URL}/api/admin/platform/users/{TEST_TARGET_EMAIL}/status",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"tenant_id": TEST_TARGET_TENANT, "is_active": new_status}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert data.get("is_active") == new_status
        print(f"✓ Status toggled from {original_status} to {new_status}")
        
        # Restore original status
        response = requests.put(
            f"{BASE_URL}/api/admin/platform/users/{TEST_TARGET_EMAIL}/status",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"tenant_id": TEST_TARGET_TENANT, "is_active": original_status}
        )
        assert response.status_code == 200
        print(f"✓ Status restored to {original_status}")
    
    def test_11_toggle_status_401_without_token(self):
        """PUT /users/{email}/status returns 401 without token"""
        response = requests.put(
            f"{BASE_URL}/api/admin/platform/users/{TEST_TARGET_EMAIL}/status",
            json={"tenant_id": TEST_TARGET_TENANT, "is_active": False}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ PUT /users/{email}/status returns 401 without token")
    
    def test_12_toggle_status_403_for_regular_user(self, regular_user_token):
        """PUT /users/{email}/status returns 403 for non-super-admin"""
        response = requests.put(
            f"{BASE_URL}/api/admin/platform/users/{TEST_TARGET_EMAIL}/status",
            headers={"Authorization": f"Bearer {regular_user_token}"},
            json={"tenant_id": TEST_TARGET_TENANT, "is_active": False}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ PUT /users/{email}/status returns 403 for regular user")


class TestResetPassword:
    """Tests for POST /api/admin/platform/users/{email}/reset-password"""
    
    def test_13_reset_password_returns_temp_password(self, super_admin_token):
        """POST /users/{email}/reset-password returns temp_password"""
        response = requests.post(
            f"{BASE_URL}/api/admin/platform/users/{TEST_TARGET_EMAIL}/reset-password",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert "temp_password" in data, "Response should contain temp_password"
        assert len(data.get("temp_password", "")) > 8, "Temp password should be at least 8 chars"
        print(f"✓ Password reset returned temp_password: {data.get('temp_password')[:4]}...")
    
    def test_14_reset_password_401_without_token(self):
        """POST /users/{email}/reset-password returns 401 without token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/platform/users/{TEST_TARGET_EMAIL}/reset-password"
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ POST /users/{email}/reset-password returns 401 without token")
    
    def test_15_reset_password_403_for_regular_user(self, regular_user_token):
        """POST /users/{email}/reset-password returns 403 for non-super-admin"""
        response = requests.post(
            f"{BASE_URL}/api/admin/platform/users/{TEST_TARGET_EMAIL}/reset-password",
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ POST /users/{email}/reset-password returns 403 for regular user")
    
    def test_16_reset_password_404_nonexistent_user(self, super_admin_token):
        """POST /users/{email}/reset-password returns 404 for non-existent user"""
        response = requests.post(
            f"{BASE_URL}/api/admin/platform/users/nonexistent@test.com/reset-password",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ POST /users/{email}/reset-password returns 404 for non-existent user")


class TestCreateUser:
    """Tests for POST /api/admin/platform/users"""
    
    def test_17_create_user_returns_temp_password(self, super_admin_token):
        """POST /users creates user and returns temp_password"""
        import time
        test_email = f"TEST_user_{int(time.time())}@test.com"
        
        response = requests.post(
            f"{BASE_URL}/api/admin/platform/users",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={
                "email": test_email,
                "name": "Test User",
                "tenant_id": "demo",
                "role": "viewer"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert "temp_password" in data
        assert data.get("email") == test_email
        print(f"✓ Created user {test_email} with temp_password")
    
    def test_18_create_user_401_without_token(self):
        """POST /users returns 401 without token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/platform/users",
            json={
                "email": "test@test.com",
                "name": "Test",
                "tenant_id": "demo",
                "role": "viewer"
            }
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ POST /users returns 401 without token")
    
    def test_19_create_user_403_for_regular_user(self, regular_user_token):
        """POST /users returns 403 for non-super-admin"""
        response = requests.post(
            f"{BASE_URL}/api/admin/platform/users",
            headers={"Authorization": f"Bearer {regular_user_token}"},
            json={
                "email": "test@test.com",
                "name": "Test",
                "tenant_id": "demo",
                "role": "viewer"
            }
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ POST /users returns 403 for regular user")
    
    def test_20_create_user_404_nonexistent_tenant(self, super_admin_token):
        """POST /users returns 404 for non-existent tenant"""
        response = requests.post(
            f"{BASE_URL}/api/admin/platform/users",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={
                "email": "test@test.com",
                "name": "Test",
                "tenant_id": "nonexistent_tenant_xyz",
                "role": "viewer"
            }
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ POST /users returns 404 for non-existent tenant")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
