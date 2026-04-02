"""
Test suite for Data Quality & SLA Dashboard endpoints
Tests: /api/admin/quality/store-uploads/{date}, /api/admin/quality/sla-metrics, /api/admin/quality/scorecard
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDataQualityEndpoints:
    """Data Quality & SLA Dashboard API tests"""

    # ── Store Uploads Endpoint ──────────────────────────────────────────
    
    def test_store_uploads_returns_array(self):
        """GET /api/admin/quality/store-uploads/{date} returns array of stores"""
        response = requests.get(f"{BASE_URL}/api/admin/quality/store-uploads/2026-04-01")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be an array"
        print(f"✓ Store uploads returns array with {len(data)} stores")

    def test_store_uploads_returns_10_stores(self):
        """GET /api/admin/quality/store-uploads/{date} returns exactly 10 stores"""
        response = requests.get(f"{BASE_URL}/api/admin/quality/store-uploads/2026-04-01")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10, f"Expected 10 stores, got {len(data)}"
        print("✓ Store uploads returns exactly 10 stores")

    def test_store_uploads_has_required_fields(self):
        """Each store has code, name, status, qualityScore, completeness, accuracy, timeliness"""
        response = requests.get(f"{BASE_URL}/api/admin/quality/store-uploads/2026-04-01")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ['code', 'name', 'status', 'qualityScore', 'completeness', 'accuracy', 'timeliness']
        for store in data:
            for field in required_fields:
                assert field in store, f"Store {store.get('code', 'unknown')} missing field: {field}"
        print(f"✓ All stores have required fields: {required_fields}")

    def test_store_uploads_status_values(self):
        """Store status is one of: uploaded, missing, late, partial"""
        response = requests.get(f"{BASE_URL}/api/admin/quality/store-uploads/2026-04-01")
        assert response.status_code == 200
        data = response.json()
        
        valid_statuses = ['uploaded', 'missing', 'late', 'partial']
        for store in data:
            assert store['status'] in valid_statuses, f"Invalid status: {store['status']}"
        print(f"✓ All store statuses are valid: {valid_statuses}")

    def test_store_uploads_quality_scores_range(self):
        """Quality scores are between 0 and 100"""
        response = requests.get(f"{BASE_URL}/api/admin/quality/store-uploads/2026-04-01")
        assert response.status_code == 200
        data = response.json()
        
        for store in data:
            assert 0 <= store['qualityScore'] <= 100, f"Invalid qualityScore: {store['qualityScore']}"
            assert 0 <= store['completeness'] <= 100, f"Invalid completeness: {store['completeness']}"
            assert 0 <= store['accuracy'] <= 100, f"Invalid accuracy: {store['accuracy']}"
            assert 0 <= store['timeliness'] <= 100, f"Invalid timeliness: {store['timeliness']}"
        print("✓ All quality scores are in valid range (0-100)")

    def test_store_uploads_different_date(self):
        """Store uploads endpoint works with different dates"""
        response = requests.get(f"{BASE_URL}/api/admin/quality/store-uploads/2026-01-15")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Store uploads works with different date, returned {len(data)} stores")

    # ── SLA Metrics Endpoint ────────────────────────────────────────────
    
    def test_sla_metrics_returns_200(self):
        """GET /api/admin/quality/sla-metrics returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/quality/sla-metrics")
        assert response.status_code == 200
        print("✓ SLA metrics endpoint returns 200")

    def test_sla_metrics_has_compliance_rate(self):
        """SLA metrics includes complianceRate"""
        response = requests.get(f"{BASE_URL}/api/admin/quality/sla-metrics")
        assert response.status_code == 200
        data = response.json()
        assert 'complianceRate' in data, "Missing complianceRate"
        assert isinstance(data['complianceRate'], (int, float))
        print(f"✓ SLA metrics has complianceRate: {data['complianceRate']}%")

    def test_sla_metrics_has_file_counts(self):
        """SLA metrics includes expectedFiles, receivedFiles, missingFiles"""
        response = requests.get(f"{BASE_URL}/api/admin/quality/sla-metrics")
        assert response.status_code == 200
        data = response.json()
        
        assert 'expectedFiles' in data, "Missing expectedFiles"
        assert 'receivedFiles' in data, "Missing receivedFiles"
        assert 'missingFiles' in data, "Missing missingFiles"
        
        assert isinstance(data['expectedFiles'], int)
        assert isinstance(data['receivedFiles'], int)
        assert isinstance(data['missingFiles'], int)
        print(f"✓ SLA metrics has file counts: expected={data['expectedFiles']}, received={data['receivedFiles']}, missing={data['missingFiles']}")

    def test_sla_metrics_has_by_file_type(self):
        """SLA metrics includes byFileType array"""
        response = requests.get(f"{BASE_URL}/api/admin/quality/sla-metrics")
        assert response.status_code == 200
        data = response.json()
        
        assert 'byFileType' in data, "Missing byFileType"
        assert isinstance(data['byFileType'], list)
        assert len(data['byFileType']) > 0, "byFileType array is empty"
        
        # Check each file type has required fields
        for ft in data['byFileType']:
            assert 'name' in ft, "File type missing name"
            assert 'compliance' in ft, "File type missing compliance"
            assert 'expected' in ft, "File type missing expected"
            assert 'received' in ft, "File type missing received"
        print(f"✓ SLA metrics has byFileType with {len(data['byFileType'])} types")

    def test_sla_metrics_has_trend(self):
        """SLA metrics includes trend value"""
        response = requests.get(f"{BASE_URL}/api/admin/quality/sla-metrics")
        assert response.status_code == 200
        data = response.json()
        
        assert 'trend' in data, "Missing trend"
        assert isinstance(data['trend'], (int, float))
        print(f"✓ SLA metrics has trend: {data['trend']}")

    # ── Scorecard Endpoint ──────────────────────────────────────────────
    
    def test_scorecard_returns_200(self):
        """GET /api/admin/quality/scorecard returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/quality/scorecard")
        assert response.status_code == 200
        print("✓ Scorecard endpoint returns 200")

    def test_scorecard_has_overall_score(self):
        """Scorecard includes overall score"""
        response = requests.get(f"{BASE_URL}/api/admin/quality/scorecard")
        assert response.status_code == 200
        data = response.json()
        
        assert 'overall' in data, "Missing overall score"
        assert isinstance(data['overall'], (int, float))
        assert 0 <= data['overall'] <= 100, f"Invalid overall score: {data['overall']}"
        print(f"✓ Scorecard has overall score: {data['overall']}")

    def test_scorecard_has_five_metrics(self):
        """Scorecard includes 5 metric breakdowns: completeness, accuracy, timeliness, consistency, validity"""
        response = requests.get(f"{BASE_URL}/api/admin/quality/scorecard")
        assert response.status_code == 200
        data = response.json()
        
        required_metrics = ['completeness', 'accuracy', 'timeliness', 'consistency', 'validity']
        for metric in required_metrics:
            assert metric in data, f"Missing metric: {metric}"
            assert 'current' in data[metric], f"{metric} missing 'current'"
            assert 'target' in data[metric], f"{metric} missing 'target'"
            assert 'gap' in data[metric], f"{metric} missing 'gap'"
        print(f"✓ Scorecard has all 5 metrics: {required_metrics}")

    def test_scorecard_metric_values_valid(self):
        """Scorecard metric values are in valid range"""
        response = requests.get(f"{BASE_URL}/api/admin/quality/scorecard")
        assert response.status_code == 200
        data = response.json()
        
        metrics = ['completeness', 'accuracy', 'timeliness', 'consistency', 'validity']
        for metric in metrics:
            assert 0 <= data[metric]['current'] <= 100, f"Invalid {metric} current: {data[metric]['current']}"
            assert 0 <= data[metric]['target'] <= 100, f"Invalid {metric} target: {data[metric]['target']}"
        print("✓ All scorecard metric values are in valid range")

    def test_scorecard_has_recommendations(self):
        """Scorecard includes recommendations array"""
        response = requests.get(f"{BASE_URL}/api/admin/quality/scorecard")
        assert response.status_code == 200
        data = response.json()
        
        assert 'recommendations' in data, "Missing recommendations"
        assert isinstance(data['recommendations'], list)
        print(f"✓ Scorecard has {len(data['recommendations'])} recommendations")


class TestExistingEndpoints:
    """Verify existing endpoints still work after Data Quality feature addition"""

    def test_root_endpoint(self):
        """GET /api/ returns 200"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        print("✓ Root endpoint works")

    def test_upload_status(self):
        """GET /api/upload/status returns 200"""
        response = requests.get(f"{BASE_URL}/api/upload/status")
        assert response.status_code == 200
        print("✓ Upload status endpoint works")

    def test_sftp_status(self):
        """GET /api/admin/sftp/status returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/sftp/status")
        assert response.status_code == 200
        data = response.json()
        assert 'demo_mode' in data
        print("✓ SFTP status endpoint works")

    def test_sftp_stats(self):
        """GET /api/admin/sftp/stats returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/sftp/stats")
        assert response.status_code == 200
        print("✓ SFTP stats endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
