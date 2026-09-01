"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Calendar, Clock, ChevronRight, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import type { Appointment } from "@zenglow/types";
import { formatDate, formatTime, formatCurrency, cn } from "@/lib/utils";
import { Header } from "@/components/layout/Header";

const STATUS_STYLES: Record<string, string> = {
  CONFIRMED: "bg-green-100 text-green-800",
  PENDING: "bg-yellow-100 text-yellow-800",
  COMPLETED: "bg-gray-100 text-gray-600",
  CANCELLED: "bg-red-100 text-red-700",
  IN_PROGRESS: "bg-blue-100 text-blue-800",
  NO_SHOW: "bg-orange-100 text-orange-700",
};

export default function BookingsPage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [tab, setTab] = useState<"upcoming" | "past">("upcoming");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login?next=/bookings");
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (!isAuthenticated) return;
    async function load() {
      setIsLoading(true);
      try {
        const res = await api.get<Appointment[]>("/bookings/me");
        setAppointments(res);
      } catch { /* ignore */ }
      finally { setIsLoading(false); }
    }
    load();
  }, [isAuthenticated]);

  const now = new Date();
  const filtered = appointments.filter((a) => {
    const isUpcoming = new Date(a.start_time) >= now &&
      !["CANCELLED", "COMPLETED", "NO_SHOW"].includes(a.status);
    return tab === "upcoming" ? isUpcoming : !isUpcoming;
  });

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />
      <main className="flex-1 max-w-3xl mx-auto w-full px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">My Bookings</h1>

        <div className="flex gap-2 mb-6">
          {(["upcoming", "past"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={cn("px-5 py-2 rounded-full text-sm font-medium transition-colors capitalize",
                tab === t ? "bg-brand-600 text-white" : "bg-white text-gray-600 border border-gray-300 hover:border-brand-300"
              )}
            >
              {t}
            </button>
          ))}
        </div>

        {isLoading ? (
          <div className="flex justify-center py-16"><Loader2 className="w-6 h-6 animate-spin text-brand-600" /></div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-2xl border border-gray-200">
            <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="font-semibold text-gray-900 mb-2">
              {tab === "upcoming" ? "No upcoming bookings" : "No past bookings"}
            </h3>
            <p className="text-gray-500 text-sm mb-6">
              {tab === "upcoming" ? "Discover and book your next appointment." : "Your completed appointments will appear here."}
            </p>
            {tab === "upcoming" && (
              <Link href="/explore" className="inline-flex items-center gap-2 bg-brand-600 text-white text-sm font-semibold px-5 py-2.5 rounded-lg hover:bg-brand-700 transition-colors">
                Explore businesses
              </Link>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map((appt) => (
              <Link
                key={appt.id}
                href={`/bookings/${appt.id}`}
                className="flex items-center justify-between p-4 bg-white rounded-xl border border-gray-200 hover:border-brand-200 hover:shadow-sm transition-all"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={cn("text-xs font-medium px-2 py-0.5 rounded-full", STATUS_STYLES[appt.status] ?? "bg-gray-100 text-gray-600")}>
                      {appt.status.replace("_", " ")}
                    </span>
                  </div>
                  <p className="font-medium text-gray-900 text-sm">{appt.items?.[0]?.service_name ?? "Appointment"}</p>
                  <div className="flex items-center gap-4 mt-1 text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>{formatDate(appt.start_time)}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{formatTime(appt.start_time)}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3 ml-4">
                  <span className="font-semibold text-gray-900 text-sm">{formatCurrency(appt.total_amount)}</span>
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
