-- ============================================================
-- Migration 004: Database Functions & Triggers
-- ============================================================

-- ============================================================
-- updated_at trigger
-- Automatically bumps updated_at on any row update.
-- ============================================================
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger trg_user_profiles_updated_at
    before update on public.user_profiles
    for each row execute function public.set_updated_at();

create trigger trg_drafts_updated_at
    before update on public.drafts
    for each row execute function public.set_updated_at();

-- ============================================================
-- handle_new_user
-- Creates a user_profile row automatically when a new user
-- signs up via Supabase Auth.
-- ============================================================
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    insert into public.user_profiles (id, full_name, company_name)
    values (
        new.id,
        coalesce(new.raw_user_meta_data->>'full_name', ''),
        coalesce(new.raw_user_meta_data->>'company_name', '')
    );
    return new;
end;
$$;

create trigger trg_on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();

-- ============================================================
-- content_performance view
-- Per-user, per-theme performance summary using the 7d
-- analytics snapshot (most complete data).
-- Used by the content generator feedback loop.
-- ============================================================
create or replace view public.content_performance as
select
    d.user_id,
    d.theme,
    d.post_type,
    d.audience,
    count(*)                                as post_count,
    round(avg(pa.engagement_rate), 3)       as avg_engagement_rate,
    round(avg(pa.impressions), 0)           as avg_impressions,
    round(avg(pa.reach), 0)                 as avg_reach,
    round(avg(pa.likes), 0)                 as avg_likes,
    round(avg(pa.saves), 0)                 as avg_saves,
    max(pa.fetched_at)                      as last_updated
from public.drafts d
join public.post_results pr on pr.draft_id = d.id
join public.post_analytics pa on pa.post_result_id = pr.id
where
    d.status = 'posted'
    and pa.fetch_stage = '7d'
group by d.user_id, d.theme, d.post_type, d.audience;

-- ============================================================
-- get_top_performing_themes
-- Returns top N themes for a user sorted by engagement rate.
-- Called by the content generator before picking a theme.
-- ============================================================
create or replace function public.get_top_performing_themes(
    p_user_id uuid,
    p_limit   int default 5
)
returns table (
    theme               text,
    post_type           post_type,
    audience            audience_type,
    avg_engagement_rate numeric,
    post_count          bigint
)
language sql
stable
as $$
    select
        theme,
        post_type,
        audience,
        avg_engagement_rate,
        post_count
    from public.content_performance
    where
        user_id = p_user_id
        and post_count >= 2                 -- need at least 2 posts to trust the signal
    order by avg_engagement_rate desc
    limit p_limit;
$$;

-- ============================================================
-- get_worst_performing_themes
-- Returns bottom N themes for a user to avoid/improve.
-- ============================================================
create or replace function public.get_worst_performing_themes(
    p_user_id uuid,
    p_limit   int default 5
)
returns table (
    theme               text,
    post_type           post_type,
    audience            audience_type,
    avg_engagement_rate numeric,
    post_count          bigint
)
language sql
stable
as $$
    select
        theme,
        post_type,
        audience,
        avg_engagement_rate,
        post_count
    from public.content_performance
    where
        user_id = p_user_id
        and post_count >= 2
    order by avg_engagement_rate asc
    limit p_limit;
$$;

-- ============================================================
-- get_due_analytics_jobs
-- Returns all analytics jobs that are scheduled and past due.
-- Called by the background job runner.
-- ============================================================
create or replace function public.get_due_analytics_jobs()
returns table (
    id              uuid,
    post_result_id  uuid,
    user_id         uuid,
    fetch_stage     analytics_stage,
    scheduled_for   timestamptz
)
language sql
stable
as $$
    select id, post_result_id, user_id, fetch_stage, scheduled_for
    from public.analytics_jobs
    where
        status = 'scheduled'
        and scheduled_for <= now()
    order by scheduled_for asc;
$$;
