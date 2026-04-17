import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import { toast } from "sonner";
import {
  BarChart3, RefreshCw, Zap, Store, Tag, Grid3X3,
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
  const [loading, setLoading] = useState({});
  const [tab, setTab] = useState("overview");

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

  const wedgeSummary = wedge?.summary || { A: 0, B: 0, C: 0 };
  const mixSummary = mix?.summary || { Core: 0, Fashion: 0, Test: 0 };
  const totalStyles = mixSummary.Core + mixSummary.Fashion + mixSummary.Test;

  return (
    <div data-testid="buy-planning-page" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 data-testid="page-title" className="text-2xl font-bold text-gray-900">Buy Planning</h1>
          <p className="text-sm text-gray-500 mt-1">Store Wedge Classification + Style Mix Tagging</p>
        </div>
        <button onClick={fetchAll} className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50">
          <RefreshCw className="h-4 w-4" />
        </button>
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
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {[
          { id: "overview", label: "Assortment Matrix", icon: Grid3X3 },
          { id: "stores", label: "Store Wedge", icon: Store },
          { id: "styles", label: "Style Mix", icon: Tag },
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
        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <table data-testid="store-wedge-table" className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-3 font-medium text-gray-600">Store</th>
                <th className="text-left p-3 font-medium text-gray-600">Name</th>
                <th className="text-left p-3 font-medium text-gray-600">City</th>
                <th className="text-left p-3 font-medium text-gray-600">Channel</th>
                <th className="text-left p-3 font-medium text-gray-600">Area (sqft)</th>
                <th className="text-left p-3 font-medium text-gray-600">Wedge</th>
                <th className="text-right p-3 font-medium text-gray-600">Revenue</th>
              </tr>
            </thead>
            <tbody>
              {(wedge?.stores || []).map(s => (
                <tr key={s.store_code} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="p-3 font-mono text-xs font-medium">{s.store_code}</td>
                  <td className="p-3 text-gray-700">{s.store_name || "—"}</td>
                  <td className="p-3 text-gray-500">{s.city || "—"}</td>
                  <td className="p-3 text-gray-500">{s.channel || "—"}</td>
                  <td className="p-3 text-gray-500">{s.area_sqft ? s.area_sqft.toLocaleString() : "—"}</td>
                  <td className="p-3"><WedgeBadge wedge={s.wedge_class} /></td>
                  <td className="p-3 text-right text-gray-700 font-medium">
                    {s.total_revenue ? `₹${Math.round(s.total_revenue).toLocaleString()}` : "—"}
                  </td>
                </tr>
              ))}
              {(wedge?.stores || []).length === 0 && (
                <tr><td colSpan={7} className="p-8 text-center text-gray-400">
                  No stores found. Upload store master data first.
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {tab === "styles" && (
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
              </tr>
            </thead>
            <tbody>
              {(mix?.styles || []).map(s => (
                <tr key={s.style} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="p-3 font-mono text-xs font-medium">{s.style}</td>
                  <td className="p-3"><MixBadge mix={s.style_mix} /></td>
                  <td className="p-3 text-gray-600">{s.sku_count || "—"}</td>
                  <td className="p-3 text-gray-600">{s.stats?.avg_weekly_qty ?? "—"}</td>
                  <td className="p-3 text-gray-600">{s.stats?.weeks_active ?? "—"}</td>
                  <td className="p-3 text-gray-600">{s.stats?.peak_to_avg != null ? `${s.stats.peak_to_avg}x` : "—"}</td>
                  <td className="p-3 text-gray-600">{s.stats?.week_presence_pct != null ? `${s.stats.week_presence_pct}%` : "—"}</td>
                </tr>
              ))}
              {(mix?.styles || []).length === 0 && (
                <tr><td colSpan={7} className="p-8 text-center text-gray-400">
                  No style mix data. Run Style Mix Classification after uploading sales data.
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
