"""
Multi-Tenant Architecture Tests - Iteration 14
Tests tenant management, authentication, and data isolation.
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
DEMO_TENANT_ID = "demo"
DEMO_EMAIL = "admin@demo.com"
DEMO_PASSWORD = "demo1234"

ACME_TENANT_ID = "acme_corp"
ACME_EMAIL = "admin@acme.com"
ACME_PASSWORD = "AcmePass123!"


class TestTenantManagement:
    """Tests for /api/tenants/* endpoints"""
    
    def test_list_tenants(self):
        """GET /api/tenants/ - lists all active tenants"""
        resp = requests.get(f"{BASE_URL}/api/tenants/")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert "tenants" in data, "Response should have 'tenants' key"
        assert isinstance(data["tenants"], list), "tenants should be a list"
        
        # Verify demo tenant exists
        tenant_ids = [t["tenant_id"] for t in data["tenants"]]
        assert "demo" in tenant_ids, "Demo tenant should exist"
        
        # Verify tenant structure
        demo = next(t for t in data["tenants"] if t["tenant_id"] == "demo")
        assert "company_name" in demo
        assert "subdomain" in demo
        assert "plan_type" in demo
        assert "status" in demo
        assert demo["status"] == "active"
    
    def test_check_subdomain_available(self):
        """GET /api/tenants/check-subdomain - checks subdomain availability"""
        unique_subdomain = f"test{uuid.uuid4().hex[:8]}"
        resp = requests.get(f"{BASE_URL}/api/tenants/check-subdomain?subdomain={unique_subdomain}")
        assert resp.status_code == 200
        
        data = resp.json()
        assert "subdomain" in data
        assert "available" in data
        assert data["subdomain"] == unique_subdomain
        assert data["available"] is True
    
    def test_check_subdomain_taken(self):
        """GET /api/tenants/check-subdomain - returns false for taken subdomain"""
        resp = requests.get(f"{BASE_URL}/api/tenants/check-subdomain?subdomain=demo")
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["available"] is False
    
    def test_tenant_status_demo(self):
        """GET /api/tenants/{tenant_id}/status - returns demo tenant metrics"""
        resp = requests.get(
            f"{BASE_URL}/api/tenants/demo/status",
            headers={"X-Tenant-ID": "demo"}
        )
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["tenant_id"] == "demo"
        assert "company_name" in data
        assert "subdomain" in data
        assert "plan_type" in data
        assert "status" in data
        assert "metrics" in data
        
        # Demo tenant should have 7 uploaded files
        assert data["metrics"]["uploaded_files"] == 7, f"Demo should have 7 files, got {data['metrics']['uploaded_files']}"
    
    def test_tenant_status_acme(self):
        """GET /api/tenants/{tenant_id}/status - returns acme tenant metrics (0 files)"""
        resp = requests.get(
            f"{BASE_URL}/api/tenants/acme_corp/status",
            headers={"X-Tenant-ID": "acme_corp"}
        )
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["tenant_id"] == "acme_corp"
        # Acme tenant should have 0 uploaded files (data isolation)
        assert data["metrics"]["uploaded_files"] == 0, f"Acme should have 0 files, got {data['metrics']['uploaded_files']}"
    
    def test_tenant_not_found(self):
        """GET /api/tenants/{tenant_id}/status - returns 404 for non-existent tenant"""
        resp = requests.get(
            f"{BASE_URL}/api/tenants/nonexistent_tenant_xyz/status",
            headers={"X-Tenant-ID": "demo"}
        )
        assert resp.status_code == 404


class TestAuthentication:
    """Tests for /api/auth/* endpoints"""
    
    def test_login_demo_tenant(self):
        """POST /api/auth/login - successful login with demo tenant"""
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
            headers={"X-Tenant-ID": DEMO_TENANT_ID}
        )
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        
        data = resp.json()
        assert "access_token" in data, "Response should have access_token"
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        
        user = data["user"]
        assert user["email"] == DEMO_EMAIL
        assert user["tenant_id"] == DEMO_TENANT_ID
        assert "role" in user
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login - fails with invalid credentials"""
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_EMAIL, "password": "wrongpassword"},
            headers={"X-Tenant-ID": DEMO_TENANT_ID}
        )
        assert resp.status_code == 401
    
    def test_login_without_tenant_header(self):
        """POST /api/auth/login - falls back to demo tenant without X-Tenant-ID"""
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}
        )
        # Should work because middleware falls back to demo tenant
        assert resp.status_code == 200
    
    def test_auth_me_endpoint(self):
        """GET /api/auth/me - returns user info from token"""
        # First login to get token
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
            headers={"X-Tenant-ID": DEMO_TENANT_ID}
        )
        token = login_resp.json()["access_token"]
        
        # Test /me endpoint
        resp = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["email"] == DEMO_EMAIL
        assert data["tenant_id"] == DEMO_TENANT_ID
        assert "role" in data
        assert "user_id" in data
    
    def test_auth_me_without_token(self):
        """GET /api/auth/me - fails without token"""
        resp = requests.get(f"{BASE_URL}/api/auth/me")
        assert resp.status_code == 401


class TestTenantDataIsolation:
    """Tests for tenant data isolation"""
    
    def test_demo_tenant_has_data(self):
        """Demo tenant should have 7/7 uploaded files"""
        resp = requests.get(
            f"{BASE_URL}/api/upload/status",
            headers={"X-Tenant-ID": "demo"}
        )
        assert resp.status_code == 200
        
        data = resp.json()
        uploaded_count = sum(1 for v in data.values() if v.get("uploaded"))
        assert uploaded_count == 7, f"Demo should have 7 files, got {uploaded_count}"
    
    def test_acme_tenant_no_data(self):
        """Acme tenant should have 0/7 uploaded files (isolated)"""
        resp = requests.get(
            f"{BASE_URL}/api/upload/status",
            headers={"X-Tenant-ID": "acme_corp"}
        )
        assert resp.status_code == 200
        
        data = resp.json()
        uploaded_count = sum(1 for v in data.values() if v.get("uploaded"))
        assert uploaded_count == 0, f"Acme should have 0 files, got {uploaded_count}"
    
    def test_analytics_with_demo_tenant(self):
        """Analytics endpoints work with demo tenant data"""
        resp = requests.get(
            f"{BASE_URL}/api/analytics/overview",
            headers={"X-Tenant-ID": "demo"}
        )
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["total_styles"] > 0, "Demo should have styles"
        assert data["sales_records"] > 0, "Demo should have sales records"
    
    def test_analytics_with_acme_tenant(self):
        """Analytics endpoints return empty for acme tenant (no data)"""
        resp = requests.get(
            f"{BASE_URL}/api/analytics/overview",
            headers={"X-Tenant-ID": "acme_corp"}
        )
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["total_styles"] == 0, "Acme should have 0 styles"
        assert data["sales_records"] == 0, "Acme should have 0 sales records"


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing endpoints"""
    
    def test_upload_status_without_tenant(self):
        """Upload status works without X-Tenant-ID (falls back to demo)"""
        resp = requests.get(f"{BASE_URL}/api/upload/status")
        assert resp.status_code == 200
        
        data = resp.json()
        uploaded_count = sum(1 for v in data.values() if v.get("uploaded"))
        assert uploaded_count == 7, "Should fall back to demo tenant with 7 files"
    
    def test_analytics_overview_without_tenant(self):
        """Analytics overview works without X-Tenant-ID"""
        resp = requests.get(f"{BASE_URL}/api/analytics/overview")
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["total_styles"] > 0
    
    def test_executive_dashboard_without_tenant(self):
        """Executive dashboard works without X-Tenant-ID"""
        resp = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        assert resp.status_code == 200
        
        data = resp.json()
        assert "health_score" in data
        assert "modules" in data
        assert "alerts" in data
    
    def test_ros_gap_analysis(self):
        """ROS gap analysis still works"""
        resp = requests.get(
            f"{BASE_URL}/api/analytics/ros-gap",
            headers={"X-Tenant-ID": "demo"}
        )
        assert resp.status_code == 200
    
    def test_stock_out_analysis(self):
        """Stock-out analysis still works"""
        resp = requests.get(
            f"{BASE_URL}/api/analytics/stock-out",
            headers={"X-Tenant-ID": "demo"}
        )
        assert resp.status_code == 200
    
    def test_doh_analysis(self):
        """DOH analysis still works"""
        resp = requests.get(
            f"{BASE_URL}/api/analytics/doh",
            headers={"X-Tenant-ID": "demo"}
        )
        assert resp.status_code == 200
    
    def test_planogram_fill_rate(self):
        """Planogram fill rate still works"""
        resp = requests.get(
            f"{BASE_URL}/api/analytics/planogram-fill-rate",
            headers={"X-Tenant-ID": "demo"}
        )
        assert resp.status_code == 200
    
    def test_replenishment_plan(self):
        """Replenishment plan still works"""
        resp = requests.get(
            f"{BASE_URL}/api/analytics/replenishment",
            headers={"X-Tenant-ID": "demo"}
        )
        assert resp.status_code == 200
    
    def test_filter_options(self):
        """Filter options still works"""
        resp = requests.get(
            f"{BASE_URL}/api/analytics/filter-options",
            headers={"X-Tenant-ID": "demo"}
        )
        assert resp.status_code == 200


class TestTenantCreation:
    """Tests for tenant creation (POST /api/tenants/create)"""
    
    def test_create_tenant_validation(self):
        """POST /api/tenants/create - validates required fields"""
        # Missing required fields
        resp = requests.post(
            f"{BASE_URL}/api/tenants/create",
            json={"company_name": "Test"}
        )
        assert resp.status_code == 422, "Should fail validation"
    
    def test_create_tenant_subdomain_pattern(self):
        """POST /api/tenants/create - validates subdomain pattern"""
        resp = requests.post(
            f"{BASE_URL}/api/tenants/create",
            json={
                "company_name": "Test Company",
                "subdomain": "a",  # Too short
                "admin_email": "test@test.com",
                "admin_password": "testpass123"
            }
        )
        assert resp.status_code == 422, "Should fail subdomain validation"
    
    def test_create_tenant_duplicate_subdomain(self):
        """POST /api/tenants/create - rejects duplicate subdomain"""
        resp = requests.post(
            f"{BASE_URL}/api/tenants/create",
            json={
                "company_name": "Another Demo",
                "subdomain": "demo",  # Already taken
                "admin_email": "another@demo.com",
                "admin_password": "testpass123"
            }
        )
        assert resp.status_code == 400, "Should reject duplicate subdomain"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
