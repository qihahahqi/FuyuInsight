#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
账户管理 API
"""

from flask import Blueprint, request
from .. import db
from ..models import Account, Position
from ..utils import success_response, error_response
from ..utils.decorators import login_required, get_current_user
from datetime import datetime

accounts_bp = Blueprint('accounts', __name__)


@accounts_bp.route('/accounts', methods=['GET'])
@login_required
def get_accounts():
    """获取账户列表"""
    try:
        user = get_current_user()
        accounts = Account.query.filter_by(user_id=user.id, is_active=True).all()
        result = []

        for acc in accounts:
            # 计算账户汇总
            positions = Position.query.filter_by(user_id=user.id, account_id=acc.id).all()
            total_cost = sum(float(p.total_cost) for p in positions)
            market_value = sum(float(p.market_value) for p in positions if p.market_value) or total_cost
            profit_rate = (market_value - total_cost) / total_cost if total_cost > 0 else 0

            acc_dict = acc.to_dict()
            acc_dict['summary'] = {
                'position_count': len(positions),
                'total_cost': total_cost,
                'market_value': market_value,
                'profit_rate': profit_rate
            }
            result.append(acc_dict)

        return success_response(result)
    except Exception as e:
        return error_response(str(e))


@accounts_bp.route('/accounts/<int:account_id>', methods=['GET'])
@login_required
def get_account(account_id):
    """获取单个账户"""
    try:
        user = get_current_user()
        account = Account.query.filter_by(id=account_id, user_id=user.id).first()
        if not account:
            return error_response("账户不存在", 404)
        return success_response(account.to_dict())
    except Exception as e:
        return error_response(str(e))


@accounts_bp.route('/accounts', methods=['POST'])
@login_required
def create_account():
    """创建账户"""
    try:
        user = get_current_user()
        data = request.get_json()

        if not data.get('name'):
            return error_response("账户名称不能为空")

        account = Account(
            user_id=user.id,
            name=data['name'],
            account_type=data.get('account_type', 'personal'),
            broker=data.get('broker'),
            description=data.get('description'),
            is_active=data.get('is_active', True)
        )

        db.session.add(account)
        db.session.commit()

        return success_response(account.to_dict(), "账户创建成功")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@accounts_bp.route('/accounts/<int:account_id>', methods=['PUT'])
@login_required
def update_account(account_id):
    """更新账户"""
    try:
        user = get_current_user()
        account = Account.query.filter_by(id=account_id, user_id=user.id).first()
        if not account:
            return error_response("账户不存在", 404)

        data = request.get_json()

        if 'name' in data:
            account.name = data['name']
        if 'account_type' in data:
            account.account_type = data['account_type']
        if 'broker' in data:
            account.broker = data['broker']
        if 'description' in data:
            account.description = data['description']
        if 'is_active' in data:
            account.is_active = data['is_active']

        db.session.commit()
        return success_response(account.to_dict(), "账户更新成功")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@accounts_bp.route('/accounts/<int:account_id>', methods=['DELETE'])
@login_required
def delete_account(account_id):
    """删除账户（软删除）"""
    try:
        user = get_current_user()
        account = Account.query.filter_by(id=account_id, user_id=user.id).first()
        if not account:
            return error_response("账户不存在", 404)

        # 检查是否有持仓
        position_count = Position.query.filter_by(user_id=user.id, account_id=account_id).count()
        if position_count > 0:
            return error_response(f"该账户下还有 {position_count} 个持仓，无法删除")

        account.is_active = False
        db.session.commit()

        return success_response(None, "账户已禁用")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@accounts_bp.route('/accounts/<int:account_id>/summary', methods=['GET'])
@login_required
def get_account_summary(account_id):
    """获取账户汇总"""
    try:
        user = get_current_user()
        account = Account.query.filter_by(id=account_id, user_id=user.id).first()
        if not account:
            return error_response("账户不存在", 404)

        positions = Position.query.filter_by(user_id=user.id, account_id=account_id).all()

        total_cost = sum(float(p.total_cost) for p in positions)
        market_value = sum(float(p.market_value) for p in positions if p.market_value) or total_cost
        total_profit = market_value - total_cost
        profit_rate = (market_value - total_cost) / total_cost if total_cost > 0 else 0

        # 按资产类型分组
        by_type = {}
        for p in positions:
            asset_type = p.asset_type
            if asset_type not in by_type:
                by_type[asset_type] = {'count': 0, 'value': 0}
            by_type[asset_type]['count'] += 1
            by_type[asset_type]['value'] += float(p.market_value) if p.market_value else float(p.total_cost)

        return success_response({
            'account': account.to_dict(),
            'position_count': len(positions),
            'total_cost': total_cost,
            'market_value': market_value,
            'total_profit': total_profit,
            'profit_rate': profit_rate,
            'by_type': by_type
        })
    except Exception as e:
        return error_response(str(e))