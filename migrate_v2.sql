-- Tenant Management System Database Migration v2.0
-- This script migrates from v1.0 to v2.0 (adds multi-client support and rent breakdown)
-- MySQL 5.7+ / MySQL 8.0+
--
-- IMPORTANT: Backup your database before running this migration!
-- Run: mysqldump -u root -p tenant_management > tenant_management_backup.sql

USE tenant_management;

-- ============================================
-- STEP 1: Create Clients Table
-- ============================================
CREATE TABLE IF NOT EXISTS clients (
    client_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    role VARCHAR(20) NOT NULL DEFAULT 'client',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- STEP 2: Create a default admin client
-- Password: 'admin123' (bcrypt hashed)
-- CHANGE THIS PASSWORD IMMEDIATELY after first login!
-- ============================================
INSERT INTO clients (username, password_hash, name, email, role, is_active)
VALUES (
    'admin',
    '$2b$12$K9LjVDqqvdYAe.A7ugcsreYNrtIb3aR8zjuT62bkpc1gI9DWw/7du',
    'System Administrator',
    'admin@example.com',
    'admin',
    TRUE
) ON DUPLICATE KEY UPDATE name = name;

-- ============================================
-- STEP 3: Add client_id column to owners table
-- ============================================
-- First, check if column exists
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'owners'
    AND COLUMN_NAME = 'client_id');

-- Add client_id column if it doesn't exist
SET @add_col = IF(@col_exists = 0,
    'ALTER TABLE owners ADD COLUMN client_id INT NOT NULL DEFAULT 1 AFTER owner_id',
    'SELECT "client_id column already exists"');
PREPARE stmt FROM @add_col;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add foreign key constraint (if not exists)
SET @fk_exists = (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'owners'
    AND CONSTRAINT_NAME = 'fk_owners_client');

SET @add_fk = IF(@fk_exists = 0,
    'ALTER TABLE owners ADD CONSTRAINT fk_owners_client FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE',
    'SELECT "foreign key already exists"');
PREPARE stmt FROM @add_fk;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add index on client_id
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'owners'
    AND INDEX_NAME = 'idx_client_id');

SET @add_idx = IF(@idx_exists = 0,
    'ALTER TABLE owners ADD INDEX idx_client_id (client_id)',
    'SELECT "index already exists"');
PREPARE stmt FROM @add_idx;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ============================================
-- STEP 4: Add new rent breakdown columns to tenants table
-- ============================================
-- Add water_charge column
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tenants'
    AND COLUMN_NAME = 'water_charge');

SET @add_col = IF(@col_exists = 0,
    'ALTER TABLE tenants ADD COLUMN water_charge DECIMAL(10, 2) NOT NULL DEFAULT 0 AFTER rent_amount',
    'SELECT "water_charge column already exists"');
PREPARE stmt FROM @add_col;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add maintenance_charge column
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tenants'
    AND COLUMN_NAME = 'maintenance_charge');

SET @add_col = IF(@col_exists = 0,
    'ALTER TABLE tenants ADD COLUMN maintenance_charge DECIMAL(10, 2) NOT NULL DEFAULT 0 AFTER water_charge',
    'SELECT "maintenance_charge column already exists"');
PREPARE stmt FROM @add_col;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add advance_amount column
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tenants'
    AND COLUMN_NAME = 'advance_amount');

SET @add_col = IF(@col_exists = 0,
    'ALTER TABLE tenants ADD COLUMN advance_amount DECIMAL(10, 2) NOT NULL DEFAULT 0 AFTER maintenance_charge',
    'SELECT "advance_amount column already exists"');
PREPARE stmt FROM @add_col;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ============================================
-- STEP 5: Update existing owners to belong to admin client
-- ============================================
UPDATE owners SET client_id = 1 WHERE client_id = 0 OR client_id IS NULL;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================
-- Check the new table structure
SELECT 'Clients table created:' AS status;
DESCRIBE clients;

SELECT 'Owners table updated:' AS status;
DESCRIBE owners;

SELECT 'Tenants table updated:' AS status;
DESCRIBE tenants;

-- Show default admin account
SELECT 'Default admin account:' AS status;
SELECT client_id, username, name, role, is_active FROM clients WHERE role = 'admin';

-- ============================================
-- NOTES:
-- ============================================
-- 1. Default admin password is 'admin123' - CHANGE IT IMMEDIATELY!
-- 2. All existing owners have been assigned to the admin client (client_id = 1)
-- 3. To create new clients, use the API endpoint or admin UI
-- 4. The rent_amount field now represents BASE rent only
-- 5. Total rent = rent_amount + water_charge + maintenance_charge
-- 6. advance_amount tracks the security deposit/advance paid

SELECT 'Migration completed successfully!' AS result;
