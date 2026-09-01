"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Star, MessageSquare, Reply, CheckCircle2,
  Filter, Loader2, Sparkles, AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import { formatDate, cn } from "@/lib/utils";
import { toast } from "sonner";

interface Review {
  id: string;
  business_id: string;
  customer_id: string;
  appointment_id: string | null;
  rating: number;
  comment: string | null;
  is_published: boolean;
  owner_reply: string | null;
  created_at: string;
}

interface ReviewStats {
  average_rating: number;
  total_reviews: number;
}

export default function ReviewsPage() {
  const { business } = useAuth();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedRating, setSelectedRating] = useState<number | null>(null);
  const [replyFilter, setReplyFilter] = useState<"all" | "unreplied" | "replied">("all");

  // Replying state
  const [replyingReviewId, setReplyingReviewId] = useState<string | null>(null);
  const [replyText, setReplyText] = useState("");
  const [isSubmittingReply, setIsSubmittingReply] = useState(false);

  const loadData = useCallback(async () => {
    if (!business) return;
    setIsLoading(true);
    try {
      const [reviewList, statData] = await Promise.all([
        api.get<Review[]>(`/businesses/${business.id}/reviews?page=1&page_size=50`),
        api.get<ReviewStats>(`/businesses/${business.id}/reviews/stats`),
      ]);
      setReviews(reviewList);
      setStats(statData);
    } catch {
      toast.error("Failed to load reviews");
    } finally {
      setIsLoading(false);
    }
  }, [business]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleStartReply = (review: Review) => {
    setReplyingReviewId(review.id);
    setReplyText(review.owner_reply || "");
  };

  const handleCancelReply = () => {
    setReplyingReviewId(null);
    setReplyText("");
  };

  const handleSubmitReply = async (reviewId: string) => {
    if (!business || !replyText.trim()) return;
    setIsSubmittingReply(true);
    try {
      await api.post(`/businesses/${business.id}/reviews/${reviewId}/reply`, {
        reply: replyText.trim(),
      });
      toast.success("Reply saved successfully");
      setReplyingReviewId(null);
      setReplyText("");
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to submit reply");
    } finally {
      setIsSubmittingReply(false);
    }
  };

  const filteredReviews = reviews.filter((r) => {
    if (selectedRating !== null && r.rating !== selectedRating) return false;
    if (replyFilter === "unreplied" && r.owner_reply) return false;
    if (replyFilter === "replied" && !r.owner_reply) return false;
    return true;
  });

  // Calculate rating distribution
  const ratingCounts = [5, 4, 3, 2, 1].map((stars) => ({
    stars,
    count: reviews.filter((r) => r.rating === stars).length,
    percentage: reviews.length > 0 ? (reviews.filter((r) => r.rating === stars).length / reviews.length) * 100 : 0,
  }));

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-brand-600" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reviews & Ratings</h1>
        <p className="text-gray-500 text-sm mt-1">
          Monitor feedback from your clients and manage public responses
        </p>
      </div>

      {/* Stats and Rating Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Overall Rating Card */}
        <div className="bg-white p-6 rounded-2xl border border-gray-200 flex flex-col justify-center items-center text-center">
          <span className="text-5xl font-black text-gray-900 mb-2">
            {stats?.average_rating ? stats.average_rating.toFixed(1) : "0.0"}
          </span>
          <div className="flex gap-1 mb-2 text-amber-400">
            {[1, 2, 3, 4, 5].map((s) => (
              <Star
                key={s}
                className={cn(
                  "w-5 h-5",
                  stats && stats.average_rating >= s
                    ? "fill-amber-400 text-amber-400"
                    : stats && stats.average_rating >= s - 0.5
                    ? "fill-amber-200 text-amber-400"
                    : "text-gray-200"
                )}
              />
            ))}
          </div>
          <p className="text-sm font-medium text-gray-500">
            Based on {stats?.total_reviews ?? 0} reviews
          </p>
        </div>

        {/* Rating Breakdown Bars */}
        <div className="md:col-span-2 bg-white p-6 rounded-2xl border border-gray-200 space-y-2.5">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">Rating Breakdown</h2>
          {ratingCounts.map(({ stars, count, percentage }) => (
            <button
              key={stars}
              onClick={() => setSelectedRating(selectedRating === stars ? null : stars)}
              className={cn(
                "w-full flex items-center gap-3 p-1.5 rounded-lg text-xs font-medium transition-colors hover:bg-gray-50",
                selectedRating === stars && "bg-brand-50 text-brand-700"
              )}
            >
              <div className="flex items-center gap-1 w-12 text-gray-700 font-semibold">
                <span>{stars}</span>
                <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
              </div>
              <div className="flex-1 h-2.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-amber-400 rounded-full transition-all duration-500"
                  style={{ width: `${percentage}%` }}
                />
              </div>
              <span className="w-10 text-right text-gray-500 font-medium">{count}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-4 rounded-xl border border-gray-200">
        <div className="flex items-center gap-2 overflow-x-auto">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider mr-1 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5" /> Rating:
          </span>
          <button
            onClick={() => setSelectedRating(null)}
            className={cn(
              "px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors",
              selectedRating === null
                ? "bg-brand-600 text-white border-brand-600"
                : "bg-white text-gray-600 border-gray-200 hover:border-gray-300"
            )}
          >
            All Ratings
          </button>
          {[5, 4, 3, 2, 1].map((rating) => (
            <button
              key={rating}
              onClick={() => setSelectedRating(selectedRating === rating ? null : rating)}
              className={cn(
                "flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors",
                selectedRating === rating
                  ? "bg-brand-600 text-white border-brand-600"
                  : "bg-white text-gray-600 border-gray-200 hover:border-gray-300"
              )}
            >
              <span>{rating}</span>
              <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1 text-xs">
          <button
            onClick={() => setReplyFilter("all")}
            className={cn(
              "px-3 py-1.5 rounded-lg font-medium transition-colors",
              replyFilter === "all" ? "bg-gray-100 text-gray-900 font-semibold" : "text-gray-500 hover:text-gray-900"
            )}
          >
            All ({reviews.length})
          </button>
          <button
            onClick={() => setReplyFilter("unreplied")}
            className={cn(
              "px-3 py-1.5 rounded-lg font-medium transition-colors",
              replyFilter === "unreplied" ? "bg-amber-100 text-amber-900 font-semibold" : "text-gray-500 hover:text-gray-900"
            )}
          >
            Unreplied ({reviews.filter((r) => !r.owner_reply).length})
          </button>
          <button
            onClick={() => setReplyFilter("replied")}
            className={cn(
              "px-3 py-1.5 rounded-lg font-medium transition-colors",
              replyFilter === "replied" ? "bg-green-100 text-green-900 font-semibold" : "text-gray-500 hover:text-gray-900"
            )}
          >
            Replied ({reviews.filter((r) => Boolean(r.owner_reply)).length})
          </button>
        </div>
      </div>

      {/* Reviews List */}
      {filteredReviews.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-200 text-center py-16 px-4">
          <Sparkles className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-gray-900">No reviews found</h3>
          <p className="text-sm text-gray-400 mt-1">
            {reviews.length === 0
              ? "Your business doesn't have any customer reviews yet."
              : "No reviews match the selected filter criteria."}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredReviews.map((review) => (
            <div
              key={review.id}
              className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4 shadow-sm hover:border-gray-300 transition-colors"
            >
              {/* Review Header */}
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-1 mb-1">
                    {[1, 2, 3, 4, 5].map((s) => (
                      <Star
                        key={s}
                        className={cn(
                          "w-4 h-4",
                          review.rating >= s ? "fill-amber-400 text-amber-400" : "text-gray-200"
                        )}
                      />
                    ))}
                    <span className="text-sm font-bold text-gray-900 ml-2">
                      {review.rating}.0
                    </span>
                  </div>
                  <p className="text-xs text-gray-400">
                    Reviewed on {formatDate(review.created_at)}
                  </p>
                </div>

                {!review.owner_reply && replyingReviewId !== review.id && (
                  <button
                    onClick={() => handleStartReply(review)}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-brand-50 text-brand-700 hover:bg-brand-100 transition-colors"
                  >
                    <Reply className="w-3.5 h-3.5" />
                    Reply
                  </button>
                )}
              </div>

              {/* Review Comment */}
              <p className="text-sm text-gray-700 leading-relaxed">
                {review.comment || <span className="italic text-gray-400">No written comment provided.</span>}
              </p>

              {/* Existing Owner Reply */}
              {review.owner_reply && replyingReviewId !== review.id && (
                <div className="bg-gray-50 rounded-xl p-4 border border-gray-200 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 bg-brand-600 rounded-md flex items-center justify-center text-white text-xs font-bold">
                        {business?.name[0] || "B"}
                      </div>
                      <span className="text-xs font-semibold text-gray-900">
                        Response from {business?.name || "Business"}
                      </span>
                    </div>
                    <button
                      onClick={() => handleStartReply(review)}
                      className="text-xs font-medium text-gray-500 hover:text-brand-600 transition-colors"
                    >
                      Edit
                    </button>
                  </div>
                  <p className="text-xs text-gray-600 leading-relaxed pl-8">
                    {review.owner_reply}
                  </p>
                </div>
              )}

              {/* Reply Form */}
              {replyingReviewId === review.id && (
                <div className="bg-brand-50/50 rounded-xl p-4 border border-brand-100 space-y-3">
                  <label className="block text-xs font-semibold text-gray-700">
                    Your response (will be publicly visible on your profile):
                  </label>
                  <textarea
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    rows={3}
                    placeholder="Thank the customer for their feedback and share your thoughts..."
                    className="w-full p-3 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
                  />
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={handleCancelReply}
                      className="px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => handleSubmitReply(review.id)}
                      disabled={isSubmittingReply || !replyText.trim()}
                      className="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 disabled:opacity-50 rounded-lg transition-colors"
                    >
                      {isSubmittingReply && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                      Publish Response
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
