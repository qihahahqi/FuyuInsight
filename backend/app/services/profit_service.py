#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收益计算服务
"""

from typing import List, Dict, Tuple, Optional
from decimal import Decimal


class ProfitService:
    """收益计算服务"""

    # 止盈阈值（分三档）
    STOP_PROFIT_LEVELS = [
        (0.15, "第一档止盈", "卖出30%"),
        (0.18, "第二档止盈", "再卖出30%"),
        (0.20, "第三档止盈", "卖出剩余40%"),
    ]

    # 加仓阈值（金字塔加仓）
    ADD_POSITION_LEVELS = [
        (-0.05, 0.05, "第一档加仓", "加仓5%"),
        (-0.10, 0.10, "第二档加仓", "加仓10%"),
        (-0.15, 0.15, "第三档加仓", "加仓15%"),
        (-0.20, 0.20, "第四档加仓", "加仓20%"),
        (-0.25, 0.25, "第五档加仓", "加仓25%"),
        (-0.30, 0.30, "第六档加仓", "加仓30%或止损观望"),
    ]

    def __init__(self, stop_profit_target: float = 0.20, max_loss: float = 0.30):
        self.stop_profit_target = stop_profit_target
        self.max_loss = max_loss

    def calculate_profit(
        self,
        cost_price: float,
        current_price: float,
        quantity: int
    ) -> Dict:
        """
        计算持仓收益

        Args:
            cost_price: 成本价
            current_price: 当前价格
            quantity: 持仓数量

        Returns:
            收益计算结果字典
        """
        cost_price = float(cost_price)
        current_price = float(current_price)

        # 计算收益
        total_cost = cost_price * quantity
        market_value = current_price * quantity
        profit_amount = market_value - total_cost
        profit_rate = (current_price - cost_price) / cost_price if cost_price > 0 else 0

        # 判断信号
        stop_profit_signal, add_position_signal, signal_level, suggestion = \
            self._check_signals(profit_rate)

        return {
            'total_cost': round(total_cost, 2),
            'market_value': round(market_value, 2),
            'profit_amount': round(profit_amount, 2),
            'profit_rate': round(profit_rate, 4),
            'stop_profit_signal': stop_profit_signal,
            'add_position_signal': add_position_signal,
            'signal_level': signal_level,
            'suggestion': suggestion
        }

    def _check_signals(self, profit_rate: float) -> Tuple[bool, bool, str, str]:
        """检查止盈/加仓信号"""

        # 检查止盈信号（正向收益）
        if profit_rate >= 0:
            for threshold, level, action in self.STOP_PROFIT_LEVELS:
                if profit_rate >= threshold:
                    return True, False, level, f"触发{level}（{threshold*100:.0f}%），建议{action}"

            # 超过25%启动移动止盈
            if profit_rate >= 0.25:
                return True, False, "移动止盈", f"收益率{profit_rate*100:.1f}%，设置回撤10%清仓"

            return False, False, "持有", f"收益率{profit_rate*100:.1f}%，未触发信号，继续持有"

        # 检查加仓信号（负向收益）
        else:
            for threshold, add_ratio, level, action in self.ADD_POSITION_LEVELS:
                if profit_rate <= threshold:
                    return False, True, level, f"触发{level}（{threshold*100:.0f}%），建议{action}"

            return False, False, "观察", f"浮亏{abs(profit_rate)*100:.1f}%，继续观察"

    def portfolio_summary(self, positions: List[Dict]) -> Dict:
        """
        投资组合汇总

        Args:
            positions: 持仓列表，每个持仓包含 cost_price, current_price, quantity

        Returns:
            汇总信息字典
        """
        total_cost = 0
        total_value = 0
        results = []
        stop_profit_count = 0
        add_position_count = 0

        for p in positions:
            result = self.calculate_profit(
                p.get('cost_price', 0),
                p.get('current_price') or p.get('cost_price', 0),
                p.get('quantity', 0)
            )
            result['position'] = p
            results.append(result)

            total_cost += result['total_cost']
            total_value += result['market_value']

            if result['stop_profit_signal']:
                stop_profit_count += 1
            if result['add_position_signal']:
                add_position_count += 1

        total_profit = total_value - total_cost
        total_profit_rate = total_profit / total_cost if total_cost > 0 else 0

        return {
            'total_cost': round(total_cost, 2),
            'total_value': round(total_value, 2),
            'total_profit': round(total_profit, 2),
            'total_profit_rate': round(total_profit_rate, 4),
            'position_count': len(positions),
            'stop_profit_signals': stop_profit_count,
            'add_position_signals': add_position_count,
            'details': results
        }

    def calculate_max_drawdown(self, values: List[float]) -> float:
        """
        计算最大回撤

        Args:
            values: 资产净值序列

        Returns:
            最大回撤率
        """
        if not values:
            return 0

        peak = values[0]
        max_dd = 0

        for value in values:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

        return round(max_dd, 4)

    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.03
    ) -> float:
        """
        计算夏普比率

        Args:
            returns: 收益率序列
            risk_free_rate: 无风险利率（年化）

        Returns:
            夏普比率
        """
        if not returns or len(returns) < 2:
            return 0

        import statistics

        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)

        if std_return == 0:
            return 0

        # 年化处理
        sharpe = (avg_return * 252 - risk_free_rate) / (std_return * (252 ** 0.5))
        return round(sharpe, 4)