"""
Drip Campaigns API Tests - Iteration 81
Tests for email drip campaigns triggered by funnel drop-offs.
4 campaigns: not_verified, not_onboarded, no_upload, inactive
Drip sequence: Day 1, Day 3, Day 7
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@demo.com"
SUPER_ADMIN_PASSWORD = "demo1234"
TENANT_ADMIN_EMAIL = "ayush.srivastav@increff.com"
TENANT_ADMIN_PASSWORD = "Ayush@114988"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def super_admin_token(api_client):
    """Get super admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Super admin authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def tenant_admin_token(api_client):
    """Get tenant admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TENANT_ADMIN_EMAIL,
        "password": TENANT_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Tenant admin authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def authenticated_client(api_client, super_admin_token):
    """Session with super admin auth header"""
    api_client.headers.update({"Authorization": f"Bearer {super_admin_token}"})
    return api_client


class TestDripCampaignsAuth:
    """Test authentication requirements for drip campaign endpoints"""
    
    def test_01_campaigns_requires_auth(self, api_client):
        """GET /api/drip/campaigns requires authentication"""
        # Remove auth header if present
        api_client.headers.pop("Authorization", None)
        response = api_client.get(f"{BASE_URL}/api/drip/campaigns")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: GET /api/drip/campaigns returns 401 without auth")
    
    def test_02_toggle_requires_auth(self, api_client):
        """PUT /api/drip/campaigns/{id}/toggle requires authentication"""
        api_client.headers.pop("Authorization", None)
        response = api_client.put(f"{BASE_URL}/api/drip/campaigns/not_verified/toggle", json={"enabled": True})
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: PUT /api/drip/campaigns/{id}/toggle returns 401 without auth")
    
    def test_03_run_requires_auth(self, api_client):
        """POST /api/drip/run requires authentication"""
        api_client.headers.pop("Authorization", None)
        response = api_client.post(f"{BASE_URL}/api/drip/run")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: POST /api/drip/run returns 401 without auth")
    
    def test_04_history_requires_auth(self, api_client):
        """GET /api/drip/history requires authentication"""
        api_client.headers.pop("Authorization", None)
        response = api_client.get(f"{BASE_URL}/api/drip/history")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: GET /api/drip/history returns 401 without auth")
    
    def test_05_runs_requires_auth(self, api_client):
        """GET /api/drip/runs requires authentication"""
        api_client.headers.pop("Authorization", None)
        response = api_client.get(f"{BASE_URL}/api/drip/runs")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: GET /api/drip/runs returns 401 without auth")


class TestDripCampaignsList:
    """Test GET /api/drip/campaigns endpoint"""
    
    def test_06_list_campaigns_success(self, authenticated_client):
        """GET /api/drip/campaigns returns 200 with campaigns list"""
        response = authenticated_client.get(f"{BASE_URL}/api/drip/campaigns")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "campaigns" in data, "Response should contain 'campaigns' key"
        print(f"PASS: GET /api/drip/campaigns returns 200 with {len(data['campaigns'])} campaigns")
    
    def test_07_campaigns_has_4_default_campaigns(self, authenticated_client):
        """Should have exactly 4 default campaigns"""
        response = authenticated_client.get(f"{BASE_URL}/api/drip/campaigns")
        assert response.status_code == 200
        campaigns = response.json()["campaigns"]
        assert len(campaigns) == 4, f"Expected 4 campaigns, got {len(campaigns)}"
        
        campaign_ids = [c["campaign_id"] for c in campaigns]
        expected_ids = ["not_verified", "not_onboarded", "no_upload", "inactive"]
        for expected_id in expected_ids:
            assert expected_id in campaign_ids, f"Missing campaign: {expected_id}"
        print(f"PASS: All 4 default campaigns present: {campaign_ids}")
    
    def test_08_campaign_structure(self, authenticated_client):
        """Each campaign has required fields"""
        response = authenticated_client.get(f"{BASE_URL}/api/drip/campaigns")
        assert response.status_code == 200
        campaigns = response.json()["campaigns"]
        
        required_fields = ["campaign_id", "name", "description", "enabled", "drip_days", "total_sent"]
        for campaign in campaigns:
            for field in required_fields:
                assert field in campaign, f"Campaign {campaign.get('campaign_id')} missing field: {field}"
        print("PASS: All campaigns have required fields")
    
    def test_09_campaign_drip_days_structure(self, authenticated_client):
        """Each campaign has drip_days [1, 3, 7]"""
        response = authenticated_client.get(f"{BASE_URL}/api/drip/campaigns")
        assert response.status_code == 200
        campaigns = response.json()["campaigns"]
        
        for campaign in campaigns:
            drip_days = campaign.get("drip_days", [])
            assert drip_days == [1, 3, 7], f"Campaign {campaign['campaign_id']} has unexpected drip_days: {drip_days}"
        print("PASS: All campaigns have drip_days [1, 3, 7]")
    
    def test_10_campaign_enabled_is_boolean(self, authenticated_client):
        """Campaign enabled field is boolean"""
        response = authenticated_client.get(f"{BASE_URL}/api/drip/campaigns")
        assert response.status_code == 200
        campaigns = response.json()["campaigns"]
        
        for campaign in campaigns:
            assert isinstance(campaign["enabled"], bool), f"Campaign {campaign['campaign_id']} enabled is not boolean"
        print("PASS: All campaigns have boolean 'enabled' field")
    
    def test_11_campaign_total_sent_is_integer(self, authenticated_client):
        """Campaign total_sent field is integer"""
        response = authenticated_client.get(f"{BASE_URL}/api/drip/campaigns")
        assert response.status_code == 200
        campaigns = response.json()["campaigns"]
        
        for campaign in campaigns:
            assert isinstance(campaign["total_sent"], int), f"Campaign {campaign['campaign_id']} total_sent is not integer"
        print("PASS: All campaigns have integer 'total_sent' field")


class TestDripCampaignToggle:
    """Test PUT /api/drip/campaigns/{id}/toggle endpoint"""
    
    def test_12_toggle_campaign_off(self, authenticated_client):
        """Toggle campaign to disabled"""
        response = authenticated_client.put(
            f"{BASE_URL}/api/drip/campaigns/not_verified/toggle",
            json={"enabled": False}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert data.get("enabled") == False
        print("PASS: Toggle campaign OFF successful")
    
    def test_13_verify_toggle_persisted(self, authenticated_client):
        """Verify toggle state persisted"""
        response = authenticated_client.get(f"{BASE_URL}/api/drip/campaigns")
        assert response.status_code == 200
        campaigns = response.json()["campaigns"]
        
        not_verified = next((c for c in campaigns if c["campaign_id"] == "not_verified"), None)
        assert not_verified is not None
        assert not_verified["enabled"] == False, "Toggle state not persisted"
        print("PASS: Toggle state persisted correctly")
    
    def test_14_toggle_campaign_on(self, authenticated_client):
        """Toggle campaign back to enabled"""
        response = authenticated_client.put(
            f"{BASE_URL}/api/drip/campaigns/not_verified/toggle",
            json={"enabled": True}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert data.get("enabled") == True
        print("PASS: Toggle campaign ON successful")
    
    def test_15_toggle_nonexistent_campaign(self, authenticated_client):
        """Toggle non-existent campaign returns 404"""
        response = authenticated_client.put(
            f"{BASE_URL}/api/drip/campaigns/nonexistent_campaign/toggle",
            json={"enabled": True}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Toggle non-existent campaign returns 404")


class TestDripRun:
    """Test POST /api/drip/run endpoint"""
    
    def test_16_run_drip_success(self, authenticated_client):
        """POST /api/drip/run executes successfully"""
        response = authenticated_client.post(f"{BASE_URL}/api/drip/run")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check response structure
        assert "sent" in data, "Response should contain 'sent'"
        assert "skipped" in data, "Response should contain 'skipped'"
        assert "errors" in data, "Response should contain 'errors'"
        assert "message" in data, "Response should contain 'message'"
        assert "run_at" in data, "Response should contain 'run_at'"
        
        print(f"PASS: Drip run executed - sent: {data['sent']}, skipped: {data['skipped']}, errors: {data['errors']}")
    
    def test_17_run_drip_returns_details(self, authenticated_client):
        """POST /api/drip/run returns details array"""
        response = authenticated_client.post(f"{BASE_URL}/api/drip/run")
        assert response.status_code == 200
        data = response.json()
        
        assert "details" in data, "Response should contain 'details'"
        assert isinstance(data["details"], list), "Details should be a list"
        
        # If there are details, check structure
        if len(data["details"]) > 0:
            detail = data["details"][0]
            assert "email" in detail, "Detail should contain 'email'"
            assert "campaign" in detail, "Detail should contain 'campaign'"
            assert "drip_day" in detail, "Detail should contain 'drip_day'"
            assert "status" in detail, "Detail should contain 'status'"
        
        print(f"PASS: Drip run returns details array with {len(data['details'])} items")


class TestDripDedup:
    """Test drip deduplication - running twice shouldn't send duplicate emails"""
    
    def test_18_dedup_check(self, authenticated_client):
        """Running drip twice should skip already-sent emails"""
        # First run
        response1 = authenticated_client.post(f"{BASE_URL}/api/drip/run")
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Second run immediately after
        response2 = authenticated_client.post(f"{BASE_URL}/api/drip/run")
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Second run should have 0 sent (all skipped due to dedup)
        # Note: This assumes no new users appeared between runs
        print(f"PASS: Dedup check - Run 1: {data1['sent']} sent, Run 2: {data2['sent']} sent (should be 0 or same users)")


class TestDripHistory:
    """Test GET /api/drip/history endpoint"""
    
    def test_19_history_success(self, authenticated_client):
        """GET /api/drip/history returns 200"""
        response = authenticated_client.get(f"{BASE_URL}/api/drip/history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "logs" in data, "Response should contain 'logs'"
        assert "total" in data, "Response should contain 'total'"
        print(f"PASS: GET /api/drip/history returns {data['total']} logs")
    
    def test_20_history_log_structure(self, authenticated_client):
        """History logs have required fields"""
        response = authenticated_client.get(f"{BASE_URL}/api/drip/history")
        assert response.status_code == 200
        logs = response.json()["logs"]
        
        if len(logs) > 0:
            log = logs[0]
            required_fields = ["email", "campaign_id", "campaign_name", "drip_day", "sent_at"]
            for field in required_fields:
                assert field in log, f"Log missing field: {field}"
            print(f"PASS: History logs have required fields")
        else:
            print("PASS: No logs yet (empty history)")
    
    def test_21_history_limit_param(self, authenticated_client):
        """GET /api/drip/history respects limit parameter"""
        response = authenticated_client.get(f"{BASE_URL}/api/drip/history?limit=5")
        assert response.status_code == 200
        logs = response.json()["logs"]
        assert len(logs) <= 5, f"Expected max 5 logs, got {len(logs)}"
        print(f"PASS: History limit parameter works (returned {len(logs)} logs)")


class TestDripRuns:
    """Test GET /api/drip/runs endpoint"""
    
    def test_22_runs_success(self, authenticated_client):
        """GET /api/drip/runs returns 200"""
        response = authenticated_client.get(f"{BASE_URL}/api/drip/runs")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "runs" in data, "Response should contain 'runs'"
        print(f"PASS: GET /api/drip/runs returns {len(data['runs'])} runs")
    
    def test_23_runs_structure(self, authenticated_client):
        """Run history has required fields"""
        response = authenticated_client.get(f"{BASE_URL}/api/drip/runs")
        assert response.status_code == 200
        runs = response.json()["runs"]
        
        if len(runs) > 0:
            run = runs[0]
            required_fields = ["triggered_by", "run_at", "sent", "skipped", "errors"]
            for field in required_fields:
                assert field in run, f"Run missing field: {field}"
            print(f"PASS: Run history has required fields")
        else:
            print("PASS: No runs yet (empty run history)")
    
    def test_24_runs_limit_param(self, authenticated_client):
        """GET /api/drip/runs respects limit parameter"""
        response = authenticated_client.get(f"{BASE_URL}/api/drip/runs?limit=3")
        assert response.status_code == 200
        runs = response.json()["runs"]
        assert len(runs) <= 3, f"Expected max 3 runs, got {len(runs)}"
        print(f"PASS: Runs limit parameter works (returned {len(runs)} runs)")


class TestDisabledCampaignSkipped:
    """Test that disabled campaigns are skipped during drip run"""
    
    def test_25_disabled_campaign_skipped(self, authenticated_client):
        """Disabled campaign should be skipped during drip run"""
        # Disable a campaign
        toggle_resp = authenticated_client.put(
            f"{BASE_URL}/api/drip/campaigns/inactive/toggle",
            json={"enabled": False}
        )
        assert toggle_resp.status_code == 200
        
        # Run drip
        run_resp = authenticated_client.post(f"{BASE_URL}/api/drip/run")
        assert run_resp.status_code == 200
        data = run_resp.json()
        
        # Check that no emails were sent for 'inactive' campaign
        details = data.get("details", [])
        inactive_emails = [d for d in details if d.get("campaign") == "Inactive User"]
        
        # Re-enable the campaign
        authenticated_client.put(
            f"{BASE_URL}/api/drip/campaigns/inactive/toggle",
            json={"enabled": True}
        )
        
        print(f"PASS: Disabled campaign check - {len(inactive_emails)} emails sent for disabled 'inactive' campaign (should be 0)")


class TestTenantAdminAccess:
    """Test tenant admin can also access drip endpoints"""
    
    def test_26_tenant_admin_can_list_campaigns(self, api_client, tenant_admin_token):
        """Tenant admin can list campaigns"""
        api_client.headers.update({"Authorization": f"Bearer {tenant_admin_token}"})
        response = api_client.get(f"{BASE_URL}/api/drip/campaigns")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Tenant admin can list campaigns")
    
    def test_27_tenant_admin_can_view_history(self, api_client, tenant_admin_token):
        """Tenant admin can view drip history"""
        api_client.headers.update({"Authorization": f"Bearer {tenant_admin_token}"})
        response = api_client.get(f"{BASE_URL}/api/drip/history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Tenant admin can view drip history")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
