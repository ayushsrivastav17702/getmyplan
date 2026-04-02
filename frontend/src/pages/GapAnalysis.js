import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import { RefreshCw, Download, Users, Briefcase, BarChart3, TrendingDown, ShieldCheck, AlertTriangle, Activity } from "lucide-react";
import FilterPanel from "../components/FilterPanel";
import { BarChart, DoughnutChart, StackedBarChart } from "../components/Charts";

const GapAnalysis = () => {
  const [activeTab, setActiveTab] = useState("noos");
  const [persona, setPersona] = useState("cxo");
  const [noosData, setNoosData] = useState(null);
  const [sizeGapData, setSizeGapData] = useState(null);
  const [rosGapData, setRosGapData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filterOptions, setFilterOptions] = useState({});
  const [filters, setFilters] = useState({
    startDate: "",
    endDate: "",
    categories: [],
    channels: [],
    regions: [],
    understockThreshold: -5,
    overstockThreshold: 5
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
    if (activeTab === "size-gap") {
      params.append('understock_threshold', filters.understockThreshold);
      params.append('overstock_threshold', filters.overstockThreshold);
    }
    return params.toString();
  };

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    const queryParams = buildQueryParams();

    try {
      if (activeTab === "noos") {
        const response = await axios.get(`${API}/analytics/noos?${queryParams}`);
        if (response.data.error) setError(response.data.error);
        else setNoosData(response.data);
      } else if (activeTab === "size-gap") {
        const response = await axios.get(`${API}/analytics/size-gap?${queryParams}`);
        if (response.data.error) setError(response.data.error);
        else setSizeGapData(response.data);
      } else if (activeTab === "ros-gap") {
        const response = await axios.get(`${API}/analytics/ros-gap?${queryParams}`);
        if (response.data.error) setError(response.data.error);
        else setRosGapData(response.data);
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
      understockThreshold: -5,
      overstockThreshold: 5
    });
  };

  const tabs = [
    { key: "noos", label: "NOOS Analysis" },
    { key: "size-gap", label: "Size Set Gap" },
    { key: "ros-gap", label: "ROS Gap Analysis" },
  ];

  const personas = [
    { key: "cxo", label: "CXO View", icon: Users, description: "High-level metrics and revenue impact" },
    { key: "merchandiser", label: "Merchandiser", icon: Briefcase, description: "Detailed style-level analysis" },
    { key: "consultant", label: "Consultant", icon: BarChart3, description: "Methodology and calculations" },
  ];

  const formatCurrency = (value) => {
    if (!value) return "\u20B90";
    if (value >= 1000000) return `\u20B9${(value / 1000000).toFixed(1)}M`;
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
    let data = [];
    if (activeTab === "noos") data = noosData?.data || [];
    else if (activeTab === "size-gap") data = sizeGapData?.data || [];
    else if (activeTab === "ros-gap") data = rosGapData?.style_ros_gap || [];
    if (data.length === 0) return;

    const csv = [
      Object.keys(data[0]).join(','),
      ...data.map(row => Object.values(row).map(v => `"${v}"`).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${activeTab}_analysis.csv`;
    a.click();
  };

  return (
    <div className="animate-fade-in-up" data-testid="gap-analysis-page">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
            Gap Analysis
          </h1>
          <p className="text-slate-500">
            Identify sales gaps and optimization opportunities
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            data-testid="refresh-gap-btn"
            onClick={fetchData}
            disabled={loading}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button
            data-testid="export-gap-btn"
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
        pageType="gap-analysis"
      />

      {/* Persona Selector */}
      <div className="mb-6">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-3">
          View As
        </span>
        <div className="flex flex-wrap gap-2">
          {personas.map((p) => {
            const Icon = p.icon;
            return (
              <button
                key={p.key}
                data-testid={`persona-${p.key}`}
                onClick={() => setPersona(p.key)}
                className={`flex items-center gap-2 px-4 py-2 text-sm rounded transition-all ${
                  persona === p.key
                    ? 'bg-[#0176D3] text-white shadow-sm'
                    : 'border border-slate-200 text-slate-600 hover:border-slate-400'
                }`}
              >
                <Icon size={16} />
                {p.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            data-testid={`gap-tab-${tab.key}`}
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

      {/* ==================== NOOS Analysis Tab ==================== */}
      {activeTab === "noos" && noosData && !loading && (
        <NOOSTab noosData={noosData} persona={persona} formatCurrency={formatCurrency} formatNumber={formatNumber} />
      )}

      {/* ==================== Size Gap Tab ==================== */}
      {activeTab === "size-gap" && sizeGapData && !loading && (
        <SizeGapTab sizeGapData={sizeGapData} persona={persona} formatCurrency={formatCurrency} formatNumber={formatNumber} />
      )}

      {/* ==================== ROS Gap Tab ==================== */}
      {activeTab === "ros-gap" && rosGapData && !loading && (
        <ROSGapTab rosGapData={rosGapData} persona={persona} formatCurrency={formatCurrency} formatNumber={formatNumber} />
      )}

      {/* Empty State */}
      {!loading && !error && (
        (activeTab === "noos" && !noosData?.data?.length) ||
        (activeTab === "size-gap" && !sizeGapData?.data?.length) ||
        (activeTab === "ros-gap" && !rosGapData?.style_ros_gap?.length)
      ) && (
        <div className="bg-slate-50 border border-slate-200 p-12 text-center rounded">
          <p className="text-slate-500 mb-2">No data available</p>
          <p className="text-sm text-slate-400">
            Upload the required files to see gap analysis
          </p>
        </div>
      )}
    </div>
  );
};


/* ==================== NOOS Analysis Sub-component ==================== */
const NOOSTab = ({ noosData, persona, formatCurrency, formatNumber }) => (
  <div data-testid="noos-analysis-section">
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div className="metric-card">
        <span className="metric-label">Store-Style Combinations</span>
        <span className="metric-value">{formatNumber(noosData.summary?.total_combinations)}</span>
      </div>
      <div className="metric-card">
        <span className="metric-label">NOOS Candidates</span>
        <span className="metric-value text-green-600">{formatNumber(noosData.summary?.noos_candidates)}</span>
      </div>
      <div className="metric-card">
        <span className="metric-label">Avg Availability</span>
        <span className="metric-value">{noosData.summary?.avg_availability?.toFixed(1)}%</span>
      </div>
      <div className="metric-card">
        <span className="metric-label">Total Revenue</span>
        <span className="metric-value">{formatCurrency(noosData.summary?.total_revenue)}</span>
      </div>
    </div>

    {persona === "cxo" && (
      <div className="bg-blue-50 border border-blue-200 p-6 mb-8 rounded">
        <h3 className="font-semibold text-slate-900 mb-2">Executive Insight</h3>
        <p className="text-slate-700">
          {noosData.summary?.noos_candidates > 0
            ? `${noosData.summary?.noos_candidates} store-style combinations qualify as NOOS candidates with high availability and proven sales performance. Maintaining stock for these items could prevent significant revenue loss.`
            : "Analyze your inventory to identify NOOS candidates that should always remain in stock."}
        </p>
      </div>
    )}

    {noosData.data?.length > 0 && (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
          <h3 className="font-semibold text-slate-900 mb-4">NOOS Candidate Distribution</h3>
          <DoughnutChart
            labels={['NOOS Candidates', 'Non-NOOS']}
            data={[
              noosData.summary?.noos_candidates || 0,
              (noosData.summary?.total_combinations || 0) - (noosData.summary?.noos_candidates || 0)
            ]}
            height={260}
          />
        </div>
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
          <h3 className="font-semibold text-slate-900 mb-4">Top Styles by Revenue</h3>
          {(() => {
            const styleRevenue = {};
            noosData.data.forEach(row => {
              if (row.style && row.revenue) {
                styleRevenue[row.style] = (styleRevenue[row.style] || 0) + row.revenue;
              }
            });
            const sorted = Object.entries(styleRevenue).sort((a, b) => b[1] - a[1]).slice(0, 10);
            return (
              <BarChart
                labels={sorted.map(([s]) => s)}
                datasets={[{ label: 'Revenue', data: sorted.map(([, v]) => v), color: '#0176D3' }]}
                horizontal={true}
                height={260}
                formatValue={formatCurrency}
                showLegend={false}
              />
            );
          })()}
        </div>
      </div>
    )}

    {persona === "consultant" && (
      <div className="bg-white border border-slate-200 p-6 mb-8 rounded shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">NOOS Methodology</h3>
        <div className="space-y-4 text-sm text-slate-600">
          <div className="p-4 bg-slate-50 border border-slate-100 rounded">
            <h4 className="font-semibold text-slate-900 mb-2">Definition</h4>
            <p>NOOS (Never Out Of Stock) identifies styles that should always be available based on consistent demand and high availability performance.</p>
          </div>
          <div className="p-4 bg-slate-50 border border-slate-100 rounded">
            <h4 className="font-semibold text-slate-900 mb-2">Qualification Criteria</h4>
            <ul className="list-disc list-inside space-y-1">
              <li>{"Exposure days >= Minimum shelf life threshold (configurable)"}</li>
              <li>Positive sales quantity during the analysis period</li>
              <li>{"Availability percentage >= 80%"}</li>
            </ul>
          </div>
          <div className="p-4 bg-slate-50 border border-slate-100 rounded">
            <h4 className="font-semibold text-slate-900 mb-2">Key Metrics</h4>
            <ul className="list-disc list-inside space-y-1">
              <li><strong>Exposure Days:</strong> Days with positive inventory</li>
              <li><strong>Availability %:</strong> (Exposure Days / Total Days) x 100</li>
              <li><strong>NOOS Gap:</strong> Revenue lost due to stockouts for NOOS items</li>
            </ul>
          </div>
        </div>
      </div>
    )}

    {(persona === "merchandiser" || persona === "cxo") && (
      <div className="bg-white border border-slate-200 rounded shadow-sm">
        <div className="p-4 border-b border-slate-100">
          <h3 className="font-semibold text-slate-900">NOOS Candidate Details</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table w-full">
            <thead>
              <tr>
                <th>Store</th>
                <th>Style</th>
                <th>Exposure Days</th>
                <th>Availability %</th>
                <th>Quantity</th>
                <th>Revenue</th>
                <th>NOOS</th>
              </tr>
            </thead>
            <tbody>
              {noosData.data?.slice(0, 25).map((row, i) => (
                <tr key={i}>
                  <td className="font-medium text-slate-900">{row.store_code}</td>
                  <td>{row.style}</td>
                  <td>{row.exposure_days}</td>
                  <td>{row.availability_pct?.toFixed(1)}%</td>
                  <td>{formatNumber(row.quantity)}</td>
                  <td>{formatCurrency(row.revenue)}</td>
                  <td>
                    <span className={`badge ${row.noos_candidate ? 'badge-healthy' : 'bg-slate-100 text-slate-500'}`}>
                      {row.noos_candidate ? "Yes" : "No"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )}
  </div>
);


/* ==================== Size Gap Sub-component ==================== */
const SizeGapTab = ({ sizeGapData, persona, formatCurrency, formatNumber }) => (
  <div data-testid="size-gap-section">
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div className="metric-card">
        <span className="metric-label">Overstock</span>
        <span className="metric-value text-amber-600">{sizeGapData.summary?.overstock || 0}</span>
      </div>
      <div className="metric-card">
        <span className="metric-label">Understock</span>
        <span className="metric-value text-red-600">{sizeGapData.summary?.understock || 0}</span>
      </div>
      <div className="metric-card">
        <span className="metric-label">Optimal</span>
        <span className="metric-value text-green-600">{sizeGapData.summary?.optimal || 0}</span>
      </div>
      <div className="metric-card">
        <span className="metric-label">Total Gap</span>
        <span className="metric-value">{formatNumber(sizeGapData.summary?.total_gap)}</span>
        <span className="text-sm text-slate-500">units</span>
      </div>
    </div>

    {sizeGapData.data?.length > 0 && (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
          <h3 className="font-semibold text-slate-900 mb-4">Status Distribution</h3>
          <DoughnutChart
            labels={['Overstock', 'Understock', 'Optimal']}
            data={[
              sizeGapData.summary?.overstock || 0,
              sizeGapData.summary?.understock || 0,
              sizeGapData.summary?.optimal || 0
            ]}
            height={260}
          />
        </div>
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
          <h3 className="font-semibold text-slate-900 mb-4">Gap by Style (Top 10)</h3>
          {(() => {
            const styleGap = {};
            sizeGapData.data.forEach(row => {
              if (row.style) {
                styleGap[row.style] = (styleGap[row.style] || 0) + Math.abs(row.gap || 0);
              }
            });
            const sorted = Object.entries(styleGap).sort((a, b) => b[1] - a[1]).slice(0, 10);
            return (
              <BarChart
                labels={sorted.map(([s]) => s)}
                datasets={[{ label: 'Abs Gap', data: sorted.map(([, v]) => v), color: '#EA001E' }]}
                horizontal={true}
                height={260}
                formatValue={formatNumber}
                showLegend={false}
              />
            );
          })()}
        </div>
      </div>
    )}

    <div className="bg-white border border-slate-200 rounded shadow-sm">
      <div className="p-4 border-b border-slate-100">
        <h3 className="font-semibold text-slate-900">Size Gap Details</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="data-table w-full">
          <thead>
            <tr>
              <th>Style</th>
              <th>Size</th>
              <th>Current Qty</th>
              <th>Ideal Qty</th>
              <th>Gap</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {sizeGapData.data?.slice(0, 25).map((row, i) => (
              <tr key={i}>
                <td className="font-medium text-slate-900">{row.style}</td>
                <td>{row.size}</td>
                <td>{formatNumber(row.current_qty)}</td>
                <td>{formatNumber(row.ideal_qty)}</td>
                <td className={row.gap > 0 ? 'text-amber-600' : row.gap < 0 ? 'text-red-600' : 'text-green-600'}>
                  {row.gap > 0 ? '+' : ''}{formatNumber(row.gap)}
                </td>
                <td>
                  <span className={`badge ${
                    row.status === 'Overstock' ? 'badge-overstock' :
                    row.status === 'Understock' ? 'badge-understock' :
                    'badge-optimal'
                  }`}>
                    {row.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </div>
);


/* ==================== ROS Gap Sub-component ==================== */
const ROSGapTab = ({ rosGapData, persona, formatCurrency, formatNumber }) => {
  const summary = rosGapData.summary || {};
  const styleData = rosGapData.style_ros_gap || [];
  const storeData = rosGapData.store_health || [];
  const noosStyles = rosGapData.noos_styles || [];

  return (
    <div data-testid="ros-gap-section">
      {/* PRD Formula Card */}
      <div className="bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded shadow-sm p-6 mb-8">
        <div className="flex items-center gap-2 mb-4">
          <Activity size={20} className="text-[#0176D3]" />
          <h3 className="text-lg font-semibold text-slate-900">PRD Formulas</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded border border-slate-200 p-4" data-testid="formula-raw-ros">
            <div className="text-xs font-semibold uppercase tracking-wider text-[#0176D3] mb-2">Raw ROS</div>
            <p className="text-sm text-slate-700 font-mono leading-relaxed">
              Net Sales Qty (30d) / True Live Days (30d)
            </p>
          </div>
          <div className="bg-white rounded border border-slate-200 p-4" data-testid="formula-healthy-size">
            <div className="text-xs font-semibold uppercase tracking-wider text-[#2E844A] mb-2">Healthy Size Set</div>
            <p className="text-sm text-slate-700 font-mono leading-relaxed">
              {">="}  75% sizes available in store-style-day
            </p>
          </div>
          <div className="bg-white rounded border border-slate-200 p-4" data-testid="formula-sales-loss">
            <div className="text-xs font-semibold uppercase tracking-wider text-[#EA001E] mb-2">Sales Loss</div>
            <p className="text-sm text-slate-700 font-mono leading-relaxed">
              (Healthy ROS x Broken Days) - Actual Broken Sales
            </p>
          </div>
          <div className="bg-white rounded border border-slate-200 p-4" data-testid="formula-noos">
            <div className="text-xs font-semibold uppercase tracking-wider text-[#DD7A01] mb-2">NOOS</div>
            <p className="text-sm text-slate-700 font-mono leading-relaxed">
              {"Sales >80% days + Inventory >80% days"}
            </p>
          </div>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="metric-card" data-testid="kpi-avg-ros-gap">
          <div className="flex items-center gap-2 mb-1">
            <TrendingDown size={16} className="text-[#0176D3]" />
            <span className="metric-label">Avg ROS Gap</span>
          </div>
          <span className="metric-value">{summary.avg_ros_gap?.toFixed(2) || "0"}</span>
          <span className="text-xs text-slate-500">units/day</span>
        </div>
        <div className="metric-card" data-testid="kpi-total-sales-loss">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle size={16} className="text-[#EA001E]" />
            <span className="metric-label">Total Sales Loss</span>
          </div>
          <span className="metric-value text-red-600">{formatNumber(summary.total_sales_loss)}</span>
          <span className="text-xs text-slate-500">units lost</span>
        </div>
        <div className="metric-card" data-testid="kpi-healthy-coverage">
          <div className="flex items-center gap-2 mb-1">
            <ShieldCheck size={16} className="text-[#2E844A]" />
            <span className="metric-label">Healthy Size Set Coverage</span>
          </div>
          <span className="metric-value text-green-600">{summary.healthy_coverage_pct || 0}%</span>
          <span className="text-xs text-slate-500">{summary.healthy_styles || 0} healthy / {summary.total_styles || 0} total</span>
        </div>
        <div className="metric-card" data-testid="kpi-noos-styles">
          <div className="flex items-center gap-2 mb-1">
            <Activity size={16} className="text-[#DD7A01]" />
            <span className="metric-label">NOOS Qualified Styles</span>
          </div>
          <span className="metric-value text-amber-600">{summary.noos_styles || 0}</span>
          <span className="text-xs text-slate-500">of {summary.total_noos_candidates || 0} candidates</span>
        </div>
      </div>

      {/* CXO Executive Insight */}
      {persona === "cxo" && (
        <div className="bg-blue-50 border border-blue-200 p-6 mb-8 rounded" data-testid="ros-cxo-insight">
          <h3 className="font-semibold text-slate-900 mb-2">Executive Insight</h3>
          <p className="text-slate-700">
            {summary.total_sales_loss > 0
              ? `Broken size sets are costing approximately ${formatNumber(summary.total_sales_loss)} units in lost sales. ${summary.broken_styles || 0} styles are classified as "Broken" with less than 75% size availability. Improving size set health to ${summary.healthy_coverage_pct || 0}% coverage could recover significant revenue.`
              : "All styles are performing optimally with healthy size set coverage. Continue monitoring to maintain performance."}
          </p>
          {summary.noos_styles > 0 && (
            <p className="text-slate-600 mt-2 text-sm">
              {summary.noos_styles} styles qualify as Never-Out-Of-Stock (NOOS) based on consistent sales and inventory patterns.
            </p>
          )}
        </div>
      )}

      {/* Charts Row */}
      {styleData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white border border-slate-200 rounded shadow-sm p-6" data-testid="chart-style-status">
            <h3 className="font-semibold text-slate-900 mb-4">Style Health Distribution</h3>
            <DoughnutChart
              labels={['Healthy', 'Broken']}
              data={[summary.healthy_styles || 0, summary.broken_styles || 0]}
              height={260}
            />
          </div>
          <div className="bg-white border border-slate-200 rounded shadow-sm p-6" data-testid="chart-sales-loss-by-style">
            <h3 className="font-semibold text-slate-900 mb-4">Top 10 Sales Loss by Style</h3>
            {(() => {
              const top = styleData.filter(s => s.total_sales_loss > 0).slice(0, 10);
              return (
                <BarChart
                  labels={top.map(s => s.style || 'Unknown')}
                  datasets={[{ label: 'Sales Loss (units)', data: top.map(s => s.total_sales_loss), color: '#EA001E' }]}
                  horizontal={true}
                  height={260}
                  formatValue={formatNumber}
                  showLegend={false}
                />
              );
            })()}
          </div>
        </div>
      )}

      {/* Store Health Chart */}
      {storeData.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="chart-store-health">
          <h3 className="font-semibold text-slate-900 mb-4">Store-wise Size Set Health</h3>
          <StackedBarChart
            labels={storeData.slice(0, 15).map(s => s.store_code)}
            datasets={[
              { label: 'Healthy %', data: storeData.slice(0, 15).map(s => s.healthy_pct), color: '#2E844A' },
              { label: 'Broken %', data: storeData.slice(0, 15).map(s => s.broken_pct), color: '#EA001E' },
            ]}
            height={300}
            formatValue={(v) => `${v}%`}
          />
        </div>
      )}

      {/* Consultant Methodology */}
      {persona === "consultant" && (
        <div className="bg-white border border-slate-200 p-6 mb-8 rounded shadow-sm" data-testid="ros-consultant-methodology">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">ROS Gap Methodology</h3>
          <div className="space-y-4 text-sm text-slate-600">
            <div className="p-4 bg-slate-50 border border-slate-100 rounded">
              <h4 className="font-semibold text-slate-900 mb-2">Raw ROS Calculation</h4>
              <p>Raw Rate of Sale is computed per store-style combination.</p>
              <code className="block mt-2 p-3 bg-slate-100 rounded text-xs font-mono text-slate-800">
                Raw ROS = Net Sales Qty (Last 30 days) / True Live Days (Last 30 days)
              </code>
              <p className="mt-2">{"True Live Days = days where any size had positive inventory (stock > 0)."}</p>
            </div>
            <div className="p-4 bg-slate-50 border border-slate-100 rounded">
              <h4 className="font-semibold text-slate-900 mb-2">Healthy Size Set Definition</h4>
              <code className="block mt-2 p-3 bg-slate-100 rounded text-xs font-mono text-slate-800">
                {"Healthy Day = (Available Sizes / Total Sizes for Style) >= 75%"}
              </code>
              <p className="mt-2">A store-style-day is classified as "Healthy" when at least 75% of the style's sizes have positive inventory. Days below this threshold are "Broken".</p>
            </div>
            <div className="p-4 bg-slate-50 border border-slate-100 rounded">
              <h4 className="font-semibold text-slate-900 mb-2">Sales Loss Calculation</h4>
              <code className="block mt-2 p-3 bg-slate-100 rounded text-xs font-mono text-slate-800">
                Healthy ROS = Sales on Healthy Days / Healthy Day Count{"\n"}
                Sales Loss = (Healthy ROS x Broken Days) - Actual Broken Day Sales
              </code>
              <p className="mt-2">Sales Loss estimates the units that would have been sold on broken days if the size set had been healthy.</p>
            </div>
            <div className="p-4 bg-slate-50 border border-slate-100 rounded">
              <h4 className="font-semibold text-slate-900 mb-2">NOOS Qualification</h4>
              <code className="block mt-2 p-3 bg-slate-100 rounded text-xs font-mono text-slate-800">
                {"NOOS = Sales on >80% of period days AND Inventory on >80% of period days"}
              </code>
              <p className="mt-2">Styles that maintain consistent sales and inventory across the majority of stores are flagged as Never-Out-Of-Stock candidates.</p>
            </div>
          </div>
        </div>
      )}

      {/* Style-wise ROS Gap Table */}
      {(persona === "merchandiser" || persona === "cxo") && styleData.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm mb-8" data-testid="table-style-ros-gap">
          <div className="p-4 border-b border-slate-100">
            <h3 className="font-semibold text-slate-900">Style-wise ROS Gap</h3>
            <p className="text-xs text-slate-500 mt-1">Sorted by sales loss (highest first)</p>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table w-full">
              <thead>
                <tr>
                  <th>Style</th>
                  <th>Healthy ROS</th>
                  <th>Actual ROS</th>
                  <th>ROS Gap</th>
                  <th>Sales Loss</th>
                  <th>Stores</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {styleData.slice(0, 30).map((row, i) => (
                  <tr key={i}>
                    <td className="font-medium text-slate-900">{row.style}</td>
                    <td>{(row.healthy_ros || 0).toFixed(2)}</td>
                    <td>{(row.raw_ros || 0).toFixed(2)}</td>
                    <td className={row.ros_gap > 0 ? 'text-red-600 font-semibold' : 'text-green-600'}>
                      {row.ros_gap > 0 ? '+' : ''}{(row.ros_gap || 0).toFixed(2)}
                    </td>
                    <td className="text-red-600 font-medium">{formatNumber(row.total_sales_loss)}</td>
                    <td>{row.store_count}</td>
                    <td>
                      <span className={`badge ${row.status === 'Healthy' ? 'badge-healthy' : 'badge-understock'}`}>
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Store-wise Size Set Health Table */}
      {(persona === "merchandiser" || persona === "cxo") && storeData.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm mb-8" data-testid="table-store-health">
          <div className="p-4 border-b border-slate-100">
            <h3 className="font-semibold text-slate-900">Store-wise Size Set Health</h3>
            <p className="text-xs text-slate-500 mt-1">Sorted by sales loss (highest first)</p>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table w-full">
              <thead>
                <tr>
                  <th>Store</th>
                  <th>Healthy %</th>
                  <th>Broken %</th>
                  <th>Sales Loss</th>
                  <th>Styles</th>
                </tr>
              </thead>
              <tbody>
                {storeData.slice(0, 25).map((row, i) => (
                  <tr key={i}>
                    <td className="font-medium text-slate-900">{row.store_code}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-green-500 rounded-full" style={{ width: `${row.healthy_pct}%` }} />
                        </div>
                        <span className="text-green-600 text-sm">{row.healthy_pct}%</span>
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-red-500 rounded-full" style={{ width: `${row.broken_pct}%` }} />
                        </div>
                        <span className="text-red-600 text-sm">{row.broken_pct}%</span>
                      </div>
                    </td>
                    <td className="text-red-600 font-medium">{formatNumber(row.total_sales_loss)}</td>
                    <td>{row.style_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* NOOS Style Analysis */}
      {noosStyles.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="table-noos-styles">
          <div className="p-4 border-b border-slate-100">
            <h3 className="font-semibold text-slate-900">NOOS Style Analysis</h3>
            <p className="text-xs text-slate-500 mt-1">{"Styles that should never be out of stock (sales + inventory on >80% of days)"}</p>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table w-full">
              <thead>
                <tr>
                  <th>Style</th>
                  <th>Stores</th>
                  <th>NOOS Stores</th>
                  <th>Sales Consistency</th>
                  <th>Inventory Consistency</th>
                  <th>NOOS %</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {noosStyles.slice(0, 25).map((row, i) => (
                  <tr key={i}>
                    <td className="font-medium text-slate-900">{row.style}</td>
                    <td>{row.store_count}</td>
                    <td>{row.noos_store_count}</td>
                    <td>{row.avg_sales_consistency?.toFixed(1)}%</td>
                    <td>{row.avg_inv_consistency?.toFixed(1)}%</td>
                    <td className={row.noos_pct >= 50 ? 'text-green-600 font-semibold' : 'text-amber-600'}>
                      {row.noos_pct?.toFixed(1)}%
                    </td>
                    <td>
                      <span className={`badge ${row.is_noos ? 'badge-healthy' : 'bg-slate-100 text-slate-500'}`}>
                        {row.is_noos ? "NOOS" : "Monitor"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default GapAnalysis;
