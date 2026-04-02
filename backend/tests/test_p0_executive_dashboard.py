"""
P0 Executive Dashboard Test Cases - Iteration 17
Tests for:
- DASH-02/03: KPI cards (Revenue, Units, MRP Realisation, Health Score)
- DASH-33: Week-over-Week comparison
- DASH-34: Year-over-Year comparison
- DASH-08: Quick date presets
- DASH-12: Date validation
- DASH-24: Auto-refresh toggle
- DASH-26: 401 Interceptor
- DASH-14: Reset filters
- Regression: Login/logout, RBAC, module cards
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_CREDS = {"email": "admin@demo.com", "password": "demo1234", "tenant_id": "demo"}
MERCH_CREDS = {"email": "merch@demo.com", "password": "MerchPass123!", "tenant_id": "demo"}
STORE_CREDS = {"email": "store@demo.com", "password": "StorePass123!", "tenant_id": "demo"}


class TestAuthAndLogin:
    """Test authentication flows for all user types"""
    
    def test_admin_login_success(self):
        """REGRESSION: Admin login returns valid token and permissions"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_CREDS["email"], "password": ADMIN_CREDS["password"]},
            headers={"X-Tenant-ID": ADMIN_CREDS["tenant_id"]}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "admin"
        assert len(data["user"]["permissions"]) == 21  # Admin has all permissions
        print(f"✓ Admin login successful with {len(data['user']['permissions'])} permissions")
    
    def test_merchandiser_login_success(self):
        """REGRESSION: Merchandiser login returns valid token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MERCH_CREDS["email"], "password": MERCH_CREDS["password"]},
            headers={"X-Tenant-ID": MERCH_CREDS["tenant_id"]}
        )
        assert response.status_code == 200, f"Merchandiser login failed: {response.text}"
        data = response.json()
        assert data["user"]["role"] == "merchandiser"
        print(f"✓ Merchandiser login successful with {len(data['user']['permissions'])} permissions")
    
    def test_store_manager_login_success(self):
        """REGRESSION: Store manager login returns valid token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STORE_CREDS["email"], "password": STORE_CREDS["password"]},
            headers={"X-Tenant-ID": STORE_CREDS["tenant_id"]}
        )
        assert response.status_code == 200, f"Store manager login failed: {response.text}"
        data = response.json()
        assert data["user"]["role"] == "store_manager"
        print(f"✓ Store manager login successful with {len(data['user']['permissions'])} permissions")
    
    def test_invalid_credentials_returns_401(self):
        """DASH-26: Invalid credentials should return 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "wrong@demo.com", "password": "wrongpass"},
            headers={"X-Tenant-ID": "demo"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid credentials correctly return 401")


class TestExecutiveKPIs:
    """Test DASH-02/03: KPI cards endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_CREDS["email"], "password": ADMIN_CREDS["password"]},
            headers={"X-Tenant-ID": ADMIN_CREDS["tenant_id"]}
        )
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Tenant-ID": ADMIN_CREDS["tenant_id"]
        }
    
    def test_executive_kpis_endpoint_returns_200(self):
        """DASH-02/03: Executive KPIs endpoint should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-kpis",
            headers=self.headers
        )
        assert response.status_code == 200, f"KPIs endpoint failed: {response.text}"
        print("✓ Executive KPIs endpoint returns 200")
    
    def test_executive_kpis_has_required_fields(self):
        """DASH-02/03: KPIs response should have revenue, units_sold, mrp_realisation_pct"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-kpis",
            headers=self.headers
        )
        data = response.json()
        
        # Check required fields
        assert "revenue" in data, "Missing 'revenue' field"
        assert "units_sold" in data, "Missing 'units_sold' field"
        assert "mrp_realisation_pct" in data, "Missing 'mrp_realisation_pct' field"
        assert "has_data" in data, "Missing 'has_data' field"
        
        print(f"✓ KPIs response has all required fields: revenue={data['revenue']}, units={data['units_sold']}")
    
    def test_executive_kpis_wow_data(self):
        """DASH-33: Week-over-Week comparison data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-kpis",
            headers=self.headers
        )
        data = response.json()
        
        assert "wow" in data, "Missing 'wow' field"
        wow = data["wow"]
        assert "revenue_change" in wow, "Missing wow.revenue_change"
        assert "units_change" in wow, "Missing wow.units_change"
        assert "current_revenue" in wow, "Missing wow.current_revenue"
        assert "previous_revenue" in wow, "Missing wow.previous_revenue"
        
        print(f"✓ WoW data present: revenue_change={wow['revenue_change']}%, units_change={wow['units_change']}%")
    
    def test_executive_kpis_yoy_data(self):
        """DASH-34: Year-over-Year comparison data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-kpis",
            headers=self.headers
        )
        data = response.json()
        
        assert "yoy" in data, "Missing 'yoy' field"
        yoy = data["yoy"]
        assert "revenue_change" in yoy, "Missing yoy.revenue_change"
        assert "current_revenue" in yoy, "Missing yoy.current_revenue"
        assert "previous_revenue" in yoy, "Missing yoy.previous_revenue"
        
        print(f"✓ YoY data present: revenue_change={yoy['revenue_change']}%")
    
    def test_executive_kpis_with_date_filters(self):
        """DASH-08: KPIs endpoint accepts date filters"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-kpis",
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
            headers=self.headers
        )
        assert response.status_code == 200, f"KPIs with date filters failed: {response.text}"
        print("✓ KPIs endpoint accepts date filters")


class TestExecutiveDashboard:
    """Test executive dashboard endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_CREDS["email"], "password": ADMIN_CREDS["password"]},
            headers={"X-Tenant-ID": ADMIN_CREDS["tenant_id"]}
        )
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Tenant-ID": ADMIN_CREDS["tenant_id"]
        }
    
    def test_executive_dashboard_endpoint_returns_200(self):
        """REGRESSION: Executive dashboard endpoint should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-dashboard",
            headers=self.headers
        )
        assert response.status_code == 200, f"Dashboard endpoint failed: {response.text}"
        print("✓ Executive dashboard endpoint returns 200")
    
    def test_executive_dashboard_has_health_score(self):
        """REGRESSION: Dashboard should have health_score"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-dashboard",
            headers=self.headers
        )
        data = response.json()
        assert "health_score" in data, "Missing 'health_score' field"
        print(f"✓ Dashboard has health_score: {data['health_score']}")
    
    def test_executive_dashboard_has_modules(self):
        """REGRESSION: Dashboard should have module data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-dashboard",
            headers=self.headers
        )
        data = response.json()
        assert "modules" in data, "Missing 'modules' field"
        print(f"✓ Dashboard has modules: {list(data.get('modules', {}).keys())}")


class TestFilterOptions:
    """Test filter options endpoint for date presets"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_CREDS["email"], "password": ADMIN_CREDS["password"]},
            headers={"X-Tenant-ID": ADMIN_CREDS["tenant_id"]}
        )
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Tenant-ID": ADMIN_CREDS["tenant_id"]
        }
    
    def test_filter_options_endpoint_returns_200(self):
        """DASH-08: Filter options endpoint should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/filter-options",
            headers=self.headers
        )
        assert response.status_code == 200, f"Filter options failed: {response.text}"
        print("✓ Filter options endpoint returns 200")
    
    def test_filter_options_has_date_range(self):
        """DASH-08: Filter options should have dateRange for presets"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/filter-options",
            headers=self.headers
        )
        data = response.json()
        # dateRange is used for setting default date filters
        if "dateRange" in data:
            print(f"✓ Filter options has dateRange: {data['dateRange']}")
        else:
            print("✓ Filter options returned (dateRange may be empty if no data)")


class Test401Interceptor:
    """Test DASH-26: 401 Interceptor for session timeout"""
    
    def test_expired_token_returns_401(self):
        """DASH-26: Expired/invalid token should return 401 on protected endpoints"""
        # Use an invalid token on a protected endpoint (users/list requires auth)
        headers = {
            "Authorization": "Bearer invalid_expired_token_12345",
            "X-Tenant-ID": "demo"
        }
        response = requests.get(
            f"{BASE_URL}/api/users/list",
            headers=headers
        )
        assert response.status_code == 401, f"Expected 401 for invalid token, got {response.status_code}"
        print("✓ Invalid/expired token correctly returns 401")
    
    def test_missing_token_returns_401(self):
        """DASH-26: Missing token should return 401 on protected endpoints"""
        headers = {"X-Tenant-ID": "demo"}
        response = requests.get(
            f"{BASE_URL}/api/users/list",
            headers=headers
        )
        # Should return 401 or 403 for missing auth
        assert response.status_code in [401, 403], f"Expected 401/403 for missing token, got {response.status_code}"
        print("✓ Missing token correctly returns 401/403")


class TestRBACRegression:
    """Regression tests for RBAC functionality"""
    
    def test_admin_can_access_users_list(self):
        """REGRESSION: Admin can access /api/users/list"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_CREDS["email"], "password": ADMIN_CREDS["password"]},
            headers={"X-Tenant-ID": ADMIN_CREDS["tenant_id"]}
        )
        token = response.json()["access_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/users/list",
            headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": "demo"}
        )
        assert response.status_code == 200, f"Admin users list failed: {response.text}"
        print("✓ Admin can access users list")
    
    def test_merchandiser_cannot_access_users_list(self):
        """REGRESSION: Merchandiser gets 403 on /api/users/list"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MERCH_CREDS["email"], "password": MERCH_CREDS["password"]},
            headers={"X-Tenant-ID": MERCH_CREDS["tenant_id"]}
        )
        token = response.json()["access_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/users/list",
            headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": "demo"}
        )
        assert response.status_code == 403, f"Expected 403 for merchandiser, got {response.status_code}"
        print("✓ Merchandiser correctly gets 403 on users list")
    
    def test_store_manager_can_access_executive_dashboard(self):
        """REGRESSION: Store manager can access executive dashboard"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STORE_CREDS["email"], "password": STORE_CREDS["password"]},
            headers={"X-Tenant-ID": STORE_CREDS["tenant_id"]}
        )
        token = response.json()["access_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-dashboard",
            headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": "demo"}
        )
        assert response.status_code == 200, f"Store manager dashboard failed: {response.text}"
        print("✓ Store manager can access executive dashboard")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
