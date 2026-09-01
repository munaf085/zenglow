"use client";

import { useEffect, useState } from "react";
import { Plus, Loader2, Package } from "lucide-react";
import { api } from "@/lib/api";
import { formatCurrency, cn } from "@/lib/utils";
import { toast } from "sonner";
import type { SubscriptionPlan } from "@zenglow/types";

const TIER_COLORS: Record<string, string> = {
  FREE:         "bg-gray-100 text-gray-700",
  STARTER:      "bg-blue-100 text-blue-700",
  PROFESSIONAL: "bg-purple-100 text-purple-700",
  ENTERPRISE:   "bg-yellow-100 text-yellow-700",
};

export default function AdminSettingsPage() {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    tier: "STARTER",
    name: "",
    monthly_price: "",
    yearly_price: "",
    max_branches: "1",
    max_staff: "5",
    max_services: "20",
    max_bookings_per_month: "200",
    description: "",
  });

  const load = async () => {
    setIsLoading(true);
    try {
      const res = await api.get<SubscriptionPlan[]>("/admin/subscription-plans");
      setPlans(res);
    } catch { setPlans([]); }
    finally { setIsLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.post("/admin/subscription-plans", {
        tier: form.tier,
        name: form.name,
        monthly_price: parseFloat(form.monthly_price),
        yearly_price: parseFloat(form.yearly_price),
        max_branches: parseInt(form.max_branches),
        max_staff: parseInt(form.max_staff),
        max_services: parseInt(form.max_services),
        max_bookings_per_month: parseInt(form.max_bookings_per_month),
        description: form.description || undefined,
      });
      toast.success("Plan created");
      setShowForm(false);
      load();
    } catch (err: any) {
      toast.error(err.message ?? "Failed to create plan");
    } finally {
      setCreating(false);
    }
  };

  const fieldCls = "w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500";

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-500 text-sm mt-1">Platform configuration</p>
        </div>
      </div>

      {/* Subscription Plans */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Subscription Plans</h2>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Plan
          </button>
        </div>

        {/* Create plan form */}
        {showForm && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 mb-4">
            <h3 className="font-semibold text-gray-900 mb-4">Create New Plan</h3>
            <form onSubmit={handleCreate} className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Tier *</label>
                <select
                  value={form.tier}
                  onChange={e => setForm(f => ({ ...f, tier: e.target.value }))}
                  className={cn(fieldCls, "bg-white")}
                >
                  {["FREE","STARTER","PROFESSIONAL","ENTERPRISE"].map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Name *</label>
                <input
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  required
                  className={fieldCls}
                  placeholder="e.g. Professional"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Monthly Price (₹) *</label>
                <input
                  type="number"
                  value={form.monthly_price}
                  onChange={e => setForm(f => ({ ...f, monthly_price: e.target.value }))}
                  required
                  min="0"
                  step="0.01"
                  className={fieldCls}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Yearly Price (₹) *</label>
                <input
                  type="number"
                  value={form.yearly_price}
                  onChange={e => setForm(f => ({ ...f, yearly_price: e.target.value }))}
                  required
                  min="0"
                  step="0.01"
                  className={fieldCls}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Max Branches</label>
                <input
                  type="number"
                  value={form.max_branches}
                  onChange={e => setForm(f => ({ ...f, max_branches: e.target.value }))}
                  min="1"
                  className={fieldCls}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Max Staff</label>
                <input
                  type="number"
                  value={form.max_staff}
                  onChange={e => setForm(f => ({ ...f, max_staff: e.target.value }))}
                  min="1"
                  className={fieldCls}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Max Services</label>
                <input
                  type="number"
                  value={form.max_services}
                  onChange={e => setForm(f => ({ ...f, max_services: e.target.value }))}
                  min="1"
                  className={fieldCls}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Max Bookings/Month</label>
                <input
                  type="number"
                  value={form.max_bookings_per_month}
                  onChange={e => setForm(f => ({ ...f, max_bookings_per_month: e.target.value }))}
                  min="1"
                  className={fieldCls}
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
                <textarea
                  value={form.description}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                  rows={2}
                  className={cn(fieldCls, "resize-none")}
                />
              </div>
              <div className="sm:col-span-2 flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-semibold rounded-lg transition-colors"
                >
                  {creating && <Loader2 className="w-4 h-4 animate-spin" />}
                  Create plan
                </button>
              </div>
            </form>
          </div>
        )}

        {isLoading ? (
          <div className="flex justify-center py-10">
            <Loader2 className="w-6 h-6 animate-spin text-brand-600" />
          </div>
        ) : plans.length === 0 ? (
          <div className="text-center py-10 bg-white rounded-xl border border-gray-200">
            <Package className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">No subscription plans yet</p>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {plans.map((plan) => (
              <div key={plan.id} className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className={cn(
                    "text-xs font-semibold px-2 py-0.5 rounded-full",
                    TIER_COLORS[plan.tier] ?? "bg-gray-100 text-gray-700"
                  )}>
                    {plan.tier}
                  </span>
                  {plan.is_active && (
                    <span className="w-2 h-2 bg-green-500 rounded-full" title="Active" />
                  )}
                </div>
                <h3 className="font-bold text-gray-900 mb-1">{plan.name}</h3>
                {plan.description && (
                  <p className="text-xs text-gray-500 mb-3 line-clamp-2">{plan.description}</p>
                )}
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Monthly</span>
                    <span className="font-semibold">{formatCurrency(plan.monthly_price)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Yearly</span>
                    <span className="font-semibold">{formatCurrency(plan.yearly_price)}</span>
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-gray-100 space-y-1 text-xs text-gray-500">
                  <p>Up to {plan.max_branches} branch{plan.max_branches !== 1 ? "es" : ""}</p>
                  <p>Up to {plan.max_staff} staff</p>
                  <p>Up to {plan.max_services} services</p>
                  <p>{plan.max_bookings_per_month} bookings/month</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
