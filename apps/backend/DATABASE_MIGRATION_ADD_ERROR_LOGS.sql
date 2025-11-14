-- ============================================================
-- RunBeat Database Migration - Error Logs Table
-- ============================================================
-- This migration creates a table for storing error logs
-- Execute this SQL in Supabase SQL Editor
-- ============================================================

-- Error logs table
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

-- Indexes for efficient querying
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

-- Optional: Create a scheduled job to run cleanup (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-error-logs', '0 2 * * *', 'SELECT cleanup_old_error_logs()');

