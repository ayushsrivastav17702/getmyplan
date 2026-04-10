import React, { useState } from "react";
import {
  Calendar, Clock, FileText, AlertTriangle, CheckCircle,
  XCircle, ChevronDown, ChevronUp, Download, Info,
} from "lucide-react";

/* ────── Upload Type Requirement Data ────── */
const REQUIREMENTS = {
  daily_sales: {
    title: "Daily Sales",
    dateRange: "Last 30-90 days of sales transactions",
    minimum: "Last 30 days",
    recommended: "Last 90 days",
    forAI: "Last 180+ days",
    schedule: "Upload previous day's sales each morning",
    columns: "sku, store_code, day, quantity, revenue, discount, is_return",
    hasDateRange: true,
  },
  store_inventory: {
    title: "Store Inventory",
    dateRange: "Current snapshot (today's stock levels)",
    minimum: "Current day",
    recommended: "Daily end-of-day snapshots",
    schedule: "Daily (end of day) or weekly",
    columns: "store_code, sku, snapshot_date, closing_stock",
    hasDateRange: false,
  },
  warehouse_inventory: {
    title: "Warehouse Inventory",
    dateRange: "Current snapshot (today's stock levels)",
    minimum: "Current day",
    recommended: "Daily snapshots",
    schedule: "Daily or weekly",
    columns: "warehouse, sku, snapshot_date, on_hand_qty, available_qty",
    hasDateRange: false,
  },
  cogs: {
    title: "COGS (Cost of Goods Sold)",
    dateRange: "Must match Daily Sales date range exactly",
    minimum: "Same period as Daily Sales",
    recommended: "Same period as Daily Sales",
    schedule: "Upload alongside Daily Sales",
    columns: "transaction_date, store_code, sku_code, cogs",
    hasDateRange: true,
    note: "If you uploaded sales for Jan 10 - Apr 9, upload COGS for the same period",
  },
  open_orders: {
    title: "Open Orders",
    dateRange: "Current open POs and in-transit orders",
    minimum: "All outstanding orders",
    recommended: "All pending and in-transit",
    schedule: "Weekly or as orders are placed",
    columns: "order_date, expected_delivery_date, store_code, sku_code, order_quantity, status",
    hasDateRange: false,
  },
  sku_master: {
    title: "SKU Master",
    isMaster: true,
    schedule: "Setup once, update when products change",
    tip: "Upload BEFORE any transactional data",
  },
  store_master: {
    title: "Store Master",
    isMaster: true,
    schedule: "Setup once, update when store locations change",
    tip: "Upload BEFORE any transactional data",
  },
  warehouse_master: {
    title: "Warehouse Master",
    isMaster: true,
    schedule: "Setup once, update when warehouses change",
    tip: "Upload BEFORE any transactional data",
  },
  style_master: {
    title: "Style Master",
    isMaster: true,
    schedule: "Setup once, update when styles/categories change",
    tip: "Upload BEFORE any transactional data",
  },
  planogram: {
    title: "Planogram",
    isMaster: true,
    schedule: "Setup once, update when shelf norms change",
    tip: "Upload BEFORE any transactional data",
  },
};

const DATE_RANGE_TABLE = [
  { range: "< 30 days", label: "Basic analytics only", icon: "warn", detail: "ROS, DOH available. AI forecast unavailable" },
  { range: "30-90 days", label: "Full analytics", icon: "ok", detail: "ROS, DOH, Stockout, Gap Analysis" },
  { range: "90-180 days", label: "All features + AI forecast (demo mode)", icon: "ok", detail: "Seasonal patterns detected" },
  { range: "180+ days", label: "All features + AI forecast (real ML)", icon: "best", detail: "92%+ confidence, full seasonality" },
];

/* ────── Sub-Components ────── */

const Section = ({ icon: Icon, iconColor, title, children, defaultOpen = true }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden">
      <button
        className="w-full flex items-center gap-2.5 px-4 py-3 bg-slate-50/70 hover:bg-slate-100/70 transition-colors text-left"
        onClick={() => setOpen(!open)}
        data-testid={`req-section-${title.toLowerCase().replace(/\s+/g, '-')}`}
      >
        <Icon className={`w-4 h-4 ${iconColor} shrink-0`} />
        <span className="text-sm font-semibold text-slate-800 flex-1">{title}</span>
        {open ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
      </button>
      {open && <div className="px-4 py-3 text-sm text-slate-700 space-y-2">{children}</div>}
    </div>
  );
};

const DataDaysIndicator = ({ days }) => {
  if (days === null || days === undefined) return null;
  let color, text, icon;
  if (days >= 180) { color = "emerald"; text = "Excellent — all features unlocked"; icon = CheckCircle; }
  else if (days >= 90) { color = "emerald"; text = "Great — full analytics + demo AI forecast"; icon = CheckCircle; }
  else if (days >= 30) { color = "amber"; text = "Good — basic analytics available"; icon = AlertTriangle; }
  else if (days > 0) { color = "amber"; text = "Limited — upload more history for full features"; icon = AlertTriangle; }
  else { color = "slate"; text = "No data uploaded yet"; icon = XCircle; }
  const Icon = icon;
  const colors = {
    emerald: "text-emerald-600 bg-emerald-50 border-emerald-200",
    amber: "text-amber-600 bg-amber-50 border-amber-200",
    slate: "text-slate-500 bg-slate-50 border-slate-200",
  };
  return (
    <div className={`flex items-center gap-2 p-2.5 rounded-md border ${colors[color]}`} data-testid="data-days-indicator">
      <Icon className="w-4 h-4 shrink-0" />
      <span className="font-medium">Your current data: {days} days</span>
      <span className="text-xs opacity-80 ml-1">{text}</span>
    </div>
  );
};

/* ────── Master Data Panel ────── */
const MasterRequirements = ({ req }) => (
  <div className="space-y-3" data-testid="master-requirements">
    <Section icon={Calendar} iconColor="text-blue-500" title="When to Upload">
      <p>Represents your <strong>current</strong> catalog/locations.</p>
      <p className="flex items-center gap-1.5">
        <Clock className="w-3.5 h-3.5 text-slate-400" />
        {req.schedule}
      </p>
    </Section>
    {req.tip && (
      <div className="flex items-start gap-2 p-3 rounded-lg bg-blue-50 border border-blue-200">
        <Info className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" />
        <span className="text-sm text-blue-800">{req.tip}</span>
      </div>
    )}
  </div>
);

/* ────── Transactional Data Panel ────── */
const TransactionalRequirements = ({ req, currentDays, onDownloadTemplate }) => {
  const today = new Date();
  const fmt = (d) => d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  const d90 = new Date(today); d90.setDate(d90.getDate() - 90);
  const yesterday = new Date(today); yesterday.setDate(yesterday.getDate() - 1);

  return (
    <div className="space-y-3" data-testid="transactional-requirements">
      {/* Date range section */}
      <Section icon={Calendar} iconColor="text-blue-500" title="Required Date Range" defaultOpen={true}>
        <div className="space-y-2">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <div className="p-2 rounded bg-slate-50 border border-slate-150">
              <span className="text-xs text-slate-500 block">Minimum</span>
              <span className="font-medium text-slate-800">{req.minimum}</span>
            </div>
            <div className="p-2 rounded bg-blue-50 border border-blue-150">
              <span className="text-xs text-blue-500 block">Recommended</span>
              <span className="font-medium text-blue-800">{req.recommended}</span>
            </div>
            {req.forAI && (
              <div className="p-2 rounded bg-violet-50 border border-violet-150">
                <span className="text-xs text-violet-500 block">For AI Forecast</span>
                <span className="font-medium text-violet-800">{req.forAI}</span>
              </div>
            )}
          </div>
          <DataDaysIndicator days={currentDays} />
          {req.hasDateRange && (
            <p className="text-xs text-slate-500">
              Example: If today is {fmt(today)}, upload data from {fmt(d90)} to {fmt(yesterday)}
            </p>
          )}
          {req.note && (
            <p className="text-xs text-amber-700 bg-amber-50 p-2 rounded border border-amber-200">
              {req.note}
            </p>
          )}
        </div>
      </Section>

      {/* Date format section */}
      <Section icon={FileText} iconColor="text-indigo-500" title="Date Format" defaultOpen={false}>
        <p>Use: <strong className="text-slate-900">YYYY-MM-DD</strong>
          <span className="text-slate-500 ml-1">(Example: {today.toISOString().split('T')[0]})</span>
        </p>
        <div className="flex flex-wrap gap-2 mt-1">
          <span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle className="w-3 h-3" /> 2026-04-10
          </span>
          <span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle className="w-3 h-3" /> 2026/04/10
          </span>
          <span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle className="w-3 h-3" /> 10-Apr-2026
          </span>
          <span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-red-50 text-red-700 border border-red-200">
            <XCircle className="w-3 h-3" /> 10/04/26
          </span>
          <span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-red-50 text-red-700 border border-red-200">
            <XCircle className="w-3 h-3" /> April 10
          </span>
        </div>
      </Section>

      {/* Important rules */}
      <Section icon={AlertTriangle} iconColor="text-amber-500" title="Important Rules" defaultOpen={false}>
        <ul className="space-y-1.5 list-none">
          <li className="flex items-start gap-2"><span className="text-amber-500 mt-0.5">&#8226;</span> Upload data for <strong>past dates only</strong> (yesterday or earlier)</li>
          <li className="flex items-start gap-2"><span className="text-amber-500 mt-0.5">&#8226;</span> Today's data should be uploaded tomorrow</li>
          <li className="flex items-start gap-2"><span className="text-amber-500 mt-0.5">&#8226;</span> Future dates will show a warning</li>
          <li className="flex items-start gap-2"><span className="text-amber-500 mt-0.5">&#8226;</span> You can upload multiple files &mdash; we'll merge them</li>
          <li className="flex items-start gap-2"><span className="text-amber-500 mt-0.5">&#8226;</span> Duplicate dates will be replaced if "Replace existing" is checked</li>
        </ul>
      </Section>

      {/* What happens with different date ranges */}
      {req.hasDateRange && (
        <Section icon={Info} iconColor="text-sky-500" title="What Happens With Different Date Ranges" defaultOpen={false}>
          <div className="overflow-x-auto -mx-1">
            <table className="w-full text-sm border-separate border-spacing-0 rounded-lg overflow-hidden border border-slate-200">
              <thead>
                <tr className="bg-slate-50">
                  <th className="text-left px-3 py-2 font-medium text-slate-600 border-b border-slate-200 w-28">Date Range</th>
                  <th className="text-left px-3 py-2 font-medium text-slate-600 border-b border-slate-200">What You Can Do</th>
                </tr>
              </thead>
              <tbody>
                {DATE_RANGE_TABLE.map(({ range, label, icon, detail }) => (
                  <tr key={range} className="hover:bg-slate-50/50">
                    <td className="px-3 py-2 border-b border-slate-100 font-medium text-slate-800 whitespace-nowrap">{range}</td>
                    <td className="px-3 py-2 border-b border-slate-100">
                      <span className="flex items-center gap-1.5">
                        {icon === "warn" && <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />}
                        {icon === "ok" && <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0" />}
                        {icon === "best" && <CheckCircle className="w-3.5 h-3.5 text-blue-500 shrink-0" />}
                        <span>{label}</span>
                      </span>
                      <span className="text-xs text-slate-500 block mt-0.5">{detail}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}

      {/* Upload schedule and columns */}
      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 pt-1">
        <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> {req.schedule}</span>
        {req.columns && (
          <span className="flex items-center gap-1" title={req.columns}>
            <FileText className="w-3.5 h-3.5" /> Columns: {req.columns.split(",").length} required fields
          </span>
        )}
        {onDownloadTemplate && (
          <button
            onClick={onDownloadTemplate}
            className="flex items-center gap-1 text-blue-600 hover:text-blue-800 hover:underline transition-colors"
            data-testid="panel-download-template"
          >
            <Download className="w-3.5 h-3.5" /> Download Template
          </button>
        )}
      </div>
    </div>
  );
};

/* ────── Main Panel ────── */
export const DataRequirementsPanel = ({ selectedType, currentDays, onDownloadTemplate }) => {
  const req = REQUIREMENTS[selectedType];
  if (!req) return null;

  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden mb-4" data-testid="data-requirements-panel">
      {/* Header */}
      <div className="flex items-center gap-2.5 px-4 py-3 bg-gradient-to-r from-slate-50 to-white border-b border-slate-200">
        <FileText className="w-4 h-4 text-slate-500" />
        <h3 className="text-sm font-semibold text-slate-800">
          Data Requirements &mdash; {req.title}
        </h3>
      </div>
      {/* Body */}
      <div className="p-4">
        {req.isMaster ? (
          <MasterRequirements req={req} />
        ) : (
          <TransactionalRequirements
            req={req}
            currentDays={currentDays}
            onDownloadTemplate={onDownloadTemplate}
          />
        )}
      </div>
    </div>
  );
};
