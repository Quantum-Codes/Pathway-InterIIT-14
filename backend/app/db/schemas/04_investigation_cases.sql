-- =============================================================================
-- TABLE: investigation_cases
-- PURPOSE: Fraud investigation case management and tracking
-- =============================================================================

CREATE TABLE
IF NOT EXISTS investigation_cases
(
    -- Primary Key
    id VARCHAR
(50) PRIMARY KEY,  -- Format: CASE-YYYY-NNNNN
    
    -- Foreign Keys
    user_id INTEGER NOT NULL,
    
    -- Case Details
    case_title VARCHAR
(255) NOT NULL,
    case_description TEXT,
    case_type VARCHAR
(50) NOT NULL,
    severity VARCHAR
(20) DEFAULT 'medium',
    
    -- Case Status
    status VARCHAR
(20) DEFAULT 'open',
    priority VARCHAR
(20) DEFAULT 'medium',
    
    -- Assignment & Ownership
    assigned_to VARCHAR
(100),
    assigned_at DATETIME,
    created_by VARCHAR
(100) NOT NULL,
    
    -- Evidence & Context
    transaction_ids TEXT,  -- JSON array of transaction IDs
    alert_ids TEXT,  -- JSON array of alert IDs
    evidence_urls TEXT,  -- JSON array of evidence file URLs
    
    -- Investigation Progress
    investigation_notes TEXT,
    findings TEXT,
    recommended_action TEXT,
    
    -- Resolution
    resolved_at DATETIME,
    resolution_notes TEXT,
    outcome VARCHAR
(50),
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    due_date DATETIME,
    
    -- Foreign Key Constraints
    FOREIGN KEY
(user_id) REFERENCES users
(id) ON
DELETE CASCADE,
    
    -- Check Constraints
    CHECK (case_type
IN
('fraud', 'aml', 'kyc', 'sanctions', 'behavioral', 'other')),
    CHECK
(severity IN
('low', 'medium', 'high', 'critical')),
    CHECK
(status IN
('open', 'investigating', 'pending_review', 'closed', 'escalated')),
    CHECK
(priority IN
('low', 'medium', 'high', 'critical')),
    CHECK
(outcome IN
('cleared', 'fraud_confirmed', 'account_suspended', 'legal_action', 'pending', NULL))
);

-- Indexes for Performance
CREATE INDEX
IF NOT EXISTS idx_cases_user_id ON investigation_cases
(user_id);
CREATE INDEX
IF NOT EXISTS idx_cases_status ON investigation_cases
(status);
CREATE INDEX
IF NOT EXISTS idx_cases_priority ON investigation_cases
(priority);
CREATE INDEX
IF NOT EXISTS idx_cases_assigned_to ON investigation_cases
(assigned_to);
CREATE INDEX
IF NOT EXISTS idx_cases_created ON investigation_cases
(created_at);
CREATE INDEX
IF NOT EXISTS idx_cases_due_date ON investigation_cases
(due_date);

-- Composite Indexes for Dashboard Queries
CREATE INDEX
IF NOT EXISTS idx_cases_user_status ON investigation_cases
(user_id, status);
CREATE INDEX
IF NOT EXISTS idx_cases_status_priority ON investigation_cases
(status, priority DESC);

-- Comments
-- id: Auto-generated format CASE-YYYY-NNNNN (e.g., CASE-2025-00123)
-- transaction_ids: JSON array storing related transaction IDs as evidence
-- alert_ids: JSON array of alerts that triggered this investigation
-- evidence_urls: JSON array of document/file URLs for evidence storage
