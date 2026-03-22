#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一金融数据源服务
自动选择数据源：用户配置的API > BaoStock（默认免费）
"""

import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import time
import threading

logger = logging.getLogger(__name__)


class DataSourceService:
    """
    统一金融数据源服务

    优先级：
    1. 用户配置的 Tushare API
    2. BaoStock（免费，无需配置）
    """

    # 数据源类型
    SOURCE_BAOSTOCK = 'baostock'
    SOURCE_TUSHARE = 'tushare'

    # API 请求限制配置
    TUSHARE_RATE_LIMIT = 0.3  # Tushare 每次请求间隔（秒）
    BAOSTOCK_RATE_LIMIT = 0.1  # BaoStock 每次请求间隔

    def __init__(self):
        self._lock = threading.Lock()
        self._last_request_time = 0

    def _rate_limit(self, source: str = 'baostock'):
        """API 请求频率限制"""
        interval = self.TUSHARE_RATE_LIMIT if source == 'tushare' else self.BAOSTOCK_RATE_LIMIT

        with self._lock:
            elapsed = time.time() - self._last_request_time
            if elapsed < interval:
                time.sleep(interval - elapsed)
            self._last_request_time = time.time()

    def get_user_datasource_config(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户的数据源配置

        Args:
            user_id: 用户ID

        Returns:
            dict: 数据源配置
        """
        from ..models import Config
        from .. import db

        config = {}

        # 获取用户配置的数据源类型
        ds_type = Config.query.filter_by(key='data_source.type', user_id=user_id).first()
        config['type'] = ds_type.value if ds_type else 'baostock'

        # 获取 Tushare Token
        token = Config.query.filter_by(key='tushare.token', user_id=user_id).first()
        config['tushare_token'] = token.value if token else None

        # 获取 Tushare Base URL
        base_url = Config.query.filter_by(key='tushare.base_url', user_id=user_id).first()
        config['tushare_base_url'] = base_url.value if base_url else 'https://api.tushare.pro'

        return config

    def get_datasource(self, user_id: int = None):
        """
        获取数据源实例

        Args:
            user_id: 用户ID，如果提供则优先使用用户配置

        Returns:
            tuple: (数据源实例, 数据源类型)
        """
        # 检查用户配置
        if user_id:
            config = self.get_user_datasource_config(user_id)

            # 如果用户配置了 Tushare Token，使用 Tushare
            if config.get('tushare_token'):
                from .tushare_service import TushareService
                service = TushareService(
                    token=config['tushare_token'],
                    base_url=config.get('tushare_base_url', 'https://api.tushare.pro')
                )
                return service, self.SOURCE_TUSHARE

        # 默认使用 BaoStock
        from .baostock_service import get_baostock_service
        return get_baostock_service(), self.SOURCE_BAOSTOCK

    def get_stock_daily(self, symbol: str, start_date: str, end_date: str,
                        user_id: int = None) -> pd.DataFrame:
        """
        获取股票日线数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户ID

        Returns:
            DataFrame: 日线数据
        """
        service, source = self.get_datasource(user_id)
        self._rate_limit(source)

        try:
            if source == 'tushare':
                # Tushare 日期格式: 20230101
                start = start_date.replace('-', '')
                end = end_date.replace('-', '')
                ts_code = service.convert_symbol_to_ts_code(symbol)
                return service.get_stock_daily(ts_code, start, end)
            else:
                # BaoStock 日期格式: 2023-01-01
                return service.get_stock_daily(symbol, start_date, end_date)
        except Exception as e:
            logger.error(f"获取股票日线数据失败 [{source}]: {str(e)}")
            # 如果 Tushare 失败，尝试 BaoStock
            if source == 'tushare':
                logger.info("尝试使用 BaoStock 获取数据...")
                from .baostock_service import get_baostock_service
                self._rate_limit('baostock')
                return get_baostock_service().get_stock_daily(symbol, start_date, end_date)
            raise

    def get_stock_all_data(self, symbol: str, years: int = 5,
                           user_id: int = None) -> pd.DataFrame:
        """
        获取股票全量历史数据

        Args:
            symbol: 股票代码
            years: 年数
            user_id: 用户ID

        Returns:
            DataFrame: 日线数据
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=years*365)).strftime('%Y-%m-%d')

        return self.get_stock_daily(symbol, start_date, end_date, user_id)

    def get_stock_latest_price(self, symbol: str, user_id: int = None) -> Optional[float]:
        """
        获取股票最新价格

        Args:
            symbol: 股票代码
            user_id: 用户ID

        Returns:
            float: 最新价格
        """
        service, source = self.get_datasource(user_id)
        self._rate_limit(source)

        try:
            if source == 'tushare':
                # 获取最近几天的数据
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
                ts_code = service.convert_symbol_to_ts_code(symbol)
                df = service.get_stock_daily(ts_code, start_date, end_date)

                if df.empty:
                    return None

                return float(df.iloc[-1]['close'])
            else:
                return service.get_stock_latest_price(symbol)
        except Exception as e:
            logger.error(f"获取最新价格失败: {str(e)}")
            return None

    def get_multiple_stocks_prices(self, symbols: List[str],
                                   user_id: int = None) -> Dict[str, float]:
        """
        批量获取多只股票的最新价格

        Args:
            symbols: 股票代码列表
            user_id: 用户ID

        Returns:
            dict: {symbol: price}
        """
        result = {}

        for symbol in symbols:
            try:
                price = self.get_stock_latest_price(symbol, user_id)
                if price:
                    result[symbol] = price
            except Exception as e:
                logger.warning(f"获取{symbol}价格失败: {str(e)}")
                continue

        return result

    def get_index_daily(self, symbol: str, start_date: str, end_date: str,
                        user_id: int = None) -> pd.DataFrame:
        """
        获取指数日线数据

        Args:
            symbol: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户ID

        Returns:
            DataFrame: 指数日线数据
        """
        service, source = self.get_datasource(user_id)
        self._rate_limit(source)

        try:
            if source == 'tushare':
                start = start_date.replace('-', '')
                end = end_date.replace('-', '')
                return service.get_index_daily(symbol, start, end)
            else:
                return service.get_index_daily(symbol, start_date, end_date)
        except Exception as e:
            logger.error(f"获取指数数据失败: {str(e)}")
            raise

    def sync_position_prices(self, user_id: int) -> Dict[str, Any]:
        """
        同步用户持仓股票的最新价格

        Args:
            user_id: 用户ID

        Returns:
            dict: 同步结果
        """
        from ..models import Position
        from .. import db

        # 获取用户所有持仓
        positions = Position.query.filter_by(user_id=user_id).all()

        if not positions:
            return {"success": True, "message": "无持仓数据", "updated": 0}

        # 提取股票代码
        symbols = [p.symbol for p in positions if p.asset_type in ['stock', 'etf_index', 'etf_sector']]

        if not symbols:
            return {"success": True, "message": "无股票类持仓", "updated": 0}

        # 批量获取价格
        prices = self.get_multiple_stocks_prices(symbols, user_id)

        # 更新持仓价格
        updated = 0
        for position in positions:
            if position.symbol in prices:
                position.current_price = prices[position.symbol]
                updated += 1

        db.session.commit()

        return {
            "success": True,
            "message": f"成功更新 {updated} 条持仓价格",
            "updated": updated,
            "total": len(positions)
        }

    def fetch_position_history_data(self, user_id: int, years: int = 5) -> Dict[str, Any]:
        """
        获取用户所有持仓股票的历史数据

        Args:
            user_id: 用户ID
            years: 获取最近N年数据

        Returns:
            dict: 各股票的历史数据
        """
        from ..models import Position, PriceHistory
        from .. import db

        # 获取用户所有持仓
        positions = Position.query.filter_by(user_id=user_id).all()

        if not positions:
            return {"success": True, "message": "无持仓数据", "data": {}}

        result = {}
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=years*365)).strftime('%Y-%m-%d')

        for position in positions:
            if position.asset_type not in ['stock', 'etf_index', 'etf_sector']:
                continue

            try:
                df = self.get_stock_daily(position.symbol, start_date, end_date, user_id)

                if df.empty:
                    continue

                result[position.symbol] = {
                    "name": position.name,
                    "data": df.to_dict('records')
                }

                # 保存到数据库（可选）
                self._save_history_to_db(user_id, position.symbol, df)

            except Exception as e:
                logger.warning(f"获取{position.symbol}历史数据失败: {str(e)}")
                continue

        return {
            "success": True,
            "message": f"成功获取 {len(result)} 只股票的历史数据",
            "data": result,
            "period": {
                "start": start_date,
                "end": end_date,
                "years": years
            }
        }

    def _save_history_to_db(self, user_id: int, symbol: str, df: pd.DataFrame):
        """
        保存历史数据到数据库

        Args:
            user_id: 用户ID
            symbol: 股票代码
            df: 数据DataFrame
        """
        from ..models import Position, PriceHistory
        from .. import db

        try:
            # 删除旧数据
            PriceHistory.query.filter_by(user_id=user_id, symbol=symbol).delete()

            # 批量插入新数据
            records = []
            for _, row in df.iterrows():
                record = PriceHistory(
                    user_id=user_id,
                    symbol=symbol,
                    trade_date=row['date'],
                    open_price=float(row['open']) if pd.notna(row['open']) else None,
                    high_price=float(row['high']) if pd.notna(row['high']) else None,
                    low_price=float(row['low']) if pd.notna(row['low']) else None,
                    close_price=float(row['close']) if pd.notna(row['close']) else None,
                    volume=float(row['volume']) if pd.notna(row['volume']) else None
                )
                records.append(record)

            if records:
                db.session.bulk_save_objects(records)
                db.session.commit()
                logger.info(f"保存 {symbol} 历史数据 {len(records)} 条")

        except Exception as e:
            db.session.rollback()
            logger.error(f"保存历史数据失败: {str(e)}")


# 全局实例
datasource_service = DataSourceService()


def get_datasource_service() -> DataSourceService:
    """获取数据源服务实例"""
    return datasource_service