-- =============================================================================
-- DUMMY DATA POPULATION SCRIPT
-- =============================================================================

-- =============================================================================
-- USERS TABLE - Sample users with varied risk profiles
-- =============================================================================

INSERT INTO users
    (entity_id, applicant_name, email, phone, kyc_status, i_360_score, i_not_score, suspicious_score, risk_level, is_blacklisted, account_status, address, city, state, country, postal_code, date_of_birth, kyc_verified_at)
VALUES
    ('APP-2024-00001', 'Rajesh Kumar', 'rajesh.kumar@email.com', '+91-9876543210', 'approved', 25.5, 15.0, 20.0, 'low', FALSE, 'active', '123 MG Road', 'Mumbai', 'Maharashtra', 'India', '400001', '1985-03-15', NOW() - INTERVAL
'30 days'),
('APP-2024-00002', 'Priya Sharma', 'priya.sharma@email.com', '+91-9876543211', 'approved', 45.2, 38.0, 42.0, 'medium', FALSE, 'active', '456 Park Street', 'Kolkata', 'West Bengal', 'India', '700016', '1990-07-22', NOW
() - INTERVAL '45 days'),
('APP-2024-00003', 'Amit Patel', 'amit.patel@email.com', '+91-9876543212', 'pending', 75.8, 72.0, 78.5, 'high', FALSE, 'under_investigation', '789 Civil Lines', 'Ahmedabad', 'Gujarat', 'India', '380001', '1988-11-30', NULL),
('APP-2024-00004', 'Sneha Reddy', 'sneha.reddy@email.com', '+91-9876543213', 'approved', 18.0, 12.5, 15.0, 'low', FALSE, 'active', '321 Banjara Hills', 'Hyderabad', 'Telangana', 'India', '500034', '1992-05-18', NOW
() - INTERVAL '60 days'),
('APP-2024-00005', 'Vikram Singh', 'vikram.singh@email.com', '+91-9876543214', 'rejected', 92.3, 88.5, 95.0, 'critical', TRUE, 'suspended', '654 Connaught Place', 'New Delhi', 'Delhi', 'India', '110001', '1983-09-25', NULL),
('APP-2024-00006', 'Ananya Iyer', 'ananya.iyer@email.com', '+91-9876543215', 'approved', 32.1, 28.0, 30.0, 'low', FALSE, 'active', '987 Brigade Road', 'Bangalore', 'Karnataka', 'India', '560001', '1995-02-14', NOW
() - INTERVAL '20 days'),
('APP-2024-00007', 'Rahul Mehta', 'rahul.mehta@email.com', '+91-9876543216', 'under_review', 58.9, 55.0, 60.0, 'medium', FALSE, 'active', '147 FC Road', 'Pune', 'Maharashtra', 'India', '411004', '1987-12-08', NULL),
('APP-2024-00008', 'Divya Nair', 'divya.nair@email.com', '+91-9876543217', 'approved', 22.3, 18.5, 20.0, 'low', FALSE, 'active', '258 Marine Drive', 'Kochi', 'Kerala', 'India', '682011', '1993-06-30', NOW
() - INTERVAL '90 days'),
('APP-2024-00009', 'Karan Chopra', 'karan.chopra@email.com', '+91-9876543218', 'approved', 65.7, 62.0, 68.0, 'high', FALSE, 'active', '369 Mall Road', 'Chandigarh', 'Chandigarh', 'India', '160001', '1989-04-12', NOW
() - INTERVAL '15 days'),
('APP-2024-00010', 'Meera Joshi', 'meera.joshi@email.com', '+91-9876543219', 'approved', 28.5, 25.0, 27.0, 'low', FALSE, 'active', '741 Residency Road', 'Jaipur', 'Rajasthan', 'India', '302001', '1991-08-20', NOW
() - INTERVAL '50 days');

-- =============================================================================
-- TRANSACTIONS TABLE - Sample transactions with varied risk levels
-- =============================================================================

INSERT INTO transactions
    (user_id, transaction_id, transaction_type, amount, currency, sender_account, receiver_account, sender_name, receiver_name, suspicious_score, risk_level, is_flagged, status, payment_method, ip_address, device_id, location, transaction_date)
VALUES
    (1, 'TXN-2024-10001', 'deposit', 50000.00, 'INR', 'ACC-100001', 'ACC-100002', 'Rajesh Kumar', 'Merchant Account', 15.0, 'low', FALSE, 'completed', 'UPI', '192.168.1.1', 'DEV-001', 'Mumbai, Maharashtra', NOW() - INTERVAL
'5 days'),
(1, 'TXN-2024-10002', 'withdrawal', 25000.00, 'INR', 'ACC-100002', 'ACC-100001', 'Rajesh Kumar', 'Bank Account', 20.0, 'low', FALSE, 'completed', 'Bank Transfer', '192.168.1.1', 'DEV-001', 'Mumbai, Maharashtra', NOW
() - INTERVAL '3 days'),
(2, 'TXN-2024-10003', 'transfer', 150000.00, 'INR', 'ACC-100003', 'ACC-200001', 'Priya Sharma', 'Business Partner', 48.5, 'medium', TRUE, 'completed', 'NEFT', '192.168.2.10', 'DEV-002', 'Kolkata, West Bengal', NOW
() - INTERVAL '7 days'),
(2, 'TXN-2024-10004', 'payment', 75000.00, 'INR', 'ACC-100003', 'MERCHANT-001', 'Priya Sharma', 'Online Merchant', 42.0, 'medium', FALSE, 'completed', 'Credit Card', '192.168.2.10', 'DEV-002', 'Kolkata, West Bengal', NOW
() - INTERVAL '2 days'),
(3, 'TXN-2024-10005', 'deposit', 500000.00, 'INR', 'ACC-UNKNOWN', 'ACC-100004', 'Unknown Source', 'Amit Patel', 85.0, 'high', TRUE, 'under_review', 'Cash Deposit', '10.0.0.5', 'DEV-003', 'Ahmedabad, Gujarat', NOW
() - INTERVAL '1 day'),
(3, 'TXN-2024-10006', 'withdrawal', 450000.00, 'INR', 'ACC-100004', 'ACC-OFFSHORE', 'Amit Patel', 'Offshore Account', 92.0, 'critical', TRUE, 'pending', 'Wire Transfer', '10.0.0.5', 'DEV-003', 'Ahmedabad, Gujarat', NOW
() - INTERVAL '6 hours'),
(4, 'TXN-2024-10007', 'payment', 35000.00, 'INR', 'ACC-100005', 'MERCHANT-002', 'Sneha Reddy', 'E-commerce Store', 18.0, 'low', FALSE, 'completed', 'Debit Card', '192.168.3.15', 'DEV-004', 'Hyderabad, Telangana', NOW
() - INTERVAL '8 days'),
(5, 'TXN-2024-10008', 'transfer', 1000000.00, 'INR', 'ACC-100006', 'ACC-SUSPICIOUS', 'Vikram Singh', 'Shell Company', 98.5, 'critical', TRUE, 'cancelled', 'RTGS', '203.0.113.42', 'DEV-005', 'New Delhi, Delhi', NOW
() - INTERVAL '10 days'),
(6, 'TXN-2024-10009', 'deposit', 80000.00, 'INR', 'SALARY-ACC', 'ACC-100007', 'Employer', 'Ananya Iyer', 12.0, 'low', FALSE, 'completed', 'Direct Deposit', '192.168.4.20', 'DEV-006', 'Bangalore, Karnataka', NOW
() - INTERVAL '4 days'),
(6, 'TXN-2024-10010', 'payment', 45000.00, 'INR', 'ACC-100007', 'UTILITY-001', 'Ananya Iyer', 'Utility Bills', 15.0, 'low', FALSE, 'completed', 'Auto Debit', '192.168.4.20', 'DEV-006', 'Bangalore, Karnataka', NOW
() - INTERVAL '1 day'),
(7, 'TXN-2024-10011', 'transfer', 200000.00, 'INR', 'ACC-100008', 'ACC-RELATIVE', 'Rahul Mehta', 'Family Member', 55.0, 'medium', TRUE, 'completed', 'IMPS', '192.168.5.25', 'DEV-007', 'Pune, Maharashtra', NOW
() - INTERVAL '9 days'),
(8, 'TXN-2024-10012', 'withdrawal', 60000.00, 'INR', 'ACC-100009', 'ATM-001', 'Divya Nair', 'ATM Withdrawal', 22.0, 'low', FALSE, 'completed', 'ATM', '192.168.6.30', 'DEV-008', 'Kochi, Kerala', NOW
() - INTERVAL '6 days'),
(9, 'TXN-2024-10013', 'deposit', 350000.00, 'INR', 'INVESTMENT-ACC', 'ACC-100010', 'Investment Firm', 'Karan Chopra', 68.0, 'high', TRUE, 'completed', 'Wire Transfer', '192.168.7.35', 'DEV-009', 'Chandigarh, Chandigarh', NOW
() - INTERVAL '12 days'),
(10, 'TXN-2024-10014', 'payment', 25000.00, 'INR', 'ACC-100011', 'MERCHANT-003', 'Meera Joshi', 'Local Shop', 25.0, 'low', FALSE, 'completed', 'Cash', '192.168.8.40', 'DEV-010', 'Jaipur, Rajasthan', NOW
() - INTERVAL '2 days');

-- =============================================================================
-- COMPLIANCE ALERTS TABLE - Sample alerts for various scenarios
-- =============================================================================

INSERT INTO compliance_alerts
    (user_id, transaction_id, alert_type, severity, title, description, entity_id, entity_type, rps360, status, priority, source, triggered_by, alert_metadata, triggered_at)
VALUES
    (3, 5, 'transaction_alert', 'high', 'Large Cash Deposit Detected', 'Cash deposit of ₹500,000 from unknown source', 'APP-2024-00003', 'user', 85.0, 'active', 'high', 'Transaction Monitoring System', 'Auto-Detection', '{"amount": 500000, "method": "cash", "threshold_exceeded": true}', NOW() - INTERVAL
'1 day'),
(3, 6, 'fraud_alert', 'critical', 'Suspicious Offshore Transfer', 'Attempt to transfer large amount to offshore account', 'APP-2024-00003', 'user', 92.0, 'investigating', 'critical', 'Fraud Detection AI', 'ML Model', '{"destination": "offshore", "risk_score": 92}', NOW
() - INTERVAL '6 hours'),
(5, 8, 'aml_alert', 'critical', 'Potential Money Laundering Activity', 'Transfer to known shell company flagged', 'APP-2024-00005', 'user', 98.5, 'escalated', 'critical', 'AML Screening', 'Compliance Team', '{"matched_entity": "shell_company", "confidence": 0.98}', NOW
() - INTERVAL '10 days'),
(2, 3, 'transaction_alert', 'medium', 'High Value Transaction', 'Transfer of ₹150,000 exceeds normal pattern', 'APP-2024-00002', 'user', 48.5, 'resolved', 'medium', 'Behavioral Analysis', 'Auto-Detection', '{"amount": 150000, "avg_transaction": 45000}', NOW
() - INTERVAL '7 days'),
(7, 11, 'behavioral_alert', 'medium', 'Unusual Transaction Pattern', 'Large transfer to new recipient', 'APP-2024-00007', 'user', 55.0, 'active', 'medium', 'Pattern Recognition', 'ML Model', '{"new_recipient": true, "amount_deviation": 2.5}', NOW
() - INTERVAL '9 days'),
(9, 13, 'kyc_alert', 'high', 'KYC Verification Required', 'Large investment deposit requires enhanced due diligence', 'APP-2024-00009', 'user', 68.0, 'active', 'high', 'KYC System', 'Compliance Officer', '{"enhanced_dd_required": true}', NOW
() - INTERVAL '12 days'),
(1, NULL, 'system_alert', 'low', 'Password Reset Request', 'User requested password reset', 'APP-2024-00001', 'user', 15.0, 'resolved', 'low', 'Security System', 'User Action', '{"ip": "192.168.1.1"}', NOW
() - INTERVAL '14 days'),
(4, NULL, 'kyc_alert', 'medium', 'Document Expiry Reminder', 'KYC document expires in 30 days', 'APP-2024-00004', 'user', 18.0, 'active', 'low', 'KYC System', 'Scheduled Task', '{"expiry_date": "2025-01-15"}', NOW
() - INTERVAL '5 days'),
(6, NULL, 'sanction_alert', 'low', 'Routine Sanction Screening', 'Periodic sanction list check completed', 'APP-2024-00006', 'user', 12.0, 'resolved', 'low', 'Sanction Screening', 'Scheduled Task', '{"matches_found": 0}', NOW
() - INTERVAL '3 days'),
(8, NULL, 'transaction_alert', 'low', 'ATM Withdrawal Limit Warning', 'Approaching daily ATM withdrawal limit', 'APP-2024-00008', 'user', 22.0, 'dismissed', 'low', 'Transaction System', 'Auto-Detection', '{"limit": 100000, "used": 60000}', NOW
() - INTERVAL '6 days');

-- =============================================================================
-- INVESTIGATION CASES TABLE - Sample investigation cases
-- =============================================================================

INSERT INTO investigation_cases
    (id, user_id, case_title, case_description, case_type, severity, status, priority, assigned_to, created_by, transaction_ids, alert_ids, investigation_notes, created_at, due_date)
VALUES
    ('CASE-2024-00001', 3, 'High-Risk Transaction Investigation', 'Investigating large cash deposits and offshore transfer attempts', 'fraud', 'critical', 'investigating', 'critical', 'investigator@example.com', 'system@example.com', '["TXN-2024-10005", "TXN-2024-10006"]', '["1", "2"]', 'User has history of suspicious activities. Awaiting bank statements.', NOW() - INTERVAL
'1 day', NOW
() + INTERVAL '7 days'),
('CASE-2024-00002', 5, 'AML Compliance Investigation', 'Potential money laundering through shell company', 'aml', 'critical', 'escalated', 'critical', 'senior-investigator@example.com', 'compliance@example.com', '["TXN-2024-10008"]', '["3"]', 'Case escalated to legal team. Evidence collected and documented.', NOW
() - INTERVAL '10 days', NOW
() + INTERVAL '3 days'),
('CASE-2024-00003', 2, 'Transaction Pattern Analysis', 'Review of high-value transaction patterns', 'behavioral', 'medium', 'closed', 'medium', 'analyst@example.com', 'system@example.com', '["TXN-2024-10003"]', '["4"]', 'Verified as legitimate business transaction. Case closed.', NOW
() - INTERVAL '7 days', NOW
() - INTERVAL '2 days'),
('CASE-2024-00004', 7, 'Unusual Activity Review', 'Large transfer to new recipient requires verification', 'behavioral', 'medium', 'pending_review', 'medium', 'reviewer@example.com', 'system@example.com', '["TXN-2024-10011"]', '["5"]', 'User provided documentation. Under final review.', NOW
() - INTERVAL '9 days', NOW
() + INTERVAL '5 days'),
('CASE-2024-00005', 9, 'Enhanced Due Diligence', 'KYC verification for high-value investment', 'kyc', 'high', 'open', 'high', 'kyc-officer@example.com', 'compliance@example.com', '["TXN-2024-10013"]', '["6"]', 'Requested additional documentation from user.', NOW
() - INTERVAL '12 days', NOW
() + INTERVAL '10 days');

-- =============================================================================
-- ACCOUNT HOLDS TABLE - Sample account restrictions
-- =============================================================================

INSERT INTO account_holds
    (id, user_id, case_id, hold_type, hold_reason, severity, status, hold_placed_at, hold_expires_at, restrictions, placed_by, approved_by, notification_sent)
VALUES
    ('HOLD-2024-00001', 3, 'CASE-2024-00001', 'investigation', 'Account frozen pending fraud investigation', 'critical', 'active', NOW() - INTERVAL
'1 day', NOW
() + INTERVAL '30 days', '["withdrawals", "transfers", "new_transactions"]', 'investigator@example.com', 'manager@example.com', TRUE),
('HOLD-2024-00002', 5, 'CASE-2024-00002', 'permanent', 'Account suspended due to AML violations', 'critical', 'active', NOW
() - INTERVAL '10 days', NULL, '["all_transactions", "account_access"]', 'compliance@example.com', 'legal@example.com', TRUE),
('HOLD-2024-00003', 7, 'CASE-2024-00004', 'temporary', 'Temporary hold for verification', 'medium', 'active', NOW
() - INTERVAL '9 days', NOW
() + INTERVAL '14 days', '["large_transactions"]', 'reviewer@example.com', 'supervisor@example.com', TRUE),
('HOLD-2024-00004', 2, 'CASE-2024-00003', 'temporary', 'Precautionary hold during investigation', 'medium', 'released', NOW
() - INTERVAL '7 days', NOW
() + INTERVAL '7 days', '["transfers"]', 'analyst@example.com', 'manager@example.com', TRUE);

-- =============================================================================
-- NOTIFICATION SETTINGS TABLE - Sample notification preferences
-- =============================================================================

INSERT INTO notification_settings
    (user_id, enable_email, email_frequency, enable_sms, enable_push, notify_kyc_alerts, notify_transaction_alerts, notify_fraud_alerts, notify_aml_alerts, notify_case_updates, notify_hold_updates, min_severity_level)
VALUES
    (1, TRUE, 'immediate', FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, 'medium'),
    (2, TRUE, 'daily', FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, 'low'),
    (3, TRUE, 'immediate', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, 'low'),
    (4, TRUE, 'immediate', FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, 'medium'),
    (5, FALSE, 'immediate', FALSE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, 'critical'),
    (6, TRUE, 'hourly', FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, 'medium'),
    (7, TRUE, 'immediate', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, 'low'),
    (8, TRUE, 'daily', FALSE, TRUE, TRUE, FALSE, TRUE, TRUE, TRUE, TRUE, 'high'),
    (9, TRUE, 'immediate', FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, 'medium'),
    (10, TRUE, 'weekly', FALSE, FALSE, TRUE, TRUE, TRUE, TRUE, FALSE, FALSE, 'high');

-- =============================================================================
-- VERIFICATION - Count records in each table
-- =============================================================================

    SELECT 'Users' as table_name, COUNT(*) as record_count
    FROM users
UNION ALL
    SELECT 'Transactions', COUNT(*)
    FROM transactions
UNION ALL
    SELECT 'Compliance Alerts', COUNT(*)
    FROM compliance_alerts
UNION ALL
    SELECT 'Investigation Cases', COUNT(*)
    FROM investigation_cases
UNION ALL
    SELECT 'Account Holds', COUNT(*)
    FROM account_holds
UNION ALL
    SELECT 'Notification Settings', COUNT(*)
    FROM notification_settings
UNION ALL
    SELECT 'Organization Settings', COUNT(*)
    FROM organization_settings;
