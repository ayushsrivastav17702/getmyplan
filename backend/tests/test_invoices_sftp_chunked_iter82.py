"""
Iteration 82: Invoice Generation, SFTP Schedule, and Chunked Upload Tests
Tests for P2 Invoice Generation, P3 SFTP Auto-Schedule, P3 Chunked Uploads
"""
import pytest
import requests
import os
import io
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN = {"email": "admin@demo.com", "password": "demo1234"}
TENANT_ADMIN = {"email": "ayush.srivastav@increff.com", "password": "Ayush@114988"}


@pytest.fixture(scope="module")
def super_admin_token():
    """Get auth token for super admin (demo tenant - Professional plan)"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN)
    if resp.status_code == 200:
        return resp.json().get("access_token")
    pytest.skip(f"Super admin login failed: {resp.status_code}")


@pytest.fixture(scope="module")
def tenant_admin_token():
    """Get auth token for tenant admin (increff tenant - Trial plan)"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json=TENANT_ADMIN)
    if resp.status_code == 200:
        return resp.json().get("access_token")
    pytest.skip(f"Tenant admin login failed: {resp.status_code}")


@pytest.fixture
def super_admin_client(super_admin_token):
    """Session with super admin auth"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {super_admin_token}"
    })
    return session


@pytest.fixture
def tenant_admin_client(tenant_admin_token):
    """Session with tenant admin auth"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tenant_admin_token}"
    })
    return session


# ============================================================================
# P2 INVOICE GENERATION TESTS
# ============================================================================

class TestInvoiceAuth:
    """Test invoice endpoints require authentication"""
    
    def test_01_list_invoices_requires_auth(self):
        """GET /api/invoices requires auth"""
        resp = requests.get(f"{BASE_URL}/api/invoices")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("TEST_01 PASS: List invoices requires auth")
    
    def test_02_generate_invoice_requires_auth(self):
        """POST /api/invoices/generate requires auth"""
        resp = requests.post(f"{BASE_URL}/api/invoices/generate", json={})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("TEST_02 PASS: Generate invoice requires auth")
    
    def test_03_get_invoice_requires_auth(self):
        """GET /api/invoices/{id} requires auth"""
        resp = requests.get(f"{BASE_URL}/api/invoices/507f1f77bcf86cd799439011")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("TEST_03 PASS: Get invoice requires auth")
    
    def test_04_update_status_requires_auth(self):
        """PUT /api/invoices/{id}/status requires auth"""
        resp = requests.put(f"{BASE_URL}/api/invoices/507f1f77bcf86cd799439011/status", json={"status": "paid"})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("TEST_04 PASS: Update status requires auth")
    
    def test_05_download_requires_auth(self):
        """GET /api/invoices/{id}/download requires auth"""
        resp = requests.get(f"{BASE_URL}/api/invoices/507f1f77bcf86cd799439011/download")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("TEST_05 PASS: Download invoice requires auth")
    
    def test_06_delete_requires_auth(self):
        """DELETE /api/invoices/{id} requires auth"""
        resp = requests.delete(f"{BASE_URL}/api/invoices/507f1f77bcf86cd799439011")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("TEST_06 PASS: Delete invoice requires auth")


class TestInvoiceGeneration:
    """Test invoice generation and listing"""
    
    def test_07_list_invoices_success(self, super_admin_client):
        """GET /api/invoices returns list"""
        resp = super_admin_client.get(f"{BASE_URL}/api/invoices")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "invoices" in data, "Response should have 'invoices' key"
        print(f"TEST_07 PASS: List invoices returns {len(data['invoices'])} invoices")
    
    def test_08_generate_invoice_success(self, super_admin_client):
        """POST /api/invoices/generate creates invoice with plan pricing"""
        resp = super_admin_client.post(f"{BASE_URL}/api/invoices/generate", json={})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Verify response structure
        assert "invoice_id" in data, "Response should have invoice_id"
        assert "invoice_number" in data, "Response should have invoice_number"
        assert "total" in data, "Response should have total"
        assert "currency" in data, "Response should have currency"
        assert "status" in data, "Response should have status"
        
        # Verify invoice number format: GMP-YYYYMM-TENANT-NNNN
        inv_num = data["invoice_number"]
        assert inv_num.startswith("GMP-"), f"Invoice number should start with GMP-: {inv_num}"
        
        print(f"TEST_08 PASS: Generated invoice {inv_num}, total={data['total']} {data['currency']}")
        return data["invoice_id"]
    
    def test_09_generate_invoice_with_custom_amount(self, super_admin_client):
        """POST /api/invoices/generate with custom amount"""
        resp = super_admin_client.post(f"{BASE_URL}/api/invoices/generate", json={
            "description": "Custom test invoice",
            "custom_amount": 50000
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        
        # Custom amount should be 50000 + 18% GST = 59000
        expected_total = 50000 * 1.18
        assert abs(data["total"] - expected_total) < 1, f"Expected total ~{expected_total}, got {data['total']}"
        print(f"TEST_09 PASS: Custom amount invoice total={data['total']}")
    
    def test_10_get_invoice_detail(self, super_admin_client):
        """GET /api/invoices/{id} returns full detail with usage metrics"""
        # First list invoices to get an ID
        list_resp = super_admin_client.get(f"{BASE_URL}/api/invoices")
        invoices = list_resp.json().get("invoices", [])
        if not invoices:
            pytest.skip("No invoices to test detail")
        
        invoice_id = invoices[0]["invoice_id"]
        resp = super_admin_client.get(f"{BASE_URL}/api/invoices/{invoice_id}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        
        # Verify full detail structure
        assert "invoice_number" in data
        assert "company_name" in data
        assert "plan_type" in data
        assert "plan_label" in data
        assert "billing_period" in data
        assert "subtotal" in data
        assert "tax_rate" in data
        assert "tax_amount" in data
        assert "total" in data
        assert "usage_metrics" in data
        assert "plan_limits" in data
        
        # Verify usage metrics structure
        usage = data["usage_metrics"]
        assert "active_users" in usage
        assert "total_uploads" in usage
        assert "sales_records" in usage
        
        print(f"TEST_10 PASS: Invoice detail has usage_metrics with {len(usage)} fields")
    
    def test_11_invoice_has_8_usage_metrics(self, super_admin_client):
        """Verify invoice has all 8 usage metrics"""
        list_resp = super_admin_client.get(f"{BASE_URL}/api/invoices")
        invoices = list_resp.json().get("invoices", [])
        if not invoices:
            pytest.skip("No invoices to test")
        
        invoice_id = invoices[0]["invoice_id"]
        resp = super_admin_client.get(f"{BASE_URL}/api/invoices/{invoice_id}")
        usage = resp.json().get("usage_metrics", {})
        
        expected_metrics = [
            "active_users", "total_uploads", "sales_records", "style_master_records",
            "store_count", "forecast_snapshots", "buy_plans_generated", "estimated_storage_mb"
        ]
        for metric in expected_metrics:
            assert metric in usage, f"Missing usage metric: {metric}"
        
        print(f"TEST_11 PASS: All 8 usage metrics present")
    
    def test_12_update_invoice_status_to_paid(self, super_admin_client):
        """PUT /api/invoices/{id}/status updates to paid"""
        # Generate a new invoice to update
        gen_resp = super_admin_client.post(f"{BASE_URL}/api/invoices/generate", json={
            "description": "Test invoice for status update"
        })
        invoice_id = gen_resp.json()["invoice_id"]
        
        # Update to paid
        resp = super_admin_client.put(f"{BASE_URL}/api/invoices/{invoice_id}/status", json={
            "status": "paid",
            "payment_reference": "TEST-PAY-001"
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data["success"] is True
        assert data["status"] == "paid"
        
        # Verify status persisted
        get_resp = super_admin_client.get(f"{BASE_URL}/api/invoices/{invoice_id}")
        assert get_resp.json()["status"] == "paid"
        
        print("TEST_12 PASS: Invoice status updated to paid")
    
    def test_13_update_invoice_status_to_cancelled(self, super_admin_client):
        """PUT /api/invoices/{id}/status updates to cancelled"""
        gen_resp = super_admin_client.post(f"{BASE_URL}/api/invoices/generate", json={})
        invoice_id = gen_resp.json()["invoice_id"]
        
        resp = super_admin_client.put(f"{BASE_URL}/api/invoices/{invoice_id}/status", json={
            "status": "cancelled"
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"
        print("TEST_13 PASS: Invoice status updated to cancelled")
    
    def test_14_update_invoice_status_to_overdue(self, super_admin_client):
        """PUT /api/invoices/{id}/status updates to overdue"""
        gen_resp = super_admin_client.post(f"{BASE_URL}/api/invoices/generate", json={})
        invoice_id = gen_resp.json()["invoice_id"]
        
        resp = super_admin_client.put(f"{BASE_URL}/api/invoices/{invoice_id}/status", json={
            "status": "overdue"
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "overdue"
        print("TEST_14 PASS: Invoice status updated to overdue")
    
    def test_15_download_invoice_html(self, super_admin_client):
        """GET /api/invoices/{id}/download returns styled HTML"""
        list_resp = super_admin_client.get(f"{BASE_URL}/api/invoices")
        invoices = list_resp.json().get("invoices", [])
        if not invoices:
            pytest.skip("No invoices to download")
        
        invoice_id = invoices[0]["invoice_id"]
        resp = super_admin_client.get(f"{BASE_URL}/api/invoices/{invoice_id}/download")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        # Verify it's HTML
        content_type = resp.headers.get("content-type", "")
        assert "text/html" in content_type, f"Expected text/html, got {content_type}"
        
        # Verify HTML content
        html = resp.text
        assert "<!DOCTYPE html>" in html
        assert "Invoice" in html
        assert "GetMyPlan" in html
        assert "Usage Metrics" in html
        
        print("TEST_15 PASS: Download returns styled HTML invoice")
    
    def test_16_delete_invoice_admin_only(self, super_admin_client):
        """DELETE /api/invoices/{id} works for admin"""
        # Generate invoice to delete
        gen_resp = super_admin_client.post(f"{BASE_URL}/api/invoices/generate", json={
            "description": "Invoice to delete"
        })
        invoice_id = gen_resp.json()["invoice_id"]
        
        # Delete
        resp = super_admin_client.delete(f"{BASE_URL}/api/invoices/{invoice_id}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert resp.json()["success"] is True
        
        # Verify deleted
        get_resp = super_admin_client.get(f"{BASE_URL}/api/invoices/{invoice_id}")
        assert get_resp.status_code == 404
        
        print("TEST_16 PASS: Admin can delete invoice")
    
    def test_17_invalid_invoice_id_returns_400(self, super_admin_client):
        """Invalid invoice ID returns 400"""
        resp = super_admin_client.get(f"{BASE_URL}/api/invoices/invalid-id")
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        print("TEST_17 PASS: Invalid invoice ID returns 400")
    
    def test_18_nonexistent_invoice_returns_404(self, super_admin_client):
        """Nonexistent invoice returns 404"""
        resp = super_admin_client.get(f"{BASE_URL}/api/invoices/507f1f77bcf86cd799439011")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("TEST_18 PASS: Nonexistent invoice returns 404")


class TestInvoiceTenantIsolation:
    """Test invoice tenant isolation"""
    
    def test_19_tenant_admin_can_generate_invoice(self, tenant_admin_client):
        """Tenant admin can generate invoice for their tenant"""
        resp = tenant_admin_client.post(f"{BASE_URL}/api/invoices/generate", json={})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        
        # Trial plan should have 0 amount
        # Note: Trial plan pricing is 0 INR
        print(f"TEST_19 PASS: Tenant admin generated invoice, total={data['total']}")
    
    def test_20_tenant_admin_sees_only_own_invoices(self, tenant_admin_client, super_admin_client):
        """Tenant admin only sees their own tenant's invoices"""
        # Get tenant admin invoices
        tenant_resp = tenant_admin_client.get(f"{BASE_URL}/api/invoices")
        tenant_invoices = tenant_resp.json().get("invoices", [])
        
        # Get super admin invoices
        admin_resp = super_admin_client.get(f"{BASE_URL}/api/invoices")
        admin_invoices = admin_resp.json().get("invoices", [])
        
        # They should be different (different tenants)
        tenant_ids = {inv["invoice_id"] for inv in tenant_invoices}
        admin_ids = {inv["invoice_id"] for inv in admin_invoices}
        
        # No overlap expected
        overlap = tenant_ids & admin_ids
        assert len(overlap) == 0, f"Tenant isolation violated: {overlap}"
        
        print(f"TEST_20 PASS: Tenant isolation verified ({len(tenant_invoices)} vs {len(admin_invoices)} invoices)")


# ============================================================================
# P3 SFTP SCHEDULE TESTS
# ============================================================================

class TestSFTPScheduleAuth:
    """Test SFTP schedule endpoints require authentication"""
    
    def test_21_get_schedule_requires_auth(self):
        """GET /api/data/sftp-schedule requires auth"""
        resp = requests.get(f"{BASE_URL}/api/data/sftp-schedule")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("TEST_21 PASS: Get SFTP schedule requires auth")
    
    def test_22_update_schedule_requires_auth(self):
        """PUT /api/data/sftp-schedule requires auth"""
        resp = requests.put(f"{BASE_URL}/api/data/sftp-schedule", json={"enabled": True})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("TEST_22 PASS: Update SFTP schedule requires auth")
    
    def test_23_history_requires_auth(self):
        """GET /api/data/sftp-schedule/history requires auth"""
        resp = requests.get(f"{BASE_URL}/api/data/sftp-schedule/history")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("TEST_23 PASS: SFTP schedule history requires auth")


class TestSFTPSchedule:
    """Test SFTP schedule CRUD"""
    
    def test_24_get_schedule_returns_config(self, super_admin_client):
        """GET /api/data/sftp-schedule returns config"""
        resp = super_admin_client.get(f"{BASE_URL}/api/data/sftp-schedule")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        
        # Verify config structure
        assert "enabled" in data
        assert "frequency" in data
        assert "hour" in data
        assert "file_types" in data
        assert "destination_path" in data
        
        print(f"TEST_24 PASS: SFTP schedule config: enabled={data['enabled']}, freq={data['frequency']}")
    
    def test_25_update_schedule_success(self, super_admin_client):
        """PUT /api/data/sftp-schedule updates config"""
        resp = super_admin_client.put(f"{BASE_URL}/api/data/sftp-schedule", json={
            "enabled": True,
            "frequency": "weekly",
            "hour": 3,
            "file_types": ["daily_sales", "store_inventory", "warehouse_inventory"],
            "destination_path": "/exports/weekly"
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data["success"] is True
        
        # Verify config updated
        config = data["config"]
        assert config["enabled"] is True
        assert config["frequency"] == "weekly"
        assert config["hour"] == 3
        assert "daily_sales" in config["file_types"]
        
        print("TEST_25 PASS: SFTP schedule updated successfully")
    
    def test_26_schedule_persists(self, super_admin_client):
        """Verify schedule config persists"""
        # Update
        super_admin_client.put(f"{BASE_URL}/api/data/sftp-schedule", json={
            "enabled": False,
            "frequency": "monthly",
            "hour": 5
        })
        
        # Get and verify
        resp = super_admin_client.get(f"{BASE_URL}/api/data/sftp-schedule")
        data = resp.json()
        assert data["enabled"] is False
        assert data["frequency"] == "monthly"
        assert data["hour"] == 5
        
        print("TEST_26 PASS: SFTP schedule config persists")
    
    def test_27_schedule_history_returns_runs(self, super_admin_client):
        """GET /api/data/sftp-schedule/history returns run history"""
        resp = super_admin_client.get(f"{BASE_URL}/api/data/sftp-schedule/history")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "runs" in data
        print(f"TEST_27 PASS: SFTP schedule history returns {len(data['runs'])} runs")


# ============================================================================
# P3 CHUNKED UPLOAD TESTS
# ============================================================================

class TestChunkedUploadAuth:
    """Test chunked upload endpoints require authentication"""
    
    def test_28_init_upload_requires_auth(self):
        """POST /api/data/upload/init requires auth"""
        resp = requests.post(f"{BASE_URL}/api/data/upload/init", data={
            "file_name": "test.csv",
            "file_type": "daily_sales",
            "file_size": 1000,
            "total_chunks": 1
        })
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("TEST_28 PASS: Init upload requires auth")
    
    def test_29_upload_chunk_requires_auth(self):
        """POST /api/data/upload/chunk/{id} requires auth"""
        resp = requests.post(f"{BASE_URL}/api/data/upload/chunk/test-id", data={"chunk_index": 0})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("TEST_29 PASS: Upload chunk requires auth")
    
    def test_30_complete_upload_requires_auth(self):
        """POST /api/data/upload/complete/{id} requires auth"""
        resp = requests.post(f"{BASE_URL}/api/data/upload/complete/test-id")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("TEST_30 PASS: Complete upload requires auth")
    
    def test_31_status_requires_auth(self):
        """GET /api/data/upload/status/{id} requires auth"""
        resp = requests.get(f"{BASE_URL}/api/data/upload/status/test-id")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("TEST_31 PASS: Upload status requires auth")
    
    def test_32_cancel_requires_auth(self):
        """DELETE /api/data/upload/{id} requires auth"""
        resp = requests.delete(f"{BASE_URL}/api/data/upload/test-id")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("TEST_32 PASS: Cancel upload requires auth")


class TestChunkedUpload:
    """Test chunked upload flow"""
    
    def test_33_init_upload_success(self, super_admin_client):
        """POST /api/data/upload/init initializes session"""
        resp = requests.post(
            f"{BASE_URL}/api/data/upload/init",
            headers={"Authorization": super_admin_client.headers["Authorization"]},
            data={
                "file_name": "test_sales.csv",
                "file_type": "daily_sales",
                "file_size": 5000,
                "total_chunks": 3
            }
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert "upload_id" in data
        assert data["total_chunks"] == 3
        assert data["status"] == "ready"
        
        print(f"TEST_33 PASS: Upload initialized with ID {data['upload_id']}")
        return data["upload_id"]
    
    def test_34_upload_chunk_success(self, super_admin_client):
        """POST /api/data/upload/chunk/{id} uploads chunk"""
        # Init upload
        init_resp = requests.post(
            f"{BASE_URL}/api/data/upload/init",
            headers={"Authorization": super_admin_client.headers["Authorization"]},
            data={
                "file_name": "chunk_test.csv",
                "file_type": "daily_sales",
                "file_size": 3000,
                "total_chunks": 3
            }
        )
        upload_id = init_resp.json()["upload_id"]
        
        # Upload first chunk
        chunk_data = b"store_id,date,sku,qty\n" + b"S001,2024-01-01,SKU001,10\n" * 50
        resp = requests.post(
            f"{BASE_URL}/api/data/upload/chunk/{upload_id}",
            headers={"Authorization": super_admin_client.headers["Authorization"]},
            data={"chunk_index": 0},
            files={"chunk": ("chunk_0", io.BytesIO(chunk_data), "application/octet-stream")}
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert data["chunk_index"] == 0
        assert data["chunks_received"] == 1
        assert data["total_chunks"] == 3
        
        print(f"TEST_34 PASS: Chunk 0 uploaded, progress={data['progress']}%")
        return upload_id
    
    def test_35_upload_all_chunks_and_complete(self, super_admin_client):
        """Full chunked upload flow: init -> chunks -> complete"""
        # Init
        init_resp = requests.post(
            f"{BASE_URL}/api/data/upload/init",
            headers={"Authorization": super_admin_client.headers["Authorization"]},
            data={
                "file_name": "full_test.csv",
                "file_type": "daily_sales",
                "file_size": 3000,
                "total_chunks": 2
            }
        )
        upload_id = init_resp.json()["upload_id"]
        
        # Upload chunks
        for i in range(2):
            chunk_data = f"chunk_{i}_data\n".encode() * 100
            resp = requests.post(
                f"{BASE_URL}/api/data/upload/chunk/{upload_id}",
                headers={"Authorization": super_admin_client.headers["Authorization"]},
                data={"chunk_index": i},
                files={"chunk": (f"chunk_{i}", io.BytesIO(chunk_data), "application/octet-stream")}
            )
            assert resp.status_code == 200, f"Chunk {i} failed: {resp.text}"
        
        # Complete
        complete_resp = requests.post(
            f"{BASE_URL}/api/data/upload/complete/{upload_id}",
            headers={"Authorization": super_admin_client.headers["Authorization"]}
        )
        assert complete_resp.status_code == 200, f"Complete failed: {complete_resp.text}"
        data = complete_resp.json()
        
        assert data["status"] == "complete"
        assert data["file_name"] == "full_test.csv"
        assert "file_size_mb" in data
        
        print(f"TEST_35 PASS: Full upload complete, size={data['file_size_mb']}MB")
    
    def test_36_get_upload_status(self, super_admin_client):
        """GET /api/data/upload/status/{id} returns status"""
        # Init upload
        init_resp = requests.post(
            f"{BASE_URL}/api/data/upload/init",
            headers={"Authorization": super_admin_client.headers["Authorization"]},
            data={
                "file_name": "status_test.csv",
                "file_type": "daily_sales",
                "file_size": 1000,
                "total_chunks": 1
            }
        )
        upload_id = init_resp.json()["upload_id"]
        
        # Get status
        resp = super_admin_client.get(f"{BASE_URL}/api/data/upload/status/{upload_id}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        
        assert data["status"] == "uploading"
        assert data["progress"] == 0
        assert data["chunks_received"] == 0
        
        print(f"TEST_36 PASS: Upload status: {data['status']}")
    
    def test_37_cancel_upload(self, super_admin_client):
        """DELETE /api/data/upload/{id} cancels upload"""
        # Init upload
        init_resp = requests.post(
            f"{BASE_URL}/api/data/upload/init",
            headers={"Authorization": super_admin_client.headers["Authorization"]},
            data={
                "file_name": "cancel_test.csv",
                "file_type": "daily_sales",
                "file_size": 1000,
                "total_chunks": 1
            }
        )
        upload_id = init_resp.json()["upload_id"]
        
        # Cancel
        resp = super_admin_client.delete(f"{BASE_URL}/api/data/upload/{upload_id}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert resp.json()["success"] is True
        
        # Verify cancelled - status should return 404
        status_resp = super_admin_client.get(f"{BASE_URL}/api/data/upload/status/{upload_id}")
        assert status_resp.status_code == 404
        
        print("TEST_37 PASS: Upload cancelled successfully")
    
    def test_38_complete_with_missing_chunks_fails(self, super_admin_client):
        """Complete fails if chunks are missing"""
        # Init with 3 chunks
        init_resp = requests.post(
            f"{BASE_URL}/api/data/upload/init",
            headers={"Authorization": super_admin_client.headers["Authorization"]},
            data={
                "file_name": "missing_chunks.csv",
                "file_type": "daily_sales",
                "file_size": 3000,
                "total_chunks": 3
            }
        )
        upload_id = init_resp.json()["upload_id"]
        
        # Upload only chunk 0
        chunk_data = b"test data"
        requests.post(
            f"{BASE_URL}/api/data/upload/chunk/{upload_id}",
            headers={"Authorization": super_admin_client.headers["Authorization"]},
            data={"chunk_index": 0},
            files={"chunk": ("chunk_0", io.BytesIO(chunk_data), "application/octet-stream")}
        )
        
        # Try to complete - should fail
        complete_resp = requests.post(
            f"{BASE_URL}/api/data/upload/complete/{upload_id}",
            headers={"Authorization": super_admin_client.headers["Authorization"]}
        )
        assert complete_resp.status_code == 400, f"Expected 400, got {complete_resp.status_code}"
        assert "Missing chunks" in complete_resp.json().get("detail", "")
        
        print("TEST_38 PASS: Complete fails with missing chunks")
    
    def test_39_invalid_upload_id_returns_404(self, super_admin_client):
        """Invalid upload ID returns 404"""
        resp = super_admin_client.get(f"{BASE_URL}/api/data/upload/status/nonexistent-id")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("TEST_39 PASS: Invalid upload ID returns 404")
    
    def test_40_invalid_chunk_index_returns_400(self, super_admin_client):
        """Invalid chunk index returns 400"""
        # Init upload
        init_resp = requests.post(
            f"{BASE_URL}/api/data/upload/init",
            headers={"Authorization": super_admin_client.headers["Authorization"]},
            data={
                "file_name": "invalid_chunk.csv",
                "file_type": "daily_sales",
                "file_size": 1000,
                "total_chunks": 2
            }
        )
        upload_id = init_resp.json()["upload_id"]
        
        # Try to upload chunk with invalid index
        chunk_data = b"test data"
        resp = requests.post(
            f"{BASE_URL}/api/data/upload/chunk/{upload_id}",
            headers={"Authorization": super_admin_client.headers["Authorization"]},
            data={"chunk_index": 5},  # Invalid - only 0 and 1 are valid
            files={"chunk": ("chunk_5", io.BytesIO(chunk_data), "application/octet-stream")}
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        
        print("TEST_40 PASS: Invalid chunk index returns 400")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
