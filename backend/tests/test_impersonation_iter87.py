"""
Iteration 87: Impersonation Flow Backend Tests
Tests the POST /api/admin/platform/impersonate/{tenant_id} endpoint
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


class TestImpersonationEndpoint:
    """Tests for POST /api/admin/platform/impersonate/{tenant_id}"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_super_admin_token(self):
        """Login as super admin and return token"""
        resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert resp.status_code == 200, f"Super admin login failed: {resp.text}"
        return resp.json().get("access_token")
    
    def get_regular_user_token(self):
        """Login as regular user and return token"""
        resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": REGULAR_USER_EMAIL,
            "password": REGULAR_USER_PASSWORD
        })
        assert resp.status_code == 200, f"Regular user login failed: {resp.text}"
        return resp.json().get("access_token")
    
    # ── Test 1: Impersonate endpoint returns correct structure ──
    def test_01_impersonate_returns_access_token(self):
        """POST /api/admin/platform/impersonate/{tenant_id} returns access_token"""
        token = self.get_super_admin_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        resp = self.session.post(f"{BASE_URL}/api/admin/platform/impersonate/increff")
        assert resp.status_code == 200, f"Impersonate failed: {resp.text}"
        
        data = resp.json()
        assert "access_token" in data, "Response missing access_token"
        assert isinstance(data["access_token"], str), "access_token should be string"
        assert len(data["access_token"]) > 0, "access_token should not be empty"
        print(f"TEST_01 PASS: access_token returned (length: {len(data['access_token'])})")
    
    def test_02_impersonate_returns_user_object(self):
        """POST /api/admin/platform/impersonate/{tenant_id} returns user object"""
        token = self.get_super_admin_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        resp = self.session.post(f"{BASE_URL}/api/admin/platform/impersonate/increff")
        assert resp.status_code == 200, f"Impersonate failed: {resp.text}"
        
        data = resp.json()
        assert "user" in data, "Response missing user object"
        user = data["user"]
        assert "email" in user, "User object missing email"
        assert "role" in user, "User object missing role"
        assert "tenant_id" in user, "User object missing tenant_id"
        assert user["tenant_id"] == "increff", f"User tenant_id should be 'increff', got {user['tenant_id']}"
        print(f"TEST_02 PASS: user object returned with email={user['email']}, role={user['role']}")
    
    def test_03_impersonate_returns_impersonated_by(self):
        """POST /api/admin/platform/impersonate/{tenant_id} returns impersonated_by"""
        token = self.get_super_admin_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        resp = self.session.post(f"{BASE_URL}/api/admin/platform/impersonate/increff")
        assert resp.status_code == 200, f"Impersonate failed: {resp.text}"
        
        data = resp.json()
        assert "impersonated_by" in data, "Response missing impersonated_by"
        assert data["impersonated_by"] == SUPER_ADMIN_EMAIL, f"impersonated_by should be {SUPER_ADMIN_EMAIL}"
        print(f"TEST_03 PASS: impersonated_by={data['impersonated_by']}")
    
    def test_04_impersonate_returns_company_name(self):
        """POST /api/admin/platform/impersonate/{tenant_id} returns company_name"""
        token = self.get_super_admin_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        resp = self.session.post(f"{BASE_URL}/api/admin/platform/impersonate/increff")
        assert resp.status_code == 200, f"Impersonate failed: {resp.text}"
        
        data = resp.json()
        assert "company_name" in data, "Response missing company_name"
        assert isinstance(data["company_name"], str), "company_name should be string"
        print(f"TEST_04 PASS: company_name={data['company_name']}")
    
    def test_05_impersonate_returns_tenant_id(self):
        """POST /api/admin/platform/impersonate/{tenant_id} returns tenant_id"""
        token = self.get_super_admin_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        resp = self.session.post(f"{BASE_URL}/api/admin/platform/impersonate/increff")
        assert resp.status_code == 200, f"Impersonate failed: {resp.text}"
        
        data = resp.json()
        assert "tenant_id" in data, "Response missing tenant_id"
        assert data["tenant_id"] == "increff", f"tenant_id should be 'increff', got {data['tenant_id']}"
        print(f"TEST_05 PASS: tenant_id={data['tenant_id']}")
    
    # ── Test 6: Regular user cannot impersonate (403) ──
    def test_06_regular_user_cannot_impersonate(self):
        """Regular (non-super-admin) user cannot access impersonate endpoint (403)"""
        token = self.get_regular_user_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        resp = self.session.post(f"{BASE_URL}/api/admin/platform/impersonate/demo")
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print(f"TEST_06 PASS: Regular user gets 403 Forbidden")
    
    # ── Test 7: Impersonate non-existent tenant returns 404 ──
    def test_07_impersonate_nonexistent_tenant_404(self):
        """POST /api/admin/platform/impersonate/{tenant_id} returns 404 for non-existent tenant"""
        token = self.get_super_admin_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        resp = self.session.post(f"{BASE_URL}/api/admin/platform/impersonate/nonexistent_tenant_xyz")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        print(f"TEST_07 PASS: Non-existent tenant returns 404")
    
    # ── Test 8: Impersonate without auth returns 401 ──
    def test_08_impersonate_without_auth_401(self):
        """POST /api/admin/platform/impersonate/{tenant_id} returns 401 without auth"""
        # Clear any auth headers
        self.session.headers.pop("Authorization", None)
        
        resp = self.session.post(f"{BASE_URL}/api/admin/platform/impersonate/increff")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
        print(f"TEST_08 PASS: No auth returns 401")
    
    # ── Test 9: Impersonation token contains required fields ──
    def test_09_impersonation_token_contains_required_fields(self):
        """Impersonation token contains email, tenant_id, role, impersonated_by fields"""
        import jwt
        
        token = self.get_super_admin_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        resp = self.session.post(f"{BASE_URL}/api/admin/platform/impersonate/increff")
        assert resp.status_code == 200, f"Impersonate failed: {resp.text}"
        
        data = resp.json()
        impersonation_token = data["access_token"]
        
        # Decode JWT without verification to check claims
        try:
            decoded = jwt.decode(impersonation_token, options={"verify_signature": False})
            assert "email" in decoded, "Token missing email claim"
            assert "tenant_id" in decoded, "Token missing tenant_id claim"
            assert "role" in decoded, "Token missing role claim"
            assert "impersonated_by" in decoded, "Token missing impersonated_by claim"
            assert decoded["impersonated_by"] == SUPER_ADMIN_EMAIL, f"impersonated_by should be {SUPER_ADMIN_EMAIL}"
            print(f"TEST_09 PASS: Token contains email={decoded['email']}, tenant_id={decoded['tenant_id']}, role={decoded['role']}, impersonated_by={decoded['impersonated_by']}")
        except Exception as e:
            pytest.fail(f"Failed to decode JWT: {e}")
    
    # ── Test 10: User object contains permissions ──
    def test_10_user_object_contains_permissions(self):
        """User object in impersonate response contains permissions array"""
        token = self.get_super_admin_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        resp = self.session.post(f"{BASE_URL}/api/admin/platform/impersonate/increff")
        assert resp.status_code == 200, f"Impersonate failed: {resp.text}"
        
        data = resp.json()
        user = data["user"]
        assert "permissions" in user, "User object missing permissions"
        assert isinstance(user["permissions"], list), "permissions should be a list"
        print(f"TEST_10 PASS: User has {len(user['permissions'])} permissions")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
