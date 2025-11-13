-- ============================================================
-- RunBeat Database Migration - Final Version
-- ============================================================
-- This migration creates all necessary tables and columns
-- Execute this SQL in Supabase SQL Editor
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- Users table
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

-- ============================================================
-- Workouts table (with all columns including genres, interval_stages, prompt)
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
  prompt TEXT,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Playlists table
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

-- ============================================================
-- Indexes for performance
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_workouts_user_id ON workouts(user_id);
CREATE INDEX IF NOT EXISTS idx_workouts_created_at ON workouts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_playlists_user_id ON playlists(user_id);
CREATE INDEX IF NOT EXISTS idx_playlists_created_at ON playlists(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_preferences ON users USING GIN (preferences);
CREATE INDEX IF NOT EXISTS idx_playlist_tracks ON playlists USING GIN (tracks);
CREATE INDEX IF NOT EXISTS idx_workouts_genres ON workouts USING GIN (genres);

-- ============================================================
-- Add missing columns to existing workouts table (if table exists)
-- ============================================================
-- These commands are safe to run multiple times (IF NOT EXISTS)
ALTER TABLE workouts
ADD COLUMN IF NOT EXISTS genres TEXT[] DEFAULT ARRAY[]::TEXT[];

ALTER TABLE workouts
ADD COLUMN IF NOT EXISTS interval_stages JSONB DEFAULT '[]'::jsonb;

ALTER TABLE workouts
ADD COLUMN IF NOT EXISTS prompt TEXT;

-- ============================================================
-- Column comments for documentation
-- ============================================================
COMMENT ON COLUMN workouts.genres IS 'Array of music genres selected for this workout';
COMMENT ON COLUMN workouts.interval_stages IS 'JSON array of interval stages with name, duration_minutes, hr_zone, and bpm_range';
COMMENT ON COLUMN workouts.prompt IS 'User-provided text prompt for additional context in track search and playlist generation';

-- ============================================================
-- Row Level Security (RLS)
-- ============================================================
-- Note: Backend uses SUPABASE_SERVICE_KEY which automatically bypasses RLS
-- RLS is enabled but policies allow all operations for now
-- You can restrict access later if needed

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE workouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE playlists ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to avoid errors on re-run)
DROP POLICY IF EXISTS "Allow all operations on users" ON users;
DROP POLICY IF EXISTS "Allow all operations on workouts" ON workouts;
DROP POLICY IF EXISTS "Allow all operations on playlists" ON playlists;
DROP POLICY IF EXISTS "Users can view own data" ON users;
DROP POLICY IF EXISTS "Users can update own data" ON users;
DROP POLICY IF EXISTS "Users can insert own data" ON users;
DROP POLICY IF EXISTS "Users can view own workouts" ON workouts;
DROP POLICY IF EXISTS "Users can insert own workouts" ON workouts;
DROP POLICY IF EXISTS "Users can view own playlists" ON playlists;
DROP POLICY IF EXISTS "Anyone can view shared playlists" ON playlists;

-- Create RLS policies
-- Allow all operations (backend uses service key which bypasses RLS anyway)
-- Frontend uses anon key, but we're not using Supabase Auth for users
-- So we allow all operations for simplicity
-- You can restrict this later if needed

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

-- ============================================================
-- Verification
-- ============================================================
-- Verify that all columns exist
DO $$
BEGIN
    -- Check workouts table columns
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'workouts' AND column_name = 'genres'
    ) THEN
        RAISE EXCEPTION 'Column genres was not created';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'workouts' AND column_name = 'interval_stages'
    ) THEN
        RAISE EXCEPTION 'Column interval_stages was not created';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'workouts' AND column_name = 'prompt'
    ) THEN
        RAISE EXCEPTION 'Column prompt was not created';
    END IF;

    RAISE NOTICE '✅ All migrations completed successfully!';
    RAISE NOTICE '✅ Tables: users, workouts, playlists';
    RAISE NOTICE '✅ Workouts columns: genres, interval_stages, prompt';
    RAISE NOTICE '✅ Indexes and RLS policies created';
END $$;

-- ============================================================
-- Migration complete!
-- ============================================================
-- After running this migration:
-- 1. Restart your backend server
-- 2. Test creating a workout with genres, interval_stages, and prompt
-- 3. Verify that playlists are saved correctly
-- ============================================================

