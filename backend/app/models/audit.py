#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审计日志模型
"""

from datetime import datetime
from .. import db


class AuditLog(db.Model):
    """审计日志表 - 记录用户操作行为"""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='用户ID')
    action = db.Column(db.String(50), nullable=False, comment='操作类型: create/update/delete/login/logout')
    resource_type = db.Column(db.String(50), comment='资源类型: position/trade/account/config')
    resource_id = db.Column(db.Integer, comment='资源ID')
    details = db.Column(db.JSON, comment='操作详情')
    old_values = db.Column(db.JSON, comment='变更前的值')
    new_values = db.Column(db.JSON, comment='变更后的值')
    ip_address = db.Column(db.String(45), comment='IP地址')
    user_agent = db.Column(db.String(255), comment='用户代理')
    request_method = db.Column(db.String(10), comment='请求方法')
    request_path = db.Column(db.String(255), comment='请求路径')
    status_code = db.Column(db.Integer, comment='响应状态码')
    duration_ms = db.Column(db.Integer, comment='请求耗时(毫秒)')
    error_message = db.Column(db.Text, comment='错误信息')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    # 索引
    __table_args__ = (
        db.Index('idx_audit_user', 'user_id'),
        db.Index('idx_audit_action', 'action'),
        db.Index('idx_audit_resource', 'resource_type', 'resource_id'),
        db.Index('idx_audit_created', 'created_at'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'status_code': self.status_code,
            'duration_ms': self.duration_ms,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }