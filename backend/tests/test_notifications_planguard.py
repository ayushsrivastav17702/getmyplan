"""
Test Suite for Notification System and PlanGuard Module Access
Iteration 48: Testing SFTP Alert/Notification System and Plan-based access control

Tests:
- Notification CRUD endpoints
- Plan info returned on login
- Module access based on plan type
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
DEMO_TENANT = "demo"
DEMO_ADMIN_EMAIL = "admin@demo.com"
DEMO_ADMIN_PASSWORD = "demo1234"


class TestAuthWithPlanInfo:
    """Test that login returns plan_info with modules"""
    
    def test_login_returns_plan_info(self):
        """Login with demo admin should return plan_info with modules"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_ADMIN_EMAIL, "password": DEMO_ADMIN_PASSWORD},
            headers={"X-Tenant-ID": DEMO_TENANT}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Missing access_token"
        assert "plan_info" in data, "Missing plan_info in login response"
        
        plan_info = data["plan_info"]
        assert "modules" in plan_info, "Missing modules in plan_info"
        assert "limits" in plan_info, "Missing limits in plan_info"
        
        # Demo tenant should have professional plan - all modules full access
        modules = plan_info["modules"]
        assert "dashboard" in modules, "Missing dashboard module"
        assert "ai_forecasting" in modules, "Missing ai_forecasting module"
        assert "buy_plan" in modules, "Missing buy_plan module"
        
        # Professional plan should have full access to all modules
        assert modules["dashboard"]["access"] == "full", "Dashboard should have full access"
        assert modules["ai_forecasting"]["access"] == "full", "AI forecasting should have full access"
        assert modules["buy_plan"]["access"] == "full", "Buy plan should have full access"
        
        print(f"✓ Login returns plan_info with {len(modules)} modules")
        print(f"✓ Plan type: {data.get('plan_type', 'unknown')}")
        return data["access_token"]


class TestNotificationEndpoints:
    """Test notification CRUD endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for authenticated requests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_ADMIN_EMAIL, "password": DEMO_ADMIN_PASSWORD},
            headers={"X-Tenant-ID": DEMO_TENANT}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Tenant-ID": DEMO_TENANT,
            "Content-Type": "application/json"
        }
    
    def test_get_notifications(self):
        """GET /api/notifications returns notifications list with unread_count"""
        response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed to get notifications: {response.text}"
        
        data = response.json()
        assert "notifications" in data, "Missing notifications array"
        assert "unread_count" in data, "Missing unread_count"
        assert "total" in data, "Missing total count"
        
        assert isinstance(data["notifications"], list), "notifications should be a list"
        assert isinstance(data["unread_count"], int), "unread_count should be an integer"
        
        print(f"✓ GET /api/notifications - {len(data['notifications'])} notifications, {data['unread_count']} unread")
    
    def test_get_unread_count(self):
        """GET /api/notifications/unread-count returns unread count"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/unread-count",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed to get unread count: {response.text}"
        
        data = response.json()
        assert "unread_count" in data, "Missing unread_count"
        assert isinstance(data["unread_count"], int), "unread_count should be an integer"
        
        print(f"✓ GET /api/notifications/unread-count - {data['unread_count']} unread")
    
    def test_trigger_daily_summary(self):
        """POST /api/notifications/trigger-daily-summary creates a notification"""
        response = requests.post(
            f"{BASE_URL}/api/notifications/trigger-daily-summary",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed to trigger daily summary: {response.text}"
        
        data = response.json()
        assert "summary" in data, "Missing summary in response"
        assert "notification" in data, "Missing notification in response"
        
        notification = data["notification"]
        assert "type" in notification, "Missing type in notification"
        assert "title" in notification, "Missing title in notification"
        assert "message" in notification, "Missing message in notification"
        assert "severity" in notification, "Missing severity in notification"
        assert notification["type"] == "sftp_daily_summary", f"Expected sftp_daily_summary, got {notification['type']}"
        
        print(f"✓ POST /api/notifications/trigger-daily-summary - Created notification: {notification['title']}")
    
    def test_mark_all_read(self):
        """PUT /api/notifications/mark-all-read marks notifications as read"""
        response = requests.put(
            f"{BASE_URL}/api/notifications/mark-all-read",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed to mark all read: {response.text}"
        
        data = response.json()
        assert "marked_read" in data, "Missing marked_read count"
        
        print(f"✓ PUT /api/notifications/mark-all-read - Marked {data['marked_read']} as read")
        
        # Verify unread count is now 0
        verify_response = requests.get(
            f"{BASE_URL}/api/notifications/unread-count",
            headers=self.headers
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["unread_count"] == 0, "Unread count should be 0 after marking all read"
        
        print("✓ Verified unread_count is 0 after mark-all-read")
    
    def test_clear_old_notifications(self):
        """DELETE /api/notifications/clear?days=7 clears old notifications"""
        response = requests.delete(
            f"{BASE_URL}/api/notifications/clear",
            params={"days": 7},
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed to clear notifications: {response.text}"
        
        data = response.json()
        assert "deleted" in data, "Missing deleted count"
        
        print(f"✓ DELETE /api/notifications/clear?days=7 - Deleted {data['deleted']} old notifications")
    
    def test_notification_workflow(self):
        """Full workflow: create notification, verify unread, mark read, verify"""
        # 1. Create a notification via trigger-daily-summary
        create_response = requests.post(
            f"{BASE_URL}/api/notifications/trigger-daily-summary",
            headers=self.headers
        )
        assert create_response.status_code == 200, "Failed to create notification"
        print("✓ Step 1: Created notification via trigger-daily-summary")
        
        # 2. Get unread count - should be at least 1
        unread_response = requests.get(
            f"{BASE_URL}/api/notifications/unread-count",
            headers=self.headers
        )
        assert unread_response.status_code == 200
        unread_before = unread_response.json()["unread_count"]
        assert unread_before >= 1, f"Expected at least 1 unread, got {unread_before}"
        print(f"✓ Step 2: Unread count is {unread_before}")
        
        # 3. Get notifications list
        list_response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=self.headers
        )
        assert list_response.status_code == 200
        notifications = list_response.json()["notifications"]
        assert len(notifications) >= 1, "Expected at least 1 notification"
        print(f"✓ Step 3: Got {len(notifications)} notifications")
        
        # 4. Mark all as read
        mark_response = requests.put(
            f"{BASE_URL}/api/notifications/mark-all-read",
            headers=self.headers
        )
        assert mark_response.status_code == 200
        print(f"✓ Step 4: Marked {mark_response.json()['marked_read']} as read")
        
        # 5. Verify unread count is 0
        verify_response = requests.get(
            f"{BASE_URL}/api/notifications/unread-count",
            headers=self.headers
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["unread_count"] == 0
        print("✓ Step 5: Verified unread count is 0")


class TestPlanAccessControl:
    """Test plan-based module access control"""
    
    def test_starter_plan_modules(self):
        """Verify starter plan has correct module access levels"""
        from core.plan_access import get_plan_info
        
        plan_info = get_plan_info("starter")
        modules = plan_info["modules"]
        
        # Starter plan: full access
        assert modules["dashboard"]["access"] == "full", "Dashboard should be full"
        assert modules["topseller"]["access"] == "full", "Topseller should be full"
        assert modules["gap_analysis"]["access"] == "full", "Gap analysis should be full"
        
        # Starter plan: view-only
        assert modules["stock_out"]["access"] == "view_only", "Stock-out should be view_only"
        assert modules["doh_analysis"]["access"] == "view_only", "DOH should be view_only"
        assert modules["planogram"]["access"] == "view_only", "Planogram should be view_only"
        
        # Starter plan: locked (none)
        assert modules["ai_forecasting"]["access"] == "none", "AI forecasting should be none"
        assert modules["buy_plan"]["access"] == "none", "Buy plan should be none"
        assert modules["multi_channel"]["access"] == "none", "Multi-channel should be none"
        
        print("✓ Starter plan module access verified")
    
    def test_professional_plan_modules(self):
        """Verify professional plan has full access to all modules"""
        from core.plan_access import get_plan_info
        
        plan_info = get_plan_info("professional")
        modules = plan_info["modules"]
        
        # Professional plan: all modules should be full
        for module_name, module_info in modules.items():
            assert module_info["access"] == "full", f"{module_name} should be full for professional plan"
        
        print(f"✓ Professional plan - all {len(modules)} modules have full access")
    
    def test_enterprise_plan_modules(self):
        """Verify enterprise plan has full access to all modules"""
        from core.plan_access import get_plan_info
        
        plan_info = get_plan_info("enterprise")
        modules = plan_info["modules"]
        
        # Enterprise plan: all modules should be full
        for module_name, module_info in modules.items():
            assert module_info["access"] == "full", f"{module_name} should be full for enterprise plan"
        
        print(f"✓ Enterprise plan - all {len(modules)} modules have full access")
    
    def test_trial_plan_modules(self):
        """Verify trial plan has full access to all modules"""
        from core.plan_access import get_plan_info
        
        plan_info = get_plan_info("trial")
        modules = plan_info["modules"]
        
        # Trial plan: all modules should be full
        for module_name, module_info in modules.items():
            assert module_info["access"] == "full", f"{module_name} should be full for trial plan"
        
        print(f"✓ Trial plan - all {len(modules)} modules have full access")


class TestHealthCheck:
    """Basic health check to ensure API is running"""
    
    def test_health_endpoint(self):
        """GET /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        
        data = response.json()
        assert data.get("status") in ["healthy", "degraded"], f"Unexpected status: {data.get('status')}"
        
        print(f"✓ Health check: {data.get('status')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
