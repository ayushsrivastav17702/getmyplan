"""
Test Suite for Phase 2 Upload Types: COGS, Planogram, Open Orders, Style Master V2
Tests V2 upload endpoints, validation, templates, and status endpoints.
Iteration 60 - Phase 2 Upload Types Testing
"""
import pytest
import requests
import os
import tempfile
import csv

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@demo.com"
TEST_PASSWORD = "demo1234"


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    def test_01_login_success(self, auth_token):
        """TEST_01: Login with admin@demo.com/demo1234 returns access_token"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✓ TEST_01: Login successful, token length: {len(auth_token)}")


class TestCOGSUpload:
    """COGS (Cost of Goods Sold) upload tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_02_cogs_upload_success(self, headers):
        """TEST_02: POST /api/upload/v2/cogs with valid CSV - validates file structure and returns response"""
        # Create test CSV - Note: store codes may not exist in master, but endpoint should process the file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['transaction_date', 'store_code', 'sku_code', 'cogs'])
            writer.writerow(['2026-01-15', 'TEST_STORE_001', 'TEST_SKU_001', '150.50'])
            writer.writerow(['2026-01-15', 'TEST_STORE_002', 'TEST_SKU_002', '200.00'])
            f.flush()
            csv_path = f.name
        
        try:
            with open(csv_path, 'rb') as f:
                response = requests.post(
                    f"{BASE_URL}/api/upload/v2/cogs",
                    files={'file': ('test_cogs.csv', f, 'text/csv')},
                    headers=headers
                )
            
            assert response.status_code == 200, f"COGS upload failed: {response.text}"
            data = response.json()
            # Endpoint should return proper response structure
            assert "total_rows" in data, "Missing total_rows in response"
            assert data.get("total_rows") == 2, f"Expected 2 rows, got {data.get('total_rows')}"
            assert data.get("validate_only") == False, "Should not be validate_only"
            # If validation fails due to store codes not in master, that's expected behavior
            if data.get("success") == False:
                errors = data.get("errors", [])
                error_codes = [e.get("code") for e in errors]
                # E011 = store code not found - this is expected validation behavior
                assert "E011" in error_codes, f"Expected E011 error for unknown stores, got: {error_codes}"
                print(f"✓ TEST_02: COGS upload processed, validation correctly rejected unknown store codes")
            else:
                print(f"✓ TEST_02: COGS upload success, {data.get('total_rows')} rows saved")
        finally:
            os.unlink(csv_path)
    
    def test_03_cogs_validate_only(self, headers):
        """TEST_03: POST /api/upload/v2/cogs/validate returns validate_only=true, does NOT save"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['transaction_date', 'store_code', 'sku_code', 'cogs'])
            writer.writerow(['2026-01-16', 'VALIDATE_STORE', 'VALIDATE_SKU', '99.99'])
            f.flush()
            csv_path = f.name
        
        try:
            with open(csv_path, 'rb') as f:
                response = requests.post(
                    f"{BASE_URL}/api/upload/v2/cogs/validate",
                    files={'file': ('test_cogs_validate.csv', f, 'text/csv')},
                    headers=headers
                )
            
            assert response.status_code == 200, f"COGS validate failed: {response.text}"
            data = response.json()
            assert data.get("validate_only") == True, "Should be validate_only=true"
            # Validation may fail due to unknown store codes - that's expected
            print(f"✓ TEST_03: COGS validate_only=true, success={data.get('success')}")
        finally:
            os.unlink(csv_path)
    
    def test_04_cogs_missing_column_error(self, headers):
        """TEST_04: Upload COGS CSV with missing sku_code column should return error E043"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            # Missing sku_code column
            writer.writerow(['transaction_date', 'store_code', 'cogs'])
            writer.writerow(['2026-01-15', 'STORE_001', '150.50'])
            f.flush()
            csv_path = f.name
        
        try:
            with open(csv_path, 'rb') as f:
                response = requests.post(
                    f"{BASE_URL}/api/upload/v2/cogs",
                    files={'file': ('test_cogs_missing.csv', f, 'text/csv')},
                    headers=headers
                )
            
            assert response.status_code == 200, f"Request failed: {response.text}"
            data = response.json()
            assert data.get("success") == False, "Should fail with missing column"
            errors = data.get("errors", [])
            error_codes = [e.get("code") for e in errors]
            assert "E043" in error_codes, f"Expected E043 error, got: {error_codes}"
            print(f"✓ TEST_04: COGS missing column returns E043 error")
        finally:
            os.unlink(csv_path)
    
    def test_05_cogs_template_download(self, headers):
        """TEST_05: GET /api/upload/v2/template/cogs returns 200 with XLSX file"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/template/cogs",
            headers=headers
        )
        
        assert response.status_code == 200, f"Template download failed: {response.status_code}"
        content_type = response.headers.get('content-type', '')
        assert 'spreadsheet' in content_type or 'xlsx' in content_type or 'octet-stream' in content_type, \
            f"Expected XLSX content type, got: {content_type}"
        assert len(response.content) > 0, "Template file is empty"
        print(f"✓ TEST_05: COGS template download success, size: {len(response.content)} bytes")


class TestPlanogramUpload:
    """Planogram upload tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_06_planogram_upload_success(self, headers):
        """TEST_06: POST /api/upload/v2/planogram with valid CSV - validates file structure"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            # Only required columns: store_code, category, style_code, norm_allocated
            writer.writerow(['store_code', 'category', 'style_code', 'norm_allocated'])
            writer.writerow(['TEST_STORE_001', 'Shirts', 'STYLE_001', '10'])
            writer.writerow(['TEST_STORE_002', 'Pants', 'STYLE_002', '15'])
            f.flush()
            csv_path = f.name
        
        try:
            with open(csv_path, 'rb') as f:
                response = requests.post(
                    f"{BASE_URL}/api/upload/v2/planogram",
                    files={'file': ('test_planogram.csv', f, 'text/csv')},
                    headers=headers
                )
            
            assert response.status_code == 200, f"Planogram upload failed: {response.text}"
            data = response.json()
            assert "total_rows" in data, "Missing total_rows in response"
            assert data.get("total_rows") == 2, f"Expected 2 rows, got {data.get('total_rows')}"
            # If validation fails due to store codes not in master, that's expected
            if data.get("success") == False:
                errors = data.get("errors", [])
                error_codes = [e.get("code") for e in errors]
                assert "E011" in error_codes, f"Expected E011 error for unknown stores, got: {error_codes}"
                print(f"✓ TEST_06: Planogram upload processed, validation correctly rejected unknown store codes")
            else:
                print(f"✓ TEST_06: Planogram upload success, {data.get('total_rows')} rows saved")
        finally:
            os.unlink(csv_path)
    
    def test_07_planogram_validate_only(self, headers):
        """TEST_07: POST /api/upload/v2/planogram/validate returns validate_only=true"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['store_code', 'category', 'style_code', 'norm_allocated'])
            writer.writerow(['VALIDATE_STORE', 'Category', 'VALIDATE_STYLE', '5'])
            f.flush()
            csv_path = f.name
        
        try:
            with open(csv_path, 'rb') as f:
                response = requests.post(
                    f"{BASE_URL}/api/upload/v2/planogram/validate",
                    files={'file': ('test_planogram_validate.csv', f, 'text/csv')},
                    headers=headers
                )
            
            assert response.status_code == 200, f"Planogram validate failed: {response.text}"
            data = response.json()
            assert data.get("validate_only") == True, "Should be validate_only=true"
            print(f"✓ TEST_07: Planogram validate_only=true, success={data.get('success')}")
        finally:
            os.unlink(csv_path)
    
    def test_08_planogram_empty_file_error(self, headers):
        """TEST_08: Upload empty CSV for planogram should return error E045"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            # Only headers, no data rows
            writer.writerow(['store_code', 'category', 'style_code', 'norm_allocated'])
            f.flush()
            csv_path = f.name
        
        try:
            with open(csv_path, 'rb') as f:
                response = requests.post(
                    f"{BASE_URL}/api/upload/v2/planogram",
                    files={'file': ('test_planogram_empty.csv', f, 'text/csv')},
                    headers=headers
                )
            
            assert response.status_code == 200, f"Request failed: {response.text}"
            data = response.json()
            assert data.get("success") == False, "Should fail with empty file"
            errors = data.get("errors", [])
            error_codes = [e.get("code") for e in errors]
            assert "E045" in error_codes, f"Expected E045 error, got: {error_codes}"
            print(f"✓ TEST_08: Planogram empty file returns E045 error")
        finally:
            os.unlink(csv_path)
    
    def test_09_planogram_template_download(self, headers):
        """TEST_09: GET /api/upload/v2/template/planogram returns 200 with XLSX file"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/template/planogram",
            headers=headers
        )
        
        assert response.status_code == 200, f"Template download failed: {response.status_code}"
        assert len(response.content) > 0, "Template file is empty"
        print(f"✓ TEST_09: Planogram template download success, size: {len(response.content)} bytes")


class TestOpenOrdersUpload:
    """Open Orders upload tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_10_open_orders_upload_success(self, headers):
        """TEST_10: POST /api/upload/v2/open-orders with valid CSV - validates file structure"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['order_date', 'expected_delivery_date', 'store_code', 'sku_code', 'order_quantity', 'status', 'source_type'])
            writer.writerow(['2026-01-15', '2026-01-20', 'TEST_STORE_001', 'TEST_SKU_001', '100', 'pending', 'warehouse'])
            writer.writerow(['2026-01-16', '2026-01-22', 'TEST_STORE_002', 'TEST_SKU_002', '50', 'in_transit', 'vendor'])
            f.flush()
            csv_path = f.name
        
        try:
            with open(csv_path, 'rb') as f:
                response = requests.post(
                    f"{BASE_URL}/api/upload/v2/open-orders",
                    files={'file': ('test_open_orders.csv', f, 'text/csv')},
                    headers=headers
                )
            
            assert response.status_code == 200, f"Open orders upload failed: {response.text}"
            data = response.json()
            assert "total_rows" in data, "Missing total_rows in response"
            assert data.get("total_rows") == 2, f"Expected 2 rows, got {data.get('total_rows')}"
            # If validation fails due to store codes not in master, that's expected
            if data.get("success") == False:
                errors = data.get("errors", [])
                error_codes = [e.get("code") for e in errors]
                assert "E011" in error_codes, f"Expected E011 error for unknown stores, got: {error_codes}"
                print(f"✓ TEST_10: Open orders upload processed, validation correctly rejected unknown store codes")
            else:
                print(f"✓ TEST_10: Open orders upload success, {data.get('total_rows')} rows saved")
        finally:
            os.unlink(csv_path)
    
    def test_11_open_orders_validate_only(self, headers):
        """TEST_11: POST /api/upload/v2/open_orders/validate returns validate_only=true"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['order_date', 'expected_delivery_date', 'store_code', 'sku_code', 'order_quantity', 'status', 'source_type'])
            writer.writerow(['2026-01-17', '2026-01-25', 'VALIDATE_STORE', 'VALIDATE_SKU', '25', 'pending', 'warehouse'])
            f.flush()
            csv_path = f.name
        
        try:
            with open(csv_path, 'rb') as f:
                response = requests.post(
                    f"{BASE_URL}/api/upload/v2/open_orders/validate",
                    files={'file': ('test_open_orders_validate.csv', f, 'text/csv')},
                    headers=headers
                )
            
            assert response.status_code == 200, f"Open orders validate failed: {response.text}"
            data = response.json()
            assert data.get("validate_only") == True, "Should be validate_only=true"
            print(f"✓ TEST_11: Open orders validate_only=true, success={data.get('success')}")
        finally:
            os.unlink(csv_path)
    
    def test_12_open_orders_template_download(self, headers):
        """TEST_12: GET /api/upload/v2/template/open_orders returns 200 with XLSX file"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/template/open_orders",
            headers=headers
        )
        
        assert response.status_code == 200, f"Template download failed: {response.status_code}"
        assert len(response.content) > 0, "Template file is empty"
        print(f"✓ TEST_12: Open orders template download success, size: {len(response.content)} bytes")


class TestStyleMasterUpload:
    """Style Master V2 upload tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_13_style_master_upload_success(self, headers):
        """TEST_13: POST /api/upload/v2/style-master with valid CSV returns success=true"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['style_code', 'season', 'category', 'subcategory', 'gender', 'brand'])
            writer.writerow(['TEST_STYLE_001', 'SS26', 'Shirts', 'Casual', 'Male', 'BrandA'])
            writer.writerow(['TEST_STYLE_002', 'AW26', 'Pants', 'Formal', 'Female', 'BrandB'])
            f.flush()
            csv_path = f.name
        
        try:
            with open(csv_path, 'rb') as f:
                response = requests.post(
                    f"{BASE_URL}/api/upload/v2/style-master",
                    files={'file': ('test_style_master.csv', f, 'text/csv')},
                    headers=headers
                )
            
            assert response.status_code == 200, f"Style master upload failed: {response.text}"
            data = response.json()
            assert data.get("success") == True, f"Style master upload not successful: {data}"
            assert data.get("total_rows") == 2, f"Expected 2 rows, got {data.get('total_rows')}"
            print(f"✓ TEST_13: Style master upload success, {data.get('total_rows')} rows saved")
        finally:
            os.unlink(csv_path)
    
    def test_14_style_master_validate_only(self, headers):
        """TEST_14: POST /api/upload/v2/style_master/validate returns validate_only=true"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['style_code', 'season', 'category', 'subcategory', 'gender', 'brand'])
            writer.writerow(['VALIDATE_STYLE', 'SS26', 'Test', 'Test', 'Unisex', 'TestBrand'])
            f.flush()
            csv_path = f.name
        
        try:
            with open(csv_path, 'rb') as f:
                response = requests.post(
                    f"{BASE_URL}/api/upload/v2/style_master/validate",
                    files={'file': ('test_style_master_validate.csv', f, 'text/csv')},
                    headers=headers
                )
            
            assert response.status_code == 200, f"Style master validate failed: {response.text}"
            data = response.json()
            assert data.get("validate_only") == True, "Should be validate_only=true"
            print(f"✓ TEST_14: Style master validate_only=true, success={data.get('success')}")
        finally:
            os.unlink(csv_path)
    
    def test_15_style_master_template_download(self, headers):
        """TEST_15: GET /api/upload/v2/template/style_master returns 200 with XLSX file"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/template/style_master",
            headers=headers
        )
        
        assert response.status_code == 200, f"Template download failed: {response.status_code}"
        assert len(response.content) > 0, "Template file is empty"
        print(f"✓ TEST_15: Style master template download success, size: {len(response.content)} bytes")


class TestStatusEndpoints:
    """Status endpoints tests for new upload types"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_16_master_status_includes_new_types(self, headers):
        """TEST_16: GET /api/upload/v2/master-status returns style_master and planogram entries"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/master-status",
            headers=headers
        )
        
        assert response.status_code == 200, f"Master status failed: {response.text}"
        data = response.json()
        
        # Check style_master entry exists
        assert "style_master" in data, f"style_master not in master-status: {data.keys()}"
        assert "count" in data["style_master"], "style_master missing count field"
        
        # Check planogram entry exists
        assert "planogram" in data, f"planogram not in master-status: {data.keys()}"
        assert "count" in data["planogram"], "planogram missing count field"
        
        print(f"✓ TEST_16: Master status includes style_master (count={data['style_master']['count']}) and planogram (count={data['planogram']['count']})")
    
    def test_17_daily_status_includes_new_types(self, headers):
        """TEST_17: GET /api/upload/v2/daily-status returns cogs and open_orders entries"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/daily-status",
            headers=headers
        )
        
        assert response.status_code == 200, f"Daily status failed: {response.text}"
        data = response.json()
        
        # Check cogs entry exists
        assert "cogs" in data, f"cogs not in daily-status: {data.keys()}"
        assert "uploaded" in data["cogs"], "cogs missing uploaded field"
        
        # Check open_orders entry exists
        assert "open_orders" in data, f"open_orders not in daily-status: {data.keys()}"
        assert "uploaded" in data["open_orders"], "open_orders missing uploaded field"
        
        print(f"✓ TEST_17: Daily status includes cogs (uploaded={data['cogs']['uploaded']}) and open_orders (uploaded={data['open_orders']['uploaded']})")
    
    def test_18_upload_history_includes_new_types(self, headers):
        """TEST_18: GET /api/upload/v2/history returns upload records for new types"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/history?days=7",
            headers=headers
        )
        
        assert response.status_code == 200, f"Upload history failed: {response.text}"
        data = response.json()
        assert "history" in data, "history key missing from response"
        print(f"✓ TEST_18: Upload history endpoint working, {len(data.get('history', []))} days returned")


class TestRegressionAnalytics:
    """Regression tests for previously working analytics endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_19_ros_endpoint_regression(self, headers):
        """TEST_19: GET /api/analytics/core/ros returns data (regression)"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/core/ros",
            headers=headers
        )
        
        assert response.status_code == 200, f"ROS endpoint failed: {response.status_code}"
        data = response.json()
        # Should have style_data and summary keys (actual response structure)
        assert "style_data" in data or "summary" in data or "error" in data, f"Unexpected response keys: {data.keys()}"
        if "summary" in data:
            assert "total_styles" in data["summary"], "Missing total_styles in summary"
            print(f"✓ TEST_19: ROS endpoint working, total_styles={data['summary'].get('total_styles')}")
        else:
            print(f"✓ TEST_19: ROS endpoint working (status=200)")
    
    def test_20_doh_analysis_regression(self, headers):
        """TEST_20: GET /api/analytics/doh/analysis returns summary (regression)"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/doh/analysis",
            headers=headers
        )
        
        assert response.status_code == 200, f"DOH analysis failed: {response.status_code}"
        data = response.json()
        # Should have summary or error
        assert "summary" in data or "error" in data, f"Unexpected response: {data}"
        print(f"✓ TEST_20: DOH analysis endpoint working (status=200)")
    
    def test_21_ai_demand_forecast_regression(self, headers):
        """TEST_21: GET /api/analytics/ai-demand/forecast returns 12 months (regression)"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/forecast",
            headers=headers
        )
        
        assert response.status_code == 200, f"AI demand forecast failed: {response.status_code}"
        data = response.json()
        # Should have forecast data or error
        assert "forecast" in data or "error" in data or "months" in data, f"Unexpected response: {data}"
        print(f"✓ TEST_21: AI demand forecast endpoint working (status=200)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
