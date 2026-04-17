#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审计日志服务
"""

from flask import request, g
from .. import db
from ..models.audit import AuditLog
from datetime import datetime
import json


class AuditService:
    """审计日志服务"""

    @staticmethod
    def log(
        action: str,
        resource_type: str = None,
        resource_id: int = None,
        details: dict = None,
        old_values: dict = None,
        new_values: dict = None,
        status_code: int = None,
        error_message: str = None
    ):
        """
        记录审计日志

        Args:
            action: 操作类型 (create/update/delete/login/logout/etc)
            resource_type: 资源类型 (position/trade/account/config)
            resource_id: 资源ID
            details: 操作详情
            old_values: 变更前的值
            new_values: 变更后的值
            status_code: 响应状态码
            error_message: 错误信息
        """
        user_id = None
        if hasattr(g, 'current_user') and g.current_user:
            user_id = g.current_user.id

        duration_ms = None
        if hasattr(g, 'start_time'):
            import time
            duration_ms = int((time.time() - g.start_time) * 1000)

        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            old_values=old_values,
            new_values=new_values,
            ip_address=request.remote_addr if request else None,
            user_agent=request.user_agent.string[:255] if request and request.user_agent else None,
            request_method=request.method if request else None,
            request_path=request.path if request else None,
            status_code=status_code,
            duration_ms=duration_ms,
            error_message=error_message,
            created_at=datetime.utcnow()
        )

        try:
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # 审计日志失败不应影响主流程
            print(f"Audit log failed: {e}")

    @staticmethod
    def log_create(resource_type: str, resource_id: int, new_values: dict = None, details: dict = None):
        """记录创建操作"""
        AuditService.log(
            action='create',
            resource_type=resource_type,
            resource_id=resource_id,
            new_values=new_values,
            details=details,
            status_code=201
        )

    @staticmethod
    def log_update(resource_type: str, resource_id: int, old_values: dict = None, new_values: dict = None, details: dict = None):
        """记录更新操作"""
        AuditService.log(
            action='update',
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            details=details,
            status_code=200
        )

    @staticmethod
    def log_delete(resource_type: str, resource_id: int, old_values: dict = None, details: dict = None):
        """记录删除操作"""
        AuditService.log(
            action='delete',
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            details=details,
            status_code=200
        )

    @staticmethod
    def log_login(user_id: int, success: bool = True, error_message: str = None):
        """记录登录操作"""
        AuditService.log(
            action='login' if success else 'login_failed',
            resource_type='user',
            resource_id=user_id,
            status_code=200 if success else 401,
            error_message=error_message
        )

    @staticmethod
    def log_logout(user_id: int):
        """记录登出操作"""
        AuditService.log(
            action='logout',
            resource_type='user',
            resource_id=user_id,
            status_code=200
        )

    @staticmethod
    def get_user_logs(user_id: int, limit: int = 50, offset: int = 0):
        """获取用户操作日志"""
        logs = AuditLog.query.filter_by(user_id=user_id)\
            .order_by(AuditLog.created_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
        return [log.to_dict() for log in logs]

    @staticmethod
    def get_resource_logs(resource_type: str, resource_id: int, limit: int = 50):
        """获取资源操作日志"""
        logs = AuditLog.query.filter_by(resource_type=resource_type, resource_id=resource_id)\
            .order_by(AuditLog.created_at.desc())\
            .limit(limit)\
            .all()
        return [log.to_dict() for log in logs]