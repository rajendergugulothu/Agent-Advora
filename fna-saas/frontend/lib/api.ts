/**
 * Typed API client for the FastAPI backend.
 * All requests include the Supabase session token as Bearer.
 */

import { createClient } from "./supabase";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function getAuthHeaders(): Promise<HeadersInit> {
  const supabase = createClient();
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { ...headers, ...(options.headers ?? {}) },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface UserProfile {
  id: string;
  full_name: string;
  company_name: string | null;
  whatsapp_number: string | null;
  post_time_hour: number;
  post_time_minute: number;
  timezone: string;
  scheduler_active: boolean;
  instagram_connected: boolean;
  instagram_username: string | null;
  created_at: string;
}

export interface Analytics {
  fetch_stage: "24h" | "72h" | "7d";
  fetched_at: string;
  impressions: number;
  reach: number;
  likes: number;
  comments: number;
  shares: number;
  saves: number;
  engagement_rate: number | null;
}

export interface PostResult {
  instagram_post_id: string;
  instagram_url: string | null;
  image_url: string | null;
  image_urls: string[];
  posted_at: string;
  analytics: Analytics[];
}

export interface Draft {
  id: string;
  theme: string;
  audience: string;
  hook: string;
  caption: string;
  hashtags: string;
  post_type: "single_image" | "carousel";
  status: "pending" | "approved" | "rejected" | "posting" | "posted" | "image_failed" | "post_failed";
  created_at: string;
  updated_at: string;
  post_result: PostResult | null;
}

export interface DraftList {
  items: Draft[];
  total: number;
  page: number;
  page_size: number;
}

export interface InstagramStatus {
  connected: boolean;
  username: string | null;
  profile_picture_url: string | null;
  token_expires_at: string | null;
}

export interface UpdateProfilePayload {
  full_name?: string;
  company_name?: string;
  whatsapp_number?: string;
  post_time_hour?: number;
  post_time_minute?: number;
  timezone?: string;
}

// ── API calls ─────────────────────────────────────────────────────────────────

export const api = {
  // Users
  getProfile: () => request<UserProfile>("/users/me"),
  updateProfile: (data: UpdateProfilePayload) =>
    request<UserProfile>("/users/me", { method: "PATCH", body: JSON.stringify(data) }),
  toggleScheduler: (active: boolean) =>
    request<{ scheduler_active: boolean }>("/users/me/scheduler", {
      method: "POST",
      body: JSON.stringify({ active }),
    }),

  // Drafts
  listDrafts: (page = 1, pageSize = 20, status?: string) => {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (status) params.set("status", status);
    return request<DraftList>(`/drafts?${params}`);
  },
  getDraft: (id: string) => request<Draft>(`/drafts/${id}`),
  triggerGeneration: (theme?: string, audience?: string) =>
    request<{ status: string }>("/drafts/trigger", {
      method: "POST",
      body: JSON.stringify({ theme, audience }),
    }),

  // Instagram
  getConnectUrl: () => request<{ url: string }>("/instagram/connect"),
  getInstagramStatus: () => request<InstagramStatus>("/instagram/status"),
  disconnectInstagram: () =>
    request<{ disconnected: boolean }>("/instagram/disconnect", { method: "DELETE" }),
};
