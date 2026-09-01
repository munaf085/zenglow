"use client";

import { useEffect, useState, useCallback } from "react";
import { CreditCard, Loader2, TrendingUp, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import { formatCurrency, formatDateTime, cn } from "@/lib/utils";
import { toast } from "sonner";

interface Payment {
  id: string;
  appointment_id?: string;
  customer_id: string;
  amount: number;
  currency: string;
  provider: string;
  status: string;
  provider_payment_id?: string;
  paid_at?: string;
  created_at: string;
}

const STATUS_STYLES: Record<string, string> = {
  CAPTURED:           "bg-green-100 text-green-700",
  PENDING:            "bg-yellow-100 text-yellow-700",
  FAILED:             "bg-red-100 text-red-700",
  REFUNDED:           "bg-purple-100 text-purple-700",
  PARTIALLY_REFUNDED: "bg-blue-100 text-blue-700",
  CANCELLED:          "bg-gray-100 text-gray-500",
  PROCESSING:         "bg-orange-100 text-orange-700",
};

export default function PaymentsPage() {
  const { business } = useAuth();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [refunding, setRefunding] = useState<string | null>(null);

  const totalRevenue = payments
    .filter((p) => p.status === "CAPTURED")
    .reduce((s, p) => s + p.amount, 0);

  const load = useCallback(async () => {
    if (!business) return;
    setIsLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: "20" });
      const res = await api.get<Payment[]>(
        `/businesses/${business.id}/payments?${params}`
      );
      setPayments(Array.isArray(res) ? res : []);
    } catch { setPayments([]); }
    finally { setIsLoading(false); }
  }, [business, page]);

  useEffect(() => { load(); }, [load]);

  const handleRefund = async (paymentId: string, amount: number) => {
    if (!confirm(`Refund ${formatCurrency(amount)}?`)) return;
    setRefunding(paymentId);
    try {
      await api.post(`/payments/${paymentId}/refunds`, { amount, reason: "Business-initiated refund" });
      toast.success("Refund initiated successfully");
      load();
    } catch (err: any) {
      toast.error(err.message ?? "Could not process refund");
    } finally {
      setRefunding(null);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Payments</h1>
          <p className="text-gray-500 text-sm mt-1">Transaction history for your business</p>
        </div>
      </div>

      {/* Revenue stat */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="w-9 h-9 bg-green-50 rounded-lg flex items-center justify-center mb-3">
            <TrendingUp className="w-4 h-4 text-green-600" />
          </div>
          <p className="text-xl font-bold text-gray-900">{formatCurrency(totalRevenue)}</p>
          <p className="text-xs text-gray-500 mt-0.5">Revenue (shown records)</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="w-9 h-9 bg-brand-50 rounded-lg flex items-center justify-center mb-3">
            <CreditCard className="w-4 h-4 text-brand-600" />
          </div>
          <p className="text-xl font-bold text-gray-900">
            {payments.filter(p => p.status === "CAPTURED").length}
          </p>
          <p className="text-xs text-gray-500 mt-0.5">Successful payments</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="w-9 h-9 bg-purple-50 rounded-lg flex items-center justify-center mb-3">
            <RefreshCw className="w-4 h-4 text-purple-600" />
          </div>
          <p className="text-xl font-bold text-gray-900">
            {payments.filter(p => ["REFUNDED","PARTIALLY_REFUNDED"].includes(p.status)).length}
          </p>
          <p className="text-xs text-gray-500 mt-0.5">Refunds</p>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-5 py-3 font-medium text-gray-600">Date</th>
                <th className="text-left px-5 py-3 font-medium text-gray-600 hidden sm:table-cell">Reference</th>
                <th className="text-left px-5 py-3 font-medium text-gray-600">Status</th>
                <th className="text-right px-5 py-3 font-medium text-gray-600">Amount</th>
                <th className="text-right px-5 py-3 font-medium text-gray-600 hidden md:table-cell">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                [...Array(5)].map((_, i) => (
                  <tr key={i}>
                    <td colSpan={5} className="px-5 py-3">
                      <div className="h-4 bg-gray-100 rounded animate-pulse" />
                    </td>
                  </tr>
                ))
              ) : payments.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-5 py-16 text-center">
                    <CreditCard className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500 text-sm">No payments recorded yet</p>
                  </td>
                </tr>
              ) : payments.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-4 text-gray-700">
                    {p.paid_at ? formatDateTime(p.paid_at) : formatDateTime(p.created_at)}
                  </td>
                  <td className="px-5 py-4 font-mono text-xs text-gray-500 hidden sm:table-cell">
                    {p.provider_payment_id
                      ? p.provider_payment_id.slice(0, 20) + "…"
                      : p.id.slice(0, 8) + "…"}
                  </td>
                  <td className="px-5 py-4">
                    <span className={cn("text-xs font-medium px-2 py-0.5 rounded-full",
                      STATUS_STYLES[p.status] ?? "bg-gray-100 text-gray-600")}>
                      {p.status}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right font-semibold text-gray-900">
                    {formatCurrency(p.amount)}
                  </td>
                  <td className="px-5 py-4 text-right hidden md:table-cell">
                    {p.status === "CAPTURED" && (
                      <button
                        onClick={() => handleRefund(p.id, p.amount)}
                        disabled={refunding === p.id}
                        className="flex items-center gap-1.5 text-xs font-medium text-purple-600 hover:text-purple-700 hover:bg-purple-50 px-2 py-1.5 rounded-lg ml-auto transition-colors disabled:opacity-50"
                      >
                        {refunding === p.id
                          ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          : <RefreshCw className="w-3.5 h-3.5" />}
                        Refund
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
