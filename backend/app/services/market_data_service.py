#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一市场数据服务
整合多数据源，提供统一的数据访问接口
支持股票/基金分离配置，自动降级
数据存入数据库，只获取缺失的日期数据
"""

import pandas as pd
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, date
import logging
import time
import threading

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    统一市场数据服务

    数据源优先级：
    - 股票数据：用户配置 > AKShare > BaoStock
    - 基金数据：用户配置 > 天天基金 > AKShare

    数据存储策略：
    - 历史数据存入数据库，不会重复获取
    - 每次只获取数据库中缺失的日期数据
    """

    # 数据源类型
    SOURCE_AKSHARE = 'akshare'
    SOURCE_BAOSTOCK = 'baostock'
    SOURCE_TUSHARE = 'tushare'
    SOURCE_EASTMONEY = 'eastmoney'

    # 请求限流配置
    REQUEST_INTERVAL = 0.5  # 每次请求间隔（秒）

    def __init__(self):
        self._lock = threading.Lock()
        self._last_request_time = 0

    def _rate_limit(self):
        """API 请求频率限制"""
        with self._lock:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.REQUEST_INTERVAL:
                time.sleep(self.REQUEST_INTERVAL - elapsed)
            self._last_request_time = time.time()

    # ============ 用户配置获取 ============

    def get_user_stock_datasource_config(self, user_id: int) -> Dict[str, Any]:
        """获取用户的股票数据源配置"""
        from ..models import Config

        config = {
            'type': 'default',
            'tushare_token': None,
            'tushare_base_url': 'https://api.tushare.pro'
        }

        ds_type = Config.query.filter_by(key='stock_datasource.type', user_id=user_id).first()
        if ds_type:
            config['type'] = ds_type.value

        token = Config.query.filter_by(key='stock_datasource.tushare_token', user_id=user_id).first()
        if token and token.value:
            config['tushare_token'] = token.value

        base_url = Config.query.filter_by(key='stock_datasource.tushare_base_url', user_id=user_id).first()
        if base_url and base_url.value:
            config['tushare_base_url'] = base_url.value

        return config

    def get_user_fund_datasource_config(self, user_id: int) -> Dict[str, Any]:
        """获取用户的基金数据源配置"""
        from ..models import Config

        config = {
            'type': 'default',
            'tushare_token': None
        }

        ds_type = Config.query.filter_by(key='fund_datasource.type', user_id=user_id).first()
        if ds_type:
            config['type'] = ds_type.value

        token = Config.query.filter_by(key='fund_datasource.tushare_token', user_id=user_id).first()
        if token and token.value:
            config['tushare_token'] = token.value

        return config

    # ============ 数据库查询 ============

    def _get_existing_dates(self, user_id: int, symbol: str) -> set:
        """获取数据库中已存在的日期"""
        from ..models import PriceHistory

        records = PriceHistory.query.filter_by(
            user_id=user_id,
            symbol=symbol
        ).with_entities(PriceHistory.trade_date).all()

        return {r.trade_date for r in records if r.trade_date}

    def _get_date_range(self, user_id: int, symbol: str) -> Tuple[Optional[date], Optional[date]]:
        """获取数据库中该标的的日期范围"""
        from ..models import PriceHistory
        from sqlalchemy import func

        result = PriceHistory.query.filter_by(
            user_id=user_id,
            symbol=symbol
        ).with_entities(
            func.min(PriceHistory.trade_date).label('min_date'),
            func.max(PriceHistory.trade_date).label('max_date')
        ).first()

        if result and result.min_date and result.max_date:
            return result.min_date, result.max_date
        return None, None

    # ============ 股票数据接口 ============

    def get_stock_realtime(self, symbols: List[str], user_id: int = None) -> Dict[str, Dict]:
        """
        获取股票实时行情

        Args:
            symbols: 股票代码列表
            user_id: 用户ID

        Returns:
            dict: {symbol: {name, price, change_pct, volume, ...}}
        """
        result = {}

        config = self.get_user_stock_datasource_config(user_id) if user_id else {}
        self._rate_limit()

        # 优先级：用户配置的 Tushare > AKShare > BaoStock

        # 1. 尝试用户配置的 Tushare
        if config.get('type') == 'tushare' and config.get('tushare_token'):
            try:
                from .tushare_service import TushareService
                service = TushareService(token=config['tushare_token'])
                prices = service.get_multiple_stocks_prices(symbols)
                for symbol, price in prices.items():
                    result[symbol] = {'price': price, 'source': 'tushare'}
                logger.info(f"Tushare 获取 {len(result)} 只股票实时价格")
                return result
            except Exception as e:
                logger.warning(f"Tushare 获取失败: {str(e)}，尝试其他数据源")

        # 2. 尝试 AKShare
        try:
            from .akshare_service import get_akshare_service
            service = get_akshare_service()
            result = service.get_stock_realtime(symbols)
            for symbol in result:
                result[symbol]['source'] = 'akshare'
            logger.info(f"AKShare 获取 {len(result)} 只股票实时价格")
            if result:
                return result
        except Exception as e:
            logger.warning(f"AKShare 获取失败: {str(e)}，尝试 BaoStock")

        # 3. 尝试 BaoStock
        try:
            from .baostock_service import get_baostock_service
            service = get_baostock_service()
            prices = service.get_multiple_stocks_prices(symbols)
            for symbol, price in prices.items():
                result[symbol] = {'price': price, 'source': 'baostock'}
            logger.info(f"BaoStock 获取 {len(result)} 只股票实时价格")
        except Exception as e:
            logger.error(f"所有数据源获取失败: {str(e)}")

        return result

    def get_stock_history(self, symbol: str, start_date: str, end_date: str,
                          user_id: int = None, force_refresh: bool = False) -> pd.DataFrame:
        """
        获取股票历史数据（优先从数据库读取，只获取缺失部分）

        Args:
            symbol: 股票代码
            start_date: 开始日期 '2023-01-01'
            end_date: 结束日期 '2024-01-01'
            user_id: 用户ID
            force_refresh: 是否强制刷新（重新获取所有数据）

        Returns:
            DataFrame: 历史数据
        """
        from ..models import PriceHistory

        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()

        # 检查数据库中是否已有数据
        if not force_refresh and user_id:
            min_date, max_date = self._get_date_range(user_id, symbol)

            # 如果数据库中有数据且覆盖了请求范围，直接返回
            if min_date and max_date:
                if min_date <= start_dt and max_date >= end_dt:
                    # 从数据库读取
                    records = PriceHistory.query.filter_by(
                        user_id=user_id,
                        symbol=symbol
                    ).filter(
                        PriceHistory.trade_date >= start_dt,
                        PriceHistory.trade_date <= end_dt
                    ).order_by(PriceHistory.trade_date).all()

                    if records:
                        logger.info(f"从数据库读取 {symbol} 历史数据 {len(records)} 条")
                        return self._price_history_to_df(records)

                # 计算需要获取的日期范围
                if max_date < end_dt:
                    # 需要获取 max_date+1 到 end_dt 的数据
                    fetch_start = (max_date + timedelta(days=1)).strftime('%Y-%m-%d')
                    fetch_end = end_date
                    new_df = self._fetch_stock_history_from_api(symbol, fetch_start, fetch_end, user_id)

                    if not new_df.empty:
                        self._save_price_history(user_id, symbol, new_df)

                    # 合并数据库和新获取的数据
                    return self._merge_db_and_new_data(user_id, symbol, start_date, end_date, new_df)

                if min_date > start_dt:
                    # 需要获取 start_date 到 min_date-1 的数据
                    fetch_start = start_date
                    fetch_end = (min_date - timedelta(days=1)).strftime('%Y-%m-%d')
                    new_df = self._fetch_stock_history_from_api(symbol, fetch_start, fetch_end, user_id)

                    if not new_df.empty:
                        self._save_price_history(user_id, symbol, new_df)

                    return self._merge_db_and_new_data(user_id, symbol, start_date, end_date, new_df)

        # 从API获取全部数据
        df = self._fetch_stock_history_from_api(symbol, start_date, end_date, user_id)

        if not df.empty and user_id:
            self._save_price_history(user_id, symbol, df)

        return df

    def _fetch_stock_history_from_api(self, symbol: str, start_date: str, end_date: str,
                                       user_id: int = None) -> pd.DataFrame:
        """从API获取股票历史数据（按优先级尝试各数据源）"""
        config = self.get_user_stock_datasource_config(user_id) if user_id else {}
        self._rate_limit()

        # 1. 尝试用户配置的 Tushare
        if config.get('type') == 'tushare' and config.get('tushare_token'):
            try:
                from .tushare_service import TushareService
                service = TushareService(token=config['tushare_token'])
                ts_code = service.convert_symbol_to_ts_code(symbol)
                df = service.get_stock_daily(ts_code, start_date.replace('-', ''),
                                             end_date.replace('-', ''))
                if not df.empty:
                    logger.info(f"Tushare 获取 {symbol} 历史数据 {len(df)} 条")
                    return df
            except Exception as e:
                logger.warning(f"Tushare 获取历史数据失败: {str(e)}")

        # 2. 尝试 AKShare
        try:
            from .akshare_service import get_akshare_service
            service = get_akshare_service()
            df = service.get_stock_daily(symbol, start_date, end_date)
            if not df.empty:
                logger.info(f"AKShare 获取 {symbol} 历史数据 {len(df)} 条")
                return df
        except Exception as e:
            logger.warning(f"AKShare 获取历史数据失败: {str(e)}")

        # 3. 尝试 BaoStock
        try:
            from .baostock_service import get_baostock_service
            service = get_baostock_service()
            df = service.get_stock_daily(symbol, start_date, end_date)
            if not df.empty:
                logger.info(f"BaoStock 获取 {symbol} 历史数据 {len(df)} 条")
                return df
        except Exception as e:
            logger.error(f"所有数据源获取历史数据失败: {str(e)}")

        return pd.DataFrame()

    def get_stock_all_history(self, symbol: str, years: int = 5,
                              user_id: int = None) -> pd.DataFrame:
        """获取股票全部历史数据"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=years*365)).strftime('%Y-%m-%d')
        return self.get_stock_history(symbol, start_date, end_date, user_id)

    # ============ 基金数据接口 ============

    def get_fund_realtime(self, fund_codes: List[str], user_id: int = None) -> Dict[str, Dict]:
        """
        获取基金实时净值

        Args:
            fund_codes: 基金代码列表
            user_id: 用户ID

        Returns:
            dict: {fund_code: {nav, name, change_pct, ...}}
        """
        result = {}

        config = self.get_user_fund_datasource_config(user_id) if user_id else {}
        self._rate_limit()

        # 优先级：用户配置的 Tushare > 天天基金 > AKShare

        # 1. 尝试用户配置的 Tushare
        if config.get('type') == 'tushare' and config.get('tushare_token'):
            try:
                # Tushare 基金接口需要额外权限
                pass
            except Exception as e:
                logger.warning(f"Tushare 基金数据获取失败: {str(e)}")

        # 2. 尝试天天基金
        try:
            from .eastmoney_fund_service import get_eastmoney_fund_service
            service = get_eastmoney_fund_service()
            result = service.get_fund_realtime(fund_codes)
            for code in result:
                result[code]['source'] = 'eastmoney'
            logger.info(f"天天基金获取 {len(result)} 只基金实时净值")
            if result:
                return result
        except Exception as e:
            logger.warning(f"天天基金获取失败: {str(e)}")

        # 3. 尝试 AKShare（备用）
        try:
            import akshare as ak
            for code in fund_codes:
                try:
                    df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
                    if df is not None and len(df) > 0:
                        latest = df.iloc[-1]
                        result[code] = {
                            'nav': float(latest.get('单位净值', 0)),
                            'name': '',
                            'source': 'akshare'
                        }
                except:
                    continue
            if result:
                logger.info(f"AKShare 获取 {len(result)} 只基金净值")
        except Exception as e:
            logger.warning(f"AKShare 获取基金净值失败: {str(e)}")

        return result

    def get_fund_nav_history(self, fund_code: str, start_date: str, end_date: str,
                             user_id: int = None, force_refresh: bool = False) -> pd.DataFrame:
        """
        获取基金净值历史（优先从数据库读取，只获取缺失部分）

        Args:
            fund_code: 基金代码
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户ID
            force_refresh: 是否强制刷新

        Returns:
            DataFrame: 净值历史
        """
        from ..models import PriceHistory

        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()

        # 检查数据库中是否已有数据
        if not force_refresh and user_id:
            min_date, max_date = self._get_date_range(user_id, fund_code)

            if min_date and max_date:
                if min_date <= start_dt and max_date >= end_dt:
                    records = PriceHistory.query.filter_by(
                        user_id=user_id,
                        symbol=fund_code
                    ).filter(
                        PriceHistory.trade_date >= start_dt,
                        PriceHistory.trade_date <= end_dt
                    ).order_by(PriceHistory.trade_date).all()

                    if records:
                        logger.info(f"从数据库读取 {fund_code} 基金净值 {len(records)} 条")
                        df = self._price_history_to_df(records)
                        # 确保基金数据有 nav 字段
                        if 'nav' not in df.columns and 'close' in df.columns:
                            df['nav'] = df['close']
                        return df

                # 只获取缺失的日期范围
                if max_date < end_dt:
                    fetch_start = (max_date + timedelta(days=1)).strftime('%Y-%m-%d')
                    fetch_end = end_date
                    new_df = self._fetch_fund_nav_from_api(fund_code, fetch_start, fetch_end, user_id)

                    if not new_df.empty:
                        self._save_fund_nav_history(user_id, fund_code, new_df)

                    return self._merge_db_and_new_data(user_id, fund_code, start_date, end_date, new_df)

        # 从API获取数据
        df = self._fetch_fund_nav_from_api(fund_code, start_date, end_date, user_id)

        if not df.empty and user_id:
            self._save_fund_nav_history(user_id, fund_code, df)
            # 确保基金数据有 nav 字段
            if 'nav' not in df.columns and 'close' in df.columns:
                df['nav'] = df['close']

        return df

    def _fetch_fund_nav_from_api(self, fund_code: str, start_date: str, end_date: str,
                                  user_id: int = None) -> pd.DataFrame:
        """从API获取基金净值历史（按优先级尝试各数据源）

        优先级：用户配置 > AKShare > 天天基金
        """
        config = self.get_user_fund_datasource_config(user_id) if user_id else {}
        self._rate_limit()

        datasource_type = config.get('type', 'default')

        # 根据用户配置的数据源类型决定优先级
        if datasource_type == 'eastmoney':
            # 用户选择优先天天基金
            # 1. 尝试天天基金
            try:
                from .eastmoney_fund_service import get_eastmoney_fund_service
                service = get_eastmoney_fund_service()
                df = service.get_fund_nav_history(fund_code, start_date, end_date)
                if not df.empty:
                    logger.info(f"天天基金获取 {fund_code} 净值历史 {len(df)} 条")
                    return df
            except Exception as e:
                logger.warning(f"天天基金获取净值历史失败: {str(e)}")

            # 2. 降级到 AKShare
            try:
                import akshare as ak
                df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
                if df is not None and len(df) > 0:
                    df = df.rename(columns={
                        '净值日期': 'date',
                        '单位净值': 'nav',
                        '日增长率': 'change_pct'
                    })
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
                        logger.info(f"AKShare 获取 {fund_code} 净值历史 {len(df)} 条")
                        return df
            except Exception as e:
                logger.warning(f"AKShare 获取基金净值失败: {str(e)}")

        else:
            # 默认或用户选择优先 AKShare
            # 1. 尝试 AKShare
            try:
                import akshare as ak
                df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
                if df is not None and len(df) > 0:
                    df = df.rename(columns={
                        '净值日期': 'date',
                        '单位净值': 'nav',
                        '日增长率': 'change_pct'
                    })
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
                        logger.info(f"AKShare 获取 {fund_code} 净值历史 {len(df)} 条")
                        return df
            except Exception as e:
                logger.warning(f"AKShare 获取基金净值失败: {str(e)}")

            # 2. 降级到天天基金
            try:
                from .eastmoney_fund_service import get_eastmoney_fund_service
                service = get_eastmoney_fund_service()
                df = service.get_fund_nav_history(fund_code, start_date, end_date)
                if not df.empty:
                    logger.info(f"天天基金获取 {fund_code} 净值历史 {len(df)} 条")
                    return df
            except Exception as e:
                logger.warning(f"天天基金获取净值历史失败: {str(e)}")

        return pd.DataFrame()

    def get_fund_all_nav_history(self, fund_code: str, years: int = 5,
                                  user_id: int = None) -> pd.DataFrame:
        """获取基金全部净值历史"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=years*365)).strftime('%Y-%m-%d')
        return self.get_fund_nav_history(fund_code, start_date, end_date, user_id)

    # ============ 指数数据接口 ============

    def get_index_history(self, symbol: str, start_date: str, end_date: str,
                          user_id: int = None) -> pd.DataFrame:
        """获取指数历史数据"""
        self._rate_limit()

        # 优先 AKShare
        try:
            from .akshare_service import get_akshare_service
            service = get_akshare_service()
            df = service.get_index_daily(symbol, start_date, end_date)
            if not df.empty:
                return df
        except Exception as e:
            logger.warning(f"AKShare 指数数据获取失败: {str(e)}")

        # 降级到 BaoStock
        try:
            from .baostock_service import get_baostock_service
            service = get_baostock_service()
            df = service.get_index_daily(symbol, start_date, end_date)
            if not df.empty:
                return df
        except Exception as e:
            logger.error(f"指数数据获取失败: {str(e)}")

        return pd.DataFrame()

    # ============ 持仓数据同步 ============

    def sync_position_prices(self, user_id: int) -> Dict[str, Any]:
        """同步用户持仓的最新价格，并更新市值和收益率，同时获取近一周历史数据"""
        from ..models import Position
        from .. import db

        positions = Position.query.filter_by(user_id=user_id).filter(Position.quantity > 0).all()

        if not positions:
            return {"success": True, "message": "无持仓数据", "updated": 0}

        stock_symbols = []
        fund_codes = []
        etf_symbols = []

        for p in positions:
            if p.asset_type in ['stock']:
                stock_symbols.append(p.symbol)
            elif p.asset_type == 'fund':
                fund_codes.append(p.symbol)
            elif p.asset_type in ['etf_index', 'etf_sector']:
                etf_symbols.append(p.symbol)

        updated = 0
        errors = []
        price_data = {}  # 用于存储所有价格数据

        # 获取股票价格
        if stock_symbols:
            try:
                stock_prices = self.get_stock_realtime(stock_symbols, user_id)
                price_data.update(stock_prices)
            except Exception as e:
                errors.append(f"获取股票价格失败: {str(e)}")

        # 获取基金净值
        if fund_codes:
            try:
                fund_navs = self.get_fund_realtime(fund_codes, user_id)
                price_data.update(fund_navs)
            except Exception as e:
                errors.append(f"获取基金净值失败: {str(e)}")

        # 获取ETF价格（使用股票接口）
        if etf_symbols:
            try:
                etf_prices = self.get_stock_realtime(etf_symbols, user_id)
                price_data.update(etf_prices)
            except Exception as e:
                errors.append(f"获取ETF价格失败: {str(e)}")

        # 更新持仓数据
        for position in positions:
            if position.symbol in price_data:
                data = price_data[position.symbol]

                # 获取新价格
                new_price = data.get('price') or data.get('nav') or data.get('dwjz')
                if new_price is None:
                    continue

                # 更新当前价格
                position.current_price = float(new_price)

                # 更新市值
                position.market_value = position.quantity * float(new_price)

                # 更新收益率
                if position.cost_price and float(position.cost_price) > 0:
                    position.profit_rate = (float(new_price) - float(position.cost_price)) / float(position.cost_price)

                updated += 1
                logger.info(f"更新 {position.symbol} ({position.name}): 价格={new_price}, 市值={position.market_value}, 收益率={position.profit_rate:.2%}")

        db.session.commit()

        # 获取近一周历史数据（用于收益曲线计算）
        history_updated = 0
        try:
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

            for position in positions:
                try:
                    if position.asset_type in ['stock', 'etf_index', 'etf_sector']:
                        df = self.get_stock_history(position.symbol, start_date, end_date, user_id)
                        if not df.empty:
                            history_updated += len(df)
                    elif position.asset_type == 'fund':
                        df = self.get_fund_nav_history(position.symbol, start_date, end_date, user_id)
                        if not df.empty:
                            history_updated += len(df)
                except Exception as e:
                    logger.warning(f"获取 {position.symbol} 近一周历史数据失败: {str(e)}")

        except Exception as e:
            logger.warning(f"获取近一周历史数据失败: {str(e)}")

        # 创建今日快照
        try:
            from .snapshot_service import SnapshotService
            snapshot_service = SnapshotService()

            # 获取用户的账户列表
            from ..models import Account
            accounts = Account.query.filter_by(user_id=user_id, is_active=True).all()

            for account in accounts:
                snapshot_service.create_daily_snapshot(account.id, user_id)

        except Exception as e:
            logger.warning(f"创建快照失败: {str(e)}")

        return {
            "success": True,
            "message": f"成功更新 {updated} 条持仓价格和市值，获取 {history_updated} 条历史数据",
            "updated": updated,
            "history_updated": history_updated,
            "total": len(positions),
            "stocks": len(stock_symbols),
            "funds": len(fund_codes),
            "etfs": len(etf_symbols),
            "errors": errors
        }

    def fetch_position_history(self, user_id: int, years: int = 5) -> Dict[str, Any]:
        """
        获取用户所有持仓的历史数据
        只获取数据库中缺失的日期数据，避免重复获取
        """
        from ..models import Position

        positions = Position.query.filter_by(user_id=user_id).all()

        if not positions:
            return {"success": True, "message": "无持仓数据", "data": {}}

        result = {
            'stocks': {},
            'funds': {}
        }

        total_fetched = 0

        for position in positions:
            symbol = position.symbol
            name = position.name

            try:
                if position.asset_type in ['stock', 'etf_index', 'etf_sector']:
                    df = self.get_stock_all_history(symbol, years, user_id)
                    if not df.empty:
                        # 统计新增的数据条数
                        result['stocks'][symbol] = {
                            'name': name,
                            'count': len(df)
                        }
                        total_fetched += len(df)

                elif position.asset_type == 'fund':
                    df = self.get_fund_all_nav_history(symbol, years, user_id)
                    if not df.empty:
                        result['funds'][symbol] = {
                            'name': name,
                            'count': len(df)
                        }
                        total_fetched += len(df)

            except Exception as e:
                logger.warning(f"获取 {symbol} 历史数据失败: {str(e)}")
                continue

        stock_count = len(result['stocks'])
        fund_count = len(result['funds'])

        return {
            "success": True,
            "message": f"成功获取 {stock_count} 只股票、{fund_count} 只基金的历史数据，共 {total_fetched} 条",
            "data": result,
            "years": years
        }

    # ============ 数据存储 ============

    def _save_price_history(self, user_id: int, symbol: str, df: pd.DataFrame, asset_type: str = 'stock'):
        """保存股票历史数据到数据库"""
        from ..models import PriceHistory
        from .. import db

        try:
            # 获取已存在的日期
            existing_dates = self._get_existing_dates(user_id, symbol)

            records = []
            for _, row in df.iterrows():
                trade_date = row['date']
                if isinstance(trade_date, str):
                    trade_date = datetime.strptime(trade_date, '%Y-%m-%d').date()

                # 跳过已存在的数据
                if trade_date in existing_dates:
                    continue

                record = PriceHistory(
                    user_id=user_id,
                    symbol=symbol,
                    asset_type=asset_type,
                    trade_date=trade_date,
                    open_price=float(row['open']) if pd.notna(row.get('open')) else None,
                    high_price=float(row['high']) if pd.notna(row.get('high')) else None,
                    low_price=float(row['low']) if pd.notna(row.get('low')) else None,
                    close_price=float(row['close']) if pd.notna(row.get('close')) else None,
                    volume=float(row['volume']) if pd.notna(row.get('volume')) else None,
                    turnover=float(row['turnover']) if pd.notna(row.get('turnover')) else None,
                    change_pct=float(row['change_pct']) if pd.notna(row.get('change_pct')) else None,
                    amplitude=float(row['amplitude']) if pd.notna(row.get('amplitude')) else None,
                    turnover_rate=float(row['turnover_rate']) if pd.notna(row.get('turnover_rate')) else None,
                    data_source=row.get('source', 'unknown')
                )
                records.append(record)

            if records:
                db.session.bulk_save_objects(records)
                db.session.commit()
                logger.info(f"保存 {symbol} 历史数据 {len(records)} 条（跳过已存在的 {len(df) - len(records)} 条）")

        except Exception as e:
            db.session.rollback()
            logger.error(f"保存历史数据失败: {str(e)}")

    def _save_fund_nav_history(self, user_id: int, symbol: str, df: pd.DataFrame):
        """保存基金净值历史到数据库"""
        from ..models import PriceHistory
        from .. import db

        try:
            existing_dates = self._get_existing_dates(user_id, symbol)

            records = []
            for _, row in df.iterrows():
                trade_date = row['date']
                if isinstance(trade_date, str):
                    trade_date = datetime.strptime(trade_date, '%Y-%m-%d').date()

                if trade_date in existing_dates:
                    continue

                record = PriceHistory(
                    user_id=user_id,
                    symbol=symbol,
                    asset_type='fund',
                    trade_date=trade_date,
                    close_price=float(row['nav']) if pd.notna(row.get('nav')) else None,
                    acc_nav=float(row['acc_nav']) if pd.notna(row.get('acc_nav')) else None,
                    change_pct=float(row['change_pct']) if pd.notna(row.get('change_pct')) else None,
                    data_source=row.get('source', 'eastmoney')
                )
                records.append(record)

            if records:
                db.session.bulk_save_objects(records)
                db.session.commit()
                logger.info(f"保存 {symbol} 基金净值历史 {len(records)} 条")

        except Exception as e:
            db.session.rollback()
            logger.error(f"保存基金净值历史失败: {str(e)}")

    def _price_history_to_df(self, records) -> pd.DataFrame:
        """将数据库记录转换为DataFrame"""
        data = []
        for r in records:
            record = {
                'date': r.trade_date.strftime('%Y-%m-%d') if r.trade_date else None,
                'volume': float(r.volume) if r.volume else None
            }
            # 对于基金，使用 nav 字段作为主要价格字段
            if r.asset_type == 'fund':
                if r.close_price:
                    record['nav'] = float(r.close_price)
                    record['close'] = float(r.close_price)  # 同时提供 close 以便回测使用
            else:
                # 股票数据
                record['open'] = float(r.open_price) if r.open_price else None
                record['high'] = float(r.high_price) if r.high_price else None
                record['low'] = float(r.low_price) if r.low_price else None
                record['close'] = float(r.close_price) if r.close_price else None

            if r.acc_nav:
                record['acc_nav'] = float(r.acc_nav)
            if r.change_pct:
                record['change_pct'] = float(r.change_pct)
            data.append(record)
        return pd.DataFrame(data)

    def _merge_db_and_new_data(self, user_id: int, symbol: str,
                               start_date: str, end_date: str,
                               new_df: pd.DataFrame) -> pd.DataFrame:
        """合并数据库数据和新获取的数据"""
        from ..models import PriceHistory
        from datetime import datetime

        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()

        records = PriceHistory.query.filter_by(
            user_id=user_id,
            symbol=symbol
        ).filter(
            PriceHistory.trade_date >= start_dt,
            PriceHistory.trade_date <= end_dt
        ).order_by(PriceHistory.trade_date).all()

        db_df = self._price_history_to_df(records)

        if new_df.empty:
            return db_df

        return pd.concat([db_df, new_df], ignore_index=True).sort_values('date')

    # ============ 数据源状态 ============

    def get_datasource_status(self, user_id: int = None) -> Dict[str, Any]:
        """获取数据源状态"""
        stock_config = self.get_user_stock_datasource_config(user_id) if user_id else {}
        fund_config = self.get_user_fund_datasource_config(user_id) if user_id else {}

        return {
            'stock': {
                'current': stock_config.get('type', 'default'),
                'sources': {
                    'default': {
                        'name': 'AKShare + BaoStock',
                        'description': '免费数据源，自动降级',
                        'status': 'available'
                    },
                    'tushare': {
                        'name': 'Tushare Pro',
                        'description': '需要配置Token',
                        'status': 'configured' if stock_config.get('tushare_token') else 'not_configured'
                    }
                }
            },
            'fund': {
                'current': fund_config.get('type', 'default'),
                'sources': {
                    'default': {
                        'name': 'AKShare + 天天基金',
                        'description': '免费数据源，自动降级',
                        'status': 'available'
                    },
                    'akshare': {
                        'name': 'AKShare',
                        'description': '优先使用AKShare',
                        'status': 'available'
                    },
                    'eastmoney': {
                        'name': '天天基金',
                        'description': '优先使用天天基金',
                        'status': 'available'
                    },
                    'tushare': {
                        'name': 'Tushare Pro',
                        'description': '需要配置Token',
                        'status': 'configured' if fund_config.get('tushare_token') else 'not_configured'
                    }
                }
            }
        }


# 全局实例
market_data_service = MarketDataService()


def get_market_data_service() -> MarketDataService:
    """获取市场数据服务实例"""
    return market_data_service