import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { RefreshCw, Download, TrendingUp, TrendingDown, Minus } from "lucide-react";

const CoreLogics = () => {
  const [activeTab, setActiveTab] = useState("ros");
  const [rosData, setRosData] = useState(null);
  const [storeStyleData, setStoreStyleData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      if (activeTab === "ros") {
        const response = await axios.get(`${API}/analytics/ros`);
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
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

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
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-4xl font-light tracking-tight text-neutral-900 mb-2">
            Increff Core Logics
          </h1>
          <p className="text-neutral-500">
            Advanced analytics powered by Increff algorithms
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            data-testid="refresh-btn"
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 text-sm border border-neutral-200 hover:border-neutral-400 transition-colors"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button
            data-testid="export-btn"
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-neutral-900 text-white hover:bg-neutral-800 transition-colors"
          >
            <Download size={16} />
            Export CSV
          </button>
        </div>
      </div>

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
        <div className="bg-amber-50 border border-amber-200 p-6 mb-6">
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
              <span className="metric-value text-emerald-600">{rosData.summary?.healthy_count || 0}</span>
              <span className="text-sm text-neutral-500">
                Avg ROS: {rosData.summary?.avg_healthy_ros?.toFixed(2) || 0}
              </span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Broken Styles</span>
              <span className="metric-value text-red-600">{rosData.summary?.broken_count || 0}</span>
              <span className="text-sm text-neutral-500">
                Avg ROS: {rosData.summary?.avg_broken_ros?.toFixed(2) || 0}
              </span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Total Sales Loss</span>
              <span className="metric-value text-amber-600">
                {formatNumber(rosData.summary?.total_sales_loss || 0)}
              </span>
              <span className="text-sm text-neutral-500">units</span>
            </div>
          </div>

          {/* Data Table */}
          <div className="bg-white border border-neutral-200">
            <div className="p-4 border-b border-neutral-100">
              <h3 className="font-medium text-neutral-900">Style Details</h3>
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
                      <td className="font-medium text-neutral-900">{row.style}</td>
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

          {/* Data Table */}
          <div className="bg-white border border-neutral-200">
            <div className="p-4 border-b border-neutral-100">
              <h3 className="font-medium text-neutral-900">Store-Style Performance</h3>
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
                      <td className="font-medium text-neutral-900">{row.store_code}</td>
                      <td>{row.style}</td>
                      <td>{formatNumber(row.quantity)}</td>
                      <td>{formatCurrency(row.revenue)}</td>
                      <td>{row.days_on_sale}</td>
                      <td className="font-medium">{formatCurrency(row.revenue_per_day)}</td>
                      <td>
                        <span className="inline-flex items-center gap-1">
                          {row.store_rank_for_style <= 3 ? (
                            <TrendingUp size={14} className="text-emerald-500" />
                          ) : row.store_rank_for_style <= 10 ? (
                            <Minus size={14} className="text-neutral-400" />
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
        <div className="bg-neutral-50 border border-neutral-200 p-12 text-center">
          <p className="text-neutral-500 mb-2">No data available</p>
          <p className="text-sm text-neutral-400">
            Upload the required files to see analytics
          </p>
        </div>
      )}
    </div>
  );
};

export default CoreLogics;
