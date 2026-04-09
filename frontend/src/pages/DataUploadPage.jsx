import React, { useState, useEffect } from "react";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import {
  Package, CheckCircle, Upload, Download, RefreshCw,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

import { MasterCard } from "../components/upload/MasterCard";
import { DailyStatusCard } from "../components/upload/DailyStatusCard";
import { PreviousDaysList } from "../components/upload/PreviousDaysList";
import { FileDropzone } from "../components/upload/FileDropzone";

const API = process.env.REACT_APP_BACKEND_URL;

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

  useEffect(() => { refresh(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const refresh = () => {
    fetchDailyStatus();
    fetchMasterStatus();
    fetchPreviousDays();
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

  const fetchPreviousDays = async () => {
    try {
      const r = await fetch(`${API}/api/upload/v2/history/days?days=7`, { headers: hdrs });
      const d = await r.json();
      setPreviousDays(d.days || []);
    } catch (e) { console.error(e); }
  };

  /* ─── Step 1: Validate Only ─── */
  const handleValidate = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(10);
    const fd = new FormData();
    fd.append("file", file);

    try {
      const iv = setInterval(() => setProgress((p) => Math.min(p + 12, 90)), 250);
      const r = await fetch(`${API}/api/upload/v2/${selectedType}/validate`, {
        method: "POST", body: fd, headers: hdrs,
      });
      clearInterval(iv);
      setProgress(100);
      const data = await r.json();
      setResult(data);
    } catch {
      setResult({
        success: false,
        errors: [{ code: "NET", message: "Network error" }],
        total_rows: 0, valid_rows: 0, corrections: [], warnings: [], preview: [],
      });
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  /* ─── Step 2: Save After Validation ─── */
  const handleSave = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(10);
    const fd = new FormData();
    fd.append("file", file);

    try {
      const iv = setInterval(() => setProgress((p) => Math.min(p + 15, 90)), 200);
      const slug = selectedType.replace(/_/g, "-");
      const r = await fetch(`${API}/api/upload/v2/${slug}?replace_existing=true`, {
        method: "POST", body: fd, headers: hdrs,
      });
      clearInterval(iv);
      setProgress(100);
      const data = await r.json();
      if (data.success) {
        setShowSaveConfirm(false);
        setFile(null);
        setResult(null);
        refresh();
      } else {
        setResult(data);
        setShowSaveConfirm(false);
      }
    } catch {
      setResult({
        success: false,
        errors: [{ code: "NET", message: "Network error during save" }],
        total_rows: 0, valid_rows: 0, corrections: [], warnings: [], preview: [],
      });
      setShowSaveConfirm(false);
    } finally {
      setUploading(false);
      setProgress(0);
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

      {/* SECTION 1: MASTER DATA */}
      <section data-testid="master-data-section">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-violet-100 rounded-lg"><Package className="w-5 h-5 text-violet-600" /></div>
          <h2 className="text-lg font-semibold text-slate-900">Master Data</h2>
          <span className="text-xs text-slate-400 ml-1">Setup once &mdash; rarely changes</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MasterCard type="sku" title="SKU Master" description="Products & pricing"
            count={masterStatus?.sku_master?.count} lastUpdated={masterStatus?.sku_master?.last_updated}
            onUpload={() => { setSelectedType("sku_master"); setFile(null); setResult(null); }}
            onDownload={() => downloadTemplate("sku_master")} />
          <MasterCard type="store" title="Store Master" description="Store locations"
            count={masterStatus?.store_master?.count} lastUpdated={masterStatus?.store_master?.last_updated}
            onUpload={() => { setSelectedType("store_master"); setFile(null); setResult(null); }}
            onDownload={() => downloadTemplate("store_master")} />
          <MasterCard type="warehouse" title="Warehouse Master" description="Warehouses & capacity"
            count={masterStatus?.warehouse_master?.count} lastUpdated={masterStatus?.warehouse_master?.last_updated}
            onUpload={() => { setSelectedType("warehouse_master"); setFile(null); setResult(null); }}
            onDownload={() => downloadTemplate("warehouse_master")} />
        </div>
      </section>

      {/* SECTION 2: TODAY'S STATUS */}
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
          {["daily_sales", "store_inventory", "warehouse_inventory"].map((key) => (
            <DailyStatusCard
              key={key}
              type={key}
              status={dailyStatus?.[key]}
              onUploadNow={() => { setSelectedType(key); setFile(null); setResult(null); }}
            />
          ))}
        </div>
        {allDone && (
          <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-2" data-testid="all-complete-banner">
            <CheckCircle className="w-5 h-5 text-emerald-600" />
            <span className="text-emerald-800 font-medium text-sm">All daily data uploaded for today</span>
          </div>
        )}
      </section>

      {/* SECTION 3: UPLOAD NEW DATA */}
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
              <Select value={selectedType} onValueChange={(v) => { setSelectedType(v); setFile(null); setResult(null); setShowSaveConfirm(false); }}>
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

            {/* File Dropzone + Validation + Save */}
            <FileDropzone
              file={file}
              onFile={(f) => { setFile(f); setResult(null); setShowSaveConfirm(false); }}
              selectedType={selectedType}
              dailyStatus={dailyStatus}
              uploading={uploading}
              progress={progress}
              result={result}
              showSaveConfirm={showSaveConfirm}
              onValidate={handleValidate}
              onSave={handleSave}
              onCancelSave={() => setShowSaveConfirm(false)}
              onRetry={() => { setResult(null); setFile(null); }}
              onShowSaveConfirm={() => setShowSaveConfirm(true)}
            />
          </CardContent>
        </Card>
      </section>

      {/* SECTION 4: PREVIOUS DAYS */}
      <section data-testid="previous-days-section">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-slate-900">Previous Days</h3>
        </div>
        <PreviousDaysList days={previousDays} onViewDay={(date) => console.log("View day:", date)} />
      </section>
    </div>
  );
};

export default DataUploadPage;
