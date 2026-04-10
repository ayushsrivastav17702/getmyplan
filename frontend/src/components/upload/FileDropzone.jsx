import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import {
  Upload, Save, X, CheckCircle, XCircle, AlertTriangle,
  ChevronUp, ChevronDown, Info, Calendar,
} from "lucide-react";
import { Button } from "../ui/button";
import { Progress } from "../ui/progress";

const SEVERITY = {
  error: { cls: "border-red-200 bg-red-50", icon: <XCircle className="w-4 h-4 text-red-500 shrink-0" /> },
  blocking: { cls: "border-red-200 bg-red-50", icon: <XCircle className="w-4 h-4 text-red-500 shrink-0" /> },
  warning: { cls: "border-amber-200 bg-amber-50", icon: <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" /> },
  auto_fix: { cls: "border-emerald-200 bg-emerald-50", icon: <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" /> },
  auto_fixed: { cls: "border-emerald-200 bg-emerald-50", icon: <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" /> },
  info: { cls: "border-blue-200 bg-blue-50", icon: <Info className="w-4 h-4 text-blue-500 shrink-0" /> },
};
const sev = (s) => SEVERITY[s] || SEVERITY.info;

const Toggle = ({ title, open, onToggle, titleCls, children }) => (
  <div>
    <button
      className={`flex items-center gap-2 text-sm font-medium hover:opacity-80 ${titleCls || "text-slate-700"}`}
      onClick={() => onToggle(!open)}
    >
      {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />} {title}
    </button>
    {open && <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">{children}</div>}
  </div>
);

const Row = ({ sev: s, children }) => (
  <div className={`p-2 rounded border ${sev(s).cls}`}>
    <div className="flex items-start gap-2">{sev(s).icon}<span className="text-sm">{children}</span></div>
  </div>
);

const StatBox = ({ label, value, color = "slate" }) => {
  const cls = { emerald: "text-emerald-600", amber: "text-amber-600", red: "text-red-600", slate: "text-slate-900" }[color];
  return (
    <div className="text-center p-2 bg-white rounded border">
      <div className={`text-xl font-bold ${cls}`}>{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  );
};

/* ─── Validation Results ─── */
const ValidationResults = ({ result, onSave, onRetry }) => {
  const [showC, setShowC] = useState(false);
  const [showW, setShowW] = useState(false);
  const [showE, setShowE] = useState(true);
  const [showP, setShowP] = useState(false);

  return (
    <div className="mt-6 space-y-4" data-testid="validation-results">
      <div className="flex items-center gap-2">
        {result.success ? <CheckCircle className="w-5 h-5 text-emerald-500" /> : <XCircle className="w-5 h-5 text-red-500" />}
        <span className="font-semibold text-sm">Validation Results</span>
        <span className="text-xs text-slate-500">{result.total_rows} rows &middot; {result.valid_rows} valid</span>
      </div>

      <div className="grid grid-cols-4 gap-3">
        <StatBox label="Total" value={result.total_rows} />
        <StatBox label="Valid" value={result.valid_rows} color="emerald" />
        <StatBox label="Warnings" value={(result.warnings || []).length} color="amber" />
        <StatBox label="Errors" value={(result.errors || []).length} color="red" />
      </div>

      {result.corrections?.length > 0 && (
        <Toggle title={`Auto-Corrections (${result.corrections.length})`} open={showC} onToggle={setShowC}>
          {result.corrections.map((c, i) => <Row key={i} sev="auto_fix">{c.action || c.message}</Row>)}
        </Toggle>
      )}
      {result.warnings?.length > 0 && (
        <Toggle title={`Warnings (${result.warnings.length})`} open={showW} onToggle={setShowW}>
          {result.warnings.map((w, i) => <Row key={i} sev="warning">{w.user_message || w.message}</Row>)}
        </Toggle>
      )}
      {result.errors?.length > 0 && (
        <Toggle title={`Errors (${result.errors.length})`} open={showE} onToggle={setShowE} titleCls="text-red-600">
          {result.errors.map((e, i) => <Row key={i} sev="error"><b>{e.code}:</b> {e.user_message || e.message}</Row>)}
        </Toggle>
      )}
      {result.preview?.length > 0 && (
        <Toggle title="Data Preview" open={showP} onToggle={setShowP}>
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs border">
              <thead className="bg-slate-50">
                <tr>{Object.keys(result.preview[0]).map((k) => <th key={k} className="px-2 py-1 text-left border font-medium text-slate-600">{k}</th>)}</tr>
              </thead>
              <tbody>{result.preview.map((r, i) => <tr key={i} className="border-t">{Object.values(r).map((v, j) => <td key={j} className="px-2 py-1 border">{String(v)}</td>)}</tr>)}</tbody>
            </table>
          </div>
        </Toggle>
      )}

      {result.success ? (
        <div className="flex justify-end">
          <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={onSave} data-testid="proceed-save-btn">
            <Save className="w-4 h-4 mr-2" /> Proceed to Save
          </Button>
        </div>
      ) : (
        <div className="flex justify-end">
          <Button variant="outline" onClick={onRetry} data-testid="retry-btn">Fix Errors & Retry</Button>
        </div>
      )}
    </div>
  );
};

/* ─── Main FileDropzone ─── */
export const FileDropzone = ({
  file, onFile, selectedType, dailyStatus,
  uploading, progress, result,
  showSaveConfirm, onValidate, onSave, onCancelSave,
  onRetry, onShowSaveConfirm,
}) => {
  const onDrop = useCallback((a) => a[0] && onFile(a[0]), [onFile]);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    },
    maxFiles: 1,
  });

  /* Expected date range for transactional types */
  const TRANSACTIONAL = ["daily_sales", "store_inventory", "warehouse_inventory", "cogs", "open_orders"];
  const isTransactional = TRANSACTIONAL.includes(selectedType);
  const today = new Date();
  const d90 = new Date(today); d90.setDate(d90.getDate() - 90);
  const yesterday = new Date(today); yesterday.setDate(yesterday.getDate() - 1);
  const fmt = (d) => d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });

  return (
    <>
      {/* Dropzone */}
      <div
        {...getRootProps()}
        data-testid="file-dropzone"
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive ? "border-blue-500 bg-blue-50" : "border-slate-300 hover:border-slate-400"}
          ${file ? "bg-slate-50" : ""}`}
      >
        <input {...getInputProps()} />
        <Upload className="w-10 h-10 mx-auto text-slate-400 mb-3" />
        {file ? (
          <div>
            <p className="font-medium text-sm" data-testid="selected-file-name">{file.name}</p>
            <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</p>
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={(e) => { e.stopPropagation(); onFile(null); }}
              data-testid="change-file-btn"
            >
              Change File
            </Button>
          </div>
        ) : (
          <div>
            <p className="text-sm text-slate-700">
              {isDragActive ? "Drop your file here" : "Drag & drop or click to browse"}
            </p>
            <p className="text-xs text-slate-400 mt-1">CSV or Excel (max 50 MB)</p>
          </div>
        )}
      </div>

      {/* Expected date range hint */}
      {isTransactional && !file && (
        <div className="mt-2 flex items-center gap-2 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-600" data-testid="expected-date-hint">
          <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span>
            Expected date range in your file: <strong>{fmt(d90)} &mdash; {fmt(yesterday)}</strong>
          </span>
          <span className="text-slate-400 ml-auto hidden sm:inline">Different dates? We'll show a warning but still accept it.</span>
        </div>
      )}

      {/* Replace warning */}
      {file && dailyStatus?.[selectedType]?.uploaded && (
        <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
          <div>
            <p className="font-medium text-amber-800 text-sm">This will replace today's existing data</p>
            <p className="text-xs text-amber-700">
              You already uploaded {selectedType.replace(/_/g, " ")} at {dailyStatus[selectedType].time}.
            </p>
          </div>
        </div>
      )}

      {/* Validate button */}
      {file && !uploading && !result && (
        <div className="mt-4 flex justify-end">
          <Button onClick={onValidate} data-testid="validate-upload-btn">
            <Upload className="w-4 h-4 mr-2" /> Validate File
          </Button>
        </div>
      )}

      {/* Progress */}
      {uploading && (
        <div className="mt-4 space-y-2">
          <div className="flex justify-between text-sm text-slate-600">
            <span>Processing...</span>
            <span>{progress}%</span>
          </div>
          <Progress value={progress} />
        </div>
      )}

      {/* Validation Results */}
      {result && !showSaveConfirm && (
        <ValidationResults result={result} onSave={onShowSaveConfirm} onRetry={onRetry} />
      )}

      {/* Save confirmation */}
      {showSaveConfirm && result?.success && (
        <div className="mt-4 p-4 border-2 border-emerald-300 rounded-lg bg-emerald-50/50" data-testid="save-confirm">
          <p className="font-medium text-slate-900 mb-3">
            Ready to save {result.valid_rows} rows to today's {selectedType.replace(/_/g, " ")}?
          </p>
          <div className="flex gap-3">
            <Button
              className="bg-emerald-600 hover:bg-emerald-700"
              onClick={onSave}
              disabled={uploading}
              data-testid="confirm-save-btn"
            >
              <Save className="w-4 h-4 mr-2" /> {uploading ? "Saving..." : "Save Today's Data"}
            </Button>
            <Button variant="outline" onClick={onCancelSave}>
              <X className="w-4 h-4 mr-2" /> Cancel
            </Button>
          </div>
        </div>
      )}
    </>
  );
};
