#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
请求验证装饰器
"""

from functools import wraps
from flask import request
from pydantic import ValidationError
from ..utils.response import error_response


def validate_body(schema_class):
    """
    验证请求体的装饰器

    用法:
        @validate_body(PositionCreateSchema)
        def create_position():
            data = request.validated_data
            # ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                json_data = request.get_json()
                if json_data is None:
                    return error_response("请求体不是有效的JSON", 400)

                validated = schema_class(**json_data)
                request.validated_data = validated.model_dump()
                return f(*args, **kwargs)

            except ValidationError as e:
                errors = []
                for error in e.errors():
                    field = '.'.join(str(loc) for loc in error['loc'])
                    message = error['msg']
                    errors.append(f"{field}: {message}")
                return error_response(f"参数验证失败: {'; '.join(errors)}", 400)

            except Exception as e:
                return error_response(f"请求处理错误: {str(e)}", 400)

        return wrapper
    return decorator


def validate_query(schema_class):
    """
    验证查询参数的装饰器

    用法:
        @validate_query(PaginationSchema)
        def list_items():
            data = request.validated_data
            page = data['page']
            # ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                query_params = dict(request.args)
                # 转换类型
                for key, value in query_params.items():
                    if value.isdigit():
                        query_params[key] = int(value)
                    elif value.replace('.', '').isdigit():
                        query_params[key] = float(value)
                    elif value.lower() in ['true', 'false']:
                        query_params[key] = value.lower() == 'true'

                validated = schema_class(**query_params)
                request.validated_data = validated.model_dump()
                return f(*args, **kwargs)

            except ValidationError as e:
                errors = []
                for error in e.errors():
                    field = '.'.join(str(loc) for loc in error['loc'])
                    message = error['msg']
                    errors.append(f"{field}: {message}")
                return error_response(f"参数验证失败: {'; '.join(errors)}", 400)

            except Exception as e:
                return error_response(f"请求处理错误: {str(e)}", 400)

        return wrapper
    return decorator


# 常用查询参数 Schema
from pydantic import BaseModel, Field
from typing import Optional


class PaginationSchema(BaseModel):
    """分页参数 Schema"""
    page: int = Field(1, ge=1, description="页码")
    per_page: int = Field(20, ge=1, le=100, description="每页数量")


class DateRangeSchema(BaseModel):
    """日期范围参数 Schema"""
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")