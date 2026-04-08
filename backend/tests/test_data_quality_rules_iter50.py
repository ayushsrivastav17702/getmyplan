"""
Test Data Quality Rules Engine - Iteration 50
Tests CRUD operations, rule types, validation, toggle, evaluate, and file-columns endpoints.
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
DEMO_ADMIN = {"email": "admin@demo.com", "password": "demo1234", "tenant": "demo"}
B2BLEADS_ADMIN = {"email": "akash@b2bleads.co.in", "password": "Test1234!", "tenant": "b2bleads"}


@pytest.fixture(scope="module")
def demo_session():
    """Authenticated session for demo tenant"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    resp = session.post(f"{BASE_URL}/api/auth/login", json=DEMO_ADMIN)
    assert resp.status_code == 200, f"Demo login failed: {resp.text}"
    token = resp.json().get("access_token")  # API returns access_token not token
    assert token, f"No access_token in response: {resp.json()}"
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


@pytest.fixture(scope="module")
def b2bleads_session():
    """Authenticated session for b2bleads tenant"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    resp = session.post(f"{BASE_URL}/api/auth/login", json=B2BLEADS_ADMIN)
    assert resp.status_code == 200, f"B2BLeads login failed: {resp.text}"
    token = resp.json().get("access_token")  # API returns access_token not token
    assert token, f"No access_token in response: {resp.json()}"
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


class TestRulesListEndpoint:
    """Test GET /api/quality/rules/ - List all rules"""
    
    def test_list_rules_returns_array(self, demo_session):
        """DQR-01: List rules returns array"""
        resp = demo_session.get(f"{BASE_URL}/api/quality/rules/")
        assert resp.status_code == 200
        data = resp.json()
        assert "rules" in data
        assert isinstance(data["rules"], list)
        print(f"DQR-01 PASS: Found {len(data['rules'])} rules")


class TestRulesCreateEndpoint:
    """Test POST /api/quality/rules/ - Create rules with different types"""
    
    def test_create_threshold_rule(self, demo_session):
        """DQR-02: Create threshold rule with operator and value"""
        payload = {
            "name": f"TEST_Threshold_{uuid.uuid4().hex[:6]}",
            "description": "Test threshold rule",
            "file_type": "daily_sales",
            "rule_type": "threshold",
            "column": "revenue",
            "operator": ">",
            "value": 0,
            "severity": "error",
            "threshold_pct": 95
        }
        resp = demo_session.post(f"{BASE_URL}/api/quality/rules/", json=payload)
        assert resp.status_code == 200, f"Create failed: {resp.text}"
        data = resp.json()
        assert "rule" in data
        assert data["rule"]["name"] == payload["name"]
        assert data["rule"]["rule_type"] == "threshold"
        assert data["rule"]["operator"] == ">"
        assert data["rule"]["value"] == 0
        print(f"DQR-02 PASS: Created threshold rule {data['rule']['rule_id']}")
        return data["rule"]["rule_id"]
    
    def test_create_null_check_rule(self, demo_session):
        """DQR-03: Create null_check rule"""
        payload = {
            "name": f"TEST_NullCheck_{uuid.uuid4().hex[:6]}",
            "file_type": "daily_sales",
            "rule_type": "null_check",
            "column": "sku",
            "severity": "warning"
        }
        resp = demo_session.post(f"{BASE_URL}/api/quality/rules/", json=payload)
        assert resp.status_code == 200, f"Create failed: {resp.text}"
        data = resp.json()
        assert data["rule"]["rule_type"] == "null_check"
        print(f"DQR-03 PASS: Created null_check rule {data['rule']['rule_id']}")
        return data["rule"]["rule_id"]
    
    def test_create_pattern_rule(self, demo_session):
        """DQR-04: Create pattern rule with regex"""
        payload = {
            "name": f"TEST_Pattern_{uuid.uuid4().hex[:6]}",
            "file_type": "sku_ean_master",
            "rule_type": "pattern",
            "column": "ean",
            "value_str": "^[0-9]{13}$",
            "severity": "error"
        }
        resp = demo_session.post(f"{BASE_URL}/api/quality/rules/", json=payload)
        assert resp.status_code == 200, f"Create failed: {resp.text}"
        data = resp.json()
        assert data["rule"]["rule_type"] == "pattern"
        assert data["rule"]["value_str"] == "^[0-9]{13}$"
        print(f"DQR-04 PASS: Created pattern rule {data['rule']['rule_id']}")
        return data["rule"]["rule_id"]
    
    def test_create_uniqueness_rule(self, demo_session):
        """DQR-05: Create uniqueness rule"""
        payload = {
            "name": f"TEST_Uniqueness_{uuid.uuid4().hex[:6]}",
            "file_type": "store_master",
            "rule_type": "uniqueness",
            "column": "store_code",
            "severity": "error"
        }
        resp = demo_session.post(f"{BASE_URL}/api/quality/rules/", json=payload)
        assert resp.status_code == 200, f"Create failed: {resp.text}"
        data = resp.json()
        assert data["rule"]["rule_type"] == "uniqueness"
        print(f"DQR-05 PASS: Created uniqueness rule {data['rule']['rule_id']}")
        return data["rule"]["rule_id"]
    
    def test_create_range_rule(self, demo_session):
        """DQR-06: Create range rule with min/max"""
        payload = {
            "name": f"TEST_Range_{uuid.uuid4().hex[:6]}",
            "file_type": "daily_sales",
            "rule_type": "range",
            "column": "quantity",
            "min_value": 1,
            "max_value": 10000,
            "severity": "warning"
        }
        resp = demo_session.post(f"{BASE_URL}/api/quality/rules/", json=payload)
        assert resp.status_code == 200, f"Create failed: {resp.text}"
        data = resp.json()
        assert data["rule"]["rule_type"] == "range"
        assert data["rule"]["min_value"] == 1
        assert data["rule"]["max_value"] == 10000
        print(f"DQR-06 PASS: Created range rule {data['rule']['rule_id']}")
        return data["rule"]["rule_id"]
    
    def test_create_cross_reference_rule(self, demo_session):
        """DQR-07: Create cross_reference rule with ref_file_type"""
        payload = {
            "name": f"TEST_CrossRef_{uuid.uuid4().hex[:6]}",
            "file_type": "daily_sales",
            "rule_type": "cross_reference",
            "column": "sku",
            "ref_file_type": "sku_ean_master",
            "ref_column": "sku",
            "severity": "error"
        }
        resp = demo_session.post(f"{BASE_URL}/api/quality/rules/", json=payload)
        assert resp.status_code == 200, f"Create failed: {resp.text}"
        data = resp.json()
        assert data["rule"]["rule_type"] == "cross_reference"
        assert data["rule"]["ref_file_type"] == "sku_ean_master"
        print(f"DQR-07 PASS: Created cross_reference rule {data['rule']['rule_id']}")
        return data["rule"]["rule_id"]


class TestRulesValidation:
    """Test validation errors for invalid inputs"""
    
    def test_invalid_file_type_returns_400(self, demo_session):
        """DQR-08: Invalid file_type returns 400"""
        payload = {
            "name": "TEST_Invalid",
            "file_type": "invalid_file_type",
            "rule_type": "null_check",
            "column": "test"
        }
        resp = demo_session.post(f"{BASE_URL}/api/quality/rules/", json=payload)
        assert resp.status_code == 400
        assert "file_type" in resp.text.lower()
        print("DQR-08 PASS: Invalid file_type returns 400")
    
    def test_invalid_rule_type_returns_400(self, demo_session):
        """DQR-09: Invalid rule_type returns 400"""
        payload = {
            "name": "TEST_Invalid",
            "file_type": "daily_sales",
            "rule_type": "invalid_rule_type",
            "column": "test"
        }
        resp = demo_session.post(f"{BASE_URL}/api/quality/rules/", json=payload)
        assert resp.status_code == 400
        assert "rule_type" in resp.text.lower()
        print("DQR-09 PASS: Invalid rule_type returns 400")
    
    def test_range_requires_min_max(self, demo_session):
        """DQR-10: Range rule requires both min_value and max_value"""
        payload = {
            "name": "TEST_RangeMissingMax",
            "file_type": "daily_sales",
            "rule_type": "range",
            "column": "quantity",
            "min_value": 1
            # missing max_value
        }
        resp = demo_session.post(f"{BASE_URL}/api/quality/rules/", json=payload)
        assert resp.status_code == 400
        assert "min_value" in resp.text.lower() or "max_value" in resp.text.lower()
        print("DQR-10 PASS: Range rule requires both min/max")
    
    def test_cross_reference_requires_ref_file_type(self, demo_session):
        """DQR-11: Cross-reference rule requires ref_file_type"""
        payload = {
            "name": "TEST_CrossRefMissingRef",
            "file_type": "daily_sales",
            "rule_type": "cross_reference",
            "column": "sku"
            # missing ref_file_type
        }
        resp = demo_session.post(f"{BASE_URL}/api/quality/rules/", json=payload)
        assert resp.status_code == 400
        assert "ref_file_type" in resp.text.lower()
        print("DQR-11 PASS: Cross-reference requires ref_file_type")


class TestRulesUpdateDelete:
    """Test PUT and DELETE endpoints"""
    
    def test_update_rule(self, demo_session):
        """DQR-12: Update rule via PUT"""
        # First create a rule
        create_payload = {
            "name": f"TEST_ToUpdate_{uuid.uuid4().hex[:6]}",
            "file_type": "daily_sales",
            "rule_type": "threshold",
            "column": "revenue",
            "operator": ">",
            "value": 0
        }
        create_resp = demo_session.post(f"{BASE_URL}/api/quality/rules/", json=create_payload)
        assert create_resp.status_code == 200
        rule_id = create_resp.json()["rule"]["rule_id"]
        
        # Update the rule
        update_payload = {
            "name": "TEST_Updated_Name",
            "value": 100,
            "severity": "error"
        }
        update_resp = demo_session.put(f"{BASE_URL}/api/quality/rules/{rule_id}", json=update_payload)
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["rule"]["name"] == "TEST_Updated_Name"
        assert data["rule"]["value"] == 100
        assert data["rule"]["severity"] == "error"
        print(f"DQR-12 PASS: Updated rule {rule_id}")
        
        # Cleanup
        demo_session.delete(f"{BASE_URL}/api/quality/rules/{rule_id}")
    
    def test_delete_rule(self, demo_session):
        """DQR-13: Delete rule via DELETE"""
        # First create a rule
        create_payload = {
            "name": f"TEST_ToDelete_{uuid.uuid4().hex[:6]}",
            "file_type": "daily_sales",
            "rule_type": "null_check",
            "column": "sku"
        }
        create_resp = demo_session.post(f"{BASE_URL}/api/quality/rules/", json=create_payload)
        assert create_resp.status_code == 200
        rule_id = create_resp.json()["rule"]["rule_id"]
        
        # Delete the rule
        delete_resp = demo_session.delete(f"{BASE_URL}/api/quality/rules/{rule_id}")
        assert delete_resp.status_code == 200
        assert "deleted" in delete_resp.text.lower()
        print(f"DQR-13 PASS: Deleted rule {rule_id}")
    
    def test_delete_nonexistent_returns_404(self, demo_session):
        """DQR-14: Delete nonexistent rule returns 404"""
        resp = demo_session.delete(f"{BASE_URL}/api/quality/rules/nonexistent_id")
        assert resp.status_code == 404
        print("DQR-14 PASS: Delete nonexistent returns 404")


class TestRulesToggle:
    """Test POST /api/quality/rules/{rule_id}/toggle"""
    
    def test_toggle_rule(self, demo_session):
        """DQR-15: Toggle rule active status"""
        # Create a rule
        create_payload = {
            "name": f"TEST_ToToggle_{uuid.uuid4().hex[:6]}",
            "file_type": "daily_sales",
            "rule_type": "null_check",
            "column": "sku",
            "is_active": True
        }
        create_resp = demo_session.post(f"{BASE_URL}/api/quality/rules/", json=create_payload)
        assert create_resp.status_code == 200
        rule_id = create_resp.json()["rule"]["rule_id"]
        initial_active = create_resp.json()["rule"]["is_active"]
        
        # Toggle the rule
        toggle_resp = demo_session.post(f"{BASE_URL}/api/quality/rules/{rule_id}/toggle")
        assert toggle_resp.status_code == 200
        data = toggle_resp.json()
        assert data["is_active"] != initial_active
        print(f"DQR-15 PASS: Toggled rule {rule_id} from {initial_active} to {data['is_active']}")
        
        # Cleanup
        demo_session.delete(f"{BASE_URL}/api/quality/rules/{rule_id}")


class TestRulesEvaluate:
    """Test POST /api/quality/rules/evaluate"""
    
    def test_evaluate_rules_returns_results(self, demo_session):
        """DQR-16: Evaluate rules returns results and summary"""
        resp = demo_session.post(f"{BASE_URL}/api/quality/rules/evaluate")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "summary" in data
        assert isinstance(data["results"], list)
        assert "total" in data["summary"]
        assert "passed" in data["summary"]
        assert "failed" in data["summary"]
        print(f"DQR-16 PASS: Evaluated {data['summary']['total']} rules")
    
    def test_evaluate_with_no_active_rules(self, demo_session):
        """DQR-17: Evaluate with no active rules returns empty results"""
        # This test checks the behavior when there are no active rules
        # The demo tenant may have existing rules, so we just verify the structure
        resp = demo_session.post(f"{BASE_URL}/api/quality/rules/evaluate")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "summary" in data
        print("DQR-17 PASS: Evaluate endpoint returns correct structure")


class TestFileColumns:
    """Test GET /api/quality/rules/file-columns/{file_type}"""
    
    def test_file_columns_valid_file_type(self, demo_session):
        """DQR-18: Get columns for valid file type"""
        resp = demo_session.get(f"{BASE_URL}/api/quality/rules/file-columns/daily_sales")
        assert resp.status_code == 200
        data = resp.json()
        assert "columns" in data
        assert "row_count" in data
        assert isinstance(data["columns"], list)
        print(f"DQR-18 PASS: Got {len(data['columns'])} columns for daily_sales")
    
    def test_file_columns_invalid_file_type(self, demo_session):
        """DQR-19: Invalid file type returns 400"""
        resp = demo_session.get(f"{BASE_URL}/api/quality/rules/file-columns/invalid_type")
        assert resp.status_code == 400
        print("DQR-19 PASS: Invalid file type returns 400")


class TestCleanup:
    """Cleanup TEST_ prefixed rules after all tests"""
    
    def test_cleanup_test_rules(self, demo_session):
        """DQR-CLEANUP: Remove all TEST_ prefixed rules"""
        resp = demo_session.get(f"{BASE_URL}/api/quality/rules/")
        if resp.status_code == 200:
            rules = resp.json().get("rules", [])
            test_rules = [r for r in rules if r.get("name", "").startswith("TEST_")]
            for rule in test_rules:
                demo_session.delete(f"{BASE_URL}/api/quality/rules/{rule['rule_id']}")
            print(f"DQR-CLEANUP: Removed {len(test_rules)} test rules")
        else:
            print("DQR-CLEANUP: Could not fetch rules for cleanup")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
