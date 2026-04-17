#!/bin/bash
# ===========================================
# 投资理财管理系统 - 数据库备份脚本
# ===========================================
# 使用方法:
#   ./scripts/backup_db.sh
#
# 建议配置 crontab 每日自动执行:
#   0 2 * * * /path/to/scripts/backup_db.sh
# ===========================================

# 配置变量（请根据实际情况修改）
DB_NAME="myapp"
DB_USER="devuser"
DB_PASS="YOUR_PASSWORD_HERE"  # 请修改为实际密码
BACKUP_DIR="./backup"
KEEP_DAYS=7  # 保留最近7天备份

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 生成备份文件名（带日期时间）
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${DATE}.sql"

# 执行备份
echo "开始备份数据库: $DB_NAME"
mysqldump -u "$DB_USER" -p"$DB_PASS" \
    --single-transaction \
    --routines \
    --triggers \
    "$DB_NAME" > "$BACKUP_FILE"

# 检查备份是否成功
if [ $? -eq 0 ]; then
    # 压缩备份文件
    gzip "$BACKUP_FILE"
    echo "备份成功: ${BACKUP_FILE}.gz"

    # 计算备份文件大小
    SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
    echo "备份大小: $SIZE"
else
    echo "备份失败！请检查数据库连接配置"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# 清理过期备份（保留最近 KEEP_DAYS 天）
echo "清理超过 $KEEP_DAYS 天的旧备份..."
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$KEEP_DAYS -delete

# 显示当前备份列表
echo "当前备份文件列表:"
ls -lh "$BACKUP_DIR"/*.sql.gz 2>/dev/null | tail -5

echo "备份完成！"