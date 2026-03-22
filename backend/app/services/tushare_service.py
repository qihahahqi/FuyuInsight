#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare金融数据服务
提供股票、基金、指数等金融数据获取功能
"""

import tushare as ts
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import os


class TushareService:
    """Tushare数据服务"""

    def __init__(self, token: str = "", base_url: str = "https://api.tushare.pro"):
        """
        初始化Tushare服务

        Args:
            token: Tushare API Token
            base_url: API基础URL
        """
        self.token = token
        self.base_url = base_url
        self._pro = None

    @property
    def pro(self):
        """获取Tushare Pro API实例"""
        if self._pro is None and self.token:
            self._pro = ts.pro_api(self.token)
        return self._pro

    def set_token(self, token: str):
        """设置Token"""
        self.token = token
        self._pro = None  # 重置实例

    def test_connection(self) -> Dict[str, Any]:
        """
        测试API连接

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self.token:
            return {"success": False, "message": "Token未配置"}

        try:
            # 尝试获取交易日期，测试连接
            df = self.pro.trade_cal(exchange='SSE', start_date='20240101', end_date='20240110')
            if df is not None and len(df) > 0:
                return {"success": True, "message": "连接成功"}
            return {"success": False, "message": "API返回数据为空"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {str(e)}"}

    def get_stock_daily(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取股票日线数据

        Args:
            ts_code: 股票代码，如 '601168.SH'
            start_date: 开始日期，格式 '20230101'
            end_date: 结束日期，格式 '20240101'

        Returns:
            DataFrame: 包含open, high, low, close, volume等列
        """
        if not self.pro:
            raise ValueError("Tushare未初始化，请先配置Token")

        try:
            df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

            if df is None or len(df) == 0:
                return pd.DataFrame()

            # 按日期升序排列
            df = df.sort_values('trade_date')
            df = df.reset_index(drop=True)

            # 重命名列以匹配系统格式
            df = df.rename(columns={
                'trade_date': 'date',
                'vol': 'volume',
                'amount': 'turnover'
            })

            return df[['date', 'open', 'high', 'low', 'close', 'volume', 'turnover']]

        except Exception as e:
            raise Exception(f"获取股票日线数据失败: {str(e)}")

    def get_stock_basic(self, ts_code: str) -> Dict[str, Any]:
        """
        获取股票基本信息

        Args:
            ts_code: 股票代码

        Returns:
            dict: 股票基本信息
        """
        if not self.pro:
            raise ValueError("Tushare未初始化")

        try:
            df = self.pro.stock_basic(ts_code=ts_code, fields='ts_code,symbol,name,area,industry,list_date')

            if df is None or len(df) == 0:
                return {}

            row = df.iloc[0]
            return {
                'ts_code': row['ts_code'],
                'symbol': row['symbol'],
                'name': row['name'],
                'area': row['area'],
                'industry': row['industry'],
                'list_date': row['list_date']
            }
        except Exception as e:
            raise Exception(f"获取股票基本信息失败: {str(e)}")

    def get_stock_daily_basic(self, ts_code: str, trade_date: str = None) -> Dict[str, Any]:
        """
        获取股票每日基本面指标

        Args:
            ts_code: 股票代码
            trade_date: 交易日期，默认最新

        Returns:
            dict: PE、PB、换手率等指标
        """
        if not self.pro:
            raise ValueError("Tushare未初始化")

        try:
            if trade_date is None:
                # 获取最新交易日
                cal_df = self.pro.trade_cal(exchange='SSE', is_open='1')
                trade_date = cal_df['cal_date'].max()

            df = self.pro.daily_basic(ts_code=ts_code, trade_date=trade_date,
                                      fields='ts_code,trade_date,close,pe,pe_ttm,pb,ps,dv_ratio,turnover_rate,turnover_rate_f,volume_ratio,total_mv,circ_mv')

            if df is None or len(df) == 0:
                return {}

            row = df.iloc[0]
            return {
                'ts_code': row['ts_code'],
                'trade_date': row['trade_date'],
                'close': float(row['close']) if pd.notna(row['close']) else None,
                'pe': float(row['pe']) if pd.notna(row['pe']) else None,
                'pe_ttm': float(row['pe_ttm']) if pd.notna(row['pe_ttm']) else None,
                'pb': float(row['pb']) if pd.notna(row['pb']) else None,
                'ps': float(row['ps']) if pd.notna(row['ps']) else None,
                'dv_ratio': float(row['dv_ratio']) if pd.notna(row['dv_ratio']) else None,  # 股息率
                'turnover_rate': float(row['turnover_rate']) if pd.notna(row['turnover_rate']) else None,
                'turnover_rate_f': float(row['turnover_rate_f']) if pd.notna(row['turnover_rate_f']) else None,  # 换手率（自由流通股）
                'volume_ratio': float(row['volume_ratio']) if pd.notna(row['volume_ratio']) else None,
                'total_mv': float(row['total_mv']) if pd.notna(row['total_mv']) else None,  # 总市值（亿）
                'circ_mv': float(row['circ_mv']) if pd.notna(row['circ_mv']) else None   # 流通市值（亿）
            }
        except Exception as e:
            raise Exception(f"获取股票每日基本面失败: {str(e)}")

    def get_stock_finance_indicator(self, ts_code: str, period: str = None) -> Dict[str, Any]:
        """
        获取股票财务指标

        Args:
            ts_code: 股票代码
            period: 报告期，如 '20231231'，默认最新

        Returns:
            dict: 财务指标数据
        """
        if not self.pro:
            raise ValueError("Tushare未初始化")

        try:
            df = self.pro.fina_indicator(ts_code=ts_code, period=period,
                                         fields='ts_code,ann_date,roe,roe_dt,roa,netprofit_margin,grossprofit_margin,current_ratio,quick_ratio,assets_turn,debt_to_assets')

            if df is None or len(df) == 0:
                return {}

            row = df.iloc[0]
            return {
                'ts_code': row['ts_code'],
                'ann_date': row['ann_date'],
                'roe': float(row['roe']) if pd.notna(row['roe']) else None,
                'roe_dt': float(row['roe_dt']) if pd.notna(row['roe_dt']) else None,  # ROE(摊薄)
                'roa': float(row['roa']) if pd.notna(row['roa']) else None,
                'netprofit_margin': float(row['netprofit_margin']) if pd.notna(row['netprofit_margin']) else None,  # 销售净利率
                'grossprofit_margin': float(row['grossprofit_margin']) if pd.notna(row['grossprofit_margin']) else None,  # 销售毛利率
                'current_ratio': float(row['current_ratio']) if pd.notna(row['current_ratio']) else None,
                'quick_ratio': float(row['quick_ratio']) if pd.notna(row['quick_ratio']) else None,
                'assets_turn': float(row['assets_turn']) if pd.notna(row['assets_turn']) else None,  # 资产周转率
                'debt_to_assets': float(row['debt_to_assets']) if pd.notna(row['debt_to_assets']) else None  # 资产负债率
            }
        except Exception as e:
            raise Exception(f"获取财务指标失败: {str(e)}")

    def get_index_daily(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取指数日线数据

        Args:
            ts_code: 指数代码，如 '000300.SH' (沪深300)
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame: 指数日线数据
        """
        if not self.pro:
            raise ValueError("Tushare未初始化")

        try:
            df = self.pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

            if df is None or len(df) == 0:
                return pd.DataFrame()

            df = df.sort_values('trade_date')
            df = df.reset_index(drop=True)

            df = df.rename(columns={
                'trade_date': 'date',
                'vol': 'volume',
                'amount': 'turnover'
            })

            return df[['date', 'open', 'high', 'low', 'close', 'volume', 'turnover']]
        except Exception as e:
            raise Exception(f"获取指数数据失败: {str(e)}")

    def get_index_basic(self, ts_code: str = None) -> List[Dict[str, Any]]:
        """
        获取指数基本信息

        Args:
            ts_code: 指数代码，为空则获取所有指数

        Returns:
            list: 指数列表
        """
        if not self.pro:
            raise ValueError("Tushare未初始化")

        try:
            if ts_code:
                df = self.pro.index_basic(ts_code=ts_code)
            else:
                df = self.pro.index_basic(market='SSE')  # 上交所
                df2 = self.pro.index_basic(market='SZSE')  # 深交所
                df = pd.concat([df, df2])

            if df is None or len(df) == 0:
                return []

            return df.to_dict('records')
        except Exception as e:
            raise Exception(f"获取指数信息失败: {str(e)}")

    def get_moneyflow(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取个股资金流向

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame: 资金流向数据
        """
        if not self.pro:
            raise ValueError("Tushare未初始化")

        try:
            df = self.pro.moneyflow(ts_code=ts_code, start_date=start_date, end_date=end_date)

            if df is None or len(df) == 0:
                return pd.DataFrame()

            df = df.sort_values('trade_date')
            return df
        except Exception as e:
            raise Exception(f"获取资金流向失败: {str(e)}")

    def convert_symbol_to_ts_code(self, symbol: str) -> str:
        """
        将股票代码转换为Tushare格式

        Args:
            symbol: 股票代码，如 '601168' 或 '000001'

        Returns:
            str: Tushare格式代码，如 '601168.SH'
        """
        if '.' in symbol:
            return symbol

        # 判断市场
        if symbol.startswith('6'):
            return f"{symbol}.SH"
        elif symbol.startswith(('0', '3')):
            return f"{symbol}.SZ"
        elif symbol.startswith(('4', '8')):
            return f"{symbol}.BJ"
        else:
            return f"{symbol}.SH"  # 默认上交所


# 全局实例
tushare_service = TushareService()


def init_tushare_service(token: str, base_url: str = "https://api.tushare.pro"):
    """初始化Tushare服务"""
    global tushare_service
    tushare_service = TushareService(token, base_url)
    return tushare_service


def get_tushare_service() -> TushareService:
    """获取Tushare服务实例"""
    return tushare_service