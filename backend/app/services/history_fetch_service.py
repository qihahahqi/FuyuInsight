#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史数据后台获取服务
支持分批获取持仓历史数据，防止接口频繁访问
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
from flask import Flask

logger = logging.getLogger(__name__)


class HistoryFetchService:
    """历史数据后台获取服务"""

    def __init__(self):
        self._running = False
        self._thread = None
        self._app = None
        self._user_id = None
        self._progress = {}  # 存储每个用户的获取进度
        self._stop_flag = False

    def get_progress(self, user_id: int) -> Dict[str, Any]:
        """获取用户的进度信息"""
        return self._progress.get(user_id, {
            'status': 'idle',
            'total': 0,
            'completed': 0,
            'current_symbol': None,
            'message': '等待启动'
        })

    def stop_fetch(self, user_id: int):
        """停止获取任务"""
        if user_id in self._progress:
            self._progress[user_id]['status'] = 'stopped'
            self._progress[user_id]['message'] = '用户手动停止'
        self._stop_flag = True

    def start_fetch(self, app: Flask, user_id: int, years: int = 10) -> Dict[str, Any]:
        """
        启动后台获取任务

        Args:
            app: Flask应用实例
            user_id: 用户ID
            years: 获取年数

        Returns:
            启动状态信息
        """
        # 检查是否已有任务在运行
        progress = self.get_progress(user_id)
        if progress['status'] == 'running':
            return {
                'success': False,
                'message': '已有获取任务在运行，请等待完成或停止后再试',
                'progress': progress
            }

        self._app = app
        self._user_id = user_id
        self._stop_flag = False

        # 初始化进度
        self._progress[user_id] = {
            'status': 'running',
            'total': 0,
            'completed': 0,
            'current_symbol': None,
            'current_name': None,
            'year_progress': {},  # 每个标的每年的进度
            'message': '正在启动...'
        }

        # 启动后台线程
        self._thread = threading.Thread(
            target=self._fetch_history_loop,
            args=(user_id, years),
            daemon=True
        )
        self._thread.start()

        return {
            'success': True,
            'message': '后台获取任务已启动',
            'progress': self._progress[user_id]
        }

    def _fetch_history_loop(self, user_id: int, years: int):
        """后台获取循环"""
        from .. import db
        from ..models import Position, PriceHistory
        from .market_data_service import get_market_data_service

        with self._app.app_context():
            try:
                # 获取用户持仓
                positions = Position.query.filter_by(user_id=user_id).all()

                if not positions:
                    self._progress[user_id] = {
                        'status': 'completed',
                        'total': 0,
                        'completed': 0,
                        'message': '无持仓数据，获取完成'
                    }
                    return

                # 计算总任务数：每个标的 * 每年
                total_tasks = len(positions) * years
                self._progress[user_id]['total'] = total_tasks
                self._progress[user_id]['message'] = f'开始获取 {len(positions)} 个标的，{years} 年数据'

                service = get_market_data_service()
                completed = 0

                # 计算起始年份（从最早年份开始）
                current_year = datetime.now().year
                year_list = list(range(current_year - years + 1, current_year + 1))

                for position in positions:
                    if self._stop_flag or self._progress[user_id]['status'] == 'stopped':
                        break

                    symbol = position.symbol
                    name = position.name
                    asset_type = position.asset_type

                    self._progress[user_id]['current_symbol'] = symbol
                    self._progress[user_id]['current_name'] = name

                    # 初始化该标的的年度进度
                    self._progress[user_id]['year_progress'][symbol] = {
                        'name': name,
                        'years_completed': [],
                        'years_pending': year_list.copy()
                    }

                    # 检查已有数据，确定哪些年份需要获取
                    existing_dates = db.session.query(PriceHistory.trade_date).filter(
                        PriceHistory.user_id == user_id,
                        PriceHistory.symbol == symbol
                    ).all()
                    existing_years = set()
                    for d in existing_dates:
                        if d[0]:
                            existing_years.add(d[0].year)

                    # 只获取缺失的年份
                    years_to_fetch = [y for y in year_list if y not in existing_years]

                    for year in years_to_fetch:
                        if self._stop_flag or self._progress[user_id]['status'] == 'stopped':
                            break

                        # 计算该年的日期范围
                        start_date = f"{year}-01-01"
                        end_date = f"{year}-12-31"

                        # 如果是当前年，结束日期用今天
                        if year == current_year:
                            end_date = datetime.now().strftime('%Y-%m-%d')

                        self._progress[user_id]['message'] = f'正在获取 {name} ({symbol}) {year} 年数据...'

                        try:
                            if asset_type in ['stock', 'etf_index', 'etf_sector']:
                                df = service.get_stock_history(symbol, start_date, end_date, user_id)
                            elif asset_type == 'fund':
                                df = service.get_fund_nav_history(symbol, start_date, end_date, user_id)
                            else:
                                df = None

                            if df is not None and not df.empty:
                                # 更新进度
                                self._progress[user_id]['year_progress'][symbol]['years_completed'].append(year)
                                if year in self._progress[user_id]['year_progress'][symbol]['years_pending']:
                                    self._progress[user_id]['year_progress'][symbol]['years_pending'].remove(year)

                                logger.info(f"获取 {symbol} {year} 年数据成功: {len(df)} 条")

                        except Exception as e:
                            logger.warning(f"获取 {symbol} {year} 年数据失败: {str(e)}")

                        completed += 1
                        self._progress[user_id]['completed'] = completed

                        # 每次获取后暂停3秒，防止接口频繁访问
                        time.sleep(3)

                    # 每个标之间暂停5秒
                    if not self._stop_flag and self._progress[user_id]['status'] != 'stopped':
                        time.sleep(5)

                # 完成
                if self._progress[user_id]['status'] != 'stopped':
                    self._progress[user_id]['status'] = 'completed'
                    self._progress[user_id]['message'] = f'获取完成！共处理 {len(positions)} 个标的'
                    self._progress[user_id]['current_symbol'] = None
                    self._progress[user_id]['current_name'] = None

            except Exception as e:
                logger.error(f"后台获取任务失败: {str(e)}")
                self._progress[user_id] = {
                    'status': 'error',
                    'total': 0,
                    'completed': 0,
                    'message': f'获取失败: {str(e)}'
                }


# 全局服务实例
history_fetch_service = HistoryFetchService()