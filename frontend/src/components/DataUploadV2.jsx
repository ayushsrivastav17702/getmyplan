import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./ui/card";
import { Button } from "./ui/button";
import { Progress } from "./ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Checkbox } from "./ui/checkbox";
import { Label } from "./ui/label";
import {
  Upload, FileSpreadsheet, CheckCircle, XCircle, AlertTriangle,
  Info, ChevronDown, ChevronUp,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

const API = process.env.REACT_APP_BACKEND_URL;

const SEVERITY_STYLES = {
  error: { border: "border-red-200 bg-red-50", icon: <XCircle className="w-4 h-4 text-red-500 shrink-0" /> },
  blocking: { border: "border-red-200 bg-red-50", icon: <XCircle className="w-4 h-4 text-red-500 shrink-0" /> },
  warning: { border: "border-amber-200 bg-amber-50", icon: <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" /> },
  auto_fix: { border: "border-emerald-200 bg-emerald-50", icon: <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" /> },
  auto_fixed: { border: "border-emerald-200 bg-emerald-50", icon: <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" /> },
  info: { border: "border-blue-200 bg-blue-50", icon: <Info className="w-4 h-4 text-blue-500 shrink-0" /> },
};

const DataUploadV2 = ({ onSuccess }) => {
  const { token } = useAuth();
  const [uploadType, setUploadType] = useState("daily_sales");
  const [replaceExisting, setReplaceExisting] = useState(false);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [showErrors, setShowErrors] = useState(true);
  const [showWarnings, setShowWarnings] = useState(false);
  const [showCorrections, setShowCorrections] = useState(false);

  const onDrop = useCallback((accepted) => {
    if (accepted.length > 0) {
      setFile(accepted[0]);
      setResult(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    },
    maxFiles: 1,
  });

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(10);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const iv = setInterval(() => setProgress((p) => Math.min(p + 10, 90)), 300);
      const endpoint = `${API}/api/upload/v2/${uploadType.replace(/_/g, "-")}?replace_existing=${replaceExisting}`;
      const res = await fetch(endpoint, {
        method: "POST",
        body: formData,
        headers: { Authorization: `Bearer ${token}` },
      });
      clearInterval(iv);
      setProgress(100);
      const data = await res.json();
      setResult(data);
      if (data.success) onSuccess?.();
    } catch (err) {
      setResult({
        success: false, file_name: file.name, total_rows: 0, valid_rows: 0,
        corrections: [], warnings: [],
        errors: [{ code: "NETWORK", message: "Network error. Please try again.", severity: "error" }],
        requires_approval: false, approval_items: [], preview: [],
      });
    } finally {
      setUploading(false);
    }
  };

  const sev = (s) => SEVERITY_STYLES[s] || SEVERITY_STYLES.info;

  return (
    <div className="space-y-6" data-testid="data-upload-v2">
      {/* Config */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Upload Configuration</CardTitle>
          <CardDescription>Select data type and upload options</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Data Type</Label>
              <Select value={uploadType} onValueChange={setUploadType}>
                <SelectTrigger data-testid="upload-type-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily_sales">Daily Sales</SelectItem>
                  <SelectItem value="store_inventory">Store Inventory</SelectItem>
                  <SelectItem value="warehouse_inventory">Warehouse Inventory</SelectItem>
                  <SelectItem value="sku_master">SKU Master</SelectItem>
                  <SelectItem value="store_master">Store Master</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="replace"
                  checked={replaceExisting}
                  onCheckedChange={(v) => setReplaceExisting(!!v)}
                  data-testid="replace-checkbox"
                />
                <Label htmlFor="replace">Replace existing data for same date</Label>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Dropzone */}
      <Card>
        <CardContent className="p-6">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
              ${isDragActive ? "border-blue-500 bg-blue-50" : "border-slate-300 hover:border-slate-400"}
              ${file ? "bg-slate-50" : ""}`}
            data-testid="file-dropzone"
          >
            <input {...getInputProps()} />
            <FileSpreadsheet className="w-12 h-12 mx-auto text-slate-400 mb-4" />
            {file ? (
              <div>
                <p className="text-base font-medium" data-testid="selected-file-name">{file.name}</p>
                <p className="text-sm text-slate-500">{(file.size / 1024).toFixed(1)} KB</p>
                <Button variant="outline" size="sm" className="mt-2"
                  onClick={(e) => { e.stopPropagation(); setFile(null); setResult(null); }}
                  data-testid="change-file-btn">Change File</Button>
              </div>
            ) : (
              <div>
                <p className="text-base">{isDragActive ? "Drop your file here" : "Drag & drop your CSV or Excel file here"}</p>
                <p className="text-sm text-slate-500 mt-1">or click to browse</p>
              </div>
            )}
          </div>

          {file && !uploading && !result && (
            <div className="mt-4 flex justify-end">
              <Button onClick={handleUpload} data-testid="upload-btn">
                <Upload className="w-4 h-4 mr-2" /> Upload and Validate
              </Button>
            </div>
          )}

          {uploading && (
            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-sm"><span>Processing...</span><span>{progress}%</span></div>
              <Progress value={progress} />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <Card data-testid="upload-result">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              {result.success
                ? <CheckCircle className="w-5 h-5 text-emerald-500" />
                : <XCircle className="w-5 h-5 text-red-500" />}
              Validation Results
            </CardTitle>
            <CardDescription>
              {result.total_rows} rows processed &middot; {result.valid_rows} valid
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Stats */}
            <div className="grid grid-cols-4 gap-4" data-testid="result-stats">
              <div className="text-center p-3 bg-slate-50 rounded">
                <div className="text-2xl font-bold">{result.total_rows}</div>
                <div className="text-xs text-slate-500">Total Rows</div>
              </div>
              <div className="text-center p-3 bg-emerald-50 rounded">
                <div className="text-2xl font-bold text-emerald-600">{result.valid_rows}</div>
                <div className="text-xs text-slate-500">Valid</div>
              </div>
              <div className="text-center p-3 bg-amber-50 rounded">
                <div className="text-2xl font-bold text-amber-600">{(result.warnings || []).length}</div>
                <div className="text-xs text-slate-500">Warnings</div>
              </div>
              <div className="text-center p-3 bg-red-50 rounded">
                <div className="text-2xl font-bold text-red-600">{(result.errors || []).length}</div>
                <div className="text-xs text-slate-500">Errors</div>
              </div>
            </div>

            {/* Corrections */}
            {result.corrections?.length > 0 && (
              <Section title={`Auto-Corrections (${result.corrections.length})`} open={showCorrections} toggle={setShowCorrections}>
                {result.corrections.map((c, i) => (
                  <div key={i} className={`p-2 rounded border ${sev("auto_fix").border}`}>
                    <div className="flex items-start gap-2">{sev("auto_fix").icon}<span className="text-sm">{c.action || c.message}</span></div>
                  </div>
                ))}
              </Section>
            )}

            {/* Warnings */}
            {result.warnings?.length > 0 && (
              <Section title={`Warnings (${result.warnings.length})`} open={showWarnings} toggle={setShowWarnings}>
                {result.warnings.map((w, i) => (
                  <div key={i} className={`p-2 rounded border ${sev("warning").border}`}>
                    <div className="flex items-start gap-2">{sev("warning").icon}<span className="text-sm">{w.user_message || w.message}</span></div>
                  </div>
                ))}
              </Section>
            )}

            {/* Errors */}
            {result.errors?.length > 0 && (
              <Section title={`Errors (${result.errors.length})`} open={showErrors} toggle={setShowErrors} titleCls="text-red-600">
                {result.errors.map((e, i) => (
                  <div key={i} className={`p-2 rounded border ${sev("error").border}`}>
                    <div className="flex items-start gap-2">
                      {sev("error").icon}
                      <div><span className="text-sm font-medium">{e.code}:</span> <span className="text-sm">{e.user_message || e.message}</span></div>
                    </div>
                  </div>
                ))}
              </Section>
            )}

            {/* Preview */}
            {result.preview?.length > 0 && (
              <Section title="Data Preview" open={showPreview} toggle={setShowPreview}>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm border">
                    <thead className="bg-slate-50">
                      <tr>{Object.keys(result.preview[0]).map((k) => <th key={k} className="px-3 py-2 text-left border text-xs font-medium text-slate-600">{k}</th>)}</tr>
                    </thead>
                    <tbody>
                      {result.preview.map((row, i) => (
                        <tr key={i} className="border-t">
                          {Object.values(row).map((v, j) => <td key={j} className="px-3 py-1 border text-xs">{String(v)}</td>)}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Section>
            )}

            {/* Actions */}
            {result.success && (
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => { setFile(null); setResult(null); }} data-testid="upload-another-btn">Upload Another File</Button>
              </div>
            )}
            {!result.success && result.errors?.length > 0 && (
              <div className="flex justify-end">
                <Button variant="outline" onClick={() => setResult(null)} data-testid="retry-btn">Fix Errors and Retry</Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

const Section = ({ title, open, toggle, titleCls, children }) => (
  <div>
    <button className={`flex items-center gap-2 text-sm font-medium hover:opacity-80 ${titleCls || "text-slate-700"}`} onClick={() => toggle(!open)}>
      {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />} {title}
    </button>
    {open && <div className="mt-2 space-y-1 max-h-60 overflow-y-auto">{children}</div>}
  </div>
);

export default DataUploadV2;
