import { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import { API } from "../App";
import { useNavigate } from "react-router-dom";
import {
  RefreshCw, AlertTriangle, TrendingDown, TrendingUp, ShieldCheck,
  XCircle, Clock, Layout, Package, ShoppingCart, ArrowRight,
  ChevronRight, Activity, IndianRupee, Percent, ArrowUpRight, ArrowDownRight,
  FileDown, Loader2, BarChart3, Upload, Server, MessageCircle, Database
} from "lucide-react";
import FilterPanel from "../components/FilterPanel";
import { DoughnutChart } from "../components/Charts";
import { Line } from "react-chartjs-2";
import html2canvas from "html2canvas";
import { jsPDF } from "jspdf";

const ExecutiveDashboard = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [kpis, setKpis] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filterOptions, setFilterOptions] = useState({});
  const [filters, setFilters] = useState({
    startDate: "", endDate: "",
    categories: [], channels: [], regions: [],
  });

  // Auto-refresh state
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [countdown, setCountdown] = useState(30);
  const autoRefreshRef = useRef(null);
  const countdownRef = useRef(null);

  // PDF Export
  const [exporting, setExporting] = useState(false);
  const dashboardRef = useRef(null);

  const handleExportPDF = async () => {
    if (!dashboardRef.current || exporting) return;
    setExporting(true);
    try {
      const canvas = await html2canvas(dashboardRef.current, {
        scale: 2,
        useCORS: true,
        logging: false,
        backgroundColor: "#F8F9FA",
      });
      const imgData = canvas.toDataURL("image/png");
      const imgW = canvas.width;
      const imgH = canvas.height;

      const pdf = new jsPDF({ orientation: imgW > imgH ? "l" : "p", unit: "px", format: [imgW + 40, imgH + 100] });

      // Header
      pdf.setFillColor(1, 118, 211);
      pdf.rect(0, 0, imgW + 40, 50, "F");
      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(18);
      pdf.setTextColor(255, 255, 255);
      pdf.text("Executive Dashboard Report", 20, 33);

      // Date
      pdf.setFontSize(10);
      pdf.setTextColor(200, 220, 255);
      const dateStr = new Date().toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" });
      pdf.text(`Generated: ${dateStr}`, imgW + 20, 33, { align: "right" });

      // Dashboard image
      pdf.addImage(imgData, "PNG", 20, 60, imgW, imgH);

      // Footer
      pdf.setFontSize(8);
      pdf.setTextColor(150, 150, 150);
      pdf.text("GetMyPlan Analytics - Confidential", 20, imgH + 85);
      pdf.text(`Page 1 of 1`, imgW + 20, imgH + 85, { align: "right" });

      pdf.save(`executive-dashboard-${new Date().toISOString().split("T")[0]}.pdf`);
    } catch (err) {
      console.error("PDF export failed:", err);
    } finally {
      setExporting(false);
    }
  };

  const fetchFilterOptions = useCallback(async () => {
    try {
      const resp = await axios.get(`${API}/analytics/filter-options`);
      setFilterOptions(resp.data);
      if (resp.data.dateRange?.min) {
        setFilters(prev => ({
          ...prev,
          startDate: resp.data.dateRange.min.split('T')[0],
          endDate: resp.data.dateRange.max.split('T')[0],
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
      const [dashResp, kpiResp, trendResp] = await Promise.all([
        axios.get(`${API}/analytics/executive-dashboard?${queryParams}`),
        axios.get(`${API}/analytics/executive-kpis?${queryParams}`),
        axios.get(`${API}/analytics/executive-revenue-trend?${queryParams}`),
      ]);
      if (dashResp.data.error) setError(dashResp.data.error);
      else setData(dashResp.data);
      setKpis(kpiResp.data);
      setTrendData(trendResp.data);
    } catch (err) {
      setError("Failed to fetch dashboard data.");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { fetchData(); }, []);

  // Auto-refresh logic
  useEffect(() => {
    if (autoRefresh) {
      setCountdown(30);
      countdownRef.current = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            return 30;
          }
          return prev - 1;
        });
      }, 1000);
      autoRefreshRef.current = setInterval(() => {
        fetchData();
      }, 30000);
    }
    return () => {
      if (autoRefreshRef.current) clearInterval(autoRefreshRef.current);
      if (countdownRef.current) clearInterval(countdownRef.current);
    };
  }, [autoRefresh, fetchData]);

  const handleFilterChange = (field, value) => setFilters(prev => ({ ...prev, [field]: value }));
  const handleApplyFilters = () => fetchData();
  const handleResetFilters = () => {
    setFilters({
      startDate: filterOptions.dateRange?.min?.split('T')[0] || "",
      endDate: filterOptions.dateRange?.max?.split('T')[0] || "",
      categories: [], channels: [], regions: [],
    });
  };

  const fmtCur = (v) => {
    if (v === null || v === undefined) return "N/A";
    if (v < 0) return "-" + fmtCur(-v);
    if (v >= 10000000) return `\u20B9${(v / 10000000).toFixed(1)}Cr`;
    if (v >= 100000) return `\u20B9${(v / 100000).toFixed(1)}L`;
    if (v >= 1000) return `\u20B9${(v / 1000).toFixed(0)}K`;
    return `\u20B9${Math.round(v)}`;
  };
  const fmtNum = (v) => {
    if (v === null || v === undefined) return "N/A";
    if (v === 0) return "0";
    if (v >= 1000000) return `${(v / 1000000).toFixed(1)}M`;
    if (v >= 1000) return `${(v / 1000).toFixed(0)}K`;
    return Math.round(v).toString();
  };

  const healthScore = data?.health_score || 0;
  const m = data?.modules || {};
  const hasModuleData = Object.values(m).some(v => v !== null && v !== undefined);

  const getScoreColor = (s) => {
    if (!hasModuleData) return 'text-slate-400';
    if (s >= 70) return 'text-green-600';
    if (s >= 40) return 'text-amber-600';
    return 'text-red-600';
  };

  const getScoreLabel = (s) => {
    if (!hasModuleData) return 'No module data uploaded yet';
    if (s >= 70) return 'Healthy — operations running well';
    if (s >= 40) return 'Needs attention — some modules at risk';
    return 'Critical — multiple modules need action';
  };

  return (
    <div className="animate-fade-in-up" data-testid="executive-dashboard-page">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
            Executive Dashboard
          </h1>
          <p className="text-slate-500">
            Unified view of all merchandising analytics modules
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* PDF Export */}
          <button
            data-testid="export-pdf-btn"
            onClick={handleExportPDF}
            disabled={exporting || !data}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 transition-colors disabled:opacity-50"
          >
            {exporting ? <Loader2 size={14} className="animate-spin" /> : <FileDown size={14} />}
            {exporting ? 'Exporting...' : 'Export PDF'}
          </button>
          {/* Auto-refresh Toggle */}
          <button
            data-testid="auto-refresh-toggle"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium border transition-colors ${
              autoRefresh
                ? 'bg-green-50 border-green-200 text-green-700'
                : 'bg-white border-slate-200 text-slate-500 hover:bg-slate-50'
            }`}
          >
            <RefreshCw size={14} className={autoRefresh ? 'animate-spin' : ''} />
            {autoRefresh ? `Auto ${countdown}s` : 'Auto-refresh'}
          </button>
          <button data-testid="refresh-exec-btn" onClick={fetchData} disabled={loading}
            className="btn-secondary flex items-center gap-2">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Refresh
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
        pageType="executive"
      />

      {/* Error */}
      {error && (
        <div className="bg-amber-50 border border-amber-200 p-6 mb-6 rounded text-center" data-testid="exec-error">
          <AlertTriangle size={36} className="text-amber-500 mx-auto mb-2" />
          <p className="text-amber-700">{error}</p>
          <button onClick={() => navigate('/upload')} className="btn-primary mt-3 inline-flex items-center gap-2">
            Go to Data Upload <ArrowRight size={16} />
          </button>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-20"><div className="spinner" /></div>
      )}

      {data && !loading && !error && (
        <div ref={dashboardRef}>
        <>
          {/* ── Revenue & Margin KPI Row ── */}
          {kpis && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6" data-testid="kpi-cards">
              {/* Total Revenue */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm" data-testid="kpi-revenue">
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-blue-50">
                    <IndianRupee size={20} className="text-blue-500" />
                  </div>
                  <span className="text-2xl font-bold text-slate-900">{fmtCur(kpis.revenue)}</span>
                </div>
                <p className="text-sm text-slate-500">Total Revenue</p>
                {kpis.has_data && kpis.wow?.revenue_change !== 0 && (
                  <div className="mt-2 flex items-center gap-1">
                    {kpis.wow.revenue_change >= 0 ? (
                      <ArrowUpRight size={14} className="text-green-500" />
                    ) : (
                      <ArrowDownRight size={14} className="text-red-500" />
                    )}
                    <span className={`text-xs font-medium ${kpis.wow.revenue_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {kpis.wow.revenue_change >= 0 ? '+' : ''}{kpis.wow.revenue_change}% WoW
                    </span>
                  </div>
                )}
              </div>

              {/* Units Sold */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm" data-testid="kpi-units">
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-emerald-50">
                    <ShoppingCart size={20} className="text-emerald-500" />
                  </div>
                  <span className="text-2xl font-bold text-slate-900">{fmtNum(kpis.units_sold)}</span>
                </div>
                <p className="text-sm text-slate-500">Units Sold</p>
                {kpis.has_data && kpis.wow?.units_change !== 0 && (
                  <div className="mt-2 flex items-center gap-1">
                    {kpis.wow.units_change >= 0 ? (
                      <ArrowUpRight size={14} className="text-green-500" />
                    ) : (
                      <ArrowDownRight size={14} className="text-red-500" />
                    )}
                    <span className={`text-xs font-medium ${kpis.wow.units_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {kpis.wow.units_change >= 0 ? '+' : ''}{kpis.wow.units_change}% WoW
                    </span>
                  </div>
                )}
              </div>

              {/* MRP Realisation (Margin proxy) */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm" data-testid="kpi-margin">
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-purple-50">
                    <Percent size={20} className="text-purple-500" />
                  </div>
                  <span className="text-2xl font-bold text-slate-900">
                    {kpis.mrp_realisation_pct !== null ? `${kpis.mrp_realisation_pct}%` : 'N/A'}
                  </span>
                </div>
                <p className="text-sm text-slate-500">MRP Realisation</p>
                <p className="text-[11px] text-slate-400 mt-1">Revenue vs MRP value</p>
              </div>

              {/* Health Score */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm" data-testid="kpi-health">
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-amber-50">
                    <Activity size={20} className="text-amber-500" />
                  </div>
                  <span className={`text-2xl font-bold ${getScoreColor(healthScore)}`}>{healthScore}</span>
                </div>
                <p className="text-sm text-slate-500">Health Score</p>
                <p className="text-[11px] text-slate-400 mt-1">
                  {!hasModuleData ? 'Upload data to calculate' : (healthScore >= 70 ? 'Healthy' : healthScore >= 40 ? 'Needs attention' : 'Critical')}
                </p>
              </div>
            </div>
          )}

          {/* ── WoW & YoY Comparison Row ── */}
          {kpis?.has_data && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8" data-testid="comparison-cards">
              {/* Week-over-Week */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm" data-testid="wow-card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Week-over-Week</h3>
                  <Clock size={14} className="text-slate-400" />
                </div>
                <div className="flex items-baseline justify-between mb-4">
                  <div>
                    <p className={`text-2xl font-bold ${kpis.wow?.revenue_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {kpis.wow?.revenue_change >= 0 ? '+' : ''}{kpis.wow?.revenue_change || 0}%
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5">Revenue change</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-slate-700">This week: {fmtCur(kpis.wow?.current_revenue)}</p>
                    <p className="text-sm text-slate-400">Last week: {fmtCur(kpis.wow?.previous_revenue)}</p>
                  </div>
                </div>
                <div className="pt-3 border-t border-slate-100 flex justify-between text-sm">
                  <span className="text-slate-500">Units</span>
                  <span className={kpis.wow?.units_change >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {kpis.wow?.units_change >= 0 ? '+' : ''}{kpis.wow?.units_change || 0}%
                  </span>
                </div>
              </div>

              {/* Year-over-Year */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm" data-testid="yoy-card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Year-over-Year</h3>
                  <Clock size={14} className="text-slate-400" />
                </div>
                <div className="flex items-baseline justify-between mb-4">
                  <div>
                    <p className={`text-2xl font-bold ${kpis.yoy?.revenue_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {kpis.yoy?.revenue_change >= 0 ? '+' : ''}{kpis.yoy?.revenue_change || 0}%
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5">Revenue change</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-slate-700">This period: {fmtCur(kpis.yoy?.current_revenue)}</p>
                    <p className="text-sm text-slate-400">Last year: {fmtCur(kpis.yoy?.previous_revenue)}</p>
                  </div>
                </div>
                {kpis.yoy?.previous_revenue === 0 && (
                  <p className="text-xs text-slate-400 italic">No data from same period last year</p>
                )}
                {kpis.yoy?.previous_revenue > 0 && (
                  <div className="pt-3 border-t border-slate-100 flex justify-between text-sm">
                    <span className="text-slate-500">Units</span>
                    <span className={kpis.yoy?.units_change >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {kpis.yoy?.units_change >= 0 ? '+' : ''}{kpis.yoy?.units_change || 0}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── Revenue Trend Line Chart (DASH-15) ── */}
          {trendData && trendData.labels && trendData.labels.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-6 mb-8" data-testid="revenue-trend-chart">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-slate-900">Revenue Trend</h3>
                  <p className="text-xs text-slate-400 mt-0.5">Daily revenue &amp; units sold over the selected period</p>
                </div>
                <TrendingUp size={18} className="text-[#0176D3]" />
              </div>
              <div style={{ height: 320 }}>
                <Line
                  data={{
                    labels: trendData.labels.map(d => {
                      const dt = new Date(d + 'T00:00:00');
                      return dt.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
                    }),
                    datasets: [
                      {
                        label: 'Revenue',
                        data: trendData.revenue,
                        borderColor: '#0176D3',
                        backgroundColor: '#0176D320',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        yAxisID: 'y',
                      },
                      {
                        label: 'Units Sold',
                        data: trendData.units,
                        borderColor: '#2E844A',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.3,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        yAxisID: 'y1',
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                      legend: { position: 'bottom', labels: { usePointStyle: true, pointStyle: 'circle', padding: 16, font: { size: 12 } } },
                      tooltip: {
                        backgroundColor: '#0F172A',
                        padding: 12,
                        cornerRadius: 4,
                        callbacks: {
                          label: (ctx) => {
                            const v = ctx.raw;
                            if (ctx.datasetIndex === 0) {
                              if (v >= 10000000) return `Revenue: \u20B9${(v/10000000).toFixed(1)}Cr`;
                              if (v >= 100000) return `Revenue: \u20B9${(v/100000).toFixed(1)}L`;
                              if (v >= 1000) return `Revenue: \u20B9${(v/1000).toFixed(0)}K`;
                              return `Revenue: \u20B9${Math.round(v)}`;
                            }
                            return `Units: ${v.toLocaleString('en-IN')}`;
                          }
                        }
                      }
                    },
                    scales: {
                      x: { grid: { display: false }, ticks: { font: { size: 10 }, maxRotation: 45, autoSkip: true, maxTicksLimit: 20 } },
                      y: {
                        type: 'linear', position: 'left',
                        grid: { color: '#E2E8F0' },
                        title: { display: true, text: 'Revenue (\u20B9)', font: { size: 11 }, color: '#0176D3' },
                        ticks: {
                          font: { size: 10 }, color: '#0176D3',
                          callback: (v) => {
                            if (v >= 10000000) return `\u20B9${(v/10000000).toFixed(1)}Cr`;
                            if (v >= 100000) return `\u20B9${(v/100000).toFixed(1)}L`;
                            if (v >= 1000) return `\u20B9${(v/1000).toFixed(0)}K`;
                            return `\u20B9${v}`;
                          }
                        }
                      },
                      y1: {
                        type: 'linear', position: 'right',
                        grid: { drawOnChartArea: false },
                        title: { display: true, text: 'Units Sold', font: { size: 11 }, color: '#2E844A' },
                        ticks: { font: { size: 10 }, color: '#2E844A' }
                      },
                    },
                  }}
                />
              </div>
            </div>
          )}

          {/* Health Score Circle + Alert Summary */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* Health Score */}
            <div className="bg-white border border-slate-200 rounded shadow-sm p-6 flex flex-col items-center justify-center" data-testid="health-score-card">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">Inventory Health Score</p>
              <div className="relative w-36 h-36 mb-3">
                <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
                  <circle cx="60" cy="60" r="52" fill="none" stroke="#e2e8f0" strokeWidth="10" />
                  <circle cx="60" cy="60" r="52" fill="none"
                    stroke="url(#scoreGrad)" strokeWidth="10" strokeLinecap="round"
                    strokeDasharray={`${healthScore * 3.267} ${326.7 - healthScore * 3.267}`}
                  />
                  <defs>
                    <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" className={healthScore >= 70 ? 'text-green-500' : healthScore >= 40 ? 'text-amber-500' : 'text-red-500'} style={{ stopColor: 'currentColor' }} />
                      <stop offset="100%" className={healthScore >= 70 ? 'text-emerald-400' : healthScore >= 40 ? 'text-yellow-400' : 'text-rose-400'} style={{ stopColor: 'currentColor' }} />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className={`text-3xl font-bold ${getScoreColor(healthScore)}`}>{healthScore}</span>
                  <span className="text-xs text-slate-400">/ 100</span>
                </div>
              </div>
              <p className="text-sm text-slate-600">
                {getScoreLabel(healthScore)}
              </p>
            </div>

            {/* Alerts */}
            <div className="lg:col-span-2 bg-white border border-slate-200 rounded shadow-sm" data-testid="alerts-panel">
              <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                <h3 className="font-semibold text-slate-900">Alerts & Actions</h3>
                <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium">
                  {data.alerts?.filter(a => a.priority === 'high').length} high priority
                </span>
              </div>
              <div className="divide-y divide-slate-100 max-h-72 overflow-y-auto">
                {data.alerts?.map((alert, idx) => (
                  <button key={idx} onClick={() => navigate(alert.link)}
                    className="w-full p-4 flex items-start gap-3 hover:bg-slate-50 transition-colors text-left"
                    data-testid={`alert-${idx}`}>
                    <div className={`p-1.5 rounded-lg ${alert.priority === 'high' ? 'bg-red-50' : 'bg-amber-50'}`}>
                      <AlertTriangle size={16} className={alert.priority === 'high' ? 'text-red-500' : 'text-amber-500'} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-xs text-slate-400 font-medium">{alert.module}</span>
                        <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${
                          alert.priority === 'high' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                        }`}>{alert.priority}</span>
                      </div>
                      <p className="text-sm font-medium text-slate-900 truncate">{alert.title}</p>
                      <p className="text-xs text-slate-500 truncate">{alert.description}</p>
                    </div>
                    <ChevronRight size={16} className="text-slate-300 mt-1 shrink-0" />
                  </button>
                ))}
                {(!data.alerts || data.alerts.length === 0) && (
                  <div className="p-6 text-center text-slate-400 text-sm">
                    No alerts — all modules operating normally
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Module Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
            {/* ROS Gap Module */}
            <ModuleCard
              testId="module-ros-gap"
              title="ROS Gap Analysis"
              icon={<Activity size={20} className="text-[#0176D3]" />}
              link="/gap-analysis"
              navigate={navigate}
              available={!!m.ros_gap}
              metrics={m.ros_gap ? [
                { label: 'Avg ROS Gap', value: m.ros_gap.avg_ros_gap?.toFixed(2) || '0', unit: 'units/day' },
                { label: 'Sales Loss', value: fmtNum(m.ros_gap.total_sales_loss), unit: 'units', alert: m.ros_gap.total_sales_loss > 0 },
                { label: 'Healthy Coverage', value: `${m.ros_gap.healthy_coverage_pct}%`, color: m.ros_gap.healthy_coverage_pct >= 50 ? 'text-green-600' : 'text-red-600' },
              ] : []}
              chart={m.ros_gap ? (
                <MiniDoughnut labels={['Healthy', 'Broken']} data={[m.ros_gap.healthy_styles || 0, m.ros_gap.broken_styles || 0]} />
              ) : null}
            />

            {/* Stock-Out Module */}
            <ModuleCard
              testId="module-stock-out"
              title="Stock-Out Analysis"
              icon={<XCircle size={20} className="text-red-500" />}
              link="/stock-out"
              navigate={navigate}
              available={!!m.stock_out}
              metrics={m.stock_out ? [
                { label: 'Total Stock-Outs', value: fmtNum(m.stock_out.total_stockouts), alert: true },
                { label: 'Stock-Out Rate', value: `${m.stock_out.stockout_rate}%`, color: m.stock_out.stockout_rate > 10 ? 'text-red-600' : 'text-amber-600' },
                { label: 'Daily Loss', value: fmtCur(m.stock_out.total_lost_sales), alert: true },
              ] : []}
            />

            {/* DOH Module */}
            <ModuleCard
              testId="module-doh"
              title="DOH Analysis"
              icon={<Clock size={20} className="text-[#0176D3]" />}
              link="/doh"
              navigate={navigate}
              available={!!m.doh}
              metrics={m.doh ? [
                { label: 'Overall DOH', value: `${m.doh.overall_doh} days`, color: Math.abs(m.doh.overall_doh - m.doh.ideal_doh) <= m.doh.ideal_doh * 0.2 ? 'text-green-600' : 'text-amber-600' },
                { label: 'Optimal', value: fmtNum(m.doh.optimal_count), color: 'text-green-600' },
                { label: 'At Risk', value: fmtNum(m.doh.understocked_count + m.doh.stockedout_count), alert: (m.doh.understocked_count + m.doh.stockedout_count) > 0 },
              ] : []}
              chart={m.doh ? (
                <MiniDoughnut labels={['Optimal', 'Over', 'Under', 'Out']} data={[m.doh.optimal_count, m.doh.overstocked_count, m.doh.understocked_count, m.doh.stockedout_count]} />
              ) : null}
            />

            {/* Planogram Module */}
            <ModuleCard
              testId="module-planogram"
              title="Planogram Fill Rate"
              icon={<Layout size={20} className="text-[#DD7A01]" />}
              link="/planogram"
              navigate={navigate}
              available={!!m.planogram}
              metrics={m.planogram ? [
                { label: 'Fill Rate', value: `${m.planogram.overall_fill_rate}%`, color: m.planogram.overall_fill_rate >= 90 ? 'text-green-600' : m.planogram.overall_fill_rate >= 80 ? 'text-amber-600' : 'text-red-600' },
                { label: 'Critical SKUs', value: fmtNum(m.planogram.critical_count), alert: m.planogram.critical_count > 0 },
                { label: 'Lost Sales', value: fmtCur(m.planogram.total_lost_sales), alert: true },
              ] : []}
              chart={m.planogram ? (
                <MiniDoughnut labels={['Good', 'Moderate', 'Critical']} data={[m.planogram.good_count, m.planogram.moderate_count, m.planogram.critical_count]} />
              ) : null}
            />

            {/* Replenishment Module */}
            <ModuleCard
              testId="module-replenishment"
              title="Replenishment Planner"
              icon={<ShoppingCart size={20} className="text-[#2E844A]" />}
              link="/replenishment"
              navigate={navigate}
              available={!!m.replenishment}
              metrics={m.replenishment ? [
                { label: 'Total PO Value', value: fmtCur(m.replenishment.total_po_value) },
                { label: 'SKUs to Reorder', value: fmtNum(m.replenishment.skus_needing_reorder) },
                { label: 'Urgent Items', value: fmtNum(m.replenishment.stockout_count + m.replenishment.critical_count), alert: (m.replenishment.stockout_count + m.replenishment.critical_count) > 0 },
              ] : []}
            />

            {/* NOOS Module (from ROS Gap) */}
            <ModuleCard
              testId="module-noos"
              title="NOOS & Size Gap"
              icon={<ShieldCheck size={20} className="text-[#2E844A]" />}
              link="/gap-analysis"
              navigate={navigate}
              available={!!m.ros_gap}
              metrics={m.ros_gap ? [
                { label: 'NOOS Styles', value: fmtNum(m.ros_gap.noos_styles), color: 'text-green-600' },
                { label: 'Total Styles', value: fmtNum(m.ros_gap.healthy_styles + m.ros_gap.broken_styles) },
                { label: 'Healthy %', value: `${m.ros_gap.healthy_coverage_pct}%`, color: m.ros_gap.healthy_coverage_pct >= 50 ? 'text-green-600' : 'text-red-600' },
              ] : []}
            />
          </div>

          {/* Quick Links */}
          <div className="bg-white border border-slate-200 rounded shadow-sm p-6" data-testid="quick-links">
            <h3 className="font-semibold text-slate-900 mb-4">Quick Navigation</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {[
                { label: 'Core Logics', path: '/core-logics', icon: Activity },
                { label: 'Gap Analysis', path: '/gap-analysis', icon: TrendingDown },
                { label: 'Stock-Outs', path: '/stock-out', icon: XCircle },
                { label: 'Replenishment', path: '/replenishment', icon: ShoppingCart },
                { label: 'DOH', path: '/doh', icon: Clock },
                { label: 'Planogram', path: '/planogram', icon: Layout },
                { label: 'BI Dashboards', path: '/bi-dashboards', icon: BarChart3 },
                { label: 'Warehouse', path: '/warehouse', icon: Package },
                { label: 'Data Upload', path: '/upload', icon: Upload },
                { label: 'SFTP Monitor', path: '/sftp-monitor', icon: Server },
                { label: 'Data Quality', path: '/data-quality', icon: Database },
                { label: 'FAQ Chatbot', path: '/chatbot', icon: MessageCircle },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <button key={item.path} onClick={() => navigate(item.path)}
                    className="flex flex-col items-center gap-2 p-3 rounded border border-slate-100 hover:border-[#0176D3] hover:bg-blue-50 transition-all text-center">
                    <Icon size={20} className="text-slate-500" />
                    <span className="text-xs text-slate-700 font-medium">{item.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </>
        </div>
      )}

      {!loading && !error && !data && (
        <div className="bg-slate-50 border border-slate-200 p-12 text-center rounded" data-testid="no-data-message">
          <p className="text-slate-500 mb-2">No data available</p>
          <p className="text-sm text-slate-400">Upload required files to see the executive dashboard</p>
        </div>
      )}
    </div>
  );
};


/* Module Card sub-component */
const ModuleCard = ({ testId, title, icon, link, navigate, available, metrics, chart }) => (
  <div className="bg-white border border-slate-200 rounded shadow-sm overflow-hidden hover:shadow-md transition-shadow"
    data-testid={testId}>
    <div className="p-4 border-b border-slate-100 flex items-center justify-between">
      <div className="flex items-center gap-2">
        {icon}
        <h3 className="font-semibold text-slate-900 text-sm">{title}</h3>
      </div>
      <button onClick={() => navigate(link)}
        className="text-xs text-[#0176D3] hover:text-blue-700 flex items-center gap-1 font-medium">
        View <ChevronRight size={14} />
      </button>
    </div>
    {available ? (
      <div className="p-4">
        <div className="space-y-3 mb-3">
          {metrics.map((m, i) => (
            <div key={i} className="flex items-center justify-between">
              <span className="text-xs text-slate-500">{m.label}</span>
              <span className={`text-sm font-semibold ${m.alert ? 'text-red-600' : m.color || 'text-slate-900'}`}>
                {m.value}{m.unit ? <span className="text-xs text-slate-400 ml-1">{m.unit}</span> : null}
              </span>
            </div>
          ))}
        </div>
        {chart && <div className="pt-2 border-t border-slate-50">{chart}</div>}
      </div>
    ) : (
      <div className="p-4 text-center text-sm text-slate-400">
        No data — <button onClick={() => navigate('/upload')} className="text-[#0176D3] underline">upload files</button>
      </div>
    )}
  </div>
);


/* Mini Doughnut Chart sub-component */
const MiniDoughnut = ({ labels, data }) => (
  <div className="h-24">
    <DoughnutChart labels={labels} data={data} height={96} />
  </div>
);


export default ExecutiveDashboard;