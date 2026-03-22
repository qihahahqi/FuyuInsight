#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资组合快照服务
"""

from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from .. import db
from ..models import Position, PortfolioSnapshot


class SnapshotService:
    """投资组合快照服务"""

    def create_daily_snapshot(self, account_id: int, user_id: int = None) -> Dict:
        """
        创建每日快照

        Args:
            account_id: 账户 ID
            user_id: 用户 ID

        Returns:
            Dict: 快照结果
        """
        # 获取账户持仓
        query = Position.query.filter_by(account_id=account_id)
        if user_id:
            query = query.filter_by(user_id=user_id)
        positions = query.all()

        if not positions:
            return {
                'success': False,
                'message': '该账户没有持仓'
            }

        # 计算汇总数据
        total_cost = sum(float(p.total_cost) for p in positions)
        market_value = sum(float(p.market_value) for p in positions if p.market_value)
        profit_rate = (market_value - total_cost) / total_cost if total_cost > 0 else 0

        # 检查今天是否已有快照
        today = date.today()
        query = PortfolioSnapshot.query.filter_by(
            account_id=account_id,
            snapshot_date=today
        )
        if user_id:
            query = query.filter_by(user_id=user_id)
        existing = query.first()

        if existing:
            # 更新现有快照
            existing.total_cost = total_cost
            existing.market_value = market_value
            existing.profit_rate = profit_rate
            existing.position_count = len(positions)
        else:
            # 创建新快照
            snapshot = PortfolioSnapshot(
                user_id=user_id,
                account_id=account_id,
                snapshot_date=today,
                total_cost=total_cost,
                market_value=market_value,
                profit_rate=profit_rate,
                position_count=len(positions)
            )
            db.session.add(snapshot)

        db.session.commit()

        return {
            'success': True,
            'message': '快照创建成功',
            'snapshot': {
                'date': today.isoformat(),
                'total_cost': total_cost,
                'market_value': market_value,
                'profit_rate': profit_rate,
                'position_count': len(positions)
            }
        }

    def get_snapshots(self, account_id: int, days: int = 30, user_id: int = None) -> List[Dict]:
        """
        获取历史快照

        Args:
            account_id: 账户 ID
            days: 天数
            user_id: 用户 ID

        Returns:
            List[Dict]: 快照列表
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        query = PortfolioSnapshot.query.filter(
            PortfolioSnapshot.account_id == account_id,
            PortfolioSnapshot.snapshot_date >= start_date,
            PortfolioSnapshot.snapshot_date <= end_date
        )
        if user_id:
            query = query.filter(PortfolioSnapshot.user_id == user_id)

        snapshots = query.order_by(PortfolioSnapshot.snapshot_date).all()

        return [s.to_dict() for s in snapshots]

    def get_profit_curve_data(self, account_id: int, days: int = 30, user_id: int = None) -> Dict:
        """
        获取收益曲线数据

        Args:
            account_id: 账户 ID
            days: 天数
            user_id: 用户 ID

        Returns:
            Dict: 图表数据
        """
        snapshots = self.get_snapshots(account_id, days, user_id)

        if not snapshots:
            # 如果没有快照，计算当前持仓并返回单点数据
            query = Position.query.filter_by(account_id=account_id)
            if user_id:
                query = query.filter_by(user_id=user_id)
            positions = query.all()
            if positions:
                total_cost = sum(float(p.total_cost) for p in positions)
                market_value = sum(float(p.market_value) for p in positions if p.market_value)
                profit_rate = (market_value - total_cost) / total_cost if total_cost > 0 else 0

                return {
                    'labels': [date.today().isoformat()],
                    'profit_rates': [round(profit_rate * 100, 2)],
                    'market_values': [market_value],
                    'total_costs': [total_cost]
                }
            return {
                'labels': [],
                'profit_rates': [],
                'market_values': [],
                'total_costs': []
            }

        # 提取数据
        labels = [s['snapshot_date'] for s in snapshots]
        profit_rates = [round(s['profit_rate'] * 100, 2) if s['profit_rate'] else 0 for s in snapshots]
        market_values = [s['market_value'] for s in snapshots]
        total_costs = [s['total_cost'] for s in snapshots]

        return {
            'labels': labels,
            'profit_rates': profit_rates,
            'market_values': market_values,
            'total_costs': total_costs
        }

    def fill_missing_snapshots(self, account_id: int, days: int = 90, user_id: int = None) -> Dict:
        """
        补充缺失的快照数据（用于初始化）

        Args:
            account_id: 账户 ID
            days: 天数
            user_id: 用户 ID

        Returns:
            Dict: 填充结果
        """
        query = Position.query.filter_by(account_id=account_id)
        if user_id:
            query = query.filter_by(user_id=user_id)
        positions = query.all()

        if not positions:
            return {'success': False, 'message': '没有持仓数据'}

        total_cost = sum(float(p.total_cost) for p in positions)
        market_value = sum(float(p.market_value) for p in positions if p.market_value)
        profit_rate = (market_value - total_cost) / total_cost if total_cost > 0 else 0

        filled = 0
        for i in range(days):
            snapshot_date = date.today() - timedelta(days=days - i - 1)

            # 检查是否存在
            query = PortfolioSnapshot.query.filter_by(
                account_id=account_id,
                snapshot_date=snapshot_date
            )
            if user_id:
                query = query.filter_by(user_id=user_id)
            existing = query.first()

            if not existing:
                snapshot = PortfolioSnapshot(
                    user_id=user_id,
                    account_id=account_id,
                    snapshot_date=snapshot_date,
                    total_cost=total_cost,
                    market_value=market_value,
                    profit_rate=profit_rate,
                    position_count=len(positions)
                )
                db.session.add(snapshot)
                filled += 1

        db.session.commit()

        return {
            'success': True,
            'filled': filled,
            'message': f'已补充 {filled} 条快照记录'
        }