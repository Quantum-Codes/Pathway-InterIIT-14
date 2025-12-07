-- =============================================================================
-- DATABASE RESET SCRIPT - CLEAR EXISTING DATA AND RECREATE TABLES
-- =============================================================================
-- This script will drop all existing tables and recreate them with the new schema
-- WARNING: This will delete ALL existing data except admin accounts
-- =============================================================================

-- Drop existing tables in reverse dependency order
DROP TABLE IF EXISTS notification_settings CASCADE;
DROP TABLE IF EXISTS account_holds CASCADE;
DROP TABLE IF EXISTS investigation_cases CASCADE;
DROP TABLE IF EXISTS compliance_alerts CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS toxicityhistory CASCADE;
DROP TABLE IF EXISTS user_sanction_matches CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS organization_settings CASCADE;

-- Keep admin tables (admins, audit_logs, system_health, system_metrics)
-- These will not be dropped to preserve admin/superadmin accounts

-- =============================================================================
-- TABLE: users
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Core Identity
    entity_id VARCHAR(50) UNIQUE NOT NULL,
    applicant_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    
    -- KYC Status
    kyc_status VARCHAR(20) DEFAULT 'pending',
    kyc_verified_at TIMESTAMP,
    kyc_document_url TEXT,
    
    -- Risk & Fraud Scoring
    i_360_score FLOAT DEFAULT 0.0,
    i_not_score FLOAT DEFAULT 0.0,
    suspicious_score FLOAT DEFAULT 0.0,
    risk_level VARCHAR(20) DEFAULT 'low',
    
    -- Account Status
    is_blacklisted BOOLEAN DEFAULT FALSE,
    blacklist_reason TEXT,
    blacklisted_at TIMESTAMP,
    account_status VARCHAR(20) DEFAULT 'active',
    
    -- Location & Demographics
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    postal_code VARCHAR(20),
    date_of_birth DATE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    
    -- Constraints
    CHECK (kyc_status IN ('pending', 'approved', 'rejected', 'under_review')),
    CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    CHECK (account_status IN ('active', 'suspended', 'closed', 'under_investigation')),
    CHECK (i_360_score BETWEEN 0 AND 100),
    CHECK (i_not_score BETWEEN 0 AND 100),
    CHECK (suspicious_score BETWEEN 0 AND 100)
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_users_entity_id ON users(entity_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_kyc_status ON users(kyc_status);
CREATE INDEX IF NOT EXISTS idx_users_risk_level ON users(risk_level);
CREATE INDEX IF NOT EXISTS idx_users_blacklisted ON users(is_blacklisted);
CREATE INDEX IF NOT EXISTS idx_users_account_status ON users(account_status);

-- =============================================================================
-- TABLE: transactions
-- =============================================================================

CREATE TABLE IF NOT EXISTS transactions (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id INTEGER NOT NULL,
    
    -- Transaction Details
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    
    -- Transaction Parties
    sender_account VARCHAR(100),
    receiver_account VARCHAR(100),
    sender_name VARCHAR(255),
    receiver_name VARCHAR(255),
    
    -- Risk Assessment
    suspicious_score FLOAT DEFAULT 0.0,
    risk_level VARCHAR(20) DEFAULT 'low',
    is_flagged BOOLEAN DEFAULT FALSE,
    flag_reason TEXT,
    
    -- Transaction Status
    status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(50),
    
    -- Location & Context
    ip_address VARCHAR(45),
    device_id VARCHAR(100),
    location TEXT,
    
    -- Metadata
    transaction_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Check Constraints
    CHECK (transaction_type IN ('deposit', 'withdrawal', 'transfer', 'payment', 'refund')),
    CHECK (amount > 0),
    CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    CHECK (status IN ('pending', 'completed', 'failed', 'cancelled', 'under_review')),
    CHECK (suspicious_score BETWEEN 0 AND 100)
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_transaction_id ON transactions(transaction_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_flagged ON transactions(is_flagged);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_risk_level ON transactions(risk_level);

-- =============================================================================
-- TABLE: compliance_alerts
-- =============================================================================

CREATE TABLE IF NOT EXISTS compliance_alerts (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id INTEGER,
    transaction_id INTEGER,
    
    -- Alert Classification
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Alert Details
    entity_id VARCHAR(100),
    entity_type VARCHAR(50),
    rps360 REAL DEFAULT 0.0,
    
    -- Alert Status
    status VARCHAR(20) DEFAULT 'active',
    priority VARCHAR(20) DEFAULT 'medium',
    
    -- Dismissal & Acknowledgment
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR(100),
    dismissal_reason TEXT,
    
    -- Source & Context
    source VARCHAR(100),
    triggered_by VARCHAR(100),
    alert_metadata TEXT,
    
    -- Alert Classification (for marking as true/false positive)
    is_true_positive BOOLEAN,
    reviewed_at TIMESTAMP,
    reviewed_by VARCHAR(100),
    
    -- Timestamps
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE SET NULL,
    
    -- Check Constraints
    CHECK (alert_type IN ('kyc_alert', 'transaction_alert', 'fraud_alert', 'aml_alert', 'sanction_alert', 'behavioral_alert', 'system_alert')),
    CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CHECK (status IN ('active', 'investigating', 'resolved', 'dismissed', 'escalated')),
    CHECK (priority IN ('low', 'medium', 'high', 'critical'))
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON compliance_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_transaction_id ON compliance_alerts(transaction_id);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON compliance_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON compliance_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON compliance_alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON compliance_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON compliance_alerts(is_acknowledged);

-- =============================================================================
-- TABLE: investigation_cases
-- =============================================================================

CREATE TABLE IF NOT EXISTS investigation_cases (
    -- Primary Key
    id VARCHAR(50) PRIMARY KEY,
    
    -- Foreign Keys
    user_id INTEGER NOT NULL,
    
    -- Case Details
    case_title VARCHAR(255) NOT NULL,
    case_description TEXT,
    case_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    
    -- Case Status
    status VARCHAR(20) DEFAULT 'open',
    priority VARCHAR(20) DEFAULT 'medium',
    
    -- Assignment & Ownership
    assigned_to VARCHAR(100),
    assigned_at TIMESTAMP,
    created_by VARCHAR(100) NOT NULL,
    
    -- Evidence & Context
    transaction_ids TEXT,
    alert_ids TEXT,
    evidence_urls TEXT,
    
    -- Investigation Progress
    investigation_notes TEXT,
    findings TEXT,
    recommended_action TEXT,
    
    -- Resolution
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    outcome VARCHAR(50),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Check Constraints
    CHECK (case_type IN ('fraud', 'aml', 'kyc', 'sanctions', 'behavioral', 'other')),
    CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CHECK (status IN ('open', 'investigating', 'pending_review', 'closed', 'escalated')),
    CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    CHECK (outcome IN ('cleared', 'fraud_confirmed', 'account_suspended', 'legal_action', 'pending') OR outcome IS NULL)
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_cases_user_id ON investigation_cases(user_id);
CREATE INDEX IF NOT EXISTS idx_cases_status ON investigation_cases(status);
CREATE INDEX IF NOT EXISTS idx_cases_priority ON investigation_cases(priority);
CREATE INDEX IF NOT EXISTS idx_cases_assigned_to ON investigation_cases(assigned_to);
CREATE INDEX IF NOT EXISTS idx_cases_created ON investigation_cases(created_at);

-- =============================================================================
-- TABLE: account_holds
-- =============================================================================

CREATE TABLE IF NOT EXISTS account_holds (
    -- Primary Key
    id VARCHAR(50) PRIMARY KEY,
    
    -- Foreign Keys
    user_id INTEGER NOT NULL,
    case_id VARCHAR(50),
    
    -- Hold Details
    hold_type VARCHAR(50) NOT NULL,
    hold_reason TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    
    -- Hold Status
    status VARCHAR(20) DEFAULT 'active',
    
    -- Hold Duration
    hold_placed_at TIMESTAMP NOT NULL,
    hold_expires_at TIMESTAMP,
    hold_released_at TIMESTAMP,
    
    -- Actions Restricted
    restrictions TEXT,
    
    -- Authorization
    placed_by VARCHAR(100) NOT NULL,
    approved_by VARCHAR(100),
    released_by VARCHAR(100),
    
    -- Resolution
    release_reason TEXT,
    release_notes TEXT,
    
    -- Notifications
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_sent_at TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (case_id) REFERENCES investigation_cases(id) ON DELETE SET NULL,
    
    -- Check Constraints
    CHECK (hold_type IN ('temporary', 'permanent', 'investigation', 'regulatory', 'fraud')),
    CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CHECK (status IN ('active', 'expired', 'released', 'appealed'))
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_holds_user_id ON account_holds(user_id);
CREATE INDEX IF NOT EXISTS idx_holds_case_id ON account_holds(case_id);
CREATE INDEX IF NOT EXISTS idx_holds_status ON account_holds(status);
CREATE INDEX IF NOT EXISTS idx_holds_type ON account_holds(hold_type);

-- =============================================================================
-- TABLE: organization_settings
-- =============================================================================

CREATE TABLE IF NOT EXISTS organization_settings (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
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
    enable_email_alerts BOOLEAN DEFAULT TRUE,
    enable_sms_alerts BOOLEAN DEFAULT FALSE,
    enable_dashboard_alerts BOOLEAN DEFAULT TRUE,
    
    -- Auto-Actions
    auto_flag_high_risk BOOLEAN DEFAULT TRUE,
    auto_hold_critical_risk BOOLEAN DEFAULT FALSE,
    auto_escalate_threshold FLOAT DEFAULT 90.0,
    
    -- Compliance Settings
    require_dual_approval BOOLEAN DEFAULT FALSE,
    data_retention_days INTEGER DEFAULT 2555,
    enable_audit_logging BOOLEAN DEFAULT TRUE,
    
    -- Feature Flags
    enable_cns_screening BOOLEAN DEFAULT TRUE,
    enable_transaction_monitoring BOOLEAN DEFAULT TRUE,
    enable_behavioral_analysis BOOLEAN DEFAULT TRUE,
    
    -- API & Integration
    api_rate_limit INTEGER DEFAULT 1000,
    webhook_url TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
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

-- =============================================================================
-- TABLE: notification_settings
-- =============================================================================

CREATE TABLE IF NOT EXISTS notification_settings (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id INTEGER UNIQUE NOT NULL,
    
    -- Email Preferences
    enable_email BOOLEAN DEFAULT TRUE,
    email_frequency VARCHAR(20) DEFAULT 'immediate',
    
    -- SMS Preferences
    enable_sms BOOLEAN DEFAULT FALSE,
    sms_number VARCHAR(20),
    
    -- Push Notification Preferences
    enable_push BOOLEAN DEFAULT TRUE,
    device_tokens TEXT,
    
    -- Alert Type Preferences
    notify_kyc_alerts BOOLEAN DEFAULT TRUE,
    notify_transaction_alerts BOOLEAN DEFAULT TRUE,
    notify_fraud_alerts BOOLEAN DEFAULT TRUE,
    notify_aml_alerts BOOLEAN DEFAULT TRUE,
    notify_case_updates BOOLEAN DEFAULT TRUE,
    notify_hold_updates BOOLEAN DEFAULT TRUE,
    
    -- Severity Filters
    min_severity_level VARCHAR(20) DEFAULT 'medium',
    
    -- Quiet Hours
    quiet_hours_enabled BOOLEAN DEFAULT FALSE,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    quiet_hours_timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Digest Settings
    enable_daily_digest BOOLEAN DEFAULT FALSE,
    digest_time TIME DEFAULT '09:00:00',
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Check Constraints
    CHECK (email_frequency IN ('immediate', 'hourly', 'daily', 'weekly')),
    CHECK (min_severity_level IN ('low', 'medium', 'high', 'critical'))
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_notif_user_id ON notification_settings(user_id);

-- =============================================================================
-- INITIAL DATA - Default organization settings
-- =============================================================================

INSERT INTO organization_settings (
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
) ON CONFLICT (organization_code) DO NOTHING;

-- =============================================================================
-- SUCCESS MESSAGE
-- =============================================================================

SELECT 'Database schema reset complete! Tables have been recreated with new schema.' AS status;
