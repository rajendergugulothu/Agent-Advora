"use client";

import { useEffect, useState } from "react";
import { api, type Draft, type DraftList } from "@/lib/api";
import { format } from "date-fns";
import { IconDocument, IconSparkles } from "@/components/NavIcons";

const STATUS_FILTERS = ["all", "pending", "posted", "rejected", "image_failed", "post_failed"] as const;
type StatusFilter = typeof STATUS_FILTERS[number];

const STATUS_LABELS: Record<StatusFilter, string> = {
  all:          "All",
  pending:      "Pending",
  posted:       "Posted",
  rejected:     "Rejected",
  image_failed: "Image failed",
  post_failed:  "Post failed",
};

export default function DraftsPage() {
  const [drafts, setDrafts] = useState<DraftList | null>(null);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [triggered, setTriggered] = useState(false);

  useEffect(() => {
    setLoading(true);
    api
      .listDrafts(page, 20, statusFilter === "all" ? undefined : statusFilter)
      .then(setDrafts)
      .finally(() => setLoading(false));
  }, [page, statusFilter]);

  async function handleTrigger() {
    setTriggering(true);
    await api.triggerGeneration();
    setTriggered(true);
    setTriggering(false);
    setTimeout(() => setTriggered(false), 4000);
  }

  const totalPages = drafts ? Math.ceil(drafts.total / 20) : 1;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title">Drafts</h1>
          <p className="page-subtitle">
            {drafts?.total ?? 0} total draft{(drafts?.total ?? 0) !== 1 ? "s" : ""}
          </p>
        </div>
        <button
          onClick={handleTrigger}
          disabled={triggering}
          className={`flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold transition-all duration-200 ${
            triggered
              ? "bg-green-500 text-white"
              : "btn-gradient"
          }`}
        >
          {triggered ? (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              Draft sent to WhatsApp!
            </>
          ) : triggering ? (
            <>
              <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Generating...
            </>
          ) : (
            <>
              <IconSparkles className="w-4 h-4" />
              Generate now
            </>
          )}
        </button>
      </div>

      {/* Status filter tabs */}
      <div className="flex gap-2 flex-wrap">
        {STATUS_FILTERS.map((s) => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s); setPage(1); }}
            className={`rounded-full px-3.5 py-1.5 text-xs font-medium transition-all duration-150 border ${
              statusFilter === s
                ? "bg-brand-600 text-white border-brand-600 shadow-sm"
                : "bg-white border-gray-200 text-gray-600 hover:border-brand-300 hover:text-brand-600"
            }`}
          >
            {STATUS_LABELS[s]}
          </button>
        ))}
      </div>

      {/* Draft list */}
      {loading ? (
        <div className="space-y-3 animate-pulse">
          {[0, 1, 2, 3, 4].map((i) => <div key={i} className="h-24 bg-gray-200 rounded-2xl" />)}
        </div>
      ) : drafts?.items.length === 0 ? (
        <EmptyState filter={statusFilter} />
      ) : (
        <div className="space-y-3">
          {drafts?.items.map((draft) => (
            <DraftCard key={draft.id} draft={draft} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="btn-secondary px-4 py-2 text-xs disabled:opacity-40"
          >
            ← Previous
          </button>
          <span className="text-sm text-gray-500 font-medium">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="btn-secondary px-4 py-2 text-xs disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}

function DraftCard({ draft }: { draft: Draft }) {
  const [expanded, setExpanded] = useState(false);
  const result = draft.post_result;
  const latest =
    result?.analytics.find((a) => a.fetch_stage === "7d") ??
    result?.analytics.find((a) => a.fetch_stage === "72h") ??
    result?.analytics.find((a) => a.fetch_stage === "24h");

  return (
    <div className={`card overflow-hidden transition-shadow duration-200 ${expanded ? "shadow-card-hover" : ""}`}>
      <button
        className="w-full text-left px-5 py-4 flex items-start justify-between gap-4 hover:bg-gray-50/50 transition-colors"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap mb-0.5">
            <span className="text-sm font-semibold text-navy-800 truncate">{draft.theme}</span>
            <span className="text-xs text-gray-400 bg-gray-100 rounded px-1.5 py-0.5">
              {draft.post_type === "carousel" ? "Carousel" : "Single image"}
            </span>
          </div>
          <p className="text-xs text-gray-500 truncate">{draft.hook}</p>
          <p className="text-xs text-gray-400 mt-1.5">
            {format(new Date(draft.created_at), "MMM d, yyyy · h:mm a")}
          </p>
        </div>
        <div className="flex flex-col items-end gap-2 shrink-0">
          <StatusBadge status={draft.status} />
          {latest && (
            <span className="text-xs text-brand-600 font-medium">
              {latest.engagement_rate?.toFixed(1)}% eng.
            </span>
          )}
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-gray-100 px-5 py-5 space-y-5 bg-gray-50/70">
          {/* Caption */}
          <div>
            <p className="section-title mb-2">Caption</p>
            <p className="text-sm text-gray-700 whitespace-pre-line leading-relaxed">{draft.caption}</p>
          </div>

          {/* Hashtags */}
          <div>
            <p className="section-title mb-2">Hashtags</p>
            <div className="flex flex-wrap gap-1.5">
              {draft.hashtags.split(" ").filter(Boolean).map((tag, i) => (
                <span key={i} className="text-xs bg-brand-50 text-brand-600 rounded-full px-2.5 py-1 font-medium">
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Performance */}
          {result && (
            <div>
              <p className="section-title mb-3">Performance</p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {result.analytics.map((a) => (
                  <div key={a.fetch_stage} className="bg-white rounded-xl border border-gray-100 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">{a.fetch_stage}</p>
                    </div>
                    <p className="text-lg font-bold text-navy-800">{a.impressions.toLocaleString()}</p>
                    <p className="text-xs text-gray-400">impressions</p>
                    <div className="mt-2 pt-2 border-t border-gray-100 flex gap-3 text-xs text-gray-500">
                      <span>{a.likes} likes</span>
                      <span>{a.saves} saves</span>
                    </div>
                    {a.engagement_rate != null && (
                      <p className="text-xs text-brand-600 font-semibold mt-1.5">
                        {a.engagement_rate.toFixed(2)}% engagement
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* View on Instagram */}
          {result?.instagram_url && (
            <a
              href={result.instagram_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-brand-600 font-semibold hover:underline"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
              </svg>
              View on Instagram
            </a>
          )}
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    posted:       "bg-green-50 text-green-700 border-green-100",
    pending:      "bg-amber-50 text-amber-700 border-amber-100",
    approved:     "bg-blue-50 text-blue-700 border-blue-100",
    posting:      "bg-blue-50 text-blue-600 border-blue-100",
    rejected:     "bg-gray-100 text-gray-500 border-gray-200",
    image_failed: "bg-red-50 text-red-600 border-red-100",
    post_failed:  "bg-red-50 text-red-600 border-red-100",
  };
  return (
    <span className={`badge border ${map[status] ?? "bg-gray-100 text-gray-500 border-gray-200"}`}>
      {status.replace("_", " ")}
    </span>
  );
}

function EmptyState({ filter }: { filter: string }) {
  return (
    <div className="card border-dashed px-8 py-16 text-center">
      <div className="w-12 h-12 rounded-2xl bg-brand-50 flex items-center justify-center mx-auto mb-3">
        <IconDocument className="w-6 h-6 text-brand-400" />
      </div>
      <p className="text-sm font-medium text-gray-500">
        {filter === "all" ? "No drafts yet" : `No ${filter.replace("_", " ")} drafts`}
      </p>
      <p className="text-xs text-gray-400 mt-1">
        {filter === "all"
          ? "Use \"Generate now\" to create your first draft."
          : "Try a different filter to see other drafts."}
      </p>
    </div>
  );
}
