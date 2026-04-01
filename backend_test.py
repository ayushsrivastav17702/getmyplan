import requests
import sys
import json
from datetime import datetime
from pathlib import Path

class FashionRetailAPITester:
    def __init__(self, base_url="https://zip-improved.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'} if not files else {}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and 'error' in response_data:
                        print(f"   ⚠️  API returned error: {response_data['error']}")
                        return False, response_data
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append(f"{name}: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test backend API health check"""
        return self.run_test("Backend Health Check", "GET", "", 200)

    def test_upload_status(self):
        """Test upload status endpoint"""
        return self.run_test("Upload Status", "GET", "upload/status", 200)

    def test_config_endpoints(self):
        """Test configuration GET and POST"""
        # Test GET config
        get_success, config_data = self.run_test("Get Configuration", "GET", "config", 200)
        
        # Test POST config
        test_config = {
            "noos_enabled": True,
            "ros_enabled": True,
            "size_gap_enabled": True,
            "lifecycle_enabled": True,
            "min_shelf_life_days": 30,
            "pivotal_size_threshold": 75,
            "selected_seasons": ["SS24", "AW24"]
        }
        post_success, _ = self.run_test("Save Configuration", "POST", "config", 200, data=test_config)
        
        return get_success and post_success

    def test_filter_options(self):
        """Test filter options endpoint"""
        success, response_data = self.run_test("Filter Options", "GET", "analytics/filter-options", 200)
        if success and response_data:
            # Verify response structure
            expected_keys = ['categories', 'channels', 'regions', 'dateRange']
            for key in expected_keys:
                if key not in response_data:
                    print(f"   ⚠️  Missing key '{key}' in filter options response")
                    return False
            print(f"   ✅ Filter options structure valid")
            print(f"   📊 Categories: {len(response_data.get('categories', []))}")
            print(f"   📊 Channels: {len(response_data.get('channels', []))}")
            print(f"   📊 Regions: {len(response_data.get('regions', []))}")
            print(f"   📊 Date Range: {response_data.get('dateRange', {})}")
        return success

    def test_analytics_overview(self):
        """Test analytics overview endpoint"""
        return self.run_test("Analytics Overview", "GET", "analytics/overview", 200)

    def test_ros_analysis(self):
        """Test ROS analysis endpoint"""
        return self.run_test("ROS Analysis", "GET", "analytics/ros", 200)

    def test_ros_analysis_with_filters(self):
        """Test ROS analysis with filter parameters"""
        filter_params = "start_date=2024-01-01&end_date=2024-12-31&min_size_percent=50"
        return self.run_test("ROS Analysis with Filters", "GET", f"analytics/ros?{filter_params}", 200)

    def test_size_gap_analysis(self):
        """Test size gap analysis endpoint"""
        return self.run_test("Size Gap Analysis", "GET", "analytics/size-gap", 200)

    def test_size_gap_with_thresholds(self):
        """Test size gap analysis with threshold filters"""
        filter_params = "understock_threshold=-10&overstock_threshold=10"
        return self.run_test("Size Gap with Thresholds", "GET", f"analytics/size-gap?{filter_params}", 200)

    def test_noos_analysis(self):
        """Test NOOS analysis endpoint"""
        return self.run_test("NOOS Analysis", "GET", "analytics/noos", 200)

    def test_noos_analysis_with_filters(self):
        """Test NOOS analysis with filter parameters"""
        filter_params = "start_date=2024-01-01&categories=Apparel&channels=Online"
        return self.run_test("NOOS Analysis with Filters", "GET", f"analytics/noos?{filter_params}", 200)

    def test_bi_dashboard(self):
        """Test BI dashboard endpoint"""
        return self.run_test("BI Dashboard", "GET", "analytics/bi-dashboard", 200)

    def test_bi_dashboard_with_filters(self):
        """Test BI dashboard with filter parameters"""
        filter_params = "start_date=2024-01-01&end_date=2024-12-31&regions=North,South"
        return self.run_test("BI Dashboard with Filters", "GET", f"analytics/bi-dashboard?{filter_params}", 200)

    def test_chat_endpoint(self):
        """Test chat endpoint"""
        chat_message = {
            "message": "What is NOOS analysis?",
            "session_id": None
        }
        return self.run_test("Chat Endpoint", "POST", "chat", 200, data=chat_message)

    def test_file_upload(self):
        """Test file upload functionality with sample data"""
        sample_data_path = Path("/app/sample_data")
        if not sample_data_path.exists():
            print("⚠️  Sample data directory not found, skipping file upload test")
            return True

        # Test uploading a sample CSV file
        csv_files = list(sample_data_path.glob("*.csv"))
        if not csv_files:
            print("⚠️  No CSV files found in sample data, skipping file upload test")
            return True

        # Try to upload the first CSV file
        sample_file = csv_files[0]
        file_type = sample_file.stem  # Get filename without extension
        
        try:
            with open(sample_file, 'rb') as f:
                files = {'file': (sample_file.name, f, 'text/csv')}
                success, response_data = self.run_test(
                    f"File Upload ({file_type})", 
                    "POST", 
                    f"upload/{file_type}", 
                    200, 
                    files=files
                )
                return success
        except Exception as e:
            print(f"❌ File upload test failed: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting Fashion Retail Gap Analysis API Tests")
        print(f"   Base URL: {self.base_url}")
        print("=" * 60)

        # Core API tests
        self.test_health_check()
        self.test_upload_status()
        self.test_config_endpoints()
        
        # Filter options test
        self.test_filter_options()
        
        # Analytics tests
        self.test_analytics_overview()
        self.test_ros_analysis()
        self.test_ros_analysis_with_filters()
        self.test_size_gap_analysis()
        self.test_size_gap_with_thresholds()
        self.test_noos_analysis()
        self.test_noos_analysis_with_filters()
        self.test_bi_dashboard()
        self.test_bi_dashboard_with_filters()
        
        # Chat test
        self.test_chat_endpoint()
        
        # File upload test
        self.test_file_upload()

        # Print results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for failure in self.failed_tests:
                print(f"   • {failure}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"\n✨ Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = FashionRetailAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())