-- ============================================================
-- HotelOS Customer Module -- Migration v1
-- Database: hotel (existing)
-- MySQL: 8.0+
-- Run: mysql -u root -p hotel < customer_migration.sql
-- ============================================================

-- 1. Create customer_users table (never stores plain-text passwords)
CREATE TABLE IF NOT EXISTS customer_users (
    id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(150) NOT NULL UNIQUE,
    phone      VARCHAR(20)  DEFAULT NULL,
    address    TEXT         DEFAULT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status     ENUM('active','inactive') NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_customer_email (email)
);

-- 2. Add nullable customer_user_id to guest table
ALTER TABLE guest
    ADD COLUMN IF NOT EXISTS customer_user_id INT UNSIGNED NULL DEFAULT NULL;

-- 3. Same column on permanent_guest for history queries
ALTER TABLE permanent_guest
    ADD COLUMN IF NOT EXISTS customer_user_id INT UNSIGNED NULL DEFAULT NULL;

-- Verify
SELECT 'customer_users created'        AS result;
SELECT 'guest column added'            AS result;
SELECT 'permanent_guest column added'  AS result;
