-- Migration: Add genres and interval_stages to workouts table
-- Execute this SQL in Supabase SQL Editor

-- Add genres column (array of text)
ALTER TABLE workouts
ADD COLUMN IF NOT EXISTS genres TEXT[] DEFAULT ARRAY[]::TEXT[];

-- Add interval_stages column (JSONB for flexible structure)
ALTER TABLE workouts
ADD COLUMN IF NOT EXISTS interval_stages JSONB DEFAULT '[]'::jsonb;

-- Add comment for documentation
COMMENT ON COLUMN workouts.genres IS 'Array of music genres selected for this workout';
COMMENT ON COLUMN workouts.interval_stages IS 'JSON array of interval stages with name, duration_minutes, hr_zone, and bpm_range';

