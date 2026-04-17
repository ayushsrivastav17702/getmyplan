"""
Iteration 103: Multi-Level Approval Workflow Tests
Tests the extended buy plan approval workflow:
- Status chain: draft → submitted → category_approved → senior_approved → head_approved → ordered
- Rejection and request_changes flows
- Approval history tracking
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestApprovalWorkflow:
    """Multi-level approval workflow tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as super_admin
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "demo1234"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("access_token")
        assert token, "No access_token in login response"
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.plan_id = None
        yield
        # Cleanup: delete test plan if created
        if self.plan_id:
            try:
                self.session.delete(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}")
            except:
                pass
    
    def _generate_plan(self):
        """Helper to generate a new buy plan"""
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/generate", json={
            "plan_name": "TEST_Approval_Workflow_Plan",
            "cover_days": 30,
            "safety_days": 7
        })
        assert resp.status_code == 200, f"Generate plan failed: {resp.text}"
        data = resp.json()
        assert data.get("success") == True
        assert "plan_id" in data
        self.plan_id = data["plan_id"]
        return data
    
    # ═══════════════════════════════════════════════════
    # TEST: Submit action (draft → submitted)
    # ═══════════════════════════════════════════════════
    
    def test_01_submit_draft_to_submitted(self):
        """POST /api/buy-planning/buy-plans/{plan_id}/approval with action=submit moves draft→submitted"""
        self._generate_plan()
        
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "submit"
        })
        assert resp.status_code == 200, f"Submit failed: {resp.text}"
        data = resp.json()
        assert data.get("success") == True
        assert data.get("old_status") == "draft"
        assert data.get("new_status") == "submitted"
        assert data.get("action") == "submit"
        
        # Verify plan status changed
        get_resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}")
        assert get_resp.status_code == 200
        plan = get_resp.json()
        assert plan.get("status") == "submitted"
        assert plan.get("submitted_at") is not None
        assert plan.get("submitted_by") == "admin@demo.com"
    
    # ═══════════════════════════════════════════════════
    # TEST: Category approval (submitted → category_approved)
    # ═══════════════════════════════════════════════════
    
    def test_02_approve_category(self):
        """POST with action=approve_category moves submitted→category_approved"""
        self._generate_plan()
        
        # First submit
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        
        # Then approve category
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "approve_category",
            "comment": "Category approved by planner"
        })
        assert resp.status_code == 200, f"Category approval failed: {resp.text}"
        data = resp.json()
        assert data.get("success") == True
        assert data.get("old_status") == "submitted"
        assert data.get("new_status") == "category_approved"
        
        # Verify
        get_resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}")
        plan = get_resp.json()
        assert plan.get("status") == "category_approved"
        assert plan.get("category_approved_at") is not None
        assert plan.get("category_approved_by") == "admin@demo.com"
    
    # ═══════════════════════════════════════════════════
    # TEST: Senior approval (category_approved → senior_approved)
    # ═══════════════════════════════════════════════════
    
    def test_03_approve_senior(self):
        """POST with action=approve_senior moves category_approved→senior_approved"""
        self._generate_plan()
        
        # Progress through stages
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_category"})
        
        # Senior approval
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "approve_senior",
            "comment": "Senior approved"
        })
        assert resp.status_code == 200, f"Senior approval failed: {resp.text}"
        data = resp.json()
        assert data.get("success") == True
        assert data.get("old_status") == "category_approved"
        assert data.get("new_status") == "senior_approved"
        
        # Verify
        get_resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}")
        plan = get_resp.json()
        assert plan.get("status") == "senior_approved"
        assert plan.get("senior_approved_at") is not None
        assert plan.get("senior_approved_by") == "admin@demo.com"
    
    # ═══════════════════════════════════════════════════
    # TEST: Head approval (senior_approved → head_approved)
    # ═══════════════════════════════════════════════════
    
    def test_04_approve_head(self):
        """POST with action=approve_head moves senior_approved→head_approved"""
        self._generate_plan()
        
        # Progress through stages
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_category"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_senior"})
        
        # Head approval
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "approve_head",
            "comment": "Final head approval"
        })
        assert resp.status_code == 200, f"Head approval failed: {resp.text}"
        data = resp.json()
        assert data.get("success") == True
        assert data.get("old_status") == "senior_approved"
        assert data.get("new_status") == "head_approved"
        
        # Verify
        get_resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}")
        plan = get_resp.json()
        assert plan.get("status") == "head_approved"
        assert plan.get("head_approved_at") is not None
        assert plan.get("head_approved_by") == "admin@demo.com"
    
    # ═══════════════════════════════════════════════════
    # TEST: Finance acknowledgment (head_approved → ordered)
    # ═══════════════════════════════════════════════════
    
    def test_05_finance_ack(self):
        """POST with action=finance_ack moves head_approved→ordered"""
        self._generate_plan()
        
        # Progress through all stages
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_category"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_senior"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_head"})
        
        # Finance acknowledgment
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "finance_ack",
            "comment": "Finance acknowledged, order placed"
        })
        assert resp.status_code == 200, f"Finance ack failed: {resp.text}"
        data = resp.json()
        assert data.get("success") == True
        assert data.get("old_status") == "head_approved"
        assert data.get("new_status") == "ordered"
        
        # Verify
        get_resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}")
        plan = get_resp.json()
        assert plan.get("status") == "ordered"
        assert plan.get("ordered_at") is not None
        assert plan.get("ordered_by") == "admin@demo.com"
        
        # Cannot delete ordered plan
        self.plan_id = None  # Don't try to delete in cleanup
    
    # ═══════════════════════════════════════════════════
    # TEST: Reject action (requires comment)
    # ═══════════════════════════════════════════════════
    
    def test_06_reject_requires_comment(self):
        """POST with action=reject without comment returns 400"""
        self._generate_plan()
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "reject"
        })
        assert resp.status_code == 400, f"Expected 400 for reject without comment, got {resp.status_code}"
        assert "comment" in resp.text.lower() or "required" in resp.text.lower()
    
    def test_07_reject_with_comment(self):
        """POST with action=reject and comment moves to rejected"""
        self._generate_plan()
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "reject",
            "comment": "Budget exceeded, please revise"
        })
        assert resp.status_code == 200, f"Reject failed: {resp.text}"
        data = resp.json()
        assert data.get("success") == True
        assert data.get("new_status") == "rejected"
        
        # Verify
        get_resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}")
        plan = get_resp.json()
        assert plan.get("status") == "rejected"
        assert plan.get("approvals", {}).get("reject", {}).get("comment") == "Budget exceeded, please revise"
        
        self.plan_id = None  # Cannot delete rejected plan
    
    # ═══════════════════════════════════════════════════
    # TEST: Request changes (requires comment, moves to draft)
    # ═══════════════════════════════════════════════════
    
    def test_08_request_changes_requires_comment(self):
        """POST with action=request_changes without comment returns 400"""
        self._generate_plan()
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "request_changes"
        })
        assert resp.status_code == 400, f"Expected 400 for request_changes without comment, got {resp.status_code}"
    
    def test_09_request_changes_with_comment(self):
        """POST with action=request_changes and comment moves back to draft"""
        self._generate_plan()
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "request_changes",
            "comment": "Please add more Core styles"
        })
        assert resp.status_code == 200, f"Request changes failed: {resp.text}"
        data = resp.json()
        assert data.get("success") == True
        assert data.get("old_status") == "submitted"
        assert data.get("new_status") == "draft"
        
        # Verify plan is back to draft
        get_resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}")
        plan = get_resp.json()
        assert plan.get("status") == "draft"
    
    # ═══════════════════════════════════════════════════
    # TEST: Invalid action from wrong status returns 400
    # ═══════════════════════════════════════════════════
    
    def test_10_invalid_action_from_wrong_status(self):
        """Cannot approve_category from draft status"""
        self._generate_plan()
        
        # Try to approve_category directly from draft (should fail)
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "approve_category"
        })
        assert resp.status_code == 400, f"Expected 400 for invalid transition, got {resp.status_code}"
        assert "cannot" in resp.text.lower() or "draft" in resp.text.lower()
    
    def test_11_invalid_action_approve_senior_from_submitted(self):
        """Cannot approve_senior from submitted status"""
        self._generate_plan()
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "approve_senior"
        })
        assert resp.status_code == 400, f"Expected 400 for invalid transition, got {resp.status_code}"
    
    def test_12_invalid_action_name(self):
        """Invalid action name returns 400"""
        self._generate_plan()
        
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "invalid_action"
        })
        assert resp.status_code == 400, f"Expected 400 for invalid action, got {resp.status_code}"
    
    # ═══════════════════════════════════════════════════
    # TEST: Approval history endpoint
    # ═══════════════════════════════════════════════════
    
    def test_13_approval_history(self):
        """GET /api/buy-planning/buy-plans/{plan_id}/approval-history returns ordered list"""
        self._generate_plan()
        
        # Perform multiple actions
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_category", "comment": "Cat approved"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_senior", "comment": "Senior approved"})
        
        # Get history
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval-history")
        assert resp.status_code == 200, f"Get history failed: {resp.text}"
        data = resp.json()
        
        assert "history" in data
        history = data["history"]
        assert len(history) >= 3, f"Expected at least 3 history entries, got {len(history)}"
        
        # Check history entries have required fields
        for entry in history:
            assert "action" in entry
            assert "from_status" in entry
            assert "to_status" in entry
            assert "performed_by" in entry
            assert "performed_at" in entry
        
        # Verify order (should be chronological)
        actions = [h["action"] for h in history]
        assert "submit" in actions
        assert "approve_category" in actions
        assert "approve_senior" in actions
    
    def test_14_approval_history_empty_for_new_plan(self):
        """New plan has empty approval history"""
        self._generate_plan()
        
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval-history")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("history") == [] or data.get("total") == 0
    
    # ═══════════════════════════════════════════════════
    # TEST: Get plan returns approval fields
    # ═══════════════════════════════════════════════════
    
    def test_15_get_plan_returns_approval_fields(self):
        """GET /api/buy-planning/buy-plans/{plan_id} returns approval timestamp fields"""
        self._generate_plan()
        
        # Progress through stages
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_category"})
        
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}")
        assert resp.status_code == 200
        plan = resp.json()
        
        # Check approval fields exist
        assert "approvals" in plan
        assert "submitted_at" in plan
        assert "submitted_by" in plan
        assert "category_approved_at" in plan
        assert "category_approved_by" in plan
        
        # Verify values
        assert plan["submitted_at"] is not None
        assert plan["submitted_by"] == "admin@demo.com"
        assert plan["category_approved_at"] is not None
        assert plan["category_approved_by"] == "admin@demo.com"
    
    # ═══════════════════════════════════════════════════
    # TEST: Full workflow end-to-end
    # ═══════════════════════════════════════════════════
    
    def test_16_full_workflow_e2e(self):
        """Complete workflow: draft → submitted → category → senior → head → ordered"""
        self._generate_plan()
        
        # Verify initial status
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}")
        assert resp.json().get("status") == "draft"
        
        # Submit
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        assert resp.status_code == 200
        assert resp.json().get("new_status") == "submitted"
        
        # Category approve
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_category"})
        assert resp.status_code == 200
        assert resp.json().get("new_status") == "category_approved"
        
        # Senior approve
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_senior"})
        assert resp.status_code == 200
        assert resp.json().get("new_status") == "senior_approved"
        
        # Head approve
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_head"})
        assert resp.status_code == 200
        assert resp.json().get("new_status") == "head_approved"
        
        # Finance ack
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "finance_ack"})
        assert resp.status_code == 200
        assert resp.json().get("new_status") == "ordered"
        
        # Verify final state
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}")
        plan = resp.json()
        assert plan.get("status") == "ordered"
        assert plan.get("ordered_at") is not None
        
        # Check history has all 5 actions
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval-history")
        history = resp.json().get("history", [])
        assert len(history) == 5
        
        self.plan_id = None  # Cannot delete ordered plan
    
    # ═══════════════════════════════════════════════════
    # TEST: Backward compat - old /approve endpoint
    # ═══════════════════════════════════════════════════
    
    def test_17_backward_compat_approve_endpoint(self):
        """POST /api/buy-planning/buy-plans/{plan_id}/approve still works (sets to ordered)"""
        self._generate_plan()
        
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approve")
        assert resp.status_code == 200, f"Old approve endpoint failed: {resp.text}"
        data = resp.json()
        assert data.get("success") == True
        assert data.get("status") == "ordered"
        
        # Verify plan is ordered
        get_resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}")
        plan = get_resp.json()
        assert plan.get("status") == "ordered"
        
        self.plan_id = None  # Cannot delete ordered plan


class TestApprovalWorkflowEdgeCases:
    """Edge cases and error handling for approval workflow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "demo1234"
        })
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.plan_id = None
        yield
        if self.plan_id:
            try:
                self.session.delete(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}")
            except:
                pass
    
    def _generate_plan(self):
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/generate", json={
            "plan_name": "TEST_Edge_Case_Plan",
            "cover_days": 30
        })
        self.plan_id = resp.json().get("plan_id")
        return resp.json()
    
    def test_18_reject_from_category_approved(self):
        """Can reject from category_approved status"""
        self._generate_plan()
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_category"})
        
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "reject",
            "comment": "Rejected at category level"
        })
        assert resp.status_code == 200
        assert resp.json().get("new_status") == "rejected"
        self.plan_id = None
    
    def test_19_reject_from_senior_approved(self):
        """Can reject from senior_approved status"""
        self._generate_plan()
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_category"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_senior"})
        
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "reject",
            "comment": "Rejected at senior level"
        })
        assert resp.status_code == 200
        assert resp.json().get("new_status") == "rejected"
        self.plan_id = None
    
    def test_20_reject_from_head_approved(self):
        """Can reject from head_approved status"""
        self._generate_plan()
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_category"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_senior"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_head"})
        
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "reject",
            "comment": "Rejected at head level"
        })
        assert resp.status_code == 200
        assert resp.json().get("new_status") == "rejected"
        self.plan_id = None
    
    def test_21_cannot_reject_from_draft(self):
        """Cannot reject from draft status"""
        self._generate_plan()
        
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "reject",
            "comment": "Trying to reject draft"
        })
        assert resp.status_code == 400
    
    def test_22_request_changes_from_category_approved(self):
        """Can request_changes from category_approved"""
        self._generate_plan()
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_category"})
        
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "request_changes",
            "comment": "Need more details"
        })
        assert resp.status_code == 200
        assert resp.json().get("new_status") == "draft"
    
    def test_23_request_changes_from_senior_approved(self):
        """Can request_changes from senior_approved"""
        self._generate_plan()
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_category"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_senior"})
        
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "request_changes",
            "comment": "Revise quantities"
        })
        assert resp.status_code == 200
        assert resp.json().get("new_status") == "draft"
    
    def test_24_cannot_request_changes_from_head_approved(self):
        """Cannot request_changes from head_approved (only reject allowed)"""
        self._generate_plan()
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "submit"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_category"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_senior"})
        self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={"action": "approve_head"})
        
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/{self.plan_id}/approval", json={
            "action": "request_changes",
            "comment": "Too late for changes"
        })
        assert resp.status_code == 400
    
    def test_25_invalid_plan_id(self):
        """Invalid plan ID returns 404"""
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/invalid_id_123/approval", json={
            "action": "submit"
        })
        assert resp.status_code == 404
    
    def test_26_nonexistent_plan_id(self):
        """Nonexistent plan ID returns 404"""
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-plans/507f1f77bcf86cd799439011/approval", json={
            "action": "submit"
        })
        assert resp.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
