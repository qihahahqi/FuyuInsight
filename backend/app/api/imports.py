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
from ..constants import ProductCategory
from io import BytesIO
import logging

imports_bp = Blueprint('imports', __name__)
export_service = ExportService()
logger = logging.getLogger(__name__)


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

        # 将文件内容读取到 BytesIO，解决 SpooledTemporaryFile 不支持 seekable 的问题
        file_content = file.stream.read()
        file_stream = BytesIO(file_content)

        # 根据文件类型解析
        filename = file.filename.lower()
        if filename.endswith('.csv'):
            positions = export_service.import_positions_from_csv(file_stream)
        elif filename.endswith(('.xlsx', '.xls')):
            positions = export_service.import_positions_from_excel(file_stream)
        else:
            return error_response("不支持的文件格式，请上传 Excel 或 CSV 文件")

        if not positions:
            return error_response("文件中没有有效的持仓数据")

        # 导入数据
        imported = 0
        skipped = 0
        errors = []
        import json

        for idx, p in enumerate(positions, 1):
            try:
                # 验证必填字段
                if not p.get('name'):
                    errors.append(f"第{idx}行: 名称不能为空")
                    continue

                # 根据资产类型验证代码是否必填
                asset_type = p.get('asset_type', 'etf_index')
                market_types = ['stock', 'etf_index', 'etf_sector', 'fund', 'gold', 'silver']

                symbol = p.get('symbol', '').strip()
                if asset_type in market_types and not symbol:
                    errors.append(f"第{idx}行: 市价型产品({asset_type})必须填写代码")
                    continue

                # 自动生成代码
                if not symbol:
                    from datetime import datetime
                    import random
                    date_str = datetime.now().strftime('%Y%m%d')
                    random_num = random.randint(0, 999)

                    fixed_income_types = ['bank_deposit', 'bank_current', 'bank_wealth', 'treasury_bond', 'corporate_bond', 'money_fund']
                    manual_types = ['insurance', 'trust', 'other']

                    if asset_type in fixed_income_types:
                        symbol = f"FI_{date_str}_{random_num:03d}"
                    elif asset_type in manual_types:
                        symbol = f"MF_{date_str}_{random_num:03d}"
                    else:
                        symbol = f"MK_{date_str}_{random_num:03d}"

                # 根据账户名称查找账户ID
                final_account_id = account_id
                if p.get('account_name'):
                    from ..models import Account
                    acct = Account.query.filter_by(user_id=user.id, name=p['account_name']).first()
                    if acct:
                        final_account_id = acct.id

                # 检查是否已存在（同账户同标的）
                existing = Position.query.filter_by(
                    user_id=user.id,
                    account_id=final_account_id,
                    symbol=symbol
                ).first()

                if existing:
                    skipped += 1
                    errors.append(f"第{idx}行: 标的 {symbol} 已存在，跳过")
                    continue

                # 计算总成本
                quantity = float(p.get('quantity', 0))
                cost_price = float(p.get('cost_price', 0))

                if quantity <= 0:
                    errors.append(f"第{idx}行: 数量必须大于0")
                    continue
                if cost_price <= 0:
                    errors.append(f"第{idx}行: 成本价必须大于0")
                    continue

                total_cost = quantity * cost_price

                # 确定产品大类
                product_category = 'market'
                if asset_type in ['bank_deposit', 'bank_current', 'bank_wealth', 'treasury_bond', 'corporate_bond', 'money_fund']:
                    product_category = ProductCategory.FIXED_INCOME
                elif asset_type in ['insurance', 'trust', 'other']:
                    product_category = ProductCategory.MANUAL

                # 构建 product_params（固定收益类存储起息日等）
                product_params = None
                if product_category == 'fixed_income':
                    start_date = p.get('start_date')
                    if start_date:
                        product_params = {
                            'start_date': str(start_date),
                            'interest_rate': str(p.get('expected_return', 0) or 0)
                        }

                # 处理到期日
                mature_date = None
                if p.get('mature_date'):
                    md = p['mature_date']
                    if hasattr(md, 'strftime'):
                        mature_date = md
                    elif isinstance(md, str) and md.strip():
                        try:
                            from datetime import datetime as dt
                            mature_date = dt.strptime(md.strip(), '%Y-%m-%d').date()
                        except:
                            pass

                position = Position(
                    user_id=user.id,
                    account_id=final_account_id,
                    symbol=symbol,
                    name=p['name'],
                    asset_type=asset_type,
                    quantity=quantity,
                    cost_price=cost_price,
                    current_price=p.get('current_price'),
                    total_cost=total_cost,
                    market_value=p.get('market_value'),
                    profit_rate=p.get('profit_rate'),
                    category=p.get('category'),
                    notes=p.get('notes'),
                    product_category=product_category,
                    expected_return=p.get('expected_return'),
                    mature_date=mature_date,
                    risk_level=p.get('risk_level'),
                    product_params=product_params,
                    stop_profit_triggered='[false, false, false]'
                )

                # 计算收益率
                if position.current_price:
                    market_value = quantity * float(position.current_price)
                    position.market_value = market_value
                    position.profit_rate = (float(position.current_price) - cost_price) / cost_price

                db.session.add(position)
                imported += 1

            except Exception as e:
                errors.append(f"第{idx}行: 导入失败 - {str(e)}")
                logger.warning(f"导入持仓失败: {e}")

        db.session.commit()

        result = {
            'imported': imported,
            'skipped': skipped,
            'total': len(positions),
            'errors': errors
        }

        message = f"成功导入 {imported} 条持仓"
        if skipped > 0:
            message += f"，跳过 {skipped} 条已存在的记录"
        if errors:
            message += f"，{len(errors)} 条失败"

        return success_response(result, message)

    except Exception as e:
        db.session.rollback()
        logger.error(f"导入持仓异常: {e}")
        return error_response(str(e))


@imports_bp.route('/import/template', methods=['GET'])
@login_required
def download_template():
    """下载持仓导入模板（包含所有资产类型）"""
    try:
        file_stream = export_service.export_positions_template()

        return send_file(
            file_stream,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='positions_import_template.xlsx'
        )
    except Exception as e:
        return error_response(str(e))


@imports_bp.route('/import/template/<category>', methods=['GET'])
@login_required
def download_category_template(category):
    """下载指定类型的持仓导入模板

    Args:
        category: 产品大类 (market/fixed_income/manual)
    """
    try:
        valid_categories = ['market', 'fixed_income', 'manual']
        if category not in valid_categories:
            return error_response(f"无效的类型分类，可选: {', '.join(valid_categories)}")

        file_stream = export_service.export_positions_template(category=category)

        category_names = {
            'market': '市价型产品',
            'fixed_income': '固定收益类',
            'manual': '其他产品'
        }

        return send_file(
            file_stream,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{category_names[category]}_import_template.xlsx'
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

        # 将文件内容读取到 BytesIO，解决 SpooledTemporaryFile 不支持 seekable 的问题
        file_content = file.stream.read()
        file_stream = BytesIO(file_content)

        # 根据文件类型解析
        filename = file.filename.lower()
        if not filename.endswith(('.xlsx', '.xls')):
            return error_response("请上传 Excel 文件（.xlsx 或 .xls）")

        trades = export_service.import_trades_from_excel(file_stream)

        if not trades:
            return error_response("文件中没有有效的交易记录，请检查格式是否正确")

        account_id = request.form.get('account_id', type=int, default=1)

        # 导入数据
        imported = 0
        errors = []

        for idx, t in enumerate(trades, 1):
            try:
                # 验证必填字段
                if not t.get('symbol'):
                    errors.append(f"第{idx}行: 代码不能为空")
                    continue
                if not t.get('trade_date'):
                    errors.append(f"第{idx}行: 日期不能为空")
                    continue
                if not t.get('trade_type'):
                    errors.append(f"第{idx}行: 类型不能为空")
                    continue

                if t.get('quantity', 0) <= 0:
                    errors.append(f"第{idx}行: 数量必须大于0")
                    continue
                if t.get('price', 0) <= 0:
                    errors.append(f"第{idx}行: 价格必须大于0")
                    continue

                # 根据账户名称查找账户ID
                final_account_id = account_id
                if t.get('account_name'):
                    from ..models import Account
                    acct = Account.query.filter_by(user_id=user.id, name=t['account_name']).first()
                    if acct:
                        final_account_id = acct.id

                # 计算金额
                amount = t['amount'] or (t['quantity'] * t['price'])

                # 查找关联的持仓（优先按账户+代码匹配）
                position = Position.query.filter_by(
                    user_id=user.id,
                    account_id=final_account_id,
                    symbol=t['symbol']
                ).first()
                if not position:
                    position = Position.query.filter_by(user_id=user.id, symbol=t['symbol']).first()

                # 构建备注（手续费信息附加到备注）
                notes = t.get('notes') or ''
                commission = t.get('commission')
                if commission and float(commission) > 0:
                    notes = f"{notes} [手续费:{commission}元]".strip()

                # 解析日期
                from datetime import datetime
                trade_date = datetime.strptime(str(t['trade_date']), '%Y-%m-%d').date()

                trade = Trade(
                    user_id=user.id,
                    account_id=final_account_id,
                    position_id=position.id if position else None,
                    symbol=t['symbol'],
                    trade_type=t['trade_type'],
                    quantity=t['quantity'],
                    price=t['price'],
                    amount=amount,
                    trade_date=trade_date,
                    reason=t.get('reason'),
                    notes=notes
                )

                db.session.add(trade)

                # 更新持仓
                if position:
                    if t['trade_type'] == 'buy':
                        # 买入：更新成本价
                        total_cost = float(position.total_cost) + amount
                        total_quantity = float(position.quantity) + t['quantity']
                        position.cost_price = total_cost / total_quantity
                        position.quantity = total_quantity
                        position.total_cost = total_cost
                    else:
                        # 卖出：减少数量
                        position.quantity = float(position.quantity) - t['quantity']
                        position.total_cost = float(position.total_cost) - float(position.cost_price) * t['quantity']

                        # 如果卖出后数量为0，重置相关字段
                        if position.quantity <= 0:
                            position.quantity = 0
                            position.total_cost = 0
                            position.market_value = 0
                            position.profit_rate = 0
                            position.current_price = None

                imported += 1

            except Exception as e:
                errors.append(f"第{idx}行 ({t.get('symbol', '未知')}): {str(e)}")

        db.session.commit()

        result = {
            'imported': imported,
            'total': len(trades),
            'errors': errors
        }

        message = f"成功导入 {imported} 条交易记录"
        if errors:
            message += f"，{len(errors)} 条失败"

        return success_response(result, message)

    except Exception as e:
        db.session.rollback()
        logger.error(f"导入交易记录异常: {e}")
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
            download_name='trades_import_template.xlsx'
        )
    except Exception as e:
        return error_response(str(e))