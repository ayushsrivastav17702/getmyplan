"""
Iteration 69: Onboarding Wizard API Tests
Tests for GET /api/onboarding/status, POST /api/onboarding/skip, /complete, /reset
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
INCREFF_USER = {"email": "ayush.srivastav@increff.com", "password": "Ayush@114988"}
DEMO_USER = {"email": "admin@demo.com", "password": "demo1234"}


class TestOnboardingStatusStructure:
    """Test GET /api/onboarding/status response structure"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for increff tenant"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as increff user
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=INCREFF_USER)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    def test_01_status_endpoint_returns_200(self):
        """GET /api/onboarding/status returns 200"""
        response = self.session.get(f"{BASE_URL}/api/onboarding/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: GET /api/onboarding/status returns 200")
    
    def test_02_status_has_is_onboarded_field(self):
        """Response has is_onboarded boolean field"""
        response = self.session.get(f"{BASE_URL}/api/onboarding/status")
        data = response.json()
        assert "is_onboarded" in data, "Missing is_onboarded field"
        assert isinstance(data["is_onboarded"], bool), "is_onboarded should be boolean"
        print(f"PASS: is_onboarded = {data['is_onboarded']}")
    
    def test_03_status_has_current_step_field(self):
        """Response has current_step integer field (1-4)"""
        response = self.session.get(f"{BASE_URL}/api/onboarding/status")
        data = response.json()
        assert "current_step" in data, "Missing current_step field"
        assert isinstance(data["current_step"], int), "current_step should be integer"
        assert 1 <= data["current_step"] <= 4, f"current_step should be 1-4, got {data['current_step']}"
        print(f"PASS: current_step = {data['current_step']}")
    
    def test_04_status_has_progress_percentage_field(self):
        """Response has progress_percentage integer field (0-100)"""
        response = self.session.get(f"{BASE_URL}/api/onboarding/status")
        data = response.json()
        assert "progress_percentage" in data, "Missing progress_percentage field"
        assert isinstance(data["progress_percentage"], int), "progress_percentage should be integer"
        assert 0 <= data["progress_percentage"] <= 100, f"progress_percentage should be 0-100, got {data['progress_percentage']}"
        print(f"PASS: progress_percentage = {data['progress_percentage']}")
    
    def test_05_status_has_sample_data_loaded_field(self):
        """Response has sample_data_loaded boolean field"""
        response = self.session.get(f"{BASE_URL}/api/onboarding/status")
        data = response.json()
        assert "sample_data_loaded" in data, "Missing sample_data_loaded field"
        assert isinstance(data["sample_data_loaded"], bool), "sample_data_loaded should be boolean"
        print(f"PASS: sample_data_loaded = {data['sample_data_loaded']}")
    
    def test_06_status_has_master_data_object(self):
        """Response has master_data object with required fields"""
        response = self.session.get(f"{BASE_URL}/api/onboarding/status")
        data = response.json()
        assert "master_data" in data, "Missing master_data field"
        md = data["master_data"]
        
        # Check required sub-fields
        required_fields = ["sku_master", "store_master", "style_master", "warehouse_master", 
                          "total_uploaded", "complete", "all_complete"]
        for field in required_fields:
            assert field in md, f"Missing master_data.{field}"
        
        # Check each master type has uploaded and count
        for master_type in ["sku_master", "store_master", "style_master", "warehouse_master"]:
            assert "uploaded" in md[master_type], f"Missing master_data.{master_type}.uploaded"
            assert "count" in md[master_type], f"Missing master_data.{master_type}.count"
        
        print(f"PASS: master_data structure valid, total_uploaded = {md['total_uploaded']}")
    
    def test_07_status_has_transactional_data_object(self):
        """Response has transactional_data object with required fields"""
        response = self.session.get(f"{BASE_URL}/api/onboarding/status")
        data = response.json()
        assert "transactional_data" in data, "Missing transactional_data field"
        td = data["transactional_data"]
        
        # Check required sub-fields
        required_fields = ["daily_sales", "store_inventory", "cogs", "open_orders", 
                          "total_uploaded", "complete"]
        for field in required_fields:
            assert field in td, f"Missing transactional_data.{field}"
        
        # Check each transactional type has uploaded and count
        for trans_type in ["daily_sales", "store_inventory", "cogs", "open_orders"]:
            assert "uploaded" in td[trans_type], f"Missing transactional_data.{trans_type}.uploaded"
            assert "count" in td[trans_type], f"Missing transactional_data.{trans_type}.count"
        
        # daily_sales should also have days field
        assert "days" in td["daily_sales"], "Missing transactional_data.daily_sales.days"
        
        print(f"PASS: transactional_data structure valid, total_uploaded = {td['total_uploaded']}")


class TestOnboardingStatusIncreffTenant:
    """Test onboarding status for increff tenant (fully onboarded)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for increff tenant"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=INCREFF_USER)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    def test_08_increff_is_onboarded_true(self):
        """Increff tenant should have is_onboarded=true"""
        response = self.session.get(f"{BASE_URL}/api/onboarding/status")
        data = response.json()
        assert data["is_onboarded"] == True, f"Expected is_onboarded=true, got {data['is_onboarded']}"
        print("PASS: increff tenant is_onboarded = true")
    
    def test_09_increff_current_step_4(self):
        """Increff tenant should be at step 4"""
        response = self.session.get(f"{BASE_URL}/api/onboarding/status")
        data = response.json()
        assert data["current_step"] == 4, f"Expected current_step=4, got {data['current_step']}"
        print("PASS: increff tenant current_step = 4")
    
    def test_10_increff_progress_100(self):
        """Increff tenant should have 100% progress"""
        response = self.session.get(f"{BASE_URL}/api/onboarding/status")
        data = response.json()
        assert data["progress_percentage"] == 100, f"Expected progress_percentage=100, got {data['progress_percentage']}"
        print("PASS: increff tenant progress_percentage = 100")


class TestOnboardingStatusDemoTenant:
    """Test onboarding status for demo tenant (fully onboarded)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for demo tenant"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=DEMO_USER)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    def test_11_demo_is_onboarded_true(self):
        """Demo tenant should have is_onboarded=true"""
        response = self.session.get(f"{BASE_URL}/api/onboarding/status")
        data = response.json()
        assert data["is_onboarded"] == True, f"Expected is_onboarded=true, got {data['is_onboarded']}"
        print("PASS: demo tenant is_onboarded = true")
    
    def test_12_demo_has_all_data_types(self):
        """Demo tenant should have all data types uploaded"""
        response = self.session.get(f"{BASE_URL}/api/onboarding/status")
        data = response.json()
        
        md = data["master_data"]
        td = data["transactional_data"]
        
        # Check master data
        assert md["sku_master"]["uploaded"] == True, "Demo should have sku_master"
        assert md["store_master"]["uploaded"] == True, "Demo should have store_master"
        
        # Check transactional data
        assert td["daily_sales"]["uploaded"] == True, "Demo should have daily_sales"
        
        print(f"PASS: demo tenant has required data - master: {md['total_uploaded']}/4, trans: {td['total_uploaded']}/4")


class TestOnboardingSkipEndpoint:
    """Test POST /api/onboarding/skip"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=INCREFF_USER)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    def test_13_skip_returns_200(self):
        """POST /api/onboarding/skip returns 200"""
        response = self.session.post(f"{BASE_URL}/api/onboarding/skip")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: POST /api/onboarding/skip returns 200")
    
    def test_14_skip_returns_success(self):
        """POST /api/onboarding/skip returns success message"""
        response = self.session.post(f"{BASE_URL}/api/onboarding/skip")
        data = response.json()
        assert data.get("success") == True, f"Expected success=true, got {data}"
        print(f"PASS: skip response = {data}")


class TestOnboardingCompleteEndpoint:
    """Test POST /api/onboarding/complete"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=INCREFF_USER)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    def test_15_complete_returns_200(self):
        """POST /api/onboarding/complete returns 200"""
        response = self.session.post(f"{BASE_URL}/api/onboarding/complete")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: POST /api/onboarding/complete returns 200")
    
    def test_16_complete_returns_success(self):
        """POST /api/onboarding/complete returns success message"""
        response = self.session.post(f"{BASE_URL}/api/onboarding/complete")
        data = response.json()
        assert data.get("success") == True, f"Expected success=true, got {data}"
        print(f"PASS: complete response = {data}")


class TestOnboardingResetEndpoint:
    """Test POST /api/onboarding/reset"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=INCREFF_USER)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    def test_17_reset_returns_200(self):
        """POST /api/onboarding/reset returns 200"""
        response = self.session.post(f"{BASE_URL}/api/onboarding/reset")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: POST /api/onboarding/reset returns 200")
    
    def test_18_reset_returns_success(self):
        """POST /api/onboarding/reset returns success message"""
        response = self.session.post(f"{BASE_URL}/api/onboarding/reset")
        data = response.json()
        assert data.get("success") == True, f"Expected success=true, got {data}"
        print(f"PASS: reset response = {data}")


class TestOnboardingWithoutAuth:
    """Test onboarding endpoints without authentication"""
    
    def test_19_status_without_auth(self):
        """GET /api/onboarding/status should work without auth (returns demo tenant)"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.get(f"{BASE_URL}/api/onboarding/status")
        # Should return 200 with demo tenant data
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "is_onboarded" in data, "Should return onboarding status"
        print(f"PASS: Unauthenticated status returns tenant_id={data.get('tenant_id', 'demo')}")
