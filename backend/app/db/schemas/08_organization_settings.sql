-- =============================================================================
-- TABLE: organization_settings
-- PURPOSE: System-wide configuration and organization preferences
-- =============================================================================

CREATE TABLE IF NOT EXISTS organization_settings (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Organization Identity
    organization_name VARCHAR(255) NOT NULL,
    organization_code VARCHAR(50) UNIQUE NOT NULL,
    
    -- Branding
    logo_url TEXT,
    primary_color VARCHAR(20),
    secondary_color VARCHAR(20),
    
    -- Contact Information
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    support_url TEXT,
    
    -- Risk Thresholds
    fraud_threshold FLOAT DEFAULT 70.0,
    aml_threshold FLOAT DEFAULT 75.0,
    kyc_threshold FLOAT DEFAULT 60.0,
    
    -- Alert Settings
    enable_email_alerts BOOLEAN DEFAULT 1,
    enable_sms_alerts BOOLEAN DEFAULT 0,
    enable_dashboard_alerts BOOLEAN DEFAULT 1,
    
    -- Auto-Actions
    auto_flag_high_risk BOOLEAN DEFAULT 1,
    auto_hold_critical_risk BOOLEAN DEFAULT 0,
    auto_escalate_threshold FLOAT DEFAULT 90.0,
    
    -- Compliance Settings
    require_dual_approval BOOLEAN DEFAULT 0,
    data_retention_days INTEGER DEFAULT 2555,  -- 7 years
    enable_audit_logging BOOLEAN DEFAULT 1,
    
    -- Feature Flags
    enable_cns_screening BOOLEAN DEFAULT 1,
    enable_transaction_monitoring BOOLEAN DEFAULT 1,
    enable_behavioral_analysis BOOLEAN DEFAULT 1,
    
    -- API & Integration
    api_rate_limit INTEGER DEFAULT 1000,
    webhook_url TEXT,
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Check Constraints
    CHECK (fraud_threshold BETWEEN 0 AND 100),
    CHECK (aml_threshold BETWEEN 0 AND 100),
    CHECK (kyc_threshold BETWEEN 0 AND 100),
    CHECK (auto_escalate_threshold BETWEEN 0 AND 100),
    CHECK (data_retention_days > 0),
    CHECK (api_rate_limit > 0)
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_org_code ON organization_settings(organization_code);

-- Comments
-- fraud_threshold: Suspicious score threshold to flag transactions (0-100)
-- aml_threshold: Anti-money laundering detection threshold (0-100)
-- data_retention_days: Default 2555 days = 7 years (typical compliance requirement)
-- auto_escalate_threshold: Score that triggers automatic escalation (0-100)
