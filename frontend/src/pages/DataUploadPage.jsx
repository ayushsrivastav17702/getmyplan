import React, { useState, useEffect } from "react";
import DataUploadV2 from "../components/DataUploadV2";
import UploadHistory from "../components/UploadHistory";
import UploadStatus from "../components/UploadStatus";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Download, Upload, History } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const API = process.env.REACT_APP_BACKEND_URL;

const TEMPLATES = [
  { type: "daily_sales", name: "Daily Sales", desc: "SKU, Store, Day, Quantity, Revenue" },
  { type: "store_inventory", name: "Store Inventory", desc: "Store, SKU, Closing Stock" },
  { type: "warehouse_inventory", name: "Warehouse Inventory", desc: "Warehouse, SKU, On Hand, Available" },
  { type: "sku_master", name: "SKU Master", desc: "SKU, Name, Category" },
  { type: "store_master", name: "Store Master", desc: "Store Code, Store Name" },
  { type: "warehouse_master", name: "Warehouse Master", desc: "Warehouse Code, Name, Online Flag" },
];

const DataUploadPage = () => {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState("upload");
  const [dailyStatus, setDailyStatus] = useState(null);

  useEffect(() => {
    fetchDailyStatus();
  }, []);

  const fetchDailyStatus = async () => {
    try {
      const res = await fetch(`${API}/api/upload/v2/daily-status`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setDailyStatus(data);
    } catch (err) {
      console.error("Failed to fetch daily status:", err);
    }
  };

  const downloadTemplate = (type) => {
    window.open(`${API}/api/upload/v2/template/${type}`, "_blank");
  };

  return (
    <div className="space-y-6" data-testid="data-upload-page">
      {/* Header */}
      <div className="flex justify-between items-center flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Data Upload</h1>
          <p className="text-sm text-slate-500 mt-1">Upload and manage your inventory and sales data</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => downloadTemplate("daily_sales")} data-testid="dl-sales-template">
            <Download className="w-4 h-4 mr-2" /> Sales Template
          </Button>
          <Button variant="outline" size="sm" onClick={() => downloadTemplate("store_inventory")} data-testid="dl-inventory-template">
            <Download className="w-4 h-4 mr-2" /> Inventory Template
          </Button>
        </div>
      </div>

      {/* Today's Status */}
      <UploadStatus status={dailyStatus} onRefresh={fetchDailyStatus} />

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full max-w-md grid-cols-3">
          <TabsTrigger value="upload" data-testid="tab-upload">
            <Upload className="w-4 h-4 mr-2" /> Upload
          </TabsTrigger>
          <TabsTrigger value="history" data-testid="tab-history">
            <History className="w-4 h-4 mr-2" /> History
          </TabsTrigger>
          <TabsTrigger value="templates" data-testid="tab-templates">
            <Download className="w-4 h-4 mr-2" /> Templates
          </TabsTrigger>
        </TabsList>

        <TabsContent value="upload" className="mt-6">
          <DataUploadV2
            onSuccess={() => {
              fetchDailyStatus();
              setActiveTab("history");
            }}
          />
        </TabsContent>

        <TabsContent value="history" className="mt-6">
          <UploadHistory />
        </TabsContent>

        <TabsContent value="templates" className="mt-6">
          <Card>
            <CardHeader><CardTitle className="text-base">Download Templates</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {TEMPLATES.map((t) => (
                  <Card
                    key={t.type}
                    className="cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => downloadTemplate(t.type)}
                    data-testid={`template-${t.type}`}
                  >
                    <CardContent className="p-4 flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-sm">{t.name}</h3>
                        <p className="text-xs text-slate-500">{t.desc}</p>
                      </div>
                      <Download className="w-5 h-5 text-slate-400" />
                    </CardContent>
                  </Card>
                ))}
              </div>
              <p className="text-xs text-slate-500 mt-4">
                Templates include dropdown validation with your actual SKUs and stores.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DataUploadPage;
