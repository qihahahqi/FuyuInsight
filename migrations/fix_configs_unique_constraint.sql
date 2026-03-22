-- =====================================================
-- 修复 configs 表唯一约束问题
-- 执行时间: 2026-03-21
-- 问题: configs.key 有单独的唯一约束，导致多用户无法有相同配置键
-- 解决: 删除 key 的单独唯一约束，改为 (user_id, key) 组合唯一
-- =====================================================

-- 步骤1: 删除 key 的单独唯一约束（如果有）
-- 先查看约束名称
SELECT CONSTRAINT_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'configs'
AND COLUMN_NAME = 'key'
AND NON_UNIQUE = 0;

-- 如果上面查询返回结果，执行下面的语句删除约束
-- 假设约束名称可能是 'key' 或其他名称，需要手动确认
-- ALTER TABLE configs DROP INDEX `key`;

-- 步骤2: 删除重复数据（保留 id 最小的记录）
DELETE c1 FROM configs c1
INNER JOIN configs c2
WHERE c1.`key` = c2.`key`
AND c1.id > c2.id;

-- 步骤3: 添加 (user_id, key) 组合唯一索引
-- 如果报错索引已存在，可以忽略
-- ALTER TABLE configs ADD UNIQUE INDEX idx_configs_user_key (user_id, `key`);

-- 步骤4: 验证表结构
SHOW CREATE TABLE configs;