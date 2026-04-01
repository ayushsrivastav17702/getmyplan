import { useState, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import Papa from "papaparse";
import { 
  Upload, CheckCircle, AlertCircle, X, FileText, 
  Trash2, Eye, EyeOff
} from "lucide-react";

const FILE_TYPES = [
  { key: "style_master", name: "Style Master", description: "Style codes, brands, categories, gender, season" },
  { key: "sku_ean_master", name: "SKU-EAN Master", description: "SKU to EAN mapping with sizes and MRP" },
  { key: "store_master", name: "Store Master", description: "Store information and hierarchy" },
  { key: "warehouse_master", name: "Warehouse Master", description: "Warehouse information and hierarchy" },
  { key: "daily_sales", name: "Daily Sales", description: "Transaction-level sales data" },
  { key: "store_inventory", name: "Store Inventory", description: "Current store stock levels" },
  { key: "warehouse_inventory", name: "Warehouse Inventory", description: "Current warehouse stock levels" },
];

const DataUpload = ({ onUploadComplete }) => {
  const [uploadStatus, setUploadStatus] = useState({});
  const [uploading, setUploading] = useState({});
  const [preview, setPreview] = useState({});
  const [showPreview, setShowPreview] = useState({});
  const [dragActive, setDragActive] = useState({});

  const fetchStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/upload/status`);
      setUploadStatus(response.data);
    } catch (error) {
      console.error("Error fetching upload status:", error);
    }
  }, []);

  useState(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleDrag = (e, fileKey, active) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(prev => ({ ...prev, [fileKey]: active }));
  };

  const handleDrop = (e, fileKey) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(prev => ({ ...prev, [fileKey]: false }));
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(fileKey, e.dataTransfer.files[0]);
    }
  };

  const handleFileUpload = async (fileKey, file) => {
    if (!file) return;

    setUploading(prev => ({ ...prev, [fileKey]: true }));

    // Parse CSV for preview
    if (file.name.endsWith('.csv')) {
      Papa.parse(file, {
        preview: 5,
        header: true,
        complete: (results) => {
          setPreview(prev => ({ ...prev, [fileKey]: results.data }));
        }
      });
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(`${API}/upload/${fileKey}`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      setUploadStatus(prev => ({
        ...prev,
        [fileKey]: {
          uploaded: true,
          valid: response.data.valid,
          rows: response.data.rows,
          columns: response.data.columns,
          errors: response.data.errors,
          preview: response.data.preview
        }
      }));

      if (response.data.preview) {
        setPreview(prev => ({ ...prev, [fileKey]: response.data.preview }));
      }

      if (onUploadComplete) {
        onUploadComplete();
      }
    } catch (error) {
      console.error("Upload error:", error);
      setUploadStatus(prev => ({
        ...prev,
        [fileKey]: {
          uploaded: false,
          valid: false,
          errors: [error.response?.data?.detail || "Upload failed"]
        }
      }));
    } finally {
      setUploading(prev => ({ ...prev, [fileKey]: false }));
    }
  };

  const handleDelete = async (fileKey) => {
    try {
      await axios.delete(`${API}/upload/${fileKey}`);
      setUploadStatus(prev => {
        const newStatus = { ...prev };
        delete newStatus[fileKey];
        return newStatus;
      });
      setPreview(prev => {
        const newPreview = { ...prev };
        delete newPreview[fileKey];
        return newPreview;
      });
      if (onUploadComplete) {
        onUploadComplete();
      }
    } catch (error) {
      console.error("Delete error:", error);
    }
  };

  const handleClearAll = async () => {
    try {
      await axios.delete(`${API}/upload/all`);
      setUploadStatus({});
      setPreview({});
      if (onUploadComplete) {
        onUploadComplete();
      }
    } catch (error) {
      console.error("Clear all error:", error);
    }
  };

  const getStatusIcon = (status) => {
    if (!status) return null;
    if (status.valid) return <CheckCircle className="text-emerald-500" size={20} />;
    if (status.uploaded) return <AlertCircle className="text-amber-500" size={20} />;
    return <AlertCircle className="text-red-500" size={20} />;
  };

  const uploadedCount = Object.values(uploadStatus).filter(s => s?.uploaded && s?.valid).length;

  return (
    <div className="animate-fade-in-up" data-testid="data-upload-page">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-4xl font-light tracking-tight text-neutral-900 mb-2">
            Data Upload
          </h1>
          <p className="text-neutral-500">
            Upload your retail data files for comprehensive gap analysis
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <span className="text-sm text-neutral-500">
            {uploadedCount}/7 files uploaded
          </span>
          {uploadedCount > 0 && (
            <button
              data-testid="clear-all-btn"
              onClick={handleClearAll}
              className="flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors border border-red-200"
            >
              <Trash2 size={16} />
              Clear All
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-8 bg-white border border-neutral-200 p-6">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium uppercase tracking-widest text-neutral-400">
            Upload Progress
          </span>
          <span className="text-sm font-medium text-neutral-900">
            {Math.round((uploadedCount / 7) * 100)}%
          </span>
        </div>
        <div className="w-full h-2 bg-neutral-100">
          <div 
            className="h-full bg-[#C4A47C] transition-all duration-500"
            style={{ width: `${(uploadedCount / 7) * 100}%` }}
          />
        </div>
      </div>

      {/* File Upload Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {FILE_TYPES.map((fileType) => {
          const status = uploadStatus[fileType.key];
          const isUploading = uploading[fileType.key];
          const isDragActive = dragActive[fileType.key];
          const previewData = preview[fileType.key];
          const isShowingPreview = showPreview[fileType.key];

          return (
            <div 
              key={fileType.key}
              data-testid={`upload-card-${fileType.key}`}
              className="bg-white border border-neutral-200"
            >
              {/* Card Header */}
              <div className="p-4 border-b border-neutral-100 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText size={20} className="text-neutral-400" />
                  <div>
                    <h3 className="font-medium text-neutral-900">{fileType.name}</h3>
                    <p className="text-xs text-neutral-500">{fileType.description}</p>
                  </div>
                </div>
                {getStatusIcon(status)}
              </div>

              {/* Upload Zone */}
              <div
                className={`dropzone ${isDragActive ? 'active' : ''} ${status?.valid ? 'bg-emerald-50/50' : ''}`}
                onDragEnter={(e) => handleDrag(e, fileType.key, true)}
                onDragLeave={(e) => handleDrag(e, fileType.key, false)}
                onDragOver={(e) => handleDrag(e, fileType.key, true)}
                onDrop={(e) => handleDrop(e, fileType.key)}
              >
                {isUploading ? (
                  <div className="flex flex-col items-center gap-3">
                    <div className="spinner" />
                    <span className="text-sm text-neutral-500">Uploading...</span>
                  </div>
                ) : status?.valid ? (
                  <div className="flex flex-col items-center gap-2">
                    <CheckCircle size={32} className="text-emerald-500" />
                    <span className="text-sm font-medium text-emerald-700">
                      {status.rows?.toLocaleString()} rows uploaded
                    </span>
                    <span className="text-xs text-neutral-500">
                      {status.columns?.length} columns
                    </span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-3">
                    <Upload size={32} className="text-neutral-300" />
                    <div className="text-center">
                      <p className="text-sm text-neutral-500 mb-1">
                        Drag & drop your CSV file here
                      </p>
                      <label className="text-sm text-[#C4A47C] hover:text-[#A68A68] cursor-pointer font-medium">
                        or browse to upload
                        <input
                          type="file"
                          accept=".csv,.xlsx,.xls"
                          className="hidden"
                          data-testid={`file-input-${fileType.key}`}
                          onChange={(e) => handleFileUpload(fileType.key, e.target.files[0])}
                        />
                      </label>
                    </div>
                  </div>
                )}
              </div>

              {/* Errors */}
              {status?.errors?.length > 0 && (
                <div className="p-4 bg-red-50 border-t border-red-100">
                  {status.errors.map((error, i) => (
                    <p key={i} className="text-sm text-red-600 flex items-center gap-2">
                      <AlertCircle size={14} />
                      {error}
                    </p>
                  ))}
                </div>
              )}

              {/* Actions */}
              {status?.uploaded && (
                <div className="p-4 border-t border-neutral-100 flex items-center gap-3">
                  {previewData && (
                    <button
                      data-testid={`preview-btn-${fileType.key}`}
                      onClick={() => setShowPreview(prev => ({ ...prev, [fileType.key]: !isShowingPreview }))}
                      className="flex items-center gap-2 text-sm text-neutral-600 hover:text-neutral-900"
                    >
                      {isShowingPreview ? <EyeOff size={16} /> : <Eye size={16} />}
                      {isShowingPreview ? "Hide Preview" : "Show Preview"}
                    </button>
                  )}
                  <button
                    data-testid={`delete-btn-${fileType.key}`}
                    onClick={() => handleDelete(fileType.key)}
                    className="flex items-center gap-2 text-sm text-red-500 hover:text-red-700 ml-auto"
                  >
                    <X size={16} />
                    Remove
                  </button>
                </div>
              )}

              {/* Preview Table */}
              {isShowingPreview && previewData && (
                <div className="p-4 border-t border-neutral-100 overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr>
                        {Object.keys(previewData[0] || {}).map((col) => (
                          <th key={col} className="text-left p-2 bg-neutral-50 font-medium text-neutral-600">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.slice(0, 3).map((row, i) => (
                        <tr key={i}>
                          {Object.values(row).map((val, j) => (
                            <td key={j} className="p-2 border-b border-neutral-50 text-neutral-500">
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
        })}
      </div>
    </div>
  );
};

export default DataUpload;
