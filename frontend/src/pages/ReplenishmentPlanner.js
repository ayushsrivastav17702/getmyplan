import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  RefreshCw, Download, Package, TrendingDown, AlertTriangle,
  Store, ShoppingCart, Sliders, ArrowRight, ArrowLeftRight,
  Play, CheckCircle, XCircle, Clock, Calendar, Settings,
  ChevronDown, ChevronUp, Filter, Truck, BarChart3, Target,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import FilterPanel from "../components/FilterPanel";
import { BarChart, DoughnutChart, LineChart } from "../components/Charts";

/* ================================================================
   TAB DEFINITIONS
   ================================================================ */
const TABS = [
  { id: "reorder", label: "Reorder Points", icon: Target },
  { id: "orders",  label: "Order Quantity",  icon: ShoppingCart },
  { id: "ist",     label: "Inter-Store Transfer", icon: ArrowLeftRight },
  { id: "run",     label: "Replenishment Run", icon: Play },
  { id: "dashboard", label: "Orders Dashboard", icon: BarChart3 },
];

/* ================================================================
   HELPERS
   ================================================================ */
const fmt = (v) => {
  if (!v && v !== 0) return "0";
  if (v >= 10000000) return `${(v/10000000).toFixed(1)}Cr`;
  if (v >= 100000)   return `${(v/100000).toFixed(1)}L`;
  if (v >= 1000)     return `${(v/1000).toFixed(0)}K`;
  return Math.round(v).toString();
};
const fmtC = (v) => `\u20B9${fmt(v)}`;

const Badge = ({ type, children }) => {
  const cls = {
    "Stock-Out": "bg-red-100 text-red-800",
    Critical: "bg-red-50 text-red-700",
    High: "bg-amber-100 text-amber-800",
    Medium: "bg-yellow-50 text-yellow-700",
    Low: "bg-green-100 text-green-700",
    pending: "bg-amber-100 text-amber-700",
    approved: "bg-green-100 text-green-700",
    rejected: "bg-red-100 text-red-700",
    true: "bg-red-100 text-red-700",
    false: "bg-green-100 text-green-700",
  }[type || children] || "bg-slate-100 text-slate-600";
  return <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cls}`} data-testid={`badge-${type || children}`}>{children}</span>;
};

const KPI = ({ label, value, sub, icon: Icon, color = "#0176D3", testId }) => (
  <div className="metric-card" data-testid={testId}>
    <div className="flex items-center justify-between mb-2">
      <span className="metric-label">{label}</span>
      {Icon && <Icon size={18} style={{ color }} />}
    </div>
    <span className="metric-value" style={{ color }}>{value}</span>
    {sub && <span className="text-xs text-slate-500 block mt-1">{sub}</span>}
  </div>
);

/* ================================================================
   MAIN COMPONENT
   ================================================================ */
const ReplenishmentPlanner = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("reorder");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Config
  const [leadTime, setLeadTime] = useState(14);
  const [safetyDays, setSafetyDays] = useState(7);
  const [coverDays, setCoverDays] = useState(21);
  const [moq, setMoq] = useState(1);
  const [packSize, setPackSize] = useState(1);

  // Filters
  const [filterOptions, setFilterOptions] = useState({});
  const [filters, setFilters] = useState({
    startDate: "", endDate: "",
    categories: [], channels: [], regions: [],
  });

  // Data stores
  const [reorderData, setReorderData] = useState(null);
  const [orderData, setOrderData] = useState(null);
  const [istData, setIstData] = useState(null);
  const [runResult, setRunResult] = useState(null);
  const [runHistory, setRunHistory] = useState([]);
  const [ordersData, setOrdersData] = useState(null);
  const [scheduleData, setScheduleData] = useState(null);

  // IST thresholds
  const [overstockDoh, setOverstockDoh] = useState(30);
  const [understockDoh, setUnderstockDoh] = useState(7);

  // Orders filter
  const [orderStatusFilter, setOrderStatusFilter] = useState("");
  const [selectedOrders, setSelectedOrders] = useState(new Set());

  const fetchFilterOptions = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/analytics/filter-options`);
      setFilterOptions(r.data);
      if (r.data.dateRange?.min) {
        setFilters(prev => ({
          ...prev,
          startDate: r.data.dateRange.min.split("T")[0],
          endDate: r.data.dateRange.max.split("T")[0],
        }));
      }
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchFilterOptions(); }, [fetchFilterOptions]);

  const qp = () => {
    const p = new URLSearchParams();
    if (filters.startDate) p.append("start_date", filters.startDate);
    if (filters.endDate) p.append("end_date", filters.endDate);
    if (filters.categories?.length) p.append("categories", filters.categories.join(","));
    if (filters.channels?.length) p.append("channels", filters.channels.join(","));
    if (filters.regions?.length) p.append("regions", filters.regions.join(","));
    p.append("lead_time_days", leadTime);
    p.append("safety_days", safetyDays);
    return p.toString();
  };

  /* --- Tab data fetchers --- */
  const fetchReorder = async () => {
    setLoading(true); setError(null);
    try {
      const r = await axios.get(`${API}/analytics/replenishment/reorder-points?${qp()}`);
      if (r.data.error) setError(r.data.error); else setReorderData(r.data);
    } catch { setError("Failed to load reorder points"); }
    finally { setLoading(false); }
  };

  const fetchOrders = async () => {
    setLoading(true); setError(null);
    try {
      const p = qp();
      const r = await axios.get(`${API}/analytics/replenishment/order-quantity?${p}&cover_days=${coverDays}&moq=${moq}&pack_size=${packSize}`);
      if (r.data.error) setError(r.data.error); else setOrderData(r.data);
    } catch { setError("Failed to load order quantities"); }
    finally { setLoading(false); }
  };

  const fetchIST = async () => {
    setLoading(true); setError(null);
    try {
      const p = qp();
      const r = await axios.get(`${API}/analytics/replenishment/ist?${p}&overstock_doh_threshold=${overstockDoh}&understock_doh_threshold=${understockDoh}`);
      if (r.data.error) setError(r.data.error); else setIstData(r.data);
    } catch { setError("Failed to load IST suggestions"); }
    finally { setLoading(false); }
  };

  const fetchRunHistory = async () => {
    try {
      const r = await axios.get(`${API}/analytics/replenishment/runs`);
      setRunHistory(r.data.runs || []);
    } catch { /* ignore */ }
  };

  const fetchDashboardOrders = async () => {
    setLoading(true); setError(null);
    try {
      const params = new URLSearchParams();
      if (orderStatusFilter) params.append("status", orderStatusFilter);
      const r = await axios.get(`${API}/analytics/replenishment/orders?${params}`);
      setOrdersData(r.data);
    } catch { setError("Failed to load orders"); }
    finally { setLoading(false); }
  };

  const fetchSchedule = async () => {
    try {
      const r = await axios.get(`${API}/analytics/replenishment/schedule`);
      setScheduleData(r.data);
    } catch { /* ignore */ }
  };

  // Load data for active tab
  useEffect(() => {
    const loaders = {
      reorder: fetchReorder,
      orders: fetchOrders,
      ist: fetchIST,
      run: () => { fetchRunHistory(); },
      dashboard: () => { fetchDashboardOrders(); fetchSchedule(); },
    };
    loaders[activeTab]?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const handleFilterChange = (f, v) => setFilters(prev => ({ ...prev, [f]: v }));
  const handleApply = () => {
    const loaders = { reorder: fetchReorder, orders: fetchOrders, ist: fetchIST };
    loaders[activeTab]?.();
  };
  const handleReset = () => {
    setFilters({
      startDate: filterOptions.dateRange?.min?.split("T")[0] || "",
      endDate: filterOptions.dateRange?.max?.split("T")[0] || "",
      categories: [], channels: [], regions: [],
    });
    setLeadTime(14); setSafetyDays(7); setCoverDays(21); setMoq(1); setPackSize(1);
  };

  /* --- Replenishment Run --- */
  const runReplenishment = async () => {
    setLoading(true); setError(null); setRunResult(null);
    try {
      const r = await axios.post(`${API}/analytics/replenishment/run?lead_time_days=${leadTime}&safety_days=${safetyDays}&cover_days=${coverDays}&moq=${moq}&pack_size=${packSize}`);
      if (r.data.error) setError(r.data.error);
      else { setRunResult(r.data); fetchRunHistory(); }
    } catch { setError("Failed to run replenishment"); }
    finally { setLoading(false); }
  };

  /* --- Order actions (REP-29, REP-30) --- */
  const handleOrderAction = async (orderId, action) => {
    try {
      await axios.post(`${API}/analytics/replenishment/orders/action`, { order_id: orderId, action, notes: "" });
      fetchDashboardOrders();
    } catch (err) { console.error(err); }
  };

  const handleBulkAction = async (action) => {
    if (selectedOrders.size === 0) return;
    try {
      await axios.post(`${API}/analytics/replenishment/orders/bulk-action`, {
        order_ids: Array.from(selectedOrders), action, notes: "",
      });
      setSelectedOrders(new Set());
      fetchDashboardOrders();
    } catch (err) { console.error(err); }
  };

  /* --- IST Transfer Actions (REP-21) --- */
  const handleISTAction = async (transferId, action) => {
    try {
      await axios.post(`${API}/analytics/replenishment/ist/action`, { transfer_id: transferId, action, notes: "" });
      fetchIST();
    } catch (err) { console.error(err); }
  };

  /* --- Schedule (REP-32) --- */
  const saveSchedule = async (sched) => {
    try {
      await axios.post(`${API}/analytics/replenishment/schedule`, sched);
      setScheduleData(sched);
    } catch (err) { console.error(err); }
  };

  /* --- Manual Override (REP-07) --- */
  const handleOverride = async (storeCode, sku, reorderPoint) => {
    try {
      await axios.post(`${API}/analytics/replenishment/reorder-points/override`, {
        store_code: storeCode, sku: String(sku), reorder_point: Number(reorderPoint),
      });
      fetchReorder();
    } catch (err) { console.error(err); }
  };

  /* --- CSV Export (REP-31) --- */
  const exportCSV = (rows, filename) => {
    if (!rows?.length) return;
    const keys = Object.keys(rows[0]);
    const csv = [keys.join(","), ...rows.map(r => keys.map(k => `"${r[k] ?? ""}"`).join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url;
    a.download = filename; a.click();
  };

  /* ================================================================
     RENDER
     ================================================================ */
  return (
    <div className="animate-fade-in-up" data-testid="replenishment-page">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
            Replenishment Planner
          </h1>
          <p className="text-slate-500">
            Reorder points, order quantities, inter-store transfers, and replenishment runs
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-slate-200 overflow-x-auto" data-testid="repl-tabs">
        {TABS.map(t => (
          <button
            key={t.id}
            data-testid={`tab-${t.id}`}
            onClick={() => { setError(null); setActiveTab(t.id); }}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === t.id
                ? "border-[#0176D3] text-[#0176D3]"
                : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
            }`}
          >
            <t.icon size={16} />{t.label}
          </button>
        ))}
      </div>

      {/* Filter Panel — shown for first 3 tabs */}
      {["reorder", "orders", "ist"].includes(activeTab) && (
        <FilterPanel
          filters={filters} filterOptions={filterOptions}
          onFilterChange={handleFilterChange} onApply={handleApply} onReset={handleReset}
          pageType="replenishment"
        />
      )}

      {/* Error */}
      {error && (
        <div className="bg-amber-50 border border-amber-200 p-6 mb-6 rounded text-center" data-testid="repl-error">
          <AlertTriangle size={32} className="text-amber-500 mx-auto mb-2" />
          <p className="text-amber-700 mb-3">{error}</p>
          <button onClick={() => navigate("/upload")} className="btn-primary inline-flex items-center gap-2 text-sm">
            Go to Data Upload <ArrowRight size={14} />
          </button>
        </div>
      )}

      {/* Loading */}
      {loading && <div className="flex items-center justify-center py-16"><div className="spinner" /></div>}

      {/* ============== TAB: REORDER POINTS ============== */}
      {activeTab === "reorder" && !loading && !error && reorderData && (
        <ReorderTab data={reorderData} leadTime={leadTime} setLeadTime={setLeadTime}
          safetyDays={safetyDays} setSafetyDays={setSafetyDays}
          onRecalc={fetchReorder} onOverride={handleOverride} />
      )}

      {/* ============== TAB: ORDER QUANTITY ============== */}
      {activeTab === "orders" && !loading && !error && orderData && (
        <OrderQuantityTab data={orderData} coverDays={coverDays} setCoverDays={setCoverDays}
          moq={moq} setMoq={setMoq} packSize={packSize} setPackSize={setPackSize}
          leadTime={leadTime} setLeadTime={setLeadTime}
          safetyDays={safetyDays} setSafetyDays={setSafetyDays}
          onRecalc={fetchOrders} onExport={() => exportCSV(orderData.detail, "order_quantities.csv")} />
      )}

      {/* ============== TAB: IST ============== */}
      {activeTab === "ist" && !loading && !error && istData && (
        <ISTTab data={istData}
          overstockDoh={overstockDoh} setOverstockDoh={setOverstockDoh}
          understockDoh={understockDoh} setUnderstockDoh={setUnderstockDoh}
          onRecalc={fetchIST} onAction={handleISTAction} />
      )}

      {/* ============== TAB: REPLENISHMENT RUN ============== */}
      {activeTab === "run" && !loading && !error && (
        <RunTab leadTime={leadTime} setLeadTime={setLeadTime}
          safetyDays={safetyDays} setSafetyDays={setSafetyDays}
          coverDays={coverDays} setCoverDays={setCoverDays}
          moq={moq} setMoq={setMoq} packSize={packSize} setPackSize={setPackSize}
          onRun={runReplenishment} result={runResult} history={runHistory} loading={loading} />
      )}

      {/* ============== TAB: ORDERS DASHBOARD ============== */}
      {activeTab === "dashboard" && !loading && !error && (
        <DashboardTab data={ordersData} scheduleData={scheduleData}
          statusFilter={orderStatusFilter} setStatusFilter={(v) => { setOrderStatusFilter(v); }}
          onRefresh={fetchDashboardOrders}
          selectedOrders={selectedOrders} setSelectedOrders={setSelectedOrders}
          onOrderAction={handleOrderAction} onBulkAction={handleBulkAction}
          onSaveSchedule={saveSchedule}
          onExport={() => exportCSV(ordersData?.orders, "replenishment_orders.csv")} />
      )}

      {/* Empty state */}
      {!loading && !error && !reorderData && activeTab === "reorder" && (
        <EmptyState />
      )}
      {!loading && !error && !orderData && activeTab === "orders" && (
        <EmptyState />
      )}
      {!loading && !error && !istData && activeTab === "ist" && (
        <EmptyState />
      )}
    </div>
  );
};

/* ================================================================
   REORDER POINTS TAB (REP-01 to REP-08)
   ================================================================ */
const ReorderTab = ({ data, leadTime, setLeadTime, safetyDays, setSafetyDays, onRecalc, onOverride }) => {
  const s = data.summary || {};
  const [overrideRow, setOverrideRow] = useState(null);
  const [overrideVal, setOverrideVal] = useState("");

  return (
    <div data-testid="tab-reorder-content">
      {/* Config */}
      <div className="bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded shadow-sm p-5 mb-6" data-testid="reorder-config">
        <div className="flex items-center gap-2 mb-3">
          <Settings size={16} className="text-[#0176D3]" />
          <h3 className="text-sm font-semibold text-slate-900">Reorder Point Formula</h3>
        </div>
        <p className="text-xs text-slate-600 font-mono mb-4">RP = (Avg Daily Sales x Lead Time) + Safety Stock</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium text-slate-700 flex justify-between">
              Lead Time <span className="text-[#0176D3] font-semibold">{leadTime}d</span>
            </label>
            <input type="range" min="0" max="60" value={leadTime}
              onChange={e => setLeadTime(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg accent-[#0176D3] mt-1"
              data-testid="slider-lead-time" />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700 flex justify-between">
              Safety Days <span className="text-[#2E844A] font-semibold">{safetyDays}d</span>
            </label>
            <input type="range" min="0" max="30" value={safetyDays}
              onChange={e => setSafetyDays(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg accent-[#2E844A] mt-1"
              data-testid="slider-safety-days" />
          </div>
        </div>
        <button onClick={onRecalc} className="btn-primary mt-3 flex items-center gap-2 text-sm" data-testid="recalculate-reorder-btn">
          <RefreshCw size={14} /> Recalculate
        </button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <KPI label="Total Store-SKU Pairs" value={fmt(s.total_store_sku_pairs)} icon={Package} testId="kpi-total-pairs" />
        <KPI label="Trigger Replenishment" value={fmt(s.triggered_count)} icon={AlertTriangle} color="#EA001E" testId="kpi-triggered" />
        <KPI label="High Variability" value={fmt(s.high_variability_count)} icon={TrendingDown} color="#DD7A01" testId="kpi-high-var" />
        <KPI label="Seasonal Styles" value={fmt(s.seasonal_count)} icon={Calendar} color="#9050E9" testId="kpi-seasonal" />
        <KPI label="New Styles" value={fmt(s.new_style_count)} icon={Store} color="#0B827C" testId="kpi-new-style" />
        <KPI label="Manual Overrides" value={fmt(s.override_count)} icon={Settings} color="#596773" testId="kpi-overrides" />
      </div>

      {/* Detail Table */}
      {data.detail?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="reorder-table">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center">
            <div>
              <h3 className="font-semibold text-slate-900">Reorder Point Details</h3>
              <p className="text-xs text-slate-500 mt-1">Sorted by trigger status (triggered first)</p>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table w-full">
              <thead>
                <tr>
                  <th>Store</th><th>SKU</th><th>Style</th><th>Size</th>
                  <th>Avg Daily Sales</th><th>Lead Demand</th><th>Safety Stock</th>
                  <th>Reorder Point</th><th>Current SOH</th><th>Trigger</th>
                  <th>Flags</th><th>Override</th>
                </tr>
              </thead>
              <tbody>
                {data.detail.slice(0, 50).map((r, i) => (
                  <tr key={i}>
                    <td className="font-medium">{r.store_code}</td>
                    <td>{r.sku}</td>
                    <td>{r.style}</td>
                    <td>{r.size}</td>
                    <td>{(r.avg_daily_sales || 0).toFixed(2)}</td>
                    <td>{Math.round(r.demand_during_lead)}</td>
                    <td>{Math.round(r.safety_stock)}</td>
                    <td className="font-semibold text-[#0176D3]">{Math.round(r.reorder_point)}</td>
                    <td>{Math.round(r.current_soh)}</td>
                    <td><Badge type={String(r.trigger_replenishment)}>{r.trigger_replenishment ? "YES" : "No"}</Badge></td>
                    <td className="space-x-1">
                      {r.is_high_variability && <span className="text-xs bg-amber-50 text-amber-700 px-1 rounded">HiVar</span>}
                      {r.is_seasonal && <span className="text-xs bg-purple-50 text-purple-700 px-1 rounded">Season</span>}
                      {r.is_new_style && <span className="text-xs bg-teal-50 text-teal-700 px-1 rounded">New</span>}
                      {r.has_manual_override && <span className="text-xs bg-blue-50 text-blue-700 px-1 rounded">Override</span>}
                    </td>
                    <td>
                      {overrideRow === i ? (
                        <div className="flex gap-1 items-center">
                          <input type="number" value={overrideVal} onChange={e => setOverrideVal(e.target.value)}
                            className="w-16 px-1 py-0.5 border rounded text-xs" data-testid={`override-input-${i}`} />
                          <button onClick={() => { onOverride(r.store_code, r.sku, overrideVal); setOverrideRow(null); }}
                            className="text-green-600 hover:text-green-800" data-testid={`override-save-${i}`}>
                            <CheckCircle size={14} />
                          </button>
                          <button onClick={() => setOverrideRow(null)} className="text-slate-400">
                            <XCircle size={14} />
                          </button>
                        </div>
                      ) : (
                        <button onClick={() => { setOverrideRow(i); setOverrideVal(Math.round(r.reorder_point)); }}
                          className="text-xs text-[#0176D3] hover:underline" data-testid={`override-btn-${i}`}>
                          Set
                        </button>
                      )}
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


/* ================================================================
   ORDER QUANTITY TAB (REP-09 to REP-15)
   ================================================================ */
const OrderQuantityTab = ({ data, coverDays, setCoverDays, moq, setMoq, packSize, setPackSize,
  leadTime, setLeadTime, safetyDays, setSafetyDays, onRecalc, onExport }) => {
  const s = data.summary || {};

  return (
    <div data-testid="tab-orders-content">
      {/* Config */}
      <div className="bg-gradient-to-r from-slate-50 to-emerald-50 border border-slate-200 rounded shadow-sm p-5 mb-6" data-testid="order-config">
        <div className="flex items-center gap-2 mb-3">
          <Settings size={16} className="text-[#2E844A]" />
          <h3 className="text-sm font-semibold text-slate-900">Order Quantity Formula</h3>
        </div>
        <p className="text-xs text-slate-600 font-mono mb-4">Order Qty = (Cover Days x Avg Sales) - Current Stock | MOQ & Pack Size applied</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          <div>
            <label className="text-xs font-medium text-slate-600">Lead Time</label>
            <input type="number" min="0" max="60" value={leadTime} onChange={e => setLeadTime(Number(e.target.value))}
              className="input-field mt-1" data-testid="input-lead-time" />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600">Safety Days</label>
            <input type="number" min="0" max="30" value={safetyDays} onChange={e => setSafetyDays(Number(e.target.value))}
              className="input-field mt-1" data-testid="input-safety-days" />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600">Cover Days</label>
            <input type="number" min="1" max="90" value={coverDays} onChange={e => setCoverDays(Number(e.target.value))}
              className="input-field mt-1" data-testid="input-cover-days" />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600">MOQ</label>
            <input type="number" min="1" max="1000" value={moq} onChange={e => setMoq(Number(e.target.value))}
              className="input-field mt-1" data-testid="input-moq" />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600">Pack Size</label>
            <input type="number" min="1" max="100" value={packSize} onChange={e => setPackSize(Number(e.target.value))}
              className="input-field mt-1" data-testid="input-pack-size" />
          </div>
        </div>
        <div className="flex gap-2 mt-3">
          <button onClick={onRecalc} className="btn-primary flex items-center gap-2 text-sm" data-testid="recalculate-orders-btn">
            <RefreshCw size={14} /> Recalculate
          </button>
          <button onClick={onExport} className="btn-secondary flex items-center gap-2 text-sm" data-testid="export-orders-btn">
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KPI label="Total PO Value" value={fmtC(s.total_po_value)} sub={`${fmt(s.total_order_units)} units`} icon={ShoppingCart} testId="kpi-oq-po" />
        <KPI label="SKUs to Order" value={fmt(s.skus_needing_order)} icon={Package} color="#DD7A01" testId="kpi-oq-skus" />
        <KPI label="Stores Needing Orders" value={fmt(s.stores_needing_order)} icon={Store} color="#2E844A" testId="kpi-oq-stores" />
        <KPI label="Config" value={`${s.cover_days}d / MOQ ${s.moq} / Pack ${s.pack_size}`} icon={Settings} color="#596773" testId="kpi-oq-config" />
      </div>

      {/* Warehouse Alerts (REP-13, REP-27) */}
      {data.warehouse_alerts?.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded p-4 mb-6" data-testid="warehouse-alerts">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={16} className="text-red-600" />
            <h4 className="text-sm font-semibold text-red-800">Warehouse Stock Alerts</h4>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead><tr className="text-left text-red-700">
                <th className="pb-1">SKU</th><th>Total Demand</th><th>WH Available</th><th>Shortfall</th>
              </tr></thead>
              <tbody>
                {data.warehouse_alerts.slice(0, 10).map((a, i) => (
                  <tr key={i} className="border-t border-red-100">
                    <td className="py-1 font-medium">{a.sku}</td>
                    <td>{fmt(a.total_demand)}</td>
                    <td>{fmt(a.warehouse_available)}</td>
                    <td className="text-red-700 font-semibold">{fmt(a.shortfall)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {data.by_priority?.length > 0 && (
          <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="chart-oq-priority">
            <h3 className="font-semibold text-slate-900 mb-3">By Priority</h3>
            <DoughnutChart
              labels={data.by_priority.map(p => p.priority)}
              data={data.by_priority.map(p => p.count)}
              height={240} formatValue={fmt}
            />
          </div>
        )}
        {data.by_store?.length > 0 && (
          <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="chart-oq-store">
            <h3 className="font-semibold text-slate-900 mb-3">PO Value by Store</h3>
            <BarChart
              labels={data.by_store.slice(0, 10).map(s => s.store_code)}
              datasets={[{ label: "PO Value", data: data.by_store.slice(0, 10).map(s => s.total_value), color: "#0176D3" }]}
              horizontal height={240} formatValue={fmtC} showLegend={false}
            />
          </div>
        )}
      </div>

      {/* Detail table */}
      {data.detail?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="order-detail-table">
          <div className="p-4 border-b border-slate-100">
            <h3 className="font-semibold text-slate-900">Order Quantity Details</h3>
            <p className="text-xs text-slate-500 mt-1">Store class allocation applied (REP-14/15)</p>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table w-full">
              <thead>
                <tr>
                  <th>SKU</th><th>Style</th><th>Store</th><th>Class</th>
                  <th>Avg Sales/Day</th><th>SOH</th><th>Requirement</th>
                  <th>Order Qty</th><th>PO Value</th><th>Priority</th>
                </tr>
              </thead>
              <tbody>
                {data.detail.slice(0, 50).map((r, i) => (
                  <tr key={i}>
                    <td className="font-medium">{r.sku}</td>
                    <td>{r.style}</td>
                    <td>{r.store_code}</td>
                    <td><span className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">{r.store_class}</span></td>
                    <td>{(r.avg_daily_sales || 0).toFixed(2)}</td>
                    <td>{Math.round(r.current_soh)}</td>
                    <td>{Math.round(r.requirement)}</td>
                    <td className="font-semibold text-[#0176D3]">{r.order_qty}</td>
                    <td>{fmtC(r.po_value)}</td>
                    <td><Badge type={r.priority}>{r.priority}</Badge></td>
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


/* ================================================================
   IST TAB (REP-16 to REP-21)
   ================================================================ */
const ISTTab = ({ data, overstockDoh, setOverstockDoh, understockDoh, setUnderstockDoh, onRecalc, onAction }) => {
  const s = data.summary || {};

  return (
    <div data-testid="tab-ist-content">
      {/* Config */}
      <div className="bg-gradient-to-r from-slate-50 to-purple-50 border border-slate-200 rounded shadow-sm p-5 mb-6" data-testid="ist-config">
        <div className="flex items-center gap-2 mb-3">
          <ArrowLeftRight size={16} className="text-[#9050E9]" />
          <h3 className="text-sm font-semibold text-slate-900">Inter-Store Transfer Thresholds</h3>
        </div>
        <p className="text-xs text-slate-600 font-mono mb-4">Transfer Qty = Min(Overstock Surplus, Understock Need) | Same-region prioritized</p>
        <div className="grid grid-cols-2 gap-4 max-w-md">
          <div>
            <label className="text-xs font-medium text-slate-600">Overstock DOH Threshold</label>
            <input type="number" min="10" max="90" value={overstockDoh} onChange={e => setOverstockDoh(Number(e.target.value))}
              className="input-field mt-1" data-testid="input-overstock-doh" />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600">Understock DOH Threshold</label>
            <input type="number" min="1" max="30" value={understockDoh} onChange={e => setUnderstockDoh(Number(e.target.value))}
              className="input-field mt-1" data-testid="input-understock-doh" />
          </div>
        </div>
        <button onClick={onRecalc} className="btn-primary mt-3 flex items-center gap-2 text-sm" data-testid="recalculate-ist-btn">
          <RefreshCw size={14} /> Recalculate
        </button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <KPI label="Overstocked Stores" value={fmt(s.overstocked_stores)} sub={`DOH > ${s.overstock_threshold_doh}d`} icon={ChevronUp} color="#DD7A01" testId="kpi-ist-over" />
        <KPI label="Understocked Stores" value={fmt(s.understocked_stores)} sub={`DOH < ${s.understock_threshold_doh}d`} icon={ChevronDown} color="#EA001E" testId="kpi-ist-under" />
        <KPI label="Suggested Transfers" value={fmt(s.total_suggested_transfers)} icon={ArrowLeftRight} color="#0176D3" testId="kpi-ist-transfers" />
        <KPI label="Units to Transfer" value={fmt(s.total_transfer_units)} icon={Truck} color="#2E844A" testId="kpi-ist-units" />
        <KPI label="Same Region %" value={`${s.same_region_pct || 0}%`} sub="Lower cost transfers" icon={Target} color="#9050E9" testId="kpi-ist-region" />
      </div>

      {/* Transfer Suggestions Table */}
      {data.transfers?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm mb-6" data-testid="ist-transfers-table">
          <div className="p-4 border-b border-slate-100">
            <h3 className="font-semibold text-slate-900">Transfer Suggestions</h3>
            <p className="text-xs text-slate-500 mt-1">Prioritized by same-region and surplus availability</p>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table w-full">
              <thead>
                <tr>
                  <th>ID</th><th>SKU</th><th>Style</th>
                  <th>Source Store</th><th>Source DOH</th>
                  <th>Dest Store</th><th>Dest DOH</th>
                  <th>Transfer Qty</th><th>Same Region</th><th>Action</th>
                </tr>
              </thead>
              <tbody>
                {data.transfers.slice(0, 50).map((t, i) => (
                  <tr key={i}>
                    <td className="font-mono text-xs">{t.transfer_id}</td>
                    <td>{t.sku}</td>
                    <td>{t.style}</td>
                    <td className="font-medium">{t.source_store}</td>
                    <td>{t.source_doh}d</td>
                    <td className="font-medium">{t.dest_store}</td>
                    <td className={t.dest_doh < 7 ? "text-red-600 font-semibold" : ""}>{t.dest_doh}d</td>
                    <td className="font-semibold text-[#0176D3]">{t.transfer_qty}</td>
                    <td>{t.same_region ? <span className="text-green-600 text-xs">Yes</span> : <span className="text-slate-400 text-xs">No</span>}</td>
                    <td>
                      <div className="flex gap-1">
                        <button onClick={() => onAction(t.transfer_id, "approve")}
                          className="text-green-600 hover:text-green-800" data-testid={`ist-approve-${i}`}>
                          <CheckCircle size={16} />
                        </button>
                        <button onClick={() => onAction(t.transfer_id, "reject")}
                          className="text-red-500 hover:text-red-700" data-testid={`ist-reject-${i}`}>
                          <XCircle size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Overstocked / Understocked Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {data.overstocked_detail?.length > 0 && (
          <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="ist-overstocked-table">
            <div className="p-4 border-b border-slate-100">
              <h3 className="font-semibold text-slate-900">Overstocked Stores (DOH &gt; {overstockDoh}d)</h3>
            </div>
            <div className="overflow-x-auto max-h-64 overflow-y-auto">
              <table className="data-table w-full">
                <thead><tr><th>Store</th><th>SKU</th><th>SOH</th><th>DOH</th><th>Surplus</th></tr></thead>
                <tbody>
                  {data.overstocked_detail.slice(0, 30).map((r, i) => (
                    <tr key={i}>
                      <td>{r.store_code}</td><td>{r.sku}</td><td>{Math.round(r.soh)}</td>
                      <td className="text-amber-600 font-semibold">{r.doh}d</td><td>{Math.round(r.surplus)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        {data.understocked_detail?.length > 0 && (
          <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="ist-understocked-table">
            <div className="p-4 border-b border-slate-100">
              <h3 className="font-semibold text-slate-900">Understocked Stores (DOH &lt; {understockDoh}d)</h3>
            </div>
            <div className="overflow-x-auto max-h-64 overflow-y-auto">
              <table className="data-table w-full">
                <thead><tr><th>Store</th><th>SKU</th><th>SOH</th><th>DOH</th><th>Need</th></tr></thead>
                <tbody>
                  {data.understocked_detail.slice(0, 30).map((r, i) => (
                    <tr key={i}>
                      <td>{r.store_code}</td><td>{r.sku}</td><td>{Math.round(r.soh)}</td>
                      <td className="text-red-600 font-semibold">{r.doh}d</td><td>{Math.round(r.need)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};


/* ================================================================
   REPLENISHMENT RUN TAB (REP-22 to REP-27)
   ================================================================ */
const RunTab = ({ leadTime, setLeadTime, safetyDays, setSafetyDays, coverDays, setCoverDays,
  moq, setMoq, packSize, setPackSize, onRun, result, history, loading }) => (
  <div data-testid="tab-run-content">
    {/* Config */}
    <div className="bg-gradient-to-r from-slate-50 to-green-50 border border-slate-200 rounded shadow-sm p-5 mb-6" data-testid="run-config">
      <div className="flex items-center gap-2 mb-3">
        <Play size={16} className="text-[#2E844A]" />
        <h3 className="text-sm font-semibold text-slate-900">Run Replenishment Algorithm</h3>
      </div>
      <p className="text-xs text-slate-600 mb-4">Generates purchase orders, compares pre vs post metrics, and checks warehouse stock exhaustion.</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div>
          <label className="text-xs font-medium text-slate-600">Lead Time</label>
          <input type="number" min="0" max="60" value={leadTime} onChange={e => setLeadTime(Number(e.target.value))}
            className="input-field mt-1" data-testid="run-lead-time" />
        </div>
        <div>
          <label className="text-xs font-medium text-slate-600">Safety Days</label>
          <input type="number" min="0" max="30" value={safetyDays} onChange={e => setSafetyDays(Number(e.target.value))}
            className="input-field mt-1" data-testid="run-safety-days" />
        </div>
        <div>
          <label className="text-xs font-medium text-slate-600">Cover Days</label>
          <input type="number" min="1" max="90" value={coverDays} onChange={e => setCoverDays(Number(e.target.value))}
            className="input-field mt-1" data-testid="run-cover-days" />
        </div>
        <div>
          <label className="text-xs font-medium text-slate-600">MOQ</label>
          <input type="number" min="1" value={moq} onChange={e => setMoq(Number(e.target.value))}
            className="input-field mt-1" data-testid="run-moq" />
        </div>
        <div>
          <label className="text-xs font-medium text-slate-600">Pack Size</label>
          <input type="number" min="1" value={packSize} onChange={e => setPackSize(Number(e.target.value))}
            className="input-field mt-1" data-testid="run-pack-size" />
        </div>
      </div>
      <button onClick={onRun} disabled={loading}
        className="btn-primary mt-4 flex items-center gap-2" data-testid="run-replenishment-btn">
        <Play size={16} /> {loading ? "Running..." : "Run Replenishment"}
      </button>
    </div>

    {/* Result */}
    {result && (
      <div className="space-y-6 mb-8" data-testid="run-result">
        {/* Pre vs Post Comparison (REP-23) */}
        <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="run-comparison">
          <h3 className="font-semibold text-slate-900 mb-4">Pre vs Post Comparison</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {/* Stock-out Reduction (REP-24) */}
            <div className="text-center" data-testid="metric-stockout-reduction">
              <p className="text-xs text-slate-500 mb-1">Stock-Out Reduction</p>
              <p className="text-3xl font-bold text-[#2E844A]">{result.improvements?.stockout_reduction_pct}%</p>
              <div className="flex justify-center gap-4 mt-2 text-xs">
                <span className="text-slate-500">Pre: <b className="text-red-600">{fmt(result.pre_metrics?.stockout_count)}</b></span>
                <span className="text-slate-500">Post: <b className="text-green-600">{fmt(result.post_metrics?.stockout_count)}</b></span>
              </div>
            </div>
            {/* Fill Rate (REP-25) */}
            <div className="text-center" data-testid="metric-fill-rate">
              <p className="text-xs text-slate-500 mb-1">Fill Rate Improvement</p>
              <p className="text-3xl font-bold text-[#0176D3]">+{result.improvements?.fill_rate_improvement}%</p>
              <div className="flex justify-center gap-4 mt-2 text-xs">
                <span className="text-slate-500">Pre: <b>{result.pre_metrics?.fill_rate}%</b></span>
                <span className="text-slate-500">Post: <b className="text-[#0176D3]">{result.post_metrics?.fill_rate}%</b></span>
              </div>
            </div>
            {/* DOH (REP-26) */}
            <div className="text-center" data-testid="metric-doh-improvement">
              <p className="text-xs text-slate-500 mb-1">DOH Improvement</p>
              <p className="text-3xl font-bold text-[#9050E9]">+{result.improvements?.doh_improvement}d</p>
              <div className="flex justify-center gap-4 mt-2 text-xs">
                <span className="text-slate-500">Pre: <b>{result.pre_metrics?.avg_doh}d</b></span>
                <span className="text-slate-500">Post: <b className="text-[#9050E9]">{result.post_metrics?.avg_doh}d</b></span>
              </div>
            </div>
          </div>
        </div>

        {/* Orders Generated */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KPI label="Orders Generated" value={fmt(result.total_orders)} icon={Package} testId="kpi-run-orders" />
          <KPI label="Total Units" value={fmt(result.total_units)} icon={ShoppingCart} color="#2E844A" testId="kpi-run-units" />
          <KPI label="Total PO Value" value={fmtC(result.total_po_value)} icon={Target} color="#DD7A01" testId="kpi-run-po" />
          <KPI label="Run ID" value={result.run_id} icon={Settings} color="#596773" testId="kpi-run-id" />
        </div>

        {/* Warehouse Alerts (REP-27) */}
        {result.warehouse_alerts?.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded p-4" data-testid="run-wh-alerts">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle size={16} className="text-red-600" />
              <h4 className="text-sm font-semibold text-red-800">Warehouse Stock Exhaustion Alerts</h4>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead><tr className="text-left text-red-700">
                  <th className="pb-1">SKU</th><th>Demand</th><th>WH Stock</th><th>Shortfall</th><th>Exhausted</th>
                </tr></thead>
                <tbody>
                  {result.warehouse_alerts.slice(0, 15).map((a, i) => (
                    <tr key={i} className="border-t border-red-100">
                      <td className="py-1 font-medium">{a.sku}</td>
                      <td>{fmt(a.demand)}</td>
                      <td>{fmt(a.warehouse_stock)}</td>
                      <td className="text-red-700 font-semibold">{fmt(a.shortfall)}</td>
                      <td>{a.exhausted ? <Badge type="true">YES</Badge> : <span className="text-green-600">No</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    )}

    {/* Run History */}
    {history.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="run-history">
        <div className="p-4 border-b border-slate-100">
          <h3 className="font-semibold text-slate-900">Replenishment Run History</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table w-full">
            <thead>
              <tr>
                <th>Run ID</th><th>Date</th><th>Orders</th><th>Units</th><th>PO Value</th>
                <th>Stock-Out Reduction</th><th>Fill Rate +</th><th>Status</th>
              </tr>
            </thead>
            <tbody>
              {history.slice(0, 10).map((r, i) => (
                <tr key={i}>
                  <td className="font-mono text-xs">{r.run_id}</td>
                  <td className="text-xs">{new Date(r.created_at).toLocaleDateString()}</td>
                  <td>{fmt(r.total_orders)}</td>
                  <td>{fmt(r.total_units)}</td>
                  <td>{fmtC(r.total_po_value)}</td>
                  <td className="text-green-600 font-semibold">{r.improvements?.stockout_reduction_pct}%</td>
                  <td className="text-blue-600 font-semibold">+{r.improvements?.fill_rate_improvement}%</td>
                  <td><Badge type={r.status}>{r.status}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )}
  </div>
);


/* ================================================================
   ORDERS DASHBOARD TAB (REP-28 to REP-32)
   ================================================================ */
const DashboardTab = ({ data, scheduleData, statusFilter, setStatusFilter, onRefresh,
  selectedOrders, setSelectedOrders, onOrderAction, onBulkAction, onSaveSchedule, onExport }) => {
  const [schedEditing, setSchedEditing] = useState(false);
  const [schedForm, setSchedForm] = useState(scheduleData || {
    enabled: false, frequency: "weekly", day_of_week: 1, lead_time_days: 14, safety_days: 7,
  });

  useEffect(() => {
    if (scheduleData) setSchedForm(scheduleData);
  }, [scheduleData]);

  const counts = data?.counts || { pending: 0, approved: 0, rejected: 0 };
  const orders = data?.orders || [];

  const toggleSelect = (id) => {
    setSelectedOrders(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedOrders.size === orders.length) setSelectedOrders(new Set());
    else setSelectedOrders(new Set(orders.map(o => o.order_id)));
  };

  return (
    <div data-testid="tab-dashboard-content">
      {/* Status Tabs + Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div className="flex gap-2">
          {[
            { val: "", label: "All", count: counts.pending + counts.approved + counts.rejected },
            { val: "pending", label: "Pending", count: counts.pending },
            { val: "approved", label: "Approved", count: counts.approved },
            { val: "rejected", label: "Rejected", count: counts.rejected },
          ].map(f => (
            <button key={f.val} data-testid={`filter-status-${f.val || 'all'}`}
              onClick={() => { setStatusFilter(f.val); setTimeout(onRefresh, 100); }}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition ${
                statusFilter === f.val
                  ? "bg-[#0176D3] text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}>
              {f.label} ({f.count})
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          {selectedOrders.size > 0 && (
            <>
              <button onClick={() => onBulkAction("approve")} className="btn-primary text-xs flex items-center gap-1" data-testid="bulk-approve-btn">
                <CheckCircle size={14} /> Approve ({selectedOrders.size})
              </button>
              <button onClick={() => onBulkAction("reject")} className="bg-red-600 text-white px-3 py-1.5 rounded text-xs flex items-center gap-1 hover:bg-red-700" data-testid="bulk-reject-btn">
                <XCircle size={14} /> Reject ({selectedOrders.size})
              </button>
            </>
          )}
          <button onClick={onExport} className="btn-secondary text-xs flex items-center gap-1" data-testid="export-dashboard-btn">
            <Download size={14} /> Export
          </button>
          <button onClick={onRefresh} className="btn-secondary text-xs flex items-center gap-1" data-testid="refresh-dashboard-btn">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {/* Orders Table (REP-28, REP-29, REP-30) */}
      <div className="bg-white border border-slate-200 rounded shadow-sm mb-6" data-testid="orders-table">
        <div className="p-4 border-b border-slate-100">
          <h3 className="font-semibold text-slate-900">Replenishment Orders</h3>
          <p className="text-xs text-slate-500 mt-1">{orders.length} orders shown</p>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table w-full">
            <thead>
              <tr>
                <th className="w-8">
                  <input type="checkbox" checked={selectedOrders.size === orders.length && orders.length > 0}
                    onChange={toggleAll} data-testid="select-all-orders" />
                </th>
                <th>Order ID</th><th>Run ID</th><th>SKU</th><th>Store</th>
                <th>Qty</th><th>PO Value</th><th>Status</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {orders.slice(0, 50).map((o, i) => (
                <tr key={i}>
                  <td>
                    <input type="checkbox" checked={selectedOrders.has(o.order_id)}
                      onChange={() => toggleSelect(o.order_id)} data-testid={`select-order-${i}`} />
                  </td>
                  <td className="font-mono text-xs">{o.order_id}</td>
                  <td className="font-mono text-xs">{o.run_id}</td>
                  <td>{o.sku}</td>
                  <td>{o.store_code}</td>
                  <td className="font-semibold">{o.order_qty}</td>
                  <td>{fmtC(o.po_value)}</td>
                  <td><Badge type={o.status}>{o.status}</Badge></td>
                  <td>
                    {o.status === "pending" && (
                      <div className="flex gap-1">
                        <button onClick={() => onOrderAction(o.order_id, "approve")}
                          className="text-green-600 hover:text-green-800" data-testid={`approve-order-${i}`}>
                          <CheckCircle size={16} />
                        </button>
                        <button onClick={() => onOrderAction(o.order_id, "reject")}
                          className="text-red-500 hover:text-red-700" data-testid={`reject-order-${i}`}>
                          <XCircle size={16} />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {orders.length === 0 && (
          <div className="p-8 text-center text-slate-400 text-sm">
            No orders found. Run a replenishment to generate orders.
          </div>
        )}
      </div>

      {/* Schedule Config (REP-32) */}
      <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="schedule-config">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Calendar size={16} className="text-[#0176D3]" />
            <h3 className="font-semibold text-slate-900">Auto-Replenishment Schedule</h3>
          </div>
          {!schedEditing && (
            <button onClick={() => setSchedEditing(true)} className="text-xs text-[#0176D3] hover:underline" data-testid="edit-schedule-btn">
              Edit
            </button>
          )}
        </div>
        {schedEditing ? (
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <label className="text-sm text-slate-700">Enabled</label>
              <input type="checkbox" checked={schedForm.enabled}
                onChange={e => setSchedForm(p => ({ ...p, enabled: e.target.checked }))}
                data-testid="schedule-enabled" />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <label className="text-xs font-medium text-slate-600">Frequency</label>
                <select value={schedForm.frequency}
                  onChange={e => setSchedForm(p => ({ ...p, frequency: e.target.value }))}
                  className="input-field mt-1" data-testid="schedule-frequency">
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                </select>
              </div>
              {schedForm.frequency === "weekly" && (
                <div>
                  <label className="text-xs font-medium text-slate-600">Day of Week</label>
                  <select value={schedForm.day_of_week}
                    onChange={e => setSchedForm(p => ({ ...p, day_of_week: Number(e.target.value) }))}
                    className="input-field mt-1" data-testid="schedule-day">
                    {["Mon","Tue","Wed","Thu","Fri","Sat","Sun"].map((d, i) => (
                      <option key={i} value={i}>{d}</option>
                    ))}
                  </select>
                </div>
              )}
              <div>
                <label className="text-xs font-medium text-slate-600">Lead Time</label>
                <input type="number" value={schedForm.lead_time_days}
                  onChange={e => setSchedForm(p => ({ ...p, lead_time_days: Number(e.target.value) }))}
                  className="input-field mt-1" data-testid="schedule-lead-time" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Safety Days</label>
                <input type="number" value={schedForm.safety_days}
                  onChange={e => setSchedForm(p => ({ ...p, safety_days: Number(e.target.value) }))}
                  className="input-field mt-1" data-testid="schedule-safety-days" />
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={() => { onSaveSchedule(schedForm); setSchedEditing(false); }}
                className="btn-primary text-xs flex items-center gap-1" data-testid="save-schedule-btn">
                <CheckCircle size={14} /> Save
              </button>
              <button onClick={() => setSchedEditing(false)} className="btn-secondary text-xs">Cancel</button>
            </div>
          </div>
        ) : (
          <div className="text-sm text-slate-600">
            <p>Status: <b className={schedForm.enabled ? "text-green-600" : "text-slate-400"}>
              {schedForm.enabled ? "Enabled" : "Disabled"}
            </b></p>
            <p>Frequency: <b>{schedForm.frequency}</b>
              {schedForm.frequency === "weekly" && ` (${["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][schedForm.day_of_week || 0]})`}
            </p>
            <p>Lead Time: <b>{schedForm.lead_time_days}d</b> | Safety Days: <b>{schedForm.safety_days}d</b></p>
          </div>
        )}
      </div>
    </div>
  );
};


/* ================================================================
   EMPTY STATE
   ================================================================ */
const EmptyState = () => (
  <div className="bg-slate-50 border border-slate-200 p-12 text-center rounded" data-testid="repl-empty">
    <Package size={40} className="text-slate-300 mx-auto mb-3" />
    <p className="text-slate-500 mb-2">No data available</p>
    <p className="text-sm text-slate-400">Upload the required files to generate a replenishment plan</p>
  </div>
);


export default ReplenishmentPlanner;
