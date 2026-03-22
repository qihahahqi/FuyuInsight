#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入导出服务
"""

from typing import List, Dict, Optional
from io import BytesIO
from datetime import datetime
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side


class ExportService:
    """导入导出服务"""

    # 表头样式
    HEADER_FILL = PatternFill(start_color="4A90E2", end_color="4A90E2", fill_type="solid")
    HEADER_FONT = Font(bold=True, color="FFFFFF")
    HEADER_ALIGNMENT = Alignment(horizontal="center", vertical="center")

    def export_positions_to_excel(self, positions: List[Dict], filename: str = "positions.xlsx") -> BytesIO:
        """
        导出持仓到 Excel

        Args:
            positions: 持仓数据列表
            filename: 文件名

        Returns:
            BytesIO: Excel 文件流
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "持仓明细"

        # 表头
        headers = ["代码", "名称", "类型", "数量", "成本价", "现价", "总成本", "市值", "收益率", "分类", "备注"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = self.HEADER_FILL
            cell.font = self.HEADER_FONT
            cell.alignment = self.HEADER_ALIGNMENT

        # 数据行
        for row, p in enumerate(positions, 2):
            ws.cell(row=row, column=1, value=p.get('symbol', ''))
            ws.cell(row=row, column=2, value=p.get('name', ''))
            ws.cell(row=row, column=3, value=self._get_asset_type_label(p.get('asset_type', '')))
            ws.cell(row=row, column=4, value=p.get('quantity', 0))
            ws.cell(row=row, column=5, value=p.get('cost_price', 0))
            ws.cell(row=row, column=6, value=p.get('current_price') or '')
            ws.cell(row=row, column=7, value=p.get('total_cost', 0))
            ws.cell(row=row, column=8, value=p.get('market_value') or '')
            ws.cell(row=row, column=9, value=f"{p.get('profit_rate', 0)*100:.2f}%" if p.get('profit_rate') is not None else '')
            ws.cell(row=row, column=10, value=p.get('category') or '')
            ws.cell(row=row, column=11, value=p.get('notes') or '')

        # 调整列宽
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 10
        ws.column_dimensions['D'].width = 10
        ws.column_dimensions['E'].width = 10
        ws.column_dimensions['F'].width = 10
        ws.column_dimensions['G'].width = 12
        ws.column_dimensions['H'].width = 12
        ws.column_dimensions['I'].width = 10
        ws.column_dimensions['J'].width = 10
        ws.column_dimensions['K'].width = 20

        # 保存到 BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    def export_trades_to_excel(self, trades: List[Dict], filename: str = "trades.xlsx") -> BytesIO:
        """
        导出交易记录到 Excel

        Args:
            trades: 交易记录列表
            filename: 文件名

        Returns:
            BytesIO: Excel 文件流
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "交易记录"

        # 表头
        headers = ["日期", "代码", "类型", "数量", "价格", "金额", "理由", "备注"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = self.HEADER_FILL
            cell.font = self.HEADER_FONT
            cell.alignment = self.HEADER_ALIGNMENT

        # 数据行
        for row, t in enumerate(trades, 2):
            ws.cell(row=row, column=1, value=t.get('trade_date', ''))
            ws.cell(row=row, column=2, value=t.get('symbol', ''))
            ws.cell(row=row, column=3, value='买入' if t.get('trade_type') == 'buy' else '卖出')
            ws.cell(row=row, column=4, value=t.get('quantity', 0))
            ws.cell(row=row, column=5, value=t.get('price', 0))
            ws.cell(row=row, column=6, value=t.get('amount', 0))
            ws.cell(row=row, column=7, value=t.get('reason') or '')
            ws.cell(row=row, column=8, value=t.get('notes') or '')

        # 调整列宽
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 8
        ws.column_dimensions['D'].width = 10
        ws.column_dimensions['E'].width = 10
        ws.column_dimensions['F'].width = 12
        ws.column_dimensions['G'].width = 15
        ws.column_dimensions['H'].width = 20

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    def import_positions_from_excel(self, file_stream) -> List[Dict]:
        """
        从 Excel 导入持仓

        Args:
            file_stream: 文件流

        Returns:
            List[Dict]: 持仓数据列表
        """
        df = pd.read_excel(file_stream)

        # 列名映射
        column_map = {
            '代码': 'symbol',
            '名称': 'name',
            '类型': 'asset_type',
            '数量': 'quantity',
            '成本价': 'cost_price',
            '现价': 'current_price',
            '总成本': 'total_cost',
            '市值': 'market_value',
            '收益率': 'profit_rate',
            '分类': 'category',
            '备注': 'notes'
        }

        df = df.rename(columns=column_map)

        # 转换资产类型
        type_map = {
            '宽基ETF': 'etf_index',
            '行业ETF': 'etf_sector',
            '基金': 'fund',
            '股票': 'stock'
        }

        results = []
        for _, row in df.iterrows():
            if pd.isna(row.get('symbol')) or pd.isna(row.get('name')):
                continue

            asset_type = row.get('asset_type', '')
            if asset_type in type_map:
                asset_type = type_map[asset_type]

            # 处理收益率
            profit_rate = row.get('profit_rate')
            if isinstance(profit_rate, str):
                profit_rate = float(profit_rate.replace('%', '')) / 100

            results.append({
                'symbol': str(row.get('symbol', '')).strip(),
                'name': str(row.get('name', '')).strip(),
                'asset_type': asset_type or 'etf_index',
                'quantity': int(row.get('quantity', 0)) if not pd.isna(row.get('quantity')) else 0,
                'cost_price': float(row.get('cost_price', 0)) if not pd.isna(row.get('cost_price')) else 0,
                'current_price': float(row.get('current_price')) if not pd.isna(row.get('current_price')) else None,
                'total_cost': float(row.get('total_cost', 0)) if not pd.isna(row.get('total_cost')) else 0,
                'market_value': float(row.get('market_value')) if not pd.isna(row.get('market_value')) else None,
                'profit_rate': profit_rate,
                'category': str(row.get('category', '')).strip() if not pd.isna(row.get('category')) else None,
                'notes': str(row.get('notes', '')).strip() if not pd.isna(row.get('notes')) else None
            })

        return results

    def import_positions_from_csv(self, file_stream) -> List[Dict]:
        """
        从 CSV 导入持仓

        Args:
            file_stream: 文件流

        Returns:
            List[Dict]: 持仓数据列表
        """
        df = pd.read_csv(file_stream)
        return self._parse_dataframe(df)

    def _parse_dataframe(self, df: pd.DataFrame) -> List[Dict]:
        """解析 DataFrame"""
        results = []
        for _, row in df.iterrows():
            results.append({
                'symbol': str(row.get('symbol', '')).strip(),
                'name': str(row.get('name', '')).strip(),
                'asset_type': row.get('asset_type', 'etf_index'),
                'quantity': int(row.get('quantity', 0)),
                'cost_price': float(row.get('cost_price', 0)),
                'current_price': float(row.get('current_price')) if pd.notna(row.get('current_price')) else None,
                'category': row.get('category'),
                'notes': row.get('notes')
            })
        return results

    def _get_asset_type_label(self, asset_type: str) -> str:
        """获取资产类型标签"""
        labels = {
            'etf_index': '宽基ETF',
            'etf_sector': '行业ETF',
            'fund': '基金',
            'stock': '股票'
        }
        return labels.get(asset_type, asset_type)

    def export_positions_template(self) -> BytesIO:
        """
        生成持仓导入模板（带字段说明）
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "持仓导入模板"

        # 表头（带必填标记）
        headers = [
            ("代码*", "symbol"),
            ("名称*", "name"),
            ("类型", "asset_type"),
            ("数量*", "quantity"),
            ("成本价*", "cost_price"),
            ("现价", "current_price"),
            ("总成本", "total_cost"),
            ("市值", "market_value"),
            ("收益率", "profit_rate"),
            ("分类", "category"),
            ("备注", "notes")
        ]

        for col, (header, _) in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = self.HEADER_FILL
            cell.font = self.HEADER_FONT
            cell.alignment = self.HEADER_ALIGNMENT

        # 示例数据
        example_data = [
            ["510300", "沪深300ETF", "宽基ETF", 5000, 4.000, 4.200, 20000, 21000, "5%", "core", "示例数据"],
            ["159915", "创业板ETF", "宽基ETF", 3000, 2.500, 2.600, 7500, 7800, "4%", "satellite", ""],
            ["515030", "新能源ETF", "行业ETF", 2000, 3.000, "", 6000, "", "", "aggressive", "观察仓"]
        ]

        for row_idx, row_data in enumerate(example_data, 2):
            for col_idx, value in enumerate(row_data, 1):
                ws.cell(row=row_idx, column=col_idx, value=value)

        # 添加说明工作表
        ws_desc = wb.create_sheet("字段说明")
        descriptions = [
            ["字段名", "是否必填", "说明", "示例值"],
            ["代码", "是", "标的代码，如 510300", "510300"],
            ["名称", "是", "标的名称", "沪深300ETF"],
            ["类型", "否", "资产类型：宽基ETF/行业ETF/基金/股票，默认为宽基ETF", "宽基ETF"],
            ["数量", "是", "持有数量（股/份）", "5000"],
            ["成本价", "是", "买入成本价", "4.000"],
            ["现价", "否", "当前价格，不填则无法计算市值", "4.200"],
            ["总成本", "否", "总成本金额，不填则自动计算（数量×成本价）", "20000"],
            ["市值", "否", "当前市值，需填写现价", "21000"],
            ["收益率", "否", "收益率百分比，如 5%", "5%"],
            ["分类", "否", "仓位分类：core(核心)/satellite(卫星)/aggressive(进攻)", "core"],
            ["备注", "否", "备注信息", "定投标的"]
        ]

        for row_idx, row_data in enumerate(descriptions, 1):
            for col_idx, value in enumerate(row_data, 1):
                cell = ws_desc.cell(row=row_idx, column=col_idx, value=value)
                if row_idx == 1:
                    cell.fill = self.HEADER_FILL
                    cell.font = self.HEADER_FONT

        ws_desc.column_dimensions['A'].width = 12
        ws_desc.column_dimensions['B'].width = 10
        ws_desc.column_dimensions['C'].width = 40
        ws_desc.column_dimensions['D'].width = 15

        # 调整主表列宽
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 10
        ws.column_dimensions['D'].width = 10
        ws.column_dimensions['E'].width = 10
        ws.column_dimensions['F'].width = 10
        ws.column_dimensions['G'].width = 12
        ws.column_dimensions['H'].width = 12
        ws.column_dimensions['I'].width = 10
        ws.column_dimensions['J'].width = 12
        ws.column_dimensions['K'].width = 20

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    def export_trades_template(self) -> BytesIO:
        """
        生成交易记录导入模板（带字段说明）
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "交易记录导入模板"

        # 表头（带必填标记）
        headers = [
            ("日期*", "trade_date"),
            ("代码*", "symbol"),
            ("类型*", "trade_type"),
            ("数量*", "quantity"),
            ("价格*", "price"),
            ("金额", "amount"),
            ("理由", "reason"),
            ("备注", "notes")
        ]

        for col, (header, _) in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = self.HEADER_FILL
            cell.font = self.HEADER_FONT
            cell.alignment = self.HEADER_ALIGNMENT

        # 示例数据
        example_data = [
            ["2024-01-15", "510300", "买入", 1000, 4.000, 4000, "低估建仓", "定投"],
            ["2024-02-20", "510300", "买入", 500, 3.900, 1950, "加仓", ""],
            ["2024-03-10", "159915", "卖出", 1000, 2.800, 2800, "止盈", "获利了结"]
        ]

        for row_idx, row_data in enumerate(example_data, 2):
            for col_idx, value in enumerate(row_data, 1):
                ws.cell(row=row_idx, column=col_idx, value=value)

        # 添加说明工作表
        ws_desc = wb.create_sheet("字段说明")
        descriptions = [
            ["字段名", "是否必填", "说明", "示例值"],
            ["日期", "是", "交易日期，格式：YYYY-MM-DD", "2024-01-15"],
            ["代码", "是", "标的代码，如 510300", "510300"],
            ["类型", "是", "交易类型：买入/卖出", "买入"],
            ["数量", "是", "交易数量（股/份）", "1000"],
            ["价格", "是", "交易价格", "4.000"],
            ["金额", "否", "交易金额，不填则自动计算（数量×价格）", "4000"],
            ["理由", "否", "交易理由，如：低估建仓/止盈/止损", "低估建仓"],
            ["备注", "否", "备注信息", "定投"]
        ]

        for row_idx, row_data in enumerate(descriptions, 1):
            for col_idx, value in enumerate(row_data, 1):
                cell = ws_desc.cell(row=row_idx, column=col_idx, value=value)
                if row_idx == 1:
                    cell.fill = self.HEADER_FILL
                    cell.font = self.HEADER_FONT

        ws_desc.column_dimensions['A'].width = 12
        ws_desc.column_dimensions['B'].width = 10
        ws_desc.column_dimensions['C'].width = 35
        ws_desc.column_dimensions['D'].width = 15

        # 调整主表列宽
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 8
        ws.column_dimensions['D'].width = 10
        ws.column_dimensions['E'].width = 10
        ws.column_dimensions['F'].width = 12
        ws.column_dimensions['G'].width = 15
        ws.column_dimensions['H'].width = 20

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    def import_trades_from_excel(self, file_stream) -> List[Dict]:
        """
        从 Excel 导入交易记录

        Args:
            file_stream: 文件流

        Returns:
            List[Dict]: 交易记录列表
        """
        df = pd.read_excel(file_stream, sheet_name=0)  # 只读取第一个工作表

        # 列名映射
        column_map = {
            '日期': 'trade_date',
            '代码': 'symbol',
            '类型': 'trade_type',
            '数量': 'quantity',
            '价格': 'price',
            '金额': 'amount',
            '理由': 'reason',
            '备注': 'notes'
        }

        df = df.rename(columns=column_map)

        results = []
        for _, row in df.iterrows():
            # 跳过空行或说明行
            if pd.isna(row.get('trade_date')) or pd.isna(row.get('symbol')):
                continue

            # 处理交易类型
            trade_type = str(row.get('trade_type', '')).strip()
            if trade_type == '买入':
                trade_type = 'buy'
            elif trade_type == '卖出':
                trade_type = 'sell'
            elif trade_type not in ['buy', 'sell']:
                continue  # 跳过无效类型

            # 处理日期
            trade_date = row.get('trade_date')
            if isinstance(trade_date, str):
                trade_date = trade_date.strip()
            elif hasattr(trade_date, 'strftime'):
                trade_date = trade_date.strftime('%Y-%m-%d')

            results.append({
                'trade_date': trade_date,
                'symbol': str(row.get('symbol', '')).strip(),
                'trade_type': trade_type,
                'quantity': int(row.get('quantity', 0)) if not pd.isna(row.get('quantity')) else 0,
                'price': float(row.get('price', 0)) if not pd.isna(row.get('price')) else 0,
                'amount': float(row.get('amount', 0)) if not pd.isna(row.get('amount')) else None,
                'reason': str(row.get('reason', '')).strip() if not pd.isna(row.get('reason')) else None,
                'notes': str(row.get('notes', '')).strip() if not pd.isna(row.get('notes')) else None
            })

        return results