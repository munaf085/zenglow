"use client";

import { useEffect, useState, useCallback } from "react";
import { format, addDays, startOfWeek, endOfWeek, isSameDay, parseISO } from "date-fns";
import { ChevronLeft, ChevronRight, Plus, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import type { Appointment } from "@zenglow/types";
import { cn } from "@/lib/utils";

type ViewMode = "day" | "week";
const HOURS = Array.from({ length: 13 }, (_, i) => i + 8); // 8am to 8pm

const STATUS_BG: Record<string, string> = {
  CONFIRMED: "bg-green-100 border-green-400 text-green-900",
  PENDING: "bg-yellow-100 border-yellow-400 text-yellow-900",
  COMPLETED: "bg-gray-100 border-gray-400 text-gray-700",
  CANCELLED: "bg-red-100 border-red-300 text-red-700 line-through opacity-60",
  IN_PROGRESS: "bg-blue-100 border-blue-400 text-blue-900",
};

export default function CalendarPage() {
  const { business } = useAuth();
  const [view, setView] = useState<ViewMode>("day");
  const [currentDate, setCurrentDate] = useState(new Date());
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadAppointments = useCallback(async () => {
    if (!business) return;
    setIsLoading(true);
    try {
      const start = view === "day" ? new Date(currentDate.setHours(0, 0, 0, 0)) : startOfWeek(currentDate, { weekStartsOn: 1 });
      const end = view === "day" ? new Date(currentDate.setHours(23, 59, 59, 999)) : endOfWeek(currentDate, { weekStartsOn: 1 });
      const params = new URLSearchParams({ start_date: start.toISOString(), end_date: end.toISOString() });
      const res = await api.get<Appointment[]>(`/businesses/${business.id}/appointments?${params}`);
      setAppointments(res);
    } catch { /* ignore */ }
    finally { setIsLoading(false); }
  }, [business, currentDate, view]);

  useEffect(() => { loadAppointments(); }, [loadAppointments]);

  const navigate = (dir: 1 | -1) => {
    setCurrentDate((d) => addDays(d, dir * (view === "week" ? 7 : 1)));
  };

  const getDayAppts = (date: Date) =>
    appointments.filter((a) => isSameDay(parseISO(a.start_time), date));

  const getApptTop = (appt: Appointment) => {
    const start = parseISO(appt.start_time);
    const h = start.getHours() - 8;
    const m = start.getMinutes();
    return (h * 60 + m) * (64 / 60); // 64px per hour
  };

  const getApptHeight = (appt: Appointment) => {
    const start = parseISO(appt.start_time);
    const end = parseISO(appt.end_time);
    const mins = (end.getTime() - start.getTime()) / 60000;
    return Math.max(mins * (64 / 60), 32);
  };

  const weekDays = view === "week"
    ? Array.from({ length: 7 }, (_, i) => addDays(startOfWeek(currentDate, { weekStartsOn: 1 }), i))
    : [currentDate];

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Calendar</h1>
          <p className="text-gray-500 text-sm mt-1">
            {view === "day" ? format(currentDate, "EEEE, MMMM d, yyyy") : `${format(weekDays[0], "MMM d")} – ${format(weekDays[6], "MMM d, yyyy")}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* View toggle */}
          <div className="flex border border-gray-200 rounded-lg overflow-hidden">
            {(["day", "week"] as ViewMode[]).map((v) => (
              <button key={v} onClick={() => setView(v)}
                className={cn("px-4 py-1.5 text-sm font-medium capitalize transition-colors",
                  view === v ? "bg-brand-600 text-white" : "bg-white text-gray-600 hover:bg-gray-50"
                )}>
                {v}
              </button>
            ))}
          </div>
          {/* Nav */}
          <div className="flex border border-gray-200 rounded-lg overflow-hidden">
            <button onClick={() => navigate(-1)} className="px-3 py-1.5 bg-white hover:bg-gray-50 border-r border-gray-200 text-gray-600">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button onClick={() => setCurrentDate(new Date())} className="px-3 py-1.5 bg-white hover:bg-gray-50 text-sm font-medium text-gray-600 border-r border-gray-200">
              Today
            </button>
            <button onClick={() => navigate(1)} className="px-3 py-1.5 bg-white hover:bg-gray-50 text-gray-600">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Calendar grid */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {/* Day headers (week view) */}
        {view === "week" && (
          <div className="grid grid-cols-[64px_repeat(7,1fr)] border-b border-gray-200">
            <div className="border-r border-gray-200" />
            {weekDays.map((d) => (
              <div key={d.toISOString()} className={cn("py-3 text-center border-r border-gray-200 last:border-0",
                isSameDay(d, new Date()) ? "bg-brand-50" : "")}>
                <p className="text-xs font-medium text-gray-500 uppercase">{format(d, "EEE")}</p>
                <p className={cn("text-lg font-bold mt-0.5", isSameDay(d, new Date()) ? "text-brand-600" : "text-gray-900")}>
                  {format(d, "d")}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Time grid */}
        <div className="overflow-y-auto" style={{ maxHeight: "calc(100vh - 280px)" }}>
          {isLoading ? (
            <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-brand-600" /></div>
          ) : (
            <div className={cn("grid", view === "week" ? "grid-cols-[64px_repeat(7,1fr)]" : "grid-cols-[64px_1fr]")}>
              {/* Time column */}
              <div>
                {HOURS.map((h) => (
                  <div key={h} className="h-16 border-b border-gray-100 border-r border-gray-200 px-2 pt-1">
                    <span className="text-xs text-gray-400">{format(new Date().setHours(h, 0), "h a")}</span>
                  </div>
                ))}
              </div>

              {/* Day columns */}
              {weekDays.map((day) => {
                const dayAppts = getDayAppts(day);
                return (
                  <div key={day.toISOString()} className={cn("relative border-r border-gray-200 last:border-0",
                    isSameDay(day, new Date()) ? "bg-brand-50/30" : "")}>
                    {HOURS.map((h) => (
                      <div key={h} className="h-16 border-b border-gray-100" />
                    ))}
                    {dayAppts.map((appt) => (
                      <div
                        key={appt.id}
                        className={cn("absolute left-1 right-1 rounded border-l-4 px-2 py-1 overflow-hidden cursor-pointer hover:shadow-sm transition-shadow",
                          STATUS_BG[appt.status] ?? "bg-gray-100 border-gray-400")}
                        style={{ top: getApptTop(appt), height: getApptHeight(appt) }}
                        title={`${appt.items?.[0]?.service_name} — ${format(parseISO(appt.start_time), "h:mm a")}`}
                      >
                        <p className="text-xs font-semibold truncate">{format(parseISO(appt.start_time), "h:mm a")}</p>
                        <p className="text-xs truncate">{appt.items?.[0]?.service_name}</p>
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
