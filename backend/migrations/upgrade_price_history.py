#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：更新 price_histories 表结构
添加基金和新字段支持

使用方法：
    python backend/migrations/upgrade_price_history.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app import create_app, db
from sqlalchemy import text


def upgrade():
    """升级数据库表结构"""
    app = create_app()

    with app.app_context():
        print("开始迁移 price_histories 表...")

        try:
            # 检查表是否存在
            result = db.session.execute(text("SHOW TABLES LIKE 'price_histories'"))
            if result.fetchone() is None:
                print("price_histories 表不存在，将创建新表...")
                db.create_all()
                print("表创建完成")
                return

            # 获取现有列
            result = db.session.execute(text("DESCRIBE price_histories"))
            existing_columns = {row[0] for row in result.fetchall()}

            # 需要添加的新列
            new_columns = [
                ("asset_type", "VARCHAR(20) COMMENT '资产类型: stock/fund/etf'"),
                ("turnover", "DECIMAL(16, 2) COMMENT '成交额'"),
                ("change_pct", "DECIMAL(8, 4) COMMENT '涨跌幅(%)'"),
                ("amplitude", "DECIMAL(8, 4) COMMENT '振幅(%)'"),
                ("turnover_rate", "DECIMAL(8, 4) COMMENT '换手率(%)'"),
                ("acc_nav", "DECIMAL(10, 4) COMMENT '累计净值(基金专用)'"),
                ("data_source", "VARCHAR(20) COMMENT '数据来源: akshare/baostock/eastmoney/tushare'"),
            ]

            # 添加缺失的列
            for col_name, col_def in new_columns:
                if col_name not in existing_columns:
                    print(f"添加列: {col_name}")
                    db.session.execute(text(f"ALTER TABLE price_histories ADD COLUMN {col_name} {col_def}"))

            # 添加唯一约束（如果不存在）
            try:
                db.session.execute(text("""
                    ALTER TABLE price_histories
                    ADD CONSTRAINT uix_user_symbol_date UNIQUE (user_id, symbol, trade_date)
                """))
                print("添加唯一约束: uix_user_symbol_date")
            except Exception as e:
                if "Duplicate key name" in str(e) or "already exists" in str(e):
                    print("唯一约束已存在，跳过")
                else:
                    print(f"添加唯一约束时出错: {e}")

            # 添加索引
            try:
                db.session.execute(text("""
                    CREATE INDEX idx_price_history_user_symbol ON price_histories (user_id, symbol)
                """))
                print("添加索引: idx_price_history_user_symbol")
            except Exception as e:
                if "Duplicate key name" in str(e) or "already exists" in str(e):
                    print("索引已存在，跳过")
                else:
                    print(f"添加索引时出错: {e}")

            try:
                db.session.execute(text("""
                    CREATE INDEX idx_price_history_date ON price_histories (trade_date)
                """))
                print("添加索引: idx_price_history_date")
            except Exception as e:
                if "Duplicate key name" in str(e) or "already exists" in str(e):
                    print("索引已存在，跳过")
                else:
                    print(f"添加索引时出错: {e}")

            db.session.commit()
            print("迁移完成!")

        except Exception as e:
            db.session.rollback()
            print(f"迁移失败: {e}")
            raise


def downgrade():
    """回滚数据库表结构（可选）"""
    app = create_app()

    with app.app_context():
        print("开始回滚 price_histories 表...")

        try:
            # 删除新增的列
            columns_to_drop = [
                'asset_type', 'turnover', 'change_pct',
                'amplitude', 'turnover_rate', 'acc_nav', 'data_source'
            ]

            for col in columns_to_drop:
                try:
                    db.session.execute(text(f"ALTER TABLE price_histories DROP COLUMN {col}"))
                    print(f"删除列: {col}")
                except Exception as e:
                    print(f"删除列 {col} 失败: {e}")

            db.session.commit()
            print("回滚完成!")

        except Exception as e:
            db.session.rollback()
            print(f"回滚失败: {e}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='数据库迁移脚本')
    parser.add_argument('--downgrade', action='store_true', help='回滚迁移')
    args = parser.parse_args()

    if args.downgrade:
        downgrade()
    else:
        upgrade()