-- ============================================================
-- RunBeat Database Migration - Complete Version 2.0
-- ============================================================
-- This migration creates ALL necessary tables, columns, and policies
-- Execute this SQL in Supabase SQL Editor
-- Safe to run multiple times (uses IF NOT EXISTS)
-- ============================================================

-- ============================================================
-- 1. EXTENSIONS
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 2. USERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE,
  spotify_user_id TEXT UNIQUE,
  spotify_access_token TEXT,
  spotify_refresh_token TEXT,
  spotify_token_expires_at TIMESTAMPTZ,
  preferences JSONB DEFAULT '{
    "top_genres": [],
    "top_artists": [],
    "avg_bpm": 145
  }'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for users
CREATE INDEX IF NOT EXISTS idx_users_spotify_user_id ON users(spotify_user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_user_preferences ON users USING GIN (preferences);

-- ============================================================
-- 3. WORKOUTS TABLE (with all features)
-- ============================================================
CREATE TABLE IF NOT EXISTS workouts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN ('steady', 'progressive', 'intervals', 'fartlek')),
  duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
  intensity TEXT NOT NULL CHECK (intensity IN ('low', 'moderate', 'high')),
  hr_zones INTEGER[] DEFAULT ARRAY[110, 180],
  genres TEXT[] DEFAULT ARRAY[]::TEXT[],
  interval_stages JSONB DEFAULT '[]'::jsonb,
  prompt TEXT DEFAULT '',
  is_active BOOLEAN DEFAULT FALSE,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add columns if they don't exist (for existing tables)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'workouts' AND column_name = 'genres') THEN
        ALTER TABLE workouts ADD COLUMN genres TEXT[] DEFAULT ARRAY[]::TEXT[];
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'workouts' AND column_name = 'interval_stages') THEN
        ALTER TABLE workouts ADD COLUMN interval_stages JSONB DEFAULT '[]'::jsonb;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'workouts' AND column_name = 'prompt') THEN
        ALTER TABLE workouts ADD COLUMN prompt TEXT DEFAULT '';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'workouts' AND column_name = 'is_active') THEN
        ALTER TABLE workouts ADD COLUMN is_active BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Indexes for workouts
CREATE INDEX IF NOT EXISTS idx_workouts_user_id ON workouts(user_id);
CREATE INDEX IF NOT EXISTS idx_workouts_created_at ON workouts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workouts_genres ON workouts USING GIN (genres);
CREATE INDEX IF NOT EXISTS idx_workouts_is_active ON workouts(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_workouts_user_active ON workouts(user_id, is_active) WHERE is_active = TRUE;

-- Comments for workouts columns
COMMENT ON COLUMN workouts.genres IS 'Array of music genres selected for this workout';
COMMENT ON COLUMN workouts.interval_stages IS 'JSON array of interval stages with name, duration_minutes, hr_zone, and bpm_range';
COMMENT ON COLUMN workouts.prompt IS 'User-provided text prompt for additional context in track search and playlist generation';
COMMENT ON COLUMN workouts.is_active IS 'Indicates if this workout is currently active for the user';

-- ============================================================
-- 4. PLAYLISTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS playlists (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  workout_id UUID REFERENCES workouts(id) ON DELETE CASCADE,
  spotify_playlist_id TEXT,
  spotify_url TEXT,
  tracks JSONB NOT NULL DEFAULT '[]'::jsonb,
  total_duration_seconds INTEGER NOT NULL,
  generation_time_seconds FLOAT NOT NULL,
  shared BOOLEAN DEFAULT FALSE,
  share_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for playlists
CREATE INDEX IF NOT EXISTS idx_playlists_user_id ON playlists(user_id);
CREATE INDEX IF NOT EXISTS idx_playlists_workout_id ON playlists(workout_id);
CREATE INDEX IF NOT EXISTS idx_playlists_created_at ON playlists(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_playlist_tracks ON playlists USING GIN (tracks);

-- ============================================================
-- 5. CONVERSATIONS TABLE (AI Chat History)
-- ============================================================
CREATE TABLE IF NOT EXISTS conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  state VARCHAR(50) NOT NULL DEFAULT 'new',
  messages JSONB NOT NULL DEFAULT '[]'::jsonb,
  workout_intent JSONB,
  playlist JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for conversations
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_state ON conversations(state);

-- Comment for conversations table
COMMENT ON TABLE conversations IS 'Stores multi-turn conversation history for workout planning and AI learning';

-- ============================================================
-- 6. ERROR_LOGS TABLE (Error Tracking)
-- ============================================================
CREATE TABLE IF NOT EXISTS error_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  level TEXT NOT NULL CHECK (level IN ('ERROR', 'CRITICAL', 'WARNING')),
  message TEXT NOT NULL,
  error_type TEXT,
  error_details JSONB,
  stack_trace TEXT,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  request_path TEXT,
  request_method TEXT,
  request_body JSONB,
  response_status INTEGER,
  environment TEXT DEFAULT 'production',
  service_name TEXT DEFAULT 'runbeat-backend',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for error_logs
CREATE INDEX IF NOT EXISTS idx_error_logs_level ON error_logs(level);
CREATE INDEX IF NOT EXISTS idx_error_logs_created_at ON error_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_error_logs_user_id ON error_logs(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_error_logs_error_type ON error_logs(error_type) WHERE error_type IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_error_logs_environment ON error_logs(environment);

-- Function to automatically clean old error logs (older than 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_error_logs()
RETURNS void AS $$
BEGIN
  DELETE FROM error_logs
  WHERE created_at < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

-- Comment for error_logs table
COMMENT ON TABLE error_logs IS 'Stores application error logs for debugging and monitoring';

-- ============================================================
-- 7. ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE workouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE playlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE error_logs ENABLE ROW LEVEL SECURITY;

-- Drop existing policies (safe to run multiple times)
DROP POLICY IF EXISTS "Allow all operations on users" ON users;
DROP POLICY IF EXISTS "Allow all operations on workouts" ON workouts;
DROP POLICY IF EXISTS "Allow all operations on playlists" ON playlists;
DROP POLICY IF EXISTS "Allow all operations on conversations" ON conversations;
DROP POLICY IF EXISTS "Service role can insert error logs" ON error_logs;
DROP POLICY IF EXISTS "Authenticated service can insert error logs" ON error_logs;
DROP POLICY IF EXISTS "Service role can read all error logs" ON error_logs;
DROP POLICY IF EXISTS "Users can read their own error logs" ON error_logs;
DROP POLICY IF EXISTS "Service role can update error logs" ON error_logs;
DROP POLICY IF EXISTS "Service role can delete error logs" ON error_logs;

-- ============================================================
-- RLS Policies for USERS, WORKOUTS, PLAYLISTS, CONVERSATIONS
-- ============================================================
-- Note: Backend uses SUPABASE_SERVICE_KEY which bypasses RLS
-- These policies allow all operations for simplicity
-- Restrict later if needed

CREATE POLICY "Allow all operations on users"
  ON users FOR ALL
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow all operations on workouts"
  ON workouts FOR ALL
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow all operations on playlists"
  ON playlists FOR ALL
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow all operations on conversations"
  ON conversations FOR ALL
  USING (true)
  WITH CHECK (true);

-- ============================================================
-- RLS Policies for ERROR_LOGS (More Restrictive)
-- ============================================================

-- Service role can insert error logs
CREATE POLICY "Service role can insert error logs"
ON error_logs
FOR INSERT
TO service_role
WITH CHECK (true);

-- Authenticated service can insert error logs
CREATE POLICY "Authenticated service can insert error logs"
ON error_logs
FOR INSERT
TO authenticated
WITH CHECK (true);

-- Service role can read all error logs
CREATE POLICY "Service role can read all error logs"
ON error_logs
FOR SELECT
TO service_role
USING (true);

-- Users can read only their own error logs
CREATE POLICY "Users can read their own error logs"
ON error_logs
FOR SELECT
TO authenticated
USING (
  auth.uid()::text = user_id::text
  OR user_id IS NULL
);

-- Service role can update error logs
CREATE POLICY "Service role can update error logs"
ON error_logs
FOR UPDATE
TO service_role
USING (true)
WITH CHECK (true);

-- Service role can delete error logs
CREATE POLICY "Service role can delete error logs"
ON error_logs
FOR DELETE
TO service_role
USING (true);

-- ============================================================
-- 8. VERIFICATION
-- ============================================================
DO $$
DECLARE
  missing_columns TEXT := '';
BEGIN
  -- Check all required columns exist
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'workouts' AND column_name = 'genres') THEN
    missing_columns := missing_columns || 'workouts.genres, ';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'workouts' AND column_name = 'interval_stages') THEN
    missing_columns := missing_columns || 'workouts.interval_stages, ';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'workouts' AND column_name = 'prompt') THEN
    missing_columns := missing_columns || 'workouts.prompt, ';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'workouts' AND column_name = 'is_active') THEN
    missing_columns := missing_columns || 'workouts.is_active, ';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                 WHERE table_name = 'conversations') THEN
    missing_columns := missing_columns || 'conversations table, ';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                 WHERE table_name = 'error_logs') THEN
    missing_columns := missing_columns || 'error_logs table, ';
  END IF;

  IF missing_columns != '' THEN
    RAISE EXCEPTION 'Missing: %', missing_columns;
  END IF;

  -- Success message
  RAISE NOTICE '╔══════════════════════════════════════════════════════════╗';
  RAISE NOTICE '║  ✅ RunBeat Database Migration Completed Successfully!  ║';
  RAISE NOTICE '╚══════════════════════════════════════════════════════════╝';
  RAISE NOTICE '';
  RAISE NOTICE '📊 Created/Updated Tables:';
  RAISE NOTICE '   ✓ users';
  RAISE NOTICE '   ✓ workouts (with genres, interval_stages, prompt, is_active)';
  RAISE NOTICE '   ✓ playlists';
  RAISE NOTICE '   ✓ conversations';
  RAISE NOTICE '   ✓ error_logs';
  RAISE NOTICE '';
  RAISE NOTICE '🔒 RLS Policies:';
  RAISE NOTICE '   ✓ All tables have RLS enabled';
  RAISE NOTICE '   ✓ Service role has full access';
  RAISE NOTICE '   ✓ Error logs have restricted access';
  RAISE NOTICE '';
  RAISE NOTICE '📈 Indexes:';
  RAISE NOTICE '   ✓ Performance indexes created for all tables';
  RAISE NOTICE '   ✓ GIN indexes for JSONB columns';
  RAISE NOTICE '';
  RAISE NOTICE '🎯 Next Steps:';
  RAISE NOTICE '   1. Restart your backend server';
  RAISE NOTICE '   2. Test creating a workout with genres';
  RAISE NOTICE '   3. Test AI chat conversations';
  RAISE NOTICE '   4. Verify error logging works';
  RAISE NOTICE '';
END $$;

-- ============================================================
-- Migration Complete! 🎉
-- ============================================================
-- Version: 2.0
-- Date: 2024
-- Description: Complete database schema for RunBeat
-- Includes: Users, Workouts, Playlists, Conversations, Error Logs
-- ============================================================

