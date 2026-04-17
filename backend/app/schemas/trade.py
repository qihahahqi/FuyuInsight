#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易记录相关 Schema
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class TradeCreateSchema(BaseModel):
    """创建交易记录 Schema"""
    symbol: str = Field(..., max_length=20, description="标的代码")
    trade_type: str = Field(..., description="交易类型: buy/sell")
    quantity: int = Field(..., gt=0, description="交易数量")
    price: float = Field(..., gt=0, description="交易价格")
    trade_date: str = Field(..., description="交易日期")
    account_id: Optional[int] = Field(None, description="账户ID")
    position_id: Optional[int] = Field(None, description="关联持仓ID")
    reason: Optional[str] = Field(None, max_length=100, description="交易理由")
    signal_type: Optional[str] = Field(None, max_length=20, description="信号类型")
    notes: Optional[str] = Field(None, description="备注")

    @field_validator('trade_type')
    @classmethod
    def validate_trade_type(cls, v):
        if v not in ['buy', 'sell']:
            raise ValueError('交易类型必须是 buy 或 sell')
        return v


class TradeUpdateSchema(BaseModel):
    """更新交易记录 Schema"""
    quantity: Optional[int] = Field(None, gt=0, description="交易数量")
    price: Optional[float] = Field(None, gt=0, description="交易价格")
    trade_date: Optional[str] = Field(None, description="交易日期")
    reason: Optional[str] = Field(None, max_length=100, description="交易理由")
    notes: Optional[str] = Field(None, description="备注")