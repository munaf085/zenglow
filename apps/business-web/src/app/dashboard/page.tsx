"use client";

import { useEffect, useState } from "react";
import { Calendar, Users, TrendingUp, Clock, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import type { Appointment } from "@zenglow/types";
import { formatDateTime, formatCurrency, cn } from "@/lib/utils";
import Link from "next/link";
import { format, startOfDay, endOfDay } from "date-fns";

const STATUS_COLORS: Record<string, string> = {
  CONFIRMED: "bg-green-100 text-green-700",
  PENDING: "bg-yellow-100 text-yellow-700",
  COMPLETED: "bg-gray-100 text-gray-600",
  CANCELLED: "bg-red-100 text-red-700",
  IN_PROGRESS: "bg-blue-100 text-blue-700",
};

import { GoLiveChecklist } from "@/components/dashboard/GoLiveChecklist";

export default function DashboardPage() {
  const { business } = useAuth();
  const [todayAppts, setTodayAppts] = useState<Appointment[]>([]);
  const [stats, setStats] = useState({ today: 0, week: 0, revenue: 0, customers: 0 });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!business) return;
    async function load() {
      setIsLoading(true);
      try {
        const today = new Date();
        const params = new URLSearchParams({
          start_date: startOfDay(today).toISOString(),
          end_date: endOfDay(today).toISOString(),
        });
        const appts = await api.get<Appointment[]>(
          `/businesses/${business!.id}/appointments?${params}`
        );
        setTodayAppts(appts.slice(0, 8));
        setStats({
          today: appts.length,
          week: appts.length * 3, // approximate
          revenue: appts.reduce((s, a) => s + a.total_amount, 0),
          customers: new Set(appts.map((a) => a.customer_id)).size,
        });
      } catch { /* ignore */ }
      finally { setIsLoading(false); }
    }
    load();
  }, [business]);

  if (!business) return null;

  const statCards = [
    { label: "Today's Appointments", value: stats.today, icon: Calendar, color: "text-brand-600", bg: "bg-brand-50" },
    { label: "This Week", value: stats.week, icon: TrendingUp, color: "text-green-600", bg: "bg-green-50" },
    { label: "Today's Revenue", value: formatCurrency(stats.revenue), icon: TrendingUp, color: "text-purple-600", bg: "bg-purple-50", isAmount: true },
    { label: "Unique Customers", value: stats.customers, icon: Users, color: "text-orange-600", bg: "bg-orange-50" },
  ];

  return (
    <div className="space-y-6">
      {/* Go Live Checklist */}
      <GoLiveChecklist />

      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">{format(new Date(), "EEEE, MMMM d, yyyy")}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-200 p-5">
            <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center mb-3", s.bg)}>
              <s.icon className={cn("w-5 h-5", s.color)} />
            </div>
            <p className="text-2xl font-bold text-gray-900">{s.value}</p>
            <p className="text-xs text-gray-500 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Today's appointments */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Today's Appointments</h2>
          <Link href="/dashboard/calendar" className="flex items-center gap-1 text-sm text-brand-600 hover:text-brand-700">
            View all <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        {isLoading ? (
          <div className="divide-y divide-gray-100">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="px-5 py-4 animate-pulse flex gap-4">
                <div className="w-12 h-12 bg-gray-200 rounded-lg" />
                <div className="flex-1 space-y-2">
                  <div className="h-3.5 bg-gray-200 rounded w-1/3" />
                  <div className="h-3 bg-gray-200 rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : todayAppts.length === 0 ? (
          <div className="px-5 py-12 text-center text-gray-400">
            <Calendar className="w-10 h-10 mx-auto mb-3 opacity-40" />
            <p className="text-sm">No appointments today</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {todayAppts.map((appt) => (
              <div key={appt.id} className="px-5 py-4 flex items-center gap-4">
                <div className="w-12 h-12 bg-brand-50 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Clock className="w-5 h-5 text-brand-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {appt.items?.[0]?.service_name ?? "Appointment"}
                  </p>
                  <p className="text-xs text-gray-500">{format(new Date(appt.start_time), "h:mm a")}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={cn("text-xs font-medium px-2 py-0.5 rounded-full", STATUS_COLORS[appt.status] ?? "bg-gray-100 text-gray-600")}>
                    {appt.status.replace("_", " ")}
                  </span>
                  <span className="text-sm font-semibold text-gray-900 hidden sm:block">
                    {formatCurrency(appt.total_amount)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
