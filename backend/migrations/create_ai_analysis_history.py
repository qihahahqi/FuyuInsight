#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：创建 AI 分析历史表

使用方法：
    python backend/migrations/create_ai_analysis_history.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app import create_app, db
from sqlalchemy import text


def upgrade():
    """创建 ai_analysis_history 表"""
    app = create_app()

    with app.app_context():
        print("开始创建 ai_analysis_history 表...")

        try:
            # 检查表是否存在
            result = db.session.execute(text("SHOW TABLES LIKE 'ai_analysis_history'"))
            if result.fetchone() is not None:
                print("ai_analysis_history 表已存在，跳过创建")
                return

            # 创建表
            db.session.execute(text("""
                CREATE TABLE ai_analysis_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL COMMENT '用户ID',
                    position_id INT NULL COMMENT '持仓ID（单标的分析时）',
                    analysis_type VARCHAR(20) COMMENT '分析类型: single/portfolio',
                    symbol VARCHAR(20) NULL COMMENT '标的代码（单标的分析时）',
                    dimensions TEXT COMMENT '分析维度JSON',
                    analysis_content LONGTEXT COMMENT '分析结果JSON',
                    overall_score INT NULL COMMENT '综合评分',
                    model_provider VARCHAR(50) COMMENT '模型提供商',
                    model_name VARCHAR(100) COMMENT '模型名称',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI分析历史记录表'
            """))

            db.session.commit()
            print("ai_analysis_history 表创建成功!")

        except Exception as e:
            db.session.rollback()
            print(f"创建表失败: {e}")
            raise


def downgrade():
    """删除 ai_analysis_history 表"""
    app = create_app()

    with app.app_context():
        print("开始删除 ai_analysis_history 表...")

        try:
            db.session.execute(text("DROP TABLE IF EXISTS ai_analysis_history"))
            db.session.commit()
            print("ai_analysis_history 表删除成功!")

        except Exception as e:
            db.session.rollback()
            print(f"删除表失败: {e}")
            raise


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='数据库迁移脚本')
    parser.add_argument('--downgrade', action='store_true', help='回滚迁移')
    args = parser.parse_args()

    if args.downgrade:
        downgrade()
    else:
        upgrade()