#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app, db
from backend.app.models import Position, Trade, Valuation, CashPool, Config, Account, User


def init_database():
    """初始化数据库"""
    print("=" * 60)
    print("开始初始化数据库...")
    print("=" * 60)

    app = create_app()

    with app.app_context():
        # 创建所有表
        print("\n正在创建数据表...")
        db.create_all()
        print("✓ 数据表创建成功")

        # 检查是否已有数据
        if Config.query.first() is not None:
            print("\n数据库已有数据，跳过初始化")
            return

        # 初始化默认配置
        print("\n正在初始化默认配置...")
        default_configs = [
            Config(key='app.initialized', value='true', description='系统初始化标记'),
            Config(key='app.version', value='1.0.0', description='系统版本'),
        ]

        for config in default_configs:
            db.session.add(config)

        db.session.commit()
        print("✓ 默认配置初始化成功")

        # 创建默认用户
        print("\n正在创建默认用户...")

        # 创建默认管理员用户
        default_user = User(username='admin', email='admin@example.com')
        default_user.set_password('admin123')  # 请在生产环境中修改
        db.session.add(default_user)
        db.session.commit()
        print(f"✓ 默认用户创建成功 (用户名: admin, 密码: admin123)")
        print("  ⚠️  请在生产环境中立即修改默认密码！")

        # 创建默认账户
        print("\n正在创建默认投资账户...")
        default_account = Account(
            user_id=default_user.id,
            name='主账户',
            account_type='personal',
            broker='默认',
            description='系统自动创建的默认账户',
            is_active=True
        )
        db.session.add(default_account)
        db.session.commit()
        print(f"✓ 默认账户创建成功 (ID: {default_account.id})")

        # 初始化现金池
        print("\n正在初始化现金池...")
        from datetime import date
        initial_cash = CashPool(
            user_id=default_user.id,
            amount=5000,
            balance=5000,
            event='初始储备',
            event_date=date.today()
        )
        db.session.add(initial_cash)
        db.session.commit()
        print("✓ 现金池初始化成功（初始金额: 5000元）")

        # 添加示例数据（可选）
        print("\n是否添加示例数据？(y/n): ", end="")
        try:
            choice = input().strip().lower()
            if choice == 'y':
                add_sample_data(default_user.id, default_account.id)
        except EOFError:
            pass

    print("\n" + "=" * 60)
    print("数据库初始化完成！")
    print("=" * 60)
    print("\n默认登录信息:")
    print("  用户名: admin")
    print("  密码: admin123")
    print("  ⚠️  请登录后立即修改密码！")
    print("=" * 60)


def add_sample_data(user_id, account_id):
    """添加示例数据"""
    from datetime import date, datetime

    print("\n正在添加示例数据...")

    # 示例持仓
    positions = [
        Position(
            user_id=user_id,
            account_id=account_id,
            symbol='510300',
            name='沪深300ETF',
            asset_type='etf_index',
            quantity=5000,
            cost_price=4.000,
            current_price=4.200,
            total_cost=20000,
            market_value=21000,
            profit_rate=0.05,
            category='core',
            notes='核心仓位'
        ),
        Position(
            user_id=user_id,
            account_id=account_id,
            symbol='159915',
            name='创业板ETF',
            asset_type='etf_index',
            quantity=3000,
            cost_price=2.000,
            current_price=1.800,
            total_cost=6000,
            market_value=5400,
            profit_rate=-0.10,
            category='satellite',
            notes='卫星仓位'
        ),
    ]

    for p in positions:
        p.stop_profit_triggered = '[false, false, false]'
        db.session.add(p)

    # 示例估值数据
    valuations = [
        Valuation(
            user_id=user_id,
            symbol='000300',
            index_name='沪深300',
            pe=12.5,
            pb=1.35,
            pe_percentile=35.0,
            pb_percentile=28.0,
            rsi=48.0,
            level='合理偏低',
            score=36.4,
            suggestion='合理偏低，可正常买入',
            record_date=date.today()
        ),
    ]

    for v in valuations:
        db.session.add(v)

    # 示例交易记录
    trades = [
        Trade(
            user_id=user_id,
            account_id=account_id,
            symbol='510300',
            trade_type='buy',
            quantity=5000,
            price=4.000,
            amount=20000,
            trade_date=date(2026, 3, 15),
            reason='低估建仓'
        ),
    ]

    for t in trades:
        db.session.add(t)

    db.session.commit()
    print("✓ 示例数据添加成功")


def reset_database():
    """重置数据库（删除所有数据）"""
    print("=" * 60)
    print("警告：这将删除所有数据！")
    print("=" * 60)

    try:
        confirm = input("确认要重置数据库吗？输入 'yes' 确认: ").strip()
        if confirm != 'yes':
            print("操作已取消")
            return
    except EOFError:
        print("操作已取消")
        return

    app = create_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✓ 数据库已重置")

    # 重新初始化
    init_database()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='数据库初始化工具')
    parser.add_argument('--reset', action='store_true', help='重置数据库')
    args = parser.parse_args()

    if args.reset:
        reset_database()
    else:
        init_database()