"use client";

import { useEffect, useState, useCallback } from "react";
import { CreditCard, TrendingUp, RefreshCw, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { Payment, PaginatedResponse } from "@zenglow/types";
import { formatCurrency, formatDate, cn } from "@/lib/utils";

const STATUS_STYLES: Record<string, string> = {
  CAPTURED:           "bg-green-100 text-green-700",
  PENDING:            "bg-yellow-100 text-yellow-700",
  FAILED:             "bg-red-100 text-red-700",
  REFUNDED:           "bg-purple-100 text-purple-700",
  PARTIALLY_REFUNDED: "bg-blue-100 text-blue-700",
  CANCELLED:          "bg-gray-100 text-gray-500",
  PROCESSING:         "bg-orange-100 text-orange-700",
};

export default function AdminPaymentsPage() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: "20" });
      const res = await api.get<PaginatedResponse<Payment>>(`/admin/payments?${params}`);
      setPayments(res.items);
      setTotal(res.total);
    } catch { setPayments([]); }
    finally { setIsLoading(false); }
  }, [page]);

  useEffect(() => { load(); }, [load]);

  const totalRevenue = payments
    .filter((p) => p.status === "CAPTURED")
    .reduce((s, p) => s + p.amount, 0);

  const refundCount = payments
    .filter((p) => ["REFUNDED", "PARTIALLY_REFUNDED"].includes(p.status)).length;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Payments</h1>
        <p className="text-gray-500 text-sm mt-1">All platform transactions</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          { label: "Total (shown)", value: formatCurrency(totalRevenue), icon: TrendingUp, color: "text-green-600", bg: "bg-green-50" },
          { label: "Transactions", value: payments.length, icon: CreditCard, color: "text-brand-600", bg: "bg-brand-50" },
          { label: "Successful", value: payments.filter(p => p.status === "CAPTURED").length, icon: CreditCard, color: "text-blue-600", bg: "bg-blue-50" },
          { label: "Refunds", value: refundCount, icon: RefreshCw, color: "text-purple-600", bg: "bg-purple-50" },
        ].map((card) => (
          <div key={card.label} className="bg-white rounded-xl border border-gray-200 p-5">
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-3 ${card.bg}`}>
              <card.icon className={`w-4 h-4 ${card.color}`} />
            </div>
            <p className="text-xl font-bold text-gray-900">{card.value}</p>
            <p className="text-xs text-gray-500 mt-0.5">{card.label}</p>
          </div>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-5 py-3 font-medium text-gray-600">Date</th>
                <th className="text-left px-5 py-3 font-medium text-gray-600 hidden sm:table-cell">Provider</th>
                <th className="text-left px-5 py-3 font-medium text-gray-600">Status</th>
                <th className="text-left px-5 py-3 font-medium text-gray-600 hidden md:table-cell">Reference</th>
                <th className="text-right px-5 py-3 font-medium text-gray-600">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                [...Array(8)].map((_, i) => (
                  <tr key={i}>
                    {[...Array(5)].map((_, j) => (
                      <td key={j} className="px-5 py-3">
                        <div className="h-4 bg-gray-100 rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : payments.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-5 py-16 text-center">
                    <CreditCard className="w-10 h-10 text-gray-200 mx-auto mb-3" />
                    <p className="text-gray-400 text-sm">No payments recorded yet</p>
                  </td>
                </tr>
              ) : payments.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-4 text-gray-700">{formatDate(p.created_at)}</td>
                  <td className="px-5 py-4 text-gray-500 capitalize hidden sm:table-cell">
                    {p.provider.toLowerCase()}
                  </td>
                  <td className="px-5 py-4">
                    <span className={cn(
                      "text-xs font-medium px-2 py-0.5 rounded-full",
                      STATUS_STYLES[p.status] ?? "bg-gray-100 text-gray-600"
                    )}>
                      {p.status}
                    </span>
                  </td>
                  <td className="px-5 py-4 font-mono text-xs text-gray-400 hidden md:table-cell">
                    {p.provider_payment_id
                      ? p.provider_payment_id.slice(0, 24) + "…"
                      : p.id.slice(0, 8) + "…"}
                  </td>
                  <td className="px-5 py-4 text-right font-semibold text-gray-900">
                    {formatCurrency(p.amount)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {total > 20 && (
          <div className="px-5 py-3 border-t border-gray-200 flex items-center justify-between text-sm text-gray-500">
            <span>Page {page} of {Math.ceil(total / 20)}</span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={page * 20 >= total}
                className="px-3 py-1 border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
