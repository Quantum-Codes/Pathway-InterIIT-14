-- Create admins table
CREATE TABLE
IF NOT EXISTS admins
(
    id SERIAL PRIMARY KEY,
    username VARCHAR
(100) UNIQUE NOT NULL,
    email VARCHAR
(255) UNIQUE NOT NULL,
    hashed_password VARCHAR
(255) NOT NULL,
    role VARCHAR
(20) NOT NULL DEFAULT 'ADMIN' CHECK
(role IN
('ADMIN', 'SUPERADMIN')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP
WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
WITH TIME ZONE
);

-- Create indexes for admins
CREATE INDEX idx_admins_username ON admins(username);
CREATE INDEX idx_admins_email ON admins(email);
CREATE INDEX idx_admins_role ON admins(role);

-- Create audit_logs table
CREATE TABLE
IF NOT EXISTS audit_logs
(
    id SERIAL PRIMARY KEY,
    admin_id INTEGER NOT NULL REFERENCES admins
(id) ON
DELETE CASCADE,
    action_type VARCHAR(50)
NOT NULL,
    action_description TEXT NOT NULL,
    target_type VARCHAR
(50),
    target_id INTEGER,
    target_identifier VARCHAR
(255),
    action_metadata JSONB,
    ip_address VARCHAR
(50),
    user_agent TEXT,
    created_at TIMESTAMP
WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for audit_logs
CREATE INDEX idx_audit_logs_admin_id ON audit_logs(admin_id);
CREATE INDEX idx_audit_logs_action_type ON audit_logs(action_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_target_type ON audit_logs(target_type);
CREATE INDEX idx_audit_logs_target_id ON audit_logs(target_id);

-- Create trigger to update updated_at timestamp for admins
CREATE OR REPLACE FUNCTION update_updated_at_column
()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_admins_updated_at BEFORE
UPDATE ON admins
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column
();
