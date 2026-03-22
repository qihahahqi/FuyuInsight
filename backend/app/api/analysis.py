#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收益分析 API
"""

from flask import Blueprint, request
from .. import db
from ..models import Position, Trade
from ..utils import success_response, error_response
from ..utils.decorators import login_required, get_current_user
from ..services import ProfitService

analysis_bp = Blueprint('analysis', __name__)
profit_service = ProfitService()


@analysis_bp.route('/analysis/profit', methods=['GET'])
@login_required
def get_profit_analysis():
    """获取收益分析"""
    try:
        user = get_current_user()
        positions = Position.query.filter_by(user_id=user.id).all()

        positions_data = [p.to_dict() for p in positions]
        summary = profit_service.portfolio_summary(positions_data)

        # 添加信号详情
        signals = []
        for p in positions:
            if p.current_price:
                result = profit_service.calculate_profit(
                    p.cost_price,
                    p.current_price,
                    p.quantity
                )
                if result['stop_profit_signal'] or result['add_position_signal']:
                    signals.append({
                        'symbol': p.symbol,
                        'name': p.name,
                        **result
                    })

        summary['signals'] = signals

        return success_response(summary)
    except Exception as e:
        return error_response(str(e))


@analysis_bp.route('/analysis/risk', methods=['GET'])
@login_required
def get_risk_analysis():
    """获取风险分析"""
    try:
        user = get_current_user()
        positions = Position.query.filter_by(user_id=user.id).all()

        if not positions:
            return success_response({
                'max_drawdown': 0,
                'volatility': 0,
                'sharpe_ratio': 0,
                'message': '暂无持仓数据'
            })

        # 计算各持仓的风险指标
        risks = []
        for p in positions:
            if p.current_price and p.cost_price:
                profit_rate = float(p.profit_rate) if p.profit_rate else 0
                risks.append({
                    'symbol': p.symbol,
                    'name': p.name,
                    'profit_rate': profit_rate,
                    'risk_level': _get_risk_level(profit_rate)
                })

        # 计算组合最大回撤（简化：使用当前浮亏作为参考）
        total_cost = sum(float(p.total_cost) for p in positions)
        total_value = sum(float(p.market_value) for p in positions if p.market_value)
        portfolio_profit_rate = (total_value - total_cost) / total_cost if total_cost > 0 else 0

        return success_response({
            'portfolio_profit_rate': portfolio_profit_rate,
            'total_cost': total_cost,
            'total_value': total_value,
            'position_risks': risks,
            'risk_summary': {
                'profit_positions': len([r for r in risks if r['profit_rate'] > 0]),
                'loss_positions': len([r for r in risks if r['profit_rate'] < 0]),
                'high_risk_positions': len([r for r in risks if r['risk_level'] == '高风险'])
            }
        })
    except Exception as e:
        return error_response(str(e))


@analysis_bp.route('/analysis/signals', methods=['GET'])
@login_required
def get_signals():
    """获取所有操作信号"""
    try:
        user = get_current_user()
        positions = Position.query.filter_by(user_id=user.id).all()

        stop_profit_signals = []
        add_position_signals = []

        for p in positions:
            if not p.current_price:
                continue

            result = profit_service.calculate_profit(
                p.cost_price,
                p.current_price,
                p.quantity
            )

            signal_data = {
                'position_id': p.id,
                'symbol': p.symbol,
                'name': p.name,
                'quantity': p.quantity,
                'cost_price': float(p.cost_price),
                'current_price': float(p.current_price),
                'profit_rate': result['profit_rate'],
                'signal_level': result['signal_level'],
                'suggestion': result['suggestion']
            }

            if result['stop_profit_signal']:
                stop_profit_signals.append(signal_data)

            if result['add_position_signal']:
                add_position_signals.append(signal_data)

        return success_response({
            'stop_profit_signals': stop_profit_signals,
            'add_position_signals': add_position_signals,
            'total_stop_profit': len(stop_profit_signals),
            'total_add_position': len(add_position_signals)
        })
    except Exception as e:
        return error_response(str(e))


@analysis_bp.route('/analysis/distribution', methods=['GET'])
@login_required
def get_distribution():
    """获取持仓分布"""
    try:
        user = get_current_user()
        positions = Position.query.filter_by(user_id=user.id).all()

        # 按资产类型分布
        by_type = {}
        # 按分类分布
        by_category = {}
        # 按收益率分布
        by_profit = {
            'high_profit': [],  # >20%
            'profit': [],       # 0-20%
            'loss': [],         # -20%-0
            'high_loss': []     # <-20%
        }

        total_value = 0
        for p in positions:
            value = float(p.market_value) if p.market_value else float(p.total_cost)
            total_value += value

            # 按资产类型
            asset_type = p.asset_type or 'unknown'
            if asset_type not in by_type:
                by_type[asset_type] = {'count': 0, 'value': 0}
            by_type[asset_type]['count'] += 1
            by_type[asset_type]['value'] += value

            # 按分类
            category = p.category or '未分类'
            if category not in by_category:
                by_category[category] = {'count': 0, 'value': 0}
            by_category[category]['count'] += 1
            by_category[category]['value'] += value

            # 按收益率
            if p.profit_rate:
                profit_rate = float(p.profit_rate)
                item = {'symbol': p.symbol, 'name': p.name, 'profit_rate': profit_rate}
                if profit_rate >= 0.2:
                    by_profit['high_profit'].append(item)
                elif profit_rate >= 0:
                    by_profit['profit'].append(item)
                elif profit_rate >= -0.2:
                    by_profit['loss'].append(item)
                else:
                    by_profit['high_loss'].append(item)

        # 计算百分比
        for key in by_type:
            by_type[key]['percentage'] = round(by_type[key]['value'] / total_value * 100, 2) if total_value > 0 else 0

        for key in by_category:
            by_category[key]['percentage'] = round(by_category[key]['value'] / total_value * 100, 2) if total_value > 0 else 0

        return success_response({
            'total_value': total_value,
            'by_type': by_type,
            'by_category': by_category,
            'by_profit': by_profit
        })
    except Exception as e:
        return error_response(str(e))


def _get_risk_level(profit_rate: float) -> str:
    """判断风险等级"""
    if profit_rate >= 0.2:
        return '低风险（盈利）'
    elif profit_rate >= 0:
        return '正常'
    elif profit_rate >= -0.15:
        return '轻度风险'
    elif profit_rate >= -0.25:
        return '中度风险'
    else:
        return '高风险'