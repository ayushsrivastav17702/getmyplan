import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  RefreshCw, CheckCircle, XCircle, AlertTriangle, Clock,
  FileText, Calendar, Award, Shield, Activity, Database,
  ThumbsUp, Store, X, Zap, Download, ChevronRight, TrendingUp
} from "lucide-react";
import { BarChart, DoughnutChart } from "../components/Charts";
import { Line } from "react-chartjs-2";

// ── Status helpers
const STATUS_CFG = {
  uploaded: { bg: "bg-green-50 border-green-300", text: "text-green-700", label: "Uploaded", Icon: CheckCircle, color: "text-green-500" },
  missing:  { bg: "bg-red-50 border-red-300",     text: "text-red-700",   label: "Missing",  Icon: XCircle,     color: "text-red-500" },
  late:     { bg: "bg-amber-50 border-amber-300",  text: "text-amber-700", label: "Late",     Icon: Clock,       color: "text-amber-500" },
  partial:  { bg: "bg-orange-50 border-orange-300", text: "text-orange-700",label: "Partial",  Icon: AlertTriangle, color: "text-orange-500" },
};

const StatusBadge = ({ status }) => {
  const c = STATUS_CFG[status] || STATUS_CFG.missing;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${c.bg} ${c.text} border`}>
      <c.Icon size={10} />{c.label}
    </span>
  );
};

// ── Quality ring (SVG)
const QualityRing = ({ score, size = 72 }) => {
  const r = (size - 12) / 2;
  const circ = 2 * Math.PI * r;
  const color = score >= 80 ? "#2E844A" : score >= 60 ? "#DD7A01" : "#EA001E";
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="#E2E8F0" strokeWidth={6} fill="none" />
        <circle cx={size / 2} cy={size / 2} r={r} stroke={color} strokeWidth={6} fill="none"
          strokeDasharray={`${circ * score / 100} ${circ}`} strokeLinecap="round" />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-base font-bold text-slate-900">{score}</span>
    </div>
  );
};

// ── Progress bar
const ProgressBar = ({ value, max = 100, color = "#0176D3", height = 6, label, rightLabel }) => (
  <div>
    {(label || rightLabel) && (
      <div className="flex justify-between text-xs text-slate-500 mb-1">
        {label && <span>{label}</span>}
        {rightLabel && <span>{rightLabel}</span>}
      </div>
    )}
    <div className="w-full rounded-full overflow-hidden" style={{ height, background: "#E2E8F0" }}>
      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${Math.min(value, max)}%`, background: color }} />
    </div>
  </div>
);

// ── Check status icon
const CheckIcon = ({ status }) => {
  if (status === "pass") return <CheckCircle size={14} className="text-green-500" />;
  if (status === "warn") return <AlertTriangle size={14} className="text-amber-500" />;
  return <XCircle size={14} className="text-red-500" />;
};

// ── Store Detail Modal
const StoreModal = ({ store, onClose }) => {
  if (!store) return null;
  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-xl w-full max-w-xl max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="sticky top-0 bg-white border-b border-slate-100 px-6 py-4 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <Store size={20} className="text-slate-500" />
            <div>
              <h3 className="font-bold text-slate-900">{store.name}</h3>
              <p className="text-xs text-slate-500">{store.code} · {store.region}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors"><X size={18} /></button>
        </div>
        <div className="p-6 space-y-6">
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Today's Uploads</h4>
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center p-3 bg-slate-50 rounded-lg">
                <FileText size={18} className="text-slate-400 mx-auto mb-1" />
                <p className="text-xs font-medium text-slate-700">Sales</p>
                <StatusBadge status={store.salesStatus} />
              </div>
              <div className="text-center p-3 bg-slate-50 rounded-lg">
                <Database size={18} className="text-slate-400 mx-auto mb-1" />
                <p className="text-xs font-medium text-slate-700">Inventory</p>
                <StatusBadge status={store.inventoryStatus} />
              </div>
              <div className="text-center p-3 bg-slate-50 rounded-lg">
                <Clock size={18} className="text-slate-400 mx-auto mb-1" />
                <p className="text-xs font-medium text-slate-700">Last Upload</p>
                <p className="text-[10px] text-slate-500 mt-1">{store.lastUpload || "Never"}</p>
              </div>
            </div>
          </div>
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Data Quality Score</h4>
            <div className="flex items-center gap-6">
              <QualityRing score={store.qualityScore} size={80} />
              <div className="flex-1 space-y-2.5">
                <ProgressBar value={store.completeness} label="Completeness" rightLabel={`${store.completeness}%`} color="#0176D3" height={5} />
                <ProgressBar value={store.accuracy} label="Accuracy" rightLabel={`${store.accuracy}%`} color="#2E844A" height={5} />
                <ProgressBar value={store.timeliness} label="Timeliness" rightLabel={`${store.timeliness}%`} color="#DD7A01" height={5} />
              </div>
            </div>
          </div>
          {store.issues?.length > 0 && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Issues</h4>
              <div className="space-y-2">
                {store.issues.map((issue, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-red-700 bg-red-50 border border-red-100 p-2.5 rounded-lg">
                    <AlertTriangle size={13} className="flex-shrink-0" />{issue}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ── Main page
const DataQuality = () => {
  const [stores, setStores] = useState([]);
  const [sla, setSla] = useState(null);
  const [scorecard, setScorecard] = useState(null);
  const [dataChecks, setDataChecks] = useState(null);
  const [categoryScorecard, setCategoryScorecard] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [selectedStore, setSelectedStore] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState("completeness");
  const [selectedDate, setSelectedDate] = useState(() => {
    const d = new Date(); d.setDate(d.getDate() - 1);
    return d.toISOString().slice(0, 10);
  });

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [storesRes, slaRes, scRes, dcRes, catRes, trendRes] = await Promise.all([
        axios.get(`${API}/admin/quality/store-uploads/${selectedDate}`),
        axios.get(`${API}/admin/quality/sla-metrics`),
        axios.get(`${API}/admin/quality/scorecard`),
        axios.get(`${API}/quality/data-checks`).catch(() => ({ data: null })),
        axios.get(`${API}/quality/category-scorecard`).catch(() => ({ data: null })),
        axios.get(`${API}/quality/trend`).catch(() => ({ data: null })),
      ]);
      setStores(storesRes.data);
      setSla(slaRes.data);
      setScorecard(scRes.data);
      setDataChecks(dcRes.data);
      setCategoryScorecard(catRes.data);
      setTrendData(trendRes.data);
    } catch (err) {
      console.error("Quality fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, [selectedDate]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const uploaded = stores.filter(s => s.status === "uploaded").length;
  const missing = stores.filter(s => s.status === "missing").length;
  const late = stores.filter(s => s.status === "late").length;
  const partial = stores.filter(s => s.status === "partial").length;
  const completionRate = stores.length > 0 ? ((uploaded + late) / stores.length * 100).toFixed(1) : 0;

  const METRICS = [
    { id: "completeness", label: "Completeness", Icon: CheckCircle, color: "#0176D3" },
    { id: "accuracy", label: "Accuracy", Icon: Award, color: "#2E844A" },
    { id: "timeliness", label: "Timeliness", Icon: Clock, color: "#DD7A01" },
    { id: "consistency", label: "Consistency", Icon: Activity, color: "#9050E9" },
    { id: "validity", label: "Validity", Icon: Shield, color: "#EA001E" },
  ];

  const TABS = [
    { id: "overview", label: "Overview", icon: Activity },
    { id: "checks", label: "Data Checks", icon: Shield },
    { id: "categories", label: "Category Scorecard", icon: Database },
    { id: "trend", label: "Quality Trend", icon: TrendingUp },
    { id: "stores", label: "Store Tracker", icon: Store },
  ];

  const handleExport = async () => {
    try {
      const resp = await axios.get(`${API}/quality/export`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([resp.data]));
      const a = document.createElement("a"); a.href = url; a.download = "data_quality_report.csv"; a.click();
    } catch { alert("Export failed"); }
  };

  const slaColor = (pct) => (pct >= 95 ? "#2E844A" : pct >= 85 ? "#DD7A01" : "#EA001E");

  return (
    <div className="animate-fade-in-up" data-testid="data-quality-page">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-1">Data Quality & SLA</h1>
          <p className="text-slate-500">Store upload compliance, data quality checks, and SLA performance</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-lg px-3 py-1.5">
            <Calendar size={14} className="text-slate-400" />
            <input data-testid="quality-date-picker" type="date" value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)} className="text-sm border-none p-0 focus:ring-0" />
          </div>
          <button data-testid="export-quality-btn" onClick={handleExport}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600">
            <Download size={13} /> Export CSV
          </button>
          <button data-testid="refresh-quality-btn" onClick={fetchAll} disabled={loading}
            className="btn-secondary flex items-center gap-1.5 text-xs">
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-200 mb-6">
        {TABS.map(tab => {
          const Icon = tab.icon;
          return (
            <button key={tab.id} data-testid={`dq-tab-${tab.id}`} onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${
                activeTab === tab.id ? "border-[#0176D3] text-[#0176D3]" : "border-transparent text-slate-500 hover:text-slate-700"}`}>
              <Icon size={16} />{tab.label}
            </button>
          );
        })}
      </div>

      {loading && !sla && (
        <div className="flex items-center justify-center py-20"><div className="spinner" /></div>
      )}

      {!loading && (
        <>
          {/* ── OVERVIEW TAB ── */}
          {activeTab === "overview" && (
            <>
              {/* Score Cards Row */}
              {dataChecks?.scores && (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6" data-testid="quality-scores-row">
                  {[
                    { label: "Overall", value: dataChecks.scores.overall, color: "#0F172A" },
                    { label: "Completeness", value: dataChecks.scores.completeness, color: "#0176D3" },
                    { label: "Accuracy", value: dataChecks.scores.accuracy, color: "#2E844A" },
                    { label: "Consistency", value: dataChecks.scores.consistency, color: "#9050E9" },
                    { label: "Timeliness", value: dataChecks.scores.timeliness, color: "#DD7A01" },
                  ].map(s => (
                    <div key={s.label} className="bg-white border border-slate-200 rounded-xl p-4 text-center" data-testid={`score-${s.label.toLowerCase()}`}>
                      <QualityRing score={Math.round(s.value)} size={64} />
                      <p className="text-xs font-medium text-slate-500 mt-2">{s.label}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* SLA + Scorecard row */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {sla && (
                  <div data-testid="sla-monitor" className="bg-white border border-slate-200 rounded-lg">
                    <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                      <div>
                        <h2 className="font-bold text-sm text-slate-900">SLA Monitoring</h2>
                        <p className="text-xs text-slate-500">Service level agreement compliance</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-slate-900">{sla.complianceRate}%</p>
                        <p className="text-[10px] text-slate-500">Overall SLA</p>
                      </div>
                    </div>
                    <div className="p-5 space-y-5">
                      <div className="grid grid-cols-3 gap-3 text-center">
                        <div><p className="text-xl font-bold text-slate-900">{sla.expectedFiles}</p><p className="text-[10px] text-slate-500">Expected</p></div>
                        <div><p className="text-xl font-bold text-green-600">{sla.receivedFiles}</p><p className="text-[10px] text-slate-500">Received ({sla.onTimeFiles} on time)</p></div>
                        <div><p className="text-xl font-bold text-red-600">{sla.missingFiles}</p><p className="text-[10px] text-slate-500">Missing ({sla.lateFiles} late)</p></div>
                      </div>
                      <div className="space-y-3">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">By File Type</h4>
                        {sla.byFileType?.map(ft => (
                          <div key={ft.name}>
                            <ProgressBar value={ft.compliance} label={ft.name} rightLabel={`${ft.compliance}%`} color={slaColor(ft.compliance)} height={6} />
                            <p className="text-[10px] text-slate-400 mt-0.5">{ft.received}/{ft.expected} files · Target: {ft.target}%</p>
                          </div>
                        ))}
                      </div>
                      {sla.trend !== undefined && (
                        <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                          <span className="text-slate-500">7-day trend</span>
                          <span className={`font-medium ${sla.trend >= 0 ? "text-green-600" : "text-red-600"}`}>
                            {sla.trend >= 0 ? "+" : ""}{sla.trend}% vs last week
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {scorecard && (
                  <div data-testid="quality-scorecard" className="bg-white border border-slate-200 rounded-lg">
                    <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                      <div>
                        <h2 className="font-bold text-sm text-slate-900">Data Quality Scorecard</h2>
                        <p className="text-xs text-slate-500">Overall data health across all sources</p>
                      </div>
                      <div className="text-center">
                        <p className={`text-2xl font-bold ${scorecard.overall >= 80 ? "text-green-600" : scorecard.overall >= 60 ? "text-amber-600" : "text-red-600"}`}>{scorecard.overall}</p>
                        <p className="text-[10px] text-slate-500">Overall</p>
                      </div>
                    </div>
                    <div className="p-5 space-y-5">
                      <div className="flex gap-1.5 overflow-x-auto pb-1">
                        {METRICS.map(m => (
                          <button key={m.id} data-testid={`metric-tab-${m.id}`} onClick={() => setSelectedMetric(m.id)}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                              selectedMetric === m.id ? "text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}
                            style={selectedMetric === m.id ? { background: m.color } : {}}>
                            <m.Icon size={12} />{m.label}
                          </button>
                        ))}
                      </div>
                      {scorecard[selectedMetric] && (() => {
                        const met = scorecard[selectedMetric];
                        const mc = METRICS.find(m => m.id === selectedMetric);
                        return (
                          <div className="space-y-4">
                            <ProgressBar value={met.current} label="Current Score" rightLabel={`${met.current}%`} color={mc.color} height={8} />
                            <ProgressBar value={met.target} label="Target" rightLabel={`${met.target}%`} color="#94A3B8" height={4} />
                            <div className={`p-3 rounded-lg ${met.gap > 0 ? "bg-red-50 border border-red-100" : "bg-green-50 border border-green-100"}`}>
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-slate-700">Gap to Target</span>
                                <span className={`text-sm font-bold ${met.gap > 0 ? "text-red-600" : "text-green-600"}`}>
                                  {met.gap > 0 ? `-${met.gap}%` : "On Target"}
                                </span>
                              </div>
                            </div>
                            {met.issues?.length > 0 && (
                              <div>
                                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Issues</h4>
                                {met.issues.map((issue, i) => (
                                  <div key={i} className="flex items-center justify-between text-xs py-1.5">
                                    <span className="text-slate-600">{issue.description}</span>
                                    <span className="font-medium text-red-600">-{issue.impact}%</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })()}
                      {scorecard.recommendations?.length > 0 && (
                        <div className="pt-3 border-t border-slate-100">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Recommendations</h4>
                          <div className="space-y-1.5">
                            {scorecard.recommendations.slice(0, 3).map((rec, i) => (
                              <div key={i} className="flex items-start gap-2 text-xs text-slate-600">
                                <ThumbsUp size={11} className="text-green-500 mt-0.5 flex-shrink-0" />{rec}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Recommendations from data checks */}
              {dataChecks?.recommendations?.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-5 mb-6" data-testid="dq-recommendations">
                  <h3 className="text-sm font-semibold text-blue-800 mb-3">Improvement Recommendations</h3>
                  <div className="space-y-2">
                    {dataChecks.recommendations.map((rec, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm text-blue-700">
                        <ThumbsUp size={14} className="text-blue-500 mt-0.5 flex-shrink-0" />{rec}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* ── DATA CHECKS TAB ── */}
          {activeTab === "checks" && dataChecks && (
            <div className="space-y-6">
              {["completeness", "accuracy", "consistency", "timeliness", "scorecard"].map(cat => {
                const catChecks = dataChecks.checks.filter(c => c.category === cat);
                if (catChecks.length === 0) return null;
                return (
                  <div key={cat} className="bg-white border border-slate-200 rounded-lg" data-testid={`checks-${cat}`}>
                    <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
                      <h3 className="font-semibold text-sm text-slate-900 capitalize">{cat} Checks</h3>
                      <span className="text-xs text-slate-400">{catChecks.filter(c => c.status === "pass").length}/{catChecks.length} passed</span>
                    </div>
                    <div className="divide-y divide-slate-50">
                      {catChecks.map((check, i) => (
                        <div key={i} className="px-5 py-3 flex items-start gap-3" data-testid={`check-${check.id}`}>
                          <CheckIcon status={check.status} />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between">
                              <p className="text-sm font-medium text-slate-800">{check.name}</p>
                              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                                check.status === "pass" ? "bg-green-100 text-green-700" :
                                check.status === "warn" ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"}`}>
                                {check.value}%
                              </span>
                            </div>
                            <p className="text-xs text-slate-500 mt-0.5">{check.detail}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* ── CATEGORY SCORECARD TAB ── */}
          {activeTab === "categories" && (
            <div className="bg-white border border-slate-200 rounded-lg" data-testid="category-scorecard-table">
              <div className="px-5 py-4 border-b border-slate-100">
                <h2 className="font-bold text-sm text-slate-900">Category-Level Quality Scorecard</h2>
                <p className="text-xs text-slate-500 mt-0.5">Data quality broken down by product category</p>
              </div>
              {categoryScorecard?.categories?.length > 0 ? (
                <table className="w-full text-sm">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase">Category</th>
                      <th className="text-right px-5 py-3 text-xs font-semibold text-slate-500 uppercase">Records</th>
                      <th className="text-right px-5 py-3 text-xs font-semibold text-slate-500 uppercase">Completeness</th>
                      <th className="text-right px-5 py-3 text-xs font-semibold text-slate-500 uppercase">Accuracy</th>
                      <th className="text-right px-5 py-3 text-xs font-semibold text-slate-500 uppercase">Consistency</th>
                      <th className="text-right px-5 py-3 text-xs font-semibold text-slate-500 uppercase">Overall</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {categoryScorecard.categories.map((cat, i) => (
                      <tr key={i} className="hover:bg-slate-50" data-testid={`cat-row-${cat.category}`}>
                        <td className="px-5 py-3 font-medium text-slate-800">{cat.category}</td>
                        <td className="px-5 py-3 text-right text-slate-600">{cat.records.toLocaleString()}</td>
                        <td className="px-5 py-3 text-right">
                          <span className={cat.completeness >= 90 ? "text-green-600" : cat.completeness >= 70 ? "text-amber-600" : "text-red-600"}>{cat.completeness}%</span>
                        </td>
                        <td className="px-5 py-3 text-right">
                          <span className={cat.accuracy >= 90 ? "text-green-600" : cat.accuracy >= 70 ? "text-amber-600" : "text-red-600"}>{cat.accuracy}%</span>
                        </td>
                        <td className="px-5 py-3 text-right">
                          <span className={cat.consistency >= 90 ? "text-green-600" : cat.consistency >= 70 ? "text-amber-600" : "text-red-600"}>{cat.consistency}%</span>
                        </td>
                        <td className="px-5 py-3 text-right font-bold">
                          <span className={cat.overall >= 80 ? "text-green-600" : cat.overall >= 60 ? "text-amber-600" : "text-red-600"}>{cat.overall}%</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="py-12 text-center text-sm text-slate-400">No category data available. Upload sales and master files first.</div>
              )}
            </div>
          )}

          {/* ── TREND TAB ── */}
          {activeTab === "trend" && (
            <div className="bg-white border border-slate-200 rounded-lg p-6" data-testid="quality-trend-chart">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="font-bold text-sm text-slate-900">Quality Score Trend</h2>
                  <p className="text-xs text-slate-500">Quality metrics over time</p>
                </div>
                <TrendingUp size={18} className="text-[#0176D3]" />
              </div>
              {trendData?.trend?.length > 0 ? (
                <div style={{ height: 320 }}>
                  <Line
                    data={{
                      labels: trendData.trend.map(d => {
                        const dt = new Date(d.date + "T00:00:00");
                        return dt.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
                      }),
                      datasets: [
                        { label: "Overall", data: trendData.trend.map(d => d.overall), borderColor: "#0F172A", borderWidth: 2.5, tension: 0.3, pointRadius: 2 },
                        { label: "Completeness", data: trendData.trend.map(d => d.completeness), borderColor: "#0176D3", borderWidth: 1.5, tension: 0.3, pointRadius: 1, borderDash: [4, 2] },
                        { label: "Accuracy", data: trendData.trend.map(d => d.accuracy), borderColor: "#2E844A", borderWidth: 1.5, tension: 0.3, pointRadius: 1, borderDash: [4, 2] },
                      ],
                    }}
                    options={{
                      responsive: true, maintainAspectRatio: false,
                      plugins: { legend: { position: "bottom", labels: { usePointStyle: true, pointStyle: "circle", padding: 16, font: { size: 11 } } } },
                      scales: {
                        x: { grid: { display: false }, ticks: { font: { size: 10 }, maxRotation: 45, autoSkip: true, maxTicksLimit: 15 } },
                        y: { min: 0, max: 100, grid: { color: "#E2E8F0" }, ticks: { font: { size: 10 }, callback: v => `${v}%` } },
                      },
                    }}
                  />
                </div>
              ) : (
                <div className="py-16 text-center text-sm text-slate-400">No trend data available yet.</div>
              )}
            </div>
          )}

          {/* ── STORE TRACKER TAB ── */}
          {activeTab === "stores" && (
            <>
              <div data-testid="store-upload-tracker" className="bg-white border border-slate-200 rounded-lg mb-6">
                <div className="px-5 py-4 border-b border-slate-100">
                  <div className="flex items-center justify-between flex-wrap gap-3">
                    <div>
                      <h2 className="font-bold text-sm text-slate-900">Store Upload Tracker</h2>
                      <p className="text-xs text-slate-500">Real-time upload status for {selectedDate}</p>
                    </div>
                    <div className="flex gap-4 text-xs text-slate-600">
                      <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-green-500" /> Uploaded ({uploaded})</span>
                      <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-red-500" /> Missing ({missing})</span>
                      <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Late ({late})</span>
                      <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-orange-500" /> Partial ({partial})</span>
                    </div>
                  </div>
                  <div className="mt-3">
                    <ProgressBar value={Number(completionRate)} label="Completion Rate" rightLabel={`${completionRate}%`} color="#2E844A" height={6} />
                  </div>
                </div>
                <div className="p-5 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                  {stores.map(store => {
                    const cfg = STATUS_CFG[store.status] || STATUS_CFG.missing;
                    return (
                      <button key={store.code} data-testid={`store-card-${store.code}`} onClick={() => setSelectedStore(store)}
                        className={`p-3 rounded-lg border-2 transition-all hover:shadow-md text-left ${cfg.bg}`}>
                        <div className="flex items-center justify-between mb-1.5">
                          <Store size={14} className="text-slate-500" /><cfg.Icon size={14} className={cfg.color} />
                        </div>
                        <p className="font-bold text-sm text-slate-900">{store.code}</p>
                        <p className="text-[10px] text-slate-500 truncate">{store.name}</p>
                        {store.uploadTime && <p className="text-[10px] text-slate-400 mt-1">{store.uploadTime}</p>}
                        {store.qualityScore > 0 && (
                          <div className="mt-1.5">
                            <div className="w-full h-1 bg-white/60 rounded-full overflow-hidden">
                              <div className="h-full rounded-full"
                                style={{ width: `${store.qualityScore}%`, background: store.qualityScore >= 80 ? "#2E844A" : store.qualityScore >= 60 ? "#DD7A01" : "#EA001E" }} />
                            </div>
                            <p className="text-[9px] text-slate-400 mt-0.5">Q: {store.qualityScore}%</p>
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>

              {stores.length > 0 && (
                <div className="bg-white border border-slate-200 rounded-lg p-5 mb-6" data-testid="store-quality-chart">
                  <h3 className="font-bold text-sm text-slate-900 mb-4">Quality Score by Store</h3>
                  <BarChart labels={stores.map(s => s.code)}
                    datasets={[{ label: "Quality Score", data: stores.map(s => s.qualityScore),
                      colors: stores.map(s => s.qualityScore >= 80 ? "#2E844A" : s.qualityScore >= 60 ? "#DD7A01" : "#EA001E") }]}
                    height={250} showLegend={false} />
                </div>
              )}
            </>
          )}
        </>
      )}

      <StoreModal store={selectedStore} onClose={() => setSelectedStore(null)} />
    </div>
  );
};

export default DataQuality;
