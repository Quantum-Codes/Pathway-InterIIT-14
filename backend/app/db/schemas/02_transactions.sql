-- =============================================================================
-- TABLE: transactions
-- PURPOSE: Financial transaction records with fraud detection
-- =============================================================================

CREATE TABLE
IF NOT EXISTS transactions
(
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Keys
    user_id INTEGER NOT NULL,
    
    -- Transaction Details
    transaction_id VARCHAR
(100) UNIQUE NOT NULL,
    transaction_type VARCHAR
(50) NOT NULL,
    amount DECIMAL
(15, 2) NOT NULL,
    currency VARCHAR
(10) DEFAULT 'INR',
    
    -- Transaction Parties
    sender_account VARCHAR
(100),
    receiver_account VARCHAR
(100),
    sender_name VARCHAR
(255),
    receiver_name VARCHAR
(255),
    
    -- Risk Assessment
    suspicious_score FLOAT DEFAULT 0.0,
    risk_level VARCHAR
(20) DEFAULT 'low',
    is_flagged BOOLEAN DEFAULT 0,
    flag_reason TEXT,
    
    -- Transaction Status
    status VARCHAR
(20) DEFAULT 'pending',
    payment_method VARCHAR
(50),
    
    -- Location & Context
    ip_address VARCHAR
(45),
    device_id VARCHAR
(100),
    location TEXT,
    
    -- Metadata
    transaction_date DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY
(user_id) REFERENCES users
(id) ON
DELETE CASCADE,
    
    -- Check Constraints
    CHECK (transaction_type
IN
('deposit', 'withdrawal', 'transfer', 'payment', 'refund')),
    CHECK
(amount > 0),
    CHECK
(risk_level IN
('low', 'medium', 'high', 'critical')),
    CHECK
(status IN
('pending', 'completed', 'failed', 'cancelled', 'under_review')),
    CHECK
(suspicious_score BETWEEN 0 AND 1)
);

-- Indexes for Performance
CREATE INDEX
IF NOT EXISTS idx_transactions_user_id ON transactions
(user_id);
CREATE INDEX
IF NOT EXISTS idx_transactions_transaction_id ON transactions
(transaction_id);
CREATE INDEX
IF NOT EXISTS idx_transactions_date ON transactions
(transaction_date);
CREATE INDEX
IF NOT EXISTS idx_transactions_flagged ON transactions
(is_flagged);
CREATE INDEX
IF NOT EXISTS idx_transactions_status ON transactions
(status);
CREATE INDEX
IF NOT EXISTS idx_transactions_risk_level ON transactions
(risk_level);
CREATE INDEX
IF NOT EXISTS idx_transactions_type ON transactions
(transaction_type);

-- Composite Indexes for Dashboard Queries
CREATE INDEX
IF NOT EXISTS idx_transactions_user_date ON transactions
(user_id, transaction_date);
CREATE INDEX
IF NOT EXISTS idx_transactions_flagged_date ON transactions
(is_flagged, transaction_date);

-- Comments
-- transaction_id: Unique identifier (e.g., TXN-2024-123456)
-- suspicious_score: ML-based fraud detection score (0-1)
-- is_flagged: Quick filter for flagged transactions requiring review
