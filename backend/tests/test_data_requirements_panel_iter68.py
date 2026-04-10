"""
Test Data Requirements Panel - Iteration 68
Tests the /api/upload/v2/data-days endpoint and related functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
INCREFF_USER = {"email": "ayush.srivastav@increff.com", "password": "Ayush@114988"}
DEMO_USER = {"email": "admin@demo.com", "password": "demo1234"}


class TestDataDaysEndpoint:
    """Tests for GET /api/upload/v2/data-days endpoint"""
    
    @pytest.fixture(scope="class")
    def increff_token(self):
        """Get auth token for increff tenant"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=INCREFF_USER
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def demo_token(self):
        """Get auth token for demo tenant"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=DEMO_USER
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    def test_data_days_increff_returns_90(self, increff_token):
        """Test that increff tenant returns 90 days of data"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/data-days",
            headers={"Authorization": f"Bearer {increff_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "days" in data
        assert data["days"] == 90, f"Expected 90 days, got {data['days']}"
    
    def test_data_days_demo_returns_29(self, demo_token):
        """Test that demo tenant returns 29 days of data"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/data-days",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "days" in data
        assert data["days"] == 29, f"Expected 29 days, got {data['days']}"
    
    def test_data_days_tenant_isolation(self, increff_token, demo_token):
        """Test that different tenants get different day counts"""
        # Get increff days
        response1 = requests.get(
            f"{BASE_URL}/api/upload/v2/data-days",
            headers={"Authorization": f"Bearer {increff_token}"}
        )
        increff_days = response1.json()["days"]
        
        # Get demo days
        response2 = requests.get(
            f"{BASE_URL}/api/upload/v2/data-days",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        demo_days = response2.json()["days"]
        
        # They should be different (90 vs 29)
        assert increff_days != demo_days, "Tenant isolation failed - same day count"
        assert increff_days == 90
        assert demo_days == 29


class TestUploadTemplates:
    """Tests for template download endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=INCREFF_USER
        )
        assert response.status_code == 200
        return response.json().get("access_token")
    
    def test_daily_sales_template(self, auth_token):
        """Test daily_sales template download"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/template/daily_sales",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "application/vnd.openxmlformats" in response.headers.get("content-type", "")
    
    def test_sku_master_template(self, auth_token):
        """Test sku_master template download"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/template/sku_master",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "application/vnd.openxmlformats" in response.headers.get("content-type", "")
    
    def test_cogs_template(self, auth_token):
        """Test cogs template download"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/template/cogs",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "application/vnd.openxmlformats" in response.headers.get("content-type", "")


class TestUploadStatus:
    """Tests for upload status endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=INCREFF_USER
        )
        assert response.status_code == 200
        return response.json().get("access_token")
    
    def test_daily_status(self, auth_token):
        """Test daily status endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/daily-status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Should have status for all upload types
        expected_types = ["daily_sales", "store_inventory", "warehouse_inventory", "cogs", "open_orders"]
        for ut in expected_types:
            assert ut in data, f"Missing {ut} in daily status"
    
    def test_master_status(self, auth_token):
        """Test master status endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/master-status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Should have status for all master types
        expected_types = ["sku_master", "store_master", "warehouse_master", "style_master", "planogram"]
        for mt in expected_types:
            assert mt in data, f"Missing {mt} in master status"
    
    def test_history_days(self, auth_token):
        """Test history days endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/history/days?days=7",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "days" in data
        assert isinstance(data["days"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
