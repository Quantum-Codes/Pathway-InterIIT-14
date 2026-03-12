-- =============================================================================
-- DUMMY DATA POPULATION SCRIPT - ORIGINAL SCHEMA
-- =============================================================================
-- This script populates test data using the ORIGINAL schema structure
-- Includes: admin, superadmin, test users, transactions, and alerts
-- =============================================================================

-- =============================================================================
-- STEP 1: Create admin and superadmin accounts
-- =============================================================================

-- Password hashes for 'admin123' and 'superadmin123'
-- These are bcrypt hashes generated with cost=12
INSERT INTO admins (username, email, hashed_password, role, created_at, updated_at)
VALUES 
    ('admin', 'admin@compliance.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg7CW', 'admin', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('superadmin', 'superadmin@compliance.local', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'superadmin', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (username) DO NOTHING;

\echo '✅ Admin accounts created: admin/admin123, superadmin/superadmin123'

-- =============================================================================
-- STEP 2: Create test users (ORIGINAL SCHEMA)
-- =============================================================================

INSERT INTO Users (
    user_id, uin, uin_hash, username, profile_pic, email, phone,
    date_of_birth, address, occupation, annual_income,
    kyc_status, credit_score, blacklisted, 
    current_rps_not, current_rps_360, risk_category,
    version, time, diff, created_at, updated_at
) VALUES
    -- High Risk Users
    (1001, 'UIN1001', 'hash1001', 'john_doe', NULL, 'john.doe@email.com', '9876543210',
     '1985-03-15', '123 Main St, Mumbai', 'Business Owner', 1500000,
     'approved', 720, FALSE,
     75.5, 82.3, 'high',
     1, EXTRACT(EPOCH FROM NOW())::BIGINT, 0, NOW(), NOW()),
    
    (1002, 'UIN1002', 'hash1002', 'jane_smith', NULL, 'jane.smith@email.com', '9876543211',
     '1990-07-22', '456 Park Ave, Delhi', 'Software Engineer', 1200000,
     'approved', 680, TRUE,
     88.2, 91.5, 'critical',
     1, EXTRACT(EPOCH FROM NOW())::BIGINT, 0, NOW(), NOW() - INTERVAL '2 days'),
    
    -- Medium Risk Users
    (1003, 'UIN1003', 'hash1003', 'bob_johnson', NULL, 'bob.j@email.com', '9876543212',
     '1988-11-30', '789 Lake Road, Bangalore', 'Doctor', 2000000,
     'approved', 750, FALSE,
     45.8, 52.1, 'medium',
     1, EXTRACT(EPOCH FROM NOW())::BIGINT, 0, NOW(), NOW()),
    
    (1004, 'UIN1004', 'hash1004', 'alice_wong', NULL, 'alice.w@email.com', '9876543213',
     '1992-05-18', '321 Hill St, Chennai', 'Teacher', 600000,
     'approved', 690, FALSE,
     38.5, 41.2, 'medium',
     1, EXTRACT(EPOCH FROM NOW())::BIGINT, 0, NOW(), NOW()),
    
    -- Low Risk Users
    (1005, 'UIN1005', 'hash1005', 'charlie_brown', NULL, 'charlie@email.com', '9876543214',
     '1995-01-10', '555 River St, Pune', 'Analyst', 800000,
     'approved', 780, FALSE,
     12.3, 15.8, 'low',
     1, EXTRACT(EPOCH FROM NOW())::BIGINT, 0, NOW(), NOW()),
    
    (1006, 'UIN1006', 'hash1006', 'diana_prince', NULL, 'diana@email.com', '9876543215',
     '1987-09-25', '777 Ocean Drive, Hyderabad', 'Manager', 1800000,
     'approved', 810, FALSE,
     8.5, 10.2, 'low',
     1, EXTRACT(EPOCH FROM NOW())::BIGINT, 0, NOW(), NOW()),
    
    -- Pending KYC
    (1007, 'UIN1007', 'hash1007', 'eve_adams', NULL, 'eve@email.com', '9876543216',
     '1993-12-05', '888 Garden St, Kolkata', 'Freelancer', 500000,
     'pending', 650, FALSE,
     25.3, 28.7, 'medium',
     1, EXTRACT(EPOCH FROM NOW())::BIGINT, 0, NOW(), NOW()),
    
    (1008, 'UIN1008', 'hash1008', 'frank_castle', NULL, 'frank@email.com', '9876543217',
     '1980-06-14', '999 Castle Road, Jaipur', 'Entrepreneur', 3000000,
     'under_review', 700, FALSE,
     55.2, 60.8, 'high',
     1, EXTRACT(EPOCH FROM NOW())::BIGINT, 0, NOW(), NOW()),
    
    -- Recently Blacklisted
    (1009, 'UIN1009', 'hash1009', 'grace_hopper', NULL, 'grace@email.com', '9876543218',
     '1991-04-20', '111 Tech Park, Ahmedabad', 'Developer', 900000,
     'approved', 640, TRUE,
     92.5, 95.3, 'critical',
     1, EXTRACT(EPOCH FROM NOW())::BIGINT, 0, NOW() - INTERVAL '5 days', NOW()),
    
    -- Young Professional
    (1010, 'UIN1010', 'hash1010', 'henry_ford', NULL, 'henry@email.com', '9876543219',
     '1998-08-30', '222 Auto Street, Surat', 'Graduate Trainee', 400000,
     'approved', 660, FALSE,
     18.2, 22.5, 'low',
     1, EXTRACT(EPOCH FROM NOW())::BIGINT, 0, NOW(), NOW());

\echo '✅ Created 10 test users with varying risk profiles'

-- =============================================================================
-- STEP 3: Create test transactions (ORIGINAL SCHEMA)
-- =============================================================================

INSERT INTO Transactions (
    transaction_id, user_id, timestamp, amount, currency, 
    txn_type, counterparty_id, is_fraud
) VALUES
    -- Normal transactions
    (2001, 1001, NOW() - INTERVAL '1 day', 50000, 'INR', 'TRANSFER', 1003, 0),
    (2002, 1003, NOW() - INTERVAL '2 days', 25000, 'INR', 'DEPOSIT', NULL, 0),
    (2003, 1005, NOW() - INTERVAL '1 hour', 10000, 'INR', 'WITHDRAWAL', NULL, 0),
    (2004, 1006, NOW() - INTERVAL '3 hours', 75000, 'INR', 'TRANSFER', 1004, 0),
    (2005, 1010, NOW() - INTERVAL '12 hours', 5000, 'INR', 'PAYMENT', 1005, 0),
    
    -- Suspicious transactions (is_fraud = 1)
    (2006, 1002, NOW() - INTERVAL '6 hours', 500000, 'INR', 'TRANSFER', 1009, 1),
    (2007, 1002, NOW() - INTERVAL '8 hours', 300000, 'INR', 'WITHDRAWAL', NULL, 1),
    (2008, 1008, NOW() - INTERVAL '2 days', 250000, 'INR', 'TRANSFER', NULL, 1),
    (2009, 1009, NOW() - INTERVAL '1 day', 450000, 'INR', 'TRANSFER', 1002, 1),
    
    -- Recent large transactions
    (2010, 1001, NOW() - INTERVAL '30 minutes', 100000, 'INR', 'TRANSFER', 1006, 0),
    (2011, 1004, NOW() - INTERVAL '2 hours', 35000, 'INR', 'PAYMENT', NULL, 0),
    (2012, 1007, NOW() - INTERVAL '4 hours', 15000, 'INR', 'DEPOSIT', NULL, 0),
    
    -- High frequency from same user
    (2013, 1001, NOW() - INTERVAL '45 minutes', 80000, 'INR', 'TRANSFER', 1005, 0),
    (2014, 1001, NOW() - INTERVAL '1 hour 15 minutes', 60000, 'INR', 'TRANSFER', 1010, 0),
    (2015, 1001, NOW() - INTERVAL '1 hour 45 minutes', 70000, 'INR', 'PAYMENT', NULL, 0),
    
    -- Cross-border (different currency)
    (2016, 1003, NOW() - INTERVAL '5 hours', 2000, 'USD', 'TRANSFER', NULL, 0),
    (2017, 1006, NOW() - INTERVAL '1 day', 1500, 'EUR', 'PAYMENT', NULL, 0),
    
    -- Potential fraud patterns
    (2018, 1008, NOW() - INTERVAL '3 hours', 200000, 'INR', 'WITHDRAWAL', NULL, 1),
    (2019, 1009, NOW() - INTERVAL '4 hours', 180000, 'INR', 'TRANSFER', 1001, 1),
    (2020, 1002, NOW() - INTERVAL '10 hours', 350000, 'INR', 'PAYMENT', NULL, 1);

\echo '✅ Created 20 test transactions (15 normal, 5 fraudulent)'

-- =============================================================================
-- STEP 4: Create compliance alerts (NO classification fields)
-- =============================================================================

INSERT INTO compliance_alerts (
    user_id, transaction_id, alert_type, severity, title, description,
    entity_id, entity_type, rps360, status, priority,
    is_acknowledged, source, triggered_by,
    triggered_at, created_at, updated_at
) VALUES
    -- Critical alerts for blacklisted users
    (1002, 2006, 'fraud_alert', 'critical', 'Large Transfer from Blacklisted User', 
     'User 1002 (blacklisted) attempted transfer of INR 500,000', 
     'UIN1002', 'user', 91.5, 'active', 'critical',
     FALSE, 'fraud_detection_system', 'automated_check',
     NOW() - INTERVAL '6 hours', NOW() - INTERVAL '6 hours', NOW() - INTERVAL '6 hours'),
    
    (1009, 2009, 'fraud_alert', 'critical', 'Blacklisted User Transaction',
     'User 1009 (recently blacklisted) made large transfer',
     'UIN1009', 'user', 95.3, 'investigating', 'critical',
     TRUE, 'fraud_detection_system', 'automated_check',
     NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day', NOW() - INTERVAL '12 hours'),
    
    -- High risk alerts
    (1001, 2010, 'behavioral_alert', 'high', 'High Frequency Transactions',
     'User 1001 made 4 large transactions in 2 hours',
     'UIN1001', 'user', 82.3, 'active', 'high',
     FALSE, 'behavioral_analysis', 'pattern_detection',
     NOW() - INTERVAL '30 minutes', NOW() - INTERVAL '30 minutes', NOW() - INTERVAL '30 minutes'),
    
    (1008, 2018, 'transaction_alert', 'high', 'Large Withdrawal Detected',
     'Unusual withdrawal amount of INR 200,000',
     'UIN1008', 'user', 60.8, 'active', 'high',
     FALSE, 'transaction_monitoring', 'threshold_check',
     NOW() - INTERVAL '3 hours', NOW() - INTERVAL '3 hours', NOW() - INTERVAL '3 hours'),
    
    -- Medium severity alerts
    (1007, NULL, 'kyc_alert', 'medium', 'Pending KYC Verification',
     'KYC documents pending review for over 7 days',
     'UIN1007', 'user', 28.7, 'active', 'medium',
     FALSE, 'kyc_system', 'scheduled_check',
     NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),
    
    (1004, 2011, 'transaction_alert', 'medium', 'Unusual Payment Pattern',
     'Payment to new counterparty - review recommended',
     'UIN1004', 'user', 41.2, 'investigating', 'medium',
     TRUE, 'transaction_monitoring', 'rule_based',
     NOW() - INTERVAL '2 hours', NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 hour'),
    
    -- Resolved alerts
    (1005, 2003, 'transaction_alert', 'low', 'Small Withdrawal',
     'Minor withdrawal - routine check',
     'UIN1005', 'user', 15.8, 'resolved', 'low',
     TRUE, 'transaction_monitoring', 'automated_check',
     NOW() - INTERVAL '1 hour', NOW() - INTERVAL '1 hour', NOW() - INTERVAL '30 minutes'),
    
    (1006, 2004, 'transaction_alert', 'low', 'Standard Transfer Alert',
     'Regular transfer between known parties',
     'UIN1006', 'user', 10.2, 'resolved', 'low',
     TRUE, 'transaction_monitoring', 'routine_scan',
     NOW() - INTERVAL '3 hours', NOW() - INTERVAL '3 hours', NOW() - INTERVAL '2 hours'),
    
    -- AML alerts
    (1002, 2007, 'aml_alert', 'critical', 'Suspicious Cash Withdrawal',
     'Large cash withdrawal from blacklisted account',
     'UIN1002', 'user', 91.5, 'escalated', 'critical',
     TRUE, 'aml_system', 'compliance_rule',
     NOW() - INTERVAL '8 hours', NOW() - INTERVAL '8 hours', NOW() - INTERVAL '4 hours'),
    
    (1003, 2016, 'aml_alert', 'medium', 'Cross-Border Transaction',
     'USD transfer requires additional screening',
     'UIN1003', 'user', 52.1, 'investigating', 'medium',
     TRUE, 'aml_system', 'cross_border_check',
     NOW() - INTERVAL '5 hours', NOW() - INTERVAL '5 hours', NOW() - INTERVAL '3 hours'),
    
    -- Dismissed alerts
    (1010, 2005, 'transaction_alert', 'low', 'Small Payment',
     'Routine small payment - no risk',
     'UIN1010', 'user', 22.5, 'dismissed', 'low',
     TRUE, 'transaction_monitoring', 'automated_check',
     NOW() - INTERVAL '12 hours', NOW() - INTERVAL '12 hours', NOW() - INTERVAL '10 hours'),
    
    (1005, NULL, 'behavioral_alert', 'low', 'Login from New Device',
     'User logged in from new device - verified',
     'UIN1005', 'user', 15.8, 'dismissed', 'low',
     TRUE, 'security_system', 'device_fingerprint',
     NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day', NOW() - INTERVAL '18 hours');

\echo '✅ Created 12 compliance alerts (NO is_true_positive column)'

-- =============================================================================
-- STEP 5: Create audit log entries
-- =============================================================================

INSERT INTO audit_logs (
    admin_id, action_type, action_description, target_type, target_id, target_identifier,
    action_metadata, ip_address, created_at
) VALUES
    (1, 'blacklist_user', 'Blacklisted user due to fraudulent activity', 'user', 1002, 'UIN1002',
     '{"reason": "Multiple fraudulent transactions", "previous_state": {"blacklisted": false}}'::jsonb,
     '192.168.1.100', NOW() - INTERVAL '2 days'),
    
    (2, 'escalate_alert', 'Escalated critical AML alert', 'alert', 9, 'alert_9',
     '{"severity": "critical", "reason": "Large cash withdrawal from blacklisted account"}'::jsonb,
     '192.168.1.101', NOW() - INTERVAL '4 hours'),
    
    (1, 'dismiss_alert', 'Dismissed low priority alert', 'alert', 11, 'alert_11',
     '{"reason": "Verified as routine payment", "classification": "false_positive"}'::jsonb,
     '192.168.1.100', NOW() - INTERVAL '10 hours'),
    
    (2, 'blacklist_user', 'Blacklisted user after investigation', 'user', 1009, 'UIN1009',
     '{"reason": "Confirmed fraudulent pattern", "investigation_id": "INV-2024-001"}'::jsonb,
     '192.168.1.101', NOW() - INTERVAL '5 days');

\echo '✅ Created 4 audit log entries'

-- =============================================================================
-- STEP 6: Display summary
-- =============================================================================

\echo ''
\echo '═══════════════════════════════════════════════════════════════'
\echo '✅ DUMMY DATA POPULATION COMPLETE'
\echo '═══════════════════════════════════════════════════════════════'
\echo ''
\echo '📊 Data Summary:'
\echo '  • Admin Accounts: 2 (admin/admin123, superadmin/superadmin123)'
\echo '  • Test Users: 10 (varying risk levels)'
\echo '  • Transactions: 20 (15 normal, 5 fraudulent)'
\echo '  • Compliance Alerts: 12 (4 critical, 4 high, 4 medium/low)'
\echo '  • Audit Logs: 4 entries'
\echo ''
\echo '🔑 Login Credentials:'
\echo '  Admin: username=admin, password=admin123'
\echo '  Superadmin: username=superadmin, password=superadmin123'
\echo ''
\echo '⚠️  Important Notes:'
\echo '  • Users table uses: user_id (BIGINT), uin, username, blacklisted, current_rps_360, risk_category'
\echo '  • Transactions table uses: transaction_id (BIGINT), txn_type, is_fraud (INT 0/1)'
\echo '  • Compliance alerts do NOT have: is_true_positive, reviewed_at, reviewed_by'
\echo ''
\echo '🚀 Next Steps:'
\echo '  1. Restart backend server to reload models'
\echo '  2. Test API endpoints with new schema'
\echo '  3. Update frontend to use correct field names'
\echo ''
\echo '═══════════════════════════════════════════════════════════════'
