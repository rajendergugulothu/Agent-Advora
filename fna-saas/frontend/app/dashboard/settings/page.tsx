"use client";

import { useEffect, useState } from "react";
import { api, type UserProfile, type UpdateProfilePayload } from "@/lib/api";

const TIMEZONES = [
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "America/Phoenix",
  "America/Anchorage",
  "Pacific/Honolulu",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Asia/Dubai",
  "Asia/Kolkata",
  "Asia/Singapore",
  "Asia/Tokyo",
  "Australia/Sydney",
];

export default function SettingsPage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [form, setForm] = useState<UpdateProfilePayload>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [togglingScheduler, setTogglingScheduler] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getProfile().then((p) => {
      setProfile(p);
      setForm({
        full_name:       p.full_name,
        company_name:    p.company_name ?? "",
        whatsapp_number: p.whatsapp_number ?? "",
        post_time_hour:  p.post_time_hour,
        post_time_minute: p.post_time_minute,
        timezone:        p.timezone,
      });
    }).finally(() => setLoading(false));
  }, []);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const updated = await api.updateProfile(form);
      setProfile(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  }

  async function handleToggleScheduler() {
    if (!profile) return;
    setTogglingScheduler(true);
    try {
      const result = await api.toggleScheduler(!profile.scheduler_active);
      setProfile((p) => p ? { ...p, scheduler_active: result.scheduler_active } : p);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update scheduler");
    } finally {
      setTogglingScheduler(false);
    }
  }

  if (loading) return <Skeleton />;

  const postTimeFormatted = `${String(form.post_time_hour ?? 9).padStart(2, "0")}:${String(form.post_time_minute ?? 0).padStart(2, "0")}`;

  return (
    <div className="space-y-8 animate-fade-in max-w-2xl">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Manage your profile and posting preferences.</p>
      </div>

      {/* Profile section */}
      <form onSubmit={handleSave} className="space-y-5">
        <div className="card p-6 space-y-5">
          <div className="flex items-center gap-3 pb-4 border-b border-gray-100">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-brand-500 to-advora-teal flex items-center justify-center shrink-0">
              <span className="text-base font-bold text-white">
                {(form.full_name ?? profile?.full_name ?? "U")[0]?.toUpperCase()}
              </span>
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-800">{form.full_name || "Your name"}</p>
              <p className="text-xs text-gray-400">{form.company_name || "Your company"}</p>
            </div>
          </div>

          <h2 className="text-sm font-semibold text-gray-700">Profile information</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="Full name">
              <input
                type="text"
                required
                value={form.full_name ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
                className="input-field"
                placeholder="Jane Smith"
              />
            </Field>

            <Field label="Company name" optional>
              <input
                type="text"
                value={form.company_name ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, company_name: e.target.value }))}
                className="input-field"
                placeholder="Smith Financial Group"
              />
            </Field>
          </div>

          <Field
            label="WhatsApp number"
            hint="Include country code — e.g. +15551234567"
          >
            <div className="relative">
              <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z" />
                </svg>
              </div>
              <input
                type="tel"
                value={form.whatsapp_number ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, whatsapp_number: e.target.value }))}
                className="input-field pl-10"
                placeholder="+15551234567"
              />
            </div>
          </Field>
        </div>

        {/* Posting schedule */}
        <div className="card p-6 space-y-5">
          <h2 className="text-sm font-semibold text-gray-700">Posting schedule</h2>

          <div className="grid grid-cols-3 gap-4">
            <Field label="Hour">
              <input
                type="number"
                min={0}
                max={23}
                value={form.post_time_hour ?? 9}
                onChange={(e) => setForm((f) => ({ ...f, post_time_hour: parseInt(e.target.value) }))}
                className="input-field text-center"
              />
            </Field>
            <Field label="Minute">
              <input
                type="number"
                min={0}
                max={59}
                step={5}
                value={form.post_time_minute ?? 0}
                onChange={(e) => setForm((f) => ({ ...f, post_time_minute: parseInt(e.target.value) }))}
                className="input-field text-center"
              />
            </Field>
            <Field label="Preview">
              <div className="input-field bg-gray-50 text-gray-600 font-mono text-center cursor-default select-none">
                {postTimeFormatted}
              </div>
            </Field>
          </div>

          <Field label="Timezone">
            <select
              value={form.timezone ?? "America/Chicago"}
              onChange={(e) => setForm((f) => ({ ...f, timezone: e.target.value }))}
              className="input-field"
            >
              {TIMEZONES.map((tz) => (
                <option key={tz} value={tz}>{tz.replace(/_/g, " ")}</option>
              ))}
            </select>
          </Field>
        </div>

        {error && (
          <div className="flex items-start gap-2.5 rounded-xl bg-red-50 border border-red-100 px-4 py-3">
            <svg className="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={saving}
          className={`btn-gradient flex items-center gap-2 ${saved ? "!bg-green-500 !from-green-500 !to-green-500" : ""}`}
        >
          {saving ? (
            <>
              <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Saving...
            </>
          ) : saved ? (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              Saved!
            </>
          ) : (
            "Save changes"
          )}
        </button>
      </form>

      {/* Scheduler toggle */}
      <div className="card p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <p className="text-sm font-semibold text-gray-900">Daily scheduler</p>
              <span className={`badge border text-[10px] ${
                profile?.scheduler_active
                  ? "bg-green-50 text-green-700 border-green-100"
                  : "bg-gray-100 text-gray-500 border-gray-200"
              }`}>
                {profile?.scheduler_active ? "Active" : "Paused"}
              </span>
            </div>
            <p className="text-xs text-gray-500">
              {profile?.scheduler_active
                ? `Posts are sent daily at ${String(profile.post_time_hour).padStart(2, "0")}:${String(profile.post_time_minute).padStart(2, "0")} ${profile.timezone}`
                : "Enable to automatically send drafts to WhatsApp for approval."}
            </p>
          </div>

          <button
            onClick={handleToggleScheduler}
            disabled={togglingScheduler || !profile?.whatsapp_number}
            title={!profile?.whatsapp_number ? "Add your WhatsApp number first" : undefined}
            className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 disabled:opacity-40 shrink-0 ${
              profile?.scheduler_active ? "bg-brand-600" : "bg-gray-200"
            }`}
          >
            <span
              className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition-transform duration-200 ${
                profile?.scheduler_active ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
        </div>

        {!profile?.whatsapp_number && (
          <div className="mt-4 flex items-start gap-2.5 rounded-xl bg-amber-50 border border-amber-100 px-4 py-3">
            <svg className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
            <p className="text-xs text-amber-700">
              Add your WhatsApp number above and save to enable the daily scheduler.
            </p>
          </div>
        )}
      </div>

      {/* Danger zone */}
      <div className="card p-6 border-red-100">
        <h2 className="text-sm font-semibold text-red-600 mb-1">Danger zone</h2>
        <p className="text-xs text-gray-500 mb-4">These actions are permanent and cannot be undone.</p>
        <form action="/auth/signout" method="post">
          <button
            type="submit"
            className="rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-100 transition-colors"
          >
            Sign out of all devices
          </button>
        </form>
      </div>
    </div>
  );
}

function Field({
  label,
  optional,
  hint,
  children,
}: {
  label: string;
  optional?: boolean;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1.5">
        {label}{" "}
        {optional && <span className="text-gray-400 font-normal text-xs">(optional)</span>}
      </label>
      {children}
      {hint && <p className="text-xs text-gray-400 mt-1.5">{hint}</p>}
    </div>
  );
}

function Skeleton() {
  return (
    <div className="space-y-6 animate-pulse max-w-2xl">
      <div className="h-8 w-40 bg-gray-200 rounded-xl" />
      <div className="h-96 bg-gray-200 rounded-2xl" />
      <div className="h-32 bg-gray-200 rounded-2xl" />
    </div>
  );
}
