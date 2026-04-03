"""
Onboarding Wizard Tests - Iteration 40
Tests for 3-step onboarding wizard: Marketplaces → Stores → Categories

Test Coverage:
- OW-WF-01: Complete full 3-step onboarding flow
- OW-WF-02: Add marketplace with all fields
- OW-WF-03: Add store with marketplace mapping
- OW-WF-04: Build nested category hierarchy
- OW-WF-05: Delete marketplace
- OW-WF-06: Delete parent category (cascades to children)
- OW-WF-07: Skip step functionality
- OW-WF-08: Auto-onboard existing tenant (demo)
- OW-WF-10: Update store marketplace mapping
- OW-WF-11: Duplicate prevention (marketplace, store, category)
- OW-WF-13: Complete onboarding with minimum data
- OW-WF-14: Reset onboarding
- OW-WF-15: Concurrent users test
"""

import pytest
import requests
import os
import time
import concurrent.futures

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
DEMO_CREDS = {"email": "admin@demo.com", "password": "demo1234", "tenant_id": "demo"}
ACME_CREDS = {"email": "admin@acme.com", "password": "AcmePass123!", "tenant_id": "acme_corp"}


@pytest.fixture(scope="module")
def demo_token():
    """Get auth token for demo tenant"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_CREDS)
    assert response.status_code == 200, f"Demo login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def acme_token():
    """Get auth token for acme_corp tenant (requires X-Tenant-ID header)"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json=ACME_CREDS,
        headers={"X-Tenant-ID": "acme_corp"}
    )
    assert response.status_code == 200, f"Acme login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def demo_session(demo_token):
    """Session with demo tenant auth"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {demo_token}",
        "Content-Type": "application/json"
    })
    return session


@pytest.fixture
def acme_session(acme_token):
    """Session with acme_corp tenant auth (includes X-Tenant-ID header)"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {acme_token}",
        "Content-Type": "application/json",
        "X-Tenant-ID": "acme_corp"
    })
    return session


class TestOnboardingStatus:
    """OW-WF-08: Auto-onboard existing tenant tests"""
    
    def test_demo_tenant_auto_onboarded(self, demo_session):
        """Demo tenant with uploaded_files should be auto-onboarded"""
        response = demo_session.get(f"{BASE_URL}/api/onboarding/status")
        assert response.status_code == 200
        data = response.json()
        
        # Demo tenant should be auto-onboarded because it has uploaded_files
        assert data.get("is_onboarded") == True, f"Demo tenant should be auto-onboarded: {data}"
        assert data.get("progress_percentage") == 100
        print(f"✓ Demo tenant auto-onboarded: is_onboarded={data.get('is_onboarded')}")
    
    def test_acme_tenant_status(self, acme_session):
        """Acme tenant status check"""
        response = acme_session.get(f"{BASE_URL}/api/onboarding/status")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Acme tenant status: is_onboarded={data.get('is_onboarded')}, current_step={data.get('current_step')}")


class TestOnboardingReset:
    """OW-WF-14: Reset onboarding tests"""
    
    def test_reset_onboarding_acme(self, acme_session):
        """Reset onboarding clears all data and status"""
        # Reset onboarding
        response = acme_session.post(f"{BASE_URL}/api/onboarding/reset")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Onboarding reset: {data.get('message')}")
        
        # Verify status is reset
        status_response = acme_session.get(f"{BASE_URL}/api/onboarding/status")
        assert status_response.status_code == 200
        status = status_response.json()
        
        # After reset, should be non-onboarded
        assert status.get("is_onboarded") == False, f"Should be non-onboarded after reset: {status}"
        assert status.get("current_step") == 1
        assert status.get("progress_percentage") == 0
        print(f"✓ Status after reset: is_onboarded={status.get('is_onboarded')}, step={status.get('current_step')}")


class TestMarketplaceCRUD:
    """OW-WF-02, OW-WF-05, OW-WF-11: Marketplace CRUD tests"""
    
    def test_add_marketplace_with_all_fields(self, acme_session):
        """OW-WF-02: Add marketplace with all fields"""
        marketplace_data = {
            "name": "TEST_Amazon India",
            "currency": "INR",
            "tax_rate": 18.0,
            "commission_percentage": 15.0,
            "type": "marketplace"
        }
        
        response = acme_session.post(f"{BASE_URL}/api/onboarding/marketplaces", json=marketplace_data)
        assert response.status_code == 200, f"Add marketplace failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "marketplace_id" in data
        assert data["marketplace_id"] == "test_amazon_india"  # Auto-generated from name
        print(f"✓ Added marketplace: {data.get('marketplace_id')}")
        
        # Verify in GET
        get_response = acme_session.get(f"{BASE_URL}/api/onboarding/marketplaces")
        assert get_response.status_code == 200
        marketplaces = get_response.json()
        
        mp = next((m for m in marketplaces if m["marketplace_id"] == "test_amazon_india"), None)
        assert mp is not None, "Marketplace not found in GET response"
        assert mp["name"] == "TEST_Amazon India"
        assert mp["currency"] == "INR"
        assert mp["tax_rate"] == 18.0
        assert mp["commission_percentage"] == 15.0
        print(f"✓ Verified marketplace in API: {mp['name']}")
    
    def test_duplicate_marketplace_rejected(self, acme_session):
        """OW-WF-11: Duplicate marketplace_id rejected with 400"""
        marketplace_data = {
            "name": "TEST_Amazon India",  # Same name = same marketplace_id
            "currency": "USD",
            "tax_rate": 10.0,
            "commission_percentage": 5.0,
            "type": "website"
        }
        
        response = acme_session.post(f"{BASE_URL}/api/onboarding/marketplaces", json=marketplace_data)
        assert response.status_code == 400, f"Should reject duplicate: {response.text}"
        assert "already exists" in response.json().get("detail", "").lower()
        print(f"✓ Duplicate marketplace rejected: {response.json().get('detail')}")
    
    def test_add_second_marketplace(self, acme_session):
        """Add another marketplace for store mapping tests"""
        marketplace_data = {
            "name": "TEST_Flipkart",
            "currency": "INR",
            "tax_rate": 18.0,
            "commission_percentage": 12.0,
            "type": "marketplace"
        }
        
        response = acme_session.post(f"{BASE_URL}/api/onboarding/marketplaces", json=marketplace_data)
        assert response.status_code == 200
        print(f"✓ Added second marketplace: TEST_Flipkart")
    
    def test_delete_marketplace(self, acme_session):
        """OW-WF-05: Delete marketplace and verify removal"""
        # First add a marketplace to delete
        mp_data = {"name": "TEST_ToDelete", "currency": "INR", "tax_rate": 5.0, "commission_percentage": 2.0, "type": "website"}
        add_response = acme_session.post(f"{BASE_URL}/api/onboarding/marketplaces", json=mp_data)
        assert add_response.status_code == 200
        mp_id = add_response.json()["marketplace_id"]
        
        # Delete it
        del_response = acme_session.delete(f"{BASE_URL}/api/onboarding/marketplaces/{mp_id}")
        assert del_response.status_code == 200
        assert del_response.json().get("success") == True
        print(f"✓ Deleted marketplace: {mp_id}")
        
        # Verify it's gone
        get_response = acme_session.get(f"{BASE_URL}/api/onboarding/marketplaces")
        marketplaces = get_response.json()
        assert not any(m["marketplace_id"] == mp_id for m in marketplaces), "Marketplace should be deleted"
        print(f"✓ Verified marketplace removed from API")


class TestStoreCRUD:
    """OW-WF-03, OW-WF-10, OW-WF-11: Store CRUD tests"""
    
    def test_add_store_with_marketplace_mapping(self, acme_session):
        """OW-WF-03: Add store with marketplace mapping"""
        store_data = {
            "store_code": "TEST_DEL01",
            "store_name": "TEST Delhi Store",
            "type": "physical",
            "city": "Delhi",
            "state": "Delhi",
            "pincode": "110001",
            "marketplaces": ["TEST_Amazon India", "TEST_Flipkart"]
        }
        
        response = acme_session.post(f"{BASE_URL}/api/onboarding/stores", json=store_data)
        assert response.status_code == 200, f"Add store failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Added store: {store_data['store_code']}")
        
        # Verify in GET
        get_response = acme_session.get(f"{BASE_URL}/api/onboarding/stores")
        assert get_response.status_code == 200
        stores = get_response.json()
        
        store = next((s for s in stores if s["store_code"] == "TEST_DEL01"), None)
        assert store is not None, "Store not found in GET response"
        assert store["store_name"] == "TEST Delhi Store"
        assert store["city"] == "Delhi"
        assert store["state"] == "Delhi"
        assert store["pincode"] == "110001"
        assert "TEST_Amazon India" in store.get("marketplaces", [])
        assert "TEST_Flipkart" in store.get("marketplaces", [])
        print(f"✓ Verified store in API with marketplace mapping")
    
    def test_duplicate_store_code_rejected(self, acme_session):
        """OW-WF-11: Duplicate store_code rejected with 400"""
        store_data = {
            "store_code": "TEST_DEL01",  # Same code
            "store_name": "Another Store",
            "type": "warehouse",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "marketplaces": []
        }
        
        response = acme_session.post(f"{BASE_URL}/api/onboarding/stores", json=store_data)
        assert response.status_code == 400, f"Should reject duplicate: {response.text}"
        assert "already exists" in response.json().get("detail", "").lower()
        print(f"✓ Duplicate store code rejected: {response.json().get('detail')}")
    
    def test_update_store_marketplace_mapping(self, acme_session):
        """OW-WF-10: Update store marketplace mapping via PUT"""
        new_marketplaces = ["TEST_Amazon India"]  # Remove Flipkart
        
        response = acme_session.put(
            f"{BASE_URL}/api/onboarding/stores/TEST_DEL01/marketplaces",
            json=new_marketplaces
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        assert response.json().get("success") == True
        print(f"✓ Updated store marketplace mapping")
        
        # Verify update
        get_response = acme_session.get(f"{BASE_URL}/api/onboarding/stores")
        stores = get_response.json()
        store = next((s for s in stores if s["store_code"] == "TEST_DEL01"), None)
        assert store is not None
        assert store.get("marketplaces") == ["TEST_Amazon India"]
        print(f"✓ Verified marketplace mapping updated")
    
    def test_delete_store(self, acme_session):
        """Delete store and verify removal"""
        # Add a store to delete
        store_data = {
            "store_code": "TEST_TODEL",
            "store_name": "To Delete Store",
            "type": "dark_store",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "pincode": "600001",
            "marketplaces": []
        }
        add_response = acme_session.post(f"{BASE_URL}/api/onboarding/stores", json=store_data)
        assert add_response.status_code == 200
        
        # Delete it
        del_response = acme_session.delete(f"{BASE_URL}/api/onboarding/stores/TEST_TODEL")
        assert del_response.status_code == 200
        print(f"✓ Deleted store: TEST_TODEL")
        
        # Verify it's gone
        get_response = acme_session.get(f"{BASE_URL}/api/onboarding/stores")
        stores = get_response.json()
        assert not any(s["store_code"] == "TEST_TODEL" for s in stores)
        print(f"✓ Verified store removed from API")


class TestCategoryCRUD:
    """OW-WF-04, OW-WF-06, OW-WF-11: Category CRUD tests"""
    
    def test_build_nested_category_hierarchy(self, acme_session):
        """OW-WF-04: Build nested category hierarchy (Apparel→Men→Jeans→Slim Fit)"""
        # Level 1: Apparel (root)
        cat1 = {"name": "TEST_Apparel", "parent_id": None, "description": "All apparel"}
        r1 = acme_session.post(f"{BASE_URL}/api/onboarding/categories", json=cat1)
        assert r1.status_code == 200, f"Add Apparel failed: {r1.text}"
        apparel_id = r1.json()["category_id"]
        print(f"✓ Added root category: {apparel_id}")
        
        # Level 2: Men (child of Apparel)
        cat2 = {"name": "TEST_Men", "parent_id": apparel_id, "description": "Men's clothing"}
        r2 = acme_session.post(f"{BASE_URL}/api/onboarding/categories", json=cat2)
        assert r2.status_code == 200, f"Add Men failed: {r2.text}"
        men_id = r2.json()["category_id"]
        print(f"✓ Added child category: {men_id}")
        
        # Level 3: Jeans (child of Men)
        cat3 = {"name": "TEST_Jeans", "parent_id": men_id, "description": "Jeans"}
        r3 = acme_session.post(f"{BASE_URL}/api/onboarding/categories", json=cat3)
        assert r3.status_code == 200, f"Add Jeans failed: {r3.text}"
        jeans_id = r3.json()["category_id"]
        print(f"✓ Added grandchild category: {jeans_id}")
        
        # Level 4: Slim Fit (child of Jeans)
        cat4 = {"name": "TEST_Slim Fit", "parent_id": jeans_id, "description": "Slim fit jeans"}
        r4 = acme_session.post(f"{BASE_URL}/api/onboarding/categories", json=cat4)
        assert r4.status_code == 200, f"Add Slim Fit failed: {r4.text}"
        slim_id = r4.json()["category_id"]
        print(f"✓ Added great-grandchild category: {slim_id}")
        
        # Verify tree structure via API
        tree_response = acme_session.get(f"{BASE_URL}/api/onboarding/categories/tree")
        assert tree_response.status_code == 200
        tree = tree_response.json()
        
        # Find Apparel in roots
        apparel = next((c for c in tree if c["category_id"] == apparel_id), None)
        assert apparel is not None, "Apparel not found in tree roots"
        
        # Check nested structure
        men = next((c for c in apparel.get("children", []) if c["category_id"] == men_id), None)
        assert men is not None, "Men not found as child of Apparel"
        
        jeans = next((c for c in men.get("children", []) if c["category_id"] == jeans_id), None)
        assert jeans is not None, "Jeans not found as child of Men"
        
        slim = next((c for c in jeans.get("children", []) if c["category_id"] == slim_id), None)
        assert slim is not None, "Slim Fit not found as child of Jeans"
        
        print(f"✓ Verified nested tree structure: Apparel→Men→Jeans→Slim Fit")
    
    def test_duplicate_category_rejected(self, acme_session):
        """OW-WF-11: Duplicate category_id rejected with 400"""
        cat_data = {"name": "TEST_Apparel", "parent_id": None, "description": "Duplicate"}
        
        response = acme_session.post(f"{BASE_URL}/api/onboarding/categories", json=cat_data)
        assert response.status_code == 400, f"Should reject duplicate: {response.text}"
        assert "already exists" in response.json().get("detail", "").lower()
        print(f"✓ Duplicate category rejected: {response.json().get('detail')}")
    
    def test_delete_parent_cascades_to_children(self, acme_session):
        """OW-WF-06: Delete parent category and verify all children are also deleted"""
        # Add a parent with children
        parent = {"name": "TEST_ToDeleteParent", "parent_id": None, "description": "Parent to delete"}
        r1 = acme_session.post(f"{BASE_URL}/api/onboarding/categories", json=parent)
        assert r1.status_code == 200
        parent_id = r1.json()["category_id"]
        
        child1 = {"name": "TEST_Child1", "parent_id": parent_id, "description": "Child 1"}
        r2 = acme_session.post(f"{BASE_URL}/api/onboarding/categories", json=child1)
        assert r2.status_code == 200
        child1_id = r2.json()["category_id"]
        
        child2 = {"name": "TEST_Child2", "parent_id": parent_id, "description": "Child 2"}
        r3 = acme_session.post(f"{BASE_URL}/api/onboarding/categories", json=child2)
        assert r3.status_code == 200
        child2_id = r3.json()["category_id"]
        
        grandchild = {"name": "TEST_Grandchild", "parent_id": child1_id, "description": "Grandchild"}
        r4 = acme_session.post(f"{BASE_URL}/api/onboarding/categories", json=grandchild)
        assert r4.status_code == 200
        grandchild_id = r4.json()["category_id"]
        
        print(f"✓ Created hierarchy: {parent_id} → [{child1_id}, {child2_id}] → {grandchild_id}")
        
        # Delete parent
        del_response = acme_session.delete(f"{BASE_URL}/api/onboarding/categories/{parent_id}")
        assert del_response.status_code == 200
        data = del_response.json()
        assert data.get("success") == True
        # Should delete 4 categories (parent + 2 children + 1 grandchild)
        assert "4" in data.get("message", "") or "Deleted" in data.get("message", "")
        print(f"✓ Deleted parent: {data.get('message')}")
        
        # Verify all are gone
        tree_response = acme_session.get(f"{BASE_URL}/api/onboarding/categories/tree")
        tree = tree_response.json()
        
        # Flatten tree to check
        def flatten(nodes):
            result = []
            for n in nodes:
                result.append(n["category_id"])
                if n.get("children"):
                    result.extend(flatten(n["children"]))
            return result
        
        all_ids = flatten(tree)
        assert parent_id not in all_ids, "Parent should be deleted"
        assert child1_id not in all_ids, "Child1 should be deleted"
        assert child2_id not in all_ids, "Child2 should be deleted"
        assert grandchild_id not in all_ids, "Grandchild should be deleted"
        print(f"✓ Verified cascade delete: all 4 categories removed")


class TestSkipStep:
    """OW-WF-07: Skip step functionality tests"""
    
    def test_skip_step_marks_complete(self, acme_session):
        """Skip step and verify it's marked complete in status"""
        # Get current status
        status_before = acme_session.get(f"{BASE_URL}/api/onboarding/status").json()
        print(f"Status before skip: step={status_before.get('current_step')}")
        
        # Skip step 1 (marketplaces)
        skip_response = acme_session.post(f"{BASE_URL}/api/onboarding/skip?step=1")
        assert skip_response.status_code == 200
        assert skip_response.json().get("success") == True
        print(f"✓ Skipped step 1: {skip_response.json().get('message')}")
        
        # Verify status updated
        status_after = acme_session.get(f"{BASE_URL}/api/onboarding/status").json()
        assert status_after.get("step_1_marketplaces_complete") == True
        print(f"✓ Step 1 marked complete after skip")


class TestCompleteOnboarding:
    """OW-WF-01, OW-WF-13: Complete onboarding flow tests"""
    
    def test_complete_onboarding_with_minimum_data(self, acme_session):
        """OW-WF-13: Complete onboarding with minimum data (1 mp, 1 store, 3 categories)"""
        # Reset first
        acme_session.post(f"{BASE_URL}/api/onboarding/reset")
        
        # Add 1 marketplace
        mp = {"name": "TEST_MinMP", "currency": "INR", "tax_rate": 18.0, "commission_percentage": 10.0, "type": "marketplace"}
        r1 = acme_session.post(f"{BASE_URL}/api/onboarding/marketplaces", json=mp)
        assert r1.status_code == 200
        print(f"✓ Added 1 marketplace")
        
        # Add 1 store
        store = {"store_code": "TEST_MIN01", "store_name": "Min Store", "type": "physical", "city": "Mumbai", "state": "Maharashtra", "pincode": "400001", "marketplaces": ["TEST_MinMP"]}
        r2 = acme_session.post(f"{BASE_URL}/api/onboarding/stores", json=store)
        assert r2.status_code == 200
        print(f"✓ Added 1 store")
        
        # Add 3 categories (minimum required)
        for i in range(3):
            cat = {"name": f"TEST_MinCat{i+1}", "parent_id": None, "description": f"Min category {i+1}"}
            r = acme_session.post(f"{BASE_URL}/api/onboarding/categories", json=cat)
            assert r.status_code == 200
        print(f"✓ Added 3 categories")
        
        # Complete onboarding
        complete_response = acme_session.post(f"{BASE_URL}/api/onboarding/complete")
        assert complete_response.status_code == 200, f"Complete failed: {complete_response.text}"
        data = complete_response.json()
        assert data.get("success") == True
        print(f"✓ Completed onboarding: {data.get('message')}")
        
        # Verify status
        status = acme_session.get(f"{BASE_URL}/api/onboarding/status").json()
        assert status.get("is_onboarded") == True
        print(f"✓ Verified is_onboarded=True")
    
    def test_complete_fails_without_required_data(self, acme_session):
        """Complete onboarding fails if steps not complete"""
        # Reset
        acme_session.post(f"{BASE_URL}/api/onboarding/reset")
        
        # Try to complete without any data
        complete_response = acme_session.post(f"{BASE_URL}/api/onboarding/complete")
        assert complete_response.status_code == 400, f"Should fail: {complete_response.text}"
        detail = complete_response.json().get("detail", "")
        # API returns "Start onboarding first" when no status exists, or "Please complete: ..." when steps incomplete
        assert "start" in detail.lower() or "complete" in detail.lower() or "add" in detail.lower()
        print(f"✓ Complete correctly rejected: {detail}")


class TestConcurrentUsers:
    """OW-WF-15: Concurrent users test"""
    
    def test_concurrent_marketplace_additions(self, acme_session):
        """Two concurrent requests adding data to same tenant"""
        # Reset first
        acme_session.post(f"{BASE_URL}/api/onboarding/reset")
        
        def add_marketplace(name):
            mp = {"name": name, "currency": "INR", "tax_rate": 18.0, "commission_percentage": 10.0, "type": "marketplace"}
            response = acme_session.post(f"{BASE_URL}/api/onboarding/marketplaces", json=mp)
            return response.status_code, response.json()
        
        # Run concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(add_marketplace, "TEST_Concurrent1")
            future2 = executor.submit(add_marketplace, "TEST_Concurrent2")
            
            result1 = future1.result()
            result2 = future2.result()
        
        # Both should succeed
        assert result1[0] == 200, f"First request failed: {result1}"
        assert result2[0] == 200, f"Second request failed: {result2}"
        print(f"✓ Both concurrent requests succeeded")
        
        # Verify both exist
        get_response = acme_session.get(f"{BASE_URL}/api/onboarding/marketplaces")
        marketplaces = get_response.json()
        mp_ids = [m["marketplace_id"] for m in marketplaces]
        assert "test_concurrent1" in mp_ids
        assert "test_concurrent2" in mp_ids
        print(f"✓ Both marketplaces persisted: {mp_ids}")


class TestCleanup:
    """Cleanup test data after all tests"""
    
    def test_cleanup_acme_data(self, acme_session):
        """Reset acme tenant data after tests"""
        response = acme_session.post(f"{BASE_URL}/api/onboarding/reset")
        assert response.status_code == 200
        print(f"✓ Cleaned up acme tenant onboarding data")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
