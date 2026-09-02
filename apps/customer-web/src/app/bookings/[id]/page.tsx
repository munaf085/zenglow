"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Calendar, Clock, User, ChevronLeft,
  CheckCircle, XCircle, AlertCircle, Loader2, Star,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import type { Appointment } from "@zenglow/types";
import { formatDate, formatTime, formatCurrency, durationLabel, cn } from "@/lib/utils";
import { toast } from "sonner";
import { Header } from "@/components/layout/Header";

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  CONFIRMED:   { label: "Confirmed",   color: "text-green-700 bg-green-50 border-green-200",   icon: CheckCircle },
  PENDING:     { label: "Pending",     color: "text-yellow-700 bg-yellow-50 border-yellow-200", icon: AlertCircle },
  IN_PROGRESS: { label: "In Progress", color: "text-blue-700 bg-blue-50 border-blue-200",      icon: Clock },
  COMPLETED:   { label: "Completed",   color: "text-gray-700 bg-gray-50 border-gray-200",      icon: CheckCircle },
  CANCELLED:   { label: "Cancelled",   color: "text-red-700 bg-red-50 border-red-200",          icon: XCircle },
  NO_SHOW:     { label: "No Show",     color: "text-orange-700 bg-orange-50 border-orange-200", icon: XCircle },
  RESCHEDULED: { label: "Rescheduled", color: "text-purple-700 bg-purple-50 border-purple-200", icon: AlertCircle },
};

export default function BookingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const [appointment, setAppointment] = useState<Appointment | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCancelling, setIsCancelling] = useState(false);
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [cancelReason, setCancelReason] = useState("");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push(`/login?next=/bookings/${id}`);
    }
  }, [authLoading, isAuthenticated, id, router]);

  useEffect(() => {
    if (!isAuthenticated || !id) return;
    api
      .get<Appointment>(`/bookings/${id}`)
      .then(setAppointment)
      .catch(() => router.push("/bookings"))
      .finally(() => setIsLoading(false));
  }, [id, isAuthenticated, router]);

  const handleCancel = async () => {
    if (!appointment) return;
    setIsCancelling(true);
    try {
      const updated = await api.post<Appointment>(`/bookings/${appointment.id}/cancel`, {
        reason: cancelReason || undefined,
      });
      setAppointment(updated);
      setShowCancelDialog(false);
      toast.success("Appointment cancelled");
    } catch (err: any) {
      toast.error(err.message ?? "Could not cancel appointment");
    } finally {
      setIsCancelling(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-brand-600" />
        </div>
      </div>
    );
  }

  if (!appointment) return null;

  const statusCfg = STATUS_CONFIG[appointment.status] ?? STATUS_CONFIG.PENDING;
  const StatusIcon = statusCfg.icon;
  const canCancel = ["CONFIRMED", "PENDING"].includes(appointment.status);
  const isPast = new Date(appointment.start_time) < new Date();

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />
      <main className="flex-1 max-w-2xl mx-auto w-full px-4 py-8">
        {/* Back */}
        <Link
          href="/bookings"
          className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-6"
        >
          <ChevronLeft className="w-4 h-4" /> Back to bookings
        </Link>

        {/* Status banner */}
        <div className={cn("flex items-center gap-3 p-4 rounded-xl border mb-6", statusCfg.color)}>
          <StatusIcon className="w-5 h-5 flex-shrink-0" />
          <div>
            <p className="font-semibold">{statusCfg.label}</p>
            {appointment.status === "CONFIRMED" && !isPast && (
              <p className="text-sm opacity-80">Your appointment is confirmed!</p>
            )}
          </div>
        </div>

        {/* Details */}
        <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden mb-4">
          <div className="px-6 py-5 border-b border-gray-100">
            <h1 className="text-lg font-bold text-gray-900">Appointment Details</h1>
          </div>

          <div className="px-6 py-5 space-y-4">
            {/* Date & Time */}
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 bg-brand-50 rounded-lg flex items-center justify-center flex-shrink-0">
                <Calendar className="w-4 h-4 text-brand-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900 text-sm">{formatDate(appointment.start_time)}</p>
                <p className="text-sm text-gray-500">
                  {formatTime(appointment.start_time)} – {formatTime(appointment.end_time)}
                </p>
              </div>
            </div>

            {/* Services */}
            {appointment.items && appointment.items.length > 0 && (
              <div className="border-t border-gray-100 pt-4">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
                  Services
                </p>
                <div className="space-y-3">
                  {appointment.items.map((item) => (
                    <div key={item.id} className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{item.service_name}</p>
                        <div className="flex items-center gap-2 mt-0.5 text-xs text-gray-500">
                          <Clock className="w-3.5 h-3.5" />
                          <span>{durationLabel(item.duration_minutes)}</span>
                        </div>
                      </div>
                      <span className="text-sm font-medium text-gray-900">
                        {formatCurrency(item.price)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Price summary */}
            <div className="border-t border-gray-100 pt-4 space-y-2">
              <div className="flex justify-between text-sm text-gray-500">
                <span>Subtotal</span>
                <span>{formatCurrency(appointment.subtotal)}</span>
              </div>
              {appointment.tax_amount > 0 && (
                <div className="flex justify-between text-sm text-gray-500">
                  <span>Tax</span>
                  <span>{formatCurrency(appointment.tax_amount)}</span>
                </div>
              )}
              <div className="flex justify-between text-sm font-bold text-gray-900 pt-2 border-t border-gray-100">
                <span>Total</span>
                <span>{formatCurrency(appointment.total_amount)}</span>
              </div>
            </div>

            {/* Customer notes */}
            {appointment.customer_notes && (
              <div className="border-t border-gray-100 pt-4">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">
                  Your notes
                </p>
                <p className="text-sm text-gray-600">{appointment.customer_notes}</p>
              </div>
            )}

            {/* Booking reference */}
            <div className="border-t border-gray-100 pt-4">
              <p className="text-xs text-gray-400">Booking reference</p>
              <p className="text-xs font-mono text-gray-500 mt-0.5 break-all">{appointment.id}</p>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-3">
          {canCancel && !isPast && (
            <button
              onClick={() => setShowCancelDialog(true)}
              className="w-full py-3 rounded-xl border border-red-300 text-red-600 text-sm font-medium hover:bg-red-50 transition-colors"
            >
              Cancel appointment
            </button>
          )}

          {appointment.status === "COMPLETED" && (
            <Link
              href={`/review?appointment_id=${appointment.id}&business_id=${appointment.business_id}`}
              className="flex items-center justify-center gap-2 w-full bg-brand-600 hover:bg-brand-700 text-white font-semibold py-3 rounded-xl text-sm transition-colors"
            >
              <Star className="w-4 h-4" />
              Leave a review
            </Link>
          )}
        </div>
      </main>

      {/* Cancel dialog */}
      {showCancelDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-start sm:items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm my-8 sm:my-0">
            <div className="px-6 py-5 border-b border-gray-200">
              <h2 className="text-base font-bold text-gray-900">Cancel appointment?</h2>
              <p className="text-sm text-gray-500 mt-1">This cannot be undone.</p>
            </div>
            <div className="px-6 py-4">
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Reason <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <textarea
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
                placeholder="Let the business know why..."
              />
            </div>
            <div className="px-6 pb-5 flex gap-3">
              <button
                onClick={() => setShowCancelDialog(false)}
                className="flex-1 py-2.5 rounded-lg border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Keep it
              </button>
              <button
                onClick={handleCancel}
                disabled={isCancelling}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 disabled:opacity-60 text-sm font-semibold text-white"
              >
                {isCancelling && <Loader2 className="w-4 h-4 animate-spin" />}
                Confirm cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
