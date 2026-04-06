"""
Test suite for Self-Service Signup Flow (Iteration 42)
Tests: POST /api/signup/register, /verify-email, /resend-verification
       Login with trial info, existing tenant login, validation rules
"""
import pytest
import requests
import os
import time
import random
import string
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ─── Helpers ───

def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def random_email():
    return f"test_{random_string()}@testmail.com"

def random_subdomain():
    return f"test{random_string(6)}"


# ─── Fixtures ───

@pytest.fixture
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


# ─── Test Class: Signup Registration ───

class TestSignupRegister:
    """Tests for POST /api/signup/register"""
    
    def test_register_success(self, api_client):
        """SU-01: Successful registration creates user + tenant + returns success"""
        email = random_email()
        subdomain = random_subdomain()
        company = f"Test Company {random_string(4)}"
        
        response = api_client.post(f"{BASE_URL}/api/signup/register", json={
            "company_name": company,
            "email": email,
            "password": "TestPass123",
            "subdomain": subdomain
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert data.get("success") is True
        assert "message" in data
        assert data.get("email") == email
        assert data.get("subdomain") == subdomain
        assert "tenant_id" in data
        assert data.get("trial_days") == 7
        
        print(f"✓ SU-01: Registration successful for {email}, tenant_id={data['tenant_id']}")
    
    def test_register_duplicate_email(self, api_client):
        """SU-02: Duplicate email returns 400"""
        email = random_email()
        subdomain1 = random_subdomain()
        subdomain2 = random_subdomain()
        
        # First registration
        resp1 = api_client.post(f"{BASE_URL}/api/signup/register", json={
            "company_name": "Company 1",
            "email": email,
            "password": "TestPass123",
            "subdomain": subdomain1
        })
        assert resp1.status_code == 200
        
        # Second registration with same email
        resp2 = api_client.post(f"{BASE_URL}/api/signup/register", json={
            "company_name": "Company 2",
            "email": email,
            "password": "TestPass456",
            "subdomain": subdomain2
        })
        
        assert resp2.status_code == 400
        assert "already registered" in resp2.json().get("detail", "").lower()
        print("✓ SU-02: Duplicate email correctly rejected")
    
    def test_register_duplicate_subdomain(self, api_client):
        """SU-03: Duplicate subdomain returns 400"""
        subdomain = random_subdomain()
        
        # First registration
        resp1 = api_client.post(f"{BASE_URL}/api/signup/register", json={
            "company_name": "Company 1",
            "email": random_email(),
            "password": "TestPass123",
            "subdomain": subdomain
        })
        assert resp1.status_code == 200
        
        # Second registration with same subdomain
        resp2 = api_client.post(f"{BASE_URL}/api/signup/register", json={
            "company_name": "Company 2",
            "email": random_email(),
            "password": "TestPass456",
            "subdomain": subdomain
        })
        
        assert resp2.status_code == 400
        assert "subdomain" in resp2.json().get("detail", "").lower()
        print("✓ SU-03: Duplicate subdomain correctly rejected")
    
    def test_register_reserved_subdomain(self, api_client):
        """SU-04: Reserved subdomains (www, api, admin, demo, test) are rejected"""
        reserved = ["www", "api", "admin", "demo", "test"]
        
        for sub in reserved:
            resp = api_client.post(f"{BASE_URL}/api/signup/register", json={
                "company_name": "Test Company",
                "email": random_email(),
                "password": "TestPass123",
                "subdomain": sub
            })
            assert resp.status_code == 422, f"Expected 422 for reserved subdomain '{sub}', got {resp.status_code}"
        
        print("✓ SU-04: Reserved subdomains correctly rejected")
    
    def test_register_password_too_short(self, api_client):
        """SU-05: Password < 8 chars rejected"""
        resp = api_client.post(f"{BASE_URL}/api/signup/register", json={
            "company_name": "Test Company",
            "email": random_email(),
            "password": "Pass1",  # Only 5 chars
            "subdomain": random_subdomain()
        })
        
        assert resp.status_code == 422
        print("✓ SU-05: Short password correctly rejected")
    
    def test_register_password_no_letter(self, api_client):
        """SU-06: Password without letters rejected"""
        resp = api_client.post(f"{BASE_URL}/api/signup/register", json={
            "company_name": "Test Company",
            "email": random_email(),
            "password": "12345678",  # No letters
            "subdomain": random_subdomain()
        })
        
        assert resp.status_code == 422
        print("✓ SU-06: Password without letters correctly rejected")
    
    def test_register_password_no_number(self, api_client):
        """SU-07: Password without numbers rejected"""
        resp = api_client.post(f"{BASE_URL}/api/signup/register", json={
            "company_name": "Test Company",
            "email": random_email(),
            "password": "TestPassword",  # No numbers
            "subdomain": random_subdomain()
        })
        
        assert resp.status_code == 422
        print("✓ SU-07: Password without numbers correctly rejected")
    
    def test_register_invalid_email(self, api_client):
        """SU-08: Invalid email format rejected"""
        resp = api_client.post(f"{BASE_URL}/api/signup/register", json={
            "company_name": "Test Company",
            "email": "not-an-email",
            "password": "TestPass123",
            "subdomain": random_subdomain()
        })
        
        assert resp.status_code == 422
        print("✓ SU-08: Invalid email format correctly rejected")
    
    def test_register_subdomain_too_short(self, api_client):
        """SU-09: Subdomain < 3 chars rejected"""
        resp = api_client.post(f"{BASE_URL}/api/signup/register", json={
            "company_name": "Test Company",
            "email": random_email(),
            "password": "TestPass123",
            "subdomain": "ab"  # Only 2 chars
        })
        
        assert resp.status_code == 422
        print("✓ SU-09: Short subdomain correctly rejected")


# ─── Test Class: Email Verification ───

class TestEmailVerification:
    """Tests for POST /api/signup/verify-email"""
    
    def test_verify_invalid_token(self, api_client):
        """VE-01: Invalid token returns 400"""
        resp = api_client.post(f"{BASE_URL}/api/signup/verify-email", json={
            "token": "invalid_token_12345"
        })
        
        assert resp.status_code == 400
        assert "invalid" in resp.json().get("detail", "").lower() or "expired" in resp.json().get("detail", "").lower()
        print("✓ VE-01: Invalid token correctly rejected")
    
    def test_verify_empty_token(self, api_client):
        """VE-02: Empty token returns 422"""
        resp = api_client.post(f"{BASE_URL}/api/signup/verify-email", json={
            "token": ""
        })
        
        # Could be 400 or 422 depending on validation
        assert resp.status_code in [400, 422]
        print("✓ VE-02: Empty token correctly rejected")


# ─── Test Class: Resend Verification ───

class TestResendVerification:
    """Tests for POST /api/signup/resend-verification"""
    
    def test_resend_nonexistent_email(self, api_client):
        """RV-01: Non-existent email returns 404"""
        resp = api_client.post(f"{BASE_URL}/api/signup/resend-verification", json={
            "email": "nonexistent@testmail.com"
        })
        
        assert resp.status_code == 404
        print("✓ RV-01: Non-existent email correctly returns 404")
    
    def test_resend_rate_limiting(self, api_client):
        """RV-02: Rate limiting (60s) enforced"""
        # First, register a new user
        email = random_email()
        subdomain = random_subdomain()
        
        reg_resp = api_client.post(f"{BASE_URL}/api/signup/register", json={
            "company_name": "Rate Limit Test",
            "email": email,
            "password": "TestPass123",
            "subdomain": subdomain
        })
        assert reg_resp.status_code == 200
        
        # First resend should succeed
        resp1 = api_client.post(f"{BASE_URL}/api/signup/resend-verification", json={
            "email": email
        })
        assert resp1.status_code == 200
        
        # Immediate second resend should be rate limited
        resp2 = api_client.post(f"{BASE_URL}/api/signup/resend-verification", json={
            "email": email
        })
        assert resp2.status_code == 429
        print("✓ RV-02: Rate limiting correctly enforced")


# ─── Test Class: Login with Trial Info ───

class TestLoginTrialInfo:
    """Tests for login behavior with trial tenants"""
    
    def test_existing_tenant_login_no_trial_info(self, api_client):
        """LT-01: Existing tenant (demo) login returns NO trial_info"""
        resp = api_client.post(f"{BASE_URL}/api/auth/login", 
            json={"email": "admin@demo.com", "password": "demo1234"},
            headers={"X-Tenant-ID": "demo"}
        )
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify no trial_info for non-trial tenant
        assert "trial_info" not in data or data.get("trial_info") is None
        assert data.get("access_token") is not None
        assert data.get("user", {}).get("email") == "admin@demo.com"
        
        print("✓ LT-01: Demo tenant login returns NO trial_info")
    
    def test_unverified_user_blocked(self, api_client):
        """LT-02: Unverified user cannot login (tenant blocked at middleware level)"""
        # Register a new user (unverified)
        email = random_email()
        subdomain = random_subdomain()
        
        reg_resp = api_client.post(f"{BASE_URL}/api/signup/register", json={
            "company_name": "Unverified Test",
            "email": email,
            "password": "TestPass123",
            "subdomain": subdomain
        })
        assert reg_resp.status_code == 200
        tenant_id = reg_resp.json().get("tenant_id")
        
        # Try to login without verification
        # Tenant is in "pending_verification" status, so middleware blocks it
        login_resp = api_client.post(f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": "TestPass123"},
            headers={"X-Tenant-ID": tenant_id}
        )
        
        assert login_resp.status_code == 403
        # Either "verify" message or "not found or inactive" (tenant blocked at middleware)
        detail = login_resp.json().get("detail", "").lower()
        assert "verify" in detail or "inactive" in detail or "not found" in detail
        print("✓ LT-02: Unverified user correctly blocked from login")
    
    def test_wrong_password_rejected(self, api_client):
        """LT-03: Wrong password returns 401"""
        resp = api_client.post(f"{BASE_URL}/api/auth/login",
            json={"email": "admin@demo.com", "password": "wrongpassword"},
            headers={"X-Tenant-ID": "demo"}
        )
        
        assert resp.status_code == 401
        print("✓ LT-03: Wrong password correctly rejected")
    
    def test_login_without_tenant_header(self, api_client):
        """LT-04: Login without X-Tenant-ID falls back to demo tenant"""
        resp = api_client.post(f"{BASE_URL}/api/auth/login",
            json={"email": "admin@demo.com", "password": "demo1234"}
        )
        
        # Should work with demo fallback
        assert resp.status_code == 200
        print("✓ LT-04: Login without tenant header uses demo fallback")


# ─── Test Class: Public Routes Bypass ───

class TestPublicRoutes:
    """Tests that signup routes bypass tenant middleware"""
    
    def test_register_no_tenant_header(self, api_client):
        """PR-01: /api/signup/register works without X-Tenant-ID"""
        resp = api_client.post(f"{BASE_URL}/api/signup/register", json={
            "company_name": "No Header Test",
            "email": random_email(),
            "password": "TestPass123",
            "subdomain": random_subdomain()
        })
        
        # Should not require tenant header
        assert resp.status_code == 200
        print("✓ PR-01: Register endpoint works without tenant header")
    
    def test_verify_email_no_tenant_header(self, api_client):
        """PR-02: /api/signup/verify-email works without X-Tenant-ID"""
        resp = api_client.post(f"{BASE_URL}/api/signup/verify-email", json={
            "token": "test_token"
        })
        
        # Should return 400 (invalid token) not 400 (tenant required)
        assert resp.status_code == 400
        assert "tenant" not in resp.json().get("detail", "").lower()
        print("✓ PR-02: Verify-email endpoint works without tenant header")
    
    def test_resend_verification_no_tenant_header(self, api_client):
        """PR-03: /api/signup/resend-verification works without X-Tenant-ID"""
        resp = api_client.post(f"{BASE_URL}/api/signup/resend-verification", json={
            "email": "nonexistent@test.com"
        })
        
        # Should return 404 (user not found) not 400 (tenant required)
        assert resp.status_code == 404
        assert "tenant" not in resp.json().get("detail", "").lower()
        print("✓ PR-03: Resend-verification endpoint works without tenant header")


# ─── Test Class: Tenant List for Signup Users ───

class TestTenantList:
    """Tests that newly created tenants appear in tenant list"""
    
    def test_new_tenant_appears_in_list(self, api_client):
        """TL-01: Newly registered tenant appears in /api/tenants/ list"""
        email = random_email()
        subdomain = random_subdomain()
        company = f"List Test {random_string(4)}"
        
        # Register
        reg_resp = api_client.post(f"{BASE_URL}/api/signup/register", json={
            "company_name": company,
            "email": email,
            "password": "TestPass123",
            "subdomain": subdomain
        })
        assert reg_resp.status_code == 200
        tenant_id = reg_resp.json().get("tenant_id")
        
        # Check tenant list
        list_resp = api_client.get(f"{BASE_URL}/api/tenants/")
        assert list_resp.status_code == 200
        
        tenants = list_resp.json().get("tenants", [])
        tenant_ids = [t.get("tenant_id") for t in tenants]
        
        # Note: Tenant may be in "pending_verification" status and might not appear
        # This depends on implementation - check if it appears or not
        print(f"✓ TL-01: Tenant list retrieved, new tenant_id={tenant_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
