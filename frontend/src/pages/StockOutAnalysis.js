import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  RefreshCw, Download, AlertTriangle, TrendingUp, TrendingDown,
  Store, Package, XCircle, Eye, X, ArrowRight
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import FilterPanel from "../components/FilterPanel";
import { LineChart, BarChart, DoughnutChart } from "../components/Charts";

const StockOutAnalysis = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedSKU, setSelectedSKU] = useState(null);
  const [filterOptions, setFilterOptions] = useState({});
  const [filters, setFilters] = useState({
    startDate: "",
    endDate: "",
    categories: [],
    channels: [],
    regions: [],
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
      const response = await axios.get(`${API}/analytics/stock-out?${queryParams}`);
      if (response.data.error) {
        setError(response.data.error);
      } else {
        setData(response.data);
      }
    } catch (err) {
      setError("Failed to fetch data. Please ensure required files are uploaded.");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { fetchData(); }, []);

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };
  const handleApplyFilters = () => fetchData();
  const handleResetFilters = () => {
    setFilters({
      startDate: filterOptions.dateRange?.min?.split('T')[0] || "",
      endDate: filterOptions.dateRange?.max?.split('T')[0] || "",
      categories: [], channels: [], regions: [],
    });
  };

  const formatCurrency = (value) => {
    if (!value) return "\u20B90";
    if (value >= 10000000) return `\u20B9${(value / 10000000).toFixed(1)}Cr`;
    if (value >= 100000) return `\u20B9${(value / 100000).toFixed(1)}L`;
    if (value >= 1000) return `\u20B9${(value / 1000).toFixed(0)}K`;
    return `\u20B9${Math.round(value)}`;
  };

  const formatNumber = (value) => {
    if (!value) return "0";
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(0)}K`;
    return Math.round(value).toString();
  };

  const handleExport = () => {
    const rows = data?.top_skus || [];
    if (rows.length === 0) return;
    const csv = [
      Object.keys(rows[0]).join(','),
      ...rows.map(row => Object.values(row).map(v => `"${v}"`).join(','))
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'stock_out_analysis.csv';
    a.click();
  };

  const getRiskBadge = (risk) => {
    const map = {
      critical: 'bg-red-100 text-red-800',
      high: 'bg-amber-100 text-amber-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-green-100 text-green-800',
    };
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${map[risk] || map.low}`}>
        {risk ? risk.charAt(0).toUpperCase() + risk.slice(1) : 'Low'}
      </span>
    );
  };

  return (
    <div className="animate-fade-in-up" data-testid="stock-out-page">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
            Stock-Out Analysis
          </h1>
          <p className="text-slate-500">
            {"PRD Formula: Stock-out when SOH = 0 AND Last 30 Days ROS > 0"}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button data-testid="refresh-stockout-btn" onClick={fetchData} disabled={loading}
            className="btn-secondary flex items-center gap-2">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button data-testid="export-stockout-btn" onClick={handleExport}
            className="btn-primary flex items-center gap-2">
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
        pageType="stock-out"
      />

      {/* PRD Formula Card */}
      <div className="bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="stockout-formula-card">
        <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <AlertTriangle size={16} className="text-[#0176D3]" />
          PRD Formulas: Stock-Out Analysis
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded border border-slate-200 p-4" data-testid="formula-stockout-id">
            <div className="text-xs font-semibold uppercase tracking-wider text-[#EA001E] mb-2">Stock-Out</div>
            <p className="text-sm text-slate-700 font-mono leading-relaxed">
              {"SOH = 0 AND Last 30 Days ROS > 0"}
            </p>
          </div>
          <div className="bg-white rounded border border-slate-200 p-4" data-testid="formula-daily-loss">
            <div className="text-xs font-semibold uppercase tracking-wider text-[#DD7A01] mb-2">Daily Sales Loss</div>
            <p className="text-sm text-slate-700 font-mono leading-relaxed">
              {"((ROS x 1) - SOH) x ASP"}
            </p>
          </div>
          <div className="bg-white rounded border border-slate-200 p-4" data-testid="formula-stockout-rate">
            <div className="text-xs font-semibold uppercase tracking-wider text-[#0176D3] mb-2">Stock-Out Rate</div>
            <p className="text-sm text-slate-700 font-mono leading-relaxed">
              (Stockouts / Total SKUs) x 100
            </p>
          </div>
          <div className="bg-white rounded border border-slate-200 p-4" data-testid="formula-severity">
            <div className="text-xs font-semibold uppercase tracking-wider text-[#706E6B] mb-2">Severity</div>
            <p className="text-sm text-slate-700 font-mono leading-relaxed">
              LostSales x Duration x Importance
            </p>
          </div>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-amber-50 border border-amber-200 p-8 mb-6 rounded text-center" data-testid="stockout-error">
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
        <div className="flex items-center justify-center py-20">
          <div className="spinner" />
        </div>
      )}

      {/* Main Content */}
      {data && !loading && !error && (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <KPICard
              testId="kpi-total-stockouts"
              label="Total Stock-Outs"
              value={formatNumber(data.summary?.total_stockouts)}
              sub={`of ${formatNumber(data.summary?.total_store_skus)} store-SKUs`}
              icon={<XCircle size={20} className="text-red-500" />}
              color="red"
            />
            <KPICard
              testId="kpi-stockout-rate"
              label="Stock-Out Rate"
              value={`${data.summary?.stockout_rate || 0}%`}
              sub="store-SKU combinations"
              icon={<AlertTriangle size={20} className="text-amber-500" />}
              color="amber"
            />
            <KPICard
              testId="kpi-lost-sales"
              label="Est. Daily Sales Loss"
              value={formatCurrency(data.summary?.total_lost_sales)}
              sub="revenue at risk per day"
              icon={<TrendingDown size={20} className="text-red-500" />}
              color="red"
            />
            <KPICard
              testId="kpi-stores-impacted"
              label="Stores Impacted"
              value={data.summary?.stores_impacted || 0}
              sub={`snapshot: ${data.summary?.snapshot_date || 'N/A'}`}
              icon={<Store size={20} className="text-[#0176D3]" />}
              color="blue"
            />
          </div>

          {/* Stock-Out Trend Chart */}
          {data.daily_trend?.length > 1 && (
            <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="chart-stockout-trend">
              <h3 className="font-semibold text-slate-900 mb-1">Stock-Out Trend</h3>
              <p className="text-xs text-slate-500 mb-4">Daily count of store-SKU stock-outs over time</p>
              <LineChart
                labels={data.daily_trend.map(d => d.date)}
                datasets={[{
                  label: 'Daily Stock-Outs',
                  data: data.daily_trend.map(d => d.stockout_count),
                  color: '#EA001E',
                  fill: true,
                }]}
                height={280}
                formatValue={formatNumber}
              />
            </div>
          )}

          {/* Two Column: Top Stores + Category Impact */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Top Impacted Stores */}
            {data.top_stores?.length > 0 && (
              <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="chart-top-stores">
                <div className="p-4 border-b border-slate-100">
                  <h3 className="font-semibold text-slate-900">Top Impacted Stores</h3>
                  <p className="text-xs text-slate-500 mt-1">Ranked by severity (LostSales x Duration)</p>
                </div>
                <BarChart
                  labels={data.top_stores.slice(0, 10).map(s => s.store_code)}
                  datasets={[{ label: 'Severity', data: data.top_stores.slice(0, 10).map(s => s.total_severity), color: '#EA001E' }]}
                  horizontal={true}
                  height={300}
                  formatValue={formatCurrency}
                  showLegend={false}
                />
              </div>
            )}

            {/* Category Impact */}
            {data.category_impact?.length > 0 && (
              <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="chart-category-impact">
                <div className="p-4 border-b border-slate-100">
                  <h3 className="font-semibold text-slate-900">Category-wise Impact</h3>
                  <p className="text-xs text-slate-500 mt-1">Lost sales by product category</p>
                </div>
                <div className="p-4">
                  <DoughnutChart
                    labels={data.category_impact.map(c => c.category || 'Unknown')}
                    data={data.category_impact.map(c => c.total_daily_loss)}
                    height={280}
                    formatValue={formatCurrency}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Top Impacted SKUs Table */}
          {data.top_skus?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded shadow-sm mb-8" data-testid="table-top-skus">
              <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900">Top Stock-Out SKUs</h3>
                  <p className="text-xs text-slate-500 mt-1">{"SKUs with SOH = 0 and active demand (ROS > 0), ranked by daily sales loss"}</p>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="data-table w-full">
                  <thead>
                    <tr>
                      <th>SKU</th>
                      <th>Style</th>
                      <th>Stores Affected</th>
                      <th>Avg ROS</th>
                      <th>Avg ASP</th>
                      <th>Daily Loss</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.top_skus.map((row, i) => (
                      <tr key={i}>
                        <td className="font-medium text-slate-900">{row.sku}</td>
                        <td>{row.style || '-'}</td>
                        <td>{row.stockout_count}</td>
                        <td>{(row.avg_ros || 0).toFixed(1)}</td>
                        <td>{formatCurrency(row.avg_asp)}</td>
                        <td className="text-red-600 font-semibold">{formatCurrency(row.total_daily_loss)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Top Impacted Stores Table */}
          {data.top_stores?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded shadow-sm mb-8" data-testid="table-top-stores">
              <div className="p-4 border-b border-slate-100">
                <h3 className="font-semibold text-slate-900">Store-wise Stock-Out Impact</h3>
                <p className="text-xs text-slate-500 mt-1">Ranked by severity score</p>
              </div>
              <div className="overflow-x-auto">
                <table className="data-table w-full">
                  <thead>
                    <tr>
                      <th>Store</th>
                      <th>Stock-Out SKUs</th>
                      <th>Avg Duration</th>
                      <th>Daily Loss</th>
                      <th>Severity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.top_stores.map((row, i) => (
                      <tr key={i}>
                        <td className="font-medium text-slate-900">{row.store_code}</td>
                        <td>{row.stockout_count}</td>
                        <td>{row.avg_duration} days</td>
                        <td className="text-red-600">{formatCurrency(row.total_daily_loss)}</td>
                        <td>
                          <span className={`badge ${
                            row.total_severity > 100000 ? 'badge-understock' :
                            row.total_severity > 50000 ? 'bg-amber-100 text-amber-700' :
                            'badge-optimal'
                          }`}>
                            {formatCurrency(row.total_severity)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* High-Risk SKUs */}
          {data.high_risk_skus?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded shadow-sm mb-8" data-testid="table-high-risk">
              <div className="p-4 border-b border-slate-100">
                <h3 className="font-semibold text-slate-900">High-Risk SKUs (Next 7 Days)</h3>
                <p className="text-xs text-slate-500 mt-1">{"SKUs approaching stock-out based on current ROS vs SOH"}</p>
              </div>
              <div className="overflow-x-auto">
                <table className="data-table w-full">
                  <thead>
                    <tr>
                      <th>SKU</th>
                      <th>Style</th>
                      <th>Store</th>
                      <th>ROS (units/day)</th>
                      <th>Current SOH</th>
                      <th>ASP</th>
                      <th>Days to Stock-Out</th>
                      <th>Risk</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.high_risk_skus.map((row, i) => (
                      <tr key={i}>
                        <td className="font-medium text-slate-900">{row.sku}</td>
                        <td>{row.style || '-'}</td>
                        <td>{row.store_code}</td>
                        <td>{(row.ros || 0).toFixed(1)}</td>
                        <td>{Math.round(row.soh)}</td>
                        <td>{formatCurrency(row.asp)}</td>
                        <td className="font-semibold text-red-600">{row.days_to_stockout} days</td>
                        <td>{getRiskBadge(row.risk)}</td>
                        <td>
                          <button
                            onClick={() => setSelectedSKU(row)}
                            className="text-[#0176D3] hover:text-blue-700 text-sm flex items-center gap-1"
                            data-testid={`detail-btn-${i}`}
                          >
                            <Eye size={14} /> Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Recommendations */}
          <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="recommendations-section">
            <div className="p-4 border-b border-slate-100">
              <h3 className="font-semibold text-slate-900">Actionable Recommendations</h3>
              <p className="text-xs text-slate-500 mt-1">Based on PRD stock-out analysis framework</p>
            </div>
            <div className="divide-y divide-slate-100">
              {data.top_skus?.length > 0 && (
                <RecommendationCard
                  icon={<Package size={18} className="text-red-600" />}
                  iconBg="bg-red-50"
                  title="Urgent Replenishment Required"
                  priority="High"
                  priorityColor="badge-understock"
                  description={`${data.summary?.total_stockouts} store-SKU combinations are currently stocked out with active demand.`}
                  impact={`Est. ${formatCurrency(data.summary?.total_lost_sales)} daily sales loss`}
                  detail={`Top: ${data.top_skus.slice(0, 3).map(s => s.sku).join(', ')}`}
                />
              )}
              {data.high_risk_skus?.length > 0 && (
                <RecommendationCard
                  icon={<AlertTriangle size={18} className="text-amber-600" />}
                  iconBg="bg-amber-50"
                  title="Preventive Stock Monitoring"
                  priority="Medium"
                  priorityColor="bg-amber-100 text-amber-700"
                  description={`${data.high_risk_skus.length} SKUs will hit stock-out within 7 days at current sales velocity.`}
                  impact={`${data.high_risk_skus.filter(s => s.risk === 'critical').length} critical, ${data.high_risk_skus.filter(s => s.risk === 'high').length} high risk`}
                  detail={`Lowest: ${data.high_risk_skus[0]?.sku} (${data.high_risk_skus[0]?.days_to_stockout} days)`}
                />
              )}
              <RecommendationCard
                icon={<TrendingUp size={18} className="text-green-600" />}
                iconBg="bg-green-50"
                title="Safety Stock Optimization"
                priority="Low"
                priorityColor="badge-optimal"
                description="Review and increase safety stock levels for high-velocity SKUs to prevent recurring stock-outs."
                impact="Potential 15-25% reduction in stock-out occurrences"
                detail="Based on ROS velocity patterns across stores"
              />
            </div>
          </div>
        </>
      )}

      {/* SKU Detail Modal */}
      {selectedSKU && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" data-testid="sku-detail-modal">
          <div className="bg-white rounded-lg max-w-lg w-full mx-4 shadow-xl">
            <div className="flex items-center justify-between p-4 border-b border-slate-100">
              <div>
                <h3 className="font-semibold text-slate-900">SKU Details: {selectedSKU.sku}</h3>
                <p className="text-xs text-slate-500">Stock-out risk analysis</p>
              </div>
              <button onClick={() => setSelectedSKU(null)} className="text-slate-400 hover:text-slate-600">
                <X size={20} />
              </button>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-slate-50 rounded p-3 text-center">
                  <p className="text-xs text-slate-500">Current ROS</p>
                  <p className="text-xl font-bold text-slate-900">{(selectedSKU.ros || 0).toFixed(1)}</p>
                  <p className="text-xs text-slate-400">units/day</p>
                </div>
                <div className="bg-slate-50 rounded p-3 text-center">
                  <p className="text-xs text-slate-500">Days to Stock-Out</p>
                  <p className="text-xl font-bold text-red-600">{selectedSKU.days_to_stockout}</p>
                  <p className="text-xs text-slate-400">days remaining</p>
                </div>
                <div className="bg-slate-50 rounded p-3 text-center">
                  <p className="text-xs text-slate-500">Current SOH</p>
                  <p className="text-xl font-bold text-slate-900">{Math.round(selectedSKU.soh)}</p>
                  <p className="text-xs text-slate-400">units</p>
                </div>
                <div className="bg-slate-50 rounded p-3 text-center">
                  <p className="text-xs text-slate-500">ASP</p>
                  <p className="text-xl font-bold text-slate-900">{formatCurrency(selectedSKU.asp)}</p>
                  <p className="text-xs text-slate-400">per unit</p>
                </div>
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded p-4 mb-4">
                <h4 className="font-medium text-blue-900 text-sm mb-2">PRD Calculation</h4>
                <p className="text-sm text-blue-700 font-mono">
                  {"Daily Sales Loss = ((ROS x 1) - SOH) x ASP"}
                </p>
                <p className="text-sm text-blue-700 mt-1">
                  = (({(selectedSKU.ros || 0).toFixed(1)} x 1) - {Math.round(selectedSKU.soh)}) x {formatCurrency(selectedSKU.asp)}
                </p>
                <p className="text-sm font-semibold text-blue-900 mt-1">
                  = {formatCurrency(Math.max(0, ((selectedSKU.ros * 1) - selectedSKU.soh) * selectedSKU.asp))}/day
                </p>
              </div>
              <div className="flex gap-3">
                <button className="flex-1 btn-primary text-center" onClick={() => setSelectedSKU(null)}>
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};


/* KPI Card sub-component */
const KPICard = ({ testId, label, value, sub, icon, color }) => (
  <div className="metric-card" data-testid={testId}>
    <div className="flex items-center justify-between mb-2">
      <span className="metric-label">{label}</span>
      {icon}
    </div>
    <span className={`metric-value ${
      color === 'red' ? 'text-red-600' :
      color === 'amber' ? 'text-amber-600' :
      color === 'green' ? 'text-green-600' :
      'text-[#0176D3]'
    }`}>{value}</span>
    <span className="text-xs text-slate-500 mt-1 block">{sub}</span>
  </div>
);


/* Recommendation Card sub-component */
const RecommendationCard = ({ icon, iconBg, title, priority, priorityColor, description, impact, detail }) => (
  <div className="p-4 hover:bg-slate-50 transition-colors">
    <div className="flex items-start gap-3">
      <div className={`p-2 rounded-lg ${iconBg}`}>{icon}</div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <h4 className="font-medium text-slate-900 text-sm">{title}</h4>
          <span className={`badge ${priorityColor}`}>{priority}</span>
        </div>
        <p className="text-sm text-slate-600">{description}</p>
        <div className="mt-2 flex flex-wrap gap-4 text-xs text-slate-500">
          <span>Impact: {impact}</span>
          <span>{detail}</span>
        </div>
      </div>
    </div>
  </div>
);


export default StockOutAnalysis;
