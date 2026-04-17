#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块
支持多种日志模式：debug（全量）、prod（关键）、file（文件保存）
支持敏感数据脱敏
"""

import os
import sys
import time
import uuid
import logging
import re
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from flask import request, g, has_request_context
from functools import wraps


# 关键日志模块（在 prod 模式下保留 INFO 级别）
KEY_MODULES = [
    'ai', 'llm', 'scheduler', 'history_fetch', 'profit', 'backtest',
    'valuation', 'snapshot', 'import', 'export', 'audit'
]

# 完全静默的模块（不显示任何日志）
SILENT_MODULES = ['werkzeug', 'urllib3', 'socketio', 'engineio', 'sqlalchemy', 'alembic']

# 敏感字段列表（用于脱敏）
SENSITIVE_FIELDS = [
    'password', 'api_key', 'apikey', 'token', 'secret', 'credential',
    'jwt', 'auth', 'key', 'private', 'session', 'cookie', 'authorization'
]


def sanitize_for_log(data):
    """
    脱敏敏感字段

    Args:
        data: 字典、字符串或其他数据

    Returns:
        脱敏后的数据
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(s in key_lower for s in SENSITIVE_FIELDS):
                result[key] = '***REDACTED***'
            elif isinstance(value, (dict, str)):
                result[key] = sanitize_for_log(value)
            else:
                result[key] = value
        return result
    elif isinstance(data, str):
        # 脱敏字符串中的敏感信息
        sanitized = data
        # 脱敏 JWT Token 格式
        if re.search(r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*', data):
            sanitized = re.sub(
                r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*',
                '***JWT_TOKEN***',
                sanitized
            )
        # 脱敏 API Key 格式（常见的长度）
        if re.search(r'[a-zA-Z0-9]{32,}', data):
            sanitized = re.sub(
                r'(api[_-]?key["\']?\s*[:=]\s*["\']?)[a-zA-Z0-9]{32,}',
                r'\1***API_KEY***',
                sanitized,
                flags=re.IGNORECASE
            )
        return sanitized
    return data


def setup_log_level(mode='prod', log_dir=None):
    """
    配置日志级别

    Args:
        mode: 日志模式（从环境变量 LOG_MODE 读取）
            - 'debug': 全量日志（DEBUG级别，所有模块）
            - 'prod': 关键日志（INFO级别，过滤SQL/HTTP等）
            - 'prod-file': 关键日志 + 文件保存（按日期）
        log_dir: 日志文件目录（仅 prod-file 模式使用）
    """
    # 从环境变量获取模式
    mode = os.environ.get('LOG_MODE', mode)

    # 确定根日志级别
    if mode == 'debug':
        root_level = logging.DEBUG
        console_level = logging.DEBUG
    else:
        root_level = logging.INFO
        console_level = logging.INFO

    # 创建日志目录
    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'logs')

    if mode in ['prod-file', 'file'] and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(root_level)

    # 清除已有的处理器
    root_logger.handlers.clear()

    # 创建格式器
    if mode == 'debug':
        # 详细格式
        console_format = logging.Formatter(
            '[%(levelname)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        file_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # 简洁格式（只显示时间、级别、消息）
        console_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        file_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_format)

    # 在 prod 模式下，添加过滤器
    if mode in ['prod', 'prod-file', 'file']:
        console_handler.addFilter(KeyLogFilter())

    root_logger.addHandler(console_handler)

    # 文件处理器（仅 prod-file/file 模式）
    if mode in ['prod-file', 'file']:
        log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y-%m-%d")}.log')
        file_handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_format)
        file_handler.addFilter(KeyLogFilter())
        root_logger.addHandler(file_handler)

        logging.info(f"日志文件: {log_file}")

    # 完全静默的模块（不显示任何日志）
    for module in SILENT_MODULES:
        silent_logger = logging.getLogger(module)
        silent_logger.setLevel(logging.CRITICAL + 1)
        silent_logger.propagate = False

    # 额外静默 SQLAlchemy 的所有子 logger
    for name in list(logging.root.manager.loggerDict.keys()):
        if 'sqlalchemy' in name.lower() or 'engine' in name.lower():
            silent_logger = logging.getLogger(name)
            silent_logger.setLevel(logging.CRITICAL + 1)
            silent_logger.propagate = False

    return root_logger


class KeyLogFilter(logging.Filter):
    """关键日志过滤器 - 只显示关键模块的 INFO 日志，并脱敏敏感信息"""

    def filter(self, record):
        # 应用日志脱敏
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = sanitize_for_log(record.msg)
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                record.args = sanitize_for_log(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(sanitize_for_log(arg) if isinstance(arg, (dict, str)) else arg for arg in record.args)

        # ERROR 及以上级别始终显示
        if record.levelno >= logging.ERROR:
            return True

        # WARNING 级别始终显示（但排除静默模块）
        if record.levelno >= logging.WARNING:
            module_name = record.name.lower()
            for silent in SILENT_MODULES:
                if silent in module_name:
                    return False
            return True

        # INFO 级别：只显示关键模块
        if record.levelno == logging.INFO:
            module_name = record.name.lower()
            # 排除静默模块
            for silent in SILENT_MODULES:
                if silent in module_name:
                    return False
            # 只显示关键模块
            for key_module in KEY_MODULES:
                if key_module.lower() in module_name:
                    return True
            return False

        # DEBUG 级别：在 prod 模式下过滤掉
        return False


def get_logger(name):
    """获取日志器"""
    return logging.getLogger(name)


class RequestFormatter(logging.Formatter):
    """支持 request_id 的日志格式化器"""

    def format(self, record):
        if has_request_context():
            record.request_id = getattr(g, 'request_id', 'no-request')
        else:
            record.request_id = 'no-request'
        return super().format(record)


def init_request_logging(app):
    """初始化请求日志中间件"""

    @app.before_request
    def before_request():
        """请求开始前"""
        g.start_time = time.time()
        g.request_id = str(uuid.uuid4())[:8]

    @app.after_request
    def after_request(response):
        """请求结束后记录日志"""
        if request.path.startswith('/api/'):
            duration = int((time.time() - g.get('start_time', time.time())) * 1000)
            user_id = getattr(g, 'current_user_id', None)
            if user_id is None:
                user_obj = getattr(g, 'current_user', None)
                try:
                    user_id = user_obj.id if user_obj else None
                except Exception:
                    user_id = None

            logging.info(
                f"[{request.method}] {request.path} - {response.status_code} - {duration}ms - user:{user_id}"
            )

        return response

    @app.teardown_request
    def teardown_request(exception=None):
        """请求结束清理"""
        if exception:
            logging.error(f"Request failed: {exception}")


def log_action(action, resource_type=None, resource_id=None, details=None):
    """记录操作日志的装饰器"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                # 记录成功日志
                user_id = getattr(g, 'current_user', None)
                user_id = user_id.id if user_id else None
                logging.info(
                    f"Action: {action} | Resource: {resource_type}:{resource_id} | User: {user_id} | Details: {details}"
                )
                return result
            except Exception as e:
                logging.error(f"Action failed: {action} - {str(e)}")
                raise
        return wrapper
    return decorator