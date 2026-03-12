-- =============================================================================
-- COMPLIANCE & FRAUD DETECTION DATABASE SCHEMA
-- =============================================================================
-- Purpose: Complete database schema for compliance, fraud detection, and KYC
-- Version: 2.0
-- Created: December 3, 2025
-- Database: SQLite (compatible with PostgreSQL/MySQL with minor modifications)
-- =============================================================================

-- USAGE:
-- To create all tables, run this file:
--   sqlite3 database.db < 00_create_all.sql
--
-- Or source individual files in order:
--   01_users.sql
--   02_transactions.sql
--   alert.sql
--   04_investigation_cases.sql
--   05_account_holds.sql
--   06_cns_databases.sql
--   07_cns_matches.sql
--   08_organization_settings.sql
--   09_notification_settings.sql

-- =============================================================================
-- ENABLE FOREIGN KEY SUPPORT (SQLite)
-- =============================================================================
PRAGMA foreign_keys = ON;

-- =============================================================================
-- TABLE CREATION ORDER (respects foreign key dependencies)
-- =============================================================================

.read 01_users.sql
.read 02_transactions.sql
.read alert.sql
.read 04_investigation_cases.sql
.read 05_account_holds.sql
.read 06_cns_databases.sql
.read 07_cns_matches.sql
.read 08_organization_settings.sql
.read 09_notification_settings.sql

-- =============================================================================
-- DATABASE RELATIONSHIPS SUMMARY
-- =============================================================================

-- users (1) → (N) transactions
-- users (1) → (N) compliance_alerts
-- users (1) → (N) investigation_cases
-- users (1) → (N) account_holds
-- users (1) → (1) notification_settings
--
-- transactions (1) → (N) compliance_alerts
--
-- investigation_cases (1) → (N) account_holds
--
-- cns_databases (1) → (N) cns_matches

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- List all tables
SELECT '=== DATABASE TABLES ===' AS info;
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

-- Count tables
SELECT '=== TABLE COUNT ===' AS info;
SELECT COUNT(*) AS table_count FROM sqlite_master WHERE type='table';

-- List all indexes
SELECT '=== DATABASE INDEXES ===' AS info;
SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;

-- =============================================================================
-- INITIAL DATA (Optional)
-- =============================================================================

-- Default organization settings
INSERT OR IGNORE INTO organization_settings (
    organization_name,
    organization_code,
    contact_email,
    fraud_threshold,
    aml_threshold,
    kyc_threshold
) VALUES (
    'Default Organization',
    'DEFAULT',
    'compliance@example.com',
    70.0,
    75.0,
    60.0
);

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================
