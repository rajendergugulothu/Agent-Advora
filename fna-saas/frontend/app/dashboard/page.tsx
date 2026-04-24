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
      <div className="shine-border relative overflow-hidden rounded-2xl bg-navy-900 px-6 py-7 text-white shadow-2xl shadow-navy-900/20 sm:px-8">
        <div className="absolute inset-0 bg-[linear-gradient(115deg,rgba(124,58,237,0.34),rgba(6,182,212,0.22),rgba(249,115,22,0.20))]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.08)_1px,transparent_1px)] bg-[size:36px_36px] opacity-35" />
        <div className="relative flex flex-col gap-7 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-semibold text-cyan-100 backdrop-blur">
              <span className="h-2 w-2 rounded-full bg-green-300 shadow-[0_0_12px_rgba(134,239,172,0.9)]" />
              Client growth cockpit
            </div>
            <h1 className="text-balance text-3xl font-black tracking-tight sm:text-4xl">
              {greeting()}{profile?.full_name ? `, ${profile.full_name.split(" ")[0]}` : ""}
            </h1>
            <p className="mt-3 max-w-xl text-sm leading-6 text-slate-200">
              Your Advora workspace is ready to turn daily market insight into polished Instagram content.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3 text-center sm:min-w-[22rem]">
            <HeroMiniStat label="Ready" value={drafts?.items.length ?? 0} />
            <HeroMiniStat label="Posted" value={posted} />
            <HeroMiniStat label="Pending" value={pending} />
          </div>
        </div>
      </div>

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

      {!profile?.instagram_connected && (
        <div className="shine-border relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-600 via-navy-800 to-advora-teal p-6 shadow-2xl shadow-brand-700/18 sm:p-8">
          <div className="absolute inset-0 bg-[linear-gradient(120deg,transparent,rgba(255,255,255,0.16),transparent)] animate-[shimmer_4s_ease-in-out_infinite]" />
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
              className="shrink-0 flex items-center gap-2 rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-brand-700 shadow-lg transition-all hover:-translate-y-0.5 hover:bg-brand-50 hover:shadow-xl"
            >
              Connect now
              <IconArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[1fr_22rem]">
        <div className="card p-5 sm:p-6">
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

        <div className="card p-5 sm:p-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <p className="section-title">Momentum</p>
              <h2 className="mt-1 text-base font-semibold text-navy-800">Weekly content flow</h2>
            </div>
            <IconSparkles className="h-5 w-5 text-brand-500" />
          </div>
          <div className="space-y-4">
            <ProgressRow label="Instagram setup" value={profile?.instagram_connected ? 100 : 42} tone="cyan" />
            <ProgressRow label="Scheduler health" value={profile?.scheduler_active ? 88 : 28} tone="purple" />
            <ProgressRow label="Approval rhythm" value={pending > 0 ? 68 : posted > 0 ? 92 : 35} tone="orange" />
          </div>
          <div className="mt-6 rounded-2xl border border-white/80 bg-gradient-to-br from-white/90 to-cyan-50/80 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Next best move</p>
            <p className="mt-2 text-sm font-semibold text-navy-800">
              {profile?.instagram_connected ? "Review pending drafts and keep the queue moving." : "Connect Instagram to unlock automatic publishing."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function HeroMiniStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-white/[0.14] bg-white/10 px-3 py-4 backdrop-blur">
      <p className="text-2xl font-black">{value}</p>
      <p className="mt-1 text-[11px] font-semibold uppercase tracking-wide text-slate-300">{label}</p>
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
    <Link href={href} className="card-hover shine-border p-5 block group">
      <div className="flex items-start justify-between mb-3">
        <div className={`p-2 rounded-xl shadow-sm ${iconBg[status]}`}>{icon}</div>
        <IconArrowRight className="w-4 h-4 text-gray-300 transition-all group-hover:translate-x-1 group-hover:text-brand-500" />
      </div>
      <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">{label}</p>
      <p className={`mt-1 text-lg font-bold ${statusColors[status]}`}>{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{sub}</p>
    </Link>
  );
}

function ProgressRow({ label, value, tone }: { label: string; value: number; tone: "cyan" | "purple" | "orange" }) {
  const tones = {
    cyan: "from-cyan-400 to-sky-500",
    purple: "from-brand-500 to-advora-pink",
    orange: "from-advora-orange to-amber-400",
  };

  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="font-medium text-gray-700">{label}</span>
        <span className="font-bold text-navy-800">{value}%</span>
      </div>
      <div className="h-2.5 overflow-hidden rounded-full bg-gray-100 shadow-inner">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${tones[tone]} shadow-sm transition-all duration-700`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
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
