#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓管理 API
"""

from flask import Blueprint, request, g
from .. import db
from ..models import Position, Trade
from ..utils import success_response, error_response
from ..utils.decorators import login_required, get_current_user
from ..services import ProfitService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

positions_bp = Blueprint('positions', __name__)
profit_service = ProfitService()


@positions_bp.route('/positions', methods=['GET'])
@login_required
def get_positions():
    """获取持仓列表"""
    try:
        user = get_current_user()
        account_id = request.args.get('account_id', type=int)

        query = Position.query.filter_by(user_id=user.id)
        if account_id:
            query = query.filter_by(account_id=account_id)

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
def create_position():
    """创建持仓"""
    try:
        user = get_current_user()
        data = request.get_json()

        # 验证必填字段
        required = ['symbol', 'name', 'asset_type', 'quantity', 'cost_price']
        for field in required:
            if field not in data:
                return error_response(f"缺少必填字段: {field}")

        # 获取账户 ID（默认为 1）
        account_id = data.get('account_id', 1)

        # 检查是否已存在（同账户内）
        existing = Position.query.filter_by(user_id=user.id, account_id=account_id, symbol=data['symbol']).first()
        if existing:
            return error_response(f"账户中已存在标的 {data['symbol']}")

        # 计算总成本
        quantity = int(data['quantity'])
        cost_price = float(data['cost_price'])
        total_cost = quantity * cost_price

        position = Position(
            user_id=user.id,
            account_id=account_id,
            symbol=data['symbol'],
            name=data['name'],
            asset_type=data['asset_type'],
            quantity=quantity,
            cost_price=cost_price,
            current_price=data.get('current_price'),
            total_cost=total_cost,
            market_value=data.get('market_value'),
            category=data.get('category'),
            notes=data.get('notes'),
            stop_profit_triggered='[false, false, false]'
        )

        # 计算收益率
        if position.current_price:
            market_value = quantity * float(position.current_price)
            position.market_value = market_value
            position.profit_rate = (float(position.current_price) - cost_price) / cost_price

        db.session.add(position)
        db.session.commit()

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
    """获取持仓汇总"""
    try:
        user = get_current_user()
        account_id = request.args.get('account_id', type=int)

        query = Position.query.filter_by(user_id=user.id)
        if account_id:
            query = query.filter_by(account_id=account_id)

        positions = query.all()

        # 转换为字典列表
        positions_data = [p.to_dict() for p in positions]

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
    """获取持仓操作信号"""
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

        result = profit_service.calculate_profit(
            position.cost_price,
            position.current_price,
            position.quantity
        )

        return success_response({
            'position': position.to_dict(),
            'signals': result
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