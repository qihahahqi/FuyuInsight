# 数据库备份策略

**最后更新：2026年4月17日**

---

## 1. 备份方案概述

本系统提供自动化数据库备份脚本，支持：
- Linux/macOS: `scripts/backup_db.sh`
- Windows: `scripts/backup_db.bat`

---

## 2. 备份内容

| 数据 | 备份方式 | 说明 |
|-----|---------|------|
| 用户数据 | mysqldump | 持仓、交易、账户等所有业务数据 |
| 表结构 | mysqldump | 数据库表定义 |
| 触发器/存储过程 | mysqldump | 自动包含 |

---

## 3. 备份频率建议

| 环境 | 频率 | 保留时间 |
|-----|------|---------|
| 个人使用 | 每日 | 7天 |
| 生产环境 | 每日 + 每周 | 30天 |

---

## 4. Linux/macOS 自动备份配置

### 4.1 编辑 crontab

```bash
crontab -e
```

### 4.2 添加定时任务

```bash
# 每天凌晨2点执行备份
0 2 * * * cd /path/to/financial-management-system && ./scripts/backup_db.sh >> logs/backup.log 2>&1
```

### 4.3 验证 crontab

```bash
crontab -l
```

---

## 5. Windows 自动备份配置

### 5.1 打开任务计划程序

1. 按 `Win + R`，输入 `taskschd.msc`
2. 点击「创建基本任务」

### 5.2 配置任务

- **名称**: FuyuInsight 数据库备份
- **触发器**: 每天凌晨2点
- **操作**: 启动程序
  - 程序路径: `scripts\backup_db.bat`
  - 起始于: 项目根目录

---

## 6. 备份恢复步骤

### 6.1 恢复单个数据库

```bash
# Linux/macOS
gunzip backup/myapp_20260417.sql.gz
mysql -u devuser -p myapp < backup/myapp_20260417.sql

# Windows
mysql -u devuser -p myapp < backup\myapp_20260417.sql
```

### 6.2 恢复到新数据库（安全恢复）

```bash
# 创建临时数据库
mysql -u root -p -e "CREATE DATABASE myapp_restore"

# 恢复备份到临时数据库
mysql -u devuser -p myapp_restore < backup/myapp_20260417.sql

# 验证数据后，重命名
mysql -u root -p -e "DROP DATABASE myapp; RENAME DATABASE myapp_restore TO myapp"
```

---

## 7. 备份文件管理

### 7.1 备份文件命名规则

```
myapp_YYYYMMDD_HHMMSS.sql.gz
```

示例: `myapp_20260417_020000.sql.gz`

### 7.2 存储位置

默认存储在项目 `backup/` 目录。建议：
- 本地备份: `backup/` 目录
- 远程备份: 云存储或异地服务器

---

## 8. 备份验证

定期验证备份有效性：

```bash
# 检查备份文件大小（不应为0）
ls -lh backup/

# 检查备份内容
zcat backup/myapp_20260417.sql.gz | head -20
```

---

## 9. 备份脚本配置

修改 `scripts/backup_db.sh` 中的配置：

```bash
DB_NAME="myapp"           # 数据库名
DB_USER="devuser"         # 用户名
DB_PASS="YOUR_PASSWORD"   # 密码（请修改）
BACKUP_DIR="./backup"     # 备份目录
KEEP_DAYS=7               # 保留天数
```

---

## 10. 安全建议

1. **备份文件加密**: 建议对敏感备份文件进行加密
2. **异地备份**: 重要数据建议异地存储
3. **定期验证**: 每月验证一次备份恢复流程
4. **监控告警**: 备份失败时发送通知