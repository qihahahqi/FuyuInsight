#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入导出 API
"""

from flask import Blueprint, request, send_file
from .. import db
from ..models import Position, Trade
from ..utils import success_response, error_response
from ..utils.decorators import login_required, get_current_user
from ..services.export_service import ExportService
from io import BytesIO

imports_bp = Blueprint('imports', __name__)
export_service = ExportService()


@imports_bp.route('/export/positions', methods=['GET'])
@login_required
def export_positions():
    """导出持仓到 Excel"""
    try:
        user = get_current_user()
        account_id = request.args.get('account_id', type=int)

        query = Position.query.filter_by(user_id=user.id)
        if account_id:
            query = query.filter_by(account_id=account_id)

        positions = query.all()
        positions_data = [p.to_dict() for p in positions]

        if not positions_data:
            return error_response("没有可导出的持仓数据")

        file_stream = export_service.export_positions_to_excel(positions_data)

        return send_file(
            file_stream,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='positions.xlsx'
        )
    except Exception as e:
        return error_response(str(e))


@imports_bp.route('/export/trades', methods=['GET'])
@login_required
def export_trades():
    """导出交易记录到 Excel"""
    try:
        user = get_current_user()
        account_id = request.args.get('account_id', type=int)

        query = Trade.query.filter_by(user_id=user.id)
        if account_id:
            query = query.filter_by(account_id=account_id)

        trades = query.order_by(Trade.trade_date.desc()).all()
        trades_data = [t.to_dict() for t in trades]

        if not trades_data:
            return error_response("没有可导出的交易记录")

        file_stream = export_service.export_trades_to_excel(trades_data)

        return send_file(
            file_stream,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='trades.xlsx'
        )
    except Exception as e:
        return error_response(str(e))


@imports_bp.route('/import/positions', methods=['POST'])
@login_required
def import_positions():
    """从 Excel/CSV 导入持仓"""
    try:
        user = get_current_user()
        if 'file' not in request.files:
            return error_response("请选择要导入的文件")

        file = request.files['file']
        if file.filename == '':
            return error_response("请选择要导入的文件")

        account_id = request.form.get('account_id', type=int, default=1)

        # 根据文件类型解析
        filename = file.filename.lower()
        if filename.endswith('.csv'):
            positions = export_service.import_positions_from_csv(file.stream)
        elif filename.endswith(('.xlsx', '.xls')):
            positions = export_service.import_positions_from_excel(file.stream)
        else:
            return error_response("不支持的文件格式，请上传 Excel 或 CSV 文件")

        if not positions:
            return error_response("文件中没有有效的持仓数据")

        # 导入数据
        imported = 0
        skipped = 0
        errors = []

        for p in positions:
            try:
                # 检查是否已存在（同账户同标的）
                existing = Position.query.filter_by(
                    user_id=user.id,
                    account_id=account_id,
                    symbol=p['symbol']
                ).first()

                if existing:
                    skipped += 1
                    continue

                position = Position(
                    user_id=user.id,
                    account_id=account_id,
                    symbol=p['symbol'],
                    name=p['name'],
                    asset_type=p.get('asset_type', 'etf_index'),
                    quantity=p.get('quantity', 0),
                    cost_price=p.get('cost_price', 0),
                    current_price=p.get('current_price'),
                    total_cost=p.get('total_cost') or (p.get('quantity', 0) * p.get('cost_price', 0)),
                    market_value=p.get('market_value'),
                    profit_rate=p.get('profit_rate'),
                    category=p.get('category'),
                    notes=p.get('notes'),
                    stop_profit_triggered='[false, false, false]'
                )

                db.session.add(position)
                imported += 1

            except Exception as e:
                errors.append(f"{p.get('symbol', '未知')}: {str(e)}")

        db.session.commit()

        return success_response({
            'imported': imported,
            'skipped': skipped,
            'errors': errors
        }, f"成功导入 {imported} 条持仓，跳过 {skipped} 条已存在的记录")

    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@imports_bp.route('/import/template', methods=['GET'])
@login_required
def download_template():
    """下载持仓导入模板"""
    try:
        file_stream = export_service.export_positions_template()

        return send_file(
            file_stream,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='positions_template.xlsx'
        )
    except Exception as e:
        return error_response(str(e))


@imports_bp.route('/import/trades', methods=['POST'])
@login_required
def import_trades():
    """从 Excel 导入交易记录"""
    try:
        user = get_current_user()
        if 'file' not in request.files:
            return error_response("请选择要导入的文件")

        file = request.files['file']
        if file.filename == '':
            return error_response("请选择要导入的文件")

        # 根据文件类型解析
        filename = file.filename.lower()
        if not filename.endswith(('.xlsx', '.xls')):
            return error_response("请上传 Excel 文件（.xlsx 或 .xls）")

        trades = export_service.import_trades_from_excel(file.stream)

        if not trades:
            return error_response("文件中没有有效的交易记录，请检查格式是否正确")

        # 导入数据
        imported = 0
        errors = []

        for t in trades:
            try:
                # 验证必填字段
                if not t.get('symbol') or not t.get('trade_date') or not t.get('trade_type'):
                    errors.append(f"数据不完整: {t}")
                    continue

                if t.get('quantity', 0) <= 0 or t.get('price', 0) <= 0:
                    errors.append(f"数量或价格无效: {t['symbol']}")
                    continue

                # 计算金额
                amount = t['amount'] or (t['quantity'] * t['price'])

                # 查找关联的持仓
                position = Position.query.filter_by(user_id=user.id, symbol=t['symbol']).first()

                # 解析日期
                from datetime import datetime
                trade_date = datetime.strptime(str(t['trade_date']), '%Y-%m-%d').date()

                trade = Trade(
                    user_id=user.id,
                    position_id=position.id if position else None,
                    symbol=t['symbol'],
                    trade_type=t['trade_type'],
                    quantity=t['quantity'],
                    price=t['price'],
                    amount=amount,
                    trade_date=trade_date,
                    reason=t.get('reason'),
                    notes=t.get('notes')
                )

                db.session.add(trade)
                imported += 1

            except Exception as e:
                errors.append(f"{t.get('symbol', '未知')}: {str(e)}")

        db.session.commit()

        return success_response({
            'imported': imported,
            'errors': errors
        }, f"成功导入 {imported} 条交易记录")

    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@imports_bp.route('/import/trades/template', methods=['GET'])
@login_required
def download_trades_template():
    """下载交易记录导入模板"""
    try:
        file_stream = export_service.export_trades_template()

        return send_file(
            file_stream,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='trades_template.xlsx'
        )
    except Exception as e:
        return error_response(str(e))