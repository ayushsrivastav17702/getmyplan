import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  RefreshCw, Download, Package, TrendingDown, AlertTriangle,
  Store, ShoppingCart, Sliders, ArrowRight
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import FilterPanel from "../components/FilterPanel";
import { BarChart, DoughnutChart } from "../components/Charts";

const ReplenishmentPlanner = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [leadTime, setLeadTime] = useState(14);
  const [safetyDays, setSafetyDays] = useState(7);
  const [filterOptions, setFilterOptions] = useState({});
  const [filters, setFilters] = useState({
    startDate: "", endDate: "",
    categories: [], channels: [], regions: [],
  });

  const fetchFilterOptions = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/analytics/filter-options`);
      setFilterOptions(response.data);
      if (response.data.dateRange?.min) {
        setFilters(prev => ({
          ...prev,
          startDate: response.data.dateRange.min.split('T')[0],
          endDate: response.data.dateRange.max.split('T')[0],
        }));
      }
    } catch (err) {
      console.error("Error fetching filter options:", err);
    }
  }, []);

  useEffect(() => { fetchFilterOptions(); }, [fetchFilterOptions]);

  const buildQueryParams = () => {
    const params = new URLSearchParams();
    if (filters.startDate) params.append('start_date', filters.startDate);
    if (filters.endDate) params.append('end_date', filters.endDate);
    if (filters.categories?.length) params.append('categories', filters.categories.join(','));
    if (filters.channels?.length) params.append('channels', filters.channels.join(','));
    if (filters.regions?.length) params.append('regions', filters.regions.join(','));
    params.append('lead_time_days', leadTime);
    params.append('safety_days', safetyDays);
    return params.toString();
  };

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = buildQueryParams();
      const response = await axios.get(`${API}/analytics/replenishment?${queryParams}`);
      if (response.data.error) setError(response.data.error);
      else setData(response.data);
    } catch (err) {
      setError("Failed to fetch data. Please ensure required files are uploaded.");
    } finally {
      setLoading(false);
    }
  }, [filters, leadTime, safetyDays]);

  useEffect(() => { fetchData(); }, []);

  const handleFilterChange = (field, value) => setFilters(prev => ({ ...prev, [field]: value }));
  const handleApplyFilters = () => fetchData();
  const handleResetFilters = () => {
    setFilters({
      startDate: filterOptions.dateRange?.min?.split('T')[0] || "",
      endDate: filterOptions.dateRange?.max?.split('T')[0] || "",
      categories: [], channels: [], regions: [],
    });
    setLeadTime(14);
    setSafetyDays(7);
  };

  const formatCurrency = (v) => {
    if (!v) return "\u20B90";
    if (v >= 10000000) return `\u20B9${(v / 10000000).toFixed(1)}Cr`;
    if (v >= 100000) return `\u20B9${(v / 100000).toFixed(1)}L`;
    if (v >= 1000) return `\u20B9${(v / 1000).toFixed(0)}K`;
    return `\u20B9${Math.round(v)}`;
  };
  const formatNumber = (v) => {
    if (!v) return "0";
    if (v >= 1000000) return `${(v / 1000000).toFixed(1)}M`;
    if (v >= 1000) return `${(v / 1000).toFixed(0)}K`;
    return Math.round(v).toString();
  };

  const handleExportCSV = () => {
    const rows = data?.detail || [];
    if (rows.length === 0) return;
    const headers = ['SKU', 'Style', 'Size', 'Store', 'Current SOH', 'ROS (units/day)',
      'Days to Stock-Out', 'Safety Stock', 'Lead Time Demand', 'Reorder Qty', 'ASP', 'PO Value', 'Priority'];
    const keys = ['sku', 'style', 'size', 'store_code', 'current_soh', 'ros',
      'days_to_stockout', 'safety_stock', 'demand_during_lead', 'reorder_qty', 'asp', 'po_value', 'priority'];
    const csv = [
      headers.join(','),
      ...rows.map(row => keys.map(k => `"${row[k] ?? ''}"`).join(','))
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `replenishment_plan_LT${leadTime}_SS${safetyDays}.csv`;
    a.click();
  };

  const getPriorityBadge = (priority) => {
    const map = {
      'Stock-Out': 'bg-red-100 text-red-800',
      'Critical': 'bg-red-50 text-red-700',
      'High': 'bg-amber-100 text-amber-800',
      'Medium': 'bg-yellow-50 text-yellow-700',
      'Low': 'bg-green-100 text-green-700',
    };
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${map[priority] || 'bg-slate-100 text-slate-600'}`}>
        {priority}
      </span>
    );
  };

  const summary = data?.summary || {};

  return (
    <div className="animate-fade-in-up" data-testid="replenishment-page">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
            Replenishment Planner
          </h1>
          <p className="text-slate-500">
            Generate purchase order suggestions based on ROS velocity and lead times
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button data-testid="refresh-repl-btn" onClick={fetchData} disabled={loading}
            className="btn-secondary flex items-center gap-2">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button data-testid="export-repl-btn" onClick={handleExportCSV}
            className="btn-primary flex items-center gap-2">
            <Download size={16} />
            Export PO as CSV
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
        pageType="replenishment"
      />

      {/* PRD Formula + Config Card */}
      <div className="bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="repl-formula-card">
        <div className="flex items-center gap-2 mb-4">
          <Package size={18} className="text-[#0176D3]" />
          <h3 className="text-sm font-semibold text-slate-900">PRD Formulas & Configuration</h3>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Formulas */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="bg-white rounded border border-slate-200 p-3" data-testid="formula-reorder-qty">
              <div className="text-xs font-semibold uppercase tracking-wider text-[#0176D3] mb-1">Reorder Qty</div>
              <p className="text-xs text-slate-700 font-mono">(ROS x Lead Time) + Safety Stock - SOH</p>
            </div>
            <div className="bg-white rounded border border-slate-200 p-3" data-testid="formula-safety-stock">
              <div className="text-xs font-semibold uppercase tracking-wider text-[#2E844A] mb-1">Safety Stock</div>
              <p className="text-xs text-slate-700 font-mono">ROS x Safety Days</p>
            </div>
            <div className="bg-white rounded border border-slate-200 p-3" data-testid="formula-stockout-date">
              <div className="text-xs font-semibold uppercase tracking-wider text-[#EA001E] mb-1">Days to Stock-Out</div>
              <p className="text-xs text-slate-700 font-mono">Current SOH / ROS</p>
            </div>
            <div className="bg-white rounded border border-slate-200 p-3" data-testid="formula-po-value">
              <div className="text-xs font-semibold uppercase tracking-wider text-[#DD7A01] mb-1">PO Value</div>
              <p className="text-xs text-slate-700 font-mono">Reorder Qty x ASP</p>
            </div>
          </div>
          {/* Config Sliders */}
          <div className="space-y-4" data-testid="repl-config">
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-sm font-medium text-slate-700 flex items-center gap-1">
                  <Sliders size={14} /> Lead Time
                </label>
                <span className="text-sm font-semibold text-[#0176D3]">{leadTime} days</span>
              </div>
              <input type="range" min="1" max="60" value={leadTime}
                onChange={(e) => setLeadTime(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#0176D3]"
                data-testid="slider-lead-time"
              />
              <div className="flex justify-between text-xs text-slate-400 mt-1">
                <span>1 day</span><span>60 days</span>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-sm font-medium text-slate-700 flex items-center gap-1">
                  <Sliders size={14} /> Safety Days
                </label>
                <span className="text-sm font-semibold text-[#2E844A]">{safetyDays} days</span>
              </div>
              <input type="range" min="0" max="30" value={safetyDays}
                onChange={(e) => setSafetyDays(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#2E844A]"
                data-testid="slider-safety-days"
              />
              <div className="flex justify-between text-xs text-slate-400 mt-1">
                <span>0 days</span><span>30 days</span>
              </div>
            </div>
            <button onClick={fetchData} disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2 mt-2"
              data-testid="recalculate-btn">
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              Recalculate Plan
            </button>
          </div>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-amber-50 border border-amber-200 p-8 mb-6 rounded text-center" data-testid="repl-error">
          <AlertTriangle size={40} className="text-amber-500 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">No Data Available</h3>
          <p className="text-amber-700 mb-4">{error}</p>
          <button onClick={() => navigate('/upload')}
            className="btn-primary inline-flex items-center gap-2">
            Go to Data Upload <ArrowRight size={16} />
          </button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-20"><div className="spinner" /></div>
      )}

      {/* Main Content */}
      {data && !loading && !error && (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="metric-card" data-testid="kpi-po-value">
              <div className="flex items-center justify-between mb-2">
                <span className="metric-label">Total PO Value</span>
                <ShoppingCart size={18} className="text-[#0176D3]" />
              </div>
              <span className="metric-value text-[#0176D3]">{formatCurrency(summary.total_po_value)}</span>
              <span className="text-xs text-slate-500 block mt-1">{formatNumber(summary.total_reorder_units)} units to reorder</span>
            </div>
            <div className="metric-card" data-testid="kpi-skus-reorder">
              <div className="flex items-center justify-between mb-2">
                <span className="metric-label">SKUs Needing Reorder</span>
                <Package size={18} className="text-amber-500" />
              </div>
              <span className="metric-value text-amber-600">{formatNumber(summary.skus_needing_reorder)}</span>
              <span className="text-xs text-slate-500 block mt-1">across {summary.stores_needing_reorder} stores</span>
            </div>
            <div className="metric-card" data-testid="kpi-urgent">
              <div className="flex items-center justify-between mb-2">
                <span className="metric-label">Urgent (Stock-Out + Critical)</span>
                <AlertTriangle size={18} className="text-red-500" />
              </div>
              <span className="metric-value text-red-600">{(summary.stockout_count || 0) + (summary.critical_count || 0)}</span>
              <span className="text-xs text-slate-500 block mt-1">{summary.stockout_count} stocked out, {summary.critical_count} critical</span>
            </div>
            <div className="metric-card" data-testid="kpi-config">
              <div className="flex items-center justify-between mb-2">
                <span className="metric-label">Plan Configuration</span>
                <Sliders size={18} className="text-slate-500" />
              </div>
              <span className="metric-value text-slate-700 text-xl">{summary.lead_time_days}d + {summary.safety_days}d</span>
              <span className="text-xs text-slate-500 block mt-1">Lead Time + Safety Buffer</span>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Priority Distribution */}
            {data.by_priority?.length > 0 && (
              <div className="bg-white border border-slate-200 rounded shadow-sm p-6" data-testid="chart-priority">
                <h3 className="font-semibold text-slate-900 mb-4">Reorder by Priority</h3>
                <DoughnutChart
                  labels={data.by_priority.map(p => p.priority)}
                  data={data.by_priority.map(p => p.count)}
                  height={260}
                  formatValue={formatNumber}
                />
              </div>
            )}
            {/* PO Value by Store */}
            {data.by_store?.length > 0 && (
              <div className="bg-white border border-slate-200 rounded shadow-sm p-6" data-testid="chart-store-po">
                <h3 className="font-semibold text-slate-900 mb-4">PO Value by Store</h3>
                <BarChart
                  labels={data.by_store.slice(0, 12).map(s => s.store_code)}
                  datasets={[{ label: 'PO Value', data: data.by_store.slice(0, 12).map(s => s.total_value), color: '#0176D3' }]}
                  horizontal={true}
                  height={260}
                  formatValue={formatCurrency}
                  showLegend={false}
                />
              </div>
            )}
          </div>

          {/* Top Styles needing reorder */}
          {data.by_style?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="chart-style-po">
              <h3 className="font-semibold text-slate-900 mb-4">Top Styles by PO Value</h3>
              <BarChart
                labels={data.by_style.slice(0, 15).map(s => s.style)}
                datasets={[{ label: 'PO Value', data: data.by_style.slice(0, 15).map(s => s.total_value), color: '#DD7A01' }]}
                height={260}
                formatValue={formatCurrency}
                showLegend={false}
              />
            </div>
          )}

          {/* Priority Summary Table */}
          {data.by_priority?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded shadow-sm mb-8" data-testid="table-priority">
              <div className="p-4 border-b border-slate-100">
                <h3 className="font-semibold text-slate-900">Priority Breakdown</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="data-table w-full">
                  <thead>
                    <tr>
                      <th>Priority</th>
                      <th>Store-SKU Count</th>
                      <th>Total Units</th>
                      <th>Total PO Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.by_priority.map((row, i) => (
                      <tr key={i}>
                        <td>{getPriorityBadge(row.priority)}</td>
                        <td>{formatNumber(row.count)}</td>
                        <td>{formatNumber(row.total_units)}</td>
                        <td className="font-semibold">{formatCurrency(row.total_value)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Detail Replenishment Table */}
          {data.detail?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded shadow-sm mb-8" data-testid="table-detail">
              <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900">Replenishment Detail</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Sorted by urgency (lowest days to stock-out first) &bull; Showing top {Math.min(data.detail.length, 200)} rows
                  </p>
                </div>
                <button onClick={handleExportCSV}
                  className="btn-secondary flex items-center gap-2 text-sm"
                  data-testid="export-detail-btn">
                  <Download size={14} /> Export CSV
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="data-table w-full">
                  <thead>
                    <tr>
                      <th>SKU</th>
                      <th>Style</th>
                      <th>Size</th>
                      <th>Store</th>
                      <th>SOH</th>
                      <th>ROS</th>
                      <th>Days Left</th>
                      <th>Safety Stock</th>
                      <th>Reorder Qty</th>
                      <th>PO Value</th>
                      <th>Priority</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.detail.slice(0, 50).map((row, i) => (
                      <tr key={i}>
                        <td className="font-medium text-slate-900">{row.sku}</td>
                        <td>{row.style}</td>
                        <td>{row.size}</td>
                        <td>{row.store_code}</td>
                        <td>{Math.round(row.current_soh)}</td>
                        <td>{(row.ros || 0).toFixed(1)}</td>
                        <td className={`font-semibold ${
                          row.days_to_stockout <= 3 ? 'text-red-600' :
                          row.days_to_stockout <= 7 ? 'text-amber-600' :
                          'text-slate-700'
                        }`}>
                          {row.days_to_stockout >= 999 ? 'N/A' : `${row.days_to_stockout}d`}
                        </td>
                        <td>{Math.round(row.safety_stock)}</td>
                        <td className="font-semibold text-[#0176D3]">{Math.round(row.reorder_qty)}</td>
                        <td>{formatCurrency(row.po_value)}</td>
                        <td>{getPriorityBadge(row.priority)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Store Summary Table */}
          {data.by_store?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="table-by-store">
              <div className="p-4 border-b border-slate-100">
                <h3 className="font-semibold text-slate-900">Store-wise PO Summary</h3>
                <p className="text-xs text-slate-500 mt-1">Ranked by total PO value</p>
              </div>
              <div className="overflow-x-auto">
                <table className="data-table w-full">
                  <thead>
                    <tr>
                      <th>Store</th>
                      <th>SKUs to Reorder</th>
                      <th>Total Units</th>
                      <th>PO Value</th>
                      <th>Urgent Items</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.by_store.map((row, i) => (
                      <tr key={i}>
                        <td className="font-medium text-slate-900">{row.store_code}</td>
                        <td>{row.sku_count}</td>
                        <td>{formatNumber(row.total_units)}</td>
                        <td className="font-semibold">{formatCurrency(row.total_value)}</td>
                        <td>
                          {row.urgent_count > 0 ? (
                            <span className="badge badge-understock">{row.urgent_count} urgent</span>
                          ) : (
                            <span className="badge badge-optimal">All OK</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!loading && !error && !data && (
        <div className="bg-slate-50 border border-slate-200 p-12 text-center rounded">
          <p className="text-slate-500 mb-2">No data available</p>
          <p className="text-sm text-slate-400">
            Upload the required files to generate a replenishment plan
          </p>
        </div>
      )}
    </div>
  );
};

export default ReplenishmentPlanner;
