#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资组合快照服务
支持动态计算历史收益曲线（基于交易记录和历史价格）
"""

from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from .. import db
from ..models import Position, PortfolioSnapshot, Account, Trade, PriceHistory
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


class SnapshotService:
    """投资组合快照服务"""

    def create_daily_snapshot(self, account_id: int, user_id: int = None) -> Dict:
        """
        创建每日快照（支持并发安全）

        Args:
            account_id: 账户 ID
            user_id: 用户 ID

        Returns:
            Dict: 快照结果
        """
        # 验证账户是否存在
        account = Account.query.filter_by(id=account_id).first()
        if not account:
            logger.warning(f"账户 {account_id} 不存在，跳过创建快照")
            return {
                'success': False,
                'message': f'账户 {account_id} 不存在'
            }

        # 获取账户持仓
        query = Position.query.filter_by(account_id=account_id)
        if user_id:
            query = query.filter_by(user_id=user_id)
        positions = query.all()

        if not positions:
            return {
                'success': False,
                'message': '该账户没有持仓'
            }

        # 计算汇总数据
        total_cost = sum(float(p.total_cost) for p in positions)
        market_value = 0
        for p in positions:
            if p.market_value:
                market_value += float(p.market_value)
            elif p.current_price:
                # 如果有现价但没有市值，计算市值
                market_value += float(p.current_price) * p.quantity
            else:
                # 使用成本作为备用
                market_value += float(p.total_cost)

        profit_rate = (market_value - total_cost) / total_cost if total_cost > 0 else 0

        today = date.today()

        # 使用并发安全的方式创建或更新快照
        try:
            # 先尝试创建新快照
            snapshot = PortfolioSnapshot(
                user_id=user_id,
                account_id=account_id,
                snapshot_date=today,
                total_cost=total_cost,
                market_value=market_value,
                profit_rate=profit_rate,
                position_count=len(positions)
            )
            db.session.add(snapshot)
            db.session.commit()
            logger.info(f"成功创建新快照: account_id={account_id}, date={today}")

        except IntegrityError:
            # 并发冲突：其他请求已创建了快照，回滚后更新现有记录
            db.session.rollback()

            query = PortfolioSnapshot.query.filter_by(
                account_id=account_id,
                snapshot_date=today
            )
            if user_id:
                query = query.filter_by(user_id=user_id)
            existing = query.first()

            if existing:
                existing.total_cost = total_cost
                existing.market_value = market_value
                existing.profit_rate = profit_rate
                existing.position_count = len(positions)
                db.session.commit()
                logger.info(f"更新已存在的快照: account_id={account_id}, date={today}")
            else:
                # 极端情况：回滚后记录不存在，重新尝试创建
                logger.warning(f"快照记录异常消失，重新创建: account_id={account_id}")
                snapshot = PortfolioSnapshot(
                    user_id=user_id,
                    account_id=account_id,
                    snapshot_date=today,
                    total_cost=total_cost,
                    market_value=market_value,
                    profit_rate=profit_rate,
                    position_count=len(positions)
                )
                db.session.add(snapshot)
                db.session.commit()

        except Exception as e:
            db.session.rollback()
            logger.error(f"创建快照失败: {str(e)}")
            return {
                'success': False,
                'message': f'创建快照失败: {str(e)}'
            }

        return {
            'success': True,
            'message': '快照创建成功',
            'snapshot': {
                'date': today.isoformat(),
                'total_cost': total_cost,
                'market_value': market_value,
                'profit_rate': profit_rate,
                'position_count': len(positions)
            }
        }

    def get_snapshots(self, account_id: int, days: int = 30, user_id: int = None) -> List[Dict]:
        """
        获取历史快照

        Args:
            account_id: 账户 ID
            days: 天数
            user_id: 用户 ID

        Returns:
            List[Dict]: 快照列表
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        query = PortfolioSnapshot.query.filter(
            PortfolioSnapshot.account_id == account_id,
            PortfolioSnapshot.snapshot_date >= start_date,
            PortfolioSnapshot.snapshot_date <= end_date
        )
        if user_id:
            query = query.filter(PortfolioSnapshot.user_id == user_id)

        snapshots = query.order_by(PortfolioSnapshot.snapshot_date).all()

        return [s.to_dict() for s in snapshots]

    def get_profit_curve_data(self, account_id: int, days: int = 30, user_id: int = None) -> Dict:
        """
        获取收益曲线数据

        Args:
            account_id: 账户 ID
            days: 天数
            user_id: 用户 ID

        Returns:
            Dict: 图表数据
        """
        snapshots = self.get_snapshots(account_id, days, user_id)

        if not snapshots:
            # 如果没有快照，计算当前持仓并返回单点数据
            query = Position.query.filter_by(account_id=account_id)
            if user_id:
                query = query.filter_by(user_id=user_id)
            positions = query.all()
            if positions:
                total_cost = sum(float(p.total_cost) for p in positions)
                market_value = sum(float(p.market_value) for p in positions if p.market_value)
                profit_rate = (market_value - total_cost) / total_cost if total_cost > 0 else 0

                return {
                    'labels': [date.today().isoformat()],
                    'profit_rates': [round(profit_rate * 100, 2)],
                    'market_values': [market_value],
                    'total_costs': [total_cost]
                }
            return {
                'labels': [],
                'profit_rates': [],
                'market_values': [],
                'total_costs': []
            }

        # 提取数据
        labels = [s['snapshot_date'] for s in snapshots]
        profit_rates = [round(s['profit_rate'] * 100, 2) if s['profit_rate'] else 0 for s in snapshots]
        market_values = [s['market_value'] for s in snapshots]
        total_costs = [s['total_cost'] for s in snapshots]

        return {
            'labels': labels,
            'profit_rates': profit_rates,
            'market_values': market_values,
            'total_costs': total_costs
        }

    def get_all_accounts_profit_curve(self, user_id: int, days: int = 30) -> Dict:
        """
        获取用户所有账户汇总的收益曲线数据（动态计算）

        Args:
            user_id: 用户 ID
            days: 天数

        Returns:
            Dict: 图表数据
        """
        # 获取用户所有活跃账户
        accounts = Account.query.filter_by(user_id=user_id, is_active=True).all()

        if not accounts:
            # 没有账户，直接从持仓计算
            positions = Position.query.filter_by(user_id=user_id).filter(Position.quantity > 0).all()
            if positions:
                total_cost = sum(float(p.total_cost) for p in positions)
                market_value = 0
                for p in positions:
                    if p.market_value:
                        market_value += float(p.market_value)
                    elif p.current_price:
                        market_value += float(p.current_price) * p.quantity
                    else:
                        market_value += float(p.total_cost)

                profit_rate = (market_value - total_cost) / total_cost * 100 if total_cost > 0 else 0

                return {
                    'labels': [date.today().isoformat()],
                    'profit_rates': [round(profit_rate, 2)],
                    'market_values': [market_value],
                    'total_costs': [total_cost]
                }
            return {
                'labels': [],
                'profit_rates': [],
                'market_values': [],
                'total_costs': []
            }

        # 使用动态计算方法，合并所有账户的数据
        return self._calculate_all_accounts_curve_dynamically(accounts, user_id, days)

    def _calculate_all_accounts_curve_dynamically(self, accounts: List, user_id: int, days: int) -> Dict:
        """
        动态计算所有账户汇总的收益曲线（结合持仓表和交易记录）

        Args:
            accounts: 账户列表
            user_id: 用户 ID
            days: 天数

        Returns:
            Dict: 图表数据
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # 1. 收集所有账户的持仓
        all_positions = []
        account_ids = [a.id for a in accounts]

        for account_id in account_ids:
            positions = Position.query.filter_by(account_id=account_id, user_id=user_id).all()
            all_positions.extend(positions)

        if not all_positions:
            return {
                'labels': [],
                'profit_rates': [],
                'market_values': [],
                'total_costs': []
            }

        # 2. 收集所有账户的卖出交易记录
        all_sells = []
        for account_id in account_ids:
            sells = Trade.query.filter_by(account_id=account_id, user_id=user_id, trade_type='sell').order_by(Trade.trade_date.desc()).all()
            all_sells.extend(sells)

        # 3. 计算每个标的的原始持仓（反向应用卖出交易）
        holdings = {}
        for pos in all_positions:
            current_qty = pos.quantity
            current_cost = float(pos.total_cost) if pos.total_cost and pos.quantity > 0 else 0
            cost_price = float(pos.cost_price) if pos.cost_price else 0

            symbol_sells = [t for t in all_sells if t.symbol == pos.symbol]
            total_sell_qty = sum(t.quantity for t in symbol_sells)

            original_qty = current_qty + total_sell_qty
            original_cost = original_qty * cost_price if cost_price > 0 else current_cost

            created_date = pos.created_at.date() if pos.created_at else date.today()

            holdings[pos.symbol] = {
                'original_quantity': original_qty,
                'current_quantity': current_qty,
                'total_cost': original_cost,
                'avg_cost': cost_price,
                'created_date': created_date,
                'sells': sorted(symbol_sells, key=lambda t: t.trade_date)
            }

        # 4. 获取历史价格数据
        symbols = set(holdings.keys())
        price_data = self._get_price_data_for_symbols(symbols, user_id, start_date - timedelta(days=30), end_date)

        # 5. 获取有价格数据的交易日列表
        trade_dates = self._get_trade_dates_with_price_data(price_data, start_date, end_date)

        if not trade_dates:
            # 没有历史价格数据，返回当前持仓
            active_positions = [p for p in all_positions if p.quantity > 0]
            if active_positions:
                total_cost = sum(float(p.total_cost) for p in active_positions)
                market_value = sum(float(p.market_value or p.total_cost) for p in active_positions)
                profit_rate = (market_value - total_cost) / total_cost * 100 if total_cost > 0 else 0
                return {
                    'labels': [date.today().isoformat()],
                    'profit_rates': [round(profit_rate, 2)],
                    'market_values': [market_value],
                    'total_costs': [total_cost]
                }
            return {
                'labels': [],
                'profit_rates': [],
                'market_values': [],
                'total_costs': []
            }

        # 6. 遍历每个交易日，计算汇总收益
        labels = []
        profit_rates = []
        market_values = []
        total_costs = []

        for trade_date in trade_dates:
            # 计算当天的持仓状态
            daily_holdings = self._calculate_holdings_on_date(holdings, trade_date)

            # 计算当天市值和成本
            result = self._calculate_daily_portfolio_value(daily_holdings, price_data, trade_date)

            if result['total_cost'] > 0:
                labels.append(trade_date.isoformat())
                total_costs.append(result['total_cost'])
                market_values.append(result['market_value'])
                profit_rate = (result['market_value'] - result['total_cost']) / result['total_cost'] * 100
                profit_rates.append(round(profit_rate, 2))

        return {
            'labels': labels,
            'profit_rates': profit_rates,
            'market_values': market_values,
            'total_costs': total_costs
        }

    def fill_missing_snapshots(self, account_id: int, days: int = 90, user_id: int = None) -> Dict:
        """
        补充缺失的快照数据（仅用于手动触发）

        注意：缺失的日期表示当时还未持有，不应填充假数据。
        此方法主要用于用户手动请求补充特定日期的快照。

        Args:
            account_id: 账户 ID
            days: 天数（仅用于确定检查范围）
            user_id: 用户 ID

        Returns:
            Dict: 填充结果
        """
        # 缺失的日期表示还未持有，不填充假数据
        # 此方法保留但不执行填充，供将来可能的手动补充功能使用
        return {
            'success': True,
            'filled': 0,
            'message': '缺失日期表示未持有期间，不填充数据'
        }

    # ============ 动态计算收益曲线（基于持仓、交易记录和历史价格） ============

    def calculate_profit_curve_dynamically(self, account_id: int, days: int = 30, user_id: int = None) -> Dict:
        """
        动态计算收益曲线（结合持仓表、交易记录和历史价格数据）

        核心算法：
        1. 从 Position 表获取初始持仓（持仓是手动添加或导入的）
        2. 从 Trade 表获取卖出记录，反向推导原始买入数量
        3. 从 PriceHistory 表获取每个标的每天的价格
        4. 动态计算：市值 = Σ(持仓数量 × 当天价格)，收益率 = (市值 - 成本) / 成本

        Args:
            account_id: 账户 ID
            days: 天数
            user_id: 用户 ID

        Returns:
            Dict: 图表数据 {labels, profit_rates, market_values, total_costs}
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # 1. 获取该账户所有持仓（包括数量为0的，因为它们曾经持有）
        query = Position.query.filter_by(account_id=account_id)
        if user_id:
            query = query.filter_by(user_id=user_id)
        positions = query.all()

        if not positions:
            return {
                'labels': [],
                'profit_rates': [],
                'market_values': [],
                'total_costs': []
            }

        # 2. 获取该账户所有卖出交易记录（按日期倒序，用于反向推导）
        trades_query = Trade.query.filter_by(account_id=account_id, trade_type='sell')
        if user_id:
            trades_query = trades_query.filter_by(user_id=user_id)
        sells = trades_query.order_by(Trade.trade_date.desc()).all()

        # 3. 计算每个标的的原始持仓（反向应用卖出交易）
        # holdings = {symbol: {'original_quantity', 'current_quantity', 'total_cost', 'avg_cost', 'created_date'}}
        holdings = {}
        for pos in positions:
            # 当前持仓数量
            current_qty = pos.quantity
            # 当前总成本（如果数量为0，使用历史成本价×原始数量估算）
            current_cost = float(pos.total_cost) if pos.total_cost and pos.quantity > 0 else 0
            cost_price = float(pos.cost_price) if pos.cost_price else 0

            # 找到该标的的所有卖出记录
            symbol_sells = [t for t in sells if t.symbol == pos.symbol]
            total_sell_qty = sum(t.quantity for t in symbol_sells)
            total_sell_amount = sum(float(t.amount) for t in symbol_sells)

            # 原始数量 = 当前数量 + 已卖出数量
            original_qty = current_qty + total_sell_qty

            # 原始成本估算（如果有卖出，需要加回卖出金额）
            # 注意：卖出金额是按当时价格计算的，不是按成本
            # 使用成本价计算原始成本
            original_cost = original_qty * cost_price if cost_price > 0 else current_cost

            # 买入时间取持仓创建时间
            created_date = pos.created_at.date() if pos.created_at else date.today()

            holdings[pos.symbol] = {
                'original_quantity': original_qty,
                'current_quantity': current_qty,
                'total_cost': original_cost,
                'avg_cost': cost_price,
                'created_date': created_date,
                'sells': sorted(symbol_sells, key=lambda t: t.trade_date)  # 按日期升序
            }

        # 4. 获取所有标的的历史价格数据
        symbols = set(holdings.keys())
        price_data = self._get_price_data_for_symbols(symbols, user_id, start_date - timedelta(days=30), end_date)

        # 5. 获取有价格数据的交易日列表
        trade_dates = self._get_trade_dates_with_price_data(price_data, start_date, end_date)

        if not trade_dates:
            # 没有历史价格数据，返回当前持仓数据
            return self._get_current_positions_data(account_id, user_id)

        # 6. 遍历每个交易日，计算收益
        labels = []
        profit_rates = []
        market_values = []
        total_costs = []

        for trade_date in trade_dates:
            # 计算当天的持仓状态（正向应用卖出交易）
            daily_holdings = self._calculate_holdings_on_date(holdings, trade_date)

            # 计算当天市值和成本
            result = self._calculate_daily_portfolio_value(daily_holdings, price_data, trade_date)

            if result['total_cost'] > 0:
                labels.append(trade_date.isoformat())
                total_costs.append(result['total_cost'])
                market_values.append(result['market_value'])
                profit_rate = (result['market_value'] - result['total_cost']) / result['total_cost'] * 100
                profit_rates.append(round(profit_rate, 2))

        return {
            'labels': labels,
            'profit_rates': profit_rates,
            'market_values': market_values,
            'total_costs': total_costs
        }

    def _calculate_holdings_on_date(self, holdings: Dict, target_date: date) -> Dict:
        """
        计算某一天的持仓状态（基于原始持仓，扣除该日期之前已发生的卖出）

        Args:
            holdings: 原始持仓信息 {symbol: {original_quantity, current_quantity, total_cost, avg_cost, sells}}
            target_date: 目标日期

        Returns:
            Dict: 当天的持仓状态 {symbol: {quantity, total_cost, avg_cost}}
        """
        result = {}

        for symbol, holding in holdings.items():
            # 检查该标的是否在目标日期之前已经买入
            if target_date < holding['created_date']:
                continue  # 还没有买入这个标的

            original_qty = holding['original_quantity']
            original_cost = holding['total_cost']
            avg_cost = holding['avg_cost']
            sells = holding['sells']

            # 计算截止目标日期已卖出的数量
            sold_qty = sum(t.quantity for t in sells if t.trade_date <= target_date)

            # 当天数量 = 原始数量 - 已卖出数量
            current_qty = original_qty - sold_qty

            if current_qty <= 0:
                continue  # 已经清仓

            # 当天成本 = 当前数量 × 平均成本（卖出不影响平均成本）
            current_cost = current_qty * avg_cost

            result[symbol] = {
                'quantity': current_qty,
                'total_cost': current_cost,
                'avg_cost': avg_cost
            }

        return result

    def _get_price_data_for_symbols(self, symbols: set, user_id: int, start_date: date, end_date: date) -> Dict:
        """
        获取所有标的的历史价格数据

        Args:
            symbols: 标的代码集合
            user_id: 用户 ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            Dict: {symbol: {date: price}}
        """
        price_data = {}

        for symbol in symbols:
            query = PriceHistory.query.filter_by(user_id=user_id, symbol=symbol).filter(
                PriceHistory.trade_date >= start_date,
                PriceHistory.trade_date <= end_date
            ).order_by(PriceHistory.trade_date)

            records = query.all()

            # 构建 {date: close_price} 字典
            price_data[symbol] = {}
            for record in records:
                if record.close_price:
                    price_data[symbol][record.trade_date] = float(record.close_price)

        return price_data

    def _get_trade_dates_with_price_data(self, price_data: Dict, start_date: date, end_date: date) -> List[date]:
        """
        获取有价格数据的交易日列表（所有标的中至少有一个有价格数据的日期）

        Args:
            price_data: 价格数据字典
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            List[date]: 有数据的日期列表（排序后）
        """
        # 收集所有有价格数据的日期
        all_dates = set()
        for symbol, dates_dict in price_data.items():
            for d in dates_dict.keys():
                if start_date <= d <= end_date:
                    all_dates.add(d)

        # 排序返回
        return sorted(all_dates)

    def _calculate_daily_portfolio_value(self, holdings: Dict, price_data: Dict, trade_date: date) -> Dict:
        """
        计算某一天的持仓市值和成本

        Args:
            holdings: 持仓信息
            price_data: 价格数据
            trade_date: 交易日期

        Returns:
            Dict: {total_cost, market_value}
        """
        total_cost = 0
        market_value = 0

        for symbol, holding in holdings.items():
            if holding['quantity'] <= 0:
                continue

            # 获取当天价格
            price = self._get_price_for_date(price_data, symbol, trade_date)

            if price is None:
                # 没有当天价格，使用平均成本价作为备用（保守估计）
                price = holding['avg_cost']

            quantity = holding['quantity']
            cost = holding['total_cost']

            total_cost += cost
            market_value += quantity * price

        return {
            'total_cost': round(total_cost, 2),
            'market_value': round(market_value, 2)
        }

    def _get_price_for_date(self, price_data: Dict, symbol: str, target_date: date) -> Optional[float]:
        """
        获取某标的在某日期的价格（如果当天没有，使用最近的前一个有数据的日期）

        Args:
            price_data: 价格数据字典 {symbol: {date: price}}
            symbol: 标的代码
            target_date: 目标日期

        Returns:
            Optional[float]: 价格，如果没有则返回 None
        """
        if symbol not in price_data:
            return None

        symbol_data = price_data[symbol]

        # 优先使用当天价格
        if target_date in symbol_data:
            return symbol_data[target_date]

        # 查找最近的前一个有数据的日期
        available_dates = sorted([d for d in symbol_data.keys() if d <= target_date], reverse=True)

        if available_dates:
            return symbol_data[available_dates[0]]

        # 查找最近的后一个有数据的日期（用于起始日期附近可能还没有数据的情况）
        future_dates = sorted([d for d in symbol_data.keys() if d > target_date])

        if future_dates:
            return symbol_data[future_dates[0]]

        return None

    def _get_current_positions_data(self, account_id: int, user_id: int = None) -> Dict:
        """
        获取当前持仓数据（用于没有历史数据时的备用）

        Args:
            account_id: 账户 ID
            user_id: 用户 ID

        Returns:
            Dict: 图表数据
        """
        query = Position.query.filter_by(account_id=account_id).filter(Position.quantity > 0)
        if user_id:
            query = query.filter_by(user_id=user_id)
        positions = query.all()

        if not positions:
            return {
                'labels': [],
                'profit_rates': [],
                'market_values': [],
                'total_costs': []
            }

        total_cost = sum(float(p.total_cost) for p in positions)
        market_value = 0
        for p in positions:
            if p.market_value:
                market_value += float(p.market_value)
            elif p.current_price:
                market_value += float(p.current_price) * p.quantity
            else:
                market_value += float(p.total_cost)

        profit_rate = (market_value - total_cost) / total_cost * 100 if total_cost > 0 else 0

        return {
            'labels': [date.today().isoformat()],
            'profit_rates': [round(profit_rate, 2)],
            'market_values': [market_value],
            'total_costs': [total_cost]
        }