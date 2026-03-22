#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理后台 API
"""

from flask import Blueprint, request
from .. import db
from ..models import User, Position, Trade, Account
from ..utils import success_response, error_response
from ..utils.decorators import admin_required, get_current_user
from datetime import datetime

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    """获取所有用户列表"""
    try:
        users = User.query.order_by(User.created_at.desc()).all()

        users_data = []
        for u in users:
            # 统计用户数据
            position_count = Position.query.filter_by(user_id=u.id).count()
            trade_count = Trade.query.filter_by(user_id=u.id).count()
            account_count = Account.query.filter_by(user_id=u.id).count()

            users_data.append({
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'is_active': u.is_active,
                'is_admin': u.is_admin,
                'last_login': u.last_login.isoformat() if u.last_login else None,
                'created_at': u.created_at.isoformat() if u.created_at else None,
                'position_count': position_count,
                'trade_count': trade_count,
                'account_count': account_count
            })

        return success_response(users_data)
    except Exception as e:
        return error_response(str(e))


@admin_bp.route('/admin/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """更新用户状态"""
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response("用户不存在", 404)

        data = request.get_json()

        # 不能禁用自己
        current_user = get_current_user()
        if user.id == current_user.id and data.get('is_active') == False:
            return error_response("不能禁用自己的账户")

        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'is_admin' in data:
            # 不能取消自己的管理员权限
            if user.id == current_user.id and not data['is_admin']:
                return error_response("不能取消自己的管理员权限")
            user.is_admin = data['is_admin']

        db.session.commit()

        return success_response(user.to_dict(), "用户更新成功")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@admin_bp.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    """重置用户密码"""
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response("用户不存在", 404)

        data = request.get_json()
        new_password = data.get('new_password', '123456')  # 默认重置为 123456

        user.set_password(new_password)
        db.session.commit()

        return success_response(None, f"密码已重置为: {new_password}")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@admin_bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """删除用户"""
    try:
        from ..models import Valuation, CashPool, Config, PortfolioSnapshot, PriceHistory

        current_user = get_current_user()

        # 不能删除自己
        if user_id == current_user.id:
            return error_response("不能删除自己的账户")

        user = User.query.get(user_id)
        if not user:
            return error_response("用户不存在", 404)

        # 删除用户的所有相关数据
        Position.query.filter_by(user_id=user_id).delete()
        Trade.query.filter_by(user_id=user_id).delete()
        Account.query.filter_by(user_id=user_id).delete()
        Valuation.query.filter_by(user_id=user_id).delete()
        CashPool.query.filter_by(user_id=user_id).delete()
        Config.query.filter_by(user_id=user_id).delete()
        PortfolioSnapshot.query.filter_by(user_id=user_id).delete()
        PriceHistory.query.filter_by(user_id=user_id).delete()

        # 删除用户
        db.session.delete(user)
        db.session.commit()

        return success_response(None, "用户及其所有数据已删除")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@admin_bp.route('/admin/positions', methods=['GET'])
@admin_required
def get_all_positions():
    """获取所有用户的持仓"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        user_id = request.args.get('user_id', type=int)

        query = Position.query

        if user_id:
            query = query.filter_by(user_id=user_id)

        pagination = query.order_by(Position.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        positions_data = []
        for p in pagination.items:
            p_dict = p.to_dict()
            # 添加用户信息
            user = User.query.get(p.user_id)
            p_dict['username'] = user.username if user else 'Unknown'
            positions_data.append(p_dict)

        return success_response({
            'items': positions_data,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return error_response(str(e))


@admin_bp.route('/admin/positions/<int:position_id>', methods=['GET'])
@admin_required
def get_position(position_id):
    """获取单个持仓详情"""
    try:
        position = Position.query.get(position_id)
        if not position:
            return error_response("持仓不存在", 404)

        p_dict = position.to_dict()
        user = User.query.get(position.user_id)
        p_dict['username'] = user.username if user else 'Unknown'

        return success_response(p_dict)
    except Exception as e:
        return error_response(str(e))


@admin_bp.route('/admin/positions', methods=['POST'])
@admin_required
def create_position():
    """管理员创建持仓"""
    try:
        data = request.get_json()

        # 验证必需字段
        required_fields = ['user_id', 'symbol', 'name', 'quantity', 'cost_price']
        for field in required_fields:
            if not data.get(field):
                return error_response(f"缺少必需字段: {field}")

        # 验证用户是否存在
        user = User.query.get(data['user_id'])
        if not user:
            return error_response("用户不存在")

        # 创建持仓
        position = Position(
            user_id=data['user_id'],
            symbol=data['symbol'],
            name=data['name'],
            asset_type=data.get('asset_type', 'etf_index'),
            quantity=int(data['quantity']),
            cost_price=float(data['cost_price']),
            current_price=float(data['current_price']) if data.get('current_price') else None,
            total_cost=int(data['quantity']) * float(data['cost_price']),
            category=data.get('category'),
            notes=data.get('notes')
        )

        # 计算市值和收益率
        if position.current_price:
            position.market_value = position.quantity * position.current_price
            if position.total_cost > 0:
                position.profit_rate = (position.market_value - position.total_cost) / position.total_cost

        db.session.add(position)
        db.session.commit()

        return success_response(position.to_dict(), "持仓创建成功")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@admin_bp.route('/admin/positions/<int:position_id>', methods=['PUT'])
@admin_required
def update_position(position_id):
    """管理员更新持仓"""
    try:
        position = Position.query.get(position_id)
        if not position:
            return error_response("持仓不存在", 404)

        data = request.get_json()

        # 更新字段
        if 'user_id' in data:
            user = User.query.get(data['user_id'])
            if not user:
                return error_response("用户不存在")
            position.user_id = data['user_id']

        if 'symbol' in data:
            position.symbol = data['symbol']
        if 'name' in data:
            position.name = data['name']
        if 'asset_type' in data:
            position.asset_type = data['asset_type']
        if 'quantity' in data:
            position.quantity = int(data['quantity'])
        if 'cost_price' in data:
            position.cost_price = float(data['cost_price'])
        if 'current_price' in data:
            position.current_price = float(data['current_price']) if data['current_price'] else None
        if 'category' in data:
            position.category = data['category']
        if 'notes' in data:
            position.notes = data['notes']

        # 重新计算
        position.total_cost = position.quantity * float(position.cost_price)
        if position.current_price:
            position.market_value = position.quantity * position.current_price
            if position.total_cost > 0:
                position.profit_rate = (position.market_value - position.total_cost) / position.total_cost
        else:
            position.market_value = None
            position.profit_rate = None

        db.session.commit()

        return success_response(position.to_dict(), "持仓更新成功")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@admin_bp.route('/admin/positions/<int:position_id>', methods=['DELETE'])
@admin_required
def delete_position(position_id):
    """管理员删除持仓"""
    try:
        position = Position.query.get(position_id)
        if not position:
            return error_response("持仓不存在", 404)

        db.session.delete(position)
        db.session.commit()

        return success_response(None, "持仓已删除")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@admin_bp.route('/admin/trades', methods=['GET'])
@admin_required
def get_all_trades():
    """获取所有用户的交易记录"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        user_id = request.args.get('user_id', type=int)

        query = Trade.query

        if user_id:
            query = query.filter_by(user_id=user_id)

        pagination = query.order_by(Trade.trade_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        trades_data = []
        for t in pagination.items:
            t_dict = t.to_dict()
            # 添加用户信息
            user = User.query.get(t.user_id)
            t_dict['username'] = user.username if user else 'Unknown'
            trades_data.append(t_dict)

        return success_response({
            'items': trades_data,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return error_response(str(e))


@admin_bp.route('/admin/accounts', methods=['GET'])
@admin_required
def get_all_accounts():
    """获取所有用户的投资账户"""
    try:
        user_id = request.args.get('user_id', type=int)

        query = Account.query

        if user_id:
            query = query.filter_by(user_id=user_id)

        accounts = query.order_by(Account.created_at.desc()).all()

        accounts_data = []
        for a in accounts:
            a_dict = a.to_dict()
            # 添加用户信息
            user = User.query.get(a.user_id)
            a_dict['username'] = user.username if user else 'Unknown'
            accounts_data.append(a_dict)

        return success_response(accounts_data)
    except Exception as e:
        return error_response(str(e))


@admin_bp.route('/admin/statistics', methods=['GET'])
@admin_required
def get_statistics():
    """获取系统统计信息"""
    try:
        from sqlalchemy import func

        # 用户统计
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        admin_users = User.query.filter_by(is_admin=True).count()

        # 数据统计
        total_positions = Position.query.count()
        total_trades = Trade.query.count()
        total_accounts = Account.query.count()

        # 按日期统计新用户（最近7天）
        from datetime import date, timedelta
        daily_new_users = []
        for i in range(7):
            d = date.today() - timedelta(days=i)
            count = User.query.filter(
                db.func.date(User.created_at) == d
            ).count()
            daily_new_users.append({
                'date': d.isoformat(),
                'count': count
            })

        return success_response({
            'users': {
                'total': total_users,
                'active': active_users,
                'admins': admin_users
            },
            'data': {
                'positions': total_positions,
                'trades': total_trades,
                'accounts': total_accounts
            },
            'daily_new_users': daily_new_users
        })
    except Exception as e:
        return error_response(str(e))