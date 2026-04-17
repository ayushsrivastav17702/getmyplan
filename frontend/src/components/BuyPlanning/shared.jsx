import React from "react";

export function WedgeBadge({ wedge }) {
  const s = { A: "bg-emerald-100 text-emerald-800", B: "bg-blue-100 text-blue-800", C: "bg-gray-100 text-gray-600" };
  return <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${s[wedge] || s.C}`}>{wedge || "\u2014"}</span>;
}

export function MixBadge({ mix }) {
  const s = { Core: "bg-emerald-100 text-emerald-800", Fashion: "bg-purple-100 text-purple-800", Test: "bg-amber-100 text-amber-800" };
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${s[mix] || "bg-gray-100 text-gray-600"}`}>{mix || "\u2014"}</span>;
}

export function StatCard({ label, value, sub, icon: Icon, color = "blue" }) {
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
