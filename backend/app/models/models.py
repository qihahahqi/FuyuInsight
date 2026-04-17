#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模型定义
"""

from datetime import datetime, date
from .. import db
import json


class Account(db.Model):
    """投资账户表"""
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='用户ID')
    name = db.Column(db.String(50), nullable=False, comment='账户名称')
    account_type = db.Column(db.String(50), default='personal', comment='账户类型')
    broker = db.Column(db.String(50), comment='券商/平台')
    description = db.Column(db.Text, comment='描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'account_type': self.account_type,
            'broker': self.broker,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Position(db.Model):
    """持仓表"""
    __tablename__ = 'positions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='用户ID')
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), comment='账户ID')
    symbol = db.Column(db.String(20), nullable=False, comment='标的代码')
    name = db.Column(db.String(50), nullable=False, comment='标的名称')
    asset_type = db.Column(db.String(20), nullable=False, comment='资产类型')
    product_category = db.Column(db.String(20), default='market', comment='产品大类: market/fixed_income/manual')
    quantity = db.Column(db.Integer, nullable=False, default=0, comment='持仓数量')
    cost_price = db.Column(db.Numeric(10, 4), nullable=False, default=0, comment='成本价')
    current_price = db.Column(db.Numeric(10, 4), comment='当前价格')
    total_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0, comment='总成本')
    market_value = db.Column(db.Numeric(12, 2), comment='当前市值')
    profit_rate = db.Column(db.Numeric(8, 4), comment='收益率')
    product_params = db.Column(db.JSON, comment='产品特性参数')
    expected_return = db.Column(db.Numeric(8, 4), comment='预期收益率(年化)')
    actual_return = db.Column(db.Numeric(8, 4), comment='实际收益率')
    mature_date = db.Column(db.Date, comment='到期日')
    risk_level = db.Column(db.String(10), comment='风险等级: R1/R2/R3/R4/R5')
    stop_profit_triggered = db.Column(db.Text, comment='止盈触发状态')
    add_position_ratio = db.Column(db.Numeric(5, 4), default=0, comment='已加仓比例')
    category = db.Column(db.String(20), comment='分类')
    notes = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    account = db.relationship('Account', backref=db.backref('positions', lazy='dynamic'))

    @property
    def stop_profit_status(self):
        """解析止盈状态"""
        if self.stop_profit_triggered:
            try:
                return json.loads(self.stop_profit_triggered)
            except:
                return [False, False, False]
        return [False, False, False]

    @stop_profit_status.setter
    def stop_profit_status(self, value):
        self.stop_profit_triggered = json.dumps(value)

    def calculate_fixed_income_profit(self):
        """计算固定收益产品的收益"""
        if self.product_category != 'fixed_income':
            return None

        params = self.product_params or {}
        interest_rate = float(params.get('interest_rate', 0)) / 100
        start_date = params.get('start_date')

        if not start_date:
            return None

        try:
            from datetime import datetime as dt
            start = dt.strptime(start_date, '%Y-%m-%d').date()
            today = date.today()
            days = (today - start).days

            principal = float(self.total_cost) if self.total_cost else 0
            interest_type = params.get('interest_type', 'simple')

            if interest_type == 'compound':
                profit = principal * ((1 + interest_rate / 365) ** days - 1)
            else:
                profit = principal * interest_rate * days / 365

            return {
                'profit_amount': round(profit, 2),
                'profit_rate': round(profit / principal, 4) if principal > 0 else 0,
                'annualized_return': interest_rate,
                'holding_days': days,
                'market_value': round(principal + profit, 2)
            }
        except:
            return None

    def to_dict(self):
        """转换为字典"""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'account_id': self.account_id,
            'symbol': self.symbol,
            'name': self.name,
            'asset_type': self.asset_type,
            'product_category': self.product_category,
            'quantity': self.quantity,
            'cost_price': float(self.cost_price) if self.cost_price else 0,
            'current_price': float(self.current_price) if self.current_price else None,
            'total_cost': float(self.total_cost) if self.total_cost else 0,
            'market_value': float(self.market_value) if self.market_value else None,
            'profit_rate': float(self.profit_rate) if self.profit_rate else None,
            'product_params': self.product_params,
            'expected_return': float(self.expected_return) if self.expected_return else None,
            'actual_return': float(self.actual_return) if self.actual_return else None,
            'mature_date': self.mature_date.isoformat() if self.mature_date else None,
            'risk_level': self.risk_level,
            'stop_profit_triggered': self.stop_profit_status,
            'add_position_ratio': float(self.add_position_ratio) if self.add_position_ratio else 0,
            'category': self.category,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        return result


class Trade(db.Model):
    """交易记录表"""
    __tablename__ = 'trades'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='用户ID')
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), comment='账户ID')
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id'), comment='关联持仓ID')
    symbol = db.Column(db.String(20), nullable=False, comment='标的代码')
    trade_type = db.Column(db.String(10), nullable=False, comment='交易类型')
    quantity = db.Column(db.Integer, nullable=False, comment='交易数量')
    price = db.Column(db.Numeric(10, 4), nullable=False, comment='交易价格')
    amount = db.Column(db.Numeric(12, 2), nullable=False, comment='交易金额')
    trade_date = db.Column(db.Date, nullable=False, comment='交易日期')
    reason = db.Column(db.String(100), comment='交易理由')
    signal_type = db.Column(db.String(20), comment='信号类型')
    notes = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    account = db.relationship('Account', backref=db.backref('trades', lazy='dynamic'))
    position = db.relationship('Position', backref=db.backref('trades', lazy='dynamic'))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_id': self.account_id,
            'position_id': self.position_id,
            'symbol': self.symbol,
            'trade_type': self.trade_type,
            'quantity': self.quantity,
            'price': float(self.price) if self.price else 0,
            'amount': float(self.amount) if self.amount else 0,
            'trade_date': self.trade_date.isoformat() if self.trade_date else None,
            'reason': self.reason,
            'signal_type': self.signal_type,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Valuation(db.Model):
    """估值数据表"""
    __tablename__ = 'valuations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='用户ID')
    symbol = db.Column(db.String(20), nullable=False, comment='标的代码')
    index_name = db.Column(db.String(50), nullable=False, comment='指数名称')
    pe = db.Column(db.Numeric(10, 2), comment='市盈率')
    pb = db.Column(db.Numeric(10, 4), comment='市净率')
    pe_percentile = db.Column(db.Numeric(5, 2), comment='PE历史百分位')
    pb_percentile = db.Column(db.Numeric(5, 2), comment='PB历史百分位')
    rsi = db.Column(db.Numeric(5, 2), comment='RSI指标')
    roe = db.Column(db.Numeric(5, 2), comment='ROE')
    dividend_yield = db.Column(db.Numeric(5, 2), comment='股息率')
    level = db.Column(db.String(20), comment='估值等级')
    score = db.Column(db.Numeric(5, 2), comment='综合评分')
    suggestion = db.Column(db.String(100), comment='操作建议')
    record_date = db.Column(db.Date, nullable=False, comment='记录日期')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'index_name': self.index_name,
            'pe': float(self.pe) if self.pe else None,
            'pb': float(self.pb) if self.pb else None,
            'pe_percentile': float(self.pe_percentile) if self.pe_percentile else None,
            'pb_percentile': float(self.pb_percentile) if self.pb_percentile else None,
            'rsi': float(self.rsi) if self.rsi else None,
            'roe': float(self.roe) if self.roe else None,
            'dividend_yield': float(self.dividend_yield) if self.dividend_yield else None,
            'level': self.level,
            'score': float(self.score) if self.score else None,
            'suggestion': self.suggestion,
            'record_date': self.record_date.isoformat() if self.record_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CashPool(db.Model):
    """现金池表"""
    __tablename__ = 'cash_pool'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='用户ID')
    amount = db.Column(db.Numeric(12, 2), nullable=False, comment='金额')
    balance = db.Column(db.Numeric(12, 2), nullable=False, comment='余额')
    event = db.Column(db.String(100), nullable=False, comment='事件描述')
    event_date = db.Column(db.Date, nullable=False, comment='事件日期')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': float(self.amount) if self.amount else 0,
            'balance': float(self.balance) if self.balance else 0,
            'event': self.event,
            'event_date': self.event_date.isoformat() if self.event_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Config(db.Model):
    """系统配置表"""
    __tablename__ = 'configs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='用户ID (NULL表示系统配置)')
    key = db.Column(db.String(50), nullable=False, comment='配置键')
    value = db.Column(db.Text, nullable=False, comment='配置值')
    description = db.Column(db.String(200), comment='配置说明')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PortfolioSnapshot(db.Model):
    """投资组合快照表"""
    __tablename__ = 'portfolio_snapshots'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='用户ID')
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), comment='账户ID')
    snapshot_date = db.Column(db.Date, nullable=False, comment='快照日期')
    total_cost = db.Column(db.Numeric(12, 2), nullable=False, comment='总成本')
    market_value = db.Column(db.Numeric(12, 2), nullable=False, comment='市值')
    profit_rate = db.Column(db.Numeric(8, 4), comment='收益率')
    position_count = db.Column(db.Integer, default=0, comment='持仓数')
    notes = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    account = db.relationship('Account', backref=db.backref('snapshots', lazy='dynamic'))

    # 唯一约束：同一账户同一日期只能有一条快照
    __table_args__ = (
        db.UniqueConstraint('account_id', 'snapshot_date', name='uix_account_snapshot_date'),
        db.Index('idx_snapshot_account_date', 'account_id', 'snapshot_date'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_id': self.account_id,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None,
            'total_cost': float(self.total_cost) if self.total_cost else 0,
            'market_value': float(self.market_value) if self.market_value else 0,
            'profit_rate': float(self.profit_rate) if self.profit_rate else None,
            'position_count': self.position_count,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PriceHistory(db.Model):
    """历史价格数据表（股票/基金通用）"""
    __tablename__ = 'price_histories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='用户ID')
    symbol = db.Column(db.String(20), nullable=False, comment='标的代码')
    name = db.Column(db.String(50), comment='标的名称')
    asset_type = db.Column(db.String(20), comment='资产类型: stock/fund/etf')
    trade_date = db.Column(db.Date, nullable=False, comment='交易日期')

    # 股票数据字段
    open_price = db.Column(db.Numeric(10, 4), comment='开盘价')
    high_price = db.Column(db.Numeric(10, 4), comment='最高价')
    low_price = db.Column(db.Numeric(10, 4), comment='最低价')
    close_price = db.Column(db.Numeric(10, 4), comment='收盘价/单位净值')
    volume = db.Column(db.BigInteger, comment='成交量')
    turnover = db.Column(db.Numeric(16, 2), comment='成交额')
    change_pct = db.Column(db.Numeric(8, 4), comment='涨跌幅(%)')
    amplitude = db.Column(db.Numeric(8, 4), comment='振幅(%)')
    turnover_rate = db.Column(db.Numeric(8, 4), comment='换手率(%)')

    # 基金特有字段
    acc_nav = db.Column(db.Numeric(10, 4), comment='累计净值(基金专用)')

    # 数据来源
    data_source = db.Column(db.String(20), comment='数据来源: akshare/baostock/eastmoney/tushare')

    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    # 唯一约束：同一用户、同一标的、同一日期只能有一条记录
    __table_args__ = (
        db.UniqueConstraint('user_id', 'symbol', 'trade_date', name='uix_user_symbol_date'),
        db.Index('idx_price_history_user_symbol', 'user_id', 'symbol'),
        db.Index('idx_price_history_date', 'trade_date'),
    )

    user = db.relationship('User', backref=db.backref('price_histories', lazy='dynamic'))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'name': self.name,
            'asset_type': self.asset_type,
            'trade_date': self.trade_date.isoformat() if self.trade_date else None,
            'open': float(self.open_price) if self.open_price else None,
            'high': float(self.high_price) if self.high_price else None,
            'low': float(self.low_price) if self.low_price else None,
            'close': float(self.close_price) if self.close_price else None,
            'volume': float(self.volume) if self.volume else None,
            'turnover': float(self.turnover) if self.turnover else None,
            'change_pct': float(self.change_pct) if self.change_pct else None,
            'amplitude': float(self.amplitude) if self.amplitude else None,
            'turnover_rate': float(self.turnover_rate) if self.turnover_rate else None,
            'acc_nav': float(self.acc_nav) if self.acc_nav else None,
            'data_source': self.data_source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AIAnalysisHistory(db.Model):
    """AI分析历史记录表"""
    __tablename__ = 'ai_analysis_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='用户ID')
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id'), nullable=True, comment='持仓ID（单标的分析时）')
    analysis_type = db.Column(db.String(20), comment='分析类型: single/portfolio')
    symbol = db.Column(db.String(20), nullable=True, comment='标的代码（单标的分析时）')
    dimensions = db.Column(db.Text, comment='分析维度JSON')
    analysis_content = db.Column(db.Text, comment='分析结果JSON')
    overall_score = db.Column(db.Integer, nullable=True, comment='综合评分')
    model_provider = db.Column(db.String(50), comment='模型提供商')
    model_name = db.Column(db.String(100), comment='模型名称')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    user = db.relationship('User', backref=db.backref('ai_analyses', lazy='dynamic'))
    position = db.relationship('Position', backref=db.backref('ai_analyses', lazy='dynamic'))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'position_id': self.position_id,
            'analysis_type': self.analysis_type,
            'symbol': self.symbol,
            'dimensions': self.dimensions,
            'analysis_content': self.analysis_content,
            'overall_score': self.overall_score,
            'model_provider': self.model_provider,
            'model_name': self.model_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class IncomeRecord(db.Model):
    """收益记录表 - 用于手动录入型产品和固定收益产品的收益记录"""
    __tablename__ = 'income_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id'), comment='关联持仓ID')
    record_date = db.Column(db.Date, nullable=False, comment='收益日期')
    income_amount = db.Column(db.Numeric(12, 2), nullable=False, comment='收益金额')
    income_type = db.Column(db.String(20), comment='收益类型: interest/dividend/maturity/other')
    note = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    position = db.relationship('Position', backref=db.backref('income_records', lazy='dynamic'))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'position_id': self.position_id,
            'record_date': self.record_date.isoformat() if self.record_date else None,
            'income_amount': float(self.income_amount) if self.income_amount else 0,
            'income_type': self.income_type,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AIAnalysisTask(db.Model):
    """AI 分析异步任务表"""
    __tablename__ = 'ai_analysis_tasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    analysis_type = db.Column(db.String(20), comment='分析类型: single/portfolio')
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id'), comment='持仓ID（单标的分析时）')
    symbol = db.Column(db.String(20), comment='标的代码（单标的分析时）')
    dimensions = db.Column(db.Text, comment='分析维度JSON列表')
    status = db.Column(db.String(20), default='pending', comment='任务状态: pending/running/completed/failed/cancelled')
    progress = db.Column(db.Integer, default=0, comment='已完成维度数')
    total_dimensions = db.Column(db.Integer, default=0, comment='总维度数')
    current_dimension = db.Column(db.String(50), comment='当前正在分析的维度')
    overall_score = db.Column(db.Integer, comment='综合评分')
    model_provider = db.Column(db.String(50), comment='模型提供商')
    model_name = db.Column(db.String(100), comment='模型名称')
    error_message = db.Column(db.Text, comment='错误信息')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')

    user = db.relationship('User', backref=db.backref('ai_tasks', lazy='dynamic'))
    position = db.relationship('Position', backref=db.backref('ai_tasks', lazy='dynamic'))
    dimension_results = db.relationship('AIAnalysisDimension', backref='task', lazy='dynamic',
                                        cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('idx_ai_task_user_status', 'user_id', 'status'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'analysis_type': self.analysis_type,
            'position_id': self.position_id,
            'symbol': self.symbol,
            'dimensions': json.loads(self.dimensions) if self.dimensions else [],
            'status': self.status,
            'progress': self.progress,
            'total_dimensions': self.total_dimensions,
            'current_dimension': self.current_dimension,
            'overall_score': self.overall_score,
            'model_provider': self.model_provider,
            'model_name': self.model_name,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

    def get_progress_percentage(self):
        """获取进度百分比"""
        if self.total_dimensions == 0:
            return 0
        return int((self.progress / self.total_dimensions) * 100)


class AIAnalysisDimension(db.Model):
    """AI 分析维度结果表（增量保存）"""
    __tablename__ = 'ai_analysis_dimensions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('ai_analysis_tasks.id'), nullable=False, comment='任务ID')
    dimension = db.Column(db.String(50), nullable=False, comment='维度名称')
    status = db.Column(db.String(20), default='pending', comment='状态: pending/completed/failed')
    score = db.Column(db.Integer, comment='评分')
    analysis = db.Column(db.Text, comment='分析内容')
    error_message = db.Column(db.Text, comment='错误信息')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        db.UniqueConstraint('task_id', 'dimension', name='uix_task_dimension'),
        db.Index('idx_ai_dimension_task', 'task_id'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'dimension': self.dimension,
            'status': self.status,
            'score': self.score,
            'analysis': self.analysis,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class BacktestHistory(db.Model):
    """回测历史记录表"""
    __tablename__ = 'backtest_histories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    symbol = db.Column(db.String(20), nullable=False, comment='标的代码')
    name = db.Column(db.String(50), comment='标的名称')
    start_date = db.Column(db.Date, nullable=False, comment='回测开始日期')
    end_date = db.Column(db.Date, nullable=False, comment='回测结束日期')
    initial_capital = db.Column(db.Numeric(12, 2), nullable=False, comment='初始资金')
    strategy_type = db.Column(db.String(50), comment='策略类型: single/compare')
    results = db.Column(db.Text, comment='回测结果JSON')
    best_strategy = db.Column(db.String(50), comment='最佳策略名称')
    best_return = db.Column(db.Numeric(8, 4), comment='最佳收益率')
    notes = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    user = db.relationship('User', backref=db.backref('backtest_histories', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'symbol', 'start_date', 'end_date', name='uix_backtest_user_symbol_range'),
        db.Index('idx_backtest_user', 'user_id'),
        db.Index('idx_backtest_symbol', 'symbol'),
        db.Index('idx_backtest_date', 'start_date', 'end_date'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'name': self.name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'initial_capital': float(self.initial_capital) if self.initial_capital else 0,
            'strategy_type': self.strategy_type,
            'best_strategy': self.best_strategy,
            'best_return': float(self.best_return) if self.best_return else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def get_results(self):
        """解析回测结果"""
        if self.results:
            try:
                return json.loads(self.results)
            except:
                return None
        return None