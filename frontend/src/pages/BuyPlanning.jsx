import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import { toast } from "sonner";
import {
  BarChart3, RefreshCw, Zap, Store, Tag, Grid3X3, Download, Edit2, Settings, RotateCcw, Save,
  Search, TrendingUp, TrendingDown, CheckCircle2, Eye, Crown, Star, MapPin, ClipboardList,
  Ban, Plus, X, Send, History, Upload, Package, Calendar, Truck,
} from "lucide-react";

function WedgeBadge({ wedge }) {
  const s = { A: "bg-emerald-100 text-emerald-800", B: "bg-blue-100 text-blue-800", C: "bg-gray-100 text-gray-600" };
  return <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${s[wedge] || s.C}`}>{wedge || "—"}</span>;
}

function MixBadge({ mix }) {
  const s = { Core: "bg-emerald-100 text-emerald-800", Fashion: "bg-purple-100 text-purple-800", Test: "bg-amber-100 text-amber-800" };
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${s[mix] || "bg-gray-100 text-gray-600"}`}>{mix || "—"}</span>;
}

function StatCard({ label, value, sub, icon: Icon, color = "blue" }) {
  const c = { blue: "bg-blue-50 text-blue-600", emerald: "bg-emerald-50 text-emerald-600", purple: "bg-purple-50 text-purple-600", amber: "bg-amber-50 text-amber-600", gray: "bg-gray-50 text-gray-600" };
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${c[color]}`}><Icon className="h-5 w-5" /></div>
        <div>
          <div className="text-2xl font-bold text-gray-900">{value}</div>
          <div className="text-xs text-gray-500">{label}</div>
          {sub && <div className="text-[10px] text-gray-400">{sub}</div>}
        </div>
      </div>
    </div>
  );
}

export default function BuyPlanning() {
  const [wedge, setWedge] = useState(null);
  const [mix, setMix] = useState(null);
  const [matrix, setMatrix] = useState(null);
  const [buyPlan, setBuyPlan] = useState(null);
  const [dnaTags, setDnaTags] = useState(null);
  const [attribution, setAttribution] = useState(null);
  const [displayMins, setDisplayMins] = useState([]);
  const [sellThroughConfigs, setSellThroughConfigs] = useState([]);
  const [editingMultipliers, setEditingMultipliers] = useState({});
  const [storeSearch, setStoreSearch] = useState("");
  const [storeWedgeFilter, setStoreWedgeFilter] = useState("all");
  const [styleSearch, setStyleSearch] = useState("");
  const [selectedAttr, setSelectedAttr] = useState(null);
  const [loading, setLoading] = useState({});
  const [tab, setTab] = useState("overview");
  const [overrideModal, setOverrideModal] = useState(null);
  const [overrideValue, setOverrideValue] = useState("");
  const [overrideReason, setOverrideReason] = useState("");
  const [savedPlans, setSavedPlans] = useState([]);
  const [selectedPlanId, setSelectedPlanId] = useState("");
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [planItems, setPlanItems] = useState([]);
  const [editingItemIdx, setEditingItemIdx] = useState(null);
  const [editingQty, setEditingQty] = useState("");
  const [detailItem, setDetailItem] = useState(null);
  const [planCoverDays, setPlanCoverDays] = useState(30);
  const [auditLog, setAuditLog] = useState([]);
  const [auditFilter, setAuditFilter] = useState({ entity_type: "", source: "" });
  const [regionFilter, setRegionFilter] = useState("all");
  const [tierFilter, setTierFilter] = useState("all");
  const [formatFilter, setFormatFilter] = useState("all");
  const [exclusions, setExclusions] = useState([]);
  const [exclusionModal, setExclusionModal] = useState(false);
  const [newExclusion, setNewExclusion] = useState({ store_code: "", sku: "", reason: "" });
  const [storeEditModal, setStoreEditModal] = useState(null);
  const [approvalComment, setApprovalComment] = useState("");
  const [approvalHistory, setApprovalHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [inventorySummary, setInventorySummary] = useState(null);
  const [inventoryRecords, setInventoryRecords] = useState([]);
  const [syncStatus, setSyncStatus] = useState(null);
  const [safetyConfig, setSafetyConfig] = useState(null);
  const [editingSafetyConfig, setEditingSafetyConfig] = useState(null);
  const [orders, setOrders] = useState([]);
  const [phasedPos, setPhasedPos] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [phaseModal, setPhaseModal] = useState(null);
  const [phaseWeeks, setPhaseWeeks] = useState("0,2,4");
  const [phasePcts, setPhasePcts] = useState("50,30,20");
  const [promotions, setPromotions] = useState([]);
  const [promoModal, setPromoModal] = useState(false);
  const [newPromo, setNewPromo] = useState({ name: "", promo_type: "national", start_date: "", end_date: "", discount_type: "percentage", discount_value: 0, affected_categories: "", lift_factor: 1.3, notes: "" });

  const fetchAll = useCallback(async () => {
    try {
      const [w, m, mx] = await Promise.all([
        axios.get(`${API}/buy-planning/store-wedge`).catch(() => ({ data: { stores: [], summary: { A: 0, B: 0, C: 0 }, classified: false } })),
        axios.get(`${API}/buy-planning/style-mix`).catch(() => ({ data: { styles: [], summary: { Core: 0, Fashion: 0, Test: 0 }, classified: false } })),
        axios.get(`${API}/buy-planning/assortment-matrix`).catch(() => ({ data: { matrix: {} } })),
      ]);
      setWedge(w.data);
      setMix(m.data);
      setMatrix(mx.data);
      // Fetch Phase 2+3 data
      const [bp, dna, attr, dm, stc, plansRes] = await Promise.all([
        axios.post(`${API}/buy-planning/buy-formula/calculate`, { cover_days: 30, safety_days: 7 }).catch(() => ({ data: null })),
        axios.get(`${API}/buy-planning/dna-tags`).catch(() => ({ data: { styles: [] } })),
        axios.get(`${API}/buy-planning/attribution/matrix`).catch(() => ({ data: { attributions: [] } })),
        axios.get(`${API}/buy-planning/display-minimums`).catch(() => ({ data: { configs: [] } })),
        axios.get(`${API}/buy-planning/sell-through-config`).catch(() => ({ data: { configs: [] } })),
        axios.get(`${API}/buy-planning/buy-plans`).catch(() => ({ data: { plans: [] } })),
      ]);
      setBuyPlan(bp.data);
      setDnaTags(dna.data);
      setAttribution(attr.data);
      setDisplayMins(dm.data?.configs || []);
      setSellThroughConfigs(stc.data?.configs || []);
      setSavedPlans(plansRes.data?.plans || []);
      setEditingMultipliers({});
      // Fetch audit log
      const auditRes = await axios.get(`${API}/buy-planning/audit-log`).catch(() => ({ data: { entries: [] } }));
      setAuditLog(auditRes.data?.entries || []);
      // Fetch exclusions
      const exclRes = await axios.get(`${API}/buy-planning/exclusions`).catch(() => ({ data: { exclusions: [] } }));
      setExclusions(exclRes.data?.exclusions || []);
      // Fetch inventory & safety config
      const [invSum, invSync, safeRes] = await Promise.all([
        axios.get(`${API}/buy-planning/inventory/summary`).catch(() => ({ data: null })),
        axios.get(`${API}/buy-planning/inventory/sync-status`).catch(() => ({ data: { last_sync: null } })),
        axios.get(`${API}/buy-planning/safety-stock/config`).catch(() => ({ data: null })),
      ]);
      setInventorySummary(invSum.data);
      setSyncStatus(invSync.data?.last_sync);
      setSafetyConfig(safeRes.data);
      // Fetch orders & promotions
      const [ordRes, promRes] = await Promise.all([
        axios.get(`${API}/buy-planning/orders`).catch(() => ({ data: { orders: [] } })),
        axios.get(`${API}/buy-planning/promotions`).catch(() => ({ data: { promotions: [] } })),
      ]);
      setOrders(ordRes.data?.orders || []);
      setPromotions(promRes.data?.promotions || []);
    } catch {}
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const runClassification = async (type) => {
    setLoading(prev => ({ ...prev, [type]: true }));
    try {
      const res = await axios.post(`${API}/buy-planning/${type}/classify`);
      toast.success(`${type === "store-wedge" ? "Store Wedge" : "Style Mix"} classification complete`);
      fetchAll();
    } catch (e) {
      toast.error(e.response?.data?.detail || `Failed to classify ${type}`);
    }
    setLoading(prev => ({ ...prev, [type]: false }));
  };

  const submitOverride = async () => {
    if (!overrideModal || !overrideValue) return;
    try {
      if (overrideModal.type === "store") {
        await axios.post(`${API}/buy-planning/overrides/store-wedge`, {
          store_code: overrideModal.id, wedge_class: overrideValue, reason: overrideReason,
        });
      } else {
        await axios.post(`${API}/buy-planning/overrides/style-mix`, {
          style: overrideModal.id, style_mix: overrideValue, reason: overrideReason,
        });
      }
      toast.success("Override applied");
      setOverrideModal(null); setOverrideValue(""); setOverrideReason("");
      fetchAll();
    } catch (e) { toast.error(e.response?.data?.detail || "Override failed"); }
  };

  const exportCSV = async () => {
    try {
      const res = await axios.get(`${API}/buy-planning/buy-formula/export/csv`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a"); a.href = url;
      a.download = `buy_plan_${new Date().toISOString().slice(0, 10)}.csv`;
      a.click(); window.URL.revokeObjectURL(url);
      toast.success("Buy plan exported to CSV");
    } catch { toast.error("Export failed"); }
  };

  const saveSellThrough = async (styleMix) => {
    const val = parseFloat(editingMultipliers[styleMix]);
    if (isNaN(val) || val < 0 || val > 5) { toast.error("Multiplier must be between 0 and 5"); return; }
    try {
      await axios.put(`${API}/buy-planning/sell-through-config`, { style_mix: styleMix, target_multiplier: val });
      toast.success(`${styleMix} multiplier updated to ${val}`);
      setEditingMultipliers(p => { const n = { ...p }; delete n[styleMix]; return n; });
      fetchAll();
    } catch (e) { toast.error(e.response?.data?.detail || "Update failed"); }
  };

  const resetSellThrough = async () => {
    try {
      await axios.post(`${API}/buy-planning/sell-through-config/reset`);
      toast.success("Sell-through targets reset to defaults");
      fetchAll();
    } catch { toast.error("Reset failed"); }
  };

  const generatePlan = async () => {
    setLoading(p => ({ ...p, generate: true }));
    try {
      const res = await axios.post(`${API}/buy-planning/buy-plans/generate`, {
        cover_days: planCoverDays, safety_days: 7,
        plan_name: `Buy Plan ${new Date().toLocaleDateString()} (${planCoverDays}d)`,
      });
      toast.success("Plan generated and saved");
      fetchAll();
      loadPlan(res.data.plan_id);
    } catch (e) { toast.error(e.response?.data?.detail || "Plan generation failed"); }
    setLoading(p => ({ ...p, generate: false }));
  };

  const loadPlan = async (planId) => {
    if (!planId) { setSelectedPlanId(""); setSelectedPlan(null); setPlanItems([]); return; }
    setSelectedPlanId(planId);
    try {
      const res = await axios.get(`${API}/buy-planning/buy-plans/${planId}`);
      setSelectedPlan(res.data);
      setPlanItems(res.data.items || []);
    } catch { toast.error("Failed to load plan"); }
  };

  const updateItemQty = async () => {
    if (editingItemIdx === null || !editingQty) return;
    try {
      await axios.put(`${API}/buy-planning/buy-plans/${selectedPlanId}/items`, {
        item_index: editingItemIdx, new_qty: parseInt(editingQty),
      });
      toast.success("Quantity updated");
      setEditingItemIdx(null); setEditingQty("");
      loadPlan(selectedPlanId);
    } catch (e) { toast.error(e.response?.data?.detail || "Update failed"); }
  };

  const approvePlan = async () => {
    try {
      await axios.post(`${API}/buy-planning/buy-plans/${selectedPlanId}/approve`);
      toast.success("Plan approved");
      loadPlan(selectedPlanId); fetchAll();
    } catch (e) { toast.error(e.response?.data?.detail || "Approval failed"); }
  };

  const deletePlan = async () => {
    try {
      await axios.delete(`${API}/buy-planning/buy-plans/${selectedPlanId}`);
      toast.success("Plan deleted");
      setSelectedPlanId(""); setSelectedPlan(null); setPlanItems([]);
      fetchAll();
    } catch (e) { toast.error(e.response?.data?.detail || "Delete failed"); }
  };

  const fetchExclusions = async () => {
    try {
      const res = await axios.get(`${API}/buy-planning/exclusions`);
      setExclusions(res.data?.exclusions || []);
    } catch {}
  };

  const addExclusion = async () => {
    if (!newExclusion.store_code || !newExclusion.sku) { toast.error("Store and SKU are required"); return; }
    try {
      await axios.post(`${API}/buy-planning/exclusions`, newExclusion);
      toast.success("Exclusion added");
      setNewExclusion({ store_code: "", sku: "", reason: "" });
      fetchExclusions();
    } catch (e) { toast.error(e.response?.data?.detail || "Failed to add exclusion"); }
  };

  const removeExclusion = async (storeCode, sku) => {
    try {
      await axios.delete(`${API}/buy-planning/exclusions/${storeCode}/${sku}`);
      toast.success("Exclusion removed");
      fetchExclusions();
    } catch (e) { toast.error(e.response?.data?.detail || "Failed to remove"); }
  };

  const updateStoreAttrs = async (storeCode, attrs) => {
    try {
      await axios.put(`${API}/buy-planning/stores/${storeCode}/attributes`, attrs);
      toast.success("Store attributes updated");
      setStoreEditModal(null);
      fetchAll();
    } catch (e) { toast.error(e.response?.data?.detail || "Update failed"); }
  };

  const processApproval = async (action) => {
    if ((action === "reject" || action === "request_changes") && !approvalComment) {
      toast.error("Comment is required for reject/request changes");
      return;
    }
    try {
      await axios.post(`${API}/buy-planning/buy-plans/${selectedPlanId}/approval`, {
        action, comment: approvalComment || undefined,
      });
      toast.success(`Plan ${action.replace(/_/g, " ")} successfully`);
      setApprovalComment("");
      loadPlan(selectedPlanId);
      fetchAll();
    } catch (e) { toast.error(e.response?.data?.detail || "Action failed"); }
  };

  const loadApprovalHistory = async (planId) => {
    try {
      const res = await axios.get(`${API}/buy-planning/buy-plans/${planId}/approval-history`);
      setApprovalHistory(res.data?.history || []);
      setShowHistory(true);
    } catch { toast.error("Failed to load history"); }
  };

  const PLAN_STAGES = [
    { key: "draft", label: "Draft" },
    { key: "submitted", label: "Submitted" },
    { key: "category_approved", label: "Category" },
    { key: "senior_approved", label: "Senior" },
    { key: "head_approved", label: "Head" },
    { key: "ordered", label: "Ordered" },
  ];

  const getAvailableActions = (status) => {
    const map = {
      draft: [{ action: "submit", label: "Submit for Approval", color: "bg-blue-600 hover:bg-blue-700" }],
      submitted: [
        { action: "approve_category", label: "Approve (Category)", color: "bg-emerald-600 hover:bg-emerald-700" },
        { action: "request_changes", label: "Request Changes", color: "bg-amber-600 hover:bg-amber-700" },
        { action: "reject", label: "Reject", color: "bg-red-600 hover:bg-red-700" },
      ],
      category_approved: [
        { action: "approve_senior", label: "Approve (Senior)", color: "bg-emerald-600 hover:bg-emerald-700" },
        { action: "request_changes", label: "Request Changes", color: "bg-amber-600 hover:bg-amber-700" },
        { action: "reject", label: "Reject", color: "bg-red-600 hover:bg-red-700" },
      ],
      senior_approved: [
        { action: "approve_head", label: "Final Approve (Head)", color: "bg-purple-600 hover:bg-purple-700" },
        { action: "reject", label: "Reject", color: "bg-red-600 hover:bg-red-700" },
      ],
      head_approved: [
        { action: "finance_ack", label: "Acknowledge & Order", color: "bg-[#0B2545] hover:bg-[#13315C]" },
      ],
    };
    return map[status] || [];
  };

  const handleInventoryUpload = async (file) => {
    if (!file) return;
    setLoading(p => ({ ...p, inventory: true }));
    try {
      const text = await file.text();
      const lines = text.trim().split("\n");
      const headers = lines[0].split(",").map(h => h.trim().toLowerCase());
      const records = lines.slice(1).filter(l => l.trim()).map(line => {
        const vals = line.split(",").map(v => v.trim());
        const obj = {};
        headers.forEach((h, i) => { obj[h] = vals[i] || ""; });
        return {
          store_code: obj.store_code || obj.store_id || "",
          sku: obj.sku || obj.sku_id || "",
          date: obj.date || new Date().toISOString().split("T")[0],
          soh: parseInt(obj.soh) || 0,
          in_transit: parseInt(obj.in_transit) || 0,
          open_po_qty: parseInt(obj.open_po_qty) || 0,
        };
      }).filter(r => r.store_code && r.sku);
      const res = await axios.post(`${API}/buy-planning/inventory/bulk`, { records, source: "csv" });
      toast.success(`Uploaded: ${res.data.inserted} new, ${res.data.updated} updated`);
      fetchAll();
    } catch (e) { toast.error(e.response?.data?.detail || "Upload failed"); }
    setLoading(p => ({ ...p, inventory: false }));
  };

  const saveSafetyConfig = async () => {
    if (!editingSafetyConfig) return;
    try {
      await axios.put(`${API}/buy-planning/safety-stock/config`, editingSafetyConfig);
      toast.success("Safety stock config saved");
      setEditingSafetyConfig(null);
      fetchAll();
    } catch (e) { toast.error(e.response?.data?.detail || "Save failed"); }
  };

  const resetSafetyConfig = async () => {
    try {
      await axios.post(`${API}/buy-planning/safety-stock/config/reset`);
      toast.success("Reset to defaults");
      fetchAll();
    } catch { toast.error("Reset failed"); }
  };

  const SL_OPTIONS = [
    { val: 0.80, label: "80% - Low stock, low cost" },
    { val: 0.90, label: "90% - Moderate" },
    { val: 0.95, label: "95% - Standard (Recommended)" },
    { val: 0.98, label: "98% - High availability" },
    { val: 0.99, label: "99% - Critical items" },
  ];

  const consolidateOrders = async (planId) => {
    try {
      const res = await axios.post(`${API}/buy-planning/orders/consolidate`, { plan_id: planId });
      toast.success(`Created ${res.data.pos_created} consolidated POs`);
      fetchAll();
    } catch (e) { toast.error(e.response?.data?.detail || "Consolidation failed"); }
  };

  const updatePOStatus = async (poNumber, status) => {
    try {
      await axios.put(`${API}/buy-planning/orders/${poNumber}/status`, { status });
      toast.success(`PO ${poNumber} → ${status}`);
      fetchAll();
    } catch (e) { toast.error(e.response?.data?.detail || "Update failed"); }
  };

  const createPhasedPO = async () => {
    if (!phaseModal) return;
    try {
      const weeks = phaseWeeks.split(",").map(Number);
      const pcts = phasePcts.split(",").map(Number);
      await axios.post(`${API}/buy-planning/orders/phase`, { po_number: phaseModal, phase_weeks: weeks, phase_percentages: pcts });
      toast.success("Phased PO created");
      setPhaseModal(null);
      fetchAll();
    } catch (e) { toast.error(e.response?.data?.detail || "Phase creation failed"); }
  };

  const createPromotion = async () => {
    try {
      await axios.post(`${API}/buy-planning/promotions`, {
        ...newPromo, affected_categories: newPromo.affected_categories ? newPromo.affected_categories.split(",").map(s => s.trim()) : [],
      });
      toast.success("Promotion created");
      setPromoModal(false);
      setNewPromo({ name: "", promo_type: "national", start_date: "", end_date: "", discount_type: "percentage", discount_value: 0, affected_categories: "", lift_factor: 1.3, notes: "" });
      fetchAll();
    } catch (e) { toast.error(e.response?.data?.detail || "Failed to create promotion"); }
  };

  const deletePromotion = async (promoId) => {
    try {
      await axios.delete(`${API}/buy-planning/promotions/${promoId}`);
      toast.success("Promotion deleted");
      fetchAll();
    } catch (e) { toast.error(e.response?.data?.detail || "Delete failed"); }
  };

  const wedgeSummary = wedge?.summary || { A: 0, B: 0, C: 0 };
  const mixSummary = mix?.summary || { Core: 0, Fashion: 0, Test: 0 };
  const totalStyles = mixSummary.Core + mixSummary.Fashion + mixSummary.Test;

  const filteredStores = (wedge?.stores || []).filter(s => {
    if (storeWedgeFilter !== "all" && s.wedge_class !== storeWedgeFilter) return false;
    if (regionFilter !== "all" && s.region !== regionFilter) return false;
    if (tierFilter !== "all" && s.city_tier !== tierFilter) return false;
    if (formatFilter !== "all" && s.store_format !== formatFilter) return false;
    if (!storeSearch) return true;
    const term = storeSearch.toLowerCase();
    return (s.store_code || "").toLowerCase().includes(term) || (s.store_name || "").toLowerCase().includes(term) || (s.city || "").toLowerCase().includes(term);
  });

  const filteredStyles = (mix?.styles || []).filter(s => {
    if (!styleSearch) return true;
    return (s.style || "").toLowerCase().includes(styleSearch.toLowerCase());
  });

  const DEFAULTS = { Core: 1.2, Fashion: 0.8, Test: 0.4 };

  return (
    <div data-testid="buy-planning-page" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 data-testid="page-title" className="text-2xl font-bold text-gray-900">Buy Planning</h1>
          <p className="text-sm text-gray-500 mt-1">Store Wedge Classification + Style Mix Tagging</p>
        </div>
        <div className="flex gap-2">
          <button data-testid="export-csv-btn" onClick={exportCSV}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">
            <Download className="h-4 w-4" /> Export CSV
          </button>
          <button onClick={fetchAll} className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50">
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <StatCard icon={Store} label="A-Stores" value={wedgeSummary.A} sub="Full assortment" color="emerald" />
        <StatCard icon={Store} label="B-Stores" value={wedgeSummary.B} sub="Standard" color="blue" />
        <StatCard icon={Store} label="C-Stores" value={wedgeSummary.C} sub="Core only" color="gray" />
        <StatCard icon={Tag} label="Core Styles" value={mixSummary.Core} sub=">5 units/wk, >80% presence" color="emerald" />
        <StatCard icon={Tag} label="Fashion" value={mixSummary.Fashion} sub="Peak/avg >3x" color="purple" />
        <StatCard icon={Tag} label="Test" value={mixSummary.Test} sub="<8 weeks or <2/wk" color="amber" />
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-3">
        <button
          data-testid="classify-wedge-btn"
          onClick={() => runClassification("store-wedge")}
          disabled={loading["store-wedge"]}
          className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C] disabled:opacity-50"
        >
          <Zap className="h-4 w-4" />
          {loading["store-wedge"] ? "Classifying..." : "Run Store Wedge Classification"}
        </button>
        <button
          data-testid="classify-mix-btn"
          onClick={() => runClassification("style-mix")}
          disabled={loading["style-mix"]}
          className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
        >
          <Tag className="h-4 w-4" />
          {loading["style-mix"] ? "Classifying..." : "Run Style Mix Classification"}
        </button>
        <button
          data-testid="auto-dna-btn"
          onClick={async () => {
            setLoading(p => ({ ...p, dna: true }));
            try { await axios.post(`${API}/buy-planning/dna-tag/auto`); toast.success("DNA tagging complete"); fetchAll(); }
            catch (e) { toast.error(e.response?.data?.detail || "DNA tagging failed"); }
            setLoading(p => ({ ...p, dna: false }));
          }}
          disabled={loading.dna}
          className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
        >
          <BarChart3 className="h-4 w-4" />
          {loading.dna ? "Tagging..." : "Auto DNA Tag"}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 overflow-x-auto">
        {[
          { id: "overview", label: "Assortment Matrix", icon: Grid3X3 },
          { id: "buy-plan", label: "Buy Plan", icon: BarChart3 },
          { id: "stores", label: "Store Wedge", icon: Store },
          { id: "styles", label: "Style Mix", icon: Tag },
          { id: "dna", label: "DNA Tags", icon: Zap },
          { id: "attribution", label: "Attribution", icon: Grid3X3 },
          { id: "config", label: "Config", icon: Settings },
          { id: "audit", label: "Audit Log", icon: ClipboardList },
          { id: "inventory", label: "Inventory", icon: Package },
          { id: "orders", label: "Orders", icon: Truck },
          { id: "promotions", label: "Promotions", icon: Calendar },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${tab === t.id ? "border-[#0B2545] text-[#0B2545]" : "border-transparent text-gray-500 hover:text-gray-700"}`}
          >
            <t.icon className="h-4 w-4" /> {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {tab === "overview" && matrix?.matrix && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {["A", "B", "C"].map(w => {
            const m = matrix.matrix[w];
            if (!m) return null;
            const borderColor = w === "A" ? "border-emerald-300" : w === "B" ? "border-blue-300" : "border-gray-300";
            return (
              <div key={w} className={`border-2 ${borderColor} rounded-xl bg-white p-5 space-y-3`}>
                <div className="flex items-center justify-between">
                  <WedgeBadge wedge={w} />
                  <span className="text-xs text-gray-400">{m.stores} store{m.stores !== 1 ? "s" : ""}</span>
                </div>
                <h3 className="text-sm font-semibold text-gray-700">{m.assortment}</h3>
                <div className="text-3xl font-bold text-gray-900">{m.styles} <span className="text-sm font-normal text-gray-400">styles</span></div>
                <div className="space-y-1">
                  {Object.entries(m.style_breakdown || {}).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-xs">
                      <MixBadge mix={k} />
                      <span className="text-gray-600 font-medium">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {tab === "stores" && (
        <div className="space-y-4">
          {/* Distribution Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-white border border-gray-200 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-1">
                <Store className="h-4 w-4 text-gray-400" />
                <span className="text-xs text-gray-500">Total Stores</span>
              </div>
              <div className="text-2xl font-bold text-gray-900">{wedge?.total || 0}</div>
            </div>
            {[
              { w: "A", Icon: Crown, color: "amber", border: "border-l-amber-400", desc: "Full Assortment" },
              { w: "B", Icon: Star, color: "blue", border: "border-l-blue-400", desc: "Standard" },
              { w: "C", Icon: MapPin, color: "gray", border: "border-l-gray-300", desc: "Core Only" },
            ].map(({ w, Icon, color, border, desc }) => {
              const count = wedgeSummary[w];
              const total = wedge?.total || 1;
              const pct = Math.round((count / total) * 100);
              return (
                <div key={w} className={`bg-white border border-gray-200 border-l-4 ${border} rounded-xl p-4`}>
                  <div className="flex items-center gap-1.5 mb-1">
                    <Icon className={`h-3.5 w-3.5 text-${color}-500`} />
                    <span className="text-xs text-gray-500">{w}-Stores</span>
                    <span className="text-[10px] text-gray-400 ml-auto">{desc}</span>
                  </div>
                  <div className="text-2xl font-bold text-gray-900">{count}</div>
                  <div className="w-full bg-gray-100 rounded-full h-1.5 mt-2">
                    <div className={`h-1.5 rounded-full ${w === "A" ? "bg-amber-400" : w === "B" ? "bg-blue-400" : "bg-gray-300"}`} style={{ width: `${pct}%` }} />
                  </div>
                  <div className="text-[10px] text-gray-400 mt-1">{pct}% of total</div>
                </div>
              );
            })}
          </div>

          {/* Search & Filter */}
          <div data-testid="store-filters" className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                data-testid="store-search-input"
                placeholder="Search by store ID, name, or city..."
                value={storeSearch}
                onChange={e => setStoreSearch(e.target.value)}
                className="w-full pl-10 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0B2545] focus:border-[#0B2545] outline-none"
              />
            </div>
            <select data-testid="store-wedge-filter" value={storeWedgeFilter} onChange={e => setStoreWedgeFilter(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#0B2545] outline-none">
              <option value="all">All Wedges</option>
              <option value="A">A-Stores</option>
              <option value="B">B-Stores</option>
              <option value="C">C-Stores</option>
            </select>
            <select data-testid="store-region-filter" value={regionFilter} onChange={e => setRegionFilter(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#0B2545] outline-none">
              <option value="all">All Regions</option>
              <option value="North">North</option>
              <option value="South">South</option>
              <option value="East">East</option>
              <option value="West">West</option>
              <option value="Central">Central</option>
            </select>
            <select data-testid="store-tier-filter" value={tierFilter} onChange={e => setTierFilter(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#0B2545] outline-none">
              <option value="all">All Tiers</option>
              <option value="tier1">Tier 1</option>
              <option value="tier2">Tier 2</option>
              <option value="tier3">Tier 3</option>
            </select>
            <select data-testid="store-format-filter" value={formatFilter} onChange={e => setFormatFilter(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#0B2545] outline-none">
              <option value="all">All Formats</option>
              <option value="hypermarket">Hypermarket</option>
              <option value="supermarket">Supermarket</option>
              <option value="convenience">Convenience</option>
            </select>
            <span className="text-xs text-gray-400">{filteredStores.length} stores</span>
          </div>

          {/* Table */}
          <div className="border border-gray-200 rounded-xl overflow-hidden">
            <table data-testid="store-wedge-table" className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left p-3 font-medium text-gray-600">Store</th>
                  <th className="text-left p-3 font-medium text-gray-600">Name</th>
                  <th className="text-left p-3 font-medium text-gray-600">City</th>
                  <th className="text-left p-3 font-medium text-gray-600">Region</th>
                  <th className="text-left p-3 font-medium text-gray-600">Format</th>
                  <th className="text-left p-3 font-medium text-gray-600">Tier</th>
                  <th className="text-left p-3 font-medium text-gray-600">Wedge</th>
                  <th className="text-right p-3 font-medium text-gray-600">Area</th>
                  <th className="text-right p-3 font-medium text-gray-600">Revenue</th>
                  <th className="text-left p-3 font-medium text-gray-600">Type</th>
                  <th className="w-20"></th>
                </tr>
              </thead>
              <tbody>
                {filteredStores.map(s => (
                  <tr key={s.store_code} className="border-t border-gray-100 hover:bg-gray-50">
                    <td className="p-3 font-mono text-xs font-medium">{s.store_code}</td>
                    <td className="p-3 text-gray-700">{s.store_name || "\u2014"}</td>
                    <td className="p-3 text-gray-500">{s.city || "\u2014"}</td>
                    <td className="p-3 text-gray-500">{s.region || "\u2014"}</td>
                    <td className="p-3">
                      {s.store_format ? (
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${s.store_format === "hypermarket" ? "bg-purple-50 text-purple-700" : s.store_format === "supermarket" ? "bg-blue-50 text-blue-700" : "bg-gray-100 text-gray-600"}`}>
                          {s.store_format}
                        </span>
                      ) : "\u2014"}
                    </td>
                    <td className="p-3">
                      {s.city_tier ? (
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${s.city_tier === "tier1" ? "bg-amber-50 text-amber-700" : s.city_tier === "tier2" ? "bg-blue-50 text-blue-700" : "bg-gray-100 text-gray-600"}`}>
                          {s.city_tier}
                        </span>
                      ) : "\u2014"}
                    </td>
                    <td className="p-3"><WedgeBadge wedge={s.wedge_class} /></td>
                    <td className="p-3 text-right text-gray-500 text-xs">{s.area_sqft ? s.area_sqft.toLocaleString() : "\u2014"}</td>
                    <td className="p-3 text-right text-gray-700 font-medium">
                      {s.total_revenue ? `\u20B9${Math.round(s.total_revenue).toLocaleString()}` : "\u2014"}
                    </td>
                    <td className="p-3">
                      {s.wedge_manual_override ? (
                        <span className="px-1.5 py-0.5 bg-orange-50 text-orange-600 rounded text-[10px] font-medium">Manual</span>
                      ) : s.wedge_class ? (
                        <span className="px-1.5 py-0.5 bg-emerald-50 text-emerald-600 rounded text-[10px] font-medium">Auto</span>
                      ) : null}
                    </td>
                    <td className="p-3 text-right flex gap-1">
                      <button onClick={() => setStoreEditModal(s)} className="p-1 hover:bg-blue-50 rounded text-blue-500" title="Edit attributes">
                        <Settings className="h-3.5 w-3.5" />
                      </button>
                      <button onClick={() => { setOverrideModal({ type: "store", id: s.store_code, current: s.wedge_class }); setOverrideValue(s.wedge_class || "C"); }}
                        className="p-1 hover:bg-indigo-50 rounded text-indigo-500" title="Override wedge">
                        <Edit2 className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
                {filteredStores.length === 0 && (
                  <tr><td colSpan={11} className="p-8 text-center text-gray-400">
                    {storeSearch || storeWedgeFilter !== "all" || regionFilter !== "all" || tierFilter !== "all" || formatFilter !== "all" ? "No stores match your filters." : "No stores found. Upload store master data first."}
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === "styles" && (
        <div className="space-y-4">
          {/* Search */}
          <div data-testid="style-filters" className="flex items-center gap-3">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                data-testid="style-search-input"
                placeholder="Search by style name..."
                value={styleSearch}
                onChange={e => setStyleSearch(e.target.value)}
                className="w-full pl-10 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0B2545] focus:border-[#0B2545] outline-none"
              />
            </div>
            <span className="text-xs text-gray-400">{filteredStyles.length} styles</span>
          </div>

          <div className="border border-gray-200 rounded-xl overflow-hidden">
            <table data-testid="style-mix-table" className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left p-3 font-medium text-gray-600">Style</th>
                  <th className="text-left p-3 font-medium text-gray-600">Mix</th>
                  <th className="text-left p-3 font-medium text-gray-600">SKUs</th>
                  <th className="text-left p-3 font-medium text-gray-600">Avg/Wk</th>
                  <th className="text-left p-3 font-medium text-gray-600">Weeks Active</th>
                  <th className="text-left p-3 font-medium text-gray-600">Peak:Avg</th>
                  <th className="text-left p-3 font-medium text-gray-600">Presence</th>
                  <th className="w-12"></th>
                </tr>
              </thead>
              <tbody>
                {filteredStyles.map(s => (
                  <tr key={s.style} className="border-t border-gray-100 hover:bg-gray-50">
                    <td className="p-3 font-mono text-xs font-medium">{s.style}</td>
                    <td className="p-3"><MixBadge mix={s.style_mix} /></td>
                    <td className="p-3 text-gray-600">{s.sku_count || "\u2014"}</td>
                    <td className="p-3 text-gray-600">{s.stats?.avg_weekly_qty ?? "\u2014"}</td>
                    <td className="p-3 text-gray-600">{s.stats?.weeks_active ?? "\u2014"}</td>
                    <td className="p-3 text-gray-600">{s.stats?.peak_to_avg != null ? `${s.stats.peak_to_avg}x` : "\u2014"}</td>
                    <td className="p-3 text-gray-600">{s.stats?.week_presence_pct != null ? `${s.stats.week_presence_pct}%` : "\u2014"}</td>
                    <td className="p-3">
                      <button onClick={() => { setOverrideModal({ type: "sku", id: s.style, current: s.style_mix }); setOverrideValue(s.style_mix || "Test"); }}
                        className="p-1 hover:bg-indigo-50 rounded text-indigo-500" title="Override mix">
                        <Edit2 className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
                {filteredStyles.length === 0 && (
                  <tr><td colSpan={8} className="p-8 text-center text-gray-400">
                    {styleSearch ? "No styles match your search." : "No style mix data. Run Style Mix Classification after uploading sales data."}
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Buy Plan Tab */}
      {tab === "buy-plan" && (
        <div className="space-y-4">
          {/* Generation Controls */}
          <div data-testid="plan-generation-controls" className="bg-gray-50 rounded-xl p-4 flex flex-wrap items-end gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Cover Period</label>
              <select data-testid="plan-cover-days" value={planCoverDays} onChange={e => setPlanCoverDays(parseInt(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm">
                <option value={30}>30 Days</option>
                <option value={60}>60 Days</option>
                <option value={90}>90 Days</option>
              </select>
            </div>
            <button data-testid="generate-plan-btn" onClick={generatePlan} disabled={loading.generate}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C] disabled:opacity-50">
              <Zap className="h-4 w-4" />
              {loading.generate ? "Generating..." : "Generate & Save Plan"}
            </button>
            <button data-testid="manage-exclusions-btn" onClick={() => setExclusionModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-600">
              <Ban className="h-4 w-4" />
              Exclusions {exclusions.length > 0 && <span className="bg-red-100 text-red-700 px-1.5 rounded-full text-xs font-bold">{exclusions.length}</span>}
            </button>
          </div>

          {/* Plan Selector + Actions */}
          <div data-testid="plan-selector-row" className="flex flex-wrap items-center gap-3">
            <div className="flex-1 min-w-[240px]">
              <select data-testid="plan-selector" value={selectedPlanId} onChange={e => loadPlan(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
                <option value="">-- Select a saved plan --</option>
                {savedPlans.map(p => (
                  <option key={p.plan_id} value={p.plan_id}>
                    {p.plan_name} ({p.status}) - {p.generated_at ? new Date(p.generated_at).toLocaleDateString() : ""}
                  </option>
                ))}
              </select>
            </div>
            {selectedPlan && (
              <span data-testid="plan-status-badge" className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                selectedPlan.status === "ordered" ? "bg-emerald-100 text-emerald-800" :
                selectedPlan.status === "rejected" ? "bg-red-100 text-red-800" :
                selectedPlan.status === "head_approved" ? "bg-purple-100 text-purple-800" :
                selectedPlan.status === "senior_approved" ? "bg-indigo-100 text-indigo-800" :
                selectedPlan.status === "category_approved" ? "bg-cyan-100 text-cyan-800" :
                selectedPlan.status === "submitted" ? "bg-blue-100 text-blue-800" :
                "bg-amber-100 text-amber-800"
              }`}>
                {(selectedPlan.status || "draft").toUpperCase().replace(/_/g, " ")}
              </span>
            )}
            {selectedPlan && selectedPlan.status === "draft" && (
              <button data-testid="delete-plan-btn" onClick={deletePlan}
                className="inline-flex items-center gap-1.5 px-3 py-2 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50">
                Delete Draft
              </button>
            )}
            {selectedPlan && (
              <button data-testid="view-history-btn" onClick={() => loadApprovalHistory(selectedPlanId)}
                className="inline-flex items-center gap-1.5 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-600">
                <History className="h-3.5 w-3.5" /> History
              </button>
            )}
          </div>

          {/* Approval Workflow Panel */}
          {selectedPlan && selectedPlan.status !== "ordered" && selectedPlan.status !== "rejected" && (
            <div data-testid="approval-workflow-panel" className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-gray-900">Approval Workflow</h3>
              </div>

              {/* Status Timeline */}
              <div data-testid="approval-timeline" className="flex items-center justify-between">
                {PLAN_STAGES.map((stage, idx) => {
                  const stageIdx = PLAN_STAGES.findIndex(s => s.key === selectedPlan.status);
                  const isCompleted = idx <= stageIdx;
                  const isCurrent = stage.key === selectedPlan.status;
                  return (
                    <React.Fragment key={stage.key}>
                      <div className="flex flex-col items-center">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                          isCompleted ? "bg-emerald-500 text-white" : "bg-gray-200 text-gray-400"
                        } ${isCurrent ? "ring-2 ring-emerald-400 ring-offset-2" : ""}`}>
                          {isCompleted ? <CheckCircle2 className="h-4 w-4" /> : idx + 1}
                        </div>
                        <span className={`text-[10px] mt-1 ${isCurrent ? "font-bold text-emerald-700" : "text-gray-400"}`}>{stage.label}</span>
                      </div>
                      {idx < PLAN_STAGES.length - 1 && (
                        <div className={`flex-1 h-0.5 mx-1 ${idx < stageIdx ? "bg-emerald-400" : "bg-gray-200"}`} />
                      )}
                    </React.Fragment>
                  );
                })}
              </div>

              {/* Actions + Comment */}
              {getAvailableActions(selectedPlan.status).length > 0 && (
                <div className="space-y-3 pt-2 border-t border-gray-100">
                  <input
                    data-testid="approval-comment"
                    placeholder="Add comment (required for reject/request changes)"
                    value={approvalComment}
                    onChange={e => setApprovalComment(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  />
                  <div className="flex flex-wrap gap-2">
                    {getAvailableActions(selectedPlan.status).map(a => (
                      <button key={a.action} data-testid={`approval-action-${a.action}`}
                        onClick={() => processApproval(a.action)}
                        className={`inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white rounded-lg ${a.color}`}>
                        {a.action === "submit" && <Send className="h-3.5 w-3.5" />}
                        {a.action.startsWith("approve") && <CheckCircle2 className="h-3.5 w-3.5" />}
                        {a.action === "finance_ack" && <CheckCircle2 className="h-3.5 w-3.5" />}
                        {a.action === "reject" && <X className="h-3.5 w-3.5" />}
                        {a.action === "request_changes" && <RotateCcw className="h-3.5 w-3.5" />}
                        {a.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Rejected Banner */}
          {selectedPlan?.status === "rejected" && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
              <X className="h-5 w-5 text-red-500 shrink-0" />
              <div>
                <p className="text-sm font-medium text-red-800">This plan was rejected</p>
                <p className="text-xs text-red-600">{selectedPlan.approvals?.reject?.comment || "No reason provided"} - by {selectedPlan.approvals?.reject?.by}</p>
              </div>
            </div>
          )}

          {/* Summary Cards */}
          {(() => {
            const t = selectedPlan ? selectedPlan.totals : buyPlan?.totals;
            const count = selectedPlan ? selectedPlan.sku_count : buyPlan?.sku_count;
            if (!t && !count) return null;
            return (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-white border rounded-xl p-3 text-center">
                  <div className="text-xl font-bold text-gray-900">{count || 0}</div>
                  <div className="text-xs text-gray-500">SKUs</div>
                </div>
                <div className="bg-white border rounded-xl p-3 text-center">
                  <div className="text-xl font-bold text-emerald-700">{(t?.total_buy_qty || 0).toLocaleString()}</div>
                  <div className="text-xs text-gray-500">Total Buy Qty</div>
                </div>
                <div className="bg-white border rounded-xl p-3 text-center">
                  <div className="text-xl font-bold text-indigo-700">{"\u20B9"}{((t?.total_buy_value || 0) / 1e6).toFixed(1)}M</div>
                  <div className="text-xs text-gray-500">Buy Value</div>
                </div>
                <div className="bg-white border rounded-xl p-3 text-center">
                  <div className="text-xl font-bold text-amber-700">{(t?.total_display_qty || 0).toLocaleString()}</div>
                  <div className="text-xs text-gray-500">Display Min Qty</div>
                </div>
              </div>
            );
          })()}

          {/* Items Table */}
          {(() => {
            const items = planItems.length > 0 ? planItems : (buyPlan?.buy_plan || []);
            const isDraft = selectedPlan?.status === "draft";
            if (items.length === 0) return (
              <div className="border border-gray-200 rounded-xl p-12 text-center text-gray-400">
                No plan data. Generate a new plan or select a saved one above.
              </div>
            );
            return (
              <div className="border border-gray-200 rounded-xl overflow-hidden">
                <table data-testid="buy-plan-table" className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left p-3 font-medium text-gray-600">SKU</th>
                      <th className="text-left p-3 font-medium text-gray-600">Mix</th>
                      <th className="text-right p-3 font-medium text-gray-600">ROS/day</th>
                      <th className="text-right p-3 font-medium text-gray-600">SOH</th>
                      <th className="text-right p-3 font-medium text-gray-600">Demand</th>
                      <th className="text-right p-3 font-medium text-gray-600">Display Min</th>
                      <th className="text-right p-3 font-medium text-gray-600">Safety</th>
                      <th className="text-right p-3 font-medium text-gray-600 bg-emerald-50">Buy Qty</th>
                      <th className="text-right p-3 font-medium text-gray-600">Value</th>
                      <th className="text-left p-3 font-medium text-gray-600">Constraint</th>
                      <th className="w-10"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.slice(0, 50).map((s, idx) => {
                      const qty = s.edited_qty || s.buy_qty;
                      return (
                        <tr key={`${s.sku}-${idx}`} className="border-t border-gray-100 hover:bg-gray-50 group">
                          <td className="p-3 font-mono text-xs">{s.sku}</td>
                          <td className="p-3"><MixBadge mix={s.style_mix} /></td>
                          <td className="p-3 text-right text-gray-600">{s.daily_ros}</td>
                          <td className="p-3 text-right text-gray-500">{s.current_soh}</td>
                          <td className="p-3 text-right text-gray-600">{(s.demand_buy ?? 0).toLocaleString()}</td>
                          <td className="p-3 text-right text-gray-600">{(s.display_minimum ?? 0).toLocaleString()}</td>
                          <td className="p-3 text-right text-gray-600">{(s.safety_stock ?? 0).toLocaleString()}</td>
                          <td className="p-3 text-right bg-emerald-50">
                            {editingItemIdx === idx ? (
                              <div className="flex items-center gap-1 justify-end">
                                <input type="number" value={editingQty} onChange={e => setEditingQty(e.target.value)}
                                  className="w-20 border rounded px-1.5 py-0.5 text-sm text-right" autoFocus />
                                <button onClick={updateItemQty} className="text-emerald-600 hover:text-emerald-800">
                                  <Save className="h-3.5 w-3.5" />
                                </button>
                                <button onClick={() => { setEditingItemIdx(null); setEditingQty(""); }} className="text-gray-400 hover:text-gray-600 text-xs ml-0.5">{"\u2715"}</button>
                              </div>
                            ) : (
                              <div className="flex items-center justify-end gap-1">
                                <span className="font-bold text-emerald-700">{qty?.toLocaleString()}</span>
                                {s.edited_qty && <span className="text-[9px] text-orange-500 ml-0.5">edited</span>}
                                {isDraft && (
                                  <button onClick={() => { setEditingItemIdx(idx); setEditingQty(String(qty)); }}
                                    className="ml-1 p-0.5 hover:bg-emerald-100 rounded text-emerald-600 opacity-40 group-hover:opacity-100">
                                    <Edit2 className="h-3 w-3" />
                                  </button>
                                )}
                              </div>
                            )}
                          </td>
                          <td className="p-3 text-right text-gray-700">{"\u20B9"}{((qty * (s.mrp || 0)) / 1000).toFixed(0)}k</td>
                          <td className="p-3"><span className={`px-2 py-0.5 rounded text-xs ${s.binding_constraint === "demand" ? "bg-blue-50 text-blue-700" : s.binding_constraint === "display_min" ? "bg-amber-50 text-amber-700" : "bg-gray-100 text-gray-600"}`}>{s.binding_constraint}</span></td>
                          <td className="p-3">
                            <button data-testid={`detail-btn-${idx}`} onClick={() => setDetailItem(s)} className="p-1 hover:bg-gray-100 rounded text-gray-400">
                              <Eye className="h-3.5 w-3.5" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            );
          })()}

          {/* Calculation Breakdown Modal */}
          {detailItem && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setDetailItem(null)}>
              <div data-testid="calc-breakdown-modal" onClick={e => e.stopPropagation()} className="bg-white rounded-xl p-6 w-full max-w-md shadow-2xl space-y-4">
                <h2 className="text-lg font-bold text-gray-900">Calculation Breakdown</h2>
                <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                  <span className="text-gray-500">SKU:</span><span className="font-mono">{detailItem.sku}</span>
                  <span className="text-gray-500">Style:</span><span>{detailItem.style}</span>
                  <span className="text-gray-500">Style Mix:</span><span><MixBadge mix={detailItem.style_mix} /></span>
                  <span className="text-gray-500">Category:</span><span>{detailItem.category || "\u2014"}</span>
                  <span className="text-gray-500">Daily ROS:</span><span>{detailItem.daily_ros} units/day</span>
                  <span className="text-gray-500">Forecasted Demand:</span><span>{detailItem.forecasted_demand} units</span>
                  <span className="text-gray-500">Sell-Through Target:</span><span>{detailItem.sell_through_target}x</span>
                  <span className="text-gray-500">Current SOH:</span><span>{detailItem.current_soh} units</span>
                  <span className="text-gray-500">Demand Buy:</span><span>{detailItem.demand_buy} units</span>
                  <span className="text-gray-500">Display Minimum:</span><span>{detailItem.display_minimum} units</span>
                  <span className="text-gray-500">Safety Stock:</span><span>{detailItem.safety_stock} units</span>
                  <span className="text-gray-500">MRP:</span><span>{"\u20B9"}{detailItem.mrp}</span>
                  <span className="text-gray-500">Constraint:</span>
                  <span className={`px-2 py-0.5 rounded text-xs inline-block w-fit ${detailItem.binding_constraint === "demand" ? "bg-blue-50 text-blue-700" : detailItem.binding_constraint === "display_min" ? "bg-amber-50 text-amber-700" : "bg-gray-100 text-gray-600"}`}>{detailItem.binding_constraint}</span>
                </div>
                <div className="pt-3 border-t border-gray-100 flex justify-between items-center">
                  <div>
                    <div className="text-gray-500 text-xs">Final Buy Qty</div>
                    <div className="text-xl font-bold text-emerald-700">{(detailItem.edited_qty || detailItem.buy_qty)?.toLocaleString()} units</div>
                  </div>
                  <div className="text-right">
                    <div className="text-gray-500 text-xs">Buy Value</div>
                    <div className="text-lg font-bold text-indigo-700">{"\u20B9"}{detailItem.buy_value?.toLocaleString()}</div>
                  </div>
                </div>
                <div className="flex justify-end pt-2">
                  <button onClick={() => setDetailItem(null)} className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50">Close</button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* DNA Tags Tab */}
      {tab === "dna" && (
        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <table data-testid="dna-table" className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-3 font-medium text-gray-600">Style</th>
                <th className="text-left p-3 font-medium text-gray-600">Mix</th>
                <th className="text-left p-3 font-medium text-gray-600">Flow Rank</th>
                <th className="text-left p-3 font-medium text-gray-600">Lifecycle</th>
                <th className="text-left p-3 font-medium text-gray-600">Launch Date</th>
                <th className="text-left p-3 font-medium text-gray-600">Expected Weeks</th>
                <th className="text-left p-3 font-medium text-gray-600">SKUs</th>
              </tr>
            </thead>
            <tbody>
              {(dnaTags?.styles || []).map(s => (
                <tr key={s.style} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="p-3 font-mono text-xs font-medium">{s.style}</td>
                  <td className="p-3"><MixBadge mix={s.style_mix} /></td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${s.flow_rank === 1 ? "bg-emerald-100 text-emerald-800" : s.flow_rank === 2 ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-600"}`}>
                      {s.flow_rank === 1 ? "Hero" : s.flow_rank === 2 ? "Core" : "Fill-in"}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-xs ${s.lifecycle_stage === "Peak" ? "bg-emerald-50 text-emerald-700" : s.lifecycle_stage === "Launch" ? "bg-blue-50 text-blue-700" : s.lifecycle_stage === "Decline" ? "bg-amber-50 text-amber-700" : "bg-red-50 text-red-700"}`}>
                      {s.lifecycle_stage || "—"}
                    </span>
                  </td>
                  <td className="p-3 text-xs text-gray-500">{s.launch_date || "—"}</td>
                  <td className="p-3 text-gray-600">{s.expected_weeks ?? "—"}w</td>
                  <td className="p-3 text-gray-500">{s.sku_count}</td>
                </tr>
              ))}
              {(dnaTags?.styles || []).length === 0 && (
                <tr><td colSpan={7} className="p-8 text-center text-gray-400">No DNA tags. Click "Auto DNA Tag" to classify.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Attribution Tab */}
      {tab === "attribution" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Attribution Table */}
            <div className={`${selectedAttr ? "lg:col-span-2" : "lg:col-span-3"} border border-gray-200 rounded-xl overflow-hidden`}>
              <table data-testid="attribution-table" className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left p-3 font-medium text-gray-600">Style</th>
                    <th className="text-left p-3 font-medium text-gray-600">Mix</th>
                    <th className="text-center p-3 font-medium text-gray-600">A-Stores</th>
                    <th className="text-center p-3 font-medium text-gray-600">B-Stores</th>
                    <th className="text-center p-3 font-medium text-gray-600">C-Stores</th>
                    <th className="text-left p-3 font-medium text-gray-600">Coverage</th>
                    <th className="w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {(attribution?.attributions || []).map(a => (
                    <tr key={a.style} className={`border-t border-gray-100 hover:bg-gray-50 cursor-pointer ${selectedAttr?.style === a.style ? "bg-blue-50/50" : ""}`}
                      onClick={() => setSelectedAttr(selectedAttr?.style === a.style ? null : a)}>
                      <td className="p-3 font-mono text-xs font-medium">{a.style}</td>
                      <td className="p-3"><MixBadge mix={a.style_mix} /></td>
                      {["A", "B", "C"].map(w => (
                        <td key={w} className="p-3 text-center">
                          {a.wedge_allocation[w]?.eligible ? (
                            <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded text-xs font-medium">{a.wedge_allocation[w].allocation_pct}%</span>
                          ) : (
                            <span className="text-xs text-gray-300">{"\u2014"}</span>
                          )}
                        </td>
                      ))}
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                            <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${a.coverage_pct}%` }} />
                          </div>
                          <span className="text-xs text-gray-500">{a.coverage_pct}%</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <Eye className="h-3.5 w-3.5 text-gray-400" />
                      </td>
                    </tr>
                  ))}
                  {(attribution?.attributions || []).length === 0 && (
                    <tr><td colSpan={7} className="p-8 text-center text-gray-400">No attribution data. Run classifications first.</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Detail Panel */}
            {selectedAttr && (
              <div data-testid="attribution-detail-panel" className="border border-gray-200 rounded-xl bg-white p-5 space-y-4 h-fit">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-gray-900">Attribution Detail</h3>
                  <button onClick={() => setSelectedAttr(null)} className="text-gray-400 hover:text-gray-600 text-xs">Close</button>
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Style</span>
                    <span className="font-mono font-medium">{selectedAttr.style}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Style Mix</span>
                    <MixBadge mix={selectedAttr.style_mix} />
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">SKU Count</span>
                    <span className="font-medium">{selectedAttr.sku_count}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Eligible Stores</span>
                    <span className="font-medium">{selectedAttr.eligible_stores} / {selectedAttr.total_stores}</span>
                  </div>
                </div>
                <div className="pt-3 border-t border-gray-100 space-y-3">
                  <p className="text-xs font-medium text-gray-600">Wedge Allocation</p>
                  {["A", "B", "C"].map(w => {
                    const alloc = selectedAttr.wedge_allocation[w];
                    const color = w === "A" ? "bg-amber-400" : w === "B" ? "bg-blue-400" : "bg-gray-300";
                    return (
                      <div key={w}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="font-medium">{w}-Stores {alloc?.eligible ? "" : "(not eligible)"}</span>
                          <span className={alloc?.eligible ? "text-gray-900 font-medium" : "text-gray-300"}>{alloc?.eligible ? `${alloc.allocation_pct}%` : "\u2014"}</span>
                        </div>
                        {alloc?.eligible && (
                          <div className="w-full bg-gray-100 rounded-full h-2">
                            <div className={`h-2 rounded-full ${color}`} style={{ width: `${alloc.allocation_pct}%` }} />
                          </div>
                        )}
                        {alloc?.eligible && (
                          <p className="text-[10px] text-gray-400 mt-0.5">{alloc.stores} stores allocated</p>
                        )}
                      </div>
                    );
                  })}
                </div>
                <div className="pt-3 border-t border-gray-100">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Coverage</span>
                    <span className="font-bold text-emerald-700">{selectedAttr.coverage_pct}%</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Config Tab: Sell-Through Targets */}
      {tab === "config" && (
        <div data-testid="sell-through-config-panel" className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-gray-900">Sell-Through Targets</h2>
                <p className="text-sm text-gray-500 mt-0.5">Configure target sell-through multipliers per style mix used in the buy formula</p>
              </div>
              <button data-testid="reset-sell-through-btn" onClick={resetSellThrough}
                className="inline-flex items-center gap-1.5 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-600">
                <RotateCcw className="h-3.5 w-3.5" /> Reset Defaults
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left: Multiplier Cards */}
              <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-3 gap-4">
                {sellThroughConfigs.map(c => {
                  const isEditing = editingMultipliers[c.style_mix] !== undefined;
                  const currentVal = isEditing ? parseFloat(editingMultipliers[c.style_mix]) || 0 : c.target_multiplier;
                  const defaultVal = DEFAULTS[c.style_mix] || 1;
                  const mixColors = { Core: "border-emerald-300 bg-emerald-50/30", Fashion: "border-purple-300 bg-purple-50/30", Test: "border-amber-300 bg-amber-50/30" };
                  const mixDesc = { Core: "High-velocity staples with consistent demand", Fashion: "Trend-driven styles with seasonal peaks", Test: "New introductions with limited history" };
                  return (
                    <div key={c.style_mix} className={`border-2 ${mixColors[c.style_mix] || "border-gray-200"} rounded-xl p-5 space-y-3`}>
                      <div className="flex items-center justify-between">
                        <MixBadge mix={c.style_mix} />
                        <div className="flex items-center gap-1.5">
                          {currentVal > defaultVal ? (
                            <span className="inline-flex items-center gap-0.5 text-[10px] text-red-600 bg-red-50 px-1.5 py-0.5 rounded font-medium">
                              <TrendingUp className="h-3 w-3" /> Aggressive
                            </span>
                          ) : currentVal < defaultVal ? (
                            <span className="inline-flex items-center gap-0.5 text-[10px] text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded font-medium">
                              <TrendingDown className="h-3 w-3" /> Conservative
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-0.5 text-[10px] text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded font-medium">
                              <CheckCircle2 className="h-3 w-3" /> Balanced
                            </span>
                          )}
                          {c.is_default && <span className="text-[10px] text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">DEFAULT</span>}
                          {!c.is_default && <span className="text-[10px] text-blue-500 bg-blue-50 px-1.5 py-0.5 rounded">CUSTOM</span>}
                        </div>
                      </div>
                      <p className="text-xs text-gray-500">{mixDesc[c.style_mix]}</p>
                      <div className="space-y-2">
                        <label className="text-xs font-medium text-gray-600">Target Multiplier</label>
                        <div className="flex items-center gap-2">
                          <input
                            data-testid={`sell-through-input-${c.style_mix.toLowerCase()}`}
                            type="number"
                            step="0.1"
                            min="0"
                            max="5"
                            value={isEditing ? editingMultipliers[c.style_mix] : c.target_multiplier}
                            onChange={e => setEditingMultipliers(p => ({ ...p, [c.style_mix]: e.target.value }))}
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-[#0B2545] focus:border-[#0B2545] outline-none"
                          />
                          {isEditing && (
                            <button
                              data-testid={`save-sell-through-${c.style_mix.toLowerCase()}`}
                              onClick={() => saveSellThrough(c.style_mix)}
                              className="p-2 bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C] shrink-0"
                            >
                              <Save className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                        <p className="text-[10px] text-gray-400">
                          Buy = {c.target_multiplier}x forecasted demand &minus; SOH
                        </p>
                      </div>
                      {c.updated_by && (
                        <p className="text-[10px] text-gray-400 pt-1 border-t border-gray-100">
                          Last updated by {c.updated_by} {c.updated_at ? `on ${new Date(c.updated_at).toLocaleDateString()}` : ""}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Right: Impact Summary */}
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-xl p-4 space-y-3">
                  <h3 className="text-sm font-bold text-gray-700">Impact Summary</h3>
                  {sellThroughConfigs.map(c => {
                    const val = editingMultipliers[c.style_mix] !== undefined ? parseFloat(editingMultipliers[c.style_mix]) || 0 : c.target_multiplier;
                    const def = DEFAULTS[c.style_mix] || 1;
                    const isHigh = val > def;
                    const isLow = val < def;
                    const impactText = {
                      Core: isHigh ? "Better availability, higher carrying cost" : isLow ? "Lower stock levels, potential OOS risk" : "Standard approach for high-velocity items",
                      Fashion: isHigh ? "More markdown risk, better availability" : isLow ? "Lower risk, may miss trend winners" : "Standard approach for seasonal items",
                      Test: isHigh ? "More test units = higher learning, higher risk" : isLow ? "Cautious testing, limited market learning" : "Standard approach for new items",
                    };
                    return (
                      <div key={c.style_mix} className="p-3 bg-white rounded-lg border border-gray-100">
                        <div className="flex items-center justify-between mb-1">
                          <MixBadge mix={c.style_mix} />
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${isHigh ? "bg-red-50 text-red-600" : isLow ? "bg-amber-50 text-amber-600" : "bg-emerald-50 text-emerald-600"}`}>
                            {isHigh ? "Higher Inventory" : isLow ? "Lower Inventory" : "Balanced"}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500">{impactText[c.style_mix]}</p>
                      </div>
                    );
                  })}
                </div>

                {/* Example Calculation */}
                <div data-testid="config-example-calc" className="bg-[#0B2545]/5 rounded-xl p-4 space-y-2">
                  <h3 className="text-sm font-bold text-gray-700">Example Calculation</h3>
                  <div className="bg-white rounded-lg p-3 text-xs font-mono space-y-1 border">
                    <p className="text-gray-500">Forecast: <span className="text-gray-900 font-bold">100 units</span></p>
                    <p className="text-gray-500">Current Stock: <span className="text-gray-900 font-bold">20 units</span></p>
                    <p className="text-gray-500">Core Multiplier: <span className="text-gray-900 font-bold">{sellThroughConfigs.find(c => c.style_mix === "Core")?.target_multiplier || 1.2}x</span></p>
                    <div className="border-t border-dashed border-gray-200 pt-1 mt-1">
                      <p className="text-emerald-700 font-bold">
                        Buy Qty = ({sellThroughConfigs.find(c => c.style_mix === "Core")?.target_multiplier || 1.2} x 100) - 20 = {Math.max(0, (sellThroughConfigs.find(c => c.style_mix === "Core")?.target_multiplier || 1.2) * 100 - 20)} units
                      </p>
                    </div>
                  </div>
                </div>

                {/* Info */}
                <div className="bg-gray-50 rounded-xl p-4 text-xs text-gray-500 space-y-1">
                  <p className="font-medium text-gray-600">How multipliers work:</p>
                  <p><strong>Core (1.2x)</strong> &mdash; Overbuy 20% to prevent stockouts</p>
                  <p><strong>Fashion (0.8x)</strong> &mdash; Conservative to manage markdown risk</p>
                  <p><strong>Test (0.4x)</strong> &mdash; Minimal investment for unproven styles</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Inventory & Safety Stock Tab */}
      {tab === "inventory" && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="bg-white border rounded-xl p-4">
              <div className="text-xs text-gray-500">Total Records</div>
              <div className="text-xl font-bold text-gray-900">{(inventorySummary?.total_records || 0).toLocaleString()}</div>
            </div>
            <div className="bg-white border rounded-xl p-4">
              <div className="text-xs text-gray-500">Total SOH</div>
              <div className="text-xl font-bold text-emerald-700">{(inventorySummary?.total_soh || 0).toLocaleString()}</div>
            </div>
            <div className="bg-white border rounded-xl p-4">
              <div className="text-xs text-gray-500">In Transit</div>
              <div className="text-xl font-bold text-blue-700">{(inventorySummary?.total_in_transit || 0).toLocaleString()}</div>
            </div>
            <div className="bg-white border rounded-xl p-4">
              <div className="text-xs text-gray-500">Stores</div>
              <div className="text-xl font-bold text-gray-900">{inventorySummary?.unique_stores || 0}</div>
            </div>
            <div className="bg-white border rounded-xl p-4">
              <div className="text-xs text-gray-500">SKUs</div>
              <div className="text-xl font-bold text-gray-900">{inventorySummary?.unique_skus || 0}</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Upload Panel */}
            <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
              <h3 className="text-base font-bold text-gray-900">Upload Inventory</h3>
              <p className="text-xs text-gray-500">Upload CSV with columns: store_code, sku, date, soh, in_transit, open_po_qty</p>
              <div data-testid="inventory-upload-area" className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center">
                <Upload className="h-8 w-8 mx-auto text-gray-300 mb-2" />
                <p className="text-sm text-gray-500 mb-3">Drag & drop or click to upload CSV</p>
                <label className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C] cursor-pointer">
                  <Upload className="h-4 w-4" />
                  {loading.inventory ? "Uploading..." : "Select File"}
                  <input type="file" accept=".csv" className="hidden" data-testid="inventory-file-input"
                    onChange={e => handleInventoryUpload(e.target.files[0])} disabled={loading.inventory} />
                </label>
              </div>
              {syncStatus && (
                <div className="text-xs text-gray-400 bg-gray-50 rounded-lg p-3">
                  <p>Last sync: {syncStatus.synced_at ? new Date(syncStatus.synced_at).toLocaleString() : "Never"}</p>
                  <p>By: {syncStatus.synced_by} | Source: {syncStatus.source} | Records: {syncStatus.total}</p>
                </div>
              )}
            </div>

            {/* Safety Stock Config */}
            <div data-testid="safety-stock-config" className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-gray-900">Safety Stock Configuration</h3>
                <button onClick={resetSafetyConfig} className="text-xs text-gray-400 hover:text-gray-600 underline">Reset Defaults</button>
              </div>
              <p className="text-xs text-gray-500">Formula: SS = z {"\u00D7"} MAD {"\u00D7"} {"\u221A"}(LT / RP)</p>

              {safetyConfig && (() => {
                const cfg = editingSafetyConfig || safetyConfig;
                const isEditing = !!editingSafetyConfig;
                return (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Service Level (z-score)</label>
                      <select data-testid="safety-service-level"
                        value={cfg.service_level}
                        onChange={e => setEditingSafetyConfig({ ...(editingSafetyConfig || safetyConfig), service_level: parseFloat(e.target.value) })}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
                        {SL_OPTIONS.map(o => <option key={o.val} value={o.val}>{o.label}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Review Period: {cfg.review_period_days} days</label>
                      <input type="range" data-testid="safety-review-period" min={1} max={30} value={cfg.review_period_days}
                        onChange={e => setEditingSafetyConfig({ ...(editingSafetyConfig || safetyConfig), review_period_days: parseInt(e.target.value) })}
                        className="w-full" />
                      <div className="flex justify-between text-[10px] text-gray-400"><span>1 day</span><span>30 days</span></div>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Max Safety: {cfg.max_safety_weeks} weeks of MAD</label>
                      <input type="range" data-testid="safety-max-weeks" min={1} max={26} value={cfg.max_safety_weeks}
                        onChange={e => setEditingSafetyConfig({ ...(editingSafetyConfig || safetyConfig), max_safety_weeks: parseInt(e.target.value) })}
                        className="w-full" />
                      <div className="flex justify-between text-[10px] text-gray-400"><span>1 week</span><span>26 weeks</span></div>
                    </div>

                    <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-500 space-y-1">
                      <p><strong>z-score:</strong> {cfg.z_score || {0.80: 0.842, 0.90: 1.282, 0.95: 1.645, 0.98: 2.054, 0.99: 2.326}[cfg.service_level] || 1.645}</p>
                      <p>Higher service level = more safety stock = lower OOS risk but higher cost</p>
                    </div>

                    {isEditing && (
                      <div className="flex gap-2">
                        <button data-testid="save-safety-config-btn" onClick={saveSafetyConfig}
                          className="flex-1 px-4 py-2 text-sm bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C]">
                          <Save className="h-3.5 w-3.5 inline mr-1" /> Save Configuration
                        </button>
                        <button onClick={() => setEditingSafetyConfig(null)}
                          className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
                      </div>
                    )}
                    {!isEditing && !safetyConfig.is_default && (
                      <p className="text-[10px] text-emerald-600">Custom config active. Updated by {safetyConfig.updated_by}</p>
                    )}
                    {!isEditing && safetyConfig.is_default && (
                      <p className="text-[10px] text-gray-400">Using system defaults</p>
                    )}
                  </div>
                );
              })()}
            </div>
          </div>
        </div>
      )}

      {/* Orders Tab */}
      {tab === "orders" && (
        <div className="space-y-4">
          {/* Consolidate from plan */}
          {selectedPlan && selectedPlan.status !== "draft" && (
            <div className="bg-gray-50 rounded-xl p-4 flex items-center gap-4">
              <div className="flex-1">
                <p className="text-sm font-medium">Generate POs from: <strong>{selectedPlan.plan_name}</strong></p>
                <p className="text-xs text-gray-500">Groups buy plan items by category into supplier-level purchase orders</p>
              </div>
              <button data-testid="consolidate-orders-btn" onClick={() => consolidateOrders(selectedPlanId)}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C]">
                <Package className="h-4 w-4" /> Consolidate into POs
              </button>
            </div>
          )}
          {!selectedPlan && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-700">
              Select an approved/ordered plan from the Buy Plan tab first to generate consolidated POs.
            </div>
          )}

          {/* PO List */}
          <div className="border border-gray-200 rounded-xl overflow-hidden">
            <table data-testid="orders-table" className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left p-3 font-medium text-gray-600">PO Number</th>
                  <th className="text-left p-3 font-medium text-gray-600">Category</th>
                  <th className="text-left p-3 font-medium text-gray-600">Plan</th>
                  <th className="text-right p-3 font-medium text-gray-600">SKUs</th>
                  <th className="text-right p-3 font-medium text-gray-600">Units</th>
                  <th className="text-right p-3 font-medium text-gray-600">Value</th>
                  <th className="text-left p-3 font-medium text-gray-600">Status</th>
                  <th className="text-left p-3 font-medium text-gray-600">Phased</th>
                  <th className="w-28"></th>
                </tr>
              </thead>
              <tbody>
                {orders.map(o => (
                  <tr key={o.po_number} className="border-t border-gray-100 hover:bg-gray-50">
                    <td className="p-3 font-mono text-xs font-medium">{o.po_number}</td>
                    <td className="p-3 text-gray-600">{o.supplier_group}</td>
                    <td className="p-3 text-xs text-gray-500">{o.plan_name}</td>
                    <td className="p-3 text-right">{o.unique_skus}</td>
                    <td className="p-3 text-right font-medium">{o.total_units?.toLocaleString()}</td>
                    <td className="p-3 text-right">{"\u20B9"}{((o.total_value || 0) / 1e3).toFixed(0)}k</td>
                    <td className="p-3">
                      <select data-testid={`po-status-${o.po_number}`} value={o.status} onChange={e => updatePOStatus(o.po_number, e.target.value)}
                        className={`border rounded px-2 py-0.5 text-xs font-medium ${
                          o.status === "received" ? "bg-emerald-50 text-emerald-700 border-emerald-200" :
                          o.status === "shipped" ? "bg-purple-50 text-purple-700 border-purple-200" :
                          o.status === "confirmed" ? "bg-cyan-50 text-cyan-700 border-cyan-200" :
                          o.status === "sent" ? "bg-blue-50 text-blue-700 border-blue-200" :
                          o.status === "cancelled" ? "bg-red-50 text-red-700 border-red-200" :
                          "bg-gray-50 text-gray-600 border-gray-200"
                        }`}>
                        <option value="draft">Draft</option>
                        <option value="sent">Sent</option>
                        <option value="confirmed">Confirmed</option>
                        <option value="shipped">Shipped</option>
                        <option value="received">Received</option>
                        <option value="cancelled">Cancelled</option>
                      </select>
                    </td>
                    <td className="p-3">
                      {o.is_phased ? (
                        <span className="px-1.5 py-0.5 bg-indigo-50 text-indigo-700 rounded text-[10px] font-medium">Phased</span>
                      ) : (
                        <button data-testid={`phase-btn-${o.po_number}`} onClick={() => setPhaseModal(o.po_number)}
                          className="text-xs text-indigo-600 hover:underline">Phase it</button>
                      )}
                    </td>
                    <td className="p-3 text-right">
                      <button onClick={() => setSelectedOrder(selectedOrder === o.po_number ? null : o.po_number)}
                        className="text-xs text-gray-500 hover:text-gray-800">{selectedOrder === o.po_number ? "Hide" : "Items"}</button>
                    </td>
                  </tr>
                ))}
                {orders.length === 0 && (
                  <tr><td colSpan={9} className="p-12 text-center text-gray-400">No POs yet. Consolidate an approved buy plan to generate purchase orders.</td></tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Expanded PO Items */}
          {selectedOrder && (() => {
            const o = orders.find(x => x.po_number === selectedOrder);
            if (!o) return null;
            return (
              <div data-testid="po-detail" className="border border-indigo-200 bg-indigo-50/30 rounded-xl p-4 space-y-2">
                <h4 className="text-sm font-bold text-gray-900">{o.po_number} - Items ({o.items?.length})</h4>
                <div className="border rounded-lg overflow-hidden bg-white">
                  <table className="w-full text-xs">
                    <thead className="bg-gray-50"><tr>
                      <th className="text-left p-2">SKU</th><th className="text-left p-2">Style</th>
                      <th className="text-left p-2">Mix</th><th className="text-right p-2">Qty</th>
                      <th className="text-right p-2">MRP</th><th className="text-right p-2">Value</th>
                    </tr></thead>
                    <tbody>
                      {(o.items || []).slice(0, 30).map((it, i) => (
                        <tr key={i} className="border-t border-gray-50">
                          <td className="p-2 font-mono">{it.sku}</td>
                          <td className="p-2">{it.style}</td>
                          <td className="p-2"><MixBadge mix={it.style_mix} /></td>
                          <td className="p-2 text-right font-medium">{it.po_qty?.toLocaleString()}</td>
                          <td className="p-2 text-right">{"\u20B9"}{it.mrp}</td>
                          <td className="p-2 text-right">{"\u20B9"}{it.po_value?.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })()}
        </div>
      )}

      {/* Promotions Tab */}
      {tab === "promotions" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-gray-900">Promotion Calendar</h2>
              <p className="text-sm text-gray-500">Active promotions automatically apply lift factors to the buy formula</p>
            </div>
            <button data-testid="add-promotion-btn" onClick={() => setPromoModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C]">
              <Plus className="h-4 w-4" /> Add Promotion
            </button>
          </div>

          <div className="border border-gray-200 rounded-xl overflow-hidden">
            <table data-testid="promotions-table" className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left p-3 font-medium text-gray-600">Name</th>
                  <th className="text-left p-3 font-medium text-gray-600">Type</th>
                  <th className="text-left p-3 font-medium text-gray-600">Start</th>
                  <th className="text-left p-3 font-medium text-gray-600">End</th>
                  <th className="text-left p-3 font-medium text-gray-600">Discount</th>
                  <th className="text-left p-3 font-medium text-gray-600">Categories</th>
                  <th className="text-center p-3 font-medium text-gray-600">Lift Factor</th>
                  <th className="text-left p-3 font-medium text-gray-600">Status</th>
                  <th className="w-12"></th>
                </tr>
              </thead>
              <tbody>
                {promotions.map(p => {
                  const isActive = p.status === "active" && p.start_date <= new Date().toISOString().split("T")[0] && p.end_date >= new Date().toISOString().split("T")[0];
                  return (
                    <tr key={p.promo_id} className="border-t border-gray-100 hover:bg-gray-50">
                      <td className="p-3 font-medium text-gray-900">{p.name}</td>
                      <td className="p-3"><span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-700">{p.promo_type}</span></td>
                      <td className="p-3 text-gray-500 text-xs">{p.start_date}</td>
                      <td className="p-3 text-gray-500 text-xs">{p.end_date}</td>
                      <td className="p-3 text-gray-600">{p.discount_value}{p.discount_type === "percentage" ? "%" : ""} {p.discount_type}</td>
                      <td className="p-3 text-xs text-gray-500">{(p.affected_categories || []).join(", ") || "All"}</td>
                      <td className="p-3 text-center">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${p.lift_factor > 1 ? "bg-emerald-50 text-emerald-700" : "bg-gray-100 text-gray-600"}`}>
                          {p.lift_factor}x
                        </span>
                      </td>
                      <td className="p-3">
                        {isActive ? (
                          <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded-full text-[10px] font-bold">ACTIVE</span>
                        ) : p.end_date < new Date().toISOString().split("T")[0] ? (
                          <span className="px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full text-[10px] font-bold">ENDED</span>
                        ) : (
                          <span className="px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full text-[10px] font-bold">UPCOMING</span>
                        )}
                      </td>
                      <td className="p-3">
                        <button onClick={() => deletePromotion(p.promo_id)} className="text-red-400 hover:text-red-600"><X className="h-3.5 w-3.5" /></button>
                      </td>
                    </tr>
                  );
                })}
                {promotions.length === 0 && (
                  <tr><td colSpan={9} className="p-12 text-center text-gray-400">No promotions yet. Add one to apply lift factors to the buy formula.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Audit Log Tab */}
      {tab === "audit" && (
        <div className="space-y-4">
          {/* Filters */}
          <div data-testid="audit-filters" className="flex items-center gap-3">
            <select data-testid="audit-entity-filter" value={auditFilter.entity_type}
              onChange={e => {
                const f = { ...auditFilter, entity_type: e.target.value };
                setAuditFilter(f);
                axios.get(`${API}/buy-planning/audit-log`, { params: { entity_type: f.entity_type || undefined, source: f.source || undefined, limit: 100 } })
                  .then(r => setAuditLog(r.data?.entries || [])).catch(() => {});
              }}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm">
              <option value="">All Types</option>
              <option value="store">Store Wedge</option>
              <option value="style">Style Mix</option>
              <option value="config">Config</option>
            </select>
            <select data-testid="audit-source-filter" value={auditFilter.source}
              onChange={e => {
                const f = { ...auditFilter, source: e.target.value };
                setAuditFilter(f);
                axios.get(`${API}/buy-planning/audit-log`, { params: { entity_type: f.entity_type || undefined, source: f.source || undefined, limit: 100 } })
                  .then(r => setAuditLog(r.data?.entries || [])).catch(() => {});
              }}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm">
              <option value="">All Sources</option>
              <option value="auto">Auto Classification</option>
              <option value="manual">Manual Override</option>
            </select>
            <span className="text-xs text-gray-400">{auditLog.length} entries</span>
          </div>

          {/* Audit Table */}
          <div className="border border-gray-200 rounded-xl overflow-hidden">
            <table data-testid="audit-log-table" className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left p-3 font-medium text-gray-600">Timestamp</th>
                  <th className="text-left p-3 font-medium text-gray-600">Action</th>
                  <th className="text-left p-3 font-medium text-gray-600">Type</th>
                  <th className="text-left p-3 font-medium text-gray-600">Entity</th>
                  <th className="text-left p-3 font-medium text-gray-600">Field</th>
                  <th className="text-left p-3 font-medium text-gray-600">Change</th>
                  <th className="text-left p-3 font-medium text-gray-600">Source</th>
                  <th className="text-left p-3 font-medium text-gray-600">User</th>
                  <th className="text-left p-3 font-medium text-gray-600">Reason</th>
                </tr>
              </thead>
              <tbody>
                {auditLog.map((e, i) => (
                  <tr key={i} className="border-t border-gray-100 hover:bg-gray-50">
                    <td className="p-3 text-xs text-gray-500 whitespace-nowrap">
                      {e.created_at ? new Date(e.created_at).toLocaleString() : "\u2014"}
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        e.action === "classify" ? "bg-blue-50 text-blue-700" :
                        e.action === "override" ? "bg-orange-50 text-orange-700" :
                        e.action === "config_update" ? "bg-purple-50 text-purple-700" :
                        "bg-gray-100 text-gray-600"
                      }`}>{e.action}</span>
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        e.entity_type === "store" ? "bg-emerald-50 text-emerald-700" :
                        e.entity_type === "style" ? "bg-indigo-50 text-indigo-700" :
                        "bg-gray-50 text-gray-600"
                      }`}>{e.entity_type}</span>
                    </td>
                    <td className="p-3 font-mono text-xs font-medium">{e.entity_id}</td>
                    <td className="p-3 text-xs text-gray-500">{e.field}</td>
                    <td className="p-3">
                      <div className="flex items-center gap-1 text-xs">
                        <span className="text-red-500 line-through">{e.old_value || "none"}</span>
                        <span className="text-gray-400">{"\u2192"}</span>
                        <span className="text-emerald-700 font-medium">{e.new_value}</span>
                      </div>
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        e.source === "auto" ? "bg-blue-100 text-blue-800" : "bg-orange-100 text-orange-800"
                      }`}>{e.source === "auto" ? "AUTO" : "MANUAL"}</span>
                    </td>
                    <td className="p-3 text-xs text-gray-500">{e.created_by || "\u2014"}</td>
                    <td className="p-3 text-xs text-gray-500 max-w-[200px] truncate" title={e.reason}>{e.reason || "\u2014"}</td>
                  </tr>
                ))}
                {auditLog.length === 0 && (
                  <tr><td colSpan={9} className="p-12 text-center text-gray-400">
                    No audit entries yet. Run classifications or make manual overrides to generate audit logs.
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Phase Replenishment Modal */}
      {phaseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setPhaseModal(null)}>
          <div data-testid="phase-modal" onClick={e => e.stopPropagation()} className="bg-white rounded-xl p-6 w-full max-w-sm shadow-2xl space-y-4">
            <h2 className="text-lg font-bold text-gray-900">Create Phased Replenishment</h2>
            <p className="text-sm text-gray-500">PO: <code>{phaseModal}</code></p>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Phase Weeks (comma-separated)</label>
              <input data-testid="phase-weeks-input" value={phaseWeeks} onChange={e => setPhaseWeeks(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="0,2,4" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Phase Percentages (must sum to 100)</label>
              <input data-testid="phase-pcts-input" value={phasePcts} onChange={e => setPhasePcts(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="50,30,20" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setPhaseModal(null)} className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50">Cancel</button>
              <button data-testid="create-phase-btn" onClick={createPhasedPO}
                className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">Create Phases</button>
            </div>
          </div>
        </div>
      )}

      {/* Promotion Create Modal */}
      {promoModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setPromoModal(false)}>
          <div data-testid="promo-modal" onClick={e => e.stopPropagation()} className="bg-white rounded-xl p-6 w-full max-w-md shadow-2xl space-y-3 max-h-[85vh] overflow-y-auto">
            <h2 className="text-lg font-bold text-gray-900">Add Promotion</h2>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Promotion Name</label>
              <input data-testid="promo-name" value={newPromo.name} onChange={e => setNewPromo(p => ({ ...p, name: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="Summer Sale 2026" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
                <select data-testid="promo-type" value={newPromo.promo_type} onChange={e => setNewPromo(p => ({ ...p, promo_type: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
                  <option value="national">National</option>
                  <option value="regional">Regional</option>
                  <option value="store">Store</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Discount Type</label>
                <select data-testid="promo-discount-type" value={newPromo.discount_type} onChange={e => setNewPromo(p => ({ ...p, discount_type: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
                  <option value="percentage">Percentage</option>
                  <option value="fixed">Fixed Amount</option>
                  <option value="bogo">Buy One Get One</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Start Date</label>
                <input data-testid="promo-start" type="date" value={newPromo.start_date} onChange={e => setNewPromo(p => ({ ...p, start_date: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">End Date</label>
                <input data-testid="promo-end" type="date" value={newPromo.end_date} onChange={e => setNewPromo(p => ({ ...p, end_date: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Discount Value</label>
                <input data-testid="promo-discount-val" type="number" value={newPromo.discount_value} onChange={e => setNewPromo(p => ({ ...p, discount_value: parseFloat(e.target.value) || 0 }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Lift Factor</label>
                <input data-testid="promo-lift" type="number" step="0.1" min="0.5" max="5" value={newPromo.lift_factor}
                  onChange={e => setNewPromo(p => ({ ...p, lift_factor: parseFloat(e.target.value) || 1 }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Affected Categories (comma-separated)</label>
              <input data-testid="promo-categories" value={newPromo.affected_categories} onChange={e => setNewPromo(p => ({ ...p, affected_categories: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="Apparel, Footwear" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
              <input value={newPromo.notes} onChange={e => setNewPromo(p => ({ ...p, notes: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="Optional notes" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setPromoModal(false)} className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50">Cancel</button>
              <button data-testid="save-promo-btn" onClick={createPromotion}
                className="px-4 py-2 text-sm bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C]">Create Promotion</button>
            </div>
          </div>
        </div>
      )}

      {/* Approval History Modal */}
      {showHistory && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowHistory(false)}>
          <div data-testid="approval-history-modal" onClick={e => e.stopPropagation()} className="bg-white rounded-xl p-6 w-full max-w-lg shadow-2xl space-y-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-900">Approval History</h2>
              <button onClick={() => setShowHistory(false)} className="text-gray-400 hover:text-gray-600"><X className="h-5 w-5" /></button>
            </div>
            {approvalHistory.length > 0 ? (
              <div className="space-y-3">
                {approvalHistory.map((h, i) => (
                  <div key={i} className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-white text-xs ${
                        h.action === "reject" ? "bg-red-500" :
                        h.action === "request_changes" ? "bg-amber-500" :
                        "bg-emerald-500"
                      }`}>
                        {h.action === "reject" ? <X className="h-3 w-3" /> :
                         h.action === "request_changes" ? <RotateCcw className="h-3 w-3" /> :
                         <CheckCircle2 className="h-3 w-3" />}
                      </div>
                      {i < approvalHistory.length - 1 && <div className="w-0.5 flex-1 bg-gray-200 mt-1" />}
                    </div>
                    <div className="flex-1 pb-3">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-900">{h.action.replace(/_/g, " ")}</span>
                        <span className="text-[10px] text-gray-400">{h.from_status} {"\u2192"} {h.to_status}</span>
                      </div>
                      <p className="text-xs text-gray-500">by {h.performed_by} {"\u2022"} {h.performed_at ? new Date(h.performed_at).toLocaleString() : ""}</p>
                      {h.comment && <p className="text-xs text-gray-600 mt-1 bg-gray-50 rounded p-2">{h.comment}</p>}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400 text-center py-8">No approval actions yet.</p>
            )}
          </div>
        </div>
      )}

      {/* Store Attribute Edit Modal */}
      {storeEditModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setStoreEditModal(null)}>
          <div data-testid="store-edit-modal" onClick={e => e.stopPropagation()} className="bg-white rounded-xl p-6 w-full max-w-sm shadow-2xl space-y-4">
            <h2 className="text-lg font-bold text-gray-900">Edit Store Attributes</h2>
            <p className="text-sm text-gray-500">Store: <code className="bg-gray-100 px-1 rounded">{storeEditModal.store_code}</code> {storeEditModal.store_name}</p>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Store Format</label>
                <select data-testid="edit-store-format" defaultValue={storeEditModal.store_format || ""} id="edit-fmt"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
                  <option value="hypermarket">Hypermarket</option>
                  <option value="supermarket">Supermarket</option>
                  <option value="convenience">Convenience</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">City Tier</label>
                <select data-testid="edit-city-tier" defaultValue={storeEditModal.city_tier || ""} id="edit-tier"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
                  <option value="tier1">Tier 1</option>
                  <option value="tier2">Tier 2</option>
                  <option value="tier3">Tier 3</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Region</label>
                <select data-testid="edit-region" defaultValue={storeEditModal.region || ""} id="edit-region"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
                  <option value="North">North</option>
                  <option value="South">South</option>
                  <option value="East">East</option>
                  <option value="West">West</option>
                  <option value="Central">Central</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Area (sqft)</label>
                <input data-testid="edit-area" type="number" defaultValue={storeEditModal.area_sqft || ""} id="edit-area"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setStoreEditModal(null)} className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50">Cancel</button>
              <button data-testid="save-store-attrs-btn" onClick={() => {
                const fmt = document.getElementById("edit-fmt").value;
                const tier = document.getElementById("edit-tier").value;
                const region = document.getElementById("edit-region").value;
                const area = document.getElementById("edit-area").value;
                updateStoreAttrs(storeEditModal.store_code, {
                  store_format: fmt, city_tier: tier, region: region,
                  ...(area ? { area_sqft: parseInt(area) } : {}),
                });
              }} className="px-4 py-2 text-sm bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C]">Save Attributes</button>
            </div>
          </div>
        </div>
      )}

      {/* Exclusion Management Modal */}
      {exclusionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setExclusionModal(false)}>
          <div data-testid="exclusion-modal" onClick={e => e.stopPropagation()} className="bg-white rounded-xl p-6 w-full max-w-lg shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-900">Manage Exclusions</h2>
              <button onClick={() => setExclusionModal(false)} className="text-gray-400 hover:text-gray-600"><X className="h-5 w-5" /></button>
            </div>
            <p className="text-sm text-gray-500">Excluded store-SKU pairs are skipped during buy plan generation.</p>

            {/* Add new exclusion */}
            <div className="bg-gray-50 rounded-lg p-3 space-y-2">
              <p className="text-xs font-medium text-gray-600">Add Exclusion</p>
              <div className="flex gap-2">
                <input data-testid="excl-store-input" placeholder="Store code" value={newExclusion.store_code}
                  onChange={e => setNewExclusion(p => ({ ...p, store_code: e.target.value }))}
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
                <input data-testid="excl-sku-input" placeholder="SKU / EAN" value={newExclusion.sku}
                  onChange={e => setNewExclusion(p => ({ ...p, sku: e.target.value }))}
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
              </div>
              <div className="flex gap-2">
                <input data-testid="excl-reason-input" placeholder="Reason" value={newExclusion.reason}
                  onChange={e => setNewExclusion(p => ({ ...p, reason: e.target.value }))}
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
                <button data-testid="add-exclusion-btn" onClick={addExclusion}
                  className="inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C]">
                  <Plus className="h-3.5 w-3.5" /> Add
                </button>
              </div>
            </div>

            {/* Exclusion list */}
            {exclusions.length > 0 ? (
              <div className="border border-gray-200 rounded-lg overflow-hidden max-h-60 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="text-left p-2 font-medium text-gray-600">Store</th>
                      <th className="text-left p-2 font-medium text-gray-600">SKU</th>
                      <th className="text-left p-2 font-medium text-gray-600">Reason</th>
                      <th className="w-10"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {exclusions.map((ex, i) => (
                      <tr key={i} className="border-t border-gray-100">
                        <td className="p-2 font-mono text-xs">{ex.store_code}</td>
                        <td className="p-2 font-mono text-xs">{ex.sku}</td>
                        <td className="p-2 text-xs text-gray-500">{ex.reason || "\u2014"}</td>
                        <td className="p-2">
                          <button onClick={() => removeExclusion(ex.store_code, ex.sku)} className="text-red-400 hover:text-red-600">
                            <X className="h-3.5 w-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-gray-400 text-center py-4">No exclusions. All store-SKU pairs will be included in buy plans.</p>
            )}
          </div>
        </div>
      )}

      {/* Override Modal */}
      {overrideModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setOverrideModal(null)}>
          <div data-testid="override-modal" onClick={e => e.stopPropagation()} className="bg-white rounded-xl p-6 w-full max-w-sm shadow-2xl space-y-4">
            <h2 className="text-lg font-bold text-gray-900">
              Override {overrideModal.type === "store" ? "Store Wedge" : "Style Mix"}
            </h2>
            <p className="text-sm text-gray-500">
              {overrideModal.type === "store" ? "Store" : "Style"}: <code className="bg-gray-100 px-1 rounded">{overrideModal.id}</code>
              &nbsp;(current: <strong>{overrideModal.current || "—"}</strong>)
            </p>
            <select data-testid="override-value" value={overrideValue} onChange={e => setOverrideValue(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
              {overrideModal.type === "store"
                ? ["A", "B", "C"].map(v => <option key={v} value={v}>{v} — {v === "A" ? "Full assortment" : v === "B" ? "Standard" : "Core only"}</option>)
                : ["Core", "Fashion", "Test"].map(v => <option key={v} value={v}>{v}</option>)
              }
            </select>
            <input data-testid="override-reason" placeholder="Reason (e.g., new flagship store)" value={overrideReason}
              onChange={e => setOverrideReason(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setOverrideModal(null)} className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50">Cancel</button>
              <button data-testid="submit-override" onClick={submitOverride}
                className="px-4 py-2 text-sm bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C]">Apply Override</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
