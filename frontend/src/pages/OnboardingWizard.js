import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  Globe, Store, CheckCircle, ArrowRight, ArrowLeft,
  Plus, Trash2, X, AlertCircle, Loader2, Package
} from "lucide-react";

const CURRENCY_OPTIONS = [
  { value: "INR", label: "INR" },
  { value: "USD", label: "USD" },
  { value: "GBP", label: "GBP" },
  { value: "EUR", label: "EUR" },
];

const TYPE_OPTIONS = [
  { value: "marketplace", label: "Marketplace" },
  { value: "website", label: "Own Website" },
  { value: "social_commerce", label: "Social Commerce" },
];

const STORE_TYPES = [
  { value: "physical", label: "Physical Store" },
  { value: "warehouse", label: "Warehouse" },
  { value: "dark_store", label: "Dark Store" },
];

const STEP_META = [
  { num: 1, label: "Marketplaces", icon: Globe },
  { num: 2, label: "Stores", icon: Store },
  { num: 3, label: "Categories", icon: Package },
];

/* ═══════════════════════════════════════════════════════ */

export default function OnboardingWizard({ onComplete }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState(null);

  // Step 1
  const [marketplaces, setMarketplaces] = useState([]);
  const [showMpForm, setShowMpForm] = useState(false);
  const [mpForm, setMpForm] = useState({ name: "", currency: "INR", tax_rate: 18, commission_percentage: 0, type: "marketplace" });

  // Step 2
  const [stores, setStores] = useState([]);
  const [showStoreForm, setShowStoreForm] = useState(false);
  const [storeForm, setStoreForm] = useState({ store_code: "", store_name: "", type: "physical", city: "", state: "", pincode: "", marketplaces: [] });

  // Step 3
  const [categories, setCategories] = useState([]);
  const [showCatForm, setShowCatForm] = useState(false);
  const [catForm, setCatForm] = useState({ name: "", parent_id: null, description: "" });

  /* ── Loaders ── */
  const loadStatus = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/onboarding/status`);
      setStatus(data);
      // When fully onboarded (step 4), default to step 1 for review/reconfiguration
      setStep(data.current_step >= 4 ? 1 : data.current_step || 1);
      // Always try loading existing data for review
      loadMarketplaces();
      loadStores();
      loadCategories();
    } catch { setError("Failed to load onboarding status"); }
  }, []);

  const loadMarketplaces = async () => { try { const { data } = await axios.get(`${API}/onboarding/marketplaces`); setMarketplaces(data); } catch {} };
  const loadStores      = async () => { try { const { data } = await axios.get(`${API}/onboarding/stores`); setStores(data); } catch {} };
  const loadCategories  = async () => { try { const { data } = await axios.get(`${API}/onboarding/categories/tree`); setCategories(data); } catch {} };

  useEffect(() => { loadStatus(); }, [loadStatus]);

  const refreshStatus = async () => { const { data } = await axios.get(`${API}/onboarding/status`); setStatus(data); return data; };

  /* ── Actions ── */
  const addMarketplace = async () => {
    setLoading(true); setError(null);
    try {
      await axios.post(`${API}/onboarding/marketplaces`, mpForm);
      await loadMarketplaces();
      setShowMpForm(false);
      setMpForm({ name: "", currency: "INR", tax_rate: 18, commission_percentage: 0, type: "marketplace" });
      await refreshStatus();
    } catch (e) { setError(e.response?.data?.detail || "Failed to add marketplace"); }
    setLoading(false);
  };

  const delMarketplace = async (id) => {
    if (!window.confirm("Delete this marketplace?")) return;
    setLoading(true);
    try { await axios.delete(`${API}/onboarding/marketplaces/${id}`); await loadMarketplaces(); await refreshStatus(); } catch { setError("Delete failed"); }
    setLoading(false);
  };

  const addStore = async () => {
    setLoading(true); setError(null);
    try {
      await axios.post(`${API}/onboarding/stores`, storeForm);
      await loadStores();
      setShowStoreForm(false);
      setStoreForm({ store_code: "", store_name: "", type: "physical", city: "", state: "", pincode: "", marketplaces: [] });
      await refreshStatus();
    } catch (e) { setError(e.response?.data?.detail || "Failed to add store"); }
    setLoading(false);
  };

  const delStore = async (code) => {
    if (!window.confirm("Delete this store?")) return;
    setLoading(true);
    try { await axios.delete(`${API}/onboarding/stores/${code}`); await loadStores(); await refreshStatus(); } catch { setError("Delete failed"); }
    setLoading(false);
  };

  const addCategory = async () => {
    setLoading(true); setError(null);
    try {
      await axios.post(`${API}/onboarding/categories`, catForm);
      await loadCategories();
      setShowCatForm(false);
      setCatForm({ name: "", parent_id: null, description: "" });
      await refreshStatus();
    } catch (e) { setError(e.response?.data?.detail || "Failed to add category"); }
    setLoading(false);
  };

  const delCategory = async (id) => {
    if (!window.confirm("Delete this category and all children?")) return;
    setLoading(true);
    try { await axios.delete(`${API}/onboarding/categories/${id}`); await loadCategories(); await refreshStatus(); } catch { setError("Delete failed"); }
    setLoading(false);
  };

  const skipStep = async () => {
    if (!window.confirm("Skip this step? You can configure it later.")) return;
    setLoading(true);
    try {
      await axios.post(`${API}/onboarding/skip?step=${step}`);
      const s = await refreshStatus();
      setStep(s.current_step);
    } catch { setError("Skip failed"); }
    setLoading(false);
  };

  const completeOnboarding = async () => {
    setLoading(true); setError(null);
    try {
      await axios.post(`${API}/onboarding/complete`);
      if (onComplete) onComplete();
    } catch (e) { setError(e.response?.data?.detail || "Cannot complete onboarding"); }
    setLoading(false);
  };

  /* ── Flatten categories helper ── */
  const flatten = (nodes, lvl = 0, out = []) => {
    for (const n of nodes) { out.push({ ...n, _lvl: lvl }); if (n.children) flatten(n.children, lvl + 1, out); }
    return out;
  };

  /* ══════════════════════════════════════════════════════════════ */
  /* STEP 1 — Marketplaces                                        */
  /* ══════════════════════════════════════════════════════════════ */
  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div data-testid="step1-icon" className="w-16 h-16 bg-[#E8F0FE] rounded-full flex items-center justify-center mx-auto mb-4">
          <Globe className="h-8 w-8 text-[#0176D3]" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900">Where do you sell?</h2>
        <p className="text-slate-500 mt-2">Add all marketplaces where you sell your products</p>
      </div>

      {marketplaces.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-medium text-slate-700">Your Marketplaces ({marketplaces.length})</h3>
          {marketplaces.map(m => (
            <div key={m.marketplace_id} data-testid={`mp-${m.marketplace_id}`} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center"><Globe className="h-5 w-5 text-blue-600" /></div>
                <div>
                  <p className="font-medium text-slate-800">{m.name}</p>
                  <p className="text-sm text-slate-500">{m.currency} | Tax: {m.tax_rate}% | Commission: {m.commission_percentage}%</p>
                </div>
              </div>
              <button data-testid={`del-mp-${m.marketplace_id}`} onClick={() => delMarketplace(m.marketplace_id)} className="p-1.5 text-slate-400 hover:text-red-500 rounded hover:bg-red-50 transition-colors"><Trash2 className="h-4 w-4" /></button>
            </div>
          ))}
        </div>
      )}

      {!showMpForm ? (
        <button data-testid="add-mp-btn" onClick={() => setShowMpForm(true)} className="w-full py-3 border-2 border-dashed border-slate-300 rounded-lg text-slate-500 hover:border-[#0176D3] hover:text-[#0176D3] flex items-center justify-center gap-2 transition-colors">
          <Plus className="h-5 w-5" /> Add Marketplace
        </button>
      ) : (
        <div data-testid="mp-form" className="border border-slate-200 rounded-lg p-4 space-y-3 bg-slate-50">
          <div className="flex justify-between items-center"><h3 className="font-medium text-slate-800">Add New Marketplace</h3><button onClick={() => setShowMpForm(false)} className="text-slate-400 hover:text-slate-600"><X className="h-4 w-4" /></button></div>
          <input data-testid="mp-name" type="text" placeholder="Marketplace Name (e.g., Amazon India)" className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-[#0176D3] focus:border-transparent outline-none" value={mpForm.name} onChange={(e) => setMpForm({ ...mpForm, name: e.target.value })} />
          <div className="grid grid-cols-2 gap-3">
            <select data-testid="mp-currency" className="px-3 py-2 border border-slate-200 rounded-lg text-sm" value={mpForm.currency} onChange={(e) => setMpForm({ ...mpForm, currency: e.target.value })}>
              {CURRENCY_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <select data-testid="mp-type" className="px-3 py-2 border border-slate-200 rounded-lg text-sm" value={mpForm.type} onChange={(e) => setMpForm({ ...mpForm, type: e.target.value })}>
              {TYPE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input data-testid="mp-tax" type="number" placeholder="Tax Rate %" className="px-3 py-2 border border-slate-200 rounded-lg text-sm" value={mpForm.tax_rate} onChange={(e) => setMpForm({ ...mpForm, tax_rate: parseFloat(e.target.value) || 0 })} />
            <input data-testid="mp-comm" type="number" placeholder="Commission %" className="px-3 py-2 border border-slate-200 rounded-lg text-sm" value={mpForm.commission_percentage} onChange={(e) => setMpForm({ ...mpForm, commission_percentage: parseFloat(e.target.value) || 0 })} />
          </div>
          <button data-testid="mp-submit" onClick={addMarketplace} disabled={!mpForm.name || loading} className="w-full py-2 bg-[#0176D3] text-white rounded-lg hover:bg-[#015CA8] flex items-center justify-center gap-2 disabled:opacity-50 text-sm font-medium transition-colors">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />} Add Marketplace
          </button>
        </div>
      )}

      <div className="flex justify-between gap-3 pt-4 border-t border-slate-100">
        <button data-testid="skip-step1" onClick={skipStep} className="px-4 py-2 text-slate-500 hover:text-slate-700 text-sm">Skip for now</button>
        <button data-testid="next-step2" onClick={() => setStep(2)} disabled={marketplaces.length === 0} className="px-6 py-2.5 bg-[#0176D3] text-white rounded-lg hover:bg-[#015CA8] flex items-center gap-2 disabled:opacity-50 text-sm font-medium transition-colors">
          Next: Add Stores <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );

  /* ══════════════════════════════════════════════════════════════ */
  /* STEP 2 — Stores                                               */
  /* ══════════════════════════════════════════════════════════════ */
  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div data-testid="step2-icon" className="w-16 h-16 bg-[#E8F0FE] rounded-full flex items-center justify-center mx-auto mb-4">
          <Store className="h-8 w-8 text-[#0176D3]" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900">Where is your inventory?</h2>
        <p className="text-slate-500 mt-2">Add stores and warehouses, then map them to marketplaces</p>
      </div>

      {stores.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-medium text-slate-700">Your Locations ({stores.length})</h3>
          {stores.map(s => (
            <div key={s.store_code} data-testid={`store-${s.store_code}`} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${s.type === "warehouse" ? "bg-purple-100" : "bg-green-100"}`}>
                    {s.type === "warehouse" ? <Package className="h-5 w-5 text-purple-600" /> : <Store className="h-5 w-5 text-green-600" />}
                  </div>
                  <div>
                    <p className="font-medium text-slate-800">{s.store_name}</p>
                    <p className="text-sm text-slate-500">{s.store_code} | {s.city}, {s.state}</p>
                  </div>
                </div>
                <button data-testid={`del-store-${s.store_code}`} onClick={() => delStore(s.store_code)} className="p-1.5 text-slate-400 hover:text-red-500 rounded hover:bg-red-50"><Trash2 className="h-4 w-4" /></button>
              </div>
              {s.marketplaces?.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {s.marketplaces.map(m => <span key={m} className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full text-xs">{m}</span>)}
                </div>
              )}
              {(!s.marketplaces || s.marketplaces.length === 0) && <p className="mt-1.5 text-xs text-slate-400">Not mapped to any marketplace</p>}
            </div>
          ))}
        </div>
      )}

      {!showStoreForm ? (
        <button data-testid="add-store-btn" onClick={() => setShowStoreForm(true)} className="w-full py-3 border-2 border-dashed border-slate-300 rounded-lg text-slate-500 hover:border-[#0176D3] hover:text-[#0176D3] flex items-center justify-center gap-2 transition-colors">
          <Plus className="h-5 w-5" /> Add Store or Warehouse
        </button>
      ) : (
        <div data-testid="store-form" className="border border-slate-200 rounded-lg p-4 space-y-3 bg-slate-50">
          <div className="flex justify-between items-center"><h3 className="font-medium text-slate-800">Add New Store/Warehouse</h3><button onClick={() => setShowStoreForm(false)}><X className="h-4 w-4 text-slate-400" /></button></div>
          <div className="grid grid-cols-2 gap-3">
            <input data-testid="store-code" type="text" placeholder="Store Code" className="px-3 py-2 border border-slate-200 rounded-lg text-sm" value={storeForm.store_code} onChange={(e) => setStoreForm({ ...storeForm, store_code: e.target.value.toUpperCase() })} />
            <input data-testid="store-name" type="text" placeholder="Store Name" className="px-3 py-2 border border-slate-200 rounded-lg text-sm" value={storeForm.store_name} onChange={(e) => setStoreForm({ ...storeForm, store_name: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <select data-testid="store-type" className="px-3 py-2 border border-slate-200 rounded-lg text-sm" value={storeForm.type} onChange={(e) => setStoreForm({ ...storeForm, type: e.target.value })}>
              {STORE_TYPES.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <input data-testid="store-city" type="text" placeholder="City" className="px-3 py-2 border border-slate-200 rounded-lg text-sm" value={storeForm.city} onChange={(e) => setStoreForm({ ...storeForm, city: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input data-testid="store-state" type="text" placeholder="State" className="px-3 py-2 border border-slate-200 rounded-lg text-sm" value={storeForm.state} onChange={(e) => setStoreForm({ ...storeForm, state: e.target.value })} />
            <input data-testid="store-pincode" type="text" placeholder="Pincode" className="px-3 py-2 border border-slate-200 rounded-lg text-sm" value={storeForm.pincode} onChange={(e) => setStoreForm({ ...storeForm, pincode: e.target.value })} />
          </div>
          {marketplaces.length > 0 && (
            <>
              <select data-testid="store-mp-select" multiple className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm min-h-[80px]" value={storeForm.marketplaces} onChange={(e) => setStoreForm({ ...storeForm, marketplaces: Array.from(e.target.selectedOptions, o => o.value) })}>
                {marketplaces.map(m => <option key={m.marketplace_id} value={m.name}>{m.name}</option>)}
              </select>
              <p className="text-xs text-slate-500">Hold Ctrl/Cmd to select multiple</p>
            </>
          )}
          <button data-testid="store-submit" onClick={addStore} disabled={!storeForm.store_code || !storeForm.store_name || loading} className="w-full py-2 bg-[#0176D3] text-white rounded-lg hover:bg-[#015CA8] flex items-center justify-center gap-2 disabled:opacity-50 text-sm font-medium">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />} Add Store
          </button>
        </div>
      )}

      <div className="flex justify-between gap-3 pt-4 border-t border-slate-100">
        <button data-testid="back-step1" onClick={() => setStep(1)} className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 flex items-center gap-2 text-sm"><ArrowLeft className="h-4 w-4" /> Back</button>
        <div className="flex gap-3">
          <button data-testid="skip-step2" onClick={skipStep} className="px-4 py-2 text-slate-500 hover:text-slate-700 text-sm">Skip</button>
          <button data-testid="next-step3" onClick={() => setStep(3)} disabled={stores.length === 0} className="px-6 py-2.5 bg-[#0176D3] text-white rounded-lg hover:bg-[#015CA8] flex items-center gap-2 disabled:opacity-50 text-sm font-medium">
            Next: Categories <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );

  /* ══════════════════════════════════════════════════════════════ */
  /* STEP 3 — Category Taxonomy                                    */
  /* ══════════════════════════════════════════════════════════════ */
  const renderCategoryTree = (nodes, level = 0) => nodes.map(n => (
    <div key={n.category_id} style={{ marginLeft: level * 24 }} className="py-0.5 group">
      <div className="flex items-center justify-between p-1.5 hover:bg-slate-50 rounded">
        <div className="flex items-center gap-2 text-sm">
          <Package className="h-3.5 w-3.5 text-slate-400" />
          <span className="font-medium text-slate-800">{n.name}</span>
          <span className="text-xs text-slate-400">({n.category_id})</span>
        </div>
        <button data-testid={`del-cat-${n.category_id}`} onClick={() => delCategory(n.category_id)} className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-500 p-0.5"><Trash2 className="h-3 w-3" /></button>
      </div>
      {n.children && renderCategoryTree(n.children, level + 1)}
    </div>
  ));

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div data-testid="step3-icon" className="w-16 h-16 bg-[#E8F0FE] rounded-full flex items-center justify-center mx-auto mb-4">
          <Package className="h-8 w-8 text-[#0176D3]" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900">Build your product hierarchy</h2>
        <p className="text-slate-500 mt-2">Create categories like Apparel &rarr; Men &rarr; Jeans &rarr; Slim Fit</p>
      </div>

      {categories.length > 0 && (
        <div data-testid="category-tree" className="border border-slate-200 rounded-lg p-4 max-h-80 overflow-y-auto bg-slate-50">
          <h3 className="font-medium text-slate-700 mb-2">Your Category Tree ({flatten(categories).length} total)</h3>
          {renderCategoryTree(categories)}
        </div>
      )}

      {!showCatForm ? (
        <button data-testid="add-cat-btn" onClick={() => setShowCatForm(true)} className="w-full py-3 border-2 border-dashed border-slate-300 rounded-lg text-slate-500 hover:border-[#0176D3] hover:text-[#0176D3] flex items-center justify-center gap-2 transition-colors">
          <Plus className="h-5 w-5" /> Add Category
        </button>
      ) : (
        <div data-testid="cat-form" className="border border-slate-200 rounded-lg p-4 space-y-3 bg-slate-50">
          <div className="flex justify-between items-center"><h3 className="font-medium text-slate-800">Add New Category</h3><button onClick={() => setShowCatForm(false)}><X className="h-4 w-4 text-slate-400" /></button></div>
          <input data-testid="cat-name" type="text" placeholder="Category Name (e.g., Jeans, T-Shirts)" className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" value={catForm.name} onChange={(e) => setCatForm({ ...catForm, name: e.target.value })} />
          <textarea data-testid="cat-desc" placeholder="Description (optional)" className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" rows="2" value={catForm.description} onChange={(e) => setCatForm({ ...catForm, description: e.target.value })} />
          <select data-testid="cat-parent" className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" value={catForm.parent_id || ""} onChange={(e) => setCatForm({ ...catForm, parent_id: e.target.value || null })}>
            <option value="">Root Category (Top Level)</option>
            {flatten(categories).map(c => <option key={c.category_id} value={c.category_id}>{"  ".repeat(c._lvl)} {c.name}</option>)}
          </select>
          <button data-testid="cat-submit" onClick={addCategory} disabled={!catForm.name || loading} className="w-full py-2 bg-[#0176D3] text-white rounded-lg hover:bg-[#015CA8] flex items-center justify-center gap-2 disabled:opacity-50 text-sm font-medium">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />} Add Category
          </button>
        </div>
      )}

      <div className="flex justify-between gap-3 pt-4 border-t border-slate-100">
        <button data-testid="back-step2" onClick={() => setStep(2)} className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 flex items-center gap-2 text-sm"><ArrowLeft className="h-4 w-4" /> Back</button>
        <div className="flex gap-3">
          <button data-testid="skip-step3" onClick={skipStep} className="px-4 py-2 text-slate-500 hover:text-slate-700 text-sm">Skip</button>
          <button data-testid="complete-onboarding-btn" onClick={completeOnboarding} disabled={flatten(categories).length < 3 || loading} className="px-6 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2 disabled:opacity-50 text-sm font-medium transition-colors">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />} Complete Setup
          </button>
        </div>
      </div>
    </div>
  );

  /* ══════════════════════════════════════════════════════════════ */
  /* Main Layout                                                   */
  /* ══════════════════════════════════════════════════════════════ */
  return (
    <div data-testid="onboarding-wizard" className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-12">
      <div className="max-w-2xl mx-auto px-4">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Welcome to Merchandising Platform</h1>
          <p className="text-slate-500">Let's get your store configured in 3 simple steps</p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex justify-between">
            {STEP_META.map(({ num, label, icon: Icon }) => (
              <div key={num} className="flex-1 text-center">
                <div className={`w-10 h-10 rounded-full mx-auto flex items-center justify-center transition-all ${step >= num ? "bg-[#0176D3] text-white shadow-lg" : "bg-slate-200 text-slate-500"}`}>
                  {step > num ? <CheckCircle className="h-5 w-5" /> : <Icon className="h-5 w-5" />}
                </div>
                <p className={`text-xs mt-2 font-medium ${step >= num ? "text-[#0176D3]" : "text-slate-400"}`}>{label}</p>
              </div>
            ))}
          </div>
          <div className="mt-4 h-2 bg-slate-200 rounded-full overflow-hidden">
            <div data-testid="progress-bar" className="h-full bg-[#0176D3] transition-all duration-500 rounded-full" style={{ width: `${status?.progress_percentage || 0}%` }} />
          </div>
        </div>

        {error && (
          <div data-testid="onboarding-error" className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-600 text-sm">
            <AlertCircle className="h-4 w-4 flex-shrink-0" /><span>{error}</span>
            <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600"><X className="h-3.5 w-3.5" /></button>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-8">
          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}
        </div>
      </div>
    </div>
  );
}
