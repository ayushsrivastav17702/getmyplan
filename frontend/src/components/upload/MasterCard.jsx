import React from "react";
import { Package, Store, Warehouse, Download, Upload, Eye } from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";

const iconMap = { sku: Package, store: Store, warehouse: Warehouse };
const colorMap = {
  sku: { bg: "bg-blue-100", fg: "text-blue-600" },
  store: { bg: "bg-emerald-100", fg: "text-emerald-600" },
  warehouse: { bg: "bg-violet-100", fg: "text-violet-600" },
};

export const MasterCard = ({ type, title, description, count, lastUpdated, onUpload, onDownload, onPreview }) => {
  const Icon = iconMap[type] || Package;
  const colors = colorMap[type] || colorMap.sku;

  return (
    <Card data-testid={`master-${title.toLowerCase().replace(/ /g, "-")}`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`p-2 ${colors.bg} rounded-lg`}>
              <Icon className={`w-5 h-5 ${colors.fg}`} />
            </div>
            <div>
              <h3 className="font-medium text-slate-900 text-sm">{title}</h3>
              <p className="text-xs text-slate-500">{description}</p>
            </div>
          </div>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <span className="text-2xl font-bold text-slate-900">{count ?? 0}</span>
            <span className="text-xs text-slate-400 ml-2">
              {lastUpdated ? `Updated ${lastUpdated}` : "Not set up"}
            </span>
          </div>
          <div className="flex gap-1">
            {(count ?? 0) > 0 && onPreview && (
              <Button variant="ghost" size="sm" onClick={onPreview} title="Preview data" data-testid={`preview-${type}`}>
                <Eye className="w-4 h-4" />
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={onDownload} title="Download template">
              <Download className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={onUpload} title="Upload">
              <Upload className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
