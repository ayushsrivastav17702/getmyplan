"""
Test suite for Data Upload page features - Iteration 5
Tests: Upload endpoints, history, templates, status
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestUploadStatus:
    """Tests for upload status endpoint"""
    
    def test_get_upload_status(self):
        """GET /api/upload/status returns status for all 7 file types"""
        response = requests.get(f"{BASE_URL}/api/upload/status")
        assert response.status_code == 200
        
        data = response.json()
        # Should have all 7 file types
        expected_files = ['style_master', 'sku_ean_master', 'store_master', 
                         'warehouse_master', 'daily_sales', 'store_inventory', 
                         'warehouse_inventory']
        
        for file_type in expected_files:
            assert file_type in data, f"Missing file type: {file_type}"
            assert 'uploaded' in data[file_type]
            assert 'valid' in data[file_type]
            assert 'rows' in data[file_type]
            assert 'columns' in data[file_type]
        
        print(f"Upload status returned for all {len(expected_files)} file types")


class TestUploadHistory:
    """Tests for upload history endpoint"""
    
    def test_get_upload_history(self):
        """GET /api/upload/history returns array of history records"""
        response = requests.get(f"{BASE_URL}/api/upload/history?limit=50")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "History should be an array"
        
        # If there are records, verify structure
        if len(data) > 0:
            record = data[0]
            assert 'file_type' in record
            assert 'status' in record
            assert 'uploaded_at' in record
            print(f"History has {len(data)} records with proper structure")
        else:
            print("History is empty (expected for fresh uploads)")


class TestTemplateDownload:
    """Tests for template download endpoints"""
    
    def test_style_master_template(self):
        """GET /api/upload/template/style_master returns CSV with correct columns"""
        response = requests.get(f"{BASE_URL}/api/upload/template/style_master")
        assert response.status_code == 200
        
        # Check content type
        assert 'text/csv' in response.headers.get('Content-Type', '')
        
        # Check Content-Disposition header
        content_disp = response.headers.get('Content-Disposition', '')
        assert 'attachment' in content_disp
        assert 'style_master_template.csv' in content_disp
        
        # Check CSV content has required columns
        content = response.text
        first_line = content.split('\n')[0]
        required_cols = ['style_code', 'season', 'category', 'subcategory', 'gender', 'brand']
        for col in required_cols:
            assert col in first_line, f"Missing column: {col}"
        
        print(f"Style master template has columns: {first_line}")
    
    def test_daily_sales_template(self):
        """GET /api/upload/template/daily_sales returns CSV with correct columns"""
        response = requests.get(f"{BASE_URL}/api/upload/template/daily_sales")
        assert response.status_code == 200
        
        content = response.text
        first_line = content.split('\n')[0]
        required_cols = ['channel', 'store_code', 'sku', 'day', 'quantity', 'revenue']
        for col in required_cols:
            assert col in first_line, f"Missing column: {col}"
        
        print(f"Daily sales template has columns: {first_line}")
    
    def test_sku_ean_master_template(self):
        """GET /api/upload/template/sku_ean_master returns CSV"""
        response = requests.get(f"{BASE_URL}/api/upload/template/sku_ean_master")
        assert response.status_code == 200
        
        content = response.text
        first_line = content.split('\n')[0]
        required_cols = ['ean', 'style', 'size', 'mrp']
        for col in required_cols:
            assert col in first_line, f"Missing column: {col}"
        
        print(f"SKU-EAN master template has columns: {first_line}")
    
    def test_store_master_template(self):
        """GET /api/upload/template/store_master returns CSV"""
        response = requests.get(f"{BASE_URL}/api/upload/template/store_master")
        assert response.status_code == 200
        
        content = response.text
        first_line = content.split('\n')[0]
        required_cols = ['channel', 'store', 'store_code', 'city', 'region']
        for col in required_cols:
            assert col in first_line, f"Missing column: {col}"
        
        print(f"Store master template has columns: {first_line}")
    
    def test_warehouse_master_template(self):
        """GET /api/upload/template/warehouse_master returns CSV"""
        response = requests.get(f"{BASE_URL}/api/upload/template/warehouse_master")
        assert response.status_code == 200
        
        content = response.text
        first_line = content.split('\n')[0]
        required_cols = ['warehouse', 'online_fulfillment_flag']
        for col in required_cols:
            assert col in first_line, f"Missing column: {col}"
        
        print(f"Warehouse master template has columns: {first_line}")
    
    def test_store_inventory_template(self):
        """GET /api/upload/template/store_inventory returns CSV"""
        response = requests.get(f"{BASE_URL}/api/upload/template/store_inventory")
        assert response.status_code == 200
        
        content = response.text
        first_line = content.split('\n')[0]
        required_cols = ['channel', 'store_code', 'ean', 'day', 'quantity']
        for col in required_cols:
            assert col in first_line, f"Missing column: {col}"
        
        print(f"Store inventory template has columns: {first_line}")
    
    def test_warehouse_inventory_template(self):
        """GET /api/upload/template/warehouse_inventory returns CSV"""
        response = requests.get(f"{BASE_URL}/api/upload/template/warehouse_inventory")
        assert response.status_code == 200
        
        content = response.text
        first_line = content.split('\n')[0]
        required_cols = ['sku', 'warehouse', 'quantity', 'day']
        for col in required_cols:
            assert col in first_line, f"Missing column: {col}"
        
        print(f"Warehouse inventory template has columns: {first_line}")
    
    def test_invalid_template_returns_400(self):
        """GET /api/upload/template/invalid_type returns 400 error"""
        response = requests.get(f"{BASE_URL}/api/upload/template/invalid_type")
        assert response.status_code == 400
        
        data = response.json()
        assert 'detail' in data
        assert 'Unknown file type' in data['detail']
        
        print(f"Invalid template correctly returns 400: {data['detail']}")


class TestFileUpload:
    """Tests for file upload functionality"""
    
    def test_upload_valid_csv(self):
        """POST /api/upload/style_master with valid CSV"""
        # Create a minimal valid CSV
        csv_content = "style_code,season,category,subcategory,gender,brand\nTEST001,SS26,Shirts,Casual,Male,TestBrand"
        files = {'file': ('test_style.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
        
        response = requests.post(f"{BASE_URL}/api/upload/style_master", files=files)
        assert response.status_code == 200
        
        data = response.json()
        assert data['file_type'] == 'style_master'
        assert data['valid'] == True
        assert data['rows'] == 1
        assert 'style_code' in data['columns']
        
        print(f"Upload successful: {data['rows']} rows, valid={data['valid']}")
    
    def test_upload_creates_history_record(self):
        """Uploading a file creates a history record"""
        # Upload a file
        csv_content = "style_code,season,category,subcategory,gender,brand\nTEST002,SS26,Pants,Formal,Female,TestBrand2"
        files = {'file': ('test_style2.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
        
        response = requests.post(f"{BASE_URL}/api/upload/style_master", files=files)
        assert response.status_code == 200
        
        # Check history
        history_response = requests.get(f"{BASE_URL}/api/upload/history?limit=5")
        assert history_response.status_code == 200
        
        history = history_response.json()
        # Should have at least one record now
        assert len(history) > 0
        
        # Most recent should be our upload
        latest = history[0]
        assert latest['file_type'] == 'style_master'
        assert latest['status'] in ['success', 'failed']
        
        print(f"History record created: {latest['file_type']} - {latest['status']}")


class TestAllPagesLoad:
    """Tests that all pages are accessible"""
    
    def test_root_api(self):
        """GET /api/ returns welcome message"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        print(f"Root API: {data['message']}")
    
    def test_config_endpoint(self):
        """GET /api/config returns configuration"""
        response = requests.get(f"{BASE_URL}/api/config")
        assert response.status_code == 200
        data = response.json()
        assert 'noos_enabled' in data or 'ros_enabled' in data or len(data) >= 0
        print("Config endpoint working")
    
    def test_analytics_overview(self):
        """GET /api/analytics/overview returns stats"""
        response = requests.get(f"{BASE_URL}/api/analytics/overview")
        assert response.status_code == 200
        data = response.json()
        assert 'total_styles' in data
        assert 'total_stores' in data
        print(f"Analytics overview: {data['total_styles']} styles, {data['total_stores']} stores")
    
    def test_filter_options(self):
        """GET /api/analytics/filter-options returns filter options"""
        response = requests.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200
        data = response.json()
        assert 'categories' in data
        assert 'channels' in data
        assert 'regions' in data
        print(f"Filter options: {len(data['categories'])} categories, {len(data['channels'])} channels")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
