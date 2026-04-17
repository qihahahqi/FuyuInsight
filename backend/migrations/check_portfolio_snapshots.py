#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移：确保 portfolio_snapshots 表存在
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app, db
from backend.app.models import PortfolioSnapshot


def migrate():
    """执行迁移"""
    print("=" * 60)
    print("检查 portfolio_snapshots 表...")
    print("=" * 60)

    app = create_app()

    with app.app_context():
        # 创建表（如果不存在）
        db.create_all()
        print("✓ 数据表检查完成")

        # 检查现有快照数量
        count = PortfolioSnapshot.query.count()
        print(f"当前快照记录数: {count}")

        if count == 0:
            print("\n提示: 快照表为空，这是因为还没有积累历史数据。")
            print("解决方法:")
            print("  1. 点击「同步价格」按钮，系统会创建今日快照")
            print("  2. 每天同步价格，积累历史数据")
            print("  3. 交易日系统会自动同步价格（需要启动服务）")

    print("\n" + "=" * 60)
    print("迁移完成！")
    print("=" * 60)


if __name__ == '__main__':
    migrate()