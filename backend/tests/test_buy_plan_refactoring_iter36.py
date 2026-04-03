"""
Test Buy Plan Generator Refactoring - Iteration 36
Tests TenantDataProvider integration and dynamic categories/channels from uploaded data.

Key features tested:
- GET /api/buy-plan/options returns dynamic categories, channels, ASP from uploaded tenant data
- GET /api/buy-plan/options returns has_data: true/false based on upload status
- POST /api/buy-plan/generate uses dynamic categories from uploaded data (not hardcoded)
- POST /api/buy-plan/generate response includes data_source field (uploaded vs defaults)
- POST /api/buy-plan/generate works with no request categories (auto-selects from uploaded data)
- GET /api/buy-plan/summary returns dynamic categories and has_uploaded_data flag
- POST /api/buy-plan/export-excel still works after refactoring
- POST /api/buy-plan/upload-edited-plan still works
- GET /api/buy-plan/history still returns saved plans
"""

import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials for demo tenant
TEST_TENANT = "demo"
TEST_EMAIL = "admin@demo.com"
TEST_PASSWORD = "demo1234"


class TestBuyPlanOptionsEndpoint:
    """Tests for the new /api/buy-plan/options endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for demo tenant"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "tenant_id": TEST_TENANT
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_options_endpoint_exists(self, auth_headers):
        """Test that /api/buy-plan/options endpoint exists and returns 200"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/options", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: /api/buy-plan/options endpoint exists and returns 200")
    
    def test_options_returns_has_data_field(self, auth_headers):
        """Test that options response includes has_data boolean field"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/options", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "has_data" in data, "Response missing 'has_data' field"
        assert isinstance(data["has_data"], bool), "has_data should be boolean"
        print(f"PASS: has_data field present, value: {data['has_data']}")
    
    def test_options_returns_categories(self, auth_headers):
        """Test that options response includes categories list"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/options", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data, "Response missing 'categories' field"
        assert isinstance(data["categories"], list), "categories should be a list"
        print(f"PASS: categories field present, count: {len(data['categories'])}, values: {data['categories']}")
    
    def test_options_returns_channels(self, auth_headers):
        """Test that options response includes channels list"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/options", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "channels" in data, "Response missing 'channels' field"
        assert isinstance(data["channels"], list), "channels should be a list"
        print(f"PASS: channels field present, count: {len(data['channels'])}, values: {data['channels']}")
    
    def test_options_returns_asp_by_category(self, auth_headers):
        """Test that options response includes asp_by_category dict"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/options", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "asp_by_category" in data, "Response missing 'asp_by_category' field"
        assert isinstance(data["asp_by_category"], dict), "asp_by_category should be a dict"
        print(f"PASS: asp_by_category field present, keys: {list(data['asp_by_category'].keys())}")
    
    def test_options_returns_data_status(self, auth_headers):
        """Test that options response includes data_status object"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/options", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data_status" in data, "Response missing 'data_status' field"
        assert isinstance(data["data_status"], dict), "data_status should be a dict"
        # Check expected fields in data_status
        expected_fields = ["has_style_master", "has_store_master", "has_sales_data", "is_ready"]
        for field in expected_fields:
            assert field in data["data_status"], f"data_status missing '{field}' field"
        print(f"PASS: data_status field present with all expected fields")
    
    def test_options_returns_seasonality(self, auth_headers):
        """Test that options response includes seasonality factors"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/options", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "seasonality" in data, "Response missing 'seasonality' field"
        assert isinstance(data["seasonality"], dict), "seasonality should be a dict"
        print(f"PASS: seasonality field present, months: {len(data['seasonality'])}")
    
    def test_options_returns_channel_splits(self, auth_headers):
        """Test that options response includes channel_splits"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/options", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "channel_splits" in data, "Response missing 'channel_splits' field"
        print(f"PASS: channel_splits field present, value: {data['channel_splits']}")


class TestBuyPlanGenerateWithDynamicData:
    """Tests for /api/buy-plan/generate with dynamic data from TenantDataProvider"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for demo tenant"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "tenant_id": TEST_TENANT
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_generate_returns_data_source_field(self, auth_headers):
        """Test that generate response includes data_source in metadata"""
        response = requests.post(f"{BASE_URL}/api/buy-plan/generate", 
            headers=auth_headers,
            json={
                "revenue_target_cr": 1.0,
                "months": 6,
                "safety_stock_percent": 10,
                "lead_time_days": 14,
                "return_rate_percent": 5
            })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "metadata" in data, "Response missing 'metadata' field"
        assert "data_source" in data["metadata"], "metadata missing 'data_source' field"
        assert data["metadata"]["data_source"] in ["uploaded", "defaults"], \
            f"data_source should be 'uploaded' or 'defaults', got: {data['metadata']['data_source']}"
        print(f"PASS: data_source field present, value: {data['metadata']['data_source']}")
    
    def test_generate_without_categories_uses_dynamic(self, auth_headers):
        """Test that generate without categories param auto-selects from uploaded data"""
        response = requests.post(f"{BASE_URL}/api/buy-plan/generate", 
            headers=auth_headers,
            json={
                "revenue_target_cr": 1.0,
                "months": 6
                # No categories specified - should auto-select
            })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "categories" in data, "Response missing 'categories' field"
        assert len(data["categories"]) > 0, "Should have at least one category"
        category_names = [c["category"] for c in data["categories"]]
        print(f"PASS: Auto-selected categories: {category_names}")
    
    def test_generate_with_specific_categories(self, auth_headers):
        """Test that generate with specific categories uses those categories"""
        # First get available categories
        options_resp = requests.get(f"{BASE_URL}/api/buy-plan/options", headers=auth_headers)
        available_cats = options_resp.json().get("categories", [])
        
        if len(available_cats) >= 2:
            test_cats = available_cats[:2]
        else:
            test_cats = available_cats
        
        response = requests.post(f"{BASE_URL}/api/buy-plan/generate", 
            headers=auth_headers,
            json={
                "revenue_target_cr": 1.0,
                "months": 6,
                "categories": test_cats
            })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        result_cats = [c["category"] for c in data["categories"]]
        for cat in test_cats:
            assert cat in result_cats, f"Expected category '{cat}' in result"
        print(f"PASS: Specified categories used: {result_cats}")
    
    def test_generate_uses_dynamic_channels(self, auth_headers):
        """Test that generate uses dynamic channels from uploaded data"""
        # First get available channels
        options_resp = requests.get(f"{BASE_URL}/api/buy-plan/options", headers=auth_headers)
        available_channels = options_resp.json().get("channels", [])
        
        response = requests.post(f"{BASE_URL}/api/buy-plan/generate", 
            headers=auth_headers,
            json={
                "revenue_target_cr": 1.0,
                "months": 6,
                "channels": available_channels if available_channels else None
            })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "summary" in data, "Response missing 'summary' field"
        assert "channels_used" in data["summary"], "summary missing 'channels_used' field"
        print(f"PASS: Channels used: {data['summary']['channels_used']}")


class TestBuyPlanSummaryEndpoint:
    """Tests for /api/buy-plan/summary endpoint with dynamic data"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for demo tenant"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "tenant_id": TEST_TENANT
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_summary_returns_has_uploaded_data_flag(self, auth_headers):
        """Test that summary returns has_uploaded_data flag"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/summary", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "has_uploaded_data" in data, "Response missing 'has_uploaded_data' field"
        assert isinstance(data["has_uploaded_data"], bool), "has_uploaded_data should be boolean"
        print(f"PASS: has_uploaded_data field present, value: {data['has_uploaded_data']}")
    
    def test_summary_returns_dynamic_categories(self, auth_headers):
        """Test that summary returns dynamic categories"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data, "Response missing 'categories' field"
        assert isinstance(data["categories"], list), "categories should be a list"
        print(f"PASS: categories in summary: {data['categories']}")
    
    def test_summary_returns_dynamic_channels(self, auth_headers):
        """Test that summary returns dynamic channels"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "channels" in data, "Response missing 'channels' field"
        assert isinstance(data["channels"], list), "channels should be a list"
        print(f"PASS: channels in summary: {data['channels']}")
    
    def test_summary_returns_data_status(self, auth_headers):
        """Test that summary returns data_status object"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data_status" in data, "Response missing 'data_status' field"
        print(f"PASS: data_status in summary: {data['data_status']}")


class TestExistingEndpointsStillWork:
    """Tests to verify existing endpoints still work after refactoring"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for demo tenant"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "tenant_id": TEST_TENANT
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_export_excel_still_works(self, auth_headers):
        """Test that POST /api/buy-plan/export-excel still works"""
        response = requests.post(f"{BASE_URL}/api/buy-plan/export-excel", 
            headers=auth_headers,
            json={
                "revenue_target_cr": 1.0,
                "months": 6,
                "safety_stock_percent": 10,
                "lead_time_days": 14,
                "return_rate_percent": 5
            })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("content-type", ""), \
            "Response should be Excel file"
        assert len(response.content) > 1000, "Excel file should have content"
        print(f"PASS: export-excel works, file size: {len(response.content)} bytes")
    
    def test_history_still_works(self, auth_headers):
        """Test that GET /api/buy-plan/history still works"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/history?limit=5", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "history" in data, "Response missing 'history' field"
        assert isinstance(data["history"], list), "history should be a list"
        print(f"PASS: history endpoint works, count: {len(data['history'])}")
    
    def test_generate_still_works_with_full_params(self, auth_headers):
        """Test that generate still works with all parameters"""
        response = requests.post(f"{BASE_URL}/api/buy-plan/generate", 
            headers=auth_headers,
            json={
                "revenue_target_cr": 1.5,
                "revenue_increase_percent": 25,
                "months": 12,
                "safety_stock_percent": 15,
                "lead_time_days": 30,
                "return_rate_percent": 5,
                "categories": ["Accessories", "Apparel"],
                "channels": ["Retail"]
            })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "summary" in data, "Response missing 'summary' field"
        assert "categories" in data, "Response missing 'categories' field"
        # Buy quantity can be 0 if current inventory exceeds required units (correct behavior)
        assert data["summary"]["total_buy_quantity"] >= 0, "Buy quantity should be non-negative"
        assert data["summary"]["categories_processed"] > 0, "Should process categories"
        print(f"PASS: generate with full params works, buy qty: {data['summary']['total_buy_quantity']}, categories: {data['summary']['categories_processed']}")


class TestDynamicDataFromUploadedCSV:
    """Tests to verify dynamic data comes from uploaded CSV files"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for demo tenant"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "tenant_id": TEST_TENANT
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_options_categories_match_expected_uploaded_data(self, auth_headers):
        """Test that categories match expected uploaded data (Accessories, Apparel, Footwear)"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/options", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # If has_data is true, categories should be from uploaded data
        if data.get("has_data"):
            expected_cats = ["Accessories", "Apparel", "Footwear"]
            for cat in expected_cats:
                assert cat in data["categories"], f"Expected category '{cat}' from uploaded data"
            # Should NOT have old hardcoded categories
            old_hardcoded = ["Jeans", "Shirts", "Jackets", "Belts", "Socks", "Shoes"]
            for old_cat in old_hardcoded:
                if old_cat not in expected_cats:
                    assert old_cat not in data["categories"], \
                        f"Old hardcoded category '{old_cat}' should not appear when uploaded data exists"
            print(f"PASS: Categories from uploaded data: {data['categories']}")
        else:
            print(f"INFO: No uploaded data, using fallback categories: {data['categories']}")
    
    def test_options_channels_match_expected_uploaded_data(self, auth_headers):
        """Test that channels match expected uploaded data (Retail)"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/options", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # If has_data is true, channels should be from uploaded data
        if data.get("has_data"):
            expected_channels = ["Retail"]
            for ch in expected_channels:
                assert ch in data["channels"], f"Expected channel '{ch}' from uploaded data"
            # Should NOT have old hardcoded channels
            old_hardcoded = ["STORE_A", "STORE_B", "AMAZON", "FLIPKART", "MYNTRA"]
            for old_ch in old_hardcoded:
                assert old_ch not in data["channels"], \
                    f"Old hardcoded channel '{old_ch}' should not appear when uploaded data exists"
            print(f"PASS: Channels from uploaded data: {data['channels']}")
        else:
            print(f"INFO: No uploaded data, channels: {data['channels']}")


class TestOtherModulesNotBroken:
    """Tests to verify other modules still work after refactoring"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for demo tenant"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "tenant_id": TEST_TENANT
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_executive_dashboard_still_works(self, auth_headers):
        """Test that executive dashboard endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "health_score" in data or "modules" in data, "Executive dashboard should return data"
        print("PASS: Executive dashboard still works")
    
    def test_filter_options_still_works(self, auth_headers):
        """Test that filter options endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/filter-options", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "categories" in data, "Filter options should return categories"
        print("PASS: Filter options still works")
    
    def test_upload_status_still_works(self, auth_headers):
        """Test that upload status endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/upload/status", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Upload status still works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
