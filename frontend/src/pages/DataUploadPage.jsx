import React, { useState, useEffect, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import {
  Package, Store, Warehouse, FileText, CheckCircle, AlertTriangle,
  Upload, Download, ChevronRight, ChevronDown, ChevronUp, RefreshCw,
  Save, X, Eye, XCircle, Info,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

const API = process.env.REACT_APP_BACKEND_URL;

/* ════════════════════════════════════════════════════════════
   MAIN PAGE
   ════════════════════════════════════════════════════════════ */
const DataUploadPage = () => {
  const { token } = useAuth();
  const [dailyStatus, setDailyStatus] = useState(null);
  const [masterStatus, setMasterStatus] = useState(null);
  const [previousDays, setPreviousDays] = useState([]);

  const [selectedType, setSelectedType] = useState("daily_sales");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [showSaveConfirm, setShowSaveConfirm] = useState(false);

  const hdrs = { Authorization: `Bearer ${token}` };

  useEffect(() => { refresh(); }, []);

  const refresh = () => {
    fetchDailyStatus();
    fetchMasterStatus();
    fetchHistory();
  };

  const fetchDailyStatus = async () => {
    try {
      const r = await fetch(`${API}/api/upload/v2/daily-status`, { headers: hdrs });
      setDailyStatus(await r.json());
    } catch (e) { console.error(e); }
  };

  const fetchMasterStatus = async () => {
    try {
      const r = await fetch(`${API}/api/upload/v2/master-status`, { headers: hdrs });
      setMasterStatus(await r.json());
    } catch (e) { console.error(e); }
  };

  const fetchHistory = async () => {
    try {
      const r = await fetch(`${API}/api/upload/v2/history?days=7`, { headers: hdrs });
      const d = await r.json();
      setPreviousDays((d.history || []).filter((h) => h.label !== "Today"));
    } catch (e) { console.error(e); }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(10);
    const fd = new FormData();
    fd.append("file", file);

    try {
      const iv = setInterval(() => setProgress((p) => Math.min(p + 12, 90)), 250);
      const slug = selectedType.replace(/_/g, "-");
      const r = await fetch(`${API}/api/upload/v2/${slug}?replace_existing=true`, {
        method: "POST", body: fd, headers: hdrs,
      });
      clearInterval(iv);
      setProgress(100);
      const data = await r.json();
      setResult(data);
      if (data.success) {
        setShowSaveConfirm(false);
        refresh();
      }
    } catch {
      setResult({ success: false, errors: [{ code: "NET", message: "Network error" }], total_rows: 0, valid_rows: 0, corrections: [], warnings: [], preview: [] });
    } finally {
      setUploading(false);
    }
  };

  const allDone = dailyStatus &&
    dailyStatus.daily_sales?.uploaded &&
    dailyStatus.store_inventory?.uploaded &&
    dailyStatus.warehouse_inventory?.uploaded;

  const downloadTemplate = (t) => window.open(`${API}/api/upload/v2/template/${t}`, "_blank");

  return (
    <div className="space-y-8" data-testid="data-upload-page">
      {/* Header */}
      <div className="flex justify-between items-center flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Data Upload</h1>
          <p className="text-sm text-slate-500 mt-1">Manage master data and upload daily transactions</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => downloadTemplate("daily_sales")} data-testid="dl-sales-tpl">
            <Download className="w-4 h-4 mr-1" /> Sales Template
          </Button>
          <Button variant="outline" size="sm" onClick={() => downloadTemplate("store_inventory")} data-testid="dl-inv-tpl">
            <Download className="w-4 h-4 mr-1" /> Inventory Template
          </Button>
        </div>
      </div>

      {/* ═══════ SECTION 1: MASTER DATA ═══════ */}
      <section data-testid="master-data-section">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-violet-100 rounded-lg"><Package className="w-5 h-5 text-violet-600" /></div>
          <h2 className="text-lg font-semibold text-slate-900">Master Data</h2>
          <span className="text-xs text-slate-400 ml-1">Setup once &mdash; rarely changes</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MasterCard icon={Package} color="blue" title="SKU Master" desc="Products & pricing"
            count={masterStatus?.sku_master?.count} updated={masterStatus?.sku_master?.last_updated}
            onUpload={() => { setSelectedType("sku_master"); setFile(null); setResult(null); }}
            onDownload={() => downloadTemplate("sku_master")} />
          <MasterCard icon={Store} color="emerald" title="Store Master" desc="Store locations"
            count={masterStatus?.store_master?.count} updated={masterStatus?.store_master?.last_updated}
            onUpload={() => { setSelectedType("store_master"); setFile(null); setResult(null); }}
            onDownload={() => downloadTemplate("store_master")} />
          <MasterCard icon={Warehouse} color="violet" title="Warehouse Master" desc="Warehouses & capacity"
            count={masterStatus?.warehouse_master?.count} updated={masterStatus?.warehouse_master?.last_updated}
            onUpload={() => { setSelectedType("warehouse_master"); setFile(null); setResult(null); }}
            onDownload={() => downloadTemplate("warehouse_master")} />
        </div>
      </section>

      {/* ═══════ SECTION 2: TODAY'S STATUS ═══════ */}
      <section data-testid="daily-status-section">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-100 rounded-lg"><CheckCircle className="w-5 h-5 text-emerald-600" /></div>
            <h2 className="text-lg font-semibold text-slate-900">
              Today's Status &mdash; {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
            </h2>
          </div>
          <Button variant="ghost" size="sm" onClick={fetchDailyStatus} data-testid="refresh-daily-btn">
            <RefreshCw className="w-4 h-4 mr-1" /> Refresh
          </Button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { key: "daily_sales", label: "Daily Sales", Icon: FileText },
            { key: "store_inventory", label: "Store Inventory", Icon: Store },
            { key: "warehouse_inventory", label: "Warehouse Inventory", Icon: Warehouse },
          ].map(({ key, label, Icon }) => (
            <DailyCard key={key} label={label} Icon={Icon} data={dailyStatus?.[key]}
              onUploadNow={() => { setSelectedType(key); setFile(null); setResult(null); }} />
          ))}
        </div>
        {allDone && (
          <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-2" data-testid="all-complete-banner">
            <CheckCircle className="w-5 h-5 text-emerald-600" />
            <span className="text-emerald-800 font-medium text-sm">All daily data uploaded for today</span>
          </div>
        )}
      </section>

      {/* ═══════ SECTION 3: UPLOAD NEW DATA ═══════ */}
      <section data-testid="upload-section">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="p-2 bg-blue-100 rounded-lg"><Upload className="w-5 h-5 text-blue-600" /></div>
              <h2 className="text-lg font-semibold text-slate-900">Upload New Data</h2>
            </div>

            {/* Type selector */}
            <div className="mb-4 max-w-xs">
              <label className="block text-sm font-medium text-slate-700 mb-1">Data Type</label>
              <Select value={selectedType} onValueChange={(v) => { setSelectedType(v); setFile(null); setResult(null); }}>
                <SelectTrigger data-testid="upload-type-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily_sales">Daily Sales</SelectItem>
                  <SelectItem value="store_inventory">Store Inventory</SelectItem>
                  <SelectItem value="warehouse_inventory">Warehouse Inventory</SelectItem>
                  <SelectItem value="sku_master">SKU Master</SelectItem>
                  <SelectItem value="store_master">Store Master</SelectItem>
                  <SelectItem value="warehouse_master">Warehouse Master</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Dropzone */}
            <Dropzone file={file} onFile={(f) => { setFile(f); setResult(null); setShowSaveConfirm(false); }} />

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

            {/* Upload button */}
            {file && !uploading && !result && (
              <div className="mt-4 flex justify-end">
                <Button onClick={handleUpload} data-testid="validate-upload-btn">
                  <Upload className="w-4 h-4 mr-2" /> Upload & Validate
                </Button>
              </div>
            )}

            {/* Progress */}
            {uploading && (
              <div className="mt-4 space-y-2">
                <div className="flex justify-between text-sm text-slate-600"><span>Processing...</span><span>{progress}%</span></div>
                <Progress value={progress} />
              </div>
            )}

            {/* Validation Results */}
            {result && <ValidationResults result={result} onSave={() => setShowSaveConfirm(true)} onRetry={() => { setResult(null); setFile(null); }} />}

            {/* Explicit SAVE confirmation */}
            {showSaveConfirm && result?.success && (
              <div className="mt-4 p-4 border-2 border-emerald-300 rounded-lg bg-emerald-50/50" data-testid="save-confirm">
                <p className="font-medium text-slate-900 mb-3">
                  Ready to save {result.valid_rows} rows to today's {selectedType.replace(/_/g, " ")}?
                </p>
                <div className="flex gap-3">
                  <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={() => { setShowSaveConfirm(false); refresh(); setFile(null); setResult(null); }} data-testid="confirm-save-btn">
                    <Save className="w-4 h-4 mr-2" /> Save Today's Data
                  </Button>
                  <Button variant="outline" onClick={() => setShowSaveConfirm(false)}><X className="w-4 h-4 mr-2" /> Cancel</Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      {/* ═══════ SECTION 4: PREVIOUS DAYS ═══════ */}
      <section data-testid="previous-days-section">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-slate-900">Previous Days</h3>
        </div>
        {previousDays.length === 0 ? (
          <Card><CardContent className="p-6 text-center text-slate-500 text-sm">No previous upload history.</CardContent></Card>
        ) : (
          <Card>
            <CardContent className="p-0 divide-y divide-slate-100">
              {previousDays.slice(0, 5).map((day) => (
                <div key={day.date} className="px-4 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="font-medium text-sm text-slate-800 w-28">{day.label}</span>
                    <span className="text-xs text-slate-400">{day.date}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusDot uploaded={!!day.uploads?.daily_sales} label="Sales" />
                    <StatusDot uploaded={!!day.uploads?.store_inventory} label="Store" />
                    <StatusDot uploaded={!!day.uploads?.warehouse_inventory} label="WH" />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </section>
    </div>
  );
};

/* ════════════════════════════════════════════════════════════
   SUB-COMPONENTS
   ════════════════════════════════════════════════════════════ */

const MasterCard = ({ icon: Icon, color, title, desc, count, updated, onUpload, onDownload }) => {
  const bg = { blue: "bg-blue-100", emerald: "bg-emerald-100", violet: "bg-violet-100" }[color] || "bg-slate-100";
  const fg = { blue: "text-blue-600", emerald: "text-emerald-600", violet: "text-violet-600" }[color] || "text-slate-600";
  return (
    <Card data-testid={`master-${title.toLowerCase().replace(/ /g, "-")}`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`p-2 ${bg} rounded-lg`}><Icon className={`w-5 h-5 ${fg}`} /></div>
            <div>
              <h3 className="font-medium text-slate-900 text-sm">{title}</h3>
              <p className="text-xs text-slate-500">{desc}</p>
            </div>
          </div>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <span className="text-2xl font-bold text-slate-900">{count ?? 0}</span>
            <span className="text-xs text-slate-400 ml-2">{updated ? `Updated ${updated}` : "Not set up"}</span>
          </div>
          <div className="flex gap-1">
            <Button variant="ghost" size="sm" onClick={onDownload} title="Download template"><Download className="w-4 h-4" /></Button>
            <Button variant="ghost" size="sm" onClick={onUpload} title="Upload"><Upload className="w-4 h-4" /></Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const DailyCard = ({ label, Icon, data, onUploadNow }) => (
  <Card data-testid={`daily-card-${label.toLowerCase().replace(/ /g, "-")}`}>
    <CardContent className="p-4">
      <div className="flex items-center gap-2 mb-3">
        <Icon className="w-4 h-4 text-slate-500" />
        <h4 className="font-medium text-slate-900 text-sm">{label}</h4>
      </div>
      {data?.uploaded ? (
        <>
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle className="w-4 h-4 text-emerald-500" />
            <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200" variant="outline">Uploaded</Badge>
          </div>
          <p className="text-xs text-slate-600">{data.time} &middot; {data.rows} rows</p>
        </>
      ) : (
        <>
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            <Badge className="bg-amber-50 text-amber-700 border-amber-200" variant="outline">Not Uploaded</Badge>
          </div>
          <Button variant="link" size="sm" className="p-0 h-auto text-blue-600" onClick={onUploadNow}>
            Upload Now <ChevronRight className="w-3 h-3 ml-1" />
          </Button>
        </>
      )}
    </CardContent>
  </Card>
);

const Dropzone = ({ file, onFile }) => {
  const onDrop = useCallback((a) => a[0] && onFile(a[0]), [onFile]);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"] },
    maxFiles: 1,
  });
  return (
    <div {...getRootProps()} data-testid="file-dropzone"
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
        ${isDragActive ? "border-blue-500 bg-blue-50" : "border-slate-300 hover:border-slate-400"}
        ${file ? "bg-slate-50" : ""}`}>
      <input {...getInputProps()} />
      <Upload className="w-10 h-10 mx-auto text-slate-400 mb-3" />
      {file ? (
        <div>
          <p className="font-medium text-sm" data-testid="selected-file-name">{file.name}</p>
          <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</p>
          <Button variant="outline" size="sm" className="mt-2"
            onClick={(e) => { e.stopPropagation(); onFile(null); }}
            data-testid="change-file-btn">Change File</Button>
        </div>
      ) : (
        <div>
          <p className="text-sm text-slate-700">{isDragActive ? "Drop your file here" : "Drag & drop or click to browse"}</p>
          <p className="text-xs text-slate-400 mt-1">CSV or Excel (max 50 MB)</p>
        </div>
      )}
    </div>
  );
};

const SEVERITY = {
  error: { cls: "border-red-200 bg-red-50", icon: <XCircle className="w-4 h-4 text-red-500 shrink-0" /> },
  blocking: { cls: "border-red-200 bg-red-50", icon: <XCircle className="w-4 h-4 text-red-500 shrink-0" /> },
  warning: { cls: "border-amber-200 bg-amber-50", icon: <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" /> },
  auto_fix: { cls: "border-emerald-200 bg-emerald-50", icon: <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" /> },
  auto_fixed: { cls: "border-emerald-200 bg-emerald-50", icon: <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" /> },
  info: { cls: "border-blue-200 bg-blue-50", icon: <Info className="w-4 h-4 text-blue-500 shrink-0" /> },
};
const sev = (s) => SEVERITY[s] || SEVERITY.info;

const ValidationResults = ({ result, onSave, onRetry }) => {
  const [showC, setShowC] = useState(false);
  const [showW, setShowW] = useState(false);
  const [showE, setShowE] = useState(true);
  const [showP, setShowP] = useState(false);

  return (
    <div className="mt-6 space-y-4" data-testid="validation-results">
      {/* Summary bar */}
      <div className="flex items-center gap-2">
        {result.success ? <CheckCircle className="w-5 h-5 text-emerald-500" /> : <XCircle className="w-5 h-5 text-red-500" />}
        <span className="font-semibold text-sm">Validation Results</span>
        <span className="text-xs text-slate-500">{result.total_rows} rows &middot; {result.valid_rows} valid</span>
      </div>

      {/* Stat boxes */}
      <div className="grid grid-cols-4 gap-3">
        <StatBox label="Total" value={result.total_rows} />
        <StatBox label="Valid" value={result.valid_rows} color="emerald" />
        <StatBox label="Warnings" value={(result.warnings || []).length} color="amber" />
        <StatBox label="Errors" value={(result.errors || []).length} color="red" />
      </div>

      {/* Collapsible sections */}
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

      {/* Action buttons */}
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

const StatBox = ({ label, value, color = "slate" }) => {
  const cls = { emerald: "text-emerald-600", amber: "text-amber-600", red: "text-red-600", slate: "text-slate-900" }[color];
  return (
    <div className="text-center p-2 bg-white rounded border">
      <div className={`text-xl font-bold ${cls}`}>{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  );
};

const Toggle = ({ title, open, onToggle, titleCls, children }) => (
  <div>
    <button className={`flex items-center gap-2 text-sm font-medium hover:opacity-80 ${titleCls || "text-slate-700"}`} onClick={() => onToggle(!open)}>
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

const StatusDot = ({ uploaded, label }) => (
  <div className="flex items-center gap-1.5">
    <div className={`w-2 h-2 rounded-full ${uploaded ? "bg-emerald-500" : "bg-slate-300"}`} />
    <span className="text-xs text-slate-500">{label}</span>
  </div>
);

export default DataUploadPage;
