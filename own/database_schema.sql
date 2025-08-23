-- Database schema for Online Compiler with Google Authentication
-- MySQL Database Setup

-- Create database (run as root/admin user)
-- CREATE DATABASE online_compiler_db;
-- CREATE USER 'compiler_user'@'localhost' IDENTIFIED BY 'your_secure_password';
-- GRANT ALL PRIVILEGES ON online_compiler_db.* TO 'compiler_user'@'localhost';
-- FLUSH PRIVILEGES;

USE online_compiler_db;

-- Users table optimized for millions of concurrent users
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(32),

    -- Profile fields
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    profile_picture_url VARCHAR(500),

    -- Account status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    email_verified BOOLEAN DEFAULT FALSE,
    
    -- Security
    failed_login_attempts INT DEFAULT 0,
    account_locked_until DATETIME NULL,
    last_login DATETIME,
    last_password_change DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- User role
    user_role ENUM('standard_user', 'premium_user', 'admin') DEFAULT 'standard_user',
    timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
    
    -- Optimized indexes for millions of users
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_email_verified (email_verified),
    INDEX idx_is_active (is_active),
    INDEX idx_last_login (last_login),
    INDEX idx_created_at (created_at),
    INDEX idx_composite_login (username, password_hash, is_active),
    INDEX idx_composite_email (email, email_verified, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User sessions table optimized for high concurrency (sessions stored in Redis for better performance)
CREATE TABLE user_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    refresh_token_hash VARCHAR(255),
    device_info JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    location_info JSON,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at),
    INDEX idx_is_active (is_active),
    INDEX idx_composite_session (user_id, is_active, expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Code executions table optimized for high volume logging
CREATE TABLE code_executions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    session_id VARCHAR(255),
    language VARCHAR(50) NOT NULL,
    code_hash VARCHAR(64), -- SHA256 hash of code to detect duplicates
    code_snippet_compressed MEDIUMBLOB, -- Compressed code for storage efficiency
    output_compressed BLOB, -- Compressed output
    error_message TEXT,
    execution_time DECIMAL(10, 6),
    memory_used INT, -- Memory usage in KB
    cpu_time DECIMAL(10, 6), -- CPU time used
    status ENUM('success', 'error', 'timeout', 'memory_limit', 'time_limit') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_language (language),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_session_id (session_id),
    INDEX idx_composite_user_date (user_id, created_at),
    INDEX idx_composite_stats (user_id, language, status),
    
    -- Partitioning by month for better performance with large datasets
    PARTITION BY RANGE (YEAR(created_at) * 100 + MONTH(created_at)) (
        PARTITION p202401 VALUES LESS THAN (202402),
        PARTITION p202402 VALUES LESS THAN (202403),
        PARTITION p202403 VALUES LESS THAN (202404),
        PARTITION p_future VALUES LESS THAN MAXVALUE
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User preferences table to store user settings
CREATE TABLE user_preferences (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    default_language VARCHAR(50) DEFAULT 'python',
    theme VARCHAR(20) DEFAULT 'dark',
    font_size INT DEFAULT 14,
    auto_save BOOLEAN DEFAULT TRUE,
    notifications BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Saved code snippets table
CREATE TABLE saved_snippets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    language VARCHAR(50) NOT NULL,
    code TEXT NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    tags VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_language (language),
    INDEX idx_is_public (is_public),
    INDEX idx_created_at (created_at)
);

-- Questions table for coding problems
CREATE TABLE questions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    difficulty ENUM('easy', 'medium', 'hard') NOT NULL,
    category VARCHAR(100),
    tags VARCHAR(500),
    input_format TEXT,
    output_format TEXT,
    constraints TEXT,
    sample_input TEXT,
    sample_output TEXT,
    explanation TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_difficulty (difficulty),
    INDEX idx_category (category),
    INDEX idx_is_active (is_active)
);

-- User question attempts table
CREATE TABLE question_attempts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    question_id INT NOT NULL,
    language VARCHAR(50) NOT NULL,
    code TEXT NOT NULL,
    status ENUM('attempted', 'solved', 'partially_solved') NOT NULL,
    execution_time DECIMAL(10, 6),
    memory_used INT,
    test_cases_passed INT DEFAULT 0,
    total_test_cases INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_question_id (question_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Rate limiting table for API security
CREATE TABLE rate_limits (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    identifier VARCHAR(255) NOT NULL, -- IP address or user_id
    identifier_type ENUM('ip', 'user') NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    requests_count INT DEFAULT 0,
    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    blocked_until TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_rate_limit (identifier, endpoint),
    INDEX idx_identifier (identifier),
    INDEX idx_window_start (window_start),
    INDEX idx_blocked_until (blocked_until)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User activity logs for security monitoring
CREATE TABLE user_activity_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT,
    activity_type ENUM('login', 'logout', 'failed_login', 'password_change', 'email_change', 'account_locked', 'account_unlocked') NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    additional_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_activity_type (activity_type),
    INDEX idx_created_at (created_at),
    INDEX idx_ip_address (ip_address),
    
    -- Partitioning by month for performance
    PARTITION BY RANGE (YEAR(created_at) * 100 + MONTH(created_at)) (
        PARTITION p202401 VALUES LESS THAN (202402),
        PARTITION p202402 VALUES LESS THAN (202403),
        PARTITION p202403 VALUES LESS THAN (202404),
        PARTITION p_future VALUES LESS THAN MAXVALUE
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- System-wide statistics cache table
CREATE TABLE system_stats_cache (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stat_key VARCHAR(255) UNIQUE NOT NULL,
    stat_value BIGINT NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    
    INDEX idx_stat_key (stat_key),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert sample question
INSERT INTO questions (title, description, difficulty, category, tags, sample_input, sample_output, explanation) VALUES
(
    'Two Sum',
    'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target. You may assume that each input would have exactly one solution, and you may not use the same element twice.',
    'easy',
    'Array',
    'array,hash-table,two-pointers',
    'nums = [2,7,11,15], target = 9',
    '[0,1]',
    'Because nums[0] + nums[1] == 9, we return [0, 1].'
);

-- Insert initial system stats
INSERT INTO system_stats_cache (stat_key, stat_value) VALUES
('total_users', 0),
('active_users_today', 0),
('total_executions', 0),
('executions_today', 0);

-- Create indexes for performance
CREATE INDEX idx_users_last_login ON users(last_login);
CREATE INDEX idx_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_executions_user_created ON code_executions(user_id, created_at);
CREATE INDEX idx_snippets_user_updated ON saved_snippets(user_id, updated_at);
