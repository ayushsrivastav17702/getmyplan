import React from "react";
import { WedgeBadge, MixBadge } from "./shared";

export function OverviewTab({ matrix }) {
  if (!matrix?.matrix) return null;
  return (
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
  );
}
