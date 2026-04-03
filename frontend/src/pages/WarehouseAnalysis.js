import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  RefreshCw, Package, Search, AlertTriangle, ArrowDownCircle, ArrowUpCircle,
  TrendingUp, Truck, CheckCircle, XCircle, Clock, BarChart3,
  Download, Filter, Warehouse, Activity, Gauge, ShieldAlert, FileText
} from "lucide-react";
import { BarChart, LineChart, DoughnutChart } from "../components/Charts";

const fmt = (n) => {
  if (!n && n !== 0) return "0";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
};
const currency = (v) => `$${(v / 100000).toFixed(1)}L`;

const WarehouseAnalysis = () => {
  const [activeTab, setActiveTab] = useState("stock");
  const [loading, setLoading] = useState(true);

  // Stock
  const [stockData, setStockData] = useState(null);
  const [whFilter, setWhFilter] = useState("");
  const [catFilter, setCatFilter] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [alertFilter, setAlertFilter] = useState("all");

  // Movements
  const [movements, setMovements] = useState(null);
  const [dailyChange, setDailyChange] = useState(null);
  const [movementDir, setMovementDir] = useState("all");

  // Transfers
  const [transfers, setTransfers] = useState(null);
  const [inTransit, setInTransit] = useState(null);
  const [transferStatus, setTransferStatus] = useState("all");

  // Performance
  const [performance, setPerformance] = useState(null);

  // Dashboard
  const [dashboard, setDashboard] = useState(null);

  // Adjustments & Reconciliation
  const [adjustments, setAdjustments] = useState(null);
  const [reconciliations, setReconciliations] = useState(null);

  const fetchStock = useCallback(async () => {
    try {
      const params = {};
      if (whFilter) params.warehouse = whFilter;
      if (catFilter) params.category = catFilter;
      if (searchTerm) params.search = searchTerm;
      if (alertFilter !== "all") params.alert_type = alertFilter;
      const res = await axios.get(`${API}/analytics/warehouse/stock`, { params });
      setStockData(res.data);
    } catch (err) { console.error(err); }
  }, [whFilter, catFilter, searchTerm, alertFilter]);

  const fetchTab = useCallback(async (tab) => {
    setLoading(true);
    try {
      if (tab === "stock") {
        await fetchStock();
      } else if (tab === "movements") {
        const [mv, dc, adj, rec] = await Promise.all([
          axios.get(`${API}/analytics/warehouse/movements`, { params: { direction: movementDir } }),
          axios.get(`${API}/analytics/warehouse/daily-change`),
          axios.get(`${API}/analytics/warehouse/adjustments`),
          axios.get(`${API}/analytics/warehouse/reconciliation`),
        ]);
        setMovements(mv.data);
        setDailyChange(dc.data);
        setAdjustments(adj.data);
        setReconciliations(rec.data);
      } else if (tab === "transfers") {
        const [tr, it] = await Promise.all([
          axios.get(`${API}/analytics/warehouse/transfers`, { params: { status: transferStatus } }),
          axios.get(`${API}/analytics/warehouse/transfers/in-transit`),
        ]);
        setTransfers(tr.data);
        setInTransit(it.data);
      } else if (tab === "performance") {
        const res = await axios.get(`${API}/analytics/warehouse/performance`);
        setPerformance(res.data);
      } else if (tab === "dashboard") {
        const res = await axios.get(`${API}/analytics/warehouse/dashboard`);
        setDashboard(res.data);
      }
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, [fetchStock, movementDir, transferStatus]);

  useEffect(() => { fetchTab(activeTab); }, [activeTab, fetchTab]);
  useEffect(() => { if (activeTab === "stock") fetchStock(); }, [whFilter, catFilter, searchTerm, alertFilter, fetchStock, activeTab]);

  const handleSeedDemo = async () => {
    await axios.post(`${API}/analytics/warehouse/seed-demo`);
    fetchTab(activeTab);
  };

  const exportCSV = () => {
    if (!stockData?.items?.length) return;
    const headers = ["SKU", "Style", "Size", "Warehouse", "Quantity", "MRP", "Stock Value", "Alert", "Category"];
    const rows = stockData.items.map(i => [i.sku, i.style || "", i.size || "", i.warehouse, i.quantity, i.mrp || 0, i.stock_value || 0, i.alert, i.category || ""]);
    const csv = [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `warehouse_stock_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
  };

  const alertBadge = (a) => ({
    low_stock: "bg-amber-50 text-amber-700",
    out_of_stock: "bg-red-50 text-red-700",
    overstock: "bg-purple-50 text-purple-700",
    normal: "bg-green-50 text-green-700",
  }[a] || "bg-slate-50 text-slate-600");

  const transferBadge = (s) => ({
    pending: "bg-slate-100 text-slate-600",
    allocated: "bg-blue-50 text-blue-700",
    approved: "bg-indigo-50 text-indigo-700",
    in_transit: "bg-amber-50 text-amber-700",
    received: "bg-green-50 text-green-700",
  }[s] || "bg-slate-50 text-slate-600");

  const tabs = [
    { key: "dashboard", label: "Dashboard", icon: BarChart3 },
    { key: "stock", label: "Stock", icon: Package },
    { key: "movements", label: "Movements", icon: Activity },
    { key: "transfers", label: "Transfers", icon: Truck },
    { key: "performance", label: "Performance", icon: Gauge },
  ];

  return (
    <div className="animate-fade-in-up" data-testid="warehouse-page">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-1">Warehouse Management</h1>
          <p className="text-slate-500">Stock levels, movements, transfers, and performance analytics</p>
        </div>
        <div className="flex items-center gap-2">
          <button data-testid="seed-wh-demo-btn" onClick={handleSeedDemo} className="btn-secondary text-xs flex items-center gap-1.5">
            <RefreshCw size={13} /> Seed Demo
          </button>
          <button data-testid="refresh-wh-btn" onClick={() => fetchTab(activeTab)} disabled={loading} className="btn-secondary text-xs flex items-center gap-1.5">
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
          {activeTab === "stock" && (
            <button data-testid="export-csv-btn" onClick={exportCSV} className="btn-primary text-xs flex items-center gap-1.5">
              <Download size={13} /> Export CSV
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs mb-6">
        {tabs.map(t => (
          <button key={t.key} data-testid={`wh-tab-${t.key}`}
            className={`tab ${activeTab === t.key ? "active" : ""}`}
            onClick={() => setActiveTab(t.key)}>
            <t.icon size={14} className="mr-1.5 inline" />{t.label}
          </button>
        ))}
      </div>

      {loading && !stockData && !dashboard && (
        <div className="flex items-center justify-center py-20"><div className="spinner" /></div>
      )}

      {/* ═══════ DASHBOARD TAB ═══════ */}
      {activeTab === "dashboard" && dashboard && (
        <div data-testid="wh-dashboard-tab">
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
            <div className="metric-card" data-testid="kpi-total-stock">
              <span className="metric-label">Total Stock</span>
              <span className="metric-value">{fmt(dashboard.kpis?.total_stock)}</span>
            </div>
            <div className="metric-card" data-testid="kpi-stock-value">
              <span className="metric-label">Stock Value</span>
              <span className="metric-value">{currency(dashboard.kpis?.total_value || 0)}</span>
            </div>
            <div className="metric-card" data-testid="kpi-total-skus">
              <span className="metric-label">Active SKUs</span>
              <span className="metric-value">{fmt(dashboard.kpis?.total_skus)}</span>
            </div>
            <div className="metric-card" data-testid="kpi-warehouses">
              <span className="metric-label">Warehouses</span>
              <span className="metric-value">{dashboard.kpis?.total_warehouses}</span>
            </div>
            <div className="metric-card" data-testid="kpi-snapshot-date">
              <span className="metric-label">Snapshot Date</span>
              <span className="metric-value text-base">{dashboard.kpis?.snapshot_date}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Category Chart WH-27 */}
            {dashboard.category_chart?.length > 0 && (
              <div className="bg-white border border-slate-200 rounded-lg p-5" data-testid="category-chart">
                <h3 className="font-bold text-sm text-slate-900 mb-4">Stock by Category</h3>
                <BarChart
                  labels={dashboard.category_chart.map(c => c.category || "Unknown")}
                  datasets={[{ label: "Quantity", data: dashboard.category_chart.map(c => c.total_qty), color: "#0176D3" }]}
                  height={280} formatValue={fmt} showLegend={false} />
              </div>
            )}

            {/* Movement Trend WH-28 */}
            {dashboard.movement_trend?.length > 0 && (
              <div className="bg-white border border-slate-200 rounded-lg p-5" data-testid="movement-trend-chart">
                <h3 className="font-bold text-sm text-slate-900 mb-4">Stock Movement Trend</h3>
                <LineChart
                  labels={dashboard.movement_trend.map(d => d.date)}
                  datasets={[
                    { label: "Inbound", data: dashboard.movement_trend.map(d => d.inbound), color: "#2E844A" },
                    { label: "Outbound", data: dashboard.movement_trend.map(d => d.outbound), color: "#EA001E" },
                  ]} height={280} />
              </div>
            )}
          </div>

          {/* Multi-warehouse comparison WH-30 */}
          {dashboard.comparison?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg p-5" data-testid="warehouse-comparison">
              <h3 className="font-bold text-sm text-slate-900 mb-4">Multi-Warehouse Comparison</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-50 text-left">
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Warehouse</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Total Stock</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Stock Value</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">SKUs</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Share %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {dashboard.comparison.map((w, i) => {
                      const totalAll = dashboard.comparison.reduce((s, x) => s + x.total_qty, 0);
                      const pct = totalAll > 0 ? ((w.total_qty / totalAll) * 100).toFixed(1) : 0;
                      return (
                        <tr key={i} className="hover:bg-slate-50/50">
                          <td className="px-4 py-2.5 font-medium text-slate-900">{w.warehouse}</td>
                          <td className="px-4 py-2.5">{fmt(w.total_qty)}</td>
                          <td className="px-4 py-2.5">{currency(w.stock_value || 0)}</td>
                          <td className="px-4 py-2.5">{w.sku_count}</td>
                          <td className="px-4 py-2.5">
                            <div className="flex items-center gap-2">
                              <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                <div className="h-full bg-blue-500 rounded-full" style={{ width: `${pct}%` }} />
                              </div>
                              <span className="text-xs">{pct}%</span>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══════ STOCK TAB ═══════ */}
      {activeTab === "stock" && stockData && (
        <div data-testid="wh-stock-tab">
          {/* Alert Summary Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
            <div className="metric-card" data-testid="stock-total">
              <span className="metric-label">Total Stock</span>
              <span className="metric-value">{fmt(stockData.totals?.total_stock)}</span>
            </div>
            <div className="metric-card" data-testid="stock-value">
              <span className="metric-label">Stock Value</span>
              <span className="metric-value">{currency(stockData.totals?.total_value || 0)}</span>
            </div>
            <div className="metric-card cursor-pointer hover:shadow-md transition-shadow" data-testid="stock-low" onClick={() => setAlertFilter(alertFilter === "low_stock" ? "all" : "low_stock")}>
              <span className="metric-label flex items-center gap-1"><AlertTriangle size={12} className="text-amber-500" /> Low Stock</span>
              <span className="metric-value text-amber-600">{stockData.totals?.low_stock}</span>
              <span className="text-[10px] text-slate-400">Below {stockData.totals?.reorder_point} units</span>
            </div>
            <div className="metric-card cursor-pointer hover:shadow-md transition-shadow" data-testid="stock-oos" onClick={() => setAlertFilter(alertFilter === "out_of_stock" ? "all" : "out_of_stock")}>
              <span className="metric-label flex items-center gap-1"><XCircle size={12} className="text-red-500" /> Out of Stock</span>
              <span className="metric-value text-red-600">{stockData.totals?.out_of_stock}</span>
            </div>
            <div className="metric-card cursor-pointer hover:shadow-md transition-shadow" data-testid="stock-overstock" onClick={() => setAlertFilter(alertFilter === "overstock" ? "all" : "overstock")}>
              <span className="metric-label flex items-center gap-1"><ShieldAlert size={12} className="text-purple-500" /> Overstock</span>
              <span className="metric-value text-purple-600">{stockData.totals?.overstock}</span>
              <span className="text-[10px] text-slate-400">Above {stockData.totals?.max_threshold} units</span>
            </div>
          </div>

          {/* Filters */}
          <div className="flex items-end gap-3 flex-wrap mb-4">
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Warehouse</label>
              <select data-testid="wh-filter-warehouse" value={whFilter} onChange={e => setWhFilter(e.target.value)} className="text-xs border border-slate-200 rounded px-2 py-1.5 min-w-[140px]">
                <option value="">All Warehouses</option>
                {stockData.warehouses?.map(w => <option key={w} value={w}>{w}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Category</label>
              <select data-testid="wh-filter-category" value={catFilter} onChange={e => setCatFilter(e.target.value)} className="text-xs border border-slate-200 rounded px-2 py-1.5 min-w-[140px]">
                <option value="">All Categories</option>
                {stockData.categories?.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Search SKU/Style</label>
              <div className="relative">
                <Search size={13} className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-400" />
                <input data-testid="wh-search-input" type="text" value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
                  placeholder="SKU or Style..." className="pl-7 pr-3 py-1.5 text-xs border border-slate-200 rounded w-48" />
              </div>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Alert</label>
              <select data-testid="wh-filter-alert" value={alertFilter} onChange={e => setAlertFilter(e.target.value)} className="text-xs border border-slate-200 rounded px-2 py-1.5">
                <option value="all">All</option>
                <option value="low_stock">Low Stock</option>
                <option value="out_of_stock">Out of Stock</option>
                <option value="overstock">Overstock</option>
                <option value="normal">Normal</option>
              </select>
            </div>
          </div>

          {/* Stock Table */}
          <div data-testid="stock-table" className="bg-white border border-slate-200 rounded-lg overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
              <h3 className="font-bold text-sm text-slate-900">Inventory ({stockData.items?.length} items)</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 text-left">
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">SKU</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Style</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Size</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Warehouse</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Category</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Qty</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">MRP</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Stock Value</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Alert</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {stockData.items?.slice(0, 100).map((item, i) => (
                    <tr key={i} className="hover:bg-slate-50/50">
                      <td className="px-4 py-2 text-xs font-mono">{item.sku}</td>
                      <td className="px-4 py-2 text-xs">{item.style || "-"}</td>
                      <td className="px-4 py-2 text-xs">{item.size || "-"}</td>
                      <td className="px-4 py-2 text-xs">{item.warehouse}</td>
                      <td className="px-4 py-2 text-xs">{item.category || "-"}</td>
                      <td className="px-4 py-2 text-xs font-medium">{item.quantity}</td>
                      <td className="px-4 py-2 text-xs">{item.mrp || "-"}</td>
                      <td className="px-4 py-2 text-xs font-medium">{item.stock_value ? `$${item.stock_value.toLocaleString()}` : "-"}</td>
                      <td className="px-4 py-2">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${alertBadge(item.alert)}`}>
                          {item.alert?.replace("_", " ")}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {(!stockData.items || stockData.items.length === 0) && (
                    <tr><td colSpan={9} className="px-4 py-10 text-center text-slate-400">No items match filters</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ═══════ MOVEMENTS TAB ═══════ */}
      {activeTab === "movements" && (
        <div data-testid="wh-movements-tab">
          {/* Summary */}
          {movements?.summary && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="metric-card" data-testid="mv-inbound-qty">
                <span className="metric-label flex items-center gap-1"><ArrowDownCircle size={12} className="text-green-500" /> Inbound Qty</span>
                <span className="metric-value text-green-600">{fmt(movements.summary.total_inbound)}</span>
              </div>
              <div className="metric-card" data-testid="mv-outbound-qty">
                <span className="metric-label flex items-center gap-1"><ArrowUpCircle size={12} className="text-blue-500" /> Outbound Qty</span>
                <span className="metric-value text-blue-600">{fmt(movements.summary.total_outbound)}</span>
              </div>
              <div className="metric-card" data-testid="mv-inbound-count">
                <span className="metric-label">Inbound Transactions</span>
                <span className="metric-value">{movements.summary.inbound_count}</span>
              </div>
              <div className="metric-card" data-testid="mv-outbound-count">
                <span className="metric-label">Outbound Transactions</span>
                <span className="metric-value">{movements.summary.outbound_count}</span>
              </div>
            </div>
          )}

          {/* Direction Filter */}
          <div className="flex items-center gap-3 mb-4">
            <label className="text-xs font-medium text-slate-600">Direction:</label>
            <select data-testid="mv-direction-filter" value={movementDir} onChange={e => { setMovementDir(e.target.value); }} className="text-xs border border-slate-200 rounded px-2 py-1.5">
              <option value="all">All</option>
              <option value="inbound">Inbound</option>
              <option value="outbound">Outbound</option>
            </select>
          </div>

          {/* Movements Timeline */}
          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden mb-6" data-testid="movements-table">
            <div className="px-5 py-4 border-b border-slate-100">
              <h3 className="font-bold text-sm text-slate-900">Stock Movement History ({movements?.movements?.length || 0})</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 text-left">
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Time</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Direction</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Warehouse</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">SKU</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Qty</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Reference</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Source/Dest</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {movements?.movements?.slice(0, 100).map((m, i) => (
                    <tr key={i} className="hover:bg-slate-50/50">
                      <td className="px-4 py-2 text-xs text-slate-500">{m.timestamp ? new Date(m.timestamp).toLocaleString() : "-"}</td>
                      <td className="px-4 py-2">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${m.direction === "inbound" ? "bg-green-50 text-green-700" : "bg-blue-50 text-blue-700"}`}>
                          {m.direction === "inbound" ? <ArrowDownCircle size={10} /> : <ArrowUpCircle size={10} />}{m.direction}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-xs">{m.warehouse}</td>
                      <td className="px-4 py-2 text-xs font-mono">{m.sku}</td>
                      <td className="px-4 py-2 text-xs font-medium">{m.quantity}</td>
                      <td className="px-4 py-2 text-xs text-slate-500">{m.reference}</td>
                      <td className="px-4 py-2 text-xs">{m.source || m.destination || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Daily Change WH-12 */}
          {dailyChange?.days?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg p-5 mb-6" data-testid="daily-change">
              <h3 className="font-bold text-sm text-slate-900 mb-4">Daily Stock Change (Opening vs Closing)</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-50 text-left">
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Date</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Opening Stock</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Closing Stock</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Change</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {dailyChange.days.map((d, i) => (
                      <tr key={i}>
                        <td className="px-4 py-2 text-xs">{d.date}</td>
                        <td className="px-4 py-2 text-xs">{fmt(d.opening_stock)}</td>
                        <td className="px-4 py-2 text-xs">{fmt(d.closing_stock)}</td>
                        <td className={`px-4 py-2 text-xs font-medium ${d.change >= 0 ? "text-green-600" : "text-red-600"}`}>{d.change >= 0 ? "+" : ""}{fmt(d.change)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Reconciliation WH-13 */}
          {reconciliations?.reconciliations?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg p-5 mb-6" data-testid="reconciliation-table">
              <h3 className="font-bold text-sm text-slate-900 mb-4">Stock Reconciliation (System vs Physical)</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-50 text-left">
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Date</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Warehouse</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">SKU</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">System Qty</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Physical Qty</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Variance</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">By</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {reconciliations.reconciliations.map((r, i) => (
                      <tr key={i}>
                        <td className="px-4 py-2 text-xs">{r.reconciled_at ? new Date(r.reconciled_at).toLocaleDateString() : "-"}</td>
                        <td className="px-4 py-2 text-xs">{r.warehouse}</td>
                        <td className="px-4 py-2 text-xs font-mono">{r.sku}</td>
                        <td className="px-4 py-2 text-xs">{r.system_qty}</td>
                        <td className="px-4 py-2 text-xs">{r.physical_qty}</td>
                        <td className={`px-4 py-2 text-xs font-medium ${r.variance === 0 ? "text-green-600" : "text-red-600"}`}>{r.variance > 0 ? "+" : ""}{r.variance}</td>
                        <td className="px-4 py-2 text-xs text-slate-500">{r.reconciled_by}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Adjustments WH-14 */}
          {adjustments?.adjustments?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg p-5" data-testid="adjustments-table">
              <h3 className="font-bold text-sm text-slate-900 mb-4">Stock Adjustment Log</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-50 text-left">
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Date</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Warehouse</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">SKU</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Previous</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">New</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Change</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Reason</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">By</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {adjustments.adjustments.map((a, i) => (
                      <tr key={i}>
                        <td className="px-4 py-2 text-xs">{a.adjusted_at ? new Date(a.adjusted_at).toLocaleString() : "-"}</td>
                        <td className="px-4 py-2 text-xs">{a.warehouse}</td>
                        <td className="px-4 py-2 text-xs font-mono">{a.sku}</td>
                        <td className="px-4 py-2 text-xs">{a.previous_qty}</td>
                        <td className="px-4 py-2 text-xs">{a.new_qty}</td>
                        <td className={`px-4 py-2 text-xs font-medium ${a.change >= 0 ? "text-green-600" : "text-red-600"}`}>{a.change > 0 ? "+" : ""}{a.change}</td>
                        <td className="px-4 py-2 text-xs text-slate-500">{a.reason}</td>
                        <td className="px-4 py-2 text-xs text-slate-500">{a.adjusted_by}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══════ TRANSFERS TAB ═══════ */}
      {activeTab === "transfers" && (
        <div data-testid="wh-transfers-tab">
          {/* In-transit KPI */}
          {inTransit && (
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              <div className="metric-card" data-testid="transit-count">
                <span className="metric-label flex items-center gap-1"><Truck size={12} className="text-amber-500" /> In Transit</span>
                <span className="metric-value text-amber-600">{inTransit.transfers?.length || 0}</span>
              </div>
              <div className="metric-card" data-testid="transit-qty">
                <span className="metric-label">In-Transit Quantity</span>
                <span className="metric-value">{fmt(inTransit.total_in_transit)}</span>
              </div>
              <div className="metric-card" data-testid="total-transfers">
                <span className="metric-label">Total Transfer Orders</span>
                <span className="metric-value">{transfers?.transfers?.length || 0}</span>
              </div>
            </div>
          )}

          {/* Status Filter */}
          <div className="flex items-center gap-3 mb-4">
            <label className="text-xs font-medium text-slate-600">Status:</label>
            <select data-testid="transfer-status-filter" value={transferStatus} onChange={e => setTransferStatus(e.target.value)} className="text-xs border border-slate-200 rounded px-2 py-1.5">
              <option value="all">All</option>
              <option value="pending">Pending</option>
              <option value="allocated">Allocated</option>
              <option value="approved">Approved</option>
              <option value="in_transit">In Transit</option>
              <option value="received">Received</option>
            </select>
          </div>

          {/* Transfer Table */}
          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden" data-testid="transfers-table">
            <div className="px-5 py-4 border-b border-slate-100">
              <h3 className="font-bold text-sm text-slate-900">Transfer Orders</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 text-left">
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">ID</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">From</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">To Store</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Items</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Total Qty</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Status</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Created</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Dispatched</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Received</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {transfers?.transfers?.map((t, i) => (
                    <tr key={i} className="hover:bg-slate-50/50">
                      <td className="px-4 py-2 text-xs font-mono">{t.transfer_id}</td>
                      <td className="px-4 py-2 text-xs">{t.from_warehouse}</td>
                      <td className="px-4 py-2 text-xs">{t.to_store}</td>
                      <td className="px-4 py-2 text-xs">{t.items?.length || 0}</td>
                      <td className="px-4 py-2 text-xs font-medium">{t.total_qty}</td>
                      <td className="px-4 py-2">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${transferBadge(t.status)}`}>
                          {t.status?.replace("_", " ")}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-xs text-slate-500">{t.created_at ? new Date(t.created_at).toLocaleDateString() : "-"}</td>
                      <td className="px-4 py-2 text-xs text-slate-500">{t.dispatched_at ? new Date(t.dispatched_at).toLocaleDateString() : "-"}</td>
                      <td className="px-4 py-2 text-xs text-slate-500">{t.received_at ? new Date(t.received_at).toLocaleDateString() : "-"}</td>
                    </tr>
                  ))}
                  {(!transfers?.transfers || transfers.transfers.length === 0) && (
                    <tr><td colSpan={9} className="px-4 py-10 text-center text-slate-400">No transfers found</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ═══════ PERFORMANCE TAB ═══════ */}
      {activeTab === "performance" && performance && (
        <div data-testid="wh-performance-tab">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="metric-card" data-testid="perf-fulfillment">
              <span className="metric-label">Order Fulfillment Rate</span>
              <span className="metric-value">{performance.fulfillment_rate}%</span>
            </div>
            <div className="metric-card" data-testid="perf-dispatch">
              <span className="metric-label">Avg Dispatch Time</span>
              <span className="metric-value">{performance.avg_dispatch_hours}h</span>
            </div>
            <div className="metric-card" data-testid="perf-turnover">
              <span className="metric-label">Warehouse Turnover</span>
              <span className="metric-value">{performance.turnover_ratio}</span>
            </div>
            <div className="metric-card" data-testid="perf-utilization">
              <span className="metric-label">Storage Utilization</span>
              <span className="metric-value">{performance.utilization_pct}%</span>
            </div>
          </div>

          {/* Warehouse Utilization */}
          {performance.by_warehouse?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg p-5 mb-6" data-testid="utilization-table">
              <h3 className="font-bold text-sm text-slate-900 mb-4">Storage Utilization by Warehouse</h3>
              <div className="space-y-3">
                {performance.by_warehouse.map((w, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-sm font-medium text-slate-900 w-24">{w.warehouse}</span>
                    <div className="flex-1 h-3 bg-slate-100 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full transition-all ${w.utilization_pct > 90 ? "bg-red-500" : w.utilization_pct > 70 ? "bg-amber-500" : "bg-green-500"}`}
                        style={{ width: `${Math.min(w.utilization_pct, 100)}%` }} />
                    </div>
                    <span className="text-xs text-slate-600 w-20 text-right">{w.utilization_pct}%</span>
                    <span className="text-[10px] text-slate-400 w-32 text-right">{fmt(w.current_stock)} / {fmt(w.capacity)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Slow-Moving Stock */}
          {performance.slow_moving?.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg overflow-hidden" data-testid="slow-moving-table">
              <div className="px-5 py-4 border-b border-slate-100">
                <h3 className="font-bold text-sm text-slate-900">Slow-Moving Stock ({performance.slow_moving_count || performance.slow_moving.length} SKUs — no sales for 90+ days)</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-50 text-left">
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">SKU</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Style</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Size</th>
                      <th className="px-4 py-2.5 text-xs font-semibold uppercase text-slate-500">Stock Qty</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {performance.slow_moving.slice(0, 30).map((s, i) => (
                      <tr key={i}>
                        <td className="px-4 py-2 text-xs font-mono">{s.sku}</td>
                        <td className="px-4 py-2 text-xs">{s.style || "-"}</td>
                        <td className="px-4 py-2 text-xs">{s.size || "-"}</td>
                        <td className="px-4 py-2 text-xs font-medium">{s.total_qty}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WarehouseAnalysis;
