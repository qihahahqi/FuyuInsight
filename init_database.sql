-- ===========================================
-- 投资理财管理系统 - 数据库初始化脚本
-- ===========================================
-- 使用方法:
--   mysql -u root -p < init_database.sql
--
-- 或在 MySQL 客户端中执行:
--   source /path/to/init_database.sql
-- ===========================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS myapp
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 创建用户（如果不存在）
-- ⚠️ 重要：请将 YOUR_PASSWORD_HERE 替换为您的实际密码
-- 建议使用强密码（至少12位，包含大小写字母、数字、特殊字符）
CREATE USER IF NOT EXISTS 'devuser'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD_HERE';

-- 授权
GRANT ALL PRIVILEGES ON myapp.* TO 'devuser'@'localhost';
FLUSH PRIVILEGES;

-- 切换到数据库
USE myapp;

-- 显示成功信息
SELECT '数据库初始化完成！' AS message;
SELECT '数据库名: myapp' AS info
UNION ALL
SELECT '用户名: devuser'
UNION ALL
SELECT '密码: 请在上方 SQL 中设置您的密码'
UNION ALL
SELECT '请运行 python init_db.py 完成表结构初始化';

-- ===========================================
-- 表结构将由 SQLAlchemy 自动创建
-- 运行 python init_db.py 即可
-- ===========================================