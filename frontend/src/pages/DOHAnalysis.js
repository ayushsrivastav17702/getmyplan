import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  RefreshCw, Download, AlertTriangle, CheckCircle, XCircle,
  Package, Store, Clock, ArrowRight, Sliders
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import FilterPanel from "../components/FilterPanel";
import { LineChart, BarChart, DoughnutChart } from "../components/Charts";

const DOHAnalysis = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedView, setSelectedView] = useState("store");
  const [idealDOH, setIdealDOH] = useState(9);
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
    params.append('ideal_doh', idealDOH);
    return params.toString();
  };

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = buildQueryParams();
      const response = await axios.get(`${API}/analytics/doh?${queryParams}`);
      if (response.data.error) setError(response.data.error);
      else setData(response.data);
    } catch (err) {
      setError("Failed to fetch data. Please ensure required files are uploaded.");
    } finally {
      setLoading(false);
    }
  }, [filters, idealDOH]);

  useEffect(() => { fetchData(); }, []);

  const handleFilterChange = (field, value) => setFilters(prev => ({ ...prev, [field]: value }));
  const handleApplyFilters = () => fetchData();
  const handleResetFilters = () => {
    setFilters({
      startDate: filterOptions.dateRange?.min?.split('T')[0] || "",
      endDate: filterOptions.dateRange?.max?.split('T')[0] || "",
      categories: [], channels: [], regions: [],
    });
    setIdealDOH(9);
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
    const headers = ['Store', 'SKU', 'Style', 'SOH', 'ROS', 'DOH', 'Ideal DOH', 'Status'];
    const keys = ['store_code', 'sku', 'style', 'soh', 'ros', 'doh', 'ideal_doh', 'status'];
    const csv = [
      headers.join(','),
      ...rows.map(row => keys.map(k => `"${row[k] ?? ''}"`).join(','))
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `doh_analysis_ideal${idealDOH}.csv`;
    a.click();
  };

  const getStatusBadge = (status) => {
    const map = {
      OPTIMAL: { cls: 'badge-healthy', icon: CheckCircle, label: 'Optimal' },
      OVERSTOCKED: { cls: 'bg-amber-100 text-amber-700', icon: AlertTriangle, label: 'Overstocked' },
      UNDERSTOCKED: { cls: 'badge-understock', icon: AlertTriangle, label: 'Understocked' },
      STOCKED_OUT: { cls: 'bg-red-100 text-red-700', icon: XCircle, label: 'Stocked Out' },
      NO_SALES: { cls: 'bg-slate-100 text-slate-500', icon: Clock, label: 'No Sales' },
    };
    const cfg = map[status] || map.OPTIMAL;
    const Icon = cfg.icon;
    return (
      <span className={`badge ${cfg.cls} inline-flex items-center gap-1`}>
        <Icon size={12} /> {cfg.label}
      </span>
    );
  };

  const summary = data?.summary || {};
  const displayData = selectedView === "store" ? (data?.store_data || []) : (data?.category_data || []);

  return (
    <div className="animate-fade-in-up" data-testid="doh-analysis-page">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
            Days on Hand (DOH) Analysis
          </h1>
          <p className="text-slate-500">
            DOH = Inventory / Daily ROS | Weighted by inventory quantity
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button data-testid="refresh-doh-btn" onClick={fetchData} disabled={loading}
            className="btn-secondary flex items-center gap-2">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
          <button data-testid="export-doh-btn" onClick={handleExportCSV}
            className="btn-primary flex items-center gap-2">
            <Download size={16} /> Export
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
        pageType="doh"
      />

      {/* PRD Formula + Config */}
      <div className="bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="doh-formula-card">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Formulas */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Clock size={18} className="text-[#0176D3]" />
              <h3 className="text-sm font-semibold text-slate-900">PRD Formulas</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="bg-white rounded border border-slate-200 p-3" data-testid="formula-doh">
                <div className="text-xs font-semibold uppercase tracking-wider text-[#0176D3] mb-1">DOH (Store-SKU)</div>
                <p className="text-xs text-slate-700 font-mono">Inventory / Daily ROS</p>
              </div>
              <div className="bg-white rounded border border-slate-200 p-3" data-testid="formula-channel-doh">
                <div className="text-xs font-semibold uppercase tracking-wider text-[#2E844A] mb-1">Channel DOH</div>
                <p className="text-xs text-slate-700 font-mono">{"Sum(DOH x Inv) / Sum(Inv)"}</p>
              </div>
              <div className="bg-white rounded border border-slate-200 p-3" data-testid="formula-classification">
                <div className="text-xs font-semibold uppercase tracking-wider text-[#DD7A01] mb-1">Classification</div>
                <p className="text-xs text-slate-700 font-mono">{"Optimal: ±20% of ideal"}</p>
              </div>
            </div>
          </div>
          {/* Ideal DOH Config */}
          <div data-testid="doh-config">
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-slate-700 flex items-center gap-1">
                <Sliders size={14} /> Ideal DOH Target
              </label>
              <span className="text-sm font-semibold text-[#0176D3]">{idealDOH} days</span>
            </div>
            <input type="range" min="1" max="60" value={idealDOH}
              onChange={(e) => setIdealDOH(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#0176D3]"
              data-testid="slider-ideal-doh"
            />
            <div className="flex justify-between text-xs text-slate-400 mt-1">
              <span>1 day</span><span>60 days</span>
            </div>
            <div className="mt-2 text-xs text-slate-500">
              {"Optimal range: "}{(idealDOH * 0.8).toFixed(0)}{" – "}{(idealDOH * 1.2).toFixed(0)}{" days (±20%)"}
            </div>
            <button onClick={fetchData} disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2 mt-3"
              data-testid="recalculate-doh-btn">
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Recalculate
            </button>
          </div>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-amber-50 border border-amber-200 p-8 mb-6 rounded text-center" data-testid="doh-error">
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
            <div className="metric-card" data-testid="kpi-overall-doh">
              <div className="flex items-center justify-between mb-2">
                <span className="metric-label">Overall DOH</span>
                <Clock size={18} className="text-[#0176D3]" />
              </div>
              <span className="metric-value text-[#0176D3]">{summary.overall_doh || 0} days</span>
              <span className="text-xs text-slate-500 block mt-1">Weighted avg | Ideal: {summary.ideal_doh} days</span>
            </div>
            <div className="metric-card" data-testid="kpi-optimal">
              <div className="flex items-center justify-between mb-2">
                <span className="metric-label">Optimal</span>
                <CheckCircle size={18} className="text-green-500" />
              </div>
              <span className="metric-value text-green-600">{formatNumber(summary.optimal_count)}</span>
              <span className="text-xs text-slate-500 block mt-1">{"within ±20% of ideal"}</span>
            </div>
            <div className="metric-card" data-testid="kpi-at-risk">
              <div className="flex items-center justify-between mb-2">
                <span className="metric-label">At Risk</span>
                <AlertTriangle size={18} className="text-amber-500" />
              </div>
              <span className="metric-value text-amber-600">
                {(summary.overstocked_count || 0) + (summary.understocked_count || 0)}
              </span>
              <span className="text-xs text-slate-500 block mt-1">
                {summary.overstocked_count || 0} over, {summary.understocked_count || 0} under
              </span>
            </div>
            <div className="metric-card" data-testid="kpi-stockedout">
              <div className="flex items-center justify-between mb-2">
                <span className="metric-label">Stocked Out</span>
                <XCircle size={18} className="text-red-500" />
              </div>
              <span className="metric-value text-red-600">{formatNumber(summary.stockedout_count)}</span>
              <span className="text-xs text-slate-500 block mt-1">
                of {formatNumber(summary.total_store_skus)} total store-SKUs
              </span>
            </div>
          </div>

          {/* DOH Trend + Status Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* DOH Trend Chart */}
            {data.trend_data?.length > 1 && (
              <div className="lg:col-span-2 bg-white border border-slate-200 rounded shadow-sm p-6" data-testid="chart-doh-trend">
                <h3 className="font-semibold text-slate-900 mb-1">DOH Trend & Stock-Outs</h3>
                <p className="text-xs text-slate-500 mb-4">Weekly weighted-average DOH with stock-out count overlay</p>
                <LineChart
                  labels={data.trend_data.map(t => t.week_label)}
                  datasets={[
                    { label: 'DOH (days)', data: data.trend_data.map(t => t.doh), color: '#0176D3', fill: true },
                    { label: 'Stock-Outs', data: data.trend_data.map(t => t.stockout_count), color: '#EA001E' },
                  ]}
                  height={280}
                />
              </div>
            )}

            {/* Status Distribution */}
            <div className="bg-white border border-slate-200 rounded shadow-sm p-6" data-testid="chart-status-dist">
              <h3 className="font-semibold text-slate-900 mb-4">DOH Status Distribution</h3>
              <DoughnutChart
                labels={['Optimal', 'Overstocked', 'Understocked', 'Stocked Out']}
                data={[
                  summary.optimal_count || 0,
                  summary.overstocked_count || 0,
                  summary.understocked_count || 0,
                  summary.stockedout_count || 0,
                ]}
                height={220}
              />
              <div className="mt-4 space-y-2 text-sm">
                <div className="flex justify-between"><span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-green-500" />Optimal</span><span className="font-medium">{summary.optimal_count || 0}</span></div>
                <div className="flex justify-between"><span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-amber-500" />Overstocked</span><span className="font-medium">{summary.overstocked_count || 0}</span></div>
                <div className="flex justify-between"><span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-red-500" />Understocked</span><span className="font-medium">{summary.understocked_count || 0}</span></div>
                <div className="flex justify-between"><span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-slate-400" />Stocked Out</span><span className="font-medium">{summary.stockedout_count || 0}</span></div>
              </div>
            </div>
          </div>

          {/* Recommendations */}
          {data.recommendations?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="doh-recommendations">
              <h3 className="font-semibold text-slate-900 mb-4">Recommended Actions</h3>
              <div className="space-y-3">
                {data.recommendations.map((rec, idx) => (
                  <div key={idx} className={`flex items-start gap-3 p-3 rounded-lg ${
                    rec.priority === 'high' ? 'bg-red-50 border border-red-100' : 'bg-amber-50 border border-amber-100'
                  }`}>
                    <AlertTriangle size={18} className={rec.priority === 'high' ? 'text-red-600 mt-0.5' : 'text-amber-600 mt-0.5'} />
                    <div>
                      <p className="font-medium text-slate-900 text-sm">{rec.title}</p>
                      <p className="text-sm text-slate-600">{rec.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* View Toggle */}
          <div className="flex items-center gap-2 mb-4">
            <button
              data-testid="view-store"
              onClick={() => setSelectedView("store")}
              className={`flex items-center gap-2 px-4 py-2 text-sm rounded transition-all ${
                selectedView === "store"
                  ? 'bg-[#0176D3] text-white shadow-sm'
                  : 'border border-slate-200 text-slate-600 hover:border-slate-400'
              }`}
            >
              <Store size={16} /> Store View
            </button>
            <button
              data-testid="view-category"
              onClick={() => setSelectedView("category")}
              className={`flex items-center gap-2 px-4 py-2 text-sm rounded transition-all ${
                selectedView === "category"
                  ? 'bg-[#0176D3] text-white shadow-sm'
                  : 'border border-slate-200 text-slate-600 hover:border-slate-400'
              }`}
            >
              <Package size={16} /> Category View
            </button>
          </div>

          {/* Store/Category DOH Bar Chart */}
          {displayData.length > 0 && (
            <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="chart-doh-bars">
              <h3 className="font-semibold text-slate-900 mb-4">
                {selectedView === "store" ? "Store-wise" : "Category-wise"} DOH
              </h3>
              <BarChart
                labels={displayData.slice(0, 15).map(d => selectedView === "store" ? d.store_code : d.category)}
                datasets={[
                  { label: 'Current DOH', data: displayData.slice(0, 15).map(d => d.doh), color: '#0176D3' },
                  { label: 'Ideal DOH', data: displayData.slice(0, 15).map(d => d.ideal_doh || idealDOH), color: '#2E844A' },
                ]}
                height={280}
                formatValue={(v) => `${v} days`}
              />
            </div>
          )}

          {/* Data Table */}
          {displayData.length > 0 && (
            <div className="bg-white border border-slate-200 rounded shadow-sm mb-8" data-testid="table-doh-summary">
              <div className="p-4 border-b border-slate-100">
                <h3 className="font-semibold text-slate-900">
                  {selectedView === "store" ? "Store-wise" : "Category-wise"} DOH Analysis
                </h3>
                <p className="text-xs text-slate-500 mt-1">DOH = Inventory / ROS | Weighted average shown</p>
              </div>
              <div className="overflow-x-auto">
                <table className="data-table w-full">
                  <thead>
                    <tr>
                      <th>{selectedView === "store" ? "Store" : "Category"}</th>
                      <th>Inventory</th>
                      <th>Current DOH</th>
                      <th>Ideal DOH</th>
                      <th>SKUs</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayData.map((row, i) => (
                      <tr key={i}>
                        <td className="font-medium text-slate-900">
                          {selectedView === "store" ? row.store_code : row.category}
                        </td>
                        <td>{formatNumber(row.total_inventory)}</td>
                        <td className={`font-semibold ${
                          row.status === 'OPTIMAL' ? 'text-green-600' :
                          row.status === 'UNDERSTOCKED' || row.status === 'STOCKED_OUT' ? 'text-red-600' :
                          'text-amber-600'
                        }`}>
                          {row.doh} days
                        </td>
                        <td>{row.ideal_doh || idealDOH} days</td>
                        <td>{row.sku_count}</td>
                        <td>{getStatusBadge(row.status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Detail Table */}
          {data.detail?.length > 0 && selectedView === "store" && (
            <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="table-doh-detail">
              <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900">Store-SKU DOH Detail</h3>
                  <p className="text-xs text-slate-500 mt-1">Sorted by lowest DOH first (most urgent)</p>
                </div>
                <button onClick={handleExportCSV}
                  className="btn-secondary flex items-center gap-2 text-sm"
                  data-testid="export-detail-doh-btn">
                  <Download size={14} /> Export CSV
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="data-table w-full">
                  <thead>
                    <tr>
                      <th>Store</th>
                      <th>SKU</th>
                      <th>Style</th>
                      <th>SOH</th>
                      <th>ROS</th>
                      <th>DOH</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.detail.slice(0, 50).map((row, i) => (
                      <tr key={i}>
                        <td className="font-medium text-slate-900">{row.store_code}</td>
                        <td>{row.sku}</td>
                        <td>{row.style}</td>
                        <td>{Math.round(row.soh)}</td>
                        <td>{(row.ros || 0).toFixed(2)}</td>
                        <td className={`font-semibold ${
                          row.doh >= 9999 ? 'text-slate-400' :
                          row.doh <= (idealDOH * 0.8) ? 'text-red-600' :
                          row.doh >= (idealDOH * 1.2) ? 'text-amber-600' :
                          'text-green-600'
                        }`}>
                          {row.doh >= 9999 ? 'N/A' : `${row.doh} days`}
                        </td>
                        <td>{getStatusBadge(row.status)}</td>
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
          <p className="text-sm text-slate-400">Upload the required files to see DOH analysis</p>
        </div>
      )}
    </div>
  );
};

export default DOHAnalysis;
