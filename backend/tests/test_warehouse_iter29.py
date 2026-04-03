"""
Warehouse Module Tests - Iteration 29
Tests WH-01 to WH-30: Stock, Movements, Transfers, Performance, Dashboard
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestWarehouseStock:
    """WH-01 to WH-08: Stock endpoint tests"""
    
    def test_wh01_stock_returns_required_fields(self):
        """WH-01: GET /api/analytics/warehouse/stock returns items with sku, warehouse, quantity, style, size"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/stock")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
        item = data["items"][0]
        assert "sku" in item
        assert "warehouse" in item
        assert "quantity" in item
        assert "style" in item
        assert "size" in item
    
    def test_wh02_stock_filter_by_warehouse(self):
        """WH-02: GET /api/analytics/warehouse/stock?warehouse=Central%20WH filters by warehouse"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/stock", params={"warehouse": "Central WH"})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # All items should be from Central WH
        for item in data["items"]:
            assert item["warehouse"] == "Central WH"
    
    def test_wh03_stock_filter_by_category(self):
        """WH-03: GET /api/analytics/warehouse/stock?category=Pants filters by category"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/stock", params={"category": "Pants"})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # All items should have category Pants
        for item in data["items"]:
            assert item.get("category", "").lower() == "pants"
    
    def test_wh04_stock_search_sku(self):
        """WH-04: GET /api/analytics/warehouse/stock?search=1769 returns matching SKU/style"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/stock", params={"search": "1769"})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # Should find items matching search
        assert len(data["items"]) > 0
        # At least one item should contain 1769 in sku or style
        found_match = False
        for item in data["items"]:
            if "1769" in str(item.get("sku", "")) or "1769" in str(item.get("style", "")):
                found_match = True
                break
        assert found_match, "No items found matching search term '1769'"
    
    def test_wh05_stock_value_calculation(self):
        """WH-05: Stock table includes mrp and stock_value (quantity x MRP). totals.total_value > 0"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/stock")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "totals" in data
        # Check totals has total_value > 0
        assert data["totals"].get("total_value", 0) > 0
        # Check items have mrp and stock_value
        item = data["items"][0]
        assert "mrp" in item
        assert "stock_value" in item
    
    def test_wh06_low_stock_count(self):
        """WH-06: totals.low_stock count (qty < reorder_point=50)"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/stock")
        assert response.status_code == 200
        data = response.json()
        assert "totals" in data
        assert "low_stock" in data["totals"]
        assert isinstance(data["totals"]["low_stock"], int)
        # Verify reorder_point is returned
        assert "reorder_point" in data["totals"]
    
    def test_wh07_out_of_stock_count(self):
        """WH-07: totals.out_of_stock count (qty = 0)"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/stock")
        assert response.status_code == 200
        data = response.json()
        assert "totals" in data
        assert "out_of_stock" in data["totals"]
        assert isinstance(data["totals"]["out_of_stock"], int)
    
    def test_wh08_overstock_count(self):
        """WH-08: totals.overstock count (qty > max_threshold=500)"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/stock")
        assert response.status_code == 200
        data = response.json()
        assert "totals" in data
        assert "overstock" in data["totals"]
        assert isinstance(data["totals"]["overstock"], int)
        # Verify max_threshold is returned
        assert "max_threshold" in data["totals"]


class TestWarehouseMovements:
    """WH-09 to WH-14: Movements, Daily Change, Reconciliation, Adjustments"""
    
    def test_wh09_movements_inbound(self):
        """WH-09: GET /api/analytics/warehouse/movements returns inbound items"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/movements")
        assert response.status_code == 200
        data = response.json()
        assert "movements" in data
        assert "summary" in data
        # Check summary has total_inbound > 0
        assert data["summary"].get("total_inbound", 0) > 0
        # Find an inbound movement
        inbound = [m for m in data["movements"] if m.get("direction") == "inbound"]
        assert len(inbound) > 0
        # Check inbound has source and reference
        assert "source" in inbound[0]
        assert "reference" in inbound[0]
    
    def test_wh10_movements_outbound(self):
        """WH-10: GET /api/analytics/warehouse/movements returns outbound items"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/movements")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        # Check summary has total_outbound > 0
        assert data["summary"].get("total_outbound", 0) > 0
        # Find an outbound movement
        outbound = [m for m in data["movements"] if m.get("direction") == "outbound"]
        assert len(outbound) > 0
        # Check outbound has destination and reference
        assert "destination" in outbound[0]
        assert "reference" in outbound[0]
    
    def test_wh11_movements_timeline(self):
        """WH-11: Movements have timestamp for timeline view"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/movements")
        assert response.status_code == 200
        data = response.json()
        assert "movements" in data
        assert len(data["movements"]) > 0
        # Check movements have timestamp
        for m in data["movements"][:5]:
            assert "timestamp" in m
    
    def test_wh12_daily_change(self):
        """WH-12: GET /api/analytics/warehouse/daily-change returns days with opening/closing/change"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/daily-change")
        assert response.status_code == 200
        data = response.json()
        assert "days" in data
        if len(data["days"]) > 0:
            day = data["days"][0]
            assert "opening_stock" in day
            assert "closing_stock" in day
            assert "change" in day
    
    def test_wh13_reconciliation_get(self):
        """WH-13: GET /api/analytics/warehouse/reconciliation returns reconciliations"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/reconciliation")
        assert response.status_code == 200
        data = response.json()
        assert "reconciliations" in data
        if len(data["reconciliations"]) > 0:
            rec = data["reconciliations"][0]
            assert "system_qty" in rec
            assert "physical_qty" in rec
            assert "variance" in rec
    
    def test_wh13_reconciliation_post(self):
        """WH-13: POST /api/analytics/warehouse/reconciliation creates new reconciliation"""
        payload = {
            "warehouse": "Central WH",
            "sku": "TEST_SKU_001",
            "system_qty": 100,
            "physical_qty": 95,
            "notes": "Test reconciliation",
            "reconciled_by": "test_user"
        }
        response = requests.post(f"{BASE_URL}/api/analytics/warehouse/reconciliation", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["system_qty"] == 100
        assert data["physical_qty"] == 95
        assert data["variance"] == -5
        assert "reconciliation_id" in data
    
    def test_wh14_adjustments(self):
        """WH-14: GET /api/analytics/warehouse/adjustments returns adjustments"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/adjustments")
        assert response.status_code == 200
        data = response.json()
        assert "adjustments" in data
        if len(data["adjustments"]) > 0:
            adj = data["adjustments"][0]
            assert "previous_qty" in adj
            assert "new_qty" in adj
            assert "change" in adj
            assert "reason" in adj
            assert "adjusted_by" in adj


class TestWarehouseTransfers:
    """WH-15 to WH-20: Transfer lifecycle tests"""
    
    @pytest.fixture
    def created_transfer(self):
        """Create a transfer for testing lifecycle"""
        payload = {
            "from_warehouse": "Central WH",
            "to_store": "ST001",
            "items": [{"sku": "TEST_SKU_002", "quantity": 10}],
            "created_by": "pytest_user"
        }
        response = requests.post(f"{BASE_URL}/api/analytics/warehouse/transfers", json=payload)
        assert response.status_code == 200
        return response.json()
    
    def test_wh15_create_transfer(self, created_transfer):
        """WH-15: POST /api/analytics/warehouse/transfers creates transfer with status=pending"""
        assert created_transfer["status"] == "pending"
        assert created_transfer["from_warehouse"] == "Central WH"
        assert created_transfer["to_store"] == "ST001"
        assert len(created_transfer["items"]) > 0
        assert "transfer_id" in created_transfer
    
    def test_wh16_allocate_transfer(self, created_transfer):
        """WH-16: PUT /api/analytics/warehouse/transfers/{id}/allocate changes status to allocated"""
        transfer_id = created_transfer["transfer_id"]
        response = requests.put(f"{BASE_URL}/api/analytics/warehouse/transfers/{transfer_id}/allocate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "allocated"
    
    def test_wh17_approve_transfer(self, created_transfer):
        """WH-17: PUT /api/analytics/warehouse/transfers/{id}/approve changes status to approved"""
        transfer_id = created_transfer["transfer_id"]
        # First allocate
        requests.put(f"{BASE_URL}/api/analytics/warehouse/transfers/{transfer_id}/allocate")
        # Then approve
        response = requests.put(
            f"{BASE_URL}/api/analytics/warehouse/transfers/{transfer_id}/approve",
            json={"approved_by": "test_manager"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
    
    def test_wh18_in_transit_transfers(self):
        """WH-18: GET /api/analytics/warehouse/transfers/in-transit returns in_transit transfers"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/transfers/in-transit")
        assert response.status_code == 200
        data = response.json()
        assert "transfers" in data
        assert "total_in_transit" in data
        # All transfers should have status in_transit
        for t in data["transfers"]:
            assert t["status"] == "in_transit"
    
    def test_wh19_receive_transfer(self, created_transfer):
        """WH-19: PUT /api/analytics/warehouse/transfers/{id}/receive changes status to received"""
        transfer_id = created_transfer["transfer_id"]
        # Full lifecycle: allocate -> approve -> dispatch -> receive
        requests.put(f"{BASE_URL}/api/analytics/warehouse/transfers/{transfer_id}/allocate")
        requests.put(f"{BASE_URL}/api/analytics/warehouse/transfers/{transfer_id}/approve", json={"approved_by": "mgr"})
        requests.put(f"{BASE_URL}/api/analytics/warehouse/transfers/{transfer_id}/dispatch")
        response = requests.put(
            f"{BASE_URL}/api/analytics/warehouse/transfers/{transfer_id}/receive",
            json={"received_by": "store_mgr"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
    
    def test_wh20_transfer_history(self):
        """WH-20: GET /api/analytics/warehouse/transfers/history returns full audit trail"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/transfers/history")
        assert response.status_code == 200
        data = response.json()
        assert "transfers" in data
        assert "total" in data
        assert data["total"] >= 0


class TestWarehousePerformance:
    """WH-21 to WH-25: Performance metrics tests"""
    
    def test_wh21_fulfillment_rate(self):
        """WH-21: GET /api/analytics/warehouse/performance returns fulfillment_rate"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/performance")
        assert response.status_code == 200
        data = response.json()
        assert "fulfillment_rate" in data
        assert isinstance(data["fulfillment_rate"], (int, float))
    
    def test_wh22_avg_dispatch_hours(self):
        """WH-22: GET /api/analytics/warehouse/performance returns avg_dispatch_hours"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/performance")
        assert response.status_code == 200
        data = response.json()
        assert "avg_dispatch_hours" in data
        assert isinstance(data["avg_dispatch_hours"], (int, float))
    
    def test_wh23_turnover_ratio(self):
        """WH-23: GET /api/analytics/warehouse/performance returns turnover_ratio"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/performance")
        assert response.status_code == 200
        data = response.json()
        assert "turnover_ratio" in data
        assert isinstance(data["turnover_ratio"], (int, float))
    
    def test_wh24_utilization(self):
        """WH-24: GET /api/analytics/warehouse/performance returns utilization_pct and by_warehouse"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/performance")
        assert response.status_code == 200
        data = response.json()
        assert "utilization_pct" in data
        assert "by_warehouse" in data
        # Check by_warehouse has capacity and utilization_pct
        if len(data["by_warehouse"]) > 0:
            wh = data["by_warehouse"][0]
            assert "capacity" in wh
            assert "utilization_pct" in wh
    
    def test_wh25_slow_moving(self):
        """WH-25: GET /api/analytics/warehouse/performance returns slow_moving array"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/performance")
        assert response.status_code == 200
        data = response.json()
        assert "slow_moving" in data
        assert isinstance(data["slow_moving"], list)


class TestWarehouseDashboard:
    """WH-26 to WH-30: Dashboard tests"""
    
    def test_wh26_dashboard_kpis(self):
        """WH-26: GET /api/analytics/warehouse/dashboard returns kpis with total_value > 0"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "kpis" in data
        kpis = data["kpis"]
        assert "total_stock" in kpis
        assert "total_value" in kpis
        assert kpis["total_value"] > 0
        assert "total_skus" in kpis
        assert "total_warehouses" in kpis
        assert "snapshot_date" in kpis
    
    def test_wh27_category_chart(self):
        """WH-27: GET /api/analytics/warehouse/dashboard returns category_chart array"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "category_chart" in data
        assert isinstance(data["category_chart"], list)
    
    def test_wh28_movement_trend(self):
        """WH-28: GET /api/analytics/warehouse/dashboard returns movement_trend with inbound/outbound"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "movement_trend" in data
        assert isinstance(data["movement_trend"], list)
        if len(data["movement_trend"]) > 0:
            trend = data["movement_trend"][0]
            assert "inbound" in trend
            assert "outbound" in trend
    
    def test_wh30_warehouse_comparison(self):
        """WH-30: GET /api/analytics/warehouse/dashboard returns comparison array"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "comparison" in data
        assert isinstance(data["comparison"], list)
        if len(data["comparison"]) > 0:
            comp = data["comparison"][0]
            assert "warehouse" in comp
            assert "total_qty" in comp
            assert "stock_value" in comp
            assert "sku_count" in comp


class TestSeedDemo:
    """Test seed demo endpoint"""
    
    def test_seed_demo(self):
        """POST /api/analytics/warehouse/seed-demo seeds demo data"""
        response = requests.post(f"{BASE_URL}/api/analytics/warehouse/seed-demo")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "counts" in data
        assert data["counts"]["movements"] > 0
        assert data["counts"]["transfers"] > 0
