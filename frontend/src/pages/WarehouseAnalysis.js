import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import { RefreshCw, Download, Warehouse } from "lucide-react";
import { BarChart, DoughnutChart, LineChart } from "../components/Charts";

const WarehouseAnalysis = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeView, setActiveView] = useState("overview");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API}/analytics/warehouse`);
      if (response.data.error) {
        setError(response.data.error);
      } else {
        setData(response.data);
      }
    } catch (err) {
      setError("Failed to fetch warehouse data. Please ensure warehouse inventory is uploaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const formatNumber = (value) => {
    if (!value) return "0";
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(0)}K`;
    return Math.round(value).toString();
  };

  const views = [
    { key: "overview", label: "Overview" },
    { key: "warehouses", label: "By Warehouse" },
    { key: "skus", label: "Top SKUs" },
    { key: "velocity", label: "Stock Velocity" },
  ];

  const handleExport = () => {
    if (!data) return;
    let exportData = [];
    if (activeView === "warehouses") exportData = data.by_warehouse;
    else if (activeView === "skus") exportData = data.by_sku;
    else if (activeView === "velocity") exportData = data.velocity;
    else return;
    if (!exportData || exportData.length === 0) return;
    const csv = [
      Object.keys(exportData[0]).join(','),
      ...exportData.map(row => Object.values(row).join(','))
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `warehouse_${activeView}.csv`;
    a.click();
  };

  return (
    <div className="animate-fade-in-up" data-testid="warehouse-analysis-page">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
            Warehouse Analysis
          </h1>
          <p className="text-slate-500">
            Warehouse inventory levels, stock velocity, and fulfillment insights
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            data-testid="refresh-warehouse-btn"
            onClick={fetchData}
            disabled={loading}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button
            data-testid="export-warehouse-btn"
            onClick={handleExport}
            className="btn-primary flex items-center gap-2"
          >
            <Download size={16} />
            Export
          </button>
        </div>
      </div>

      {/* View Tabs */}
      <div className="tabs">
        {views.map((view) => (
          <button
            key={view.key}
            data-testid={`wh-view-${view.key}`}
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
            Please upload the warehouse inventory data from the Data Upload page.
          </p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="spinner" />
        </div>
      )}

      {/* Content */}
      {data && !loading && (
        <>
          {/* Overview */}
          {activeView === "overview" && (
            <div data-testid="wh-overview-section">
              {/* KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div className="metric-card">
                  <span className="metric-label">Total Stock</span>
                  <span className="metric-value">{formatNumber(data.totals?.total_stock)}</span>
                  <span className="text-sm text-slate-500">units</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Active SKUs</span>
                  <span className="metric-value">{formatNumber(data.totals?.total_skus)}</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Warehouses</span>
                  <span className="metric-value">{data.totals?.total_warehouses || 0}</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Snapshot Date</span>
                  <span className="metric-value text-base">{data.totals?.snapshot_date || '-'}</span>
                </div>
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                {data.by_warehouse?.length > 0 && (
                  <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
                    <h3 className="font-semibold text-slate-900 mb-4">Stock by Warehouse</h3>
                    <BarChart
                      labels={data.by_warehouse.map(d => d.warehouse)}
                      datasets={[{
                        label: 'Stock Qty',
                        data: data.by_warehouse.map(d => d.total_qty),
                        color: '#0176D3'
                      }]}
                      height={280}
                      formatValue={formatNumber}
                      showLegend={false}
                    />
                  </div>
                )}

                {data.online_split?.length > 0 && (
                  <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
                    <h3 className="font-semibold text-slate-900 mb-4">Online vs Offline Fulfillment</h3>
                    <DoughnutChart
                      labels={data.online_split.map(d => d.fulfillment_type)}
                      data={data.online_split.map(d => d.total_qty)}
                      height={280}
                      formatValue={formatNumber}
                    />
                  </div>
                )}
              </div>

              {/* Trend */}
              {data.trend?.length > 0 && (
                <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8">
                  <h3 className="font-semibold text-slate-900 mb-4">Inventory Trend</h3>
                  <LineChart
                    labels={data.trend.map(d => d.date)}
                    datasets={[{
                      label: 'Total Quantity',
                      data: data.trend.map(d => d.total_qty),
                      color: '#0176D3'
                    }]}
                    height={300}
                    formatValue={formatNumber}
                    showLegend={false}
                  />
                </div>
              )}
            </div>
          )}

          {/* By Warehouse */}
          {activeView === "warehouses" && (
            <div data-testid="wh-warehouses-section">
              {data.by_warehouse?.length > 0 && (
                <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-6">
                  <h3 className="font-semibold text-slate-900 mb-4">Warehouse Stock Comparison</h3>
                  <BarChart
                    labels={data.by_warehouse.map(d => d.warehouse)}
                    datasets={[
                      { label: 'Stock Qty', data: data.by_warehouse.map(d => d.total_qty), color: '#0176D3' },
                      { label: 'SKU Count', data: data.by_warehouse.map(d => d.sku_count), color: '#2E844A' }
                    ]}
                    height={350}
                    formatValue={formatNumber}
                  />
                </div>
              )}

              <div className="bg-white border border-slate-200 rounded shadow-sm">
                <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                  <h3 className="font-semibold text-slate-900">Warehouse Details</h3>
                  <span className="text-sm text-slate-500">{data.by_warehouse?.length || 0} warehouses</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="data-table w-full">
                    <thead>
                      <tr>
                        <th>Warehouse</th>
                        <th>Total Stock</th>
                        <th>Active SKUs</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.by_warehouse?.map((row, i) => (
                        <tr key={i}>
                          <td className="font-medium text-slate-900">{row.warehouse}</td>
                          <td>{formatNumber(row.total_qty)}</td>
                          <td>{row.sku_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Top SKUs */}
          {activeView === "skus" && (
            <div data-testid="wh-skus-section">
              {data.by_sku?.length > 0 && (
                <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-6">
                  <h3 className="font-semibold text-slate-900 mb-4">Top SKUs by Stock</h3>
                  <BarChart
                    labels={data.by_sku.slice(0, 10).map(d => d.style || d.sku)}
                    datasets={[{
                      label: 'Stock Qty',
                      data: data.by_sku.slice(0, 10).map(d => d.total_qty),
                      color: '#DD7A01'
                    }]}
                    horizontal={true}
                    height={300}
                    formatValue={formatNumber}
                    showLegend={false}
                  />
                </div>
              )}

              <div className="bg-white border border-slate-200 rounded shadow-sm">
                <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                  <h3 className="font-semibold text-slate-900">SKU Inventory</h3>
                  <span className="text-sm text-slate-500">{data.by_sku?.length || 0} SKUs</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="data-table w-full">
                    <thead>
                      <tr>
                        <th>SKU</th>
                        <th>Style</th>
                        <th>Size</th>
                        <th>Stock Qty</th>
                        <th>Warehouses</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.by_sku?.map((row, i) => (
                        <tr key={i}>
                          <td className="font-medium text-slate-900">{row.sku}</td>
                          <td>{row.style || '-'}</td>
                          <td>{row.size || '-'}</td>
                          <td>{formatNumber(row.total_qty)}</td>
                          <td>{row.warehouse_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Velocity */}
          {activeView === "velocity" && (
            <div data-testid="wh-velocity-section">
              <div className="bg-blue-50 border border-blue-200 p-6 mb-6 rounded">
                <h3 className="font-semibold text-slate-900 mb-2">Stock Velocity</h3>
                <p className="text-slate-700 text-sm">
                  Days of stock estimates how long current inventory will last based on recent sales velocity. 
                  Lower values indicate fast-moving items that may need replenishment.
                </p>
              </div>

              {data.velocity?.length > 0 ? (
                <>
                  <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-6">
                    <h3 className="font-semibold text-slate-900 mb-4">Days of Stock (Fastest Moving)</h3>
                    <BarChart
                      labels={data.velocity.slice(0, 10).map(d => d.style || d.sku)}
                      datasets={[{
                        label: 'Days of Stock',
                        data: data.velocity.slice(0, 10).map(d => Math.min(d.days_of_stock, 365)),
                        colors: data.velocity.slice(0, 10).map(d => 
                          d.days_of_stock < 30 ? '#EA001E' : d.days_of_stock < 90 ? '#DD7A01' : '#2E844A'
                        )
                      }]}
                      height={300}
                      showLegend={false}
                    />
                  </div>

                  <div className="bg-white border border-slate-200 rounded shadow-sm">
                    <div className="p-4 border-b border-slate-100">
                      <h3 className="font-semibold text-slate-900">Stock Velocity Details</h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="data-table w-full">
                        <thead>
                          <tr>
                            <th>SKU</th>
                            <th>Style</th>
                            <th>Size</th>
                            <th>Current Stock</th>
                            <th>Sold (Period)</th>
                            <th>Days of Stock</th>
                            <th>Risk</th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.velocity.map((row, i) => (
                            <tr key={i}>
                              <td className="font-medium text-slate-900">{row.sku}</td>
                              <td>{row.style || '-'}</td>
                              <td>{row.size || '-'}</td>
                              <td>{formatNumber(row.stock_qty)}</td>
                              <td>{formatNumber(row.sold_qty)}</td>
                              <td>{row.days_of_stock >= 999 ? 'No Sales' : `${row.days_of_stock} days`}</td>
                              <td>
                                <span className={`badge ${
                                  row.days_of_stock < 30 ? 'badge-understock' :
                                  row.days_of_stock < 90 ? 'badge-overstock' :
                                  'badge-optimal'
                                }`}>
                                  {row.days_of_stock < 30 ? 'Critical' : row.days_of_stock < 90 ? 'Low' : 'OK'}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              ) : (
                <div className="bg-slate-50 border border-slate-200 p-12 text-center rounded">
                  <p className="text-slate-500 mb-2">No velocity data available</p>
                  <p className="text-sm text-slate-400">
                    Upload both warehouse inventory and daily sales data to see stock velocity
                  </p>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!loading && !error && !data?.totals && (
        <div className="bg-slate-50 border border-slate-200 p-12 text-center rounded">
          <p className="text-slate-500 mb-2">No warehouse data available</p>
          <p className="text-sm text-slate-400">
            Upload warehouse inventory data to see analysis
          </p>
        </div>
      )}
    </div>
  );
};

export default WarehouseAnalysis;
