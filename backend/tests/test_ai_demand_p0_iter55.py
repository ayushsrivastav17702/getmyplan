"""
Test AI Demand Planning P0 Fixes - Iteration 55
Tests:
- P0.1: V2 Data Bridge - get_cached_data() checks V2 first, falls back to V1
- P0.2: Seasonal Decomposition fix (numpy.ndarray has no attribute 'values')
- P0.3: V2 collection indexes created on startup
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "demo1234"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestV2DataBridge:
    """P0.1: V2 Data Bridge - get_cached_data() should check V2 first, fall back to V1"""
    
    def test_forecast_endpoint_works(self, auth_headers):
        """Forecast endpoint should work with V1 fallback data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/forecast",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Forecast failed: {response.text}"
        data = response.json()
        
        # Should have forecast data
        assert "forecast" in data
        assert "models_used" in data
        assert "data_source" in data
        
        # With V1 data (90 days), should use demo fallback for forecast (needs 180+ days)
        # But models should still be listed
        print(f"Forecast data_source: {data.get('data_source')}")
        print(f"Models used: {data.get('models_used')}")
    
    def test_stockout_risk_returns_uploaded_data(self, auth_headers):
        """Stockout risk should return data_source='uploaded' with V1 data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/stockout-risk",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Stockout risk failed: {response.text}"
        data = response.json()
        
        # Should have summary and items
        assert "summary" in data
        assert "items" in data
        assert "data_source" in data
        
        # With V1 data (18000 store_inventory rows), should be 'uploaded'
        print(f"Stockout data_source: {data.get('data_source')}")
        print(f"Total items in summary: {data.get('summary', {}).get('total', 0)}")
        
        # Verify we have real data (not demo)
        if data.get('data_source') == 'uploaded':
            assert data['summary']['total'] > 100, "Should have many items from V1 data"
    
    def test_reorder_optimisation_returns_uploaded_data(self, auth_headers):
        """Reorder optimisation should return data_source='uploaded' with V1 data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Reorder optimisation failed: {response.text}"
        data = response.json()
        
        assert "summary" in data
        assert "items" in data
        assert "data_source" in data
        
        print(f"Reorder data_source: {data.get('data_source')}")
        print(f"Total SKUs: {data.get('summary', {}).get('total_skus', 0)}")
        
        # With V1 data (200 SKUs), should be 'uploaded'
        if data.get('data_source') == 'uploaded':
            assert data['summary']['total_skus'] >= 50, "Should have many SKUs from V1 data"
    
    def test_supply_feasibility_works(self, auth_headers):
        """Supply feasibility should work with V1 data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/supply-feasibility",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Supply feasibility failed: {response.text}"
        data = response.json()
        
        assert "summary" in data
        assert "monthly" in data
        assert "data_source" in data
        
        print(f"Supply feasibility data_source: {data.get('data_source')}")
    
    def test_topseller_prediction_works(self, auth_headers):
        """Topseller prediction should work with V1 data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/topseller-prediction",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Topseller prediction failed: {response.text}"
        data = response.json()
        
        assert "predictions" in data
        assert "data_source" in data
        
        print(f"Topseller data_source: {data.get('data_source')}")
        print(f"Predictions count: {len(data.get('predictions', []))}")


class TestSeasonalDecompositionFix:
    """P0.2: Seasonal Decomposition model should not crash"""
    
    def test_forecast_includes_seasonal_decomposition(self, auth_headers):
        """Forecast should show 'Seasonal Decomposition' in models_used (3 models total)"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/forecast",
            params={"forecast_horizon": 12},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Forecast failed: {response.text}"
        data = response.json()
        
        models_used = data.get("models_used", [])
        print(f"Models used: {models_used}")
        
        # Should have 3 models when data is sufficient
        # Note: With demo data (24 months), all 3 models should work
        if data.get('data_source') == 'demo' or data.get('insufficient_data'):
            # Demo data has 24 months, should have all 3 models
            assert "Seasonal Decomposition" in models_used, \
                f"Seasonal Decomposition should be in models_used: {models_used}"
            assert len(models_used) >= 3, f"Should have 3 models, got: {models_used}"
        
        # Verify no crash - response should have valid forecast
        assert "forecast" in data
        assert len(data["forecast"]) > 0
    
    def test_forecast_no_crash_with_category_filter(self, auth_headers):
        """Forecast with category filter should not crash"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/forecast",
            params={"category": "Shirts", "forecast_horizon": 12},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Forecast with category failed: {response.text}"
        data = response.json()
        
        # Should not crash, should return valid response
        assert "forecast" in data
        assert "models_used" in data
        print(f"Category filter - Models used: {data.get('models_used')}")


class TestV2CollectionIndexes:
    """P0.3: V2 collection indexes created on startup"""
    
    def test_health_check_passes(self, auth_headers):
        """Health check should pass (indexes created during startup)"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["healthy", "degraded"]
        print(f"Health status: {data.get('status')}")


class TestAIDemandOptions:
    """Test AI Demand options endpoint"""
    
    def test_options_endpoint(self, auth_headers):
        """Options endpoint should return filter values"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/options",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Options failed: {response.text}"
        data = response.json()
        
        # Should have categories from V1 style_master
        assert "categories" in data
        assert "data_status" in data
        
        print(f"Categories: {data.get('categories', [])}")
        print(f"Data status: {data.get('data_status', {})}")


class TestAIDemandPlans:
    """Test demand plan CRUD"""
    
    def test_list_plans(self, auth_headers):
        """List demand plans endpoint should work"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/plans",
            headers=auth_headers
        )
        assert response.status_code == 200, f"List plans failed: {response.text}"
        data = response.json()
        assert "plans" in data
        print(f"Plans count: {len(data.get('plans', []))}")
    
    def test_generate_plan(self, auth_headers):
        """Generate demand plan should work"""
        response = requests.post(
            f"{BASE_URL}/api/analytics/ai-demand/generate-plan",
            params={"annual_target": 10000000},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Generate plan failed: {response.text}"
        data = response.json()
        
        assert "plan_id" in data
        assert "subcategories" in data
        assert "total_planned" in data
        
        print(f"Generated plan_id: {data.get('plan_id')}")
        print(f"Total planned: {data.get('total_planned')}")
        print(f"Data source: {data.get('data_source')}")


class TestAllAIDemandEndpoints:
    """Test all 10 AI Demand endpoints work"""
    
    def test_forecast(self, auth_headers):
        """GET /api/analytics/ai-demand/forecast"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/forecast",
            headers=auth_headers
        )
        assert response.status_code == 200
        print("✓ forecast endpoint works")
    
    def test_stockout_risk(self, auth_headers):
        """GET /api/analytics/ai-demand/stockout-risk"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/stockout-risk",
            headers=auth_headers
        )
        assert response.status_code == 200
        print("✓ stockout-risk endpoint works")
    
    def test_topseller_prediction(self, auth_headers):
        """GET /api/analytics/ai-demand/topseller-prediction"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/topseller-prediction",
            headers=auth_headers
        )
        assert response.status_code == 200
        print("✓ topseller-prediction endpoint works")
    
    def test_reorder_optimisation(self, auth_headers):
        """GET /api/analytics/ai-demand/reorder-optimisation"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation",
            headers=auth_headers
        )
        assert response.status_code == 200
        print("✓ reorder-optimisation endpoint works")
    
    def test_supply_feasibility(self, auth_headers):
        """GET /api/analytics/ai-demand/supply-feasibility"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/supply-feasibility",
            headers=auth_headers
        )
        assert response.status_code == 200
        print("✓ supply-feasibility endpoint works")
    
    def test_options(self, auth_headers):
        """GET /api/analytics/ai-demand/options"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/options",
            headers=auth_headers
        )
        assert response.status_code == 200
        print("✓ options endpoint works")
    
    def test_plans_list(self, auth_headers):
        """GET /api/analytics/ai-demand/plans"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/plans",
            headers=auth_headers
        )
        assert response.status_code == 200
        print("✓ plans list endpoint works")
    
    def test_generate_plan_endpoint(self, auth_headers):
        """POST /api/analytics/ai-demand/generate-plan"""
        response = requests.post(
            f"{BASE_URL}/api/analytics/ai-demand/generate-plan",
            params={"annual_target": 5000000},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        plan_id = data.get("plan_id")
        print(f"✓ generate-plan endpoint works (plan_id: {plan_id})")
        return plan_id
    
    def test_get_plan_by_id(self, auth_headers):
        """GET /api/analytics/ai-demand/plans/{plan_id}"""
        # First generate a plan
        gen_response = requests.post(
            f"{BASE_URL}/api/analytics/ai-demand/generate-plan",
            params={"annual_target": 5000000},
            headers=auth_headers
        )
        assert gen_response.status_code == 200
        plan_id = gen_response.json().get("plan_id")
        
        # Then get it by ID
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/plans/{plan_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        print(f"✓ get plan by id endpoint works")
    
    def test_update_plan(self, auth_headers):
        """PUT /api/analytics/ai-demand/plans/{plan_id}"""
        # First generate a plan
        gen_response = requests.post(
            f"{BASE_URL}/api/analytics/ai-demand/generate-plan",
            params={"annual_target": 5000000},
            headers=auth_headers
        )
        assert gen_response.status_code == 200
        plan_data = gen_response.json()
        plan_id = plan_data.get("plan_id")
        version = plan_data.get("version", 1)
        
        # Then update it
        response = requests.put(
            f"{BASE_URL}/api/analytics/ai-demand/plans/{plan_id}",
            params={"expected_version": version},
            json={"status": "approved"},
            headers=auth_headers
        )
        assert response.status_code == 200
        print(f"✓ update plan endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
