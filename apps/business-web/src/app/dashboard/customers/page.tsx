"use client";

import { useEffect, useState, useCallback } from "react";
import { Search, User, Loader2, ChevronRight } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import { cn, initials, formatDate } from "@/lib/utils";

interface CustomerProfile {
  id: string;
  user_id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  notes?: string;
  tags?: string;
  created_at: string;
}

interface PaginatedCustomers {
  items: CustomerProfile[];
  total: number;
  page: number;
  pages: number;
}

export default function CustomersPage() {
  const { business } = useAuth();
  const [customers, setCustomers] = useState<CustomerProfile[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [selected, setSelected] = useState<CustomerProfile | null>(null);
  const [editNotes, setEditNotes] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const load = useCallback(async () => {
    if (!business) return;
    setIsLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: "20" });
      if (q) params.set("q", q);
      const res = await api.get<PaginatedCustomers>(
        `/businesses/${business.id}/customers?${params}`
      );
      setCustomers(res.items);
      setTotal(res.total);
    } catch { setCustomers([]); }
    finally { setIsLoading(false); }
  }, [business, page, q]);

  useEffect(() => { load(); }, [load]);

  const openCustomer = (c: CustomerProfile) => {
    setSelected(c);
    setEditNotes(c.notes ?? "");
  };

  const saveNotes = async () => {
    if (!business || !selected) return;
    setIsSaving(true);
    try {
      await api.patch(`/businesses/${business.id}/customers/${selected.id}`, {
        notes: editNotes || undefined,
      });
      setSelected({ ...selected, notes: editNotes });
      load();
    } catch { /* ignore */ }
    finally { setIsSaving(false); }
  };

  return (
    <div className="flex gap-6 h-full">
      {/* List */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Customers</h1>
            <p className="text-gray-500 text-sm mt-1">{total} total customers</p>
          </div>
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            value={q}
            onChange={(e) => { setQ(e.target.value); setPage(1); }}
            placeholder="Search by name or email..."
            className="w-full max-w-sm pl-10 pr-4 py-2.5 bg-white rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {isLoading ? (
            <div className="flex justify-center py-16">
              <Loader2 className="w-6 h-6 animate-spin text-brand-600" />
            </div>
          ) : customers.length === 0 ? (
            <div className="text-center py-16">
              <User className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="font-medium text-gray-900 mb-1">No customers yet</p>
              <p className="text-sm text-gray-500">Customers appear here once they book with your business</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {customers.map((c) => (
                <button
                  key={c.id}
                  onClick={() => openCustomer(c)}
                  className={cn(
                    "w-full flex items-center gap-4 px-5 py-4 hover:bg-gray-50 transition-colors text-left",
                    selected?.id === c.id && "bg-brand-50"
                  )}
                >
                  <div className="w-10 h-10 bg-brand-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-brand-700 text-sm font-semibold">
                      {initials(c.first_name, c.last_name)}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 text-sm">
                      {c.first_name} {c.last_name}
                    </p>
                    <p className="text-xs text-gray-500 truncate">{c.email}</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                </button>
              ))}
            </div>
          )}

          {/* Pagination */}
          {total > 20 && (
            <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between text-sm text-gray-500">
              <span>Page {page} of {Math.ceil(total / 20)}</span>
              <div className="flex gap-2">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                  className="px-3 py-1 border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50">Prev</button>
                <button onClick={() => setPage(p => p + 1)} disabled={page * 20 >= total}
                  className="px-3 py-1 border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50">Next</button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Detail panel */}
      {selected && (
        <div className="w-80 flex-shrink-0">
          <div className="bg-white rounded-xl border border-gray-200 p-5 sticky top-8">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-12 h-12 bg-brand-100 rounded-full flex items-center justify-center">
                <span className="text-brand-700 font-bold">{initials(selected.first_name, selected.last_name)}</span>
              </div>
              <div>
                <p className="font-semibold text-gray-900">{selected.first_name} {selected.last_name}</p>
                <p className="text-xs text-gray-500">{selected.email}</p>
              </div>
            </div>

            <div className="space-y-3 mb-5 text-sm text-gray-600">
              {selected.phone && <p>📱 {selected.phone}</p>}
              <p>📅 Customer since {formatDate(selected.created_at)}</p>
              {selected.tags && (
                <div className="flex flex-wrap gap-1">
                  {selected.tags.split(",").map(t => t.trim()).filter(Boolean).map(tag => (
                    <span key={tag} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs">{tag}</span>
                  ))}
                </div>
              )}
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
                Staff notes
              </label>
              <textarea
                value={editNotes}
                onChange={(e) => setEditNotes(e.target.value)}
                rows={4}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
                placeholder="Add notes visible to your staff only..."
              />
              <button
                onClick={saveNotes}
                disabled={isSaving}
                className="w-full mt-2 flex items-center justify-center gap-2 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium"
              >
                {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                Save notes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
