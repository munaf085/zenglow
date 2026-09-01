"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { api } from "@/lib/api";
import { toast } from "sonner";
import {
  CreditCard, CheckCircle2, ShieldCheck, Sparkles, Zap,
  Check, ArrowRight, Building2, Users, Scissors, Calendar,
  Receipt, AlertCircle, RefreshCw,
} from "lucide-react";
import { cn, formatPrice } from "@/lib/utils";

// Load Razorpay checkout script dynamically
function loadRazorpayScript(): Promise<boolean> {
  return new Promise((resolve) => {
    if (typeof window === "undefined") return resolve(false);
    if ((window as any).Razorpay) return resolve(true);

    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

export default function SubscriptionBillingPage() {
  const { user, business, refreshUser } = useAuth();
  const [plans, setPlans] = useState<any[]>([]);
  const [currentSubscription, setCurrentSubscription] = useState<any | null>(null);
  const [billingCycle, setBillingCycle] = useState<"MONTHLY" | "YEARLY">("MONTHLY");
  const [loading, setLoading] = useState(true);
  const [upgradingTier, setUpgradingTier] = useState<string | null>(null);

  useEffect(() => {
    if (!business?.id) return;
    loadData();
  }, [business?.id]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [plansRes, subRes] = await Promise.allSettled([
        api.get<any[]>("/subscriptions/plans"),
        api.get<any>(`/subscriptions/businesses/${business?.id}/current`),
      ]);

      if (plansRes.status === "fulfilled") setPlans(plansRes.value ?? []);
      if (subRes.status === "fulfilled") setCurrentSubscription(subRes.value);
    } catch (e) {
      toast.error("Failed to load subscription plans");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPlan = async (plan: any) => {
    if (!business?.id || !user) return;
    try {
      setUpgradingTier(plan.tier);
      toast.info(`Preparing checkout for ${plan.name}...`);

      // 1. Create order on backend
      const orderData = await api.post<any>("/subscriptions/create-order", {
        business_id: business.id,
        plan_id: plan.id,
        billing_cycle: billingCycle,
      });

      // 2. Load Razorpay script
      const scriptLoaded = await loadRazorpayScript();
      if (!scriptLoaded && process.env.NODE_ENV === "production") {
        toast.error("Razorpay SDK failed to load. Please check your internet connection.");
        setUpgradingTier(null);
        return;
      }

      // 3. If in mock / test environment or standard checkout
      const rzpKey = orderData.key_id;
      if (rzpKey.startsWith("rzp_test_mock") || !(window as any).Razorpay) {
        // Mock verification
        const mockVerify = await api.post<any>("/subscriptions/verify", {
          business_id: business.id,
          plan_id: plan.id,
          billing_cycle: billingCycle,
          provider_payment_id: "mock_pay_" + Date.now(),
          provider_order_id: orderData.provider_order_id,
          provider_signature: "mock_sig_upgrade",
        });

        toast.success(`Upgraded to ${plan.name}!`);
        setCurrentSubscription(mockVerify);
        if (refreshUser) await refreshUser();
        setUpgradingTier(null);
        return;
      }

      // 4. Open Razorpay Checkout Modal
      const options = {
        key: rzpKey,
        amount: Math.round(orderData.amount * 100),
        currency: orderData.currency,
        name: "Zenglow Platform",
        description: `${plan.name} (${billingCycle.toLowerCase()} subscription)`,
        order_id: orderData.provider_order_id,
        prefill: {
          name: `${user.first_name} ${user.last_name || ""}`.trim(),
          email: user.email,
          contact: user.phone || "",
        },
        theme: {
          color: "#7c3aed",
        },
        handler: async function (response: any) {
          try {
            const verifyRes = await api.post<any>("/subscriptions/verify", {
              business_id: business.id,
              plan_id: plan.id,
              billing_cycle: billingCycle,
              provider_payment_id: response.razorpay_payment_id,
              provider_order_id: response.razorpay_order_id,
              provider_signature: response.razorpay_signature,
            });

            toast.success(`🎉 You're now on the ${plan.name}!`);
            setCurrentSubscription(verifyRes);
            if (refreshUser) await refreshUser();
          } catch (err: any) {
            toast.error(err?.message || "Payment verification failed");
          } finally {
            setUpgradingTier(null);
          }
        },
        modal: {
          ondismiss: function () {
            setUpgradingTier(null);
          },
        },
      };

      const rzpInstance = new (window as any).Razorpay(options);
      rzpInstance.open();
    } catch (e: any) {
      toast.error(e?.message || "Failed to initiate checkout");
      setUpgradingTier(null);
    }
  };

  const currentTier = currentSubscription?.plan?.tier || "STARTER";

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto space-y-2">
        <span className="px-3.5 py-1 bg-brand-100 text-brand-800 rounded-full text-xs font-bold uppercase tracking-wider">
          Plans & Pricing
        </span>
        <h1 className="text-3xl font-extrabold text-gray-900">
          Grow your salon with the right plan
        </h1>
        <p className="text-sm text-gray-500">
          Transparent pricing. No hidden fees. Cancel or switch anytime.
        </p>

        {/* Monthly vs Annual Toggle */}
        <div className="pt-4 flex items-center justify-center gap-3">
          <span className={cn("text-sm font-medium", billingCycle === "MONTHLY" ? "text-gray-900 font-bold" : "text-gray-500")}>
            Monthly
          </span>
          <button
            onClick={() => setBillingCycle(billingCycle === "MONTHLY" ? "YEARLY" : "MONTHLY")}
            className="w-14 h-7 bg-brand-600 rounded-full p-1 transition-colors relative"
          >
            <div
              className={cn(
                "w-5 h-5 bg-white rounded-full transition-transform",
                billingCycle === "YEARLY" ? "translate-x-7" : "translate-x-0"
              )}
            />
          </button>
          <span className={cn("text-sm font-medium flex items-center gap-1.5", billingCycle === "YEARLY" ? "text-gray-900 font-bold" : "text-gray-500")}>
            Annual <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded-full text-xs font-bold">2 Months Free</span>
          </span>
        </div>
      </div>

      {/* Current Active Plan Banner */}
      {currentSubscription && (
        <div className="bg-gradient-to-r from-brand-600 to-indigo-700 rounded-2xl p-6 text-white shadow-lg flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="space-y-1 text-center md:text-left">
            <span className="px-2.5 py-0.5 bg-white/20 rounded text-xs font-bold uppercase">Current Plan</span>
            <h2 className="text-2xl font-bold">{currentSubscription.plan?.name || "Active Subscription"}</h2>
            <p className="text-white/80 text-xs">
              Billing cycle: <strong>{currentSubscription.billing_cycle}</strong> · Valid until{" "}
              <strong>{new Date(currentSubscription.end_date).toLocaleDateString()}</strong>
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-4 py-2 bg-white text-brand-700 rounded-xl font-bold text-sm shadow">
              Status: {currentSubscription.status}
            </span>
          </div>
        </div>
      )}

      {/* Pricing Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => {
          const isCurrent = currentTier === plan.tier;
          const isPopular = plan.tier === "PROFESSIONAL";
          const price = billingCycle === "YEARLY" ? plan.yearly_price : plan.monthly_price;

          return (
            <div
              key={plan.id}
              className={cn(
                "bg-white rounded-2xl p-6 border shadow-sm flex flex-col justify-between relative transition-all",
                isPopular ? "border-brand-500 ring-2 ring-brand-500 shadow-md" : "border-gray-200",
                isCurrent && "bg-brand-50/20"
              )}
            >
              {isPopular && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-3.5 py-1 bg-brand-600 text-white rounded-full text-xs font-extrabold uppercase tracking-wider shadow">
                  Most Popular
                </div>
              )}

              <div className="space-y-4">
                <div className="space-y-1">
                  <h3 className="font-bold text-gray-900 text-lg">{plan.name}</h3>
                  <p className="text-xs text-gray-500 min-h-[32px]">{plan.description}</p>
                </div>

                <div className="pt-2">
                  <span className="text-3xl font-extrabold text-gray-900">{formatPrice(price)}</span>
                  <span className="text-xs text-gray-500 font-medium">
                    /{billingCycle === "YEARLY" ? "year" : "month"}
                  </span>
                </div>

                {/* Features List */}
                <div className="space-y-2.5 pt-4 border-t border-gray-100 text-sm text-gray-700">
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                    <span>Up to <strong>{plan.max_staff}</strong> staff accounts</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                    <span>Up to <strong>{plan.max_branches}</strong> salon location(s)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                    <span>Up to <strong>{plan.max_services}</strong> service catalog items</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                    <span>Up to <strong>{plan.max_bookings_per_month}</strong> bookings/month</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                    <span>POS Terminal, Cart & Invoices</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                    <span>SMS & WhatsApp booking reminders</span>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-6">
                {isCurrent ? (
                  <button
                    disabled
                    className="w-full py-2.5 bg-gray-100 text-gray-600 rounded-xl font-bold text-sm cursor-default"
                  >
                    Current Active Plan
                  </button>
                ) : (
                  <button
                    onClick={() => handleSelectPlan(plan)}
                    disabled={upgradingTier === plan.tier}
                    className={cn(
                      "w-full py-2.5 rounded-xl font-bold text-sm transition-all shadow flex items-center justify-center gap-2",
                      isPopular
                        ? "bg-brand-600 text-white hover:bg-brand-700"
                        : "bg-gray-900 text-white hover:bg-black"
                    )}
                  >
                    {upgradingTier === plan.tier ? "Opening Checkout..." : "Upgrade Now"}
                    <ArrowRight className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Trust & Guarantee */}
      <div className="bg-gray-50 rounded-2xl p-6 border border-gray-200 grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
        <div className="space-y-1">
          <ShieldCheck className="w-6 h-6 text-brand-600 mx-auto" />
          <h4 className="font-bold text-gray-900 text-sm">Secure Razorpay Payments</h4>
          <p className="text-xs text-gray-500">256-bit encrypted card, UPI, and net banking checkout</p>
        </div>
        <div className="space-y-1">
          <RefreshCw className="w-6 h-6 text-brand-600 mx-auto" />
          <h4 className="font-bold text-gray-900 text-sm">Switch Anytime</h4>
          <p className="text-xs text-gray-500">Upgrade or downgrade as your salon team expands</p>
        </div>
        <div className="space-y-1">
          <Receipt className="w-6 h-6 text-brand-600 mx-auto" />
          <h4 className="font-bold text-gray-900 text-sm">Automated GST Invoices</h4>
          <p className="text-xs text-gray-500">Instant tax invoices issued for all subscription charges</p>
        </div>
      </div>
    </div>
  );
}
