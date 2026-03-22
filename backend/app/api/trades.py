#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易记录 API
"""

from flask import Blueprint, request
from .. import db
from ..models import Position, Trade
from ..utils import success_response, error_response
from ..utils.decorators import login_required, get_current_user
from datetime import datetime

trades_bp = Blueprint('trades', __name__)


@trades_bp.route('/trades', methods=['GET'])
@login_required
def get_trades():
    """获取交易记录"""
    try:
        user = get_current_user()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        symbol = request.args.get('symbol')

        query = Trade.query.filter_by(user_id=user.id)

        if symbol:
            query = query.filter_by(symbol=symbol)

        pagination = query.order_by(Trade.trade_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        trades = [t.to_dict() for t in pagination.items]

        return success_response({
            'items': trades,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return error_response(str(e))


@trades_bp.route('/trades', methods=['POST'])
@login_required
def create_trade():
    """创建交易记录"""
    try:
        user = get_current_user()
        data = request.get_json()

        # 验证必填字段
        required = ['symbol', 'trade_type', 'quantity', 'price', 'trade_date']
        for field in required:
            if field not in data:
                return error_response(f"缺少必填字段: {field}")

        # 验证交易类型
        if data['trade_type'] not in ['buy', 'sell']:
            return error_response("交易类型必须是 buy 或 sell")

        quantity = int(data['quantity'])
        price = float(data['price'])
        amount = quantity * price

        # 查找关联的持仓
        position = Position.query.filter_by(user_id=user.id, symbol=data['symbol']).first()

        trade = Trade(
            user_id=user.id,
            position_id=position.id if position else None,
            symbol=data['symbol'],
            trade_type=data['trade_type'],
            quantity=quantity,
            price=price,
            amount=amount,
            trade_date=datetime.strptime(data['trade_date'], '%Y-%m-%d').date(),
            reason=data.get('reason'),
            signal_type=data.get('signal_type'),
            notes=data.get('notes')
        )

        db.session.add(trade)

        # 更新持仓
        if position:
            if data['trade_type'] == 'buy':
                # 买入：更新成本价
                total_cost = float(position.total_cost) + amount
                total_quantity = position.quantity + quantity
                position.cost_price = total_cost / total_quantity
                position.quantity = total_quantity
                position.total_cost = total_cost
            else:
                # 卖出：减少数量
                position.quantity -= quantity
                position.total_cost = float(position.total_cost) - float(position.cost_price) * quantity

        db.session.commit()

        return success_response(trade.to_dict(), "交易记录创建成功")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@trades_bp.route('/trades/<int:trade_id>', methods=['GET'])
@login_required
def get_trade(trade_id):
    """获取单个交易记录"""
    try:
        user = get_current_user()
        trade = Trade.query.filter_by(id=trade_id, user_id=user.id).first()
        if not trade:
            return error_response("交易记录不存在", 404)
        return success_response(trade.to_dict())
    except Exception as e:
        return error_response(str(e))


@trades_bp.route('/trades/<int:trade_id>', methods=['DELETE'])
@login_required
def delete_trade(trade_id):
    """删除交易记录"""
    try:
        user = get_current_user()
        trade = Trade.query.filter_by(id=trade_id, user_id=user.id).first()
        if not trade:
            return error_response("交易记录不存在", 404)

        db.session.delete(trade)
        db.session.commit()
        return success_response(None, "交易记录删除成功")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@trades_bp.route('/trades/statistics', methods=['GET'])
@login_required
def get_trade_statistics():
    """获取交易统计"""
    try:
        user = get_current_user()
        from sqlalchemy import func

        # 总交易次数
        total_trades = Trade.query.filter_by(user_id=user.id).count()

        # 买入/卖出次数
        buy_count = Trade.query.filter_by(user_id=user.id, trade_type='buy').count()
        sell_count = Trade.query.filter_by(user_id=user.id, trade_type='sell').count()

        # 总交易金额
        buy_amount = db.session.query(func.sum(Trade.amount)).filter_by(user_id=user.id, trade_type='buy').scalar() or 0
        sell_amount = db.session.query(func.sum(Trade.amount)).filter_by(user_id=user.id, trade_type='sell').scalar() or 0

        # 按标的统计
        by_symbol = db.session.query(
            Trade.symbol,
            func.count(Trade.id).label('count'),
            func.sum(Trade.amount).label('total_amount')
        ).filter_by(user_id=user.id).group_by(Trade.symbol).all()

        by_symbol_data = [{
            'symbol': s,
            'count': c,
            'total_amount': float(t) if t else 0
        } for s, c, t in by_symbol]

        return success_response({
            'total_trades': total_trades,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'buy_amount': float(buy_amount),
            'sell_amount': float(sell_amount),
            'by_symbol': by_symbol_data
        })
    except Exception as e:
        return error_response(str(e))