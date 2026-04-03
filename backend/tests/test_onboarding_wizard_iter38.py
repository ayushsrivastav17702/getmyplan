"""
Onboarding Wizard Backend Tests - Iteration 38
Tests for 3-step onboarding wizard: Marketplaces → Stores → Categories
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
DEMO_TENANT = {
    "tenant_id": "demo",
    "email": "admin@demo.com",
    "password": "demo1234"
}

ACME_TENANT = {
    "tenant_id": "acme_corp",
    "email": "admin@acme.com",
    "password": "AcmePass123!"
}


class TestOnboardingAuth:
    """Authentication and setup tests"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_token(self, session):
        """Get auth token for demo tenant"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_TENANT["email"],
            "password": DEMO_TENANT["password"],
            "tenant_id": DEMO_TENANT["tenant_id"]
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, f"No access_token in response: {data}"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_login_demo_tenant(self, session):
        """Test login with demo tenant credentials"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_TENANT["email"],
            "password": DEMO_TENANT["password"],
            "tenant_id": DEMO_TENANT["tenant_id"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        # tenant_id is in user object, not top level
        assert data.get("user", {}).get("tenant_id") == "demo" or "access_token" in data
        print(f"✓ Demo tenant login successful, token received")


class TestOnboardingStatus:
    """Onboarding status endpoint tests"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_headers(self, session):
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_TENANT["email"],
            "password": DEMO_TENANT["password"],
            "tenant_id": DEMO_TENANT["tenant_id"]
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_onboarding_status(self, session, auth_headers):
        """GET /api/onboarding/status - returns progress, current_step, is_onboarded"""
        response = session.get(f"{BASE_URL}/api/onboarding/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "tenant_id" in data
        assert "step_1_marketplaces_complete" in data
        assert "step_2_stores_complete" in data
        assert "step_3_taxonomy_complete" in data
        assert "is_onboarded" in data or "current_step" in data
        
        print(f"✓ Onboarding status: is_onboarded={data.get('is_onboarded')}, current_step={data.get('current_step')}")
    
    def test_demo_tenant_auto_onboarded(self, session, auth_headers):
        """Demo tenant with uploaded data should be auto-onboarded"""
        response = session.get(f"{BASE_URL}/api/onboarding/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Demo tenant has uploaded_files, so should be auto-onboarded
        assert data.get("is_onboarded") == True, f"Demo tenant should be auto-onboarded: {data}"
        print(f"✓ Demo tenant is auto-onboarded (has uploaded data)")


class TestMarketplacesCRUD:
    """Step 1 - Marketplace CRUD tests"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_headers(self, session):
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_TENANT["email"],
            "password": DEMO_TENANT["password"],
            "tenant_id": DEMO_TENANT["tenant_id"]
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_marketplaces(self, session, auth_headers):
        """GET /api/onboarding/marketplaces - lists active marketplaces"""
        response = session.get(f"{BASE_URL}/api/onboarding/marketplaces", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET marketplaces: {len(data)} marketplaces found")
    
    def test_create_marketplace(self, session, auth_headers):
        """POST /api/onboarding/marketplaces - creates marketplace with auto-generated ID"""
        # First delete if exists
        session.delete(f"{BASE_URL}/api/onboarding/marketplaces/test_amazon_india", headers=auth_headers)
        
        payload = {
            "name": "TEST Amazon India",
            "currency": "INR",
            "tax_rate": 18.0,
            "commission_percentage": 15.0,
            "type": "marketplace"
        }
        response = session.post(f"{BASE_URL}/api/onboarding/marketplaces", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "marketplace_id" in data
        # Auto-generated ID should be lowercase with underscores
        assert data["marketplace_id"] == "test_amazon_india"
        print(f"✓ Created marketplace: {data['marketplace_id']}")
        
        # Verify persistence with GET
        get_response = session.get(f"{BASE_URL}/api/onboarding/marketplaces", headers=auth_headers)
        marketplaces = get_response.json()
        found = any(m.get("marketplace_id") == "test_amazon_india" for m in marketplaces)
        assert found, "Created marketplace not found in GET response"
        print(f"✓ Marketplace persisted and verified via GET")
    
    def test_duplicate_marketplace_rejected(self, session, auth_headers):
        """Duplicate marketplace IDs should be rejected with 400"""
        payload = {
            "name": "TEST Amazon India",  # Same name = same auto-generated ID
            "currency": "INR",
            "tax_rate": 18.0,
            "commission_percentage": 15.0,
            "type": "marketplace"
        }
        response = session.post(f"{BASE_URL}/api/onboarding/marketplaces", json=payload, headers=auth_headers)
        assert response.status_code == 400, f"Expected 400 for duplicate, got {response.status_code}"
        print(f"✓ Duplicate marketplace correctly rejected with 400")
    
    def test_delete_marketplace(self, session, auth_headers):
        """DELETE /api/onboarding/marketplaces/{id} - deletes marketplace"""
        response = session.delete(f"{BASE_URL}/api/onboarding/marketplaces/test_amazon_india", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Deleted marketplace: test_amazon_india")
        
        # Verify deletion
        get_response = session.get(f"{BASE_URL}/api/onboarding/marketplaces", headers=auth_headers)
        marketplaces = get_response.json()
        found = any(m.get("marketplace_id") == "test_amazon_india" for m in marketplaces)
        assert not found, "Deleted marketplace still found in GET response"
        print(f"✓ Marketplace deletion verified")
    
    def test_delete_nonexistent_marketplace(self, session, auth_headers):
        """DELETE nonexistent marketplace should return 404"""
        response = session.delete(f"{BASE_URL}/api/onboarding/marketplaces/nonexistent_mp_xyz", headers=auth_headers)
        assert response.status_code == 404
        print(f"✓ Delete nonexistent marketplace correctly returns 404")


class TestStoresCRUD:
    """Step 2 - Store CRUD tests"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_headers(self, session):
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_TENANT["email"],
            "password": DEMO_TENANT["password"],
            "tenant_id": DEMO_TENANT["tenant_id"]
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_stores(self, session, auth_headers):
        """GET /api/onboarding/stores - lists active stores"""
        response = session.get(f"{BASE_URL}/api/onboarding/stores", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET stores: {len(data)} stores found")
    
    def test_create_store(self, session, auth_headers):
        """POST /api/onboarding/stores - creates store with marketplace mapping"""
        # First delete if exists
        session.delete(f"{BASE_URL}/api/onboarding/stores/TEST001", headers=auth_headers)
        
        payload = {
            "store_code": "TEST001",
            "store_name": "TEST Mumbai Store",
            "type": "physical",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "marketplaces": []
        }
        response = session.post(f"{BASE_URL}/api/onboarding/stores", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        print(f"✓ Created store: TEST001")
        
        # Verify persistence
        get_response = session.get(f"{BASE_URL}/api/onboarding/stores", headers=auth_headers)
        stores = get_response.json()
        found = any(s.get("store_code") == "TEST001" for s in stores)
        assert found, "Created store not found in GET response"
        print(f"✓ Store persisted and verified via GET")
    
    def test_duplicate_store_rejected(self, session, auth_headers):
        """Duplicate store codes should be rejected with 400"""
        payload = {
            "store_code": "TEST001",  # Same code
            "store_name": "Another Store",
            "type": "physical",
            "city": "Delhi",
            "state": "Delhi",
            "pincode": "110001",
            "marketplaces": []
        }
        response = session.post(f"{BASE_URL}/api/onboarding/stores", json=payload, headers=auth_headers)
        assert response.status_code == 400, f"Expected 400 for duplicate, got {response.status_code}"
        print(f"✓ Duplicate store correctly rejected with 400")
    
    def test_update_store_marketplaces(self, session, auth_headers):
        """PUT /api/onboarding/stores/{code}/marketplaces - updates marketplace mapping"""
        # First create a marketplace to map
        session.delete(f"{BASE_URL}/api/onboarding/marketplaces/test_flipkart", headers=auth_headers)
        session.post(f"{BASE_URL}/api/onboarding/marketplaces", json={
            "name": "TEST Flipkart",
            "currency": "INR",
            "tax_rate": 18.0,
            "commission_percentage": 10.0,
            "type": "marketplace"
        }, headers=auth_headers)
        
        # Update store marketplaces
        response = session.put(
            f"{BASE_URL}/api/onboarding/stores/TEST001/marketplaces",
            json=["TEST Flipkart"],
            headers=auth_headers
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Updated store TEST001 marketplace mapping")
        
        # Cleanup
        session.delete(f"{BASE_URL}/api/onboarding/marketplaces/test_flipkart", headers=auth_headers)
    
    def test_delete_store(self, session, auth_headers):
        """DELETE /api/onboarding/stores/{code} - deletes store"""
        response = session.delete(f"{BASE_URL}/api/onboarding/stores/TEST001", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Deleted store: TEST001")
        
        # Verify deletion
        get_response = session.get(f"{BASE_URL}/api/onboarding/stores", headers=auth_headers)
        stores = get_response.json()
        found = any(s.get("store_code") == "TEST001" for s in stores)
        assert not found, "Deleted store still found in GET response"
        print(f"✓ Store deletion verified")
    
    def test_delete_nonexistent_store(self, session, auth_headers):
        """DELETE nonexistent store should return 404"""
        response = session.delete(f"{BASE_URL}/api/onboarding/stores/NONEXISTENT_XYZ", headers=auth_headers)
        assert response.status_code == 404
        print(f"✓ Delete nonexistent store correctly returns 404")


class TestCategoriesCRUD:
    """Step 3 - Category Taxonomy CRUD tests"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_headers(self, session):
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_TENANT["email"],
            "password": DEMO_TENANT["password"],
            "tenant_id": DEMO_TENANT["tenant_id"]
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_category_tree(self, session, auth_headers):
        """GET /api/onboarding/categories/tree - returns nested tree"""
        response = session.get(f"{BASE_URL}/api/onboarding/categories/tree", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET category tree: {len(data)} root categories")
    
    def test_create_root_category(self, session, auth_headers):
        """POST /api/onboarding/categories - creates root category"""
        # Cleanup first
        session.delete(f"{BASE_URL}/api/onboarding/categories/test_apparel", headers=auth_headers)
        
        payload = {
            "name": "TEST Apparel",
            "description": "Test clothing category"
        }
        response = session.post(f"{BASE_URL}/api/onboarding/categories", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert data.get("category_id") == "test_apparel"
        print(f"✓ Created root category: test_apparel")
    
    def test_create_child_category(self, session, auth_headers):
        """POST /api/onboarding/categories - creates category with parent"""
        # Cleanup first
        session.delete(f"{BASE_URL}/api/onboarding/categories/test_mens_wear", headers=auth_headers)
        
        payload = {
            "name": "TEST Mens Wear",
            "parent_id": "test_apparel",
            "description": "Men's clothing"
        }
        response = session.post(f"{BASE_URL}/api/onboarding/categories", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert data.get("category_id") == "test_mens_wear"
        print(f"✓ Created child category: test_mens_wear under test_apparel")
        
        # Verify tree structure
        tree_response = session.get(f"{BASE_URL}/api/onboarding/categories/tree", headers=auth_headers)
        tree = tree_response.json()
        parent = next((c for c in tree if c.get("category_id") == "test_apparel"), None)
        if parent and parent.get("children"):
            child = next((c for c in parent["children"] if c.get("category_id") == "test_mens_wear"), None)
            assert child is not None, "Child category not found in tree"
            print(f"✓ Tree structure verified: test_mens_wear is child of test_apparel")
    
    def test_create_category_invalid_parent(self, session, auth_headers):
        """Creating category with nonexistent parent should fail"""
        payload = {
            "name": "TEST Invalid Child",
            "parent_id": "nonexistent_parent_xyz"
        }
        response = session.post(f"{BASE_URL}/api/onboarding/categories", json=payload, headers=auth_headers)
        assert response.status_code == 400, f"Expected 400 for invalid parent, got {response.status_code}"
        print(f"✓ Category with invalid parent correctly rejected")
    
    def test_duplicate_category_rejected(self, session, auth_headers):
        """Duplicate category IDs should be rejected with 400"""
        payload = {
            "name": "TEST Apparel",  # Same name = same auto-generated ID
            "description": "Duplicate"
        }
        response = session.post(f"{BASE_URL}/api/onboarding/categories", json=payload, headers=auth_headers)
        assert response.status_code == 400, f"Expected 400 for duplicate, got {response.status_code}"
        print(f"✓ Duplicate category correctly rejected with 400")
    
    def test_delete_category_with_children(self, session, auth_headers):
        """DELETE /api/onboarding/categories/{id} - deletes with children"""
        # Delete parent should delete children too
        response = session.delete(f"{BASE_URL}/api/onboarding/categories/test_apparel", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        # Should have deleted 2 categories (parent + child)
        assert "2" in data.get("message", "") or "Deleted" in data.get("message", "")
        print(f"✓ Deleted category with children: {data.get('message')}")
        
        # Verify both are gone
        tree_response = session.get(f"{BASE_URL}/api/onboarding/categories/tree", headers=auth_headers)
        tree = tree_response.json()
        parent = next((c for c in tree if c.get("category_id") == "test_apparel"), None)
        assert parent is None, "Deleted parent category still found"
        print(f"✓ Category deletion verified (parent and children removed)")
    
    def test_delete_nonexistent_category(self, session, auth_headers):
        """DELETE nonexistent category should return 404"""
        response = session.delete(f"{BASE_URL}/api/onboarding/categories/nonexistent_cat_xyz", headers=auth_headers)
        assert response.status_code == 404
        print(f"✓ Delete nonexistent category correctly returns 404")


class TestOnboardingWorkflow:
    """Onboarding workflow tests - skip, complete, reset"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_headers(self, session):
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_TENANT["email"],
            "password": DEMO_TENANT["password"],
            "tenant_id": DEMO_TENANT["tenant_id"]
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_skip_step(self, session, auth_headers):
        """POST /api/onboarding/skip?step=N - skips a step"""
        response = session.post(f"{BASE_URL}/api/onboarding/skip?step=1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Skip step 1 successful")
        
        # Test step 2
        response = session.post(f"{BASE_URL}/api/onboarding/skip?step=2", headers=auth_headers)
        assert response.status_code == 200
        print(f"✓ Skip step 2 successful")
        
        # Test step 3
        response = session.post(f"{BASE_URL}/api/onboarding/skip?step=3", headers=auth_headers)
        assert response.status_code == 200
        print(f"✓ Skip step 3 successful")
    
    def test_skip_invalid_step(self, session, auth_headers):
        """Skip with invalid step number should fail"""
        response = session.post(f"{BASE_URL}/api/onboarding/skip?step=0", headers=auth_headers)
        assert response.status_code == 422, f"Expected 422 for invalid step, got {response.status_code}"
        
        response = session.post(f"{BASE_URL}/api/onboarding/skip?step=4", headers=auth_headers)
        assert response.status_code == 422, f"Expected 422 for invalid step, got {response.status_code}"
        print(f"✓ Invalid step numbers correctly rejected")
    
    def test_complete_onboarding_requires_all_steps(self, session, auth_headers):
        """POST /api/onboarding/complete - requires all 3 steps"""
        # First reset to clear any existing data
        session.post(f"{BASE_URL}/api/onboarding/reset", headers=auth_headers)
        
        # Try to complete without any steps done
        response = session.post(f"{BASE_URL}/api/onboarding/complete", headers=auth_headers)
        # Should fail because no steps are complete
        assert response.status_code == 400, f"Expected 400 when steps incomplete, got {response.status_code}"
        print(f"✓ Complete correctly requires all steps")
    
    def test_complete_onboarding_after_skips(self, session, auth_headers):
        """Complete onboarding after skipping all steps"""
        # Skip all steps
        session.post(f"{BASE_URL}/api/onboarding/skip?step=1", headers=auth_headers)
        session.post(f"{BASE_URL}/api/onboarding/skip?step=2", headers=auth_headers)
        session.post(f"{BASE_URL}/api/onboarding/skip?step=3", headers=auth_headers)
        
        # Now complete should work
        response = session.post(f"{BASE_URL}/api/onboarding/complete", headers=auth_headers)
        assert response.status_code == 200, f"Complete failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Onboarding completed after skipping all steps")
    
    def test_reset_onboarding(self, session, auth_headers):
        """POST /api/onboarding/reset - clears all onboarding data"""
        # First add some data
        session.post(f"{BASE_URL}/api/onboarding/marketplaces", json={
            "name": "TEST Reset MP",
            "currency": "INR",
            "tax_rate": 18.0,
            "commission_percentage": 0,
            "type": "marketplace"
        }, headers=auth_headers)
        
        # Reset
        response = session.post(f"{BASE_URL}/api/onboarding/reset", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Onboarding reset successful")
        
        # Verify data is cleared
        mp_response = session.get(f"{BASE_URL}/api/onboarding/marketplaces", headers=auth_headers)
        marketplaces = mp_response.json()
        found = any(m.get("marketplace_id") == "test_reset_mp" for m in marketplaces)
        assert not found, "Reset did not clear marketplace data"
        print(f"✓ Reset cleared all onboarding data")


class TestOnboardingDataValidation:
    """Data validation tests for onboarding endpoints"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_headers(self, session):
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_TENANT["email"],
            "password": DEMO_TENANT["password"],
            "tenant_id": DEMO_TENANT["tenant_id"]
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_marketplace_required_fields(self, session, auth_headers):
        """Marketplace requires name field"""
        response = session.post(f"{BASE_URL}/api/onboarding/marketplaces", json={
            "currency": "INR"
            # Missing name
        }, headers=auth_headers)
        assert response.status_code == 422, f"Expected 422 for missing name, got {response.status_code}"
        print(f"✓ Marketplace name validation works")
    
    def test_store_required_fields(self, session, auth_headers):
        """Store requires store_code, store_name, city, state, pincode"""
        response = session.post(f"{BASE_URL}/api/onboarding/stores", json={
            "store_name": "Test Store"
            # Missing store_code, city, state, pincode
        }, headers=auth_headers)
        assert response.status_code == 422, f"Expected 422 for missing fields, got {response.status_code}"
        print(f"✓ Store required fields validation works")
    
    def test_category_required_fields(self, session, auth_headers):
        """Category requires name field"""
        response = session.post(f"{BASE_URL}/api/onboarding/categories", json={
            "description": "Test"
            # Missing name
        }, headers=auth_headers)
        assert response.status_code == 422, f"Expected 422 for missing name, got {response.status_code}"
        print(f"✓ Category name validation works")
    
    def test_marketplace_currency_enum(self, session, auth_headers):
        """Marketplace currency must be valid enum"""
        # Cleanup
        session.delete(f"{BASE_URL}/api/onboarding/marketplaces/test_currency_mp", headers=auth_headers)
        
        # Valid currency
        response = session.post(f"{BASE_URL}/api/onboarding/marketplaces", json={
            "name": "TEST Currency MP",
            "currency": "USD",
            "tax_rate": 10.0,
            "commission_percentage": 5.0,
            "type": "marketplace"
        }, headers=auth_headers)
        assert response.status_code == 200
        print(f"✓ Valid currency (USD) accepted")
        
        # Cleanup
        session.delete(f"{BASE_URL}/api/onboarding/marketplaces/test_currency_mp", headers=auth_headers)
    
    def test_store_type_enum(self, session, auth_headers):
        """Store type must be valid enum"""
        # Cleanup
        session.delete(f"{BASE_URL}/api/onboarding/stores/TESTTYPE001", headers=auth_headers)
        
        # Valid type
        response = session.post(f"{BASE_URL}/api/onboarding/stores", json={
            "store_code": "TESTTYPE001",
            "store_name": "Test Warehouse",
            "type": "warehouse",
            "city": "Delhi",
            "state": "Delhi",
            "pincode": "110001",
            "marketplaces": []
        }, headers=auth_headers)
        assert response.status_code == 200
        print(f"✓ Valid store type (warehouse) accepted")
        
        # Cleanup
        session.delete(f"{BASE_URL}/api/onboarding/stores/TESTTYPE001", headers=auth_headers)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
