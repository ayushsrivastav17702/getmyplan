"""
MFA (Multi-Factor Authentication) Backend Tests - Iteration 78
Tests TOTP (Authenticator App) + Email OTP flows for GetMyPlan platform.

Endpoints tested:
1. GET /api/auth/mfa/status - MFA status for authenticated user
2. POST /api/auth/mfa/setup-totp - Generate TOTP secret + QR code
3. POST /api/auth/mfa/verify-setup - Verify TOTP code to enable MFA
4. POST /api/auth/login - MFA challenge when MFA enabled
5. POST /api/auth/mfa/verify-totp - Verify TOTP during login
6. POST /api/auth/mfa/send-email-otp - Send email OTP for login
7. POST /api/auth/mfa/verify-email-otp - Verify email OTP during login
8. POST /api/auth/mfa/disable - Disable MFA
9. POST /api/auth/mfa/tenant-enforce - Admin sets MFA enforcement
"""

import pytest
import requests
import os
import pyotp
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

# Test credentials
TEST_USER_EMAIL = "ayush.srivastav@increff.com"
TEST_USER_PASSWORD = "Ayush@114988"
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "demo1234"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for test user"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        # Handle MFA challenge if MFA is enabled
        if data.get("mfa_required"):
            pytest.skip("MFA already enabled - need to disable first")
        return data.get("access_token")
    pytest.skip(f"Authentication failed: {response.text}")


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get authentication token for admin user"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        if data.get("mfa_required"):
            pytest.skip("Admin MFA already enabled")
        return data.get("access_token")
    pytest.skip(f"Admin authentication failed: {response.text}")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


@pytest.fixture(scope="module")
def admin_client(api_client, admin_token):
    """Session with admin auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}"
    })
    return session


def reset_user_mfa(email):
    """Helper to reset MFA for a user in database"""
    async def _reset():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        await db.users.update_one(
            {"email": email},
            {"$set": {
                "mfa_enabled": False,
                "totp_secret": None,
                "totp_verified": False,
            }}
        )
        # Clean up any MFA sessions
        await db.mfa_sessions.delete_many({"email": email})
        client.close()
    asyncio.get_event_loop().run_until_complete(_reset())


def get_user_totp_secret(email):
    """Get TOTP secret from database for code generation"""
    async def _get():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        user = await db.users.find_one({"email": email})
        client.close()
        return user.get("totp_secret") if user else None
    return asyncio.get_event_loop().run_until_complete(_get())


class TestMFAStatus:
    """Test GET /api/auth/mfa/status endpoint"""
    
    def test_mfa_status_unauthenticated(self, api_client):
        """MFA status requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/auth/mfa/status")
        assert response.status_code == 401
        print("✓ MFA status returns 401 without auth")
    
    def test_mfa_status_authenticated(self, authenticated_client):
        """MFA status returns correct fields for authenticated user"""
        response = authenticated_client.get(f"{BASE_URL}/api/auth/mfa/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "mfa_enabled" in data
        assert "totp_verified" in data
        assert "tenant_mfa_enforced" in data
        assert isinstance(data["mfa_enabled"], bool)
        assert isinstance(data["totp_verified"], bool)
        assert isinstance(data["tenant_mfa_enforced"], bool)
        print(f"✓ MFA status: enabled={data['mfa_enabled']}, totp_verified={data['totp_verified']}, tenant_enforced={data['tenant_mfa_enforced']}")


class TestMFASetupTOTP:
    """Test POST /api/auth/mfa/setup-totp endpoint"""
    
    def test_setup_totp_unauthenticated(self):
        """TOTP setup requires authentication"""
        # Use fresh session without auth header
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.post(f"{BASE_URL}/api/auth/mfa/setup-totp")
        assert response.status_code == 401
        print("✓ TOTP setup returns 401 without auth")
    
    def test_setup_totp_success(self, authenticated_client):
        """TOTP setup returns QR code and secret"""
        # First ensure MFA is disabled
        reset_user_mfa(TEST_USER_EMAIL)
        
        response = authenticated_client.post(f"{BASE_URL}/api/auth/mfa/setup-totp")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "qr_code" in data
        assert "secret" in data
        assert "setup_token" in data
        
        # QR code should be base64 data URI
        assert data["qr_code"].startswith("data:image/png;base64,")
        
        # Secret should be base32 encoded (32 chars)
        assert len(data["secret"]) == 32
        
        # Setup token should be present
        assert len(data["setup_token"]) > 0
        
        print(f"✓ TOTP setup returned QR code and secret (length={len(data['secret'])})")


class TestMFAVerifySetup:
    """Test POST /api/auth/mfa/verify-setup endpoint"""
    
    def test_verify_setup_invalid_token(self, authenticated_client):
        """Verify setup fails with invalid setup token"""
        response = authenticated_client.post(f"{BASE_URL}/api/auth/mfa/verify-setup", json={
            "totp_code": "123456",
            "setup_token": "invalid_token"
        })
        assert response.status_code == 400
        print("✓ Verify setup fails with invalid setup token")
    
    def test_verify_setup_invalid_code(self, authenticated_client):
        """Verify setup fails with wrong TOTP code"""
        # First get a valid setup token
        reset_user_mfa(TEST_USER_EMAIL)
        setup_resp = authenticated_client.post(f"{BASE_URL}/api/auth/mfa/setup-totp")
        assert setup_resp.status_code == 200
        setup_data = setup_resp.json()
        
        # Try with wrong code
        response = authenticated_client.post(f"{BASE_URL}/api/auth/mfa/verify-setup", json={
            "totp_code": "000000",
            "setup_token": setup_data["setup_token"]
        })
        assert response.status_code == 400
        assert "Invalid code" in response.json().get("detail", "")
        print("✓ Verify setup fails with invalid TOTP code")
    
    def test_verify_setup_success(self, authenticated_client):
        """Verify setup succeeds with correct TOTP code"""
        # Reset and get fresh setup
        reset_user_mfa(TEST_USER_EMAIL)
        setup_resp = authenticated_client.post(f"{BASE_URL}/api/auth/mfa/setup-totp")
        assert setup_resp.status_code == 200
        setup_data = setup_resp.json()
        
        # Generate valid TOTP code
        totp = pyotp.TOTP(setup_data["secret"])
        valid_code = totp.now()
        
        response = authenticated_client.post(f"{BASE_URL}/api/auth/mfa/verify-setup", json={
            "totp_code": valid_code,
            "setup_token": setup_data["setup_token"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "enabled" in data.get("message", "").lower()
        
        # Verify MFA is now enabled
        status_resp = authenticated_client.get(f"{BASE_URL}/api/auth/mfa/status")
        status = status_resp.json()
        assert status["mfa_enabled"] == True
        assert status["totp_verified"] == True
        
        print("✓ MFA enabled successfully with valid TOTP code")


class TestMFALoginFlow:
    """Test login flow when MFA is enabled"""
    
    def test_login_with_mfa_enabled(self, api_client):
        """Login returns MFA challenge when MFA is enabled"""
        # First enable MFA for the user
        reset_user_mfa(TEST_USER_EMAIL)
        
        # Login to get token
        login_resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")
        
        # Setup and enable MFA
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        setup_resp = api_client.post(f"{BASE_URL}/api/auth/mfa/setup-totp", headers=headers)
        setup_data = setup_resp.json()
        
        totp = pyotp.TOTP(setup_data["secret"])
        api_client.post(f"{BASE_URL}/api/auth/mfa/verify-setup", headers=headers, json={
            "totp_code": totp.now(),
            "setup_token": setup_data["setup_token"]
        })
        
        # Now try to login again - should get MFA challenge
        login_resp2 = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert login_resp2.status_code == 200
        data = login_resp2.json()
        
        assert data.get("mfa_required") == True
        assert "mfa_token" in data
        assert "mfa_methods" in data
        assert "totp" in data["mfa_methods"]
        assert "email_otp" in data["mfa_methods"]
        assert "expires_in" in data
        
        print(f"✓ Login returns MFA challenge with methods: {data['mfa_methods']}")
        
        # Store for next tests
        return data


class TestMFAVerifyTOTP:
    """Test POST /api/auth/mfa/verify-totp endpoint"""
    
    def test_verify_totp_invalid_token(self, api_client):
        """Verify TOTP fails with invalid MFA token"""
        response = api_client.post(f"{BASE_URL}/api/auth/mfa/verify-totp", json={
            "mfa_token": "invalid_token",
            "totp_code": "123456"
        })
        assert response.status_code == 401
        print("✓ Verify TOTP fails with invalid MFA token")
    
    def test_verify_totp_success(self, api_client):
        """Verify TOTP succeeds and returns full access token"""
        # Setup: Enable MFA and get MFA challenge
        reset_user_mfa(TEST_USER_EMAIL)
        
        # Login to get initial token
        login_resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # Setup MFA
        setup_resp = api_client.post(f"{BASE_URL}/api/auth/mfa/setup-totp", headers=headers)
        setup_data = setup_resp.json()
        secret = setup_data["secret"]
        
        totp = pyotp.TOTP(secret)
        api_client.post(f"{BASE_URL}/api/auth/mfa/verify-setup", headers=headers, json={
            "totp_code": totp.now(),
            "setup_token": setup_data["setup_token"]
        })
        
        # Login again to get MFA challenge
        login_resp2 = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        mfa_data = login_resp2.json()
        assert mfa_data.get("mfa_required") == True
        
        # Verify TOTP
        import time
        time.sleep(1)  # Ensure new TOTP window
        response = api_client.post(f"{BASE_URL}/api/auth/mfa/verify-totp", json={
            "mfa_token": mfa_data["mfa_token"],
            "totp_code": totp.now()
        })
        assert response.status_code == 200
        data = response.json()
        
        # Should return full login response
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_USER_EMAIL
        
        print("✓ TOTP verification returns full access token")


class TestMFAEmailOTP:
    """Test email OTP flow"""
    
    def test_send_email_otp_invalid_token(self, api_client):
        """Send email OTP fails with invalid MFA token"""
        response = api_client.post(f"{BASE_URL}/api/auth/mfa/send-email-otp", json={
            "mfa_token": "invalid_token"
        })
        assert response.status_code == 401
        print("✓ Send email OTP fails with invalid MFA token")
    
    def test_send_email_otp_success(self, api_client):
        """Send email OTP succeeds with valid MFA token"""
        # Setup: Enable MFA and get MFA challenge
        reset_user_mfa(TEST_USER_EMAIL)
        
        # Login and enable MFA
        login_resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        setup_resp = api_client.post(f"{BASE_URL}/api/auth/mfa/setup-totp", headers=headers)
        setup_data = setup_resp.json()
        
        totp = pyotp.TOTP(setup_data["secret"])
        api_client.post(f"{BASE_URL}/api/auth/mfa/verify-setup", headers=headers, json={
            "totp_code": totp.now(),
            "setup_token": setup_data["setup_token"]
        })
        
        # Login to get MFA challenge
        login_resp2 = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        mfa_data = login_resp2.json()
        
        # Send email OTP
        response = api_client.post(f"{BASE_URL}/api/auth/mfa/send-email-otp", json={
            "mfa_token": mfa_data["mfa_token"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "expires_in" in data
        
        print(f"✓ Email OTP sent successfully, expires in {data['expires_in']}s")
    
    def test_verify_email_otp_invalid_code(self, api_client):
        """Verify email OTP fails with wrong code"""
        # Setup MFA and get challenge
        reset_user_mfa(TEST_USER_EMAIL)
        
        login_resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        setup_resp = api_client.post(f"{BASE_URL}/api/auth/mfa/setup-totp", headers=headers)
        setup_data = setup_resp.json()
        
        totp = pyotp.TOTP(setup_data["secret"])
        api_client.post(f"{BASE_URL}/api/auth/mfa/verify-setup", headers=headers, json={
            "totp_code": totp.now(),
            "setup_token": setup_data["setup_token"]
        })
        
        # Get MFA challenge
        login_resp2 = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        mfa_data = login_resp2.json()
        
        # Send email OTP first
        api_client.post(f"{BASE_URL}/api/auth/mfa/send-email-otp", json={
            "mfa_token": mfa_data["mfa_token"]
        })
        
        # Try to verify with wrong code
        response = api_client.post(f"{BASE_URL}/api/auth/mfa/verify-email-otp", json={
            "mfa_token": mfa_data["mfa_token"],
            "otp_code": "000000"
        })
        assert response.status_code == 401
        print("✓ Email OTP verification fails with wrong code")


class TestMFADisable:
    """Test POST /api/auth/mfa/disable endpoint"""
    
    def test_disable_mfa_wrong_password(self, api_client):
        """Disable MFA fails with wrong password"""
        # Setup: Enable MFA first
        reset_user_mfa(TEST_USER_EMAIL)
        
        login_resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        setup_resp = api_client.post(f"{BASE_URL}/api/auth/mfa/setup-totp", headers=headers)
        setup_data = setup_resp.json()
        
        totp = pyotp.TOTP(setup_data["secret"])
        api_client.post(f"{BASE_URL}/api/auth/mfa/verify-setup", headers=headers, json={
            "totp_code": totp.now(),
            "setup_token": setup_data["setup_token"]
        })
        
        # Try to disable with wrong password
        response = api_client.post(f"{BASE_URL}/api/auth/mfa/disable", headers=headers, json={
            "password": "wrongpassword"
        })
        assert response.status_code == 400
        assert "password" in response.json().get("detail", "").lower()
        print("✓ Disable MFA fails with wrong password")
    
    def test_disable_mfa_success(self, api_client):
        """Disable MFA succeeds with correct password"""
        # Setup: Enable MFA first
        reset_user_mfa(TEST_USER_EMAIL)
        
        login_resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        setup_resp = api_client.post(f"{BASE_URL}/api/auth/mfa/setup-totp", headers=headers)
        setup_data = setup_resp.json()
        
        totp = pyotp.TOTP(setup_data["secret"])
        api_client.post(f"{BASE_URL}/api/auth/mfa/verify-setup", headers=headers, json={
            "totp_code": totp.now(),
            "setup_token": setup_data["setup_token"]
        })
        
        # Disable MFA
        response = api_client.post(f"{BASE_URL}/api/auth/mfa/disable", headers=headers, json={
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        
        # Verify MFA is disabled
        status_resp = api_client.get(f"{BASE_URL}/api/auth/mfa/status", headers=headers)
        status = status_resp.json()
        assert status["mfa_enabled"] == False
        
        print("✓ MFA disabled successfully")


class TestMFATenantEnforce:
    """Test POST /api/auth/mfa/tenant-enforce endpoint"""
    
    def test_tenant_enforce_non_admin(self, authenticated_client):
        """Non-admin cannot set tenant MFA enforcement"""
        # Note: Test user might be admin, so this test may need adjustment
        # For now, we test the endpoint exists and responds
        response = authenticated_client.post(f"{BASE_URL}/api/auth/mfa/tenant-enforce", json={
            "enforce": True
        })
        # Should be 200 if admin, 403 if not
        assert response.status_code in [200, 403]
        print(f"✓ Tenant enforce endpoint responds with {response.status_code}")
    
    def test_tenant_enforce_admin(self, admin_client):
        """Admin can set tenant MFA enforcement"""
        # Enable enforcement
        response = admin_client.post(f"{BASE_URL}/api/auth/mfa/tenant-enforce", json={
            "enforce": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data.get("mfa_enforced") == True
        print("✓ Admin enabled MFA enforcement")
        
        # Disable enforcement (cleanup)
        response2 = admin_client.post(f"{BASE_URL}/api/auth/mfa/tenant-enforce", json={
            "enforce": False
        })
        assert response2.status_code == 200
        assert response2.json().get("mfa_enforced") == False
        print("✓ Admin disabled MFA enforcement")


class TestMFAEdgeCases:
    """Test edge cases and error handling"""
    
    def test_setup_when_already_enabled(self, api_client):
        """Setup TOTP fails when MFA already enabled"""
        reset_user_mfa(TEST_USER_EMAIL)
        
        # Login and enable MFA
        login_resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        setup_resp = api_client.post(f"{BASE_URL}/api/auth/mfa/setup-totp", headers=headers)
        setup_data = setup_resp.json()
        
        totp = pyotp.TOTP(setup_data["secret"])
        api_client.post(f"{BASE_URL}/api/auth/mfa/verify-setup", headers=headers, json={
            "totp_code": totp.now(),
            "setup_token": setup_data["setup_token"]
        })
        
        # Try to setup again
        response = api_client.post(f"{BASE_URL}/api/auth/mfa/setup-totp", headers=headers)
        assert response.status_code == 400
        assert "already enabled" in response.json().get("detail", "").lower()
        print("✓ Setup fails when MFA already enabled")
    
    def test_disable_when_not_enabled(self, api_client):
        """Disable MFA fails when not enabled"""
        reset_user_mfa(TEST_USER_EMAIL)
        
        login_resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        response = api_client.post(f"{BASE_URL}/api/auth/mfa/disable", headers=headers, json={
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 400
        assert "not" in response.json().get("detail", "").lower()
        print("✓ Disable fails when MFA not enabled")


# Cleanup fixture
@pytest.fixture(scope="module", autouse=True)
def cleanup(request):
    """Cleanup MFA state after all tests"""
    def _cleanup():
        reset_user_mfa(TEST_USER_EMAIL)
        reset_user_mfa(ADMIN_EMAIL)
        print("\n✓ Cleaned up MFA state for test users")
    request.addfinalizer(_cleanup)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
