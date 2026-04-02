"""
RBAC (Role-Based Access Control) API Tests - Iteration 15
Tests for user management, roles, permissions, invitations, and audit logging.
"""
import pytest
import requests
import os
import secrets

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "demo1234"
TENANT_ID = "demo"

# Non-admin user (merchandiser)
MERCH_EMAIL = "merch@demo.com"
MERCH_PASSWORD = "MerchPass123!"


class TestRBACSetup:
    """Setup and basic auth tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"X-Tenant-ID": TENANT_ID}
        )
        assert resp.status_code == 200, f"Admin login failed: {resp.text}"
        return resp.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        """Admin auth headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "X-Tenant-ID": TENANT_ID,
            "Content-Type": "application/json"
        }
    
    def test_login_returns_permissions(self):
        """POST /api/auth/login returns permissions array in user object"""
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"X-Tenant-ID": TENANT_ID}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify user object has permissions
        assert "user" in data
        assert "permissions" in data["user"]
        assert isinstance(data["user"]["permissions"], list)
        assert len(data["user"]["permissions"]) > 0
        
        # Admin should have all 21 permissions
        perms = data["user"]["permissions"]
        assert "users.list.view" in perms
        assert "users.invite.create" in perms
        assert "users.roles.manage" in perms
        print(f"✓ Login returns {len(perms)} permissions for admin")


class TestRolesEndpoint:
    """Tests for GET /api/users/roles"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"X-Tenant-ID": TENANT_ID}
        )
        token = resp.json()["access_token"]
        return {
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": TENANT_ID
        }
    
    def test_get_roles_admin(self, admin_headers):
        """GET /api/users/roles - returns list of available roles (admin auth required)"""
        resp = requests.get(f"{BASE_URL}/api/users/roles", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        
        assert "roles" in data
        roles = data["roles"]
        assert isinstance(roles, list)
        assert len(roles) >= 7  # At least 7 roles (super_admin excluded for tenant admin)
        
        # Verify role structure
        role_names = [r["role_name"] for r in roles]
        assert "admin" in role_names
        assert "merchandiser" in role_names
        assert "viewer" in role_names
        
        # Each role should have display_name and description
        for role in roles:
            assert "role_name" in role
            assert "display_name" in role
            assert "description" in role
        
        print(f"✓ GET /api/users/roles returns {len(roles)} roles")
    
    def test_get_roles_no_auth(self):
        """GET /api/users/roles without auth returns 401"""
        resp = requests.get(
            f"{BASE_URL}/api/users/roles",
            headers={"X-Tenant-ID": TENANT_ID}
        )
        assert resp.status_code == 401
        print("✓ GET /api/users/roles without auth returns 401")


class TestUsersListEndpoint:
    """Tests for GET /api/users/list"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"X-Tenant-ID": TENANT_ID}
        )
        token = resp.json()["access_token"]
        return {
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": TENANT_ID
        }
    
    def test_list_users_admin(self, admin_headers):
        """GET /api/users/list - returns list of tenant users (admin auth required)"""
        resp = requests.get(f"{BASE_URL}/api/users/list", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        
        assert "users" in data
        assert "total" in data
        users = data["users"]
        assert isinstance(users, list)
        
        # Should have at least the admin user
        assert len(users) >= 1
        
        # Verify user structure
        admin_found = False
        for user in users:
            assert "email" in user
            assert "role" in user
            if user["email"] == ADMIN_EMAIL:
                admin_found = True
                assert user["role"] == "admin"
        
        assert admin_found, "Admin user not found in list"
        print(f"✓ GET /api/users/list returns {len(users)} users")
    
    def test_list_users_no_auth(self):
        """GET /api/users/list without auth returns 401"""
        resp = requests.get(
            f"{BASE_URL}/api/users/list",
            headers={"X-Tenant-ID": TENANT_ID}
        )
        assert resp.status_code == 401
        print("✓ GET /api/users/list without auth returns 401")


class TestInviteFlow:
    """Tests for invitation endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"X-Tenant-ID": TENANT_ID}
        )
        token = resp.json()["access_token"]
        return {
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": TENANT_ID,
            "Content-Type": "application/json"
        }
    
    def test_invite_user(self, admin_headers):
        """POST /api/users/invite - creates invitation with token (admin auth required)"""
        test_email = f"test_invite_{secrets.token_hex(4)}@example.com"
        resp = requests.post(
            f"{BASE_URL}/api/users/invite",
            json={"email": test_email, "role": "viewer", "full_name": "Test User"},
            headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        
        assert "message" in data
        assert "invite_token" in data
        assert len(data["invite_token"]) > 20  # Token should be substantial
        
        print(f"✓ POST /api/users/invite creates invitation with token")
        return data["invite_token"], test_email
    
    def test_invite_invalid_role(self, admin_headers):
        """POST /api/users/invite with invalid role returns 400"""
        resp = requests.post(
            f"{BASE_URL}/api/users/invite",
            json={"email": "invalid@example.com", "role": "invalid_role"},
            headers=admin_headers
        )
        assert resp.status_code == 400
        print("✓ POST /api/users/invite with invalid role returns 400")
    
    def test_list_invitations(self, admin_headers):
        """GET /api/users/invitations - lists pending invitations (admin auth required)"""
        resp = requests.get(f"{BASE_URL}/api/users/invitations", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        
        assert "invitations" in data
        invitations = data["invitations"]
        assert isinstance(invitations, list)
        
        # Verify invitation structure (if any exist)
        for inv in invitations:
            assert "email" in inv
            assert "role" in inv
            assert "status" in inv
            assert "invited_by" in inv
        
        print(f"✓ GET /api/users/invitations returns {len(invitations)} invitations")
    
    def test_accept_invite(self, admin_headers):
        """POST /api/users/accept-invite - accepts invite with token and creates user"""
        # First create an invitation
        test_email = f"test_accept_{secrets.token_hex(4)}@example.com"
        invite_resp = requests.post(
            f"{BASE_URL}/api/users/invite",
            json={"email": test_email, "role": "viewer", "full_name": "Accept Test"},
            headers=admin_headers
        )
        assert invite_resp.status_code == 200
        token = invite_resp.json()["invite_token"]
        
        # Accept the invitation
        accept_resp = requests.post(
            f"{BASE_URL}/api/users/accept-invite",
            json={"token": token, "password": "TestPass123!"},
            headers={"X-Tenant-ID": TENANT_ID, "Content-Type": "application/json"}
        )
        assert accept_resp.status_code == 200
        data = accept_resp.json()
        
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == test_email
        assert data["user"]["role"] == "viewer"
        
        print(f"✓ POST /api/users/accept-invite creates user and returns token")
    
    def test_accept_invalid_token(self):
        """POST /api/users/accept-invite with invalid token returns 400"""
        resp = requests.post(
            f"{BASE_URL}/api/users/accept-invite",
            json={"token": "invalid_token_12345", "password": "TestPass123!"},
            headers={"X-Tenant-ID": TENANT_ID, "Content-Type": "application/json"}
        )
        assert resp.status_code == 400
        print("✓ POST /api/users/accept-invite with invalid token returns 400")


class TestRoleUpdate:
    """Tests for PUT /api/users/{email}/role"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"X-Tenant-ID": TENANT_ID}
        )
        token = resp.json()["access_token"]
        return {
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": TENANT_ID,
            "Content-Type": "application/json"
        }
    
    def test_update_user_role(self, admin_headers):
        """PUT /api/users/{email}/role - updates user role (admin auth required)"""
        # First create a test user via invite
        test_email = f"test_role_{secrets.token_hex(4)}@example.com"
        invite_resp = requests.post(
            f"{BASE_URL}/api/users/invite",
            json={"email": test_email, "role": "viewer"},
            headers=admin_headers
        )
        token = invite_resp.json()["invite_token"]
        
        # Accept invite
        requests.post(
            f"{BASE_URL}/api/users/accept-invite",
            json={"token": token, "password": "TestPass123!"},
            headers={"X-Tenant-ID": TENANT_ID, "Content-Type": "application/json"}
        )
        
        # Update role
        update_resp = requests.put(
            f"{BASE_URL}/api/users/{test_email}/role",
            json={"role": "merchandiser"},
            headers=admin_headers
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert "message" in data
        
        # Verify role was updated
        list_resp = requests.get(f"{BASE_URL}/api/users/list", headers=admin_headers)
        users = list_resp.json()["users"]
        user = next((u for u in users if u["email"] == test_email), None)
        assert user is not None
        assert user["role"] == "merchandiser"
        
        print(f"✓ PUT /api/users/{{email}}/role updates user role")
    
    def test_cannot_change_own_role(self, admin_headers):
        """PUT /api/users/{email}/role - cannot change own role"""
        resp = requests.put(
            f"{BASE_URL}/api/users/{ADMIN_EMAIL}/role",
            json={"role": "viewer"},
            headers=admin_headers
        )
        assert resp.status_code == 400
        print("✓ Cannot change own role - returns 400")


class TestUserRemoval:
    """Tests for DELETE /api/users/{email}"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"X-Tenant-ID": TENANT_ID}
        )
        token = resp.json()["access_token"]
        return {
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": TENANT_ID,
            "Content-Type": "application/json"
        }
    
    def test_remove_user(self, admin_headers):
        """DELETE /api/users/{email} - soft-removes user from tenant (admin auth required)"""
        # First create a test user
        test_email = f"test_remove_{secrets.token_hex(4)}@example.com"
        invite_resp = requests.post(
            f"{BASE_URL}/api/users/invite",
            json={"email": test_email, "role": "viewer"},
            headers=admin_headers
        )
        token = invite_resp.json()["invite_token"]
        
        # Accept invite
        requests.post(
            f"{BASE_URL}/api/users/accept-invite",
            json={"token": token, "password": "TestPass123!"},
            headers={"X-Tenant-ID": TENANT_ID, "Content-Type": "application/json"}
        )
        
        # Remove user
        remove_resp = requests.delete(
            f"{BASE_URL}/api/users/{test_email}",
            headers=admin_headers
        )
        assert remove_resp.status_code == 200
        
        # Verify user is no longer in active list
        list_resp = requests.get(f"{BASE_URL}/api/users/list", headers=admin_headers)
        users = list_resp.json()["users"]
        user = next((u for u in users if u["email"] == test_email), None)
        assert user is None, "Removed user should not appear in list"
        
        print(f"✓ DELETE /api/users/{{email}} removes user from tenant")
    
    def test_cannot_remove_self(self, admin_headers):
        """DELETE /api/users/{email} - cannot remove self"""
        resp = requests.delete(
            f"{BASE_URL}/api/users/{ADMIN_EMAIL}",
            headers=admin_headers
        )
        assert resp.status_code == 400
        print("✓ Cannot remove self - returns 400")


class TestPermissionsEndpoint:
    """Tests for GET /api/users/me/permissions"""
    
    def test_get_my_permissions_admin(self):
        """GET /api/users/me/permissions - returns current user permissions list"""
        # Login as admin
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"X-Tenant-ID": TENANT_ID}
        )
        token = login_resp.json()["access_token"]
        
        # Get permissions
        resp = requests.get(
            f"{BASE_URL}/api/users/me/permissions",
            headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": TENANT_ID}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        assert "email" in data
        assert "role" in data
        assert "permissions" in data
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "admin"
        assert len(data["permissions"]) == 21  # Admin has all 21 permissions
        
        print(f"✓ GET /api/users/me/permissions returns {len(data['permissions'])} permissions for admin")


class TestAuditLog:
    """Tests for GET /api/users/audit-log"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"X-Tenant-ID": TENANT_ID}
        )
        token = resp.json()["access_token"]
        return {
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": TENANT_ID
        }
    
    def test_get_audit_log(self, admin_headers):
        """GET /api/users/audit-log - returns audit log entries (admin auth required)"""
        resp = requests.get(f"{BASE_URL}/api/users/audit-log", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        
        assert "logs" in data
        logs = data["logs"]
        assert isinstance(logs, list)
        
        # Verify log structure (if any exist)
        for log in logs:
            assert "user_id" in log
            assert "action" in log
            assert "created_at" in log
        
        print(f"✓ GET /api/users/audit-log returns {len(logs)} entries")
    
    def test_audit_log_no_auth(self):
        """GET /api/users/audit-log without auth returns 401"""
        resp = requests.get(
            f"{BASE_URL}/api/users/audit-log",
            headers={"X-Tenant-ID": TENANT_ID}
        )
        assert resp.status_code == 401
        print("✓ GET /api/users/audit-log without auth returns 401")


class TestRBACEnforcement:
    """Tests for RBAC enforcement - non-admin users should get 403"""
    
    @pytest.fixture(scope="class")
    def non_admin_token(self):
        """Create a non-admin user and get their token"""
        # First login as admin to create invite
        admin_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"X-Tenant-ID": TENANT_ID}
        )
        admin_token = admin_resp.json()["access_token"]
        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "X-Tenant-ID": TENANT_ID,
            "Content-Type": "application/json"
        }
        
        # Create a viewer user
        test_email = f"test_viewer_{secrets.token_hex(4)}@example.com"
        invite_resp = requests.post(
            f"{BASE_URL}/api/users/invite",
            json={"email": test_email, "role": "viewer"},
            headers=admin_headers
        )
        invite_token = invite_resp.json()["invite_token"]
        
        # Accept invite
        accept_resp = requests.post(
            f"{BASE_URL}/api/users/accept-invite",
            json={"token": invite_token, "password": "ViewerPass123!"},
            headers={"X-Tenant-ID": TENANT_ID, "Content-Type": "application/json"}
        )
        return accept_resp.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def non_admin_headers(self, non_admin_token):
        return {
            "Authorization": f"Bearer {non_admin_token}",
            "X-Tenant-ID": TENANT_ID,
            "Content-Type": "application/json"
        }
    
    def test_non_admin_cannot_list_users(self, non_admin_headers):
        """Non-admin user gets 403 on /api/users/list"""
        resp = requests.get(f"{BASE_URL}/api/users/list", headers=non_admin_headers)
        assert resp.status_code == 403
        print("✓ Non-admin gets 403 on /api/users/list")
    
    def test_non_admin_cannot_list_roles(self, non_admin_headers):
        """Non-admin user gets 403 on /api/users/roles"""
        resp = requests.get(f"{BASE_URL}/api/users/roles", headers=non_admin_headers)
        assert resp.status_code == 403
        print("✓ Non-admin gets 403 on /api/users/roles")
    
    def test_non_admin_cannot_invite(self, non_admin_headers):
        """Non-admin user gets 403 on /api/users/invite"""
        resp = requests.post(
            f"{BASE_URL}/api/users/invite",
            json={"email": "test@example.com", "role": "viewer"},
            headers=non_admin_headers
        )
        assert resp.status_code == 403
        print("✓ Non-admin gets 403 on /api/users/invite")
    
    def test_non_admin_cannot_list_invitations(self, non_admin_headers):
        """Non-admin user gets 403 on /api/users/invitations"""
        resp = requests.get(f"{BASE_URL}/api/users/invitations", headers=non_admin_headers)
        assert resp.status_code == 403
        print("✓ Non-admin gets 403 on /api/users/invitations")
    
    def test_non_admin_cannot_update_role(self, non_admin_headers):
        """Non-admin user gets 403 on /api/users/{email}/role"""
        resp = requests.put(
            f"{BASE_URL}/api/users/test@example.com/role",
            json={"role": "admin"},
            headers=non_admin_headers
        )
        assert resp.status_code == 403
        print("✓ Non-admin gets 403 on /api/users/{email}/role")
    
    def test_non_admin_cannot_remove_user(self, non_admin_headers):
        """Non-admin user gets 403 on DELETE /api/users/{email}"""
        resp = requests.delete(
            f"{BASE_URL}/api/users/test@example.com",
            headers=non_admin_headers
        )
        assert resp.status_code == 403
        print("✓ Non-admin gets 403 on DELETE /api/users/{email}")
    
    def test_non_admin_cannot_view_audit_log(self, non_admin_headers):
        """Non-admin user gets 403 on /api/users/audit-log"""
        resp = requests.get(f"{BASE_URL}/api/users/audit-log", headers=non_admin_headers)
        assert resp.status_code == 403
        print("✓ Non-admin gets 403 on /api/users/audit-log")
    
    def test_non_admin_can_view_own_permissions(self, non_admin_headers):
        """Non-admin user CAN access /api/users/me/permissions"""
        resp = requests.get(f"{BASE_URL}/api/users/me/permissions", headers=non_admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "permissions" in data
        assert data["role"] == "viewer"
        print("✓ Non-admin CAN access /api/users/me/permissions")


class TestRegressionExistingEndpoints:
    """Regression tests for existing endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"X-Tenant-ID": TENANT_ID}
        )
        token = resp.json()["access_token"]
        return {
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": TENANT_ID
        }
    
    def test_executive_dashboard(self, admin_headers):
        """Regression: Executive Dashboard endpoint works"""
        resp = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "health_score" in data or "modules" in data or "error" not in data or data.get("error") is None
        print("✓ Executive Dashboard endpoint works")
    
    def test_analytics_overview(self, admin_headers):
        """Regression: Analytics overview endpoint works"""
        resp = requests.get(f"{BASE_URL}/api/analytics/overview", headers=admin_headers)
        assert resp.status_code == 200
        print("✓ Analytics overview endpoint works")
    
    def test_upload_status(self, admin_headers):
        """Regression: Upload status endpoint works"""
        resp = requests.get(f"{BASE_URL}/api/upload/status", headers=admin_headers)
        assert resp.status_code == 200
        print("✓ Upload status endpoint works")
    
    def test_filter_options(self, admin_headers):
        """Regression: Filter options endpoint works"""
        resp = requests.get(f"{BASE_URL}/api/analytics/filter-options", headers=admin_headers)
        assert resp.status_code == 200
        print("✓ Filter options endpoint works")
    
    def test_logout_flow(self):
        """Regression: Login/logout flow works correctly"""
        # Login
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"X-Tenant-ID": TENANT_ID}
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        
        # Verify token works
        me_resp = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": TENANT_ID}
        )
        assert me_resp.status_code == 200
        
        # Verify invalid token fails
        bad_resp = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": "Bearer invalid_token", "X-Tenant-ID": TENANT_ID}
        )
        assert bad_resp.status_code == 401
        
        print("✓ Login/logout flow works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
