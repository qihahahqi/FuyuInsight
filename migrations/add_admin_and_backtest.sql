-- =====================================================
-- 管理后台和回测增强数据库迁移
-- 执行时间: 2026-03-20
-- 说明: 创建管理员账户、历史价格数据表
-- =====================================================

-- 1. 创建历史价格数据表
CREATE TABLE IF NOT EXISTS price_histories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT COMMENT '用户ID',
    symbol VARCHAR(20) NOT NULL COMMENT '标的代码',
    name VARCHAR(50) COMMENT '标的名称',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open_price DECIMAL(10, 4) COMMENT '开盘价',
    high_price DECIMAL(10, 4) COMMENT '最高价',
    low_price DECIMAL(10, 4) COMMENT '最低价',
    close_price DECIMAL(10, 4) COMMENT '收盘价',
    volume BIGINT COMMENT '成交量',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_symbol (user_id, symbol),
    INDEX idx_trade_date (trade_date),
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='历史价格数据表';

-- 2. 创建默认管理员账户（用户名: Admin, 密码: Admin）
-- 密码哈希使用 werkzeug.security.generate_password_hash('Admin') 生成
INSERT INTO users (username, email, password_hash, is_active, is_admin, created_at)
SELECT 'Admin', 'admin@example.com',
    'scrypt:32768:8:1$qfYQVlZkJ3HZaBPd$c468f1769ee4b72239a633b8bee62e4da087e7a8abe7c496a7c7284822df0ba3396621e232ec7fb49bd07a203179afedefeb6fd9265b1cd5712d01be703d1da9',
    TRUE, TRUE, NOW()
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'Admin');

-- 迁移完成
SELECT '管理后台和回测增强数据库迁移完成!' AS message;