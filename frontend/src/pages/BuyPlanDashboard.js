import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  Brain, TrendingUp, Download, Upload, History,
  Settings, BarChart3, Package, Store, Globe,
  ChevronRight, ChevronDown, AlertCircle, CheckCircle, Clock,
  FileSpreadsheet, RefreshCw, Zap, Target, DollarSign,
  Percent, Truck, Shield, Calendar, ArrowRight, X
} from "lucide-react";
import { Line, Bar } from "react-chartjs-2";
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, BarElement, Title, Tooltip, Legend, Filler
} from "chart.js";

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, Title, Tooltip, Legend, Filler
);

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// Fallback defaults (used only when no uploaded data)
const FALLBACK_CATEGORIES = ["Jeans", "Shirts", "Jackets", "Belts", "Socks", "Shoes"];
const FALLBACK_CHANNELS = [];

// ─── Wizard Step 1: Revenue Target ───
const StepRevenue = ({ params, updateParam, onNext }) => (
  <div className="space-y-6 max-w-2xl mx-auto animate-in fade-in duration-300" data-testid="wizard-step-revenue">
    <div className="text-center space-y-1">
      <Target className="w-10 h-10 text-indigo-600 mx-auto" />
      <h2 className="text-xl font-semibold text-slate-800">Set Revenue Target</h2>
      <p className="text-sm text-slate-500">Define your overall revenue goal for the planning period</p>
    </div>
    <div className="space-y-4">
      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-1.5">
          <DollarSign size={16} className="text-slate-400" /> Annual Revenue Target (Crore)
        </label>
        <input data-testid="input-revenue-target" type="number" value={params.revenue_target_cr}
          onChange={e => updateParam("revenue_target_cr", parseFloat(e.target.value) || 0)}
          step="0.1" min="0.1"
          className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500" />
        <p className="text-xs text-slate-400 mt-1">Example: 1.1 = 1.1 Crore</p>
      </div>
      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-1.5">
          <TrendingUp size={16} className="text-slate-400" /> Revenue Increase from Baseline (%)
        </label>
        <input data-testid="input-revenue-increase" type="number" value={params.revenue_increase_percent}
          onChange={e => updateParam("revenue_increase_percent", parseFloat(e.target.value) || 0)}
          className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
      </div>
      {/* Preview card */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl p-5 mt-4">
        <h4 className="text-sm font-medium opacity-90 mb-3">Projected Impact</h4>
        <div className="flex items-center justify-around">
          <div className="text-center">
            <span className="block text-xs opacity-75">Current Baseline</span>
            <span className="block text-lg font-bold mt-0.5">
              {((params.revenue_target_cr * 100) / (100 + (params.revenue_increase_percent || 1))).toFixed(1)} Cr
            </span>
          </div>
          <ArrowRight size={20} className="opacity-60" />
          <div className="text-center">
            <span className="block text-xs opacity-75">New Target</span>
            <span className="block text-2xl font-bold mt-0.5">{params.revenue_target_cr} Cr</span>
          </div>
        </div>
      </div>
    </div>
    <button data-testid="wizard-next-1" onClick={onNext}
      className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white py-2.5 rounded-lg text-sm font-medium transition-colors">
      Next: Select Categories <ArrowRight size={16} />
    </button>
  </div>
);

// ─── Wizard Step 2: Categories ───
const StepCategories = ({ params, toggleCategory, onNext, onBack, categoriesList }) => (
  <div className="space-y-6 max-w-2xl mx-auto animate-in fade-in duration-300" data-testid="wizard-step-categories">
    <div className="text-center space-y-1">
      <Package className="w-10 h-10 text-indigo-600 mx-auto" />
      <h2 className="text-xl font-semibold text-slate-800">Select Product Categories</h2>
      <p className="text-sm text-slate-500">Choose which categories to include in the buy plan</p>
    </div>
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
      {categoriesList.map(cat => {
        const selected = params.categories.includes(cat);
        return (
          <button key={cat} data-testid={`cat-${cat.toLowerCase().replace(/\s+/g, '-')}`}
            onClick={() => toggleCategory(cat)}
            className={`relative p-4 border-2 rounded-xl text-left transition-all duration-200
              ${selected ? "border-emerald-500 bg-emerald-50" : "border-slate-200 hover:border-indigo-300 hover:shadow-sm"}`}>
            {selected && <CheckCircle size={18} className="absolute top-2 right-2 text-emerald-500" />}
            <span className="block text-sm font-semibold text-slate-800">{cat}</span>
          </button>
        );
      })}
    </div>
    <div className="flex justify-between gap-3">
      <button onClick={onBack} className="px-5 py-2.5 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors">Back</button>
      <button data-testid="wizard-next-2" onClick={onNext} disabled={params.categories.length === 0}
        className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
        Next: Select Channels <ArrowRight size={16} />
      </button>
    </div>
  </div>
);

// ─── Wizard Step 3: Channels ───
const StepChannels = ({ params, toggleChannel, onNext, onBack, channelsList }) => {
  const storeChannels = channelsList.filter(c => c.toUpperCase().includes("STORE") || c.toUpperCase().includes("EBO") || c.toUpperCase().includes("MBO") || c.toUpperCase().includes("LFS"));
  const marketChannels = channelsList.filter(c => !storeChannels.includes(c));

  return (
  <div className="space-y-6 max-w-2xl mx-auto animate-in fade-in duration-300" data-testid="wizard-step-channels">
    <div className="text-center space-y-1">
      <Store className="w-10 h-10 text-indigo-600 mx-auto" />
      <h2 className="text-xl font-semibold text-slate-800">Select Sales Channels</h2>
      <p className="text-sm text-slate-500">Choose stores and marketplaces for distribution</p>
    </div>
    <div>
      {storeChannels.length > 0 && (
        <>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Physical Stores</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
            {storeChannels.map(ch => {
              const sel = params.channels.includes(ch);
              return (
                <button key={ch} data-testid={`ch-${ch.toLowerCase().replace(/\s+/g, '-')}`} onClick={() => toggleChannel(ch)}
                  className={`flex flex-col items-center gap-1.5 p-4 border-2 rounded-xl transition-all
                  ${sel ? "border-emerald-500 bg-emerald-50" : "border-slate-200 hover:border-indigo-300"}`}>
                  {sel && <CheckCircle size={16} className="text-emerald-500" />}
                  <Store size={20} className="text-slate-500" />
                  <span className="text-sm font-medium">{ch}</span>
                </button>
              );
            })}
          </div>
        </>
      )}
      {marketChannels.length > 0 && (
        <>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Marketplaces</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {marketChannels.map(ch => {
              const sel = params.channels.includes(ch);
              return (
                <button key={ch} data-testid={`ch-${ch.toLowerCase().replace(/\s+/g, '-')}`} onClick={() => toggleChannel(ch)}
                  className={`flex flex-col items-center gap-1.5 p-4 border-2 rounded-xl transition-all
                  ${sel ? "border-emerald-500 bg-emerald-50" : "border-slate-200 hover:border-indigo-300"}`}>
                  {sel && <CheckCircle size={16} className="text-emerald-500" />}
                  <Globe size={20} className="text-slate-500" />
                  <span className="text-sm font-medium">{ch}</span>
                </button>
              );
            })}
          </div>
        </>
      )}
      {channelsList.length === 0 && (
        <div className="text-center py-8 text-slate-400 text-sm">
          <AlertCircle size={24} className="mx-auto mb-2 opacity-50" />
          No channels found. Upload store master data to see available channels.
        </div>
      )}
    </div>
    <div className="flex justify-between gap-3">
      <button onClick={onBack} className="px-5 py-2.5 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors">Back</button>
      <button data-testid="wizard-next-3" onClick={onNext} disabled={params.channels.length === 0}
        className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
        Next: Configure Parameters <ArrowRight size={16} />
      </button>
    </div>
  </div>
  );
};

// ─── Wizard Step 4: Parameters + Generate ───
const StepParams = ({ params, updateParam, onBack, onGenerate, loading }) => (
  <div className="space-y-6 max-w-2xl mx-auto animate-in fade-in duration-300" data-testid="wizard-step-params">
    <div className="text-center space-y-1">
      <Shield className="w-10 h-10 text-indigo-600 mx-auto" />
      <h2 className="text-xl font-semibold text-slate-800">Configure Parameters</h2>
      <p className="text-sm text-slate-500">Set safety stock, lead times, and other planning parameters</p>
    </div>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {[
        { key: "safety_stock_percent", label: "Safety Stock (%)", icon: Shield, desc: "Buffer stock for demand variability", step: 1, min: 0, max: 50 },
        { key: "lead_time_days", label: "Lead Time (Days)", icon: Truck, desc: "Supplier delivery lead time", step: 1, min: 1, max: 120 },
        { key: "return_rate_percent", label: "Return Rate (%)", icon: Percent, desc: "Expected returns/damage percentage", step: 0.5, min: 0, max: 30 },
        { key: "months", label: "Planning Horizon (Months)", icon: Calendar, desc: "Number of months to plan for", step: 1, min: 1, max: 24 },
      ].map(({ key, label, icon: Icon, desc, step, min, max }) => (
        <div key={key} className="border border-slate-200 rounded-xl p-4 space-y-2">
          <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <Icon size={14} className="text-slate-400" /> {label}
          </label>
          <input data-testid={`input-${key}`} type="number" value={params[key]}
            onChange={e => updateParam(key, parseFloat(e.target.value) || 0)}
            step={step} min={min} max={max}
            className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          <p className="text-[11px] text-slate-400">{desc}</p>
        </div>
      ))}
    </div>
    <div className="flex justify-between gap-3 pt-2">
      <button onClick={onBack} className="px-5 py-2.5 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors">Back</button>
      <button data-testid="generate-buy-plan-btn" onClick={onGenerate} disabled={loading}
        className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-60">
        {loading ? (
          <><RefreshCw size={16} className="animate-spin" /> Generating...</>
        ) : (
          <>Generate AI Buy Plan <Zap size={16} /></>
        )}
      </button>
    </div>
  </div>
);

// ─── Charts Component ───
const BuyPlanCharts = ({ data }) => {
  const monthlyData = {};
  data.categories.forEach(cat => {
    cat.monthly_breakdown.forEach(m => {
      if (!monthlyData[m.month_name]) monthlyData[m.month_name] = {};
      monthlyData[m.month_name][cat.category] = m.units;
    });
  });

  const lineData = {
    labels: MONTHS,
    datasets: data.categories.map((cat, i) => ({
      label: cat.category,
      data: MONTHS.map(m => monthlyData[m]?.[cat.category] || 0),
      borderColor: `hsl(${i * 60}, 70%, 50%)`,
      backgroundColor: `hsla(${i * 60}, 70%, 50%, 0.08)`,
      fill: false, tension: 0.4, pointRadius: 3, pointHoverRadius: 5,
    })),
  };

  const barData = {
    labels: data.categories.map(c => c.category),
    datasets: [
      { label: "Required Units", data: data.categories.map(c => c.required_units), backgroundColor: "rgba(99,102,241,0.7)", borderRadius: 6 },
      { label: "Buy Quantity", data: data.categories.map(c => c.total_buy_quantity), backgroundColor: "rgba(16,185,129,0.7)", borderRadius: 6 },
    ],
  };

  const channelLabels = data.categories[0]?.channel_breakdown.map(c => c.channel) || [];
  const channelBarData = {
    labels: data.categories.map(c => c.category),
    datasets: channelLabels.map((ch, i) => ({
      label: ch,
      data: data.categories.map(c => c.channel_breakdown.find(cb => cb.channel === ch)?.buy_quantity || 0),
      backgroundColor: `hsl(${i * 72}, 65%, 55%)`,
      borderRadius: 6,
    })),
  };

  const opts = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { position: "top", labels: { boxWidth: 12, font: { size: 11 } } } },
    scales: { y: { ticks: { callback: v => v.toLocaleString() }, title: { display: true, text: "Units" } } },
  };

  return (
    <div className="space-y-5" data-testid="buy-plan-charts">
      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-slate-800 mb-3">Monthly Demand Forecast by Category</h3>
        <div className="h-[340px]"><Line data={lineData} options={opts} /></div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-800 mb-3">Required vs Buy Quantity</h3>
          <div className="h-[280px]"><Bar data={barData} options={opts} /></div>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-800 mb-3">Buy Quantity by Channel</h3>
          <div className="h-[280px]"><Bar data={channelBarData} options={{...opts, scales: {...opts.scales, x: { stacked: false }}}} /></div>
        </div>
      </div>
    </div>
  );
};

// ─── Table Component ───
const BuyPlanTable = ({ data }) => {
  const [expanded, setExpanded] = useState(null);
  const toggle = cat => setExpanded(expanded === cat ? null : cat);

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden mt-5" data-testid="buy-plan-table">
      <div className="px-5 py-3 border-b border-slate-100">
        <h3 className="text-sm font-semibold text-slate-800">Category Level Buy Plan</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 text-left">
              <th className="px-4 py-3 font-semibold text-slate-600">Category</th>
              <th className="px-4 py-3 font-semibold text-slate-600">ASP</th>
              <th className="px-4 py-3 font-semibold text-slate-600">Contribution</th>
              <th className="px-4 py-3 font-semibold text-slate-600">Required Units</th>
              <th className="px-4 py-3 font-semibold text-slate-600">Buy Qty</th>
              <th className="px-4 py-3 font-semibold text-slate-600">Buy Value</th>
              <th className="px-4 py-3 font-semibold text-slate-600">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.categories.map(cat => (
              <CategoryRow key={cat.category} cat={cat} expanded={expanded === cat.category} onToggle={() => toggle(cat.category)} />
            ))}
          </tbody>
          <tfoot>
            <tr className="bg-slate-50 font-semibold text-sm">
              <td className="px-4 py-3">Total</td>
              <td className="px-4 py-3"></td>
              <td className="px-4 py-3"></td>
              <td className="px-4 py-3">{data.summary.total_buy_quantity.toLocaleString()}</td>
              <td className="px-4 py-3 text-indigo-600">{data.summary.total_buy_quantity.toLocaleString()}</td>
              <td className="px-4 py-3">{data.summary.total_buy_value.toLocaleString()}</td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
};

const CategoryRow = ({ cat, expanded, onToggle }) => {
  const status = cat.total_buy_quantity > cat.required_units ? "Overstock"
    : cat.total_buy_quantity === cat.required_units ? "Balanced" : "Need Buy";
  const statusColor = status === "Overstock" ? "bg-amber-100 text-amber-700"
    : status === "Balanced" ? "bg-emerald-100 text-emerald-700" : "bg-blue-100 text-blue-700";

  return (
    <>
      <tr className="border-b border-slate-100 cursor-pointer hover:bg-slate-50 transition-colors" onClick={onToggle} data-testid={`cat-row-${cat.category.toLowerCase()}`}>
        <td className="px-4 py-3 font-medium flex items-center gap-1.5">
          {expanded ? <ChevronDown size={14} className="text-slate-400" /> : <ChevronRight size={14} className="text-slate-400" />}
          {cat.category}
        </td>
        <td className="px-4 py-3">{cat.asp.toLocaleString()}</td>
        <td className="px-4 py-3">{cat.contribution_percent}%</td>
        <td className="px-4 py-3">{cat.required_units.toLocaleString()}</td>
        <td className="px-4 py-3 font-semibold text-indigo-600">{cat.total_buy_quantity.toLocaleString()}</td>
        <td className="px-4 py-3">{cat.total_buy_value.toLocaleString()}</td>
        <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor}`}>{status}</span></td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={7} className="bg-slate-50 px-5 py-4">
            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Channel Breakdown</h4>
                <table className="w-full text-xs">
                  <thead><tr className="text-slate-400">
                    <th className="text-left py-1.5 px-2">Channel</th><th className="text-left py-1.5 px-2">Type</th>
                    <th className="text-left py-1.5 px-2">Units Needed</th><th className="text-left py-1.5 px-2">Safety Stock</th>
                    <th className="text-left py-1.5 px-2">Current Inv</th><th className="text-left py-1.5 px-2">Buy Qty</th>
                    <th className="text-left py-1.5 px-2">Sell-Through</th>
                  </tr></thead>
                  <tbody>
                    {cat.channel_breakdown.map(ch => (
                      <tr key={ch.channel} className="border-b border-slate-100">
                        <td className="py-1.5 px-2 font-medium">{ch.channel}</td>
                        <td className="py-1.5 px-2">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${ch.channel_type === "store" ? "bg-blue-100 text-blue-600" : "bg-amber-100 text-amber-600"}`}>{ch.channel_type}</span>
                        </td>
                        <td className="py-1.5 px-2">{ch.units_needed.toLocaleString()}</td>
                        <td className="py-1.5 px-2">{ch.safety_stock.toLocaleString()}</td>
                        <td className="py-1.5 px-2">{ch.current_inventory.toLocaleString()}</td>
                        <td className="py-1.5 px-2 font-semibold text-indigo-600">{ch.buy_quantity.toLocaleString()}</td>
                        <td className="py-1.5 px-2">{ch.sell_through_rate || "N/A"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div>
                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Monthly Breakdown</h4>
                <div className="grid grid-cols-4 sm:grid-cols-6 lg:grid-cols-12 gap-2">
                  {cat.monthly_breakdown.map(m => (
                    <div key={m.month} className="bg-white border border-slate-200 rounded-lg p-2.5 text-center">
                      <div className="text-xs font-semibold text-slate-700">{m.month_name}</div>
                      <div className="text-xs text-indigo-600 font-medium">{m.units.toLocaleString()}</div>
                      <div className="text-[10px] text-slate-400">{m.seasonal_factor}x</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
};

// ─── Workbook Component ───
const BuyPlanWorkbook = ({ planData, onExport, onUpload, loading }) => {
  const [uploadStatus, setUploadStatus] = useState(null);

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-5" data-testid="buy-plan-workbook">
      <div>
        <h3 className="flex items-center gap-2 text-base font-semibold text-slate-800">
          <FileSpreadsheet size={18} className="text-emerald-600" /> Editable Excel Workbook
        </h3>
        <p className="text-sm text-slate-500 mt-0.5">Download the plan, make edits in Excel, and upload back to save changes</p>
      </div>
      <div className="flex flex-wrap gap-3">
        <button data-testid="download-excel-btn" onClick={onExport} disabled={loading}
          className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
          <Download size={16} /> Download Excel Workbook
        </button>
        <label className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer">
          <Upload size={16} /> Upload Edited Plan
          <input type="file" accept=".xlsx,.xls" onChange={e => {
            if (e.target.files[0]) {
              setUploadStatus("uploading");
              onUpload(e.target.files[0])
                .then(() => setUploadStatus("success"))
                .catch(() => setUploadStatus("error"));
            }
            e.target.value = "";
          }} className="hidden" data-testid="upload-plan-input" />
        </label>
      </div>
      {uploadStatus === "uploading" && (
        <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 text-blue-700 rounded-lg px-4 py-2.5 text-sm">
          <RefreshCw size={16} className="animate-spin" /> Processing your edited plan...
        </div>
      )}
      {uploadStatus === "success" && (
        <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-lg px-4 py-2.5 text-sm">
          <CheckCircle size={16} /> Plan uploaded successfully! Changes have been applied.
        </div>
      )}
      {uploadStatus === "error" && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-2.5 text-sm">
          <AlertCircle size={16} /> Upload failed. Please check file format and try again.
        </div>
      )}
      <div className="bg-slate-50 rounded-xl p-5 space-y-3">
        <h4 className="text-sm font-semibold text-slate-700">How to use this workbook:</h4>
        <ol className="list-decimal list-inside text-sm text-slate-600 space-y-1">
          <li>Click "Download Excel Workbook" to get the editable file</li>
          <li>Open in Microsoft Excel or Google Sheets</li>
          <li>Go to the "Buy Plan (Editable)" sheet</li>
          <li>Enter your override quantities in the "USER OVERRIDE" column</li>
          <li>Save the file and click "Upload Edited Plan" to apply changes</li>
        </ol>
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mt-2">
          <h5 className="text-xs font-semibold text-amber-700 mb-1">Pro Tips</h5>
          <ul className="list-disc list-inside text-xs text-amber-600 space-y-0.5">
            <li>Your overrides are saved to history for audit trail</li>
            <li>Negative buy quantities will be treated as zero</li>
            <li>You can compare different versions in the History tab</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

// ─── Main Dashboard ───
const BuyPlanDashboard = () => {
  const [activeTab, setActiveTab] = useState("wizard");
  const [loading, setLoading] = useState(false);
  const [planData, setPlanData] = useState(null);
  const [history, setHistory] = useState([]);
  const [wizardStep, setWizardStep] = useState(1);
  const [error, setError] = useState(null);

  // Dynamic options from backend
  const [options, setOptions] = useState(null);
  const [optionsLoading, setOptionsLoading] = useState(true);

  const [params, setParams] = useState({
    revenue_target_cr: 1.1,
    revenue_increase_percent: 20,
    categories: [],
    channels: [],
    months: 12,
    safety_stock_percent: 15,
    lead_time_days: 30,
    return_rate_percent: 5,
  });

  const updateParam = (key, value) => setParams(p => ({ ...p, [key]: value }));
  const toggleCategory = cat => setParams(p => ({
    ...p, categories: p.categories.includes(cat) ? p.categories.filter(c => c !== cat) : [...p.categories, cat]
  }));
  const toggleChannel = ch => setParams(p => ({
    ...p, channels: p.channels.includes(ch) ? p.channels.filter(c => c !== ch) : [...p.channels, ch]
  }));

  // Fetch dynamic options on mount
  useEffect(() => {
    const fetchOptions = async () => {
      setOptionsLoading(true);
      try {
        const { data } = await axios.get(`${API}/buy-plan/options`);
        setOptions(data);
        // Initialize params with dynamic data
        setParams(p => ({
          ...p,
          categories: data.categories || FALLBACK_CATEGORIES,
          channels: data.channels || FALLBACK_CHANNELS,
        }));
      } catch (e) {
        console.error("Failed to fetch options:", e);
        // Use fallbacks
        setParams(p => ({ ...p, categories: [...FALLBACK_CATEGORIES], channels: [...FALLBACK_CHANNELS] }));
      } finally {
        setOptionsLoading(false);
      }
    };
    fetchOptions();
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/buy-plan/history?limit=10`);
      setHistory(data.history || []);
    } catch (e) { console.error("History load failed:", e); }
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await axios.post(`${API}/buy-plan/generate`, params);
      setPlanData(data);
      setActiveTab("results");
      loadHistory();
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to generate plan. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleExportExcel = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/buy-plan/export-excel`, params, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `buy_plan_${new Date().toISOString().slice(0, 10)}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      setError("Export failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await axios.post(`${API}/buy-plan/upload-edited-plan`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    loadHistory();
    return data;
  };

  const tabs = [
    { key: "wizard", label: "Configuration Wizard", icon: Settings, always: true },
    { key: "results", label: "Plan Results", icon: BarChart3, always: false },
    { key: "workbook", label: "Editable Workbook", icon: FileSpreadsheet, always: false },
    { key: "history", label: "History", icon: History, always: true },
  ];

  return (
    <div className="space-y-5" data-testid="buy-plan-dashboard">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-5 text-white">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Brain size={24} />
              <h1 className="text-xl font-semibold">AI Buy Plan Generator</h1>
            </div>
            <p className="text-sm opacity-85">ML-powered demand planning with store & marketplace breakdown</p>
          </div>
          <div className="hidden sm:flex items-center gap-2 bg-white/15 px-3 py-1.5 rounded-full text-xs font-medium">
            <Zap size={14} /> ML Ensemble Forecast
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-200">
        {tabs.map(t => (
          <button key={t.key} data-testid={`tab-${t.key}`}
            onClick={() => setActiveTab(t.key)}
            disabled={!t.always && !planData}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors
              ${activeTab === t.key ? "border-indigo-600 text-indigo-600" : "border-transparent text-slate-500 hover:text-slate-700"}
              disabled:opacity-40 disabled:cursor-not-allowed`}>
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          <AlertCircle size={16} /> {error}
          <button onClick={() => setError(null)} className="ml-auto"><X size={14} /></button>
        </div>
      )}

      {/* Loading overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black/50 z-50 flex flex-col items-center justify-center gap-3">
          <RefreshCw size={32} className="text-white animate-spin" />
          <p className="text-white text-sm font-medium">Generating AI buy plan...</p>
        </div>
      )}

      {/* Content */}
      {activeTab === "wizard" && (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          {/* Data source indicator */}
          {options && (
            <div className={`px-6 py-2 text-xs font-medium flex items-center gap-1.5 ${options.has_data ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`} data-testid="data-source-indicator">
              {options.has_data ? <CheckCircle size={12} /> : <AlertCircle size={12} />}
              {options.has_data
                ? `Using uploaded data: ${options.categories.length} categories, ${options.channels.length} channels`
                : "No uploaded data yet — using default categories. Upload data for dynamic planning."}
            </div>
          )}
          {/* Progress steps */}
          <div className="flex px-6 py-4 bg-slate-50 border-b border-slate-200">
            {[
              { n: 1, label: "Revenue Target" },
              { n: 2, label: "Categories" },
              { n: 3, label: "Channels" },
              { n: 4, label: "Parameters" },
            ].map(({ n, label }) => (
              <div key={n} className="flex-1 flex flex-col items-center relative">
                {n > 1 && (
                  <div className={`absolute top-3.5 right-1/2 w-full h-0.5 -z-0
                    ${wizardStep >= n ? "bg-emerald-400" : "bg-slate-200"}`} />
                )}
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold z-10
                  ${wizardStep >= n ? "bg-emerald-500 text-white" : "bg-slate-200 text-slate-500"}`}>
                  {wizardStep > n ? <CheckCircle size={14} /> : n}
                </div>
                <span className={`text-[10px] mt-1 ${wizardStep >= n ? "text-emerald-600 font-medium" : "text-slate-400"}`}>{label}</span>
              </div>
            ))}
          </div>
          <div className="p-6">
            {optionsLoading ? (
              <div className="flex items-center justify-center py-12 text-slate-400 gap-2">
                <RefreshCw size={18} className="animate-spin" /> Loading options...
              </div>
            ) : (
              <>
                {wizardStep === 1 && <StepRevenue params={params} updateParam={updateParam} onNext={() => setWizardStep(2)} />}
                {wizardStep === 2 && <StepCategories params={params} toggleCategory={toggleCategory} onNext={() => setWizardStep(3)} onBack={() => setWizardStep(1)} categoriesList={options?.categories || FALLBACK_CATEGORIES} />}
                {wizardStep === 3 && <StepChannels params={params} toggleChannel={toggleChannel} onNext={() => setWizardStep(4)} onBack={() => setWizardStep(2)} channelsList={options?.channels || FALLBACK_CHANNELS} />}
                {wizardStep === 4 && <StepParams params={params} updateParam={updateParam} onBack={() => setWizardStep(3)} onGenerate={handleGenerate} loading={loading} />}
              </>
            )}
          </div>
        </div>
      )}

      {activeTab === "results" && planData && (
        <div className="space-y-5">
          {/* Data source badge */}
          <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${planData.metadata?.data_source === "uploaded" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`} data-testid="results-data-source">
            {planData.metadata?.data_source === "uploaded" ? <CheckCircle size={12} /> : <AlertCircle size={12} />}
            Data source: {planData.metadata?.data_source === "uploaded" ? "Uploaded tenant data" : "Default fallback values"}
          </div>
          {/* Summary KPIs */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4" data-testid="buy-plan-kpis">
            <div className="bg-white border border-slate-200 rounded-xl p-4">
              <p className="text-xs text-slate-500">Total Buy Quantity</p>
              <p className="text-lg font-bold text-slate-800">{planData.summary.total_buy_quantity.toLocaleString()}</p>
              <p className="text-xs text-slate-400">units</p>
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-4">
              <p className="text-xs text-slate-500">Total Buy Value</p>
              <p className="text-lg font-bold text-slate-800">{(planData.summary.total_buy_value / 100000).toFixed(1)}L</p>
              <p className="text-xs text-slate-400">rupees</p>
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-4">
              <p className="text-xs text-slate-500">Categories</p>
              <p className="text-lg font-bold text-slate-800">{planData.summary.categories_processed}</p>
              <p className="text-xs text-slate-400">planned</p>
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-4">
              <p className="text-xs text-slate-500">Channels</p>
              <p className="text-lg font-bold text-slate-800">{planData.summary.channels_used.length}</p>
              <p className="text-xs text-slate-400">store + marketplace</p>
            </div>
          </div>
          <BuyPlanCharts data={planData} />
          <BuyPlanTable data={planData} />
        </div>
      )}

      {activeTab === "workbook" && planData && (
        <BuyPlanWorkbook planData={planData} onExport={handleExportExcel} onUpload={handleUpload} loading={loading} />
      )}

      {activeTab === "history" && (
        <div className="bg-white border border-slate-200 rounded-xl p-5" data-testid="buy-plan-history">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-800">Recent Buy Plans</h3>
            <button onClick={loadHistory} className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 border border-slate-200 rounded-lg px-2.5 py-1.5">
              <RefreshCw size={12} /> Refresh
            </button>
          </div>
          {history.length === 0 ? (
            <div className="text-center py-10 text-slate-400">
              <History size={32} className="mx-auto mb-2 opacity-40" />
              <p className="text-sm">No plans generated yet</p>
              <button onClick={() => setActiveTab("wizard")} className="text-indigo-600 text-sm mt-1 hover:underline">Create your first plan</button>
            </div>
          ) : (
            <div className="space-y-3">
              {history.map((plan, i) => (
                <div key={i} className="flex items-center justify-between p-3 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
                  <div className="flex items-center gap-3">
                    <Clock size={16} className="text-slate-400" />
                    <div>
                      <p className="text-sm font-medium text-slate-700">
                        {new Date(plan.generated_at || plan.saved_at).toLocaleString()}
                      </p>
                      <p className="text-xs text-slate-400">
                        Target: {plan.metadata?.revenue_target_cr} Cr | Buy: {plan.summary?.total_buy_quantity?.toLocaleString()} units
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default BuyPlanDashboard;
