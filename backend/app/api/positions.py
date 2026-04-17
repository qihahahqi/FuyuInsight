#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓管理 API
"""

from flask import Blueprint, request, g
from .. import db, limiter
from ..models import Position, Trade
from ..utils import success_response, error_response
from ..utils.decorators import login_required, get_current_user
from ..utils.validation import validate_body
from ..schemas.position import PositionCreateSchema, PositionUpdateSchema
from ..services import ProfitService
from ..services.audit_service import AuditService
from ..constants import get_asset_type_category, ProductCategory
from datetime import datetime
import logging
import math
import random

logger = logging.getLogger(__name__)

positions_bp = Blueprint('positions', __name__)
profit_service = ProfitService()


def clean_nan_values(obj):
    """递归地将 NaN 和 Infinity 值转换为 None（JSON 兼容）"""
    if isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    return obj


@positions_bp.route('/positions', methods=['GET'])
@login_required
def get_positions():
    """获取持仓列表（不包含已清仓的数量为0的持仓）

    支持排序参数：
    - sort_by: 排序字段 (total_cost, market_value, profit_rate)
    - sort_order: 排序方向 (asc, desc)
    """
    try:
        user = get_current_user()
        account_id = request.args.get('account_id', type=int)
        sort_by = request.args.get('sort_by', default='created_at')
        sort_order = request.args.get('sort_order', default='desc')

        query = Position.query.filter_by(user_id=user.id)
        if account_id:
            query = query.filter_by(account_id=account_id)

        # 过滤掉数量为0的已清仓持仓
        query = query.filter(Position.quantity > 0)

        # 排序处理
        valid_sort_fields = {
            'total_cost': Position.total_cost,
            'market_value': Position.market_value,
            'profit_rate': Position.profit_rate,
            'created_at': Position.created_at,
            'name': Position.name,
            'quantity': Position.quantity
        }

        if sort_by in valid_sort_fields:
            sort_column = valid_sort_fields[sort_by]
            if sort_order == 'asc':
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
        else:
            # 默认按创建时间倒序
            query = query.order_by(Position.created_at.desc())

        positions = query.all()
        return success_response([p.to_dict() for p in positions])
    except Exception as e:
        return error_response(str(e))


@positions_bp.route('/positions/<int:position_id>', methods=['GET'])
@login_required
def get_position(position_id):
    """获取单个持仓"""
    try:
        user = get_current_user()
        position = Position.query.filter_by(id=position_id, user_id=user.id).first()
        if not position:
            return error_response("持仓不存在", 404)
        return success_response(position.to_dict())
    except Exception as e:
        return error_response(str(e))


@positions_bp.route('/positions', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
@validate_body(PositionCreateSchema)
def create_position():
    """创建持仓"""
    try:
        user = get_current_user()
        data = request.validated_data  # 使用 Pydantic 验证后的数据

        asset_type = data['asset_type']
        product_category = data.get('product_category', get_asset_type_category(asset_type))

        # 处理产品代码：市价产品必填，其他类型可自动生成
        symbol = data.get('symbol', '').strip() if data.get('symbol') else ''
        if not symbol:
            if product_category == ProductCategory.MARKET and asset_type not in ['gold', 'silver']:
                return error_response("市价型产品必须填写产品代码")
            # 自动生成代码
            date_str = datetime.now().strftime('%Y%m%d')
            random_num = random.randint(0, 999)
            if product_category == ProductCategory.FIXED_INCOME:
                symbol = f"FI_{date_str}_{random_num:03d}"
            elif product_category == ProductCategory.MANUAL:
                symbol = f"MF_{date_str}_{random_num:03d}"
            elif asset_type == 'gold':
                symbol = f"AU_{random.randint(0, 9999):04d}"
            elif asset_type == 'silver':
                symbol = f"AG_{random.randint(0, 9999):04d}"
            else:
                symbol = f"MK_{date_str}_{random_num:03d}"

        # 获取账户 ID（默认为 1）
        account_id = data.get('account_id', 1)

        # 检查是否已存在（同账户内）
        existing = Position.query.filter_by(user_id=user.id, account_id=account_id, symbol=symbol).first()
        if existing:
            return error_response(f"账户中已存在标的 {symbol}")

        # 计算总成本
        quantity = int(data['quantity'])
        cost_price = float(data['cost_price'])
        total_cost = quantity * cost_price

        position = Position(
            user_id=user.id,
            account_id=account_id,
            symbol=symbol,
            name=data['name'],
            asset_type=asset_type,
            quantity=quantity,
            cost_price=cost_price,
            current_price=data.get('current_price'),
            total_cost=total_cost,
            market_value=data.get('market_value'),
            category=data.get('category'),
            notes=data.get('notes'),
            product_category=product_category,
            product_params=data.get('product_params'),
            mature_date=data.get('mature_date'),
            risk_level=data.get('risk_level'),
            expected_return=data.get('expected_return'),
            stop_profit_triggered='[false, false, false]'
        )

        # 计算收益率
        if position.current_price:
            market_value = quantity * float(position.current_price)
            position.market_value = market_value
            position.profit_rate = (float(position.current_price) - cost_price) / cost_price

        db.session.add(position)
        db.session.commit()

        # 记录审计日志
        AuditService.log_create(
            resource_type='position',
            resource_id=position.id,
            new_values={'symbol': symbol, 'name': data['name'], 'quantity': quantity, 'cost_price': cost_price},
            details={'account_id': account_id}
        )

        return success_response(position.to_dict(), "持仓创建成功")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@positions_bp.route('/positions/<int:position_id>', methods=['PUT'])
@login_required
def update_position(position_id):
    """更新持仓"""
    try:
        user = get_current_user()
        position = Position.query.filter_by(id=position_id, user_id=user.id).first()
        if not position:
            return error_response("持仓不存在", 404)

        data = request.get_json()

        # 更新字段
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
        if 'product_category' in data:
            position.product_category = data['product_category']
        if 'product_params' in data:
            position.product_params = data['product_params']
        if 'mature_date' in data:
            position.mature_date = data['mature_date']
        if 'risk_level' in data:
            position.risk_level = data['risk_level']
        if 'expected_return' in data:
            position.expected_return = data['expected_return']

        # 重新计算
        position.total_cost = position.quantity * float(position.cost_price)
        if position.current_price:
            position.market_value = position.quantity * float(position.current_price)
            position.profit_rate = (float(position.current_price) - float(position.cost_price)) / float(position.cost_price)
        else:
            position.market_value = None
            position.profit_rate = None

        db.session.commit()
        return success_response(position.to_dict(), "持仓更新成功")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@positions_bp.route('/positions/<int:position_id>', methods=['DELETE'])
@login_required
def delete_position(position_id):
    """删除持仓"""
    try:
        user = get_current_user()
        position = Position.query.filter_by(id=position_id, user_id=user.id).first()
        if not position:
            return error_response("持仓不存在", 404)

        db.session.delete(position)
        db.session.commit()
        return success_response(None, "持仓删除成功")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@positions_bp.route('/positions/summary', methods=['GET'])
@login_required
def get_positions_summary():
    """获取持仓汇总（不包含已清仓的数量为0的持仓）"""
    try:
        user = get_current_user()
        account_id = request.args.get('account_id', type=int)

        query = Position.query.filter_by(user_id=user.id)
        if account_id:
            query = query.filter_by(account_id=account_id)

        # 过滤掉数量为0的已清仓持仓
        query = query.filter(Position.quantity > 0)

        positions = query.all()

        # 构建带交易记录的持仓数据
        positions_data = []
        for p in positions:
            # 获取卖出交易记录，计算原始持仓数量
            sells = Trade.query.filter_by(
                user_id=user.id,
                symbol=p.symbol,
                trade_type='sell'
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

        # 计算汇总
        summary = profit_service.portfolio_summary(positions_data)

        # 按资产类型分组
        by_type = {}
        for p in positions_data:
            asset_type = p.get('asset_type', 'unknown')
            if asset_type not in by_type:
                by_type[asset_type] = {
                    'count': 0,
                    'total_cost': 0,
                    'market_value': 0
                }
            by_type[asset_type]['count'] += 1
            by_type[asset_type]['total_cost'] += p.get('total_cost', 0)
            by_type[asset_type]['market_value'] += p.get('market_value', 0) or p.get('total_cost', 0)

        summary['by_type'] = by_type

        return success_response(summary)
    except Exception as e:
        return error_response(str(e))


@positions_bp.route('/positions/<int:position_id>/signals', methods=['GET'])
@login_required
def get_position_signals(position_id):
    """获取持仓操作信号（智能止盈策略）"""
    try:
        user = get_current_user()
        position = Position.query.filter_by(id=position_id, user_id=user.id).first()
        if not position:
            return error_response("持仓不存在", 404)

        if not position.current_price:
            return success_response({
                'position': position.to_dict(),
                'signals': None,
                'message': '请先更新当前价格'
            })

        # 获取该持仓的所有卖出交易记录，计算原始持仓数量
        sells = Trade.query.filter_by(
            user_id=user.id,
            symbol=position.symbol,
            trade_type='sell'
        ).order_by(Trade.trade_date).all()

        # 计算原始持仓数量 = 当前数量 + 已卖出数量
        total_sold = sum(t.quantity for t in sells)
        original_quantity = position.quantity + total_sold

        # 构建卖出记录列表
        sell_records = [{'date': t.trade_date, 'quantity': t.quantity} for t in sells]

        # 传入实际数据，智能判断
        result = profit_service.calculate_profit(
            position.cost_price,
            position.current_price,
            position.quantity,
            original_quantity=original_quantity,
            sell_records=sell_records,
            add_position_ratio=float(position.add_position_ratio) if position.add_position_ratio else 0
        )

        return success_response({
            'position': position.to_dict(),
            'signals': result,
            'original_quantity': original_quantity,
            'total_sold': total_sold,
            'sold_ratio': result.get('current_state', {}).get('sold_ratio', 0)
        })
    except Exception as e:
        return error_response(str(e))


@positions_bp.route('/positions/<int:position_id>/detail', methods=['GET'])
@login_required
def get_position_detail(position_id):
    """获取持仓详情（含详细指标和历史数据）"""
    try:
        user = get_current_user()
        position = Position.query.filter_by(id=position_id, user_id=user.id).first()
        if not position:
            return error_response("持仓不存在", 404)

        pos_data = position.to_dict()

        # 获取该持仓的交易记录
        trades = Trade.query.filter_by(
            user_id=user.id,
            symbol=position.symbol
        ).order_by(Trade.trade_date.desc()).limit(20).all()

        # 基础详情
        detail = {
            'basic': {
                'symbol': position.symbol,
                'name': position.name,
                'asset_type': position.asset_type,
                'category': position.category,
                'quantity': position.quantity,
                'cost_price': float(position.cost_price) if position.cost_price else 0,
                'current_price': float(position.current_price) if position.current_price else None,
                'total_cost': float(position.total_cost) if position.total_cost else 0,
                'market_value': float(position.market_value) if position.market_value else None,
                'profit_rate': float(position.profit_rate) if position.profit_rate else 0,
                'profit_amount': float((position.market_value or position.total_cost) - position.total_cost),
                'notes': position.notes
            },
            'trades': [t.to_dict() for t in trades],
            'metrics': {},
            'history': []  # 历史数据
        }

        # 导入数据服务
        from ..services.market_data_service import get_market_data_service
        data_service = get_market_data_service()

        # 根据资产类型获取不同的数据和指标
        if position.asset_type == 'stock':
            detail['metrics'] = {
                'valuation': {
                    'pe_ttm': None,
                    'pb': None,
                    'peg': None,
                    'ps_ttm': None,
                    'dividend_yield': None
                },
                'profitability': {
                    'roe': None,
                    'gross_margin': None,
                    'net_margin': None,
                    'roic': None
                },
                'growth': {
                    'revenue_growth': None,
                    'profit_growth': None
                },
                'safety': {
                    'debt_ratio': None,
                    'current_ratio': None,
                    'quick_ratio': None
                },
                'technical': {
                    'ma5': None,
                    'ma10': None,
                    'ma20': None,
                    'ma60': None,
                    'rsi': None,
                    'macd': None
                },
                'capital_flow': {
                    'avg_volume': None,
                    'turnover_rate': None,
                    'northbound_ratio': None
                }
            }

            # 尝试从AKShare获取股票实时数据（包含更多指标）
            try:
                from ..services.akshare_service import get_akshare_service
                ak = get_akshare_service()

                # 获取实时行情
                realtime = ak.get_stock_realtime([position.symbol])
                if position.symbol in realtime:
                    rt_data = realtime[position.symbol]
                    detail['basic']['current_price'] = rt_data.get('price', detail['basic']['current_price'])

                    # 计算技术指标需要历史数据
                    detail['metrics']['capital_flow']['turnover_rate'] = rt_data.get('turnover_rate')

                # 获取股票信息
                try:
                    info = ak.get_stock_info(position.symbol)
                    if info:
                        detail['basic']['industry'] = info.get('industry', '')
                except:
                    pass

            except Exception as e:
                logger.warning(f"AKShare获取股票数据失败: {e}")

            # 获取历史数据
            try:
                df = data_service.get_stock_all_history(position.symbol, years=1, user_id=user.id)
                if not df.empty:
                    detail['history'] = df.to_dict('records')

                    # 计算技术指标
                    if len(df) >= 60:
                        closes = df['close'].values
                        volumes = df['volume'].values if 'volume' in df.columns else None

                        # 均线
                        detail['metrics']['technical']['ma5'] = round(float(closes[-5:].mean()), 3) if len(closes) >= 5 else None
                        detail['metrics']['technical']['ma10'] = round(float(closes[-10:].mean()), 3) if len(closes) >= 10 else None
                        detail['metrics']['technical']['ma20'] = round(float(closes[-20:].mean()), 3) if len(closes) >= 20 else None
                        detail['metrics']['technical']['ma60'] = round(float(closes[-60:].mean()), 3) if len(closes) >= 60 else None

                        # 成交量均值
                        if volumes is not None:
                            detail['metrics']['capital_flow']['avg_volume'] = float(volumes[-20:].mean())
            except Exception as e:
                logger.warning(f"获取股票历史数据失败: {e}")

        elif position.asset_type in ['etf_index', 'etf_sector']:
            # ETF指标
            detail['metrics'] = {
                'returns': {
                    'return_1m': None,
                    'return_3m': None,
                    'return_6m': None,
                    'return_1y': None
                },
                'risk': {
                    'max_drawdown': None,
                    'volatility': None,
                    'sharpe_ratio': None
                },
                'tracking': {
                    'tracking_error': None,
                    'premium_discount': None,
                    'avg_volume': None
                }
            }

            # 获取ETF历史数据（用股票接口）
            try:
                df = data_service.get_stock_all_history(position.symbol, years=1, user_id=user.id)
                if not df.empty:
                    detail['history'] = df.to_dict('records')

                    # 计算收益率
                    closes = df['close'].values
                    if len(closes) > 0:
                        current = closes[-1]
                        detail['metrics']['returns']['return_1m'] = round((current / closes[-22] - 1) * 100, 2) if len(closes) >= 22 else None
                        detail['metrics']['returns']['return_3m'] = round((current / closes[-66] - 1) * 100, 2) if len(closes) >= 66 else None
                        detail['metrics']['returns']['return_6m'] = round((current / closes[-132] - 1) * 100, 2) if len(closes) >= 132 else None
                        detail['metrics']['returns']['return_1y'] = round((current / closes[0] - 1) * 100, 2) if len(closes) >= 1 else None
            except Exception as e:
                logger.warning(f"获取ETF历史数据失败: {e}")

        elif position.asset_type == 'fund':
            # 基金指标（与股票不同的指标体系）
            detail['metrics'] = {
                'returns': {
                    'return_1m': None,
                    'return_3m': None,
                    'return_6m': None,
                    'return_1y': None,
                    'return_3y': None,
                    'return_this_year': None
                },
                'risk': {
                    'max_drawdown': None,
                    'volatility': None,
                    'sharpe_ratio': None
                },
                'characteristics': {
                    'fund_type': None,
                    'manager': None,
                    'fund_size': None,
                    'establish_date': None,
                    'benchmark': None
                },
                'nav_info': {
                    'unit_nav': None,  # 单位净值
                    'acc_nav': None,   # 累计净值
                    'nav_date': None   # 净值日期
                }
            }

            # 获取基金实时净值
            try:
                realtime = data_service.get_fund_realtime([position.symbol], user.id)
                if position.symbol in realtime:
                    rt_data = realtime[position.symbol]
                    detail['basic']['current_price'] = rt_data.get('nav') or rt_data.get('dwjz')
                    detail['metrics']['nav_info']['unit_nav'] = rt_data.get('nav')
                    detail['metrics']['nav_info']['acc_nav'] = rt_data.get('acc_nav')
                    detail['metrics']['nav_info']['nav_date'] = rt_data.get('nav_date')
                    detail['basic']['name'] = rt_data.get('name', position.name)
            except Exception as e:
                logger.warning(f"获取基金实时净值失败: {e}")

            # 获取基金净值历史
            try:
                df = data_service.get_fund_all_nav_history(position.symbol, years=1, user_id=user.id)
                if not df.empty:
                    detail['history'] = df.to_dict('records')

                    # 计算收益率
                    if 'nav' in df.columns:
                        navs = df['nav'].values
                        if len(navs) > 0:
                            current = navs[-1]
                            detail['metrics']['returns']['return_1m'] = round((current / navs[-22] - 1) * 100, 2) if len(navs) >= 22 else None
                            detail['metrics']['returns']['return_3m'] = round((current / navs[-66] - 1) * 100, 2) if len(navs) >= 66 else None
                            detail['metrics']['returns']['return_6m'] = round((current / navs[-132] - 1) * 100, 2) if len(navs) >= 132 else None
                            detail['metrics']['returns']['return_1y'] = round((current / navs[0] - 1) * 100, 2) if len(navs) >= 1 else None
            except Exception as e:
                logger.warning(f"获取基金净值历史失败: {e}")

        # 清理 NaN 值，确保 JSON 序列化兼容
        detail = clean_nan_values(detail)
        return success_response(detail)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(str(e))


@positions_bp.route('/positions/<int:position_id>/fetch-metrics', methods=['GET'])
@login_required
def fetch_position_metrics(position_id):
    """获取持仓的实时指标数据（用于字段级加载）"""
    try:
        user = get_current_user()
        position = Position.query.filter_by(id=position_id, user_id=user.id).first()
        if not position:
            return error_response("持仓不存在", 404)

        fields_param = request.args.get('fields', '')
        requested_fields = fields_param.split(',') if fields_param else []

        result = {
            'position_id': position_id,
            'symbol': position.symbol,
            'metrics': {},
            'errors': {}
        }

        from ..services.market_data_service import get_market_data_service
        data_service = get_market_data_service()

        if position.asset_type == 'stock':
            # 获取股票实时数据（换手率等）
            try:
                from ..services.akshare_service import get_akshare_service
                ak = get_akshare_service()

                # 获取实时行情（换手率）
                if not requested_fields or 'turnover_rate' in requested_fields:
                    try:
                        realtime = ak.get_stock_realtime([position.symbol])
                        if position.symbol in realtime:
                            rt = realtime[position.symbol]
                            result['metrics']['turnover_rate'] = rt.get('turnover_rate')
                    except Exception as e:
                        result['errors']['turnover_rate'] = f"获取换手率失败: {str(e)}"

                # 获取历史数据计算技术指标（MA均线）
                ma_fields = ['ma5', 'ma10', 'ma20', 'ma60']
                need_ma = any(f in requested_fields for f in ma_fields) if requested_fields else True

                if need_ma:
                    try:
                        df = data_service.get_stock_all_history(position.symbol, years=1, user_id=user.id)
                        if not df.empty and len(df) >= 5:
                            closes = df['close'].values
                            result['metrics']['ma5'] = round(float(closes[-5:].mean()), 3) if len(closes) >= 5 else None
                            result['metrics']['ma10'] = round(float(closes[-10:].mean()), 3) if len(closes) >= 10 else None
                            result['metrics']['ma20'] = round(float(closes[-20:].mean()), 3) if len(closes) >= 20 else None
                            result['metrics']['ma60'] = round(float(closes[-60:].mean()), 3) if len(closes) >= 60 else None
                        else:
                            result['errors']['ma'] = "历史数据不足，无法计算均线"
                    except Exception as e:
                        result['errors']['ma'] = f"计算均线失败: {str(e)}"

            except Exception as e:
                result['errors']['general'] = str(e)

        elif position.asset_type == 'fund':
            # 获取基金实时净值
            try:
                realtime = data_service.get_fund_realtime([position.symbol], user.id)
                if position.symbol in realtime:
                    rt = realtime[position.symbol]
                    result['metrics']['unit_nav'] = rt.get('nav')
                    result['metrics']['acc_nav'] = rt.get('acc_nav')

                # 计算收益率
                try:
                    df = data_service.get_fund_all_nav_history(position.symbol, years=1, user_id=user.id)
                    if not df.empty and 'nav' in df.columns:
                        navs = df['nav'].values
                        if len(navs) > 0:
                            current = navs[-1]
                            result['metrics']['return_1m'] = round((current / navs[-22] - 1) * 100, 2) if len(navs) >= 22 else None
                            result['metrics']['return_3m'] = round((current / navs[-66] - 1) * 100, 2) if len(navs) >= 66 else None
                            result['metrics']['return_1y'] = round((current / navs[0] - 1) * 100, 2) if len(navs) >= 1 else None
                except Exception as e:
                    result['errors']['returns'] = f"计算收益率失败: {str(e)}"

            except Exception as e:
                result['errors']['general'] = str(e)

        elif position.asset_type in ['etf_index', 'etf_sector']:
            # ETF使用股票数据源
            try:
                df = data_service.get_stock_all_history(position.symbol, years=1, user_id=user.id)
                if not df.empty:
                    closes = df['close'].values
                    if len(closes) > 0:
                        current = closes[-1]
                        result['metrics']['return_1m'] = round((current / closes[-22] - 1) * 100, 2) if len(closes) >= 22 else None
                        result['metrics']['return_3m'] = round((current / closes[-66] - 1) * 100, 2) if len(closes) >= 66 else None
                        result['metrics']['return_1y'] = round((current / closes[0] - 1) * 100, 2) if len(closes) >= 1 else None
            except Exception as e:
                result['errors']['general'] = str(e)

        return success_response(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(str(e))