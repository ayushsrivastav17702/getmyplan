import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import { RefreshCw, Download, Users, Briefcase, BarChart3 } from "lucide-react";
import FilterPanel from "../components/FilterPanel";

const GapAnalysis = () => {
  const [activeTab, setActiveTab] = useState("noos");
  const [persona, setPersona] = useState("cxo");
  const [noosData, setNoosData] = useState(null);
  const [sizeGapData, setSizeGapData] = useState(null);
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
        if (response.data.error) {
          setError(response.data.error);
        } else {
          setNoosData(response.data);
        }
      } else if (activeTab === "size-gap") {
        const response = await axios.get(`${API}/analytics/size-gap?${queryParams}`);
        if (response.data.error) {
          setError(response.data.error);
        } else {
          setSizeGapData(response.data);
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
      understockThreshold: -5,
      overstockThreshold: 5
    });
  };

  const tabs = [
    { key: "noos", label: "NOOS Analysis" },
    { key: "size-gap", label: "Size Set Gap" },
  ];

  const personas = [
    { key: "cxo", label: "CXO View", icon: Users, description: "High-level metrics and revenue impact" },
    { key: "merchandiser", label: "Merchandiser", icon: Briefcase, description: "Detailed style-level analysis" },
    { key: "consultant", label: "Consultant", icon: BarChart3, description: "Methodology and calculations" },
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
    const data = activeTab === "noos" ? noosData?.data : sizeGapData?.data;
    if (!data || data.length === 0) return;
    
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

      {/* NOOS Analysis */}
      {activeTab === "noos" && noosData && !loading && (
        <div data-testid="noos-analysis-section">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="metric-card">
              <span className="metric-label">Store-Style Combinations</span>
              <span className="metric-value">{formatNumber(noosData.summary?.total_combinations)}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">NOOS Candidates</span>
              <span className="metric-value text-green-600">
                {formatNumber(noosData.summary?.noos_candidates)}
              </span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Avg Availability</span>
              <span className="metric-value">
                {noosData.summary?.avg_availability?.toFixed(1)}%
              </span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Total Revenue</span>
              <span className="metric-value">{formatCurrency(noosData.summary?.total_revenue)}</span>
            </div>
          </div>

          {/* CXO Executive Insight */}
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

          {/* Consultant Methodology */}
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
                    <li>Exposure days ≥ Minimum shelf life threshold (configurable)</li>
                    <li>Positive sales quantity during the analysis period</li>
                    <li>Availability percentage ≥ 80%</li>
                  </ul>
                </div>

                <div className="p-4 bg-slate-50 border border-slate-100 rounded">
                  <h4 className="font-semibold text-slate-900 mb-2">Key Metrics</h4>
                  <ul className="list-disc list-inside space-y-1">
                    <li><strong>Exposure Days:</strong> Days with positive inventory</li>
                    <li><strong>Availability %:</strong> (Exposure Days / Total Days) × 100</li>
                    <li><strong>NOOS Gap:</strong> Revenue lost due to stockouts for NOOS items</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Data Table - Merchandiser/CXO */}
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
      )}

      {/* Size Gap Analysis */}
      {activeTab === "size-gap" && sizeGapData && !loading && (
        <div data-testid="size-gap-section">
          {/* Summary Cards */}
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

          {/* Data Table */}
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
      )}

      {/* Empty State */}
      {!loading && !error && ((activeTab === "noos" && !noosData?.data?.length) || (activeTab === "size-gap" && !sizeGapData?.data?.length)) && (
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

export default GapAnalysis;
