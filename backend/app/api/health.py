#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康检查接口
"""

from flask import Blueprint, jsonify
from datetime import datetime
import time
import logging

health_bp = Blueprint('health', __name__)
logger = logging.getLogger(__name__)

# 服务启动时间
START_TIME = time.time()

# 版本号
VERSION = "1.2.0"


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    服务健康检查接口

    返回服务状态、版本、各组件状态等信息
    """
    from flask import current_app

    # 计算运行时间
    uptime = int(time.time() - START_TIME)

    # 检查各组件状态
    services = {}

    # 1. 数据库状态
    try:
        from ..models import db
        # 执行简单查询测试连接
        db.session.execute(db.text('SELECT 1'))
        services['database'] = 'ok'
    except Exception as e:
        logger.error(f"健康检查 - 数据库连接失败: {str(e)}")
        services['database'] = 'error'

    # 2. 定时任务调度器状态
    try:
        from ..services.scheduler_service import scheduler_service
        if scheduler_service and scheduler_service.is_running():
            services['scheduler'] = 'running'
        else:
            services['scheduler'] = 'stopped'
    except Exception as e:
        logger.warning(f"健康检查 - 调度器检查失败: {str(e)}")
        services['scheduler'] = 'unknown'

    # 3. LLM 配置状态
    try:
        config = current_app.config.get('APP_CONFIG', {})
        llm_config = config.get('llm', {})
        if llm_config.get('enabled') and llm_config.get('api_key'):
            services['llm'] = 'configured'
        else:
            services['llm'] = 'disabled'
    except Exception as e:
        logger.warning(f"健康检查 - LLM 配置检查失败: {str(e)}")
        services['llm'] = 'unknown'

    # 4. 数据源状态
    try:
        config = current_app.config.get('APP_CONFIG', {})
        akshare_enabled = config.get('akshare', {}).get('enabled', False)
        tushare_enabled = config.get('tushare', {}).get('enabled', False)
        if akshare_enabled or tushare_enabled:
            services['datasource'] = 'configured'
        else:
            services['datasource'] = 'disabled'
    except Exception as e:
        logger.warning(f"健康检查 - 数据源检查失败: {str(e)}")
        services['datasource'] = 'unknown'

    # 综合状态判定
    status = 'healthy'
    if services.get('database') == 'error':
        status = 'unhealthy'
    elif any(v in ['error', 'stopped'] for v in services.values()):
        status = 'degraded'

    response = {
        'status': status,
        'version': VERSION,
        'uptime': uptime,
        'uptime_human': format_uptime(uptime),
        'services': services,
        'timestamp': datetime.now().isoformat()
    }

    # unhealthy 返回 503
    http_status = 503 if status == 'unhealthy' else 200

    return jsonify(response), http_status


@health_bp.route('/ping', methods=['GET'])
def ping():
    """
    简单的 ping 接口，用于快速检查服务是否存活
    """
    return jsonify({'pong': True, 'timestamp': datetime.now().isoformat()})


def format_uptime(seconds):
    """格式化运行时间"""
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60

    if days > 0:
        return f"{days}天 {hours}小时 {minutes}分钟"
    elif hours > 0:
        return f"{hours}小时 {minutes}分钟"
    else:
        return f"{minutes}分钟"