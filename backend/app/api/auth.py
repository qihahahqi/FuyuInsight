#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证 API
"""

from flask import Blueprint, request, jsonify, current_app, g
from ..services.auth_service import AuthService
from ..utils.decorators import login_required, get_current_user
from ..models.user import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/auth/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()

    if not data:
        return jsonify({
            'success': False,
            'message': '请求数据无效'
        }), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    # 验证必填字段
    if not username or not email or not password:
        return jsonify({
            'success': False,
            'message': '用户名、邮箱和密码不能为空'
        }), 400

    # 验证用户名长度
    if len(username) < 3 or len(username) > 50:
        return jsonify({
            'success': False,
            'message': '用户名长度需在3-50个字符之间'
        }), 400

    # 验证密码长度
    if len(password) < 6:
        return jsonify({
            'success': False,
            'message': '密码长度至少6个字符'
        }), 400

    # 注册用户
    result = AuthService.register(username, email, password)

    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400


@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()

    if not data:
        return jsonify({
            'success': False,
            'message': '请求数据无效'
        }), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({
            'success': False,
            'message': '用户名和密码不能为空'
        }), 400

    # 创建认证服务
    secret_key = current_app.config.get('JWT_SECRET_KEY', 'dev-secret-key')
    expires_hours = current_app.config.get('JWT_EXPIRES_HOURS', 24)
    auth_service = AuthService(secret_key=secret_key, expires_hours=expires_hours)

    # 执行登录
    result = AuthService.login(username, password, auth_service)

    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 401


@auth_bp.route('/auth/me', methods=['GET'])
@login_required
def get_current_user_info():
    """获取当前用户信息"""
    user = get_current_user()
    return jsonify({
        'success': True,
        'user': user.to_dict()
    })


@auth_bp.route('/auth/password', methods=['PUT'])
@login_required
def change_password():
    """修改密码"""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({
            'success': False,
            'message': '请求数据无效'
        }), 400

    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return jsonify({
            'success': False,
            'message': '原密码和新密码不能为空'
        }), 400

    if len(new_password) < 6:
        return jsonify({
            'success': False,
            'message': '新密码长度至少6个字符'
        }), 400

    result = AuthService.change_password(user.id, old_password, new_password)

    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@auth_bp.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    """用户登出（客户端清除 Token 即可）"""
    return jsonify({
        'success': True,
        'message': '登出成功'
    })