"""
Iteration 101: Audit Logging for Buy Planning Changes
Tests for P1: Audit logging for wedge/mix changes (Option A)

Tests:
- POST /api/buy-planning/store-wedge/classify logs changes with source=auto
- POST /api/buy-planning/style-mix/classify logs changes with source=auto
- POST /api/buy-planning/overrides/store-wedge logs with action=override, source=manual
- POST /api/buy-planning/overrides/style-mix logs with action=override, source=manual
- PUT /api/buy-planning/sell-through-config logs with action=config_update, source=manual
- GET /api/buy-planning/audit-log returns entries with filters
"""
import pytest
import requests
import os

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
    # Auth returns access_token (not token)
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in response: {data}"
    return token


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestAuditLogEndpoint:
    """Tests for GET /api/buy-planning/audit-log endpoint."""
    
    def test_get_audit_log_success(self, auth_headers):
        """Test GET /api/buy-planning/audit-log returns entries."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/audit-log", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "entries" in data, f"Missing 'entries' key: {data}"
        assert "total" in data, f"Missing 'total' key: {data}"
        assert isinstance(data["entries"], list), "entries should be a list"
        print(f"Audit log has {data['total']} entries")
    
    def test_get_audit_log_filter_entity_type_store(self, auth_headers):
        """Test filtering audit log by entity_type=store."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/audit-log",
            params={"entity_type": "store"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # All entries should have entity_type=store
        for entry in data["entries"]:
            assert entry.get("entity_type") == "store", f"Entry has wrong entity_type: {entry}"
        print(f"Found {data['total']} store entries")
    
    def test_get_audit_log_filter_entity_type_style(self, auth_headers):
        """Test filtering audit log by entity_type=style."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/audit-log",
            params={"entity_type": "style"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        for entry in data["entries"]:
            assert entry.get("entity_type") == "style", f"Entry has wrong entity_type: {entry}"
        print(f"Found {data['total']} style entries")
    
    def test_get_audit_log_filter_entity_type_config(self, auth_headers):
        """Test filtering audit log by entity_type=config."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/audit-log",
            params={"entity_type": "config"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        for entry in data["entries"]:
            assert entry.get("entity_type") == "config", f"Entry has wrong entity_type: {entry}"
        print(f"Found {data['total']} config entries")
    
    def test_get_audit_log_filter_source_auto(self, auth_headers):
        """Test filtering audit log by source=auto."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/audit-log",
            params={"source": "auto"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        for entry in data["entries"]:
            assert entry.get("source") == "auto", f"Entry has wrong source: {entry}"
        print(f"Found {data['total']} auto entries")
    
    def test_get_audit_log_filter_source_manual(self, auth_headers):
        """Test filtering audit log by source=manual."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/audit-log",
            params={"source": "manual"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        for entry in data["entries"]:
            assert entry.get("source") == "manual", f"Entry has wrong source: {entry}"
        print(f"Found {data['total']} manual entries")
    
    def test_get_audit_log_combined_filters(self, auth_headers):
        """Test filtering audit log by both entity_type and source."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/audit-log",
            params={"entity_type": "store", "source": "manual"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        for entry in data["entries"]:
            assert entry.get("entity_type") == "store", f"Entry has wrong entity_type: {entry}"
            assert entry.get("source") == "manual", f"Entry has wrong source: {entry}"
        print(f"Found {data['total']} store+manual entries")


class TestStoreWedgeClassifyAudit:
    """Tests for POST /api/buy-planning/store-wedge/classify audit logging."""
    
    def test_classify_store_wedge_logs_changes(self, auth_headers):
        """Test that store wedge classification logs changes to audit log."""
        # Get initial audit log count
        initial_response = requests.get(
            f"{BASE_URL}/api/buy-planning/audit-log",
            params={"entity_type": "store", "source": "auto"},
            headers=auth_headers
        )
        assert initial_response.status_code == 200
        initial_count = initial_response.json()["total"]
        
        # Run classification
        classify_response = requests.post(
            f"{BASE_URL}/api/buy-planning/store-wedge/classify",
            headers=auth_headers
        )
        assert classify_response.status_code == 200, f"Classify failed: {classify_response.text}"
        classify_data = classify_response.json()
        
        # Check response includes audit_changes count
        assert "audit_changes" in classify_data, f"Missing audit_changes in response: {classify_data}"
        print(f"Classification logged {classify_data.get('audit_changes', 0)} changes")
        
        # Verify audit log entries
        final_response = requests.get(
            f"{BASE_URL}/api/buy-planning/audit-log",
            params={"entity_type": "store", "source": "auto"},
            headers=auth_headers
        )
        assert final_response.status_code == 200
        final_count = final_response.json()["total"]
        
        # If there were changes, count should increase
        if classify_data.get("audit_changes", 0) > 0:
            assert final_count >= initial_count, "Audit log count should increase after changes"
            print(f"Audit log count: {initial_count} -> {final_count}")


class TestStyleMixClassifyAudit:
    """Tests for POST /api/buy-planning/style-mix/classify audit logging."""
    
    def test_classify_style_mix_logs_changes(self, auth_headers):
        """Test that style mix classification logs changes to audit log."""
        # Get initial audit log count
        initial_response = requests.get(
            f"{BASE_URL}/api/buy-planning/audit-log",
            params={"entity_type": "style", "source": "auto"},
            headers=auth_headers
        )
        assert initial_response.status_code == 200
        initial_count = initial_response.json()["total"]
        
        # Run classification
        classify_response = requests.post(
            f"{BASE_URL}/api/buy-planning/style-mix/classify",
            headers=auth_headers
        )
        assert classify_response.status_code == 200, f"Classify failed: {classify_response.text}"
        classify_data = classify_response.json()
        
        # Check response includes audit_changes count
        assert "audit_changes" in classify_data, f"Missing audit_changes in response: {classify_data}"
        print(f"Classification logged {classify_data.get('audit_changes', 0)} changes")


class TestStoreWedgeOverrideAudit:
    """Tests for POST /api/buy-planning/overrides/store-wedge audit logging."""
    
    def test_override_store_wedge_logs_to_audit(self, auth_headers):
        """Test that store wedge override logs to audit log with action=override, source=manual."""
        # First get a store to override
        stores_response = requests.get(
            f"{BASE_URL}/api/buy-planning/store-wedge",
            headers=auth_headers
        )
        assert stores_response.status_code == 200
        stores = stores_response.json().get("stores", [])
        
        if not stores:
            pytest.skip("No stores available for override test")
        
        # Pick a store and determine new wedge
        store = stores[0]
        store_code = store.get("store_code")
        current_wedge = store.get("wedge_class", "C")
        new_wedge = "B" if current_wedge != "B" else "A"
        
        # Get initial audit count
        initial_response = requests.get(
            f"{BASE_URL}/api/buy-planning/audit-log",
            params={"entity_type": "store", "source": "manual"},
            headers=auth_headers
        )
        initial_count = initial_response.json()["total"]
        
        # Apply override
        override_response = requests.post(
            f"{BASE_URL}/api/buy-planning/overrides/store-wedge",
            json={
                "store_code": store_code,
                "wedge_class": new_wedge,
                "reason": "Test override for audit logging"
            },
            headers=auth_headers
        )
        assert override_response.status_code == 200, f"Override failed: {override_response.text}"
        
        # Verify audit log entry was created
        final_response = requests.get(
            f"{BASE_URL}/api/buy-planning/audit-log",
            params={"entity_type": "store", "source": "manual"},
            headers=auth_headers
        )
        final_count = final_response.json()["total"]
        assert final_count > initial_count, "Audit log should have new entry after override"
        
        # Check the latest entry
        entries = final_response.json()["entries"]
        if entries:
            latest = entries[0]
            assert latest.get("action") == "override", f"Expected action=override: {latest}"
            assert latest.get("source") == "manual", f"Expected source=manual: {latest}"
            assert latest.get("entity_type") == "store", f"Expected entity_type=store: {latest}"
            assert latest.get("entity_id") == store_code, f"Expected entity_id={store_code}: {latest}"
            print(f"Override audit entry: {latest.get('old_value')} -> {latest.get('new_value')}")


class TestStyleMixOverrideAudit:
    """Tests for POST /api/buy-planning/overrides/style-mix audit logging."""
    
    def test_override_style_mix_logs_to_audit(self, auth_headers):
        """Test that style mix override logs to audit log with action=override, source=manual."""
        # First get a style to override
        styles_response = requests.get(
            f"{BASE_URL}/api/buy-planning/style-mix",
            headers=auth_headers
        )
        assert styles_response.status_code == 200
        styles = styles_response.json().get("styles", [])
        
        if not styles:
            pytest.skip("No styles available for override test")
        
        # Pick a style and determine new mix
        style = styles[0]
        style_name = style.get("style")
        current_mix = style.get("style_mix", "Test")
        new_mix = "Fashion" if current_mix != "Fashion" else "Core"
        
        # Get initial audit count
        initial_response = requests.get(
            f"{BASE_URL}/api/buy-planning/audit-log",
            params={"entity_type": "style", "source": "manual"},
            headers=auth_headers
        )
        initial_count = initial_response.json()["total"]
        
        # Apply override
        override_response = requests.post(
            f"{BASE_URL}/api/buy-planning/overrides/style-mix",
            json={
                "style": style_name,
                "style_mix": new_mix,
                "reason": "Test override for audit logging"
            },
            headers=auth_headers
        )
        assert override_response.status_code == 200, f"Override failed: {override_response.text}"
        
        # Verify audit log entry was created
        final_response = requests.get(
            f"{BASE_URL}/api/buy-planning/audit-log",
            params={"entity_type": "style", "source": "manual"},
            headers=auth_headers
        )
        final_count = final_response.json()["total"]
        assert final_count > initial_count, "Audit log should have new entry after override"
        
        # Check the latest entry
        entries = final_response.json()["entries"]
        if entries:
            latest = entries[0]
            assert latest.get("action") == "override", f"Expected action=override: {latest}"
            assert latest.get("source") == "manual", f"Expected source=manual: {latest}"
            assert latest.get("entity_type") == "style", f"Expected entity_type=style: {latest}"
            print(f"Override audit entry: {latest.get('old_value')} -> {latest.get('new_value')}")


class TestSellThroughConfigAudit:
    """Tests for PUT /api/buy-planning/sell-through-config audit logging."""
    
    def test_sell_through_config_logs_to_audit(self, auth_headers):
        """Test that sell-through config change logs to audit log with action=config_update, source=manual."""
        # Get current config
        config_response = requests.get(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            headers=auth_headers
        )
        assert config_response.status_code == 200
        configs = config_response.json().get("configs", [])
        
        # Find Core config
        core_config = next((c for c in configs if c.get("style_mix") == "Core"), None)
        if not core_config:
            pytest.skip("No Core config found")
        
        current_multiplier = core_config.get("target_multiplier", 1.2)
        new_multiplier = 1.5 if current_multiplier != 1.5 else 1.3
        
        # Get initial audit count
        initial_response = requests.get(
            f"{BASE_URL}/api/buy-planning/audit-log",
            params={"entity_type": "config", "source": "manual"},
            headers=auth_headers
        )
        initial_count = initial_response.json()["total"]
        
        # Update config
        update_response = requests.put(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            json={
                "style_mix": "Core",
                "target_multiplier": new_multiplier
            },
            headers=auth_headers
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        # Verify audit log entry was created
        final_response = requests.get(
            f"{BASE_URL}/api/buy-planning/audit-log",
            params={"entity_type": "config", "source": "manual"},
            headers=auth_headers
        )
        final_count = final_response.json()["total"]
        assert final_count > initial_count, "Audit log should have new entry after config update"
        
        # Check the latest entry
        entries = final_response.json()["entries"]
        if entries:
            latest = entries[0]
            assert latest.get("action") == "config_update", f"Expected action=config_update: {latest}"
            assert latest.get("source") == "manual", f"Expected source=manual: {latest}"
            assert latest.get("entity_type") == "config", f"Expected entity_type=config: {latest}"
            print(f"Config audit entry: {latest.get('old_value')} -> {latest.get('new_value')}")
        
        # Reset config to default
        requests.post(
            f"{BASE_URL}/api/buy-planning/sell-through-config/reset",
            headers=auth_headers
        )


class TestAuditLogEntrySchema:
    """Tests for audit log entry schema validation."""
    
    def test_audit_entry_has_required_fields(self, auth_headers):
        """Test that audit log entries have all required fields."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/audit-log",
            headers=auth_headers
        )
        assert response.status_code == 200
        entries = response.json().get("entries", [])
        
        if not entries:
            pytest.skip("No audit entries to validate")
        
        required_fields = [
            "tenant_id", "action", "entity_type", "entity_id",
            "field", "old_value", "new_value", "source",
            "created_by", "created_at"
        ]
        
        for entry in entries[:5]:  # Check first 5 entries
            for field in required_fields:
                assert field in entry, f"Missing required field '{field}' in entry: {entry}"
        
        print(f"Validated {min(5, len(entries))} entries have all required fields")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
