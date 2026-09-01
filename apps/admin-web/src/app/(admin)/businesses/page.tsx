"use client";

import { useEffect, useState, useCallback } from "react";
import { Search, CheckCircle, XCircle, Star, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { Business, PaginatedResponse } from "@zenglow/types";
import { formatDate, cn } from "@/lib/utils";
import { toast } from "sonner";

const STATUS_STYLES: Record<string, string> = {
  ACTIVE: "bg-green-100 text-green-700",
  PENDING: "bg-yellow-100 text-yellow-700",
  SUSPENDED: "bg-red-100 text-red-700",
  DEACTIVATED: "bg-gray-100 text-gray-500",
};

export default function AdminBusinesses() {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: "20" });
      if (q) params.set("q", q);
      const res = await api.get<PaginatedResponse<Business>>(`/admin/businesses?${params}`);
      setBusinesses(res.items);
      setTotal(res.total);
    } catch { /* ignore */ }
    finally { setIsLoading(false); }
  }, [page, q]);

  useEffect(() => { load(); }, [load]);

  const updateBusiness = async (id: string, data: Record<string, unknown>) => {
    try {
      await api.patch(`/admin/businesses/${id}`, data);
      toast.success("Business updated");
      load();
    } catch (err: any) { toast.error(err.message); }
  };

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Businesses</h1>
          <p className="text-gray-500 text-sm">{total} total</p>
        </div>
      </div>

      <div className="mb-4 relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          value={q}
          onChange={(e) => { setQ(e.target.value); setPage(1); }}
          placeholder="Search businesses..."
          className="w-full max-w-sm pl-10 pr-4 py-2.5 bg-white rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-5 py-3 font-medium text-gray-600">Business</th>
                <th className="text-left px-5 py-3 font-medium text-gray-600 hidden sm:table-cell">Category</th>
                <th className="text-left px-5 py-3 font-medium text-gray-600">Status</th>
                <th className="text-left px-5 py-3 font-medium text-gray-600 hidden md:table-cell">Created</th>
                <th className="text-right px-5 py-3 font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                [...Array(5)].map((_, i) => (
                  <tr key={i}>
                    <td colSpan={5} className="px-5 py-4">
                      <div className="h-4 bg-gray-200 rounded animate-pulse w-full" />
                    </td>
                  </tr>
                ))
              ) : businesses.length === 0 ? (
                <tr><td colSpan={5} className="px-5 py-12 text-center text-gray-400">No businesses found</td></tr>
              ) : businesses.map((b) => (
                <tr key={b.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-brand-100 rounded-lg flex items-center justify-center flex-shrink-0">
                        <span className="text-brand-700 font-bold text-xs">{b.name[0]}</span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{b.name}</p>
                        {b.is_verified && <span className="text-xs text-green-600 flex items-center gap-0.5"><CheckCircle className="w-3 h-3" /> Verified</span>}
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-4 text-gray-500 hidden sm:table-cell capitalize">{b.category.toLowerCase()}</td>
                  <td className="px-5 py-4">
                    <span className={cn("text-xs font-medium px-2 py-0.5 rounded-full", STATUS_STYLES[b.status] ?? "bg-gray-100 text-gray-600")}>
                      {b.status}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-gray-500 hidden md:table-cell">{formatDate(b.created_at)}</td>
                  <td className="px-5 py-4">
                    <div className="flex items-center justify-end gap-1">
                      {b.status === "ACTIVE" ? (
                        <button
                          onClick={() => updateBusiness(b.id, { status: "SUSPENDED" })}
                          className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Suspend"
                        >
                          <XCircle className="w-4 h-4" />
                        </button>
                      ) : (
                        <button
                          onClick={() => updateBusiness(b.id, { status: "ACTIVE" })}
                          className="p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                          title="Activate"
                        >
                          <CheckCircle className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => updateBusiness(b.id, { is_featured: !b.is_featured })}
                        className={cn("p-1.5 rounded-lg transition-colors", b.is_featured ? "text-yellow-500 bg-yellow-50" : "text-gray-400 hover:text-yellow-500 hover:bg-yellow-50")}
                        title={b.is_featured ? "Unfeature" : "Feature"}
                      >
                        <Star className="w-4 h-4" />
                      </button>
                      {!b.is_verified && (
                        <button
                          onClick={() => updateBusiness(b.id, { is_verified: true })}
                          className="px-2 py-1 text-xs font-medium text-brand-600 hover:text-brand-700 hover:bg-brand-50 rounded-lg transition-colors"
                        >
                          Verify
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {total > 20 && (
          <div className="px-5 py-3 border-t border-gray-200 flex items-center justify-between text-sm text-gray-500">
            <span>Showing {(page - 1) * 20 + 1}–{Math.min(page * 20, total)} of {total}</span>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="px-3 py-1 border border-gray-300 rounded-lg disabled:opacity-50 hover:bg-gray-50">Previous</button>
              <button onClick={() => setPage(p => p + 1)} disabled={page * 20 >= total} className="px-3 py-1 border border-gray-300 rounded-lg disabled:opacity-50 hover:bg-gray-50">Next</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
