-- =============================================================================
-- TABLE: cns_matches
-- PURPOSE: CNS sanctions and watchlist entries for screening
-- =============================================================================

CREATE TABLE
IF NOT EXISTS cns_matches
(
    -- Primary Key
    id VARCHAR
(50) PRIMARY KEY,  -- Format: CNS-NNNNN
    
    -- Foreign Keys
    database_id INTEGER NOT NULL,
    
    -- Entity Information
    entity_name VARCHAR
(255) NOT NULL,
    entity_type VARCHAR
(50),
    aliases TEXT,  -- JSON array of alternative names
    
    -- Identification
    passport_number VARCHAR
(50),
    national_id VARCHAR
(50),
    date_of_birth DATE,
    place_of_birth VARCHAR
(255),
    nationality VARCHAR
(100),
    
    -- Sanctions Details
    sanctions_type VARCHAR
(100),
    sanctions_reason TEXT,
    sanctions_date DATE,
    
    -- Location
    address TEXT,
    city VARCHAR
(100),
    country VARCHAR
(100),
    
    -- Risk Assessment
    risk_category VARCHAR
(50),
    match_confidence FLOAT DEFAULT 0.0,
    
    -- Additional Context
    additional_info TEXT,
    source_url TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT 1,
    expiry_date DATE,
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_verified DATETIME,
    
    -- Foreign Key Constraints
    FOREIGN KEY
(database_id) REFERENCES cns_databases
(id) ON
DELETE CASCADE,
    
    -- Check Constraints
    CHECK (entity_type
IN
('individual', 'organization', 'vessel', 'aircraft')),
    CHECK
(risk_category IN
('low', 'medium', 'high', 'critical')),
    CHECK
(match_confidence BETWEEN 0 AND 100)
);

-- Indexes for Performance
CREATE INDEX
IF NOT EXISTS idx_cns_database_id ON cns_matches
(database_id);
CREATE INDEX
IF NOT EXISTS idx_cns_entity_name ON cns_matches
(entity_name);
CREATE INDEX
IF NOT EXISTS idx_cns_entity_type ON cns_matches
(entity_type);
CREATE INDEX
IF NOT EXISTS idx_cns_nationality ON cns_matches
(nationality);
CREATE INDEX
IF NOT EXISTS idx_cns_active ON cns_matches
(is_active);
CREATE INDEX
IF NOT EXISTS idx_cns_risk ON cns_matches
(risk_category);

-- Composite Indexes for Name Matching
CREATE INDEX
IF NOT EXISTS idx_cns_name_search ON cns_matches
(entity_name, nationality);
CREATE INDEX
IF NOT EXISTS idx_cns_database_type ON cns_matches
(database_id, entity_type);

-- Comments
-- id: Format CNS-NNNNN (e.g., CNS-12345)
-- aliases: JSON array of alternative names for fuzzy matching
-- match_confidence: Confidence score for automated matching (0-100)
-- expiry_date: When sanctions expire (NULL for permanent sanctions)
