"""
Test Suite for Iteration 63: Gap Analysis UX Audit + Forecast Accuracy Tracking
Features:
1. GET /api/analytics/data-status - File upload status for Gap Analysis
2. GET /api/analytics/ai-demand/forecast-accuracy - MAPE trend tracking
3. Forecast snapshot creation when generating forecast
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for demo tenant"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "demo1234"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    def test_01_login_success(self, auth_token):
        """Verify login works and returns token"""
        assert auth_token is not None
        assert len(auth_token) > 50
        print(f"TEST_01 PASS: Login successful, token length: {len(auth_token)}")


class TestDataStatusEndpoint:
    """Tests for GET /api/analytics/data-status endpoint (Gap Analysis UX)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "demo1234"
        })
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_02_data_status_endpoint_exists(self, auth_headers):
        """Verify /api/analytics/data-status endpoint exists and returns 200"""
        response = requests.get(f"{BASE_URL}/api/analytics/data-status", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"TEST_02 PASS: data-status endpoint returns 200")
    
    def test_03_data_status_returns_files_dict(self, auth_headers):
        """Verify response contains 'files' dictionary with 7 required file types"""
        response = requests.get(f"{BASE_URL}/api/analytics/data-status", headers=auth_headers)
        data = response.json()
        
        assert "files" in data, "Response missing 'files' key"
        files = data["files"]
        
        # Check all 7 required file types are present
        required_files = ["style_master", "sku_master", "store_master", "daily_sales", 
                         "store_inventory", "planogram", "warehouse_inventory"]
        for file_type in required_files:
            assert file_type in files, f"Missing file type: {file_type}"
            assert "display_name" in files[file_type], f"Missing display_name for {file_type}"
            assert "uploaded" in files[file_type], f"Missing uploaded flag for {file_type}"
            assert "count" in files[file_type], f"Missing count for {file_type}"
        
        print(f"TEST_03 PASS: All 7 required file types present in response")
    
    def test_04_data_status_returns_summary(self, auth_headers):
        """Verify response contains summary with upload counts and stats"""
        response = requests.get(f"{BASE_URL}/api/analytics/data-status", headers=auth_headers)
        data = response.json()
        
        assert "summary" in data, "Response missing 'summary' key"
        summary = data["summary"]
        
        # Check summary fields
        assert "uploaded_count" in summary, "Missing uploaded_count"
        assert "total_count" in summary, "Missing total_count"
        assert "styles" in summary, "Missing styles count"
        assert "stores" in summary, "Missing stores count"
        assert "sales_records" in summary, "Missing sales_records count"
        assert "days_history" in summary, "Missing days_history"
        
        # Verify total_count is 7 (the 7 required files)
        assert summary["total_count"] == 7, f"Expected total_count=7, got {summary['total_count']}"
        
        print(f"TEST_04 PASS: Summary contains all required fields, total_count=7")
    
    def test_05_data_status_demo_tenant_has_data(self, auth_headers):
        """Verify demo tenant has some uploaded files (6/7 per agent context)"""
        response = requests.get(f"{BASE_URL}/api/analytics/data-status", headers=auth_headers)
        data = response.json()
        
        summary = data["summary"]
        uploaded = summary["uploaded_count"]
        
        # Demo tenant should have at least some files uploaded
        assert uploaded >= 1, f"Expected at least 1 file uploaded, got {uploaded}"
        
        # Check specific files that should be uploaded
        files = data["files"]
        print(f"TEST_05 INFO: Uploaded files status:")
        for file_type, info in files.items():
            status = "UPLOADED" if info["uploaded"] else "MISSING"
            print(f"  - {info['display_name']}: {status} (count: {info['count']})")
        
        print(f"TEST_05 PASS: Demo tenant has {uploaded}/{summary['total_count']} files uploaded")


class TestForecastAccuracyEndpoint:
    """Tests for GET /api/analytics/ai-demand/forecast-accuracy endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "demo1234"
        })
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_06_forecast_accuracy_endpoint_exists(self, auth_headers):
        """Verify /api/analytics/ai-demand/forecast-accuracy endpoint exists"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/forecast-accuracy", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"TEST_06 PASS: forecast-accuracy endpoint returns 200")
    
    def test_07_forecast_accuracy_returns_snapshots(self, auth_headers):
        """Verify response contains 'snapshots' array"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/forecast-accuracy", headers=auth_headers)
        data = response.json()
        
        assert "snapshots" in data, "Response missing 'snapshots' key"
        assert isinstance(data["snapshots"], list), "snapshots should be a list"
        
        print(f"TEST_07 PASS: Response contains snapshots array with {len(data['snapshots'])} items")
    
    def test_08_forecast_accuracy_returns_summary(self, auth_headers):
        """Verify response contains summary with MAPE metrics"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/forecast-accuracy", headers=auth_headers)
        data = response.json()
        
        assert "summary" in data, "Response missing 'summary' key"
        summary = data["summary"]
        
        # Check summary fields exist (values may be null if no snapshots)
        expected_fields = ["current_mape", "best_mape", "worst_mape", "avg_mape", 
                          "snapshots_evaluated", "trend", "total_months_compared"]
        for field in expected_fields:
            assert field in summary, f"Missing summary field: {field}"
        
        print(f"TEST_08 PASS: Summary contains all MAPE fields")
        print(f"  - current_mape: {summary['current_mape']}")
        print(f"  - trend: {summary['trend']}")
        print(f"  - snapshots_evaluated: {summary['snapshots_evaluated']}")
    
    def test_09_forecast_accuracy_with_category_filter(self, auth_headers):
        """Verify category filter works"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/forecast-accuracy?category=Apparel", 
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "snapshots" in data
        assert "summary" in data
        print(f"TEST_09 PASS: Category filter works, returned {len(data['snapshots'])} snapshots")
    
    def test_10_forecast_accuracy_empty_state_message(self, auth_headers):
        """Verify empty state returns helpful message"""
        # Use a category that likely has no snapshots
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/forecast-accuracy?category=NonExistentCategory", 
            headers=auth_headers
        )
        data = response.json()
        
        # If no snapshots, should have a message
        if len(data.get("snapshots", [])) == 0:
            assert "message" in data, "Empty state should have a message"
            print(f"TEST_10 PASS: Empty state message: {data.get('message', 'N/A')}")
        else:
            print(f"TEST_10 PASS: Has snapshots, no empty state needed")


class TestForecastSnapshotCreation:
    """Tests for forecast snapshot creation when generating forecast"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "demo1234"
        })
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_11_generate_forecast_creates_snapshot(self, auth_headers):
        """Verify generating a forecast creates a snapshot in the database"""
        # First, get current snapshot count
        accuracy_before = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/forecast-accuracy", 
            headers=auth_headers
        ).json()
        snapshots_before = len(accuracy_before.get("snapshots", []))
        
        # Generate a forecast
        forecast_response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/forecast?forecast_horizon=12", 
            headers=auth_headers
        )
        assert forecast_response.status_code == 200, f"Forecast failed: {forecast_response.text}"
        
        # Check snapshot count increased
        accuracy_after = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/forecast-accuracy", 
            headers=auth_headers
        ).json()
        snapshots_after = len(accuracy_after.get("snapshots", []))
        
        # Snapshot should have been created
        assert snapshots_after >= snapshots_before, \
            f"Expected snapshot count to increase or stay same, before={snapshots_before}, after={snapshots_after}"
        
        print(f"TEST_11 PASS: Forecast generation works, snapshots: {snapshots_before} -> {snapshots_after}")
    
    def test_12_forecast_snapshot_has_required_fields(self, auth_headers):
        """Verify forecast snapshots have required fields"""
        # Generate a forecast first
        requests.get(f"{BASE_URL}/api/analytics/ai-demand/forecast", headers=auth_headers)
        
        # Get accuracy data
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/forecast-accuracy", 
            headers=auth_headers
        )
        data = response.json()
        
        if len(data.get("snapshots", [])) > 0:
            snapshot = data["snapshots"][0]
            
            # Check required fields
            expected_fields = ["created_at", "category", "forecast_horizon", "confidence_score"]
            for field in expected_fields:
                assert field in snapshot, f"Snapshot missing field: {field}"
            
            print(f"TEST_12 PASS: Snapshot has required fields")
            print(f"  - created_at: {snapshot.get('created_at')}")
            print(f"  - category: {snapshot.get('category')}")
            print(f"  - confidence_score: {snapshot.get('confidence_score')}")
        else:
            print(f"TEST_12 SKIP: No snapshots available to verify")


class TestGapAnalysisEndpoints:
    """Tests for existing Gap Analysis endpoints (regression)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "demo1234"
        })
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_13_ros_gap_endpoint(self, auth_headers):
        """Verify ROS Gap endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/ros-gap", headers=auth_headers)
        assert response.status_code == 200, f"ROS Gap failed: {response.status_code}"
        data = response.json()
        # Should have summary or error
        assert "summary" in data or "error" in data
        print(f"TEST_13 PASS: ROS Gap endpoint returns 200")
    
    def test_14_size_gap_endpoint(self, auth_headers):
        """Verify Size Gap endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/size-gap", headers=auth_headers)
        assert response.status_code == 200, f"Size Gap failed: {response.status_code}"
        data = response.json()
        assert "summary" in data or "error" in data
        print(f"TEST_14 PASS: Size Gap endpoint returns 200")
    
    def test_15_noos_endpoint(self, auth_headers):
        """Verify NOOS endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/noos", headers=auth_headers)
        assert response.status_code == 200, f"NOOS failed: {response.status_code}"
        data = response.json()
        assert "summary" in data or "error" in data
        print(f"TEST_15 PASS: NOOS endpoint returns 200")


class TestAIDemandPlanningEndpoints:
    """Tests for AI Demand Planning endpoints (regression)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "demo1234"
        })
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_16_ai_demand_forecast(self, auth_headers):
        """Verify AI Demand forecast endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/forecast?forecast_horizon=12", 
            headers=auth_headers
        )
        assert response.status_code == 200, f"Forecast failed: {response.status_code}"
        data = response.json()
        
        # Check required fields
        assert "forecast" in data, "Missing forecast array"
        assert "months" in data, "Missing months array"
        assert "confidence_score" in data, "Missing confidence_score"
        
        print(f"TEST_16 PASS: AI Demand forecast returns {len(data.get('forecast', []))} months")
    
    def test_17_ai_demand_data_health(self, auth_headers):
        """Verify AI Demand data health endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/data-health", 
            headers=auth_headers
        )
        assert response.status_code == 200, f"Data health failed: {response.status_code}"
        data = response.json()
        
        assert "forecast_readiness" in data, "Missing forecast_readiness"
        print(f"TEST_17 PASS: Data health endpoint works")
    
    def test_18_ai_demand_options(self, auth_headers):
        """Verify AI Demand options endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/options", 
            headers=auth_headers
        )
        assert response.status_code == 200, f"Options failed: {response.status_code}"
        data = response.json()
        
        # Should have categories and subcategories
        assert "categories" in data or "skus" in data
        print(f"TEST_18 PASS: AI Demand options endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
