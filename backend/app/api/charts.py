#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图表数据 API
"""

from flask import Blueprint, request
from ..models import Position, Trade
from ..utils import success_response, error_response
from ..utils.decorators import login_required, get_current_user
from ..services.snapshot_service import SnapshotService
from sqlalchemy import func

charts_bp = Blueprint('charts', __name__)
snapshot_service = SnapshotService()


@charts_bp.route('/charts/profit-curve', methods=['GET'])
@login_required
def get_profit_curve():
    """获取收益曲线数据"""
    try:
        user = get_current_user()
        account_id = request.args.get('account_id', type=int, default=1)
        days = request.args.get('days', type=int, default=30)

        # 创建今日快照（如果不存在）
        snapshot_service.create_daily_snapshot(account_id, user.id)

        # 获取曲线数据
        data = snapshot_service.get_profit_curve_data(account_id, days, user.id)

        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@charts_bp.route('/charts/distribution', methods=['GET'])
@login_required
def get_distribution():
    """获取持仓分布数据"""
    try:
        user = get_current_user()
        account_id = request.args.get('account_id', type=int)

        query = Position.query.filter_by(user_id=user.id)
        if account_id:
            query = query.filter_by(account_id=account_id)

        positions = query.all()

        if not positions:
            return success_response({
                'by_type': {},
                'by_category': {},
                'total_value': 0
            })

        # 按资产类型分布
        by_type = {}
        # 按分类分布
        by_category = {}
        total_value = 0

        for p in positions:
            value = float(p.market_value) if p.market_value else float(p.total_cost)
            total_value += value

            # 资产类型
            asset_type = p.asset_type or 'unknown'
            if asset_type not in by_type:
                by_type[asset_type] = {'count': 0, 'value': 0}
            by_type[asset_type]['count'] += 1
            by_type[asset_type]['value'] += value

            # 分类
            category = p.category or '未分类'
            if category not in by_category:
                by_category[category] = {'count': 0, 'value': 0}
            by_category[category]['count'] += 1
            by_category[category]['value'] += value

        # 计算百分比
        for key in by_type:
            by_type[key]['percentage'] = round(by_type[key]['value'] / total_value * 100, 2) if total_value > 0 else 0

        for key in by_category:
            by_category[key]['percentage'] = round(by_category[key]['value'] / total_value * 100, 2) if total_value > 0 else 0

        return success_response({
            'by_type': by_type,
            'by_category': by_category,
            'total_value': total_value
        })
    except Exception as e:
        return error_response(str(e))


@charts_bp.route('/charts/profit-distribution', methods=['GET'])
@login_required
def get_profit_distribution():
    """获取收益分布数据（按持仓）"""
    try:
        user = get_current_user()
        account_id = request.args.get('account_id', type=int)

        query = Position.query.filter_by(user_id=user.id)
        if account_id:
            query = query.filter_by(account_id=account_id)

        positions = query.all()

        # 按收益率分组
        distribution = {
            'high_profit': [],      # >20%
            'profit': [],           # 0-20%
            'loss': [],             # -20%-0
            'high_loss': []         # <-20%
        }

        for p in positions:
            if p.profit_rate is None:
                continue

            profit_rate = float(p.profit_rate)
            item = {
                'symbol': p.symbol,
                'name': p.name,
                'profit_rate': profit_rate,
                'market_value': float(p.market_value) if p.market_value else float(p.total_cost)
            }

            if profit_rate >= 0.2:
                distribution['high_profit'].append(item)
            elif profit_rate >= 0:
                distribution['profit'].append(item)
            elif profit_rate >= -0.2:
                distribution['loss'].append(item)
            else:
                distribution['high_loss'].append(item)

        return success_response(distribution)
    except Exception as e:
        return error_response(str(e))


@charts_bp.route('/charts/trade-summary', methods=['GET'])
@login_required
def get_trade_summary():
    """获取交易汇总统计"""
    try:
        user = get_current_user()
        account_id = request.args.get('account_id', type=int)

        # 按月份统计
        monthly = db.session.query(
            func.date_format(Trade.trade_date, '%Y-%m').label('month'),
            Trade.trade_type,
            func.sum(Trade.amount).label('total_amount'),
            func.count(Trade.id).label('count')
        ).filter(Trade.user_id == user.id)

        if account_id:
            monthly = monthly.filter(Trade.account_id == account_id)

        monthly = monthly.group_by('month', Trade.trade_type).order_by('month').all()

        monthly_data = {}
        for m in monthly:
            if m.month not in monthly_data:
                monthly_data[m.month] = {'buy': 0, 'sell': 0, 'buy_count': 0, 'sell_count': 0}

            if m.trade_type == 'buy':
                monthly_data[m.month]['buy'] = float(m.total_amount)
                monthly_data[m.month]['buy_count'] = m.count
            else:
                monthly_data[m.month]['sell'] = float(m.total_amount)
                monthly_data[m.month]['sell_count'] = m.count

        return success_response({
            'monthly': monthly_data
        })
    except Exception as e:
        return error_response(str(e))