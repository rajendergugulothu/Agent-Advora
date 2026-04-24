"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type UserProfile, type DraftList } from "@/lib/api";
import { IconSparkles, IconArrowRight, IconInstagram, IconChart, IconDocument } from "@/components/NavIcons";

export default function DashboardPage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [drafts, setDrafts] = useState<DraftList | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getProfile(), api.listDrafts(1, 5)])
      .then(([p, d]) => { setProfile(p); setDrafts(d); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Skeleton />;

  const posted = drafts?.items.filter((d) => d.status === "posted").length ?? 0;
  const pending = drafts?.items.filter((d) => d.status === "pending").length ?? 0;

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 17) return "Good afternoon";
    return "Good evening";
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="page-title">
            {greeting()}{profile?.full_name ? `, ${profile.full_name.split(" ")[0]}` : ""}
          </h1>
          <p className="page-subtitle">Here&apos;s your Advora account at a glance.</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span>Live data</span>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          label="Instagram"
          icon={<IconInstagram className="w-5 h-5" />}
          value={profile?.instagram_connected ? "Connected" : "Not connected"}
          sub={profile?.instagram_username ? `@${profile.instagram_username}` : "Connect in settings"}
          status={profile?.instagram_connected ? "success" : "warning"}
          href="/dashboard/connect"
        />
        <StatCard
          label="Daily scheduler"
          icon={<IconSparkles className="w-5 h-5" />}
          value={profile?.scheduler_active ? "Active" : "Paused"}
          sub={
            profile?.scheduler_active
              ? `${String(profile.post_time_hour).padStart(2, "0")}:${String(profile.post_time_minute).padStart(2, "0")} ${profile.timezone}`
              : "Enable in settings"
          }
          status={profile?.scheduler_active ? "success" : "neutral"}
          href="/dashboard/settings"
        />
        <StatCard
          label="This week"
          icon={<IconChart className="w-5 h-5" />}
          value={`${posted} posted`}
          sub={`${pending} pending approval`}
          status={posted > 0 ? "success" : "neutral"}
          href="/dashboard/analytics"
        />
      </div>

      {/* Quick action banner (if Instagram not connected) */}
      {!profile?.instagram_connected && (
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-600 via-brand-700 to-navy-800 p-6 sm:p-8">
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute -top-10 -right-10 w-48 h-48 rounded-full bg-white/5 blur-2xl" />
            <div className="absolute bottom-0 left-0 w-32 h-32 rounded-full bg-advora-teal/20 blur-xl" />
          </div>
          <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-5">
            <div>
              <p className="text-sm font-semibold text-brand-200 uppercase tracking-wide mb-1">
                Action required
              </p>
              <h3 className="text-xl font-bold text-white">Connect your Instagram account</h3>
              <p className="text-sm text-brand-200 mt-1">
                Required before posts can be published automatically.
              </p>
            </div>
            <Link
              href="/dashboard/connect"
              className="shrink-0 flex items-center gap-2 rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-brand-700 hover:bg-brand-50 transition-colors shadow-lg"
            >
              Connect now
              <IconArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      )}

      {/* Recent drafts */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-navy-800 flex items-center gap-2">
            <IconDocument className="w-4 h-4 text-gray-400" />
            Recent drafts
          </h2>
          <Link
            href="/dashboard/drafts"
            className="text-sm text-brand-600 font-medium hover:underline flex items-center gap-1"
          >
            View all <IconArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {drafts?.items.length === 0 ? (
          <EmptyDrafts />
        ) : (
          <div className="space-y-3">
            {drafts?.items.map((draft) => (
              <div
                key={draft.id}
                className="card-hover px-5 py-4 flex items-start justify-between gap-4 cursor-default"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-gray-900 truncate">{draft.theme}</p>
                  <p className="text-xs text-gray-500 mt-0.5 truncate">{draft.hook}</p>
                </div>
                <StatusBadge status={draft.status} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  label, icon, value, sub, status, href,
}: {
  label: string;
  icon: React.ReactNode;
  value: string;
  sub: string;
  status: "success" | "warning" | "neutral";
  href: string;
}) {
  const statusColors = {
    success: "text-green-600",
    warning: "text-amber-600",
    neutral: "text-gray-400",
  };
  const iconBg = {
    success: "bg-green-50 text-green-600",
    warning: "bg-amber-50 text-amber-600",
    neutral: "bg-gray-100 text-gray-500",
  };

  return (
    <Link href={href} className="card-hover p-5 block group">
      <div className="flex items-start justify-between mb-3">
        <div className={`p-2 rounded-xl ${iconBg[status]}`}>{icon}</div>
        <IconArrowRight className="w-4 h-4 text-gray-300 group-hover:text-brand-500 transition-colors" />
      </div>
      <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">{label}</p>
      <p className={`mt-1 text-lg font-bold ${statusColors[status]}`}>{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{sub}</p>
    </Link>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    posted:       "bg-green-50 text-green-700 border-green-100",
    pending:      "bg-amber-50 text-amber-700 border-amber-100",
    approved:     "bg-blue-50 text-blue-700 border-blue-100",
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

function EmptyDrafts() {
  return (
    <div className="card border-dashed px-8 py-14 text-center">
      <div className="w-12 h-12 rounded-2xl bg-brand-50 flex items-center justify-center mx-auto mb-3">
        <IconDocument className="w-6 h-6 text-brand-400" />
      </div>
      <p className="text-sm font-medium text-gray-500">No drafts yet</p>
      <p className="text-xs text-gray-400 mt-1">
        Your first draft will appear here after the scheduler runs.
      </p>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div>
        <div className="h-8 w-64 bg-gray-200 rounded-xl mb-2" />
        <div className="h-4 w-48 bg-gray-100 rounded-xl" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-28 bg-gray-200 rounded-2xl" />
        ))}
      </div>
      <div className="h-4 w-32 bg-gray-200 rounded-xl" />
      <div className="space-y-3">
        {[0, 1, 2].map((i) => <div key={i} className="h-16 bg-gray-200 rounded-2xl" />)}
      </div>
    </div>
  );
}
