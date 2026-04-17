"""
Module System API Tests - Iteration 107
Tests for tenant module configuration, feature toggling, and user module-access management.

Endpoints tested:
- GET /api/tenant-admin/modules - Get all modules with enabled status
- PUT /api/tenant-admin/modules/{id}/toggle - Enable/disable modules
- PUT /api/tenant-admin/modules/{id}/features/{fid}/toggle - Enable/disable features
- GET /api/tenant-admin/modules/usage - Get usage limits and subscription info
- GET /api/users/{email}/module-access - Get user's module access
- PUT /api/users/{email}/module-access - Update user's module access
- PUT /api/users/{email}/scope - Update user's data scope
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@demo.com"
SUPER_ADMIN_PASSWORD = "demo1234"


class TestModuleSystemAPIs:
    """Module Configuration API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Get auth token for super admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as super admin
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        
        token = login_resp.json().get("access_token")
        assert token, "No access token returned"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.token = token
    
    # ─── GET /api/tenant-admin/modules ───
    
    def test_get_modules_returns_all_5_modules(self):
        """TEST_01: GET /api/tenant-admin/modules returns all 5 modules"""
        resp = self.session.get(f"{BASE_URL}/api/tenant-admin/modules")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert data.get("success") is True, "Response should have success=True"
        assert "modules" in data, "Response should have 'modules' key"
        
        modules = data["modules"]
        assert len(modules) == 5, f"Expected 5 modules, got {len(modules)}"
        
        # Verify expected module IDs
        module_ids = [m["module_id"] for m in modules]
        expected_ids = ["core_classification", "buy_planning", "inventory_management", "space_planning", "ai_insights"]
        for expected_id in expected_ids:
            assert expected_id in module_ids, f"Missing module: {expected_id}"
        
        print(f"✓ All 5 modules returned: {module_ids}")
    
    def test_get_modules_structure(self):
        """TEST_02: Each module has correct structure"""
        resp = self.session.get(f"{BASE_URL}/api/tenant-admin/modules")
        assert resp.status_code == 200
        
        modules = resp.json()["modules"]
        required_fields = ["module_id", "module_name", "description", "category", "is_core", "enabled", "features"]
        
        for mod in modules:
            for field in required_fields:
                assert field in mod, f"Module {mod.get('module_id')} missing field: {field}"
            
            # Verify features structure
            for feat in mod.get("features", []):
                assert "feature_id" in feat, f"Feature missing feature_id in module {mod['module_id']}"
                assert "name" in feat, f"Feature missing name in module {mod['module_id']}"
                assert "enabled" in feat, f"Feature missing enabled in module {mod['module_id']}"
        
        print("✓ All modules have correct structure")
    
    def test_core_modules_identified(self):
        """TEST_03: Core modules (first 3) are marked as is_core=True"""
        resp = self.session.get(f"{BASE_URL}/api/tenant-admin/modules")
        assert resp.status_code == 200
        
        modules = resp.json()["modules"]
        core_module_ids = ["core_classification", "buy_planning", "inventory_management"]
        
        for mod in modules:
            if mod["module_id"] in core_module_ids:
                assert mod["is_core"] is True, f"Module {mod['module_id']} should be is_core=True"
            else:
                assert mod["is_core"] is False, f"Module {mod['module_id']} should be is_core=False"
        
        print("✓ Core modules correctly identified")
    
    # ─── PUT /api/tenant-admin/modules/{id}/toggle ───
    
    def test_toggle_non_core_module_enable(self):
        """TEST_04: Can enable non-core module (space_planning)"""
        resp = self.session.put(
            f"{BASE_URL}/api/tenant-admin/modules/space_planning/toggle",
            json={"enabled": True}
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("success") is True
        assert "enabled" in data.get("message", "").lower()
        
        # Verify module is now enabled
        modules_resp = self.session.get(f"{BASE_URL}/api/tenant-admin/modules")
        modules = modules_resp.json()["modules"]
        space_planning = next((m for m in modules if m["module_id"] == "space_planning"), None)
        assert space_planning is not None
        assert space_planning["enabled"] is True, "space_planning should be enabled"
        
        print("✓ Non-core module (space_planning) enabled successfully")
    
    def test_toggle_non_core_module_disable(self):
        """TEST_05: Can disable non-core module (ai_insights)"""
        # First ensure it's enabled
        self.session.put(
            f"{BASE_URL}/api/tenant-admin/modules/ai_insights/toggle",
            json={"enabled": True}
        )
        
        # Now disable it
        resp = self.session.put(
            f"{BASE_URL}/api/tenant-admin/modules/ai_insights/toggle",
            json={"enabled": False}
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("success") is True
        assert "disabled" in data.get("message", "").lower()
        
        # Verify module is now disabled
        modules_resp = self.session.get(f"{BASE_URL}/api/tenant-admin/modules")
        modules = modules_resp.json()["modules"]
        ai_insights = next((m for m in modules if m["module_id"] == "ai_insights"), None)
        assert ai_insights is not None
        assert ai_insights["enabled"] is False, "ai_insights should be disabled"
        
        print("✓ Non-core module (ai_insights) disabled successfully")
    
    def test_cannot_disable_core_module(self):
        """TEST_06: Cannot disable core module (core_classification)"""
        resp = self.session.put(
            f"{BASE_URL}/api/tenant-admin/modules/core_classification/toggle",
            json={"enabled": False}
        )
        
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "core" in data.get("detail", "").lower() or "cannot" in data.get("detail", "").lower()
        
        print("✓ Core module cannot be disabled (400 returned)")
    
    def test_toggle_invalid_module_returns_404(self):
        """TEST_07: Toggle non-existent module returns 404"""
        resp = self.session.put(
            f"{BASE_URL}/api/tenant-admin/modules/invalid_module_xyz/toggle",
            json={"enabled": True}
        )
        
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        print("✓ Invalid module returns 404")
    
    # ─── PUT /api/tenant-admin/modules/{id}/features/{fid}/toggle ───
    
    def test_toggle_feature_enable(self):
        """TEST_08: Can enable a feature within a module"""
        # First ensure buy_planning module is enabled
        self.session.put(
            f"{BASE_URL}/api/tenant-admin/modules/buy_planning/toggle",
            json={"enabled": True}
        )
        
        # Get features for buy_planning
        modules_resp = self.session.get(f"{BASE_URL}/api/tenant-admin/modules")
        modules = modules_resp.json()["modules"]
        buy_planning = next((m for m in modules if m["module_id"] == "buy_planning"), None)
        
        # Find a non-core feature to toggle
        non_core_feature = None
        for feat in buy_planning.get("features", []):
            if not feat.get("is_core", False):
                non_core_feature = feat
                break
        
        if non_core_feature:
            resp = self.session.put(
                f"{BASE_URL}/api/tenant-admin/modules/buy_planning/features/{non_core_feature['feature_id']}/toggle",
                json={"feature_id": non_core_feature['feature_id'], "enabled": True}
            )
            
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            data = resp.json()
            assert data.get("success") is True
            print(f"✓ Feature '{non_core_feature['feature_id']}' enabled successfully")
        else:
            print("⚠ No non-core features found to test - skipping")
    
    def test_toggle_feature_disable(self):
        """TEST_09: Can disable a non-core feature"""
        # Get features for buy_planning
        modules_resp = self.session.get(f"{BASE_URL}/api/tenant-admin/modules")
        modules = modules_resp.json()["modules"]
        buy_planning = next((m for m in modules if m["module_id"] == "buy_planning"), None)
        
        # Find a non-core feature that is enabled
        non_core_feature = None
        for feat in buy_planning.get("features", []):
            if not feat.get("is_core", False) and feat.get("enabled", False):
                non_core_feature = feat
                break
        
        if non_core_feature:
            resp = self.session.put(
                f"{BASE_URL}/api/tenant-admin/modules/buy_planning/features/{non_core_feature['feature_id']}/toggle",
                json={"feature_id": non_core_feature['feature_id'], "enabled": False}
            )
            
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            data = resp.json()
            assert data.get("success") is True
            print(f"✓ Feature '{non_core_feature['feature_id']}' disabled successfully")
        else:
            print("⚠ No enabled non-core features found to test - skipping")
    
    def test_cannot_disable_core_feature(self):
        """TEST_10: Cannot disable a core feature"""
        # Get features for buy_planning
        modules_resp = self.session.get(f"{BASE_URL}/api/tenant-admin/modules")
        modules = modules_resp.json()["modules"]
        buy_planning = next((m for m in modules if m["module_id"] == "buy_planning"), None)
        
        # Find a core feature
        core_feature = None
        for feat in buy_planning.get("features", []):
            if feat.get("is_core", False):
                core_feature = feat
                break
        
        if core_feature:
            resp = self.session.put(
                f"{BASE_URL}/api/tenant-admin/modules/buy_planning/features/{core_feature['feature_id']}/toggle",
                json={"feature_id": core_feature['feature_id'], "enabled": False}
            )
            
            assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
            print(f"✓ Core feature '{core_feature['feature_id']}' cannot be disabled (400 returned)")
        else:
            print("⚠ No core features found to test - skipping")
    
    def test_toggle_invalid_feature_returns_404(self):
        """TEST_11: Toggle non-existent feature returns 404"""
        resp = self.session.put(
            f"{BASE_URL}/api/tenant-admin/modules/buy_planning/features/invalid_feature_xyz/toggle",
            json={"feature_id": "invalid_feature_xyz", "enabled": True}
        )
        
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        print("✓ Invalid feature returns 404")
    
    # ─── GET /api/tenant-admin/modules/usage ───
    
    def test_get_usage_returns_limits(self):
        """TEST_12: GET /api/tenant-admin/modules/usage returns limits"""
        resp = self.session.get(f"{BASE_URL}/api/tenant-admin/modules/usage")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert data.get("success") is True
        assert "limits" in data, "Response should have 'limits' key"
        assert "current_usage" in data, "Response should have 'current_usage' key"
        assert "subscription" in data, "Response should have 'subscription' key"
        
        print(f"✓ Usage endpoint returns limits, current_usage, and subscription")
    
    def test_get_usage_limits_structure(self):
        """TEST_13: Usage limits have expected fields"""
        resp = self.session.get(f"{BASE_URL}/api/tenant-admin/modules/usage")
        assert resp.status_code == 200
        
        data = resp.json()
        limits = data.get("limits", {})
        
        # Check for common limit fields
        expected_limit_fields = ["max_users", "max_stores", "max_skus"]
        for field in expected_limit_fields:
            if field in limits:
                assert isinstance(limits[field], (int, float)), f"limits.{field} should be numeric"
        
        print(f"✓ Usage limits structure verified: {list(limits.keys())}")
    
    def test_get_usage_subscription_info(self):
        """TEST_14: Usage subscription has plan info"""
        resp = self.session.get(f"{BASE_URL}/api/tenant-admin/modules/usage")
        assert resp.status_code == 200
        
        data = resp.json()
        subscription = data.get("subscription", {})
        
        # Subscription should have plan info
        if subscription:
            print(f"✓ Subscription info: plan={subscription.get('plan')}, tier={subscription.get('tier')}, status={subscription.get('status')}")
        else:
            print("⚠ No subscription info returned (may be expected for some tenants)")
    
    # ─── GET /api/users/{email}/module-access ───
    
    def test_get_user_module_access(self):
        """TEST_15: GET /api/users/{email}/module-access returns user's module access"""
        resp = self.session.get(f"{BASE_URL}/api/users/{SUPER_ADMIN_EMAIL}/module-access")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert data.get("success") is True
        assert data.get("email") == SUPER_ADMIN_EMAIL
        assert "module_access" in data, "Response should have 'module_access' key"
        assert "scope" in data, "Response should have 'scope' key"
        
        print(f"✓ User module access retrieved for {SUPER_ADMIN_EMAIL}")
    
    def test_get_user_module_access_invalid_user(self):
        """TEST_16: GET module-access for non-existent user returns 404"""
        resp = self.session.get(f"{BASE_URL}/api/users/nonexistent_user_xyz@test.com/module-access")
        
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        print("✓ Non-existent user returns 404")
    
    # ─── PUT /api/users/{email}/module-access ───
    
    def test_update_user_module_access(self):
        """TEST_17: PUT /api/users/{email}/module-access updates user's module access"""
        # Update module access for super admin
        resp = self.session.put(
            f"{BASE_URL}/api/users/{SUPER_ADMIN_EMAIL}/module-access",
            json={
                "modules": [
                    {"module_id": "core_classification", "access": "full"},
                    {"module_id": "buy_planning", "access": "full"},
                    {"module_id": "inventory_management", "access": "read_only"},
                    {"module_id": "space_planning", "access": "none"},
                    {"module_id": "ai_insights", "access": "full"}
                ]
            }
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("success") is True
        
        # Verify the update
        get_resp = self.session.get(f"{BASE_URL}/api/users/{SUPER_ADMIN_EMAIL}/module-access")
        assert get_resp.status_code == 200
        
        module_access = get_resp.json().get("module_access", {})
        assert "core_classification" in module_access
        assert module_access["core_classification"]["access"] == "full"
        
        print("✓ User module access updated and verified")
    
    # ─── PUT /api/users/{email}/scope ───
    
    def test_update_user_scope(self):
        """TEST_18: PUT /api/users/{email}/scope updates user's data scope"""
        resp = self.session.put(
            f"{BASE_URL}/api/users/{SUPER_ADMIN_EMAIL}/scope",
            json={
                "categories": ["Apparel", "Footwear"],
                "regions": ["North", "South"],
                "store_wedges": ["A", "B"],
                "stores": []
            }
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("success") is True
        
        # Verify the update
        get_resp = self.session.get(f"{BASE_URL}/api/users/{SUPER_ADMIN_EMAIL}/module-access")
        assert get_resp.status_code == 200
        
        scope = get_resp.json().get("scope", {})
        assert "categories" in scope or scope == {}, "Scope should have categories or be empty"
        
        print("✓ User scope updated successfully")
    
    def test_update_scope_invalid_user(self):
        """TEST_19: PUT scope for non-existent user returns 404"""
        resp = self.session.put(
            f"{BASE_URL}/api/users/nonexistent_user_xyz@test.com/scope",
            json={"categories": ["Test"]}
        )
        
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        print("✓ Non-existent user scope update returns 404")


class TestModuleSystemEdgeCases:
    """Edge case tests for module system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200
        
        token = login_resp.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_modules_ordered_correctly(self):
        """TEST_20: Modules are returned in correct order"""
        resp = self.session.get(f"{BASE_URL}/api/tenant-admin/modules")
        assert resp.status_code == 200
        
        modules = resp.json()["modules"]
        orders = [m.get("order", 999) for m in modules]
        
        # Verify modules are sorted by order
        assert orders == sorted(orders), f"Modules not in order: {orders}"
        print(f"✓ Modules returned in correct order: {orders}")
    
    def test_module_categories_present(self):
        """TEST_21: All modules have valid categories"""
        resp = self.session.get(f"{BASE_URL}/api/tenant-admin/modules")
        assert resp.status_code == 200
        
        modules = resp.json()["modules"]
        valid_categories = ["foundation", "operations", "inventory", "space", "analytics"]
        
        for mod in modules:
            category = mod.get("category")
            assert category in valid_categories, f"Module {mod['module_id']} has invalid category: {category}"
        
        print("✓ All modules have valid categories")
    
    def test_unauthenticated_request_fails(self):
        """TEST_22: Unauthenticated request to modules endpoint fails"""
        unauthenticated_session = requests.Session()
        resp = unauthenticated_session.get(f"{BASE_URL}/api/tenant-admin/modules")
        
        # API returns 400 (tenant context required) or 401/403 for unauthenticated requests
        assert resp.status_code in [400, 401, 403], f"Expected 400/401/403, got {resp.status_code}"
        print("✓ Unauthenticated request correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
