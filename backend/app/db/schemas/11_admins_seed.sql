-- Create default admin accounts (passwords are 'admin123' and 'superadmin123' hashed with bcrypt)
-- Note: In production, change these passwords immediately!

-- Insert a default superadmin (username: superadmin, password: superadmin123)
INSERT INTO admins
    (username, email, hashed_password, role, is_active)
VALUES
    (
        'superadmin',
        'superadmin@company.com',
        '$2b$12$5b0Jm4D9LgqXxv4SmEGDQOFqlGiJ1Y8YsJDErG6QLgm9XSH72Q7NW', -- superadmin123
        'SUPERADMIN',
        TRUE
)
ON CONFLICT
(username) DO NOTHING;

-- Insert a default admin (username: admin, password: admin123)
INSERT INTO admins
    (username, email, hashed_password, role, is_active)
VALUES
    (
        'admin',
        'admin@company.com',
        '$2b$12$spgE.7sEyp7Ei9au7fwdMuz13my.a2NT96XeGXdkuuFeyE7NXequK', -- admin123
        'ADMIN',
        TRUE
)
ON CONFLICT
(username) DO NOTHING;
