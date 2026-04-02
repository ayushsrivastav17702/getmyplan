import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import { RefreshCw, Download, TrendingUp, TrendingDown, Minus } from "lucide-react";
import FilterPanel from "../components/FilterPanel";
import { BarChart, DoughnutChart } from "../components/Charts";

const CoreLogics = () => {
  const [activeTab, setActiveTab] = useState("ros");
  const [rosData, setRosData] = useState(null);
  const [storeStyleData, setStoreStyleData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filterOptions, setFilterOptions] = useState({});
  const [filters, setFilters] = useState({
    startDate: "",
    endDate: "",
    categories: [],
    channels: [],
    regions: [],
    minSize: 0,
    minSizePercent: 0
  });

  const fetchFilterOptions = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/analytics/filter-options`);
      setFilterOptions(response.data);
      // Set default dates if available
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
    if (filters.minSize > 0) params.append('min_size', filters.minSize);
    if (filters.minSizePercent > 0) params.append('min_size_percent', filters.minSizePercent);
    return params.toString();
  };

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    const queryParams = buildQueryParams();
    
    try {
      if (activeTab === "ros") {
        const response = await axios.get(`${API}/analytics/ros?${queryParams}`);
        if (response.data.error) {
          setError(response.data.error);
        } else {
          setRosData(response.data);
        }
      } else if (activeTab === "store-style") {
        const response = await axios.get(`${API}/analytics/store-style-ranking`);
        if (response.data.error) {
          setError(response.data.error);
        } else {
          setStoreStyleData(response.data);
        }
      }
    } catch (err) {
      setError("Failed to fetch data. Please ensure required files are uploaded.");
    } finally {
      setLoading(false);
    }
  }, [activeTab, filters]);

  useEffect(() => {
    fetchData();
  }, [activeTab]);

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
      regions: [],
      minSize: 0,
      minSizePercent: 0
    });
  };

  const tabs = [
    { key: "ros", label: "TrueROS Analysis" },
    { key: "store-style", label: "Store-Style Ranking" },
  ];

  const formatCurrency = (value) => {
    if (!value) return "₹0";
    if (value >= 1000000) return `₹${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `₹${(value / 1000).toFixed(0)}K`;
    return `₹${Math.round(value)}`;
  };

  const formatNumber = (value) => {
    if (!value) return "0";
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(0)}K`;
    return Math.round(value).toString();
  };

  const handleExport = () => {
    const data = activeTab === "ros" ? rosData?.data : storeStyleData?.data;
    if (!data || data.length === 0) return;
    
    const csv = [
      Object.keys(data[0]).join(','),
      ...data.map(row => Object.values(row).join(','))
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${activeTab}_analysis.csv`;
    a.click();
  };

  return (
    <div className="animate-fade-in-up" data-testid="core-logics-page">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
            Increff Core Logics
          </h1>
          <p className="text-slate-500">
            Advanced analytics powered by Increff algorithms
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            data-testid="refresh-btn"
            onClick={fetchData}
            disabled={loading}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button
            data-testid="export-btn"
            onClick={handleExport}
            className="btn-primary flex items-center gap-2"
          >
            <Download size={16} />
            Export CSV
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
        pageType="core-logics"
      />

      {/* Tabs */}
      <div className="tabs">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            data-testid={`tab-${tab.key}`}
            className={`tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
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

      {/* ROS Analysis */}
      {activeTab === "ros" && rosData && !loading && (
        <div data-testid="ros-analysis-section">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="metric-card">
              <span className="metric-label">Total Styles</span>
              <span className="metric-value">{rosData.summary?.total_styles || 0}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Healthy Styles</span>
              <span className="metric-value text-green-600">{rosData.summary?.healthy_count || 0}</span>
              <span className="text-sm text-slate-500">
                Avg ROS: {rosData.summary?.avg_healthy_ros?.toFixed(2) || 0}
              </span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Broken Styles</span>
              <span className="metric-value text-red-600">{rosData.summary?.broken_count || 0}</span>
              <span className="text-sm text-slate-500">
                Avg ROS: {rosData.summary?.avg_broken_ros?.toFixed(2) || 0}
              </span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Total Sales Loss</span>
              <span className="metric-value text-amber-600">
                {formatNumber(rosData.summary?.total_sales_loss || 0)}
              </span>
              <span className="text-sm text-slate-500">units</span>
            </div>
          </div>

          {/* ROS Charts */}
          {rosData.data?.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
                <h3 className="font-semibold text-slate-900 mb-4">Healthy vs Broken Distribution</h3>
                <DoughnutChart
                  labels={['Healthy', 'Broken']}
                  data={[
                    rosData.summary?.healthy_count || 0,
                    rosData.summary?.broken_count || 0
                  ]}
                  height={260}
                />
              </div>
              <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
                <h3 className="font-semibold text-slate-900 mb-4">Top 10 Styles by ROS</h3>
                <BarChart
                  labels={rosData.data.slice(0, 10).map(d => d.style)}
                  datasets={[{
                    label: 'ROS',
                    data: rosData.data.slice(0, 10).map(d => d.ros),
                    colors: rosData.data.slice(0, 10).map(d => d.status === 'healthy' ? '#2E844A' : '#EA001E')
                  }]}
                  horizontal={true}
                  height={260}
                  showLegend={false}
                />
              </div>
            </div>
          )}

          {/* Data Table */}
          <div className="bg-white border border-slate-200 rounded shadow-sm">
            <div className="p-4 border-b border-slate-100">
              <h3 className="font-semibold text-slate-900">Style Details</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="data-table w-full">
                <thead>
                  <tr>
                    <th>Style</th>
                    <th>Total Qty</th>
                    <th>Revenue</th>
                    <th>Live Days</th>
                    <th>ROS</th>
                    <th>Status</th>
                    <th>Sales Loss</th>
                  </tr>
                </thead>
                <tbody>
                  {rosData.data?.slice(0, 25).map((row, i) => (
                    <tr key={i}>
                      <td className="font-medium text-slate-900">{row.style}</td>
                      <td>{formatNumber(row.total_quantity)}</td>
                      <td>{formatCurrency(row.total_revenue)}</td>
                      <td>{row.live_days}</td>
                      <td className="font-medium">{row.ros?.toFixed(2)}</td>
                      <td>
                        <span className={`badge ${row.status === 'healthy' ? 'badge-healthy' : 'badge-broken'}`}>
                          {row.status}
                        </span>
                      </td>
                      <td className="text-amber-600">{formatNumber(row.sales_loss)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Store-Style Ranking */}
      {activeTab === "store-style" && storeStyleData && !loading && (
        <div data-testid="store-style-section">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
            <div className="metric-card">
              <span className="metric-label">Combinations</span>
              <span className="metric-value">{formatNumber(storeStyleData.summary?.total_combinations)}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Unique Stores</span>
              <span className="metric-value">{storeStyleData.summary?.unique_stores || 0}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Unique Styles</span>
              <span className="metric-value">{storeStyleData.summary?.unique_styles || 0}</span>
            </div>
          </div>

          {/* Store-Style Charts */}
          {storeStyleData.data?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8">
              <h3 className="font-semibold text-slate-900 mb-4">Top 10 Combos by Revenue/Day</h3>
              <BarChart
                labels={storeStyleData.data.slice(0, 10).map(d => `${d.store_code}-${d.style}`)}
                datasets={[{
                  label: 'Rev/Day',
                  data: storeStyleData.data.slice(0, 10).map(d => d.revenue_per_day),
                  color: '#0176D3'
                }]}
                height={300}
                formatValue={formatCurrency}
                showLegend={false}
              />
            </div>
          )}

          {/* Data Table */}
          <div className="bg-white border border-slate-200 rounded shadow-sm">
            <div className="p-4 border-b border-slate-100">
              <h3 className="font-semibold text-slate-900">Store-Style Performance</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="data-table w-full">
                <thead>
                  <tr>
                    <th>Store</th>
                    <th>Style</th>
                    <th>Quantity</th>
                    <th>Revenue</th>
                    <th>Days</th>
                    <th>Rev/Day</th>
                    <th>Store Rank</th>
                    <th>Style Rank</th>
                  </tr>
                </thead>
                <tbody>
                  {storeStyleData.data?.slice(0, 25).map((row, i) => (
                    <tr key={i}>
                      <td className="font-medium text-slate-900">{row.store_code}</td>
                      <td>{row.style}</td>
                      <td>{formatNumber(row.quantity)}</td>
                      <td>{formatCurrency(row.revenue)}</td>
                      <td>{row.days_on_sale}</td>
                      <td className="font-medium">{formatCurrency(row.revenue_per_day)}</td>
                      <td>
                        <span className="inline-flex items-center gap-1">
                          {row.store_rank_for_style <= 3 ? (
                            <TrendingUp size={14} className="text-green-500" />
                          ) : row.store_rank_for_style <= 10 ? (
                            <Minus size={14} className="text-slate-400" />
                          ) : (
                            <TrendingDown size={14} className="text-red-400" />
                          )}
                          #{Math.round(row.store_rank_for_style)}
                        </span>
                      </td>
                      <td>#{Math.round(row.style_rank_for_store)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && ((activeTab === "ros" && !rosData?.data?.length) || (activeTab === "store-style" && !storeStyleData?.data?.length)) && (
        <div className="bg-slate-50 border border-slate-200 p-12 text-center rounded">
          <p className="text-slate-500 mb-2">No data available</p>
          <p className="text-sm text-slate-400">
            Upload the required files to see analytics
          </p>
        </div>
      )}
    </div>
  );
};

export default CoreLogics;
