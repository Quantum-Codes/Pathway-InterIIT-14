-- =============================================================================
-- TABLE: cns_databases
-- PURPOSE: CNS sanctions database metadata and management
-- =============================================================================

CREATE TABLE
IF NOT EXISTS cns_databases
(
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Database Identity
    database_name VARCHAR
(255) UNIQUE NOT NULL,
    database_code VARCHAR
(50) UNIQUE NOT NULL,
    database_type VARCHAR
(50) NOT NULL,
    
    -- Database Details
    description TEXT,
    source_url TEXT,
    source_organization VARCHAR
(255),
    
    -- Database Status
    is_active BOOLEAN DEFAULT 1,
    last_updated DATETIME,
    update_frequency VARCHAR
(50),
    
    -- Statistics
    total_entries INTEGER DEFAULT 0,
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Check Constraints
    CHECK
(database_type IN
('sanctions', 'watchlist', 'pep', 'adverse_media', 'enforcement'))
);

-- Indexes for Performance
CREATE INDEX
IF NOT EXISTS idx_cns_db_code ON cns_databases
(database_code);
CREATE INDEX
IF NOT EXISTS idx_cns_db_type ON cns_databases
(database_type);
CREATE INDEX
IF NOT EXISTS idx_cns_db_active ON cns_databases
(is_active);

-- Comments
-- database_code: Short code for quick reference (e.g., OFAC, UN, EU, INTERPOL)
-- database_type: Category of the sanctions/watchlist database
-- update_frequency: How often the database is updated (e.g., "daily", "weekly")
