#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：扩展理财产品支持
添加新资产类型和固定收益产品相关字段

执行方式：
    python backend/migrations/add_financial_products.py
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app import create_app, db
from sqlalchemy import text


def migrate():
    """执行数据库迁移"""
    print("=" * 60)
    print("开始执行理财产品扩展迁移...")
    print("=" * 60)

    app = create_app()

    with app.app_context():
        try:
            # 1. 扩展 Position 表字段（逐个添加）
            print("\n[1/3] 扩展 positions 表字段...")

            # 定义要添加的字段
            columns_to_add = [
                ("product_category", "VARCHAR(20) DEFAULT 'market' COMMENT '产品大类'"),
                ("product_params", "JSON COMMENT '产品特性参数'"),
                ("expected_return", "DECIMAL(8,4) COMMENT '预期收益率(年化)'"),
                ("actual_return", "DECIMAL(8,4) COMMENT '实际收益率'"),
                ("mature_date", "DATE COMMENT '到期日'"),
                ("risk_level", "VARCHAR(10) COMMENT '风险等级'"),
            ]

            for col_name, col_def in columns_to_add:
                try:
                    alter_sql = f"ALTER TABLE positions ADD COLUMN {col_name} {col_def}"
                    db.session.execute(text(alter_sql))
                    db.session.commit()
                    print(f"  ✓ 添加字段 {col_name} 成功")
                except Exception as e:
                    if "Duplicate column" in str(e) or "already exists" in str(e).lower():
                        print(f"  ✓ 字段 {col_name} 已存在，跳过")
                    else:
                        print(f"  ✗ 添加字段 {col_name} 失败: {str(e)}")
                    db.session.rollback()

            # 2. 创建收益记录表
            print("\n[2/3] 创建 income_records 表...")

            create_income_records = """
            CREATE TABLE IF NOT EXISTS income_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL COMMENT '用户ID',
                position_id INT COMMENT '关联持仓ID',
                record_date DATE NOT NULL COMMENT '收益日期',
                income_amount DECIMAL(12,2) NOT NULL COMMENT '收益金额',
                income_type VARCHAR(20) COMMENT '收益类型: interest/dividend/maturity/other',
                note TEXT COMMENT '备注',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE SET NULL,
                INDEX idx_user_position (user_id, position_id),
                INDEX idx_date (record_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='收益记录表'
            """

            db.session.execute(text(create_income_records))
            db.session.commit()
            print("  ✓ income_records 表创建成功")

            # 3. 更新现有数据的 product_category
            print("\n[3/3] 更新现有数据的 product_category...")

            try:
                update_sql = """
                UPDATE positions SET product_category = 'market'
                WHERE product_category IS NULL OR product_category = 'market'
                AND asset_type IN ('stock', 'etf_index', 'etf_sector', 'fund')
                """
                db.session.execute(text(update_sql))
                db.session.commit()
                print("  ✓ 现有数据更新成功")
            except Exception as e:
                print(f"  ! 更新数据跳过: {str(e)}")
                db.session.rollback()

            print("\n" + "=" * 60)
            print("理财产品扩展迁移完成！")
            print("=" * 60)

            # 显示新增字段说明
            print("\n新增字段说明：")
            print("  - product_category: 产品大类 (market/fixed_income/manual)")
            print("  - product_params: 产品特性参数 (JSON格式)")
            print("  - expected_return: 预期收益率(年化)")
            print("  - actual_return: 实际收益率")
            print("  - mature_date: 到期日")
            print("  - risk_level: 风险等级 (R1-R5)")

            print("\n新增资产类型：")
            print("  固定收益类: bank_deposit, bank_current, bank_wealth, treasury_bond, corporate_bond, money_fund")
            print("  贵金属类: gold, silver")
            print("  其他: insurance, trust, other")

        except Exception as e:
            db.session.rollback()
            print(f"\n✗ 迁移失败: {str(e)}")
            raise


if __name__ == '__main__':
    migrate()