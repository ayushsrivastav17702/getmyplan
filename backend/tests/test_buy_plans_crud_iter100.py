"""
Test Buy Plan Persistence & Approval Workflow (Phase B)
Iteration 100: Tests for buy plan CRUD endpoints

Endpoints tested:
- POST /api/buy-planning/buy-plans/generate - Generate and save a new plan
- GET /api/buy-planning/buy-plans - List saved plans (without items)
- GET /api/buy-planning/buy-plans/{plan_id} - Get full plan with items
- PUT /api/buy-planning/buy-plans/{plan_id}/items - Update item quantity
- POST /api/buy-planning/buy-plans/{plan_id}/approve - Approve a draft plan
- DELETE /api/buy-planning/buy-plans/{plan_id} - Delete a draft plan
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@demo.com"
TEST_PASSWORD = "demo1234"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for testing."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, f"No access_token in response: {data}"
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestBuyPlanGenerate:
    """Test POST /api/buy-planning/buy-plans/generate"""
    
    def test_generate_plan_success(self, auth_headers):
        """Generate a new buy plan with default parameters."""
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/buy-plans/generate",
            headers=auth_headers,
            json={
                "cover_days": 30,
                "safety_days": 7,
                "plan_name": "TEST_Plan_30d_iter100"
            }
        )
        assert response.status_code == 200, f"Generate failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert data.get("success") is True
        assert "plan_id" in data, "Missing plan_id in response"
        assert "plan_name" in data
        assert data.get("status") == "draft", f"Expected draft status, got {data.get('status')}"
        assert "totals" in data
        assert "sku_count" in data
        
        # Store plan_id for cleanup
        pytest.generated_plan_id = data["plan_id"]
        print(f"Generated plan: {data['plan_id']} with {data['sku_count']} SKUs")
    
    def test_generate_plan_with_60_days(self, auth_headers):
        """Generate a plan with 60-day cover period."""
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/buy-plans/generate",
            headers=auth_headers,
            json={
                "cover_days": 60,
                "safety_days": 7,
                "plan_name": "TEST_Plan_60d_iter100"
            }
        )
        assert response.status_code == 200, f"Generate failed: {response.text}"
        data = response.json()
        assert data.get("success") is True
        assert data.get("status") == "draft"
        pytest.generated_plan_60d_id = data["plan_id"]
        print(f"Generated 60d plan: {data['plan_id']}")
    
    def test_generate_plan_with_notes(self, auth_headers):
        """Generate a plan with notes."""
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/buy-plans/generate",
            headers=auth_headers,
            json={
                "cover_days": 30,
                "safety_days": 7,
                "plan_name": "TEST_Plan_with_notes",
                "notes": "Test plan for iteration 100"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        pytest.generated_plan_notes_id = data["plan_id"]


class TestBuyPlanList:
    """Test GET /api/buy-planning/buy-plans"""
    
    def test_list_plans_success(self, auth_headers):
        """List all saved buy plans."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/buy-plans",
            headers=auth_headers
        )
        assert response.status_code == 200, f"List failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "plans" in data
        assert "total" in data
        assert isinstance(data["plans"], list)
        
        # Verify plan structure (without items)
        if data["plans"]:
            plan = data["plans"][0]
            assert "plan_id" in plan
            assert "plan_name" in plan
            assert "status" in plan
            assert "generated_at" in plan
            assert "totals" in plan
            # Items should NOT be included in list
            assert "items" not in plan, "Items should not be in list response"
        
        print(f"Found {data['total']} plans")
    
    def test_list_plans_filter_by_status(self, auth_headers):
        """List plans filtered by status."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/buy-plans?status=draft",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # All returned plans should be draft
        for plan in data["plans"]:
            assert plan["status"] == "draft", f"Expected draft, got {plan['status']}"
        
        print(f"Found {data['total']} draft plans")


class TestBuyPlanGet:
    """Test GET /api/buy-planning/buy-plans/{plan_id}"""
    
    def test_get_plan_success(self, auth_headers):
        """Get a single plan with full item details."""
        plan_id = getattr(pytest, 'generated_plan_id', None)
        if not plan_id:
            pytest.skip("No plan_id from generate test")
        
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get failed: {response.text}"
        data = response.json()
        
        # Verify full plan structure
        assert data.get("plan_id") == plan_id
        assert "plan_name" in data
        assert "status" in data
        assert "items" in data, "Items should be included in single plan response"
        assert "totals" in data
        assert "parameters" in data
        
        # Verify items structure
        if data["items"]:
            item = data["items"][0]
            assert "sku" in item
            assert "buy_qty" in item
            assert "style_mix" in item
            assert "daily_ros" in item
            assert "binding_constraint" in item
        
        print(f"Plan has {len(data['items'])} items")
    
    def test_get_plan_invalid_id(self, auth_headers):
        """Get plan with invalid ID returns 404."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/buy-plans/invalid_id_12345",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_get_plan_nonexistent_id(self, auth_headers):
        """Get plan with valid but nonexistent ObjectId returns 404."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/buy-plans/000000000000000000000000",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestBuyPlanUpdateItem:
    """Test PUT /api/buy-planning/buy-plans/{plan_id}/items"""
    
    def test_update_item_qty_success(self, auth_headers):
        """Update quantity for a specific item in draft plan."""
        plan_id = getattr(pytest, 'generated_plan_id', None)
        if not plan_id:
            pytest.skip("No plan_id from generate test")
        
        # First get the plan to know item count
        get_response = requests.get(
            f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        plan_data = get_response.json()
        
        if not plan_data.get("items"):
            pytest.skip("Plan has no items to update")
        
        original_qty = plan_data["items"][0].get("buy_qty", 0)
        new_qty = original_qty + 100
        
        # Update item at index 0
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}/items",
            headers=auth_headers,
            json={
                "item_index": 0,
                "new_qty": new_qty
            }
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        data = response.json()
        
        assert data.get("success") is True
        assert data.get("item_index") == 0
        assert data.get("new_qty") == new_qty
        
        # Verify the update persisted
        verify_response = requests.get(
            f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}",
            headers=auth_headers
        )
        verify_data = verify_response.json()
        assert verify_data["items"][0].get("edited_qty") == new_qty
        assert verify_data["items"][0].get("edited_by") == TEST_EMAIL
        
        print(f"Updated item 0 qty from {original_qty} to {new_qty}")
    
    def test_update_item_invalid_index(self, auth_headers):
        """Update with invalid item index returns 400."""
        plan_id = getattr(pytest, 'generated_plan_id', None)
        if not plan_id:
            pytest.skip("No plan_id from generate test")
        
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}/items",
            headers=auth_headers,
            json={
                "item_index": 99999,
                "new_qty": 100
            }
        )
        assert response.status_code == 400


class TestBuyPlanApprove:
    """Test POST /api/buy-planning/buy-plans/{plan_id}/approve"""
    
    def test_approve_draft_plan_success(self, auth_headers):
        """Approve a draft plan changes status to approved."""
        plan_id = getattr(pytest, 'generated_plan_60d_id', None)
        if not plan_id:
            pytest.skip("No plan_id from generate test")
        
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}/approve",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Approve failed: {response.text}"
        data = response.json()
        
        assert data.get("success") is True
        assert data.get("status") == "approved"
        assert "approved_at" in data
        
        # Verify the status persisted
        verify_response = requests.get(
            f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}",
            headers=auth_headers
        )
        verify_data = verify_response.json()
        assert verify_data["status"] == "approved"
        assert verify_data.get("approved_by") == TEST_EMAIL
        
        print(f"Plan {plan_id} approved")
    
    def test_approve_already_approved_plan_fails(self, auth_headers):
        """Approving an already approved plan returns 400."""
        plan_id = getattr(pytest, 'generated_plan_60d_id', None)
        if not plan_id:
            pytest.skip("No plan_id from generate test")
        
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}/approve",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "already" in response.json().get("detail", "").lower()


class TestBuyPlanDelete:
    """Test DELETE /api/buy-planning/buy-plans/{plan_id}"""
    
    def test_delete_draft_plan_success(self, auth_headers):
        """Delete a draft plan succeeds."""
        plan_id = getattr(pytest, 'generated_plan_notes_id', None)
        if not plan_id:
            pytest.skip("No plan_id from generate test")
        
        response = requests.delete(
            f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Delete failed: {response.text}"
        data = response.json()
        
        assert data.get("success") is True
        assert data.get("deleted") is True
        
        # Verify the plan is gone
        verify_response = requests.get(
            f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}",
            headers=auth_headers
        )
        assert verify_response.status_code == 404
        
        print(f"Plan {plan_id} deleted")
    
    def test_delete_approved_plan_fails(self, auth_headers):
        """Deleting an approved plan returns 400."""
        plan_id = getattr(pytest, 'generated_plan_60d_id', None)
        if not plan_id:
            pytest.skip("No plan_id from generate test")
        
        response = requests.delete(
            f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "non-draft" in response.json().get("detail", "").lower()
    
    def test_delete_nonexistent_plan(self, auth_headers):
        """Deleting nonexistent plan returns 404."""
        response = requests.delete(
            f"{BASE_URL}/api/buy-planning/buy-plans/000000000000000000000000",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestBuyPlanUpdateApprovedPlan:
    """Test that approved plans cannot be edited."""
    
    def test_update_approved_plan_fails(self, auth_headers):
        """Updating item in approved plan returns 400."""
        plan_id = getattr(pytest, 'generated_plan_60d_id', None)
        if not plan_id:
            pytest.skip("No plan_id from generate test")
        
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}/items",
            headers=auth_headers,
            json={
                "item_index": 0,
                "new_qty": 999
            }
        )
        assert response.status_code == 400
        assert "non-draft" in response.json().get("detail", "").lower()


class TestCleanup:
    """Cleanup test data."""
    
    def test_cleanup_remaining_test_plans(self, auth_headers):
        """Delete remaining test plans."""
        # Get all plans
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/buy-plans?limit=50",
            headers=auth_headers
        )
        if response.status_code != 200:
            return
        
        data = response.json()
        deleted = 0
        for plan in data.get("plans", []):
            if plan.get("plan_name", "").startswith("TEST_") and plan.get("status") == "draft":
                del_response = requests.delete(
                    f"{BASE_URL}/api/buy-planning/buy-plans/{plan['plan_id']}",
                    headers=auth_headers
                )
                if del_response.status_code == 200:
                    deleted += 1
        
        print(f"Cleaned up {deleted} test plans")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
