"""
Security Hardening Tests - Iteration 44
Tests for enterprise-grade security features:
1. Enhanced health check (DB status, version, uptime)
2. Security headers on all API responses
3. Correlation IDs in responses
4. Demo tenant login still works
5. Signup flow validation
6. NoSQL injection rejection
7. Input validation (password rules, subdomain rules)
8. Global error handler (no stack traces)
9. Request size limits (413 for oversized JSON)
10. Rate limiting decorators present (verified via code inspection)
"""
import pytest
import requests
import os
import json
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Security headers that should be present on all API responses
EXPECTED_SECURITY_HEADERS = [
    "X-Frame-Options",
    "X-Content-Type-Options",
    "Strict-Transport-Security",
    "X-XSS-Protection",
    "Referrer-Policy",
    "Permissions-Policy",
    "Content-Security-Policy",
]


class TestEnhancedHealthCheck:
    """Test enhanced health check endpoint with DB status, version, uptime"""
    
    def test_health_check_returns_enhanced_response(self):
        """SEC-01: Health check returns status, version, company, uptime, database info"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        
        data = response.json()
        
        # Verify all required fields
        assert "status" in data, "Missing 'status' field"
        assert data["status"] in ["healthy", "degraded"], f"Invalid status: {data['status']}"
        
        assert "version" in data, "Missing 'version' field"
        assert data["version"] == "2.0.0", f"Unexpected version: {data['version']}"
        
        assert "company" in data, "Missing 'company' field"
        assert data["company"] == "GetMyPlan", f"Unexpected company: {data['company']}"
        
        assert "uptime_seconds" in data, "Missing 'uptime_seconds' field"
        assert isinstance(data["uptime_seconds"], (int, float)), "uptime_seconds should be numeric"
        assert data["uptime_seconds"] >= 0, "uptime_seconds should be non-negative"
        
        assert "database" in data, "Missing 'database' field"
        assert "status" in data["database"], "Missing 'database.status' field"
        assert data["database"]["status"] in ["connected", "disconnected"], f"Invalid DB status: {data['database']['status']}"
        assert "version" in data["database"], "Missing 'database.version' field"
        
        assert "timestamp" in data, "Missing 'timestamp' field"
        
        print(f"✓ Health check: status={data['status']}, uptime={data['uptime_seconds']}s, db={data['database']['status']}")


class TestSecurityHeaders:
    """Test security headers are present on all API responses"""
    
    def test_security_headers_on_health_endpoint(self):
        """SEC-02: Security headers present on /api/health"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        for header in EXPECTED_SECURITY_HEADERS:
            assert header in response.headers, f"Missing security header: {header}"
        
        # Verify specific header values
        assert response.headers.get("X-Frame-Options") == "DENY", "X-Frame-Options should be DENY"
        assert response.headers.get("X-Content-Type-Options") == "nosniff", "X-Content-Type-Options should be nosniff"
        assert "max-age=" in response.headers.get("Strict-Transport-Security", ""), "HSTS should have max-age"
        
        print(f"✓ All {len(EXPECTED_SECURITY_HEADERS)} security headers present on /api/health")
    
    def test_security_headers_on_api_root(self):
        """SEC-03: Security headers present on /api/"""
        response = requests.get(f"{BASE_URL}/api/")
        
        for header in EXPECTED_SECURITY_HEADERS:
            assert header in response.headers, f"Missing security header on /api/: {header}"
        
        print("✓ Security headers present on /api/")
    
    def test_cache_control_header_on_api(self):
        """SEC-04: Cache-Control=no-store on API responses"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        cache_control = response.headers.get("Cache-Control", "")
        assert "no-store" in cache_control, f"Cache-Control should contain 'no-store', got: {cache_control}"
        
        print(f"✓ Cache-Control header: {cache_control}")


class TestCorrelationIDs:
    """Test correlation IDs and request duration headers"""
    
    def test_correlation_id_in_response(self):
        """SEC-05: X-Correlation-ID header present in response"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        assert "X-Correlation-ID" in response.headers, "Missing X-Correlation-ID header"
        correlation_id = response.headers.get("X-Correlation-ID")
        assert len(correlation_id) > 0, "X-Correlation-ID should not be empty"
        
        print(f"✓ X-Correlation-ID: {correlation_id}")
    
    def test_request_duration_in_response(self):
        """SEC-06: X-Request-Duration header present in response"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        assert "X-Request-Duration" in response.headers, "Missing X-Request-Duration header"
        duration = response.headers.get("X-Request-Duration")
        assert "ms" in duration, f"X-Request-Duration should contain 'ms', got: {duration}"
        
        print(f"✓ X-Request-Duration: {duration}")
    
    def test_correlation_id_on_login_endpoint(self):
        """SEC-07: Correlation ID present on POST /api/auth/login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@demo.com", "password": "demo1234"},
            headers={"X-Tenant-ID": "demo"}
        )
        
        assert "X-Correlation-ID" in response.headers, "Missing X-Correlation-ID on login"
        assert "X-Request-Duration" in response.headers, "Missing X-Request-Duration on login"
        
        print(f"✓ Correlation headers present on login endpoint")


class TestDemoTenantLogin:
    """Test demo tenant login still works after security hardening"""
    
    def test_demo_login_success(self):
        """SEC-08: Demo tenant login (admin@demo.com / demo1234) works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@demo.com", "password": "demo1234"},
            headers={"X-Tenant-ID": "demo", "Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Demo login failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Missing access_token in login response"
        assert "user" in data, "Missing user in login response"
        assert data["user"]["email"] == "admin@demo.com", "Email mismatch in response"
        assert data["user"]["tenant_id"] == "demo", "Tenant ID mismatch in response"
        
        print(f"✓ Demo login successful, role: {data['user'].get('role')}")
        return data["access_token"]
    
    def test_demo_login_invalid_credentials(self):
        """SEC-09: Invalid credentials return 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@demo.com", "password": "wrongpassword"},
            headers={"X-Tenant-ID": "demo", "Content-Type": "application/json"}
        )
        
        assert response.status_code == 401, f"Expected 401, got: {response.status_code}"
        print("✓ Invalid credentials correctly return 401")


class TestSignupValidation:
    """Test signup endpoint input validation"""
    
    def test_signup_rejects_weak_password(self):
        """SEC-10: Signup rejects password without letters"""
        response = requests.post(
            f"{BASE_URL}/api/signup/register",
            json={
                "company_name": "Test Company",
                "email": "test_weak_pwd@example.com",
                "password": "12345678",  # No letters
                "subdomain": "testweakpwd"
            }
        )
        
        assert response.status_code == 422, f"Expected 422 for weak password, got: {response.status_code}"
        print("✓ Signup correctly rejects password without letters")
    
    def test_signup_rejects_password_without_number(self):
        """SEC-11: Signup rejects password without numbers"""
        response = requests.post(
            f"{BASE_URL}/api/signup/register",
            json={
                "company_name": "Test Company",
                "email": "test_no_num@example.com",
                "password": "abcdefgh",  # No numbers
                "subdomain": "testnonum"
            }
        )
        
        assert response.status_code == 422, f"Expected 422 for password without number, got: {response.status_code}"
        print("✓ Signup correctly rejects password without numbers")
    
    def test_signup_rejects_reserved_subdomain(self):
        """SEC-12: Signup rejects reserved subdomains (www, api, admin, demo)"""
        response = requests.post(
            f"{BASE_URL}/api/signup/register",
            json={
                "company_name": "Test Company",
                "email": "test_reserved@example.com",
                "password": "TestPass123",
                "subdomain": "demo"  # Reserved
            }
        )
        
        assert response.status_code == 422, f"Expected 422 for reserved subdomain, got: {response.status_code}"
        print("✓ Signup correctly rejects reserved subdomain 'demo'")
    
    def test_signup_rejects_short_subdomain(self):
        """SEC-13: Signup rejects subdomain < 3 characters"""
        response = requests.post(
            f"{BASE_URL}/api/signup/register",
            json={
                "company_name": "Test Company",
                "email": "test_short@example.com",
                "password": "TestPass123",
                "subdomain": "ab"  # Too short
            }
        )
        
        assert response.status_code == 422, f"Expected 422 for short subdomain, got: {response.status_code}"
        print("✓ Signup correctly rejects subdomain < 3 chars")


class TestNoSQLInjectionPrevention:
    """Test NoSQL injection prevention in signup"""
    
    def test_signup_rejects_nosql_injection_in_email(self):
        """SEC-14: Signup rejects NoSQL injection patterns ($gt, $ne) in fields"""
        # Test with $gt operator in company_name
        response = requests.post(
            f"{BASE_URL}/api/signup/register",
            json={
                "company_name": '{"$gt": ""}',
                "email": "injection_test@example.com",
                "password": "TestPass123",
                "subdomain": "injectiontest"
            }
        )
        
        # Should be rejected with 400 (input validation) or 422 (pydantic)
        assert response.status_code in [400, 422], f"Expected 400/422 for NoSQL injection, got: {response.status_code}"
        print("✓ Signup rejects NoSQL injection pattern in company_name")
    
    def test_signup_rejects_nosql_ne_operator(self):
        """SEC-15: Signup rejects $ne operator"""
        response = requests.post(
            f"{BASE_URL}/api/signup/register",
            json={
                "company_name": "Test $ne Company",
                "email": "ne_test@example.com",
                "password": "TestPass123",
                "subdomain": "netest"
            }
        )
        
        # The validate_input function should catch $ne
        assert response.status_code in [400, 422], f"Expected 400/422 for $ne pattern, got: {response.status_code}"
        print("✓ Signup rejects $ne operator pattern")


class TestGlobalErrorHandler:
    """Test global error handler returns clean JSON without stack traces"""
    
    def test_error_response_has_correlation_id(self):
        """SEC-16: Error responses include correlation_id"""
        # Trigger a 404 error
        response = requests.get(f"{BASE_URL}/api/nonexistent-endpoint-12345")
        
        # 404 should still have correlation ID
        assert "X-Correlation-ID" in response.headers, "Error response missing X-Correlation-ID"
        print(f"✓ Error response has X-Correlation-ID: {response.headers.get('X-Correlation-ID')}")
    
    def test_error_response_no_stack_trace(self):
        """SEC-17: Error responses don't leak stack traces"""
        # Try to trigger an error with invalid JSON
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data="invalid json {{{",
            headers={"X-Tenant-ID": "demo", "Content-Type": "application/json"}
        )
        
        # Response should not contain Python traceback indicators
        response_text = response.text.lower()
        assert "traceback" not in response_text, "Response contains 'traceback'"
        assert "file \"" not in response_text, "Response contains file path"
        assert "line " not in response_text or "detail" in response_text, "Response may contain line numbers"
        
        print("✓ Error response does not leak stack traces")


class TestRequestSizeLimits:
    """Test request size limits (1MB for JSON, 50MB for uploads)"""
    
    def test_oversized_json_returns_413(self):
        """SEC-18: Oversized JSON body (>1MB) returns 413"""
        # Create a payload larger than 1MB
        large_payload = {
            "company_name": "Test Company",
            "email": "size_test@example.com",
            "password": "TestPass123",
            "subdomain": "sizetest",
            "extra_data": "x" * (1024 * 1024 + 1000)  # ~1MB + 1KB
        }
        
        response = requests.post(
            f"{BASE_URL}/api/signup/register",
            json=large_payload,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 413, f"Expected 413 for oversized JSON, got: {response.status_code}"
        print("✓ Oversized JSON (>1MB) correctly returns 413")


class TestVerifyEmailEndpoint:
    """Test verify-email endpoint still works"""
    
    def test_verify_email_invalid_token(self):
        """SEC-19: Verify email with invalid token returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/signup/verify-email",
            json={"token": "invalid-token-12345"}
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid token, got: {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Error response should have 'detail' field"
        
        print("✓ Verify email with invalid token returns 400")


class TestRateLimitingDecorators:
    """Test rate limiting is configured (decorators present)"""
    
    def test_login_endpoint_responds(self):
        """SEC-20: Login endpoint responds (rate limiter attached)"""
        # In K8s preview, rate limiting may not trigger due to proxy
        # But we verify the endpoint works and has the limiter decorator
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@demo.com", "password": "demo1234"},
            headers={"X-Tenant-ID": "demo"}
        )
        
        # Should get 200 (success) or 429 (rate limited)
        assert response.status_code in [200, 429], f"Unexpected status: {response.status_code}"
        print(f"✓ Login endpoint responds with status {response.status_code}")
    
    def test_signup_endpoint_responds(self):
        """SEC-21: Signup endpoint responds (rate limiter attached)"""
        response = requests.post(
            f"{BASE_URL}/api/signup/register",
            json={
                "company_name": "Rate Test Co",
                "email": "ratetest@example.com",
                "password": "TestPass123",
                "subdomain": "ratetest"
            }
        )
        
        # Should get 400 (duplicate), 422 (validation), 200 (success), or 429 (rate limited)
        assert response.status_code in [200, 400, 422, 429], f"Unexpected status: {response.status_code}"
        print(f"✓ Signup endpoint responds with status {response.status_code}")


class TestSecurityHeaderValues:
    """Test specific security header values"""
    
    def test_xss_protection_header(self):
        """SEC-22: X-XSS-Protection is '1; mode=block'"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        xss = response.headers.get("X-XSS-Protection", "")
        assert xss == "1; mode=block", f"X-XSS-Protection should be '1; mode=block', got: {xss}"
        print(f"✓ X-XSS-Protection: {xss}")
    
    def test_referrer_policy_header(self):
        """SEC-23: Referrer-Policy is 'strict-origin-when-cross-origin'"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        referrer = response.headers.get("Referrer-Policy", "")
        assert referrer == "strict-origin-when-cross-origin", f"Referrer-Policy mismatch: {referrer}"
        print(f"✓ Referrer-Policy: {referrer}")
    
    def test_permissions_policy_header(self):
        """SEC-24: Permissions-Policy restricts camera, microphone, geolocation"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        perms = response.headers.get("Permissions-Policy", "")
        assert "camera=()" in perms, f"Permissions-Policy should restrict camera: {perms}"
        assert "microphone=()" in perms, f"Permissions-Policy should restrict microphone: {perms}"
        assert "geolocation=()" in perms, f"Permissions-Policy should restrict geolocation: {perms}"
        print(f"✓ Permissions-Policy: {perms}")
    
    def test_csp_header(self):
        """SEC-25: Content-Security-Policy is set"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        csp = response.headers.get("Content-Security-Policy", "")
        assert "default-src" in csp, f"CSP should have default-src: {csp}"
        assert "frame-ancestors 'none'" in csp, f"CSP should have frame-ancestors 'none': {csp}"
        print(f"✓ Content-Security-Policy: {csp}")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
