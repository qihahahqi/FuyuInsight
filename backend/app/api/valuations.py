#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
估值判断 API
"""

from flask import Blueprint, request
from .. import db
from ..models import Valuation
from ..utils import success_response, error_response
from ..utils.decorators import login_required, get_current_user
from ..services import ValuationService

valuations_bp = Blueprint('valuations', __name__)
valuation_service = ValuationService()


@valuations_bp.route('/valuations', methods=['GET'])
@login_required
def get_valuations():
    """获取估值数据"""
    try:
        user = get_current_user()
        symbol = request.args.get('symbol')

        query = Valuation.query.filter_by(user_id=user.id)

        if symbol:
            query = query.filter_by(symbol=symbol)

        # 获取最新记录
        valuations = query.order_by(Valuation.record_date.desc()).limit(100).all()

        return success_response([v.to_dict() for v in valuations])
    except Exception as e:
        return error_response(str(e))


@valuations_bp.route('/valuations', methods=['POST'])
@login_required
def create_valuation():
    """录入估值数据"""
    try:
        user = get_current_user()
        data = request.get_json()

        # 验证必填字段
        required = ['symbol', 'index_name', 'record_date']
        for field in required:
            if field not in data:
                return error_response(f"缺少必填字段: {field}")

        from datetime import datetime

        valuation = Valuation(
            user_id=user.id,
            symbol=data['symbol'],
            index_name=data['index_name'],
            pe=data.get('pe'),
            pb=data.get('pb'),
            pe_percentile=data.get('pe_percentile'),
            pb_percentile=data.get('pb_percentile'),
            rsi=data.get('rsi'),
            roe=data.get('roe'),
            dividend_yield=data.get('dividend_yield'),
            record_date=datetime.strptime(data['record_date'], '%Y-%m-%d').date()
        )

        # 自动评估
        result = valuation_service.evaluate(
            index_name=data['index_name'],
            pe=data.get('pe'),
            pb=data.get('pb'),
            pe_percentile=data.get('pe_percentile'),
            pb_percentile=data.get('pb_percentile'),
            rsi=data.get('rsi')
        )

        valuation.level = result.level.value
        valuation.score = result.score
        valuation.suggestion = result.action

        db.session.add(valuation)
        db.session.commit()

        return success_response({
            'valuation': valuation.to_dict(),
            'analysis': {
                'level': result.level.value,
                'score': result.score,
                'position_suggestion': result.position_suggestion,
                'action': result.action,
                'details': result.details
            }
        }, "估值数据录入成功")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@valuations_bp.route('/valuations/evaluate', methods=['POST'])
@login_required
def evaluate_valuation():
    """估值评估（不保存）"""
    try:
        data = request.get_json()

        result = valuation_service.evaluate(
            index_name=data.get('index_name', ''),
            pe=data.get('pe'),
            pb=data.get('pb'),
            pe_percentile=data.get('pe_percentile'),
            pb_percentile=data.get('pb_percentile'),
            rsi=data.get('rsi')
        )

        return success_response({
            'level': result.level.value,
            'score': result.score,
            'position_suggestion': result.position_suggestion,
            'action': result.action,
            'details': result.details
        })
    except Exception as e:
        return error_response(str(e))


@valuations_bp.route('/valuations/reference', methods=['GET'])
@login_required
def get_reference():
    """获取所有指数估值参考"""
    try:
        indices = valuation_service.list_supported_indices()
        reference = {}

        for index_name in indices:
            ref = valuation_service.get_index_reference(index_name)
            if ref:
                reference[index_name] = ref

        return success_response({
            'indices': indices,
            'reference': reference
        })
    except Exception as e:
        return error_response(str(e))


@valuations_bp.route('/valuations/reference/<index_name>', methods=['GET'])
@login_required
def get_index_reference(index_name):
    """获取单个指数估值参考"""
    try:
        ref = valuation_service.get_index_reference(index_name)
        if not ref:
            return error_response(f"不支持的指数: {index_name}", 404)

        return success_response({
            'index_name': index_name,
            'reference': ref
        })
    except Exception as e:
        return error_response(str(e))


@valuations_bp.route('/valuations/<int:valuation_id>', methods=['DELETE'])
@login_required
def delete_valuation(valuation_id):
    """删除估值记录"""
    try:
        user = get_current_user()
        valuation = Valuation.query.filter_by(id=valuation_id, user_id=user.id).first()
        if not valuation:
            return error_response("估值记录不存在", 404)

        db.session.delete(valuation)
        db.session.commit()
        return success_response(None, "估值记录删除成功")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))