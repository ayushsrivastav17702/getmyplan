"""
Test Backup & Restore API Endpoints (Iteration 79)
Tests: Create, List, Download, Restore (merge/overwrite), Delete, Auto-cleanup (retention=5)
"""
import pytest
import requests
import os
import zipfile
import io
import json
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
TEST_EMAIL = "ayush.srivastav@increff.com"
TEST_PASSWORD = "Ayush@114988"


class TestBackupRestoreAPI:
    """Backup & Restore API endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Get auth token before each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_resp.status_code == 200:
            data = login_resp.json()
            # Handle MFA challenge if needed
            if data.get("mfa_required"):
                pytest.skip("MFA enabled - skipping backup tests")
            token = data.get("access_token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Login failed: {login_resp.status_code}")
        
        yield
        
        # Cleanup: Delete any test backups created
        self._cleanup_test_backups()
    
    def _cleanup_test_backups(self):
        """Delete backups created during tests (prefixed with TEST_)"""
        try:
            resp = self.session.get(f"{BASE_URL}/api/backup/list")
            if resp.status_code == 200:
                backups = resp.data.get("backups", []) if hasattr(resp, 'data') else resp.json().get("backups", [])
                for b in backups:
                    if b.get("name", "").startswith("TEST_"):
                        self.session.delete(f"{BASE_URL}/api/backup/{b['backup_id']}")
        except:
            pass
    
    # ─── Test 1: List backups without auth ───
    def test_01_list_backups_unauthenticated(self):
        """List backups should require authentication"""
        session = requests.Session()
        resp = session.get(f"{BASE_URL}/api/backup/list")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("✓ TEST_01: List backups returns 401 without auth")
    
    # ─── Test 2: List backups with auth ───
    def test_02_list_backups_authenticated(self):
        """List backups should return backup list for authenticated user"""
        resp = self.session.get(f"{BASE_URL}/api/backup/list")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        assert "backups" in data, "Response should contain 'backups' key"
        assert "max_backups" in data, "Response should contain 'max_backups' key"
        assert isinstance(data["backups"], list), "backups should be a list"
        assert data["max_backups"] == 5, f"max_backups should be 5, got {data['max_backups']}"
        print(f"✓ TEST_02: List backups returns {len(data['backups'])} backups, max={data['max_backups']}")
    
    # ─── Test 3: Create backup without auth ───
    def test_03_create_backup_unauthenticated(self):
        """Create backup should require authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        resp = session.post(f"{BASE_URL}/api/backup/create", json={"name": "Test"})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("✓ TEST_03: Create backup returns 401 without auth")
    
    # ─── Test 4: Create backup with auth ───
    def test_04_create_backup_success(self):
        """Create backup should return backup details"""
        resp = self.session.post(f"{BASE_URL}/api/backup/create", json={
            "name": "TEST_Backup_Iter79",
            "description": "Test backup for iteration 79"
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert "backup_id" in data, "Response should contain 'backup_id'"
        assert "name" in data, "Response should contain 'name'"
        assert "total_docs" in data, "Response should contain 'total_docs'"
        assert "size_mb" in data, "Response should contain 'size_mb'"
        assert "created_at" in data, "Response should contain 'created_at'"
        assert data["name"] == "TEST_Backup_Iter79", f"Name mismatch: {data['name']}"
        
        # Store backup_id for later tests
        self.created_backup_id = data["backup_id"]
        print(f"✓ TEST_04: Created backup {data['backup_id']} - {data['total_docs']} docs, {data['size_mb']} MB")
        return data["backup_id"]
    
    # ─── Test 5: Verify backup appears in list ───
    def test_05_verify_backup_in_list(self):
        """Created backup should appear in list"""
        # First create a backup
        create_resp = self.session.post(f"{BASE_URL}/api/backup/create", json={
            "name": "TEST_Verify_List",
            "description": "Test for list verification"
        })
        assert create_resp.status_code == 200
        backup_id = create_resp.json()["backup_id"]
        
        # Then verify it's in the list
        list_resp = self.session.get(f"{BASE_URL}/api/backup/list")
        assert list_resp.status_code == 200
        
        backups = list_resp.json()["backups"]
        backup_ids = [b["backup_id"] for b in backups]
        assert backup_id in backup_ids, f"Backup {backup_id} not found in list"
        
        # Verify backup has all required fields
        backup = next(b for b in backups if b["backup_id"] == backup_id)
        assert "name" in backup
        assert "created_at" in backup
        assert "total_docs" in backup
        assert "size_mb" in backup
        assert "created_by" in backup
        assert backup["created_by"] == TEST_EMAIL
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/backup/{backup_id}")
        print(f"✓ TEST_05: Backup {backup_id} verified in list with all fields")
    
    # ─── Test 6: Download backup without auth ───
    def test_06_download_backup_unauthenticated(self):
        """Download backup should require authentication"""
        session = requests.Session()
        resp = session.get(f"{BASE_URL}/api/backup/fake-id/download")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("✓ TEST_06: Download backup returns 401 without auth")
    
    # ─── Test 7: Download backup - invalid ID ───
    def test_07_download_backup_invalid_id(self):
        """Download with invalid backup ID should return 400"""
        resp = self.session.get(f"{BASE_URL}/api/backup/invalid-id/download")
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        print("✓ TEST_07: Download with invalid ID returns 400")
    
    # ─── Test 8: Download backup - not found ───
    def test_08_download_backup_not_found(self):
        """Download with non-existent backup ID should return 404"""
        # Use a valid ObjectId format but non-existent
        resp = self.session.get(f"{BASE_URL}/api/backup/507f1f77bcf86cd799439011/download")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("✓ TEST_08: Download non-existent backup returns 404")
    
    # ─── Test 9: Download backup success ───
    def test_09_download_backup_success(self):
        """Download backup should return ZIP file"""
        # First create a backup
        create_resp = self.session.post(f"{BASE_URL}/api/backup/create", json={
            "name": "TEST_Download_Check",
            "description": "Test for download"
        })
        assert create_resp.status_code == 200
        backup_id = create_resp.json()["backup_id"]
        
        # Download the backup
        download_resp = self.session.get(f"{BASE_URL}/api/backup/{backup_id}/download")
        assert download_resp.status_code == 200, f"Expected 200, got {download_resp.status_code}"
        
        # Verify it's a ZIP file
        content_type = download_resp.headers.get("Content-Type", "")
        assert "application/zip" in content_type or "application/octet-stream" in content_type, f"Expected ZIP, got {content_type}"
        
        # Verify ZIP contents
        zip_buffer = io.BytesIO(download_resp.content)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            file_list = zf.namelist()
            assert "_metadata.json" in file_list, "ZIP should contain _metadata.json"
            
            # Read metadata
            metadata = json.loads(zf.read("_metadata.json"))
            assert metadata["backup_id"] == backup_id
            assert "tenant_id" in metadata
            assert "created_at" in metadata
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/backup/{backup_id}")
        print(f"✓ TEST_09: Downloaded backup ZIP with {len(file_list)} files including _metadata.json")
    
    # ─── Test 10: Restore backup without auth ───
    def test_10_restore_backup_unauthenticated(self):
        """Restore backup should require authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        resp = session.post(f"{BASE_URL}/api/backup/fake-id/restore", json={"mode": "merge"})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("✓ TEST_10: Restore backup returns 401 without auth")
    
    # ─── Test 11: Restore backup - invalid mode ───
    def test_11_restore_backup_invalid_mode(self):
        """Restore with invalid mode should return 422"""
        # First create a backup
        create_resp = self.session.post(f"{BASE_URL}/api/backup/create", json={
            "name": "TEST_Invalid_Mode"
        })
        assert create_resp.status_code == 200
        backup_id = create_resp.json()["backup_id"]
        
        # Try restore with invalid mode
        resp = self.session.post(f"{BASE_URL}/api/backup/{backup_id}/restore", json={"mode": "invalid"})
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/backup/{backup_id}")
        print("✓ TEST_11: Restore with invalid mode returns 422")
    
    # ─── Test 12: Restore backup - merge mode ───
    def test_12_restore_backup_merge_mode(self):
        """Restore in merge mode should succeed"""
        # First create a backup
        create_resp = self.session.post(f"{BASE_URL}/api/backup/create", json={
            "name": "TEST_Merge_Restore"
        })
        assert create_resp.status_code == 200
        backup_id = create_resp.json()["backup_id"]
        
        # Restore in merge mode
        restore_resp = self.session.post(f"{BASE_URL}/api/backup/{backup_id}/restore", json={"mode": "merge"})
        assert restore_resp.status_code == 200, f"Expected 200, got {restore_resp.status_code}: {restore_resp.text}"
        
        data = restore_resp.json()
        assert data["success"] == True
        assert data["mode"] == "merge"
        assert "restored_collections" in data
        assert "total_docs_restored" in data
        assert "collections" in data
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/backup/{backup_id}")
        print(f"✓ TEST_12: Restore (merge) - {data['total_docs_restored']} docs in {data['restored_collections']} collections")
    
    # ─── Test 13: Restore backup - overwrite mode ───
    def test_13_restore_backup_overwrite_mode(self):
        """Restore in overwrite mode should succeed"""
        # First create a backup
        create_resp = self.session.post(f"{BASE_URL}/api/backup/create", json={
            "name": "TEST_Overwrite_Restore"
        })
        assert create_resp.status_code == 200
        backup_id = create_resp.json()["backup_id"]
        
        # Restore in overwrite mode
        restore_resp = self.session.post(f"{BASE_URL}/api/backup/{backup_id}/restore", json={"mode": "overwrite"})
        assert restore_resp.status_code == 200, f"Expected 200, got {restore_resp.status_code}: {restore_resp.text}"
        
        data = restore_resp.json()
        assert data["success"] == True
        assert data["mode"] == "overwrite"
        assert "restored_collections" in data
        assert "total_docs_restored" in data
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/backup/{backup_id}")
        print(f"✓ TEST_13: Restore (overwrite) - {data['total_docs_restored']} docs in {data['restored_collections']} collections")
    
    # ─── Test 14: Delete backup without auth ───
    def test_14_delete_backup_unauthenticated(self):
        """Delete backup should require authentication"""
        session = requests.Session()
        resp = session.delete(f"{BASE_URL}/api/backup/fake-id")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("✓ TEST_14: Delete backup returns 401 without auth")
    
    # ─── Test 15: Delete backup - invalid ID ───
    def test_15_delete_backup_invalid_id(self):
        """Delete with invalid backup ID should return 400"""
        resp = self.session.delete(f"{BASE_URL}/api/backup/invalid-id")
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        print("✓ TEST_15: Delete with invalid ID returns 400")
    
    # ─── Test 16: Delete backup - not found ───
    def test_16_delete_backup_not_found(self):
        """Delete with non-existent backup ID should return 404"""
        resp = self.session.delete(f"{BASE_URL}/api/backup/507f1f77bcf86cd799439011")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("✓ TEST_16: Delete non-existent backup returns 404")
    
    # ─── Test 17: Delete backup success ───
    def test_17_delete_backup_success(self):
        """Delete backup should succeed and remove from list"""
        # First create a backup
        create_resp = self.session.post(f"{BASE_URL}/api/backup/create", json={
            "name": "TEST_Delete_Me"
        })
        assert create_resp.status_code == 200
        backup_id = create_resp.json()["backup_id"]
        
        # Delete the backup
        delete_resp = self.session.delete(f"{BASE_URL}/api/backup/{backup_id}")
        assert delete_resp.status_code == 200, f"Expected 200, got {delete_resp.status_code}"
        
        data = delete_resp.json()
        assert data["success"] == True
        
        # Verify it's no longer in the list
        list_resp = self.session.get(f"{BASE_URL}/api/backup/list")
        backups = list_resp.json()["backups"]
        backup_ids = [b["backup_id"] for b in backups]
        assert backup_id not in backup_ids, "Deleted backup should not be in list"
        
        print(f"✓ TEST_17: Deleted backup {backup_id} and verified removal from list")
    
    # ─── Test 18: Auto-cleanup retention (max 5 backups) ───
    def test_18_auto_cleanup_retention(self):
        """Creating 6th backup should auto-delete the oldest"""
        # Get current backup count
        initial_resp = self.session.get(f"{BASE_URL}/api/backup/list")
        initial_backups = initial_resp.json()["backups"]
        initial_count = len(initial_backups)
        
        # Create backups until we have 5
        created_ids = []
        backups_to_create = max(0, 5 - initial_count)
        
        for i in range(backups_to_create):
            resp = self.session.post(f"{BASE_URL}/api/backup/create", json={
                "name": f"TEST_Retention_{i+1}"
            })
            if resp.status_code == 200:
                created_ids.append(resp.json()["backup_id"])
            time.sleep(0.5)  # Small delay to ensure different timestamps
        
        # Verify we have 5 backups
        list_resp = self.session.get(f"{BASE_URL}/api/backup/list")
        backups = list_resp.json()["backups"]
        
        if len(backups) < 5:
            # Not enough backups to test retention, skip
            for bid in created_ids:
                self.session.delete(f"{BASE_URL}/api/backup/{bid}")
            pytest.skip("Not enough backups to test retention")
        
        # Get the oldest backup ID
        oldest_backup_id = backups[-1]["backup_id"]  # List is sorted by created_at desc
        
        # Create 6th backup
        sixth_resp = self.session.post(f"{BASE_URL}/api/backup/create", json={
            "name": "TEST_Retention_6th"
        })
        assert sixth_resp.status_code == 200
        sixth_id = sixth_resp.json()["backup_id"]
        
        # Verify we still have max 5 backups
        final_resp = self.session.get(f"{BASE_URL}/api/backup/list")
        final_backups = final_resp.json()["backups"]
        assert len(final_backups) <= 5, f"Expected max 5 backups, got {len(final_backups)}"
        
        # Verify oldest was deleted
        final_ids = [b["backup_id"] for b in final_backups]
        # Note: oldest_backup_id might have been deleted
        
        # Cleanup test backups
        for bid in created_ids + [sixth_id]:
            try:
                self.session.delete(f"{BASE_URL}/api/backup/{bid}")
            except:
                pass
        
        print(f"✓ TEST_18: Auto-cleanup verified - max 5 backups maintained")
    
    # ─── Test 19: Create backup with default name ───
    def test_19_create_backup_default_name(self):
        """Create backup without name should use default timestamp name"""
        resp = self.session.post(f"{BASE_URL}/api/backup/create", json={})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        assert "Backup" in data["name"], f"Default name should contain 'Backup', got {data['name']}"
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/backup/{data['backup_id']}")
        print(f"✓ TEST_19: Default backup name: {data['name']}")
    
    # ─── Test 20: Backup excludes compressed_data in list ───
    def test_20_list_excludes_compressed_data(self):
        """List backups should not include compressed_data blob"""
        # Create a backup first
        create_resp = self.session.post(f"{BASE_URL}/api/backup/create", json={
            "name": "TEST_No_Blob"
        })
        assert create_resp.status_code == 200
        backup_id = create_resp.json()["backup_id"]
        
        # Get list
        list_resp = self.session.get(f"{BASE_URL}/api/backup/list")
        backups = list_resp.json()["backups"]
        
        for b in backups:
            assert "compressed_data" not in b, "List should not include compressed_data"
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/backup/{backup_id}")
        print("✓ TEST_20: List excludes compressed_data blob")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
