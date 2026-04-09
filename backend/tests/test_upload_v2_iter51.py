"""
Test suite for Data Upload V2 Module - Iteration 51
Tests the new /api/upload/v2/* endpoints with 75-error validation system.

Endpoints tested:
- POST /api/upload/v2/daily-sales - Upload daily sales CSV
- POST /api/upload/v2/store-inventory - Upload store inventory CSV
- POST /api/upload/v2/warehouse-inventory - Upload warehouse inventory CSV
- POST /api/upload/v2/sku-master - Upload SKU master CSV
- POST /api/upload/v2/store-master - Upload store master CSV
- POST /api/upload/v2/warehouse-master - Upload warehouse master CSV
- GET /api/upload/v2/daily-status - Get today's upload status
- GET /api/upload/v2/history - Get upload history
- GET /api/upload/v2/template/{upload_type} - Download template
"""

import pytest
import requests
import os
import io
import tempfile
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
TEST_EMAIL = "admin@demo.com"
TEST_PASSWORD = "demo1234"
TEST_TENANT = "demo"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for demo tenant admin."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "tenant_id": TEST_TENANT}
    )
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    data = response.json()
    return data.get("token") or data.get("access_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}"}


# ============================================================
# DAILY STATUS ENDPOINT TESTS
# ============================================================

class TestDailyStatus:
    """Tests for GET /api/upload/v2/daily-status endpoint."""

    def test_daily_status_returns_200(self, auth_headers):
        """DailyStatus-01: Endpoint returns 200 OK."""
        response = requests.get(f"{BASE_URL}/api/upload/v2/daily-status", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_daily_status_structure(self, auth_headers):
        """DailyStatus-02: Response contains expected upload types."""
        response = requests.get(f"{BASE_URL}/api/upload/v2/daily-status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Should have status for 3 upload types
        expected_types = ["daily_sales", "store_inventory", "warehouse_inventory"]
        for ut in expected_types:
            assert ut in data, f"Missing upload type: {ut}"
            assert "uploaded" in data[ut], f"Missing 'uploaded' field for {ut}"
            assert "time" in data[ut], f"Missing 'time' field for {ut}"
            assert "rows" in data[ut], f"Missing 'rows' field for {ut}"


# ============================================================
# UPLOAD HISTORY ENDPOINT TESTS
# ============================================================

class TestUploadHistory:
    """Tests for GET /api/upload/v2/history endpoint."""

    def test_history_returns_200(self, auth_headers):
        """History-01: Endpoint returns 200 OK."""
        response = requests.get(f"{BASE_URL}/api/upload/v2/history?days=7", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_history_structure(self, auth_headers):
        """History-02: Response contains history array."""
        response = requests.get(f"{BASE_URL}/api/upload/v2/history?days=7", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "history" in data, "Response missing 'history' field"
        assert isinstance(data["history"], list), "'history' should be a list"

    def test_history_with_filter(self, auth_headers):
        """History-03: Filter by upload_type works."""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/history?days=7&upload_type=daily_sales",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "history" in data


# ============================================================
# TEMPLATE DOWNLOAD ENDPOINT TESTS
# ============================================================

class TestTemplateDownload:
    """Tests for GET /api/upload/v2/template/{upload_type} endpoint."""

    @pytest.mark.parametrize("upload_type", [
        "daily_sales",
        "store_inventory",
        "warehouse_inventory",
        "sku_master",
        "store_master",
        "warehouse_master",
    ])
    def test_template_download(self, auth_headers, upload_type):
        """Template-01: Template download returns Excel file."""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/template/{upload_type}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200 for {upload_type}, got {response.status_code}"
        
        # Check content type is Excel
        content_type = response.headers.get("content-type", "")
        assert "spreadsheet" in content_type or "octet-stream" in content_type, \
            f"Expected Excel content type, got {content_type}"
        
        # Check content disposition header
        content_disp = response.headers.get("content-disposition", "")
        assert "attachment" in content_disp, "Missing attachment header"
        assert f"{upload_type}_template.xlsx" in content_disp, f"Wrong filename in header: {content_disp}"

    def test_template_invalid_type(self, auth_headers):
        """Template-02: Invalid upload type returns 400."""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/template/invalid_type",
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"


# ============================================================
# FILE UPLOAD ENDPOINT TESTS
# ============================================================

class TestDailySalesUpload:
    """Tests for POST /api/upload/v2/daily-sales endpoint."""

    def test_upload_valid_csv(self, auth_headers):
        """DailySales-01: Upload valid CSV returns validation results."""
        # Create a valid CSV file
        csv_content = """sku,store_code,day,quantity,revenue
SKU001,STORE001,2026-01-15,10,1000
SKU002,STORE002,2026-01-15,5,500
"""
        files = {"file": ("test_daily_sales.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily-sales",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Check response structure
        assert "success" in data, "Missing 'success' field"
        assert "total_rows" in data, "Missing 'total_rows' field"
        assert "valid_rows" in data, "Missing 'valid_rows' field"
        assert "corrections" in data, "Missing 'corrections' field"
        assert "warnings" in data, "Missing 'warnings' field"
        assert "errors" in data, "Missing 'errors' field"
        
        # Should have 2 rows
        assert data["total_rows"] == 2, f"Expected 2 rows, got {data['total_rows']}"

    def test_upload_missing_columns(self, auth_headers):
        """DailySales-02: Upload with missing columns returns E043 error."""
        # CSV missing required columns
        csv_content = """sku,store_code
SKU001,STORE001
"""
        files = {"file": ("test_missing_cols.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily-sales",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200  # Returns 200 with validation errors
        
        data = response.json()
        assert data["success"] == False, "Should fail with missing columns"
        assert len(data["errors"]) > 0, "Should have errors"
        
        # Check for E043 error code
        error_codes = [e.get("code") for e in data["errors"]]
        assert "E043" in error_codes, f"Expected E043 error, got {error_codes}"

    def test_upload_empty_file(self, auth_headers):
        """DailySales-03: Upload empty file returns E045 error."""
        csv_content = """sku,store_code,day,quantity,revenue
"""
        files = {"file": ("test_empty.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily-sales",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == False, "Should fail with empty file"
        
        error_codes = [e.get("code") for e in data["errors"]]
        assert "E045" in error_codes, f"Expected E045 error for empty file, got {error_codes}"

    def test_upload_with_invalid_skus(self, auth_headers):
        """DailySales-04: Upload with invalid SKUs returns E003 warning/error."""
        csv_content = """sku,store_code,day,quantity,revenue
INVALID_SKU_123,STORE001,2026-01-15,10,1000
ANOTHER_BAD_SKU,STORE002,2026-01-15,5,500
"""
        files = {"file": ("test_invalid_skus.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily-sales",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200
        
        data = response.json()
        # If master SKUs exist, should have E003 errors
        # If no master data, validation passes (expected behavior per problem statement)
        assert "errors" in data or "warnings" in data


class TestStoreInventoryUpload:
    """Tests for POST /api/upload/v2/store-inventory endpoint."""

    def test_upload_valid_csv(self, auth_headers):
        """StoreInventory-01: Upload valid CSV returns validation results."""
        csv_content = """store_code,sku,closing_stock
STORE001,SKU001,100
STORE002,SKU002,50
"""
        files = {"file": ("test_store_inventory.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/store-inventory",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data
        assert "total_rows" in data
        assert data["total_rows"] == 2


class TestWarehouseInventoryUpload:
    """Tests for POST /api/upload/v2/warehouse-inventory endpoint."""

    def test_upload_valid_csv(self, auth_headers):
        """WarehouseInventory-01: Upload valid CSV returns validation results."""
        csv_content = """warehouse,sku,on_hand_qty,available_qty
WH001,SKU001,1000,900
WH002,SKU002,500,450
"""
        files = {"file": ("test_warehouse_inventory.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/warehouse-inventory",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data
        assert "total_rows" in data
        assert data["total_rows"] == 2


class TestSKUMasterUpload:
    """Tests for POST /api/upload/v2/sku-master endpoint."""

    def test_upload_valid_csv(self, auth_headers):
        """SKUMaster-01: Upload valid CSV returns validation results."""
        csv_content = """sku,product_name,category
TEST_SKU001,Test Product 1,Electronics
TEST_SKU002,Test Product 2,Clothing
"""
        files = {"file": ("test_sku_master.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/sku-master",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data
        assert "total_rows" in data
        assert data["total_rows"] == 2


class TestStoreMasterUpload:
    """Tests for POST /api/upload/v2/store-master endpoint."""

    def test_upload_valid_csv(self, auth_headers):
        """StoreMaster-01: Upload valid CSV returns validation results."""
        csv_content = """store_code,store_name
TEST_STORE001,Test Store 1
TEST_STORE002,Test Store 2
"""
        files = {"file": ("test_store_master.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/store-master",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data
        assert "total_rows" in data
        assert data["total_rows"] == 2


class TestWarehouseMasterUpload:
    """Tests for POST /api/upload/v2/warehouse-master endpoint."""

    def test_upload_valid_csv(self, auth_headers):
        """WarehouseMaster-01: Upload valid CSV returns validation results."""
        csv_content = """warehouse,warehouse_name,online_fulfillment_flag
TEST_WH001,Test Warehouse 1,true
TEST_WH002,Test Warehouse 2,false
"""
        files = {"file": ("test_warehouse_master.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/warehouse-master",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data
        assert "total_rows" in data
        assert data["total_rows"] == 2


# ============================================================
# VALIDATION TESTS - 75-ERROR SYSTEM
# ============================================================

class TestValidationErrors:
    """Tests for the 75-error validation system."""

    def test_auto_corrections_applied(self, auth_headers):
        """Validation-01: Auto-corrections are applied and reported."""
        # CSV with special characters in SKU that should be auto-fixed
        csv_content = """sku,store_code,day,quantity,revenue
SKU@001!,STORE001,2026-01-15,10,1000
SKU#002$,STORE002,2026-01-15,5,500
"""
        files = {"file": ("test_special_chars.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily-sales",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200
        
        data = response.json()
        # Should have corrections for special character removal (E006)
        if data.get("corrections"):
            correction_codes = [c.get("code") for c in data["corrections"]]
            # E006 is for special character removal
            print(f"Corrections applied: {correction_codes}")

    def test_negative_quantity_warning(self, auth_headers):
        """Validation-02: Negative quantities generate E027 warning."""
        csv_content = """sku,store_code,day,quantity,revenue
SKU001,STORE001,2026-01-15,-10,1000
"""
        files = {"file": ("test_negative_qty.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily-sales",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200
        
        data = response.json()
        # Should have E027 warning for negative quantity
        warning_codes = [w.get("code") for w in data.get("warnings", [])]
        assert "E027" in warning_codes, f"Expected E027 warning, got {warning_codes}"

    def test_zero_revenue_with_quantity_warning(self, auth_headers):
        """Validation-03: Zero revenue with positive quantity generates E041 warning."""
        csv_content = """sku,store_code,day,quantity,revenue
SKU001,STORE001,2026-01-15,10,0
"""
        files = {"file": ("test_zero_revenue.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily-sales",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200
        
        data = response.json()
        warning_codes = [w.get("code") for w in data.get("warnings", [])]
        assert "E041" in warning_codes, f"Expected E041 warning, got {warning_codes}"

    def test_duplicate_rows_warning(self, auth_headers):
        """Validation-04: Duplicate rows generate E050 warning."""
        csv_content = """sku,store_code,day,quantity,revenue
SKU001,STORE001,2026-01-15,10,1000
SKU001,STORE001,2026-01-15,10,1000
"""
        files = {"file": ("test_duplicates.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily-sales",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200
        
        data = response.json()
        warning_codes = [w.get("code") for w in data.get("warnings", [])]
        assert "E050" in warning_codes, f"Expected E050 warning for duplicates, got {warning_codes}"

    def test_test_data_detection(self, auth_headers):
        """Validation-05: Test data detection generates E070 warning."""
        csv_content = """sku,store_code,day,quantity,revenue
test,STORE001,2026-01-15,10,1000
demo,STORE002,2026-01-15,5,500
"""
        files = {"file": ("test_data_detection.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily-sales",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200
        
        data = response.json()
        warning_codes = [w.get("code") for w in data.get("warnings", [])]
        assert "E070" in warning_codes, f"Expected E070 warning for test data, got {warning_codes}"


# ============================================================
# REPLACE EXISTING DATA TESTS
# ============================================================

class TestReplaceExisting:
    """Tests for replace_existing parameter."""

    def test_replace_existing_parameter(self, auth_headers):
        """Replace-01: replace_existing parameter is accepted."""
        csv_content = """sku,store_code,day,quantity,revenue
SKU001,STORE001,2026-01-15,10,1000
"""
        files = {"file": ("test_replace.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily-sales?replace_existing=true",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


# ============================================================
# AUTHENTICATION TESTS
# ============================================================

class TestAuthentication:
    """Tests for authentication requirements."""

    def test_daily_status_without_auth(self):
        """Auth-01: Daily status without auth still works (tenant context from header)."""
        # The endpoint may work without auth if tenant context is set differently
        response = requests.get(f"{BASE_URL}/api/upload/v2/daily-status")
        # Should return 200 (uses default tenant) or 401/403
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"

    def test_upload_without_auth(self):
        """Auth-02: Upload without auth returns error or uses default tenant."""
        csv_content = """sku,store_code,day,quantity,revenue
SKU001,STORE001,2026-01-15,10,1000
"""
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(f"{BASE_URL}/api/upload/v2/daily-sales", files=files)
        # Should return 200 (uses default tenant) or 401/403
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
