import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import Papa from "papaparse";
import {
  Upload, CheckCircle, AlertCircle, X, FileText,
  Trash2, Eye, EyeOff, Download, RefreshCw,
  Database, Calendar, Clock, Info
} from "lucide-react";

const MASTER_FILES = [
  {
    key: "style_master",
    name: "Style Master",
    description: "Style codes, brands, categories, gender, season",
    frequency: "one-time",
  },
  {
    key: "sku_ean_master",
    name: "SKU-EAN Master",
    description: "SKU to EAN mapping with sizes and MRP",
    frequency: "one-time",
  },
  {
    key: "store_master",
    name: "Store Master",
    description: "Store information and hierarchy",
    frequency: "one-time",
  },
  {
    key: "warehouse_master",
    name: "Warehouse Master",
    description: "Warehouse information and hierarchy",
    frequency: "one-time",
  },
];

const DAILY_FILES = [
  {
    key: "daily_sales",
    name: "Daily Sales",
    description: "Transaction-level sales data for yesterday",
    frequency: "daily",
  },
  {
    key: "store_inventory",
    name: "Store Inventory",
    description: "Current store stock levels (end of day)",
    frequency: "daily",
  },
  {
    key: "warehouse_inventory",
    name: "Warehouse Inventory",
    description: "Current warehouse stock levels (end of day)",
    frequency: "daily",
  },
];

const ALL_FILES = [...MASTER_FILES, ...DAILY_FILES];

const DataUpload = ({ onUploadComplete }) => {
  const [uploadStatus, setUploadStatus] = useState({});
  const [uploading, setUploading] = useState({});
  const [preview, setPreview] = useState({});
  const [showPreview, setShowPreview] = useState({});
  const [dragActive, setDragActive] = useState({});
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/upload/status`);
      setUploadStatus(response.data);
    } catch (error) {
      console.error("Error fetching upload status:", error);
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const response = await axios.get(`${API}/upload/history?limit=50`);
      setHistory(response.data);
    } catch (error) {
      console.error("Error fetching history:", error);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    fetchHistory();
  }, [fetchStatus, fetchHistory]);

  const handleDrag = (e, fileKey, active) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive((prev) => ({ ...prev, [fileKey]: active }));
  };

  const handleDrop = (e, fileKey) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive((prev) => ({ ...prev, [fileKey]: false }));
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(fileKey, e.dataTransfer.files[0]);
    }
  };

  const handleFileUpload = async (fileKey, file) => {
    if (!file) return;

    // Client-side file size validation (100 MB limit)
    const MAX_SIZE_MB = 100;
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setUploadStatus((prev) => ({
        ...prev,
        [fileKey]: {
          uploaded: false,
          valid: false,
          errors: [`File too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum allowed is ${MAX_SIZE_MB} MB.`],
        },
      }));
      return;
    }

    // Client-side extension validation
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['csv', 'xlsx', 'xls'].includes(ext)) {
      setUploadStatus((prev) => ({
        ...prev,
        [fileKey]: {
          uploaded: false,
          valid: false,
          errors: [`Unsupported file format (.${ext}). Accepted: .csv, .xlsx, .xls`],
        },
      }));
      return;
    }

    setUploading((prev) => ({ ...prev, [fileKey]: true }));

    if (file.name.endsWith(".csv")) {
      Papa.parse(file, {
        preview: 5,
        header: true,
        complete: (results) => {
          setPreview((prev) => ({ ...prev, [fileKey]: results.data }));
        },
      });
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(`${API}/upload/${fileKey}`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setUploadStatus((prev) => ({
        ...prev,
        [fileKey]: {
          uploaded: true,
          valid: response.data.valid,
          rows: response.data.rows,
          columns: response.data.columns,
          errors: response.data.errors,
          warnings: response.data.warnings || [],
          duplicates_removed: response.data.duplicates_removed || 0,
          encoding: response.data.encoding,
          preview: response.data.preview,
          uploaded_at: new Date().toISOString(),
        },
      }));

      if (response.data.preview) {
        setPreview((prev) => ({ ...prev, [fileKey]: response.data.preview }));
      }

      fetchHistory();
      if (onUploadComplete) onUploadComplete();
    } catch (error) {
      console.error("Upload error:", error);
      setUploadStatus((prev) => ({
        ...prev,
        [fileKey]: {
          uploaded: false,
          valid: false,
          errors: [error.response?.data?.detail || "Upload failed"],
        },
      }));
      fetchHistory();
    } finally {
      setUploading((prev) => ({ ...prev, [fileKey]: false }));
    }
  };

  const handleDelete = async (fileKey) => {
    try {
      await axios.delete(`${API}/upload/${fileKey}`);
      setUploadStatus((prev) => {
        const next = { ...prev };
        delete next[fileKey];
        return next;
      });
      setPreview((prev) => {
        const next = { ...prev };
        delete next[fileKey];
        return next;
      });
      if (onUploadComplete) onUploadComplete();
    } catch (error) {
      console.error("Delete error:", error);
    }
  };

  const handleClearAll = async () => {
    try {
      await axios.delete(`${API}/upload/all`);
      setUploadStatus({});
      setPreview({});
      if (onUploadComplete) onUploadComplete();
    } catch (error) {
      console.error("Clear all error:", error);
    }
  };

  const downloadTemplate = async (fileKey) => {
    try {
      const response = await axios.get(`${API}/upload/template/${fileKey}`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `${fileKey}_template.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Template download error:", err);
    }
  };

  const masterUploaded = MASTER_FILES.filter(
    (f) => uploadStatus[f.key]?.uploaded && uploadStatus[f.key]?.valid
  ).length;
  const dailyUploaded = DAILY_FILES.filter(
    (f) => uploadStatus[f.key]?.uploaded && uploadStatus[f.key]?.valid
  ).length;
  const totalUploaded = masterUploaded + dailyUploaded;

  const formatTimeAgo = (isoStr) => {
    if (!isoStr) return "";
    const diff = Date.now() - new Date(isoStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  const friendlyName = (key) =>
    ALL_FILES.find((f) => f.key === key)?.name || key;

  // -- Render helpers --

  const FrequencyBadge = ({ frequency }) =>
    frequency === "one-time" ? (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-200">
        <Database size={10} />
        Master
      </span>
    ) : (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-amber-50 text-amber-700 border border-amber-200">
        <Calendar size={10} />
        Daily
      </span>
    );

  const FileCard = ({ file }) => {
    const status = uploadStatus[file.key];
    const isUploading = uploading[file.key];
    const isDragOver = dragActive[file.key];
    const previewData = preview[file.key];
    const isPreviewing = showPreview[file.key];
    const isValid = status?.uploaded && status?.valid;

    return (
      <div
        data-testid={`upload-card-${file.key}`}
        className="bg-white border border-slate-200 rounded-lg overflow-hidden transition-shadow hover:shadow-sm"
      >
        {/* Header */}
        <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <div
              className={`p-1.5 rounded ${
                isValid ? "bg-green-50" : "bg-slate-50"
              }`}
            >
              <FileText
                size={18}
                className={isValid ? "text-green-600" : "text-slate-400"}
              />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-semibold text-sm text-slate-900 truncate">
                  {file.name}
                </h3>
                <FrequencyBadge frequency={file.frequency} />
              </div>
              <p className="text-xs text-slate-500 truncate">{file.description}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {isValid && (
              <CheckCircle size={18} className="text-green-500" />
            )}
            {status?.uploaded && !status?.valid && (
              <AlertCircle size={18} className="text-amber-500" />
            )}
          </div>
        </div>

        {/* Drop zone */}
        <div
          className={`relative px-4 py-5 flex flex-col items-center justify-center gap-2 border-b border-slate-100 transition-colors ${
            isDragOver
              ? "bg-blue-50 border-blue-300"
              : isValid
              ? "bg-green-50/30"
              : "bg-slate-50/50"
          }`}
          onDragEnter={(e) => handleDrag(e, file.key, true)}
          onDragLeave={(e) => handleDrag(e, file.key, false)}
          onDragOver={(e) => handleDrag(e, file.key, true)}
          onDrop={(e) => handleDrop(e, file.key)}
        >
          {isUploading ? (
            <div className="flex flex-col items-center gap-2">
              <RefreshCw size={24} className="text-blue-500 animate-spin" />
              <span className="text-xs text-slate-500">Uploading...</span>
            </div>
          ) : isValid ? (
            <div className="flex flex-col items-center gap-1">
              <CheckCircle size={28} className="text-green-500" />
              <span className="text-sm font-medium text-green-700">
                {status.rows?.toLocaleString()} rows
              </span>
              <span className="text-[10px] text-slate-400">
                {status.columns?.length} columns
                {status.duplicates_removed > 0 && ` · ${status.duplicates_removed} dupes removed`}
                {status.encoding && ` · ${status.encoding}`}
                {status.uploaded_at && ` · ${formatTimeAgo(status.uploaded_at)}`}
              </span>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <Upload
                size={28}
                className={isDragOver ? "text-blue-400" : "text-slate-300"}
              />
              <p className="text-xs text-slate-500 text-center">
                Drag & drop CSV here
              </p>
              <label className="text-xs text-[var(--sf-primary)] hover:underline cursor-pointer font-medium">
                or browse to upload
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  className="hidden"
                  data-testid={`file-input-${file.key}`}
                  onChange={(e) =>
                    handleFileUpload(file.key, e.target.files[0])
                  }
                />
              </label>
            </div>
          )}
        </div>

        {/* Errors */}
        {status?.errors?.length > 0 && (
          <div className="px-4 py-2 bg-red-50 border-b border-red-100" data-testid={`errors-${file.key}`}>
            {status.errors.map((err, i) => (
              <p
                key={i}
                className="text-xs text-red-600 flex items-center gap-1.5"
              >
                <AlertCircle size={12} />
                {err}
              </p>
            ))}
          </div>
        )}

        {/* Warnings (duplicates, extra columns, etc.) */}
        {status?.warnings?.length > 0 && (
          <div className="px-4 py-2 bg-amber-50 border-b border-amber-100" data-testid={`warnings-${file.key}`}>
            {status.warnings.map((w, i) => (
              <p key={i} className="text-xs text-amber-600 flex items-center gap-1.5">
                <AlertCircle size={12} />
                {w}
              </p>
            ))}
          </div>
        )}

        {/* Footer actions */}
        <div className="px-4 py-2 flex items-center gap-3 text-xs">
          <button
            data-testid={`template-btn-${file.key}`}
            onClick={() => downloadTemplate(file.key)}
            className="flex items-center gap-1 text-slate-500 hover:text-blue-600 transition-colors"
          >
            <Download size={12} />
            Template
          </button>
          {previewData && (
            <button
              data-testid={`preview-btn-${file.key}`}
              onClick={() =>
                setShowPreview((p) => ({ ...p, [file.key]: !isPreviewing }))
              }
              className="flex items-center gap-1 text-slate-500 hover:text-blue-600 transition-colors"
            >
              {isPreviewing ? <EyeOff size={12} /> : <Eye size={12} />}
              {isPreviewing ? "Hide" : "Preview"}
            </button>
          )}
          {isValid && (
            <label className="flex items-center gap-1 text-slate-500 hover:text-blue-600 transition-colors cursor-pointer">
              <RefreshCw size={12} />
              Re-upload
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                className="hidden"
                onChange={(e) =>
                  handleFileUpload(file.key, e.target.files[0])
                }
              />
            </label>
          )}
          {status?.uploaded && (
            <button
              data-testid={`delete-btn-${file.key}`}
              onClick={() => handleDelete(file.key)}
              className="flex items-center gap-1 text-red-400 hover:text-red-600 transition-colors ml-auto"
            >
              <X size={12} />
              Remove
            </button>
          )}
        </div>

        {/* Preview Table */}
        {isPreviewing && previewData && (
          <div className="px-4 py-3 border-t border-slate-100 overflow-x-auto">
            <table className="w-full text-[11px]">
              <thead>
                <tr>
                  {Object.keys(previewData[0] || {}).map((col) => (
                    <th
                      key={col}
                      className="text-left p-1.5 bg-slate-50 font-semibold text-slate-600"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {previewData.slice(0, 3).map((row, i) => (
                  <tr key={i}>
                    {Object.values(row).map((val, j) => (
                      <td
                        key={j}
                        className="p-1.5 border-b border-slate-50 text-slate-500"
                      >
                        {String(val).substring(0, 20)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="animate-fade-in-up" data-testid="data-upload-page">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-1">
            Data Upload
          </h1>
          <p className="text-slate-500">
            Upload your retail data files for comprehensive gap analysis
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-500">
            {totalUploaded}/7 files uploaded
          </span>
          {totalUploaded > 0 && (
            <button
              data-testid="clear-all-btn"
              onClick={handleClearAll}
              className="btn-secondary flex items-center gap-2 text-red-600 border-red-200 hover:bg-red-50"
            >
              <Trash2 size={14} />
              Clear All
            </button>
          )}
        </div>
      </div>

      {/* Strategy Info Banner */}
      <div
        data-testid="data-strategy-banner"
        className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6"
      >
        <div className="flex items-start gap-3">
          <Info size={18} className="text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-semibold text-blue-900">
              Data Upload Strategy
            </h3>
            <p className="text-sm text-blue-700 mt-1 leading-relaxed">
              <strong>Master Data</strong> (Style, SKU-EAN, Store, Warehouse) —
              Upload once, update when changes occur (new styles, stores, etc.).
              <br />
              <strong>Daily Data</strong> (Sales, Store Inventory, Warehouse
              Inventory) — Upload every day for fresh analysis and trend tracking.
            </p>
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div className="bg-white border border-slate-200 rounded-lg p-4 mb-6 flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div
              className={`h-2.5 w-2.5 rounded-full ${
                masterUploaded === MASTER_FILES.length
                  ? "bg-green-500"
                  : masterUploaded > 0
                  ? "bg-amber-400"
                  : "bg-red-400"
              }`}
            />
            <span className="text-sm text-slate-600">
              Master Data:{" "}
              <strong>
                {masterUploaded}/{MASTER_FILES.length}
              </strong>
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div
              className={`h-2.5 w-2.5 rounded-full ${
                dailyUploaded === DAILY_FILES.length
                  ? "bg-green-500"
                  : dailyUploaded > 0
                  ? "bg-amber-400"
                  : "bg-red-400"
              }`}
            />
            <span className="text-sm text-slate-600">
              Daily Data:{" "}
              <strong>
                {dailyUploaded}/{DAILY_FILES.length}
              </strong>
            </span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="flex items-center gap-3 min-w-[200px]">
          <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-[var(--sf-primary)] transition-all duration-500 rounded-full"
              style={{ width: `${(totalUploaded / 7) * 100}%` }}
            />
          </div>
          <span className="text-xs font-medium text-slate-500">
            {Math.round((totalUploaded / 7) * 100)}%
          </span>
        </div>
      </div>

      {/* Two Column Layout: Master + Daily */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* MASTER DATA */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Database size={18} className="text-blue-600" />
            <h2 className="text-lg font-bold text-slate-900">Master Data</h2>
            <span className="text-xs text-slate-400 ml-1">One-time setup</span>
          </div>
          <p className="text-xs text-slate-500 mb-4">
            Upload once. Update only when new styles, stores, or warehouses are
            added.
          </p>
          <div className="space-y-4">
            {MASTER_FILES.map((file) => (
              <FileCard key={file.key} file={file} />
            ))}
          </div>
        </div>

        {/* DAILY DATA */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Calendar size={18} className="text-amber-600" />
            <h2 className="text-lg font-bold text-slate-900">Daily Data</h2>
            <span className="text-xs text-slate-400 ml-1">
              Upload every day
            </span>
          </div>
          <p className="text-xs text-slate-500 mb-4">
            Upload yesterday's data daily for up-to-date analysis and trend
            tracking.
          </p>
          <div className="space-y-4">
            {DAILY_FILES.map((file) => (
              <FileCard key={file.key} file={file} />
            ))}
          </div>
        </div>
      </div>

      {/* Upload History */}
      <div
        data-testid="upload-history-section"
        className="bg-white border border-slate-200 rounded-lg overflow-hidden mb-8"
      >
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">
              Upload History
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Audit trail of all file uploads
            </p>
          </div>
          <button
            data-testid="refresh-history-btn"
            onClick={fetchHistory}
            disabled={historyLoading}
            className="btn-secondary flex items-center gap-1.5 text-xs"
          >
            <RefreshCw
              size={13}
              className={historyLoading ? "animate-spin" : ""}
            />
            Refresh
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-left">
                <th className="px-5 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  File
                </th>
                <th className="px-5 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Status
                </th>
                <th className="px-5 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Rows
                </th>
                <th className="px-5 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  File Name
                </th>
                <th className="px-5 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Uploaded
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {history.length > 0 ? (
                history.map((record, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/50">
                    <td className="px-5 py-3 font-medium text-slate-900">
                      {friendlyName(record.file_type)}
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                          record.status === "success"
                            ? "bg-green-50 text-green-700 border border-green-200"
                            : "bg-red-50 text-red-700 border border-red-200"
                        }`}
                      >
                        {record.status === "success" ? (
                          <CheckCircle size={10} />
                        ) : (
                          <AlertCircle size={10} />
                        )}
                        {record.status}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-slate-600">
                      {record.rows_processed?.toLocaleString() || "-"}
                    </td>
                    <td className="px-5 py-3 text-slate-500 text-xs">
                      {record.file_name || "-"}
                    </td>
                    <td className="px-5 py-3 text-slate-400 text-xs">
                      <div className="flex items-center gap-1.5">
                        <Clock size={11} />
                        {record.uploaded_at
                          ? new Date(record.uploaded_at).toLocaleString()
                          : "-"}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td
                    colSpan={5}
                    className="px-5 py-10 text-center text-slate-400"
                  >
                    No upload history yet. Upload your first file to get
                    started.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* SFTP Info Card */}
      <div
        data-testid="sftp-info-card"
        className="bg-white border border-slate-200 rounded-lg p-5 flex items-start gap-4"
      >
        <div className="p-2.5 bg-slate-100 rounded-lg flex-shrink-0">
          <RefreshCw size={20} className="text-slate-500" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-slate-900">
            Automate Daily Uploads with SFTP
          </h3>
          <p className="text-xs text-slate-500 mt-1 leading-relaxed">
            For production environments, configure SFTP to automatically ingest
            daily sales and inventory files from your POS/WMS systems. Contact
            your IT team to set up the automated feed.
          </p>
          <button
            data-testid="sftp-configure-btn"
            className="mt-3 text-xs text-[var(--sf-primary)] hover:underline font-semibold"
          >
            Learn More About SFTP Configuration &rarr;
          </button>
        </div>
      </div>
    </div>
  );
};

export default DataUpload;
