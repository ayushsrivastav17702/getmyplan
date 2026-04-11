"""
Test suite for User Funnel Analytics API (Iteration 80)
Tests: GET /api/analytics/funnel with various filters and access levels
Funnel stages: Signup → Email Verified → Onboarding Complete → First Upload → Active User
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@demo.com"
SUPER_ADMIN_PASSWORD = "demo1234"
TENANT_ADMIN_EMAIL = "ayush.srivastav@increff.com"
TENANT_ADMIN_PASSWORD = "Ayush@114988"


@pytest.fixture(scope="module")
def super_admin_token():
    """Get auth token for super admin (demo tenant - platform-wide access)"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Super admin login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def tenant_admin_token():
    """Get auth token for tenant admin (increff tenant - scoped access)"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TENANT_ADMIN_EMAIL,
        "password": TENANT_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Tenant admin login failed: {response.status_code} - {response.text}")


class TestFunnelAnalyticsAuth:
    """Authentication tests for funnel analytics endpoint"""
    
    def test_01_unauthenticated_access_denied(self):
        """Funnel endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/analytics/funnel")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("TEST_01 PASS: Unauthenticated access returns 401")
    
    def test_02_authenticated_access_allowed(self, super_admin_token):
        """Authenticated users can access funnel data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("TEST_02 PASS: Authenticated access returns 200")


class TestFunnelDataStructure:
    """Tests for funnel data response structure"""
    
    def test_03_response_structure(self, super_admin_token):
        """Verify response contains all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Top-level fields
        assert "funnel" in data, "Missing 'funnel' field"
        assert "time_series" in data, "Missing 'time_series' field"
        assert "users" in data, "Missing 'users' field"
        assert "total_users" in data, "Missing 'total_users' field"
        assert "is_platform_wide" in data, "Missing 'is_platform_wide' field"
        assert "date_range" in data, "Missing 'date_range' field"
        
        print("TEST_03 PASS: Response contains all required top-level fields")
    
    def test_04_funnel_stages_structure(self, super_admin_token):
        """Verify funnel.stages contains all 5 stages"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        data = response.json()
        stages = data["funnel"]["stages"]
        
        expected_stages = ["signed_up", "email_verified", "onboarding_complete", "first_upload", "active_user"]
        for stage in expected_stages:
            assert stage in stages, f"Missing stage: {stage}"
            assert isinstance(stages[stage], int), f"Stage {stage} should be integer"
        
        print(f"TEST_04 PASS: All 5 funnel stages present with counts: {stages}")
    
    def test_05_funnel_conversions_structure(self, super_admin_token):
        """Verify funnel.conversions contains stage-to-stage conversion data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        data = response.json()
        conversions = data["funnel"]["conversions"]
        
        assert len(conversions) == 4, f"Expected 4 conversion steps, got {len(conversions)}"
        
        for conv in conversions:
            assert "from" in conv, "Missing 'from' field in conversion"
            assert "to" in conv, "Missing 'to' field in conversion"
            assert "from_count" in conv, "Missing 'from_count' field"
            assert "to_count" in conv, "Missing 'to_count' field"
            assert "conversion_rate" in conv, "Missing 'conversion_rate' field"
            assert "drop_off" in conv, "Missing 'drop_off' field"
            assert 0 <= conv["conversion_rate"] <= 100, f"Invalid conversion rate: {conv['conversion_rate']}"
        
        print(f"TEST_05 PASS: Conversions structure valid with {len(conversions)} steps")
    
    def test_06_overall_conversion_rate(self, super_admin_token):
        """Verify overall conversion rate is calculated"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        data = response.json()
        
        overall = data["funnel"]["overall_conversion"]
        assert isinstance(overall, (int, float)), "Overall conversion should be numeric"
        assert 0 <= overall <= 100, f"Invalid overall conversion: {overall}"
        
        print(f"TEST_06 PASS: Overall conversion rate = {overall}%")
    
    def test_07_time_series_structure(self, super_admin_token):
        """Verify time_series contains date and signups"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel?days=30",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        data = response.json()
        time_series = data["time_series"]
        
        assert isinstance(time_series, list), "time_series should be a list"
        if len(time_series) > 0:
            for ts in time_series:
                assert "date" in ts, "Missing 'date' in time_series entry"
                assert "signups" in ts, "Missing 'signups' in time_series entry"
        
        print(f"TEST_07 PASS: Time series has {len(time_series)} entries")
    
    def test_08_users_list_structure(self, super_admin_token):
        """Verify users list contains required user fields"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        data = response.json()
        users = data["users"]
        
        assert isinstance(users, list), "users should be a list"
        if len(users) > 0:
            user = users[0]
            required_fields = ["email", "current_stage", "signed_up_at", "last_login"]
            for field in required_fields:
                assert field in user, f"Missing '{field}' in user data"
        
        print(f"TEST_08 PASS: Users list has {len(users)} users with required fields")


class TestFunnelTimeFiltering:
    """Tests for time range filtering"""
    
    def test_09_filter_by_days_7(self, super_admin_token):
        """Filter by last 7 days"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel?days=7",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["date_range"]["start"] is not None, "Start date should be set for days filter"
        print(f"TEST_09 PASS: 7-day filter applied, date_range: {data['date_range']}")
    
    def test_10_filter_by_days_30(self, super_admin_token):
        """Filter by last 30 days"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel?days=30",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["date_range"]["start"] is not None
        print(f"TEST_10 PASS: 30-day filter applied, total_users: {data['total_users']}")
    
    def test_11_filter_by_days_90(self, super_admin_token):
        """Filter by last 90 days"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel?days=90",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["date_range"]["start"] is not None
        print(f"TEST_11 PASS: 90-day filter applied, total_users: {data['total_users']}")
    
    def test_12_all_time_no_days_filter(self, super_admin_token):
        """All time - no days filter"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Without days filter, start should be None (all time)
        assert data["date_range"]["start"] is None, "Start should be None for all-time"
        print(f"TEST_12 PASS: All-time filter (no days), total_users: {data['total_users']}")
    
    def test_13_custom_date_range(self, super_admin_token):
        """Custom date range with start_date and end_date"""
        start = (datetime.now() - timedelta(days=60)).isoformat()
        end = (datetime.now() - timedelta(days=30)).isoformat()
        
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel?start_date={start}&end_date={end}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["date_range"]["start"] is not None
        assert data["date_range"]["end"] is not None
        print(f"TEST_13 PASS: Custom date range applied, total_users: {data['total_users']}")


class TestFunnelAccessControl:
    """Tests for platform-wide vs tenant-scoped access"""
    
    def test_14_super_admin_platform_wide(self, super_admin_token):
        """Super admin (demo tenant) sees platform-wide data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_platform_wide"] == True, "Super admin should see platform-wide data"
        print(f"TEST_14 PASS: Super admin has platform-wide access, total_users: {data['total_users']}")
    
    def test_15_tenant_admin_scoped(self, tenant_admin_token):
        """Tenant admin sees only their tenant's data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel",
            headers={"Authorization": f"Bearer {tenant_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_platform_wide"] == False, "Tenant admin should see scoped data"
        print(f"TEST_15 PASS: Tenant admin has scoped access, total_users: {data['total_users']}")
    
    def test_16_tenant_admin_users_belong_to_tenant(self, tenant_admin_token):
        """Verify tenant admin only sees users from their tenant"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel",
            headers={"Authorization": f"Bearer {tenant_admin_token}"}
        )
        data = response.json()
        
        # All users should belong to increff tenant
        for user in data["users"]:
            # tenant_id should be increff or company should match
            assert user.get("tenant_id") == "increff" or "increff" in str(user.get("company", "")).lower(), \
                f"User {user['email']} doesn't belong to increff tenant"
        
        print(f"TEST_16 PASS: All {len(data['users'])} users belong to increff tenant")


class TestFunnelConversionCalculations:
    """Tests for conversion rate calculations"""
    
    def test_17_conversion_rates_valid(self, super_admin_token):
        """Verify conversion rates are calculated correctly"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        data = response.json()
        
        for conv in data["funnel"]["conversions"]:
            from_count = conv["from_count"]
            to_count = conv["to_count"]
            rate = conv["conversion_rate"]
            
            if from_count > 0:
                expected_rate = round((to_count / from_count * 100), 1)
                assert rate == expected_rate, f"Rate mismatch: {rate} vs expected {expected_rate}"
            else:
                assert rate == 0, "Rate should be 0 when from_count is 0"
        
        print("TEST_17 PASS: All conversion rates calculated correctly")
    
    def test_18_drop_off_calculated(self, super_admin_token):
        """Verify drop-off is calculated correctly"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        data = response.json()
        
        for conv in data["funnel"]["conversions"]:
            expected_drop = conv["from_count"] - conv["to_count"]
            assert conv["drop_off"] == expected_drop, f"Drop-off mismatch: {conv['drop_off']} vs {expected_drop}"
        
        print("TEST_18 PASS: All drop-off values calculated correctly")
    
    def test_19_funnel_is_monotonically_decreasing(self, super_admin_token):
        """Funnel stages should be monotonically decreasing (cumulative)"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        data = response.json()
        stages = data["funnel"]["stages"]
        
        stage_order = ["signed_up", "email_verified", "onboarding_complete", "first_upload", "active_user"]
        prev_count = float('inf')
        
        for stage in stage_order:
            count = stages[stage]
            assert count <= prev_count, f"Stage {stage} ({count}) should be <= previous ({prev_count})"
            prev_count = count
        
        print(f"TEST_19 PASS: Funnel is monotonically decreasing: {[stages[s] for s in stage_order]}")


class TestFunnelUserDetails:
    """Tests for user details in funnel response"""
    
    def test_20_user_has_stage_info(self, super_admin_token):
        """Each user has current_stage field"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/funnel",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        data = response.json()
        
        valid_stages = ["signed_up", "email_verified", "onboarding_complete", "first_upload", "active_user"]
        for user in data["users"]:
            assert user["current_stage"] in valid_stages, f"Invalid stage: {user['current_stage']}"
        
        print(f"TEST_20 PASS: All {len(data['users'])} users have valid current_stage")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
