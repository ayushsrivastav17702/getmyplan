"""
Iteration 43: Branding Verification Tests
Tests that all 'Increff' and 'Merchandising Tool' references have been replaced with 'GetMyPlan'
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBrandingBackend:
    """Backend API branding verification tests"""
    
    def test_api_root_branding(self):
        """BR-01: API root should return GetMyPlan branding"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "GetMyPlan" in data.get("message", ""), f"Expected 'GetMyPlan' in root message, got: {data}"
        assert "Increff" not in data.get("message", ""), "Found 'Increff' in root message - should be removed"
        assert "Merchandising" not in data.get("message", ""), "Found 'Merchandising' in root message - should be removed"
        print(f"✓ BR-01 PASS: API root returns '{data.get('message')}'")
    
    def test_login_returns_no_increff(self):
        """BR-02: Login response should not contain Increff branding"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@demo.com", "password": "demo1234"},
            headers={"X-Tenant-ID": "demo"}
        )
        assert response.status_code == 200
        response_text = response.text.lower()
        assert "increff" not in response_text, "Found 'increff' in login response"
        assert "merchandising tool" not in response_text, "Found 'merchandising tool' in login response"
        print("✓ BR-02 PASS: Login response has no Increff branding")
    
    def test_signup_register_endpoint(self):
        """BR-03: Signup endpoint should work (functional test)"""
        # Test with invalid data to verify endpoint exists and responds
        response = requests.post(
            f"{BASE_URL}/api/signup/register",
            json={
                "company_name": "Test",
                "email": "invalid",  # Invalid email to trigger validation
                "password": "short",  # Too short
                "subdomain": "ab"  # Too short
            }
        )
        # Should return 422 for validation errors, not 404
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"
        print("✓ BR-03 PASS: Signup endpoint exists and validates input")
    
    def test_tenants_list_no_increff(self):
        """BR-04: Tenants list should not contain Increff branding"""
        response = requests.get(f"{BASE_URL}/api/tenants/")
        assert response.status_code == 200
        response_text = response.text.lower()
        assert "increff" not in response_text, "Found 'increff' in tenants list"
        print("✓ BR-04 PASS: Tenants list has no Increff branding")


class TestBrandingEnvConfig:
    """Environment configuration branding tests"""
    
    def test_from_name_env_var(self):
        """BR-05: FROM_NAME should be GetMyPlan"""
        # Read backend .env file
        env_path = "/app/backend/.env"
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        assert "FROM_NAME=GetMyPlan" in env_content, "FROM_NAME should be 'GetMyPlan'"
        assert "FROM_NAME=Increff" not in env_content, "FROM_NAME should not be 'Increff'"
        print("✓ BR-05 PASS: FROM_NAME=GetMyPlan in backend .env")


class TestBrandingFrontendFiles:
    """Frontend file branding verification tests"""
    
    def test_login_page_branding(self):
        """BR-06: LoginPage.js should have GetMyPlan branding"""
        with open("/app/frontend/src/pages/LoginPage.js", 'r') as f:
            content = f.read()
        
        assert "GetMyPlan" in content, "LoginPage should contain 'GetMyPlan'"
        assert "AI-Powered Retail Analytics" in content, "LoginPage should have subtitle"
        assert "GetMyPlan v2.0" in content, "LoginPage should have version footer"
        assert "Start your 7-day free trial" in content, "LoginPage should have trial link"
        
        # Check no old branding
        assert "Increff Analytics" not in content, "Found 'Increff Analytics' - should be removed"
        assert "Merchandising Tool" not in content, "Found 'Merchandising Tool' - should be removed"
        print("✓ BR-06 PASS: LoginPage.js has correct GetMyPlan branding")
    
    def test_signup_page_branding(self):
        """BR-07: Signup.jsx should have GetMyPlan branding"""
        with open("/app/frontend/src/pages/Signup.jsx", 'r') as f:
            content = f.read()
        
        assert "GetMyPlan v2.0" in content, "Signup should have GetMyPlan footer"
        assert "AI-powered retail analytics" in content, "Signup should have analytics subtitle"
        
        # Check no old branding
        assert "Increff" not in content, "Found 'Increff' in Signup - should be removed"
        print("✓ BR-07 PASS: Signup.jsx has correct GetMyPlan branding")
    
    def test_core_logics_branding(self):
        """BR-08: CoreLogics.js should have GetMyPlan branding"""
        with open("/app/frontend/src/pages/CoreLogics.js", 'r') as f:
            content = f.read()
        
        assert "GetMyPlan Core Logics" in content, "CoreLogics should have GetMyPlan heading"
        assert "powered by GetMyPlan algorithms" in content, "CoreLogics should mention GetMyPlan algorithms"
        
        # Check no old branding
        assert "Increff" not in content, "Found 'Increff' in CoreLogics - should be removed"
        print("✓ BR-08 PASS: CoreLogics.js has correct GetMyPlan branding")
    
    def test_onboarding_wizard_branding(self):
        """BR-09: OnboardingWizard.js should have GetMyPlan branding"""
        with open("/app/frontend/src/pages/OnboardingWizard.js", 'r') as f:
            content = f.read()
        
        assert "Welcome to GetMyPlan" in content, "OnboardingWizard should have GetMyPlan welcome"
        
        # Check no old branding
        assert "Increff" not in content, "Found 'Increff' in OnboardingWizard - should be removed"
        print("✓ BR-09 PASS: OnboardingWizard.js has correct GetMyPlan branding")
    
    def test_executive_dashboard_branding(self):
        """BR-10: ExecutiveDashboard.js should have GetMyPlan branding in PDF export"""
        with open("/app/frontend/src/pages/ExecutiveDashboard.js", 'r') as f:
            content = f.read()
        
        assert "GetMyPlan Analytics - Confidential" in content, "PDF export should have GetMyPlan watermark"
        
        # Check no old branding
        assert "Increff" not in content, "Found 'Increff' in ExecutiveDashboard - should be removed"
        print("✓ BR-10 PASS: ExecutiveDashboard.js has correct GetMyPlan branding")
    
    def test_app_js_sidebar_branding(self):
        """BR-11: App.js sidebar should fallback to GetMyPlan"""
        with open("/app/frontend/src/App.js", 'r') as f:
            content = f.read()
        
        # Check sidebar fallback
        assert '"GetMyPlan"' in content or "'GetMyPlan'" in content, "App.js sidebar should fallback to GetMyPlan"
        
        # Check no old branding
        assert "Increff" not in content, "Found 'Increff' in App.js - should be removed"
        print("✓ BR-11 PASS: App.js has correct GetMyPlan sidebar fallback")
    
    def test_index_html_title(self):
        """BR-12: index.html should have GetMyPlan title"""
        with open("/app/frontend/public/index.html", 'r') as f:
            content = f.read()
        
        assert "GetMyPlan | AI Retail Analytics" in content, "index.html should have GetMyPlan title"
        assert "GetMyPlan - AI-powered retail analytics" in content, "index.html should have GetMyPlan description"
        
        # Check no old branding
        assert "Increff" not in content, "Found 'Increff' in index.html - should be removed"
        print("✓ BR-12 PASS: index.html has correct GetMyPlan title and description")


class TestBrandingBackendFiles:
    """Backend file branding verification tests"""
    
    def test_server_py_branding(self):
        """BR-13: server.py should have GetMyPlan branding"""
        with open("/app/backend/server.py", 'r') as f:
            content = f.read()
        
        assert "GetMyPlan - AI Retail Analytics API" in content, "server.py root should return GetMyPlan"
        
        # Check no old branding
        assert "Increff" not in content, "Found 'Increff' in server.py - should be removed"
        assert "Merchandising Tool" not in content, "Found 'Merchandising Tool' in server.py - should be removed"
        print("✓ BR-13 PASS: server.py has correct GetMyPlan branding")
    
    def test_smtp_email_service_branding(self):
        """BR-14: smtp_email_service.py should have GetMyPlan branding"""
        with open("/app/backend/services/smtp_email_service.py", 'r') as f:
            content = f.read()
        
        # Check email templates use GetMyPlan
        assert "GetMyPlan" in content, "Email service should use GetMyPlan branding"
        
        # Check no old branding
        assert "Increff" not in content, "Found 'Increff' in smtp_email_service - should be removed"
        print("✓ BR-14 PASS: smtp_email_service.py has correct GetMyPlan branding")


class TestExistingFlowsStillWork:
    """Verify existing login/signup flows still work after branding changes"""
    
    def test_demo_tenant_login(self):
        """BR-15: Demo tenant login should still work"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@demo.com", "password": "demo1234"},
            headers={"X-Tenant-ID": "demo"}
        )
        assert response.status_code == 200, f"Demo login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Login should return access_token"
        print("✓ BR-15 PASS: Demo tenant login works")
    
    def test_acme_tenant_login(self):
        """BR-16: Acme Corp tenant login should still work"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@acme.com", "password": "AcmePass123!"},
            headers={"X-Tenant-ID": "acme_corp"}
        )
        assert response.status_code == 200, f"Acme login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Login should return access_token"
        print("✓ BR-16 PASS: Acme Corp tenant login works")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
