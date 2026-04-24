"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api, type InstagramStatus } from "@/lib/api";
import { format } from "date-fns";
import { IconInstagram } from "@/components/NavIcons";

export default function ConnectPage() {
  const searchParams = useSearchParams();
  const justConnected = searchParams.get("status") === "success";

  const [status, setStatus] = useState<InstagramStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);

  useEffect(() => {
    api.getInstagramStatus().then(setStatus).finally(() => setLoading(false));
  }, []);

  async function handleConnect() {
    setConnecting(true);
    try {
      const { url } = await api.getConnectUrl();
      window.location.href = url;
    } catch {
      setConnecting(false);
    }
  }

  async function handleDisconnect() {
    setDisconnecting(true);
    await api.disconnectInstagram();
    setStatus({ connected: false, username: null, profile_picture_url: null, token_expires_at: null });
    setDisconnecting(false);
  }

  if (loading) return <Skeleton />;

  return (
    <div className="space-y-8 animate-fade-in max-w-2xl">
      <div className="page-header">
        <h1 className="page-title">Connect Instagram</h1>
        <p className="page-subtitle">
          Link your Instagram Business account so Advora can publish posts on your behalf.
        </p>
      </div>

      {justConnected && (
        <div className="flex items-center gap-3 rounded-2xl bg-green-50 border border-green-200 px-5 py-4">
          <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center shrink-0">
            <svg className="w-4 h-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-semibold text-green-800">Instagram connected successfully!</p>
            <p className="text-xs text-green-600 mt-0.5">You&apos;re all set. Advora can now publish to your account.</p>
          </div>
        </div>
      )}

      {status?.connected ? (
        /* Connected state */
        <div className="space-y-5">
          {/* Profile card */}
          <div className="card p-6">
            <div className="flex items-center gap-5">
              {status.profile_picture_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={status.profile_picture_url}
                  alt="Instagram profile"
                  className="w-16 h-16 rounded-full object-cover ring-2 ring-brand-100"
                />
              ) : (
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-xl">
                  {status.username?.[0]?.toUpperCase() ?? "?"}
                </div>
              )}
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-bold text-navy-800 text-lg">@{status.username}</p>
                </div>
                <div className="flex items-center gap-1.5 mt-1">
                  <div className="w-2 h-2 rounded-full bg-green-500" />
                  <p className="text-sm font-medium text-green-600">Connected</p>
                </div>
              </div>
              <div className="ml-auto">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                  <IconInstagram className="w-6 h-6 text-white" />
                </div>
              </div>
            </div>
          </div>

          {/* Token expiry */}
          {status.token_expires_at && (
            <div className="card p-5 flex items-start gap-4">
              <div className="p-2 rounded-xl bg-blue-50 shrink-0">
                <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-800">Access token active</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Expires:{" "}
                  <span className="font-medium text-gray-700">
                    {format(new Date(status.token_expires_at), "MMMM d, yyyy")}
                  </span>
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Advora automatically refreshes your token before it expires.
                </p>
              </div>
            </div>
          )}

          {/* What Advora can do */}
          <div className="card p-5">
            <p className="text-sm font-semibold text-gray-700 mb-3">Advora is authorized to:</p>
            <ul className="space-y-2">
              {[
                "Publish photos and carousels to your feed",
                "Read your post insights and analytics",
                "Manage captions and hashtags",
              ].map((item) => (
                <li key={item} className="flex items-center gap-2.5 text-sm text-gray-600">
                  <svg className="w-4 h-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* Disconnect */}
          <div className="card p-5 border-red-50 bg-red-50/50">
            <p className="text-sm font-semibold text-gray-800 mb-1">Disconnect account</p>
            <p className="text-xs text-gray-500 mb-4">
              Removing the connection will pause all scheduled posts.
            </p>
            <button
              onClick={handleDisconnect}
              disabled={disconnecting}
              className="flex items-center gap-2 rounded-xl border border-red-200 bg-white px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50 transition-colors"
            >
              {disconnecting ? "Disconnecting..." : "Disconnect Instagram"}
            </button>
          </div>
        </div>
      ) : (
        /* Disconnected state */
        <div className="space-y-5">
          <div className="card border-amber-100 bg-amber-50/80 p-5">
            <div className="flex items-start gap-3">
              <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-700">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.25}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-bold text-amber-900">Meta app setup required</p>
                <p className="mt-1 text-sm leading-5 text-amber-800">
                  If Meta shows &quot;App not active&quot;, your Facebook app is still in development mode.
                  Add your Facebook account as an app tester/admin in Meta Developer Dashboard, or switch
                  the app to Live after completing the required app review.
                </p>
                <p className="mt-2 text-xs font-medium text-amber-700">
                  Also confirm the valid OAuth redirect URI is exactly:
                  {" "}
                  <span className="font-mono">http://localhost:8000/api/v1/instagram/callback</span>
                </p>
              </div>
            </div>
          </div>

          <div className="card p-8 text-center">
            {/* Instagram gradient icon */}
            <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-purple-500 via-pink-500 to-orange-400 mx-auto flex items-center justify-center shadow-lg mb-6">
              <IconInstagram className="w-10 h-10 text-white" />
            </div>

            <h3 className="text-xl font-bold text-navy-800">Connect your Instagram</h3>
            <p className="text-sm text-gray-500 mt-2 max-w-sm mx-auto">
              You need an Instagram Business or Creator account linked to a Facebook Page.
            </p>

            <div className="mt-8 space-y-3">
              <button
                onClick={handleConnect}
                disabled={connecting}
                className="w-full sm:w-auto mx-auto flex items-center justify-center gap-2.5 rounded-xl bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 px-8 py-3 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50 transition-opacity shadow-lg"
              >
                {connecting ? (
                  <>
                    <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Redirecting to Meta...
                  </>
                ) : (
                  <>
                    <IconInstagram className="w-4 h-4" />
                    Connect with Instagram
                  </>
                )}
              </button>
              <p className="text-xs text-gray-400">
                You&apos;ll be redirected to Meta to authorize Advora. We never store your password.
              </p>
            </div>
          </div>

          {/* Requirements */}
          <div className="card p-5">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Requirements</p>
            <ul className="space-y-2.5">
              {[
                "Instagram Business or Creator account",
                "Linked to a Facebook Page you manage",
                "Admin access to the Facebook Page",
              ].map((req) => (
                <li key={req} className="flex items-center gap-2.5 text-sm text-gray-600">
                  <div className="w-5 h-5 rounded-full bg-brand-50 flex items-center justify-center shrink-0">
                    <svg className="w-3 h-3 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                  </div>
                  {req}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

function Skeleton() {
  return (
    <div className="space-y-6 animate-pulse max-w-2xl">
      <div className="h-8 w-56 bg-gray-200 rounded-xl" />
      <div className="h-4 w-80 bg-gray-100 rounded-xl" />
      <div className="h-64 bg-gray-200 rounded-2xl" />
    </div>
  );
}
