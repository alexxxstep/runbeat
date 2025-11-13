-- Migration: Add prompt field to workouts table
-- Execute this SQL in Supabase SQL Editor

-- Add prompt column (text field for user's custom description)
ALTER TABLE workouts
ADD COLUMN IF NOT EXISTS prompt TEXT DEFAULT '';

-- Add comment for documentation
COMMENT ON COLUMN workouts.prompt IS 'User-provided text prompt for additional context in track search and playlist generation';

