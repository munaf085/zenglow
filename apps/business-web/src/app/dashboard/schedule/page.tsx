"use client";

/**
 * Staff Schedule Manager
 * 
 * Features:
 * - Weekly grid: all staff × all 7 days
 * - Per-cell shift editor: start, end, break window
 * - Shift presets: Morning / Afternoon / Full Day / Custom / Day Off
 * - Visual colour-coded shift blocks
 * - Leave management: create/view/delete absences
 * - Copy schedule from one staff to another
 * - Save individual staff or all at once
 */

import { useEffect, useState, useCallback } from "react";
import {
  Clock, Save, Loader2, Plus, Trash2, Copy,
  ChevronDown, ChevronUp, Calendar, AlertCircle,
  Sun, Sunset, Moon, Coffee,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import type { Staff } from "@zenglow/types";
import { cn, initials, formatDate } from "@/lib/utils";
import { toast } from "sonner";
import { format, addDays } from "date-fns";

// ── Types ─────────────────────────────────────────────────────────────────────

interface DaySchedule {
  day_of_week: number;
  is_open: boolean;
  open_time: string;
  close_time: string;
  break_start: string;
  break_end: string;
}

interface StaffSchedule {
  staffId: string;
  days: DaySchedule[];
  dirty: boolean;
  saving: boolean;
}

interface StaffLeave {
  id: string;
  staff_id: string;
  leave_type: string;
  start_date: string;
  end_date: string;
  reason?: string;
  approved: boolean;
}

// ── Constants ─────────────────────────────────────────────────────────────────

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const DAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const SHIFT_PRESETS = [
  { label: "Morning",   icon: Sun,     open: "08:00", close: "13:00", break_start: "", break_end: "" },
  { label: "Afternoon", icon: Coffee,  open: "13:00", close: "18:00", break_start: "", break_end: "" },
  { label: "Full Day",  icon: Sunset,  open: "09:00", close: "18:00", break_start: "13:00", break_end: "14:00" },
  { label: "Evening",   icon: Moon,    open: "15:00", close: "21:00", break_start: "", break_end: "" },
];

const LEAVE_TYPES = ["ANNUAL", "SICK", "PERSONAL", "BLOCKED"];
const LEAVE_COLORS: Record<string, string> = {
  ANNUAL:   "bg-blue-100 text-blue-700 border-blue-200",
  SICK:     "bg-red-100 text-red-700 border-red-200",
  PERSONAL: "bg-purple-100 text-purple-700 border-purple-200",
  BLOCKED:  "bg-gray-100 text-gray-600 border-gray-200",
};

// ── Default schedule helper ───────────────────────────────────────────────────

function defaultSchedule(staffId: string): StaffSchedule {
  return {
    staffId,
    dirty: false,
    saving: false,
    days: Array.from({ length: 7 }, (_, i) => ({
      day_of_week: i,
      is_open: i < 6,
      open_time: i < 6 ? "09:00" : "",
      close_time: i < 6 ? "18:00" : "",
      break_start: "",
      break_end: "",
    })),
  };
}

// ── Shift block colour ────────────────────────────────────────────────────────

function shiftColor(open: string): string {
  const h = parseInt(open.split(":")[0], 10);
  if (h < 12) return "bg-amber-50 border-amber-300 text-amber-800";
  if (h < 16) return "bg-blue-50 border-blue-300 text-blue-800";
  return "bg-purple-50 border-purple-300 text-purple-800";
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function SchedulePage() {
  const { business } = useAuth();
  const [staffList, setStaffList] = useState<Staff[]>([]);
  const [schedules, setSchedules] = useState<Record<string, StaffSchedule>>({});
  const [leaves, setLeaves] = useState<Record<string, StaffLeave[]>>({});
  const [expandedStaff, setExpandedStaff] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"schedule" | "leave">("schedule");
  const [isLoading, setIsLoading] = useState(true);

  // Leave form state
  const [leaveForm, setLeaveForm] = useState({
    staffId: "",
    leave_type: "ANNUAL",
    start_date: format(new Date(), "yyyy-MM-dd"),
    end_date: format(addDays(new Date(), 1), "yyyy-MM-dd"),
    reason: "",
  });
  const [savingLeave, setSavingLeave] = useState(false);

  // Load staff
  useEffect(() => {
    if (!business) return;
    async function load() {
      setIsLoading(true);
      try {
        const staff = await api.get<Staff[]>(`/businesses/${business!.id}/staff`);
        setStaffList(staff);

        // Load working hours for all staff in parallel
        const scheduleMap: Record<string, StaffSchedule> = {};
        const leaveMap: Record<string, StaffLeave[]> = {};

        await Promise.all(
          staff.map(async (s) => {
            try {
              const [hoursRes, leavesRes] = await Promise.all([
                api.get<DaySchedule[]>(
                  `/businesses/${business!.id}/staff/${s.id}/working-hours`
                ),
                api.get<StaffLeave[]>(
                  `/businesses/${business!.id}/staff/${s.id}/leaves`
                ),
              ]);

              // Merge API response — ensure all 7 days exist
              const days = Array.from({ length: 7 }, (_, i) => {
                const existing = hoursRes.find((h) => h.day_of_week === i);
                return existing ?? {
                  day_of_week: i,
                  is_open: i < 6,
                  open_time: i < 6 ? "09:00" : "",
                  close_time: i < 6 ? "18:00" : "",
                  break_start: "",
                  break_end: "",
                };
              });

              scheduleMap[s.id] = { staffId: s.id, days, dirty: false, saving: false };
              leaveMap[s.id] = leavesRes;
            } catch {
              scheduleMap[s.id] = defaultSchedule(s.id);
              leaveMap[s.id] = [];
            }
          })
        );

        setSchedules(scheduleMap);
        setLeaves(leaveMap);
        if (staff.length > 0) setExpandedStaff(staff[0].id);
      } catch {
        toast.error("Failed to load staff schedules");
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [business]);

  // Update a single day field for a staff member
  const updateDay = useCallback(
    (staffId: string, dayIndex: number, field: keyof DaySchedule, value: string | boolean) => {
      setSchedules((prev) => ({
        ...prev,
        [staffId]: {
          ...prev[staffId],
          dirty: true,
          days: prev[staffId].days.map((d, i) =>
            i === dayIndex ? { ...d, [field]: value } : d
          ),
        },
      }));
    },
    []
  );

  // Apply a preset to a day
  const applyPreset = (
    staffId: string,
    dayIndex: number,
    preset: typeof SHIFT_PRESETS[number] | null
  ) => {
    if (!preset) {
      // Day Off
      updateDay(staffId, dayIndex, "is_open", false);
      return;
    }
    setSchedules((prev) => ({
      ...prev,
      [staffId]: {
        ...prev[staffId],
        dirty: true,
        days: prev[staffId].days.map((d, i) =>
          i === dayIndex
            ? {
                ...d,
                is_open: true,
                open_time: preset.open,
                close_time: preset.close,
                break_start: preset.break_start,
                break_end: preset.break_end,
              }
            : d
        ),
      },
    }));
  };

  // Apply a preset to ALL days (Mon–Fri) for a staff
  const applyPresetToWeek = (staffId: string, preset: typeof SHIFT_PRESETS[number]) => {
    setSchedules((prev) => ({
      ...prev,
      [staffId]: {
        ...prev[staffId],
        dirty: true,
        days: prev[staffId].days.map((d) =>
          d.day_of_week < 5
            ? {
                ...d,
                is_open: true,
                open_time: preset.open,
                close_time: preset.close,
                break_start: preset.break_start,
                break_end: preset.break_end,
              }
            : d
        ),
      },
    }));
    toast.success(`${preset.label} shift applied to Mon–Fri`);
  };

  // Copy one staff's schedule to another
  const copySchedule = (fromId: string, toId: string) => {
    const source = schedules[fromId];
    if (!source) return;
    setSchedules((prev) => ({
      ...prev,
      [toId]: {
        ...prev[toId],
        dirty: true,
        days: source.days.map((d) => ({ ...d })),
      },
    }));
    const from = staffList.find((s) => s.id === fromId);
    const to = staffList.find((s) => s.id === toId);
    toast.success(`Copied ${from?.first_name}'s schedule to ${to?.first_name}`);
  };

  // Save one staff member's schedule
  const saveSchedule = async (staffId: string) => {
    if (!business) return;
    const sched = schedules[staffId];
    if (!sched) return;

    setSchedules((prev) => ({
      ...prev,
      [staffId]: { ...prev[staffId], saving: true },
    }));

    try {
      await api.put(`/businesses/${business.id}/staff/${staffId}/working-hours`, {
        hours: sched.days.map((d) => ({
          day_of_week: d.day_of_week,
          is_open: d.is_open,
          open_time: d.is_open && d.open_time ? d.open_time : null,
          close_time: d.is_open && d.close_time ? d.close_time : null,
          break_start: d.is_open && d.break_start ? d.break_start : null,
          break_end: d.is_open && d.break_end ? d.break_end : null,
        })),
      });
      setSchedules((prev) => ({
        ...prev,
        [staffId]: { ...prev[staffId], dirty: false, saving: false },
      }));
      const staff = staffList.find((s) => s.id === staffId);
      toast.success(`${staff?.first_name}'s schedule saved`);
    } catch (err: any) {
      setSchedules((prev) => ({
        ...prev,
        [staffId]: { ...prev[staffId], saving: false },
      }));
      toast.error(err.message ?? "Failed to save schedule");
    }
  };

  // Save ALL dirty schedules
  const saveAll = async () => {
    const dirty = Object.values(schedules).filter((s) => s.dirty);
    if (!dirty.length) { toast("No changes to save"); return; }
    await Promise.all(dirty.map((s) => saveSchedule(s.staffId)));
  };

  // Add leave
  const addLeave = async () => {
    if (!business || !leaveForm.staffId) {
      toast.error("Please select a staff member");
      return;
    }
    setSavingLeave(true);
    try {
      const leave = await api.post<StaffLeave>(
        `/businesses/${business.id}/staff/${leaveForm.staffId}/leaves`,
        {
          leave_type: leaveForm.leave_type,
          start_date: leaveForm.start_date,
          end_date: leaveForm.end_date,
          reason: leaveForm.reason || undefined,
        }
      );
      setLeaves((prev) => ({
        ...prev,
        [leaveForm.staffId]: [...(prev[leaveForm.staffId] ?? []), leave],
      }));
      toast.success("Leave added");
      setLeaveForm((f) => ({ ...f, reason: "" }));
    } catch (err: any) {
      toast.error(err.message ?? "Failed to add leave");
    } finally {
      setSavingLeave(false);
    }
  };

  // ── Render ──────────────────────────────────────────────────────────────────

  if (!business) return null;

  const dirtyCount = Object.values(schedules).filter((s) => s.dirty).length;

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Staff Schedules</h1>
          <p className="text-gray-500 text-sm mt-1">
            Manage working hours, shifts, and time off for your team
          </p>
        </div>
        <div className="flex items-center gap-3">
          {dirtyCount > 0 && (
            <span className="text-xs text-amber-600 bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-full font-medium">
              {dirtyCount} unsaved change{dirtyCount > 1 ? "s" : ""}
            </span>
          )}
          <button
            onClick={saveAll}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold px-4 py-2.5 rounded-lg text-sm transition-colors"
          >
            <Save className="w-4 h-4" />
            Save all
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl w-fit mb-6">
        {([
          { key: "schedule", label: "Work Schedules", icon: Clock },
          { key: "leave", label: "Leave & Absence", icon: Calendar },
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

      {/* ── SCHEDULE TAB ────────────────────────────────────────────────────── */}
      {activeTab === "schedule" && (
        <div>
          {isLoading ? (
            <div className="flex justify-center py-20">
              <Loader2 className="w-7 h-7 animate-spin text-brand-600" />
            </div>
          ) : staffList.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
              <p className="text-4xl mb-3">👥</p>
              <p className="font-semibold text-gray-900 mb-1">No staff yet</p>
              <p className="text-sm text-gray-500">Add staff members first, then configure their schedules.</p>
            </div>
          ) : (

            /* ── Weekly overview grid ─────────────────────────────────────── */
            <div className="space-y-4">
              {/* Quick overview table */}
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div className="px-5 py-3 border-b border-gray-100 bg-gray-50">
                  <p className="text-sm font-semibold text-gray-600">Weekly Overview</p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100">
                        <th className="text-left px-4 py-3 font-medium text-gray-600 w-36 sticky left-0 bg-white">
                          Staff
                        </th>
                        {DAY_SHORT.map((d) => (
                          <th key={d} className="text-center px-2 py-3 font-medium text-gray-600 min-w-[90px]">
                            {d}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {staffList.map((staff) => {
                        const sched = schedules[staff.id];
                        return (
                          <tr key={staff.id} className="hover:bg-gray-50 transition-colors">
                            {/* Staff name */}
                            <td className="px-4 py-3 sticky left-0 bg-white">
                              <button
                                onClick={() =>
                                  setExpandedStaff(
                                    expandedStaff === staff.id ? null : staff.id
                                  )
                                }
                                className="flex items-center gap-2 text-left w-full"
                              >
                                <div className="w-8 h-8 bg-brand-100 rounded-full flex items-center justify-center flex-shrink-0">
                                  <span className="text-brand-700 text-xs font-semibold">
                                    {initials(staff.first_name, staff.last_name)}
                                  </span>
                                </div>
                                <div className="min-w-0">
                                  <p className="font-medium text-gray-900 text-xs truncate">
                                    {staff.first_name}
                                  </p>
                                  {sched?.dirty && (
                                    <span className="text-xs text-amber-500">unsaved</span>
                                  )}
                                </div>
                              </button>
                            </td>

                            {/* Day cells */}
                            {sched?.days.map((day, i) => (
                              <td key={i} className="px-1 py-2 text-center">
                                {day.is_open ? (
                                  <div
                                    className={cn(
                                      "rounded-lg border px-1.5 py-1 text-xs font-medium cursor-pointer hover:shadow-sm transition-shadow mx-0.5",
                                      shiftColor(day.open_time)
                                    )}
                                    onClick={() =>
                                      setExpandedStaff(
                                        expandedStaff === staff.id ? null : staff.id
                                      )
                                    }
                                    title={`${day.open_time} – ${day.close_time}${day.break_start ? ` (break ${day.break_start}–${day.break_end})` : ""}`}
                                  >
                                    <p className="leading-tight">{day.open_time}</p>
                                    <p className="text-xs opacity-70">–{day.close_time}</p>
                                  </div>
                                ) : (
                                  <span className="text-xs text-gray-300 font-medium">Off</span>
                                )}
                              </td>
                            ))}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* ── Expanded staff schedule editor ──────────────────────── */}
              {staffList.map((staff) => {
                if (expandedStaff !== staff.id) return null;
                const sched = schedules[staff.id];
                if (!sched) return null;

                return (
                  <div
                    key={staff.id}
                    className="bg-white rounded-xl border border-brand-200 shadow-sm overflow-hidden"
                  >
                    {/* Staff editor header */}
                    <div className="flex items-center justify-between px-5 py-4 bg-brand-50 border-b border-brand-100">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-brand-600 rounded-full flex items-center justify-center flex-shrink-0">
                          <span className="text-white font-semibold text-sm">
                            {initials(staff.first_name, staff.last_name)}
                          </span>
                        </div>
                        <div>
                          <p className="font-bold text-gray-900">
                            {staff.first_name} {staff.last_name}
                          </p>
                          {staff.title && (
                            <p className="text-xs text-gray-500">{staff.title}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {/* Copy from another staff */}
                        {staffList.length > 1 && (
                          <div className="relative group">
                            <button className="flex items-center gap-1.5 px-3 py-1.5 border border-gray-300 rounded-lg text-xs font-medium text-gray-600 hover:bg-white transition-colors">
                              <Copy className="w-3.5 h-3.5" />
                              Copy from
                            </button>
                            <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-10 py-1 min-w-[150px] hidden group-hover:block">
                              {staffList
                                .filter((s) => s.id !== staff.id)
                                .map((other) => (
                                  <button
                                    key={other.id}
                                    onClick={() => copySchedule(other.id, staff.id)}
                                    className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 text-gray-700"
                                  >
                                    {other.first_name} {other.last_name}
                                  </button>
                                ))}
                            </div>
                          </div>
                        )}

                        {/* Quick week presets */}
                        <div className="hidden sm:flex gap-1">
                          {SHIFT_PRESETS.slice(0, 2).map((preset) => (
                            <button
                              key={preset.label}
                              onClick={() => applyPresetToWeek(staff.id, preset)}
                              className="px-2.5 py-1.5 border border-gray-300 rounded-lg text-xs font-medium text-gray-600 hover:bg-white hover:border-brand-400 hover:text-brand-700 transition-colors"
                              title={`Apply ${preset.label} to Mon–Fri`}
                            >
                              {preset.label} week
                            </button>
                          ))}
                        </div>

                        {/* Save this staff */}
                        <button
                          onClick={() => saveSchedule(staff.id)}
                          disabled={sched.saving || !sched.dirty}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition-colors"
                        >
                          {sched.saving ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Save className="w-3.5 h-3.5" />
                          )}
                          {sched.dirty ? "Save" : "Saved"}
                        </button>
                      </div>
                    </div>

                    {/* Day rows */}
                    <div className="divide-y divide-gray-100">
                      {sched.days.map((day, i) => (
                        <div
                          key={i}
                          className={cn(
                            "px-5 py-3 flex items-center gap-3 flex-wrap",
                            !day.is_open && "bg-gray-50/60"
                          )}
                        >
                          {/* Day toggle */}
                          <div className="flex items-center gap-3 w-28 flex-shrink-0">
                            <button
                              type="button"
                              onClick={() => updateDay(staff.id, i, "is_open", !day.is_open)}
                              className={cn(
                                "relative w-10 h-5 rounded-full transition-colors flex-shrink-0",
                                day.is_open ? "bg-brand-600" : "bg-gray-300"
                              )}
                              aria-label={`Toggle ${DAYS[i]}`}
                            >
                              <span
                                className={cn(
                                  "absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform",
                                  day.is_open ? "translate-x-5" : "translate-x-0.5"
                                )}
                              />
                            </button>
                            <span
                              className={cn(
                                "text-sm font-semibold w-8",
                                day.is_open ? "text-gray-900" : "text-gray-400"
                              )}
                            >
                              {DAY_SHORT[i]}
                            </span>
                          </div>

                          {day.is_open ? (
                            <>
                              {/* Shift preset buttons */}
                              <div className="flex gap-1 flex-wrap">
                                {SHIFT_PRESETS.map((preset) => {
                                  const Icon = preset.icon;
                                  const active =
                                    day.open_time === preset.open &&
                                    day.close_time === preset.close;
                                  return (
                                    <button
                                      key={preset.label}
                                      type="button"
                                      onClick={() => applyPreset(staff.id, i, preset)}
                                      className={cn(
                                        "flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium border transition-colors",
                                        active
                                          ? "bg-brand-600 text-white border-brand-600"
                                          : "bg-white text-gray-500 border-gray-200 hover:border-brand-400 hover:text-brand-700"
                                      )}
                                    >
                                      <Icon className="w-3 h-3" />
                                      {preset.label}
                                    </button>
                                  );
                                })}
                                <button
                                  type="button"
                                  onClick={() => applyPreset(staff.id, i, null)}
                                  className="px-2 py-1 rounded-md text-xs font-medium border border-red-200 text-red-500 hover:bg-red-50 transition-colors"
                                >
                                  Day off
                                </button>
                              </div>

                              {/* Time inputs */}
                              <div className="flex items-center gap-2 flex-wrap ml-auto">
                                <div className="flex items-center gap-1.5 bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5">
                                  <span className="text-xs text-gray-500 font-medium">Start</span>
                                  <input
                                    type="time"
                                    value={day.open_time}
                                    onChange={(e) =>
                                      updateDay(staff.id, i, "open_time", e.target.value)
                                    }
                                    className="text-sm font-semibold text-gray-900 bg-transparent border-none outline-none w-20"
                                  />
                                </div>
                                <span className="text-gray-400 text-sm">→</span>
                                <div className="flex items-center gap-1.5 bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5">
                                  <span className="text-xs text-gray-500 font-medium">End</span>
                                  <input
                                    type="time"
                                    value={day.close_time}
                                    onChange={(e) =>
                                      updateDay(staff.id, i, "close_time", e.target.value)
                                    }
                                    className="text-sm font-semibold text-gray-900 bg-transparent border-none outline-none w-20"
                                  />
                                </div>

                                {/* Break */}
                                <div className="flex items-center gap-1.5 bg-amber-50 border border-amber-200 rounded-lg px-3 py-1.5">
                                  <Coffee className="w-3.5 h-3.5 text-amber-500" />
                                  <input
                                    type="time"
                                    value={day.break_start}
                                    onChange={(e) =>
                                      updateDay(staff.id, i, "break_start", e.target.value)
                                    }
                                    className="text-xs text-amber-700 bg-transparent border-none outline-none w-16"
                                    placeholder="—"
                                    title="Break start"
                                  />
                                  <span className="text-amber-400 text-xs">–</span>
                                  <input
                                    type="time"
                                    value={day.break_end}
                                    onChange={(e) =>
                                      updateDay(staff.id, i, "break_end", e.target.value)
                                    }
                                    className="text-xs text-amber-700 bg-transparent border-none outline-none w-16"
                                    placeholder="—"
                                    title="Break end"
                                  />
                                </div>
                              </div>
                            </>
                          ) : (
                            <span className="text-sm text-gray-400 flex-1">
                              Not working — day off
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ── LEAVE TAB ────────────────────────────────────────────────────────── */}
      {activeTab === "leave" && (
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Add leave form */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="font-semibold text-gray-900 mb-5 flex items-center gap-2">
              <Plus className="w-4 h-4 text-brand-600" />
              Add Leave / Time Off
            </h2>

            <div className="space-y-4">
              {/* Staff selector */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Staff member *
                </label>
                <select
                  value={leaveForm.staffId}
                  onChange={(e) => setLeaveForm((f) => ({ ...f, staffId: e.target.value }))}
                  className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="">Select staff...</option>
                  {staffList.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.first_name} {s.last_name}
                      {s.title ? ` — ${s.title}` : ""}
                    </option>
                  ))}
                </select>
              </div>

              {/* Leave type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Leave type *
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {LEAVE_TYPES.map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => setLeaveForm((f) => ({ ...f, leave_type: type }))}
                      className={cn(
                        "py-2 rounded-lg border text-sm font-medium transition-colors",
                        leaveForm.leave_type === type
                          ? "bg-brand-600 text-white border-brand-600"
                          : "bg-white text-gray-600 border-gray-300 hover:border-brand-400"
                      )}
                    >
                      {type.charAt(0) + type.slice(1).toLowerCase()}
                    </button>
                  ))}
                </div>
              </div>

              {/* Dates */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Start date *
                  </label>
                  <input
                    type="date"
                    value={leaveForm.start_date}
                    onChange={(e) => setLeaveForm((f) => ({ ...f, start_date: e.target.value }))}
                    className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    End date *
                  </label>
                  <input
                    type="date"
                    value={leaveForm.end_date}
                    min={leaveForm.start_date}
                    onChange={(e) => setLeaveForm((f) => ({ ...f, end_date: e.target.value }))}
                    className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>

              {/* Reason */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Reason{" "}
                  <span className="text-gray-400 font-normal">(optional)</span>
                </label>
                <textarea
                  value={leaveForm.reason}
                  onChange={(e) => setLeaveForm((f) => ({ ...f, reason: e.target.value }))}
                  rows={2}
                  className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
                  placeholder="e.g. Annual vacation, Medical appointment..."
                />
              </div>

              <button
                onClick={addLeave}
                disabled={savingLeave || !leaveForm.staffId}
                className="w-full flex items-center justify-center gap-2 py-3 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-semibold rounded-lg text-sm transition-colors"
              >
                {savingLeave ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                Add leave
              </button>
            </div>
          </div>

          {/* Upcoming leaves */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100 bg-gray-50">
              <h2 className="font-semibold text-gray-900">Leave Calendar</h2>
              <p className="text-xs text-gray-500 mt-0.5">All staff absences</p>
            </div>
            <div className="divide-y divide-gray-100 max-h-[500px] overflow-y-auto">
              {staffList.every((s) => !leaves[s.id]?.length) ? (
                <div className="text-center py-12">
                  <Calendar className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                  <p className="text-sm text-gray-400">No leave records yet</p>
                </div>
              ) : (
                staffList.flatMap((staff) =>
                  (leaves[staff.id] ?? []).map((leave) => (
                    <div key={leave.id} className="px-5 py-4 flex items-center gap-4">
                      {/* Staff avatar */}
                      <div className="w-9 h-9 bg-brand-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-brand-700 text-xs font-semibold">
                          {initials(staff.first_name, staff.last_name)}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">
                          {staff.first_name} {staff.last_name}
                        </p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {formatDate(leave.start_date + "T00:00:00Z")} →{" "}
                          {formatDate(leave.end_date + "T00:00:00Z")}
                          {leave.reason && <span> · {leave.reason}</span>}
                        </p>
                      </div>
                      <span
                        className={cn(
                          "text-xs font-semibold px-2.5 py-0.5 rounded-full border flex-shrink-0",
                          LEAVE_COLORS[leave.leave_type] ?? "bg-gray-100 text-gray-600 border-gray-200"
                        )}
                      >
                        {leave.leave_type.charAt(0) +
                          leave.leave_type.slice(1).toLowerCase()}
                      </span>
                    </div>
                  ))
                )
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
