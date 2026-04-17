#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
账户相关 Schema
"""

from pydantic import BaseModel, Field
from typing import Optional


class AccountCreateSchema(BaseModel):
    """创建账户 Schema"""
    name: str = Field(..., min_length=1, max_length=50, description="账户名称")
    account_type: Optional[str] = Field(None, max_length=50, description="账户类型")
    broker: Optional[str] = Field(None, max_length=50, description="券商/平台")
    description: Optional[str] = Field(None, description="描述")


class AccountUpdateSchema(BaseModel):
    """更新账户 Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="账户名称")
    account_type: Optional[str] = Field(None, max_length=50, description="账户类型")
    broker: Optional[str] = Field(None, max_length=50, description="券商/平台")
    description: Optional[str] = Field(None, description="描述")
    is_active: Optional[bool] = Field(None, description="是否启用")