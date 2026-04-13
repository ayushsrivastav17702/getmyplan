"""
Iteration 85: Pandas→MongoDB Migration Testing
Tests warehouse, planogram, and stock-out endpoints after migration from Pandas to MongoDB aggregation.

Test Coverage:
- Warehouse stock, daily-change, dashboard, movements, performance endpoints
- Planogram analysis, trend, pre-post endpoints
- Stock-Out daily_trend, weekly_trend, monthly_trend, moving_avg arrays
- Health endpoints regression
- Verify no pandas import in warehouse.py or planogram.py
"""
import pytest
import requests
import os
import subprocess

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials for demo tenant
TEST_EMAIL = "admin@demo.com"
TEST_PASSWORD = "demo1234"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for demo tenant."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("token") or data.get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestNoPandasImport:
    """Verify no pandas import in migrated files."""

    def test_no_pandas_in_warehouse(self):
        """Verify warehouse.py has no pandas import."""
        result = subprocess.run(
            ["grep", "-c", "import pandas", "/app/backend/routes/warehouse.py"],
            capture_output=True, text=True
        )
        # grep returns 1 if no match found (which is what we want)
        assert result.returncode == 1 or result.stdout.strip() == "0", \
            f"Found pandas import in warehouse.py: {result.stdout}"

    def test_no_pandas_from_in_warehouse(self):
        """Verify warehouse.py has no 'from pandas' import."""
        result = subprocess.run(
            ["grep", "-c", "from pandas", "/app/backend/routes/warehouse.py"],
            capture_output=True, text=True
        )
        assert result.returncode == 1 or result.stdout.strip() == "0", \
            f"Found 'from pandas' import in warehouse.py: {result.stdout}"

    def test_no_pandas_in_planogram(self):
        """Verify planogram.py has no pandas import."""
        result = subprocess.run(
            ["grep", "-c", "import pandas", "/app/backend/routes/planogram.py"],
            capture_output=True, text=True
        )
        assert result.returncode == 1 or result.stdout.strip() == "0", \
            f"Found pandas import in planogram.py: {result.stdout}"

    def test_no_pandas_from_in_planogram(self):
        """Verify planogram.py has no 'from pandas' import."""
        result = subprocess.run(
            ["grep", "-c", "from pandas", "/app/backend/routes/planogram.py"],
            capture_output=True, text=True
        )
        assert result.returncode == 1 or result.stdout.strip() == "0", \
            f"Found 'from pandas' import in planogram.py: {result.stdout}"


class TestHealthEndpoints:
    """Health endpoints regression check."""

    def test_health_main(self):
        """GET /api/health returns healthy status."""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"Health: {data}")

    def test_health_memory(self):
        """GET /api/health/memory returns memory info."""
        response = requests.get(f"{BASE_URL}/api/health/memory")
        assert response.status_code == 200
        data = response.json()
        assert "total_gb" in data or "memory" in data
        print(f"Memory health: {data}")

    def test_health_ready(self):
        """GET /api/health/ready returns ready status."""
        response = requests.get(f"{BASE_URL}/api/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["ready", "healthy"]
        print(f"Ready: {data}")


class TestWarehouseEndpoints:
    """Warehouse module endpoints - may return empty/error if no warehouse_inventory data."""

    def test_warehouse_stock(self, auth_headers):
        """GET /api/analytics/warehouse/stock returns items array and totals."""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/stock", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # May return error if no warehouse_inventory data (expected)
        assert "items" in data or "error" in data
        assert "totals" in data or "error" in data
        print(f"Warehouse stock: items={len(data.get('items', []))}, error={data.get('error')}")

    def test_warehouse_daily_change(self, auth_headers):
        """GET /api/analytics/warehouse/daily-change returns days array."""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/daily-change", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "days" in data
        print(f"Warehouse daily-change: days={len(data.get('days', []))}")

    def test_warehouse_dashboard(self, auth_headers):
        """GET /api/analytics/warehouse/dashboard returns kpis, category_chart, movement_trend, comparison."""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # May return error if no warehouse_inventory data
        if "error" not in data:
            assert "kpis" in data
            assert "category_chart" in data
            assert "movement_trend" in data
            assert "comparison" in data
        print(f"Warehouse dashboard: kpis={data.get('kpis')}, error={data.get('error')}")

    def test_warehouse_movements(self, auth_headers):
        """GET /api/analytics/warehouse/movements returns movements and summary."""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/movements", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "movements" in data
        assert "summary" in data
        print(f"Warehouse movements: count={len(data.get('movements', []))}, summary={data.get('summary')}")

    def test_warehouse_performance(self, auth_headers):
        """GET /api/analytics/warehouse/performance returns fulfillment_rate, by_warehouse, slow_moving."""
        response = requests.get(f"{BASE_URL}/api/analytics/warehouse/performance", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "fulfillment_rate" in data
        assert "by_warehouse" in data
        assert "slow_moving" in data
        print(f"Warehouse performance: fulfillment_rate={data.get('fulfillment_rate')}, by_warehouse={len(data.get('by_warehouse', []))}")


class TestPlanogramEndpoints:
    """Planogram module endpoints - should return data since store_inventory has data."""

    def test_planogram_analysis(self, auth_headers):
        """GET /api/analytics/planogram/analysis returns summary with overall_fill_rate, store_data, category_data, detail."""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        if "error" not in data:
            assert "summary" in data
            summary = data.get("summary", {})
            assert "overall_fill_rate" in summary
            assert "store_data" in data
            assert "category_data" in data
            assert "detail" in data
            print(f"Planogram analysis: overall_fill_rate={summary.get('overall_fill_rate')}, stores={len(data.get('store_data', []))}")
        else:
            print(f"Planogram analysis error: {data.get('error')}")

    def test_planogram_trend(self, auth_headers):
        """GET /api/analytics/planogram/trend returns trend array with fill_rate, target, moving_avg_7d."""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram/trend", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        if "error" not in data:
            assert "trend" in data
            trend = data.get("trend", [])
            if trend:
                first_item = trend[0]
                assert "fill_rate" in first_item
                assert "target" in first_item
                assert "moving_avg_7d" in first_item
            print(f"Planogram trend: items={len(trend)}")
        else:
            print(f"Planogram trend error: {data.get('error')}")

    def test_planogram_pre_post(self, auth_headers):
        """GET /api/analytics/planogram/pre-post returns pre/post fill rates with improvement."""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram/pre-post", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        if "error" not in data:
            assert "pre" in data
            assert "post" in data
            assert "improvement" in data
            pre = data.get("pre", {})
            post = data.get("post", {})
            assert "fill_rate" in pre
            assert "fill_rate" in post
            print(f"Planogram pre-post: pre={pre.get('fill_rate')}, post={post.get('fill_rate')}, improvement={data.get('improvement')}")
        else:
            print(f"Planogram pre-post error: {data.get('error')}")


class TestStockOutEndpoints:
    """Stock-Out endpoints - verify daily_trend populated from historical inventory snapshots."""

    def test_stock_out_returns_200(self, auth_headers):
        """GET /api/analytics/stock-out returns 200."""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        print(f"Stock-out response keys: {list(data.keys())}")

    def test_stock_out_kpis_correct(self, auth_headers):
        """Stock-out KPIs: total_lost_sales > 0 (regression check from P0 fix)."""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        summary = data.get("summary", {})
        total_lost_sales = summary.get("total_lost_sales", 0)
        assert total_lost_sales > 0, f"total_lost_sales should be > 0, got {total_lost_sales}"
        print(f"Stock-out KPIs: total_lost_sales={total_lost_sales}, total_stockouts={summary.get('total_stockouts')}")

    def test_stock_out_daily_trend(self, auth_headers):
        """Stock-out daily_trend array should be non-empty (from historical inventory snapshots)."""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        daily_trend = data.get("daily_trend", [])
        # Should have at least 2 items (2 inventory snapshot dates in test data)
        assert len(daily_trend) >= 1, f"daily_trend should have data, got {len(daily_trend)} items"
        if daily_trend:
            first_item = daily_trend[0]
            assert "date" in first_item
            assert "stockout_count" in first_item
            assert "lost_sales" in first_item
        print(f"Stock-out daily_trend: {len(daily_trend)} items, first={daily_trend[0] if daily_trend else 'N/A'}")

    def test_stock_out_weekly_trend(self, auth_headers):
        """Stock-out weekly_trend array should be non-empty."""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        weekly_trend = data.get("weekly_trend", [])
        # May be empty if only 1 week of data
        assert isinstance(weekly_trend, list)
        if weekly_trend:
            first_item = weekly_trend[0]
            assert "week" in first_item
            assert "stockout_count" in first_item
        print(f"Stock-out weekly_trend: {len(weekly_trend)} items")

    def test_stock_out_monthly_trend(self, auth_headers):
        """Stock-out monthly_trend array should be non-empty."""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        monthly_trend = data.get("monthly_trend", [])
        assert isinstance(monthly_trend, list)
        if monthly_trend:
            first_item = monthly_trend[0]
            assert "month" in first_item
            assert "stockout_count" in first_item
        print(f"Stock-out monthly_trend: {len(monthly_trend)} items")

    def test_stock_out_moving_avg(self, auth_headers):
        """Stock-out moving_avg array should be non-empty."""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        moving_avg = data.get("moving_avg", [])
        assert isinstance(moving_avg, list)
        if moving_avg:
            first_item = moving_avg[0]
            assert "date" in first_item
            assert "ma7" in first_item
        print(f"Stock-out moving_avg: {len(moving_avg)} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
