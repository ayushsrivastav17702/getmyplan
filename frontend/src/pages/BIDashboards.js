import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { RefreshCw, Download } from "lucide-react";

const BIDashboards = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeView, setActiveView] = useState("overview");

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API}/analytics/bi-dashboard`);
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
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-4xl font-light tracking-tight text-neutral-900 mb-2">
            BI Dashboards
          </h1>
          <p className="text-neutral-500">
            Business intelligence metrics and performance trends
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            data-testid="refresh-bi-btn"
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 text-sm border border-neutral-200 hover:border-neutral-400 transition-colors"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button
            data-testid="export-bi-btn"
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-neutral-900 text-white hover:bg-neutral-800 transition-colors"
          >
            <Download size={16} />
            Export
          </button>
        </div>
      </div>

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

              {/* Monthly Trends Table */}
              {dashboardData.monthly_trends?.length > 0 && (
                <div className="bg-white border border-neutral-200 mb-6">
                  <div className="p-4 border-b border-neutral-100">
                    <h3 className="font-medium text-neutral-900">Monthly Trends</h3>
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
                        {dashboardData.monthly_trends.map((row, i) => (
                          <tr key={i}>
                            <td className="font-medium text-neutral-900">{row.month}</td>
                            <td>{formatNumber(row.quantity)}</td>
                            <td>{formatCurrency(row.revenue)}</td>
                            <td>{formatCurrency(row.asp)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Top Stores & Styles Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Top Stores */}
                {dashboardData.by_store?.length > 0 && (
                  <div className="bg-white border border-neutral-200">
                    <div className="p-4 border-b border-neutral-100">
                      <h3 className="font-medium text-neutral-900">Top 10 Stores by Revenue</h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="data-table w-full">
                        <thead>
                          <tr>
                            <th>Store</th>
                            <th>Revenue</th>
                            <th>Qty</th>
                          </tr>
                        </thead>
                        <tbody>
                          {dashboardData.by_store.slice(0, 10).map((row, i) => (
                            <tr key={i}>
                              <td className="font-medium text-neutral-900">{row.store_code}</td>
                              <td>{formatCurrency(row.revenue)}</td>
                              <td>{formatNumber(row.quantity)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Top Styles */}
                {dashboardData.by_style?.length > 0 && (
                  <div className="bg-white border border-neutral-200">
                    <div className="p-4 border-b border-neutral-100">
                      <h3 className="font-medium text-neutral-900">Top 10 Styles by Revenue</h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="data-table w-full">
                        <thead>
                          <tr>
                            <th>Style</th>
                            <th>Revenue</th>
                            <th>Qty</th>
                          </tr>
                        </thead>
                        <tbody>
                          {dashboardData.by_style.slice(0, 10).map((row, i) => (
                            <tr key={i}>
                              <td className="font-medium text-neutral-900">{row.style}</td>
                              <td>{formatCurrency(row.revenue)}</td>
                              <td>{formatNumber(row.quantity)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Stores View */}
          {activeView === "stores" && (
            <div data-testid="bi-stores-section">
              <div className="bg-white border border-neutral-200">
                <div className="p-4 border-b border-neutral-100 flex items-center justify-between">
                  <h3 className="font-medium text-neutral-900">Store Performance</h3>
                  <span className="text-sm text-neutral-500">
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
                          <td className="font-medium text-neutral-900">{row.store_code}</td>
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
              <div className="bg-white border border-neutral-200">
                <div className="p-4 border-b border-neutral-100 flex items-center justify-between">
                  <h3 className="font-medium text-neutral-900">Style Performance</h3>
                  <span className="text-sm text-neutral-500">
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
                          <td className="font-medium text-neutral-900">{row.style}</td>
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
              <div className="bg-white border border-neutral-200">
                <div className="p-4 border-b border-neutral-100">
                  <h3 className="font-medium text-neutral-900">Monthly Performance Trends</h3>
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
                          <td className="font-medium text-neutral-900">{row.month}</td>
                          <td>{formatNumber(row.quantity)}</td>
                          <td>{formatCurrency(row.revenue)}</td>
                          <td>{formatCurrency(row.asp)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!loading && !error && !dashboardData?.totals && (
        <div className="bg-neutral-50 border border-neutral-200 p-12 text-center">
          <p className="text-neutral-500 mb-2">No data available</p>
          <p className="text-sm text-neutral-400">
            Upload sales data to see BI dashboards
          </p>
        </div>
      )}
    </div>
  );
};

export default BIDashboards;
