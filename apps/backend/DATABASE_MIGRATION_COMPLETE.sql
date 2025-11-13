-- Complete Database Migration for RunBeat
-- Execute this SQL in Supabase SQL Editor
-- This migration adds all missing columns to the workouts table

-- Add genres column (array of text)
ALTER TABLE workouts
ADD COLUMN IF NOT EXISTS genres TEXT[] DEFAULT ARRAY[]::TEXT[];

-- Add interval_stages column (JSONB for flexible structure)
ALTER TABLE workouts
ADD COLUMN IF NOT EXISTS interval_stages JSONB DEFAULT '[]'::jsonb;

-- Add prompt column (text field for user's custom description)
ALTER TABLE workouts
ADD COLUMN IF NOT EXISTS prompt TEXT;

-- Add comments for documentation
COMMENT ON COLUMN workouts.genres IS 'Array of music genres selected for this workout';
COMMENT ON COLUMN workouts.interval_stages IS 'JSON array of interval stages with name, duration_minutes, hr_zone, and bpm_range';
COMMENT ON COLUMN workouts.prompt IS 'User-provided text prompt for additional context in track search and playlist generation';

-- Verify columns exist (this will show an error if table doesn't exist)
DO $$
BEGIN
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

    RAISE NOTICE 'All columns successfully added to workouts table';
END $$;

