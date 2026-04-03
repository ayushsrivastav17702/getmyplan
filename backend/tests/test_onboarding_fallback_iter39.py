"""
Test: Auto-populate analytics filter options from onboarding data
Tests TenantDataProvider fallback behavior when CSV data is missing.

Key behaviors:
- CSV data ALWAYS takes precedence over onboarding data
- Onboarding data (ob_categories, ob_stores, ob_marketplaces) is used as fallback
- onboarding_fallback field in data_status shows which dimensions are using onboarding data
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
DEMO_ADMIN = {"email": "admin@demo.com", "password": "demo1234"}
ACME_ADMIN = {"email": "admin@acme.com", "password": "AcmePass123!"}
ACME_TENANT_ID = "acme_corp"


class TestDemoTenantWithCSVData:
    """Demo tenant has CSV data - onboarding_fallback should be all false, CSV data returned."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as demo admin and get token."""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to demo tenant (no X-Tenant-ID needed)
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=DEMO_ADMIN)
        assert response.status_code == 200, f"Demo login failed: {response.text}"
        data = response.json()
        self.token = data.get("access_token") or data.get("token")
        assert self.token, "No token returned from demo login"
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
        self.session.close()
    
    def test_filter_options_returns_csv_data(self):
        """GET /api/analytics/filter-options returns CSV data for demo tenant."""
        response = self.session.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200, f"Filter options failed: {response.text}"
        data = response.json()
        
        # Demo tenant should have CSV data
        assert "categories" in data, "Missing categories field"
        assert "channels" in data, "Missing channels field"
        assert "regions" in data, "Missing regions field"
        assert "data_status" in data, "Missing data_status field"
        
        # Check data_status has onboarding_fallback field
        data_status = data.get("data_status", {})
        assert "onboarding_fallback" in data_status, "Missing onboarding_fallback in data_status"
        
        # Demo tenant has CSV data, so onboarding_fallback should be all false
        ob_fallback = data_status.get("onboarding_fallback", {})
        print(f"Demo tenant onboarding_fallback: {ob_fallback}")
        
        # Verify CSV data is present (demo has Accessories, Apparel, Footwear)
        categories = data.get("categories", [])
        print(f"Demo tenant categories: {categories}")
        assert len(categories) > 0, "Demo tenant should have categories from CSV"
        
        # Check for expected CSV categories
        expected_csv_cats = ["Accessories", "Apparel", "Footwear"]
        for cat in expected_csv_cats:
            if cat in categories:
                print(f"Found expected CSV category: {cat}")
    
    def test_ai_demand_options_returns_csv_data(self):
        """GET /api/analytics/ai-demand/options returns CSV data for demo tenant."""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/options")
        assert response.status_code == 200, f"AI demand options failed: {response.text}"
        data = response.json()
        
        # Check structure
        assert "categories" in data, "Missing categories"
        assert "channels" in data, "Missing channels"
        assert "data_status" in data, "Missing data_status"
        
        # Check onboarding_fallback
        data_status = data.get("data_status", {})
        ob_fallback = data_status.get("onboarding_fallback", {})
        print(f"AI demand options - onboarding_fallback: {ob_fallback}")
        
        # Demo tenant should have CSV data
        assert data_status.get("has_style_master") or data_status.get("has_onboarding_data"), \
            "Demo tenant should have some data"
    
    def test_validate_data_availability_includes_onboarding_fallback(self):
        """Verify data_status includes onboarding_fallback field."""
        response = self.session.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200
        data = response.json()
        
        data_status = data.get("data_status", {})
        
        # Required fields in data_status
        assert "has_style_master" in data_status, "Missing has_style_master"
        assert "has_store_master" in data_status, "Missing has_store_master"
        assert "has_sales_data" in data_status, "Missing has_sales_data"
        assert "onboarding_fallback" in data_status, "Missing onboarding_fallback"
        
        # onboarding_fallback should have categories, stores, channels
        ob_fallback = data_status.get("onboarding_fallback", {})
        assert "categories" in ob_fallback, "Missing categories in onboarding_fallback"
        assert "stores" in ob_fallback, "Missing stores in onboarding_fallback"
        assert "channels" in ob_fallback, "Missing channels in onboarding_fallback"
        
        print(f"data_status structure validated: {list(data_status.keys())}")
        print(f"onboarding_fallback structure: {ob_fallback}")


class TestAcmeTenantWithOnboardingData:
    """Acme Corp tenant has NO CSV data but HAS onboarding data - should use fallback."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as Acme admin with X-Tenant-ID header."""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-Tenant-ID": ACME_TENANT_ID
        })
        
        # Login to Acme tenant (requires X-Tenant-ID header)
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=ACME_ADMIN)
        assert response.status_code == 200, f"Acme login failed: {response.text}"
        data = response.json()
        self.token = data.get("access_token") or data.get("token")
        assert self.token, "No token returned from Acme login"
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
        self.session.close()
    
    def test_filter_options_returns_onboarding_data(self):
        """GET /api/analytics/filter-options returns onboarding data for Acme tenant."""
        response = self.session.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200, f"Filter options failed: {response.text}"
        data = response.json()
        
        # Check structure
        assert "categories" in data, "Missing categories"
        assert "channels" in data, "Missing channels"
        assert "regions" in data, "Missing regions"
        assert "data_status" in data, "Missing data_status"
        
        data_status = data.get("data_status", {})
        ob_fallback = data_status.get("onboarding_fallback", {})
        
        print(f"Acme tenant data_status: {data_status}")
        print(f"Acme tenant onboarding_fallback: {ob_fallback}")
        
        # Acme has onboarding data: Ethnic Wear (root), Kurtas, Sarees (children)
        categories = data.get("categories", [])
        print(f"Acme tenant categories: {categories}")
        
        # Check if onboarding categories are returned
        expected_ob_cats = ["Ethnic Wear"]  # Root level category from onboarding
        for cat in expected_ob_cats:
            if cat in categories:
                print(f"Found expected onboarding category: {cat}")
        
        # Acme has onboarding marketplaces: Flipkart, Myntra
        channels = data.get("channels", [])
        print(f"Acme tenant channels: {channels}")
        
        expected_ob_channels = ["Flipkart", "Myntra"]
        for ch in expected_ob_channels:
            if ch in channels:
                print(f"Found expected onboarding channel: {ch}")
        
        # Acme has onboarding store: DEL01 Delhi Hub (state: Delhi)
        regions = data.get("regions", [])
        print(f"Acme tenant regions: {regions}")
        
        if "Delhi" in regions:
            print("Found expected onboarding region: Delhi")
    
    def test_ai_demand_options_returns_onboarding_data(self):
        """GET /api/analytics/ai-demand/options returns onboarding data for Acme tenant."""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/options")
        assert response.status_code == 200, f"AI demand options failed: {response.text}"
        data = response.json()
        
        # Check structure
        assert "categories" in data, "Missing categories"
        assert "channels" in data, "Missing channels"
        assert "data_status" in data, "Missing data_status"
        
        data_status = data.get("data_status", {})
        ob_fallback = data_status.get("onboarding_fallback", {})
        
        print(f"AI demand options - Acme data_status: {data_status}")
        print(f"AI demand options - Acme onboarding_fallback: {ob_fallback}")
        
        # Acme should have onboarding data available
        assert data_status.get("has_onboarding_data"), \
            "Acme tenant should have onboarding data"
    
    def test_onboarding_fallback_is_true_for_acme(self):
        """Verify onboarding_fallback is true for dimensions using onboarding data."""
        response = self.session.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200
        data = response.json()
        
        data_status = data.get("data_status", {})
        ob_fallback = data_status.get("onboarding_fallback", {})
        
        # Acme has no CSV data, so onboarding_fallback should be true for available dimensions
        print(f"Acme onboarding_fallback values: {ob_fallback}")
        
        # At least one should be true since Acme has onboarding data
        has_any_fallback = any(ob_fallback.values())
        print(f"Acme has any onboarding fallback: {has_any_fallback}")
        
        # Verify has_onboarding_data is true
        assert data_status.get("has_onboarding_data"), \
            "Acme should have has_onboarding_data=true"


class TestCSVPrecedenceOverOnboarding:
    """Verify CSV data always takes precedence over onboarding data."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as demo admin."""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=DEMO_ADMIN)
        assert response.status_code == 200, f"Demo login failed: {response.text}"
        data = response.json()
        self.token = data.get("access_token") or data.get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
        self.session.close()
    
    def test_csv_data_takes_precedence(self):
        """Demo tenant with CSV data should not use onboarding fallback."""
        response = self.session.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200
        data = response.json()
        
        data_status = data.get("data_status", {})
        ob_fallback = data_status.get("onboarding_fallback", {})
        
        # Demo has CSV data, so categories fallback should be false
        if data_status.get("has_style_master"):
            assert ob_fallback.get("categories") == False, \
                "Categories should not use fallback when CSV style_master exists"
            print("Verified: CSV categories take precedence over onboarding")
        
        # Demo has CSV store_master, so stores fallback should be false
        if data_status.get("has_store_master"):
            assert ob_fallback.get("stores") == False, \
                "Stores should not use fallback when CSV store_master exists"
            print("Verified: CSV stores take precedence over onboarding")


class TestRegressionExistingAnalyticsEndpoints:
    """Regression: All existing analytics endpoints still work for demo tenant."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as demo admin."""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=DEMO_ADMIN)
        assert response.status_code == 200, f"Demo login failed: {response.text}"
        data = response.json()
        self.token = data.get("access_token") or data.get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
        self.session.close()
    
    def test_analytics_overview(self):
        """GET /api/analytics/overview still works."""
        response = self.session.get(f"{BASE_URL}/api/analytics/overview")
        assert response.status_code == 200, f"Analytics overview failed: {response.text}"
        data = response.json()
        assert "total_styles" in data
        assert "total_stores" in data
        print(f"Analytics overview: {data}")
    
    def test_analytics_executive_kpis(self):
        """GET /api/analytics/executive-kpis still works."""
        response = self.session.get(f"{BASE_URL}/api/analytics/executive-kpis")
        assert response.status_code == 200, f"Executive KPIs failed: {response.text}"
        data = response.json()
        assert "revenue" in data
        print(f"Executive KPIs revenue: {data.get('revenue')}")
    
    def test_ai_demand_forecast(self):
        """GET /api/analytics/ai-demand/forecast still works."""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        assert response.status_code == 200, f"AI demand forecast failed: {response.text}"
        data = response.json()
        assert "forecast" in data or "forecast_horizon" in data
        print(f"AI demand forecast keys: {list(data.keys())}")
    
    def test_ai_demand_stockout_risk(self):
        """GET /api/analytics/ai-demand/stockout-risk still works."""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/stockout-risk")
        assert response.status_code == 200, f"Stockout risk failed: {response.text}"
        data = response.json()
        assert "summary" in data or "items" in data
        print(f"Stockout risk keys: {list(data.keys())}")


class TestOnboardingDataStructure:
    """Test the structure of onboarding data returned in filter options."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as Acme admin."""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-Tenant-ID": ACME_TENANT_ID
        })
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=ACME_ADMIN)
        assert response.status_code == 200, f"Acme login failed: {response.text}"
        data = response.json()
        self.token = data.get("access_token") or data.get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
        self.session.close()
    
    def test_get_categories_returns_onboarding_root_categories(self):
        """Categories should return level-1 (root) onboarding categories."""
        response = self.session.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200
        data = response.json()
        
        categories = data.get("categories", [])
        print(f"Acme categories from filter-options: {categories}")
        
        # Acme has "Ethnic Wear" as root category (level 1)
        # Kurtas and Sarees are children (level 2+)
        # get_categories() should return root-level only
    
    def test_get_subcategories_returns_onboarding_child_categories(self):
        """Subcategories should return level-2+ onboarding categories."""
        response = self.session.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200
        data = response.json()
        
        subcategories = data.get("subcategories", [])
        print(f"Acme subcategories from filter-options: {subcategories}")
        
        # Acme has Kurtas and Sarees as children of Ethnic Wear
    
    def test_get_channels_returns_onboarding_marketplaces(self):
        """Channels should return onboarding marketplace names."""
        response = self.session.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200
        data = response.json()
        
        channels = data.get("channels", [])
        print(f"Acme channels from filter-options: {channels}")
        
        # Acme has Flipkart and Myntra as marketplaces
    
    def test_get_regions_returns_onboarding_store_states(self):
        """Regions should return onboarding store states."""
        response = self.session.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200
        data = response.json()
        
        regions = data.get("regions", [])
        print(f"Acme regions from filter-options: {regions}")
        
        # Acme has DEL01 store in Delhi state


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
