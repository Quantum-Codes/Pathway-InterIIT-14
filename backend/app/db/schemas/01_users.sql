-- =============================================================================
-- TABLE: users
-- PURPOSE: User/Applicant information with KYC data and fraud scores
-- =============================================================================

CREATE TABLE
IF NOT EXISTS users
(
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Core Identity
    entity_id VARCHAR
(50) UNIQUE NOT NULL,
    applicant_name VARCHAR
(255) NOT NULL,
    email VARCHAR
(255) UNIQUE,
    phone VARCHAR
(20),
    
    -- KYC Status
    kyc_status VARCHAR
(20) DEFAULT 'pending',
    kyc_verified_at DATETIME,
    kyc_document_url TEXT,
    
    -- Risk & Fraud Scoring
    i_360_score FLOAT DEFAULT 0.0,
    i_not_score FLOAT DEFAULT 0.0,
    suspicious_score FLOAT DEFAULT 0.0,
    risk_level VARCHAR
(20) DEFAULT 'low',
    
    -- Account Status
    is_blacklisted BOOLEAN DEFAULT 0,
    blacklist_reason TEXT,
    blacklisted_at DATETIME,
    account_status VARCHAR
(20) DEFAULT 'active',
    
    -- Location & Demographics
    address TEXT,
    city VARCHAR
(100),
    state VARCHAR
(100),
    country VARCHAR
(100) DEFAULT 'India',
    postal_code VARCHAR
(20),
    date_of_birth DATE,
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME,
    
    -- Constraints
    CHECK
(kyc_status IN
('pending', 'approved', 'rejected', 'under_review')),
    CHECK
(risk_level IN
('low', 'medium', 'high', 'critical')),
    CHECK
(account_status IN
('active', 'suspended', 'closed', 'under_investigation')),
    CHECK
(i_360_score BETWEEN 0 AND 100),
    CHECK
(i_not_score BETWEEN 0 AND 100),
    CHECK
(suspicious_score BETWEEN 0 AND 100)
);

-- Indexes for Performance
CREATE INDEX
IF NOT EXISTS idx_users_entity_id ON users
(entity_id);
CREATE INDEX
IF NOT EXISTS idx_users_email ON users
(email);
CREATE INDEX
IF NOT EXISTS idx_users_kyc_status ON users
(kyc_status);
CREATE INDEX
IF NOT EXISTS idx_users_risk_level ON users
(risk_level);
CREATE INDEX
IF NOT EXISTS idx_users_blacklisted ON users
(is_blacklisted);
CREATE INDEX
IF NOT EXISTS idx_users_account_status ON users
(account_status);

-- Comments
-- entity_id: Unique identifier for applicant (e.g., APP-2024-12345)
-- i_360_score: Comprehensive 360-degree risk assessment (0-100)
-- i_not_score: Intelligent threat detection score (0-100)
-- suspicious_score: Real-time suspicious activity score (0-100)
