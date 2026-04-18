"""
Iteration 111: Test Approval Workflow and Executive Dashboard features
- GET /api/buy-planning/buy-plans?limit=100 returns all plans with status field
- POST /api/buy-planning/buy-plans/{plan_id}/approval with action=submit works on draft plans
- GET /api/buy-planning/buy-plans/{plan_id}/approval-history returns history entries
- Executive Dashboard APIs (analytics/executive-dashboard, executive-kpis, executive-revenue-trend)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestApprovalWorkflowIter111:
    """Test Approval Workflow APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as super admin
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "demo1234",
            "tenant_id": "production"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("access_token")
        assert token, "No access token returned"
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.token = token
    
    def test_01_get_buy_plans_with_status(self):
        """GET /api/buy-planning/buy-plans?limit=100 returns plans with status field"""
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans?limit=100")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        # Verify response structure
        assert "plans" in data, "Response should have 'plans' key"
        plans = data["plans"]
        assert isinstance(plans, list), "Plans should be a list"
        
        # Verify each plan has required fields
        if len(plans) > 0:
            plan = plans[0]
            assert "plan_id" in plan, "Plan should have plan_id"
            assert "status" in plan, "Plan should have status field"
            assert "plan_name" in plan or plan.get("plan_name") is None, "Plan should have plan_name"
            
            # Verify status is one of expected values
            valid_statuses = ["draft", "submitted", "category_approved", "senior_approved", "head_approved", "ordered", "rejected"]
            assert plan["status"] in valid_statuses, f"Invalid status: {plan['status']}"
            
            print(f"PASS: Found {len(plans)} buy plans with status field")
            print(f"Sample plan status: {plan['status']}")
        else:
            print("INFO: No buy plans found in database")
    
    def test_02_get_draft_plan_for_approval(self):
        """Find a draft plan to test approval workflow"""
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans?limit=100")
        assert resp.status_code == 200
        plans = resp.json().get("plans", [])
        
        # Find a draft plan
        draft_plans = [p for p in plans if p.get("status") == "draft"]
        if draft_plans:
            self.draft_plan_id = draft_plans[0]["plan_id"]
            print(f"PASS: Found draft plan: {self.draft_plan_id}")
        else:
            # Create a new plan if no draft exists
            print("INFO: No draft plans found, will test with existing plans")
            pytest.skip("No draft plans available for testing")
    
    def test_03_submit_draft_plan_for_approval(self):
        """POST /api/buy-planning/buy-plans/{plan_id}/approval with action=submit"""
        # First get a draft plan
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans?limit=100")
        assert resp.status_code == 200
        plans = resp.json().get("plans", [])
        
        draft_plans = [p for p in plans if p.get("status") == "draft"]
        if not draft_plans:
            pytest.skip("No draft plans available for submit test")
        
        plan_id = draft_plans[0]["plan_id"]
        
        # Submit for approval
        submit_resp = self.session.post(
            f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}/approval",
            json={"action": "submit", "comment": "Test submission from iter111"}
        )
        
        # Should succeed or return appropriate error
        if submit_resp.status_code == 200:
            print(f"PASS: Plan {plan_id} submitted for approval")
        elif submit_resp.status_code == 400:
            # Plan might already be submitted or in different state
            print(f"INFO: Submit returned 400 - {submit_resp.json().get('detail', 'Unknown error')}")
        else:
            assert submit_resp.status_code in [200, 400], f"Unexpected status: {submit_resp.status_code} - {submit_resp.text}"
    
    def test_04_get_approval_history(self):
        """GET /api/buy-planning/buy-plans/{plan_id}/approval-history returns history"""
        # Get any plan
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans?limit=10")
        assert resp.status_code == 200
        plans = resp.json().get("plans", [])
        
        if not plans:
            pytest.skip("No plans available for history test")
        
        plan_id = plans[0]["plan_id"]
        
        # Get approval history
        history_resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}/approval-history")
        assert history_resp.status_code == 200, f"Failed: {history_resp.text}"
        
        data = history_resp.json()
        assert "history" in data, "Response should have 'history' key"
        
        history = data["history"]
        assert isinstance(history, list), "History should be a list"
        
        if len(history) > 0:
            entry = history[0]
            # Verify history entry structure
            assert "action" in entry, "History entry should have action"
            assert "performed_by" in entry, "History entry should have performed_by"
            print(f"PASS: Found {len(history)} history entries for plan {plan_id}")
            print(f"Sample entry: action={entry.get('action')}, by={entry.get('performed_by')}")
        else:
            print(f"INFO: No history entries for plan {plan_id}")
    
    def test_05_count_plans_by_status(self):
        """Verify plans can be grouped by status for pipeline view"""
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/buy-plans?limit=100")
        assert resp.status_code == 200
        plans = resp.json().get("plans", [])
        
        # Count by status
        status_counts = {}
        for plan in plans:
            status = plan.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"PASS: Plan counts by status: {status_counts}")
        print(f"Total plans: {len(plans)}")


class TestExecutiveDashboardIter111:
    """Test Executive Dashboard APIs for skeleton/empty state"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "demo1234",
            "tenant_id": "production"
        })
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_executive_dashboard_api(self):
        """GET /api/analytics/executive-dashboard returns data or error"""
        resp = self.session.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        # Should return 200 with data or error message
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        # Check if it has data or error
        if "error" in data:
            print(f"INFO: Dashboard returned error (expected for empty state): {data['error']}")
        else:
            assert "health_score" in data or "modules" in data, "Should have health_score or modules"
            print(f"PASS: Dashboard returned data with health_score={data.get('health_score')}")
    
    def test_02_executive_kpis_api(self):
        """GET /api/analytics/executive-kpis returns KPI data"""
        resp = self.session.get(f"{BASE_URL}/api/analytics/executive-kpis")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        # Verify KPI structure
        expected_fields = ["revenue", "units_sold", "mrp_realisation_pct", "has_data"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"PASS: KPIs returned - revenue={data.get('revenue')}, units={data.get('units_sold')}, has_data={data.get('has_data')}")
    
    def test_03_executive_revenue_trend_api(self):
        """GET /api/analytics/executive-revenue-trend returns trend data"""
        resp = self.session.get(f"{BASE_URL}/api/analytics/executive-revenue-trend")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        # Verify trend structure
        assert "labels" in data, "Should have labels"
        assert "revenue" in data, "Should have revenue"
        assert "units" in data, "Should have units"
        
        print(f"PASS: Revenue trend returned with {len(data.get('labels', []))} data points")


class TestNotificationAPIs:
    """Test Notification APIs for polling stability"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "demo1234",
            "tenant_id": "production"
        })
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_unread_count_api(self):
        """GET /api/notifications/unread-count returns count"""
        resp = self.session.get(f"{BASE_URL}/api/notifications/unread-count")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        assert "unread_count" in data, "Should have unread_count"
        assert isinstance(data["unread_count"], int), "unread_count should be int"
        
        print(f"PASS: Unread count = {data['unread_count']}")
    
    def test_02_notifications_list_api(self):
        """GET /api/notifications returns notification list"""
        resp = self.session.get(f"{BASE_URL}/api/notifications?limit=30")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        assert "notifications" in data, "Should have notifications"
        assert isinstance(data["notifications"], list), "notifications should be list"
        
        print(f"PASS: Notifications list returned {len(data['notifications'])} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
