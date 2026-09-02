"use client";

import { useEffect, useState, useCallback } from "react";
import {
  CheckCircle, XCircle, Eye, Clock, AlertCircle,
  Building2, Loader2, ChevronRight, Search,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatDate, cn } from "@/lib/utils";
import { toast } from "sonner";

interface VerificationItem {
  id: string;
  name: string;
  category: string;
  owner_id: string;
  verification_status: string;
  verification_submitted_at: string | null;
  verification_notes: string | null;
}

interface VerificationStatusResponse {
  business_id: string;
  verification_status: string;
  is_verified: boolean;
  verification_reviewed_at: string | null;
  verification_rejection_reason: string | null;
}

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  NOT_APPLIED:  { label: "Not Applied",   color: "bg-gray-100 text-gray-600",     icon: AlertCircle },
  APPLIED:      { label: "Applied",       color: "bg-blue-100 text-blue-700",      icon: Clock },
  UNDER_REVIEW: { label: "Under Review",  color: "bg-yellow-100 text-yellow-700",  icon: Eye },
  APPROVED:     { label: "Approved",      color: "bg-green-100 text-green-700",    icon: CheckCircle },
  REJECTED:     { label: "Rejected",      color: "bg-red-100 text-red-700",        icon: XCircle },
};

export default function VerificationQueuePage() {
  const [queue, setQueue] = useState<VerificationItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selected, setSelected] = useState<VerificationItem | null>(null);
  const [action, setAction] = useState<"approve" | "reject" | "review" | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [processing, setProcessing] = useState(false);
  const [filter, setFilter] = useState<"all" | "APPLIED" | "UNDER_REVIEW">("all");

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await api.get<VerificationItem[]>("/admin/verification/queue");
      setQueue(res);
    } catch { setQueue([]); }
    finally { setIsLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleAction = async () => {
    if (!selected) return;
    setProcessing(true);
    try {
      if (action === "review") {
        await api.post(`/admin/verification/${selected.id}/start-review`);
        toast.success(`${selected.name} moved to Under Review`);
      } else if (action === "approve") {
        await api.post(`/admin/verification/${selected.id}/approve`);
        toast.success(`${selected.name} approved — business is now active`);
      } else if (action === "reject") {
        if (!rejectReason.trim() || rejectReason.length < 10) {
          toast.error("Please provide a detailed rejection reason (min 10 characters)");
          return;
        }
        await api.post(`/admin/verification/${selected.id}/reject`, {
          reason: rejectReason.trim(),
        });
        toast.success(`${selected.name} rejected`);
      }
      setSelected(null);
      setAction(null);
      setRejectReason("");
      load();
    } catch (err: any) {
      toast.error(err.message ?? "Action failed");
    } finally {
      setProcessing(false);
    }
  };

  const filtered = filter === "all"
    ? queue
    : queue.filter(b => b.verification_status === filter);

  const queueCounts = {
    all: queue.length,
    APPLIED: queue.filter(b => b.verification_status === "APPLIED").length,
    UNDER_REVIEW: queue.filter(b => b.verification_status === "UNDER_REVIEW").length,
  };

  return (
    <div>
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Verification Queue</h1>
        <p className="text-gray-500 text-sm mt-1">
          Review and approve business verification applications
        </p>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-5 overflow-x-auto pb-1">
        {([
          { key: "all",          label: "All Applications" },
          { key: "APPLIED",      label: "Awaiting Review" },
          { key: "UNDER_REVIEW", label: "Under Review" },
        ] as const).map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors border",
              filter === key
                ? "bg-brand-600 text-white border-brand-600"
                : "bg-white text-gray-600 border-gray-300 hover:border-brand-400"
            )}
          >
            {label}
            <span className={cn(
              "text-xs px-1.5 py-0.5 rounded-full font-semibold",
              filter === key ? "bg-white/20 text-white" : "bg-gray-100 text-gray-600"
            )}>
              {queueCounts[key]}
            </span>
          </button>
        ))}
      </div>

      {/* Applications list */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center py-16">
            <Loader2 className="w-6 h-6 animate-spin text-brand-600" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16">
            <CheckCircle className="w-12 h-12 text-gray-200 mx-auto mb-3" />
            <p className="font-medium text-gray-900">No applications in queue</p>
            <p className="text-sm text-gray-400 mt-1">
              All verification applications have been processed.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filtered.map((item) => {
              const statusCfg = STATUS_CONFIG[item.verification_status] ?? STATUS_CONFIG.NOT_APPLIED;
              const StatusIcon = statusCfg.icon;
              return (
                <div
                  key={item.id}
                  className={cn(
                    "flex items-center gap-4 px-5 py-4 hover:bg-gray-50 transition-colors",
                    selected?.id === item.id && "bg-brand-50"
                  )}
                >
                  {/* Business icon */}
                  <div className="w-10 h-10 bg-brand-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Building2 className="w-5 h-5 text-brand-600" />
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-900 text-sm truncate">{item.name}</p>
                    <div className="flex items-center gap-3 mt-0.5 text-xs text-gray-500">
                      <span className="capitalize">{item.category?.toLowerCase()}</span>
                      {item.verification_submitted_at && (
                        <span>Submitted {formatDate(item.verification_submitted_at)}</span>
                      )}
                    </div>
                    {item.verification_notes && (
                      <p className="text-xs text-gray-400 mt-1 line-clamp-1 italic">
                        "{item.verification_notes}"
                      </p>
                    )}
                  </div>

                  {/* Status badge */}
                  <span className={cn(
                    "text-xs font-medium px-2.5 py-1 rounded-full flex items-center gap-1.5 flex-shrink-0",
                    statusCfg.color
                  )}>
                    <StatusIcon className="w-3.5 h-3.5" />
                    {statusCfg.label}
                  </span>

                  {/* Actions */}
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    {item.verification_status === "APPLIED" && (
                      <button
                        onClick={() => { setSelected(item); setAction("review"); }}
                        className="px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
                      >
                        Start Review
                      </button>
                    )}
                    {item.verification_status === "UNDER_REVIEW" && (
                      <>
                        <button
                          onClick={() => { setSelected(item); setAction("approve"); }}
                          className="px-3 py-1.5 text-xs font-semibold text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => { setSelected(item); setAction("reject"); setRejectReason(""); }}
                          className="px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
                        >
                          Reject
                        </button>
                      </>
                    )}
                    {item.verification_status === "APPLIED" && (
                      <>
                        <button
                          onClick={() => { setSelected(item); setAction("approve"); }}
                          className="px-3 py-1.5 text-xs font-semibold text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => { setSelected(item); setAction("reject"); setRejectReason(""); }}
                          className="px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
                        >
                          Reject
                        </button>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Confirmation modal */}
      {selected && action && (
        <div className="fixed inset-0 bg-black/50 flex items-start sm:items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto my-8 sm:my-0">
            {/* Header */}
            <div className={cn(
              "px-6 py-5 rounded-t-2xl border-b sticky top-0 bg-white z-10",
              action === "approve" ? "bg-green-50 border-green-100" :
              action === "reject"  ? "bg-red-50 border-red-100" :
              "bg-blue-50 border-blue-100"
            )}>
              <div className="flex items-center gap-3">
                {action === "approve" && <CheckCircle className="w-5 h-5 text-green-600" />}
                {action === "reject"  && <XCircle className="w-5 h-5 text-red-600" />}
                {action === "review"  && <Eye className="w-5 h-5 text-blue-600" />}
                <h2 className="font-bold text-gray-900">
                  {action === "approve" ? "Approve Business" :
                   action === "reject"  ? "Reject Application" :
                   "Start Review"}
                </h2>
              </div>
              <p className="text-sm text-gray-600 mt-1.5">
                <strong>{selected.name}</strong>
              </p>
            </div>

            <div className="px-6 py-5">
              {action === "approve" && (
                <div className="space-y-3">
                  <p className="text-sm text-gray-600">
                    Approving this business will:
                  </p>
                  <ul className="text-sm text-gray-600 space-y-1.5">
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                      Set status to <strong>ACTIVE</strong>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                      Add a <strong>Verified</strong> badge to their profile
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                      Allow them to appear in the marketplace
                    </li>
                  </ul>
                </div>
              )}

              {action === "reject" && (
                <div className="space-y-3">
                  <p className="text-sm text-gray-600">
                    The rejection reason will be shown to the business owner so they can
                    correct issues and reapply. Please be specific.
                  </p>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      Rejection reason <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                      rows={4}
                      placeholder="e.g. Business registration documents are missing. Please upload a valid business license and GST certificate..."
                      className={cn(
                        "w-full px-3 py-2.5 rounded-lg border text-sm resize-none focus:outline-none focus:ring-2 focus:ring-red-400",
                        rejectReason.length > 0 && rejectReason.length < 10
                          ? "border-red-400 bg-red-50"
                          : "border-gray-300"
                      )}
                    />
                    <p className="text-xs text-gray-400 mt-1">
                      {rejectReason.length}/1000 characters (min 10)
                    </p>
                  </div>
                </div>
              )}

              {action === "review" && (
                <p className="text-sm text-gray-600">
                  This will move the application to <strong>Under Review</strong> status,
                  indicating that an admin is actively reviewing the application.
                </p>
              )}
            </div>

            <div className="px-6 pb-5 flex gap-3">
              <button
                onClick={() => { setSelected(null); setAction(null); setRejectReason(""); }}
                className="flex-1 py-2.5 rounded-xl border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAction}
                disabled={processing || (action === "reject" && rejectReason.length < 10)}
                className={cn(
                  "flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold text-white transition-colors disabled:opacity-50",
                  action === "approve" ? "bg-green-600 hover:bg-green-700" :
                  action === "reject"  ? "bg-red-600 hover:bg-red-700" :
                  "bg-blue-600 hover:bg-blue-700"
                )}
              >
                {processing && <Loader2 className="w-4 h-4 animate-spin" />}
                {action === "approve" ? "Approve business" :
                 action === "reject"  ? "Reject & notify owner" :
                 "Start reviewing"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
