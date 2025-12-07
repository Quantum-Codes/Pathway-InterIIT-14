-- =============================================================================
-- TABLE: notification_settings
-- PURPOSE: User-specific notification preferences and alert configuration
-- =============================================================================

CREATE TABLE IF NOT EXISTS notification_settings (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Keys
    user_id INTEGER UNIQUE NOT NULL,
    
    -- Email Preferences
    enable_email BOOLEAN DEFAULT 1,
    email_frequency VARCHAR(20) DEFAULT 'immediate',
    
    -- SMS Preferences
    enable_sms BOOLEAN DEFAULT 0,
    sms_number VARCHAR(20),
    
    -- Push Notification Preferences
    enable_push BOOLEAN DEFAULT 1,
    device_tokens TEXT,  -- JSON array of device tokens
    
    -- Alert Type Preferences
    notify_kyc_alerts BOOLEAN DEFAULT 1,
    notify_transaction_alerts BOOLEAN DEFAULT 1,
    notify_fraud_alerts BOOLEAN DEFAULT 1,
    notify_aml_alerts BOOLEAN DEFAULT 1,
    notify_case_updates BOOLEAN DEFAULT 1,
    notify_hold_updates BOOLEAN DEFAULT 1,
    
    -- Severity Filters
    min_severity_level VARCHAR(20) DEFAULT 'medium',
    
    -- Quiet Hours
    quiet_hours_enabled BOOLEAN DEFAULT 0,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    quiet_hours_timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Digest Settings
    enable_daily_digest BOOLEAN DEFAULT 0,
    digest_time TIME DEFAULT '09:00:00',
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Check Constraints
    CHECK (email_frequency IN ('immediate', 'hourly', 'daily', 'weekly')),
    CHECK (min_severity_level IN ('low', 'medium', 'high', 'critical'))
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_notif_user_id ON notification_settings(user_id);

-- Comments
-- email_frequency: How often to batch email notifications
-- device_tokens: JSON array for push notification services (FCM, APNS)
-- min_severity_level: Only notify for alerts at or above this severity
-- quiet_hours: Suppress non-critical notifications during specified hours
