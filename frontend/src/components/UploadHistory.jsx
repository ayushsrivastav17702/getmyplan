import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Badge } from "./ui/badge";
import { CheckCircle, XCircle, FileText, Warehouse, Package, ChevronRight } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const API = process.env.REACT_APP_BACKEND_URL;

const TYPE_LABELS = {
  daily_sales: "Daily Sales",
  store_inventory: "Store Inventory",
  warehouse_inventory: "Warehouse Inventory",
  sku_master: "SKU Master",
  store_master: "Store Master",
  warehouse_master: "Warehouse Master",
};

const TYPE_ICONS = {
  daily_sales: FileText,
  store_inventory: Warehouse,
  warehouse_inventory: Warehouse,
  sku_master: Package,
  store_master: Warehouse,
  warehouse_master: Warehouse,
};

const UploadHistory = () => {
  const { token } = useAuth();
  const [history, setHistory] = useState([]);
  const [filterType, setFilterType] = useState("all");
  const [days, setDays] = useState("7");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, [filterType, days]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ days });
      if (filterType !== "all") params.append("upload_type", filterType);
      const res = await fetch(`${API}/api/upload/v2/history?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setHistory(data.history || []);
    } catch (err) {
      console.error("Failed to fetch history:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4" data-testid="upload-history">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <label className="text-sm font-medium text-slate-700">Filter by Type</label>
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger data-testid="history-filter-type"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="daily_sales">Daily Sales</SelectItem>
                  <SelectItem value="store_inventory">Store Inventory</SelectItem>
                  <SelectItem value="warehouse_inventory">Warehouse Inventory</SelectItem>
                  <SelectItem value="sku_master">SKU Master</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="w-40">
              <label className="text-sm font-medium text-slate-700">Period</label>
              <Select value={days} onValueChange={setDays}>
                <SelectTrigger data-testid="history-filter-days"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="7">Last 7 days</SelectItem>
                  <SelectItem value="14">Last 14 days</SelectItem>
                  <SelectItem value="30">Last 30 days</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <Card><CardContent className="p-8 text-center text-slate-500">Loading history...</CardContent></Card>
      ) : history.length === 0 ? (
        <Card><CardContent className="p-8 text-center text-slate-500">No upload history found.</CardContent></Card>
      ) : (
        <div className="space-y-4">
          {history.map((day) => (
            <Card key={day.date}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{day.label}</CardTitle>
                  <span className="text-sm text-slate-500">{day.date}</span>
                </div>
              </CardHeader>
              <CardContent>
                {Object.keys(day.uploads).length === 0 ? (
                  <p className="text-sm text-slate-500 py-2">No uploads for this day.</p>
                ) : (
                  <div className="space-y-2">
                    {Object.entries(day.uploads).map(([type, upload]) => {
                      const Icon = TYPE_ICONS[type] || FileText;
                      return (
                        <div
                          key={type}
                          className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
                          data-testid={`history-item-${type}`}
                        >
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-white rounded"><Icon className="w-4 h-4 text-slate-600" /></div>
                            <div>
                              <div className="font-medium text-sm">{TYPE_LABELS[type] || type}</div>
                              <div className="text-xs text-slate-500">{upload.file_name} &middot; {upload.rows} rows</div>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="text-right">
                              <div className="text-xs text-slate-600">{upload.time}</div>
                              {upload.uploaded_by && (
                                <div className="text-xs text-slate-400">by {upload.uploaded_by}</div>
                              )}
                            </div>
                            {upload.status === "completed" ? (
                              <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200" variant="outline">
                                <CheckCircle className="w-3 h-3 mr-1" /> Complete
                              </Badge>
                            ) : (
                              <Badge variant="destructive">
                                <XCircle className="w-3 h-3 mr-1" /> Failed
                              </Badge>
                            )}
                            <ChevronRight className="w-4 h-4 text-slate-400" />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default UploadHistory;
