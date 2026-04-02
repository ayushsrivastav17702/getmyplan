"""
Test Executive Dashboard API - Iteration 13
Tests the new /api/analytics/executive-dashboard endpoint that aggregates KPIs from all analytics modules.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestExecutiveDashboardAPI:
    """Tests for GET /api/analytics/executive-dashboard endpoint"""
    
    def test_executive_dashboard_returns_200(self):
        """Test that executive dashboard endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: Executive dashboard endpoint returns 200")
    
    def test_executive_dashboard_has_health_score(self):
        """Test that response contains health_score field"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        data = response.json()
        assert 'health_score' in data, "Missing health_score field"
        assert isinstance(data['health_score'], (int, float)), "health_score should be numeric"
        assert 0 <= data['health_score'] <= 100, f"health_score should be 0-100, got {data['health_score']}"
        print(f"PASS: health_score = {data['health_score']}")
    
    def test_executive_dashboard_has_modules(self):
        """Test that response contains modules object with all expected modules"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        data = response.json()
        assert 'modules' in data, "Missing modules field"
        
        expected_modules = ['ros_gap', 'stock_out', 'doh', 'planogram', 'replenishment']
        for module in expected_modules:
            assert module in data['modules'], f"Missing module: {module}"
        print(f"PASS: All expected modules present: {expected_modules}")
    
    def test_ros_gap_module_fields(self):
        """Test ROS Gap module has required fields"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        data = response.json()
        ros_gap = data['modules'].get('ros_gap')
        
        if ros_gap is not None:
            expected_fields = ['avg_ros_gap', 'total_sales_loss', 'healthy_coverage_pct', 
                             'healthy_styles', 'broken_styles', 'noos_styles']
            for field in expected_fields:
                assert field in ros_gap, f"ROS Gap missing field: {field}"
            print(f"PASS: ROS Gap module has all required fields")
        else:
            print("SKIP: ROS Gap module is None (no data)")
    
    def test_stock_out_module_fields(self):
        """Test Stock-Out module has required fields"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        data = response.json()
        stock_out = data['modules'].get('stock_out')
        
        if stock_out is not None:
            expected_fields = ['total_stockouts', 'stockout_rate', 'total_lost_sales', 'stores_impacted']
            for field in expected_fields:
                assert field in stock_out, f"Stock-Out missing field: {field}"
            print(f"PASS: Stock-Out module has all required fields")
        else:
            print("SKIP: Stock-Out module is None (no data)")
    
    def test_doh_module_fields(self):
        """Test DOH module has required fields"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        data = response.json()
        doh = data['modules'].get('doh')
        
        if doh is not None:
            expected_fields = ['overall_doh', 'ideal_doh', 'optimal_count', 
                             'overstocked_count', 'understocked_count', 'stockedout_count']
            for field in expected_fields:
                assert field in doh, f"DOH missing field: {field}"
            print(f"PASS: DOH module has all required fields")
        else:
            print("SKIP: DOH module is None (no data)")
    
    def test_planogram_module_fields(self):
        """Test Planogram module has required fields"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        data = response.json()
        planogram = data['modules'].get('planogram')
        
        if planogram is not None:
            expected_fields = ['overall_fill_rate', 'target_fill_rate', 'good_count', 
                             'moderate_count', 'critical_count', 'total_lost_sales']
            for field in expected_fields:
                assert field in planogram, f"Planogram missing field: {field}"
            print(f"PASS: Planogram module has all required fields")
        else:
            print("SKIP: Planogram module is None (no data)")
    
    def test_replenishment_module_fields(self):
        """Test Replenishment module has required fields"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        data = response.json()
        replenishment = data['modules'].get('replenishment')
        
        if replenishment is not None:
            expected_fields = ['total_po_value', 'total_reorder_units', 'skus_needing_reorder', 
                             'stockout_count', 'critical_count']
            for field in expected_fields:
                assert field in replenishment, f"Replenishment missing field: {field}"
            print(f"PASS: Replenishment module has all required fields")
        else:
            print("SKIP: Replenishment module is None (no data)")
    
    def test_executive_dashboard_has_alerts(self):
        """Test that response contains alerts array"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        data = response.json()
        assert 'alerts' in data, "Missing alerts field"
        assert isinstance(data['alerts'], list), "alerts should be a list"
        print(f"PASS: alerts array present with {len(data['alerts'])} alerts")
    
    def test_alerts_have_required_fields(self):
        """Test that each alert has required fields"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        data = response.json()
        alerts = data.get('alerts', [])
        
        if len(alerts) > 0:
            required_fields = ['module', 'priority', 'title', 'description', 'link']
            for i, alert in enumerate(alerts):
                for field in required_fields:
                    assert field in alert, f"Alert {i} missing field: {field}"
            print(f"PASS: All {len(alerts)} alerts have required fields")
        else:
            print("SKIP: No alerts to validate")
    
    def test_alerts_priority_values(self):
        """Test that alert priorities are valid values"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        data = response.json()
        alerts = data.get('alerts', [])
        
        valid_priorities = ['high', 'medium', 'low']
        for i, alert in enumerate(alerts):
            assert alert.get('priority') in valid_priorities, \
                f"Alert {i} has invalid priority: {alert.get('priority')}"
        print(f"PASS: All alerts have valid priority values")
    
    def test_alerts_sorted_by_priority(self):
        """Test that alerts are sorted by priority (high first)"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        data = response.json()
        alerts = data.get('alerts', [])
        
        if len(alerts) > 1:
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            for i in range(len(alerts) - 1):
                current_priority = priority_order.get(alerts[i].get('priority'), 2)
                next_priority = priority_order.get(alerts[i+1].get('priority'), 2)
                assert current_priority <= next_priority, \
                    f"Alerts not sorted by priority at index {i}"
            print("PASS: Alerts are sorted by priority (high first)")
        else:
            print("SKIP: Not enough alerts to verify sorting")
    
    def test_alerts_have_valid_links(self):
        """Test that alert links point to valid routes"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        data = response.json()
        alerts = data.get('alerts', [])
        
        valid_links = ['/gap-analysis', '/stock-out', '/doh', '/planogram', '/replenishment']
        for i, alert in enumerate(alerts):
            assert alert.get('link') in valid_links, \
                f"Alert {i} has invalid link: {alert.get('link')}"
        print(f"PASS: All alert links are valid routes")
    
    def test_executive_dashboard_with_date_filters(self):
        """Test that date filter parameters are accepted"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-dashboard",
            params={'start_date': '2026-01-01', 'end_date': '2026-01-31'}
        )
        assert response.status_code == 200, f"Expected 200 with date filters, got {response.status_code}"
        print("PASS: Date filter parameters accepted")
    
    def test_executive_dashboard_with_category_filter(self):
        """Test that category filter parameter is accepted"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-dashboard",
            params={'categories': 'Shirts'}
        )
        assert response.status_code == 200, f"Expected 200 with category filter, got {response.status_code}"
        print("PASS: Category filter parameter accepted")
    
    def test_executive_dashboard_with_channel_filter(self):
        """Test that channel filter parameter is accepted"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-dashboard",
            params={'channels': 'Online'}
        )
        assert response.status_code == 200, f"Expected 200 with channel filter, got {response.status_code}"
        print("PASS: Channel filter parameter accepted")
    
    def test_executive_dashboard_with_region_filter(self):
        """Test that region filter parameter is accepted"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-dashboard",
            params={'regions': 'North'}
        )
        assert response.status_code == 200, f"Expected 200 with region filter, got {response.status_code}"
        print("PASS: Region filter parameter accepted")


class TestExistingEndpointsRegression:
    """Regression tests to ensure existing endpoints still work"""
    
    def test_ros_gap_endpoint_still_works(self):
        """Regression: /api/analytics/ros-gap still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/ros-gap")
        assert response.status_code == 200, f"ROS Gap endpoint failed: {response.status_code}"
        print("PASS: /api/analytics/ros-gap still works")
    
    def test_stock_out_endpoint_still_works(self):
        """Regression: /api/analytics/stock-out still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out")
        assert response.status_code == 200, f"Stock-Out endpoint failed: {response.status_code}"
        print("PASS: /api/analytics/stock-out still works")
    
    def test_doh_endpoint_still_works(self):
        """Regression: /api/analytics/doh still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh")
        assert response.status_code == 200, f"DOH endpoint failed: {response.status_code}"
        print("PASS: /api/analytics/doh still works")
    
    def test_planogram_endpoint_still_works(self):
        """Regression: /api/analytics/planogram-fill-rate still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate")
        assert response.status_code == 200, f"Planogram endpoint failed: {response.status_code}"
        print("PASS: /api/analytics/planogram-fill-rate still works")
    
    def test_replenishment_endpoint_still_works(self):
        """Regression: /api/analytics/replenishment still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment")
        assert response.status_code == 200, f"Replenishment endpoint failed: {response.status_code}"
        print("PASS: /api/analytics/replenishment still works")
    
    def test_filter_options_endpoint_still_works(self):
        """Regression: /api/analytics/filter-options still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200, f"Filter options endpoint failed: {response.status_code}"
        print("PASS: /api/analytics/filter-options still works")
    
    def test_upload_status_endpoint_still_works(self):
        """Regression: /api/upload/status still works"""
        response = requests.get(f"{BASE_URL}/api/upload/status")
        assert response.status_code == 200, f"Upload status endpoint failed: {response.status_code}"
        print("PASS: /api/upload/status still works")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
