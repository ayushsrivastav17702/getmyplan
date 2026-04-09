import React from "react";
import { Card, CardContent } from "../ui/card";

const StatusDot = ({ uploaded, label }) => (
  <div className="flex items-center gap-1.5">
    <div className={`w-2 h-2 rounded-full ${uploaded ? "bg-emerald-500" : "bg-slate-300"}`} />
    <span className="text-xs text-slate-500">{label}</span>
  </div>
);

export const PreviousDaysList = ({ days, onViewDay }) => {
  if (!days || days.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-slate-500 text-sm">
          No previous upload history.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-0 divide-y divide-slate-100">
        {days.slice(0, 7).map((day) => (
          <div
            key={day.date}
            className="px-4 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors cursor-pointer"
            onClick={() => day.has_data && onViewDay?.(day.date)}
          >
            <div className="flex items-center gap-3">
              <span className="font-medium text-sm text-slate-800 w-28">{day.label}</span>
              <span className="text-xs text-slate-400">{day.date}</span>
            </div>
            <div className="flex items-center gap-3">
              <StatusDot uploaded={day.uploads?.daily_sales} label="Sales" />
              <StatusDot uploaded={day.uploads?.store_inventory} label="Store" />
              <StatusDot uploaded={day.uploads?.warehouse_inventory} label="WH" />
              <StatusDot uploaded={day.uploads?.cogs} label="COGS" />
              <StatusDot uploaded={day.uploads?.open_orders} label="Orders" />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};
