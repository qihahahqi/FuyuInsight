#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天天基金数据服务
免费基金数据接口
"""

import requests
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import time
import threading
import json
import re

logger = logging.getLogger(__name__)


class EastMoneyFundService:
    """天天基金数据服务 - 基金数据"""

    # API 地址
    FUND_INFO_URL = "http://fundgz.eastmoney.com/zljs/html/{fund_code}.html"
    FUND_DETAIL_URL = "http://fund.eastmoney.com/{fund_code}.html"
    FUND_HISTORY_URL = "http://api.fund.eastmoney.com/f10/lsjz"
    FUND_REALTIME_URL = "http://fundgz.eastmoney.com/js/{fund_code}.js"

    # 请求限流配置
    REQUEST_INTERVAL = 0.3
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'http://fund.eastmoney.com/'
    }

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

    def _make_request(self, url: str, params: dict = None) -> Optional[requests.Response]:
        """发送请求"""
        self._rate_limit()

        try:
            response = requests.get(url, params=params, headers=self.HEADERS, timeout=10)
            response.encoding = 'utf-8'
            return response
        except Exception as e:
            logger.error(f"请求失败: {url}, {str(e)}")
            return None

    def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        try:
            # 测试获取一只常见基金的实时数据
            result = self.get_fund_realtime(['000001'])
            if result:
                return {"success": True, "message": "天天基金连接成功（免费数据源）"}
            return {"success": False, "message": "数据返回为空"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {str(e)}"}

    def get_fund_info(self, fund_code: str) -> Dict[str, Any]:
        """
        获取基金基本信息

        Args:
            fund_code: 基金代码

        Returns:
            dict: 基金信息
        """
        url = f"http://fund.eastmoney.com/pingzhundata/{fund_code}.html"

        try:
            response = self._make_request(url)
            if not response:
                return {}

            # 解析返回的 JSON 数据
            text = response.text

            result = {
                'fund_code': fund_code,
                'name': '',
                'type': '',
                'establish_date': '',
                'manager': '',
                'company': ''
            }

            # 提取基金名称
            name_match = re.search(r'<span class="funCur-FundName">(.*?)</span>', text)
            if name_match:
                result['name'] = name_match.group(1).strip()

            # 提取基金类型
            type_match = re.search(r'基金类型：.*?title="(.*?)"', text)
            if type_match:
                result['type'] = type_match.group(1)

            return result

        except Exception as e:
            logger.error(f"获取基金信息失败: {fund_code}, {str(e)}")
            return {}

    def get_fund_realtime(self, fund_codes: List[str]) -> Dict[str, Dict]:
        """
        获取基金实时净值

        Args:
            fund_codes: 基金代码列表

        Returns:
            dict: {fund_code: {nav, nav_date, ...}}
        """
        result = {}

        for code in fund_codes:
            try:
                url = f"http://fundgz.eastmoney.com/js/{code}.js"
                response = self._make_request(url)

                if not response:
                    continue

                text = response.text

                # 解析 JSONP 响应: jsonpgz({"fundcode":"000001",...})
                match = re.search(r'jsonpgz\((.*?)\)', text)
                if match:
                    data = json.loads(match.group(1))
                    result[code] = {
                        'name': data.get('name', ''),
                        'nav': float(data.get('gsz', 0)),  # 估算净值
                        'nav_date': data.get('gztime', ''),  # 估值时间
                        'gszzl': float(data.get('gszzl', 0)),  # 估算涨跌幅
                        'jzrq': data.get('jzrq', ''),  # 净值日期
                        'dwjz': float(data.get('dwjz', 0))  # 单位净值
                    }

            except Exception as e:
                logger.warning(f"获取基金实时数据失败: {code}, {str(e)}")
                continue

        return result

    def get_fund_nav_history(self, fund_code: str, start_date: str, end_date: str,
                             page: int = 1, page_size: int = 1000) -> pd.DataFrame:
        """
        获取基金净值历史数据

        Args:
            fund_code: 基金代码
            start_date: 开始日期，格式 '2023-01-01'
            end_date: 结束日期，格式 '2024-01-01'
            page: 页码
            page_size: 每页数量

        Returns:
            DataFrame: 净值历史数据
        """
        try:
            params = {
                'fundCode': fund_code,
                'pageIndex': page,
                'pageSize': page_size,
                'startDate': start_date.replace('-', ''),
                'endDate': end_date.replace('-', ''),
                'perFundType': ''  # 空表示单位净值
            }

            response = self._make_request(self.FUND_HISTORY_URL, params)

            if not response:
                return pd.DataFrame()

            data = response.json()

            if not data:
                logger.warning(f"API返回空数据: {fund_code}")
                return pd.DataFrame()

            if data.get('ErrCode') != 0:
                logger.error(f"API返回错误: {data.get('ErrMsg', 'Unknown')}")
                return pd.DataFrame()

            # 安全获取数据，防止 None 导致的异常
            data_obj = data.get('Data')
            if not data_obj:
                logger.warning(f"API返回数据为空: {fund_code}")
                return pd.DataFrame()

            items = data_obj.get('LSJZList', [])

            if not items:
                return pd.DataFrame()

            # 构建DataFrame
            records = []
            for item in items:
                records.append({
                    'date': item.get('FSRQ', ''),  # 净值日期
                    'nav': float(item.get('DWJZ', 0)) if item.get('DWJZ') else None,  # 单位净值
                    'acc_nav': float(item.get('LJJZ', 0)) if item.get('LJJZ') else None,  # 累计净值
                    'change_pct': float(item.get('JZZZL', 0)) if item.get('JZZZL') else None,  # 日增长率
                    'subscription_status': item.get('SGZT', ''),  # 申购状态
                    'redemption_status': item.get('SHZT', '')  # 赎回状态
                })

            df = pd.DataFrame(records)

            if df.empty:
                return df

            # 按日期排序
            df = df.sort_values('date')
            df = df.reset_index(drop=True)

            return df

        except Exception as e:
            logger.error(f"获取基金净值历史失败: {fund_code}, {str(e)}")
            return pd.DataFrame()

    def get_fund_list_by_akshare(self) -> List[Dict]:
        """
        通过AKShare获取基金列表（备用）

        Returns:
            list: 基金列表
        """
        try:
            import akshare as ak
            df = ak.fund_open_fund_info_em()
            if df is not None and len(df) > 0:
                return df.to_dict('records')
        except Exception as e:
            logger.error(f"AKShare获取基金列表失败: {str(e)}")
        return []

    def get_fund_all_nav_history(self, fund_code: str, years: int = 5) -> pd.DataFrame:
        """
        获取基金全部净值历史数据

        Args:
            fund_code: 基金代码
            years: 获取最近N年数据

        Returns:
            DataFrame: 净值历史数据
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=years*365)).strftime('%Y-%m-%d')

        all_data = []
        page = 1
        page_size = 500

        while True:
            df = self.get_fund_nav_history(fund_code, start_date, end_date, page, page_size)

            if df.empty:
                break

            all_data.append(df)

            # 如果返回数据少于页面大小，说明没有更多数据了
            if len(df) < page_size:
                break

            page += 1

        if not all_data:
            return pd.DataFrame()

        result = pd.concat(all_data, ignore_index=True)
        return result

    def get_fund_dividend_history(self, fund_code: str) -> pd.DataFrame:
        """
        获取基金分红历史

        Args:
            fund_code: 基金代码

        Returns:
            DataFrame: 分红历史
        """
        url = f"http://api.fund.eastmoney.com/f10/fhsp"
        params = {
            'fundCode': fund_code,
            'pageIndex': 1,
            'pageSize': 100,
            'type': ''
        }

        try:
            response = self._make_request(url, params)

            if not response:
                return pd.DataFrame()

            data = response.json()

            if not data:
                return pd.DataFrame()

            if data.get('ErrCode') != 0:
                return pd.DataFrame()

            # 安全获取数据
            data_obj = data.get('Data')
            if not data_obj:
                return pd.DataFrame()

            items = data_obj.get('FHSPList', [])

            if not items:
                return pd.DataFrame()

            records = []
            for item in items:
                records.append({
                    'date': item.get('FSRQ', ''),  # 权益登记日
                    'ex_dividend_date': item.get('CXRQ', ''),  # 除息日
                    'dividend_per_unit': float(item.get('FHBL', 0)) if item.get('FHBL') else 0,  # 每份分红
                    'dividend_type': item.get('FHLB', '')  # 分红方式
                })

            return pd.DataFrame(records)

        except Exception as e:
            logger.error(f"获取基金分红历史失败: {fund_code}, {str(e)}")
            return pd.DataFrame()

    def search_fund(self, keyword: str, page: int = 1, page_size: int = 20) -> List[Dict]:
        """
        搜索基金

        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量

        Returns:
            list: 基金列表
        """
        url = "http://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx"
        params = {
            'm': '1',
            'key': keyword,
            'page': page,
            'size': page_size
        }

        try:
            response = self._make_request(url, params)

            if not response:
                return []

            data = response.json()

            funds = data.get('Datas', [])

            result = []
            for fund in funds:
                result.append({
                    'code': fund.get('CODE', ''),
                    'name': fund.get('NAME', ''),
                    'type': fund.get('FundBaseInfo', {}).get('FTYPE', ''),
                    'establish_date': fund.get('FundBaseInfo', {}).get('ESTABDATE', '')
                })

            return result

        except Exception as e:
            logger.error(f"搜索基金失败: {keyword}, {str(e)}")
            return []


# 全局实例
eastmoney_fund_service = EastMoneyFundService()


def get_eastmoney_fund_service() -> EastMoneyFundService:
    """获取天天基金服务实例"""
    return eastmoney_fund_service