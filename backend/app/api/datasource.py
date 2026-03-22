#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场数据 API
提供金融数据获取、价格同步等接口
支持股票/基金分离配置
"""

from flask import Blueprint, request
from .. import db
from ..models import Position, PriceHistory, Config
from ..utils import success_response, error_response
from ..utils.decorators import login_required, get_current_user
from ..services import get_market_data_service
import logging

logger = logging.getLogger(__name__)

datasource_bp = Blueprint('datasource', __name__)


# ============ 数据源状态 ============

@datasource_bp.route('/datasource/status', methods=['GET'])
@login_required
def get_datasource_status():
    """获取数据源状态（股票/基金分离）"""
    try:
        user = get_current_user()
        service = get_market_data_service()
        result = service.get_datasource_status(user.id)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))


@datasource_bp.route('/datasource/test', methods=['POST'])
@login_required
def test_datasource():
    """测试数据源连接"""
    try:
        user = get_current_user()
        data = request.get_json() or {}

        source = data.get('source', 'akshare')
        asset_type = data.get('asset_type', 'stock')  # stock 或 fund

        if asset_type == 'fund':
            from ..services import get_eastmoney_fund_service
            service = get_eastmoney_fund_service()
            result = service.test_connection()
        elif source == 'tushare':
            from ..services import TushareService
            token = data.get('token')
            if not token:
                return error_response("请提供Tushare Token")
            service = TushareService(token=token)
            result = service.test_connection()
        else:
            from ..services import get_akshare_service
            service = get_akshare_service()
            result = service.test_connection()

        return success_response(result)
    except Exception as e:
        return error_response(str(e))


# ============ 股票数据接口 ============

@datasource_bp.route('/stock/realtime', methods=['POST'])
@login_required
def get_stock_realtime():
    """获取股票实时行情"""
    try:
        user = get_current_user()
        data = request.get_json() or {}
        symbols = data.get('symbols', [])

        if not symbols:
            return error_response("请提供股票代码列表")

        service = get_market_data_service()
        result = service.get_stock_realtime(symbols, user.id)

        return success_response({
            'prices': result,
            'count': len(result)
        })
    except Exception as e:
        logger.error(f"获取股票实时行情失败: {str(e)}")
        return error_response(str(e))


@datasource_bp.route('/stock/<symbol>/history', methods=['GET'])
@login_required
def get_stock_history(symbol):
    """获取股票历史数据"""
    try:
        user = get_current_user()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date or not end_date:
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        service = get_market_data_service()
        df = service.get_stock_history(symbol, start_date, end_date, user.id)

        if df.empty:
            return success_response({
                'symbol': symbol,
                'data': [],
                'message': '未获取到数据'
            })

        return success_response({
            'symbol': symbol,
            'data': df.to_dict('records'),
            'count': len(df)
        })
    except Exception as e:
        logger.error(f"获取股票历史数据失败: {str(e)}")
        return error_response(str(e))


@datasource_bp.route('/stock/<symbol>/latest', methods=['GET'])
@login_required
def get_stock_latest(symbol):
    """获取股票最新价格"""
    try:
        user = get_current_user()
        service = get_market_data_service()
        result = service.get_stock_realtime([symbol], user.id)

        if symbol not in result:
            return error_response("无法获取股票价格", 404)

        return success_response({
            'symbol': symbol,
            'price': result[symbol].get('price'),
            'name': result[symbol].get('name'),
            'change_pct': result[symbol].get('change_pct')
        })
    except Exception as e:
        logger.error(f"获取股票最新价格失败: {str(e)}")
        return error_response(str(e))


# ============ 基金数据接口 ============

@datasource_bp.route('/fund/realtime', methods=['POST'])
@login_required
def get_fund_realtime():
    """获取基金实时净值"""
    try:
        user = get_current_user()
        data = request.get_json() or {}
        fund_codes = data.get('fund_codes', [])

        if not fund_codes:
            return error_response("请提供基金代码列表")

        service = get_market_data_service()
        result = service.get_fund_realtime(fund_codes, user.id)

        return success_response({
            'navs': result,
            'count': len(result)
        })
    except Exception as e:
        logger.error(f"获取基金实时净值失败: {str(e)}")
        return error_response(str(e))


@datasource_bp.route('/fund/<fund_code>/history', methods=['GET'])
@login_required
def get_fund_history(fund_code):
    """获取基金净值历史"""
    try:
        user = get_current_user()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date or not end_date:
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        service = get_market_data_service()
        df = service.get_fund_nav_history(fund_code, start_date, end_date, user.id)

        if df.empty:
            return success_response({
                'fund_code': fund_code,
                'data': [],
                'message': '未获取到数据'
            })

        return success_response({
            'fund_code': fund_code,
            'data': df.to_dict('records'),
            'count': len(df)
        })
    except Exception as e:
        logger.error(f"获取基金净值历史失败: {str(e)}")
        return error_response(str(e))


@datasource_bp.route('/fund/<fund_code>/latest', methods=['GET'])
@login_required
def get_fund_latest(fund_code):
    """获取基金最新净值"""
    try:
        user = get_current_user()
        service = get_market_data_service()
        result = service.get_fund_realtime([fund_code], user.id)

        if fund_code not in result:
            return error_response("无法获取基金净值", 404)

        return success_response({
            'fund_code': fund_code,
            'nav': result[fund_code].get('nav'),
            'name': result[fund_code].get('name'),
            'change_pct': result[fund_code].get('gszzl')
        })
    except Exception as e:
        logger.error(f"获取基金最新净值失败: {str(e)}")
        return error_response(str(e))


# ============ 持仓数据同步 ============

@datasource_bp.route('/sync-prices', methods=['POST'])
@login_required
def sync_prices():
    """同步持仓股票/基金最新价格"""
    try:
        user = get_current_user()
        service = get_market_data_service()
        result = service.sync_position_prices(user.id)
        return success_response(result)
    except Exception as e:
        logger.error(f"同步价格失败: {str(e)}")
        return error_response(str(e))


@datasource_bp.route('/fetch-history', methods=['POST'])
@login_required
def fetch_history():
    """获取所有持仓历史数据"""
    try:
        user = get_current_user()
        data = request.get_json() or {}
        years = data.get('years', 5)

        service = get_market_data_service()
        result = service.fetch_position_history(user.id, years)

        return success_response(result)
    except Exception as e:
        logger.error(f"获取历史数据失败: {str(e)}")
        return error_response(str(e))


# ============ 指数数据接口 ============

@datasource_bp.route('/index/<symbol>/history', methods=['GET'])
@login_required
def get_index_history(symbol):
    """获取指数历史数据"""
    try:
        user = get_current_user()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date or not end_date:
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        service = get_market_data_service()
        df = service.get_index_history(symbol, start_date, end_date, user.id)

        if df.empty:
            return success_response({
                'symbol': symbol,
                'data': [],
                'message': '未获取到数据'
            })

        return success_response({
            'symbol': symbol,
            'data': df.to_dict('records'),
            'count': len(df)
        })
    except Exception as e:
        logger.error(f"获取指数数据失败: {str(e)}")
        return error_response(str(e))


# ============ 数据源配置 ============

@datasource_bp.route('/config/stock', methods=['POST'])
@login_required
def save_stock_datasource_config():
    """
    保存股票数据源配置

    Body:
        type: 数据源类型 (default/tushare)
        tushare_token: Tushare Token (可选)
        tushare_base_url: Tushare API地址 (可选)
    """
    try:
        user = get_current_user()
        data = request.get_json() or {}

        # 保存数据源类型
        ds_type = data.get('type', 'default')
        config = Config.query.filter_by(key='stock_datasource.type', user_id=user.id).first()
        if config:
            config.value = ds_type
        else:
            config = Config(user_id=user.id, key='stock_datasource.type', value=ds_type)
            db.session.add(config)

        # 保存Tushare Token
        if data.get('tushare_token'):
            token_config = Config.query.filter_by(key='stock_datasource.tushare_token', user_id=user.id).first()
            if token_config:
                token_config.value = data['tushare_token']
            else:
                token_config = Config(user_id=user.id, key='stock_datasource.tushare_token', value=data['tushare_token'])
                db.session.add(token_config)

        # 保存Tushare Base URL
        if data.get('tushare_base_url'):
            url_config = Config.query.filter_by(key='stock_datasource.tushare_base_url', user_id=user.id).first()
            if url_config:
                url_config.value = data['tushare_base_url']
            else:
                url_config = Config(user_id=user.id, key='stock_datasource.tushare_base_url', value=data['tushare_base_url'])
                db.session.add(url_config)

        db.session.commit()

        return success_response({
            'message': '股票数据源配置保存成功',
            'type': ds_type
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存股票数据源配置失败: {str(e)}")
        return error_response(str(e))


@datasource_bp.route('/config/fund', methods=['POST'])
@login_required
def save_fund_datasource_config():
    """
    保存基金数据源配置

    Body:
        type: 数据源类型 (default/tushare)
        tushare_token: Tushare Token (可选)
    """
    try:
        user = get_current_user()
        data = request.get_json() or {}

        # 保存数据源类型
        ds_type = data.get('type', 'default')
        config = Config.query.filter_by(key='fund_datasource.type', user_id=user.id).first()
        if config:
            config.value = ds_type
        else:
            config = Config(user_id=user.id, key='fund_datasource.type', value=ds_type)
            db.session.add(config)

        # 保存Tushare Token
        if data.get('tushare_token'):
            token_config = Config.query.filter_by(key='fund_datasource.tushare_token', user_id=user.id).first()
            if token_config:
                token_config.value = data['tushare_token']
            else:
                token_config = Config(user_id=user.id, key='fund_datasource.tushare_token', value=data['tushare_token'])
                db.session.add(token_config)

        db.session.commit()

        return success_response({
            'message': '基金数据源配置保存成功',
            'type': ds_type
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存基金数据源配置失败: {str(e)}")
        return error_response(str(e))