#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
估值相关 Schema
"""

from pydantic import BaseModel, Field
from typing import Optional


class ValuationCreateSchema(BaseModel):
    """创建估值数据 Schema"""
    symbol: str = Field(..., max_length=20, description="标的代码")
    index_name: str = Field(..., min_length=1, max_length=50, description="指数名称")
    pe: Optional[float] = Field(None, description="市盈率")
    pb: Optional[float] = Field(None, description="市净率")
    pe_percentile: Optional[float] = Field(None, ge=0, le=100, description="PE百分位")
    pb_percentile: Optional[float] = Field(None, ge=0, le=100, description="PB百分位")
    rsi: Optional[float] = Field(None, ge=0, le=100, description="RSI指标")
    roe: Optional[float] = Field(None, description="ROE")
    dividend_yield: Optional[float] = Field(None, description="股息率")
    level: Optional[str] = Field(None, max_length=20, description="估值等级")
    score: Optional[float] = Field(None, description="综合评分")
    suggestion: Optional[str] = Field(None, max_length=100, description="操作建议")
    record_date: str = Field(..., description="记录日期")