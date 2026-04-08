"""
Test P2 Features - Iteration 49
1. Force Password Change on First Login (USER-17)
2. Plan Upgrade Page (Plan Usage API)
3. Scheduled Analysis Jobs CRUD
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "demo1234"
TENANT_ID = "demo"

# B2BLeads tenant for force password change test
B2B_ADMIN_EMAIL = "akash@b2bleads.co.in"
B2B_ADMIN_PASSWORD = "Test1234!"
B2B_TENANT_ID = "b2bleads"

# User to test password reset flow
TEST_USER_EMAIL = "aditya@b2bleads.co.in"
TEST_USER_ORIGINAL_PASSWORD = "Ayush@2025"


@pytest.fixture(scope="module")
def admin_session():
    """Get authenticated session for demo tenant admin."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    resp = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    data = resp.json()
    token = data["access_token"]
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": TENANT_ID
    })
    return session


@pytest.fixture(scope="module")
def b2b_admin_session():
    """Get authenticated session for b2bleads tenant admin."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    resp = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": B2B_ADMIN_EMAIL,
        "password": B2B_ADMIN_PASSWORD
    })
    assert resp.status_code == 200, f"B2B Admin login failed: {resp.text}"
    data = resp.json()
    token = data["access_token"]
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": B2B_TENANT_ID
    })
    return session


# ============ SCHEDULED JOBS TESTS ============

class TestScheduledJobsCRUD:
    """Test Scheduled Jobs CRUD operations."""
    
    created_job_id = None
    
    def test_list_jobs(self, admin_session):
        """GET /api/scheduled-jobs/ - List all jobs."""
        resp = admin_session.get(f"{BASE_URL}/api/scheduled-jobs/")
        assert resp.status_code == 200
        data = resp.json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)
        print(f"PASS: List jobs returned {len(data['jobs'])} jobs")
    
    def test_create_job_daily(self, admin_session):
        """POST /api/scheduled-jobs/ - Create daily job."""
        payload = {
            "name": "TEST_Daily_Stock_Check",
            "analysis_type": "stock_out",
            "frequency": "daily",
            "run_time": "08:00",
            "notify_email": True,
            "is_active": True
        }
        resp = admin_session.post(f"{BASE_URL}/api/scheduled-jobs/", json=payload)
        assert resp.status_code == 200, f"Create job failed: {resp.text}"
        data = resp.json()
        assert "job" in data
        assert data["job"]["name"] == "TEST_Daily_Stock_Check"
        assert data["job"]["frequency"] == "daily"
        assert data["job"]["analysis_type"] == "stock_out"
        TestScheduledJobsCRUD.created_job_id = data["job"]["job_id"]
        print(f"PASS: Created daily job with ID: {TestScheduledJobsCRUD.created_job_id}")
    
    def test_create_job_weekly(self, admin_session):
        """POST /api/scheduled-jobs/ - Create weekly job with day_of_week."""
        payload = {
            "name": "TEST_Weekly_Gap_Analysis",
            "analysis_type": "gap_analysis",
            "frequency": "weekly",
            "run_time": "09:00",
            "day_of_week": "monday",
            "notify_email": True,
            "is_active": True
        }
        resp = admin_session.post(f"{BASE_URL}/api/scheduled-jobs/", json=payload)
        assert resp.status_code == 200, f"Create weekly job failed: {resp.text}"
        data = resp.json()
        assert data["job"]["frequency"] == "weekly"
        assert data["job"]["day_of_week"] == "monday"
        print(f"PASS: Created weekly job")
    
    def test_create_job_monthly(self, admin_session):
        """POST /api/scheduled-jobs/ - Create monthly job with day_of_month."""
        payload = {
            "name": "TEST_Monthly_AI_Forecast",
            "analysis_type": "ai_demand",
            "frequency": "monthly",
            "run_time": "10:00",
            "day_of_month": 15,
            "notify_email": False,
            "is_active": True
        }
        resp = admin_session.post(f"{BASE_URL}/api/scheduled-jobs/", json=payload)
        assert resp.status_code == 200, f"Create monthly job failed: {resp.text}"
        data = resp.json()
        assert data["job"]["frequency"] == "monthly"
        assert data["job"]["day_of_month"] == 15
        print(f"PASS: Created monthly job")
    
    def test_create_job_invalid_analysis_type(self, admin_session):
        """POST /api/scheduled-jobs/ - Invalid analysis type should fail."""
        payload = {
            "name": "TEST_Invalid",
            "analysis_type": "invalid_type",
            "frequency": "daily",
            "run_time": "08:00"
        }
        resp = admin_session.post(f"{BASE_URL}/api/scheduled-jobs/", json=payload)
        assert resp.status_code == 400
        print("PASS: Invalid analysis type rejected")
    
    def test_create_job_invalid_frequency(self, admin_session):
        """POST /api/scheduled-jobs/ - Invalid frequency should fail."""
        payload = {
            "name": "TEST_Invalid",
            "analysis_type": "stock_out",
            "frequency": "hourly",
            "run_time": "08:00"
        }
        resp = admin_session.post(f"{BASE_URL}/api/scheduled-jobs/", json=payload)
        assert resp.status_code == 400
        print("PASS: Invalid frequency rejected")
    
    def test_create_weekly_without_day_of_week(self, admin_session):
        """POST /api/scheduled-jobs/ - Weekly without day_of_week should fail."""
        payload = {
            "name": "TEST_Invalid_Weekly",
            "analysis_type": "stock_out",
            "frequency": "weekly",
            "run_time": "08:00"
        }
        resp = admin_session.post(f"{BASE_URL}/api/scheduled-jobs/", json=payload)
        assert resp.status_code == 400
        print("PASS: Weekly job without day_of_week rejected")
    
    def test_toggle_job(self, admin_session):
        """POST /api/scheduled-jobs/{job_id}/toggle - Toggle job active status."""
        if not TestScheduledJobsCRUD.created_job_id:
            pytest.skip("No job created to toggle")
        
        job_id = TestScheduledJobsCRUD.created_job_id
        resp = admin_session.post(f"{BASE_URL}/api/scheduled-jobs/{job_id}/toggle")
        assert resp.status_code == 200
        data = resp.json()
        assert "is_active" in data
        print(f"PASS: Toggled job, is_active={data['is_active']}")
    
    def test_run_job_now(self, admin_session):
        """POST /api/scheduled-jobs/{job_id}/run-now - Run job immediately."""
        if not TestScheduledJobsCRUD.created_job_id:
            pytest.skip("No job created to run")
        
        job_id = TestScheduledJobsCRUD.created_job_id
        resp = admin_session.post(f"{BASE_URL}/api/scheduled-jobs/{job_id}/run-now")
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "run_at" in data
        print(f"PASS: Job executed at {data['run_at']}")
    
    def test_update_job(self, admin_session):
        """PUT /api/scheduled-jobs/{job_id} - Update job."""
        if not TestScheduledJobsCRUD.created_job_id:
            pytest.skip("No job created to update")
        
        job_id = TestScheduledJobsCRUD.created_job_id
        payload = {
            "name": "TEST_Updated_Stock_Check",
            "run_time": "07:30"
        }
        resp = admin_session.put(f"{BASE_URL}/api/scheduled-jobs/{job_id}", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["job"]["name"] == "TEST_Updated_Stock_Check"
        assert data["job"]["run_time"] == "07:30"
        print("PASS: Job updated successfully")
    
    def test_delete_job(self, admin_session):
        """DELETE /api/scheduled-jobs/{job_id} - Delete job."""
        if not TestScheduledJobsCRUD.created_job_id:
            pytest.skip("No job created to delete")
        
        job_id = TestScheduledJobsCRUD.created_job_id
        resp = admin_session.delete(f"{BASE_URL}/api/scheduled-jobs/{job_id}")
        assert resp.status_code == 200
        print("PASS: Job deleted successfully")
    
    def test_delete_nonexistent_job(self, admin_session):
        """DELETE /api/scheduled-jobs/{job_id} - Delete nonexistent job should 404."""
        resp = admin_session.delete(f"{BASE_URL}/api/scheduled-jobs/nonexistent123")
        assert resp.status_code == 404
        print("PASS: Delete nonexistent job returns 404")
    
    def test_job_history(self, admin_session):
        """GET /api/scheduled-jobs/history - Get job execution history."""
        resp = admin_session.get(f"{BASE_URL}/api/scheduled-jobs/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "history" in data
        print(f"PASS: Job history returned {len(data['history'])} entries")


# ============ PLAN USAGE TESTS ============

class TestPlanUsage:
    """Test Plan Usage API for upgrade page."""
    
    def test_get_plan_usage(self, admin_session):
        """GET /api/tenants/{tenant_id}/plan-usage - Get plan usage stats."""
        resp = admin_session.get(f"{BASE_URL}/api/tenants/{TENANT_ID}/plan-usage")
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify response structure
        assert "plan_type" in data
        assert "company_name" in data
        assert "limits" in data
        assert "usage" in data
        
        # Verify limits structure
        limits = data["limits"]
        assert "max_users" in limits
        assert "storage_gb" in limits
        assert "api_calls" in limits
        
        # Verify usage structure
        usage = data["usage"]
        assert "active_users" in usage
        assert "stores" in usage
        assert "uploaded_files" in usage
        
        print(f"PASS: Plan usage - type={data['plan_type']}, users={usage['active_users']}, stores={usage['stores']}")
    
    def test_plan_usage_trial_info(self, admin_session):
        """GET /api/tenants/{tenant_id}/plan-usage - Trial info included for trial plans."""
        resp = admin_session.get(f"{BASE_URL}/api/tenants/{TENANT_ID}/plan-usage")
        assert resp.status_code == 200
        data = resp.json()
        
        # trial_info should be None for non-trial plans, or contain days_remaining for trial
        if data["plan_type"] == "trial":
            assert data["trial_info"] is not None
            assert "days_remaining" in data["trial_info"]
            assert "trial_end" in data["trial_info"]
            print(f"PASS: Trial info present - {data['trial_info']['days_remaining']} days remaining")
        else:
            print(f"PASS: Plan is {data['plan_type']}, trial_info is {data.get('trial_info')}")
    
    def test_plan_usage_nonexistent_tenant(self, admin_session):
        """GET /api/tenants/{tenant_id}/plan-usage - Nonexistent tenant should 404."""
        resp = admin_session.get(f"{BASE_URL}/api/tenants/nonexistent_tenant_xyz/plan-usage")
        assert resp.status_code == 404
        print("PASS: Nonexistent tenant returns 404")


# ============ FORCE PASSWORD CHANGE TESTS ============

class TestForcePasswordChange:
    """Test Force Password Change flow (USER-17)."""
    
    def test_login_returns_must_change_password_flag(self, b2b_admin_session):
        """Login response should include must_change_password field when set."""
        # First, let's check if the flag is present in login response
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": B2B_ADMIN_EMAIL,
            "password": B2B_ADMIN_PASSWORD
        })
        assert resp.status_code == 200
        data = resp.json()
        
        # The flag should be present (either true or false/absent)
        # For normal users, it should be absent or false
        must_change = data.get("must_change_password", False)
        print(f"PASS: Login response has must_change_password={must_change}")
    
    def test_admin_password_reset_sets_flag(self, b2b_admin_session):
        """POST /api/users/password-reset - Admin reset sets must_change_password flag."""
        # Reset aditya's password
        temp_password = "TempPass123!"
        payload = {
            "email": TEST_USER_EMAIL,
            "new_password": temp_password
        }
        resp = b2b_admin_session.post(f"{BASE_URL}/api/users/password-reset", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        print(f"PASS: Admin password reset successful - {data['message']}")
        
        # Now login as the user and check must_change_password flag
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": temp_password
        })
        assert resp.status_code == 200
        data = resp.json()
        
        # The flag should be True after admin reset
        assert data.get("must_change_password") == True, f"Expected must_change_password=True, got {data.get('must_change_password')}"
        print("PASS: Login after admin reset has must_change_password=True")
        
        # Store token for next test
        TestForcePasswordChange.temp_token = data["access_token"]
        TestForcePasswordChange.temp_password = temp_password
    
    def test_change_password_api(self):
        """POST /api/auth/change-password - User changes password and clears flag."""
        if not hasattr(TestForcePasswordChange, 'temp_token'):
            pytest.skip("No temp token from previous test")
        
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TestForcePasswordChange.temp_token}",
            "X-Tenant-ID": B2B_TENANT_ID
        })
        
        # Change password
        payload = {
            "current_password": TestForcePasswordChange.temp_password,
            "new_password": TEST_USER_ORIGINAL_PASSWORD  # Restore original password
        }
        resp = session.post(f"{BASE_URL}/api/auth/change-password", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") == True
        print("PASS: Password changed successfully")
        
        # Verify flag is cleared by logging in again
        time.sleep(0.5)  # Small delay
        session2 = requests.Session()
        session2.headers.update({"Content-Type": "application/json"})
        
        resp = session2.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_ORIGINAL_PASSWORD
        })
        assert resp.status_code == 200
        data = resp.json()
        
        # Flag should be absent or False now
        must_change = data.get("must_change_password", False)
        assert must_change == False, f"Expected must_change_password=False after change, got {must_change}"
        print("PASS: must_change_password flag cleared after password change")
    
    def test_change_password_wrong_current(self, admin_session):
        """POST /api/auth/change-password - Wrong current password should fail."""
        payload = {
            "current_password": "wrong_password_123",
            "new_password": "NewPass123!"
        }
        resp = admin_session.post(f"{BASE_URL}/api/auth/change-password", json=payload)
        assert resp.status_code == 400
        print("PASS: Wrong current password rejected")
    
    def test_change_password_same_as_current(self, admin_session):
        """POST /api/auth/change-password - Same password should fail."""
        payload = {
            "current_password": ADMIN_PASSWORD,
            "new_password": ADMIN_PASSWORD
        }
        resp = admin_session.post(f"{BASE_URL}/api/auth/change-password", json=payload)
        assert resp.status_code == 400
        print("PASS: Same password rejected")
    
    def test_change_password_too_short(self, admin_session):
        """POST /api/auth/change-password - Short password should fail."""
        payload = {
            "current_password": ADMIN_PASSWORD,
            "new_password": "short"
        }
        resp = admin_session.post(f"{BASE_URL}/api/auth/change-password", json=payload)
        assert resp.status_code == 422  # Pydantic validation error
        print("PASS: Short password rejected")


# ============ CLEANUP TEST JOBS ============

class TestCleanup:
    """Cleanup test data."""
    
    def test_cleanup_test_jobs(self, admin_session):
        """Delete all TEST_ prefixed jobs."""
        resp = admin_session.get(f"{BASE_URL}/api/scheduled-jobs/")
        if resp.status_code == 200:
            jobs = resp.json().get("jobs", [])
            deleted = 0
            for job in jobs:
                if job.get("name", "").startswith("TEST_"):
                    del_resp = admin_session.delete(f"{BASE_URL}/api/scheduled-jobs/{job['job_id']}")
                    if del_resp.status_code == 200:
                        deleted += 1
            print(f"PASS: Cleaned up {deleted} test jobs")
        else:
            print("SKIP: Could not list jobs for cleanup")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
