"use client";

import { useEffect, useState } from "react";
import { Building2, Users, Calendar, TrendingUp, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import type { DashboardStats } from "@zenglow/types";

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api.get<DashboardStats>("/admin/dashboard").then(setStats).catch(() => {}).finally(() => setIsLoading(false));
  }, []);

  const cards = stats ? [
    { label: "Total Businesses", value: stats.total_businesses, sub: `${stats.active_businesses} active`, icon: Building2, color: "text-brand-600", bg: "bg-brand-50" },
    { label: "Total Users", value: stats.total_users, sub: `+${stats.new_users_this_month} this month`, icon: Users, color: "text-blue-600", bg: "bg-blue-50" },
    { label: "Total Bookings", value: stats.total_bookings, sub: `${stats.bookings_today} today`, icon: Calendar, color: "text-purple-600", bg: "bg-purple-50" },
    { label: "Total Revenue", value: formatCurrency(stats.total_revenue), sub: "All time", icon: TrendingUp, color: "text-orange-600", bg: "bg-orange-50", isAmount: true },
  ] : [];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">Platform-wide overview</p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-brand-600" /></div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {cards.map((c) => (
            <div key={c.label} className="bg-white rounded-xl border border-gray-200 p-5">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${c.bg}`}>
                <c.icon className={`w-5 h-5 ${c.color}`} />
              </div>
              <p className="text-2xl font-bold text-gray-900">{c.value}</p>
              <p className="text-xs font-medium text-gray-700 mt-0.5">{c.label}</p>
              <p className="text-xs text-gray-400 mt-0.5">{c.sub}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
