import React from "react";
import { MixBadge } from "./shared";
import { Search, Edit2 } from "lucide-react";

export function StyleMixTab({ filteredStyles, styleSearch, setStyleSearch, setOverrideModal, setOverrideValue }) {
  return (
    <div className="space-y-4">
      <div data-testid="style-filters" className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input data-testid="style-search-input" placeholder="Search by style name..." value={styleSearch} onChange={e => setStyleSearch(e.target.value)}
            className="w-full pl-10 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0B2545] focus:border-[#0B2545] outline-none" />
        </div>
        <span className="text-xs text-gray-400">{filteredStyles.length} styles</span>
      </div>
      <div className="border border-gray-200 rounded-xl overflow-hidden">
        <table data-testid="style-mix-table" className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-3 font-medium text-gray-600">Style</th><th className="text-left p-3 font-medium text-gray-600">Mix</th>
              <th className="text-left p-3 font-medium text-gray-600">SKUs</th><th className="text-left p-3 font-medium text-gray-600">Avg/Wk</th>
              <th className="text-left p-3 font-medium text-gray-600">Weeks Active</th><th className="text-left p-3 font-medium text-gray-600">Peak:Avg</th>
              <th className="text-left p-3 font-medium text-gray-600">Presence</th><th className="w-12"></th>
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
                    className="p-1 hover:bg-indigo-50 rounded text-indigo-500" title="Override mix"><Edit2 className="h-3.5 w-3.5" /></button>
                </td>
              </tr>
            ))}
            {filteredStyles.length === 0 && (
              <tr><td colSpan={8} className="p-8 text-center text-gray-400">{styleSearch ? "No styles match your search." : "No style mix data. Run Style Mix Classification after uploading sales data."}</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
