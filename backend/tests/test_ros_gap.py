"""
Test suite for ROS Gap Analysis API endpoint
Tests the new /api/analytics/ros-gap endpoint with PRD formulas
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestROSGapAnalysis:
    """ROS Gap Analysis endpoint tests"""
    
    def test_ros_gap_endpoint_returns_200(self):
        """Test that /api/analytics/ros-gap returns 200"""
        response = requests.get(f"{BASE_URL}/api/analytics/ros-gap")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("SUCCESS: /api/analytics/ros-gap returns 200")
    
    def test_ros_gap_has_summary(self):
        """Test that response has summary field with required KPIs"""
        response = requests.get(f"{BASE_URL}/api/analytics/ros-gap")
        data = response.json()
        
        assert 'summary' in data, "Response missing 'summary' field"
        summary = data['summary']
        
        # Check required KPI fields
        required_fields = [
            'avg_ros_gap',
            'total_sales_loss', 
            'healthy_coverage_pct',
            'total_styles',
            'healthy_styles',
            'broken_styles',
            'noos_styles',
            'total_noos_candidates'
        ]
        
        for field in required_fields:
            assert field in summary, f"Summary missing '{field}' field"
        
        print(f"SUCCESS: Summary has all required fields: {list(summary.keys())}")
    
    def test_ros_gap_has_style_ros_gap(self):
        """Test that response has style_ros_gap array"""
        response = requests.get(f"{BASE_URL}/api/analytics/ros-gap")
        data = response.json()
        
        assert 'style_ros_gap' in data, "Response missing 'style_ros_gap' field"
        style_data = data['style_ros_gap']
        
        assert isinstance(style_data, list), "style_ros_gap should be a list"
        assert len(style_data) > 0, "style_ros_gap should not be empty"
        
        # Check first item has required columns
        first_item = style_data[0]
        required_columns = ['style', 'healthy_ros', 'raw_ros', 'ros_gap', 'total_sales_loss', 'store_count', 'status']
        
        for col in required_columns:
            assert col in first_item, f"Style ROS Gap item missing '{col}' column"
        
        print(f"SUCCESS: style_ros_gap has {len(style_data)} items with required columns")
    
    def test_ros_gap_has_store_health(self):
        """Test that response has store_health array"""
        response = requests.get(f"{BASE_URL}/api/analytics/ros-gap")
        data = response.json()
        
        assert 'store_health' in data, "Response missing 'store_health' field"
        store_data = data['store_health']
        
        assert isinstance(store_data, list), "store_health should be a list"
        assert len(store_data) > 0, "store_health should not be empty"
        
        # Check first item has required columns
        first_item = store_data[0]
        required_columns = ['store_code', 'healthy_pct', 'broken_pct', 'total_sales_loss', 'style_count']
        
        for col in required_columns:
            assert col in first_item, f"Store Health item missing '{col}' column"
        
        print(f"SUCCESS: store_health has {len(store_data)} items with required columns")
    
    def test_ros_gap_has_noos_styles(self):
        """Test that response has noos_styles array"""
        response = requests.get(f"{BASE_URL}/api/analytics/ros-gap")
        data = response.json()
        
        assert 'noos_styles' in data, "Response missing 'noos_styles' field"
        noos_data = data['noos_styles']
        
        assert isinstance(noos_data, list), "noos_styles should be a list"
        assert len(noos_data) > 0, "noos_styles should not be empty"
        
        # Check first item has required columns
        first_item = noos_data[0]
        required_columns = ['style', 'store_count', 'noos_store_count', 'avg_sales_consistency', 'avg_inv_consistency', 'noos_pct', 'is_noos']
        
        for col in required_columns:
            assert col in first_item, f"NOOS Styles item missing '{col}' column"
        
        print(f"SUCCESS: noos_styles has {len(noos_data)} items with required columns")
    
    def test_ros_gap_summary_values_valid(self):
        """Test that summary values are valid numbers"""
        response = requests.get(f"{BASE_URL}/api/analytics/ros-gap")
        data = response.json()
        summary = data['summary']
        
        # Check numeric values
        assert isinstance(summary['avg_ros_gap'], (int, float)), "avg_ros_gap should be numeric"
        assert isinstance(summary['total_sales_loss'], (int, float)), "total_sales_loss should be numeric"
        assert isinstance(summary['healthy_coverage_pct'], (int, float)), "healthy_coverage_pct should be numeric"
        assert isinstance(summary['total_styles'], int), "total_styles should be integer"
        assert isinstance(summary['healthy_styles'], int), "healthy_styles should be integer"
        assert isinstance(summary['broken_styles'], int), "broken_styles should be integer"
        assert isinstance(summary['noos_styles'], int), "noos_styles should be integer"
        
        # Check coverage percentage is valid
        assert 0 <= summary['healthy_coverage_pct'] <= 100, "healthy_coverage_pct should be 0-100"
        
        # Check total = healthy + broken
        assert summary['total_styles'] == summary['healthy_styles'] + summary['broken_styles'], \
            "total_styles should equal healthy_styles + broken_styles"
        
        print(f"SUCCESS: Summary values are valid - avg_ros_gap={summary['avg_ros_gap']}, total_sales_loss={summary['total_sales_loss']}")
    
    def test_ros_gap_style_status_values(self):
        """Test that style status values are valid (Healthy or Broken)"""
        response = requests.get(f"{BASE_URL}/api/analytics/ros-gap")
        data = response.json()
        
        for item in data['style_ros_gap']:
            assert item['status'] in ['Healthy', 'Broken'], f"Invalid status: {item['status']}"
        
        print("SUCCESS: All style status values are valid (Healthy/Broken)")
    
    def test_ros_gap_with_filters(self):
        """Test that filters work correctly"""
        # Test with date filter
        response = requests.get(f"{BASE_URL}/api/analytics/ros-gap?start_date=2025-01-01&end_date=2025-12-31")
        assert response.status_code == 200, f"Expected 200 with date filter, got {response.status_code}"
        
        # Test with channel filter
        response = requests.get(f"{BASE_URL}/api/analytics/ros-gap?channels=Online")
        assert response.status_code == 200, f"Expected 200 with channel filter, got {response.status_code}"
        
        print("SUCCESS: Filters work correctly")


class TestExistingGapAnalysisEndpoints:
    """Test that existing NOOS and Size Gap endpoints still work"""
    
    def test_noos_endpoint_still_works(self):
        """Test that /api/analytics/noos still returns 200"""
        response = requests.get(f"{BASE_URL}/api/analytics/noos")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'summary' in data or 'data' in data, "NOOS response should have summary or data"
        print("SUCCESS: /api/analytics/noos still works")
    
    def test_size_gap_endpoint_still_works(self):
        """Test that /api/analytics/size-gap still returns 200"""
        response = requests.get(f"{BASE_URL}/api/analytics/size-gap")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'summary' in data or 'data' in data, "Size Gap response should have summary or data"
        print("SUCCESS: /api/analytics/size-gap still works")
    
    def test_filter_options_endpoint(self):
        """Test that filter options endpoint works"""
        response = requests.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'categories' in data, "Filter options should have categories"
        assert 'channels' in data, "Filter options should have channels"
        assert 'regions' in data, "Filter options should have regions"
        print("SUCCESS: /api/analytics/filter-options works")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
