#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测模拟服务 v2.0
支持多种策略的真实历史数据回测
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from datetime import datetime


class StrategyType(Enum):
    """策略类型"""
    DOUBLE_MA = "double_ma"           # 双均线策略
    BOLLINGER = "bollinger"           # 布林带策略
    RSI = "rsi"                       # RSI策略
    MOMENTUM = "momentum"             # 动量策略
    GRID = "grid"                     # 网格交易策略
    PYRAMID = "pyramid"               # 金字塔加仓策略


@dataclass
class TradeRecord:
    """交易记录"""
    date: str
    period: int
    price: float
    action: str
    direction: str  # buy/sell
    shares: int
    amount: float
    cash: float
    position_value: float
    total_value: float
    profit_rate: float
    signal_reason: str = ""


@dataclass
class BacktestResult:
    """回测结果"""
    strategy_name: str
    strategy_type: StrategyType
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_loss_ratio: float
    trade_count: int
    total_trades: int
    win_trades: int
    lose_trades: int
    records: List[TradeRecord] = field(default_factory=list)
    daily_values: List[Dict] = field(default_factory=list)
    indicators: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""


class BaseStrategy(ABC):
    """策略基类"""

    # 子类应覆盖此属性
    display_name: str = "基础策略"

    def __init__(self, params: Dict = None):
        # 合并默认参数和用户参数
        self.params = {**self.get_default_params(), **(params or {})}
        self.name = self.display_name  # 使用中文显示名

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号

        Args:
            data: 包含 'date', 'open', 'high', 'low', 'close', 'volume' 列的DataFrame

        Returns:
            DataFrame: 添加了 'signal' 列，1=买入，-1=卖出，0=持有
        """
        pass

    def get_required_fields(self) -> List[str]:
        """获取所需数据字段"""
        return ['date', 'close']

    def get_default_params(self) -> Dict:
        """获取默认参数"""
        return {}


class DoubleMAStrategy(BaseStrategy):
    """双均线策略"""

    display_name = "双均线策略"

    def get_default_params(self) -> Dict:
        return {
            'short_window': 5,
            'long_window': 20
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        short_window = self.params.get('short_window', 5)
        long_window = self.params.get('long_window', 20)

        # 计算均线
        df['ma_short'] = df['close'].rolling(window=short_window).mean()
        df['ma_long'] = df['close'].rolling(window=long_window).mean()

        # 生成信号
        df['signal'] = 0
        df.loc[df['ma_short'] > df['ma_long'], 'signal'] = 1
        df.loc[df['ma_short'] < df['ma_long'], 'signal'] = -1

        # 金叉死叉信号（只在交叉点产生交易信号）
        df['position'] = df['signal'].diff()
        df.loc[df['position'] == 2, 'trade_signal'] = 1   # 金叉买入
        df.loc[df['position'] == -2, 'trade_signal'] = -1  # 死叉卖出
        df['trade_signal'] = df['trade_signal'].fillna(0)

        return df


class BollingerBandsStrategy(BaseStrategy):
    """布林带策略"""

    display_name = "布林带策略"

    def get_default_params(self) -> Dict:
        return {
            'window': 20,
            'k': 2.0
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        window = self.params.get('window', 20)
        k = self.params.get('k', 2.0)

        # 计算布林带
        df['ma'] = df['close'].rolling(window=window).mean()
        df['std'] = df['close'].rolling(window=window).std()
        df['upper'] = df['ma'] + k * df['std']
        df['lower'] = df['ma'] - k * df['std']

        # 生成信号
        df['signal'] = 0
        df.loc[df['close'] < df['lower'], 'signal'] = 1   # 跌破下轨买入
        df.loc[df['close'] > df['upper'], 'signal'] = -1  # 突破上轨卖出

        # 只在首次突破时产生交易信号
        df['trade_signal'] = df['signal'].diff()
        df.loc[df['trade_signal'] == 1, 'trade_signal'] = 1
        df.loc[df['trade_signal'] == -1, 'trade_signal'] = -1
        df.loc[abs(df['trade_signal']) > 1, 'trade_signal'] = 0

        return df


class RSIStrategy(BaseStrategy):
    """RSI策略"""

    display_name = "RSI策略"

    def get_default_params(self) -> Dict:
        return {
            'period': 14,
            'oversold': 30,
            'overbought': 70
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        period = self.params.get('period', 14)
        oversold = self.params.get('oversold', 30)
        overbought = self.params.get('overbought', 70)

        # 计算RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # 生成信号
        df['signal'] = 0
        df.loc[df['rsi'] < oversold, 'signal'] = 1   # 超卖买入
        df.loc[df['rsi'] > overbought, 'signal'] = -1  # 超买卖出

        # 只在首次进入超买超卖区域时产生交易信号
        df['trade_signal'] = 0
        rsi_prev = df['rsi'].shift(1)

        # RSI从超卖区域向上突破
        df.loc[(rsi_prev < oversold) & (df['rsi'] >= oversold), 'trade_signal'] = 1
        # RSI从超买区域向下跌破
        df.loc[(rsi_prev > overbought) & (df['rsi'] <= overbought), 'trade_signal'] = -1

        return df


class MomentumStrategy(BaseStrategy):
    """动量策略"""

    display_name = "动量策略"

    def get_default_params(self) -> Dict:
        return {
            'window': 20,
            'buy_threshold': 0.05,
            'sell_threshold': -0.05
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        window = self.params.get('window', 20)
        buy_threshold = self.params.get('buy_threshold', 0.05)
        sell_threshold = self.params.get('sell_threshold', -0.05)

        # 计算动量（N日收益率）
        df['momentum'] = df['close'] / df['close'].shift(window) - 1

        # 生成信号
        df['signal'] = 0
        df.loc[df['momentum'] > buy_threshold, 'signal'] = 1
        df.loc[df['momentum'] < sell_threshold, 'signal'] = -1

        # 交易信号
        df['trade_signal'] = df['signal'].diff()
        df.loc[df['trade_signal'] == 1, 'trade_signal'] = 1
        df.loc[df['trade_signal'] == -1, 'trade_signal'] = -1
        df.loc[abs(df['trade_signal']) > 1, 'trade_signal'] = 0

        return df


class GridTradingStrategy(BaseStrategy):
    """网格交易策略"""

    display_name = "网格交易策略"

    def get_default_params(self) -> Dict:
        return {
            'grid_count': 10,
            'grid_range': 0.20,  # 网格范围（上下各20%）
            'base_position': 0.5  # 初始仓位
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        grid_count = self.params.get('grid_count', 10)
        grid_range = self.params.get('grid_range', 0.20)

        # 计算基准价格（使用第一个价格作为基准）
        base_price = df['close'].iloc[0]
        upper_price = base_price * (1 + grid_range)
        lower_price = base_price * (1 - grid_range)
        grid_size = (upper_price - lower_price) / grid_count

        # 计算网格位置
        df['grid_position'] = ((df['close'] - lower_price) / grid_size).astype(int)
        df['grid_position'] = df['grid_position'].clip(0, grid_count)

        # 生成信号：网格位置变化时交易
        df['grid_change'] = df['grid_position'].diff()
        df['trade_signal'] = 0

        # 价格下跌，网格位置减小，买入
        df.loc[df['grid_change'] > 0, 'trade_signal'] = 1
        # 价格上涨，网格位置增大，卖出
        df.loc[df['grid_change'] < 0, 'trade_signal'] = -1

        df['signal'] = df['trade_signal']

        return df


class PyramidStrategy(BaseStrategy):
    """金字塔加仓策略（原有策略优化版）"""

    display_name = "金字塔加仓策略"

    def get_default_params(self) -> Dict:
        return {
            'initial_position': 0.6,  # 初始仓位
            'stop_profit_levels': [0.15, 0.18, 0.20],
            'stop_profit_ratios': [0.30, 0.30, 0.40],
            'add_position_levels': {
                -0.05: 0.05,
                -0.10: 0.10,
                -0.15: 0.15,
                -0.20: 0.20,
                -0.25: 0.25,
            },
            'max_add_ratio': 1.0,
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """金字塔策略需要特殊处理，在回测引擎中实现"""
        df = data.copy()
        df['signal'] = 0
        df['trade_signal'] = 0
        return df


# 策略注册表
STRATEGY_REGISTRY = {
    StrategyType.DOUBLE_MA: DoubleMAStrategy,
    StrategyType.BOLLINGER: BollingerBandsStrategy,
    StrategyType.RSI: RSIStrategy,
    StrategyType.MOMENTUM: MomentumStrategy,
    StrategyType.GRID: GridTradingStrategy,
    StrategyType.PYRAMID: PyramidStrategy,
}


def create_strategy(strategy_type: StrategyType, params: Dict = None) -> BaseStrategy:
    """创建策略实例"""
    strategy_class = STRATEGY_REGISTRY.get(strategy_type)
    if not strategy_class:
        raise ValueError(f"未知策略类型: {strategy_type}")
    return strategy_class(params)


class BacktestEngine:
    """回测引擎"""

    def __init__(self, initial_capital: float = 100000, commission_rate: float = 0.0003):
        """
        初始化回测引擎

        Args:
            initial_capital: 初始资金
            commission_rate: 佣金费率
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.reset()

    def reset(self):
        """重置状态"""
        self.cash = self.initial_capital
        self.position = 0
        self.cost_price = 0
        self.trades: List[TradeRecord] = []
        self.daily_values: List[Dict] = []
        self.added_ratio = 0
        self.stop_profit_triggered = [False, False, False]

    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy: BaseStrategy,
        symbol: str = ""
    ) -> BacktestResult:
        """
        运行回测

        Args:
            data: 历史数据，包含 date, open, high, low, close, volume
            strategy: 策略实例
            symbol: 股票代码

        Returns:
            BacktestResult: 回测结果
        """
        self.reset()

        # 生成信号
        df = strategy.generate_signals(data)

        # 特殊处理金字塔策略
        if isinstance(strategy, PyramidStrategy):
            return self._run_pyramid_backtest(df, strategy, symbol)

        # 遍历数据执行交易
        position = 0
        cost_price = 0

        for i, row in df.iterrows():
            trade_signal = row.get('trade_signal', 0)
            close_price = row['close']
            date = row['date'] if 'date' in row else str(i)

            action = "持有"
            direction = ""
            shares = 0
            amount = 0

            if trade_signal == 1 and position == 0:
                # 买入信号，全仓买入
                shares = int(self.cash / close_price)
                if shares > 0:
                    commission = shares * close_price * self.commission_rate
                    cost = shares * close_price + commission
                    self.cash -= cost
                    position = shares
                    cost_price = close_price
                    action = "买入"
                    direction = "buy"
                    amount = cost

            elif trade_signal == -1 and position > 0:
                # 卖出信号，清仓
                shares = position
                commission = shares * close_price * self.commission_rate
                revenue = shares * close_price - commission
                self.cash += revenue
                action = "卖出"
                direction = "sell"
                amount = revenue
                position = 0
                cost_price = 0

            # 记录每日状态
            position_value = position * close_price
            total_value = self.cash + position_value
            profit_rate = (close_price - cost_price) / cost_price if cost_price > 0 and position > 0 else 0

            trade = TradeRecord(
                date=str(date),
                period=i,
                price=close_price,
                action=action,
                direction=direction,
                shares=shares,
                amount=amount,
                cash=self.cash,
                position_value=position_value,
                total_value=total_value,
                profit_rate=profit_rate,
                signal_reason=f"signal={trade_signal}"
            )
            self.trades.append(trade)

            self.daily_values.append({
                'date': str(date),
                'value': total_value,
                'cash': self.cash,
                'position_value': position_value
            })

        # 计算最终结果
        final_value = self.cash + position * df['close'].iloc[-1]
        return self._calculate_result(strategy, symbol, df, final_value)

    def _run_pyramid_backtest(
        self,
        df: pd.DataFrame,
        strategy: PyramidStrategy,
        symbol: str
    ) -> BacktestResult:
        """运行金字塔策略回测"""
        params = strategy.params

        # 初始买入
        initial_position_value = self.initial_capital * params.get('initial_position', 0.6)
        first_price = df['close'].iloc[0]
        shares = int(initial_position_value / first_price)
        self.position = shares
        self.cost_price = first_price
        self.cash = self.initial_capital - shares * first_price

        # 遍历价格
        for i, row in df.iterrows():
            price = row['close']
            date = row['date'] if 'date' in row else str(i)

            action = "持有"
            direction = ""
            shares_trade = 0
            amount = 0

            profit_rate = (price - self.cost_price) / self.cost_price if self.position > 0 else 0

            # 检查止盈
            for j, (level, ratio) in enumerate(zip(
                params['stop_profit_levels'],
                params['stop_profit_ratios']
            )):
                if profit_rate >= level and not self.stop_profit_triggered[j]:
                    sell_shares = int(self.position * ratio)
                    if sell_shares > 0:
                        self.cash += sell_shares * price
                        self.position -= sell_shares
                        action = f"止盈卖出{ratio*100:.0f}%"
                        direction = "sell"
                        shares_trade = sell_shares
                        amount = sell_shares * price
                        self.stop_profit_triggered[j] = True
                        break

            # 检查加仓
            if profit_rate < 0 and self.position > 0:
                for threshold, add_ratio in sorted(params['add_position_levels'].items(), reverse=True):
                    if profit_rate <= threshold and self.added_ratio < params['max_add_ratio']:
                        position_value = self.position * self.cost_price
                        add_amount = position_value * add_ratio

                        if add_amount <= self.cash and self.added_ratio + add_ratio <= params['max_add_ratio']:
                            add_shares = int(add_amount / price)
                            if add_shares > 0:
                                total_cost = self.position * self.cost_price + add_shares * price
                                self.position += add_shares
                                self.cost_price = total_cost / self.position
                                self.cash -= add_shares * price
                                self.added_ratio += add_ratio
                                action = f"加仓{add_ratio*100:.0f}%"
                                direction = "buy"
                                shares_trade = add_shares
                                amount = add_shares * price
                                break

            # 记录
            position_value = self.position * price
            total_value = self.cash + position_value

            trade = TradeRecord(
                date=str(date),
                period=i,
                price=price,
                action=action,
                direction=direction,
                shares=shares_trade,
                amount=amount,
                cash=self.cash,
                position_value=position_value,
                total_value=total_value,
                profit_rate=profit_rate
            )
            self.trades.append(trade)

            self.daily_values.append({
                'date': str(date),
                'value': total_value,
                'cash': self.cash,
                'position_value': position_value
            })

        final_value = self.cash + self.position * df['close'].iloc[-1]
        return self._calculate_result(strategy, symbol, df, final_value)

    def _calculate_result(
        self,
        strategy: BaseStrategy,
        symbol: str,
        df: pd.DataFrame,
        final_value: float
    ) -> BacktestResult:
        """计算回测结果"""
        total_return = (final_value - self.initial_capital) / self.initial_capital

        # 计算年化收益
        days = len(df)
        annual_return = (1 + total_return) ** (252 / days) - 1 if days > 0 else 0

        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown()

        # 计算夏普比率
        sharpe_ratio = self._calculate_sharpe_ratio()

        # 计算胜率
        win_rate, win_count, lose_count, profit_loss_ratio = self._calculate_trade_stats()

        # 生成总结
        summary = self._generate_summary(strategy.name, total_return, max_drawdown, win_rate)

        return BacktestResult(
            strategy_name=strategy.name,
            strategy_type=StrategyType.DOUBLE_MA,  # 默认值，实际使用时需要传入
            symbol=symbol,
            start_date=str(df['date'].iloc[0]) if 'date' in df else "",
            end_date=str(df['date'].iloc[-1]) if 'date' in df else "",
            initial_capital=self.initial_capital,
            final_value=final_value,
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            profit_loss_ratio=profit_loss_ratio,
            trade_count=len([t for t in self.trades if t.action != "持有"]),
            total_trades=len([t for t in self.trades if t.action != "持有"]),
            win_trades=win_count,
            lose_trades=lose_count,
            records=self.trades,
            daily_values=self.daily_values,
            summary=summary
        )

    def _calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        if not self.daily_values:
            return 0

        peak = self.daily_values[0]['value']
        max_dd = 0

        for dv in self.daily_values:
            if dv['value'] > peak:
                peak = dv['value']
            dd = (peak - dv['value']) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

        return max_dd

    def _calculate_sharpe_ratio(self) -> float:
        """计算夏普比率"""
        if len(self.daily_values) < 2:
            return 0

        values = [dv['value'] for dv in self.daily_values]
        returns = [(values[i] - values[i-1]) / values[i-1] for i in range(1, len(values))]

        if not returns:
            return 0

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0

        # 年化夏普比率
        return (mean_return / std_return) * np.sqrt(252)

    def _calculate_trade_stats(self) -> Tuple[float, int, int, float]:
        """计算交易统计"""
        buy_trades = [t for t in self.trades if t.direction == "buy"]
        sell_trades = [t for t in self.trades if t.direction == "sell"]

        if not sell_trades:
            return 0, 0, 0, 0

        win_count = sum(1 for t in sell_trades if "止盈" in t.action or t.profit_rate > 0)
        lose_count = len(sell_trades) - win_count

        win_rate = win_count / len(sell_trades) if sell_trades else 0

        # 计算盈亏比
        win_amounts = [t.amount for t in sell_trades if "止盈" in t.action or t.profit_rate > 0]
        lose_amounts = [t.amount for t in sell_trades if "止盈" not in t.action and t.profit_rate <= 0]

        avg_win = np.mean(win_amounts) if win_amounts else 0
        avg_lose = np.mean(lose_amounts) if lose_amounts else 0

        profit_loss_ratio = avg_win / avg_lose if avg_lose > 0 else 0

        return win_rate, win_count, lose_count, profit_loss_ratio

    def _generate_summary(self, strategy_name: str, total_return: float, max_drawdown: float, win_rate: float) -> str:
        """生成总结"""
        lines = [
            f"策略：{strategy_name}",
            f"总收益率：{total_return*100:+.2f}%",
            f"最大回撤：{max_drawdown*100:.2f}%",
            f"胜率：{win_rate*100:.1f}%",
        ]

        if total_return > 0.10:
            lines.append("结论：策略表现优秀，建议采用")
        elif total_return > 0:
            lines.append("结论：策略表现一般，可优化后使用")
        else:
            lines.append("结论：策略表现不佳，需要调整参数")

        return "\n".join(lines)


def run_multi_strategy_backtest(
    data: pd.DataFrame,
    strategy_types: List[StrategyType],
    strategy_params: Dict[str, Dict] = None,
    initial_capital: float = 100000,
    symbol: str = ""
) -> Dict[str, BacktestResult]:
    """
    运行多策略回测对比

    Args:
        data: 历史数据
        strategy_types: 策略类型列表
        strategy_params: 各策略参数
        initial_capital: 初始资金
        symbol: 股票代码

    Returns:
        Dict[str, BacktestResult]: 各策略的回测结果
    """
    results = {}
    strategy_params = strategy_params or {}

    for st in strategy_types:
        params = strategy_params.get(st.value, {})
        strategy = create_strategy(st, params)
        engine = BacktestEngine(initial_capital=initial_capital)
        result = engine.run_backtest(data, strategy, symbol)
        result.strategy_type = st
        results[st.value] = result

    return results


def get_available_strategies() -> List[Dict]:
    """获取所有可用策略列表"""
    strategies = []
    for st in StrategyType:
        strategy_class = STRATEGY_REGISTRY[st]
        instance = strategy_class()
        strategies.append({
            'value': st.value,
            'name': instance.name,
            'default_params': instance.get_default_params()
        })
    return strategies