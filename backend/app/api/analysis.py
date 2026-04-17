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
    """获取收益分析（只针对未清仓的持仓）"""
    try:
        user = get_current_user()
        # 只查询未清仓的持仓（数量大于0）
        positions = Position.query.filter_by(user_id=user.id).filter(Position.quantity > 0).all()

        # 构建带交易记录的持仓数据
        positions_data = []
        for p in positions:
            # 获取卖出交易记录，计算原始持仓数量
            sells = Trade.query.filter_by(
                user_id=user.id,
                symbol=p.symbol,
                trade_type='sell'
            ).order_by(Trade.trade_date).all()

            # 获取买入交易记录
            buys = Trade.query.filter_by(
                user_id=user.id,
                symbol=p.symbol,
                trade_type='buy'
            ).order_by(Trade.trade_date).all()

            # 计算原始持仓数量 = 当前数量 + 已卖出数量
            total_sold = sum(t.quantity for t in sells)
            original_quantity = p.quantity + total_sold

            # 构建卖出记录列表
            sell_records = [{'date': t.trade_date, 'quantity': t.quantity} for t in sells]

            pos_data = p.to_dict()
            pos_data['original_quantity'] = original_quantity
            pos_data['sell_records'] = sell_records
            pos_data['add_position_ratio'] = float(p.add_position_ratio) if p.add_position_ratio else 0
            positions_data.append(pos_data)

        summary = profit_service.portfolio_summary(positions_data)

        # 添加信号详情（每个持仓的详细信息）
        details = []
        for i, p in enumerate(positions):
            if p.current_price:
                pos_data = positions_data[i]
                result = profit_service.calculate_profit(
                    p.cost_price,
                    p.current_price,
                    p.quantity,
                    original_quantity=pos_data['original_quantity'],
                    sell_records=pos_data['sell_records'],
                    add_position_ratio=pos_data['add_position_ratio']
                )
                details.append({
                    'position': {
                        'id': p.id,
                        'symbol': p.symbol,
                        'name': p.name,
                        'asset_type': p.asset_type
                    },
                    **result
                })

        summary['details'] = details
        summary['signals'] = [d for d in details if d['stop_profit_signal'] or d['add_position_signal']]

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
    """获取所有持仓状态（智能止盈策略，根据实际交易记录判断）
    返回所有持仓的收益率、已加仓、已减仓信息，有操作建议时显示建议
    """
    try:
        user = get_current_user()
        # 只查询未清仓的持仓（数量大于0）
        positions = Position.query.filter_by(user_id=user.id).filter(Position.quantity > 0).all()

        all_positions_data = []
        stop_profit_signals = []
        add_position_signals = []

        for p in positions:
            if not p.current_price:
                continue

            # 获取该持仓的所有交易记录（买入和卖出）
            all_trades = Trade.query.filter_by(
                user_id=user.id,
                symbol=p.symbol
            ).order_by(Trade.trade_date.desc()).limit(5).all()

            # 获取卖出交易记录，计算原始持仓数量
            sells = Trade.query.filter_by(
                user_id=user.id,
                symbol=p.symbol,
                trade_type='sell'
            ).order_by(Trade.trade_date).all()

            # 获取买入交易记录，计算加仓情况
            buys = Trade.query.filter_by(
                user_id=user.id,
                symbol=p.symbol,
                trade_type='buy'
            ).order_by(Trade.trade_date).all()

            # 计算原始持仓数量 = 当前数量 + 已卖出数量
            total_sold = sum(t.quantity for t in sells)
            original_quantity = p.quantity + total_sold

            # 构建卖出记录列表
            sell_records = [{'date': t.trade_date, 'quantity': t.quantity} for t in sells]

            # 构建交易记录列表（用于前端显示）
            trade_records = [{
                'date': t.trade_date.isoformat(),
                'type': t.trade_type,
                'quantity': t.quantity,
                'price': float(t.price),
                'amount': float(t.amount),
                'reason': t.reason
            } for t in all_trades]

            # 传入实际数据，智能判断（传入持仓数量用于计算建议份额）
            result = profit_service.calculate_profit(
                p.cost_price,
                p.current_price,
                p.quantity,
                original_quantity=original_quantity,
                sell_records=sell_records,
                add_position_ratio=float(p.add_position_ratio) if p.add_position_ratio else 0
            )

            signal_data = {
                'position_id': p.id,
                'symbol': p.symbol,
                'name': p.name,
                'asset_type': p.asset_type,
                'quantity': p.quantity,
                'original_quantity': original_quantity,
                'cost_price': float(p.cost_price),
                'current_price': float(p.current_price),
                'profit_rate': result['profit_rate'],
                'profit_amount': result['profit_amount'],  # 从计算结果获取
                'signal_level': result['signal_level'],
                'suggestion': result['suggestion'],
                'suggestion_quantity': result.get('suggestion_quantity', 0),  # 建议操作份额
                'suggestion_amount': result.get('suggestion_amount', 0),  # 建议操作金额
                'current_state': result.get('current_state', {}),
                'sold_ratio': result.get('current_state', {}).get('sold_ratio', 0),
                'add_position_ratio': result.get('current_state', {}).get('add_position_ratio', 0),
                'trade_records': trade_records,  # 最近交易记录
                'total_sold': total_sold,
                'total_bought': sum(t.quantity for t in buys),
                'stop_profit_signal': result['stop_profit_signal'],
                'add_position_signal': result['add_position_signal']
            }

            # 所有持仓都加入列表
            all_positions_data.append(signal_data)

            # 有信号的单独归类
            if result['stop_profit_signal']:
                stop_profit_signals.append(signal_data)

            if result['add_position_signal']:
                add_position_signals.append(signal_data)

        return success_response({
            'all_positions': all_positions_data,  # 所有持仓的状态信息
            'stop_profit_signals': stop_profit_signals,  # 有止盈信号的
            'add_position_signals': add_position_signals,  # 有加仓信号的
            'total_positions': len(all_positions_data),
            'total_stop_profit': len(stop_profit_signals),
            'total_add_position': len(add_position_signals)
        })
    except Exception as e:
        return error_response(str(e))


@analysis_bp.route('/analysis/distribution', methods=['GET'])
@login_required
def get_distribution():
    """获取持仓分布（只针对未清仓的持仓）"""
    try:
        user = get_current_user()
        # 只查询未清仓的持仓（数量大于0）
        positions = Position.query.filter_by(user_id=user.id).filter(Position.quantity > 0).all()

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