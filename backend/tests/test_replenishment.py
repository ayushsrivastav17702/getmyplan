"""
Test suite for Replenishment Planner API endpoint
Tests the /api/analytics/replenishment endpoint with various parameters
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://zip-improved.preview.emergentagent.com').rstrip('/')


class TestReplenishmentAPI:
    """Tests for /api/analytics/replenishment endpoint"""
    
    def test_replenishment_endpoint_returns_200(self):
        """Test that replenishment endpoint returns 200 status"""
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("SUCCESS: Replenishment endpoint returns 200")
    
    def test_replenishment_response_has_summary(self):
        """Test that response contains summary with all required KPIs"""
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment")
        data = response.json()
        
        assert "summary" in data, "Response missing 'summary' field"
        summary = data["summary"]
        
        required_fields = [
            "total_po_value", "total_reorder_units", "skus_needing_reorder",
            "stores_needing_reorder", "stockout_count", "critical_count",
            "high_count", "lead_time_days", "safety_days", "snapshot_date"
        ]
        
        for field in required_fields:
            assert field in summary, f"Summary missing '{field}' field"
        
        print(f"SUCCESS: Summary has all required fields: {list(summary.keys())}")
    
    def test_replenishment_response_has_by_priority(self):
        """Test that response contains by_priority array with correct structure"""
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment")
        data = response.json()
        
        assert "by_priority" in data, "Response missing 'by_priority' field"
        assert isinstance(data["by_priority"], list), "by_priority should be a list"
        
        if len(data["by_priority"]) > 0:
            first_item = data["by_priority"][0]
            required_fields = ["priority", "count", "total_units", "total_value"]
            for field in required_fields:
                assert field in first_item, f"by_priority item missing '{field}'"
        
        print(f"SUCCESS: by_priority has {len(data['by_priority'])} items")
    
    def test_replenishment_response_has_by_store(self):
        """Test that response contains by_store array with correct structure"""
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment")
        data = response.json()
        
        assert "by_store" in data, "Response missing 'by_store' field"
        assert isinstance(data["by_store"], list), "by_store should be a list"
        
        if len(data["by_store"]) > 0:
            first_item = data["by_store"][0]
            required_fields = ["store_code", "sku_count", "total_units", "total_value", "urgent_count"]
            for field in required_fields:
                assert field in first_item, f"by_store item missing '{field}'"
        
        print(f"SUCCESS: by_store has {len(data['by_store'])} items")
    
    def test_replenishment_response_has_by_style(self):
        """Test that response contains by_style array with correct structure"""
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment")
        data = response.json()
        
        assert "by_style" in data, "Response missing 'by_style' field"
        assert isinstance(data["by_style"], list), "by_style should be a list"
        
        if len(data["by_style"]) > 0:
            first_item = data["by_style"][0]
            required_fields = ["style", "sku_count", "total_units", "total_value", "avg_days"]
            for field in required_fields:
                assert field in first_item, f"by_style item missing '{field}'"
        
        print(f"SUCCESS: by_style has {len(data['by_style'])} items")
    
    def test_replenishment_response_has_detail(self):
        """Test that response contains detail array with all required columns"""
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment")
        data = response.json()
        
        assert "detail" in data, "Response missing 'detail' field"
        assert isinstance(data["detail"], list), "detail should be a list"
        
        if len(data["detail"]) > 0:
            first_item = data["detail"][0]
            required_fields = [
                "sku", "style", "size", "store_code", "current_soh", "ros",
                "days_to_stockout", "safety_stock", "reorder_qty", "po_value", "priority"
            ]
            for field in required_fields:
                assert field in first_item, f"detail item missing '{field}'"
        
        print(f"SUCCESS: detail has {len(data['detail'])} items with all required columns")
    
    def test_replenishment_with_lead_time_param(self):
        """Test that lead_time_days parameter is accepted and reflected in response"""
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment?lead_time_days=30")
        data = response.json()
        
        assert response.status_code == 200
        assert data["summary"]["lead_time_days"] == 30, "lead_time_days not reflected in response"
        print("SUCCESS: lead_time_days parameter works correctly")
    
    def test_replenishment_with_safety_days_param(self):
        """Test that safety_days parameter is accepted and reflected in response"""
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment?safety_days=14")
        data = response.json()
        
        assert response.status_code == 200
        assert data["summary"]["safety_days"] == 14, "safety_days not reflected in response"
        print("SUCCESS: safety_days parameter works correctly")
    
    def test_replenishment_with_both_params(self):
        """Test that both lead_time_days and safety_days parameters work together"""
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment?lead_time_days=45&safety_days=21")
        data = response.json()
        
        assert response.status_code == 200
        assert data["summary"]["lead_time_days"] == 45
        assert data["summary"]["safety_days"] == 21
        print("SUCCESS: Both parameters work together correctly")
    
    def test_replenishment_po_value_increases_with_lead_time(self):
        """Test that PO value increases when lead time increases"""
        response_14 = requests.get(f"{BASE_URL}/api/analytics/replenishment?lead_time_days=14&safety_days=7")
        response_30 = requests.get(f"{BASE_URL}/api/analytics/replenishment?lead_time_days=30&safety_days=7")
        
        data_14 = response_14.json()
        data_30 = response_30.json()
        
        po_value_14 = data_14["summary"]["total_po_value"]
        po_value_30 = data_30["summary"]["total_po_value"]
        
        assert po_value_30 > po_value_14, f"PO value should increase with lead time: {po_value_14} vs {po_value_30}"
        print(f"SUCCESS: PO value increases with lead time ({po_value_14} -> {po_value_30})")
    
    def test_replenishment_priority_values_are_valid(self):
        """Test that priority values are valid (Stock-Out, Critical, High, Medium, Low)"""
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment")
        data = response.json()
        
        valid_priorities = ["Stock-Out", "Critical", "High", "Medium", "Low"]
        
        for item in data["by_priority"]:
            assert item["priority"] in valid_priorities, f"Invalid priority: {item['priority']}"
        
        for item in data["detail"][:50]:  # Check first 50 detail items
            assert item["priority"] in valid_priorities, f"Invalid priority in detail: {item['priority']}"
        
        print("SUCCESS: All priority values are valid")
    
    def test_replenishment_summary_values_are_valid_numbers(self):
        """Test that summary values are valid numbers"""
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment")
        data = response.json()
        summary = data["summary"]
        
        assert isinstance(summary["total_po_value"], (int, float)) and summary["total_po_value"] >= 0
        assert isinstance(summary["total_reorder_units"], int) and summary["total_reorder_units"] >= 0
        assert isinstance(summary["skus_needing_reorder"], int) and summary["skus_needing_reorder"] >= 0
        assert isinstance(summary["stores_needing_reorder"], int) and summary["stores_needing_reorder"] >= 0
        assert isinstance(summary["stockout_count"], int) and summary["stockout_count"] >= 0
        assert isinstance(summary["critical_count"], int) and summary["critical_count"] >= 0
        
        print("SUCCESS: All summary values are valid numbers")


class TestReplenishmentRegressionAPIs:
    """Regression tests for existing analytics endpoints"""
    
    def test_stock_out_endpoint_still_works(self):
        """Regression: Stock-Out endpoint should still work"""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data or "error" not in data
        print("SUCCESS: Stock-Out endpoint still works (regression)")
    
    def test_ros_gap_endpoint_still_works(self):
        """Regression: ROS Gap endpoint should still work"""
        response = requests.get(f"{BASE_URL}/api/analytics/ros-gap")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data or "error" not in data
        print("SUCCESS: ROS Gap endpoint still works (regression)")
    
    def test_size_gap_endpoint_still_works(self):
        """Regression: Size Gap endpoint should still work"""
        response = requests.get(f"{BASE_URL}/api/analytics/size-gap")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data or "error" not in data
        print("SUCCESS: Size Gap endpoint still works (regression)")
    
    def test_noos_endpoint_still_works(self):
        """Regression: NOOS endpoint should still work"""
        response = requests.get(f"{BASE_URL}/api/analytics/noos")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data or "error" not in data
        print("SUCCESS: NOOS endpoint still works (regression)")
    
    def test_filter_options_endpoint_still_works(self):
        """Regression: Filter options endpoint should still work"""
        response = requests.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "channels" in data
        assert "regions" in data
        print("SUCCESS: Filter options endpoint still works (regression)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
