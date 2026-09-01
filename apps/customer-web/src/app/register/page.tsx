"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, Eye, EyeOff } from "lucide-react";
import { api, setTokens } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

const schema = z.object({
  first_name: z.string().min(1, "First name is required").max(100),
  last_name: z.string().min(1, "Last name is required").max(100),
  email: z.string().email("Enter a valid email"),
  phone: z.string().optional(),
  password: z.string()
    .min(8, "Minimum 8 characters")
    .regex(/[A-Z]/, "Must include an uppercase letter")
    .regex(/[0-9]/, "Must include a number"),
  confirmPassword: z.string(),
}).refine((d) => d.password === d.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});
type FormData = z.infer<typeof schema>;

export default function RegisterPage() {
  const { refreshUser } = useAuth();
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    try {
      await api.post("/auth/register", {
        email: data.email,
        password: data.password,
        first_name: data.first_name,
        last_name: data.last_name,
        phone: data.phone || undefined,
      });
      // Auto-login after register
      const tokens = await api.post<{ access_token: string; refresh_token: string }>("/auth/login", {
        email: data.email,
        password: data.password,
      });
      setTokens(tokens.access_token, tokens.refresh_token);
      await refreshUser();
      toast.success("Account created! Welcome to Zenglow.");
      router.push("/bookings");
    } catch (err: any) {
      toast.error(err.message ?? "Registration failed");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 mb-6">
            <div className="w-9 h-9 bg-brand-600 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold">Z</span>
            </div>
            <span className="text-2xl font-bold text-gray-900">Zenglow</span>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Create your account</h1>
          <p className="text-gray-500 text-sm mt-1">Book at top salons and spas near you</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">First name</label>
                <input
                  type="text"
                  autoComplete="given-name"
                  className={cn("w-full px-4 py-3 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500",
                    errors.first_name ? "border-red-400" : "border-gray-300")}
                  {...register("first_name")}
                />
                {errors.first_name && <p className="mt-1 text-xs text-red-600">{errors.first_name.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Last name</label>
                <input
                  type="text"
                  autoComplete="family-name"
                  className={cn("w-full px-4 py-3 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500",
                    errors.last_name ? "border-red-400" : "border-gray-300")}
                  {...register("last_name")}
                />
                {errors.last_name && <p className="mt-1 text-xs text-red-600">{errors.last_name.message}</p>}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Email address</label>
              <input
                type="email"
                autoComplete="email"
                className={cn("w-full px-4 py-3 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500",
                  errors.email ? "border-red-400" : "border-gray-300")}
                placeholder="you@example.com"
                {...register("email")}
              />
              {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Phone (optional)</label>
              <input
                type="tel"
                autoComplete="tel"
                className="w-full px-4 py-3 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="+91 98765 43210"
                {...register("phone")}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
                  className={cn("w-full px-4 py-3 pr-11 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500",
                    errors.password ? "border-red-400" : "border-gray-300")}
                  {...register("password")}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Confirm password</label>
              <input
                type="password"
                autoComplete="new-password"
                className={cn("w-full px-4 py-3 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500",
                  errors.confirmPassword ? "border-red-400" : "border-gray-300")}
                {...register("confirmPassword")}
              />
              {errors.confirmPassword && <p className="mt-1 text-xs text-red-600">{errors.confirmPassword.message}</p>}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white font-semibold py-3 rounded-lg transition-colors mt-2"
            >
              {isSubmitting ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating account...</> : "Create account"}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-500">
            Already have an account?{" "}
            <Link href="/login" className="text-brand-600 hover:text-brand-700 font-medium">Sign in</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
