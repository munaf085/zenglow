"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/components/providers/AuthProvider";
import { api } from "@/lib/api";
import { toast } from "sonner";
import {
  CheckCircle2, Circle, ArrowRight, Copy, ExternalLink, Sparkles,
  Building2, Users, Scissors, Clock, CreditCard, Share2,
} from "lucide-react";
import { cn } from "@/lib/utils";

export function GoLiveChecklist() {
  const { business } = useAuth();
  const [stats, setStats] = useState({
    staffCount: 0,
    serviceCount: 0,
    hasWorkingHours: false,
    hasSubscription: false,
  });
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (!business?.id) return;
    loadChecklistData();
  }, [business?.id]);

  const loadChecklistData = async () => {
    try {
      setLoading(true);
      const [staffRes, svcRes, subRes] = await Promise.allSettled([
        api.get<any[]>(`/businesses/${business?.id}/staff`),
        api.get<any>(`/businesses/${business?.id}/services`),
        api.get<any>(`/subscriptions/businesses/${business?.id}/current`),
      ]);

      const staff = staffRes.status === "fulfilled" ? staffRes.value ?? [] : [];
      const svcs = svcRes.status === "fulfilled" ? (svcRes.value?.items ?? svcRes.value ?? []) : [];
      const sub = subRes.status === "fulfilled" ? subRes.value : null;

      setStats({
        staffCount: staff.length,
        serviceCount: svcs.length,
        hasWorkingHours: staff.length > 0, // staff schedule initialized
        hasSubscription: Boolean(sub && sub.status === "ACTIVE"),
      });
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const bookingUrl = typeof window !== "undefined"
    ? `${window.location.origin.replace("3001", "3000")}/business/${business?.slug || ""}`
    : `https://zenglow.app/business/${business?.slug || ""}`;

  const copyBookingLink = () => {
    navigator.clipboard.writeText(bookingUrl);
    toast.success("Direct booking link copied to clipboard!");
  };

  const steps = [
    {
      id: "profile",
      title: "Complete business profile",
      description: "Business name, category, and address details",
      completed: Boolean(business?.name && business?.category),
      href: "/dashboard/settings",
      icon: Building2,
    },
    {
      id: "staff",
      title: "Add your team & staff",
      description: "At least 1 team member to accept bookings",
      completed: stats.staffCount > 0,
      href: "/dashboard/staff",
      icon: Users,
    },
    {
      id: "services",
      title: "Add your services & pricing",
      description: "Haircuts, styling, spa, massages, etc.",
      completed: stats.serviceCount > 0,
      href: "/dashboard/services",
      icon: Scissors,
    },
    {
      id: "schedule",
      title: "Set operating hours",
      description: "Define weekly salon opening & shift timings",
      completed: stats.hasWorkingHours,
      href: "/dashboard/schedule",
      icon: Clock,
    },
    {
      id: "subscription",
      title: "Activate subscription plan",
      description: "Select Starter, Pro or Enterprise for digital booking",
      completed: stats.hasSubscription || Boolean(business?.subscription_plan_id),
      href: "/dashboard/settings/subscription",
      icon: CreditCard,
    },
  ];

  const completedCount = steps.filter((s) => s.completed).length;
  const progressPercent = Math.round((completedCount / steps.length) * 100);

  if (dismissed || (completedCount === steps.length && !loading)) {
    return null; // hide checklist once 100% complete
  }

  return (
    <div className="bg-gradient-to-br from-brand-900 to-indigo-950 rounded-2xl p-6 text-white shadow-xl space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-brand-500/20 text-brand-300 rounded-full text-xs font-bold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" /> Go-Live Activation Checklist
          </div>
          <h2 className="text-xl font-extrabold text-white">
            Get {business?.name || "your salon"} ready for customer bookings
          </h2>
          <p className="text-xs text-white/70">
            Complete these 5 quick steps to start taking online appointments and POS sales.
          </p>
        </div>

        <div className="text-right sm:w-48 space-y-1">
          <div className="flex justify-between text-xs font-bold">
            <span className="text-white/80">Progress</span>
            <span className="text-brand-300">{progressPercent}%</span>
          </div>
          <div className="w-full h-2 bg-white/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-brand-400 to-emerald-400 rounded-full transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Step items */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {steps.map((step) => {
          const Icon = step.icon;
          return (
            <Link
              key={step.id}
              href={step.href}
              className={cn(
                "p-3.5 rounded-xl border transition-all flex items-start justify-between gap-3 group",
                step.completed
                  ? "bg-white/5 border-white/10 hover:bg-white/10"
                  : "bg-white/10 border-brand-400/40 hover:bg-white/15 hover:border-brand-300"
              )}
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5">
                  {step.completed ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  ) : (
                    <Circle className="w-5 h-5 text-brand-300" />
                  )}
                </div>
                <div className="space-y-0.5">
                  <p className={cn("text-xs font-bold", step.completed ? "text-white/70 line-through" : "text-white")}>
                    {step.title}
                  </p>
                  <p className="text-[11px] text-white/60 line-clamp-1">{step.description}</p>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-white/40 group-hover:text-white transition-colors mt-1" />
            </Link>
          );
        })}

        {/* Direct Booking Link Sharing Card */}
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-400/30 flex flex-col justify-between space-y-2">
          <div className="flex items-center gap-2">
            <Share2 className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-bold text-emerald-200">Your Booking Website</span>
          </div>
          <p className="text-[11px] text-white/70 truncate">{bookingUrl}</p>
          <button
            onClick={copyBookingLink}
            className="w-full py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition-colors"
          >
            <Copy className="w-3 h-3" /> Copy Booking URL
          </button>
        </div>
      </div>
    </div>
  );
}
