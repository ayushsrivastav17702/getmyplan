"""
Buy Plan Generator - Backend API Tests (Iteration 35)
Tests for: /api/buy-plan/generate, /api/buy-plan/export-excel, 
           /api/buy-plan/upload-edited-plan, /api/buy-plan/history, /api/buy-plan/summary
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_CREDS = {
    "tenant_id": "demo",
    "email": "admin@demo.com",
    "password": "demo1234"
}


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestBuyPlanSummary:
    """Test GET /api/buy-plan/summary endpoint"""
    
    def test_summary_returns_categories(self, auth_headers):
        """Summary should return list of available categories"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/summary", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "categories" in data, "Response should contain 'categories'"
        assert isinstance(data["categories"], list), "Categories should be a list"
        assert len(data["categories"]) > 0, "Should have at least one category"
        
        # Verify expected categories
        expected_cats = ["Jeans", "Shirts", "Jackets", "Belts", "Socks", "Shoes"]
        for cat in expected_cats:
            assert cat in data["categories"], f"Category '{cat}' should be in list"
    
    def test_summary_returns_channels(self, auth_headers):
        """Summary should return list of available channels"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/summary", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "channels" in data, "Response should contain 'channels'"
        assert isinstance(data["channels"], list), "Channels should be a list"
        
        # Verify expected channels
        expected_channels = ["STORE_A", "STORE_B", "AMAZON", "FLIPKART", "MYNTRA"]
        for ch in expected_channels:
            assert ch in data["channels"], f"Channel '{ch}' should be in list"
    
    def test_summary_returns_defaults(self, auth_headers):
        """Summary should return default ASP and channel splits"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/summary", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "default_asp" in data, "Response should contain 'default_asp'"
        assert "default_channel_splits" in data, "Response should contain 'default_channel_splits'"
        assert "seasonal_index" in data, "Response should contain 'seasonal_index'"
        assert "channel_types" in data, "Response should contain 'channel_types'"
        
        # Verify ASP values are numbers
        for cat, asp in data["default_asp"].items():
            assert isinstance(asp, (int, float)), f"ASP for {cat} should be numeric"
            assert asp > 0, f"ASP for {cat} should be positive"


class TestBuyPlanGenerate:
    """Test POST /api/buy-plan/generate endpoint"""
    
    def test_generate_with_defaults(self, auth_headers):
        """Generate plan with default parameters"""
        payload = {
            "revenue_target_cr": 1.1,
            "revenue_increase_percent": 20,
            "categories": ["Jeans", "Shirts"],
            "channels": ["STORE_A", "AMAZON"],
            "months": 12,
            "safety_stock_percent": 15,
            "lead_time_days": 30,
            "return_rate_percent": 5
        }
        
        response = requests.post(f"{BASE_URL}/api/buy-plan/generate", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "metadata" in data, "Response should contain 'metadata'"
        assert "summary" in data, "Response should contain 'summary'"
        assert "categories" in data, "Response should contain 'categories'"
        assert "generated_at" in data, "Response should contain 'generated_at'"
        assert "version" in data, "Response should contain 'version'"
    
    def test_generate_returns_valid_summary(self, auth_headers):
        """Generated plan should have valid summary with totals"""
        payload = {
            "revenue_target_cr": 1.0,
            "categories": ["Jeans", "Shirts", "Jackets"],
            "channels": ["STORE_A", "STORE_B", "AMAZON"],
            "months": 12
        }
        
        response = requests.post(f"{BASE_URL}/api/buy-plan/generate", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        summary = data["summary"]
        
        assert "total_buy_quantity" in summary, "Summary should have total_buy_quantity"
        assert "total_buy_value" in summary, "Summary should have total_buy_value"
        assert "total_revenue_target" in summary, "Summary should have total_revenue_target"
        assert "categories_processed" in summary, "Summary should have categories_processed"
        assert "channels_used" in summary, "Summary should have channels_used"
        
        # Verify values are reasonable
        assert summary["total_buy_quantity"] >= 0, "Total buy quantity should be non-negative"
        assert summary["total_buy_value"] >= 0, "Total buy value should be non-negative"
        assert summary["categories_processed"] == 3, "Should process 3 categories"
        assert len(summary["channels_used"]) == 3, "Should use 3 channels"
    
    def test_generate_returns_category_breakdown(self, auth_headers):
        """Generated plan should have category-level breakdown"""
        payload = {
            "revenue_target_cr": 0.5,
            "categories": ["Jeans"],
            "channels": ["STORE_A"],
            "months": 6
        }
        
        response = requests.post(f"{BASE_URL}/api/buy-plan/generate", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        categories = data["categories"]
        
        assert len(categories) == 1, "Should have 1 category"
        cat = categories[0]
        
        # Verify category structure
        assert cat["category"] == "Jeans", "Category name should be Jeans"
        assert "asp" in cat, "Category should have ASP"
        assert "contribution_percent" in cat, "Category should have contribution_percent"
        assert "revenue_target" in cat, "Category should have revenue_target"
        assert "required_units" in cat, "Category should have required_units"
        assert "monthly_breakdown" in cat, "Category should have monthly_breakdown"
        assert "channel_breakdown" in cat, "Category should have channel_breakdown"
        assert "total_buy_quantity" in cat, "Category should have total_buy_quantity"
        assert "total_buy_value" in cat, "Category should have total_buy_value"
    
    def test_generate_returns_monthly_breakdown(self, auth_headers):
        """Generated plan should have monthly breakdown with seasonal factors"""
        payload = {
            "revenue_target_cr": 1.0,
            "categories": ["Shirts"],
            "channels": ["AMAZON"],
            "months": 12
        }
        
        response = requests.post(f"{BASE_URL}/api/buy-plan/generate", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        monthly = data["categories"][0]["monthly_breakdown"]
        
        assert len(monthly) == 12, "Should have 12 months"
        
        for m in monthly:
            assert "month" in m, "Monthly entry should have month number"
            assert "month_name" in m, "Monthly entry should have month_name"
            assert "units" in m, "Monthly entry should have units"
            assert "revenue" in m, "Monthly entry should have revenue"
            assert "seasonal_factor" in m, "Monthly entry should have seasonal_factor"
            assert m["units"] >= 0, "Units should be non-negative"
    
    def test_generate_returns_channel_breakdown(self, auth_headers):
        """Generated plan should have channel-level breakdown"""
        payload = {
            "revenue_target_cr": 1.0,
            "categories": ["Belts"],
            "channels": ["STORE_A", "FLIPKART"],
            "months": 12
        }
        
        response = requests.post(f"{BASE_URL}/api/buy-plan/generate", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        channels = data["categories"][0]["channel_breakdown"]
        
        assert len(channels) == 2, "Should have 2 channels"
        
        for ch in channels:
            assert "channel" in ch, "Channel entry should have channel name"
            assert "channel_type" in ch, "Channel entry should have channel_type"
            assert "revenue_target" in ch, "Channel entry should have revenue_target"
            assert "units_needed" in ch, "Channel entry should have units_needed"
            assert "safety_stock" in ch, "Channel entry should have safety_stock"
            assert "current_inventory" in ch, "Channel entry should have current_inventory"
            assert "buy_quantity" in ch, "Channel entry should have buy_quantity"
            assert "buy_value" in ch, "Channel entry should have buy_value"
            assert "asp" in ch, "Channel entry should have asp"
            assert ch["channel_type"] in ["store", "marketplace"], "Channel type should be store or marketplace"
    
    def test_generate_with_all_categories(self, auth_headers):
        """Generate plan with all 6 categories"""
        payload = {
            "revenue_target_cr": 2.0,
            "categories": ["Jeans", "Shirts", "Jackets", "Belts", "Socks", "Shoes"],
            "channels": ["STORE_A", "STORE_B", "AMAZON", "FLIPKART", "MYNTRA"],
            "months": 12
        }
        
        response = requests.post(f"{BASE_URL}/api/buy-plan/generate", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["summary"]["categories_processed"] == 6, "Should process all 6 categories"
        assert len(data["summary"]["channels_used"]) == 5, "Should use all 5 channels"
    
    def test_generate_metadata_includes_user(self, auth_headers):
        """Generated plan metadata should include user info"""
        payload = {
            "revenue_target_cr": 0.5,
            "categories": ["Socks"],
            "channels": ["MYNTRA"]
        }
        
        response = requests.post(f"{BASE_URL}/api/buy-plan/generate", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        metadata = data["metadata"]
        
        assert "generated_at" in metadata, "Metadata should have generated_at"
        assert "revenue_target_cr" in metadata, "Metadata should have revenue_target_cr"
        assert "user" in metadata, "Metadata should have user"


class TestBuyPlanHistory:
    """Test GET /api/buy-plan/history endpoint"""
    
    def test_history_returns_list(self, auth_headers):
        """History endpoint should return list of plans"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/history?limit=5", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "history" in data, "Response should contain 'history'"
        assert "count" in data, "Response should contain 'count'"
        assert isinstance(data["history"], list), "History should be a list"
    
    def test_history_respects_limit(self, auth_headers):
        """History should respect limit parameter"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/history?limit=3", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["history"]) <= 3, "Should return at most 3 items"
    
    def test_history_after_generate(self, auth_headers):
        """History should include newly generated plan"""
        # First generate a plan
        payload = {
            "revenue_target_cr": 0.8,
            "categories": ["Shoes"],
            "channels": ["STORE_B"]
        }
        gen_response = requests.post(f"{BASE_URL}/api/buy-plan/generate", json=payload, headers=auth_headers)
        assert gen_response.status_code == 200
        
        # Then check history
        hist_response = requests.get(f"{BASE_URL}/api/buy-plan/history?limit=1", headers=auth_headers)
        assert hist_response.status_code == 200
        
        data = hist_response.json()
        # Should have at least one entry (the one we just created)
        assert data["count"] >= 1, "History should have at least 1 entry after generate"


class TestBuyPlanExportExcel:
    """Test POST /api/buy-plan/export-excel endpoint"""
    
    def test_export_returns_xlsx(self, auth_headers):
        """Export should return valid Excel file"""
        payload = {
            "revenue_target_cr": 1.0,
            "categories": ["Jeans", "Shirts"],
            "channels": ["STORE_A", "AMAZON"],
            "months": 12
        }
        
        response = requests.post(f"{BASE_URL}/api/buy-plan/export-excel", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Check content type
        content_type = response.headers.get("Content-Type", "")
        assert "spreadsheet" in content_type or "octet-stream" in content_type, \
            f"Content-Type should indicate Excel file, got: {content_type}"
        
        # Check content disposition
        content_disp = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disp, "Should be an attachment"
        assert ".xlsx" in content_disp, "Filename should have .xlsx extension"
    
    def test_export_file_not_empty(self, auth_headers):
        """Exported Excel file should not be empty"""
        payload = {
            "revenue_target_cr": 0.5,
            "categories": ["Belts"],
            "channels": ["FLIPKART"]
        }
        
        response = requests.post(f"{BASE_URL}/api/buy-plan/export-excel", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        # Check file size
        content_length = len(response.content)
        assert content_length > 1000, f"Excel file should be larger than 1KB, got {content_length} bytes"


class TestBuyPlanUpload:
    """Test POST /api/buy-plan/upload-edited-plan endpoint"""
    
    def test_upload_requires_file(self, auth_headers):
        """Upload should require a file"""
        response = requests.post(f"{BASE_URL}/api/buy-plan/upload-edited-plan", headers=auth_headers)
        # Should return 422 (validation error) when no file provided
        assert response.status_code in [400, 422], f"Expected 400/422 without file, got {response.status_code}"
    
    def test_upload_rejects_invalid_file(self, auth_headers):
        """Upload should reject non-Excel files"""
        # Create a fake text file
        files = {"file": ("test.txt", io.BytesIO(b"not an excel file"), "text/plain")}
        
        response = requests.post(f"{BASE_URL}/api/buy-plan/upload-edited-plan", files=files, headers=auth_headers)
        # Should return 400 for invalid file format
        assert response.status_code == 400, f"Expected 400 for invalid file, got {response.status_code}"


class TestBuyPlanRateLimiting:
    """Test rate limiting on generate endpoint"""
    
    def test_rate_limit_not_triggered_normal_use(self, auth_headers):
        """Normal usage should not trigger rate limit"""
        payload = {
            "revenue_target_cr": 0.5,
            "categories": ["Socks"],
            "channels": ["MYNTRA"]
        }
        
        # Make a few requests (well under the 30/minute limit)
        for i in range(3):
            response = requests.post(f"{BASE_URL}/api/buy-plan/generate", json=payload, headers=auth_headers)
            assert response.status_code == 200, f"Request {i+1} should succeed, got {response.status_code}"


class TestBuyPlanRequiresAuth:
    """Test that endpoints require authentication"""
    
    def test_generate_requires_auth(self):
        """Generate endpoint should require authentication"""
        payload = {"revenue_target_cr": 1.0, "categories": ["Jeans"], "channels": ["STORE_A"]}
        response = requests.post(f"{BASE_URL}/api/buy-plan/generate", json=payload)
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
    
    def test_history_requires_auth(self):
        """History endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/buy-plan/history")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
    
    def test_export_requires_auth(self):
        """Export endpoint should require authentication"""
        payload = {"revenue_target_cr": 1.0, "categories": ["Jeans"], "channels": ["STORE_A"]}
        response = requests.post(f"{BASE_URL}/api/buy-plan/export-excel", json=payload)
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
