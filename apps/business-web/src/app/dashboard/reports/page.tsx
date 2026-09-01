"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { api } from "@/lib/api";
import { toast } from "sonner";
import {
  BarChart3, TrendingUp, DollarSign, Users, Package,
  Award, Scissors, ShoppingBag, AlertTriangle, Calendar,
} from "lucide-react";
import { cn, formatPrice } from "@/lib/utils";

export default function ReportsPage() {
  const { business } = useAuth();
  const [revenue, setRevenue] = useState<any | null>(null);
  const [staffMetrics, setStaffMetrics] = useState<any[]>([]);
  const [inventoryReport, setInventoryReport] = useState<any | null>(null);
  const [operations, setOperations] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!business?.id) return;
    loadReports();
  }, [business?.id]);

  const loadReports = async () => {
    try {
      setLoading(true);
      const [revRes, staffRes, invRes, opsRes] = await Promise.allSettled([
        api.get<any>(`/businesses/${business?.id}/reports/revenue`),
        api.get<any>(`/businesses/${business?.id}/reports/staff`),
        api.get<any>(`/businesses/${business?.id}/reports/inventory`),
        api.get<any>(`/businesses/${business?.id}/reports/operations`),
      ]);

      if (revRes.status === "fulfilled") setRevenue(revRes.value);
      if (staffRes.status === "fulfilled") setStaffMetrics(staffRes.value?.metrics ?? []);
      if (invRes.status === "fulfilled") setInventoryReport(invRes.value);
      if (opsRes.status === "fulfilled") setOperations(opsRes.value);
    } catch (e) {
      toast.error("Failed to load business analytics");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <BarChart3 className="w-7 h-7 text-brand-600" /> Business Operations & Reports
        </h1>
        <p className="text-sm text-gray-500">Live operational financial summaries, staff utilization, inventory valuation, and sales metrics</p>
      </div>

      {/* Top 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-gray-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Gross Sales</span>
            <DollarSign className="w-5 h-5 text-brand-600" />
          </div>
          <p className="text-2xl font-extrabold text-gray-900">
            {formatPrice(revenue?.total_revenue ?? 0)}
          </p>
          <p className="text-xs text-gray-500">{revenue?.total_orders ?? 0} completed orders</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-gray-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Service Revenue</span>
            <Scissors className="w-5 h-5 text-purple-600" />
          </div>
          <p className="text-2xl font-extrabold text-purple-700">
            {formatPrice(revenue?.service_revenue ?? 0)}
          </p>
          <p className="text-xs text-gray-500">From appointments & walk-ins</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-gray-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Retail Sales</span>
            <ShoppingBag className="w-5 h-5 text-blue-600" />
          </div>
          <p className="text-2xl font-extrabold text-blue-700">
            {formatPrice(revenue?.product_revenue ?? 0)}
          </p>
          <p className="text-xs text-gray-500">Product sales via POS</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-gray-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Stock Valuation</span>
            <Package className="w-5 h-5 text-emerald-600" />
          </div>
          <p className="text-2xl font-extrabold text-emerald-700">
            {formatPrice(inventoryReport?.total_valuation_retail ?? 0)}
          </p>
          <p className="text-xs text-gray-500">{inventoryReport?.total_items ?? 0} total SKU catalog</p>
        </div>
      </div>

      {/* Financial Breakdown & Operations Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Financial Summary */}
        <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm space-y-4">
          <h2 className="font-bold text-gray-900 text-base flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-brand-600" /> Financial Breakdown
          </h2>
          <div className="divide-y divide-gray-100 text-sm space-y-2.5">
            <div className="pt-2 flex justify-between">
              <span className="text-gray-600">Total Tax (GST Collected)</span>
              <span className="font-semibold text-gray-900">{formatPrice(revenue?.total_tax ?? 0)}</span>
            </div>
            <div className="pt-2 flex justify-between">
              <span className="text-gray-600">Discounts Applied</span>
              <span className="font-semibold text-red-600">-{formatPrice(revenue?.total_discounts ?? 0)}</span>
            </div>
            <div className="pt-2 flex justify-between">
              <span className="text-gray-600">Staff Tips Collected</span>
              <span className="font-semibold text-green-600">+{formatPrice(revenue?.total_tips ?? 0)}</span>
            </div>
          </div>
        </div>

        {/* Operations Overview */}
        <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm space-y-4 lg:col-span-2">
          <h2 className="font-bold text-gray-900 text-base flex items-center gap-2">
            <Calendar className="w-5 h-5 text-brand-600" /> Booking Operations Summary
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div className="bg-gray-50 p-3 rounded-xl">
              <span className="text-xs text-gray-500">Total Bookings</span>
              <p className="text-xl font-bold text-gray-900 mt-1">{operations?.total_bookings ?? 0}</p>
            </div>
            <div className="bg-green-50 p-3 rounded-xl">
              <span className="text-xs text-green-700">Completed</span>
              <p className="text-xl font-bold text-green-800 mt-1">{operations?.completed_bookings ?? 0}</p>
            </div>
            <div className="bg-red-50 p-3 rounded-xl">
              <span className="text-xs text-red-700">Cancellations</span>
              <p className="text-xl font-bold text-red-800 mt-1">{operations?.cancelled_bookings ?? 0}</p>
            </div>
            <div className="bg-purple-50 p-3 rounded-xl">
              <span className="text-xs text-purple-700">VIP Members</span>
              <p className="text-xl font-bold text-purple-800 mt-1">{operations?.active_memberships ?? 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Staff Performance Leaderboard */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden space-y-3 p-5">
        <h2 className="font-bold text-gray-900 text-base flex items-center gap-2">
          <Users className="w-5 h-5 text-brand-600" /> Staff Performance Leaderboard
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-700 font-semibold border-b border-gray-200">
              <tr>
                <th className="py-3 px-4">Staff Member</th>
                <th className="py-3 px-4 text-center">Appointments / Sales</th>
                <th className="py-3 px-4 text-right">Service Sales</th>
                <th className="py-3 px-4 text-right">Retail Sales</th>
                <th className="py-3 px-4 text-right">Tips Earned</th>
                <th className="py-3 px-4 text-right">Total Revenue</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {staffMetrics.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-400">
                    No staff sales activity recorded yet.
                  </td>
                </tr>
              ) : (
                staffMetrics.map((sm) => (
                  <tr key={sm.staff_id} className="hover:bg-gray-50/75">
                    <td className="py-3.5 px-4 font-semibold text-gray-900">
                      {sm.staff_name}
                    </td>
                    <td className="py-3.5 px-4 text-center font-bold text-gray-700">
                      {sm.appointments_count}
                    </td>
                    <td className="py-3.5 px-4 text-right text-gray-700">
                      {formatPrice(sm.services_revenue)}
                    </td>
                    <td className="py-3.5 px-4 text-right text-gray-700">
                      {formatPrice(sm.products_revenue)}
                    </td>
                    <td className="py-3.5 px-4 text-right text-green-600 font-medium">
                      +{formatPrice(sm.tips_earned)}
                    </td>
                    <td className="py-3.5 px-4 text-right font-extrabold text-brand-700">
                      {formatPrice(sm.total_revenue)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
