"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { api } from "@/lib/api";
import { toast } from "sonner";
import {
  Boxes, Plus, Trash2, CheckCircle2, User, Search, X, Layers,
} from "lucide-react";
import { cn, formatPrice } from "@/lib/utils";

export default function PackagesPage() {
  const { business } = useAuth();
  const [templates, setTemplates] = useState<any[]>([]);
  const [customerPackages, setCustomerPackages] = useState<any[]>([]);
  const [services, setServices] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"templates" | "customer_packages">("templates");
  const [loading, setLoading] = useState(true);

  // Modals
  const [isAddTemplateOpen, setIsAddTemplateOpen] = useState(false);
  const [isSellOpen, setIsSellOpen] = useState(false);

  // Forms
  const [newTemplate, setNewTemplate] = useState({
    name: "",
    description: "",
    price: 3499,
    validity_days: 180,
    items: [{ service_id: "", quantity: 1 }],
  });

  const [sellForm, setSellForm] = useState({
    customer_id: "",
    package_template_id: "",
  });

  useEffect(() => {
    if (!business?.id) return;
    loadData();
  }, [business?.id]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [tplRes, custPkgRes, svcRes, custRes] = await Promise.allSettled([
        api.get<any[]>(`/businesses/${business?.id}/packages/templates`),
        api.get<any[]>(`/businesses/${business?.id}/packages/customers`),
        api.get<any>(`/businesses/${business?.id}/services`),
        api.get<any>(`/customers`),
      ]);

      if (tplRes.status === "fulfilled") setTemplates(tplRes.value ?? []);
      if (custPkgRes.status === "fulfilled") setCustomerPackages(custPkgRes.value ?? []);
      if (svcRes.status === "fulfilled") setServices(svcRes.value?.items ?? svcRes.value ?? []);
      if (custRes.status === "fulfilled") setCustomers(custRes.value?.items ?? custRes.value ?? []);
    } catch (e) {
      toast.error("Failed to load packages");
    } finally {
      setLoading(false);
    }
  };

  const handleAddServiceItem = () => {
    setNewTemplate({
      ...newTemplate,
      items: [...newTemplate.items, { service_id: "", quantity: 1 }],
    });
  };

  const handleRemoveServiceItem = (index: number) => {
    setNewTemplate({
      ...newTemplate,
      items: newTemplate.items.filter((_, i) => i !== index),
    });
  };

  const handleCreateTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!business?.id || !newTemplate.name || newTemplate.items.some((i) => !i.service_id)) {
      toast.error("Please fill in all package items");
      return;
    }

    try {
      await api.post(`/businesses/${business.id}/packages/templates`, {
        ...newTemplate,
        price: Number(newTemplate.price),
        validity_days: Number(newTemplate.validity_days),
      });
      toast.success("Package bundle created!");
      setIsAddTemplateOpen(false);
      loadData();
    } catch (e: any) {
      toast.error(e?.message || "Failed to create package");
    }
  };

  const handleSellPackage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!business?.id || !sellForm.customer_id || !sellForm.package_template_id) {
      toast.error("Please choose a customer and a package");
      return;
    }

    try {
      await api.post(`/businesses/${business.id}/packages/sell`, sellForm);
      toast.success("Package sold successfully!");
      setIsSellOpen(false);
      loadData();
    } catch (e: any) {
      toast.error(e?.message || "Sale failed");
    }
  };

  const handleRedeemSession = async (customerPackageId: string, serviceId: string) => {
    if (!business?.id) return;
    try {
      await api.post(`/businesses/${business.id}/packages/customers/${customerPackageId}/redeem`, {
        service_id: serviceId,
      });
      toast.success("Session redeemed successfully!");
      loadData();
    } catch (e: any) {
      toast.error(e?.message || "Redemption failed");
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Boxes className="w-7 h-7 text-brand-600" /> Service Packages & Combos
          </h1>
          <p className="text-sm text-gray-500">Sell bundled service sessions and track customer redemptions</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setIsSellOpen(true)}
            className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-xl font-medium shadow-sm hover:bg-gray-50 text-sm"
          >
            Sell to Customer
          </button>
          <button
            onClick={() => setIsAddTemplateOpen(true)}
            className="px-4 py-2 bg-brand-600 text-white rounded-xl font-semibold shadow hover:bg-brand-700 flex items-center gap-1.5 text-sm"
          >
            <Plus className="w-4 h-4" /> Create Package
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 pb-2">
        <button
          onClick={() => setActiveTab("templates")}
          className={cn(
            "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
            activeTab === "templates" ? "bg-brand-50 text-brand-700" : "text-gray-600 hover:bg-gray-100"
          )}
        >
          Package Combos ({templates.length})
        </button>
        <button
          onClick={() => setActiveTab("customer_packages")}
          className={cn(
            "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
            activeTab === "customer_packages" ? "bg-brand-50 text-brand-700" : "text-gray-600 hover:bg-gray-100"
          )}
        >
          Purchased Packages ({customerPackages.length})
        </button>
      </div>

      {/* Templates View */}
      {activeTab === "templates" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {templates.length === 0 ? (
            <div className="col-span-3 text-center py-12 text-gray-400 bg-white rounded-xl border border-gray-200">
              No package templates created yet. Tap "Create Package" to bundle multiple services.
            </div>
          ) : (
            templates.map((tpl) => (
              <div
                key={tpl.id}
                className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-bold">
                      Valid {tpl.validity_days} Days
                    </span>
                    <span className="text-xl font-extrabold text-gray-900">
                      {formatPrice(tpl.price)}
                    </span>
                  </div>
                  <h3 className="font-bold text-gray-900 text-lg">{tpl.name}</h3>
                  <p className="text-sm text-gray-500">{tpl.description || "Bundled service combo"}</p>

                  <div className="space-y-1.5 pt-3 border-t border-gray-100 text-sm">
                    <p className="text-xs font-bold text-gray-500 uppercase tracking-wider">Includes:</p>
                    {tpl.items?.map((item: any, idx: number) => {
                      const svc = services.find((s) => s.id === item.service_id);
                      return (
                        <div key={idx} className="flex justify-between text-gray-700">
                          <span>{svc?.name || "Service session"}</span>
                          <span className="font-bold">x{item.quantity}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Purchased Packages View */}
      {activeTab === "customer_packages" && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-700 font-semibold border-b border-gray-200">
              <tr>
                <th className="py-3.5 px-4">Customer</th>
                <th className="py-3.5 px-4">Package</th>
                <th className="py-3.5 px-4">Expires</th>
                <th className="py-3.5 px-4">Sessions Usage</th>
                <th className="py-3.5 px-4 text-center">Status</th>
                <th className="py-3.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {customerPackages.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-10 text-gray-400">
                    No customer packages active.
                  </td>
                </tr>
              ) : (
                customerPackages.map((cp) => (
                  <tr key={cp.id} className="hover:bg-gray-50/75">
                    <td className="py-3.5 px-4 font-medium text-gray-900">
                      {cp.customer?.first_name || "Customer"} {cp.customer?.last_name || ""}
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-brand-700">
                      {cp.package_template?.name || "Package Combo"}
                    </td>
                    <td className="py-3.5 px-4 text-gray-600 text-xs">
                      {new Date(cp.expiry_date).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="space-y-1">
                        {cp.items?.map((itm: any) => {
                          const svc = services.find((s) => s.id === itm.service_id);
                          const remaining = Math.max(0, itm.total_quantity - itm.used_quantity);
                          return (
                            <div key={itm.id} className="flex items-center justify-between text-xs gap-2">
                              <span className="text-gray-700">{svc?.name || "Service"}:</span>
                              <span className="font-semibold text-gray-900">
                                {itm.used_quantity} / {itm.total_quantity} used ({remaining} left)
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <span
                        className={cn(
                          "px-2.5 py-1 rounded-full text-xs font-semibold",
                          cp.status === "ACTIVE" ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-700"
                        )}
                      >
                        {cp.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      {cp.status === "ACTIVE" && cp.items?.some((i: any) => i.used_quantity < i.total_quantity) && (
                        <button
                          onClick={() => {
                            const firstAvailable = cp.items.find((i: any) => i.used_quantity < i.total_quantity);
                            if (firstAvailable) handleRedeemSession(cp.id, firstAvailable.service_id);
                          }}
                          className="px-3 py-1 bg-brand-50 text-brand-700 hover:bg-brand-100 rounded-lg text-xs font-semibold"
                        >
                          Redeem 1
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Package Modal */}
      {isAddTemplateOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-start sm:items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-xl my-8 sm:my-0">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <h3 className="font-bold text-gray-900 text-lg">Create Package Combo</h3>
              <button onClick={() => setIsAddTemplateOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateTemplate} className="space-y-3 text-sm">
              <div>
                <label className="font-medium text-gray-700">Package Name *</label>
                <input
                  type="text"
                  required
                  value={newTemplate.name}
                  onChange={(e) => setNewTemplate({ ...newTemplate, name: e.target.value })}
                  placeholder="e.g. Bridal Glow 4-Session Package"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-medium text-gray-700">Price (₹) *</label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={newTemplate.price}
                    onChange={(e) => setNewTemplate({ ...newTemplate, price: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  />
                </div>
                <div>
                  <label className="font-medium text-gray-700">Validity (Days)</label>
                  <input
                    type="number"
                    min="1"
                    value={newTemplate.validity_days}
                    onChange={(e) => setNewTemplate({ ...newTemplate, validity_days: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  />
                </div>
              </div>

              {/* Service Line Items */}
              <div className="space-y-2 pt-2 border-t border-gray-100">
                <div className="flex justify-between items-center">
                  <label className="font-bold text-gray-800 text-xs uppercase">Included Services</label>
                  <button
                    type="button"
                    onClick={handleAddServiceItem}
                    className="text-xs text-brand-600 font-semibold hover:underline flex items-center gap-1"
                  >
                    <Plus className="w-3 h-3" /> Add Service
                  </button>
                </div>

                {newTemplate.items.map((item, idx) => (
                  <div key={idx} className="flex gap-2 items-center">
                    <select
                      required
                      value={item.service_id}
                      onChange={(e) => {
                        const next = [...newTemplate.items];
                        next[idx].service_id = e.target.value;
                        setNewTemplate({ ...newTemplate, items: next });
                      }}
                      className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-xs"
                    >
                      <option value="">Choose service...</option>
                      {services.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name} ({formatPrice(s.price)})
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      min="1"
                      value={item.quantity}
                      onChange={(e) => {
                        const next = [...newTemplate.items];
                        next[idx].quantity = Number(e.target.value);
                        setNewTemplate({ ...newTemplate, items: next });
                      }}
                      className="w-16 px-2 py-1.5 border border-gray-300 rounded-lg text-xs"
                    />
                    {newTemplate.items.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveServiceItem(idx)}
                        className="text-gray-400 hover:text-red-600 p-1"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>

              <div className="pt-3 flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setIsAddTemplateOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700"
                >
                  Create Package
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Sell Package Modal */}
      {isSellOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-start sm:items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl my-8 sm:my-0">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <h3 className="font-bold text-gray-900 text-lg">Sell Package to Customer</h3>
              <button onClick={() => setIsSellOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSellPackage} className="space-y-3 text-sm">
              <div>
                <label className="font-medium text-gray-700">Select Customer *</label>
                <select
                  required
                  value={sellForm.customer_id}
                  onChange={(e) => setSellForm({ ...sellForm, customer_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                >
                  <option value="">Choose customer...</option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.first_name || c.user?.first_name} {c.last_name || c.user?.last_name} ({c.email || c.user?.email})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="font-medium text-gray-700">Select Package *</label>
                <select
                  required
                  value={sellForm.package_template_id}
                  onChange={(e) => setSellForm({ ...sellForm, package_template_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                >
                  <option value="">Choose package combo...</option>
                  {templates.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name} — {formatPrice(t.price)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="pt-3 flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setIsSellOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700"
                >
                  Confirm Sale
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
