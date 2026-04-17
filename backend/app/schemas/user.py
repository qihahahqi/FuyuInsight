#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户相关 Schema
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class UserLoginSchema(BaseModel):
    """用户登录 Schema"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class UserRegisterSchema(BaseModel):
    """用户注册 Schema"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('邮箱格式不正确')
        return v


class UserUpdateSchema(BaseModel):
    """用户更新 Schema"""
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    old_password: Optional[str] = Field(None, min_length=6, max_length=100, description="旧密码")
    new_password: Optional[str] = Field(None, min_length=6, max_length=100, description="新密码")