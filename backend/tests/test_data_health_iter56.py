"""
Iteration 56: Data Health Dashboard Backend Tests
Tests the new /api/analytics/ai-demand/data-health endpoint and regression tests for existing AI Demand endpoints.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://zip-improved.preview.emergentagent.com').rstrip('/')

class TestDataHealthEndpoint:
    """Tests for the new data-health endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "demo1234",
            "tenant": "demo"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_data_health_endpoint_returns_200(self, auth_headers):
        """TEST_01: data-health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/data-health", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("TEST_01 PASS: data-health endpoint returns 200")
    
    def test_data_health_has_required_fields(self, auth_headers):
        """TEST_02: data-health response has all required top-level fields"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/data-health", headers=auth_headers)
        data = response.json()
        
        required_fields = ["daily_sales", "store_inventory", "warehouse_inventory", 
                          "sku_master", "store_master", "lead_times", 
                          "data_source", "forecast_readiness"]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        print(f"TEST_02 PASS: All required fields present: {required_fields}")
    
    def test_daily_sales_structure(self, auth_headers):
        """TEST_03: daily_sales has correct structure and values"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/data-health", headers=auth_headers)
        data = response.json()
        ds = data["daily_sales"]
        
        # Check structure
        assert "days_available" in ds, "Missing days_available"
        assert "status" in ds, "Missing status"
        assert "progress_pct" in ds, "Missing progress_pct"
        
        # Check expected values (90 days, partial, 50%)
        assert ds["days_available"] == 90, f"Expected 90 days, got {ds['days_available']}"
        assert ds["status"] == "partial", f"Expected 'partial', got {ds['status']}"
        assert ds["progress_pct"] == 50.0, f"Expected 50.0%, got {ds['progress_pct']}"
        
        print(f"TEST_03 PASS: daily_sales - days={ds['days_available']}, status={ds['status']}, progress={ds['progress_pct']}%")
    
    def test_store_inventory_structure(self, auth_headers):
        """TEST_04: store_inventory has correct structure"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/data-health", headers=auth_headers)
        data = response.json()
        si = data["store_inventory"]
        
        assert si["days_available"] == 90, f"Expected 90 days, got {si['days_available']}"
        assert si["status"] == "partial", f"Expected 'partial', got {si['status']}"
        
        print(f"TEST_04 PASS: store_inventory - days={si['days_available']}, status={si['status']}")
    
    def test_warehouse_inventory_structure(self, auth_headers):
        """TEST_05: warehouse_inventory has correct structure"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/data-health", headers=auth_headers)
        data = response.json()
        wi = data["warehouse_inventory"]
        
        assert wi["days_available"] == 1, f"Expected 1 day, got {wi['days_available']}"
        assert wi["status"] == "partial", f"Expected 'partial', got {wi['status']}"
        
        print(f"TEST_05 PASS: warehouse_inventory - days={wi['days_available']}, status={wi['status']}")
    
    def test_sku_master_structure(self, auth_headers):
        """TEST_06: sku_master has correct structure"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/data-health", headers=auth_headers)
        data = response.json()
        sm = data["sku_master"]
        
        assert sm["count"] == 200, f"Expected 200 SKUs, got {sm['count']}"
        assert sm["status"] == "complete", f"Expected 'complete', got {sm['status']}"
        
        print(f"TEST_06 PASS: sku_master - count={sm['count']}, status={sm['status']}")
    
    def test_store_master_structure(self, auth_headers):
        """TEST_07: store_master has correct structure"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/data-health", headers=auth_headers)
        data = response.json()
        stm = data["store_master"]
        
        assert stm["count"] == 10, f"Expected 10 stores, got {stm['count']}"
        assert stm["status"] == "complete", f"Expected 'complete', got {stm['status']}"
        
        print(f"TEST_07 PASS: store_master - count={stm['count']}, status={stm['status']}")
    
    def test_lead_times_structure(self, auth_headers):
        """TEST_08: lead_times shows 'missing' status (no lead_time_days in SKU master)"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/data-health", headers=auth_headers)
        data = response.json()
        lt = data["lead_times"]
        
        assert lt["status"] == "missing", f"Expected 'missing', got {lt['status']}"
        assert lt["total_skus"] == 200, f"Expected 200 total SKUs, got {lt['total_skus']}"
        assert lt["with_lead_time"] == 0, f"Expected 0 with lead time, got {lt['with_lead_time']}"
        
        print(f"TEST_08 PASS: lead_times - status={lt['status']}, total_skus={lt['total_skus']}, with_lead_time={lt['with_lead_time']}")
    
    def test_forecast_readiness_structure(self, auth_headers):
        """TEST_09: forecast_readiness has correct structure and values"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/data-health", headers=auth_headers)
        data = response.json()
        fr = data["forecast_readiness"]
        
        assert fr["days_available"] == 90, f"Expected 90 days, got {fr['days_available']}"
        assert fr["days_required"] == 180, f"Expected 180 days required, got {fr['days_required']}"
        assert fr["using_demo_data"] == True, f"Expected using_demo_data=True, got {fr['using_demo_data']}"
        assert fr["estimated_ready_date"] is not None, "Expected estimated_ready_date to be set"
        assert fr["progress_pct"] == 50.0, f"Expected 50.0%, got {fr['progress_pct']}"
        
        print(f"TEST_09 PASS: forecast_readiness - days={fr['days_available']}/{fr['days_required']}, using_demo={fr['using_demo_data']}, est_date={fr['estimated_ready_date']}")
    
    def test_data_source_field(self, auth_headers):
        """TEST_10: data_source field is present and valid"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/data-health", headers=auth_headers)
        data = response.json()
        
        assert data["data_source"] in ["V1", "V2"], f"Expected V1 or V2, got {data['data_source']}"
        print(f"TEST_10 PASS: data_source={data['data_source']}")


class TestAIDemandRegressionEndpoints:
    """Regression tests for existing AI Demand endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "demo1234",
            "tenant": "demo"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_forecast_endpoint(self, auth_headers):
        """TEST_11: /api/analytics/ai-demand/forecast works"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/forecast", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "forecast" in data, "Missing forecast field"
        assert "models_used" in data, "Missing models_used field"
        print(f"TEST_11 PASS: forecast endpoint - models_used={data.get('models_used')}")
    
    def test_stockout_risk_endpoint(self, auth_headers):
        """TEST_12: /api/analytics/ai-demand/stockout-risk works"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/stockout-risk", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "summary" in data, "Missing summary field"
        assert "items" in data, "Missing items field"
        print(f"TEST_12 PASS: stockout-risk endpoint - data_source={data.get('data_source')}")
    
    def test_reorder_optimisation_endpoint(self, auth_headers):
        """TEST_13: /api/analytics/ai-demand/reorder-optimisation works"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "summary" in data, "Missing summary field"
        assert "items" in data, "Missing items field"
        print(f"TEST_13 PASS: reorder-optimisation endpoint - data_source={data.get('data_source')}")
    
    def test_supply_feasibility_endpoint(self, auth_headers):
        """TEST_14: /api/analytics/ai-demand/supply-feasibility works"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/supply-feasibility", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "summary" in data, "Missing summary field"
        assert "monthly" in data, "Missing monthly field"
        print(f"TEST_14 PASS: supply-feasibility endpoint - data_source={data.get('data_source')}")
    
    def test_topseller_prediction_endpoint(self, auth_headers):
        """TEST_15: /api/analytics/ai-demand/topseller-prediction works"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/topseller-prediction", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "predictions" in data, "Missing predictions field"
        print(f"TEST_15 PASS: topseller-prediction endpoint - data_source={data.get('data_source')}")
    
    def test_options_endpoint(self, auth_headers):
        """TEST_16: /api/analytics/ai-demand/options works"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/options", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "categories" in data, "Missing categories field"
        print(f"TEST_16 PASS: options endpoint - categories={data.get('categories')}")
    
    def test_plans_list_endpoint(self, auth_headers):
        """TEST_17: /api/analytics/ai-demand/plans works"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/plans", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "plans" in data, "Missing plans field"
        print(f"TEST_17 PASS: plans list endpoint - count={len(data.get('plans', []))}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
