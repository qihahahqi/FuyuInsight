#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测模拟 API v2.0
支持多策略对比、多数据源（Tushare/AKShare/BaoStock）
"""

from flask import Blueprint, request, send_file
from werkzeug.utils import secure_filename
from datetime import datetime
from io import BytesIO
import os
import pandas as pd
import json
import logging
from .. import db
from ..utils import success_response, error_response
from ..utils.decorators import login_required
from ..utils.config import config_manager
from ..models import PriceHistory, BacktestHistory

logger = logging.getLogger(__name__)
from ..services.backtest_service import (
    BacktestEngine, StrategyType, create_strategy,
    run_multi_strategy_backtest, get_available_strategies
)
from ..services.tushare_service import get_tushare_service, TushareService
from ..services.market_data_service import get_market_data_service

backtest_bp = Blueprint('backtest', __name__)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}


@backtest_bp.route('/backtest/strategies', methods=['GET'])
@login_required
def get_strategies():
    """获取所有可用策略列表"""
    try:
        strategies = get_available_strategies()
        return success_response(strategies)
    except Exception as e:
        return error_response(str(e))


@backtest_bp.route('/backtest/scenarios', methods=['GET'])
@login_required
def get_scenarios():
    """获取市场场景列表（兼容旧API）"""
    try:
        scenarios = [
            {'value': 'BULL_MARKET', 'label': '牛市'},
            {'value': 'BEAR_MARKET', 'label': '熊市'},
            {'value': 'OSCILLATION', 'label': '震荡市'},
            {'value': 'V_SHAPED', 'label': 'V型反转'},
            {'value': 'INVERTED_V', 'label': '倒V型'},
            {'value': 'SLOW_RISE', 'label': '慢牛'},
            {'value': 'SLOW_FALL', 'label': '阴跌'}
        ]
        return success_response(scenarios)
    except Exception as e:
        return error_response(str(e))


@backtest_bp.route('/backtest/data-sources', methods=['GET'])
@login_required
def get_data_sources():
    """获取可用数据源列表"""
    try:
        user_id = request.current_user_id
        from ..models import Config

        data_sources = []

        # 免费数据源 - AKShare（优先）
        data_sources.append({
            'value': 'akshare',
            'name': 'AKShare',
            'available': True,
            'free': True,
            'description': '免费数据源，数据丰富'
        })

        # 免费数据源 - BaoStock（备用）
        data_sources.append({
            'value': 'baostock',
            'name': 'BaoStock',
            'available': True,
            'free': True,
            'description': '免费数据源，稳定可靠'
        })

        # 检查Tushare
        tushare_config = config_manager.get('tushare', {})
        db_token = Config.query.filter_by(key='tushare.token', user_id=user_id).first()
        has_tushare = bool(tushare_config.get('token') or (db_token and db_token.value))

        data_sources.append({
            'value': 'tushare',
            'name': 'Tushare Pro',
            'available': has_tushare,
            'free': False,
            'description': '专业金融数据接口，需要配置Token'
        })

        # 检查本地数据
        local_count = PriceHistory.query.filter_by(user_id=user_id).count()
        data_sources.append({
            'value': 'local',
            'name': '本地/数据库数据',
            'available': local_count > 0,
            'count': local_count,
            'free': True,
            'description': '已保存的历史价格数据'
        })

        return success_response(data_sources)
    except Exception as e:
        return error_response(str(e))


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@backtest_bp.route('/backtest/template', methods=['GET'])
@login_required
def download_template():
    """下载历史价格数据导入模板"""
    try:
        # 创建模板数据
        template_data = {
            'trade_date': ['2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', '2024-01-08'],
            'open': [4.123, 4.156, 4.089, 4.201, 4.234],
            'high': [4.256, 4.289, 4.178, 4.312, 4.356],
            'low': [4.089, 4.112, 4.045, 4.156, 4.189],
            'close': [4.201, 4.178, 4.134, 4.289, 4.312],
            'volume': [1234567, 1345678, 1123456, 1456789, 1567890]
        }

        df = pd.DataFrame(template_data)

        # 创建Excel文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='历史价格数据')

            # 添加说明sheet
            instructions = pd.DataFrame({
                '字段名': ['trade_date', 'open', 'high', 'low', 'close', 'volume'],
                '类型': ['日期', '数值', '数值', '数值', '数值', '数值(可选)'],
                '说明': [
                    '交易日期，格式：YYYY-MM-DD',
                    '开盘价',
                    '最高价',
                    '最低价',
                    '收盘价',
                    '成交量（可选）'
                ],
                '示例': ['2024-01-15', '4.123', '4.256', '4.089', '4.201', '1234567']
            })
            instructions.to_excel(writer, index=False, sheet_name='字段说明')

        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='历史价格数据导入模板.xlsx'
        )
    except Exception as e:
        return error_response(str(e))


@backtest_bp.route('/backtest/import-prices', methods=['POST'])
@login_required
def import_prices():
    """导入历史价格数据"""
    try:
        # 检查文件
        if 'file' not in request.files:
            return error_response('未找到上传文件')

        file = request.files['file']
        if file.filename == '':
            return error_response('未选择文件')

        if not allowed_file(file.filename):
            return error_response('不支持的文件格式，请使用xlsx、xls或csv')

        # 获取参数
        symbol = request.form.get('symbol', '')
        name = request.form.get('name', '')

        if not symbol:
            return error_response('请输入标的代码')

        # 读取文件
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()

        if ext == 'csv':
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        # 验证必需字段
        required_fields = ['trade_date', 'close']
        for field in required_fields:
            if field not in df.columns:
                return error_response(f'缺少必需字段: {field}')

        # 数据处理
        records = []
        user_id = request.current_user_id

        for _, row in df.iterrows():
            try:
                trade_date = pd.to_datetime(row['trade_date']).date()

                record = PriceHistory(
                    user_id=user_id,
                    symbol=symbol,
                    name=name or symbol,
                    trade_date=trade_date,
                    open_price=float(row.get('open', row.get('close', 0))) if pd.notna(row.get('open', row.get('close'))) else None,
                    high_price=float(row.get('high', row.get('close', 0))) if pd.notna(row.get('high', row.get('close'))) else None,
                    low_price=float(row.get('low', row.get('close', 0))) if pd.notna(row.get('low', row.get('close'))) else None,
                    close_price=float(row['close']) if pd.notna(row['close']) else None,
                    volume=int(row['volume']) if 'volume' in row and pd.notna(row['volume']) else None
                )
                records.append(record)
            except Exception as e:
                continue

        if not records:
            return error_response('没有有效数据可导入')

        # 批量插入
        db.session.bulk_save_objects(records)
        db.session.commit()

        return success_response({
            'message': f'成功导入 {len(records)} 条历史价格数据',
            'count': len(records),
            'symbol': symbol,
            'date_range': {
                'start': min(r.trade_date for r in records).isoformat(),
                'end': max(r.trade_date for r in records).isoformat()
            }
        })
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@backtest_bp.route('/backtest/price-histories', methods=['GET'])
@login_required
def get_price_histories():
    """获取已导入的历史价格数据列表"""
    try:
        user_id = request.current_user_id

        # 查询用户的所有历史数据，按symbol分组
        results = db.session.query(
            PriceHistory.symbol,
            PriceHistory.name,
            PriceHistory.asset_type,
            db.func.count(PriceHistory.id).label('count'),
            db.func.min(PriceHistory.trade_date).label('start_date'),
            db.func.max(PriceHistory.trade_date).label('end_date')
        ).filter(
            PriceHistory.user_id == user_id
        ).group_by(
            PriceHistory.symbol, PriceHistory.name, PriceHistory.asset_type
        ).all()

        histories = []
        need_update_funds = []  # 需要更新名称的基金

        for r in results:
            name = r.name
            # 如果是基金且没有名称，记录下来
            if r.asset_type == 'fund' and not name:
                need_update_funds.append(r.symbol)

            histories.append({
                'symbol': r.symbol,
                'name': name,
                'asset_type': r.asset_type or 'stock',
                'count': r.count,
                'start_date': r.start_date.isoformat() if r.start_date else None,
                'end_date': r.end_date.isoformat() if r.end_date else None
            })

        # 更新缺少名称的基金
        if need_update_funds:
            try:
                import akshare as ak
                for symbol in need_update_funds:
                    try:
                        fund_info = ak.fund_individual_basic_info_xq(symbol=symbol)
                        if fund_info is not None and len(fund_info) > 0:
                            name_row = fund_info[fund_info['item'] == '基金名称']
                            if not name_row.empty:
                                fund_name = name_row.iloc[0]['value']
                                # 更新数据库中的名称
                                PriceHistory.query.filter(
                                    PriceHistory.user_id == user_id,
                                    PriceHistory.symbol == symbol
                                ).update({'name': fund_name})
                                # 更新返回结果
                                for h in histories:
                                    if h['symbol'] == symbol:
                                        h['name'] = fund_name
                                logger.info(f"更新基金名称: {symbol} -> {fund_name}")
                    except Exception as e:
                        logger.warning(f"获取基金 {symbol} 名称失败: {str(e)}")
                        continue

                db.session.commit()
            except Exception as e:
                logger.warning(f"更新基金名称失败: {str(e)}")

        return success_response(histories)
    except Exception as e:
        return error_response(str(e))


@backtest_bp.route('/backtest/quick-select-symbols', methods=['GET'])
@login_required
def get_quick_select_symbols():
    """获取快速选择的股票/基金列表（从持仓和历史数据中获取）"""
    try:
        user_id = request.current_user_id
        from ..models import Position

        stocks = {}  # {symbol: name}
        funds = {}   # {symbol: name}

        # 1. 从持仓中获取
        positions = Position.query.filter_by(user_id=user_id).all()
        for p in positions:
            if p.asset_type in ['stock', 'etf_index', 'etf_sector']:
                if p.symbol not in stocks:
                    stocks[p.symbol] = p.name or p.symbol
            elif p.asset_type == 'fund':
                if p.symbol not in funds:
                    funds[p.symbol] = p.name or p.symbol

        # 2. 从历史数据中获取
        results = db.session.query(
            PriceHistory.symbol,
            PriceHistory.name,
            PriceHistory.asset_type
        ).filter(
            PriceHistory.user_id == user_id
        ).group_by(
            PriceHistory.symbol, PriceHistory.name, PriceHistory.asset_type
        ).all()

        for r in results:
            if r.asset_type == 'fund':
                if r.symbol not in funds:
                    funds[r.symbol] = r.name or r.symbol
            else:
                if r.symbol not in stocks:
                    stocks[r.symbol] = r.name or r.symbol

        return success_response({
            'stocks': [{'symbol': k, 'name': v} for k, v in sorted(stocks.items())],
            'funds': [{'symbol': k, 'name': v} for k, v in sorted(funds.items())]
        })
    except Exception as e:
        return error_response(str(e))


@backtest_bp.route('/backtest/price-histories/<symbol>', methods=['DELETE'])
@login_required
def delete_price_history(symbol):
    """删除指定标的的历史价格数据"""
    try:
        user_id = request.current_user_id

        deleted = PriceHistory.query.filter(
            PriceHistory.user_id == user_id,
            PriceHistory.symbol == symbol
        ).delete()

        db.session.commit()

        return success_response({
            'message': f'已删除 {deleted} 条记录',
            'deleted': deleted
        })
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@backtest_bp.route('/backtest/fetch-data', methods=['POST'])
@login_required
def fetch_data_from_source():
    """从在线数据源获取历史数据（支持股票/基金）"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '')
        name = data.get('name', symbol)
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        data_source = data.get('data_source', 'akshare')  # akshare, baostock, tushare, eastmoney
        asset_type = data.get('asset_type', 'stock')  # stock 或 fund

        if not symbol:
            return error_response('请输入标的代码')

        if not start_date or not end_date:
            return error_response('请选择开始和结束日期')

        user_id = request.current_user_id

        # 获取市场数据服务
        market_service = get_market_data_service()

        # 根据资产类型获取数据
        df = pd.DataFrame()

        if asset_type == 'fund':
            # 获取基金净值数据
            df = market_service.get_fund_nav_history(symbol, start_date, end_date, user_id=user_id)

            if df.empty:
                return error_response('未获取到基金数据，请检查基金代码和日期范围')

            # 自动获取基金名称
            if not name or name == symbol:
                try:
                    import akshare as ak
                    fund_info = ak.fund_individual_basic_info_xq(symbol=symbol)
                    if fund_info is not None and len(fund_info) > 0:
                        name_row = fund_info[fund_info['item'] == '基金名称']
                        if not name_row.empty:
                            name = name_row.iloc[0]['value']
                            logger.info(f"获取基金名称: {symbol} -> {name}")
                except Exception as e:
                    logger.warning(f"获取基金名称失败: {str(e)}")

            # 将基金净值数据转换为回测格式（用nav作为close）
            if 'nav' in df.columns:
                df['close'] = df['nav']
            if 'date' not in df.columns and df.index.name == 'date':
                df = df.reset_index()

            # 保存到数据库
            records = []
            for _, row in df.iterrows():
                date_val = row.get('date')
                if pd.isna(date_val):
                    continue

                record = PriceHistory(
                    user_id=user_id,
                    symbol=symbol,
                    name=name,
                    asset_type='fund',
                    trade_date=pd.to_datetime(date_val).date(),
                    close_price=float(row['close']) if pd.notna(row.get('close')) else None,
                    acc_nav=float(row['acc_nav']) if pd.notna(row.get('acc_nav')) else None,
                    change_pct=float(row['change_pct']) if pd.notna(row.get('change_pct')) else None,
                    data_source='eastmoney'
                )
                records.append(record)

            if records:
                # 删除该symbol在日期范围内的旧数据
                PriceHistory.query.filter(
                    PriceHistory.user_id == user_id,
                    PriceHistory.symbol == symbol,
                    PriceHistory.trade_date >= pd.to_datetime(start_date).date(),
                    PriceHistory.trade_date <= pd.to_datetime(end_date).date()
                ).delete()
                db.session.bulk_save_objects(records)
                db.session.commit()

            return success_response({
                'success': True,
                'message': f'成功获取 {len(records)} 条基金净值数据',
                'count': len(records),
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date,
                'asset_type': 'fund',
                'data_source': 'eastmoney'
            })

        else:
            # 获取股票数据
            if data_source == 'tushare':
                tushare_service = get_tushare_service()
                if not tushare_service.token:
                    return error_response('Tushare未配置，请先在系统设置中配置Token')
                ts_code = tushare_service.convert_symbol_to_ts_code(symbol)
                df = tushare_service.get_stock_daily(ts_code, start_date.replace('-', ''), end_date.replace('-', ''))
            elif data_source in ['akshare', 'baostock']:
                df = market_service.get_stock_history(symbol, start_date, end_date, user_id=user_id)

            if df.empty:
                return error_response('未获取到股票数据，请检查股票代码和日期范围')

            # 保存到数据库
            records = []
            for _, row in df.iterrows():
                date_val = row.get('date') or row.get('trade_date')
                if pd.isna(date_val):
                    continue

                record = PriceHistory(
                    user_id=user_id,
                    symbol=symbol,
                    name=name,
                    asset_type='stock',
                    trade_date=pd.to_datetime(date_val).date(),
                    open_price=float(row['open']) if pd.notna(row.get('open')) else None,
                    high_price=float(row['high']) if pd.notna(row.get('high')) else None,
                    low_price=float(row['low']) if pd.notna(row.get('low')) else None,
                    close_price=float(row['close']) if pd.notna(row.get('close')) else None,
                    volume=int(row['volume']) if pd.notna(row.get('volume')) else None,
                    turnover=float(row['amount']) if pd.notna(row.get('amount')) else None,
                    change_pct=float(row['pct_chg']) if pd.notna(row.get('pct_chg')) else None,
                    data_source=data_source
                )
                records.append(record)

            if not records:
                return error_response('数据解析失败')

            # 删除该symbol在日期范围内的旧数据
            PriceHistory.query.filter(
                PriceHistory.user_id == user_id,
                PriceHistory.symbol == symbol,
                PriceHistory.trade_date >= pd.to_datetime(start_date).date(),
                PriceHistory.trade_date <= pd.to_datetime(end_date).date()
            ).delete()

            db.session.bulk_save_objects(records)
            db.session.commit()

            return success_response({
                'success': True,
                'message': f'成功获取 {len(records)} 条股票数据',
                'count': len(records),
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date,
                'asset_type': 'stock',
                'data_source': data_source
            })
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return error_response(str(e))


@backtest_bp.route('/backtest/run', methods=['POST'])
@login_required
def run_backtest():
    """运行回测（支持多策略对比，多数据源，股票/基金）"""
    try:
        data = request.get_json()
        user_id = request.current_user_id

        # 获取参数
        symbol = data.get('symbol', '')
        data_source = data.get('data_source', 'akshare')  # akshare, baostock, tushare, local, eastmoney
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        initial_capital = float(data.get('initial_capital', 100000))
        strategies = data.get('strategies', ['double_ma'])  # 策略列表
        strategy_params = data.get('strategy_params', {})  # 各策略参数
        asset_type = data.get('asset_type', 'stock')  # stock 或 fund

        # 默认时间范围
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - pd.DateOffset(years=1)).strftime('%Y-%m-%d')

        # 获取市场数据服务
        market_service = get_market_data_service()

        # 获取价格数据 - 优先从数据库读取
        price_df = None

        if asset_type == 'fund':
            # 获取基金净值数据（内部会先查数据库）
            price_df = market_service.get_fund_nav_history(symbol, start_date, end_date, user_id=user_id)

            if price_df.empty:
                return error_response(f'未获取到基金 {symbol} 的净值数据，请检查基金代码')

            # 将净值数据转换为回测格式
            # 确保 close 列存在（用于回测）
            if 'close' not in price_df.columns and 'nav' in price_df.columns:
                price_df['close'] = price_df['nav']
            if 'date' not in price_df.columns:
                price_df = price_df.reset_index()

        else:
            # 股票数据：优先从数据库读取，不足时再从在线获取
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()

            # 1. 先查数据库
            histories = PriceHistory.query.filter(
                PriceHistory.user_id == user_id,
                PriceHistory.symbol == symbol,
                PriceHistory.trade_date >= start_dt,
                PriceHistory.trade_date <= end_dt
            ).order_by(PriceHistory.trade_date).all()

            if histories and len(histories) >= 5:
                # 数据库有足够数据，直接使用
                logger.info(f"从数据库读取 {symbol} 历史数据 {len(histories)} 条")
                price_df = pd.DataFrame([{
                    'date': h.trade_date.isoformat(),
                    'open': float(h.open_price) if h.open_price else None,
                    'high': float(h.high_price) if h.high_price else None,
                    'low': float(h.low_price) if h.low_price else None,
                    'close': float(h.close_price) if h.close_price else None,
                    'volume': float(h.volume) if h.volume else None
                } for h in histories])
            else:
                # 2. 数据库数据不足，从在线数据源获取
                logger.info(f"数据库数据不足({len(histories) if histories else 0}条)，从在线数据源获取")

                if data_source == 'akshare':
                    # 从AKShare获取股票数据
                    try:
                        from ..services.akshare_service import get_akshare_service
                        ak = get_akshare_service()
                        price_df = ak.get_stock_daily(symbol, start_date, end_date)

                        # 保存到数据库
                        if not price_df.empty:
                            _save_backtest_data(user_id, symbol, price_df, 'akshare')
                    except Exception as e:
                        logger.warning(f"AKShare获取数据失败: {str(e)}，尝试BaoStock")
                        price_df = pd.DataFrame()  # 重置为空，尝试BaoStock

                    # AKShare失败或返回空，尝试BaoStock
                    if price_df.empty:
                        try:
                            from ..services.baostock_service import get_baostock_service
                            bs = get_baostock_service()
                            price_df = bs.get_stock_daily(symbol, start_date, end_date)

                            if not price_df.empty:
                                _save_backtest_data(user_id, symbol, price_df, 'baostock')
                        except Exception as e2:
                            logger.warning(f"BaoStock获取数据也失败: {str(e2)}")

                elif data_source == 'baostock':
                    # 从BaoStock获取数据
                    try:
                        from ..services.baostock_service import get_baostock_service
                        bs = get_baostock_service()
                        price_df = bs.get_stock_daily(symbol, start_date, end_date)

                        # 保存到数据库
                        if not price_df.empty:
                            _save_backtest_data(user_id, symbol, price_df, 'baostock')
                    except Exception as e:
                        logger.warning(f"BaoStock获取数据失败: {str(e)}")

                elif data_source == 'tushare':
                    # 从Tushare获取数据
                    tushare_service = get_tushare_service()
                    if tushare_service.token:
                        ts_code = tushare_service.convert_symbol_to_ts_code(symbol)
                        start = start_date.replace('-', '')
                        end = end_date.replace('-', '')

                        price_df = tushare_service.get_stock_daily(ts_code, start, end)

                        if not price_df.empty:
                            _save_backtest_data(user_id, symbol, price_df, 'tushare')

                else:
                    # local 或其他：使用 market_data_service（内部会自动获取并保存）
                    price_df = market_service.get_stock_history(symbol, start_date, end_date, user_id=user_id)

        if price_df is None or price_df.empty or len(price_df) < 5:
            return error_response('数据不足，无法进行回测')

        # 确保date列格式正确
        if 'date' in price_df.columns:
            price_df['date'] = pd.to_datetime(price_df['date']).dt.strftime('%Y-%m-%d')

        # 转换策略类型
        strategy_types = []
        for s in strategies:
            try:
                strategy_types.append(StrategyType(s))
            except ValueError:
                pass  # 忽略无效策略

        if not strategy_types:
            return error_response('请选择至少一个策略')

        # 自动添加全仓持有策略作为基准（如果用户没有选择）
        if StrategyType.BUY_AND_HOLD not in strategy_types:
            strategy_types.append(StrategyType.BUY_AND_HOLD)

        # 运行多策略回测
        results = run_multi_strategy_backtest(
            data=price_df,
            strategy_types=strategy_types,
            strategy_params=strategy_params,
            initial_capital=initial_capital,
            symbol=symbol
        )

        # 转换结果
        response_data = {
            'symbol': symbol,
            'data_source': data_source,
            'asset_type': asset_type,
            'initial_capital': initial_capital,
            'start_date': price_df['date'].iloc[0],
            'end_date': price_df['date'].iloc[-1],
            'data_count': len(price_df),
            'strategies': []
        }

        for strategy_value, result in results.items():
            strategy_result = {
                'strategy': strategy_value,
                'strategy_name': result.strategy_name,
                'total_return': round(result.total_return * 100, 2),
                'annual_return': round(result.annual_return * 100, 2),
                'max_drawdown': round(result.max_drawdown * 100, 2),
                'sharpe_ratio': round(result.sharpe_ratio, 3),
                'win_rate': round(result.win_rate * 100, 1),
                'trade_count': result.trade_count,
                'final_value': round(result.final_value, 2),
                'summary': result.summary,
                'daily_values': result.daily_values,
                'records': [{
                    'date': r.date,
                    'price': round(r.price, 4),
                    'action': r.action,
                    'shares': r.shares,
                    'amount': round(r.amount, 2),
                    'total_value': round(r.total_value, 2),
                    'profit_rate': round(r.profit_rate * 100, 2)
                } for r in result.records]
            }
            response_data['strategies'].append(strategy_result)

        # 按收益率排序
        response_data['strategies'].sort(key=lambda x: x['total_return'], reverse=True)

        # 找出最佳策略
        best_strategy = response_data['strategies'][0] if response_data['strategies'] else None

        # 保存回测历史
        try:
            from datetime import date as date_type

            start_dt = datetime.strptime(response_data['start_date'], '%Y-%m-%d').date()
            end_dt = datetime.strptime(response_data['end_date'], '%Y-%m-%d').date()

            # 检查是否已存在相同的历史记录
            existing = BacktestHistory.query.filter_by(
                user_id=user_id,
                symbol=symbol,
                start_date=start_dt,
                end_date=end_dt
            ).first()

            if existing:
                # 更新现有记录
                existing.results = json.dumps(response_data, ensure_ascii=False)
                existing.strategy_type = 'multi' if len(strategies) > 1 else strategies[0]
                existing.best_strategy = best_strategy['strategy_name'] if best_strategy else None
                existing.best_return = best_strategy['total_return'] if best_strategy else None
                logger.info(f"更新回测历史记录: {symbol} {start_dt} ~ {end_dt}")
            else:
                # 创建新记录
                history_record = BacktestHistory(
                    user_id=user_id,
                    symbol=symbol,
                    name=response_data.get('name'),
                    start_date=start_dt,
                    end_date=end_dt,
                    initial_capital=initial_capital,
                    strategy_type='multi' if len(strategies) > 1 else strategies[0],
                    results=json.dumps(response_data, ensure_ascii=False),
                    best_strategy=best_strategy['strategy_name'] if best_strategy else None,
                    best_return=best_strategy['total_return'] if best_strategy else None
                )
                db.session.add(history_record)
                logger.info(f"保存回测历史记录: {symbol} {start_dt} ~ {end_dt}")

            db.session.commit()
        except Exception as save_error:
            db.session.rollback()
            logger.warning(f"保存回测历史失败: {str(save_error)}")

        return success_response(response_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(str(e))


@backtest_bp.route('/backtest/compare', methods=['POST'])
@login_required
def compare_scenarios():
    """比较不同策略（兼容旧API）"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '')
        initial_capital = float(data.get('initial_capital', 100000))

        user_id = request.current_user_id

        # 获取本地数据
        histories = PriceHistory.query.filter(
            PriceHistory.user_id == user_id,
            PriceHistory.symbol == symbol
        ).order_by(PriceHistory.trade_date).all()

        if not histories:
            return error_response(f'未找到标的 {symbol} 的历史数据')

        price_df = pd.DataFrame([{
            'date': h.trade_date.isoformat(),
            'close': float(h.close_price) if h.close_price else None,
            'open': float(h.open_price) if h.open_price else None,
            'high': float(h.high_price) if h.high_price else None,
            'low': float(h.low_price) if h.low_price else None,
            'volume': float(h.volume) if h.volume else None
        } for h in histories])

        # 运行所有策略
        strategy_types = list(StrategyType)
        results = run_multi_strategy_backtest(
            data=price_df,
            strategy_types=strategy_types,
            initial_capital=initial_capital,
            symbol=symbol
        )

        comparison = []
        for strategy_value, result in results.items():
            comparison.append({
                'strategy': strategy_value,
                'strategy_name': result.strategy_name,
                'total_return': round(result.total_return * 100, 2),
                'max_drawdown': round(result.max_drawdown * 100, 2),
                'sharpe_ratio': round(result.sharpe_ratio, 3),
                'win_rate': round(result.win_rate * 100, 1),
                'trade_count': result.trade_count,
                'final_value': round(result.final_value, 2)
            })

        # 按收益率排序
        comparison.sort(key=lambda x: x['total_return'], reverse=True)

        return success_response({
            'initial_capital': initial_capital,
            'symbol': symbol,
            'data_count': len(price_df),
            'comparison': comparison
        })
    except Exception as e:
        return error_response(str(e))


def _save_backtest_data(user_id: int, symbol: str, price_df: pd.DataFrame, data_source: str):
    """保存回测数据到数据库"""
    try:
        from sqlalchemy import and_

        saved_count = 0
        for _, row in price_df.iterrows():
            trade_date = row.get('date')
            if isinstance(trade_date, str):
                trade_date = datetime.strptime(trade_date, '%Y-%m-%d').date()
            elif hasattr(trade_date, 'date'):
                trade_date = trade_date.date()

            # 检查是否已存在
            existing = PriceHistory.query.filter(
                and_(
                    PriceHistory.user_id == user_id,
                    PriceHistory.symbol == symbol,
                    PriceHistory.trade_date == trade_date
                )
            ).first()

            if existing:
                continue

            record = PriceHistory(
                user_id=user_id,
                symbol=symbol,
                asset_type='stock',
                trade_date=trade_date,
                open_price=float(row['open']) if pd.notna(row.get('open')) else None,
                high_price=float(row['high']) if pd.notna(row.get('high')) else None,
                low_price=float(row['low']) if pd.notna(row.get('low')) else None,
                close_price=float(row['close']) if pd.notna(row.get('close')) else None,
                volume=float(row['volume']) if pd.notna(row.get('volume')) else None,
                turnover=float(row['turnover']) if pd.notna(row.get('turnover')) else None,
                data_source=data_source
            )
            db.session.add(record)
            saved_count += 1

        if saved_count > 0:
            db.session.commit()
            print(f"保存回测数据: {symbol} {saved_count} 条")

    except Exception as e:
        db.session.rollback()
        print(f"保存回测数据失败: {e}")


# ==================== 回测历史 API ====================

@backtest_bp.route('/backtest/history', methods=['GET'])
@login_required
def get_backtest_history():
    """获取回测历史列表"""
    try:
        user_id = request.current_user_id

        histories = BacktestHistory.query.filter_by(user_id=user_id).order_by(
            BacktestHistory.created_at.desc()
        ).limit(50).all()

        result = [{
            'id': h.id,
            'symbol': h.symbol,
            'name': h.name,
            'start_date': h.start_date.isoformat(),
            'end_date': h.end_date.isoformat(),
            'initial_capital': float(h.initial_capital),
            'strategy_type': h.strategy_type,
            'best_strategy': h.best_strategy,
            'best_return': float(h.best_return) if h.best_return else None,
            'created_at': h.created_at.isoformat() if h.created_at else None
        } for h in histories]

        return success_response(result)
    except Exception as e:
        return error_response(str(e))


@backtest_bp.route('/backtest/history/<int:history_id>', methods=['GET'])
@login_required
def get_backtest_history_detail(history_id):
    """获取回测历史详情"""
    try:
        user_id = request.current_user_id

        history = BacktestHistory.query.filter_by(id=history_id, user_id=user_id).first()

        if not history:
            return error_response('历史记录不存在')

        result = {
            'id': history.id,
            'symbol': history.symbol,
            'name': history.name,
            'start_date': history.start_date.isoformat(),
            'end_date': history.end_date.isoformat(),
            'initial_capital': float(history.initial_capital),
            'strategy_type': history.strategy_type,
            'best_strategy': history.best_strategy,
            'best_return': float(history.best_return) if history.best_return else None,
            'created_at': history.created_at.isoformat() if history.created_at else None,
            'results': json.loads(history.results) if history.results else None
        }

        return success_response(result)
    except Exception as e:
        return error_response(str(e))


@backtest_bp.route('/backtest/history/<int:history_id>', methods=['DELETE'])
@login_required
def delete_backtest_history(history_id):
    """删除回测历史"""
    try:
        user_id = request.current_user_id

        history = BacktestHistory.query.filter_by(id=history_id, user_id=user_id).first()

        if not history:
            return error_response('历史记录不存在')

        db.session.delete(history)
        db.session.commit()

        return success_response({'message': '删除成功'})
    except Exception as e:
        return error_response(str(e))