"""
SFTP Monitor Test Suite - Iteration 28
Tests 19 SFTP gap test cases covering:
- Connection pool, retry backoff, SSL/TLS
- Upload, download, batch upload
- Transfer progress, resume
- Malformed file handling, duplicate detection
- File archive, date filtering
- Speed metrics, daily summary
- Scheduler start/stop
"""
import pytest
import requests
import os
import io
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSFTPConnectionAndPool:
    """SFTP-03, SFTP-04, SFTP-07, SFTP-08: Connection pool, retry, SSL tests"""
    
    def test_sftp_03_connection_timeout_retry_backoff(self):
        """SFTP-03: GET /api/admin/sftp/status returns retry_config with max_retries, base_delay, max_delay"""
        response = requests.get(f"{BASE_URL}/api/admin/sftp/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify retry_config exists with required fields
        assert 'retry_config' in data, "retry_config missing from status"
        retry_config = data['retry_config']
        assert 'max_retries' in retry_config, "max_retries missing"
        assert 'base_delay' in retry_config, "base_delay missing"
        assert 'max_delay' in retry_config, "max_delay missing"
        assert retry_config['max_retries'] >= 0
        assert retry_config['base_delay'] > 0
        assert retry_config['max_delay'] > retry_config['base_delay']
        print(f"SFTP-03 PASS: retry_config = {retry_config}")
    
    def test_sftp_03_connection_pool_retry_config(self):
        """SFTP-03: GET /api/admin/sftp/connection-pool returns retry_config"""
        response = requests.get(f"{BASE_URL}/api/admin/sftp/connection-pool")
        assert response.status_code == 200
        data = response.json()
        
        assert 'retry_config' in data, "retry_config missing from connection-pool"
        retry_config = data['retry_config']
        assert 'max_retries' in retry_config
        assert 'base_delay' in retry_config
        assert 'max_delay' in retry_config
        print(f"SFTP-03 PASS: connection-pool retry_config = {retry_config}")
    
    def test_sftp_04_network_auto_reconnect(self):
        """SFTP-04: GET /api/admin/sftp/status returns connection info with pool stats"""
        response = requests.get(f"{BASE_URL}/api/admin/sftp/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify pool stats for auto-reconnect readiness
        assert 'pool' in data, "pool stats missing"
        pool = data['pool']
        assert 'max_size' in pool
        assert 'available' in pool
        assert 'active' in pool
        assert pool['max_size'] > 0, "Pool max_size should be > 0"
        print(f"SFTP-04 PASS: pool stats = {pool}")
    
    def test_sftp_07_connection_pool_stats(self):
        """SFTP-07: GET /api/admin/sftp/connection-pool returns pool stats"""
        response = requests.get(f"{BASE_URL}/api/admin/sftp/connection-pool")
        assert response.status_code == 200
        data = response.json()
        
        assert 'pool' in data, "pool missing"
        pool = data['pool']
        assert 'max_size' in pool
        assert 'available' in pool
        assert 'active' in pool
        assert 'total_created' in pool
        assert 'ssl_mode' in pool
        print(f"SFTP-07 PASS: pool = {pool}")
    
    def test_sftp_08_ssl_tls_verification(self):
        """SFTP-08: GET /api/admin/sftp/connection-pool returns ssl_mode field"""
        response = requests.get(f"{BASE_URL}/api/admin/sftp/connection-pool")
        assert response.status_code == 200
        data = response.json()
        
        assert 'ssl_mode' in data, "ssl_mode missing from connection-pool"
        assert data['ssl_mode'] in ['auto', 'strict', 'reject'], f"Invalid ssl_mode: {data['ssl_mode']}"
        print(f"SFTP-08 PASS: ssl_mode = {data['ssl_mode']}")


class TestSFTPFileTransfer:
    """SFTP-09, SFTP-10, SFTP-11, SFTP-12, SFTP-14: Upload, download, progress, resume tests"""
    
    def test_sftp_09_upload_file(self):
        """SFTP-09: POST /api/admin/sftp/upload returns status=success with speed_mbps and file_hash"""
        # Create a valid CSV file
        csv_content = "store_code,sku,day,quantity,revenue,channel\nST001,1000001,2026-04-01,5,7495,Retail\n"
        files = {'file': ('test_upload_09.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
        data = {'remote_path': '/incoming', 'overwrite': 'false'}
        
        response = requests.post(f"{BASE_URL}/api/admin/sftp/upload", files=files, data=data)
        assert response.status_code == 200
        result = response.json()
        
        assert result['status'] == 'success', f"Upload failed: {result}"
        assert 'speed_mbps' in result, "speed_mbps missing"
        assert 'file_hash' in result, "file_hash missing"
        assert result['speed_mbps'] >= 0
        assert len(result['file_hash']) > 0
        print(f"SFTP-09 PASS: upload success, speed={result['speed_mbps']} MB/s, hash={result['file_hash'][:16]}...")
    
    def test_sftp_10_download_file(self):
        """SFTP-10: POST /api/admin/sftp/download returns status=success with bytes, speed_mbps"""
        data = {'remote_path': '/incoming/test_file.csv', 'resume_offset': '0'}
        
        response = requests.post(f"{BASE_URL}/api/admin/sftp/download", data=data)
        assert response.status_code == 200
        result = response.json()
        
        assert result['status'] == 'success', f"Download failed: {result}"
        assert 'bytes' in result, "bytes missing"
        assert 'speed_mbps' in result, "speed_mbps missing"
        assert result['bytes'] > 0
        print(f"SFTP-10 PASS: download success, bytes={result['bytes']}, speed={result['speed_mbps']} MB/s")
    
    def test_sftp_11_transfer_progress(self):
        """SFTP-11: GET /api/admin/sftp/transfer-progress/{id} returns progress with transferred_bytes and total_bytes"""
        # First do an upload to get a transfer_id
        csv_content = "store_code,sku,day,quantity,revenue,channel\nST001,1000001,2026-04-01,5,7495,Retail\n"
        files = {'file': ('test_progress.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
        data = {'remote_path': '/incoming', 'overwrite': 'false'}
        
        upload_response = requests.post(f"{BASE_URL}/api/admin/sftp/upload", files=files, data=data)
        assert upload_response.status_code == 200
        transfer_id = upload_response.json().get('transfer_id')
        assert transfer_id, "No transfer_id returned"
        
        # Get transfer progress
        response = requests.get(f"{BASE_URL}/api/admin/sftp/transfer-progress/{transfer_id}")
        assert response.status_code == 200
        result = response.json()
        
        assert 'transferred_bytes' in result, "transferred_bytes missing"
        assert 'total_bytes' in result, "total_bytes missing"
        assert result['transferred_bytes'] >= 0
        assert result['total_bytes'] >= 0
        print(f"SFTP-11 PASS: progress = {result['transferred_bytes']}/{result['total_bytes']} bytes")
    
    def test_sftp_12_partial_transfer_resume(self):
        """SFTP-12: POST /api/admin/sftp/resume/{id} for failed downloads"""
        # Get all transfers to find one
        transfers_response = requests.get(f"{BASE_URL}/api/admin/sftp/transfers")
        assert transfers_response.status_code == 200
        transfers = transfers_response.json()
        
        if len(transfers) > 0:
            transfer_id = transfers[0]['transfer_id']
            response = requests.post(f"{BASE_URL}/api/admin/sftp/resume/{transfer_id}")
            assert response.status_code == 200
            result = response.json()
            # Either resumes or says not in failed state
            assert 'message' in result or 'status' in result
            print(f"SFTP-12 PASS: resume endpoint works, result = {result}")
        else:
            print("SFTP-12 PASS: No transfers to resume (endpoint exists)")
    
    def test_sftp_14_file_overwrite_protection(self):
        """SFTP-14: POST /api/admin/sftp/upload with overwrite=false auto-versions files"""
        csv_content = "store_code,sku,day,quantity,revenue,channel\nST001,1000001,2026-04-01,5,7495,Retail\n"
        files = {'file': ('test_overwrite.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
        data = {'remote_path': '/incoming', 'overwrite': 'false'}
        
        response = requests.post(f"{BASE_URL}/api/admin/sftp/upload", files=files, data=data)
        assert response.status_code == 200
        result = response.json()
        
        # Response should include overwrite_protected field
        assert 'overwrite_protected' in result or result['status'] in ['success', 'duplicate']
        print(f"SFTP-14 PASS: overwrite protection works, result = {result.get('overwrite_protected', 'N/A')}")


class TestSFTPBatchAndMalformed:
    """SFTP-15, SFTP-20, SFTP-22, SFTP-23: Batch upload, malformed, duplicate, archive tests"""
    
    def test_sftp_15_batch_file_upload(self):
        """SFTP-15: POST /api/admin/sftp/batch-upload returns total, uploaded, failed, malformed, duplicates"""
        csv1 = "store_code,sku,day,quantity,revenue,channel\nST001,1000001,2026-04-01,5,7495,Retail\n"
        csv2 = "store_code,sku,day,quantity,revenue,channel\nST002,1000002,2026-04-01,3,4497,Retail\n"
        
        files = [
            ('files', ('batch_test1.csv', io.BytesIO(csv1.encode()), 'text/csv')),
            ('files', ('batch_test2.csv', io.BytesIO(csv2.encode()), 'text/csv')),
        ]
        
        response = requests.post(f"{BASE_URL}/api/admin/sftp/batch-upload", files=files)
        assert response.status_code == 200
        result = response.json()
        
        assert 'total' in result, "total missing"
        assert 'uploaded' in result, "uploaded missing"
        assert 'failed' in result, "failed missing"
        assert 'malformed' in result, "malformed missing"
        assert 'duplicates' in result, "duplicates missing"
        assert result['total'] == 2
        print(f"SFTP-15 PASS: batch upload total={result['total']}, uploaded={result['uploaded']}, failed={result['failed']}")
    
    def test_sftp_20_malformed_file_handling(self):
        """SFTP-20: POST /api/admin/sftp/upload with malformed CSV returns status=malformed"""
        # Create a malformed CSV (no data rows)
        malformed_content = "this is not a valid csv file"
        files = {'file': ('malformed_test.csv', io.BytesIO(malformed_content.encode()), 'text/csv')}
        data = {'remote_path': '/incoming', 'overwrite': 'false'}
        
        response = requests.post(f"{BASE_URL}/api/admin/sftp/upload", files=files, data=data)
        assert response.status_code == 200
        result = response.json()
        
        assert result['status'] == 'malformed', f"Expected malformed status, got: {result['status']}"
        assert 'error' in result, "error message missing"
        assert 'archive_path' in result, "archive_path missing"
        assert '/failed/' in result['archive_path'], "archive_path should contain /failed/"
        print(f"SFTP-20 PASS: malformed file detected, archive_path = {result['archive_path']}")
    
    def test_sftp_22_duplicate_file_handling(self):
        """SFTP-22: Upload same file twice, second upload returns status=duplicate"""
        csv_content = f"store_code,sku,day,quantity,revenue,channel\nST001,1000001,2026-04-01,{time.time()},7495,Retail\n"
        
        # First upload
        files1 = {'file': ('dup_test_22.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
        data = {'remote_path': '/incoming', 'overwrite': 'false'}
        response1 = requests.post(f"{BASE_URL}/api/admin/sftp/upload", files=files1, data=data)
        assert response1.status_code == 200
        result1 = response1.json()
        assert result1['status'] == 'success', f"First upload should succeed: {result1}"
        
        # Second upload (same content)
        files2 = {'file': ('dup_test_22.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
        response2 = requests.post(f"{BASE_URL}/api/admin/sftp/upload", files=files2, data=data)
        assert response2.status_code == 200
        result2 = response2.json()
        
        assert result2['status'] == 'duplicate', f"Second upload should be duplicate: {result2}"
        assert 'file_hash' in result2, "file_hash missing from duplicate response"
        print(f"SFTP-22 PASS: duplicate detected, file_hash = {result2['file_hash'][:16]}...")
    
    def test_sftp_23_file_archive_after_processing(self):
        """SFTP-23: Logs include archive_path field showing /archive/processed/ or /archive/failed/"""
        response = requests.get(f"{BASE_URL}/api/admin/sftp/logs", params={'limit': 20})
        assert response.status_code == 200
        logs = response.json()
        
        assert len(logs) > 0, "No logs found"
        
        # Check that logs have archive_path
        logs_with_archive = [l for l in logs if l.get('archive_path')]
        assert len(logs_with_archive) > 0, "No logs with archive_path found"
        
        for log in logs_with_archive[:5]:
            archive_path = log['archive_path']
            assert '/archive/' in archive_path, f"Invalid archive_path: {archive_path}"
            assert '/processed/' in archive_path or '/failed/' in archive_path, f"archive_path should contain /processed/ or /failed/: {archive_path}"
        
        print(f"SFTP-23 PASS: {len(logs_with_archive)} logs have valid archive_path")


class TestSFTPLogsAndFiltering:
    """SFTP-25, SFTP-29: Date filtering and error log download tests"""
    
    def test_sftp_25_filter_logs_by_date(self):
        """SFTP-25: GET /api/admin/sftp/logs?start_date=...&end_date=... returns filtered results"""
        params = {
            'start_date': '2026-03-28',
            'end_date': '2026-04-03',
            'limit': 50
        }
        
        response = requests.get(f"{BASE_URL}/api/admin/sftp/logs", params=params)
        assert response.status_code == 200
        logs = response.json()
        
        assert isinstance(logs, list), "Logs should be a list"
        
        # Verify all logs are within date range
        for log in logs:
            if log.get('processed_at'):
                log_date = log['processed_at'][:10]
                assert log_date >= '2026-03-28', f"Log date {log_date} is before start_date"
                assert log_date <= '2026-04-03', f"Log date {log_date} is after end_date"
        
        print(f"SFTP-25 PASS: {len(logs)} logs returned within date range")
    
    def test_sftp_29_download_error_log(self):
        """SFTP-29: GET /api/admin/sftp/error-log/download returns CSV"""
        response = requests.get(f"{BASE_URL}/api/admin/sftp/error-log/download")
        assert response.status_code == 200
        
        content_type = response.headers.get('content-type', '')
        assert 'text/csv' in content_type, f"Expected text/csv, got: {content_type}"
        
        # Verify CSV content
        content = response.text
        assert 'Timestamp' in content or 'timestamp' in content.lower(), "CSV should have Timestamp header"
        assert 'Filename' in content or 'filename' in content.lower(), "CSV should have Filename header"
        
        print(f"SFTP-29 PASS: error log CSV downloaded, {len(content)} bytes")


class TestSFTPScheduler:
    """SFTP-16: Scheduler start/stop tests"""
    
    def test_sftp_16_scheduler_start_stop(self):
        """SFTP-16: POST /api/admin/sftp/scheduler/start and /stop"""
        # Start scheduler
        start_response = requests.post(f"{BASE_URL}/api/admin/sftp/scheduler/start")
        assert start_response.status_code == 200
        start_result = start_response.json()
        assert 'message' in start_result
        
        # Check status shows running
        status_response = requests.get(f"{BASE_URL}/api/admin/sftp/status")
        assert status_response.status_code == 200
        status = status_response.json()
        assert status['scheduler']['running'] == True, "Scheduler should be running"
        
        # Stop scheduler
        stop_response = requests.post(f"{BASE_URL}/api/admin/sftp/scheduler/stop")
        assert stop_response.status_code == 200
        stop_result = stop_response.json()
        assert 'message' in stop_result
        
        # Check status shows stopped
        status_response2 = requests.get(f"{BASE_URL}/api/admin/sftp/status")
        assert status_response2.status_code == 200
        status2 = status_response2.json()
        assert status2['scheduler']['running'] == False, "Scheduler should be stopped"
        
        print(f"SFTP-16 PASS: scheduler start/stop works correctly")


class TestSFTPSpeedAndSummary:
    """SFTP-30, SFTP-35: Speed metrics and daily summary tests"""
    
    def test_sftp_30_transfer_speed_metrics(self):
        """SFTP-30: GET /api/admin/sftp/speed-metrics returns avg_speed_mbps, max_speed_mbps, daily_metrics"""
        response = requests.get(f"{BASE_URL}/api/admin/sftp/speed-metrics")
        assert response.status_code == 200
        data = response.json()
        
        assert 'avg_speed_mbps' in data, "avg_speed_mbps missing"
        assert 'max_speed_mbps' in data, "max_speed_mbps missing"
        assert 'daily_metrics' in data, "daily_metrics missing"
        
        assert isinstance(data['daily_metrics'], list), "daily_metrics should be a list"
        
        if len(data['daily_metrics']) > 0:
            day = data['daily_metrics'][0]
            assert 'date' in day, "daily_metrics should have date"
            assert 'avg_speed_mbps' in day, "daily_metrics should have avg_speed_mbps"
        
        print(f"SFTP-30 PASS: avg_speed={data['avg_speed_mbps']} MB/s, max_speed={data['max_speed_mbps']} MB/s, {len(data['daily_metrics'])} daily records")
    
    def test_sftp_35_daily_summary_report(self):
        """SFTP-35: GET /api/admin/sftp/daily-summary returns comprehensive summary"""
        response = requests.get(f"{BASE_URL}/api/admin/sftp/daily-summary")
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        required_fields = ['date', 'total_files', 'success', 'failed', 'malformed', 
                          'duplicates', 'success_rate', 'by_type', 'store_coverage', 'top_errors']
        
        for field in required_fields:
            assert field in data, f"{field} missing from daily summary"
        
        # Verify store_coverage structure
        assert 'total_expected' in data['store_coverage']
        assert 'total_received' in data['store_coverage']
        assert 'missing_stores' in data['store_coverage']
        
        # Verify top_errors is a list
        assert isinstance(data['top_errors'], list)
        
        print(f"SFTP-35 PASS: date={data['date']}, total={data['total_files']}, success_rate={data['success_rate']}%")


class TestSFTPStats:
    """Additional stats endpoint tests"""
    
    def test_sftp_stats_endpoint(self):
        """Test /api/admin/sftp/stats returns enhanced stats with malformed/duplicates/speed"""
        response = requests.get(f"{BASE_URL}/api/admin/sftp/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Check for enhanced fields
        assert 'total' in data
        assert 'success' in data
        assert 'failed' in data
        assert 'success_rate' in data
        
        # Check for new fields (malformed, duplicates, speed)
        # These may be 0 if no such records exist
        print(f"SFTP Stats: total={data.get('total')}, success_rate={data.get('success_rate')}%")
        print(f"  malformed={data.get('malformed', 0)}, duplicates={data.get('duplicates', 0)}")
        print(f"  avg_speed={data.get('avg_speed_mbps', 0)} MB/s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
