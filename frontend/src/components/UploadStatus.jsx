import React from "react";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { CheckCircle, Clock, XCircle, FileText, Warehouse, RefreshCw } from "lucide-react";

const UploadStatus = ({ status, onRefresh }) => {
  const getDisplay = (data) => {
    if (!data || !data.uploaded) {
      return {
        icon: <Clock className="w-5 h-5 text-slate-400" />,
        label: "Not uploaded yet",
        color: "text-slate-500",
        badgeCls: "bg-slate-100 text-slate-600 border-slate-200",
        badgeText: "Pending",
      };
    }
    return {
      icon: <CheckCircle className="w-5 h-5 text-emerald-500" />,
      label: `Uploaded at ${data.time}`,
      color: "text-emerald-600",
      badgeCls: "bg-emerald-50 text-emerald-700 border-emerald-200",
      badgeText: "Complete",
      detail: `${data.rows} rows`,
    };
  };

  const types = [
    { key: "daily_sales", label: "Daily Sales", Icon: FileText },
    { key: "store_inventory", label: "Store Inventory", Icon: Warehouse },
    { key: "warehouse_inventory", label: "Warehouse Inventory", Icon: Warehouse },
  ];

  const allDone = types.every((t) => status?.[t.key]?.uploaded);
  const someDone = types.some((t) => status?.[t.key]?.uploaded);

  return (
    <Card data-testid="upload-daily-status">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-slate-900">Today's Upload Status</h3>
            {allDone ? (
              <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">All Complete</Badge>
            ) : someDone ? (
              <Badge className="bg-amber-50 text-amber-700 border-amber-200">In Progress</Badge>
            ) : (
              <Badge variant="secondary">Not Started</Badge>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={onRefresh} data-testid="refresh-status-btn">
            <RefreshCw className="w-4 h-4 mr-1" /> Refresh
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {types.map(({ key, label, Icon }) => {
            const d = getDisplay(status?.[key]);
            return (
              <div key={key} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg" data-testid={`status-${key}`}>
                <div className="p-2 bg-white rounded">
                  <Icon className="w-5 h-5 text-slate-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm">{label}</span>
                    <Badge className={d.badgeCls} variant="outline">{d.badgeText}</Badge>
                  </div>
                  <div className="flex items-center gap-1 mt-1">
                    {d.icon}
                    <span className={`text-xs ${d.color}`}>{d.label}</span>
                  </div>
                  {d.detail && <div className="text-xs text-slate-500 mt-0.5">{d.detail}</div>}
                </div>
              </div>
            );
          })}
        </div>

        {!allDone && (
          <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-200">
            <p className="text-sm text-amber-800">
              Upload all required data by 11:59 PM for complete daily reporting.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default UploadStatus;
