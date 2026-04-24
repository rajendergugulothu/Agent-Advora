-- ============================================================
-- Migration 003: Row Level Security Policies
-- All tables are locked down so users can only access
-- their own data. The service role (backend) bypasses RLS.
-- ============================================================

-- user_profiles
alter table public.user_profiles enable row level security;

create policy "users can view own profile"
    on public.user_profiles for select
    using (auth.uid() = id);

create policy "users can update own profile"
    on public.user_profiles for update
    using (auth.uid() = id)
    with check (auth.uid() = id);

create policy "users can insert own profile"
    on public.user_profiles for insert
    with check (auth.uid() = id);

-- instagram_connections
alter table public.instagram_connections enable row level security;

create policy "users can view own instagram connection"
    on public.instagram_connections for select
    using (auth.uid() = user_id);

create policy "users can insert own instagram connection"
    on public.instagram_connections for insert
    with check (auth.uid() = user_id);

create policy "users can update own instagram connection"
    on public.instagram_connections for update
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

create policy "users can delete own instagram connection"
    on public.instagram_connections for delete
    using (auth.uid() = user_id);

-- drafts
alter table public.drafts enable row level security;

create policy "users can view own drafts"
    on public.drafts for select
    using (auth.uid() = user_id);

create policy "users can insert own drafts"
    on public.drafts for insert
    with check (auth.uid() = user_id);

create policy "users can update own drafts"
    on public.drafts for update
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- post_results
alter table public.post_results enable row level security;

create policy "users can view own post results"
    on public.post_results for select
    using (auth.uid() = user_id);

create policy "users can insert own post results"
    on public.post_results for insert
    with check (auth.uid() = user_id);

-- post_analytics
alter table public.post_analytics enable row level security;

create policy "users can view own analytics"
    on public.post_analytics for select
    using (auth.uid() = user_id);

create policy "users can insert own analytics"
    on public.post_analytics for insert
    with check (auth.uid() = user_id);

-- analytics_jobs
alter table public.analytics_jobs enable row level security;

create policy "users can view own analytics jobs"
    on public.analytics_jobs for select
    using (auth.uid() = user_id);

-- webhook_events: no user-level RLS — only accessible via service role
alter table public.webhook_events enable row level security;
-- no policies = no access from client; service role bypasses RLS
