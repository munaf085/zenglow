"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { api } from "@/lib/api";
import { toast } from "sonner";
import {
  FileText, Search, Printer, Eye, Calendar, User, ArrowUpRight, X,
} from "lucide-react";
import { cn, formatPrice } from "@/lib/utils";

export default function InvoicesPage() {
  const { business } = useAuth();
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedInvoice, setSelectedInvoice] = useState<any | null>(null);

  useEffect(() => {
    if (!business?.id) return;
    loadInvoices();
  }, [business?.id]);

  const loadInvoices = async () => {
    try {
      setLoading(true);
      const res = await api.get<any[]>(`/businesses/${business?.id}/pos/orders`);
      setInvoices(res ?? []);
    } catch (e) {
      toast.error("Failed to load invoices");
    } finally {
      setLoading(false);
    }
  };

  const filtered = invoices.filter((inv) =>
    inv.order_number?.toLowerCase().includes(search.toLowerCase()) ||
    inv.customer?.first_name?.toLowerCase().includes(search.toLowerCase()) ||
    inv.customer?.last_name?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <FileText className="w-7 h-7 text-brand-600" /> Invoices & Receipts
          </h1>
          <p className="text-sm text-gray-500">View and print sales receipts, customer invoices, and tax breakdowns</p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex items-center justify-between">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search invoice # or customer..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:outline-none"
          />
        </div>
        <span className="text-xs text-gray-500 font-medium">
          Showing {filtered.length} invoices
        </span>
      </div>

      {/* Invoices Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-700 font-semibold border-b border-gray-200">
              <tr>
                <th className="py-3.5 px-4">Invoice / Order #</th>
                <th className="py-3.5 px-4">Customer</th>
                <th className="py-3.5 px-4">Date</th>
                <th className="py-3.5 px-4 text-right">Subtotal</th>
                <th className="py-3.5 px-4 text-right">Tax (GST)</th>
                <th className="py-3.5 px-4 text-right">Total Amount</th>
                <th className="py-3.5 px-4 text-center">Status</th>
                <th className="py-3.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr>
                  <td colSpan={8} className="text-center py-8 text-gray-400">
                    Loading invoices...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-10 text-gray-400">
                    No invoices generated yet.
                  </td>
                </tr>
              ) : (
                filtered.map((inv) => (
                  <tr key={inv.id} className="hover:bg-gray-50/75 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-semibold text-brand-700">
                      {inv.order_number}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-gray-900">
                      {inv.customer
                        ? `${inv.customer.first_name || ""} ${inv.customer.last_name || ""}`.trim()
                        : "Walk-in Customer"}
                    </td>
                    <td className="py-3.5 px-4 text-gray-500 text-xs">
                      {new Date(inv.created_at).toLocaleDateString("en-IN", {
                        day: "numeric",
                        month: "short",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td className="py-3.5 px-4 text-right text-gray-600">
                      {formatPrice(inv.subtotal)}
                    </td>
                    <td className="py-3.5 px-4 text-right text-gray-600">
                      {formatPrice(inv.tax_amount)}
                    </td>
                    <td className="py-3.5 px-4 text-right font-bold text-gray-900">
                      {formatPrice(inv.total_amount)}
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <span className="px-2.5 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold">
                        {inv.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => setSelectedInvoice(inv)}
                        className="px-2.5 py-1 bg-gray-100 hover:bg-brand-50 hover:text-brand-700 rounded-lg text-xs font-semibold inline-flex items-center gap-1 transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" /> View Receipt
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Invoice Modal */}
      {selectedInvoice && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div>
                <h3 className="font-bold text-gray-900 text-lg">Tax Invoice</h3>
                <p className="text-xs font-mono text-gray-500">{selectedInvoice.order_number}</p>
              </div>
              <button onClick={() => setSelectedInvoice(null)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="text-xs text-gray-600 space-y-1">
              <p><strong>Business:</strong> {business?.name}</p>
              <p><strong>Customer:</strong> {selectedInvoice.customer ? `${selectedInvoice.customer.first_name} ${selectedInvoice.customer.last_name || ""}` : "Walk-in"}</p>
              <p><strong>Date:</strong> {new Date(selectedInvoice.created_at).toLocaleString()}</p>
            </div>

            {/* Line Items */}
            <div className="border-t border-b border-gray-200 py-2 space-y-1.5 text-xs">
              {selectedInvoice.items?.map((item: any, idx: number) => (
                <div key={idx} className="flex justify-between">
                  <span>{item.quantity}x {item.name}</span>
                  <span className="font-semibold">{formatPrice(item.total_price)}</span>
                </div>
              ))}
            </div>

            <div className="space-y-1 text-xs text-right">
              <div className="flex justify-between text-gray-600">
                <span>Subtotal:</span>
                <span>{formatPrice(selectedInvoice.subtotal)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Tax:</span>
                <span>{formatPrice(selectedInvoice.tax_amount)}</span>
              </div>
              {selectedInvoice.discount_amount > 0 && (
                <div className="flex justify-between text-green-600">
                  <span>Discount:</span>
                  <span>-{formatPrice(selectedInvoice.discount_amount)}</span>
                </div>
              )}
              <div className="flex justify-between font-bold text-sm text-gray-900 pt-1 border-t border-gray-100">
                <span>Total Paid:</span>
                <span className="text-brand-600">{formatPrice(selectedInvoice.total_amount)}</span>
              </div>
            </div>

            <div className="pt-2 flex gap-2">
              <button
                onClick={() => window.print()}
                className="flex-1 py-2 bg-brand-600 text-white rounded-lg text-sm font-semibold flex items-center justify-center gap-1.5 hover:bg-brand-700"
              >
                <Printer className="w-4 h-4" /> Print Receipt
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
