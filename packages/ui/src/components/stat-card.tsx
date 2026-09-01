import * as React from "react";
import { cn } from "../lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ElementType;
  iconColor?: string;
  iconBg?: string;
  trend?: { value: number; label: string };
  className?: string;
}

function StatCard({
  label,
  value,
  sub,
  icon: Icon,
  iconColor = "text-brand-600",
  iconBg = "bg-brand-50",
  trend,
  className,
}: StatCardProps) {
  return (
    <div className={cn("bg-white rounded-xl border border-gray-200 p-5", className)}>
      <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center mb-3", iconBg)}>
        <Icon className={cn("w-5 h-5", iconColor)} />
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm font-medium text-gray-700 mt-0.5">{label}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      {trend && (
        <div className={cn(
          "flex items-center gap-1 mt-2 text-xs font-medium",
          trend.value >= 0 ? "text-green-600" : "text-red-500"
        )}>
          <span>{trend.value >= 0 ? "↑" : "↓"} {Math.abs(trend.value)}%</span>
          <span className="text-gray-400">{trend.label}</span>
        </div>
      )}
    </div>
  );
}

export { StatCard };
