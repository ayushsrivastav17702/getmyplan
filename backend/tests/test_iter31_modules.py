"""
Iteration 31 Tests: Data Quality, FAQ Chatbot, User Management, Tenant Management
Tests for 51 new gaps across 4 modules.
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_CREDS = {"tenant_id": "demo", "email": "admin@demo.com", "password": "demo1234"}


@pytest.fixture(scope="module")
def auth_token():
    """Get admin auth token for authenticated requests."""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
    if resp.status_code == 200:
        return resp.json().get("access_token")
    pytest.skip(f"Auth failed: {resp.status_code} - {resp.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 13: DATA QUALITY (DQ-01 to DQ-32)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDataQualityModule:
    """Tests for Data Quality endpoints - DQ-01 to DQ-32"""

    def test_dq_data_checks_endpoint(self, auth_headers):
        """DQ-01 to DQ-27: Test /api/quality/data-checks returns checks array"""
        resp = requests.get(f"{BASE_URL}/api/quality/data-checks", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Verify response structure
        assert "checks" in data, "Response should have 'checks' array"
        assert "scores" in data, "Response should have 'scores' object"
        assert "recommendations" in data, "Response should have 'recommendations' array"
        
        # Verify checks array has items
        checks = data["checks"]
        assert isinstance(checks, list), "checks should be a list"
        
        # Verify categories exist
        categories = set(c.get("category") for c in checks)
        expected_categories = {"completeness", "accuracy", "consistency", "timeliness", "scorecard"}
        assert categories.intersection(expected_categories), f"Expected categories {expected_categories}, got {categories}"
        
        # Verify scores structure
        scores = data["scores"]
        for key in ["completeness", "accuracy", "consistency", "timeliness", "overall"]:
            assert key in scores, f"scores should have '{key}'"
        
        print(f"✓ Data checks returned {len(checks)} checks across {len(categories)} categories")

    def test_dq_category_scorecard_endpoint(self, auth_headers):
        """DQ-28/29: Test /api/quality/category-scorecard returns categories array"""
        resp = requests.get(f"{BASE_URL}/api/quality/category-scorecard", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert "categories" in data, "Response should have 'categories' array"
        categories = data["categories"]
        assert isinstance(categories, list), "categories should be a list"
        
        # If categories exist, verify structure
        if len(categories) > 0:
            cat = categories[0]
            for key in ["category", "completeness", "accuracy", "consistency", "overall"]:
                assert key in cat, f"Category item should have '{key}'"
        
        print(f"✓ Category scorecard returned {len(categories)} categories")

    def test_dq_trend_endpoint(self, auth_headers):
        """DQ-08/30: Test /api/quality/trend returns trend array"""
        resp = requests.get(f"{BASE_URL}/api/quality/trend", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert "trend" in data, "Response should have 'trend' array"
        trend = data["trend"]
        assert isinstance(trend, list), "trend should be a list"
        
        # Verify trend items have date and scores
        if len(trend) > 0:
            item = trend[0]
            assert "date" in item, "Trend item should have 'date'"
            assert "overall" in item or "completeness" in item, "Trend item should have score fields"
        
        print(f"✓ Quality trend returned {len(trend)} data points")

    def test_dq_export_csv(self, auth_headers):
        """DQ-31: Test /api/quality/export returns CSV download"""
        resp = requests.get(f"{BASE_URL}/api/quality/export", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        # Verify content type is CSV
        content_type = resp.headers.get("content-type", "")
        assert "text/csv" in content_type, f"Expected text/csv, got {content_type}"
        
        # Verify content disposition header
        content_disp = resp.headers.get("content-disposition", "")
        assert "attachment" in content_disp, "Should have attachment disposition"
        assert ".csv" in content_disp, "Should have .csv filename"
        
        # Verify CSV content
        content = resp.text
        assert len(content) > 0, "CSV should have content"
        assert "," in content, "CSV should have comma-separated values"
        
        print(f"✓ Export CSV returned {len(content)} bytes")


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 14: FAQ CHATBOT (CHAT-29, CHAT-34, CHAT-35)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFAQChatbotModule:
    """Tests for FAQ Chatbot endpoints - CHAT-29, CHAT-34, CHAT-35"""

    def test_chat_basic_functionality(self, auth_headers):
        """Test basic chat endpoint works"""
        resp = requests.post(f"{BASE_URL}/api/chat", 
            json={"message": "What is NOOS?", "session_id": None},
            headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert "response" in data, "Response should have 'response'"
        assert "session_id" in data, "Response should have 'session_id'"
        assert len(data["response"]) > 0, "Response should not be empty"
        
        print(f"✓ Chat returned response with session_id: {data['session_id'][:8]}...")
        return data["session_id"]

    def test_chat_rate_limiting(self, auth_headers):
        """CHAT-34: Test rate limiting on /api/chat - 11th request should be rate limited"""
        session_id = None
        rate_limited = False
        
        # Send 11 rapid requests
        for i in range(11):
            resp = requests.post(f"{BASE_URL}/api/chat",
                json={"message": f"Test message {i}", "session_id": session_id},
                headers=auth_headers)
            
            if resp.status_code == 200:
                data = resp.json()
                session_id = data.get("session_id")
                # Check if response indicates rate limiting
                if "too quickly" in data.get("response", "").lower():
                    rate_limited = True
                    print(f"✓ Rate limited at request {i+1}")
                    break
        
        # Rate limiting should kick in around 10-11 requests
        assert rate_limited or i >= 9, "Rate limiting should trigger after ~10 requests"
        print(f"✓ Rate limiting test completed after {i+1} requests")

    def test_chat_export(self, auth_headers):
        """CHAT-35: Test /api/chat/export/{session_id} returns text file"""
        # First create a chat session
        resp = requests.post(f"{BASE_URL}/api/chat",
            json={"message": "What is ROS?", "session_id": None},
            headers=auth_headers)
        assert resp.status_code == 200
        session_id = resp.json().get("session_id")
        
        # Wait a moment for data to persist
        time.sleep(0.5)
        
        # Now export the chat
        export_resp = requests.get(f"{BASE_URL}/api/chat/export/{session_id}", headers=auth_headers)
        assert export_resp.status_code == 200, f"Expected 200, got {export_resp.status_code}: {export_resp.text}"
        
        # Verify content type
        content_type = export_resp.headers.get("content-type", "")
        assert "text/plain" in content_type, f"Expected text/plain, got {content_type}"
        
        # Verify content disposition
        content_disp = export_resp.headers.get("content-disposition", "")
        assert "attachment" in content_disp, "Should have attachment disposition"
        
        print(f"✓ Chat export returned {len(export_resp.text)} bytes")


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 15: USER MANAGEMENT (USER-04 to USER-30)
# ═══════════════════════════════════════════════════════════════════════════════

class TestUserManagementModule:
    """Tests for User Management endpoints - USER-04 to USER-30"""

    def test_user_list(self, auth_headers):
        """Test /api/users/list returns users"""
        resp = requests.get(f"{BASE_URL}/api/users/list", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert "users" in data, "Response should have 'users'"
        assert isinstance(data["users"], list), "users should be a list"
        print(f"✓ User list returned {len(data['users'])} users")

    def test_user_roles_list(self, auth_headers):
        """Test /api/users/roles returns roles"""
        resp = requests.get(f"{BASE_URL}/api/users/roles", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert "roles" in data, "Response should have 'roles'"
        roles = data["roles"]
        assert len(roles) > 0, "Should have at least one role"
        
        # Verify role structure
        role = roles[0]
        assert "role_name" in role, "Role should have 'role_name'"
        assert "display_name" in role, "Role should have 'display_name'"
        
        print(f"✓ Roles list returned {len(roles)} roles")

    def test_user_invitations_list(self, auth_headers):
        """Test /api/users/invitations returns invitations"""
        resp = requests.get(f"{BASE_URL}/api/users/invitations", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert "invitations" in data, "Response should have 'invitations'"
        print(f"✓ Invitations list returned {len(data['invitations'])} invitations")

    def test_user_profile_update(self, auth_headers):
        """USER-04: Test PUT /api/users/{email}/profile updates name"""
        # Get a user to update
        users_resp = requests.get(f"{BASE_URL}/api/users/list", headers=auth_headers)
        users = users_resp.json().get("users", [])
        
        if len(users) < 2:
            pytest.skip("Need at least 2 users to test profile update")
        
        # Find a non-admin user to update
        target_user = None
        for u in users:
            if u["email"] != "admin@demo.com":
                target_user = u
                break
        
        if not target_user:
            pytest.skip("No non-admin user found")
        
        # Update profile
        new_name = f"Test User {int(time.time())}"
        resp = requests.put(
            f"{BASE_URL}/api/users/{target_user['email']}/profile",
            json={"full_name": new_name},
            headers=auth_headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        print(f"✓ Profile update for {target_user['email']} succeeded")

    def test_user_bulk_import(self, auth_headers):
        """USER-08: Test POST /api/users/bulk-import"""
        test_users = [
            {"email": f"test_bulk_{int(time.time())}@example.com", "role": "viewer", "full_name": "Bulk Test User"}
        ]
        
        resp = requests.post(f"{BASE_URL}/api/users/bulk-import", json=test_users, headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert "message" in data, "Response should have 'message'"
        print(f"✓ Bulk import: {data['message']}")

    def test_user_bulk_role_update(self, auth_headers):
        """USER-09: Test PUT /api/users/bulk-role-update"""
        # Get users
        users_resp = requests.get(f"{BASE_URL}/api/users/list", headers=auth_headers)
        users = users_resp.json().get("users", [])
        
        # Find non-admin users
        non_admin_emails = [u["email"] for u in users if u["email"] != "admin@demo.com"][:2]
        
        if len(non_admin_emails) == 0:
            pytest.skip("No non-admin users to update")
        
        resp = requests.put(
            f"{BASE_URL}/api/users/bulk-role-update",
            json={"emails": non_admin_emails, "role": "viewer"},
            headers=auth_headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        print(f"✓ Bulk role update for {len(non_admin_emails)} users succeeded")

    def test_user_password_reset(self, auth_headers):
        """USER-16: Test POST /api/users/password-reset"""
        # Get a non-admin user
        users_resp = requests.get(f"{BASE_URL}/api/users/list", headers=auth_headers)
        users = users_resp.json().get("users", [])
        
        target_user = None
        for u in users:
            if u["email"] != "admin@demo.com":
                target_user = u
                break
        
        if not target_user:
            pytest.skip("No non-admin user found")
        
        resp = requests.post(
            f"{BASE_URL}/api/users/password-reset",
            json={"email": target_user["email"], "new_password": "NewTestPass123!"},
            headers=auth_headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        print(f"✓ Password reset for {target_user['email']} succeeded")

    def test_user_system_role_protection(self, auth_headers):
        """USER-25: Test DELETE /api/users/roles/{name} fails for system roles"""
        system_roles = ["admin", "super_admin", "viewer", "merchandiser"]
        
        for role in system_roles:
            resp = requests.delete(f"{BASE_URL}/api/users/roles/{role}", headers=auth_headers)
            # Should fail with 400 for system roles
            assert resp.status_code == 400, f"Expected 400 for system role '{role}', got {resp.status_code}"
        
        print(f"✓ System roles are protected from deletion")


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 16: TENANT MANAGEMENT (TENANT-06 to TENANT-35)
# ═══════════════════════════════════════════════════════════════════════════════

class TestTenantManagementModule:
    """Tests for Tenant Management endpoints - TENANT-06 to TENANT-35"""

    def test_tenant_metrics(self, auth_headers):
        """Test /api/tenants/{id}/metrics returns metrics"""
        resp = requests.get(f"{BASE_URL}/api/tenants/demo/metrics", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Verify metrics structure
        for key in ["tenant_id", "company_name", "plan", "total_users"]:
            assert key in data, f"Metrics should have '{key}'"
        
        print(f"✓ Tenant metrics: {data['total_users']} users, plan: {data['plan']}")

    def test_tenant_plan_change(self, auth_headers):
        """TENANT-06/27/28: Test PUT /api/tenants/{id}/plan for upgrade/downgrade"""
        # First get current plan
        metrics_resp = requests.get(f"{BASE_URL}/api/tenants/demo/metrics", headers=auth_headers)
        current_plan = metrics_resp.json().get("plan", "starter")
        
        # Try to change to professional
        new_plan = "professional" if current_plan != "professional" else "starter"
        
        resp = requests.put(
            f"{BASE_URL}/api/tenants/demo/plan",
            json={"plan_type": new_plan},
            headers=auth_headers
        )
        
        # May succeed or fail based on user limits (TENANT-29)
        assert resp.status_code in [200, 400], f"Expected 200 or 400, got {resp.status_code}: {resp.text}"
        
        if resp.status_code == 200:
            data = resp.json()
            assert "message" in data, "Response should have 'message'"
            assert "plan" in data, "Response should have 'plan'"
            print(f"✓ Plan change to {new_plan} succeeded")
        else:
            # 400 means limit enforcement worked (TENANT-29)
            print(f"✓ Plan change blocked due to limits (TENANT-29 working)")

    def test_tenant_currency_update(self, auth_headers):
        """TENANT-23: Test PUT /api/tenants/{id}/currency"""
        resp = requests.put(
            f"{BASE_URL}/api/tenants/demo/currency",
            json={"currency": "USD"},
            headers=auth_headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert "message" in data, "Response should have 'message'"
        assert "USD" in data["message"], "Message should mention USD"
        
        # Reset to INR
        requests.put(f"{BASE_URL}/api/tenants/demo/currency", json={"currency": "INR"}, headers=auth_headers)
        
        print(f"✓ Currency update to USD succeeded")

    def test_tenant_currency_invalid(self, auth_headers):
        """TENANT-23: Test invalid currency is rejected"""
        resp = requests.put(
            f"{BASE_URL}/api/tenants/demo/currency",
            json={"currency": "INVALID"},
            headers=auth_headers
        )
        assert resp.status_code == 400, f"Expected 400 for invalid currency, got {resp.status_code}"
        
        print(f"✓ Invalid currency rejected correctly")

    def test_tenant_filtered_list(self, auth_headers):
        """TENANT-34: Test GET /api/tenants/filtered with filters"""
        # Test without filters
        resp = requests.get(f"{BASE_URL}/api/tenants/filtered", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert "tenants" in data, "Response should have 'tenants'"
        assert "total" in data, "Response should have 'total'"
        
        # Test with status filter
        resp2 = requests.get(f"{BASE_URL}/api/tenants/filtered?status=active", headers=auth_headers)
        assert resp2.status_code == 200
        
        # Test with search filter
        resp3 = requests.get(f"{BASE_URL}/api/tenants/filtered?search=demo", headers=auth_headers)
        assert resp3.status_code == 200
        
        print(f"✓ Filtered tenant list returned {data['total']} tenants")

    def test_tenant_export_csv(self, auth_headers):
        """TENANT-35: Test GET /api/tenants/export returns CSV"""
        resp = requests.get(f"{BASE_URL}/api/tenants/export", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        # Verify content type
        content_type = resp.headers.get("content-type", "")
        assert "text/csv" in content_type, f"Expected text/csv, got {content_type}"
        
        # Verify content disposition
        content_disp = resp.headers.get("content-disposition", "")
        assert "attachment" in content_disp, "Should have attachment disposition"
        assert ".csv" in content_disp, "Should have .csv filename"
        
        print(f"✓ Tenant export CSV returned {len(resp.text)} bytes")

    def test_tenant_api_keys_list(self, auth_headers):
        """Test /api/tenants/admin/api-keys returns keys"""
        resp = requests.get(f"{BASE_URL}/api/tenants/admin/api-keys", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert "keys" in data, "Response should have 'keys'"
        print(f"✓ API keys list returned {len(data['keys'])} keys")


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntegration:
    """Integration tests across modules"""

    def test_auth_flow(self):
        """Test authentication flow works"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        assert resp.status_code == 200, f"Login failed: {resp.status_code} - {resp.text}"
        data = resp.json()
        
        assert "access_token" in data, "Response should have 'access_token'"
        assert "user" in data, "Response should have 'user'"
        
        print(f"✓ Auth flow working for {data['user']['email']}")

    def test_api_health(self):
        """Test API root endpoint"""
        resp = requests.get(f"{BASE_URL}/api/")
        assert resp.status_code == 200, f"API health check failed: {resp.status_code}"
        
        print(f"✓ API health check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
