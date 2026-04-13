"""
Iteration 84: Resilience Fixes Testing
- I-03: Upload Status localStorage cache fallback
- I-04: COGS upload count includes uploaded=true regardless of valid flag
- I-05: AI Onboarding banner shows only when no plan exists
- Health endpoints: /api/health, /api/health/memory, /api/health/ready, /api/health/live
- Regression: Stock-Out Analysis still works
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

@pytest.fixture(scope="module")
def session():
    """Create authenticated session for demo tenant"""
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    # Login as demo admin
    login_resp = s.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@demo.com",
        "password": "demo1234"
    })
    if login_resp.status_code == 200:
        data = login_resp.json()
        # Try access_token first (actual field name), then token
        token = data.get("access_token") or data.get("token")
        if token:
            s.headers.update({"Authorization": f"Bearer {token}"})
    return s


class TestHealthEndpoints:
    """Test health check endpoints for monitoring"""
    
    def test_health_main_endpoint(self, session):
        """GET /api/health returns healthy status"""
        resp = session.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data.get("status") == "healthy", f"Expected healthy, got {data}"
    
    def test_health_memory_endpoint(self, session):
        """GET /api/health/memory returns memory info"""
        resp = session.get(f"{BASE_URL}/api/health/memory")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data.get("status") == "healthy", f"Expected healthy status"
        assert "memory" in data, "Expected memory field in response"
        mem = data["memory"]
        assert "total_gb" in mem, "Expected total_gb in memory"
        assert "available_gb" in mem, "Expected available_gb in memory"
        assert "used_percent" in mem, "Expected used_percent in memory"
    
    def test_health_ready_endpoint(self, session):
        """GET /api/health/ready returns mongodb connected"""
        resp = session.get(f"{BASE_URL}/api/health/ready")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data.get("status") == "ready", f"Expected ready, got {data.get('status')}"
        assert data.get("mongodb") == "connected", f"Expected mongodb connected"
    
    def test_health_live_endpoint(self, session):
        """GET /api/health/live returns alive"""
        resp = session.get(f"{BASE_URL}/api/health/live")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data.get("status") == "alive", f"Expected alive, got {data.get('status')}"
        assert "timestamp" in data, "Expected timestamp in response"


class TestUploadStatusAPI:
    """Test upload status API for I-03 and I-04 fixes"""
    
    def test_upload_status_returns_200(self, session):
        """GET /api/upload/status returns 200"""
        resp = session.get(f"{BASE_URL}/api/upload/status")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    
    def test_upload_status_has_all_file_types(self, session):
        """Upload status should have all 7 file types"""
        resp = session.get(f"{BASE_URL}/api/upload/status")
        assert resp.status_code == 200
        data = resp.json()
        # Actual file types in the system (based on API response)
        expected_types = ["style_master", "sku_ean_master", "store_master", "warehouse_master",
                         "daily_sales", "store_inventory", "warehouse_inventory"]
        for ft in expected_types:
            assert ft in data, f"Missing file type: {ft}"
    
    def test_upload_status_files_have_uploaded_field(self, session):
        """All file types should have uploaded field (I-04 fix)"""
        resp = session.get(f"{BASE_URL}/api/upload/status")
        assert resp.status_code == 200
        data = resp.json()
        # All files should have 'uploaded' field
        for ft, info in data.items():
            if isinstance(info, dict):
                assert "uploaded" in info, f"{ft} missing 'uploaded' field: {info}"
    
    def test_upload_count_for_demo_tenant(self, session):
        """Demo tenant should have 7/7 uploaded files"""
        resp = session.get(f"{BASE_URL}/api/upload/status")
        assert resp.status_code == 200
        data = resp.json()
        # Count files where uploaded=true
        uploaded_count = sum(1 for v in data.values() if isinstance(v, dict) and v.get("uploaded"))
        assert uploaded_count == 7, f"Expected 7 uploaded files, got {uploaded_count}. Data: {data}"


class TestAIDemandPlanningAPI:
    """Test AI Demand Planning API for I-05 fix"""
    
    def test_ai_demand_options_returns_200(self, session):
        """GET /api/analytics/ai-demand/options returns 200"""
        resp = session.get(f"{BASE_URL}/api/analytics/ai-demand/options")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    
    def test_ai_demand_data_health_returns_200(self, session):
        """GET /api/analytics/ai-demand/data-health returns 200"""
        resp = session.get(f"{BASE_URL}/api/analytics/ai-demand/data-health")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        # Should have forecast_readiness
        assert "forecast_readiness" in data, f"Missing forecast_readiness: {data}"
    
    def test_ai_demand_plans_returns_200(self, session):
        """GET /api/analytics/ai-demand/plans returns 200"""
        resp = session.get(f"{BASE_URL}/api/analytics/ai-demand/plans")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    
    def test_demo_tenant_has_existing_plan(self, session):
        """Demo tenant should have an existing AI plan (so banner should NOT show)"""
        resp = session.get(f"{BASE_URL}/api/analytics/ai-demand/plans")
        assert resp.status_code == 200
        data = resp.json()
        plans = data.get("plans", [])
        # Demo tenant should have at least one plan
        assert len(plans) > 0, f"Demo tenant should have existing plan, got: {data}"


class TestStockOutRegression:
    """Regression test for Stock-Out Analysis (from iteration 83)"""
    
    def test_stock_out_api_returns_200(self, session):
        """GET /api/analytics/stock-out returns 200"""
        resp = session.get(f"{BASE_URL}/api/analytics/stock-out")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    
    def test_stock_out_has_summary(self, session):
        """Stock-out response should have summary with non-zero values"""
        resp = session.get(f"{BASE_URL}/api/analytics/stock-out")
        assert resp.status_code == 200
        data = resp.json()
        summary = data.get("summary", {})
        assert "total_stockouts" in summary, f"Missing total_stockouts"
        assert "total_lost_sales" in summary, f"Missing total_lost_sales"
        # P0 bug fix verification - lost sales should not be 0
        assert summary.get("total_lost_sales", 0) > 0, f"total_lost_sales should be > 0, got {summary}"
    
    def test_stock_out_has_top_skus(self, session):
        """Stock-out response should have top_skus array"""
        resp = session.get(f"{BASE_URL}/api/analytics/stock-out")
        assert resp.status_code == 200
        data = resp.json()
        assert "top_skus" in data, f"Missing top_skus"
        assert isinstance(data["top_skus"], list), f"top_skus should be list"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
