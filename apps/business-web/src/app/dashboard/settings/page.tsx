"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Building2, Clock, MapPin, CreditCard, Bell, Save, Loader2, CheckCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import type { Branch, WorkingHours } from "@zenglow/types";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const businessSchema = z.object({
  name: z.string().min(1, "Required"),
  description: z.string().optional(),
  phone: z.string().optional(),
  email: z.string().email("Invalid email").optional().or(z.literal("")),
  website: z.string().optional(),
  booking_advance_days: z.number({ coerce: true }).int().min(1).max(365),
  cancellation_hours: z.number({ coerce: true }).int().min(0),
  cancellation_policy: z.string().optional(),
  deposit_required: z.boolean(),
  deposit_percentage: z.number({ coerce: true }).min(0).max(100).optional(),
});
type BusinessForm = z.infer<typeof businessSchema>;

type Tab = "general" | "hours" | "booking" | "notifications";

export default function SettingsPage() {
  const { business, refreshUser } = useAuth();
  const [activeTab, setActiveTab] = useState<Tab>("general");
  const [branches, setBranches] = useState<Branch[]>([]);
  const [selectedBranch, setSelectedBranch] = useState<Branch | null>(null);
  const [workingHours, setWorkingHours] = useState<WorkingHours[]>([]);
  const [savingHours, setSavingHours] = useState(false);
  const [hours, setHours] = useState<WorkingHours[]>([]);

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<BusinessForm>({
    resolver: zodResolver(businessSchema),
  });

  // Load business data into form
  useEffect(() => {
    if (!business) return;
    reset({
      name: business.name,
      description: business.description ?? "",
      phone: business.phone ?? "",
      email: business.email ?? "",
      website: business.website ?? "",
      booking_advance_days: business.booking_advance_days,
      cancellation_hours: business.cancellation_hours,
      cancellation_policy: business.cancellation_policy ?? "",
      deposit_required: business.deposit_required,
      deposit_percentage: business.deposit_percentage ?? undefined,
    });
  }, [business, reset]);

  // Load branches
  useEffect(() => {
    if (!business) return;
    api.get<Branch[]>(`/businesses/${business.id}/branches`)
      .then((res) => {
        setBranches(res);
        const primary = res.find(b => b.is_primary) ?? res[0];
        if (primary) setSelectedBranch(primary);
      })
      .catch(() => {});
  }, [business]);

  // Load working hours for selected branch
  useEffect(() => {
    if (!business || !selectedBranch) return;
    api.get<WorkingHours[]>(
      `/businesses/${business.id}/branches/${selectedBranch.id}/working-hours`
    ).then((res) => {
      // Ensure all 7 days exist
      const filled = Array.from({ length: 7 }, (_, i) => {
        const existing = res.find(h => h.day_of_week === i);
        return existing ?? {
          id: `temp-${i}`, entity_type: "branch",
          entity_id: selectedBranch.id, business_id: business.id,
          day_of_week: i, is_open: i < 6,
          open_time: i < 6 ? "09:00" : undefined,
          close_time: i < 6 ? "18:00" : undefined,
        } as WorkingHours;
      });
      setHours(filled);
    }).catch(() => {});
  }, [business, selectedBranch]);

  const onSaveGeneral = async (data: BusinessForm) => {
    if (!business) return;
    try {
      await api.patch(`/businesses/${business.id}`, {
        ...data,
        email: data.email || undefined,
        deposit_percentage: data.deposit_percentage || undefined,
      });
      await refreshUser();
      toast.success("Business details saved");
    } catch (err: any) {
      toast.error(err.message ?? "Failed to save");
    }
  };

  const updateHourField = (
    dayIndex: number,
    field: keyof WorkingHours,
    value: string | boolean
  ) => {
    setHours(prev =>
      prev.map((h, i) => i === dayIndex ? { ...h, [field]: value } : h)
    );
  };

  const saveWorkingHours = async () => {
    if (!business || !selectedBranch) return;
    setSavingHours(true);
    try {
      await api.put(
        `/businesses/${business.id}/branches/${selectedBranch.id}/working-hours`,
        {
          hours: hours.map(h => ({
            day_of_week: h.day_of_week,
            is_open: h.is_open,
            open_time: h.is_open ? h.open_time : null,
            close_time: h.is_open ? h.close_time : null,
            break_start: h.break_start ?? null,
            break_end: h.break_end ?? null,
          })),
        }
      );
      toast.success("Working hours saved");
    } catch (err: any) {
      toast.error(err.message ?? "Failed to save hours");
    } finally {
      setSavingHours(false);
    }
  };

  const TABS: { key: Tab; label: string; icon: React.ElementType }[] = [
    { key: "general",       label: "General",       icon: Building2 },
    { key: "hours",         label: "Opening Hours", icon: Clock },
    { key: "booking",       label: "Booking Rules",  icon: CreditCard },
    { key: "notifications", label: "Notifications", icon: Bell },
  ];

  const inputCls = "w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500";
  const labelCls = "block text-sm font-medium text-gray-700 mb-1.5";

  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-500 text-sm mt-1">Manage your business configuration</p>
        </div>
        <a
          href="/dashboard/settings/subscription"
          className="px-4 py-2 bg-gradient-to-r from-brand-600 to-indigo-600 text-white rounded-xl text-sm font-bold shadow hover:from-brand-700 hover:to-indigo-700 flex items-center gap-2 w-fit"
        >
          <CreditCard className="w-4 h-4" /> Subscription & Plans
        </a>
      </div>

      {/* Tab nav */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl w-fit mb-6 overflow-x-auto">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap",
              activeTab === key
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            )}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* ── General ──────────────────────────────────────────────────────────── */}
      {activeTab === "general" && (
        <form onSubmit={handleSubmit(onSaveGeneral)} className="space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="font-semibold text-gray-900 mb-5">Business Information</h2>
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <label className={labelCls}>Business name *</label>
                <input {...register("name")} className={cn(inputCls, errors.name && "border-red-400")} />
                {errors.name && <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>}
              </div>
              <div className="sm:col-span-2">
                <label className={labelCls}>Description</label>
                <textarea
                  {...register("description")}
                  rows={3}
                  className={cn(inputCls, "resize-none")}
                  placeholder="Tell customers about your business..."
                />
              </div>
              <div>
                <label className={labelCls}>Business phone</label>
                <input {...register("phone")} type="tel" className={inputCls} placeholder="+91 98765 43210" />
              </div>
              <div>
                <label className={labelCls}>Business email</label>
                <input {...register("email")} type="email" className={cn(inputCls, errors.email && "border-red-400")} />
                {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
              </div>
              <div className="sm:col-span-2">
                <label className={labelCls}>Website</label>
                <input {...register("website")} type="url" className={inputCls} placeholder="https://yourbusiness.com" />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white font-semibold px-6 py-2.5 rounded-lg text-sm transition-colors"
          >
            {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Save changes
          </button>
        </form>
      )}

      {/* ── Opening Hours ──────────────────────────────────────────────────── */}
      {activeTab === "hours" && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="font-semibold text-gray-900">Opening Hours</h2>
              {branches.length > 1 && (
                <select
                  value={selectedBranch?.id ?? ""}
                  onChange={e => setSelectedBranch(branches.find(b => b.id === e.target.value) ?? null)}
                  className="mt-2 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  {branches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                </select>
              )}
            </div>
          </div>

          <div className="space-y-3">
            {hours.map((h, i) => (
              <div key={i} className="flex items-center gap-4 p-3 rounded-lg border border-gray-100 hover:bg-gray-50">
                {/* Day toggle */}
                <div className="flex items-center gap-3 w-32 flex-shrink-0">
                  <button
                    type="button"
                    onClick={() => updateHourField(i, "is_open", !h.is_open)}
                    className={cn(
                      "relative w-10 h-5 rounded-full transition-colors flex-shrink-0",
                      h.is_open ? "bg-brand-600" : "bg-gray-300"
                    )}
                    aria-label={h.is_open ? "Close" : "Open"}
                  >
                    <span className={cn(
                      "absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform",
                      h.is_open ? "translate-x-5" : "translate-x-0.5"
                    )} />
                  </button>
                  <span className={cn("text-sm font-medium", h.is_open ? "text-gray-900" : "text-gray-400")}>
                    {DAYS[i]}
                  </span>
                </div>

                {h.is_open ? (
                  <div className="flex items-center gap-2 flex-1 flex-wrap">
                    <div className="flex items-center gap-1">
                      <span className="text-xs text-gray-500">Open</span>
                      <input
                        type="time"
                        value={h.open_time ?? "09:00"}
                        onChange={e => updateHourField(i, "open_time", e.target.value)}
                        className="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"
                      />
                    </div>
                    <span className="text-gray-400 text-sm">–</span>
                    <div className="flex items-center gap-1">
                      <span className="text-xs text-gray-500">Close</span>
                      <input
                        type="time"
                        value={h.close_time ?? "18:00"}
                        onChange={e => updateHourField(i, "close_time", e.target.value)}
                        className="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"
                      />
                    </div>
                    <div className="flex items-center gap-1 ml-2">
                      <span className="text-xs text-gray-400">Break</span>
                      <input
                        type="time"
                        value={h.break_start ?? ""}
                        onChange={e => updateHourField(i, "break_start", e.target.value)}
                        className="px-2 py-1 border border-gray-200 rounded text-xs text-gray-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                        placeholder="—"
                      />
                      <span className="text-gray-300 text-xs">–</span>
                      <input
                        type="time"
                        value={h.break_end ?? ""}
                        onChange={e => updateHourField(i, "break_end", e.target.value)}
                        className="px-2 py-1 border border-gray-200 rounded text-xs text-gray-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                        placeholder="—"
                      />
                    </div>
                  </div>
                ) : (
                  <span className="text-sm text-gray-400 flex-1">Closed</span>
                )}
              </div>
            ))}
          </div>

          <div className="mt-5">
            <button
              onClick={saveWorkingHours}
              disabled={savingHours}
              className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white font-semibold px-6 py-2.5 rounded-lg text-sm transition-colors"
            >
              {savingHours ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              Save hours
            </button>
          </div>
        </div>
      )}

      {/* ── Booking Rules ─────────────────────────────────────────────────── */}
      {activeTab === "booking" && (
        <form onSubmit={handleSubmit(onSaveGeneral)} className="space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="font-semibold text-gray-900 mb-5">Booking Configuration</h2>
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>Advance booking (days)</label>
                <input
                  {...register("booking_advance_days")}
                  type="number" min="1" max="365"
                  className={cn(inputCls, errors.booking_advance_days && "border-red-400")}
                />
                <p className="mt-1 text-xs text-gray-400">How far ahead customers can book</p>
              </div>
              <div>
                <label className={labelCls}>Free cancellation window (hours)</label>
                <input
                  {...register("cancellation_hours")}
                  type="number" min="0"
                  className={cn(inputCls, errors.cancellation_hours && "border-red-400")}
                />
                <p className="mt-1 text-xs text-gray-400">Hours before appointment for free cancellation</p>
              </div>
              <div className="sm:col-span-2">
                <label className={labelCls}>Cancellation policy</label>
                <textarea
                  {...register("cancellation_policy")}
                  rows={3}
                  className={cn(inputCls, "resize-none")}
                  placeholder="Describe your cancellation terms..."
                />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="font-semibold text-gray-900 mb-5">Deposit Settings</h2>
            <div className="space-y-4">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  {...register("deposit_required")}
                  type="checkbox"
                  className="w-4 h-4 rounded text-brand-600 border-gray-300"
                />
                <span className="text-sm font-medium text-gray-700">Require deposit to confirm booking</span>
              </label>
              <div>
                <label className={labelCls}>Deposit percentage (%)</label>
                <input
                  {...register("deposit_percentage")}
                  type="number" min="0" max="100" step="1"
                  className={cn(inputCls, "max-w-xs")}
                  placeholder="e.g. 20"
                />
                <p className="mt-1 text-xs text-gray-400">Percentage of total charged as deposit</p>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white font-semibold px-6 py-2.5 rounded-lg text-sm transition-colors"
          >
            {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Save settings
          </button>
        </form>
      )}

      {/* ── Notifications ─────────────────────────────────────────────────── */}
      {activeTab === "notifications" && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-semibold text-gray-900 mb-2">Notification Preferences</h2>
          <p className="text-sm text-gray-500 mb-6">
            Configure which notifications are sent to customers and staff.
          </p>
          <div className="space-y-4">
            {[
              { label: "Booking confirmation email", sub: "Sent to customer after successful booking", defaultOn: true },
              { label: "24-hour reminder email", sub: "Sent to customer one day before appointment", defaultOn: true },
              { label: "2-hour reminder email", sub: "Sent to customer two hours before appointment", defaultOn: true },
              { label: "Cancellation notification", sub: "Sent when an appointment is cancelled", defaultOn: true },
              { label: "Review request email", sub: "Sent the day after a completed appointment", defaultOn: false },
              { label: "New booking alert (staff)", sub: "Notify assigned staff of new bookings", defaultOn: false },
            ].map(({ label, sub, defaultOn }) => (
              <div key={label} className="flex items-start justify-between gap-4 py-3 border-b border-gray-100 last:border-0">
                <div>
                  <p className="text-sm font-medium text-gray-900">{label}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{sub}</p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {defaultOn && (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  )}
                  <label className="relative w-10 h-5 cursor-pointer">
                    <input
                      type="checkbox"
                      defaultChecked={defaultOn}
                      className="sr-only peer"
                    />
                    <div className="w-10 h-5 bg-gray-300 rounded-full peer-checked:bg-brand-600 transition-colors" />
                    <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-5" />
                  </label>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-5 p-4 bg-blue-50 rounded-lg border border-blue-100">
            <p className="text-xs text-blue-700">
              <strong>Note:</strong> Notification delivery depends on your email/SMS provider configuration in the platform settings. In development mode, all notifications are printed to the server console.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
