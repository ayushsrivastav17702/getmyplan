"""
RBAC Integration Tests - Iteration 16
Tests for Auth + RBAC integration with all pages:
- Permission-based route guards
- Sidebar nav filtering by role
- Access Denied page functionality
- Role-specific permission counts
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
DEMO_ADMIN = {"email": "admin@demo.com", "password": "demo1234", "tenant_id": "demo", "role": "admin"}
DEMO_MERCHANDISER = {"email": "merch@demo.com", "password": "MerchPass123!", "tenant_id": "demo", "role": "merchandiser"}
DEMO_STORE_MANAGER = {"email": "store@demo.com", "password": "StorePass123!", "tenant_id": "demo", "role": "store_manager"}


class TestLoginPermissions:
    """Test that login returns correct permissions for each role"""
    
    def test_admin_login_returns_21_permissions(self):
        """Admin should have 21 permissions (all permissions)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_ADMIN["email"], "password": DEMO_ADMIN["password"]},
            headers={"X-Tenant-ID": DEMO_ADMIN["tenant_id"]}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify user object has permissions
        assert "user" in data, "Response missing 'user' field"
        user = data["user"]
        assert "permissions" in user, "User missing 'permissions' field"
        
        permissions = user["permissions"]
        print(f"Admin permissions count: {len(permissions)}")
        print(f"Admin permissions: {permissions}")
        
        # Admin should have 21 permissions (all)
        assert len(permissions) == 21, f"Expected 21 permissions for admin, got {len(permissions)}"
        assert user["role"] == "admin"
    
    def test_merchandiser_login_returns_15_permissions(self):
        """Merchandiser should have 15 permissions"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_MERCHANDISER["email"], "password": DEMO_MERCHANDISER["password"]},
            headers={"X-Tenant-ID": DEMO_MERCHANDISER["tenant_id"]}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        user = data["user"]
        permissions = user["permissions"]
        print(f"Merchandiser permissions count: {len(permissions)}")
        print(f"Merchandiser permissions: {permissions}")
        
        # Merchandiser should have 15 permissions
        assert len(permissions) == 15, f"Expected 15 permissions for merchandiser, got {len(permissions)}"
        assert user["role"] == "merchandiser"
        
        # Verify merchandiser does NOT have users.list.view
        assert "users.list.view" not in permissions, "Merchandiser should NOT have users.list.view"
    
    def test_store_manager_login_returns_5_permissions(self):
        """Store Manager should have 5 permissions"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_STORE_MANAGER["email"], "password": DEMO_STORE_MANAGER["password"]},
            headers={"X-Tenant-ID": DEMO_STORE_MANAGER["tenant_id"]}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        user = data["user"]
        permissions = user["permissions"]
        print(f"Store Manager permissions count: {len(permissions)}")
        print(f"Store Manager permissions: {permissions}")
        
        # Store Manager should have 5 permissions
        assert len(permissions) == 5, f"Expected 5 permissions for store_manager, got {len(permissions)}"
        assert user["role"] == "store_manager"
        
        # Verify store_manager has specific permissions
        expected_perms = [
            "dashboard.executive.view",
            "analytics.stockout.view",
            "analytics.planogram.view",
            "data.quality.view",
            "chatbot.faq.view"
        ]
        for perm in expected_perms:
            assert perm in permissions, f"Store Manager missing expected permission: {perm}"
        
        # Verify store_manager does NOT have these permissions
        forbidden_perms = [
            "data.upload.manage",
            "analytics.gap.view",
            "users.list.view"
        ]
        for perm in forbidden_perms:
            assert perm not in permissions, f"Store Manager should NOT have: {perm}"


class TestRBACEndpointAccess:
    """Test that RBAC enforces endpoint access correctly"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_ADMIN["email"], "password": DEMO_ADMIN["password"]},
            headers={"X-Tenant-ID": DEMO_ADMIN["tenant_id"]}
        )
        return response.json()["access_token"]
    
    @pytest.fixture
    def merchandiser_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_MERCHANDISER["email"], "password": DEMO_MERCHANDISER["password"]},
            headers={"X-Tenant-ID": DEMO_MERCHANDISER["tenant_id"]}
        )
        return response.json()["access_token"]
    
    @pytest.fixture
    def store_manager_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_STORE_MANAGER["email"], "password": DEMO_STORE_MANAGER["password"]},
            headers={"X-Tenant-ID": DEMO_STORE_MANAGER["tenant_id"]}
        )
        return response.json()["access_token"]
    
    def test_admin_can_access_users_list(self, admin_token):
        """Admin should be able to access /api/users/list"""
        response = requests.get(
            f"{BASE_URL}/api/users/list",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "X-Tenant-ID": "demo"
            }
        )
        assert response.status_code == 200, f"Admin should access users list: {response.text}"
    
    def test_merchandiser_cannot_access_users_list(self, merchandiser_token):
        """Merchandiser should NOT be able to access /api/users/list"""
        response = requests.get(
            f"{BASE_URL}/api/users/list",
            headers={
                "Authorization": f"Bearer {merchandiser_token}",
                "X-Tenant-ID": "demo"
            }
        )
        assert response.status_code == 403, f"Merchandiser should get 403 on users list, got {response.status_code}"
    
    def test_store_manager_cannot_access_users_list(self, store_manager_token):
        """Store Manager should NOT be able to access /api/users/list"""
        response = requests.get(
            f"{BASE_URL}/api/users/list",
            headers={
                "Authorization": f"Bearer {store_manager_token}",
                "X-Tenant-ID": "demo"
            }
        )
        assert response.status_code == 403, f"Store Manager should get 403 on users list, got {response.status_code}"


class TestRegressionEndpoints:
    """Regression tests for existing analytics endpoints"""
    
    @pytest.fixture
    def admin_headers(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_ADMIN["email"], "password": DEMO_ADMIN["password"]},
            headers={"X-Tenant-ID": DEMO_ADMIN["tenant_id"]}
        )
        token = response.json()["access_token"]
        return {
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": "demo"
        }
    
    def test_executive_dashboard_endpoint(self, admin_headers):
        """Executive Dashboard endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/analytics/overview", headers=admin_headers)
        assert response.status_code == 200, f"Executive Dashboard failed: {response.text}"
    
    def test_upload_status_endpoint(self, admin_headers):
        """Upload status endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/upload/status", headers=admin_headers)
        assert response.status_code == 200, f"Upload status failed: {response.text}"
    
    def test_filter_options_endpoint(self, admin_headers):
        """Filter options endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/analytics/filter-options", headers=admin_headers)
        assert response.status_code == 200, f"Filter options failed: {response.text}"
    
    def test_stock_out_endpoint(self, admin_headers):
        """Stock-out analysis endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out", headers=admin_headers)
        assert response.status_code == 200, f"Stock-out failed: {response.text}"
    
    def test_ros_gap_analysis_endpoint(self, admin_headers):
        """ROS Gap analysis endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/analytics/ros-gap", headers=admin_headers)
        assert response.status_code == 200, f"ROS Gap analysis failed: {response.text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
