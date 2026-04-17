#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证装饰器
"""

from functools import wraps
from flask import request, jsonify, g
import jwt
from ..models.user import User


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取 Token
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else auth_header

        if not token:
            return jsonify({
                'success': False,
                'message': '未提供认证令牌'
            }), 401

        # 获取 JWT 密钥
        from flask import current_app
        secret_key = current_app.config.get('JWT_SECRET_KEY', 'dev-secret-key')

        try:
            # 验证 Token
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            user_id = payload.get('user_id')

            # 获取用户
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    'success': False,
                    'message': '用户不存在'
                }), 401

            if not user.is_active:
                return jsonify({
                    'success': False,
                    'message': '账户已被禁用'
                }), 401

            # 将用户存储到全局上下文
            g.current_user = user
            request.current_user_id = user.id

        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'message': '认证令牌已过期'
            }), 401
        except jwt.InvalidTokenError as e:
            return jsonify({
                'success': False,
                'message': '无效的认证令牌'
            }), 401

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not g.current_user.is_admin:
            return jsonify({
                'success': False,
                'message': '需要管理员权限'
            }), 403

        return f(*args, **kwargs)

    return decorated_function


def get_current_user():
    """获取当前登录用户"""
    return getattr(g, 'current_user', None)