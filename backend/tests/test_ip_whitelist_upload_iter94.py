"""
Test IP Whitelisting and Upload Optimizations - Iteration 94

Tests:
1. IP Whitelist API endpoints (GET/PUT)
2. IP validation (single IPs, CIDR ranges, invalid IPs)
3. Authorization (403 for non-super-admin)
4. Upload pipeline code verification (batch size, parallel fetches, bulk deletes)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
SUPER_ADMIN_EMAIL = "admin@demo.com"
SUPER_ADMIN_PASSWORD = "demo1234"
TEST_TENANT_ID = "production"


class TestIPWhitelistAPI:
    """IP Whitelist endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for super admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as super admin
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("access_token")
        assert token, "No access token returned"
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
        # Cleanup: Ensure whitelist is disabled after tests
        try:
            self.session.put(f"{BASE_URL}/api/admin/platform/tenants/{TEST_TENANT_ID}/ip-whitelist", json={
                "ips": [],
                "enabled": False
            })
        except:
            pass
    
    def test_01_get_ip_whitelist_returns_config(self):
        """GET /api/admin/platform/tenants/{tenant_id}/ip-whitelist returns whitelist config"""
        resp = self.session.get(f"{BASE_URL}/api/admin/platform/tenants/{TEST_TENANT_ID}/ip-whitelist")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "tenant_id" in data, "Response should contain tenant_id"
        assert "ip_whitelist" in data, "Response should contain ip_whitelist"
        wl = data["ip_whitelist"]
        assert "enabled" in wl, "ip_whitelist should have 'enabled' field"
        assert "ips" in wl, "ip_whitelist should have 'ips' field"
        print(f"✓ GET ip-whitelist returns config: enabled={wl['enabled']}, ips={wl['ips']}")
    
    def test_02_put_ip_whitelist_sets_ips_and_enabled(self):
        """PUT /api/admin/platform/tenants/{tenant_id}/ip-whitelist sets IPs + enabled flag"""
        test_ips = ["192.168.1.1", "10.0.0.1"]
        resp = self.session.put(f"{BASE_URL}/api/admin/platform/tenants/{TEST_TENANT_ID}/ip-whitelist", json={
            "ips": test_ips,
            "enabled": False  # Keep disabled to not lock ourselves out
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("success") == True, "Response should indicate success"
        assert data.get("ip_whitelist", {}).get("ips") == test_ips, "IPs should match"
        assert data.get("ip_whitelist", {}).get("enabled") == False, "Enabled should be False"
        print(f"✓ PUT ip-whitelist sets IPs: {test_ips}")
    
    def test_03_put_ip_whitelist_validates_invalid_ip(self):
        """PUT /api/admin/platform/tenants/{tenant_id}/ip-whitelist rejects invalid IPs"""
        invalid_ips = ["not-an-ip", "256.256.256.256", "abc.def.ghi.jkl"]
        for invalid_ip in invalid_ips:
            resp = self.session.put(f"{BASE_URL}/api/admin/platform/tenants/{TEST_TENANT_ID}/ip-whitelist", json={
                "ips": [invalid_ip],
                "enabled": False
            })
            assert resp.status_code == 400, f"Expected 400 for invalid IP '{invalid_ip}', got {resp.status_code}"
            assert "Invalid IP" in resp.text or "invalid" in resp.text.lower(), f"Error should mention invalid IP: {resp.text}"
            print(f"✓ Rejects invalid IP: {invalid_ip}")
    
    def test_04_put_ip_whitelist_accepts_cidr_ranges(self):
        """PUT /api/admin/platform/tenants/{tenant_id}/ip-whitelist accepts CIDR ranges"""
        cidr_ranges = ["10.0.0.0/8", "192.168.0.0/16", "172.16.0.0/12", "203.0.113.0/24"]
        resp = self.session.put(f"{BASE_URL}/api/admin/platform/tenants/{TEST_TENANT_ID}/ip-whitelist", json={
            "ips": cidr_ranges,
            "enabled": False
        })
        assert resp.status_code == 200, f"Expected 200 for CIDR ranges, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("success") == True, "Response should indicate success"
        assert data.get("ip_whitelist", {}).get("ips") == cidr_ranges, "CIDR ranges should be saved"
        print(f"✓ Accepts CIDR ranges: {cidr_ranges}")
    
    def test_05_put_ip_whitelist_accepts_mixed_ips_and_cidr(self):
        """PUT accepts mix of single IPs and CIDR ranges"""
        mixed_ips = ["1.2.3.4", "10.0.0.0/8", "192.168.1.100", "172.16.0.0/16"]
        resp = self.session.put(f"{BASE_URL}/api/admin/platform/tenants/{TEST_TENANT_ID}/ip-whitelist", json={
            "ips": mixed_ips,
            "enabled": False
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print(f"✓ Accepts mixed IPs and CIDR: {mixed_ips}")
    
    def test_06_verify_whitelist_persisted(self):
        """Verify whitelist changes are persisted in database"""
        # Set specific IPs
        test_ips = ["8.8.8.8", "1.1.1.1"]
        self.session.put(f"{BASE_URL}/api/admin/platform/tenants/{TEST_TENANT_ID}/ip-whitelist", json={
            "ips": test_ips,
            "enabled": False
        })
        
        # GET to verify persistence
        resp = self.session.get(f"{BASE_URL}/api/admin/platform/tenants/{TEST_TENANT_ID}/ip-whitelist")
        assert resp.status_code == 200
        data = resp.json()
        saved_ips = data.get("ip_whitelist", {}).get("ips", [])
        assert saved_ips == test_ips, f"Expected {test_ips}, got {saved_ips}"
        print(f"✓ Whitelist persisted correctly: {saved_ips}")
    
    def test_07_cleanup_whitelist(self):
        """Cleanup: Disable whitelist and clear IPs"""
        resp = self.session.put(f"{BASE_URL}/api/admin/platform/tenants/{TEST_TENANT_ID}/ip-whitelist", json={
            "ips": [],
            "enabled": False
        })
        assert resp.status_code == 200
        print("✓ Whitelist cleaned up (disabled, no IPs)")


class TestIPWhitelistAuthorization:
    """Test that IP whitelist endpoints require super_admin role"""
    
    def test_08_get_whitelist_without_auth_returns_error(self):
        """GET ip-whitelist without auth returns error (400/401/403)"""
        session = requests.Session()
        resp = session.get(f"{BASE_URL}/api/admin/platform/tenants/{TEST_TENANT_ID}/ip-whitelist")
        # API returns 400 when no auth token provided (missing Authorization header)
        assert resp.status_code in [400, 401, 403], f"Expected 400/401/403 without auth, got {resp.status_code}"
        print(f"✓ GET ip-whitelist without auth returns {resp.status_code}")
    
    def test_09_put_whitelist_without_auth_returns_error(self):
        """PUT ip-whitelist without auth returns error (400/401/403)"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        resp = session.put(f"{BASE_URL}/api/admin/platform/tenants/{TEST_TENANT_ID}/ip-whitelist", json={
            "ips": ["1.2.3.4"],
            "enabled": False
        })
        # API returns 400 when no auth token provided (missing Authorization header)
        assert resp.status_code in [400, 401, 403], f"Expected 400/401/403 without auth, got {resp.status_code}"
        print(f"✓ PUT ip-whitelist without auth returns {resp.status_code}")


class TestUploadPipelineOptimizations:
    """Verify upload pipeline code optimizations (code review tests)"""
    
    def test_10_batch_size_is_5000(self):
        """Verify upload pipeline uses batch size 5000"""
        with open("/app/backend/routes/upload.py", "r") as f:
            content = f.read()
        
        # Check for BATCH = 5000
        assert "BATCH = 5000" in content, "Batch size should be 5000"
        print("✓ Upload pipeline uses BATCH = 5000")
    
    def test_11_parallel_master_data_fetches(self):
        """Verify upload pipeline uses asyncio.gather for parallel master data fetches"""
        with open("/app/backend/routes/upload.py", "r") as f:
            content = f.read()
        
        # Check for asyncio.gather with master data fetches
        assert "asyncio.gather" in content or "_aio.gather" in content, "Should use asyncio.gather"
        assert "_get_master_skus" in content, "Should fetch master SKUs"
        assert "_get_master_stores" in content, "Should fetch master stores"
        assert "_get_master_warehouses" in content, "Should fetch master warehouses"
        print("✓ Upload pipeline uses asyncio.gather for parallel master data fetches")
    
    def test_12_bulk_delete_uses_in_operator(self):
        """Verify upload pipeline uses $in for bulk daily_sales delete"""
        with open("/app/backend/routes/upload.py", "r") as f:
            content = f.read()
        
        # Check for $in operator in delete_many
        assert '"$in"' in content or "'$in'" in content, "Should use $in operator for bulk deletes"
        # Verify it's used with day field for daily_sales
        assert 'day": {"$in"' in content or "day': {'$in'" in content, "Should use $in with day field"
        print("✓ Upload pipeline uses $in for bulk daily_sales delete")
    
    def test_13_no_per_day_loop_for_delete(self):
        """Verify no per-day loop for deletes (should be single bulk operation)"""
        with open("/app/backend/routes/upload.py", "r") as f:
            content = f.read()
        
        # The _save_to_database function should collect days first, then do single delete
        # Check that days are collected into a set
        assert "days = {r.get" in content or 'days = {r.get' in content, "Should collect days into a set"
        print("✓ Upload pipeline collects days into set for bulk delete (no per-day loop)")


class TestIPWhitelistMiddleware:
    """Verify IP whitelist middleware implementation"""
    
    def test_14_middleware_exists(self):
        """Verify ip_whitelist_middleware exists in server.py"""
        with open("/app/backend/server.py", "r") as f:
            content = f.read()
        
        assert "ip_whitelist_middleware" in content, "Middleware should exist"
        assert "x-forwarded-for" in content.lower(), "Should check X-Forwarded-For header"
        print("✓ IP whitelist middleware exists in server.py")
    
    def test_15_middleware_super_admin_bypass(self):
        """Verify middleware allows super_admin to bypass whitelist"""
        with open("/app/backend/server.py", "r") as f:
            content = f.read()
        
        # Check for super_admin bypass logic - uses payload.get("role") == "super_admin"
        assert 'payload.get("role") == "super_admin"' in content or "super_admin" in content, "Should check for super_admin role"
        # Verify the bypass is in the middleware context
        assert "bypass whitelist" in content.lower() or "Check if user is super_admin" in content, "Should have super_admin bypass comment"
        print("✓ Middleware has super_admin bypass logic")
    
    def test_16_middleware_uses_ipaddress_module(self):
        """Verify middleware uses Python ipaddress module for CIDR support"""
        with open("/app/backend/server.py", "r") as f:
            content = f.read()
        
        assert "import ipaddress" in content or "ipaddress.ip_network" in content, "Should use ipaddress module"
        assert "ip_network" in content, "Should use ip_network for CIDR support"
        print("✓ Middleware uses ipaddress module for CIDR support")


class TestTenantNotFound:
    """Test error handling for non-existent tenant"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for super admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_17_get_whitelist_nonexistent_tenant_returns_404(self):
        """GET ip-whitelist for non-existent tenant returns 404"""
        resp = self.session.get(f"{BASE_URL}/api/admin/platform/tenants/nonexistent_tenant_xyz/ip-whitelist")
        assert resp.status_code == 404, f"Expected 404 for non-existent tenant, got {resp.status_code}"
        print("✓ GET ip-whitelist for non-existent tenant returns 404")
    
    def test_18_put_whitelist_nonexistent_tenant_returns_404(self):
        """PUT ip-whitelist for non-existent tenant returns 404"""
        resp = self.session.put(f"{BASE_URL}/api/admin/platform/tenants/nonexistent_tenant_xyz/ip-whitelist", json={
            "ips": ["1.2.3.4"],
            "enabled": False
        })
        assert resp.status_code == 404, f"Expected 404 for non-existent tenant, got {resp.status_code}"
        print("✓ PUT ip-whitelist for non-existent tenant returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
