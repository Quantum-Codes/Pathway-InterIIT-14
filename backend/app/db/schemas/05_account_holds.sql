-- =============================================================================
-- TABLE: account_holds
-- PURPOSE: Account restriction and hold management
-- =============================================================================

CREATE TABLE
IF NOT EXISTS account_holds
(
    -- Primary Key
    id VARCHAR
(50) PRIMARY KEY,  -- Format: HOLD-YYYY-NNNNN
    
    -- Foreign Keys
    user_id INTEGER NOT NULL,
    case_id VARCHAR
(50),
    
    -- Hold Details
    hold_type VARCHAR
(50) NOT NULL,
    hold_reason TEXT NOT NULL,
    severity VARCHAR
(20) DEFAULT 'medium',
    
    -- Hold Status
    status VARCHAR
(20) DEFAULT 'active',
    
    -- Hold Duration
    hold_placed_at DATETIME NOT NULL,
    hold_expires_at DATETIME,
    hold_released_at DATETIME,
    
    -- Actions Restricted
    restrictions TEXT,  -- JSON array of restricted actions
    
    -- Authorization
    placed_by VARCHAR
(100) NOT NULL,
    approved_by VARCHAR
(100),
    released_by VARCHAR
(100),
    
    -- Resolution
    release_reason TEXT,
    release_notes TEXT,
    
    -- Notifications
    notification_sent BOOLEAN DEFAULT 0,
    notification_sent_at DATETIME,
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY
(user_id) REFERENCES users
(id) ON
DELETE CASCADE,
    FOREIGN KEY (case_id)
REFERENCES investigation_cases
(id) ON
DELETE
SET NULL
,
    
    -- Check Constraints
    CHECK
(hold_type IN
('temporary', 'permanent', 'investigation', 'regulatory', 'fraud')),
    CHECK
(severity IN
('low', 'medium', 'high', 'critical')),
    CHECK
(status IN
('active', 'expired', 'released', 'appealed'))
);

-- Indexes for Performance
CREATE INDEX
IF NOT EXISTS idx_holds_user_id ON account_holds
(user_id);
CREATE INDEX
IF NOT EXISTS idx_holds_case_id ON account_holds
(case_id);
CREATE INDEX
IF NOT EXISTS idx_holds_status ON account_holds
(status);
CREATE INDEX
IF NOT EXISTS idx_holds_type ON account_holds
(hold_type);
CREATE INDEX
IF NOT EXISTS idx_holds_placed_at ON account_holds
(hold_placed_at);

-- Composite Indexes for Dashboard Queries
CREATE INDEX
IF NOT EXISTS idx_holds_expires ON account_holds
(hold_expires_at, status);
CREATE INDEX
IF NOT EXISTS idx_holds_user_status ON account_holds
(user_id, status);

-- Comments
-- id: Auto-generated format HOLD-YYYY-NNNNN (e.g., HOLD-2025-00456)
-- restrictions: JSON array of actions that are blocked (e.g., ["withdraw", "transfer"])
-- hold_expires_at: Auto-expiry timestamp for temporary holds
-- case_id: Optional link to investigation case that triggered the hold
