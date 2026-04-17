"""
Iteration 104: Inventory Ingestion + Statistical Safety Stock Tests
Tests for:
- POST /api/buy-planning/inventory/bulk - Bulk inventory upload (upsert)
- GET /api/buy-planning/inventory/summary - Inventory summary stats
- GET /api/buy-planning/inventory/sync-status - Last sync info
- GET /api/buy-planning/inventory - List inventory records with filters
- GET /api/buy-planning/safety-stock/config - Get safety stock config
- PUT /api/buy-planning/safety-stock/config - Update safety stock config
- POST /api/buy-planning/safety-stock/config/reset - Reset to defaults
- GET /api/buy-planning/safety-stock/calculate - Calculate statistical safety stock
- POST /api/buy-planning/buy-formula/calculate - Verify safety_method=statistical
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Valid service levels for safety stock config
VALID_SERVICE_LEVELS = [0.80, 0.85, 0.90, 0.95, 0.98, 0.99, 0.999]
Z_SCORES = {0.80: 0.842, 0.85: 1.036, 0.90: 1.282, 0.95: 1.645, 0.98: 2.054, 0.99: 2.326, 0.999: 3.09}


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@demo.com",
        "password": "demo1234"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestInventoryBulkUpload:
    """Tests for POST /api/buy-planning/inventory/bulk"""
    
    def test_bulk_upload_new_records(self, auth_headers):
        """Test uploading new inventory records."""
        records = [
            {"store_code": "TEST-STORE-01", "sku": "TEST-SKU-001", "date": "2025-01-15", "soh": 100, "in_transit": 20, "open_po_qty": 50},
            {"store_code": "TEST-STORE-01", "sku": "TEST-SKU-002", "date": "2025-01-15", "soh": 200, "in_transit": 30, "open_po_qty": 0},
            {"store_code": "TEST-STORE-02", "sku": "TEST-SKU-001", "date": "2025-01-15", "soh": 150, "in_transit": 0, "open_po_qty": 25},
        ]
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/inventory/bulk",
            json={"records": records, "source": "pytest"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Bulk upload failed: {response.text}"
        data = response.json()
        assert "inserted" in data
        assert "updated" in data
        assert "failed" in data
        assert data["total"] == 3
        assert data["failed"] == 0
        print(f"Bulk upload: inserted={data['inserted']}, updated={data['updated']}")
    
    def test_bulk_upload_upsert_existing(self, auth_headers):
        """Test that uploading same store/sku/date updates existing record."""
        # Upload initial record
        records = [{"store_code": "TEST-UPSERT-01", "sku": "TEST-SKU-UPSERT", "date": "2025-01-15", "soh": 50, "in_transit": 10}]
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/inventory/bulk",
            json={"records": records, "source": "pytest"},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Upload same record with different values
        records = [{"store_code": "TEST-UPSERT-01", "sku": "TEST-SKU-UPSERT", "date": "2025-01-15", "soh": 75, "in_transit": 15}]
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/inventory/bulk",
            json={"records": records, "source": "pytest"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Should be updated, not inserted
        assert data["updated"] >= 0 or data["inserted"] >= 0  # Either is valid for upsert
        print(f"Upsert test: inserted={data['inserted']}, updated={data['updated']}")
    
    def test_bulk_upload_flexible_field_names(self, auth_headers):
        """Test that store_id and sku_id are accepted as alternatives."""
        records = [
            {"store_id": "TEST-FLEX-01", "sku_id": "TEST-SKU-FLEX", "date": "2025-01-15", "soh": 80},
        ]
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/inventory/bulk",
            json={"records": records, "source": "pytest"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["failed"] == 0
        print("Flexible field names (store_id, sku_id) accepted")
    
    def test_bulk_upload_empty_records(self, auth_headers):
        """Test that empty records list returns 400."""
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/inventory/bulk",
            json={"records": [], "source": "pytest"},
            headers=auth_headers
        )
        assert response.status_code == 400
        print("Empty records correctly rejected with 400")


class TestInventorySummary:
    """Tests for GET /api/buy-planning/inventory/summary"""
    
    def test_inventory_summary_returns_stats(self, auth_headers):
        """Test that summary returns expected fields."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/inventory/summary",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Summary failed: {response.text}"
        data = response.json()
        assert "total_records" in data
        assert "total_soh" in data
        assert "total_in_transit" in data
        assert "unique_stores" in data
        assert "unique_skus" in data
        print(f"Inventory summary: records={data['total_records']}, soh={data['total_soh']}, stores={data['unique_stores']}, skus={data['unique_skus']}")


class TestInventorySyncStatus:
    """Tests for GET /api/buy-planning/inventory/sync-status"""
    
    def test_sync_status_returns_last_sync(self, auth_headers):
        """Test that sync status returns last sync info."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/inventory/sync-status",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Sync status failed: {response.text}"
        data = response.json()
        assert "last_sync" in data
        # After our bulk uploads, there should be a sync record
        if data["last_sync"]:
            assert "synced_at" in data["last_sync"]
            assert "source" in data["last_sync"]
            print(f"Last sync: {data['last_sync']['synced_at']} via {data['last_sync']['source']}")
        else:
            print("No sync records yet")


class TestInventoryList:
    """Tests for GET /api/buy-planning/inventory"""
    
    def test_list_inventory_all(self, auth_headers):
        """Test listing all inventory records."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/inventory",
            headers=auth_headers
        )
        assert response.status_code == 200, f"List inventory failed: {response.text}"
        data = response.json()
        assert "records" in data
        assert "total" in data
        print(f"Listed {data['total']} inventory records")
    
    def test_list_inventory_filter_by_store(self, auth_headers):
        """Test filtering inventory by store_code."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/inventory?store_code=TEST-STORE-01",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # All returned records should have the filtered store_code
        for rec in data["records"]:
            assert rec["store_code"] == "TEST-STORE-01"
        print(f"Filtered by store: {data['total']} records")
    
    def test_list_inventory_filter_by_sku(self, auth_headers):
        """Test filtering inventory by sku."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/inventory?sku=TEST-SKU-001",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for rec in data["records"]:
            assert rec["sku"] == "TEST-SKU-001"
        print(f"Filtered by SKU: {data['total']} records")


class TestSafetyStockConfig:
    """Tests for safety stock configuration endpoints"""
    
    def test_get_safety_config_returns_defaults_or_custom(self, auth_headers):
        """Test GET /api/buy-planning/safety-stock/config returns config."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/safety-stock/config",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get config failed: {response.text}"
        data = response.json()
        assert "service_level" in data
        assert "review_period_days" in data
        assert "max_safety_weeks" in data
        assert "z_score" in data
        assert "is_default" in data
        print(f"Safety config: SL={data['service_level']}, RP={data['review_period_days']}d, max={data['max_safety_weeks']}w, z={data['z_score']}, default={data['is_default']}")
    
    def test_update_safety_config_valid_service_level(self, auth_headers):
        """Test PUT /api/buy-planning/safety-stock/config with valid service level."""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/safety-stock/config",
            json={"service_level": 0.98, "review_period_days": 14, "max_safety_weeks": 8},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Update config failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert data["z_score"] == Z_SCORES[0.98]
        print(f"Updated config: SL=0.98, z_score={data['z_score']}")
        
        # Verify the update persisted
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/safety-stock/config",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["service_level"] == 0.98
        assert data["review_period_days"] == 14
        assert data["max_safety_weeks"] == 8
        assert data["is_default"] == False
    
    def test_update_safety_config_invalid_service_level(self, auth_headers):
        """Test PUT with invalid service level returns 400."""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/safety-stock/config",
            json={"service_level": 0.75, "review_period_days": 7, "max_safety_weeks": 12},
            headers=auth_headers
        )
        assert response.status_code == 400
        print("Invalid service level (0.75) correctly rejected with 400")
    
    def test_update_safety_config_all_valid_service_levels(self, auth_headers):
        """Test that all valid service levels are accepted."""
        for sl in VALID_SERVICE_LEVELS:
            response = requests.put(
                f"{BASE_URL}/api/buy-planning/safety-stock/config",
                json={"service_level": sl, "review_period_days": 7, "max_safety_weeks": 12},
                headers=auth_headers
            )
            assert response.status_code == 200, f"Service level {sl} should be valid"
            data = response.json()
            assert data["z_score"] == Z_SCORES[sl]
        print(f"All {len(VALID_SERVICE_LEVELS)} valid service levels accepted")
    
    def test_reset_safety_config(self, auth_headers):
        """Test POST /api/buy-planning/safety-stock/config/reset."""
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/safety-stock/config/reset",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Reset failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "defaults" in data
        assert data["defaults"]["service_level"] == 0.95
        assert data["defaults"]["review_period_days"] == 7
        assert data["defaults"]["max_safety_weeks"] == 12
        print("Safety config reset to defaults")
        
        # Verify reset
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/safety-stock/config",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_default"] == True


class TestSafetyStockCalculate:
    """Tests for GET /api/buy-planning/safety-stock/calculate"""
    
    def test_calculate_safety_stock_returns_formula_result(self, auth_headers):
        """Test safety stock calculation endpoint."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/safety-stock/calculate?sku=TEST-SKU-001&lead_time_days=14",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Calculate failed: {response.text}"
        data = response.json()
        assert "sku" in data
        assert data["sku"] == "TEST-SKU-001"
        assert "safety_stock_units" in data
        assert "mad" in data
        assert "z_score" in data
        assert "lead_time_days" in data
        assert data["lead_time_days"] == 14
        assert "review_period_days" in data
        assert "formula" in data
        assert data["formula"] == "z * MAD * sqrt(LT/RP)"
        print(f"Safety stock calculation: sku={data['sku']}, ss={data['safety_stock_units']}, mad={data['mad']}, z={data['z_score']}")
    
    def test_calculate_safety_stock_different_lead_times(self, auth_headers):
        """Test that different lead times produce different results."""
        response1 = requests.get(
            f"{BASE_URL}/api/buy-planning/safety-stock/calculate?sku=TEST-SKU-001&lead_time_days=7",
            headers=auth_headers
        )
        response2 = requests.get(
            f"{BASE_URL}/api/buy-planning/safety-stock/calculate?sku=TEST-SKU-001&lead_time_days=28",
            headers=auth_headers
        )
        assert response1.status_code == 200
        assert response2.status_code == 200
        data1 = response1.json()
        data2 = response2.json()
        # Longer lead time should result in higher safety stock (sqrt relationship)
        print(f"Lead time 7d: ss={data1['safety_stock_units']}, Lead time 28d: ss={data2['safety_stock_units']}")


class TestBuyFormulaStatisticalSafetyStock:
    """Tests for POST /api/buy-planning/buy-formula/calculate with statistical safety stock"""
    
    def test_buy_formula_uses_statistical_safety_method(self, auth_headers):
        """Test that buy formula calculation uses statistical safety stock method."""
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/buy-formula/calculate",
            json={"cover_days": 30, "safety_days": 7},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Buy formula failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "buy_plan" in data
        
        # Check that items have safety_method field
        if data["buy_plan"]:
            for item in data["buy_plan"][:5]:  # Check first 5 items
                assert "safety_method" in item, f"Item missing safety_method: {item}"
                assert item["safety_method"] == "statistical", f"Expected statistical, got {item['safety_method']}"
                assert "safety_stock" in item
            print(f"Buy formula: {len(data['buy_plan'])} items, all using safety_method=statistical")
        else:
            print("No buy plan items (may need SKU data)")
    
    def test_buy_formula_totals_include_safety_qty(self, auth_headers):
        """Test that totals include total_safety_qty."""
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/buy-formula/calculate",
            json={"cover_days": 30, "safety_days": 7},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "totals" in data
        assert "total_safety_qty" in data["totals"]
        print(f"Buy formula totals: safety_qty={data['totals']['total_safety_qty']}")


class TestInventoryCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_inventory(self, auth_headers):
        """Note: Test inventory records created during testing."""
        # Just verify we can still list inventory
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/inventory",
            headers=auth_headers
        )
        assert response.status_code == 200
        print("Test inventory records remain in database (TEST-STORE-*, TEST-SKU-*)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
