import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  Save, RefreshCw, Plus, Pencil, Trash2, ChevronDown, ChevronRight,
  AlertCircle, CheckCircle, Store, Tag, Sliders, ToggleLeft
} from "lucide-react";

const Configuration = () => {
  const [activeTab, setActiveTab] = useState("params");
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState(null);
  const [storeClasses, setStoreClasses] = useState([]);
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      axios.get(`${API}/config`),
      axios.get(`${API}/config/store-classes`).catch(() => ({ data: { classes: [] } })),
      axios.get(`${API}/config/categories`).catch(() => ({ data: { categories: [] } })),
    ]).then(([cfgR, scR, catR]) => {
      setConfig(cfgR.data);
      setStoreClasses(scR.data.classes || []);
      setCategories(catR.data.categories || []);
    }).catch(() => setMsg({ type: "error", text: "Failed to load config" }))
      .finally(() => setLoading(false));
  }, []);

  const flash = (text, type) => {
    setMsg({ type, text });
    setTimeout(() => setMsg(null), 4000);
  };

  const saveConfig = async () => {
    setSaving(true);
    try {
      await axios.post(`${API}/config`, config);
      flash("Configuration saved", "success");
    } catch (err) {
      const d = err.response?.data?.detail;
      flash(d?.errors ? d.errors.join("; ") : (d || "Save failed"), "error");
    } finally { setSaving(false); }
  };

  const up = (k, v) => setConfig(p => ({ ...p, [k]: v }));

  if (loading || !config) return <div className="flex items-center justify-center py-20"><div className="spinner" /></div>;

  const tabs = [
    { id: "params", label: "Parameters", Icon: Sliders },
    { id: "modules", label: "Modules", Icon: ToggleLeft },
    { id: "stores", label: "Store Classes", Icon: Store },
    { id: "categories", label: "Categories", Icon: Tag },
  ];

  return (
    <div className="animate-fade-in-up" data-testid="configuration-page">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Configuration</h1>
          <p className="text-slate-500">Manage analysis parameters, modules, store classes, and categories</p>
        </div>
        <div className="flex items-center gap-3">
          {activeTab === "params" || activeTab === "modules" ? (
            <button onClick={saveConfig} disabled={saving} data-testid="save-config-btn" className="btn-primary flex items-center gap-2">
              {saving ? <RefreshCw size={16} className="animate-spin" /> : <Save size={16} />} Save Parameters & Modules
            </button>
          ) : (
            <span className="text-xs text-slate-400 italic">Changes to {activeTab === "stores" ? "Store Classes" : "Categories"} are saved individually</span>
          )}
        </div>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-3 rounded-lg flex items-center gap-2 text-sm border ${msg.type === "success" ? "bg-green-50 border-green-200 text-green-700" : "bg-red-50 border-red-200 text-red-700"}`} data-testid={msg.type === "success" ? "config-success" : "config-error"}>
          {msg.type === "success" ? <CheckCircle size={16} /> : <AlertCircle size={16} />} {msg.text}
        </div>
      )}

      <div className="flex gap-1 mb-6 border-b border-slate-200">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} data-testid={`tab-${t.id}`}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${activeTab === t.id ? "border-[#0176D3] text-[#0176D3]" : "border-transparent text-slate-500 hover:text-slate-700"}`}>
            <t.Icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      {activeTab === "params" && <ParamsTab config={config} up={up} />}
      {activeTab === "modules" && <ModulesTab config={config} up={up} />}
      {activeTab === "stores" && <StoreClassesTab classes={storeClasses} setClasses={setStoreClasses} flash={flash} />}
      {activeTab === "categories" && <CategoriesTab categories={categories} setCategories={setCategories} flash={flash} />}
    </div>
  );
};

const PF = ({ testId, label, desc, value, onChange, min, max, step, unit, integer }) => {
  const handleChange = (raw) => {
    const num = parseFloat(raw);
    if (isNaN(num)) return;
    const clamped = Math.min(max, Math.max(min, num));
    onChange(integer ? Math.round(clamped) : clamped);
  };
  const err = (() => {
    if (value < min) return `Min ${min}`;
    if (value > max) return `Max ${max}`;
    if (integer && String(value).includes(".")) return "Whole number";
    return null;
  })();

  return (
    <div data-testid={testId}>
      <div className="flex items-center justify-between mb-1">
        <label className="text-sm font-medium text-slate-700">{label}</label>
        <span className="text-xs text-slate-400">{min}–{max} {unit}</span>
      </div>
      <p className="text-xs text-slate-400 mb-2">{desc}</p>
      <div className="flex items-center gap-3">
        <input type="range" min={min} max={max} step={step} value={value} onChange={e => handleChange(e.target.value)} className="flex-1 accent-[#0176D3]" />
        <input type="number" min={min} max={max} step={step} value={value} onChange={e => handleChange(e.target.value)}
          data-testid={`${testId}-input`} className={`w-20 filter-input text-center font-semibold ${err ? "border-red-300" : ""}`} />
        <span className="text-xs text-slate-500 w-8">{unit}</span>
      </div>
      {err && <p className="text-xs text-red-500 mt-1" data-testid={`${testId}-error`}>{err}</p>}
    </div>
  );
};

const ParamsTab = ({ config, up }) => (
  <div className="bg-white border border-slate-200 rounded-lg shadow-sm" data-testid="params-panel">
    <div className="p-4 border-b border-slate-100">
      <h2 className="font-semibold text-slate-900">Analysis Parameters</h2>
      <p className="text-xs text-slate-500 mt-1">These values drive all analytics calculations</p>
    </div>
    <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
      <PF testId="param-psa-benchmark" label="PSA Benchmark (%)" desc="Minimum size availability % to mark a style as healthy" value={config.pivotal_size_threshold} onChange={v => up("pivotal_size_threshold", v)} min={0} max={100} step={1} unit="%" integer />
      <PF testId="param-cover-days" label="Cover Days" desc="Number of days of stock cover for replenishment safety buffer" value={config.cover_days} onChange={v => up("cover_days", v)} min={1} max={90} step={1} unit="days" integer />
      <PF testId="param-ros-period" label="ROS Period" desc="Lookback window (in days) for calculating Rate of Sale" value={config.ros_period} onChange={v => up("ros_period", v)} min={7} max={365} step={1} unit="days" integer />
      <PF testId="param-ideal-doh" label="Ideal DOH" desc="Target Days on Hand — optimal inventory holding period" value={config.ideal_doh} onChange={v => up("ideal_doh", v)} min={1} max={90} step={1} unit="days" integer />
      <PF testId="param-topseller-x" label="Topseller X Factor" desc="Revenue multiplier threshold to classify top-selling SKUs" value={config.topseller_x_factor} onChange={v => up("topseller_x_factor", v)} min={0.5} max={10} step={0.1} unit="x" />
      <PF testId="param-lead-time" label="Lead Time Days" desc="Average supplier lead time for replenishment orders" value={config.lead_time_days} onChange={v => up("lead_time_days", v)} min={1} max={90} step={1} unit="days" integer />
      <PF testId="param-safety-days" label="Safety Stock Days" desc="Additional buffer days added on top of lead time" value={config.safety_days} onChange={v => up("safety_days", v)} min={0} max={30} step={1} unit="days" integer />
      <PF testId="param-shelf-life" label="Min Shelf Life Days" desc="Minimum days on shelf to qualify as Never-Out-of-Stock" value={config.min_shelf_life_days} onChange={v => up("min_shelf_life_days", v)} min={1} max={365} step={1} unit="days" integer />
    </div>
  </div>
);

const ToggleBtn = ({ testId, label, desc, on, toggle }) => (
  <div className="p-4 flex items-center justify-between" data-testid={testId}>
    <div><p className="text-sm font-medium text-slate-700">{label}</p><p className="text-xs text-slate-400">{desc}</p></div>
    <button onClick={() => toggle(!on)} data-testid={`${testId}-btn`}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${on ? "bg-[#0176D3]" : "bg-slate-300"}`}>
      <span className={`inline-block h-4 w-4 rounded-full bg-white shadow transition-transform ${on ? "translate-x-6" : "translate-x-1"}`} />
    </button>
  </div>
);

const ModulesTab = ({ config, up }) => (
  <div className="bg-white border border-slate-200 rounded-lg shadow-sm" data-testid="modules-panel">
    <div className="p-4 border-b border-slate-100">
      <h2 className="font-semibold text-slate-900">Module Toggles</h2>
      <p className="text-xs text-slate-500 mt-1">Enable or disable analytics modules</p>
    </div>
    <div className="divide-y divide-slate-100">
      <ToggleBtn testId="toggle-noos" label="NOOS Analysis" desc="Never Out of Stock — identifies must-have styles" on={config.noos_enabled} toggle={v => up("noos_enabled", v)} />
      <ToggleBtn testId="toggle-ros" label="ROS Gap Analysis" desc="Rate of Sale gap detection across stores" on={config.ros_enabled} toggle={v => up("ros_enabled", v)} />
      <ToggleBtn testId="toggle-size-gap" label="Size Set Gap" desc="Identifies missing sizes in store assortments" on={config.size_gap_enabled} toggle={v => up("size_gap_enabled", v)} />
      <ToggleBtn testId="toggle-lifecycle" label="Lifecycle Analysis" desc="Tracks product performance through intro, growth, and decline phases" on={config.lifecycle_enabled} toggle={v => up("lifecycle_enabled", v)} />
      <ToggleBtn testId="toggle-replenishment" label="Replenishment Planner" desc="Generates reorder suggestions based on demand and lead time" on={config.replenishment_enabled} toggle={v => up("replenishment_enabled", v)} />
    </div>
  </div>
);

const StoreClassesTab = ({ classes, setClasses, flash }) => {
  const [nw, setNw] = useState({ code: "", name: "", priority: "" });
  const [ed, setEd] = useState(null);

  const add = async () => {
    if (!nw.code || !nw.name) return flash("Code and name required", "error");
    try {
      await axios.post(`${API}/config/store-classes`, nw);
      setNw({ code: "", name: "", priority: "" });
      const r = await axios.get(`${API}/config/store-classes`);
      setClasses(r.data.classes || []);
      flash("Store class created", "success");
    } catch (e) { flash(e.response?.data?.detail || "Failed", "error"); }
  };
  const upd = async (code) => {
    try {
      await axios.put(`${API}/config/store-classes/${code}`, ed);
      setEd(null);
      const r = await axios.get(`${API}/config/store-classes`);
      setClasses(r.data.classes || []);
      flash("Updated", "success");
    } catch (e) { flash(e.response?.data?.detail || "Failed", "error"); }
  };
  const del = async (code) => {
    if (!window.confirm(`Delete "${code}"?`)) return;
    try {
      await axios.delete(`${API}/config/store-classes/${code}`);
      const r = await axios.get(`${API}/config/store-classes`);
      setClasses(r.data.classes || []);
      flash("Deleted", "success");
    } catch (e) { flash(e.response?.data?.detail || "Cannot delete", "error"); }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-sm" data-testid="store-classes-panel">
      <div className="p-4 border-b border-slate-100">
        <h2 className="font-semibold text-slate-900">Store Classification</h2>
        <p className="text-xs text-slate-500 mt-1">Define store classes and their priority ordering</p>
      </div>
      <div className="p-4 bg-slate-50 border-b border-slate-100 flex items-end gap-3">
        <div className="flex-1"><label className="text-xs text-slate-500 font-medium">Code</label>
          <input data-testid="new-class-code" value={nw.code} onChange={e => setNw(p => ({ ...p, code: e.target.value }))} className="filter-input mt-1" placeholder="D" /></div>
        <div className="flex-[2]"><label className="text-xs text-slate-500 font-medium">Name</label>
          <input data-testid="new-class-name" value={nw.name} onChange={e => setNw(p => ({ ...p, name: e.target.value }))} className="filter-input mt-1" placeholder="Discount Store" /></div>
        <div className="flex-1"><label className="text-xs text-slate-500 font-medium">Priority</label>
          <input data-testid="new-class-priority" type="number" value={nw.priority} onChange={e => setNw(p => ({ ...p, priority: e.target.value }))} className="filter-input mt-1" placeholder="4" /></div>
        <button onClick={add} data-testid="add-class-btn" className="btn-primary flex items-center gap-1 h-[38px]"><Plus size={14} /> Add</button>
      </div>
      <div className="divide-y divide-slate-100">
        {classes.length === 0 && <div className="p-6 text-center text-slate-400 text-sm">No store classes defined yet</div>}
        {classes.map(c => (
          <div key={c.code} className="p-4 flex items-center justify-between" data-testid={`class-${c.code}`}>
            {ed?.code === c.code ? (
              <div className="flex items-center gap-3 flex-1">
                <input value={ed.name} onChange={e => setEd(p => ({ ...p, name: e.target.value }))} className="filter-input" />
                <input type="number" value={ed.priority} onChange={e => setEd(p => ({ ...p, priority: e.target.value }))} className="filter-input w-20" />
                <button onClick={() => upd(c.code)} className="btn-primary text-xs px-3 py-1">Save</button>
                <button onClick={() => setEd(null)} className="text-xs text-slate-500">Cancel</button>
              </div>
            ) : (
              <><div><span className="font-mono text-sm font-bold text-slate-700 mr-3">{c.code}</span><span className="text-sm text-slate-600">{c.name}</span><span className="text-xs text-slate-400 ml-2">Priority: {c.priority}</span></div>
                <div className="flex items-center gap-2">
                  <button onClick={() => setEd({ ...c })} data-testid={`edit-class-${c.code}`} className="p-1.5 hover:bg-slate-100 rounded"><Pencil size={14} className="text-slate-400" /></button>
                  <button onClick={() => del(c.code)} data-testid={`delete-class-${c.code}`} className="p-1.5 hover:bg-red-50 rounded"><Trash2 size={14} className="text-red-400" /></button>
                </div></>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

const CategoriesTab = ({ categories, setCategories, flash }) => {
  const [nw, setNw] = useState({ code: "", name: "", parent: "" });
  const [ed, setEd] = useState(null);

  const add = async () => {
    if (!nw.code || !nw.name) return flash("Code and name required", "error");
    try {
      await axios.post(`${API}/config/categories`, nw);
      setNw({ code: "", name: "", parent: "" });
      const r = await axios.get(`${API}/config/categories`);
      setCategories(r.data.categories || []);
      flash("Category created", "success");
    } catch (e) { flash(e.response?.data?.detail || "Failed", "error"); }
  };
  const upd = async (code) => {
    try {
      await axios.put(`${API}/config/categories/${code}`, ed);
      setEd(null);
      const r = await axios.get(`${API}/config/categories`);
      setCategories(r.data.categories || []);
      flash("Updated", "success");
    } catch (e) { flash(e.response?.data?.detail || "Failed", "error"); }
  };
  const del = async (code) => {
    if (!window.confirm(`Delete "${code}"?`)) return;
    try {
      await axios.delete(`${API}/config/categories/${code}`);
      const r = await axios.get(`${API}/config/categories`);
      setCategories(r.data.categories || []);
      flash("Deleted", "success");
    } catch (e) { flash(e.response?.data?.detail || "Cannot delete", "error"); }
  };

  const roots = categories.filter(c => !c.parent);
  const childOf = (code) => categories.filter(c => c.parent === code);

  const renderCat = (cat, depth) => (
    <div key={cat.code}>
      <div className="p-4 flex items-center justify-between" style={{ paddingLeft: `${16 + depth * 24}px` }} data-testid={`cat-${cat.code}`}>
        {ed?.code === cat.code ? (
          <div className="flex items-center gap-3 flex-1">
            <input value={ed.name} onChange={e => setEd(p => ({ ...p, name: e.target.value }))} className="filter-input" />
            <button onClick={() => upd(cat.code)} className="btn-primary text-xs px-3 py-1">Save</button>
            <button onClick={() => setEd(null)} className="text-xs text-slate-500">Cancel</button>
          </div>
        ) : (
          <><div className="flex items-center gap-2">
            {childOf(cat.code).length > 0 ? <ChevronDown size={14} className="text-slate-400" /> : <span className="w-4" />}
            <span className="font-mono text-xs font-bold text-slate-500">{cat.code}</span>
            <span className="text-sm text-slate-700">{cat.name}</span>
            {cat.parent && <span className="text-xs bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">child of {cat.parent}</span>}
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setEd({ ...cat })} data-testid={`edit-cat-${cat.code}`} className="p-1.5 hover:bg-slate-100 rounded"><Pencil size={14} className="text-slate-400" /></button>
            <button onClick={() => del(cat.code)} data-testid={`delete-cat-${cat.code}`} className="p-1.5 hover:bg-red-50 rounded"><Trash2 size={14} className="text-red-400" /></button>
          </div></>
        )}
      </div>
      {childOf(cat.code).map(ch => renderCat(ch, depth + 1))}
    </div>
  );

  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-sm" data-testid="categories-panel">
      <div className="p-4 border-b border-slate-100">
        <h2 className="font-semibold text-slate-900">Category Hierarchy</h2>
        <p className="text-xs text-slate-500 mt-1">Define product categories with optional nesting</p>
      </div>
      <div className="p-4 bg-slate-50 border-b border-slate-100 flex items-end gap-3">
        <div className="flex-1"><label className="text-xs text-slate-500 font-medium">Code</label>
          <input data-testid="new-cat-code" value={nw.code} onChange={e => setNw(p => ({ ...p, code: e.target.value }))} className="filter-input mt-1" placeholder="ACTIVE" /></div>
        <div className="flex-[2]"><label className="text-xs text-slate-500 font-medium">Name</label>
          <input data-testid="new-cat-name" value={nw.name} onChange={e => setNw(p => ({ ...p, name: e.target.value }))} className="filter-input mt-1" placeholder="Activewear" /></div>
        <div className="flex-[2]"><label className="text-xs text-slate-500 font-medium">Parent</label>
          <select data-testid="new-cat-parent" value={nw.parent} onChange={e => setNw(p => ({ ...p, parent: e.target.value }))} className="filter-input mt-1">
            <option value="">None (top level)</option>
            {categories.map(c => <option key={c.code} value={c.code}>{c.name} ({c.code})</option>)}
          </select></div>
        <button onClick={add} data-testid="add-cat-btn" className="btn-primary flex items-center gap-1 h-[38px]"><Plus size={14} /> Add</button>
      </div>
      <div className="divide-y divide-slate-100">
        {categories.length === 0 && <div className="p-6 text-center text-slate-400 text-sm">No custom categories. Auto-detected from Style Master uploads.</div>}
        {roots.map(c => renderCat(c, 0))}
      </div>
    </div>
  );
};

export default Configuration;
