"use client";

import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Area, AreaChart,
} from "recharts";
import { api, type DraftList } from "@/lib/api";
import { format } from "date-fns";
import { IconChart } from "@/components/NavIcons";

export default function AnalyticsPage() {
  const [drafts, setDrafts] = useState<DraftList | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listDrafts(1, 100, "posted").then(setDrafts).finally(() => setLoading(false));
  }, []);

  if (loading) return <Skeleton />;

  const posted = drafts?.items ?? [];

  const chartData = posted
    .filter((d) => d.post_result?.analytics.some((a) => a.fetch_stage === "7d"))
    .map((d) => {
      const analytics = d.post_result!.analytics.find((a) => a.fetch_stage === "7d")!;
      return {
        date: format(new Date(d.created_at), "MMM d"),
        impressions: analytics.impressions,
        likes: analytics.likes,
        saves: analytics.saves,
        engagement: analytics.engagement_rate ?? 0,
        theme: d.theme,
      };
    })
    .slice(-14);

  const themeMap: Record<string, { total: number; count: number }> = {};
  posted.forEach((d) => {
    const a = d.post_result?.analytics.find((a) => a.fetch_stage === "7d");
    if (!a) return;
    if (!themeMap[d.theme]) themeMap[d.theme] = { total: 0, count: 0 };
    themeMap[d.theme].total += a.engagement_rate ?? 0;
    themeMap[d.theme].count += 1;
  });
  const topThemes = Object.entries(themeMap)
    .map(([theme, { total, count }]) => ({ theme, avg: total / count, count }))
    .sort((a, b) => b.avg - a.avg)
    .slice(0, 5);

  const totalImpressions = posted.reduce((acc, d) => {
    const a = d.post_result?.analytics.find((x) => x.fetch_stage === "7d");
    return acc + (a?.impressions ?? 0);
  }, 0);
  const avgEngagement = posted.length
    ? posted.reduce((acc, d) => {
        const a = d.post_result?.analytics.find((x) => x.fetch_stage === "7d");
        return acc + (a?.engagement_rate ?? 0);
      }, 0) / posted.length
    : 0;
  const totalSaves = posted.reduce((acc, d) => {
    const a = d.post_result?.analytics.find((x) => x.fetch_stage === "7d");
    return acc + (a?.saves ?? 0);
  }, 0);
  const totalLikes = posted.reduce((acc, d) => {
    const a = d.post_result?.analytics.find((x) => x.fetch_stage === "7d");
    return acc + (a?.likes ?? 0);
  }, 0);

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">Analytics</h1>
        <p className="page-subtitle">
          Performance across your {posted.length} published post{posted.length !== 1 ? "s" : ""}.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total impressions"
          value={totalImpressions.toLocaleString()}
          change="+12%"
          positive
        />
        <MetricCard
          label="Avg engagement"
          value={`${avgEngagement.toFixed(2)}%`}
          change="+0.4%"
          positive
        />
        <MetricCard
          label="Total likes"
          value={totalLikes.toLocaleString()}
          change="+8%"
          positive
        />
        <MetricCard
          label="Total saves"
          value={totalSaves.toLocaleString()}
          change="+15%"
          positive
        />
      </div>

      {posted.length === 0 ? (
        <EmptyState />
      ) : (
        <>
          {/* Impressions chart */}
          {chartData.length > 0 && (
            <div className="card p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-sm font-semibold text-gray-800">Impressions over time</h2>
                  <p className="text-xs text-gray-400 mt-0.5">Last {chartData.length} posts</p>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={chartData} margin={{ top: 5, right: 10, bottom: 0, left: 0 }}>
                  <defs>
                    <linearGradient id="impressionsGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#7c3aed" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: "#9ca3af" }} axisLine={false} tickLine={false} width={40} />
                  <Tooltip
                    contentStyle={{ borderRadius: "12px", border: "1px solid #e5e7eb", boxShadow: "0 4px 12px rgba(0,0,0,0.08)", fontSize: 12 }}
                    cursor={{ stroke: "#7c3aed", strokeWidth: 1, strokeDasharray: "4 4" }}
                  />
                  <Area type="monotone" dataKey="impressions" stroke="#7c3aed" strokeWidth={2.5} fill="url(#impressionsGrad)" dot={false} activeDot={{ r: 5, fill: "#7c3aed" }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Engagement chart */}
          {chartData.length > 0 && (
            <div className="card p-6">
              <div className="mb-6">
                <h2 className="text-sm font-semibold text-gray-800">Engagement rate per post</h2>
                <p className="text-xs text-gray-400 mt-0.5">7-day data</p>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData} margin={{ top: 5, right: 10, bottom: 0, left: 0 }}>
                  <defs>
                    <linearGradient id="engagementGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={1} />
                      <stop offset="95%" stopColor="#7c3aed" stopOpacity={1} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: "#9ca3af" }} axisLine={false} tickLine={false} unit="%" width={40} />
                  <Tooltip
                    formatter={(v: number) => [`${v.toFixed(2)}%`, "Engagement"]}
                    contentStyle={{ borderRadius: "12px", border: "1px solid #e5e7eb", boxShadow: "0 4px 12px rgba(0,0,0,0.08)", fontSize: 12 }}
                    cursor={{ fill: "rgba(124,58,237,0.05)" }}
                  />
                  <Bar dataKey="engagement" fill="url(#engagementGrad)" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Top themes */}
          {topThemes.length > 0 && (
            <div className="card p-6">
              <h2 className="text-sm font-semibold text-gray-800 mb-5">Top performing themes</h2>
              <div className="space-y-4">
                {topThemes.map((t, i) => {
                  const pct = topThemes[0] ? (t.avg / topThemes[0].avg) * 100 : 0;
                  return (
                    <div key={t.theme} className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="text-xs font-bold text-gray-300 w-5 text-right shrink-0">{i + 1}</span>
                          <p className="text-sm font-medium text-gray-800 truncate">{t.theme}</p>
                          <span className="text-xs text-gray-400 shrink-0">
                            {t.count} post{t.count !== 1 ? "s" : ""}
                          </span>
                        </div>
                        <span className="text-sm font-bold text-brand-600 shrink-0 ml-4">
                          {t.avg.toFixed(2)}%
                        </span>
                      </div>
                      <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-brand-600 to-advora-teal transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function MetricCard({ label, value, change, positive }: { label: string; value: string; change?: string; positive?: boolean }) {
  return (
    <div className="card p-5">
      <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">{label}</p>
      <p className="mt-1.5 text-2xl font-bold text-navy-800">{value}</p>
      {change && (
        <p className={`text-xs font-medium mt-1 ${positive ? "text-green-600" : "text-red-500"}`}>
          {change} vs last period
        </p>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="card border-dashed px-8 py-16 text-center">
      <div className="w-12 h-12 rounded-2xl bg-brand-50 flex items-center justify-center mx-auto mb-3">
        <IconChart className="w-6 h-6 text-brand-400" />
      </div>
      <p className="text-sm font-medium text-gray-500">No analytics yet</p>
      <p className="text-xs text-gray-400 mt-1 max-w-xs mx-auto">
        Data appears 24 hours after your first post goes live.
      </p>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="h-8 w-48 bg-gray-200 rounded-xl" />
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[0, 1, 2, 3].map((i) => <div key={i} className="h-28 bg-gray-200 rounded-2xl" />)}
      </div>
      <div className="h-72 bg-gray-200 rounded-2xl" />
      <div className="h-72 bg-gray-200 rounded-2xl" />
    </div>
  );
}
