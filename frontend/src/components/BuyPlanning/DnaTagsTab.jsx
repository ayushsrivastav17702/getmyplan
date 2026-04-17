import React from "react";
import { MixBadge } from "./shared";

export function DnaTagsTab({ dnaTags }) {
  return (
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
              <td className="p-3"><span className={`px-2 py-0.5 rounded-full text-xs font-bold ${s.flow_rank === 1 ? "bg-emerald-100 text-emerald-800" : s.flow_rank === 2 ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-600"}`}>{s.flow_rank === 1 ? "Hero" : s.flow_rank === 2 ? "Core" : "Fill-in"}</span></td>
              <td className="p-3"><span className={`px-2 py-0.5 rounded text-xs ${s.lifecycle_stage === "Peak" ? "bg-emerald-50 text-emerald-700" : s.lifecycle_stage === "Launch" ? "bg-blue-50 text-blue-700" : s.lifecycle_stage === "Decline" ? "bg-amber-50 text-amber-700" : "bg-red-50 text-red-700"}`}>{s.lifecycle_stage || "\u2014"}</span></td>
              <td className="p-3 text-xs text-gray-500">{s.launch_date || "\u2014"}</td>
              <td className="p-3 text-gray-600">{s.expected_weeks ?? "\u2014"}w</td>
              <td className="p-3 text-gray-500">{s.sku_count}</td>
            </tr>
          ))}
          {(dnaTags?.styles || []).length === 0 && (
            <tr><td colSpan={7} className="p-8 text-center text-gray-400">No DNA tags. Click "Auto DNA Tag" to classify.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
