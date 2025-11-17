-- ============================================================
-- RunBeat Supabase Cleanup Script
-- ============================================================
-- Purpose:
--   Drops all non-system tables from the `public` schema that are
--   NOT part of the active RunBeat data model.
--
-- Usage:
--   1. Open Supabase SQL Editor.
--   2. Copy-paste this entire script.
--   3. Review the NOTICE output (tables slated for removal).
--   4. Execute once you're confident the list is correct.
--
-- Safety:
--   - Only processes tables from the 'public' schema.
--   - Keeps all tables defined in `keep_tables`.
--   - Ignores Supabase system schemas (pg_catalog, auth, storage, vault, etc.).
--   - Uses CASCADE to clean up dependent objects automatically.
--   - Handles errors gracefully (skips tables that cannot be dropped).
--
-- Update:
--   Adjust the `keep_tables` array if new tables are added to the project.
-- ============================================================

DO $cleanup$
DECLARE
    keep_tables constant text[] := ARRAY[
        'users',
        'workouts',
        'playlists',
        'conversations',
        'error_logs'
    ];
    ignored_schemas constant text[] := ARRAY[
        'pg_catalog',
        'information_schema',
        'pg_toast',
        'pg_temp_1',
        'pg_toast_temp_1',
        'storage',
        'auth',
        'realtime',
        'vault',
        'extensions',
        'graphql',
        'graphql_public',
        'net',
        'pgsodium',
        'pgsodium_masks'
    ];
    rec record;
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE '🔍  Starting cleanup of unused tables (public schema)...';
    RAISE NOTICE 'Keeping tables: %', array_to_string(keep_tables, ', ');
    RAISE NOTICE '============================================================';

    -- Тільки обробляємо таблиці зі схеми 'public'
    FOR rec IN
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_type = 'BASE TABLE'
          AND table_schema = 'public'
          AND table_name <> ALL(keep_tables)
    LOOP
        BEGIN
            RAISE NOTICE '🗑️  Dropping %.% ...', rec.table_schema, rec.table_name;
            EXECUTE format('DROP TABLE IF EXISTS %I.%I CASCADE;', rec.table_schema, rec.table_name);
            RAISE NOTICE '✅  Dropped %.%', rec.table_schema, rec.table_name;
        EXCEPTION
            WHEN insufficient_privilege THEN
                RAISE WARNING '⚠️  Insufficient privileges to drop %.% (skipping)', rec.table_schema, rec.table_name;
            WHEN OTHERS THEN
                RAISE WARNING '⚠️  Error dropping %.%: % (skipping)', rec.table_schema, rec.table_name, SQLERRM;
        END;
    END LOOP;

    RAISE NOTICE '============================================================';
    RAISE NOTICE '🎉  Cleanup complete.';
    RAISE NOTICE '============================================================';
END;
$cleanup$;

