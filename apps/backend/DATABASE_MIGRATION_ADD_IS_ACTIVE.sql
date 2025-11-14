-- ============================================================
-- RunBeat Database Migration - Add is_active column to workouts
-- ============================================================
-- This migration adds the is_active column to workouts table
-- Execute this SQL in Supabase SQL Editor
-- ============================================================

-- Add is_active column to workouts table if it doesn't exist
ALTER TABLE workouts
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT FALSE;

-- Create index for efficient querying of active workouts
CREATE INDEX IF NOT EXISTS idx_workouts_is_active ON workouts(is_active) WHERE is_active = TRUE;

-- Create index for user_id + is_active combination (common query pattern)
CREATE INDEX IF NOT EXISTS idx_workouts_user_active ON workouts(user_id, is_active) WHERE is_active = TRUE;

-- Optional: Set all existing workouts to inactive (if you want to start fresh)
-- UPDATE workouts SET is_active = FALSE WHERE is_active IS NULL;

