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
    quantity = db.Column(db.Integer, nullable=False, default=0, comment='持仓数量')
    cost_price = db.Column(db.Numeric(10, 4), nullable=False, default=0, comment='成本价')
    current_price = db.Column(db.Numeric(10, 4), comment='当前价格')
    total_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0, comment='总成本')
    market_value = db.Column(db.Numeric(12, 2), comment='当前市值')
    profit_rate = db.Column(db.Numeric(8, 4), comment='收益率')
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

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_id': self.account_id,
            'symbol': self.symbol,
            'name': self.name,
            'asset_type': self.asset_type,
            'quantity': self.quantity,
            'cost_price': float(self.cost_price) if self.cost_price else 0,
            'current_price': float(self.current_price) if self.current_price else None,
            'total_cost': float(self.total_cost) if self.total_cost else 0,
            'market_value': float(self.market_value) if self.market_value else None,
            'profit_rate': float(self.profit_rate) if self.profit_rate else None,
            'stop_profit_triggered': self.stop_profit_status,
            'add_position_ratio': float(self.add_position_ratio) if self.add_position_ratio else 0,
            'category': self.category,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


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