-- =============================================================================
-- MIGRATION: Add Alert Classification Fields
-- PURPOSE: Allow admins to mark alerts as true positive or false positive
-- =============================================================================

-- Add is_true_positive column (TRUE = positive, FALSE = negative/false positive, NULL = not reviewed)
ALTER TABLE compliance_alerts 
ADD COLUMN
IF NOT EXISTS is_true_positive BOOLEAN;

-- Add reviewed_at column (timestamp when alert was classified)
ALTER TABLE compliance_alerts 
ADD COLUMN
IF NOT EXISTS reviewed_at TIMESTAMP;

-- Add reviewed_by column (admin who classified the alert)
ALTER TABLE compliance_alerts 
ADD COLUMN
IF NOT EXISTS reviewed_by VARCHAR
(100);

-- Add index for querying by classification status
CREATE INDEX
IF NOT EXISTS idx_alerts_is_true_positive 
ON compliance_alerts
(is_true_positive);

-- Add index for querying reviewed alerts
CREATE INDEX
IF NOT EXISTS idx_alerts_reviewed_at 
ON compliance_alerts
(reviewed_at);

-- Add comments to document the columns
COMMENT ON COLUMN compliance_alerts.is_true_positive IS 'Alert classification: TRUE = true positive, FALSE = false positive, NULL = not reviewed';
COMMENT ON COLUMN compliance_alerts.reviewed_at IS 'Timestamp when alert was classified by admin';
COMMENT ON COLUMN compliance_alerts.reviewed_by IS 'Username of admin who classified the alert';
