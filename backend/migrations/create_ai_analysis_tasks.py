#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 新增 AI 分析异步任务和回测历史表

执行方式:
    python backend/migrations/create_ai_analysis_tasks.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app import create_app, db
from sqlalchemy import text

app = create_app()


def migrate():
    """执行迁移"""
    with app.app_context():
        print("=" * 60)
        print("  数据库迁移: AI 分析异步任务 & 回测历史")
        print("=" * 60)

        # 检查表是否已存在
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        with db.engine.connect() as conn:
            # 1. 创建 AI 分析任务表
            if 'ai_analysis_tasks' not in existing_tables:
                print("\n[1/3] 创建 ai_analysis_tasks 表...")
                conn.execute(text("""
                    CREATE TABLE ai_analysis_tasks (
                        id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        user_id INTEGER NOT NULL,
                        analysis_type VARCHAR(20),
                        position_id INTEGER,
                        symbol VARCHAR(20),
                        dimensions TEXT,
                        status VARCHAR(20) DEFAULT 'pending',
                        progress INTEGER DEFAULT 0,
                        total_dimensions INTEGER DEFAULT 0,
                        current_dimension VARCHAR(50),
                        overall_score INTEGER,
                        model_provider VARCHAR(50),
                        model_name VARCHAR(100),
                        error_message TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        completed_at DATETIME,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (position_id) REFERENCES positions(id)
                    )
                """))
                conn.execute(text("""
                    CREATE INDEX idx_ai_task_user_status ON ai_analysis_tasks(user_id, status)
                """))
                conn.commit()
                print("✓ ai_analysis_tasks 表创建成功")
            else:
                print("\n[1/3] ai_analysis_tasks 表已存在，跳过")

            # 2. 创建 AI 分析维度结果表
            if 'ai_analysis_dimensions' not in existing_tables:
                print("\n[2/3] 创建 ai_analysis_dimensions 表...")
                conn.execute(text("""
                    CREATE TABLE ai_analysis_dimensions (
                        id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        task_id INTEGER NOT NULL,
                        dimension VARCHAR(50) NOT NULL,
                        status VARCHAR(20) DEFAULT 'pending',
                        score INTEGER,
                        analysis TEXT,
                        error_message TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (task_id) REFERENCES ai_analysis_tasks(id) ON DELETE CASCADE,
                        UNIQUE KEY uix_task_dimension (task_id, dimension)
                    )
                """))
                conn.execute(text("""
                    CREATE INDEX idx_ai_dimension_task ON ai_analysis_dimensions(task_id)
                """))
                conn.commit()
                print("✓ ai_analysis_dimensions 表创建成功")
            else:
                print("\n[2/3] ai_analysis_dimensions 表已存在，跳过")

            # 3. 创建回测历史表
            if 'backtest_histories' not in existing_tables:
                print("\n[3/3] 创建 backtest_histories 表...")
                conn.execute(text("""
                    CREATE TABLE backtest_histories (
                        id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        user_id INTEGER NOT NULL,
                        symbol VARCHAR(20) NOT NULL,
                        name VARCHAR(50),
                        start_date DATE NOT NULL,
                        end_date DATE NOT NULL,
                        initial_capital DECIMAL(12, 2) NOT NULL,
                        strategy_type VARCHAR(50),
                        results LONGTEXT,
                        best_strategy VARCHAR(50),
                        best_return DECIMAL(8, 4),
                        notes TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        UNIQUE KEY uix_backtest_user_symbol_range (user_id, symbol, start_date, end_date)
                    )
                """))
                conn.execute(text("""
                    CREATE INDEX idx_backtest_user ON backtest_histories(user_id)
                """))
                conn.execute(text("""
                    CREATE INDEX idx_backtest_symbol ON backtest_histories(symbol)
                """))
                conn.execute(text("""
                    CREATE INDEX idx_backtest_date ON backtest_histories(start_date, end_date)
                """))
                conn.commit()
                print("✓ backtest_histories 表创建成功")
            else:
                print("\n[3/3] backtest_histories 表已存在，跳过")

        print("\n" + "=" * 60)
        print("  迁移完成！")
        print("=" * 60)


if __name__ == '__main__':
    migrate()