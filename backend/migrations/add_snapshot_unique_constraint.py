#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移：为 portfolio_snapshots 表添加唯一约束
防止同一账户同一日期有多条快照记录
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app, db
import logging

logger = logging.getLogger(__name__)


def migrate():
    """执行迁移"""
    print("=" * 60)
    print("添加 portfolio_snapshots 唯一约束...")
    print("=" * 60)

    app = create_app()

    with app.app_context():
        # 检查唯一约束是否已存在
        try:
            # 尝试直接添加约束（如果已存在会报错）
            db.session.execute(db.text("""
                ALTER TABLE portfolio_snapshots
                ADD CONSTRAINT uix_account_snapshot_date
                UNIQUE (account_id, snapshot_date)
            """))
            db.session.commit()
            print("✓ 唯一约束添加成功")
        except Exception as e:
            if 'Duplicate' in str(e) or 'already exists' in str(e) or 'Duplicate key name' in str(e):
                print("✓ 唯一约束已存在，无需添加")
            else:
                print(f"添加约束时出错: {str(e)}")
                # 尝试先删除重复数据
                print("\n检查并清理重复数据...")
                try:
                    # 查找重复记录
                    result = db.session.execute(db.text("""
                        SELECT account_id, snapshot_date, COUNT(*) as cnt
                        FROM portfolio_snapshots
                        GROUP BY account_id, snapshot_date
                        HAVING COUNT(*) > 1
                    """))
                    duplicates = result.fetchall()

                    if duplicates:
                        print(f"发现 {len(duplicates)} 组重复数据")
                        for dup in duplicates:
                            account_id, snapshot_date, cnt = dup
                            print(f"  account_id={account_id}, date={snapshot_date}, count={cnt}")

                            # 删除重复记录，只保留最新的一条
                            db.session.execute(db.text("""
                                DELETE FROM portfolio_snapshots
                                WHERE account_id = :account_id
                                AND snapshot_date = :snapshot_date
                                AND id NOT IN (
                                    SELECT MAX(id) FROM portfolio_snapshots
                                    WHERE account_id = :account_id
                                    AND snapshot_date = :snapshot_date
                                )
                            """), {'account_id': account_id, 'snapshot_date': snapshot_date})

                        db.session.commit()
                        print("✓ 重复数据已清理")

                        # 重新添加约束
                        db.session.execute(db.text("""
                            ALTER TABLE portfolio_snapshots
                            ADD CONSTRAINT uix_account_snapshot_date
                            UNIQUE (account_id, snapshot_date)
                        """))
                        db.session.commit()
                        print("✓ 唯一约束添加成功")
                    else:
                        print("没有发现重复数据")
                        db.session.rollback()

                except Exception as e2:
                    print(f"清理重复数据失败: {str(e2)}")
                    db.session.rollback()

        # 添加索引（如果不存在）
        try:
            db.session.execute(db.text("""
                CREATE INDEX idx_snapshot_account_date
                ON portfolio_snapshots (account_id, snapshot_date)
            """))
            db.session.commit()
            print("✓ 索引添加成功")
        except Exception as e:
            if 'already exists' in str(e) or 'Duplicate' in str(e):
                print("✓ 索引已存在")
            else:
                print(f"索引添加警告: {str(e)}")
            db.session.rollback()

    print("\n" + "=" * 60)
    print("迁移完成！")
    print("=" * 60)


if __name__ == '__main__':
    migrate()