-- =====================================================
-- 用户认证系统数据库迁移
-- 执行时间: 2026-03-20
-- 说明: 添加用户表，所有数据表添加 user_id 字段
-- =====================================================

-- 1. 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    email VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    is_admin BOOLEAN DEFAULT FALSE COMMENT '是否管理员',
    last_login DATETIME COMMENT '最后登录时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户账户表';

-- 2. 为所有数据表添加 user_id 字段
-- 使用存储过程安全添加列

DELIMITER //

-- 添加 user_id 到 accounts 表
DROP PROCEDURE IF EXISTS add_user_id_to_accounts //
CREATE PROCEDURE add_user_id_to_accounts()
BEGIN
    DECLARE col_exists INT DEFAULT 0;
    SELECT COUNT(*) INTO col_exists FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'accounts' AND COLUMN_NAME = 'user_id';
    IF col_exists = 0 THEN
        ALTER TABLE accounts ADD COLUMN user_id INT COMMENT '用户ID' AFTER id;
    END IF;
END //

CALL add_user_id_to_accounts() //

-- 添加 user_id 到 positions 表
DROP PROCEDURE IF EXISTS add_user_id_to_positions //
CREATE PROCEDURE add_user_id_to_positions()
BEGIN
    DECLARE col_exists INT DEFAULT 0;
    SELECT COUNT(*) INTO col_exists FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'positions' AND COLUMN_NAME = 'user_id';
    IF col_exists = 0 THEN
        ALTER TABLE positions ADD COLUMN user_id INT COMMENT '用户ID' AFTER id;
    END IF;
END //

CALL add_user_id_to_positions() //

-- 添加 user_id 到 trades 表
DROP PROCEDURE IF EXISTS add_user_id_to_trades //
CREATE PROCEDURE add_user_id_to_trades()
BEGIN
    DECLARE col_exists INT DEFAULT 0;
    SELECT COUNT(*) INTO col_exists FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trades' AND COLUMN_NAME = 'user_id';
    IF col_exists = 0 THEN
        ALTER TABLE trades ADD COLUMN user_id INT COMMENT '用户ID' AFTER id;
    END IF;
END //

CALL add_user_id_to_trades() //

-- 添加 user_id 到 valuations 表
DROP PROCEDURE IF EXISTS add_user_id_to_valuations //
CREATE PROCEDURE add_user_id_to_valuations()
BEGIN
    DECLARE col_exists INT DEFAULT 0;
    SELECT COUNT(*) INTO col_exists FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'valuations' AND COLUMN_NAME = 'user_id';
    IF col_exists = 0 THEN
        ALTER TABLE valuations ADD COLUMN user_id INT COMMENT '用户ID' AFTER id;
    END IF;
END //

CALL add_user_id_to_valuations() //

-- 添加 user_id 到 cash_pool 表
DROP PROCEDURE IF EXISTS add_user_id_to_cash_pool //
CREATE PROCEDURE add_user_id_to_cash_pool()
BEGIN
    DECLARE col_exists INT DEFAULT 0;
    SELECT COUNT(*) INTO col_exists FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'cash_pool' AND COLUMN_NAME = 'user_id';
    IF col_exists = 0 THEN
        ALTER TABLE cash_pool ADD COLUMN user_id INT COMMENT '用户ID' AFTER id;
    END IF;
END //

CALL add_user_id_to_cash_pool() //

-- 添加 user_id 到 portfolio_snapshots 表
DROP PROCEDURE IF EXISTS add_user_id_to_snapshots //
CREATE PROCEDURE add_user_id_to_snapshots()
BEGIN
    DECLARE col_exists INT DEFAULT 0;
    SELECT COUNT(*) INTO col_exists FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'portfolio_snapshots' AND COLUMN_NAME = 'user_id';
    IF col_exists = 0 THEN
        ALTER TABLE portfolio_snapshots ADD COLUMN user_id INT COMMENT '用户ID' AFTER id;
    END IF;
END //

CALL add_user_id_to_snapshots() //

-- 添加 user_id 到 configs 表
DROP PROCEDURE IF EXISTS add_user_id_to_configs //
CREATE PROCEDURE add_user_id_to_configs()
BEGIN
    DECLARE col_exists INT DEFAULT 0;
    SELECT COUNT(*) INTO col_exists FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'configs' AND COLUMN_NAME = 'user_id';
    IF col_exists = 0 THEN
        ALTER TABLE configs ADD COLUMN user_id INT COMMENT '用户ID (NULL表示系统配置)' AFTER id;
    END IF;
END //

CALL add_user_id_to_configs() //

DELIMITER ;

-- 3. 删除现有持仓数据（用户要求，便于分用户管理）
DELETE FROM portfolio_snapshots WHERE 1=1;
DELETE FROM trades WHERE 1=1;
DELETE FROM positions WHERE 1=1;
DELETE FROM accounts WHERE 1=1;

-- 4. 创建索引（使用存储过程安全创建）
DELIMITER //

DROP PROCEDURE IF EXISTS create_user_indexes //
CREATE PROCEDURE create_user_indexes()
BEGIN
    -- accounts 索引
    IF NOT EXISTS (SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'accounts' AND INDEX_NAME = 'idx_accounts_user') THEN
        CREATE INDEX idx_accounts_user ON accounts(user_id);
    END IF;
    -- positions 索引
    IF NOT EXISTS (SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'positions' AND INDEX_NAME = 'idx_positions_user') THEN
        CREATE INDEX idx_positions_user ON positions(user_id);
    END IF;
    -- trades 索引
    IF NOT EXISTS (SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trades' AND INDEX_NAME = 'idx_trades_user') THEN
        CREATE INDEX idx_trades_user ON trades(user_id);
    END IF;
    -- valuations 索引
    IF NOT EXISTS (SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'valuations' AND INDEX_NAME = 'idx_valuations_user') THEN
        CREATE INDEX idx_valuations_user ON valuations(user_id);
    END IF;
    -- cash_pool 索引
    IF NOT EXISTS (SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'cash_pool' AND INDEX_NAME = 'idx_cash_pool_user') THEN
        CREATE INDEX idx_cash_pool_user ON cash_pool(user_id);
    END IF;
    -- portfolio_snapshots 索引
    IF NOT EXISTS (SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'portfolio_snapshots' AND INDEX_NAME = 'idx_snapshots_user') THEN
        CREATE INDEX idx_snapshots_user ON portfolio_snapshots(user_id);
    END IF;
END //

CALL create_user_indexes() //

DELIMITER ;

-- 5. 添加外键约束（可选，如果需要严格引用完整性）
-- 注意：添加外键前请确保 user_id 字段已填充有效值
-- ALTER TABLE accounts ADD CONSTRAINT fk_accounts_user FOREIGN KEY (user_id) REFERENCES users(id);
-- ALTER TABLE positions ADD CONSTRAINT fk_positions_user FOREIGN KEY (user_id) REFERENCES users(id);
-- ALTER TABLE trades ADD CONSTRAINT fk_trades_user FOREIGN KEY (user_id) REFERENCES users(id);
-- ALTER TABLE valuations ADD CONSTRAINT fk_valuations_user FOREIGN KEY (user_id) REFERENCES users(id);
-- ALTER TABLE cash_pool ADD CONSTRAINT fk_cash_pool_user FOREIGN KEY (user_id) REFERENCES users(id);
-- ALTER TABLE portfolio_snapshots ADD CONSTRAINT fk_snapshots_user FOREIGN KEY (user_id) REFERENCES users(id);

-- 迁移完成
SELECT '用户认证系统数据库迁移完成!' AS message;