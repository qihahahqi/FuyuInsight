#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务调度服务
用于在交易日定时同步持仓数据
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Callable, List
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务调度器"""

    def __init__(self):
        self._running = False
        self._thread = None
        self._jobs = []
        self._app = None  # Flask 应用实例
        # 交易日的同步时间点（小时）
        self.sync_hours = [9, 12, 14, 16]

    def is_trading_day(self, date: datetime = None) -> bool:
        """
        判断是否为交易日（简单判断：周一到周五）
        实际生产环境应该查询交易日历
        """
        if date is None:
            date = datetime.now()
        # 周一到周五 (0-4)
        return date.weekday() < 5

    def is_trading_time(self) -> bool:
        """判断当前是否在交易时间"""
        if not self.is_trading_day():
            return False

        hour = datetime.now().hour
        # 交易时间：9:30-11:30, 13:00-15:00
        # 同步时间点前后也允许
        return (9 <= hour <= 11) or (13 <= hour <= 15) or hour in self.sync_hours

    def should_sync_now(self) -> bool:
        """判断当前是否应该同步"""
        if not self.is_trading_day():
            return False

        now = datetime.now()
        hour = now.hour
        minute = now.minute

        # 在同步时间点前后10分钟内触发
        for sync_hour in self.sync_hours:
            if hour == sync_hour and minute < 10:
                return True

        return False

    def add_job(self, func: Callable, interval_seconds: int = 60):
        """添加定时任务"""
        self._jobs.append({
            'func': func,
            'interval': interval_seconds
        })

    def _run_jobs(self):
        """执行所有任务（在应用上下文中）"""
        if not self._app:
            logger.error("Flask 应用未初始化，无法执行定时任务")
            return

        with self._app.app_context():
            for job in self._jobs:
                try:
                    job['func']()
                except Exception as e:
                    logger.error(f"定时任务执行失败: {str(e)}")

    def _scheduler_loop(self):
        """调度循环"""
        logger.info("定时任务调度器启动")
        last_sync_hour = -1

        while self._running:
            try:
                now = datetime.now()

                # 检查是否需要在当前时间点同步
                if self.is_trading_day():
                    current_hour = now.hour

                    # 如果是同步时间点，且还没同步过这个时间点
                    if current_hour in self.sync_hours and current_hour != last_sync_hour:
                        if now.minute < 10:  # 在整点后10分钟内执行
                            logger.info(f"触发定时同步: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                            self._run_jobs()
                            last_sync_hour = current_hour

                # 每分钟检查一次
                time.sleep(60)

            except Exception as e:
                logger.error(f"调度循环异常: {str(e)}")
                time.sleep(60)

        logger.info("定时任务调度器停止")

    def start(self):
        """启动调度器"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()
        logger.info("定时任务调度器已启动")

    def stop(self):
        """停止调度器"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("定时任务调度器已停止")

    def sync_all_users_positions(self):
        """同步所有用户的持仓数据"""
        from .. import db
        from ..models import User, Position
        from .market_data_service import get_market_data_service

        try:
            # 获取所有活跃用户
            users = User.query.filter_by(is_active=True).all()

            if not users:
                logger.info("没有活跃用户，跳过同步")
                return

            service = get_market_data_service()

            for user in users:
                try:
                    # 检查用户是否有持仓
                    positions_count = Position.query.filter_by(user_id=user.id).filter(Position.quantity > 0).count()
                    if positions_count == 0:
                        continue

                    logger.info(f"同步用户 {user.username} 的持仓数据...")
                    result = service.sync_position_prices(user.id)
                    logger.info(f"用户 {user.username} 同步完成: {result.get('message', '')}")

                except Exception as e:
                    logger.error(f"同步用户 {user.username} 失败: {str(e)}")

            db.session.commit()

        except Exception as e:
            logger.error(f"同步所有用户持仓失败: {str(e)}")
            db.session.rollback()


# 全局调度器实例
scheduler = SchedulerService()


def init_scheduler(app):
    """初始化并启动调度器"""
    # 保存 Flask 应用实例
    scheduler._app = app

    # 添加同步任务
    scheduler.add_job(scheduler.sync_all_users_positions)

    # 启动调度器
    scheduler.start()
    logger.info("定时任务调度器初始化完成")

    return scheduler