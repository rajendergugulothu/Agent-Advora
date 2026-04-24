-- ============================================================
-- Migration 001: Initial Schema
-- FNA SaaS Platform
-- ============================================================

-- Enable required extensions
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- ============================================================
-- user_profiles
-- Extends Supabase auth.users with app-specific data.
-- Sensitive credentials (tokens) are encrypted at the
-- application layer before storage.
-- ============================================================
create table public.user_profiles (
    id                          uuid primary key references auth.users(id) on delete cascade,
    full_name                   text not null,
    company_name                text,
    whatsapp_number             text,                   -- recipient number e.g. +15551234567
    whatsapp_phone_number_id    text,                   -- Meta phone number ID (encrypted at app layer)
    whatsapp_access_token       text,                   -- encrypted at app layer
    post_time_hour              smallint not null default 9 check (post_time_hour between 0 and 23),
    post_time_minute            smallint not null default 0 check (post_time_minute between 0 and 59),
    timezone                    text not null default 'America/Chicago',
    scheduler_active            boolean not null default false,
    is_active                   boolean not null default true,
    created_at                  timestamptz not null default now(),
    updated_at                  timestamptz not null default now()
);

-- ============================================================
-- instagram_connections
-- One per user. Stores OAuth tokens and account metadata.
-- Tokens are encrypted at the application layer.
-- ============================================================
create table public.instagram_connections (
    id                      uuid primary key default uuid_generate_v4(),
    user_id                 uuid not null references auth.users(id) on delete cascade,
    instagram_account_id    text not null,              -- encrypted at app layer
    instagram_access_token  text not null,              -- encrypted at app layer
    token_expires_at        timestamptz not null,
    username                text,
    profile_picture_url     text,
    page_id                 text,                       -- linked Facebook Page ID
    is_active               boolean not null default true,
    connected_at            timestamptz not null default now(),
    last_refreshed_at       timestamptz not null default now(),
    constraint uq_instagram_user unique (user_id)
);

-- ============================================================
-- drafts
-- One row per generated content draft per user.
-- ============================================================
create type draft_status as enum (
    'pending',
    'approved',
    'rejected',
    'posting',
    'posted',
    'image_failed',
    'post_failed'
);

create type post_type as enum (
    'single_image',
    'carousel'
);

create type audience_type as enum (
    'client',
    'advisor'
);

create table public.drafts (
    id                  uuid primary key default uuid_generate_v4(),
    user_id             uuid not null references auth.users(id) on delete cascade,
    theme               text not null,
    audience            audience_type not null,
    hook                text not null,
    caption             text not null,
    hashtags            text not null,
    image_concept       text,
    post_type           post_type not null default 'single_image',
    carousel_slides     jsonb not null default '[]'::jsonb,
    status              draft_status not null default 'pending',
    whatsapp_message_id text,                           -- Meta message ID for tracking
    status_reason       text,                           -- error message if failed
    created_at          timestamptz not null default now(),
    updated_at          timestamptz not null default now()
);

-- ============================================================
-- post_results
-- Stores the outcome of a successful Instagram publish.
-- ============================================================
create table public.post_results (
    id                  uuid primary key default uuid_generate_v4(),
    draft_id            uuid not null references public.drafts(id) on delete cascade,
    user_id             uuid not null references auth.users(id) on delete cascade,
    instagram_post_id   text not null,
    instagram_url       text,
    image_url           text,
    image_urls          jsonb not null default '[]'::jsonb,
    posted_at           timestamptz not null default now(),
    constraint uq_post_result_draft unique (draft_id)
);

-- ============================================================
-- post_analytics
-- Metrics fetched from Instagram Insights API.
-- Collected at 24h, 72h, and 7d after posting.
-- ============================================================
create type analytics_stage as enum ('24h', '72h', '7d');

create table public.post_analytics (
    id                  uuid primary key default uuid_generate_v4(),
    post_result_id      uuid not null references public.post_results(id) on delete cascade,
    user_id             uuid not null references auth.users(id) on delete cascade,
    draft_id            uuid not null references public.drafts(id) on delete cascade,
    instagram_post_id   text not null,
    fetch_stage         analytics_stage not null,
    fetched_at          timestamptz not null default now(),
    impressions         integer not null default 0,
    reach               integer not null default 0,
    likes               integer not null default 0,
    comments            integer not null default 0,
    shares              integer not null default 0,
    saves               integer not null default 0,
    -- engagement_rate = (likes + comments + shares + saves) / reach * 100
    engagement_rate     numeric(6, 3) generated always as (
        case
            when reach > 0
            then round(((likes + comments + shares + saves)::numeric / reach) * 100, 3)
            else 0
        end
    ) stored,
    constraint uq_analytics_stage unique (post_result_id, fetch_stage)
);

-- ============================================================
-- analytics_jobs
-- Tracks scheduled metric-fetch jobs so we never double-fetch.
-- ============================================================
create type job_status as enum ('scheduled', 'completed', 'failed');

create table public.analytics_jobs (
    id                  uuid primary key default uuid_generate_v4(),
    post_result_id      uuid not null references public.post_results(id) on delete cascade,
    user_id             uuid not null references auth.users(id) on delete cascade,
    fetch_stage         analytics_stage not null,
    scheduled_for       timestamptz not null,
    status              job_status not null default 'scheduled',
    attempted_at        timestamptz,
    error               text,
    constraint uq_analytics_job unique (post_result_id, fetch_stage)
);

-- ============================================================
-- webhook_events
-- Raw log of all incoming WhatsApp webhook payloads.
-- Useful for debugging and auditing.
-- ============================================================
create table public.webhook_events (
    id              uuid primary key default uuid_generate_v4(),
    raw_payload     jsonb not null,
    signature_valid boolean not null,
    processed       boolean not null default false,
    error           text,
    received_at     timestamptz not null default now()
);
