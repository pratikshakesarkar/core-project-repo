-- ============================================================
--  AI Study Buddy  –  Database Schema
--  MySQL 8+  |  DB: study_buddy
-- ============================================================

CREATE DATABASE IF NOT EXISTS study_buddy;
USE study_buddy;

-- Users (admin + regular users) ----------------------------
CREATE TABLE IF NOT EXISTS users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(80)  NOT NULL,
    email      VARCHAR(120) NOT NULL UNIQUE,
    password   VARCHAR(64)  NOT NULL,          -- SHA-256 hex
    role       ENUM('admin','user') DEFAULT 'user',
    is_active  TINYINT(1)   DEFAULT 1,
    created_at DATETIME     DEFAULT CURRENT_TIMESTAMP
);

-- Notes ----------------------------------------------------
CREATE TABLE IF NOT EXISTS notes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    topic       VARCHAR(200) NOT NULL,
    raw_content TEXT         NOT NULL,
    summary     TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Quizzes --------------------------------------------------
CREATE TABLE IF NOT EXISTS quizzes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    topic       VARCHAR(200) NOT NULL,
    difficulty  ENUM('easy','medium','hard') DEFAULT 'medium',
    questions   JSON         NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Quiz Sessions (attempts) ---------------------------------
CREATE TABLE IF NOT EXISTS quiz_sessions (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id  INT  NOT NULL,
    quiz_id  INT  NOT NULL,
    score    INT  NOT NULL DEFAULT 0,
    answers  JSON,
    taken_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

-- ── Seed: default admin account ──────────────────────────────
--   email: admin@studybuddy.com  |  password: Admin@123
INSERT IGNORE INTO users (username, email, password, role) VALUES
('Admin', 'admin@studybuddy.com',
 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3',
 'admin');
-- SHA-256 of "Admin@123"  →  change immediately in production!
