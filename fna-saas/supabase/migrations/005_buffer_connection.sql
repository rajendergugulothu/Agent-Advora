-- Migration 005: Add buffer_connections table
-- Replaces Instagram Graph API with Buffer API for posting.
-- Each user stores their own Buffer API token + Instagram channel ID.

CREATE TABLE IF NOT EXISTS buffer_connections (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    buffer_access_token TEXT NOT NULL,          -- encrypted Buffer API key
    buffer_channel_id   TEXT NOT NULL,          -- Buffer Instagram channel ID
    username            TEXT,                   -- Instagram username (display only)
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    connected_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_buffer_user UNIQUE (user_id)
);

-- Index for fast lookup by user
CREATE INDEX IF NOT EXISTS idx_buffer_connections_user_id
    ON buffer_connections (user_id);

-- RLS: users can only see/edit their own Buffer connection
ALTER TABLE buffer_connections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "buffer_connections_select_own"
    ON buffer_connections FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "buffer_connections_insert_own"
    ON buffer_connections FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "buffer_connections_update_own"
    ON buffer_connections FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "buffer_connections_delete_own"
    ON buffer_connections FOR DELETE
    USING (auth.uid() = user_id);
