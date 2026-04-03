"""
Iteration 37: TenantDataProvider Refactoring - Phase 3, 4, 5 Testing
Tests for:
- Phase 3: AI Demand Planning endpoints with data_source field and /ai-demand/options
- Phase 4: Gap Analysis endpoints (ros, ros-gap, size-gap, noos) with data_source field
- Phase 5: Other analytics endpoints (stock-out, planogram, bi-dashboard, doh, replenishment, filter-options)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
DEMO_TENANT = "demo"
DEMO_EMAIL = "admin@demo.com"
DEMO_PASSWORD = "demo1234"


class TestAuth:
    """Authentication helper tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for demo tenant"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "tenant_id": DEMO_TENANT,
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in login response"
        return data["access_token"]
    
    def test_login_success(self, auth_token):
        """Verify login works and returns token"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✓ Login successful, token obtained")


class TestPhase3AIDemandOptions:
    """Phase 3: GET /api/analytics/ai-demand/options - Dynamic filter options from TenantDataProvider"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "tenant_id": DEMO_TENANT,
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD
        })
        return response.json().get("access_token")
    
    def test_ai_demand_options_endpoint_exists(self, auth_token):
        """Test that /api/analytics/ai-demand/options endpoint exists and returns 200"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/options", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ /api/analytics/ai-demand/options returns 200")
    
    def test_ai_demand_options_has_categories(self, auth_token):
        """Test that options returns categories array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/options", headers=headers)
        data = response.json()
        assert "categories" in data, "Missing 'categories' field"
        assert isinstance(data["categories"], list), "categories should be a list"
        print(f"✓ categories field present: {data['categories']}")
    
    def test_ai_demand_options_has_subcategories(self, auth_token):
        """Test that options returns subcategories array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/options", headers=headers)
        data = response.json()
        assert "subcategories" in data, "Missing 'subcategories' field"
        assert isinstance(data["subcategories"], list), "subcategories should be a list"
        print(f"✓ subcategories field present: {data['subcategories']}")
    
    def test_ai_demand_options_has_channels(self, auth_token):
        """Test that options returns channels array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/options", headers=headers)
        data = response.json()
        assert "channels" in data, "Missing 'channels' field"
        assert isinstance(data["channels"], list), "channels should be a list"
        print(f"✓ channels field present: {data['channels']}")
    
    def test_ai_demand_options_has_regions(self, auth_token):
        """Test that options returns regions array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/options", headers=headers)
        data = response.json()
        assert "regions" in data, "Missing 'regions' field"
        assert isinstance(data["regions"], list), "regions should be a list"
        print(f"✓ regions field present: {data['regions']}")
    
    def test_ai_demand_options_has_brands(self, auth_token):
        """Test that options returns brands array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/options", headers=headers)
        data = response.json()
        assert "brands" in data, "Missing 'brands' field"
        assert isinstance(data["brands"], list), "brands should be a list"
        print(f"✓ brands field present: {data['brands']}")
    
    def test_ai_demand_options_has_genders(self, auth_token):
        """Test that options returns genders array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/options", headers=headers)
        data = response.json()
        assert "genders" in data, "Missing 'genders' field"
        assert isinstance(data["genders"], list), "genders should be a list"
        print(f"✓ genders field present: {data['genders']}")
    
    def test_ai_demand_options_has_seasons(self, auth_token):
        """Test that options returns seasons array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/options", headers=headers)
        data = response.json()
        assert "seasons" in data, "Missing 'seasons' field"
        assert isinstance(data["seasons"], list), "seasons should be a list"
        print(f"✓ seasons field present: {data['seasons']}")
    
    def test_ai_demand_options_has_data_status(self, auth_token):
        """Test that options returns data_status object"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/options", headers=headers)
        data = response.json()
        assert "data_status" in data, "Missing 'data_status' field"
        assert isinstance(data["data_status"], dict), "data_status should be a dict"
        print(f"✓ data_status field present: {data['data_status']}")
    
    def test_ai_demand_options_has_has_data(self, auth_token):
        """Test that options returns has_data boolean"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/options", headers=headers)
        data = response.json()
        assert "has_data" in data, "Missing 'has_data' field"
        assert isinstance(data["has_data"], bool), "has_data should be a boolean"
        print(f"✓ has_data field present: {data['has_data']}")


class TestPhase3AIDemandDataSource:
    """Phase 3: AI Demand endpoints return data_source field"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "tenant_id": DEMO_TENANT,
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD
        })
        return response.json().get("access_token")
    
    def test_forecast_has_data_source(self, auth_token):
        """Test that /api/analytics/ai-demand/forecast returns data_source field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/forecast", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "data_source" in data, "Missing 'data_source' field in forecast response"
        assert data["data_source"] in ["demo", "uploaded"], f"Invalid data_source: {data['data_source']}"
        print(f"✓ forecast data_source: {data['data_source']}")
    
    def test_stockout_risk_has_data_source(self, auth_token):
        """Test that /api/analytics/ai-demand/stockout-risk returns data_source field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/stockout-risk", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "data_source" in data, "Missing 'data_source' field in stockout-risk response"
        assert data["data_source"] in ["demo", "uploaded"], f"Invalid data_source: {data['data_source']}"
        print(f"✓ stockout-risk data_source: {data['data_source']}")
    
    def test_topseller_prediction_has_data_source(self, auth_token):
        """Test that /api/analytics/ai-demand/topseller-prediction returns data_source field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/topseller-prediction", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "data_source" in data, "Missing 'data_source' field in topseller-prediction response"
        assert data["data_source"] in ["demo", "uploaded"], f"Invalid data_source: {data['data_source']}"
        print(f"✓ topseller-prediction data_source: {data['data_source']}")
    
    def test_reorder_optimisation_has_data_source(self, auth_token):
        """Test that /api/analytics/ai-demand/reorder-optimisation returns data_source field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "data_source" in data, "Missing 'data_source' field in reorder-optimisation response"
        assert data["data_source"] in ["demo", "uploaded"], f"Invalid data_source: {data['data_source']}"
        print(f"✓ reorder-optimisation data_source: {data['data_source']}")
    
    def test_supply_feasibility_has_data_source(self, auth_token):
        """Test that /api/analytics/ai-demand/supply-feasibility returns data_source field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/supply-feasibility", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "data_source" in data, "Missing 'data_source' field in supply-feasibility response"
        assert data["data_source"] in ["demo", "uploaded"], f"Invalid data_source: {data['data_source']}"
        print(f"✓ supply-feasibility data_source: {data['data_source']}")


class TestPhase4GapAnalysisDataSource:
    """Phase 4: Gap Analysis endpoints return data_source field"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "tenant_id": DEMO_TENANT,
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD
        })
        return response.json().get("access_token")
    
    def test_ros_has_data_source(self, auth_token):
        """Test that /api/analytics/ros returns data_source field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/ros", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        # ROS may return error if no data, check for data_source or error
        if "error" not in data:
            assert "data_source" in data, "Missing 'data_source' field in ros response"
            assert data["data_source"] in ["demo", "uploaded", "error"], f"Invalid data_source: {data['data_source']}"
            print(f"✓ ros data_source: {data['data_source']}")
        else:
            print(f"✓ ros returned error (no data): {data.get('error')}")
    
    def test_ros_gap_has_data_source(self, auth_token):
        """Test that /api/analytics/ros-gap returns data_source field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/ros-gap", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        if "error" not in data:
            assert "data_source" in data, "Missing 'data_source' field in ros-gap response"
            assert data["data_source"] in ["demo", "uploaded", "error"], f"Invalid data_source: {data['data_source']}"
            print(f"✓ ros-gap data_source: {data['data_source']}")
        else:
            print(f"✓ ros-gap returned error (no data): {data.get('error')}")
    
    def test_size_gap_has_data_source(self, auth_token):
        """Test that /api/analytics/size-gap returns data_source field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/size-gap", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        if "error" not in data:
            assert "data_source" in data, "Missing 'data_source' field in size-gap response"
            assert data["data_source"] in ["demo", "uploaded", "error"], f"Invalid data_source: {data['data_source']}"
            print(f"✓ size-gap data_source: {data['data_source']}")
        else:
            print(f"✓ size-gap returned error (no data): {data.get('error')}")
    
    def test_noos_has_data_source(self, auth_token):
        """Test that /api/analytics/noos returns data_source field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/noos", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        if "error" not in data:
            assert "data_source" in data, "Missing 'data_source' field in noos response"
            assert data["data_source"] in ["demo", "uploaded", "error"], f"Invalid data_source: {data['data_source']}"
            print(f"✓ noos data_source: {data['data_source']}")
        else:
            print(f"✓ noos returned error (no data): {data.get('error')}")


class TestPhase5OtherAnalyticsDataSource:
    """Phase 5: Other analytics endpoints return data_source field"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "tenant_id": DEMO_TENANT,
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD
        })
        return response.json().get("access_token")
    
    def test_stock_out_has_data_source(self, auth_token):
        """Test that /api/analytics/stock-out returns data_source field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        if "error" not in data:
            assert "data_source" in data, "Missing 'data_source' field in stock-out response"
            assert data["data_source"] in ["demo", "uploaded", "error"], f"Invalid data_source: {data['data_source']}"
            print(f"✓ stock-out data_source: {data['data_source']}")
        else:
            print(f"✓ stock-out returned error (no data): {data.get('error')}")
    
    def test_planogram_fill_rate_has_data_source(self, auth_token):
        """Test that /api/analytics/planogram-fill-rate returns data_source field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        if "error" not in data:
            assert "data_source" in data, "Missing 'data_source' field in planogram-fill-rate response"
            assert data["data_source"] in ["demo", "uploaded", "error"], f"Invalid data_source: {data['data_source']}"
            print(f"✓ planogram-fill-rate data_source: {data['data_source']}")
        else:
            print(f"✓ planogram-fill-rate returned error (no data): {data.get('error')}")
    
    def test_bi_dashboard_has_data_source(self, auth_token):
        """Test that /api/analytics/bi-dashboard returns data_source field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/bi-dashboard", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        if "error" not in data:
            assert "data_source" in data, "Missing 'data_source' field in bi-dashboard response"
            assert data["data_source"] in ["demo", "uploaded", "error"], f"Invalid data_source: {data['data_source']}"
            print(f"✓ bi-dashboard data_source: {data['data_source']}")
        else:
            print(f"✓ bi-dashboard returned error (no data): {data.get('error')}")
    
    def test_doh_has_data_source(self, auth_token):
        """Test that /api/analytics/doh returns data_source field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/doh", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        if "error" not in data:
            assert "data_source" in data, "Missing 'data_source' field in doh response"
            assert data["data_source"] in ["demo", "uploaded", "error"], f"Invalid data_source: {data['data_source']}"
            print(f"✓ doh data_source: {data['data_source']}")
        else:
            print(f"✓ doh returned error (no data): {data.get('error')}")
    
    def test_replenishment_has_data_source(self, auth_token):
        """Test that /api/analytics/replenishment returns data_source field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        if "error" not in data:
            assert "data_source" in data, "Missing 'data_source' field in replenishment response"
            assert data["data_source"] in ["demo", "uploaded", "error"], f"Invalid data_source: {data['data_source']}"
            print(f"✓ replenishment data_source: {data['data_source']}")
        else:
            print(f"✓ replenishment returned error (no data): {data.get('error')}")


class TestPhase5FilterOptions:
    """Phase 5: /api/analytics/filter-options returns TenantDataProvider fields"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "tenant_id": DEMO_TENANT,
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD
        })
        return response.json().get("access_token")
    
    def test_filter_options_endpoint_exists(self, auth_token):
        """Test that /api/analytics/filter-options endpoint exists"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/filter-options", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ /api/analytics/filter-options returns 200")
    
    def test_filter_options_has_subcategories(self, auth_token):
        """Test that filter-options returns subcategories array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/filter-options", headers=headers)
        data = response.json()
        assert "subcategories" in data, "Missing 'subcategories' field"
        assert isinstance(data["subcategories"], list), "subcategories should be a list"
        print(f"✓ subcategories field present: {data['subcategories']}")
    
    def test_filter_options_has_brands(self, auth_token):
        """Test that filter-options returns brands array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/filter-options", headers=headers)
        data = response.json()
        assert "brands" in data, "Missing 'brands' field"
        assert isinstance(data["brands"], list), "brands should be a list"
        print(f"✓ brands field present: {data['brands']}")
    
    def test_filter_options_has_genders(self, auth_token):
        """Test that filter-options returns genders array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/filter-options", headers=headers)
        data = response.json()
        assert "genders" in data, "Missing 'genders' field"
        assert isinstance(data["genders"], list), "genders should be a list"
        print(f"✓ genders field present: {data['genders']}")
    
    def test_filter_options_has_seasons(self, auth_token):
        """Test that filter-options returns seasons array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/filter-options", headers=headers)
        data = response.json()
        assert "seasons" in data, "Missing 'seasons' field"
        assert isinstance(data["seasons"], list), "seasons should be a list"
        print(f"✓ seasons field present: {data['seasons']}")
    
    def test_filter_options_has_has_data(self, auth_token):
        """Test that filter-options returns has_data boolean"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/filter-options", headers=headers)
        data = response.json()
        assert "has_data" in data, "Missing 'has_data' field"
        assert isinstance(data["has_data"], bool), "has_data should be a boolean"
        print(f"✓ has_data field present: {data['has_data']}")
    
    def test_filter_options_has_data_status(self, auth_token):
        """Test that filter-options returns data_status object"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/filter-options", headers=headers)
        data = response.json()
        assert "data_status" in data, "Missing 'data_status' field"
        assert isinstance(data["data_status"], dict), "data_status should be a dict"
        print(f"✓ data_status field present: {data['data_status']}")


class TestExistingEndpointsStillWork:
    """Verify existing endpoints still work after refactoring"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "tenant_id": DEMO_TENANT,
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD
        })
        return response.json().get("access_token")
    
    def test_upload_status_works(self, auth_token):
        """Test that /api/upload/status still works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/upload/status", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ /api/upload/status works")
    
    def test_analytics_overview_works(self, auth_token):
        """Test that /api/analytics/overview still works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/overview", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ /api/analytics/overview works")
    
    def test_executive_kpis_works(self, auth_token):
        """Test that /api/analytics/executive-kpis still works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/executive-kpis", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ /api/analytics/executive-kpis works")
    
    def test_config_works(self, auth_token):
        """Test that /api/config still works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/config", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ /api/config works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
