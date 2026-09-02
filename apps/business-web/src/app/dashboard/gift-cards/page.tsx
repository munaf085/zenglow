"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { api } from "@/lib/api";
import { toast } from "sonner";
import {
  Gift, Plus, Search, CheckCircle2, Copy, X, Calendar, User,
} from "lucide-react";
import { cn, formatPrice } from "@/lib/utils";

export default function GiftCardsPage() {
  const { business } = useAuth();
  const [giftCards, setGiftCards] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchCode, setSearchCode] = useState("");
  const [lookupResult, setLookupResult] = useState<any | null>(null);

  // Modals
  const [isIssueOpen, setIsIssueOpen] = useState(false);

  // Form
  const [issueForm, setIssueForm] = useState({
    amount: 1000,
    recipient_name: "",
    recipient_email: "",
    recipient_phone: "",
    message: "",
    expiry_days: 365,
  });

  useEffect(() => {
    if (!business?.id) return;
    loadGiftCards();
  }, [business?.id]);

  const loadGiftCards = async () => {
    try {
      setLoading(true);
      const res = await api.get<any[]>(`/businesses/${business?.id}/gift-cards`);
      setGiftCards(res ?? []);
    } catch (e) {
      toast.error("Failed to load gift cards");
    } finally {
      setLoading(false);
    }
  };

  const handleIssueGiftCard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!business?.id || issueForm.amount <= 0) return;

    try {
      const res = await api.post<any>(`/businesses/${business.id}/gift-cards`, {
        ...issueForm,
        amount: Number(issueForm.amount),
        expiry_days: Number(issueForm.expiry_days),
      });
      toast.success(`Gift Card ${res.code} issued successfully!`);
      setIsIssueOpen(false);
      setIssueForm({
        amount: 1000,
        recipient_name: "",
        recipient_email: "",
        recipient_phone: "",
        message: "",
        expiry_days: 365,
      });
      loadGiftCards();
    } catch (e: any) {
      toast.error(e?.message || "Failed to issue gift card");
    }
  };

  const handleCheckBalance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!business?.id || !searchCode) return;

    try {
      const res = await api.get<any>(`/businesses/${business.id}/gift-cards/check/${searchCode.trim()}`);
      setLookupResult(res);
    } catch (e: any) {
      toast.error(e?.message || "Gift card code not found");
      setLookupResult(null);
    }
  };

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    toast.success(`Copied ${code} to clipboard`);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Gift className="w-7 h-7 text-brand-600" /> Digital Gift Cards
          </h1>
          <p className="text-sm text-gray-500">Issue custom gift cards, lookup balances, and accept at POS checkout</p>
        </div>
        <button
          onClick={() => setIsIssueOpen(true)}
          className="px-4 py-2 bg-brand-600 text-white rounded-xl font-semibold shadow hover:bg-brand-700 flex items-center gap-1.5 text-sm w-fit"
        >
          <Plus className="w-4 h-4" /> Issue Gift Card
        </button>
      </div>

      {/* Balance Lookup Widget */}
      <div className="bg-gradient-to-r from-brand-50 to-indigo-50 p-5 rounded-2xl border border-brand-100 shadow-sm flex flex-col md:flex-row gap-4 items-center justify-between">
        <div>
          <h3 className="font-bold text-gray-900 text-sm">Quick Balance Lookup</h3>
          <p className="text-xs text-gray-600">Verify a customer's gift card code and available credit</p>
        </div>
        <form onSubmit={handleCheckBalance} className="flex gap-2 w-full md:w-auto">
          <input
            type="text"
            placeholder="Enter GC-XXXX-XXXX..."
            value={searchCode}
            onChange={(e) => setSearchCode(e.target.value.toUpperCase())}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm uppercase font-mono w-full sm:w-56 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-semibold hover:bg-brand-700 whitespace-nowrap"
          >
            Check
          </button>
        </form>
      </div>

      {lookupResult && (
        <div className="bg-white p-4 rounded-xl border border-brand-200 shadow-sm flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-6 h-6 text-green-600" />
            <div>
              <span className="font-mono font-bold text-brand-700 text-base">{lookupResult.code}</span>
              <p className="text-xs text-gray-500">Recipient: {lookupResult.recipient_name || "Any Customer"}</p>
            </div>
          </div>
          <div className="text-right">
            <span className="text-xs text-gray-500">Current Balance</span>
            <p className="text-xl font-extrabold text-green-600">{formatPrice(lookupResult.current_balance)}</p>
          </div>
        </div>
      )}

      {/* Gift Cards Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-700 font-semibold border-b border-gray-200">
              <tr>
                <th className="py-3.5 px-4">Card Code</th>
                <th className="py-3.5 px-4">Recipient</th>
                <th className="py-3.5 px-4 text-right">Initial Value</th>
                <th className="py-3.5 px-4 text-right">Available Balance</th>
                <th className="py-3.5 px-4">Expires</th>
                <th className="py-3.5 px-4 text-center">Status</th>
                <th className="py-3.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-gray-400">
                    Loading gift cards...
                  </td>
                </tr>
              ) : giftCards.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-gray-400">
                    No gift cards issued yet. Tap "Issue Gift Card" above!
                  </td>
                </tr>
              ) : (
                giftCards.map((gc) => (
                  <tr key={gc.id} className="hover:bg-gray-50/75">
                    <td className="py-3.5 px-4 font-mono font-bold text-brand-700">
                      {gc.code}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-gray-900">
                      {gc.recipient_name || "—"}
                      {gc.recipient_email && (
                        <div className="text-xs text-gray-400">{gc.recipient_email}</div>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right text-gray-600">
                      {formatPrice(gc.initial_balance)}
                    </td>
                    <td className="py-3.5 px-4 text-right font-extrabold text-green-700">
                      {formatPrice(gc.current_balance)}
                    </td>
                    <td className="py-3.5 px-4 text-gray-500 text-xs">
                      {gc.expiry_date ? new Date(gc.expiry_date).toLocaleDateString() : "No expiry"}
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <span
                        className={cn(
                          "px-2.5 py-1 rounded-full text-xs font-semibold",
                          gc.is_active && gc.current_balance > 0
                            ? "bg-green-100 text-green-800"
                            : "bg-gray-100 text-gray-700"
                        )}
                      >
                        {gc.is_active && gc.current_balance > 0 ? "Active" : "Redeemed / Inactive"}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => copyCode(gc.code)}
                        className="p-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-600 transition-colors"
                        title="Copy Code"
                      >
                        <Copy className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Issue Gift Card Modal */}
      {isIssueOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-start sm:items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl my-8 sm:my-0">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <h3 className="font-bold text-gray-900 text-lg">Issue New Gift Card</h3>
              <button onClick={() => setIsIssueOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleIssueGiftCard} className="space-y-3 text-sm">
              <div>
                <label className="font-medium text-gray-700">Gift Amount (₹) *</label>
                <input
                  type="number"
                  required
                  min="100"
                  step="50"
                  value={issueForm.amount}
                  onChange={(e) => setIssueForm({ ...issueForm, amount: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                />
              </div>

              <div>
                <label className="font-medium text-gray-700">Recipient Name</label>
                <input
                  type="text"
                  value={issueForm.recipient_name}
                  onChange={(e) => setIssueForm({ ...issueForm, recipient_name: e.target.value })}
                  placeholder="e.g. Priya Sharma"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-medium text-gray-700">Recipient Email</label>
                  <input
                    type="email"
                    value={issueForm.recipient_email}
                    onChange={(e) => setIssueForm({ ...issueForm, recipient_email: e.target.value })}
                    placeholder="priya@example.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  />
                </div>
                <div>
                  <label className="font-medium text-gray-700">Validity (Days)</label>
                  <input
                    type="number"
                    min="30"
                    value={issueForm.expiry_days}
                    onChange={(e) => setIssueForm({ ...issueForm, expiry_days: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  />
                </div>
              </div>

              <div>
                <label className="font-medium text-gray-700">Gift Message</label>
                <textarea
                  rows={2}
                  value={issueForm.message}
                  onChange={(e) => setIssueForm({ ...issueForm, message: e.target.value })}
                  placeholder="e.g. Happy Anniversary! Enjoy your pampering day."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                />
              </div>

              <div className="pt-3 flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setIsIssueOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700"
                >
                  Issue Card
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
