"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, Check } from "lucide-react";
import { api, setTokens } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

type Step = 1 | 2 | 3;

const accountSchema = z.object({
  first_name: z.string().min(1, "Required"),
  last_name: z.string().min(1, "Required"),
  email: z.string().email("Valid email required"),
  password: z.string().min(8).regex(/[A-Z]/, "Uppercase required").regex(/[0-9]/, "Number required"),
});

const businessSchema = z.object({
  name: z.string().min(1, "Business name required"),
  category: z.string().min(1, "Required"),
  phone: z.string().optional(),
  email: z.string().email().optional().or(z.literal("")),
  description: z.string().optional(),
});

const branchSchema = z.object({
  branch_name: z.string().min(1, "Branch name required"),
  city: z.string().min(1, "City required"),
  address_line1: z.string().optional(),
  state: z.string().optional(),
  postal_code: z.string().optional(),
});

const CATEGORIES = ["SALON", "SPA", "BARBER", "BEAUTY", "WELLNESS", "NAIL_STUDIO", "MASSAGE", "OTHER"];

type AccountValues = z.infer<typeof accountSchema>;
type BusinessValues = z.infer<typeof businessSchema>;
type BranchValues = z.infer<typeof branchSchema>;

export default function OnboardingPage() {
  const router = useRouter();
  const { refreshUser } = useAuth();
  const [step, setStep] = useState<Step>(1);
  const [accountData, setAccountData] = useState<AccountValues | null>(null);
  const [bizData, setBizData] = useState<BusinessValues | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { register: reg1, handleSubmit: hs1, formState: { errors: e1 } } = useForm<AccountValues>({ resolver: zodResolver(accountSchema) });
  const { register: reg2, handleSubmit: hs2, formState: { errors: e2 } } = useForm<BusinessValues>({ resolver: zodResolver(businessSchema) });
  const { register: reg3, handleSubmit: hs3, formState: { errors: e3 } } = useForm<BranchValues>({ resolver: zodResolver(branchSchema), defaultValues: { branch_name: "Main Branch" } });

  const onStep1 = (d: AccountValues) => { setAccountData(d); setStep(2); };
  const onStep2 = (d: BusinessValues) => { setBizData(d); setStep(3); };

  const onStep3 = async (branchD: BranchValues) => {
    if (!accountData || !bizData) return;
    setIsSubmitting(true);
    try {
      // 1. Register account
      await api.post("/auth/register", { email: accountData.email, password: accountData.password, first_name: accountData.first_name, last_name: accountData.last_name });
      // 2. Login
      const tokens = await api.post<{ access_token: string; refresh_token: string }>("/auth/login", { email: accountData.email, password: accountData.password });
      setTokens(tokens.access_token, tokens.refresh_token);
      // 3. Create business
      await api.post("/businesses", {
        name: bizData.name,
        category: bizData.category,
        phone: bizData.phone,
        email: bizData.email || undefined,
        description: bizData.description,
        branch: { name: branchD.branch_name, city: branchD.city, address_line1: branchD.address_line1, state: branchD.state, postal_code: branchD.postal_code, is_primary: true },
      });
      await refreshUser();
      toast.success("Business created! Welcome to Zenglow.");
      router.push("/dashboard");
    } catch (err: any) {
      toast.error(err.message ?? "Setup failed. Please try again.");
    } finally { setIsSubmitting(false); }
  };

  const StepIndicator = () => (
    <div className="flex items-center justify-center gap-2 mb-8">
      {([1, 2, 3] as Step[]).map((s) => (
        <div key={s} className="flex items-center gap-2">
          {s > 1 && <div className={cn("w-8 h-px", step >= s ? "bg-brand-600" : "bg-gray-300")} />}
          <div className={cn("w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors",
            step > s ? "bg-brand-600 text-white" : step === s ? "bg-brand-600 text-white" : "bg-gray-200 text-gray-500"
          )}>
            {step > s ? <Check className="w-4 h-4" /> : s}
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg">
        <div className="text-center mb-6">
          <div className="w-12 h-12 bg-brand-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-white font-bold text-xl">Z</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Get started with Zenglow</h1>
          <p className="text-gray-500 text-sm mt-1">
            {step === 1 ? "Create your account" : step === 2 ? "Tell us about your business" : "Add your location"}
          </p>
        </div>

        <StepIndicator />

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
          {step === 1 && (
            <form onSubmit={hs1(onStep1)} className="space-y-4" noValidate>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">First name</label>
                  <input {...reg1("first_name")} className={cn("w-full px-3 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500", e1.first_name ? "border-red-400" : "border-gray-300")} />
                  {e1.first_name && <p className="mt-1 text-xs text-red-600">{e1.first_name.message as string}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Last name</label>
                  <input {...reg1("last_name")} className={cn("w-full px-3 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500", e1.last_name ? "border-red-400" : "border-gray-300")} />
                  {e1.last_name && <p className="mt-1 text-xs text-red-600">{e1.last_name.message as string}</p>}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input {...reg1("email")} type="email" className={cn("w-full px-3 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500", e1.email ? "border-red-400" : "border-gray-300")} />
                {e1.email && <p className="mt-1 text-xs text-red-600">{e1.email.message as string}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input {...reg1("password")} type="password" className={cn("w-full px-3 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500", e1.password ? "border-red-400" : "border-gray-300")} />
                {e1.password && <p className="mt-1 text-xs text-red-600">{e1.password.message as string}</p>}
              </div>
              <button type="submit" className="w-full bg-brand-600 hover:bg-brand-700 text-white font-semibold py-3 rounded-lg transition-colors mt-2">Continue</button>
            </form>
          )}

          {step === 2 && (
            <form onSubmit={hs2(onStep2)} className="space-y-4" noValidate>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Business name *</label>
                <input {...reg2("name")} className={cn("w-full px-3 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500", e2.name ? "border-red-400" : "border-gray-300")} placeholder="e.g. Glow Studio" />
                {e2.name && <p className="mt-1 text-xs text-red-600">{e2.name.message as string}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                <select {...reg2("category")} className={cn("w-full px-3 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white", e2.category ? "border-red-400" : "border-gray-300")}>
                  <option value="">Select...</option>
                  {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace("_", " ")}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Business phone</label>
                <input {...reg2("phone")} type="tel" className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea {...reg2("description")} rows={3} className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" placeholder="Tell customers about your business..." />
              </div>
              <div className="flex gap-3">
                <button type="button" onClick={() => setStep(1)} className="flex-1 py-3 rounded-lg border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50">Back</button>
                <button type="submit" className="flex-1 bg-brand-600 hover:bg-brand-700 text-white font-semibold py-3 rounded-lg transition-colors">Continue</button>
              </div>
            </form>
          )}

          {step === 3 && (
            <form onSubmit={hs3(onStep3)} className="space-y-4" noValidate>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Branch name *</label>
                <input {...reg3("branch_name")} className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
                <input {...reg3("address_line1")} className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" placeholder="Street address" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">City *</label>
                  <input {...reg3("city")} className={cn("w-full px-3 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500", e3.city ? "border-red-400" : "border-gray-300")} />
                  {e3.city && <p className="mt-1 text-xs text-red-600">{e3.city.message as string}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
                  <input {...reg3("state")} className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
                </div>
              </div>
              <div className="flex gap-3">
                <button type="button" onClick={() => setStep(2)} className="flex-1 py-3 rounded-lg border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50">Back</button>
                <button type="submit" disabled={isSubmitting} className="flex-1 flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white font-semibold py-3 rounded-lg transition-colors">
                  {isSubmitting ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating...</> : "Launch my business"}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
