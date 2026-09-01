"use client";

import { useEffect, useState } from "react";
import {
  TrendingUp, Users, Building2, Calendar, DollarSign, Loader2,
} from "lucide-react";
import { api } from "@/lib/api";
import type { DashboardStats } from "@zenglow/types";
import { formatCurrency } from "@/lib/utils";

function StatCard({
  label,
  value,
  sub,
  icon: Icon,
  color,
  bg,
}: {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ElementType;
  color: string;
  bg: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-4 ${bg}`}>
        <Icon className={`w-5 h-5 ${color}`} />
      </div>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
      <p className="text-sm font-medium text-gray-700 mt-1">{label}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
}

export default function AdminReportsPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api.get<DashboardStats>("/admin/dashboard")
      .then(setStats)
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-8">Reports</h1>
        <div className="flex items-center justify-center py-24">
          <Loader2 className="w-8 h-8 animate-spin text-brand-600" />
        </div>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <p className="text-gray-500 text-sm mt-1">Platform-wide metrics and growth overview</p>
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
        <StatCard
          label="Total Businesses"
          value={stats.total_businesses}
          sub={`${stats.active_businesses} active`}
          icon={Building2}
          color="text-brand-600"
          bg="bg-brand-50"
        />
        <StatCard
          label="Total Users"
          value={stats.total_users}
          sub={`+${stats.new_users_this_month} this month`}
          icon={Users}
          color="text-blue-600"
          bg="bg-blue-50"
        />
        <StatCard
          label="Total Bookings"
          value={stats.total_bookings}
          sub={`${stats.bookings_today} today`}
          icon={Calendar}
          color="text-purple-600"
          bg="bg-purple-50"
        />
        <StatCard
          label="Total Revenue"
          value={formatCurrency(stats.total_revenue)}
          sub="All time (captured)"
          icon={DollarSign}
          color="text-green-600"
          bg="bg-green-50"
        />
      </div>

      {/* Growth section */}
      <div className="grid sm:grid-cols-2 gap-5 mb-10">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-9 h-9 bg-brand-50 rounded-lg flex items-center justify-center">
              <Building2 className="w-4 h-4 text-brand-600" />
            </div>
            <h2 className="font-semibold text-gray-900">Business Growth</h2>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Total registered</span>
              <span className="font-semibold text-gray-900">{stats.total_businesses}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Currently active</span>
              <span className="font-semibold text-gray-900">{stats.active_businesses}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">New this month</span>
              <span className="font-semibold text-green-600">+{stats.new_businesses_this_month}</span>
            </div>
            <div className="pt-2 border-t border-gray-100">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Activation rate</span>
                <span className="font-semibold text-gray-900">
                  {stats.total_businesses > 0
                    ? Math.round((stats.active_businesses / stats.total_businesses) * 100)
                    : 0}%
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-9 h-9 bg-blue-50 rounded-lg flex items-center justify-center">
              <Users className="w-4 h-4 text-blue-600" />
            </div>
            <h2 className="font-semibold text-gray-900">User Growth</h2>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Total registered</span>
              <span className="font-semibold text-gray-900">{stats.total_users}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">New this month</span>
              <span className="font-semibold text-green-600">+{stats.new_users_this_month}</span>
            </div>
            <div className="pt-2 border-t border-gray-100">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Monthly growth rate</span>
                <span className="font-semibold text-gray-900">
                  {stats.total_users > 0
                    ? ((stats.new_users_this_month / stats.total_users) * 100).toFixed(1)
                    : 0}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Booking activity */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-9 h-9 bg-purple-50 rounded-lg flex items-center justify-center">
            <Calendar className="w-4 h-4 text-purple-600" />
          </div>
          <h2 className="font-semibold text-gray-900">Booking Activity</h2>
        </div>
        <div className="grid sm:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-gray-900">{stats.total_bookings}</p>
            <p className="text-xs text-gray-500 mt-1">All-time bookings</p>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <p className="text-2xl font-bold text-purple-700">{stats.bookings_today}</p>
            <p className="text-xs text-purple-500 mt-1">Bookings today</p>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <p className="text-2xl font-bold text-green-700">{formatCurrency(stats.total_revenue)}</p>
            <p className="text-xs text-green-500 mt-1">Total revenue</p>
          </div>
        </div>
      </div>
    </div>
  );
}
