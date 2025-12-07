-- =============================================================================
-- SUPERADMIN MONITORING - COMPREHENSIVE DATA POPULATION SCRIPT
-- =============================================================================
-- This script populates all superadmin monitoring tables with realistic,
-- large-scale, time-varied sample data for testing and demonstration.
--
-- Data Coverage: 90 days of historical data with realistic patterns
-- Volume: 1000+ alerts, 500+ audit logs, 2700+ metrics, 50+ health events
--
-- Usage: psql -U your_username -d your_database -f populate_superadmin_monitoring_data.sql
-- =============================================================================

BEGIN;

-- Clean existing sample data first (optional, comment out if you want to keep existing data)
DELETE FROM audit_logs WHERE admin_id IN (SELECT id FROM admins WHERE email LIKE '%@compliance.com');
DELETE FROM system_alerts;
DELETE FROM system_health;
DELETE FROM system_metrics;
DELETE FROM compliance_alerts WHERE entity_id LIKE 'USR%';
DELETE FROM transactions WHERE transaction_id LIKE 'TXN%';
DELETE FROM users WHERE entity_id LIKE 'USR%';
DELETE FROM admins WHERE email LIKE '%@compliance.com';

-- =============================================================================
-- STEP 1: Create Sample Admin Users
-- =============================================================================

-- Create superadmin user
INSERT INTO admins (username, email, hashed_password, role, is_active, created_at, last_login_at)
VALUES 
    ('superadmin', 'superadmin@compliance.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5OgqJb5dCNo4e', 'superadmin', TRUE, NOW() - INTERVAL '90 days', NOW() - INTERVAL '2 hours'),
    ('admin_john', 'john.smith@compliance.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5OgqJb5dCNo4e', 'admin', TRUE, NOW() - INTERVAL '60 days', NOW() - INTERVAL '1 day'),
    ('admin_sarah', 'sarah.johnson@compliance.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5OgqJb5dCNo4e', 'admin', TRUE, NOW() - INTERVAL '45 days', NOW() - INTERVAL '3 hours'),
    ('admin_mike', 'mike.davis@compliance.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5OgqJb5dCNo4e', 'admin', TRUE, NOW() - INTERVAL '30 days', NOW() - INTERVAL '5 hours'),
    ('admin_emma', 'emma.wilson@compliance.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5OgqJb5dCNo4e', 'admin', TRUE, NOW() - INTERVAL '20 days', NOW() - INTERVAL '1 hour')
ON CONFLICT (username) DO NOTHING;

-- =============================================================================
-- STEP 2: Create Sample Users (50 users for realistic volume)
-- =============================================================================

INSERT INTO users (entity_id, applicant_name, email, phone, kyc_status, risk_level, suspicious_score, is_blacklisted, account_status, city, state, country, created_at)
SELECT 
    'USR' || LPAD(n::TEXT, 3, '0'),
    (ARRAY['Robert', 'Maria', 'David', 'Lisa', 'James', 'Jennifer', 'Michael', 'Amanda', 'Christopher', 'Patricia', 'Daniel', 'Elizabeth', 'Matthew', 'Jessica', 'Anthony', 'Sarah', 'Mark', 'Nancy', 'Donald', 'Karen'])[1 + (n % 20)] || ' ' ||
    (ARRAY['Johnson', 'Garcia', 'Chen', 'Anderson', 'Wilson', 'Brown', 'Taylor', 'Martinez', 'Lee', 'White', 'Harris', 'Clark', 'Lewis', 'Robinson', 'Walker', 'Young', 'King', 'Wright', 'Lopez', 'Hill'])[1 + ((n + 7) % 20)],
    'user' || n || '@email.com',
    '+1-555-' || LPAD(n::TEXT, 4, '0'),
    CASE 
        WHEN n % 10 = 0 THEN 'rejected'
        WHEN n % 15 = 0 THEN 'pending'
        ELSE 'approved'
    END,
    CASE 
        WHEN n % 20 = 0 THEN 'critical'
        WHEN n % 7 = 0 THEN 'high'
        WHEN n % 3 = 0 THEN 'medium'
        ELSE 'low'
    END,
    CASE 
        WHEN n % 20 = 0 THEN 90.0 + (RANDOM() * 10)
        WHEN n % 7 = 0 THEN 70.0 + (RANDOM() * 15)
        WHEN n % 3 = 0 THEN 45.0 + (RANDOM() * 20)
        ELSE 10.0 + (RANDOM() * 25)
    END,
    n % 20 = 0,
    CASE 
        WHEN n % 20 = 0 THEN 'suspended'
        WHEN n % 15 = 0 THEN 'under_investigation'
        ELSE 'active'
    END,
    (ARRAY['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose'])[1 + (n % 10)],
    (ARRAY['NY', 'CA', 'IL', 'TX', 'AZ', 'PA', 'TX', 'CA', 'TX', 'CA'])[1 + (n % 10)],
    'USA',
    NOW() - (n * INTERVAL '1.8 days')
FROM generate_series(1, 50) AS n
ON CONFLICT (entity_id) DO NOTHING;

-- =============================================================================
-- STEP 3: Create Sample Transactions (500 transactions over 90 days)
-- =============================================================================

INSERT INTO transactions (user_id, transaction_id, transaction_type, amount, currency, sender_account, receiver_account, risk_level, suspicious_score, is_flagged, status, transaction_date, created_at)
SELECT 
    u.id,
    'TXN' || LPAD(n::TEXT, 6, '0'),
    CASE (n % 5)
        WHEN 0 THEN 'deposit'
        WHEN 1 THEN 'withdrawal'
        WHEN 2 THEN 'transfer'
        WHEN 3 THEN 'payment'
        ELSE 'transfer'
    END,
    (RANDOM() * 50000 + 100)::DECIMAL(15,2),
    'USD',
    'ACC' || LPAD(u.id::TEXT, 6, '0'),
    'ACC' || LPAD(((u.id + n) % 50 + 1)::TEXT, 6, '0'),
    u.risk_level,
    u.suspicious_score + (RANDOM() * 20 - 10),
    u.suspicious_score > 50 OR (RANDOM() < 0.1),
    CASE 
        WHEN u.suspicious_score > 80 THEN 'under_review'
        WHEN u.suspicious_score > 50 AND RANDOM() < 0.3 THEN 'under_review'
        WHEN RANDOM() < 0.05 THEN 'failed'
        ELSE 'completed'
    END,
    NOW() - ((n * 0.18)::TEXT || ' days')::INTERVAL - (RANDOM() * INTERVAL '12 hours'),
    NOW() - ((n * 0.18)::TEXT || ' days')::INTERVAL - (RANDOM() * INTERVAL '12 hours')
FROM generate_series(1, 500) n
CROSS JOIN LATERAL (
    SELECT id, risk_level, suspicious_score 
    FROM users 
    WHERE entity_id LIKE 'USR%'
    ORDER BY RANDOM() 
    LIMIT 1
) u
ON CONFLICT (transaction_id) DO NOTHING;

-- =============================================================================
-- STEP 4: Create Sample Compliance Alerts (1000 alerts over 90 days)
-- =============================================================================

INSERT INTO compliance_alerts (
    user_id, transaction_id, alert_type, severity, title, description, 
    entity_id, entity_type, status, priority, is_true_positive, 
    reviewed_at, reviewed_by, triggered_at, created_at
)
SELECT 
    u.id,
    t.id,
    CASE (n % 7)
        WHEN 0 THEN 'fraud_alert'
        WHEN 1 THEN 'aml_alert'
        WHEN 2 THEN 'transaction_alert'
        WHEN 3 THEN 'sanction_alert'
        WHEN 4 THEN 'behavioral_alert'
        WHEN 5 THEN 'kyc_alert'
        ELSE 'transaction_alert'
    END,
    CASE 
        WHEN n % 20 = 0 THEN 'critical'
        WHEN n % 7 = 0 THEN 'high'
        WHEN n % 3 = 0 THEN 'medium'
        ELSE 'low'
    END,
    (ARRAY['Suspicious Activity', 'High Risk Transaction', 'AML Violation Suspected', 'Sanction List Match', 'Behavioral Anomaly', 'KYC Verification Issue'])[1 + (n % 6)] || ' - ' || u.applicant_name,
    (ARRAY['Multiple high-value transactions detected', 'Pattern matching known fraud schemes', 'Rapid movement of funds', 'Transaction with sanctioned entity', 'Unusual account activity', 'Documentation discrepancies'])[1 + (n % 6)],
    u.entity_id,
    'user',
    CASE 
        WHEN n % 5 = 0 THEN 'active'
        WHEN n % 5 = 1 THEN 'resolved'
        WHEN n % 5 = 2 THEN 'investigating'
        WHEN n % 5 = 3 THEN 'resolved'
        ELSE 'dismissed'
    END,
    CASE 
        WHEN n % 20 = 0 THEN 'critical'
        WHEN n % 7 = 0 THEN 'high'
        WHEN n % 3 = 0 THEN 'medium'
        ELSE 'low'
    END,
    CASE 
        -- Recent alerts (last 10 days) - mostly unclassified
        WHEN n <= 100 THEN 
            CASE WHEN n % 4 = 0 THEN TRUE WHEN n % 4 = 1 THEN FALSE ELSE NULL END
        -- Older alerts - mostly classified
        ELSE 
            CASE WHEN n % 5 = 0 THEN NULL WHEN n % 2 = 0 THEN TRUE ELSE FALSE END
    END,
    CASE 
        WHEN n % 5 = 0 THEN NULL  -- Active alerts not reviewed yet
        ELSE alert_time - (RANDOM() * INTERVAL '2 days')
    END,
    CASE 
        WHEN n % 5 = 0 THEN NULL
        ELSE (ARRAY['admin_john', 'admin_sarah', 'admin_mike', 'admin_emma'])[1 + (n % 4)]
    END,
    alert_time,
    alert_time
FROM generate_series(1, 1000) n
CROSS JOIN LATERAL (
    SELECT NOW() - ((n * 0.09)::TEXT || ' days')::INTERVAL - (RANDOM() * INTERVAL '12 hours') AS alert_time
) times
CROSS JOIN LATERAL (
    SELECT id, entity_id, applicant_name
    FROM users 
    WHERE entity_id LIKE 'USR%'
    ORDER BY RANDOM() 
    LIMIT 1
) u
LEFT JOIN LATERAL (
    SELECT id
    FROM transactions
    WHERE user_id = u.id
    ORDER BY RANDOM()
    LIMIT 1
) t ON true;

-- =============================================================================
-- STEP 5: Create Audit Logs (500+ entries correlated with actions)
-- =============================================================================

-- Audit logs for alert classifications (all classified alerts)
INSERT INTO audit_logs (
    admin_id, action_type, action_description, target_type, target_id, 
    target_identifier, action_metadata, ip_address, user_agent, created_at
)
SELECT 
    CASE 
        WHEN ca.reviewed_by = 'admin_john' THEN 2
        WHEN ca.reviewed_by = 'admin_sarah' THEN 3
        WHEN ca.reviewed_by = 'admin_mike' THEN 4
        WHEN ca.reviewed_by = 'admin_emma' THEN 5
        ELSE 2
    END,
    'classify_alert',
    'Classified alert ' || ca.id || ' as ' || 
    CASE 
        WHEN ca.is_true_positive = TRUE THEN 'true_positive'
        WHEN ca.is_true_positive = FALSE THEN 'false_positive'
        ELSE 'unclassified'
    END,
    'alert',
    ca.id,
    'alert_' || ca.id,
    jsonb_build_object(
        'previous_state', jsonb_build_object(
            'is_true_positive', NULL,
            'status', 'active',
            'reviewed_at', NULL
        ),
        'new_classification', 
        CASE 
            WHEN ca.is_true_positive = TRUE THEN 'true_positive'
            WHEN ca.is_true_positive = FALSE THEN 'false_positive'
            ELSE 'unclassified'
        END,
        'is_true_positive', ca.is_true_positive,
        'alert_type', ca.alert_type,
        'severity', ca.severity,
        'user_id', ca.user_id,
        'entity_id', ca.entity_id,
        'notes', (ARRAY['Confirmed through investigation', 'False alarm - legitimate transaction', 'Verified with customer', 'Pattern matches known fraud', 'Routine check'])[1 + (ca.id % 5)]
    ),
    (ARRAY['192.168.1.100', '192.168.1.101', '192.168.1.102', '10.0.0.50', '172.16.0.10'])[1 + (ca.id % 5)],
    (ARRAY[
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    ])[1 + (ca.id % 3)],
    ca.reviewed_at
FROM compliance_alerts ca
WHERE ca.is_true_positive IS NOT NULL AND ca.reviewed_at IS NOT NULL;

-- Audit logs for user blacklisting
INSERT INTO audit_logs (
    admin_id, action_type, action_description, target_type, target_id, 
    target_identifier, action_metadata, ip_address, user_agent, created_at
)
SELECT 
    3, -- admin_sarah
    'blacklist_user',
    'Blacklisted user ' || u.applicant_name || ' due to critical risk level',
    'user',
    u.id,
    u.entity_id,
    jsonb_build_object(
        'previous_state', jsonb_build_object(
            'is_blacklisted', FALSE,
            'account_status', 'active'
        ),
        'new_state', jsonb_build_object(
            'is_blacklisted', TRUE,
            'account_status', 'suspended'
        ),
        'reason', 'Multiple fraud alerts and critical risk score',
        'risk_level', u.risk_level,
        'suspicious_score', u.suspicious_score
    ),
    '192.168.1.101',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    NOW() - INTERVAL '10 days'
FROM users u
WHERE u.is_blacklisted = TRUE
LIMIT 5;

-- Audit logs for alert escalations
INSERT INTO audit_logs (
    admin_id, action_type, action_description, target_type, target_id, 
    target_identifier, action_metadata, ip_address, user_agent, created_at
)
SELECT 
    4, -- admin_mike
    'escalate_alert',
    'Escalated alert ' || ca.id || ' to senior compliance team',
    'alert',
    ca.id,
    'alert_' || ca.id,
    jsonb_build_object(
        'previous_state', jsonb_build_object('status', 'investigating'),
        'new_state', jsonb_build_object('status', 'escalated'),
        'escalation_reason', 'Requires legal team review',
        'severity', ca.severity,
        'alert_type', ca.alert_type
    ),
    '192.168.1.103',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    NOW() - INTERVAL '5 days'
FROM compliance_alerts ca
WHERE ca.severity IN ('high', 'critical')
LIMIT 5;

-- =============================================================================
-- STEP 6: Create System Metrics (2700+ entries across 90 days)
-- =============================================================================

-- Hourly alert hit rate metrics for the past 90 days (2160 entries)
INSERT INTO system_metrics (
    metric_type, metric_category, metric_value, metric_unit, time_window,
    aggregation_period_start, aggregation_period_end, 
    total_count, positive_count, negative_count, details, is_anomaly, recorded_at
)
SELECT 
    'alert_hit_rate',
    'alert',
    CASE 
        -- Recent week - degraded performance
        WHEN day_offset < 7 THEN 60.0 + (RANDOM() * 20)
        -- Last month - improving
        WHEN day_offset < 30 THEN 70.0 + (RANDOM() * 15)
        -- 30-60 days - stable
        WHEN day_offset < 60 THEN 78.0 + (RANDOM() * 12)
        -- 60-90 days - excellent
        ELSE 82.0 + (RANDOM() * 10)
    END,
    'percentage',
    'hourly',
    NOW() - (day_offset || ' days')::INTERVAL - (hour_offset || ' hours')::INTERVAL,
    NOW() - (day_offset || ' days')::INTERVAL - (hour_offset || ' hours')::INTERVAL + INTERVAL '1 hour',
    (3 + (RANDOM() * 15))::INT,
    (2 + (RANDOM() * 12))::INT,
    (1 + (RANDOM() * 5))::INT,
    jsonb_build_object(
        'by_severity', jsonb_build_object(
            'critical', 90.0 + (RANDOM() * 8),
            'high', 85.0 + (RANDOM() * 10),
            'medium', 75.0 + (RANDOM() * 12),
            'low', 65.0 + (RANDOM() * 15)
        ),
        'by_type', jsonb_build_object(
            'fraud_alert', 88.0 + (RANDOM() * 8),
            'aml_alert', 82.0 + (RANDOM() * 10),
            'transaction_alert', 75.0 + (RANDOM() * 12),
            'sanction_alert', 95.0 + (RANDOM() * 4),
            'behavioral_alert', 70.0 + (RANDOM() * 15)
        )
    ),
    -- Mark anomalies (very low hit rates)
    CASE WHEN (day_offset = 3 AND hour_offset = 14) OR (day_offset = 25 AND hour_offset = 8) THEN TRUE ELSE FALSE END,
    NOW() - (day_offset || ' days')::INTERVAL - (hour_offset || ' hours')::INTERVAL + INTERVAL '5 minutes'
FROM generate_series(0, 89) AS day_offset
CROSS JOIN generate_series(0, 23) AS hour_offset
WHERE (day_offset * 24 + hour_offset) % 1 = 0  -- All hours
LIMIT 2160;

-- Daily false positive rate metrics for 90 days
INSERT INTO system_metrics (
    metric_type, metric_category, metric_value, metric_unit, time_window,
    aggregation_period_start, aggregation_period_end, 
    total_count, positive_count, negative_count, details, is_anomaly, recorded_at
)
SELECT 
    'false_positive_rate',
    'alert',
    CASE 
        -- Anomaly spikes
        WHEN day_offset = 5 THEN 38.0
        WHEN day_offset = 47 THEN 35.5
        -- Recent degradation
        WHEN day_offset < 7 THEN 28.0 + (RANDOM() * 6)
        -- Last month
        WHEN day_offset < 30 THEN 22.0 + (RANDOM() * 6)
        -- Good period
        WHEN day_offset < 60 THEN 18.0 + (RANDOM() * 5)
        -- Excellent period
        ELSE 15.0 + (RANDOM() * 4)
    END,
    'percentage',
    'daily',
    NOW() - (day_offset || ' days')::INTERVAL,
    NOW() - (day_offset || ' days')::INTERVAL + INTERVAL '1 day',
    (25 + (RANDOM() * 40))::INT,
    (5 + (RANDOM() * 15))::INT,
    (20 + (RANDOM() * 25))::INT,
    jsonb_build_object(
        'by_severity', jsonb_build_object(
            'critical', 5.0 + (RANDOM() * 3),
            'high', 10.0 + (RANDOM() * 5),
            'medium', 20.0 + (RANDOM() * 8),
            'low', 30.0 + (RANDOM() * 12)
        ),
        'by_type', jsonb_build_object(
            'fraud_alert', 12.0 + (RANDOM() * 5),
            'aml_alert', 18.0 + (RANDOM() * 7),
            'transaction_alert', 25.0 + (RANDOM() * 10),
            'sanction_alert', 5.0 + (RANDOM() * 3),
            'behavioral_alert', 30.0 + (RANDOM() * 15)
        )
    ),
    day_offset IN (5, 47),
    NOW() - (day_offset || ' days')::INTERVAL + INTERVAL '2 hours'
FROM generate_series(0, 89) AS day_offset;

-- Hourly API response time metrics for 90 days (select hours)
INSERT INTO system_metrics (
    metric_type, metric_category, metric_value, metric_unit, time_window,
    aggregation_period_start, aggregation_period_end, 
    total_count, details, recorded_at
)
SELECT 
    'api_response_time',
    'api',
    CASE 
        -- Performance incidents
        WHEN (day_offset = 2 AND hour_offset BETWEEN 10 AND 14) THEN 8000.0 + (RANDOM() * 4000)
        WHEN (day_offset = 15 AND hour_offset BETWEEN 8 AND 10) THEN 5500.0 + (RANDOM() * 2000)
        WHEN (day_offset = 58 AND hour_offset = 3) THEN 12000.0 + (RANDOM() * 3000)
        -- Peak hours (slower)
        WHEN hour_offset BETWEEN 9 AND 17 THEN 400.0 + (RANDOM() * 600)
        -- Off-peak (faster)
        ELSE 180.0 + (RANDOM() * 320)
    END,
    'milliseconds',
    'hourly',
    NOW() - (day_offset || ' days')::INTERVAL - (hour_offset || ' hours')::INTERVAL,
    NOW() - (day_offset || ' days')::INTERVAL - (hour_offset || ' hours')::INTERVAL + INTERVAL '1 hour',
    (200 + (RANDOM() * 800))::INT,
    jsonb_build_object(
        'by_endpoint', jsonb_build_object(
            '/api/sanctions/check', 350 + (RANDOM() * 400),
            '/api/alerts/classify', 200 + (RANDOM() * 250),
            '/api/users/verify', 280 + (RANDOM() * 320),
            '/api/transactions/analyze', 450 + (RANDOM() * 550)
        ),
        'p50', 250 + (RANDOM() * 200),
        'p95', 800 + (RANDOM() * 600),
        'p99', 1500 + (RANDOM() * 1000)
    ),
    NOW() - (day_offset || ' days')::INTERVAL - (hour_offset || ' hours')::INTERVAL + INTERVAL '5 minutes'
FROM generate_series(0, 89) AS day_offset
CROSS JOIN generate_series(0, 23, 4) AS hour_offset  -- Every 4 hours
LIMIT 540;

-- Daily API error rate metrics for 90 days
INSERT INTO system_metrics (
    metric_type, metric_category, metric_value, metric_unit, time_window,
    aggregation_period_start, aggregation_period_end, 
    total_count, positive_count, negative_count, details, is_anomaly, recorded_at
)
SELECT 
    'api_error_rate',
    'api',
    CASE 
        -- Major incidents
        WHEN day_offset = 2 THEN 12.5
        WHEN day_offset = 15 THEN 9.8
        WHEN day_offset = 58 THEN 11.2
        -- Minor incidents
        WHEN day_offset IN (7, 22, 35, 71) THEN 5.5 + (RANDOM() * 2)
        -- Recent degradation
        WHEN day_offset < 7 THEN 2.5 + (RANDOM() * 2.5)
        -- Normal operation
        ELSE 0.3 + (RANDOM() * 1.5)
    END,
    'percentage',
    'daily',
    NOW() - (day_offset || ' days')::INTERVAL,
    NOW() - (day_offset || ' days')::INTERVAL + INTERVAL '1 day',
    (2000 + (RANDOM() * 3000))::INT,
    (10 + (RANDOM() * 100))::INT,
    (1890 + (RANDOM() * 2900))::INT,
    jsonb_build_object(
        'by_error_type', jsonb_build_object(
            'timeout', (2 + (RANDOM() * 8))::INT,
            'rate_limit', (1 + (RANDOM() * 3))::INT,
            'server_error', (3 + (RANDOM() * 12))::INT,
            'validation_error', (4 + (RANDOM() * 15))::INT,
            'database_error', (1 + (RANDOM() * 5))::INT
        ),
        'by_endpoint', jsonb_build_object(
            '/api/sanctions/check', ROUND((RANDOM() * 3)::NUMERIC, 2),
            '/api/alerts/classify', ROUND((RANDOM() * 2)::NUMERIC, 2),
            '/api/users/verify', ROUND((RANDOM() * 2.5)::NUMERIC, 2)
        )
    ),
    day_offset IN (2, 7, 15, 22, 35, 58, 71),
    NOW() - (day_offset || ' days')::INTERVAL + INTERVAL '3 hours'
FROM generate_series(0, 89) AS day_offset;

-- Daily alert response time metrics for 90 days
INSERT INTO system_metrics (
    metric_type, metric_category, metric_value, metric_unit, time_window,
    aggregation_period_start, aggregation_period_end, 
    details, recorded_at
)
SELECT 
    'alert_response_time',
    'alert',
    CASE 
        -- Slower response periods
        WHEN day_offset < 7 THEN 8.5 + (RANDOM() * 6)  -- Recent backlog
        WHEN day_offset < 30 THEN 5.0 + (RANDOM() * 4)
        -- Better response times
        WHEN day_offset < 60 THEN 3.5 + (RANDOM() * 3)
        ELSE 2.5 + (RANDOM() * 2.5)
    END * 3600,  -- Convert hours to seconds
    'seconds',
    'daily',
    NOW() - (day_offset || ' days')::INTERVAL,
    NOW() - (day_offset || ' days')::INTERVAL + INTERVAL '1 day',
    jsonb_build_object(
        'by_severity', jsonb_build_object(
            'critical', ROUND((0.5 + (RANDOM() * 1)) * 3600, 0),
            'high', ROUND((1.5 + (RANDOM() * 2)) * 3600, 0),
            'medium', ROUND((4.0 + (RANDOM() * 4)) * 3600, 0),
            'low', ROUND((10.0 + (RANDOM() * 12)) * 3600, 0)
        ),
        'avg_hours', ROUND(2.5 + (RANDOM() * 8), 2),
        'median_hours', ROUND(2.0 + (RANDOM() * 5), 2),
        'max_hours', ROUND(15.0 + (RANDOM() * 25), 2)
    ),
    NOW() - (day_offset || ' days')::INTERVAL + INTERVAL '4 hours'
FROM generate_series(0, 89) AS day_offset;

-- =============================================================================
-- STEP 7: Create System Health Events (50+ events over 90 days)
-- =============================================================================

-- Resolved health issues from the past
INSERT INTO system_health (
    check_type, component_name, status, severity, error_type, error_message,
    request_context, response_time_ms, retry_count, affected_operations,
    user_impact, is_resolved, resolved_at, resolution_notes, detected_at, last_occurrence, alert_sent
)
SELECT 
    (ARRAY['api_health', 'parser_health', 'db_health', 'service_health'])[1 + (n % 4)],
    (ARRAY['sanctions_api', 'payment_gateway', 'transaction_parser', 'postgres_primary', 'redis_cache', 'alert_service'])[1 + (n % 6)],
    'failed',
    CASE WHEN n % 5 = 0 THEN 'critical' WHEN n % 3 = 0 THEN 'error' ELSE 'warning' END,
    (ARRAY['ConnectionTimeout', 'ServiceUnavailable', 'ParseError', 'HighConnectionCount', 'MemoryLimit', 'RateLimitExceeded'])[1 + (n % 6)],
    (ARRAY[
        'Connection timeout after 5000ms',
        'Service returned 503 error',
        'Failed to parse input data',
        'Connection pool exhausted',
        'Memory usage exceeds 90% threshold',
        'Rate limit exceeded: 1000 req/min'
    ])[1 + (n % 6)],
    jsonb_build_object(
        'endpoint', '/api/' || (ARRAY['sanctions', 'payment', 'alerts', 'users'])[1 + (n % 4)],
        'request_id', 'REQ' || LPAD(n::TEXT, 6, '0'),
        'timestamp', (NOW() - ((n * 2)::TEXT || ' days')::INTERVAL)::TEXT
    ),
    CASE WHEN n % 4 = 0 THEN 5000 + (RANDOM() * 10000)::INT ELSE NULL END,
    n % 3,
    (ARRAY[
        '["sanctions_check"]'::jsonb,
        '["payment_processing"]'::jsonb,
        '["alert_creation", "user_flagging"]'::jsonb,
        '["all_database_operations"]'::jsonb
    ])[1 + (n % 4)],
    CASE WHEN n % 5 = 0 THEN 'critical' WHEN n % 3 = 0 THEN 'high' ELSE 'medium' END,
    TRUE,
    NOW() - ((n * 2)::TEXT || ' days')::INTERVAL + INTERVAL '4 hours',
    (ARRAY[
        'Service provider resolved infrastructure issue',
        'Scaled up resources to handle load',
        'Updated parser to handle edge cases',
        'Optimized database queries',
        'Increased memory allocation',
        'Adjusted rate limiting configuration'
    ])[1 + (n % 6)],
    NOW() - ((n * 2)::TEXT || ' days')::INTERVAL,
    NOW() - ((n * 2)::TEXT || ' days')::INTERVAL + INTERVAL '2 hours',
    TRUE
FROM generate_series(1, 35) n
WHERE n * 2 < 90;  -- Within 90 days

-- Active health issues (recent, unresolved)
INSERT INTO system_health (
    check_type, component_name, status, severity, error_type, error_message,
    request_context, response_time_ms, retry_count, affected_operations,
    user_impact, is_resolved, detected_at, last_occurrence, alert_sent
)
VALUES 
    (
        'api_health', 'sanctions_api', 'degraded', 'warning',
        'SlowResponse', 'API response time exceeding 2000ms threshold',
        '{"endpoint": "/api/sanctions/check", "avg_response_time_ms": 2450, "p95_ms": 3200}'::jsonb,
        2450, 0, '["sanctions_check", "user_verification"]'::jsonb,
        'medium', FALSE,
        NOW() - INTERVAL '2 hours', NOW() - INTERVAL '15 minutes', TRUE
    ),
    (
        'db_health', 'postgres_primary', 'degraded', 'warning',
        'HighConnectionCount', 'Database connection pool at 85% capacity',
        '{"database": "compliance_db", "active_connections": 85, "max_connections": 100, "idle": 5}'::jsonb,
        NULL, 0, '["all_database_operations"]'::jsonb,
        'medium', FALSE,
        NOW() - INTERVAL '1 hour', NOW() - INTERVAL '5 minutes', TRUE
    ),
    (
        'api_health', 'payment_gateway', 'failed', 'error',
        'IntermittentFailures', 'Sporadic 500 errors from payment gateway',
        '{"endpoint": "/api/payment/process", "error_rate": "8.5%", "total_requests": 250}'::jsonb,
        3500, 2, '["payment_processing", "transaction_completion"]'::jsonb,
        'high', FALSE,
        NOW() - INTERVAL '45 minutes', NOW() - INTERVAL '10 minutes', TRUE
    ),
    (
        'parser_health', 'transaction_parser', 'failed', 'warning',
        'ParseError', 'Occasional parsing failures on malformed data',
        '{"failure_rate": "2.3%", "parser_version": "2.1.5", "sample_error": "Invalid currency code"}'::jsonb,
        85, 0, '["transaction_ingestion"]'::jsonb,
        'low', FALSE,
        NOW() - INTERVAL '3 hours', NOW() - INTERVAL '25 minutes', FALSE
    ),
    (
        'service_health', 'redis_cache', 'degraded', 'warning',
        'HighMemoryUsage', 'Redis memory usage at 82% capacity',
        '{"used_memory_mb": 3280, "max_memory_mb": 4000, "eviction_policy": "allkeys-lru"}'::jsonb,
        NULL, 0, '["caching", "session_management"]'::jsonb,
        'low', FALSE,
        NOW() - INTERVAL '6 hours', NOW() - INTERVAL '1 hour', TRUE
    ),
    (
        'service_health', 'alert_classification_service', 'healthy', 'info',
        NULL, 'Service operating normally',
        '{"uptime_hours": 168, "requests_processed": 15420, "avg_response_ms": 145}'::jsonb,
        NULL, 0, NULL,
        'none', FALSE,
        NOW() - INTERVAL '7 days', NOW() - INTERVAL '5 minutes', FALSE
    );

-- =============================================================================
-- STEP 8: Create System Alerts (30+ alerts over 90 days)
-- =============================================================================

-- Resolved system alerts (historical)
INSERT INTO system_alerts (
    alert_type, title, description, severity, component, metric_type,
    threshold_value, actual_value, alert_data, status, acknowledged_by,
    acknowledged_at, resolved_at, resolution_notes, triggered_at, last_updated, notifications_sent
)
SELECT 
    (ARRAY['high_error_rate', 'api_downtime', 'threshold_breach', 'anomaly_detected', 'health_check_failed', 'performance_degradation'])[1 + (n % 6)],
    (ARRAY[
        'Critical API Error Rate Spike',
        'Service Downtime Detected',
        'Threshold Breach Alert',
        'Unusual System Behavior',
        'Health Check Failure',
        'Performance Degradation'
    ])[1 + (n % 6)],
    (ARRAY[
        'API error rate exceeded acceptable thresholds',
        'Service unavailable for extended period',
        'System metric exceeded configured threshold',
        'Anomalous pattern detected in system behavior',
        'Critical health check failed multiple times',
        'System performance degraded below SLA'
    ])[1 + (n % 6)],
    CASE WHEN n % 5 = 0 THEN 'critical' WHEN n % 3 = 0 THEN 'error' ELSE 'warning' END,
    (ARRAY['payment_gateway', 'sanctions_api', 'alert_system', 'transaction_parser', 'postgres_primary', 'redis_cache'])[1 + (n % 6)],
    (ARRAY['api_error_rate', 'api_response_time', 'false_positive_rate', 'alert_hit_rate', NULL])[1 + (n % 5)],
    (ARRAY['5%', '2000ms', '30%', '75%', 'N/A'])[1 + (n % 5)],
    (ARRAY['12.5%', '8500ms', '38%', '62%', '15 failures'])[1 + (n % 5)],
    jsonb_build_object(
        'total_requests', 1000 + (n * 50),
        'failed_count', 50 + (n * 2),
        'time_window', (ARRAY['1h', '2h', '6h', '12h'])[1 + (n % 4)],
        'trend', (ARRAY['increasing', 'stable', 'decreasing'])[1 + (n % 3)]
    ),
    'resolved',
    (ARRAY['superadmin', 'admin_john', 'admin_sarah', 'admin_mike'])[1 + (n % 4)],
    alert_time + ((n % 3 + 1)::TEXT || ' hours')::INTERVAL,
    alert_time + ((n % 3 + 4)::TEXT || ' hours')::INTERVAL,
    (ARRAY[
        'Issue resolved after service restart',
        'Provider fixed infrastructure problem',
        'Configuration updated to new thresholds',
        'False alarm - expected behavior during maintenance',
        'Patched with hotfix deployment',
        'Load balanced to handle traffic spike'
    ])[1 + (n % 6)],
    alert_time,
    alert_time + ((n % 3 + 4)::TEXT || ' hours')::INTERVAL,
    2 + (n % 4)
FROM generate_series(1, 25) n
CROSS JOIN LATERAL (
    SELECT NOW() - ((n * 3.6)::TEXT || ' days')::INTERVAL AS alert_time
) times;

-- Active system alerts (recent, not resolved)
INSERT INTO system_alerts (
    alert_type, title, description, severity, component, metric_type,
    threshold_value, actual_value, alert_data, status, acknowledged_by,
    acknowledged_at, triggered_at, last_updated, notifications_sent
)
VALUES 
    (
        'threshold_breach', 'High False Positive Rate',
        'False positive rate is 32.5%, exceeding 30% threshold for the past 6 hours',
        'warning', 'alert_system', 'false_positive_rate',
        '30%', '32.5%',
        '{"total_alerts": 150, "false_positives": 49, "time_window": "6h", "trend": "increasing"}'::jsonb,
        'active', NULL, NULL,
        NOW() - INTERVAL '4 hours', NOW() - INTERVAL '3 hours', 3
    ),
    (
        'api_downtime', 'Sanctions API Degraded Performance',
        'Sanctions API response time consistently exceeding 2000ms',
        'warning', 'sanctions_api', 'api_response_time',
        '2000ms', '2450ms',
        '{"endpoint": "/api/sanctions/check", "avg_response_time_ms": 2450, "p95_ms": 3200, "failure_count": 5}'::jsonb,
        'acknowledged', 'superadmin', NOW() - INTERVAL '1 hour',
        NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 hour', 4
    ),
    (
        'threshold_breach', 'Database Connection Pool Near Capacity',
        'Database connection pool utilization at 85%, approaching maximum',
        'warning', 'postgres_primary', NULL,
        '80%', '85%',
        '{"active_connections": 85, "max_connections": 100, "idle_connections": 5}'::jsonb,
        'acknowledged', 'admin_john', NOW() - INTERVAL '30 minutes',
        NOW() - INTERVAL '1 hour', NOW() - INTERVAL '30 minutes', 2
    ),
    (
        'high_error_rate', 'Payment Gateway Error Spike',
        'Payment gateway experiencing elevated error rates',
        'error', 'payment_gateway', 'api_error_rate',
        '5%', '8.5%',
        '{"total_requests": 250, "failed_requests": 21, "primary_errors": ["500", "503"], "time_window": "1h"}'::jsonb,
        'active', NULL, NULL,
        NOW() - INTERVAL '45 minutes', NOW() - INTERVAL '30 minutes', 2
    ),
    (
        'performance_degradation', 'Redis Cache Memory High',
        'Redis cache memory usage approaching capacity limits',
        'warning', 'redis_cache', NULL,
        '80%', '82%',
        '{"used_memory_mb": 3280, "max_memory_mb": 4000, "eviction_count": 145, "hit_rate": "94.2%"}'::jsonb,
        'active', NULL, NULL,
        NOW() - INTERVAL '6 hours', NOW() - INTERVAL '5 hours', 1
    );

-- =============================================================================
-- STEP 9: Create Additional Audit Logs for System Actions
-- =============================================================================

-- Audit logs for system alert acknowledgments
INSERT INTO audit_logs (
    admin_id, action_type, action_description, target_type, target_id,
    target_identifier, action_metadata, ip_address, user_agent, created_at
)
SELECT 
    CASE 
        WHEN sa.acknowledged_by = 'superadmin' THEN 1
        WHEN sa.acknowledged_by = 'admin_john' THEN 2
        WHEN sa.acknowledged_by = 'admin_sarah' THEN 3
        WHEN sa.acknowledged_by = 'admin_mike' THEN 4
        ELSE 1
    END,
    'update_system_alert',
    'Acknowledged system alert: ' || sa.title,
    'system',
    sa.id,
    'system_alert_' || sa.id,
    jsonb_build_object(
        'alert_type', sa.alert_type,
        'severity', sa.severity,
        'previous_status', 'active',
        'new_status', sa.status,
        'component', sa.component,
        'action', 'acknowledged'
    ),
    '192.168.1.100',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    sa.acknowledged_at
FROM system_alerts sa
WHERE sa.acknowledged_at IS NOT NULL;

-- Audit logs for health check resolutions
INSERT INTO audit_logs (
    admin_id, action_type, action_description, target_type, target_id,
    target_identifier, action_metadata, ip_address, user_agent, created_at
)
SELECT 
    1, -- superadmin
    'resolve_health_check',
    'Resolved health check issue: ' || sh.component_name,
    'system',
    sh.id,
    'health_check_' || sh.id,
    jsonb_build_object(
        'check_type', sh.check_type,
        'component_name', sh.component_name,
        'severity', sh.severity,
        'error_type', sh.error_type,
        'resolution_notes', sh.resolution_notes,
        'auto_recovered', sh.auto_recovered
    ),
    '192.168.1.100',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    sh.resolved_at
FROM system_health sh
WHERE sh.is_resolved = TRUE AND sh.resolved_at IS NOT NULL;

-- Audit logs for acknowledged system alerts
INSERT INTO audit_logs (
    admin_id, action_type, action_description, target_type, target_id, target_identifier,
    changes, ip_address, user_agent, created_at
)
SELECT 
    CASE sa.acknowledged_by
        WHEN 'superadmin' THEN 1
        WHEN 'admin_john' THEN 2
        WHEN 'admin_sarah' THEN 3
        WHEN 'admin_mike' THEN 4
        WHEN 'admin_emily' THEN 5
    END,
    'acknowledge_alert',
    'Acknowledged system alert: ' || sa.title,
    'system_alert',
    sa.id,
    'alert_' || sa.id,
    jsonb_build_object(
        'alert_type', sa.alert_type,
        'severity', sa.severity,
        'component', sa.component,
        'threshold_value', sa.threshold_value,
        'actual_value', sa.actual_value
    ),
    '192.168.1.' || (100 + (sa.id % 50)),
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    sa.acknowledged_at
FROM system_alerts sa
WHERE sa.acknowledged_at IS NOT NULL;

-- Audit logs for resolved system alerts
INSERT INTO audit_logs (
    admin_id, action_type, action_description, target_type, target_id, target_identifier,
    changes, ip_address, user_agent, created_at
)
SELECT 
    CASE sa.acknowledged_by
        WHEN 'superadmin' THEN 1
        WHEN 'admin_john' THEN 2
        WHEN 'admin_sarah' THEN 3
        WHEN 'admin_mike' THEN 4
        WHEN 'admin_emily' THEN 5
    END,
    'resolve_alert',
    'Resolved system alert: ' || sa.title,
    'system_alert',
    sa.id,
    'alert_' || sa.id,
    jsonb_build_object(
        'alert_type', sa.alert_type,
        'severity', sa.severity,
        'component', sa.component,
        'resolution_notes', sa.resolution_notes,
        'time_to_resolve_hours', EXTRACT(EPOCH FROM (sa.resolved_at - sa.triggered_at)) / 3600
    ),
    '192.168.1.' || (100 + (sa.id % 50)),
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    sa.resolved_at
FROM system_alerts sa
WHERE sa.resolved_at IS NOT NULL;

-- =============================================================================
-- STEP 10: Verify Data Population
-- =============================================================================

-- Show summary of created data
DO $$
DECLARE
    admin_count INTEGER;
    user_count INTEGER;
    transaction_count INTEGER;
    alert_count INTEGER;
    audit_count INTEGER;
    metric_count INTEGER;
    health_count INTEGER;
    system_alert_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO admin_count FROM admins;
    SELECT COUNT(*) INTO user_count FROM users;
    SELECT COUNT(*) INTO transaction_count FROM transactions;
    SELECT COUNT(*) INTO alert_count FROM compliance_alerts;
    SELECT COUNT(*) INTO audit_count FROM audit_logs;
    SELECT COUNT(*) INTO metric_count FROM system_metrics;
    SELECT COUNT(*) INTO health_count FROM system_health;
    SELECT COUNT(*) INTO system_alert_count FROM system_alerts;
    
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'DATA POPULATION SUMMARY';
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'Admins:             %', admin_count;
    RAISE NOTICE 'Users:              %', user_count;
    RAISE NOTICE 'Transactions:       %', transaction_count;
    RAISE NOTICE 'Compliance Alerts:  %', alert_count;
    RAISE NOTICE 'Audit Logs:         %', audit_count;
    RAISE NOTICE 'System Metrics:     %', metric_count;
    RAISE NOTICE 'Health Checks:      %', health_count;
    RAISE NOTICE 'System Alerts:      %', system_alert_count;
    RAISE NOTICE '=============================================================================';
END $$;

COMMIT;

-- =============================================================================
-- VERIFICATION QUERIES - Test Time-Based Data Distribution
-- =============================================================================

-- View recent audit logs with admin details
SELECT 
    al.id,
    a.username as admin,
    al.action_type,
    al.action_description,
    al.target_type,
    al.created_at
FROM audit_logs al
JOIN admins a ON al.admin_id = a.id
ORDER BY al.created_at DESC
LIMIT 10;

-- View active system issues
SELECT * FROM v_active_system_issues LIMIT 10;

-- View metrics summary for last 24 hours
SELECT * FROM v_metrics_last_24h;

-- Calculate current system health status
SELECT get_system_health_status() as system_status;

-- Show alert classification statistics
SELECT 
    COUNT(*) as total_alerts,
    COUNT(*) FILTER (WHERE is_true_positive = TRUE) as true_positives,
    COUNT(*) FILTER (WHERE is_true_positive = FALSE) as false_positives,
    COUNT(*) FILTER (WHERE is_true_positive IS NULL) as unclassified,
    ROUND(
        COUNT(*) FILTER (WHERE is_true_positive = TRUE)::NUMERIC / 
        NULLIF(COUNT(*) FILTER (WHERE is_true_positive IS NOT NULL), 0) * 100, 
        2
    ) as hit_rate_percent
FROM compliance_alerts;

-- =============================================================================
-- TIME-BASED DATA VERIFICATION (Test Different Periods)
-- =============================================================================

-- Test 1: Transactions per week over 90 days
SELECT 
    DATE_TRUNC('week', created_at) as week,
    COUNT(*) as transaction_count,
    COUNT(DISTINCT user_id) as unique_users
FROM transactions
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY week DESC;

-- Test 2: Alerts by classification status across different months
SELECT 
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as total_alerts,
    COUNT(*) FILTER (WHERE is_true_positive = TRUE) as true_positives,
    COUNT(*) FILTER (WHERE is_true_positive = FALSE) as false_positives,
    COUNT(*) FILTER (WHERE is_true_positive IS NULL) as unclassified
FROM compliance_alerts
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month DESC;

-- Test 3: System metrics trend comparison (7 days vs 30 days vs 90 days)
SELECT 
    metric_type,
    ROUND(AVG(metric_value) FILTER (WHERE recorded_at >= NOW() - INTERVAL '7 days'), 2) as avg_last_7_days,
    ROUND(AVG(metric_value) FILTER (WHERE recorded_at >= NOW() - INTERVAL '30 days'), 2) as avg_last_30_days,
    ROUND(AVG(metric_value) FILTER (WHERE recorded_at >= NOW() - INTERVAL '90 days'), 2) as avg_last_90_days,
    COUNT(*) as total_records
FROM system_metrics
GROUP BY metric_type
ORDER BY metric_type;

-- Test 4: Alert response time trend over time
SELECT 
    DATE_TRUNC('day', recorded_at) as date,
    ROUND(AVG(metric_value), 2) as avg_response_time_hours,
    MIN(metric_value) as min_response_time,
    MAX(metric_value) as max_response_time
FROM system_metrics
WHERE metric_type = 'alert_response_time'
GROUP BY DATE_TRUNC('day', recorded_at)
ORDER BY date DESC
LIMIT 30;

-- Test 5: System health issues distribution over time
SELECT 
    DATE_TRUNC('week', detected_at) as week,
    COUNT(*) as total_issues,
    COUNT(*) FILTER (WHERE is_resolved = TRUE) as resolved,
    COUNT(*) FILTER (WHERE is_resolved = FALSE) as active,
    COUNT(DISTINCT component) as affected_components
FROM system_health
GROUP BY DATE_TRUNC('week', detected_at)
ORDER BY week DESC;

-- Test 6: System alerts by status and time period
SELECT 
    CASE 
        WHEN triggered_at >= NOW() - INTERVAL '7 days' THEN 'Last 7 days'
        WHEN triggered_at >= NOW() - INTERVAL '30 days' THEN 'Last 30 days'
        ELSE 'Last 90 days'
    END as time_period,
    status,
    COUNT(*) as alert_count,
    ARRAY_AGG(DISTINCT severity) as severities
FROM system_alerts
GROUP BY time_period, status
ORDER BY time_period DESC, status;

-- =============================================================================
-- END OF DATA POPULATION SCRIPT
-- =============================================================================
