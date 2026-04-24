-- ============================================================
-- Migration 002: Indexes
-- ============================================================

-- user_profiles
create index idx_user_profiles_is_active on public.user_profiles(is_active);
create index idx_user_profiles_scheduler on public.user_profiles(scheduler_active, is_active);

-- instagram_connections
create index idx_instagram_connections_user_id on public.instagram_connections(user_id);
create index idx_instagram_connections_expires on public.instagram_connections(token_expires_at) where is_active = true;

-- drafts
create index idx_drafts_user_id on public.drafts(user_id);
create index idx_drafts_status on public.drafts(status);
create index idx_drafts_user_status on public.drafts(user_id, status);
create index idx_drafts_created_at on public.drafts(created_at desc);

-- post_results
create index idx_post_results_user_id on public.post_results(user_id);
create index idx_post_results_draft_id on public.post_results(draft_id);
create index idx_post_results_posted_at on public.post_results(posted_at desc);

-- post_analytics
create index idx_post_analytics_user_id on public.post_analytics(user_id);
create index idx_post_analytics_draft_id on public.post_analytics(draft_id);
create index idx_post_analytics_post_result on public.post_analytics(post_result_id);

-- analytics_jobs
create index idx_analytics_jobs_status on public.analytics_jobs(status, scheduled_for) where status = 'scheduled';
create index idx_analytics_jobs_user_id on public.analytics_jobs(user_id);

-- webhook_events
create index idx_webhook_events_received_at on public.webhook_events(received_at desc);
create index idx_webhook_events_processed on public.webhook_events(processed) where processed = false;
