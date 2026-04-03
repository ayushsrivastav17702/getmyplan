"""
Test suite for DASH-35 (PDF Export) and TENANT-20 (Tenant Branding)
Features:
- DASH-35: Export PDF button on Executive Dashboard
- TENANT-20: Branding tab in Tenant Admin Panel (colors, logo URL)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "demo1234"
TENANT_ID = "demo"


class TestTenantBrandingEndpoints:
    """TENANT-20: Test branding GET/PUT endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-Tenant-ID": TENANT_ID
        })
        
        # Login to get token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
        # Cleanup - reset branding to defaults
        self.session.put(f"{BASE_URL}/api/tenants/{TENANT_ID}/branding", json={
            "primary_color": "#0176D3",
            "secondary_color": "#0161B0",
            "logo_url": ""
        })
    
    def test_get_branding_public_endpoint(self):
        """GET /api/tenants/{tenant_id}/branding - public endpoint returns branding data"""
        # Use a fresh session without auth to test public access
        resp = requests.get(f"{BASE_URL}/api/tenants/{TENANT_ID}/branding")
        assert resp.status_code == 200, f"GET branding failed: {resp.text}"
        
        data = resp.json()
        assert "primary_color" in data, "Response missing primary_color"
        assert "secondary_color" in data, "Response missing secondary_color"
        assert "logo_url" in data, "Response missing logo_url"
        assert "company_name" in data, "Response missing company_name"
        print(f"GET branding response: {data}")
    
    def test_get_branding_returns_default_colors(self):
        """GET branding returns default colors when not set"""
        resp = requests.get(f"{BASE_URL}/api/tenants/{TENANT_ID}/branding")
        assert resp.status_code == 200
        
        data = resp.json()
        # Default colors should be returned
        assert data["primary_color"].startswith("#"), "primary_color should be hex"
        assert data["secondary_color"].startswith("#"), "secondary_color should be hex"
    
    def test_put_branding_requires_auth(self):
        """PUT /api/tenants/{tenant_id}/branding requires admin auth"""
        # Try without auth
        resp = requests.put(f"{BASE_URL}/api/tenants/{TENANT_ID}/branding", json={
            "primary_color": "#FF0000"
        })
        assert resp.status_code in [401, 403], f"Expected 401/403 without auth, got {resp.status_code}"
    
    def test_put_branding_updates_primary_color(self):
        """PUT branding updates primary_color"""
        test_color = "#FF5733"
        resp = self.session.put(f"{BASE_URL}/api/tenants/{TENANT_ID}/branding", json={
            "primary_color": test_color
        })
        assert resp.status_code == 200, f"PUT branding failed: {resp.text}"
        
        data = resp.json()
        assert "message" in data, "Response missing message"
        assert "branding" in data, "Response missing branding"
        assert data["branding"]["primary_color"] == test_color
        
        # Verify with GET
        get_resp = requests.get(f"{BASE_URL}/api/tenants/{TENANT_ID}/branding")
        assert get_resp.status_code == 200
        assert get_resp.json()["primary_color"] == test_color
        print(f"Primary color updated to: {test_color}")
    
    def test_put_branding_updates_secondary_color(self):
        """PUT branding updates secondary_color"""
        test_color = "#33FF57"
        resp = self.session.put(f"{BASE_URL}/api/tenants/{TENANT_ID}/branding", json={
            "secondary_color": test_color
        })
        assert resp.status_code == 200, f"PUT branding failed: {resp.text}"
        
        # Verify with GET
        get_resp = requests.get(f"{BASE_URL}/api/tenants/{TENANT_ID}/branding")
        assert get_resp.status_code == 200
        assert get_resp.json()["secondary_color"] == test_color
        print(f"Secondary color updated to: {test_color}")
    
    def test_put_branding_updates_logo_url(self):
        """PUT branding updates logo_url"""
        test_logo = "https://example.com/logo.png"
        resp = self.session.put(f"{BASE_URL}/api/tenants/{TENANT_ID}/branding", json={
            "logo_url": test_logo
        })
        assert resp.status_code == 200, f"PUT branding failed: {resp.text}"
        
        # Verify with GET
        get_resp = requests.get(f"{BASE_URL}/api/tenants/{TENANT_ID}/branding")
        assert get_resp.status_code == 200
        assert get_resp.json()["logo_url"] == test_logo
        print(f"Logo URL updated to: {test_logo}")
    
    def test_put_branding_updates_all_fields(self):
        """PUT branding updates all fields at once"""
        test_data = {
            "primary_color": "#123456",
            "secondary_color": "#654321",
            "logo_url": "https://test.com/brand.png"
        }
        resp = self.session.put(f"{BASE_URL}/api/tenants/{TENANT_ID}/branding", json=test_data)
        assert resp.status_code == 200, f"PUT branding failed: {resp.text}"
        
        # Verify with GET
        get_resp = requests.get(f"{BASE_URL}/api/tenants/{TENANT_ID}/branding")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["primary_color"] == test_data["primary_color"]
        assert data["secondary_color"] == test_data["secondary_color"]
        assert data["logo_url"] == test_data["logo_url"]
        print(f"All branding fields updated successfully")
    
    def test_put_branding_validates_hex_color_format(self):
        """PUT branding validates hex color format"""
        # Invalid color (not 7 chars)
        resp = self.session.put(f"{BASE_URL}/api/tenants/{TENANT_ID}/branding", json={
            "primary_color": "red"
        })
        assert resp.status_code == 400, f"Expected 400 for invalid color, got {resp.status_code}"
        
        # Invalid color (no #)
        resp = self.session.put(f"{BASE_URL}/api/tenants/{TENANT_ID}/branding", json={
            "primary_color": "FF0000"
        })
        assert resp.status_code == 400, f"Expected 400 for color without #, got {resp.status_code}"
        
        # Invalid color (too short)
        resp = self.session.put(f"{BASE_URL}/api/tenants/{TENANT_ID}/branding", json={
            "primary_color": "#FFF"
        })
        assert resp.status_code == 400, f"Expected 400 for short hex, got {resp.status_code}"
        print("Hex color validation working correctly")
    
    def test_put_branding_empty_body_returns_400(self):
        """PUT branding with empty body returns 400"""
        resp = self.session.put(f"{BASE_URL}/api/tenants/{TENANT_ID}/branding", json={})
        assert resp.status_code == 400, f"Expected 400 for empty body, got {resp.status_code}"
    
    def test_get_branding_nonexistent_tenant_returns_404(self):
        """GET branding for non-existent tenant returns 404"""
        resp = requests.get(f"{BASE_URL}/api/tenants/nonexistent_tenant_xyz/branding")
        assert resp.status_code == 404, f"Expected 404 for non-existent tenant, got {resp.status_code}"


class TestTenantMetricsIncludesBranding:
    """TENANT-20: Test that metrics endpoint includes branding data"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-Tenant-ID": TENANT_ID
        })
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_metrics_includes_branding(self):
        """GET /api/tenants/{tenant_id}/metrics includes branding object"""
        resp = self.session.get(f"{BASE_URL}/api/tenants/{TENANT_ID}/metrics")
        assert resp.status_code == 200, f"GET metrics failed: {resp.text}"
        
        data = resp.json()
        assert "branding" in data, "Metrics response missing branding object"
        
        branding = data["branding"]
        assert "primary_color" in branding, "Branding missing primary_color"
        assert "secondary_color" in branding, "Branding missing secondary_color"
        assert "logo_url" in branding, "Branding missing logo_url"
        print(f"Metrics branding: {branding}")


class TestExecutiveDashboardEndpoints:
    """DASH-35: Test Executive Dashboard endpoints (PDF export is frontend-only)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-Tenant-ID": TENANT_ID
        })
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_executive_dashboard_endpoint(self):
        """GET /api/analytics/executive-dashboard returns data"""
        resp = self.session.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        assert resp.status_code == 200, f"Executive dashboard failed: {resp.text}"
        
        data = resp.json()
        # Should have health_score, modules, alerts
        assert "health_score" in data or "error" in data, "Response missing expected fields"
        print(f"Executive dashboard response keys: {list(data.keys())}")
    
    def test_executive_kpis_endpoint(self):
        """GET /api/analytics/executive-kpis returns KPI data"""
        resp = self.session.get(f"{BASE_URL}/api/analytics/executive-kpis")
        assert resp.status_code == 200, f"Executive KPIs failed: {resp.text}"
        
        data = resp.json()
        # Should have revenue, units_sold, etc.
        print(f"Executive KPIs response keys: {list(data.keys())}")
    
    def test_executive_revenue_trend_endpoint(self):
        """GET /api/analytics/executive-revenue-trend returns trend data"""
        resp = self.session.get(f"{BASE_URL}/api/analytics/executive-revenue-trend")
        assert resp.status_code == 200, f"Revenue trend failed: {resp.text}"
        
        data = resp.json()
        # Should have labels, revenue, units arrays
        print(f"Revenue trend response keys: {list(data.keys())}")


class TestNonAdminCannotUpdateBranding:
    """TENANT-20: Test that non-admin roles cannot update branding"""
    
    def test_store_manager_cannot_update_branding(self):
        """Store manager role should get 403 on PUT branding"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "X-Tenant-ID": TENANT_ID
        })
        
        # Login as store_manager
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "store@demo.com",
            "password": "StorePass123!"
        })
        assert login_resp.status_code == 200, f"Store manager login failed: {login_resp.text}"
        token = login_resp.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Try to update branding
        resp = session.put(f"{BASE_URL}/api/tenants/{TENANT_ID}/branding", json={
            "primary_color": "#FF0000"
        })
        assert resp.status_code == 403, f"Expected 403 for store_manager, got {resp.status_code}"
        print("Store manager correctly denied branding update")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
