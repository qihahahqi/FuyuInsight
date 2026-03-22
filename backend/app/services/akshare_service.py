#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AKShare 股票数据服务
免费、开源的金融数据接口，数据丰富
"""

import akshare as ak
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import time
import threading

logger = logging.getLogger(__name__)


class AKShareService:
    """AKShare数据服务 - 股票数据"""

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

    def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        try:
            # 尝试获取股票列表测试连接
            df = ak.stock_zh_a_spot_em()
            if df is not None and len(df) > 0:
                return {"success": True, "message": "AKShare连接成功（免费数据源）"}
            return {"success": False, "message": "数据返回为空"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {str(e)}"}

    def get_stock_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取股票日线数据

        Args:
            symbol: 股票代码，如 '601168'
            start_date: 开始日期，格式 '20230101'
            end_date: 结束日期，格式 '20240101'

        Returns:
            DataFrame: 日线数据
        """
        self._rate_limit()

        try:
            # 使用东方财富数据源
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                adjust="qfq"  # 前复权
            )

            if df is None or len(df) == 0:
                return pd.DataFrame()

            # 重命名列
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume',
                '成交额': 'turnover',
                '振幅': 'amplitude',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change_amount',
                '换手率': 'turnover_rate'
            })

            # 确保日期格式
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

            # 选择需要的列
            columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'turnover']
            extra_cols = ['amplitude', 'change_pct', 'turnover_rate']
            for col in extra_cols:
                if col in df.columns:
                    columns.append(col)

            return df[columns]

        except Exception as e:
            logger.error(f"AKShare获取股票日线失败: {str(e)}")
            return pd.DataFrame()

    def get_stock_realtime(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        获取股票实时行情

        Args:
            symbols: 股票代码列表

        Returns:
            dict: {symbol: {price, change_pct, volume, ...}}
        """
        self._rate_limit()

        try:
            # 获取全市场实时行情
            df = ak.stock_zh_a_spot_em()

            if df is None or len(df) == 0:
                return {}

            result = {}
            for symbol in symbols:
                match = df[df['代码'] == symbol]
                if len(match) > 0:
                    row = match.iloc[0]
                    result[symbol] = {
                        'name': row.get('名称', ''),
                        'price': float(row.get('最新价', 0)),
                        'change_pct': float(row.get('涨跌幅', 0)),
                        'change_amount': float(row.get('涨跌额', 0)),
                        'volume': float(row.get('成交量', 0)),
                        'turnover': float(row.get('成交额', 0)),
                        'amplitude': float(row.get('振幅', 0)),
                        'high': float(row.get('最高', 0)),
                        'low': float(row.get('最低', 0)),
                        'open': float(row.get('今开', 0)),
                        'prev_close': float(row.get('昨收', 0))
                    }

            return result

        except Exception as e:
            logger.error(f"AKShare获取实时行情失败: {str(e)}")
            return {}

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票基本信息

        Args:
            symbol: 股票代码

        Returns:
            dict: 股票信息
        """
        self._rate_limit()

        try:
            df = ak.stock_individual_info_em(symbol=symbol)

            if df is None or len(df) == 0:
                return {}

            result = {}
            for _, row in df.iterrows():
                result[row['item']] = row['value']

            return {
                'symbol': symbol,
                'name': result.get('股票简称', ''),
                'industry': result.get('行业', ''),
                'list_date': result.get('上市时间', ''),
                'total_share': result.get('总市值', ''),
                'circ_share': result.get('流通市值', '')
            }

        except Exception as e:
            logger.error(f"AKShare获取股票信息失败: {str(e)}")
            return {}

    def get_index_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取指数日线数据

        Args:
            symbol: 指数代码，如 '000300' (沪深300)
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame: 指数数据
        """
        self._rate_limit()

        try:
            df = ak.index_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', '')
            )

            if df is None or len(df) == 0:
                return pd.DataFrame()

            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume',
                '成交额': 'turnover'
            })

            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

            return df[['date', 'open', 'high', 'low', 'close', 'volume', 'turnover']]

        except Exception as e:
            logger.error(f"AKShare获取指数数据失败: {str(e)}")
            return pd.DataFrame()

    def get_index_realtime(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        获取指数实时行情

        Args:
            symbols: 指数代码列表

        Returns:
            dict: {symbol: {price, change_pct, ...}}
        """
        self._rate_limit()

        try:
            df = ak.index_zh_a_spot_em()

            if df is None or len(df) == 0:
                return {}

            result = {}
            for symbol in symbols:
                match = df[df['代码'] == symbol]
                if len(match) > 0:
                    row = match.iloc[0]
                    result[symbol] = {
                        'name': row.get('名称', ''),
                        'price': float(row.get('最新价', 0)),
                        'change_pct': float(row.get('涨跌幅', 0)),
                        'change_amount': float(row.get('涨跌额', 0)),
                        'volume': float(row.get('成交量', 0)),
                        'turnover': float(row.get('成交额', 0))
                    }

            return result

        except Exception as e:
            logger.error(f"AKShare获取指数实时行情失败: {str(e)}")
            return {}

    def get_trade_dates(self, start_date: str, end_date: str) -> List[str]:
        """
        获取交易日历

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            list: 交易日列表
        """
        self._rate_limit()

        try:
            df = ak.tool_trade_date_hist_sina()

            if df is None or len(df) == 0:
                return []

            # 转换日期格式
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')

            # 过滤日期范围
            start = start_date.replace('-', '') if '-' in start_date else start_date
            end = end_date.replace('-', '') if '-' in end_date else end_date

            mask = (df['trade_date'] >= start) & (df['trade_date'] <= end)
            return df.loc[mask, 'trade_date'].tolist()

        except Exception as e:
            logger.error(f"AKShare获取交易日历失败: {str(e)}")
            return []


# 全局实例
akshare_service = AKShareService()


def get_akshare_service() -> AKShareService:
    """获取AKShare服务实例"""
    return akshare_service