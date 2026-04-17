#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收益计算服务 - 支持智能止盈/加仓策略
根据实际交易记录计算已操作比例，给出下一步操作建议
"""

from typing import List, Dict, Tuple, Optional
from decimal import Decimal


class ProfitService:
    """收益计算服务"""

    # 止盈阈值（分三档，每档卖出比例）
    STOP_PROFIT_LEVELS = [
        {'threshold': 0.15, 'sell_ratio': 0.30, 'name': '第一档止盈'},
        {'threshold': 0.18, 'sell_ratio': 0.30, 'name': '第二档止盈'},
        {'threshold': 0.20, 'sell_ratio': 0.40, 'name': '第三档止盈'},
    ]

    # 加仓阈值（金字塔加仓）
    ADD_POSITION_LEVELS = [
        {'threshold': -0.05, 'add_ratio': 0.05, 'name': '第一档加仓'},
        {'threshold': -0.10, 'add_ratio': 0.10, 'name': '第二档加仓'},
        {'threshold': -0.15, 'add_ratio': 0.15, 'name': '第三档加仓'},
        {'threshold': -0.20, 'add_ratio': 0.20, 'name': '第四档加仓'},
        {'threshold': -0.25, 'add_ratio': 0.25, 'name': '第五档加仓'},
        {'threshold': -0.30, 'add_ratio': 0.30, 'name': '第六档加仓'},
    ]

    MAX_ADD_RATIO = 0.30  # 最大加仓比例

    def __init__(self, stop_profit_target: float = 0.20, max_loss: float = 0.30):
        self.stop_profit_target = stop_profit_target
        self.max_loss = max_loss

    def calculate_profit(
        self,
        cost_price: float,
        current_price: float,
        quantity: int,
        original_quantity: int = None,
        sell_records: List[Dict] = None,
        add_position_ratio: float = 0
    ) -> Dict:
        """
        计算持仓收益（智能止盈策略）

        Args:
            cost_price: 成本价
            current_price: 当前价格
            quantity: 当前持仓数量
            original_quantity: 原始持仓数量（用于计算卖出比例）
            sell_records: 卖出交易记录 [{'date': date, 'quantity': int}, ...]
            add_position_ratio: 已加仓比例

        Returns:
            收益计算结果字典，包含建议操作份额和金额
        """
        cost_price = float(cost_price)
        current_price = float(current_price)

        # 计算收益
        total_cost = cost_price * quantity
        market_value = current_price * quantity
        profit_amount = market_value - total_cost
        profit_rate = (current_price - cost_price) / cost_price if cost_price > 0 else 0

        # 计算已卖出比例（智能判断）
        sold_ratio = 0
        if original_quantity and original_quantity > 0 and quantity < original_quantity:
            sold_ratio = (original_quantity - quantity) / original_quantity

        # 判断信号（传入实际卖出比例、持仓数量和当前价格用于计算建议份额）
        stop_profit_signal, add_position_signal, signal_level, suggestion, suggestion_ratio, suggestion_quantity, suggestion_amount = \
            self._check_signals_smart(profit_rate, sold_ratio, sell_records, add_position_ratio, quantity, current_price)

        return {
            'total_cost': round(total_cost, 2),
            'market_value': round(market_value, 2),
            'profit_amount': round(profit_amount, 2),
            'profit_rate': round(profit_rate, 4),
            'stop_profit_signal': stop_profit_signal,
            'add_position_signal': add_position_signal,
            'signal_level': signal_level,
            'suggestion': suggestion,
            'suggestion_ratio': suggestion_ratio,  # 建议操作比例
            'suggestion_quantity': suggestion_quantity,  # 建议操作份额
            'suggestion_amount': suggestion_amount,  # 建议操作金额
            'current_state': {
                'sold_ratio': round(sold_ratio, 4),
                'add_position_ratio': add_position_ratio,
                'original_quantity': original_quantity,
                'current_quantity': quantity
            }
        }

    def _check_signals_smart(
        self,
        profit_rate: float,
        sold_ratio: float,
        sell_records: List[Dict] = None,
        add_position_ratio: float = 0,
        current_quantity: int = 0,
        current_price: float = 0
    ) -> Tuple[bool, bool, str, str, float, int, float]:
        """
        智能检查止盈/加仓信号

        根据收益率和实际卖出比例判断当前状态，给出下一步操作建议

        Args:
            profit_rate: 收益率
            sold_ratio: 已卖出比例（基于原始持仓）
            sell_records: 卖出交易记录
            add_position_ratio: 已加仓比例
            current_quantity: 当前持仓数量（用于计算建议份额）
            current_price: 当前价格（用于计算建议金额）

        Returns:
            (stop_profit_signal, add_position_signal, signal_level, suggestion, suggestion_ratio, suggestion_quantity, suggestion_amount)
        """
        # 检查止盈信号（正向收益）
        if profit_rate >= 0:
            return self._check_stop_profit_smart(profit_rate, sold_ratio, add_position_ratio, sell_records, current_quantity, current_price)

        # 检查加仓信号（负向收益）- 同时传入已减仓比例
        else:
            return self._check_add_position_smart(profit_rate, add_position_ratio, sold_ratio, current_quantity, current_price)

    def _check_stop_profit_smart(
        self,
        profit_rate: float,
        sold_ratio: float,
        add_position_ratio: float = 0,
        sell_records: List[Dict] = None,
        current_quantity: int = 0,
        current_price: float = 0
    ) -> Tuple[bool, bool, str, str, float, int, float]:
        """
        智能止盈信号检查

        根据收益率和已卖出比例判断：
        - 如果已卖出比例达到当前档位要求，提示下一档
        - 如果未达到，提示继续完成当前档位

        Returns:
            (stop_profit_signal, add_position_signal, signal_level, suggestion, suggestion_ratio, suggestion_quantity, suggestion_amount)
        """
        # 判断当前应该处于哪一档止盈
        current_level = 0
        for j, level in enumerate(self.STOP_PROFIT_LEVELS):
            if profit_rate >= level['threshold']:
                current_level = j + 1

        # 计算理论卖出比例（根据当前档位）
        # 第一档应卖出 30%，第二档应再卖出 30%（累计60%），第三档卖出剩余 40%（累计100%）
        target_sell_ratios = [0.30, 0.60, 1.00]

        # 默认返回值（无建议操作）
        default_return = (False, False, "持有",
                          f"收益率{profit_rate*100:.1f}%，已减仓{sold_ratio*100:.0f}%，已加仓{add_position_ratio*100:.0f}%，继续持有",
                          0, 0, 0)

        if current_level == 0:
            # 未达到止盈阈值
            return default_return

        elif current_level == 1:
            # 收益率在 15%-18% 区间
            target_ratio = target_sell_ratios[0]  # 30%
            if sold_ratio >= target_ratio:
                # 已完成第一档止盈
                return (False, False, "第一档完成", f"收益率{profit_rate*100:.1f}%，已减仓{sold_ratio*100:.1f}%，第一档止盈完成，等待收益率达到18%触发第二档", 0, 0, 0)
            else:
                # 需要继续卖出完成第一档
                remaining_ratio = target_ratio - sold_ratio
                remaining_qty, remaining_amount = self._calculate_operation_amount(remaining_ratio, current_quantity, current_price, 'sell')
                return (True, False, "第一档止盈（进行中）",
                        f"收益率{profit_rate*100:.1f}%，已减仓{sold_ratio*100:.1f}%，建议减仓{remaining_ratio*100:.1f}%（{remaining_qty}份，约{remaining_amount}元）",
                        remaining_ratio, remaining_qty, remaining_amount)

        elif current_level == 2:
            # 收益率在 18%-20% 区间
            target_ratio = target_sell_ratios[1]  # 60%
            if sold_ratio >= target_ratio:
                # 已完成第二档止盈
                return (False, False, "第二档完成", f"收益率{profit_rate*100:.1f}%，已减仓{sold_ratio*100:.1f}%，第二档止盈完成，等待收益率达到20%触发第三档", 0, 0, 0)
            elif sold_ratio >= target_sell_ratios[0]:
                # 已完成第一档，需要继续第二档
                remaining_ratio = target_ratio - sold_ratio
                remaining_qty, remaining_amount = self._calculate_operation_amount(remaining_ratio, current_quantity, current_price, 'sell')
                return (True, False, "第二档止盈（进行中）",
                        f"收益率{profit_rate*100:.1f}%，已减仓{sold_ratio*100:.1f}%，建议减仓{remaining_ratio*100:.1f}%（{remaining_qty}份，约{remaining_amount}元）",
                        remaining_ratio, remaining_qty, remaining_amount)
            else:
                # 第一档也没完成，跳到第二档
                remaining_ratio = target_ratio - sold_ratio
                remaining_qty, remaining_amount = self._calculate_operation_amount(remaining_ratio, current_quantity, current_price, 'sell')
                return (True, False, "第二档止盈",
                        f"收益率{profit_rate*100:.1f}%，已减仓{sold_ratio*100:.1f}%，建议减仓{remaining_ratio*100:.1f}%（{remaining_qty}份，约{remaining_amount}元）",
                        remaining_ratio, remaining_qty, remaining_amount)

        elif current_level >= 3:
            # 收益率 >= 20%
            target_ratio = target_sell_ratios[2]  # 100%
            if sold_ratio >= target_ratio:
                # 已完成全部止盈
                return (False, False, "止盈完成", f"收益率{profit_rate*100:.1f}%，已减仓{sold_ratio*100:.1f}%，三档止盈均已完成，已清仓", 0, 0, 0)
            elif sold_ratio >= target_sell_ratios[1]:
                # 已完成前两档，需要第三档
                remaining_ratio = target_ratio - sold_ratio
                remaining_qty, remaining_amount = self._calculate_operation_amount(remaining_ratio, current_quantity, current_price, 'sell')
                return (True, False, "第三档止盈（进行中）",
                        f"收益率{profit_rate*100:.1f}%，已减仓{sold_ratio*100:.1f}%，建议减仓剩余{remaining_ratio*100:.1f}%（{remaining_qty}份，约{remaining_amount}元）",
                        remaining_ratio, remaining_qty, remaining_amount)
            else:
                # 需要完成剩余止盈
                remaining_ratio = target_ratio - sold_ratio
                remaining_qty, remaining_amount = self._calculate_operation_amount(remaining_ratio, current_quantity, current_price, 'sell')
                return (True, False, "第三档止盈",
                        f"收益率{profit_rate*100:.1f}%，已减仓{sold_ratio*100:.1f}%，建议减仓剩余{remaining_ratio*100:.1f}%（{remaining_qty}份，约{remaining_amount}元）",
                        remaining_ratio, remaining_qty, remaining_amount)

        # 超过25%启动移动止盈
        if profit_rate >= 0.25 and sold_ratio < 1.0:
            remaining_ratio = 1.0 - sold_ratio
            remaining_qty, remaining_amount = self._calculate_operation_amount(remaining_ratio, current_quantity, current_price, 'sell')
            return (True, False, "移动止盈",
                    f"收益率{profit_rate*100:.1f}%，已减仓{sold_ratio*100:.1f}%，建议设置回撤10%清仓或减仓剩余{remaining_ratio*100:.1f}%（{remaining_qty}份）",
                    remaining_ratio, remaining_qty, remaining_amount)

        return default_return

    def _check_add_position_smart(
        self,
        profit_rate: float,
        add_position_ratio: float,
        sold_ratio: float = 0,
        current_quantity: int = 0,
        current_price: float = 0
    ) -> Tuple[bool, bool, str, str, float, int, float]:
        """
        智能加仓信号检查（金字塔加仓）

        根据收益率和已加仓比例判断下一步加仓建议
        同时显示已减仓比例（用户可能做了其他操作）

        Returns:
            (stop_profit_signal, add_position_signal, signal_level, suggestion, suggestion_ratio, suggestion_quantity, suggestion_amount)
        """
        # 判断当前应该处于哪一档加仓
        current_level = 0
        for j, level in enumerate(self.ADD_POSITION_LEVELS):
            if profit_rate <= level['threshold']:
                current_level = j + 1

        # 格式化已加仓和已减仓信息
        added_info = f"已加仓{add_position_ratio*100:.0f}%"
        sold_info = f"已减仓{sold_ratio*100:.0f}%"

        # 默认返回值（无建议操作）
        default_return = (False, False, "观察", f"浮亏{abs(profit_rate)*100:.1f}%，{added_info}，{sold_info}，继续观察", 0, 0, 0)

        if current_level == 0:
            # 浮亏未达到加仓阈值
            return default_return

        if add_position_ratio >= self.MAX_ADD_RATIO:
            return (False, False, "加仓完成", f"浮亏{abs(profit_rate)*100:.1f}%，{added_info}，{sold_info}，达到上限，建议止损观望", 0, 0, 0)

        # 判断需要加仓多少
        level_info = self.ADD_POSITION_LEVELS[current_level - 1]
        target_add_ratios = [0.05, 0.15, 0.30, 0.50, 0.75, 1.05]  # 累计加仓比例

        if add_position_ratio < target_add_ratios[current_level - 1]:
            remaining_add = target_add_ratios[current_level - 1] - add_position_ratio
            # 加仓份额基于当前市值的比例计算
            remaining_qty, remaining_amount = self._calculate_operation_amount(remaining_add, current_quantity, current_price, 'add')
            return (False, True, level_info['name'],
                    f"浮亏{abs(profit_rate)*100:.1f}%，{added_info}，{sold_info}，建议继续加仓{remaining_add*100:.0f}%（约{remaining_amount}元）",
                    remaining_add, remaining_qty, remaining_amount)

        return default_return

    def _calculate_operation_amount(
        self,
        ratio: float,
        current_quantity: int,
        current_price: float,
        operation_type: str = 'sell'
    ) -> Tuple[int, float]:
        """
        计算建议操作的份额和金额

        Args:
            ratio: 操作比例
            current_quantity: 当前持仓数量
            current_price: 当前价格
            operation_type: 'sell' 卖出，'add' 加仓

        Returns:
            (suggestion_quantity, suggestion_amount)
        """
        if ratio <= 0 or current_price <= 0:
            return 0, 0

        if operation_type == 'sell':
            # 卖出：基于当前持仓数量计算
            suggestion_qty = int(current_quantity * ratio)
            suggestion_amount = round(suggestion_qty * current_price, 2)
        else:
            # 加仓：基于当前市值的比例计算金额，份额需要除以价格
            current_value = current_quantity * current_price
            suggestion_amount = round(current_value * ratio, 2)
            suggestion_qty = int(suggestion_amount / current_price) if current_price > 0 else 0

        return suggestion_qty, suggestion_amount

    def portfolio_summary(self, positions: List[Dict]) -> Dict:
        """
        投资组合汇总

        Args:
            positions: 持仓列表，每个持仓包含 cost_price, current_price, quantity,
                      以及可选的 original_quantity, sell_records, add_position_ratio

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
                p.get('quantity', 0),
                original_quantity=p.get('original_quantity'),
                sell_records=p.get('sell_records'),
                add_position_ratio=p.get('add_position_ratio', 0)
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