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
        self.test_preset_id = None

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
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=30)
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

    # ==================== FILTER PRESET TESTS ====================
    
    def test_create_team_preset(self):
        """Test creating a team preset"""
        preset_data = {
            "name": "Test Preset",
            "description": "Test preset for API testing",
            "tags": ["test", "api"],
            "page_type": "gap-analysis",
            "filters": {
                "startDate": "2024-01-01",
                "endDate": "2024-12-31",
                "categories": ["Apparel"],
                "understockThreshold": -10,
                "overstockThreshold": 10
            },
            "is_favorite": False
        }
        success, response_data = self.run_test("Create Team Preset", "POST", "presets", 200, data=preset_data)
        if success and response_data:
            self.test_preset_id = response_data.get('id')
            print(f"   ✅ Created preset with ID: {self.test_preset_id}")
        return success

    def test_get_presets(self):
        """Test getting all presets"""
        return self.run_test("Get All Presets", "GET", "presets", 200)

    def test_get_presets_with_page_type_filter(self):
        """Test getting presets filtered by page type"""
        return self.run_test("Get Presets by Page Type", "GET", "presets?page_type=gap-analysis", 200)

    def test_get_preset_by_id(self):
        """Test getting a specific preset by ID"""
        if hasattr(self, 'test_preset_id') and self.test_preset_id:
            return self.run_test("Get Preset by ID", "GET", f"presets/{self.test_preset_id}", 200)
        else:
            print("⚠️  No preset ID available, skipping get preset by ID test")
            return True

    def test_toggle_preset_favorite(self):
        """Test toggling preset favorite status"""
        if hasattr(self, 'test_preset_id') and self.test_preset_id:
            success, response_data = self.run_test("Toggle Preset Favorite", "PATCH", f"presets/{self.test_preset_id}/favorite", 200)
            if success and response_data:
                print(f"   ✅ Favorite status: {response_data.get('is_favorite')}")
            return success
        else:
            print("⚠️  No preset ID available, skipping toggle favorite test")
            return True

    def test_update_preset(self):
        """Test updating a preset"""
        if hasattr(self, 'test_preset_id') and self.test_preset_id:
            update_data = {
                "name": "Updated Test Preset",
                "description": "Updated description",
                "tags": ["test", "api", "updated"],
                "page_type": "gap-analysis",
                "filters": {
                    "startDate": "2024-02-01",
                    "endDate": "2024-11-30",
                    "categories": ["Apparel", "Footwear"],
                    "understockThreshold": -15,
                    "overstockThreshold": 15
                },
                "is_favorite": True
            }
            return self.run_test("Update Preset", "PUT", f"presets/{self.test_preset_id}", 200, data=update_data)
        else:
            print("⚠️  No preset ID available, skipping update preset test")
            return True

    def test_get_all_tags(self):
        """Test getting all unique tags"""
        return self.run_test("Get All Tags", "GET", "presets/tags/all", 200)

    def test_delete_preset(self):
        """Test deleting a preset"""
        if hasattr(self, 'test_preset_id') and self.test_preset_id:
            return self.run_test("Delete Preset", "DELETE", f"presets/{self.test_preset_id}", 200)
        else:
            print("⚠️  No preset ID available, skipping delete preset test")
            return True

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

        # Filter Preset tests
        print("\n" + "=" * 40)
        print("🔖 Testing Filter Preset Functionality")
        print("=" * 40)
        self.test_create_team_preset()
        self.test_get_presets()
        self.test_get_presets_with_page_type_filter()
        self.test_get_preset_by_id()
        self.test_toggle_preset_favorite()
        self.test_update_preset()
        self.test_get_all_tags()
        self.test_delete_preset()

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