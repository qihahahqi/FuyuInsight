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
-- 注意：请修改密码为安全的密码
CREATE USER IF NOT EXISTS 'devuser'@'localhost' IDENTIFIED BY 'dev123456';

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
SELECT '密码: dev123456 (请在生产环境修改)'
UNION ALL
SELECT '请运行 python init_db.py 完成表结构初始化';

-- ===========================================
-- 表结构将由 SQLAlchemy 自动创建
-- 运行 python init_db.py 即可
-- ===========================================