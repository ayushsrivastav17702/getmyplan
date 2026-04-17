import React from "react";
import { MixBadge } from "./shared";
import { Eye } from "lucide-react";

export function AttributionTab({ attribution, selectedAttr, setSelectedAttr }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className={`${selectedAttr ? "lg:col-span-2" : "lg:col-span-3"} border border-gray-200 rounded-xl overflow-hidden`}>
          <table data-testid="attribution-table" className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-3 font-medium text-gray-600">Style</th><th className="text-left p-3 font-medium text-gray-600">Mix</th>
                <th className="text-center p-3 font-medium text-gray-600">A-Stores</th><th className="text-center p-3 font-medium text-gray-600">B-Stores</th>
                <th className="text-center p-3 font-medium text-gray-600">C-Stores</th><th className="text-left p-3 font-medium text-gray-600">Coverage</th>
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
                      {a.wedge_allocation[w]?.eligible ? <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded text-xs font-medium">{a.wedge_allocation[w].allocation_pct}%</span> : <span className="text-xs text-gray-300">{"\u2014"}</span>}
                    </td>
                  ))}
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden"><div className="h-full bg-emerald-500 rounded-full" style={{ width: `${a.coverage_pct}%` }} /></div>
                      <span className="text-xs text-gray-500">{a.coverage_pct}%</span>
                    </div>
                  </td>
                  <td className="p-3"><Eye className="h-3.5 w-3.5 text-gray-400" /></td>
                </tr>
              ))}
              {(attribution?.attributions || []).length === 0 && (
                <tr><td colSpan={7} className="p-8 text-center text-gray-400">No attribution data. Run classifications first.</td></tr>
              )}
            </tbody>
          </table>
        </div>
        {selectedAttr && (
          <div data-testid="attribution-detail-panel" className="border border-gray-200 rounded-xl bg-white p-5 space-y-4 h-fit">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-gray-900">Attribution Detail</h3>
              <button onClick={() => setSelectedAttr(null)} className="text-gray-400 hover:text-gray-600 text-xs">Close</button>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-xs"><span className="text-gray-500">Style</span><span className="font-mono font-medium">{selectedAttr.style}</span></div>
              <div className="flex justify-between text-xs"><span className="text-gray-500">Style Mix</span><MixBadge mix={selectedAttr.style_mix} /></div>
              <div className="flex justify-between text-xs"><span className="text-gray-500">SKU Count</span><span className="font-medium">{selectedAttr.sku_count}</span></div>
              <div className="flex justify-between text-xs"><span className="text-gray-500">Eligible Stores</span><span className="font-medium">{selectedAttr.eligible_stores} / {selectedAttr.total_stores}</span></div>
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
                    {alloc?.eligible && <div className="w-full bg-gray-100 rounded-full h-2"><div className={`h-2 rounded-full ${color}`} style={{ width: `${alloc.allocation_pct}%` }} /></div>}
                    {alloc?.eligible && <p className="text-[10px] text-gray-400 mt-0.5">{alloc.stores} stores allocated</p>}
                  </div>
                );
              })}
            </div>
            <div className="pt-3 border-t border-gray-100"><div className="flex justify-between text-xs"><span className="text-gray-500">Coverage</span><span className="font-bold text-emerald-700">{selectedAttr.coverage_pct}%</span></div></div>
          </div>
        )}
      </div>
    </div>
  );
}
