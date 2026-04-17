#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务管理接口
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

scheduler_bp = Blueprint('scheduler', __name__)
logger = logging.getLogger(__name__)


@scheduler_bp.route('/scheduler/status', methods=['GET'])
def get_scheduler_status():
    """
    获取调度器状态

    返回调度器运行状态、下次同步时间等信息
    """
    from ..services.scheduler_service import scheduler_service

    try:
        status = scheduler_service.get_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        logger.error(f"获取调度器状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@scheduler_bp.route('/scheduler/sync', methods=['POST'])
def trigger_sync():
    """
    手动触发价格同步

    立即执行一次所有用户的持仓价格同步
    """
    from ..services.scheduler_service import scheduler_service

    try:
        result = scheduler_service.trigger_sync()
        if result['success']:
            logger.info("手动触发价格同步成功")
            return jsonify({
                'success': True,
                'message': result['message'],
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 500
    except Exception as e:
        logger.error(f"手动触发同步失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@scheduler_bp.route('/scheduler/config', methods=['GET'])
def get_sync_config():
    """
    获取同步配置

    返回当前的同步时间点配置
    """
    from ..services.scheduler_service import scheduler_service

    try:
        config = {
            'sync_hours': scheduler_service.sync_hours,
            'sync_hour_names': {
                9: '开盘前',
                12: '午间',
                14: '下午开盘前',
                16: '收盘后'
            }
        }
        return jsonify({
            'success': True,
            'data': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@scheduler_bp.route('/scheduler/config', methods=['PUT'])
def update_sync_config():
    """
    更新同步配置

    修改同步时间点
    """
    from ..services.scheduler_service import scheduler_service

    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少请求数据'
            }), 400

        sync_hours = data.get('sync_hours')
        if not sync_hours or not isinstance(sync_hours, list):
            return jsonify({
                'success': False,
                'message': 'sync_hours 必须是列表'
            }), 400

        # 验证时间范围
        for hour in sync_hours:
            if not isinstance(hour, int) or hour < 0 or hour > 23:
                return jsonify({
                    'success': False,
                    'message': f'无效的时间点: {hour}'
                }), 400

        scheduler_service.sync_hours = sync_hours
        logger.info(f"同步配置已更新: {sync_hours}")

        return jsonify({
            'success': True,
            'message': '配置已更新',
            'data': {'sync_hours': sync_hours}
        })
    except Exception as e:
        logger.error(f"更新同步配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@scheduler_bp.route('/scheduler/history', methods=['GET'])
def get_sync_history():
    """
    获取同步历史记录

    返回最近的同步执行记录（模拟数据，实际需要持久化存储）
    """
    # 实际项目中应该有专门的同步历史表
    # 这里返回模拟数据
    history = [
        {
            'id': 1,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'manual',
            'status': 'success',
            'users_count': 1,
            'positions_updated': 5
        }
    ]

    return jsonify({
        'success': True,
        'data': history
    })