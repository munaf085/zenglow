"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { api } from "@/lib/api";
import { toast } from "sonner";
import {
  Award, Plus, Users, Search, CheckCircle, Calendar, Sparkles, X,
} from "lucide-react";
import { cn, formatPrice } from "@/lib/utils";

export default function MembershipsPage() {
  const { business } = useAuth();
  const [plans, setPlans] = useState<any[]>([]);
  const [customerMemberships, setCustomerMemberships] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"plans" | "subscribers">("plans");
  const [loading, setLoading] = useState(true);

  // Modals
  const [isAddPlanOpen, setIsAddPlanOpen] = useState(false);
  const [isEnrollOpen, setIsEnrollOpen] = useState(false);

  // Forms
  const [newPlan, setNewPlan] = useState({
    name: "",
    description: "",
    price: 1999,
    duration_months: 12,
    discount_percentage: 10,
    free_services_count: 1,
  });

  const [enrollForm, setEnrollForm] = useState({
    customer_id: "",
    plan_id: "",
    notes: "",
  });

  useEffect(() => {
    if (!business?.id) return;
    loadData();
  }, [business?.id]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [plansRes, memsRes, custRes] = await Promise.allSettled([
        api.get<any[]>(`/businesses/${business?.id}/memberships/plans`),
        api.get<any[]>(`/businesses/${business?.id}/memberships/customers`),
        api.get<any>(`/customers`),
      ]);

      if (plansRes.status === "fulfilled") setPlans(plansRes.value ?? []);
      if (memsRes.status === "fulfilled") setCustomerMemberships(memsRes.value ?? []);
      if (custRes.status === "fulfilled") setCustomers(custRes.value?.items ?? custRes.value ?? []);
    } catch (e) {
      toast.error("Failed to load memberships");
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!business?.id || !newPlan.name) return;

    try {
      await api.post(`/businesses/${business.id}/memberships/plans`, {
        ...newPlan,
        price: Number(newPlan.price),
        duration_months: Number(newPlan.duration_months),
        discount_percentage: Number(newPlan.discount_percentage),
        free_services_count: Number(newPlan.free_services_count),
      });
      toast.success("Membership plan created!");
      setIsAddPlanOpen(false);
      loadData();
    } catch (e: any) {
      toast.error(e?.message || "Failed to create plan");
    }
  };

  const handleEnroll = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!business?.id || !enrollForm.customer_id || !enrollForm.plan_id) {
      toast.error("Please select a customer and a plan");
      return;
    }

    try {
      await api.post(`/businesses/${business.id}/memberships/enroll`, enrollForm);
      toast.success("Customer enrolled successfully!");
      setIsEnrollOpen(false);
      loadData();
    } catch (e: any) {
      toast.error(e?.message || "Enrollment failed");
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Award className="w-7 h-7 text-brand-600" /> Memberships & VIP Clubs
          </h1>
          <p className="text-sm text-gray-500">Create membership tiers, member-only discounts, and track subscriptions</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setIsEnrollOpen(true)}
            className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-xl font-medium shadow-sm hover:bg-gray-50 text-sm"
          >
            Enroll Customer
          </button>
          <button
            onClick={() => setIsAddPlanOpen(true)}
            className="px-4 py-2 bg-brand-600 text-white rounded-xl font-semibold shadow hover:bg-brand-700 flex items-center gap-1.5 text-sm"
          >
            <Plus className="w-4 h-4" /> Create Plan
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 pb-2">
        <button
          onClick={() => setActiveTab("plans")}
          className={cn(
            "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
            activeTab === "plans" ? "bg-brand-50 text-brand-700" : "text-gray-600 hover:bg-gray-100"
          )}
        >
          Membership Tiers ({plans.length})
        </button>
        <button
          onClick={() => setActiveTab("subscribers")}
          className={cn(
            "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
            activeTab === "subscribers" ? "bg-brand-50 text-brand-700" : "text-gray-600 hover:bg-gray-100"
          )}
        >
          Active Subscribers ({customerMemberships.length})
        </button>
      </div>

      {/* Plans View */}
      {activeTab === "plans" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.length === 0 ? (
            <div className="col-span-3 text-center py-12 text-gray-400 bg-white rounded-xl border border-gray-200">
              No membership plans created yet. Tap "Create Plan" to get started.
            </div>
          ) : (
            plans.map((plan) => (
              <div
                key={plan.id}
                className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="px-3 py-1 bg-brand-100 text-brand-800 rounded-full text-xs font-bold">
                      {plan.duration_months} Months
                    </span>
                    <span className="text-xl font-extrabold text-gray-900">
                      {formatPrice(plan.price)}
                    </span>
                  </div>
                  <h3 className="font-bold text-gray-900 text-lg">{plan.name}</h3>
                  <p className="text-sm text-gray-500">{plan.description || "Salon membership plan"}</p>

                  <div className="space-y-2 pt-3 border-t border-gray-100 text-sm text-gray-700">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-brand-600" />
                      <span><strong>{plan.discount_percentage}% OFF</strong> on all services</span>
                    </div>
                    {plan.free_services_count > 0 && (
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span><strong>{plan.free_services_count}</strong> complimentary sessions</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Subscribers View */}
      {activeTab === "subscribers" && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-700 font-semibold border-b border-gray-200">
              <tr>
                <th className="py-3.5 px-4">Customer</th>
                <th className="py-3.5 px-4">Plan</th>
                <th className="py-3.5 px-4">Valid Until</th>
                <th className="py-3.5 px-4 text-center">Free Sessions Left</th>
                <th className="py-3.5 px-4 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {customerMemberships.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-10 text-gray-400">
                    No active subscribers.
                  </td>
                </tr>
              ) : (
                customerMemberships.map((mem) => (
                  <tr key={mem.id} className="hover:bg-gray-50/75">
                    <td className="py-3.5 px-4 font-medium text-gray-900">
                      {mem.customer?.first_name || "Customer"} {mem.customer?.last_name || ""}
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-brand-700">
                      {mem.plan?.name || "VIP Plan"}
                    </td>
                    <td className="py-3.5 px-4 text-gray-600">
                      {new Date(mem.end_date).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4 text-center font-bold text-gray-900">
                      {mem.free_services_remaining}
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <span className="px-2.5 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold">
                        {mem.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Plan Modal */}
      {isAddPlanOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-start sm:items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl my-8 sm:my-0">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <h3 className="font-bold text-gray-900 text-lg">Create Membership Plan</h3>
              <button onClick={() => setIsAddPlanOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreatePlan} className="space-y-3 text-sm">
              <div>
                <label className="font-medium text-gray-700">Plan Name *</label>
                <input
                  type="text"
                  required
                  value={newPlan.name}
                  onChange={(e) => setNewPlan({ ...newPlan, name: e.target.value })}
                  placeholder="e.g. Gold VIP Membership"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                />
              </div>

              <div>
                <label className="font-medium text-gray-700">Description</label>
                <textarea
                  rows={2}
                  value={newPlan.description}
                  onChange={(e) => setNewPlan({ ...newPlan, description: e.target.value })}
                  placeholder="e.g. Unlimited 15% discount on haircuts and styling"
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
                    value={newPlan.price}
                    onChange={(e) => setNewPlan({ ...newPlan, price: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  />
                </div>
                <div>
                  <label className="font-medium text-gray-700">Duration (Months)</label>
                  <input
                    type="number"
                    min="1"
                    max="36"
                    value={newPlan.duration_months}
                    onChange={(e) => setNewPlan({ ...newPlan, duration_months: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-medium text-gray-700">Service Discount (%)</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={newPlan.discount_percentage}
                    onChange={(e) => setNewPlan({ ...newPlan, discount_percentage: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  />
                </div>
                <div>
                  <label className="font-medium text-gray-700">Free Sessions Count</label>
                  <input
                    type="number"
                    min="0"
                    value={newPlan.free_services_count}
                    onChange={(e) => setNewPlan({ ...newPlan, free_services_count: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  />
                </div>
              </div>

              <div className="pt-3 flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setIsAddPlanOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700"
                >
                  Create Plan
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Enroll Modal */}
      {isEnrollOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-start sm:items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl my-8 sm:my-0">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <h3 className="font-bold text-gray-900 text-lg">Enroll Customer</h3>
              <button onClick={() => setIsEnrollOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleEnroll} className="space-y-3 text-sm">
              <div>
                <label className="font-medium text-gray-700">Select Customer *</label>
                <select
                  required
                  value={enrollForm.customer_id}
                  onChange={(e) => setEnrollForm({ ...enrollForm, customer_id: e.target.value })}
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
                <label className="font-medium text-gray-700">Select Plan *</label>
                <select
                  required
                  value={enrollForm.plan_id}
                  onChange={(e) => setEnrollForm({ ...enrollForm, plan_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                >
                  <option value="">Choose plan tier...</option>
                  {plans.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} — {formatPrice(p.price)} ({p.duration_months} mo)
                    </option>
                  ))}
                </select>
              </div>

              <div className="pt-3 flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setIsEnrollOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700"
                >
                  Enroll Customer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
