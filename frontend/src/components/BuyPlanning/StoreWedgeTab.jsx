import React from "react";
import { WedgeBadge } from "./shared";
import { Search, Crown, Star, MapPin, Store, Edit2, Settings } from "lucide-react";

export function StoreWedgeTab({
  wedge, filteredStores, storeSearch, setStoreSearch, storeWedgeFilter, setStoreWedgeFilter,
  regionFilter, setRegionFilter, tierFilter, setTierFilter, formatFilter, setFormatFilter,
  setOverrideModal, setOverrideValue, setStoreEditModal, wedgeSummary,
}) {
  return (
    <div className="space-y-4">
      {/* Distribution Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1"><Store className="h-4 w-4 text-gray-400" /><span className="text-xs text-gray-500">Total Stores</span></div>
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
          <input data-testid="store-search-input" placeholder="Search by store ID, name, or city..." value={storeSearch} onChange={e => setStoreSearch(e.target.value)}
            className="w-full pl-10 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0B2545] focus:border-[#0B2545] outline-none" />
        </div>
        <select data-testid="store-wedge-filter" value={storeWedgeFilter} onChange={e => setStoreWedgeFilter(e.target.value)} className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#0B2545] outline-none">
          <option value="all">All Wedges</option><option value="A">A-Stores</option><option value="B">B-Stores</option><option value="C">C-Stores</option>
        </select>
        <select data-testid="store-region-filter" value={regionFilter} onChange={e => setRegionFilter(e.target.value)} className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#0B2545] outline-none">
          <option value="all">All Regions</option><option value="North">North</option><option value="South">South</option><option value="East">East</option><option value="West">West</option><option value="Central">Central</option>
        </select>
        <select data-testid="store-tier-filter" value={tierFilter} onChange={e => setTierFilter(e.target.value)} className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#0B2545] outline-none">
          <option value="all">All Tiers</option><option value="tier1">Tier 1</option><option value="tier2">Tier 2</option><option value="tier3">Tier 3</option>
        </select>
        <select data-testid="store-format-filter" value={formatFilter} onChange={e => setFormatFilter(e.target.value)} className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#0B2545] outline-none">
          <option value="all">All Formats</option><option value="hypermarket">Hypermarket</option><option value="supermarket">Supermarket</option><option value="convenience">Convenience</option>
        </select>
        <span className="text-xs text-gray-400">{filteredStores.length} stores</span>
      </div>
      {/* Table */}
      <div className="border border-gray-200 rounded-xl overflow-hidden">
        <table data-testid="store-wedge-table" className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-3 font-medium text-gray-600">Store</th><th className="text-left p-3 font-medium text-gray-600">Name</th>
              <th className="text-left p-3 font-medium text-gray-600">City</th><th className="text-left p-3 font-medium text-gray-600">Region</th>
              <th className="text-left p-3 font-medium text-gray-600">Format</th><th className="text-left p-3 font-medium text-gray-600">Tier</th>
              <th className="text-left p-3 font-medium text-gray-600">Wedge</th><th className="text-right p-3 font-medium text-gray-600">Area</th>
              <th className="text-right p-3 font-medium text-gray-600">Revenue</th><th className="text-left p-3 font-medium text-gray-600">Type</th>
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
                <td className="p-3">{s.store_format ? <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${s.store_format === "hypermarket" ? "bg-purple-50 text-purple-700" : s.store_format === "supermarket" ? "bg-blue-50 text-blue-700" : "bg-gray-100 text-gray-600"}`}>{s.store_format}</span> : "\u2014"}</td>
                <td className="p-3">{s.city_tier ? <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${s.city_tier === "tier1" ? "bg-amber-50 text-amber-700" : s.city_tier === "tier2" ? "bg-blue-50 text-blue-700" : "bg-gray-100 text-gray-600"}`}>{s.city_tier}</span> : "\u2014"}</td>
                <td className="p-3"><WedgeBadge wedge={s.wedge_class} /></td>
                <td className="p-3 text-right text-gray-500 text-xs">{s.area_sqft ? s.area_sqft.toLocaleString() : "\u2014"}</td>
                <td className="p-3 text-right text-gray-700 font-medium">{s.total_revenue ? `\u20B9${Math.round(s.total_revenue).toLocaleString()}` : "\u2014"}</td>
                <td className="p-3">{s.wedge_manual_override ? <span className="px-1.5 py-0.5 bg-orange-50 text-orange-600 rounded text-[10px] font-medium">Manual</span> : s.wedge_class ? <span className="px-1.5 py-0.5 bg-emerald-50 text-emerald-600 rounded text-[10px] font-medium">Auto</span> : null}</td>
                <td className="p-3 text-right flex gap-1">
                  <button onClick={() => setStoreEditModal(s)} className="p-1 hover:bg-blue-50 rounded text-blue-500" title="Edit attributes"><Settings className="h-3.5 w-3.5" /></button>
                  <button onClick={() => { setOverrideModal({ type: "store", id: s.store_code, current: s.wedge_class }); setOverrideValue(s.wedge_class || "C"); }} className="p-1 hover:bg-indigo-50 rounded text-indigo-500" title="Override wedge"><Edit2 className="h-3.5 w-3.5" /></button>
                </td>
              </tr>
            ))}
            {filteredStores.length === 0 && (
              <tr><td colSpan={11} className="p-8 text-center text-gray-400">{storeSearch || storeWedgeFilter !== "all" || regionFilter !== "all" || tierFilter !== "all" || formatFilter !== "all" ? "No stores match your filters." : "No stores found. Upload store master data first."}</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
