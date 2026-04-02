"""
Iteration 4 Backend Tests - Fashion Retail Gap Analysis
Tests for: BI Dashboards, Core Logics, Gap Analysis, Warehouse Analysis, Preset Import/Export
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBIDashboards:
    """BI Dashboard endpoint tests"""
    
    def test_bi_dashboard_returns_data(self):
        """Test BI dashboard returns proper structure with totals"""
        response = requests.get(f"{BASE_URL}/api/analytics/bi-dashboard")
        assert response.status_code == 200
        data = response.json()
        
        # Check totals structure
        assert "totals" in data
        totals = data["totals"]
        assert "total_revenue" in totals
        assert "total_quantity" in totals
        assert "total_transactions" in totals
        assert "unique_stores" in totals
        print(f"BI Dashboard totals: Revenue={totals['total_revenue']}, Qty={totals['total_quantity']}, Stores={totals['unique_stores']}")
    
    def test_bi_dashboard_monthly_trends(self):
        """Test BI dashboard returns monthly trends"""
        response = requests.get(f"{BASE_URL}/api/analytics/bi-dashboard")
        assert response.status_code == 200
        data = response.json()
        
        assert "monthly_trends" in data
        if data["monthly_trends"]:
            trend = data["monthly_trends"][0]
            assert "month" in trend
            assert "quantity" in trend
            assert "revenue" in trend
            print(f"Monthly trends count: {len(data['monthly_trends'])}")
    
    def test_bi_dashboard_by_store(self):
        """Test BI dashboard returns store data"""
        response = requests.get(f"{BASE_URL}/api/analytics/bi-dashboard")
        assert response.status_code == 200
        data = response.json()
        
        assert "by_store" in data
        if data["by_store"]:
            store = data["by_store"][0]
            assert "store_code" in store
            assert "revenue" in store
            assert "quantity" in store
            print(f"Top store: {store['store_code']} with revenue {store['revenue']}")
    
    def test_bi_dashboard_by_style(self):
        """Test BI dashboard returns style data"""
        response = requests.get(f"{BASE_URL}/api/analytics/bi-dashboard")
        assert response.status_code == 200
        data = response.json()
        
        assert "by_style" in data
        if data["by_style"]:
            style = data["by_style"][0]
            assert "style" in style
            assert "revenue" in style
            print(f"Top style: {style['style']} with revenue {style['revenue']}")
    
    def test_bi_dashboard_by_region(self):
        """Test BI dashboard returns region data"""
        response = requests.get(f"{BASE_URL}/api/analytics/bi-dashboard")
        assert response.status_code == 200
        data = response.json()
        
        assert "by_region" in data
        if data["by_region"]:
            region = data["by_region"][0]
            assert "region" in region
            assert "revenue" in region
            print(f"Regions found: {len(data['by_region'])}")


class TestCoreLogics:
    """Core Logics (TrueROS and Store-Style Ranking) tests"""
    
    def test_ros_analysis_returns_data(self):
        """Test ROS analysis returns proper structure"""
        response = requests.get(f"{BASE_URL}/api/analytics/ros")
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
        assert "data" in data
        
        summary = data["summary"]
        assert "total_styles" in summary
        assert "healthy_count" in summary
        assert "broken_count" in summary
        assert "avg_healthy_ros" in summary
        assert "avg_broken_ros" in summary
        assert "total_sales_loss" in summary
        print(f"ROS Summary: {summary['total_styles']} styles, {summary['healthy_count']} healthy, {summary['broken_count']} broken")
    
    def test_ros_data_has_required_fields(self):
        """Test ROS data items have required fields"""
        response = requests.get(f"{BASE_URL}/api/analytics/ros")
        assert response.status_code == 200
        data = response.json()
        
        if data["data"]:
            item = data["data"][0]
            assert "style" in item
            assert "total_quantity" in item
            assert "total_revenue" in item
            assert "live_days" in item
            assert "ros" in item
            assert "status" in item
            assert item["status"] in ["healthy", "broken"]
            print(f"First style: {item['style']} with ROS {item['ros']} ({item['status']})")
    
    def test_store_style_ranking(self):
        """Test store-style ranking returns proper structure"""
        response = requests.get(f"{BASE_URL}/api/analytics/store-style-ranking")
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
        assert "data" in data
        
        summary = data["summary"]
        assert "total_combinations" in summary
        assert "unique_stores" in summary
        assert "unique_styles" in summary
        print(f"Store-Style: {summary['total_combinations']} combos, {summary['unique_stores']} stores, {summary['unique_styles']} styles")
    
    def test_store_style_data_fields(self):
        """Test store-style data has required fields"""
        response = requests.get(f"{BASE_URL}/api/analytics/store-style-ranking")
        assert response.status_code == 200
        data = response.json()
        
        if data["data"]:
            item = data["data"][0]
            assert "store_code" in item
            assert "style" in item
            assert "quantity" in item
            assert "revenue" in item
            assert "revenue_per_day" in item
            print(f"Top combo: {item['store_code']}-{item['style']} with rev/day {item['revenue_per_day']}")


class TestGapAnalysis:
    """Gap Analysis (NOOS and Size Gap) tests"""
    
    def test_noos_analysis_returns_data(self):
        """Test NOOS analysis returns proper structure"""
        response = requests.get(f"{BASE_URL}/api/analytics/noos")
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
        assert "data" in data
        
        summary = data["summary"]
        assert "total_combinations" in summary
        assert "noos_candidates" in summary
        assert "avg_availability" in summary
        assert "total_revenue" in summary
        print(f"NOOS: {summary['noos_candidates']} candidates out of {summary['total_combinations']} combos")
    
    def test_noos_data_fields(self):
        """Test NOOS data items have required fields"""
        response = requests.get(f"{BASE_URL}/api/analytics/noos")
        assert response.status_code == 200
        data = response.json()
        
        if data["data"]:
            item = data["data"][0]
            assert "store_code" in item
            assert "style" in item
            assert "exposure_days" in item
            assert "availability_pct" in item
            assert "noos_candidate" in item
            print(f"First NOOS item: {item['store_code']}-{item['style']}, candidate={item['noos_candidate']}")
    
    def test_size_gap_analysis_returns_data(self):
        """Test size gap analysis returns proper structure"""
        response = requests.get(f"{BASE_URL}/api/analytics/size-gap")
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
        assert "data" in data
        
        summary = data["summary"]
        assert "overstock" in summary
        assert "understock" in summary
        assert "optimal" in summary
        assert "total_gap" in summary
        print(f"Size Gap: {summary['overstock']} overstock, {summary['understock']} understock, {summary['optimal']} optimal")
    
    def test_size_gap_data_fields(self):
        """Test size gap data items have required fields"""
        response = requests.get(f"{BASE_URL}/api/analytics/size-gap")
        assert response.status_code == 200
        data = response.json()
        
        if data["data"]:
            item = data["data"][0]
            assert "style" in item
            assert "size" in item
            assert "current_qty" in item
            assert "ideal_qty" in item
            assert "gap" in item
            assert "status" in item
            assert item["status"] in ["Overstock", "Understock", "Optimal"]
            print(f"First gap item: {item['style']}-{item['size']}, gap={item['gap']}, status={item['status']}")


class TestWarehouseAnalysis:
    """Warehouse Analysis tests"""
    
    def test_warehouse_analysis_returns_data(self):
        """Test warehouse analysis returns proper structure"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse")
        assert response.status_code == 200
        data = response.json()
        
        assert "totals" in data
        totals = data["totals"]
        assert "total_stock" in totals
        assert "total_skus" in totals
        assert "total_warehouses" in totals
        assert "snapshot_date" in totals
        print(f"Warehouse totals: {totals['total_stock']} stock, {totals['total_skus']} SKUs, {totals['total_warehouses']} warehouses")
    
    def test_warehouse_by_warehouse(self):
        """Test warehouse analysis returns by_warehouse data"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse")
        assert response.status_code == 200
        data = response.json()
        
        assert "by_warehouse" in data
        if data["by_warehouse"]:
            wh = data["by_warehouse"][0]
            assert "warehouse" in wh
            assert "total_qty" in wh
            assert "sku_count" in wh
            print(f"Warehouses found: {len(data['by_warehouse'])}")
    
    def test_warehouse_by_sku(self):
        """Test warehouse analysis returns by_sku data"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse")
        assert response.status_code == 200
        data = response.json()
        
        assert "by_sku" in data
        if data["by_sku"]:
            sku = data["by_sku"][0]
            assert "sku" in sku
            assert "total_qty" in sku
            print(f"Top SKUs count: {len(data['by_sku'])}")
    
    def test_warehouse_online_split(self):
        """Test warehouse analysis returns online/offline split"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse")
        assert response.status_code == 200
        data = response.json()
        
        assert "online_split" in data
        if data["online_split"]:
            split = data["online_split"][0]
            assert "fulfillment_type" in split
            assert "total_qty" in split
            print(f"Online split: {data['online_split']}")
    
    def test_warehouse_trend(self):
        """Test warehouse analysis returns trend data"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse")
        assert response.status_code == 200
        data = response.json()
        
        assert "trend" in data
        if data["trend"]:
            trend = data["trend"][0]
            assert "date" in trend
            assert "total_qty" in trend
            print(f"Trend data points: {len(data['trend'])}")
    
    def test_warehouse_velocity(self):
        """Test warehouse analysis returns velocity data"""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse")
        assert response.status_code == 200
        data = response.json()
        
        assert "velocity" in data
        if data["velocity"]:
            vel = data["velocity"][0]
            assert "sku" in vel
            assert "stock_qty" in vel
            assert "sold_qty" in vel
            assert "days_of_stock" in vel
            print(f"Velocity items: {len(data['velocity'])}")


class TestPresetExportImport:
    """Preset Export/Import tests"""
    
    def test_preset_export(self):
        """Test GET /api/presets/export returns JSON with presets array"""
        response = requests.get(f"{BASE_URL}/api/presets/export")
        assert response.status_code == 200
        data = response.json()
        
        assert "presets" in data
        assert isinstance(data["presets"], list)
        assert "exported_at" in data
        print(f"Export returned {len(data['presets'])} presets")
    
    def test_preset_export_with_page_type(self):
        """Test preset export with page_type filter"""
        response = requests.get(f"{BASE_URL}/api/presets/export?page_type=core-logics")
        assert response.status_code == 200
        data = response.json()
        
        assert "presets" in data
        assert "page_type" in data
        assert data["page_type"] == "core-logics"
        print(f"Export for core-logics: {len(data['presets'])} presets")
    
    def test_preset_import(self):
        """Test POST /api/presets/import accepts JSON with presets array"""
        import_data = {
            "presets": [
                {
                    "name": "TEST_Import_Preset",
                    "page_type": "core-logics",
                    "filters": {"startDate": "2026-01-01"},
                    "tags": ["test", "import"]
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/presets/import", json=import_data)
        assert response.status_code == 200
        data = response.json()
        
        assert "imported" in data
        assert data["imported"] == 1
        print(f"Import result: {data}")
        
        # Cleanup - find and delete the test preset
        presets_response = requests.get(f"{BASE_URL}/api/presets?page_type=core-logics")
        presets = presets_response.json()
        for preset in presets:
            if preset.get("name") == "TEST_Import_Preset":
                requests.delete(f"{BASE_URL}/api/presets/{preset['id']}")
                print(f"Cleaned up test preset: {preset['id']}")


class TestSidebarNavigation:
    """Test sidebar navigation links"""
    
    def test_all_pages_accessible(self):
        """Test all 8 navigation pages are accessible"""
        pages = [
            "/",
            "/upload",
            "/config",
            "/core-logics",
            "/gap-analysis",
            "/bi-dashboards",
            "/warehouse",
            "/chatbot"
        ]
        
        for page in pages:
            response = requests.get(f"{BASE_URL}{page}")
            # Frontend pages return 200 (served by React)
            assert response.status_code == 200, f"Page {page} returned {response.status_code}"
            print(f"Page {page}: OK")


class TestFilterOptions:
    """Test filter options endpoint"""
    
    def test_filter_options_structure(self):
        """Test filter options returns proper structure"""
        response = requests.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200
        data = response.json()
        
        assert "categories" in data
        assert "channels" in data
        assert "regions" in data
        assert "dateRange" in data
        
        assert isinstance(data["categories"], list)
        assert isinstance(data["channels"], list)
        assert isinstance(data["regions"], list)
        
        print(f"Filter options: {len(data['categories'])} categories, {len(data['channels'])} channels, {len(data['regions'])} regions")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
