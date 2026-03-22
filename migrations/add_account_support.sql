-- 投资理财管理系统 - 数据库迁移脚本
-- 执行时间：2026-03-20
-- 说明：添加多账户支持

-- 1. 创建账户表
CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL COMMENT '账户名称',
    account_type VARCHAR(50) DEFAULT 'personal' COMMENT '账户类型',
    broker VARCHAR(50) COMMENT '券商/平台',
    description TEXT COMMENT '描述',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='投资账户表';

-- 2. 创建投资组合快照表
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT COMMENT '账户ID',
    snapshot_date DATE NOT NULL COMMENT '快照日期',
    total_cost DECIMAL(12,2) NOT NULL COMMENT '总成本',
    market_value DECIMAL(12,2) NOT NULL COMMENT '市值',
    profit_rate DECIMAL(8,4) COMMENT '收益率',
    position_count INT DEFAULT 0 COMMENT '持仓数',
    notes TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (account_id) REFERENCES accounts(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='投资组合快照表';

-- 3. 为 positions 表添加 account_id 字段
SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
               WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'positions' AND COLUMN_NAME = 'account_id');
SET @sql := IF(@exist = 0,
    'ALTER TABLE positions ADD COLUMN account_id INT COMMENT ''账户ID''',
    'SELECT ''positions.account_id already exists''');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 4. 为 trades 表添加 account_id 字段
SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
               WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trades' AND COLUMN_NAME = 'account_id');
SET @sql := IF(@exist = 0,
    'ALTER TABLE trades ADD COLUMN account_id INT COMMENT ''账户ID''',
    'SELECT ''trades.account_id already exists''');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 5. 创建默认账户
INSERT INTO accounts (name, account_type, description)
SELECT '默认账户', 'personal', '系统自动创建的默认账户'
WHERE NOT EXISTS (SELECT 1 FROM accounts WHERE id = 1);

-- 6. 将现有持仓关联到默认账户
UPDATE positions SET account_id = 1 WHERE account_id IS NULL;

-- 7. 将现有交易记录关联到默认账户
UPDATE trades SET account_id = 1 WHERE account_id IS NULL;

-- 8. 删除原有的唯一约束（如果存在）
SET @exist := (SELECT COUNT(*) FROM information_schema.STATISTICS
               WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'positions' AND INDEX_NAME = 'symbol');
SET @sql := IF(@exist > 0,
    'ALTER TABLE positions DROP INDEX symbol',
    'SELECT ''positions.symbol index not found''');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 完成
SELECT '数据库迁移完成！' AS message;