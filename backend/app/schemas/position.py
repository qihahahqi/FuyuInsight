#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓相关 Schema
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import date


class PositionCreateSchema(BaseModel):
    """创建持仓 Schema"""
    symbol: str = Field(..., max_length=20, description="标的代码")
    name: str = Field(..., min_length=1, max_length=50, description="标的名称")
    asset_type: str = Field(..., description="资产类型")
    quantity: int = Field(..., gt=0, description="持仓数量")
    cost_price: float = Field(..., gt=0, description="成本价")
    current_price: Optional[float] = Field(None, ge=0, description="当前价格")
    account_id: Optional[int] = Field(None, description="账户ID")
    product_category: Optional[str] = Field(None, description="产品大类")
    product_params: Optional[Dict[str, Any]] = Field(None, description="产品参数")
    expected_return: Optional[float] = Field(None, description="预期收益率")
    mature_date: Optional[str] = Field(None, description="到期日")
    risk_level: Optional[str] = Field(None, description="风险等级")
    category: Optional[str] = Field(None, description="分类")
    notes: Optional[str] = Field(None, description="备注")

    @field_validator('asset_type')
    @classmethod
    def validate_asset_type(cls, v):
        valid_types = [
            'stock', 'etf_index', 'etf_sector', 'fund', 'gold', 'silver',
            'bank_deposit', 'bank_current', 'bank_wealth', 'treasury_bond',
            'corporate_bond', 'money_fund', 'insurance', 'trust', 'other'
        ]
        if v not in valid_types:
            raise ValueError(f'资产类型无效，有效值: {", ".join(valid_types)}')
        return v


class PositionUpdateSchema(BaseModel):
    """更新持仓 Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="标的名称")
    quantity: Optional[int] = Field(None, gt=0, description="持仓数量")
    cost_price: Optional[float] = Field(None, gt=0, description="成本价")
    current_price: Optional[float] = Field(None, ge=0, description="当前价格")
    category: Optional[str] = Field(None, description="分类")
    notes: Optional[str] = Field(None, description="备注")
    product_category: Optional[str] = Field(None, description="产品大类")
    product_params: Optional[Dict[str, Any]] = Field(None, description="产品参数")
    mature_date: Optional[str] = Field(None, description="到期日")
    risk_level: Optional[str] = Field(None, description="风险等级")
    expected_return: Optional[float] = Field(None, description="预期收益率")