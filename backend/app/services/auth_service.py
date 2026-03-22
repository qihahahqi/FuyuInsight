#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证服务 - JWT Token 生成与验证
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
from ..models.user import User
from .. import db


class AuthService:
    """认证服务"""

    def __init__(self, secret_key: str = 'dev-secret-key', expires_hours: int = 24):
        self.secret_key = secret_key
        self.expires_hours = expires_hours

    def generate_token(self, user_id: int) -> str:
        """生成 JWT Token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=self.expires_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def verify_token(self, token: str) -> Optional[Dict]:
        """验证 JWT Token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def get_user_by_token(self, token: str) -> Optional[User]:
        """通过 Token 获取用户"""
        payload = self.verify_token(token)
        if payload:
            return User.query.get(payload.get('user_id'))
        return None

    @staticmethod
    def register(username: str, email: str, password: str) -> Dict:
        """用户注册"""
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return {
                'success': False,
                'message': '用户名已存在'
            }

        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            return {
                'success': False,
                'message': '邮箱已被注册'
            }

        # 创建用户
        user = User(username=username, email=email)
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            return {
                'success': True,
                'message': '注册成功',
                'user': user.to_dict()
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'注册失败: {str(e)}'
            }

    @staticmethod
    def login(username: str, password: str, auth_service: 'AuthService') -> Dict:
        """用户登录"""
        user = User.query.filter_by(username=username).first()

        if not user:
            return {
                'success': False,
                'message': '用户名或密码错误'
            }

        if not user.is_active:
            return {
                'success': False,
                'message': '账户已被禁用'
            }

        if not user.check_password(password):
            return {
                'success': False,
                'message': '用户名或密码错误'
            }

        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()

        # 生成 Token
        token = auth_service.generate_token(user.id)

        return {
            'success': True,
            'message': '登录成功',
            'token': token,
            'user': user.to_dict()
        }

    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str) -> Dict:
        """修改密码"""
        user = User.query.get(user_id)

        if not user:
            return {
                'success': False,
                'message': '用户不存在'
            }

        if not user.check_password(old_password):
            return {
                'success': False,
                'message': '原密码错误'
            }

        user.set_password(new_password)
        db.session.commit()

        return {
            'success': True,
            'message': '密码修改成功'
        }