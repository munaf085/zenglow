"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, Save, User, Lock } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import type { User as UserType } from "@zenglow/types";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { Header } from "@/components/layout/Header";

const profileSchema = z.object({
  first_name: z.string().min(1, "Required").max(100),
  last_name: z.string().min(1, "Required").max(100),
  phone: z.string().optional(),
});

const passwordSchema = z.object({
  current_password: z.string().min(1, "Required"),
  new_password: z.string()
    .min(8, "Minimum 8 characters")
    .regex(/[A-Z]/, "Must include an uppercase letter")
    .regex(/[0-9]/, "Must include a number"),
  confirm_password: z.string(),
}).refine((d) => d.new_password === d.confirm_password, {
  message: "Passwords do not match",
  path: ["confirm_password"],
});

type ProfileForm = z.infer<typeof profileSchema>;
type PasswordForm = z.infer<typeof passwordSchema>;

export default function ProfilePage() {
  const { user, isAuthenticated, isLoading: authLoading, refreshUser } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"profile" | "password">("profile");

  const {
    register: regP,
    handleSubmit: hsP,
    reset: resetP,
    formState: { errors: errP, isSubmitting: savingP },
  } = useForm<ProfileForm>({ resolver: zodResolver(profileSchema) });

  const {
    register: regPw,
    handleSubmit: hsPw,
    reset: resetPw,
    formState: { errors: errPw, isSubmitting: savingPw },
  } = useForm<PasswordForm>({ resolver: zodResolver(passwordSchema) });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login?next=/profile");
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (user) {
      resetP({ first_name: user.first_name, last_name: user.last_name, phone: user.phone ?? "" });
    }
  }, [user, resetP]);

  const onSaveProfile = async (data: ProfileForm) => {
    try {
      await api.patch("/users/me", { ...data, phone: data.phone || undefined });
      await refreshUser();
      toast.success("Profile updated");
    } catch (err: any) {
      toast.error(err.message ?? "Could not update profile");
    }
  };

  const onChangePassword = async (data: PasswordForm) => {
    try {
      await api.post("/auth/change-password", {
        current_password: data.current_password,
        new_password: data.new_password,
      });
      resetPw();
      toast.success("Password changed successfully");
    } catch (err: any) {
      toast.error(err.message ?? "Could not change password");
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="w-7 h-7 animate-spin text-brand-600" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />
      <main className="flex-1 max-w-2xl mx-auto w-full px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>
          <p className="text-gray-500 text-sm mt-1">Manage your account details and security settings</p>
        </div>

        {/* Avatar block */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6 flex items-center gap-4">
          <div className="w-16 h-16 bg-brand-100 rounded-full flex items-center justify-center flex-shrink-0">
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="Avatar" className="w-full h-full rounded-full object-cover" />
            ) : (
              <span className="text-brand-700 font-bold text-xl">
                {user?.first_name?.[0]}{user?.last_name?.[0]}
              </span>
            )}
          </div>
          <div>
            <p className="font-semibold text-gray-900 text-lg">{user?.first_name} {user?.last_name}</p>
            <p className="text-sm text-gray-500">{user?.email}</p>
            {user?.is_verified && (
              <span className="inline-flex items-center gap-1 text-xs text-green-700 bg-green-50 px-2 py-0.5 rounded-full mt-1">
                ✓ Verified
              </span>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-xl w-fit">
          {([
            { key: "profile", label: "Profile", icon: User },
            { key: "password", label: "Password", icon: Lock },
          ] as const).map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
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

        {/* Profile tab */}
        {activeTab === "profile" && (
          <div className="bg-white rounded-2xl border border-gray-200 p-6">
            <h2 className="font-semibold text-gray-900 mb-5">Personal information</h2>
            <form onSubmit={hsP(onSaveProfile)} className="space-y-4" noValidate>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">First name</label>
                  <input
                    {...regP("first_name")}
                    className={cn(
                      "w-full px-3 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500",
                      errP.first_name ? "border-red-400 bg-red-50" : "border-gray-300"
                    )}
                  />
                  {errP.first_name && <p className="mt-1 text-xs text-red-600">{errP.first_name.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Last name</label>
                  <input
                    {...regP("last_name")}
                    className={cn(
                      "w-full px-3 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500",
                      errP.last_name ? "border-red-400 bg-red-50" : "border-gray-300"
                    )}
                  />
                  {errP.last_name && <p className="mt-1 text-xs text-red-600">{errP.last_name.message}</p>}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Email address</label>
                <input
                  type="email"
                  value={user?.email ?? ""}
                  disabled
                  className="w-full px-3 py-2.5 rounded-lg border border-gray-200 bg-gray-50 text-sm text-gray-500 cursor-not-allowed"
                />
                <p className="mt-1 text-xs text-gray-400">Email cannot be changed</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Phone number</label>
                <input
                  {...regP("phone")}
                  type="tel"
                  className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  placeholder="+91 98765 43210"
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={savingP}
                  className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white font-semibold px-6 py-2.5 rounded-lg text-sm transition-colors"
                >
                  {savingP ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  Save changes
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Password tab */}
        {activeTab === "password" && (
          <div className="bg-white rounded-2xl border border-gray-200 p-6">
            <h2 className="font-semibold text-gray-900 mb-1">Change password</h2>
            <p className="text-sm text-gray-500 mb-5">Use a strong password with at least 8 characters, one uppercase letter, and one number.</p>
            <form onSubmit={hsPw(onChangePassword)} className="space-y-4" noValidate>
              {[
                { name: "current_password", label: "Current password", err: errPw.current_password },
                { name: "new_password", label: "New password", err: errPw.new_password },
                { name: "confirm_password", label: "Confirm new password", err: errPw.confirm_password },
              ].map(({ name, label, err }) => (
                <div key={name}>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
                  <input
                    {...regPw(name as any)}
                    type="password"
                    autoComplete={name === "current_password" ? "current-password" : "new-password"}
                    className={cn(
                      "w-full px-3 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500",
                      err ? "border-red-400 bg-red-50" : "border-gray-300"
                    )}
                  />
                  {err && <p className="mt-1 text-xs text-red-600">{err.message}</p>}
                </div>
              ))}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={savingPw}
                  className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white font-semibold px-6 py-2.5 rounded-lg text-sm transition-colors"
                >
                  {savingPw ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                  Update password
                </button>
              </div>
            </form>
          </div>
        )}
      </main>
    </div>
  );
}
