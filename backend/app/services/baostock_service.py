#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BaoStock金融数据服务
免费、开源的证券数据平台，作为系统默认数据源
"""

import baostock as bs
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class BaoStockService:
    """BaoStock数据服务 - 免费数据源"""

    # BaoStock 市场代码映射
    MARKET_MAP = {
        'SH': 'sh',  # 上交所
        'SZ': 'sz',  # 深交所
        'BJ': 'bj'   # 北交所
    }

    def __init__(self):
        """初始化BaoStock服务"""
        self._logged_in = False
        self._login_result = None

    def _ensure_login(self) -> bool:
        """确保已登录BaoStock"""
        if self._logged_in:
            return True

        try:
            self._login_result = bs.login()
            if self._login_result.error_code == '0':
                self._logged_in = True
                logger.info("BaoStock登录成功")
                return True
            else:
                logger.error(f"BaoStock登录失败: {self._login_result.error_msg}")
                return False
        except Exception as e:
            logger.error(f"BaoStock登录异常: {str(e)}")
            return False

    def _logout(self):
        """登出BaoStock"""
        if self._logged_in:
            try:
                bs.logout()
                self._logged_in = False
                logger.info("BaoStock已登出")
            except Exception as e:
                logger.error(f"BaoStock登出异常: {str(e)}")

    def test_connection(self) -> Dict[str, Any]:
        """
        测试连接

        Returns:
            dict: {"success": bool, "message": str}
        """
        try:
            if self._ensure_login():
                return {"success": True, "message": "BaoStock连接成功（免费数据源）"}
            return {"success": False, "message": "BaoStock连接失败"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {str(e)}"}

    def convert_symbol_to_bs_code(self, symbol: str) -> tuple:
        """
        将股票代码转换为BaoStock格式

        Args:
            symbol: 股票代码，如 '601168' 或 '601168.SH'（用户一般只填数字）

        Returns:
            tuple: (市场代码, 股票代码) 如 ('sh', '601168')

        代码规则:
            - 60xxxx, 68xxxx: 上交所（主板、科创板）
            - 00xxxx, 30xxxx: 深交所（主板、创业板）
            - 4xxxxx, 8xxxxx: 北交所
            - 51xxxx, 58xxxx, 56xxxx: 上交所ETF
            - 15xxxx, 16xxxx: 深交所ETF
        """
        if '.' in symbol:
            # 已经是带市场的格式，如 '601168.SH'
            code, market = symbol.split('.')
            market = market.upper()
        else:
            code = symbol.upper()
            # 根据代码规则判断市场
            if code.startswith('60') or code.startswith('68'):
                # 沪A主板(60)或科创板(68)
                market = 'SH'
            elif code.startswith('00') or code.startswith('30'):
                # 深A主板(00)或创业板(30)
                market = 'SZ'
            elif code.startswith('4') or code.startswith('8'):
                # 北交所(4开头或8开头)
                market = 'BJ'
            elif code.startswith('51') or code.startswith('58') or code.startswith('56'):
                # 上交所ETF
                market = 'SH'
            elif code.startswith('15') or code.startswith('16'):
                # 深交所ETF
                market = 'SZ'
            else:
                # 默认上交所
                market = 'SH'

        bs_market = self.MARKET_MAP.get(market.upper(), 'sh')
        return bs_market, code.lower()

    def get_stock_daily(self, symbol: str, start_date: str, end_date: str,
                        adjust: str = "2") -> pd.DataFrame:
        """
        获取股票日线数据

        Args:
            symbol: 股票代码，如 '601168' 或 '601168.SH'
            start_date: 开始日期，格式 '2023-01-01'
            end_date: 结束日期，格式 '2024-01-01'
            adjust: 复权类型，"1"-后复权，"2"-前复权，"3"-不复权

        Returns:
            DataFrame: 包含date, open, high, low, close, volume, turnover等列
        """
        if not self._ensure_login():
            raise ValueError("BaoStock连接失败")

        try:
            market, code = self.convert_symbol_to_bs_code(symbol)

            # BaoStock日期格式: yyyy-MM-dd
            # BaoStock需要完整代码格式: sh.600000
            full_code = f"{market}.{code}"
            # BaoStock支持的指标字段: pbMRQ(市净率), peTTM(市盈率TTM)
            rs = bs.query_history_k_data_plus(
                full_code,
                "date,code,open,high,low,close,volume,amount,turn,pbMRQ,peTTM",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag=adjust
            )

            if rs.error_code != '0':
                logger.error(f"BaoStock查询失败: {rs.error_msg}")
                return pd.DataFrame()

            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                return pd.DataFrame()

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 转换数据类型
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount', 'turn', 'pbMRQ', 'peTTM']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # 重命名列以匹配系统格式
            df = df.rename(columns={
                'amount': 'turnover',
                'turn': 'turnover_rate',
                'peTTM': 'pe_ttm',
                'pbMRQ': 'pb'
            })

            return df[['date', 'open', 'high', 'low', 'close', 'volume', 'turnover']]

        except Exception as e:
            logger.error(f"获取股票日线数据失败: {str(e)}")
            raise Exception(f"获取股票日线数据失败: {str(e)}")

    def get_stock_all_data(self, symbol: str, years: int = 5) -> pd.DataFrame:
        """
        获取股票全量历史数据

        Args:
            symbol: 股票代码
            years: 获取最近N年的数据，默认5年

        Returns:
            DataFrame: 日线数据
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=years*365)).strftime('%Y-%m-%d')

        return self.get_stock_daily(symbol, start_date, end_date)

    def get_stock_basic(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票基本信息

        Args:
            symbol: 股票代码

        Returns:
            dict: 股票基本信息
        """
        if not self._ensure_login():
            raise ValueError("BaoStock连接失败")

        try:
            market, code = self.convert_symbol_to_bs_code(symbol)

            # 获取股票基本信息
            rs = bs.query_stock_basic_by_code(code)

            if rs.error_code != '0' or not rs.next():
                return {}

            row = rs.get_row_data()
            fields = rs.fields

            result = dict(zip(fields, row))
            result['market'] = market.upper()

            return result

        except Exception as e:
            logger.error(f"获取股票基本信息失败: {str(e)}")
            return {}

    def get_index_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取指数日线数据

        Args:
            symbol: 指数代码，如 'sh.000300' (沪深300)
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame: 指数日线数据
        """
        if not self._ensure_login():
            raise ValueError("BaoStock连接失败")

        try:
            # BaoStock指数代码格式: sh.000300, sz.399001
            if '.' not in symbol:
                # 默认处理
                if symbol.startswith('0'):
                    symbol = f"sh.{symbol}"
                elif symbol.startswith('399'):
                    symbol = f"sz.{symbol}"
                else:
                    symbol = f"sh.{symbol}"

            rs = bs.query_history_k_data_plus(
                symbol,
                "date,code,open,high,low,close,volume,amount",
                start_date=start_date,
                end_date=end_date,
                frequency="d"
            )

            if rs.error_code != '0':
                return pd.DataFrame()

            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                return pd.DataFrame()

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 转换数据类型
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            df = df.rename(columns={'amount': 'turnover'})

            return df[['date', 'open', 'high', 'low', 'close', 'volume', 'turnover']]

        except Exception as e:
            logger.error(f"获取指数数据失败: {str(e)}")
            return pd.DataFrame()

    def get_all_stocks(self) -> List[Dict[str, Any]]:
        """
        获取全部股票列表

        Returns:
            list: 股票列表
        """
        if not self._ensure_login():
            return []

        try:
            rs = bs.query_all_stock()

            if rs.error_code != '0':
                return []

            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 过滤掉非A股
            df = df[df['code'].str.match(r'^(sh|sz)\d{6}$')]

            return df.to_dict('records')

        except Exception as e:
            logger.error(f"获取股票列表失败: {str(e)}")
            return []

    def get_trade_dates(self, start_date: str, end_date: str) -> List[str]:
        """
        获取交易日历

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            list: 交易日列表
        """
        if not self._ensure_login():
            return []

        try:
            rs = bs.query_trade_dates(start_date=start_date, end_date=end_date)

            if rs.error_code != '0':
                return []

            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 只返回交易日
            df = df[df['is_trading_day'] == '1']

            return df['calendar_date'].tolist()

        except Exception as e:
            logger.error(f"获取交易日历失败: {str(e)}")
            return []

    def get_stock_latest_price(self, symbol: str) -> Optional[float]:
        """
        获取股票最新价格

        Args:
            symbol: 股票代码

        Returns:
            float: 最新价格
        """
        try:
            # 获取最近3天的数据，确保能获取到最新
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

            df = self.get_stock_daily(symbol, start_date, end_date)

            if df.empty:
                return None

            return float(df.iloc[-1]['close'])

        except Exception as e:
            logger.error(f"获取最新价格失败: {str(e)}")
            return None

    def get_multiple_stocks_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        批量获取多只股票的最新价格

        Args:
            symbols: 股票代码列表

        Returns:
            dict: {symbol: price}
        """
        result = {}

        for symbol in symbols:
            try:
                price = self.get_stock_latest_price(symbol)
                if price:
                    result[symbol] = price
            except Exception as e:
                logger.warning(f"获取{symbol}价格失败: {str(e)}")
                continue

        return result

    def __del__(self):
        """析构时登出"""
        self._logout()


# 全局实例
baostock_service = BaoStockService()


def get_baostock_service() -> BaoStockService:
    """获取BaoStock服务实例"""
    return baostock_service