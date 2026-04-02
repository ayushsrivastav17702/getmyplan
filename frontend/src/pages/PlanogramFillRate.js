import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  RefreshCw, Download, AlertTriangle, CheckCircle, XCircle,
  Package, Store, ArrowRight, Layout
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import FilterPanel from "../components/FilterPanel";
import { LineChart, BarChart, DoughnutChart } from "../components/Charts";

const PlanogramFillRate = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedView, setSelectedView] = useState("store");
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
    return params.toString();
  };

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = buildQueryParams();
      const response = await axios.get(`${API}/analytics/planogram-fill-rate?${queryParams}`);
      if (response.data.error) setError(response.data.error);
      else setData(response.data);
    } catch (err) {
      setError("Failed to fetch data. Please ensure required files are uploaded.");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { fetchData(); }, []);

  const handleFilterChange = (field, value) => setFilters(prev => ({ ...prev, [field]: value }));
  const handleApplyFilters = () => fetchData();
  const handleResetFilters = () => {
    setFilters({
      startDate: filterOptions.dateRange?.min?.split('T')[0] || "",
      endDate: filterOptions.dateRange?.max?.split('T')[0] || "",
      categories: [], channels: [], regions: [],
    });
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
    const headers = ['Store', 'SKU', 'Style', 'Current Stock', 'Norm Allocated', 'Fill Rate %', 'Missing Facings', 'ROS', 'ASP', 'Lost Sales', 'Status'];
    const keys = ['store_code', 'ean', 'style', 'current_stock', 'norm_allocated', 'fill_rate', 'missing_facings', 'ros', 'asp', 'lost_sales', 'status'];
    const csv = [
      headers.join(','),
      ...rows.map(row => keys.map(k => `"${row[k] ?? ''}"`).join(','))
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'planogram_fill_rate.csv';
    a.click();
  };

  const getStatusBadge = (status) => {
    const map = {
      GOOD: { cls: 'badge-healthy', icon: CheckCircle, label: 'Good' },
      MODERATE: { cls: 'bg-amber-100 text-amber-700', icon: AlertTriangle, label: 'Moderate' },
      CRITICAL: { cls: 'badge-understock', icon: XCircle, label: 'Critical' },
    };
    const cfg = map[status] || map.CRITICAL;
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
    <div className="animate-fade-in-up" data-testid="planogram-page">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
            Planogram Fill Rate
          </h1>
          <p className="text-slate-500">
            Fill Rate = (Current Stock / Norm Allocated) x 100
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button data-testid="refresh-plano-btn" onClick={fetchData} disabled={loading}
            className="btn-secondary flex items-center gap-2">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
          <button data-testid="export-plano-btn" onClick={handleExportCSV}
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
        pageType="planogram"
      />

      {/* PRD Formula Card */}
      <div className="bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="plano-formula-card">
        <div className="flex items-center gap-2 mb-3">
          <Layout size={18} className="text-[#0176D3]" />
          <h3 className="text-sm font-semibold text-slate-900">PRD Formulas: Planogram Fill Rate</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
          <div className="bg-white rounded border border-slate-200 p-3" data-testid="formula-fill-rate">
            <div className="text-xs font-semibold uppercase tracking-wider text-[#0176D3] mb-1">Fill Rate</div>
            <p className="text-xs text-slate-700 font-mono">(Current Stock / Norm Allocated) x 100</p>
          </div>
          <div className="bg-white rounded border border-slate-200 p-3" data-testid="formula-overall-fill">
            <div className="text-xs font-semibold uppercase tracking-wider text-[#2E844A] mb-1">Overall Fill Rate</div>
            <p className="text-xs text-slate-700 font-mono">{"(Sum Stock / Sum Norm) x 100"}</p>
          </div>
          <div className="bg-white rounded border border-slate-200 p-3" data-testid="formula-lost-sales">
            <div className="text-xs font-semibold uppercase tracking-wider text-[#EA001E] mb-1">Lost Sales</div>
            <p className="text-xs text-slate-700 font-mono">Missing Facings x ROS x ASP</p>
          </div>
        </div>
        <div className="flex gap-4 text-xs text-slate-600">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500" /> {"Good (>=90%)"}</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" /> Moderate (80-90%)</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" /> {"Critical (<80%)"}</span>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-amber-50 border border-amber-200 p-8 mb-6 rounded text-center" data-testid="plano-error">
          <AlertTriangle size={40} className="text-amber-500 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">No Data Available</h3>
          <p className="text-amber-700 mb-4">{error}</p>
          <button onClick={() => navigate('/upload')}
            className="btn-primary inline-flex items-center gap-2">
            Go to Data Upload <ArrowRight size={16} />
          </button>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-20"><div className="spinner" /></div>
      )}

      {data && !loading && !error && (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="metric-card" data-testid="kpi-overall-fill">
              <div className="flex items-center justify-between mb-2">
                <span className="metric-label">Overall Fill Rate</span>
                <Layout size={18} className="text-[#0176D3]" />
              </div>
              <span className={`metric-value ${
                summary.overall_fill_rate >= 90 ? 'text-green-600' :
                summary.overall_fill_rate >= 80 ? 'text-amber-600' : 'text-red-600'
              }`}>{summary.overall_fill_rate}%</span>
              <span className="text-xs text-slate-500 block mt-1">Target: {summary.target_fill_rate}%</span>
            </div>
            <div className="metric-card" data-testid="kpi-compliance">
              <div className="flex items-center justify-between mb-2">
                <span className="metric-label">{"Good Compliance (>=90%)"}</span>
                <CheckCircle size={18} className="text-green-500" />
              </div>
              <span className="metric-value text-green-600">{formatNumber(summary.good_count)}</span>
              <span className="text-xs text-slate-500 block mt-1">
                of {formatNumber(summary.total_store_skus)} store-SKUs
              </span>
            </div>
            <div className="metric-card" data-testid="kpi-critical">
              <div className="flex items-center justify-between mb-2">
                <span className="metric-label">{"Critical (<80%)"}</span>
                <XCircle size={18} className="text-red-500" />
              </div>
              <span className="metric-value text-red-600">{formatNumber(summary.critical_count)}</span>
              <span className="text-xs text-slate-500 block mt-1">
                {summary.moderate_count} moderate risk
              </span>
            </div>
            <div className="metric-card" data-testid="kpi-lost-sales">
              <div className="flex items-center justify-between mb-2">
                <span className="metric-label">Est. Lost Sales</span>
                <AlertTriangle size={18} className="text-red-500" />
              </div>
              <span className="metric-value text-red-600">{formatCurrency(summary.total_lost_sales)}</span>
              <span className="text-xs text-slate-500 block mt-1">from missing facings</span>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* Fill Rate Trend */}
            {data.trend_data?.length > 1 && (
              <div className="lg:col-span-2 bg-white border border-slate-200 rounded shadow-sm p-6" data-testid="chart-fill-trend">
                <h3 className="font-semibold text-slate-900 mb-1">Fill Rate Trend</h3>
                <p className="text-xs text-slate-500 mb-4">Weekly fill rate vs target ({summary.target_fill_rate}%)</p>
                <LineChart
                  labels={data.trend_data.map(t => t.week_label)}
                  datasets={[
                    { label: 'Fill Rate %', data: data.trend_data.map(t => t.fill_rate), color: '#0176D3', fill: true },
                    { label: 'Target', data: data.trend_data.map(t => t.target), color: '#94A3B8' },
                  ]}
                  height={280}
                  formatValue={(v) => `${v}%`}
                />
              </div>
            )}

            {/* Status Distribution */}
            <div className="bg-white border border-slate-200 rounded shadow-sm p-6" data-testid="chart-status-dist">
              <h3 className="font-semibold text-slate-900 mb-4">Compliance Distribution</h3>
              <DoughnutChart
                labels={['Good', 'Moderate', 'Critical']}
                data={[
                  summary.good_count || 0,
                  summary.moderate_count || 0,
                  summary.critical_count || 0,
                ]}
                height={220}
              />
              <div className="mt-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-green-500" />{"Good (>=90%)"}</span>
                  <span className="font-medium">{summary.good_count || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-amber-500" />Moderate (80-90%)</span>
                  <span className="font-medium">{summary.moderate_count || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-red-500" />{"Critical (<80%)"}</span>
                  <span className="font-medium">{summary.critical_count || 0}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Recommendations */}
          {data.recommendations?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="plano-recommendations">
              <h3 className="font-semibold text-slate-900 mb-4">Actionable Recommendations</h3>
              <div className="space-y-3">
                {data.recommendations.map((rec, idx) => (
                  <div key={idx} className={`flex items-start gap-3 p-3 rounded-lg ${
                    rec.priority === 'high' ? 'bg-red-50 border border-red-100' : 'bg-amber-50 border border-amber-100'
                  }`}>
                    <AlertTriangle size={18} className={rec.priority === 'high' ? 'text-red-600 mt-0.5' : 'text-amber-600 mt-0.5'} />
                    <div>
                      <p className="font-medium text-slate-900 text-sm">{rec.title}</p>
                      <p className="text-sm text-slate-600">{rec.description}</p>
                      {rec.stores && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {rec.stores.slice(0, 5).map((s, i) => (
                            <span key={i} className="text-xs bg-white px-2 py-0.5 rounded-full text-slate-600 border border-slate-200">{s}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* View Toggle */}
          <div className="flex items-center gap-2 mb-4">
            <button data-testid="view-store-plano" onClick={() => setSelectedView("store")}
              className={`flex items-center gap-2 px-4 py-2 text-sm rounded transition-all ${
                selectedView === "store" ? 'bg-[#0176D3] text-white shadow-sm' : 'border border-slate-200 text-slate-600 hover:border-slate-400'
              }`}><Store size={16} /> Store View</button>
            <button data-testid="view-category-plano" onClick={() => setSelectedView("category")}
              className={`flex items-center gap-2 px-4 py-2 text-sm rounded transition-all ${
                selectedView === "category" ? 'bg-[#0176D3] text-white shadow-sm' : 'border border-slate-200 text-slate-600 hover:border-slate-400'
              }`}><Package size={16} /> Category View</button>
          </div>

          {/* Fill Rate Bar Chart */}
          {displayData.length > 0 && (
            <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="chart-fill-bars">
              <h3 className="font-semibold text-slate-900 mb-4">
                {selectedView === "store" ? "Store-wise" : "Category-wise"} Fill Rate
              </h3>
              <BarChart
                labels={displayData.slice(0, 15).map(d => selectedView === "store" ? d.store_code : d.category)}
                datasets={[
                  { label: 'Fill Rate %', data: displayData.slice(0, 15).map(d => d.fill_rate), color: '#0176D3' },
                  { label: 'Target (85%)', data: displayData.slice(0, 15).map(() => summary.target_fill_rate || 85), color: '#2E844A' },
                ]}
                height={280}
                formatValue={(v) => `${v}%`}
              />
            </div>
          )}

          {/* Summary Table */}
          {displayData.length > 0 && (
            <div className="bg-white border border-slate-200 rounded shadow-sm mb-8" data-testid="table-fill-summary">
              <div className="p-4 border-b border-slate-100">
                <h3 className="font-semibold text-slate-900">
                  {selectedView === "store" ? "Store-wise" : "Category-wise"} Fill Rate
                </h3>
                <p className="text-xs text-slate-500 mt-1">Fill Rate = (Current Stock / Norm Allocated) x 100</p>
              </div>
              <div className="overflow-x-auto">
                <table className="data-table w-full">
                  <thead>
                    <tr>
                      <th>{selectedView === "store" ? "Store" : "Category"}</th>
                      <th>Current Stock</th>
                      <th>Norm Allocated</th>
                      <th>Fill Rate</th>
                      <th>Status</th>
                      {selectedView === "store" && <th>Lost Sales</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {displayData.map((row, i) => (
                      <tr key={i}>
                        <td className="font-medium text-slate-900">
                          {selectedView === "store" ? row.store_code : row.category}
                        </td>
                        <td>{formatNumber(row.current_stock)}</td>
                        <td>{formatNumber(row.norm_allocated)}</td>
                        <td>
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden">
                              <div className={`h-full rounded-full ${
                                row.fill_rate >= 90 ? 'bg-green-500' :
                                row.fill_rate >= 80 ? 'bg-amber-500' : 'bg-red-500'
                              }`} style={{ width: `${Math.min(row.fill_rate, 100)}%` }} />
                            </div>
                            <span className="text-sm font-semibold">{row.fill_rate}%</span>
                          </div>
                        </td>
                        <td>{getStatusBadge(row.status)}</td>
                        {selectedView === "store" && (
                          <td className="text-red-600 font-medium">{formatCurrency(row.lost_sales)}</td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Detail Table */}
          {data.detail?.length > 0 && selectedView === "store" && (
            <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="table-fill-detail">
              <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900">Store-SKU Fill Rate Detail</h3>
                  <p className="text-xs text-slate-500 mt-1">Sorted by lowest fill rate first (most critical)</p>
                </div>
                <button onClick={handleExportCSV}
                  className="btn-secondary flex items-center gap-2 text-sm"
                  data-testid="export-detail-plano-btn">
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
                      <th>Stock</th>
                      <th>Norm</th>
                      <th>Fill Rate</th>
                      <th>Missing</th>
                      <th>Lost Sales</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.detail.slice(0, 50).map((row, i) => (
                      <tr key={i}>
                        <td className="font-medium text-slate-900">{row.store_code}</td>
                        <td>{row.ean}</td>
                        <td>{row.style}</td>
                        <td>{Math.round(row.current_stock)}</td>
                        <td>{Math.round(row.norm_allocated)}</td>
                        <td className={`font-semibold ${
                          row.fill_rate >= 90 ? 'text-green-600' :
                          row.fill_rate >= 80 ? 'text-amber-600' : 'text-red-600'
                        }`}>{row.fill_rate}%</td>
                        <td>{Math.round(row.missing_facings)}</td>
                        <td className="text-red-600">{formatCurrency(row.lost_sales)}</td>
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

      {!loading && !error && !data && (
        <div className="bg-slate-50 border border-slate-200 p-12 text-center rounded">
          <p className="text-slate-500 mb-2">No data available</p>
          <p className="text-sm text-slate-400">Upload the required files to see planogram fill rate analysis</p>
        </div>
      )}
    </div>
  );
};

export default PlanogramFillRate;
