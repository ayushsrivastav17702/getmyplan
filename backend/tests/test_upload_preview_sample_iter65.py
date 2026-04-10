"""
Iteration 65: Test Upload Preview and Sample Data Endpoints
Tests for:
- GET /api/upload/v2/preview/{type} - Preview data for master collections
- POST /api/upload/v2/load-sample-data - Sample data loader for onboarding
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Get auth token for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "demo1234"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Auth headers for API calls"""
        return {"Authorization": f"Bearer {auth_token}"}


class TestPreviewEndpoint(TestAuth):
    """Test GET /api/upload/v2/preview/{type} endpoint"""
    
    def test_preview_style_master(self, headers):
        """TEST_01: Preview style_master returns data without _id, tenant_id fields"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/preview/style_master", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "preview" in data, "Response missing 'preview' field"
        assert "total" in data, "Response missing 'total' field"
        assert "type" in data, "Response missing 'type' field"
        assert data["type"] == "style_master", f"Expected type 'style_master', got {data['type']}"
        
        # Verify no _id or tenant_id in preview rows
        if data["preview"]:
            for row in data["preview"]:
                assert "_id" not in row, f"Row contains _id field: {row}"
                assert "tenant_id" not in row, f"Row contains tenant_id field: {row}"
                assert "uploaded_by" not in row, f"Row contains uploaded_by field: {row}"
                assert "uploaded_at" not in row, f"Row contains uploaded_at field: {row}"
        
        print(f"PASS: style_master preview returned {len(data['preview'])} rows, total: {data['total']}")
    
    def test_preview_store_master(self, headers):
        """TEST_02: Preview store_master returns data"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/preview/store_master", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "preview" in data
        assert "total" in data
        assert data["type"] == "store_master"
        
        # Verify no sensitive fields
        if data["preview"]:
            for row in data["preview"]:
                assert "_id" not in row
                assert "tenant_id" not in row
        
        print(f"PASS: store_master preview returned {len(data['preview'])} rows, total: {data['total']}")
    
    def test_preview_planogram(self, headers):
        """TEST_03: Preview planogram returns data"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/preview/planogram", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "preview" in data
        assert "total" in data
        assert data["type"] == "planogram"
        
        # Verify no sensitive fields
        if data["preview"]:
            for row in data["preview"]:
                assert "_id" not in row
                assert "tenant_id" not in row
        
        print(f"PASS: planogram preview returned {len(data['preview'])} rows, total: {data['total']}")
    
    def test_preview_warehouse_master(self, headers):
        """TEST_04: Preview warehouse_master returns data"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/preview/warehouse_master", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "preview" in data
        assert "total" in data
        assert data["type"] == "warehouse_master"
        
        print(f"PASS: warehouse_master preview returned {len(data['preview'])} rows, total: {data['total']}")
    
    def test_preview_sku_master(self, headers):
        """TEST_05: Preview sku_master returns data"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/preview/sku_master", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "preview" in data
        assert "total" in data
        assert data["type"] == "sku_master"
        
        print(f"PASS: sku_master preview returned {len(data['preview'])} rows, total: {data['total']}")
    
    def test_preview_daily_sales(self, headers):
        """TEST_06: Preview daily_sales returns data"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/preview/daily_sales", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "preview" in data
        assert "total" in data
        assert data["type"] == "daily_sales"
        
        # Verify no sensitive fields
        if data["preview"]:
            for row in data["preview"]:
                assert "_id" not in row
                assert "tenant_id" not in row
        
        print(f"PASS: daily_sales preview returned {len(data['preview'])} rows, total: {data['total']}")
    
    def test_preview_invalid_type_returns_400(self, headers):
        """TEST_07: Preview with invalid type returns 400 error"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/preview/invalid_type", headers=headers)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        print("PASS: invalid_type returns 400 as expected")
    
    def test_preview_hyphenated_type(self, headers):
        """TEST_08: Preview with hyphenated type (style-master) works"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/preview/style-master", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["type"] == "style_master", f"Expected type 'style_master', got {data['type']}"
        
        print("PASS: hyphenated type (style-master) works correctly")
    
    def test_preview_returns_max_10_rows(self, headers):
        """TEST_09: Preview returns maximum 10 rows"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/preview/daily_sales", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["preview"]) <= 10, f"Expected max 10 rows, got {len(data['preview'])}"
        
        print(f"PASS: Preview returns max 10 rows (got {len(data['preview'])})")


class TestSampleDataEndpoint(TestAuth):
    """Test POST /api/upload/v2/load-sample-data endpoint"""
    
    def test_sample_data_returns_false_when_data_exists(self, headers):
        """TEST_10: Sample data loader returns success=false when tenant already has data"""
        response = requests.post(f"{BASE_URL}/api/upload/v2/load-sample-data", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Demo tenant has existing data (10k+ sales records), so should return success=false
        assert "success" in data, "Response missing 'success' field"
        assert data["success"] == False, f"Expected success=false for tenant with data, got {data['success']}"
        assert "message" in data, "Response missing 'message' field"
        
        print(f"PASS: Sample data returns success=false with message: {data['message']}")


class TestMasterStatusEndpoint(TestAuth):
    """Test GET /api/upload/v2/master-status endpoint"""
    
    def test_master_status_returns_counts(self, headers):
        """TEST_11: Master status returns counts for all master types"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/master-status", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        expected_types = ["sku_master", "store_master", "warehouse_master", "style_master", "planogram"]
        
        for master_type in expected_types:
            assert master_type in data, f"Missing {master_type} in response"
            assert "count" in data[master_type], f"Missing 'count' for {master_type}"
            assert isinstance(data[master_type]["count"], int), f"Count for {master_type} is not int"
        
        print(f"PASS: Master status returned counts for all types: {data}")


class TestDailyStatusEndpoint(TestAuth):
    """Test GET /api/upload/v2/daily-status endpoint"""
    
    def test_daily_status_returns_all_types(self, headers):
        """TEST_12: Daily status returns status for all 5 upload types"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/daily-status", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        expected_types = ["daily_sales", "store_inventory", "warehouse_inventory", "cogs", "open_orders"]
        
        for upload_type in expected_types:
            assert upload_type in data, f"Missing {upload_type} in response"
            assert "uploaded" in data[upload_type], f"Missing 'uploaded' for {upload_type}"
        
        print(f"PASS: Daily status returned all 5 upload types")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
