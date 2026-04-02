"""
SFTP Monitor API Tests - Iteration 6
Tests for SFTP Data Pipeline Monitor endpoints including:
- Status, config, stats, logs endpoints
- Trigger, seed-demo, retry-failed operations
- Scheduler start/stop
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestSFTPStatus:
    """SFTP status and connection tests"""
    
    def test_get_sftp_status(self):
        """GET /api/admin/sftp/status returns demo_mode, scheduler, connection info"""
        response = requests.get(f"{BASE_URL}/api/admin/sftp/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "demo_mode" in data
        assert "scheduler" in data
        assert "connection" in data
        assert "timestamp" in data
        
        # Scheduler should have running, last_run, last_result
        assert "running" in data["scheduler"]
        assert "last_run" in data["scheduler"]
        
        # Connection should have status and message
        assert "status" in data["connection"]
        assert "message" in data["connection"]
        print(f"SFTP Status: demo_mode={data['demo_mode']}, scheduler_running={data['scheduler']['running']}")


class TestSFTPConfig:
    """SFTP configuration tests"""
    
    def test_get_sftp_config(self):
        """GET /api/admin/sftp/config returns configuration"""
        response = requests.get(f"{BASE_URL}/api/admin/sftp/config")
        assert response.status_code == 200
        # Config may be empty dict if not configured
        data = response.json()
        assert isinstance(data, dict)
        print(f"SFTP Config: {data}")
    
    def test_save_sftp_config(self):
        """POST /api/admin/sftp/config saves configuration"""
        config = {
            "host": "test.sftp.example.com",
            "port": 22,
            "username": "testuser",
            "password": "",
            "base_path": "/incoming",
            "processed_path": "/processed",
            "failed_path": "/failed",
            "poll_interval_minutes": 30,
            "max_retries": 3,
            "alert_emails": ""
        }
        response = requests.post(f"{BASE_URL}/api/admin/sftp/config", json=config)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "saved" in data["message"].lower()
        print(f"Config save response: {data}")
        
        # Verify config was saved
        get_response = requests.get(f"{BASE_URL}/api/admin/sftp/config")
        assert get_response.status_code == 200
        saved_config = get_response.json()
        assert saved_config.get("host") == "test.sftp.example.com"
        assert saved_config.get("username") == "testuser"
        
        # Reset to demo mode
        reset_config = {"host": "", "port": 22, "username": "", "password": "", "base_path": "/incoming", "poll_interval_minutes": 30}
        requests.post(f"{BASE_URL}/api/admin/sftp/config", json=reset_config)


class TestSFTPStats:
    """SFTP statistics tests"""
    
    def test_get_sftp_stats(self):
        """GET /api/admin/sftp/stats returns processing statistics"""
        response = requests.get(f"{BASE_URL}/api/admin/sftp/stats")
        assert response.status_code == 200
        
        data = response.json()
        # Required fields
        assert "total" in data
        assert "success" in data
        assert "failed" in data
        assert "total_rows" in data
        assert "success_rate" in data
        assert "by_type" in data
        assert "trend" in data
        assert "stores_uploaded_today" in data
        assert "stores_total" in data
        
        # Validate by_type structure (3 types)
        by_type = data["by_type"]
        assert isinstance(by_type, dict)
        # Should have daily_sales, store_inventory, warehouse_inventory
        for file_type in ["daily_sales", "store_inventory", "warehouse_inventory"]:
            if file_type in by_type:
                type_data = by_type[file_type]
                assert "total" in type_data
                assert "success" in type_data
                assert "failed" in type_data
                assert "rows" in type_data
        
        # Validate trend structure (7 days)
        trend = data["trend"]
        assert isinstance(trend, list)
        if len(trend) > 0:
            assert "date" in trend[0]
            assert "total" in trend[0]
            assert "success" in trend[0]
            assert "failed" in trend[0]
        
        print(f"SFTP Stats: total={data['total']}, success_rate={data['success_rate']}%, by_type_count={len(by_type)}, trend_days={len(trend)}")


class TestSFTPLogs:
    """SFTP processing logs tests"""
    
    def test_get_sftp_logs(self):
        """GET /api/admin/sftp/logs returns array of log records"""
        response = requests.get(f"{BASE_URL}/api/admin/sftp/logs?days=7&limit=50")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            log = data[0]
            # Required fields in each log record
            assert "filename" in log
            assert "file_type" in log
            assert "status" in log
            assert "rows_processed" in log
            assert "processed_at" in log
            
            # Validate file_type is one of expected values
            assert log["file_type"] in ["daily_sales", "store_inventory", "warehouse_inventory"]
            # Validate status is success or error
            assert log["status"] in ["success", "error"]
        
        print(f"SFTP Logs: {len(data)} records returned")
    
    def test_get_sftp_logs_with_filters(self):
        """GET /api/admin/sftp/logs with status and file_type filters"""
        # Filter by status
        response = requests.get(f"{BASE_URL}/api/admin/sftp/logs?days=7&status=success&limit=20")
        assert response.status_code == 200
        data = response.json()
        for log in data:
            assert log["status"] == "success"
        
        # Filter by file_type
        response = requests.get(f"{BASE_URL}/api/admin/sftp/logs?days=7&file_type=daily_sales&limit=20")
        assert response.status_code == 200
        data = response.json()
        for log in data:
            assert log["file_type"] == "daily_sales"
        
        print(f"SFTP Logs filters working correctly")


class TestSFTPOperations:
    """SFTP operations tests (trigger, seed, retry)"""
    
    def test_seed_demo_data(self):
        """POST /api/admin/sftp/seed-demo seeds 7 days of demo data"""
        response = requests.post(f"{BASE_URL}/api/admin/sftp/seed-demo")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "count" in data
        
        # Should seed approximately 154 records (22 per day * 7 days)
        # 10 stores * 2 file types + 2 warehouses = 22 per day
        assert data["count"] >= 100  # Allow some variance
        print(f"Seed demo: {data['count']} records created")
    
    def test_trigger_processing(self):
        """POST /api/admin/sftp/trigger runs one demo processing cycle"""
        response = requests.post(f"{BASE_URL}/api/admin/sftp/trigger")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "total" in data
        assert "success" in data
        assert "failed" in data
        
        # Demo cycle should process 22 files (10 stores * 2 types + 2 warehouses)
        assert data["total"] == 22
        assert data["success"] + data["failed"] == data["total"]
        print(f"Trigger: processed {data['total']} files, {data['success']} success, {data['failed']} failed")
    
    def test_retry_failed_files(self):
        """POST /api/admin/sftp/retry-failed retries recently failed files"""
        response = requests.post(f"{BASE_URL}/api/admin/sftp/retry-failed")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "retried" in data
        print(f"Retry failed: {data['message']}")


class TestSFTPScheduler:
    """SFTP scheduler tests"""
    
    def test_start_scheduler(self):
        """POST /api/admin/sftp/scheduler/start starts the scheduler"""
        response = requests.post(f"{BASE_URL}/api/admin/sftp/scheduler/start")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "started" in data["message"].lower()
        print(f"Scheduler start: {data}")
    
    def test_stop_scheduler(self):
        """POST /api/admin/sftp/scheduler/stop stops the scheduler"""
        response = requests.post(f"{BASE_URL}/api/admin/sftp/scheduler/stop")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "stopped" in data["message"].lower()
        print(f"Scheduler stop: {data}")
    
    def test_scheduler_status_after_stop(self):
        """Verify scheduler is stopped after stop command"""
        # First stop the scheduler
        requests.post(f"{BASE_URL}/api/admin/sftp/scheduler/stop")
        
        # Check status
        response = requests.get(f"{BASE_URL}/api/admin/sftp/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["scheduler"]["running"] == False
        print("Scheduler confirmed stopped")


class TestSFTPTestConnection:
    """SFTP connection test endpoint"""
    
    def test_connection_demo_mode(self):
        """POST /api/admin/sftp/test-connection in demo mode"""
        # Ensure we're in demo mode
        reset_config = {"host": "", "port": 22, "username": "", "password": "", "base_path": "/incoming", "poll_interval_minutes": 30}
        requests.post(f"{BASE_URL}/api/admin/sftp/config", json=reset_config)
        
        response = requests.post(f"{BASE_URL}/api/admin/sftp/test-connection")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "demo"
        assert "message" in data
        print(f"Test connection (demo mode): {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
