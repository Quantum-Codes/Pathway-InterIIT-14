CREATE TABLE Users (
    user_id BIGINT PRIMARY KEY,
    uin CHAR(20),
    uin_hash CHAR(64),
    username VARCHAR(100),
    profile_pic TEXT, -- ADDED COLUMN
    email VARCHAR(255),
    phone VARCHAR(15),
    date_of_birth TIMESTAMP,
    address TEXT,
    occupation VARCHAR(200),
    annual_income DOUBLE PRECISION,
    
    -- Replaced MySQL ENUM with custom PostgreSQL type
    kyc_status VARCHAR(100),
    
    kyc_verified_at TIMESTAMP NULL,
    signature_hash VARCHAR(64),
    credit_score INT,
    blacklisted BOOLEAN DEFAULT FALSE,
    blacklisted_at TIMESTAMP NULL,
    current_rps_not DOUBLE PRECISION,
    current_rps_360 DOUBLE PRECISION,
    last_rps_calculation TIMESTAMP,
    
    -- Replaced MySQL ENUM with custom PostgreSQL type
    risk_category VARCHAR(100), 
    
    version INT DEFAULT 1,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    time BIGINT, -- necessary acc to pw
    diff INT, -- necessary acc to pw

    -- Corrected: Removed MySQL-specific ON UPDATE. This functionality is handled by a TRIGGER.
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
    
    -- Corrected: Replaced MySQL YEAR(CURDATE()) with PostgreSQL equivalent
    CONSTRAINT chk_age CHECK (
        EXTRACT(YEAR FROM AGE(date_of_birth)) >= 18
    ), 
    CONSTRAINT chk_credit_score CHECK (credit_score BETWEEN 300 AND 900)
);

-- =============================================================================
-- SUPERADMIN MONITORING SYSTEM - DATABASE SCHEMA
-- =============================================================================
-- This schema includes all tables needed for the superadmin monitoring feature.
-- It references existing tables (users, admins, compliance_alerts) and creates
-- new tables for audit logs, system metrics, health monitoring, and alerting.
-- =============================================================================

-- =============================================================================
-- EXISTING TABLE REFERENCE: admins
-- =============================================================================
-- This table should already exist. If not, create it:

CREATE TABLE IF NOT EXISTS admins (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Authentication
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    
    -- Role
    role VARCHAR(20) NOT NULL DEFAULT 'admin',
    
    -- Status
    -- is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CHECK (role IN ('admin', 'superadmin'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username);
CREATE INDEX IF NOT EXISTS idx_admins_email ON admins(email);
CREATE INDEX IF NOT EXISTS idx_admins_role ON admins(role);
-- CREATE INDEX IF NOT EXISTS idx_admins_is_active ON admins(is_active);

-- =============================================================================
-- EXISTING TABLE REFERENCE: users
-- =============================================================================
-- This table should already exist from create_tables_postgres.sql
-- Required fields: id, entity_id, applicant_name, email, etc.

-- =============================================================================
-- EXISTING TABLE REFERENCE: compliance_alerts
-- =============================================================================
-- This table should already exist from create_tables_postgres.sql
-- Required fields: id, user_id, alert_type, severity, status, is_true_positive, etc.

-- =============================================================================
-- NEW TABLE: audit_logs
-- =============================================================================
-- Records all admin actions for compliance and accountability
-- Tracks who was flagged, by which admin, and how decisions were resolved

CREATE TABLE IF NOT EXISTS audit_logs (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Admin who performed the action
    admin_id INTEGER NOT NULL,
    
    -- Action details
    action_type VARCHAR(50) NOT NULL,
    action_description TEXT NOT NULL,
    
    -- Target entity (what was affected)
    target_type VARCHAR(50),  -- 'user', 'alert', 'transaction', 'system'
    target_id INTEGER,  -- ID of the affected entity
    target_identifier VARCHAR(255),  -- e.g., entity_id, alert_id for easy reference
    
    -- Additional context (stored as JSON)
    action_metadata JSONB,  -- before/after values, classification, notes, etc.
    
    -- Security tracking
    ip_address VARCHAR(50),
    -- user_agent TEXT,
    
    -- Timestamp
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

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_audit_logs_admin_id ON audit_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_type ON audit_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_target_type ON audit_logs(target_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_target_id ON audit_logs(target_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_metadata ON audit_logs USING GIN(action_metadata);

-- =============================================================================
-- NEW TABLE: system_metrics
-- =============================================================================
-- Tracks system-wide performance metrics
-- Records hit rates, false positive rates, response times, and API errors

CREATE TABLE IF NOT EXISTS system_metrics (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Metric Type
    metric_type VARCHAR(50) NOT NULL,
    metric_category VARCHAR(50) NOT NULL,
    
    -- Metric Values
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(20),  -- 'percentage', 'milliseconds', 'count', 'rate'
    
    -- Time Context
    time_window VARCHAR(20),  -- 'hourly', 'daily', 'weekly', 'monthly'
    aggregation_period_start TIMESTAMP WITH TIME ZONE,
    aggregation_period_end TIMESTAMP WITH TIME ZONE,
    
    -- Additional Details (stored as JSON)
    details JSONB,  -- breakdown by severity, alert type, etc.
    
    -- Metadata
    total_count INTEGER,  -- Total items in this metric calculation
    positive_count INTEGER,  -- Count of positive cases (e.g., true positives)
    negative_count INTEGER,  -- Count of negative cases (e.g., false positives)
    
    -- Timestamp
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Anomaly Detection
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

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_system_metrics_type ON system_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_system_metrics_category ON system_metrics(metric_category);
CREATE INDEX IF NOT EXISTS idx_system_metrics_recorded_at ON system_metrics(recorded_at);
CREATE INDEX IF NOT EXISTS idx_system_metrics_time_window ON system_metrics(time_window);
CREATE INDEX IF NOT EXISTS idx_system_metrics_is_anomaly ON system_metrics(is_anomaly);
CREATE INDEX IF NOT EXISTS idx_system_metrics_period_start ON system_metrics(aggregation_period_start);
CREATE INDEX IF NOT EXISTS idx_system_metrics_details ON system_metrics USING GIN(details);

-- =============================================================================
-- NEW TABLE: system_health
-- =============================================================================
-- Tracks system health events, failures, and anomalies
-- Monitors upstream API downtime, parser errors, and unexpected behavior

CREATE TABLE IF NOT EXISTS system_health (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Health Check Type
    check_type VARCHAR(50) NOT NULL,
    component_name VARCHAR(100) NOT NULL,
    
    -- Status
    status VARCHAR(20) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    
    -- Error Details
    error_type VARCHAR(100),  -- 'connection_timeout', 'parse_error', 'api_rate_limit', etc.
    error_message TEXT,
    error_stacktrace TEXT,
    
    -- Context (stored as JSON)
    request_context JSONB,  -- details about the request that failed
    response_context JSONB,  -- details about the response if available
    
    -- Metrics
    response_time_ms INTEGER,
    retry_count INTEGER DEFAULT 0,
    
    -- Impact Assessment
    affected_operations JSONB,  -- list of operations affected
    user_impact VARCHAR(20),  -- 'none', 'low', 'medium', 'high', 'critical'
    
    -- Resolution
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    auto_recovered BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_occurrence TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Alerting
    alert_sent BOOLEAN DEFAULT FALSE,
    alert_sent_at TIMESTAMP WITH TIME ZONE,
    alert_recipients JSONB,
    
    -- Check Constraints
    CHECK (check_type IN ('api_health', 'parser_health', 'db_health', 'service_health', 'network_health')),
    CHECK (status IN ('healthy', 'degraded', 'failed', 'recovering')),
    CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    CHECK (user_impact IN ('none', 'low', 'medium', 'high', 'critical'))
);

-- Indexes for Performance
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
-- NEW TABLE: system_alerts
-- =============================================================================
-- Stores system-level alerts for superadmin monitoring
-- Triggered when system behaves unexpectedly (high error rates, API downtime, etc.)

CREATE TABLE IF NOT EXISTS system_alerts (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Alert Details
    alert_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    
    -- Context
    component VARCHAR(100),  -- component that triggered the alert
    metric_type VARCHAR(50),  -- related metric if applicable
    threshold_value VARCHAR(50),  -- the threshold that was breached
    actual_value VARCHAR(50),  -- the actual value that breached the threshold
    
    -- Additional Data (stored as JSON)
    alert_data JSONB,
    
    -- Alert Status
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    
    -- Timestamps
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Notification Tracking
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

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_system_alerts_alert_type ON system_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_system_alerts_severity ON system_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_system_alerts_status ON system_alerts(status);
CREATE INDEX IF NOT EXISTS idx_system_alerts_triggered_at ON system_alerts(triggered_at);
CREATE INDEX IF NOT EXISTS idx_system_alerts_component ON system_alerts(component);
CREATE INDEX IF NOT EXISTS idx_system_alerts_metric_type ON system_alerts(metric_type);
CREATE INDEX IF NOT EXISTS idx_system_alerts_alert_data ON system_alerts USING GIN(alert_data);

-- =============================================================================
-- HELPER VIEWS FOR COMMON QUERIES
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
-- SAMPLE DATA INSERTION (for testing)
-- =============================================================================

-- Note: Uncomment below to insert sample data for testing

/*
-- Sample audit log entry
INSERT INTO audit_logs (
    admin_id, 
    action_type, 
    action_description, 
    target_type, 
    target_id, 
    target_identifier,
    action_metadata,
    ip_address,
) VALUES (
    1,
    'classify_alert',
    'Classified alert 123 as true_positive',
    'alert',
    123,
    'alert_123',
    '{"previous_state": {"is_true_positive": null}, "new_classification": "true_positive", "notes": "Confirmed fraudulent transaction"}'::jsonb,
    '192.168.1.100',
    'Mozilla/5.0...'
);

-- Sample system metric
INSERT INTO system_metrics (
    metric_type,
    metric_category,
    metric_value,
    metric_unit,
    time_window,
    aggregation_period_start,
    aggregation_period_end,
    total_count,
    positive_count,
    negative_count,
    details
) VALUES (
    'alert_hit_rate',
    'alert',
    78.5,
    'percentage',
    'daily',
    NOW() - INTERVAL '1 day',
    NOW(),
    100,
    78,
    22,
    '{"by_severity": {"high": 85.2, "medium": 72.3, "low": 65.1}}'::jsonb
);

-- Sample health check failure
INSERT INTO system_health (
    check_type,
    component_name,
    status,
    severity,
    error_type,
    error_message,
    request_context,
    response_time_ms,
    retry_count,
    affected_operations,
    user_impact,
    alert_sent
) VALUES (
    'api_health',
    'sanctions_api',
    'failed',
    'error',
    'ConnectionTimeout',
    'Connection timeout after 5000ms',
    '{"endpoint": "/api/sanctions/check", "user_id": 12345}'::jsonb,
    5001,
    3,
    '["sanctions_check", "user_verification"]'::jsonb,
    'high',
    TRUE
);

-- Sample system alert
INSERT INTO system_alerts (
    alert_type,
    title,
    description,
    severity,
    component,
    metric_type,
    threshold_value,
    actual_value,
    alert_data,
    status
) VALUES (
    'threshold_breach',
    'High False Positive Rate',
    'False positive rate is 32.5%, exceeding 30% threshold',
    'warning',
    'alert_system',
    'false_positive_rate',
    '30%',
    '32.5%',
    '{"total_alerts": 150, "false_positives": 49, "time_window": "24h"}'::jsonb,
    'active'
);
*/

-- =============================================================================
-- UTILITY FUNCTIONS
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
    -- Count total reviewed alerts
    SELECT COUNT(*) INTO total_alerts
    FROM compliance_alerts
    WHERE created_at BETWEEN start_date AND end_date
    AND is_true_positive IS NOT NULL;
    
    -- Count true positives
    SELECT COUNT(*) INTO true_positives
    FROM compliance_alerts
    WHERE created_at BETWEEN start_date AND end_date
    AND is_true_positive = TRUE;
    
    -- Calculate hit rate
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
    -- Count critical alerts
    SELECT COUNT(*) INTO critical_count
    FROM system_alerts
    WHERE status = 'active' AND severity = 'critical';
    
    -- Count unresolved errors
    SELECT COUNT(*) INTO unresolved_errors
    FROM system_health
    WHERE is_resolved = FALSE AND severity IN ('error', 'critical');
    
    -- Determine status
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
-- MAINTENANCE & CLEANUP
-- =============================================================================

-- Function to archive old audit logs (keep last 365 days)
CREATE OR REPLACE FUNCTION archive_old_audit_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    WITH deleted AS (
        DELETE FROM audit_logs
        WHERE created_at < NOW() - INTERVAL '365 days'
        RETURNING *
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up resolved health checks older than 30 days
CREATE OR REPLACE FUNCTION cleanup_old_health_checks()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    WITH deleted AS (
        DELETE FROM system_health
        WHERE is_resolved = TRUE 
        AND resolved_at < NOW() - INTERVAL '30 days'
        RETURNING *
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- GRANTS (adjust based on your user roles)
-- =============================================================================

-- Grant superadmin full access to all monitoring tables
-- GRANT ALL PRIVILEGES ON audit_logs, system_metrics, system_health, system_alerts TO superadmin_role;

-- Grant regular admins read-only access to their own audit logs
-- GRANT SELECT ON audit_logs TO admin_role;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE audit_logs IS 'Records all admin actions for compliance tracking';
COMMENT ON TABLE system_metrics IS 'Stores system-wide performance metrics and KPIs';
COMMENT ON TABLE system_health IS 'Tracks system health checks, failures, and recovery';
COMMENT ON TABLE system_alerts IS 'System-level alerts for superadmin monitoring';

COMMENT ON COLUMN audit_logs.action_metadata IS 'JSON containing before/after states, classification details, and additional context';
COMMENT ON COLUMN system_metrics.details IS 'JSON containing metric breakdowns, distributions, and additional analysis';
COMMENT ON COLUMN system_health.request_context IS 'JSON containing request details that triggered the health check';
COMMENT ON COLUMN system_alerts.alert_data IS 'JSON containing alert-specific data and context';

DROP TABLE IF EXISTS Transactions CASCADE;

CREATE TABLE Transactions (
    transaction_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    timestamp TIMESTAMP,       -- Matches CSV header 'timestamp'
    amount DOUBLE PRECISION,
    currency VARCHAR(10),      -- e.g., 'USD'
    txn_type VARCHAR(50),      -- e.g., 'TRANSFER'
    counterparty_id BIGINT,
    is_fraud INT,              -- Matches '0' or '1' from CSV
    
    -- Foreign Key linkage
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- Index for time-based lookups
CREATE INDEX idx_txn_timestamp ON Transactions (user_id, timestamp DESC);
"