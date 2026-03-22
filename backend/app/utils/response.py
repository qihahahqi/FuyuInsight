#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
响应工具类
"""

from datetime import datetime
from flask import jsonify


def success_response(data=None, message="操作成功"):
    """成功响应"""
    return jsonify({
        'success': True,
        'data': data,
        'message': message,
        'timestamp': datetime.now().isoformat()
    })


def error_response(message="操作失败", code=400, data=None):
    """错误响应"""
    return jsonify({
        'success': False,
        'data': data,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }), code


def paginate_response(items, total, page, per_page):
    """分页响应"""
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page if per_page > 0 else 0
    }