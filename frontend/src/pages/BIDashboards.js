import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import { RefreshCw, Download } from "lucide-react";
import FilterPanel from "../components/FilterPanel";
import { LineChart, BarChart, AreaChart, DoughnutChart } from "../components/Charts";

const BIDashboards = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeView, setActiveView] = useState("overview");
  const [filterOptions, setFilterOptions] = useState({});
  const [filters, setFilters] = useState({
    startDate: "",
    endDate: "",
    categories: [],
    channels: [],
    regions: []
  });

  const fetchFilterOptions = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/analytics/filter-options`);
      setFilterOptions(response.data);
      if (response.data.dateRange?.min) {
        setFilters(prev => ({
          ...prev,
          startDate: response.data.dateRange.min.split('T')[0],
          endDate: response.data.dateRange.max.split('T')[0]
        }));
      }
    } catch (err) {
      console.error("Error fetching filter options:", err);
    }
  }, []);

  useEffect(() => {
    fetchFilterOptions();
  }, [fetchFilterOptions]);

  const buildQueryParams = () => {
    const params = new URLSearchParams();
    if (filters.startDate) params.append('start_date', filters.startDate);
    if (filters.endDate) params.append('end_date', filters.endDate);
    if (filters.categories?.length) params.append('categories', filters.categories.join(','));
    if (filters.channels?.length) params.append('channels', filters.channels.join(','));
    if (filters.regions?.length) params.append('regions', filters.regions.join(','));
    return params.toString();
  };

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    const queryParams = buildQueryParams();
    
    try {
      const response = await axios.get(`${API}/analytics/bi-dashboard?${queryParams}`);
      if (response.data.error) {
        setError(response.data.error);
      } else {
        setDashboardData(response.data);
      }
    } catch (err) {
      setError("Failed to fetch dashboard data. Please ensure sales data is uploaded.");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const handleApplyFilters = () => {
    fetchData();
  };

  const handleResetFilters = () => {
    setFilters({
      startDate: filterOptions.dateRange?.min?.split('T')[0] || "",
      endDate: filterOptions.dateRange?.max?.split('T')[0] || "",
      categories: [],
      channels: [],
      regions: []
    });
  };

  const formatCurrency = (value) => {
    if (!value) return "₹0";
    if (value >= 10000000) return `₹${(value / 10000000).toFixed(1)}Cr`;
    if (value >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
    if (value >= 1000) return `₹${(value / 1000).toFixed(0)}K`;
    return `₹${Math.round(value)}`;
  };

  const formatNumber = (value) => {
    if (!value) return "0";
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(0)}K`;
    return Math.round(value).toString();
  };

  const views = [
    { key: "overview", label: "Overview" },
    { key: "stores", label: "By Store" },
    { key: "styles", label: "By Style" },
    { key: "trends", label: "Trends" },
  ];

  const handleExport = () => {
    if (!dashboardData) return;
    
    let data = [];
    if (activeView === "stores") data = dashboardData.by_store;
    else if (activeView === "styles") data = dashboardData.by_style;
    else if (activeView === "trends") data = dashboardData.monthly_trends;
    else return;

    if (!data || data.length === 0) return;
    
    const csv = [
      Object.keys(data[0]).join(','),
      ...data.map(row => Object.values(row).join(','))
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bi_dashboard_${activeView}.csv`;
    a.click();
  };

  return (
    <div className="animate-fade-in-up" data-testid="bi-dashboards-page">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
            BI Dashboards
          </h1>
          <p className="text-slate-500">
            Business intelligence metrics and performance trends
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            data-testid="refresh-bi-btn"
            onClick={fetchData}
            disabled={loading}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button
            data-testid="export-bi-btn"
            onClick={handleExport}
            className="btn-primary flex items-center gap-2"
          >
            <Download size={16} />
            Export
          </button>
        </div>
      </div>

      {/* Filter Panel */}
      <FilterPanel
        filters={filters}
        filterOptions={filterOptions}
        onFilterChange={handleFilterChange}
        onApply={handleApplyFilters}
        onReset={handleResetFilters}
        pageType="bi-dashboards"
      />

      {/* View Selector */}
      <div className="tabs">
        {views.map((view) => (
          <button
            key={view.key}
            data-testid={`bi-view-${view.key}`}
            className={`tab ${activeView === view.key ? 'active' : ''}`}
            onClick={() => setActiveView(view.key)}
          >
            {view.label}
          </button>
        ))}
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-amber-50 border border-amber-200 p-6 mb-6 rounded">
          <p className="text-amber-800">{error}</p>
          <p className="text-sm text-amber-600 mt-1">
            Please upload the required data files from the Data Upload page.
          </p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="spinner" />
        </div>
      )}

      {/* Dashboard Content */}
      {dashboardData && !loading && (
        <>
          {/* Overview View */}
          {activeView === "overview" && (
            <div data-testid="bi-overview-section">
              {/* KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div className="metric-card">
                  <span className="metric-label">Total Revenue</span>
                  <span className="metric-value">{formatCurrency(dashboardData.totals?.total_revenue)}</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Units Sold</span>
                  <span className="metric-value">{formatNumber(dashboardData.totals?.total_quantity)}</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Transactions</span>
                  <span className="metric-value">{formatNumber(dashboardData.totals?.total_transactions)}</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Active Stores</span>
                  <span className="metric-value">{dashboardData.totals?.unique_stores || 0}</span>
                </div>
              </div>

              {/* Charts Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                {/* Revenue Trend Chart */}
                {dashboardData.monthly_trends?.length > 0 && (
                  <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
                    <h3 className="font-semibold text-slate-900 mb-4">Revenue Trend</h3>
                    <AreaChart
                      labels={dashboardData.monthly_trends.map(d => d.month)}
                      datasets={[{
                        label: 'Revenue',
                        data: dashboardData.monthly_trends.map(d => d.revenue),
                        color: '#0176D3'
                      }]}
                      height={280}
                      formatValue={formatCurrency}
                      showLegend={false}
                    />
                  </div>
                )}

                {/* Units Sold Chart */}
                {dashboardData.monthly_trends?.length > 0 && (
                  <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
                    <h3 className="font-semibold text-slate-900 mb-4">Units Sold</h3>
                    <BarChart
                      labels={dashboardData.monthly_trends.map(d => d.month)}
                      datasets={[{
                        label: 'Quantity',
                        data: dashboardData.monthly_trends.map(d => d.quantity),
                        color: '#2E844A'
                      }]}
                      height={280}
                      formatValue={formatNumber}
                      showLegend={false}
                    />
                  </div>
                )}

                {/* Top Stores Chart */}
                {dashboardData.by_store?.length > 0 && (
                  <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
                    <h3 className="font-semibold text-slate-900 mb-4">Top 10 Stores by Revenue</h3>
                    <BarChart
                      labels={dashboardData.by_store.slice(0, 10).map(d => d.store_code)}
                      datasets={[{
                        label: 'Revenue',
                        data: dashboardData.by_store.slice(0, 10).map(d => d.revenue),
                        color: '#0176D3'
                      }]}
                      horizontal={true}
                      height={300}
                      formatValue={formatCurrency}
                      showLegend={false}
                    />
                  </div>
                )}

                {/* Top Styles Chart */}
                {dashboardData.by_style?.length > 0 && (
                  <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
                    <h3 className="font-semibold text-slate-900 mb-4">Top 10 Styles by Revenue</h3>
                    <BarChart
                      labels={dashboardData.by_style.slice(0, 10).map(d => d.style)}
                      datasets={[{
                        label: 'Revenue',
                        data: dashboardData.by_style.slice(0, 10).map(d => d.revenue),
                        color: '#DD7A01'
                      }]}
                      horizontal={true}
                      height={300}
                      formatValue={formatCurrency}
                      showLegend={false}
                    />
                  </div>
                )}
              </div>

              {/* Region Distribution */}
              {dashboardData.by_region?.length > 0 && (
                <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
                  <h3 className="font-semibold text-slate-900 mb-4">Revenue by Region</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <DoughnutChart
                      labels={dashboardData.by_region.map(d => d.region)}
                      data={dashboardData.by_region.map(d => d.revenue)}
                      height={280}
                      formatValue={formatCurrency}
                    />
                    <div className="overflow-x-auto">
                      <table className="data-table w-full">
                        <thead>
                          <tr>
                            <th>Region</th>
                            <th>Revenue</th>
                            <th>Quantity</th>
                          </tr>
                        </thead>
                        <tbody>
                          {dashboardData.by_region.map((row, i) => (
                            <tr key={i}>
                              <td className="font-medium text-slate-900">{row.region}</td>
                              <td>{formatCurrency(row.revenue)}</td>
                              <td>{formatNumber(row.quantity)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Stores View */}
          {activeView === "stores" && (
            <div data-testid="bi-stores-section">
              {/* Store Performance Chart */}
              {dashboardData.by_store?.length > 0 && (
                <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-6">
                  <h3 className="font-semibold text-slate-900 mb-4">Store Performance Comparison</h3>
                  <BarChart
                    labels={dashboardData.by_store.slice(0, 15).map(d => d.store_code)}
                    datasets={[
                      {
                        label: 'Revenue',
                        data: dashboardData.by_store.slice(0, 15).map(d => d.revenue),
                        color: '#0176D3'
                      }
                    ]}
                    height={350}
                    formatValue={formatCurrency}
                  />
                </div>
              )}

              {/* Store Table */}
              <div className="bg-white border border-slate-200 rounded shadow-sm">
                <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                  <h3 className="font-semibold text-slate-900">Store Performance</h3>
                  <span className="text-sm text-slate-500">
                    {dashboardData.by_store?.length || 0} stores
                  </span>
                </div>
                <div className="overflow-x-auto">
                  <table className="data-table w-full">
                    <thead>
                      <tr>
                        <th>Store Code</th>
                        <th>Quantity Sold</th>
                        <th>Revenue</th>
                        <th>ASP</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboardData.by_store?.map((row, i) => (
                        <tr key={i}>
                          <td className="font-medium text-slate-900">{row.store_code}</td>
                          <td>{formatNumber(row.quantity)}</td>
                          <td>{formatCurrency(row.revenue)}</td>
                          <td>{formatCurrency(row.quantity > 0 ? row.revenue / row.quantity : 0)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Styles View */}
          {activeView === "styles" && (
            <div data-testid="bi-styles-section">
              {/* Style Performance Chart */}
              {dashboardData.by_style?.length > 0 && (
                <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-6">
                  <h3 className="font-semibold text-slate-900 mb-4">Style Performance</h3>
                  <BarChart
                    labels={dashboardData.by_style.slice(0, 15).map(d => d.style)}
                    datasets={[
                      {
                        label: 'Revenue',
                        data: dashboardData.by_style.slice(0, 15).map(d => d.revenue),
                        color: '#DD7A01'
                      }
                    ]}
                    height={350}
                    formatValue={formatCurrency}
                  />
                </div>
              )}

              {/* Style Table */}
              <div className="bg-white border border-slate-200 rounded shadow-sm">
                <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                  <h3 className="font-semibold text-slate-900">Style Performance</h3>
                  <span className="text-sm text-slate-500">
                    {dashboardData.by_style?.length || 0} styles
                  </span>
                </div>
                <div className="overflow-x-auto">
                  <table className="data-table w-full">
                    <thead>
                      <tr>
                        <th>Style</th>
                        <th>Quantity Sold</th>
                        <th>Revenue</th>
                        <th>ASP</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboardData.by_style?.map((row, i) => (
                        <tr key={i}>
                          <td className="font-medium text-slate-900">{row.style}</td>
                          <td>{formatNumber(row.quantity)}</td>
                          <td>{formatCurrency(row.revenue)}</td>
                          <td>{formatCurrency(row.quantity > 0 ? row.revenue / row.quantity : 0)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Trends View */}
          {activeView === "trends" && (
            <div data-testid="bi-trends-section">
              {dashboardData.monthly_trends?.length > 0 && (
                <>
                  {/* Revenue vs Quantity Dual Axis */}
                  <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-6">
                    <h3 className="font-semibold text-slate-900 mb-4">Revenue & Quantity Trends</h3>
                    <LineChart
                      labels={dashboardData.monthly_trends.map(d => d.month)}
                      datasets={[
                        {
                          label: 'Revenue',
                          data: dashboardData.monthly_trends.map(d => d.revenue),
                          color: '#0176D3'
                        },
                        {
                          label: 'Quantity (scaled)',
                          data: dashboardData.monthly_trends.map(d => d.quantity * 100),
                          color: '#2E844A'
                        }
                      ]}
                      height={350}
                      formatValue={formatCurrency}
                    />
                  </div>

                  {/* ASP Trend */}
                  <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-6">
                    <h3 className="font-semibold text-slate-900 mb-4">Average Selling Price (ASP) Trend</h3>
                    <AreaChart
                      labels={dashboardData.monthly_trends.map(d => d.month)}
                      datasets={[{
                        label: 'ASP',
                        data: dashboardData.monthly_trends.map(d => d.asp),
                        color: '#706E6B'
                      }]}
                      height={280}
                      formatValue={formatCurrency}
                      showLegend={false}
                    />
                  </div>

                  {/* Trends Table */}
                  <div className="bg-white border border-slate-200 rounded shadow-sm">
                    <div className="p-4 border-b border-slate-100">
                      <h3 className="font-semibold text-slate-900">Monthly Trends Data</h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="data-table w-full">
                        <thead>
                          <tr>
                            <th>Month</th>
                            <th>Quantity</th>
                            <th>Revenue</th>
                            <th>ASP</th>
                          </tr>
                        </thead>
                        <tbody>
                          {dashboardData.monthly_trends?.map((row, i) => (
                            <tr key={i}>
                              <td className="font-medium text-slate-900">{row.month}</td>
                              <td>{formatNumber(row.quantity)}</td>
                              <td>{formatCurrency(row.revenue)}</td>
                              <td>{formatCurrency(row.asp)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!loading && !error && !dashboardData?.totals && (
        <div className="bg-slate-50 border border-slate-200 p-12 text-center rounded">
          <p className="text-slate-500 mb-2">No data available</p>
          <p className="text-sm text-slate-400">
            Upload sales data to see BI dashboards
          </p>
        </div>
      )}
    </div>
  );
};

export default BIDashboards;
