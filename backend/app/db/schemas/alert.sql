-- =============================================================================
-- TABLE: compliance_alerts
-- PURPOSE: Security alerts, fraud notifications, and compliance warnings
-- =============================================================================

CREATE TABLE
IF NOT EXISTS compliance_alerts
(
    -- Primary Key
    id  INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Keys
    user_id INTEGER,
    transaction_id INTEGER,
    
    -- Alert Classification
    alert_type VARCHAR
(50) NOT NULL,
    severity VARCHAR
(20) NOT NULL DEFAULT 'medium',
    title VARCHAR
(255) NOT NULL,
    description TEXT,
    
    -- Alert Details
    entity_id VARCHAR
(100),
    entity_type VARCHAR
(50),
    rps360 REAL DEFAULT 0.0,
    
    -- Alert Status
    status VARCHAR
(20) DEFAULT 'active',
    priority VARCHAR
(20) DEFAULT 'medium',
    
    -- Dismissal & Acknowledgment
    is_acknowledged BOOLEAN DEFAULT 0,
    acknowledged_at DATETIME,
    acknowledged_by VARCHAR
(100),
    dismissal_reason TEXT,
    
    -- Source & Context
    source VARCHAR
(100),
    triggered_by VARCHAR
(100),
    alert_metadata TEXT,  -- JSON field for additional context
    
    -- Timestamps
    triggered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY
(user_id) REFERENCES Users
(id) ON
DELETE
SET NULL
,
    FOREIGN KEY
(transaction_id) REFERENCES transactions
(id) ON
DELETE
SET NULL
,
    
    -- Check Constraints
    CHECK
(alert_type IN
('kyc_alert', 'transaction_alert', 'fraud_alert', 'aml_alert', 'sanction_alert', 'behavioral_alert', 'system_alert')),
    CHECK
(severity IN
('low', 'medium', 'high', 'critical')),
    CHECK
(status IN
('active', 'investigating', 'resolved', 'dismissed', 'escalated')),
    CHECK
(priority IN
('low', 'medium', 'high', 'critical'))
);

-- Indexes for Performance
CREATE INDEX
IF NOT EXISTS idx_alerts_user_id ON compliance_alerts
(user_id);
CREATE INDEX
IF NOT EXISTS idx_alerts_transaction_id ON compliance_alerts
(transaction_id);
CREATE INDEX
IF NOT EXISTS idx_alerts_type ON compliance_alerts
(alert_type);
CREATE INDEX
IF NOT EXISTS idx_alerts_severity ON compliance_alerts
(severity);
CREATE INDEX
IF NOT EXISTS idx_alerts_status ON compliance_alerts
(status);
CREATE INDEX
IF NOT EXISTS idx_alerts_created ON compliance_alerts
(created_at);
CREATE INDEX
IF NOT EXISTS idx_alerts_acknowledged ON compliance_alerts
(is_acknowledged);

-- Composite Indexes for Dashboard Queries
CREATE INDEX
IF NOT EXISTS idx_alerts_severity_created ON compliance_alerts
(severity DESC, created_at DESC);
CREATE INDEX
IF NOT EXISTS idx_alerts_user_severity ON compliance_alerts
(user_id, severity);
CREATE INDEX
IF NOT EXISTS idx_alerts_status_priority ON compliance_alerts
(status, priority DESC);
