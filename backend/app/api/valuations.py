#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
估值判断 API
"""

from flask import Blueprint, request, send_file
from io import BytesIO
from .. import db
from ..models import Valuation
from ..utils import success_response, error_response
from ..utils.decorators import login_required, get_current_user
from ..services import ValuationService
from datetime import datetime
import pandas as pd

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


@valuations_bp.route('/valuations/template', methods=['GET'])
@login_required
def download_template():
    """下载估值数据导入模板"""
    try:
        # 创建模板数据
        template_data = {
            'record_date': ['2024-01-15', '2024-01-15', '2024-01-15'],
            'symbol': ['000001', '000300', '399006'],
            'index_name': ['上证指数', '沪深300', '创业板指'],
            'pe': [13.5, 11.8, 28.5],
            'pb': [1.25, 1.35, 4.2],
            'pe_percentile': [45.5, 38.2, 65.8],
            'pb_percentile': [42.1, 35.5, 72.3],
            'rsi': [55.5, 48.2, 62.1],
            'roe': [10.5, 12.3, 8.5],
            'dividend_yield': [2.5, 2.8, 0.8]
        }

        df = pd.DataFrame(template_data)

        # 创建Excel文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='估值数据')

            # 添加说明sheet
            instructions = pd.DataFrame({
                '字段名': ['record_date', 'symbol', 'index_name', 'pe', 'pb', 'pe_percentile', 'pb_percentile', 'rsi', 'roe', 'dividend_yield'],
                '必填': ['是', '是', '是', '否', '否', '否', '否', '否', '否', '否'],
                '说明': [
                    '记录日期，格式：YYYY-MM-DD',
                    '标的代码，如：000001',
                    '指数名称，如：上证指数、沪深300',
                    '市盈率',
                    '市净率',
                    'PE历史百分位(0-100)',
                    'PB历史百分位(0-100)',
                    'RSI指标(0-100)',
                    'ROE(%)',
                    '股息率(%)'
                ]
            })
            instructions.to_excel(writer, index=False, sheet_name='字段说明')

        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='估值数据导入模板.xlsx'
        )
    except Exception as e:
        return error_response(str(e))


@valuations_bp.route('/valuations/import', methods=['POST'])
@login_required
def import_valuations():
    """导入估值数据"""
    try:
        user = get_current_user()

        if 'file' not in request.files:
            return error_response('未找到上传文件')

        file = request.files['file']
        if file.filename == '':
            return error_response('未选择文件')

        # 读取文件
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        # 验证必需字段
        required_fields = ['record_date', 'symbol', 'index_name']
        for field in required_fields:
            if field not in df.columns:
                return error_response(f'缺少必填字段: {field}')

        # 导入数据
        success_count = 0
        error_count = 0

        for _, row in df.iterrows():
            try:
                record_date = pd.to_datetime(row['record_date']).date()

                valuation = Valuation(
                    user_id=user.id,
                    symbol=str(row['symbol']),
                    index_name=str(row['index_name']),
                    pe=float(row['pe']) if pd.notna(row.get('pe')) else None,
                    pb=float(row['pb']) if pd.notna(row.get('pb')) else None,
                    pe_percentile=float(row['pe_percentile']) if pd.notna(row.get('pe_percentile')) else None,
                    pb_percentile=float(row['pb_percentile']) if pd.notna(row.get('pb_percentile')) else None,
                    rsi=float(row['rsi']) if pd.notna(row.get('rsi')) else None,
                    roe=float(row['roe']) if pd.notna(row.get('roe')) else None,
                    dividend_yield=float(row['dividend_yield']) if pd.notna(row.get('dividend_yield')) else None,
                    record_date=record_date
                )

                # 自动评估
                result = valuation_service.evaluate(
                    index_name=valuation.index_name,
                    pe=valuation.pe,
                    pb=valuation.pb,
                    pe_percentile=valuation.pe_percentile,
                    pb_percentile=valuation.pb_percentile,
                    rsi=valuation.rsi
                )

                valuation.level = result.level.value
                valuation.score = result.score
                valuation.suggestion = result.action

                db.session.add(valuation)
                success_count += 1
            except Exception as e:
                error_count += 1
                continue

        db.session.commit()

        return success_response({
            'message': f'成功导入 {success_count} 条估值数据',
            'success_count': success_count,
            'error_count': error_count
        })
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@valuations_bp.route('/valuations/export', methods=['GET'])
@login_required
def export_valuations():
    """导出估值数据"""
    try:
        user = get_current_user()
        symbol = request.args.get('symbol')

        query = Valuation.query.filter_by(user_id=user.id)
        if symbol:
            query = query.filter_by(symbol=symbol)

        valuations = query.order_by(Valuation.record_date.desc()).all()

        if not valuations:
            return error_response('没有可导出的数据')

        # 转换为DataFrame
        data = [{
            'record_date': v.record_date.isoformat() if v.record_date else '',
            'symbol': v.symbol,
            'index_name': v.index_name,
            'pe': float(v.pe) if v.pe else '',
            'pb': float(v.pb) if v.pb else '',
            'pe_percentile': float(v.pe_percentile) if v.pe_percentile else '',
            'pb_percentile': float(v.pb_percentile) if v.pb_percentile else '',
            'rsi': float(v.rsi) if v.rsi else '',
            'roe': float(v.roe) if v.roe else '',
            'dividend_yield': float(v.dividend_yield) if v.dividend_yield else '',
            'level': v.level or '',
            'score': float(v.score) if v.score else '',
            'suggestion': v.suggestion or ''
        } for v in valuations]

        df = pd.DataFrame(data)

        # 创建Excel文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='估值数据')

        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'估值数据_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
    except Exception as e:
        return error_response(str(e))