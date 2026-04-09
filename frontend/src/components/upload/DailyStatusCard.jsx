import React from "react";
import { CheckCircle, AlertTriangle, ChevronRight, FileText, Store, Warehouse, DollarSign, ShoppingCart } from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";

const iconMap = {
  daily_sales: FileText,
  store_inventory: Store,
  warehouse_inventory: Warehouse,
  cogs: DollarSign,
  open_orders: ShoppingCart,
};

const labelMap = {
  daily_sales: "Daily Sales",
  store_inventory: "Store Inventory",
  warehouse_inventory: "Warehouse Inventory",
  cogs: "COGS",
  open_orders: "Open Orders",
};

export const DailyStatusCard = ({ type, status, onUploadNow }) => {
  const Icon = iconMap[type] || FileText;
  const label = labelMap[type] || type;

  return (
    <Card data-testid={`daily-card-${label.toLowerCase().replace(/ /g, "-")}`}>
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <Icon className="w-4 h-4 text-slate-500" />
          <h4 className="font-medium text-slate-900 text-sm">{label}</h4>
        </div>
        {status?.uploaded ? (
          <>
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle className="w-4 h-4 text-emerald-500" />
              <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200" variant="outline">
                Uploaded
              </Badge>
            </div>
            <p className="text-xs text-slate-600">
              {status.time} &middot; {status.rows} rows
            </p>
          </>
        ) : (
          <>
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <Badge className="bg-amber-50 text-amber-700 border-amber-200" variant="outline">
                Not Uploaded
              </Badge>
            </div>
            <Button
              variant="link"
              size="sm"
              className="p-0 h-auto text-blue-600"
              onClick={onUploadNow}
            >
              Upload Now <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
};
