"use client";

import { useEffect, useState, useCallback } from "react";
import { Calendar, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { formatDate, formatCurrency, cn } from "@/lib/utils";

interface BookingRow {
  id: string;
  business_id: string;
  status: string;
  start_time: string;
  total_amount: number;
  created_at: string;
}

interface PaginatedBookings {
  items: BookingRow[];
  total: number;
  page: number;
  pages: number;
}

const STATUS_STYLES: Record<string, string> = {
  CONFIRMED:   "bg-green-100 text-green-700",
  PENDING:     "bg-yellow-100 text-yellow-700",
  COMPLETED:   "bg-gray-100 text-gray-600",
  CANCELLED:   "bg-red-100 text-red-700",
  IN_PROGRESS: "bg-blue-100 text-blue-700",
  NO_SHOW:     "bg-orange-100 text-orange-700",
  RESCHEDULED: "bg-purple-100 text-purple-700",
};

export default function AdminBookingsPage() {
  const [bookings, setBookings] = useState<BookingRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: "20" });
      const res = await api.get<PaginatedBookings>(`/admin/bookings?${params}`);
      setBookings(res.items);
      setTotal(res.total);
    } catch { setBookings([]); }
    finally { setIsLoading(false); }
  }, [page]);

  useEffect(() => { load(); }, [load]);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Bookings</h1>
        <p className="text-gray-500 text-sm mt-1">{total} total appointments</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-5 py-3 font-medium text-gray-600">Booking ID</th>
                <th className="text-left px-5 py-3 font-medium text-gray-600 hidden sm:table-cell">Date</th>
                <th className="text-left px-5 py-3 font-medium text-gray-600">Status</th>
                <th className="text-right px-5 py-3 font-medium text-gray-600">Amount</th>
                <th className="text-left px-5 py-3 font-medium text-gray-600 hidden md:table-cell">Created</th>
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
              ) : bookings.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-5 py-16 text-center">
                    <Calendar className="w-10 h-10 text-gray-200 mx-auto mb-3" />
                    <p className="text-gray-400 text-sm">No bookings found</p>
                  </td>
                </tr>
              ) : bookings.map((b) => (
                <tr key={b.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-4 font-mono text-xs text-gray-500">
                    {b.id.slice(0, 8)}…
                  </td>
                  <td className="px-5 py-4 text-gray-700 hidden sm:table-cell">
                    {formatDate(b.start_time)}
                  </td>
                  <td className="px-5 py-4">
                    <span className={cn(
                      "text-xs font-medium px-2 py-0.5 rounded-full",
                      STATUS_STYLES[b.status] ?? "bg-gray-100 text-gray-600"
                    )}>
                      {b.status.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right font-semibold text-gray-900">
                    {formatCurrency(b.total_amount)}
                  </td>
                  <td className="px-5 py-4 text-gray-500 hidden md:table-cell">
                    {formatDate(b.created_at)}
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
