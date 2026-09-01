"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { format, addDays } from "date-fns";
import {
  ChevronLeft, Clock, Check, Loader2, Calendar,
  ShieldCheck, AlertCircle, Info, Sparkles, User,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import type { Business, Service, Staff, AvailabilityResponse, TimeSlot } from "@zenglow/types";
import { formatCurrency, formatTime, durationLabel, cn } from "@/lib/utils";
import { toast } from "sonner";

type Step = "service" | "staff" | "datetime" | "confirm";

export default function BookPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const businessId = searchParams.get("business") ?? "";
  const branchId = searchParams.get("branch") ?? "";
  const preselectedServiceId = searchParams.get("service") ?? "";

  const [step, setStep] = useState<Step>("service");
  const [business, setBusiness] = useState<Business | null>(null);
  const [services, setServices] = useState<Service[]>([]);
  const [staffList, setStaffList] = useState<Staff[]>([]);
  const [availability, setAvailability] = useState<AvailabilityResponse | null>(null);

  const [selectedService, setSelectedService] = useState<Service | null>(null);
  const [selectedStaff, setSelectedStaff] = useState<Staff | null>(null); // null = any
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null);
  const [customerNotes, setCustomerNotes] = useState("");
  const [isBooking, setIsBooking] = useState(false);
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);

  // Redirect to login if not authenticated (after loading)
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push(`/login?next=/book?${searchParams.toString()}`);
    }
  }, [authLoading, isAuthenticated, router, searchParams]);

  // Load business and services
  useEffect(() => {
    if (!businessId) return;
    async function load() {
      try {
        const [biz, svcs] = await Promise.all([
          api.publicGet<Business>(`/businesses/public/${businessId}`),
          api.publicGet<Service[]>(`/businesses/${businessId}/services?active_only=true`),
        ]);
        setBusiness(biz);
        setServices(svcs);
        if (preselectedServiceId) {
          const svc = svcs.find((s) => s.id === preselectedServiceId);
          if (svc) {
            setSelectedService(svc);
            setStep("staff");
          }
        }
      } catch {
        toast.error("Could not load business details");
      }
    }
    load();
  }, [businessId, preselectedServiceId]);

  // Load staff when service selected
  useEffect(() => {
    if (!selectedService || !businessId) return;
    async function loadStaff() {
      try {
        const res = await api.publicGet<Staff[]>(`/businesses/${businessId}/staff`);
        setStaffList(res.filter((s) => s.bookable && s.service_ids.includes(selectedService!.id)));
      } catch {
        /* ignore */
      }
    }
    loadStaff();
  }, [selectedService, businessId]);

  // Load availability
  useEffect(() => {
    if (!selectedService || !branchId || step !== "datetime") return;
    async function loadSlots() {
      setIsLoadingSlots(true);
      setAvailability(null);
      try {
        const params = new URLSearchParams({
          business_id: businessId,
          branch_id: branchId,
          service_id: selectedService!.id,
          date: format(selectedDate, "yyyy-MM-dd"),
        });
        if (selectedStaff) params.set("staff_id", selectedStaff.id);
        const res = await api.publicGet<AvailabilityResponse>(`/availability?${params}`);
        setAvailability(res);
      } catch {
        toast.error("Could not load available slots");
      } finally {
        setIsLoadingSlots(false);
      }
    }
    loadSlots();
  }, [selectedService, selectedDate, selectedStaff, step, businessId, branchId]);

  const handleBook = async () => {
    if (!selectedService || !selectedSlot || !branchId) return;
    setIsBooking(true);
    try {
      const appointment = await api.post<{ id: string }>("/bookings", {
        business_id: businessId,
        branch_id: branchId,
        customer_notes: customerNotes.trim() || undefined,
        items: [
          {
            service_id: selectedService.id,
            staff_id: selectedSlot.staff_id,
            start_time: selectedSlot.start_time,
          },
        ],
      });
      toast.success("Appointment successfully booked!");
      router.push(`/bookings/${appointment.id}`);
    } catch (err: any) {
      toast.error(err.message ?? "Booking failed. Please try again.");
    } finally {
      setIsBooking(false);
    }
  };

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-brand-600" />
      </div>
    );
  }

  // Calculate deposit details
  const price = selectedService?.price ?? 0;
  const depositRequired = Boolean(business?.deposit_required && business?.deposit_percentage);
  const depositPercentage = business?.deposit_percentage ?? 0;
  const depositAmount = depositRequired ? (price * depositPercentage) / 100 : 0;
  const balanceDue = price - depositAmount;

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 sm:py-10 pb-28 sm:pb-12">
      {/* Progress Steps Header */}
      <div className="flex items-center gap-2 mb-6 sm:mb-8 overflow-x-auto pb-2 scrollbar-none">
        {(["service", "staff", "datetime", "confirm"] as Step[]).map((s, i) => (
          <div key={s} className="flex items-center gap-2 flex-shrink-0">
            {i > 0 && <div className="w-6 sm:w-10 h-0.5 bg-gray-200" />}
            <div
              className={cn(
                "flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs sm:text-sm font-semibold transition-all shadow-sm",
                step === s
                  ? "bg-brand-600 text-white shadow-brand-200"
                  : "bg-white text-gray-500 border border-gray-200"
              )}
            >
              <span className="capitalize">{s === "datetime" ? "Date & Time" : s}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Business Banner Info */}
      {business && (
        <div className="flex items-center gap-3.5 mb-6 p-4 bg-white rounded-2xl border border-gray-200 shadow-sm">
          <div className="w-12 h-12 bg-gradient-to-br from-brand-600 to-brand-700 rounded-xl flex items-center justify-center flex-shrink-0 text-white font-bold text-lg shadow-sm">
            {business.name[0]}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-bold text-gray-900 text-base truncate">{business.name}</h3>
            <p className="text-xs text-gray-500 truncate">
              {business.branches?.find((b) => b.id === branchId)?.name ?? "Main Branch"} •{" "}
              {business.branches?.find((b) => b.id === branchId)?.city ?? "Salon"}
            </p>
          </div>
        </div>
      )}

      {/* Step 1: Choose Service */}
      {step === "service" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900">Select a Service</h2>
            <span className="text-xs font-semibold text-gray-400">{services.length} services</span>
          </div>

          <div className="space-y-3">
            {services.map((svc) => (
              <button
                key={svc.id}
                onClick={() => {
                  setSelectedService(svc);
                  setStep("staff");
                }}
                className={cn(
                  "w-full text-left p-4 sm:p-5 rounded-2xl border transition-all duration-200 shadow-sm",
                  selectedService?.id === svc.id
                    ? "border-brand-500 bg-brand-50/50 ring-2 ring-brand-400/20"
                    : "border-gray-200 hover:border-brand-300 bg-white"
                )}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-gray-900 text-base">{svc.name}</p>
                    {svc.description && (
                      <p className="text-xs text-gray-500 mt-1 line-clamp-2">{svc.description}</p>
                    )}
                    <div className="flex items-center gap-3 mt-2 text-xs text-gray-500 font-medium">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-gray-400" />
                        {durationLabel(svc.duration_minutes)}
                      </span>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <span className="font-extrabold text-base sm:text-lg text-gray-900">
                      {formatCurrency(svc.price)}
                    </span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 2: Choose Staff */}
      {step === "staff" && selectedService && (
        <div className="space-y-4">
          <button
            onClick={() => setStep("service")}
            className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-gray-900 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" /> Back to Services
          </button>

          <h2 className="text-xl font-bold text-gray-900">Choose Specialist</h2>

          <div className="space-y-3">
            {/* Any Specialist Option */}
            <button
              onClick={() => {
                setSelectedStaff(null);
                setStep("datetime");
              }}
              className={cn(
                "w-full text-left p-4 sm:p-5 rounded-2xl border transition-all shadow-sm flex items-center gap-4",
                selectedStaff === null
                  ? "border-brand-500 bg-brand-50/50 ring-2 ring-brand-400/20"
                  : "border-gray-200 hover:border-brand-300 bg-white"
              )}
            >
              <div className="w-12 h-12 bg-brand-100 rounded-full flex items-center justify-center flex-shrink-0 text-brand-700">
                <Sparkles className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <p className="font-bold text-gray-900">Any Available Specialist</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  We will assign the first available professional for you
                </p>
              </div>
            </button>

            {/* Individual Staff List */}
            {staffList.map((s) => (
              <button
                key={s.id}
                onClick={() => {
                  setSelectedStaff(s);
                  setStep("datetime");
                }}
                className={cn(
                  "w-full text-left p-4 sm:p-5 rounded-2xl border transition-all shadow-sm flex items-center gap-4",
                  selectedStaff?.id === s.id
                    ? "border-brand-500 bg-brand-50/50 ring-2 ring-brand-400/20"
                    : "border-gray-200 hover:border-brand-300 bg-white"
                )}
              >
                <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0 font-bold text-brand-700">
                  {s.first_name[0]}
                  {s.last_name[0]}
                </div>
                <div className="flex-1">
                  <p className="font-bold text-gray-900">
                    {s.first_name} {s.last_name}
                  </p>
                  {s.title && <p className="text-xs text-gray-500 mt-0.5">{s.title}</p>}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 3: Select Date & Time */}
      {step === "datetime" && selectedService && (
        <div className="space-y-6">
          <button
            onClick={() => setStep("staff")}
            className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-gray-900 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" /> Back to Specialist
          </button>

          <h2 className="text-xl font-bold text-gray-900">Select Date & Time</h2>

          {/* Date Picker Carousel */}
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2.5">
              Available Dates
            </label>
            <div className="flex gap-2.5 overflow-x-auto pb-3 scrollbar-none">
              {Array.from({ length: 14 }).map((_, i) => {
                const d = addDays(new Date(), i);
                const isSelected =
                  format(d, "yyyy-MM-dd") === format(selectedDate, "yyyy-MM-dd");
                return (
                  <button
                    key={i}
                    onClick={() => {
                      setSelectedDate(d);
                      setSelectedSlot(null);
                    }}
                    className={cn(
                      "flex flex-col items-center justify-center min-w-[68px] py-3.5 px-3 rounded-2xl border transition-all flex-shrink-0 shadow-sm",
                      isSelected
                        ? "bg-brand-600 border-brand-600 text-white shadow-md shadow-brand-200 scale-105"
                        : "bg-white border-gray-200 text-gray-700 hover:border-brand-300"
                    )}
                  >
                    <span className="text-xs font-semibold uppercase">{format(d, "EEE")}</span>
                    <span className="text-xl font-extrabold leading-tight my-0.5">
                      {format(d, "d")}
                    </span>
                    <span className="text-xs font-medium opacity-80">{format(d, "MMM")}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Time Slots Grid */}
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2.5">
              Available Slots for {format(selectedDate, "MMMM d, yyyy")}
            </label>

            {isLoadingSlots ? (
              <div className="flex flex-col items-center justify-center py-16">
                <Loader2 className="w-8 h-8 animate-spin text-brand-600 mb-2" />
                <p className="text-xs text-gray-400">Loading open slots...</p>
              </div>
            ) : availability?.slots.length === 0 ? (
              <div className="bg-white rounded-2xl border border-gray-200 text-center py-12 px-4">
                <Calendar className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                <p className="font-semibold text-gray-900 text-sm">No available slots</p>
                <p className="text-xs text-gray-400 mt-1">
                  Please pick another date or select a different specialist.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-3 sm:grid-cols-4 gap-2.5">
                {availability?.slots.map((slot, i) => {
                  const isSelected = selectedSlot?.start_time === slot.start_time;
                  return (
                    <button
                      key={i}
                      onClick={() => setSelectedSlot(slot)}
                      className={cn(
                        "py-3 px-3 rounded-xl border text-sm font-semibold transition-all shadow-sm",
                        isSelected
                          ? "bg-brand-600 border-brand-600 text-white shadow-brand-200"
                          : "bg-white border-gray-200 text-gray-800 hover:border-brand-300 hover:bg-gray-50"
                      )}
                    >
                      {formatTime(slot.start_time)}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Step 4: Confirm Booking */}
      {step === "confirm" && selectedService && selectedSlot && (
        <div className="space-y-6">
          <button
            onClick={() => setStep("datetime")}
            className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-gray-900 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" /> Back to Time Selection
          </button>

          <h2 className="text-xl font-bold text-gray-900">Review & Confirm</h2>

          {/* Appointment Details Card */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4 shadow-sm">
            <div className="flex justify-between items-center text-sm border-b border-gray-100 pb-3">
              <span className="text-gray-500 font-medium">Service</span>
              <span className="font-bold text-gray-900">{selectedService.name}</span>
            </div>
            <div className="flex justify-between items-center text-sm border-b border-gray-100 pb-3">
              <span className="text-gray-500 font-medium">Duration</span>
              <span className="font-semibold text-gray-900">
                {durationLabel(selectedService.duration_minutes)}
              </span>
            </div>
            <div className="flex justify-between items-center text-sm border-b border-gray-100 pb-3">
              <span className="text-gray-500 font-medium">Date & Time</span>
              <span className="font-semibold text-gray-900">
                {format(selectedDate, "EEE, MMM d, yyyy")} at {formatTime(selectedSlot.start_time)}
              </span>
            </div>
            <div className="flex justify-between items-center text-sm border-b border-gray-100 pb-3">
              <span className="text-gray-500 font-medium">Specialist</span>
              <span className="font-semibold text-gray-900">
                {selectedSlot.staff_name || "Assigned Specialist"}
              </span>
            </div>

            {/* Price breakdown */}
            <div className="pt-2 space-y-2">
              <div className="flex justify-between items-center text-sm font-semibold text-gray-700">
                <span>Service Total</span>
                <span>{formatCurrency(price)}</span>
              </div>

              {depositRequired && (
                <>
                  <div className="flex justify-between items-center text-sm font-bold text-brand-600 bg-brand-50 p-2.5 rounded-xl">
                    <span className="flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4" /> Deposit Required ({depositPercentage}%)
                    </span>
                    <span>{formatCurrency(depositAmount)}</span>
                  </div>
                  <div className="flex justify-between items-center text-xs text-gray-500 px-1">
                    <span>Payable at salon during visit</span>
                    <span>{formatCurrency(balanceDue)}</span>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Notes input */}
          <div className="bg-white rounded-2xl border border-gray-200 p-5 space-y-2 shadow-sm">
            <label className="block text-xs font-semibold text-gray-700">
              Special requests or notes (optional):
            </label>
            <textarea
              value={customerNotes}
              onChange={(e) => setCustomerNotes(e.target.value)}
              rows={2}
              placeholder="e.g. Any allergies, preferences, or hair length notes..."
              className="w-full text-sm p-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          {/* Cancellation Policy Banner */}
          <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-2xl border border-gray-200 text-xs text-gray-600">
            <Info className="w-4 h-4 text-gray-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-gray-800">Cancellation Policy</p>
              <p className="mt-0.5">
                Free cancellation up to {business?.cancellation_hours ?? 24} hours before your
                appointment.
                {depositRequired && " Late cancellations may forfeit the deposit."}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Sticky Bottom Action Bar (Mobile & Desktop) */}
      <div className="fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur border-t border-gray-200 p-4 z-30 shadow-lg">
        <div className="max-w-3xl mx-auto flex items-center justify-between gap-4">
          <div>
            <p className="text-xs text-gray-500 font-medium">Total</p>
            <p className="text-lg font-black text-gray-900">
              {selectedService ? formatCurrency(selectedService.price) : "—"}
            </p>
          </div>

          {step === "datetime" && (
            <button
              onClick={() => setStep("confirm")}
              disabled={!selectedSlot}
              className="px-6 py-3 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-bold text-sm rounded-xl transition-colors shadow-md shadow-brand-200"
            >
              Continue
            </button>
          )}

          {step === "confirm" && (
            <button
              onClick={handleBook}
              disabled={isBooking}
              className="flex items-center gap-2 px-8 py-3.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white font-bold text-sm rounded-xl transition-all shadow-md shadow-brand-200"
            >
              {isBooking ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Confirming...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" /> Confirm Booking
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
