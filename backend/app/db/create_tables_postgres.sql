-- =============================================================================
-- COMPLIANCE & FRAUD DETECTION DATABASE SCHEMA - PostgreSQL Version
-- Aligned with core_schema.sql
-- =============================================================================

-- =============================================================================
-- TABLE: users (matching core_schema.sql)
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    uin CHAR(20),
    uin_hash CHAR(64),
    username VARCHAR(100),
    profile_pic TEXT,
    email VARCHAR(255),
    phone VARCHAR(15),
    date_of_birth TIMESTAMP,
    address TEXT,
    occupation VARCHAR(200),
    annual_income DOUBLE PRECISION,
    
    -- KYC Status
    kyc_status VARCHAR(100),
    kyc_verified_at TIMESTAMP NULL,
    signature_hash VARCHAR(64),
    
    -- Credit & Risk Scoring
    credit_score INT,
    blacklisted BOOLEAN DEFAULT FALSE,
    blacklisted_at TIMESTAMP NULL,
    current_rps_not DOUBLE PRECISION,
    current_rps_360 DOUBLE PRECISION,
    last_rps_calculation TIMESTAMP,
    risk_category VARCHAR(100),
    
    -- Version Control & Pathway Fields
    version INT DEFAULT 1,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    time BIGINT,
    diff INT,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_age CHECK (
        EXTRACT(YEAR FROM AGE(date_of_birth)) >= 18
    ),
    CONSTRAINT chk_credit_score CHECK (credit_score BETWEEN 300 AND 900)
);

-- Indexes for Users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_kyc_status ON users(kyc_status);
CREATE INDEX IF NOT EXISTS idx_users_risk_category ON users(risk_category);
CREATE INDEX IF NOT EXISTS idx_users_blacklisted ON users(blacklisted);

-- =============================================================================
-- TABLE: admins (matching core_schema.sql)
-- =============================================================================

CREATE TABLE IF NOT EXISTS admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'admin',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CHECK (role IN ('admin', 'superadmin'))
);

-- Indexes for Admins
CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username);
CREATE INDEX IF NOT EXISTS idx_admins_email ON admins(email);
CREATE INDEX IF NOT EXISTS idx_admins_role ON admins(role);

-- =============================================================================
-- TABLE: audit_logs (matching core_schema.sql)
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    action_description TEXT NOT NULL,
    target_type VARCHAR(50),
    target_id INTEGER,
    target_identifier VARCHAR(255),
    action_metadata JSONB,
    ip_address VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE,
    
    -- Check Constraints
    CHECK (action_type IN (
        'classify_alert',
        'dismiss_alert',
        'escalate_alert',
        'blacklist_user',
        'whitelist_user',
        'flag_user',
        'unflag_user',
        'block_transaction',
        'approve_transaction',
        'update_system_alert',
        'resolve_health_check',
        'other'
    ))
);

-- Indexes for Audit Logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_admin_id ON audit_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_type ON audit_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_target_type ON audit_logs(target_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_target_id ON audit_logs(target_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_metadata ON audit_logs USING GIN(action_metadata);

-- =============================================================================
-- TABLE: system_metrics (matching core_schema.sql)
-- =============================================================================

CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL,
    metric_category VARCHAR(50) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(20),
    time_window VARCHAR(20),
    aggregation_period_start TIMESTAMP WITH TIME ZONE,
    aggregation_period_end TIMESTAMP WITH TIME ZONE,
    details JSONB,
    total_count INTEGER,
    positive_count INTEGER,
    negative_count INTEGER,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_threshold FLOAT,
    
    -- Check Constraints
    CHECK (metric_type IN (
        'alert_hit_rate',
        'false_positive_rate',
        'api_response_time',
        'api_error_rate',
        'alert_response_time',
        'user_flag_rate',
        'transaction_block_rate',
        'other'
    )),
    CHECK (metric_category IN ('alert', 'api', 'transaction', 'user', 'system')),
    CHECK (metric_unit IN ('percentage', 'milliseconds', 'seconds', 'count', 'rate', 'ratio')),
    CHECK (time_window IN ('hourly', 'daily', 'weekly', 'monthly', 'realtime'))
);

-- Indexes for System Metrics
CREATE INDEX IF NOT EXISTS idx_system_metrics_type ON system_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_system_metrics_category ON system_metrics(metric_category);
CREATE INDEX IF NOT EXISTS idx_system_metrics_recorded_at ON system_metrics(recorded_at);
CREATE INDEX IF NOT EXISTS idx_system_metrics_time_window ON system_metrics(time_window);
CREATE INDEX IF NOT EXISTS idx_system_metrics_is_anomaly ON system_metrics(is_anomaly);
CREATE INDEX IF NOT EXISTS idx_system_metrics_period_start ON system_metrics(aggregation_period_start);
CREATE INDEX IF NOT EXISTS idx_system_metrics_details ON system_metrics USING GIN(details);

-- =============================================================================
-- TABLE: system_health (matching core_schema.sql)
-- =============================================================================

CREATE TABLE IF NOT EXISTS system_health (
    id SERIAL PRIMARY KEY,
    check_type VARCHAR(50) NOT NULL,
    component_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    error_type VARCHAR(100),
    error_message TEXT,
    error_stacktrace TEXT,
    request_context JSONB,
    response_context JSONB,
    response_time_ms INTEGER,
    retry_count INTEGER DEFAULT 0,
    affected_operations JSONB,
    user_impact VARCHAR(20),
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    auto_recovered BOOLEAN DEFAULT FALSE,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_occurrence TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    alert_sent BOOLEAN DEFAULT FALSE,
    alert_sent_at TIMESTAMP WITH TIME ZONE,
    alert_recipients JSONB,
    
    -- Check Constraints
    CHECK (check_type IN ('api_health', 'parser_health', 'db_health', 'service_health', 'network_health')),
    CHECK (status IN ('healthy', 'degraded', 'failed', 'recovering')),
    CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    CHECK (user_impact IN ('none', 'low', 'medium', 'high', 'critical'))
);

-- Indexes for System Health
CREATE INDEX IF NOT EXISTS idx_system_health_check_type ON system_health(check_type);
CREATE INDEX IF NOT EXISTS idx_system_health_component_name ON system_health(component_name);
CREATE INDEX IF NOT EXISTS idx_system_health_status ON system_health(status);
CREATE INDEX IF NOT EXISTS idx_system_health_severity ON system_health(severity);
CREATE INDEX IF NOT EXISTS idx_system_health_is_resolved ON system_health(is_resolved);
CREATE INDEX IF NOT EXISTS idx_system_health_detected_at ON system_health(detected_at);
CREATE INDEX IF NOT EXISTS idx_system_health_user_impact ON system_health(user_impact);
CREATE INDEX IF NOT EXISTS idx_system_health_request_context ON system_health USING GIN(request_context);
CREATE INDEX IF NOT EXISTS idx_system_health_response_context ON system_health USING GIN(response_context);

-- =============================================================================
-- TABLE: system_alerts (matching core_schema.sql)
-- =============================================================================

CREATE TABLE IF NOT EXISTS system_alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    component VARCHAR(100),
    metric_type VARCHAR(50),
    threshold_value VARCHAR(50),
    actual_value VARCHAR(50),
    alert_data JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notifications_sent INTEGER DEFAULT 0,
    last_notification_at TIMESTAMP WITH TIME ZONE,
    
    -- Check Constraints
    CHECK (alert_type IN (
        'high_error_rate',
        'api_downtime',
        'anomaly_detected',
        'threshold_breach',
        'health_check_failed',
        'performance_degradation',
        'security_incident',
        'other'
    )),
    CHECK (severity IN ('warning', 'error', 'critical')),
    CHECK (status IN ('active', 'acknowledged', 'resolved', 'false_alarm'))
);

-- Indexes for System Alerts
CREATE INDEX IF NOT EXISTS idx_system_alerts_alert_type ON system_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_system_alerts_severity ON system_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_system_alerts_status ON system_alerts(status);
CREATE INDEX IF NOT EXISTS idx_system_alerts_triggered_at ON system_alerts(triggered_at);
CREATE INDEX IF NOT EXISTS idx_system_alerts_component ON system_alerts(component);
CREATE INDEX IF NOT EXISTS idx_system_alerts_metric_type ON system_alerts(metric_type);
CREATE INDEX IF NOT EXISTS idx_system_alerts_alert_data ON system_alerts USING GIN(alert_data);

-- =============================================================================
-- TABLE: transactions (matching core_schema.sql)
-- =============================================================================

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    timestamp TIMESTAMP,
    amount DOUBLE PRECISION,
    currency VARCHAR(10),
    txn_type VARCHAR(50),
    counterparty_id BIGINT,
    is_fraud INT,
    
    -- Foreign Key linkage
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Index for time-based lookups
CREATE INDEX IF NOT EXISTS idx_txn_timestamp ON transactions(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_txn_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_txn_is_fraud ON transactions(is_fraud);
CREATE INDEX IF NOT EXISTS idx_txn_type ON transactions(txn_type);

-- =============================================================================
-- TABLE: compliance_alerts
-- =============================================================================

CREATE TABLE IF NOT EXISTS compliance_alerts (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    transaction_id BIGINT,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
    title VARCHAR(255) NOT NULL,
    description TEXT,
    entity_id VARCHAR(100),
    entity_type VARCHAR(50),
    rps360 REAL DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'active',
    priority VARCHAR(20) DEFAULT 'medium',
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR(100),
    dismissal_reason TEXT,
    source VARCHAR(100),
    triggered_by VARCHAR(100),
    alert_metadata TEXT,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE SET NULL,
    
    -- Check Constraints
    CHECK (alert_type IN ('kyc_alert', 'transaction_alert', 'fraud_alert', 'aml_alert', 'sanction_alert', 'behavioral_alert', 'system_alert')),
    CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CHECK (status IN ('active', 'investigating', 'resolved', 'dismissed', 'escalated')),
    CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    CHECK (rps360 >= 0 AND rps360 <= 1)
);

-- Indexes for Compliance Alerts
CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON compliance_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_transaction_id ON compliance_alerts(transaction_id);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON compliance_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON compliance_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON compliance_alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON compliance_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON compliance_alerts(is_acknowledged);

-- =============================================================================
-- TABLE: toxicityhistory (for RPS score tracking)
-- =============================================================================

CREATE TABLE IF NOT EXISTS toxicityhistory (
    history_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    rps_not DOUBLE PRECISION,
    rps_360 DOUBLE PRECISION,
    sanction_score DOUBLE PRECISION,
    news_score DOUBLE PRECISION,
    transaction_score DOUBLE PRECISION,
    portfolio_score DOUBLE PRECISION,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    calculation_trigger VARCHAR(50),
    time BIGINT,
    diff INT,
    
    -- Foreign Key Constraint
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes for Toxicity History
CREATE INDEX IF NOT EXISTS idx_toxicity_user_id ON toxicityhistory(user_id);
CREATE INDEX IF NOT EXISTS idx_toxicity_calculated_at ON toxicityhistory(calculated_at);

-- =============================================================================
-- TABLE: usersanctionmatches
-- =============================================================================

CREATE TABLE IF NOT EXISTS usersanctionmatches (
    match_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    match_found BOOLEAN,
    match_confidence DOUBLE PRECISION,
    matched_entity_name VARCHAR(500),
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    time BIGINT,
    diff INT,
    
    -- Foreign Key Constraint
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes for User Sanction Matches
CREATE INDEX IF NOT EXISTS idx_sanction_user_id ON usersanctionmatches(user_id);
CREATE INDEX IF NOT EXISTS idx_sanction_checked_at ON usersanctionmatches(checked_at);
CREATE INDEX IF NOT EXISTS idx_sanction_match_found ON usersanctionmatches(match_found);

-- =============================================================================
-- HELPER VIEWS (matching core_schema.sql)
-- =============================================================================

-- View: Recent Audit Logs with Admin Details
CREATE OR REPLACE VIEW v_audit_logs_with_admin AS
SELECT 
    al.*,
    a.username as admin_username,
    a.email as admin_email,
    a.role as admin_role
FROM audit_logs al
JOIN admins a ON al.admin_id = a.id
ORDER BY al.created_at DESC;

-- View: Active System Issues
CREATE OR REPLACE VIEW v_active_system_issues AS
SELECT 
    'health_check' as issue_type,
    id,
    component_name as component,
    severity,
    error_message as description,
    detected_at as created_at,
    is_resolved
FROM system_health
WHERE is_resolved = FALSE AND severity IN ('error', 'critical')
UNION ALL
SELECT 
    'system_alert' as issue_type,
    id,
    component,
    severity,
    description,
    triggered_at as created_at,
    CASE WHEN status IN ('resolved', 'false_alarm') THEN TRUE ELSE FALSE END as is_resolved
FROM system_alerts
WHERE status IN ('active', 'acknowledged')
ORDER BY created_at DESC;

-- View: Metrics Summary (Last 24 Hours)
CREATE OR REPLACE VIEW v_metrics_last_24h AS
SELECT 
    metric_type,
    metric_category,
    AVG(metric_value) as avg_value,
    MIN(metric_value) as min_value,
    MAX(metric_value) as max_value,
    COUNT(*) as data_points,
    SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) as anomaly_count
FROM system_metrics
WHERE recorded_at >= NOW() - INTERVAL '24 hours'
GROUP BY metric_type, metric_category;

-- =============================================================================
-- UTILITY FUNCTIONS (matching core_schema.sql)
-- =============================================================================

-- Function to calculate alert hit rate for a time period
CREATE OR REPLACE FUNCTION calculate_alert_hit_rate(
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE
)
RETURNS FLOAT AS $$
DECLARE
    total_alerts INTEGER;
    true_positives INTEGER;
    hit_rate FLOAT;
BEGIN
    SELECT COUNT(*) INTO total_alerts
    FROM compliance_alerts
    WHERE created_at BETWEEN start_date AND end_date
    AND status IN ('resolved', 'dismissed');
    
    SELECT COUNT(*) INTO true_positives
    FROM compliance_alerts
    WHERE created_at BETWEEN start_date AND end_date
    AND status = 'resolved';
    
    IF total_alerts > 0 THEN
        hit_rate := (true_positives::FLOAT / total_alerts::FLOAT) * 100;
    ELSE
        hit_rate := 0;
    END IF;
    
    RETURN hit_rate;
END;
$$ LANGUAGE plpgsql;

-- Function to get system health status
CREATE OR REPLACE FUNCTION get_system_health_status()
RETURNS VARCHAR AS $$
DECLARE
    critical_count INTEGER;
    unresolved_errors INTEGER;
    health_status VARCHAR(20);
BEGIN
    SELECT COUNT(*) INTO critical_count
    FROM system_alerts
    WHERE status = 'active' AND severity = 'critical';
    
    SELECT COUNT(*) INTO unresolved_errors
    FROM system_health
    WHERE is_resolved = FALSE AND severity IN ('error', 'critical');
    
    IF critical_count > 0 THEN
        health_status := 'critical';
    ELSIF unresolved_errors > 0 THEN
        health_status := 'degraded';
    ELSE
        health_status := 'healthy';
    END IF;
    
    RETURN health_status;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE users IS 'User accounts matching core_schema.sql';
COMMENT ON TABLE admins IS 'Admin accounts for dashboard access';
COMMENT ON TABLE audit_logs IS 'Records all admin actions for compliance tracking';
COMMENT ON TABLE system_metrics IS 'Stores system-wide performance metrics and KPIs';
COMMENT ON TABLE system_health IS 'Tracks system health checks, failures, and recovery';
COMMENT ON TABLE system_alerts IS 'System-level alerts for superadmin monitoring';
COMMENT ON TABLE transactions IS 'Individual transactions matching core_schema.sql';
COMMENT ON TABLE compliance_alerts IS 'Alerts for compliance and fraud detection';
COMMENT ON TABLE toxicityhistory IS 'Historical RPS scores for users';
COMMENT ON TABLE usersanctionmatches IS 'Sanction screening results for users';
