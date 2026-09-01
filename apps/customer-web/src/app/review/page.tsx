"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Star, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { Header } from "@/components/layout/Header";

export default function ReviewPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const appointmentId = searchParams.get("appointment_id");
  const businessId = searchParams.get("business_id");

  const [rating, setRating] = useState(0);
  const [hovered, setHovered] = useState(0);
  const [comment, setComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rating) { toast.error("Please select a rating"); return; }
    if (!businessId) { toast.error("Missing business information"); return; }

    setIsSubmitting(true);
    try {
      await api.post("/reviews", {
        business_id: businessId,
        appointment_id: appointmentId || undefined,
        rating,
        comment: comment.trim() || undefined,
      });
      toast.success("Thank you for your review!");
      router.push(appointmentId ? `/bookings/${appointmentId}` : "/bookings");
    } catch (err: any) {
      toast.error(err.message ?? "Could not submit review");
    } finally {
      setIsSubmitting(false);
    }
  };

  const LABELS = ["", "Poor", "Fair", "Good", "Very good", "Excellent"];

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />
      <main className="flex-1 max-w-lg mx-auto w-full px-4 py-12">
        <div className="bg-white rounded-2xl border border-gray-200 p-8">
          <div className="text-center mb-8">
            <div className="w-14 h-14 bg-brand-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Star className="w-7 h-7 text-brand-600" />
            </div>
            <h1 className="text-xl font-bold text-gray-900">How was your experience?</h1>
            <p className="text-gray-500 text-sm mt-1">Your feedback helps others discover great businesses</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Star rating */}
            <div className="text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    onMouseEnter={() => setHovered(star)}
                    onMouseLeave={() => setHovered(0)}
                    className="focus:outline-none transition-transform hover:scale-110"
                    aria-label={`Rate ${star} star${star !== 1 ? "s" : ""}`}
                  >
                    <Star
                      className={cn(
                        "w-10 h-10 transition-colors",
                        (hovered || rating) >= star
                          ? "fill-yellow-400 text-yellow-400"
                          : "text-gray-300"
                      )}
                    />
                  </button>
                ))}
              </div>
              {(hovered || rating) > 0 && (
                <p className="text-sm font-medium text-gray-700">
                  {LABELS[hovered || rating]}
                </p>
              )}
            </div>

            {/* Comment */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Share your experience <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={4}
                maxLength={1000}
                className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
                placeholder="What did you love? What could be better?"
              />
              <p className="text-xs text-gray-400 text-right mt-1">{comment.length}/1000</p>
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !rating}
              className="w-full flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition-colors"
            >
              {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              Submit review
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
