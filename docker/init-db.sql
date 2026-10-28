-- PostgreSQL initialisation run by docker-entrypoint-initdb.d
-- Creates the restricted tamper role used by the demo tamper/restore endpoints.
-- The main application user (trueroll_app) is created by the postgres image from
-- the POSTGRES_USER env var and already owns the database.

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT FROM pg_catalog.pg_roles WHERE rolname = 'trueroll_tamper'
  ) THEN
    CREATE ROLE trueroll_tamper
      LOGIN
      PASSWORD 'trueroll_tamper_password'
      NOSUPERUSER NOCREATEDB NOCREATEROLE;
  END IF;
END
$$;

-- Grant connect so the tamper role can reach the DB
GRANT CONNECT ON DATABASE trueroll TO trueroll_tamper;

-- Note: table-level permissions (GRANT/REVOKE on audit_entry) are applied after
-- schema creation by init_db.py. In a production deployment these would be set
-- via a post-migration hook in your CI pipeline.
