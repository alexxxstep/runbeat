-- ============================================================
-- RunBeat Database Migration - Error Logs RLS Policies
-- ============================================================
-- This migration adds Row Level Security (RLS) policies to error_logs table
-- Execute this SQL in Supabase SQL Editor
-- ============================================================

-- Enable RLS on error_logs table
ALTER TABLE error_logs ENABLE ROW LEVEL SECURITY;

-- Policy 1: Allow service role (backend) to insert error logs
-- This allows the backend service to log errors
CREATE POLICY "Service role can insert error logs"
ON error_logs
FOR INSERT
TO service_role
WITH CHECK (true);

-- Policy 2: Allow authenticated service role to insert error logs
-- This allows authenticated backend requests to log errors
CREATE POLICY "Authenticated service can insert error logs"
ON error_logs
FOR INSERT
TO authenticated
WITH CHECK (true);

-- Policy 3: Allow service role to read all error logs
-- This allows backend/admin tools to read all logs
CREATE POLICY "Service role can read all error logs"
ON error_logs
FOR SELECT
TO service_role
USING (true);

-- Policy 4: Allow authenticated users to read only their own error logs
-- Users can only see errors related to their user_id
CREATE POLICY "Users can read their own error logs"
ON error_logs
FOR SELECT
TO authenticated
USING (
  auth.uid()::text = user_id::text
  OR user_id IS NULL  -- Allow reading logs without user_id (system errors)
);

-- Policy 5: Allow service role to update error logs (for cleanup, etc.)
CREATE POLICY "Service role can update error logs"
ON error_logs
FOR UPDATE
TO service_role
USING (true)
WITH CHECK (true);

-- Policy 6: Allow service role to delete error logs (for cleanup)
CREATE POLICY "Service role can delete error logs"
ON error_logs
FOR DELETE
TO service_role
USING (true);

-- Note: Anonymous users (anon role) cannot access error_logs table
-- This ensures that error logs are not publicly accessible

