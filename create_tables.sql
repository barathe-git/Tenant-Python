-- Tenant Management System Database Schema
-- MySQL 5.7+ / MySQL 8.0+

CREATE DATABASE IF NOT EXISTS tenant_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE tenant_management;

-- Owners Table
CREATE TABLE IF NOT EXISTS owners (
    owner_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255) NOT NULL,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Buildings Table
CREATE TABLE IF NOT EXISTS buildings (
    building_id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT NOT NULL,
    building_name VARCHAR(255) NOT NULL,
    building_type ENUM('Residence', 'Commercial') NOT NULL DEFAULT 'Residence',
    number_of_portions INT NOT NULL DEFAULT 1,
    location VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES owners(owner_id) ON DELETE CASCADE,
    INDEX idx_owner_id (owner_id),
    INDEX idx_building_type (building_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tenants Table
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    portion_number VARCHAR(50) NOT NULL,
    rent_amount DECIMAL(10, 2) NOT NULL,
    agreement_start_date DATE NOT NULL,
    agreement_end_date DATE NOT NULL,
    building_id INT NOT NULL,
    owner_id INT NOT NULL,
    agreement_pdf_path VARCHAR(500),
    aadhar_number VARCHAR(12),
    aadhar_pdf_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (building_id) REFERENCES buildings(building_id) ON DELETE CASCADE,
    FOREIGN KEY (owner_id) REFERENCES owners(owner_id) ON DELETE CASCADE,
    INDEX idx_building_id (building_id),
    INDEX idx_owner_id (owner_id),
    INDEX idx_agreement_end_date (agreement_end_date),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Alerts Table (for expiring agreements)
CREATE TABLE IF NOT EXISTS alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    tenant_name VARCHAR(255) NOT NULL,
    building_name VARCHAR(255) NOT NULL,
    agreement_end_date DATE NOT NULL,
    days_remaining INT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_is_read (is_read),
    INDEX idx_agreement_end_date (agreement_end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

