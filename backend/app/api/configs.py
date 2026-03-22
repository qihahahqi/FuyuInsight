#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统配置 API
"""

from flask import Blueprint, request
from .. import db
from ..models import Config
from ..utils import success_response, error_response
from ..utils.decorators import login_required, get_current_user
from ..utils.config import config_manager
import json
import yaml
import os

configs_bp = Blueprint('configs', __name__)


@configs_bp.route('/configs', methods=['GET'])
@login_required
def get_configs():
    """获取所有配置"""
    try:
        user = get_current_user()
        # 从数据库获取用户配置
        db_configs = Config.query.filter(
            (Config.user_id == user.id) | (Config.user_id == None)
        ).all()
        db_config_dict = {c.key: c.value for c in db_configs}

        # 从配置文件获取
        file_configs = config_manager.get_all()

        # 合并配置（数据库优先）
        merged = {**file_configs, **db_config_dict}

        # 隐藏敏感信息
        if 'llm' in merged and isinstance(merged['llm'], dict):
            merged['llm'] = {**merged['llm']}
            if merged['llm'].get('api_key'):
                merged['llm']['api_key'] = '******'

        return success_response(merged)
    except Exception as e:
        return error_response(str(e))


@configs_bp.route('/configs/<key>', methods=['GET'])
@login_required
def get_config(key):
    """获取单个配置"""
    try:
        user = get_current_user()
        # 先从数据库查找
        config = Config.query.filter_by(key=key, user_id=user.id).first()

        if config:
            value = config.value
            # 尝试解析 JSON
            try:
                value = json.loads(value)
            except:
                pass
            return success_response({'key': key, 'value': value})

        # 再从配置文件查找
        value = config_manager.get(key)
        if value is not None:
            return success_response({'key': key, 'value': value})

        return error_response("配置项不存在", 404)
    except Exception as e:
        return error_response(str(e))


@configs_bp.route('/configs', methods=['PUT'])
@login_required
def update_configs():
    """更新配置"""
    try:
        user = get_current_user()
        data = request.get_json()

        for key, value in data.items():
            # 转换值为字符串
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False)
            else:
                value_str = str(value)

            # 更新或创建配置
            config = Config.query.filter_by(key=key, user_id=user.id).first()
            if config:
                config.value = value_str
            else:
                config = Config(user_id=user.id, key=key, value=value_str)
                db.session.add(config)

        db.session.commit()

        # 更新内存配置
        for key, value in data.items():
            config_manager.set(key, value)

        return success_response(None, "配置更新成功")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@configs_bp.route('/configs/<key>', methods=['PUT'])
@login_required
def update_config(key):
    """更新单个配置"""
    try:
        user = get_current_user()
        data = request.get_json()

        if 'value' not in data:
            return error_response("缺少 value 字段")

        value = data['value']
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, ensure_ascii=False)
        else:
            value_str = str(value)

        config = Config.query.filter_by(key=key, user_id=user.id).first()
        if config:
            config.value = value_str
        else:
            config = Config(user_id=user.id, key=key, value=value_str, description=data.get('description'))
            db.session.add(config)

        db.session.commit()

        # 更新内存配置
        config_manager.set(key, value)

        return success_response(None, "配置更新成功")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@configs_bp.route('/configs/llm', methods=['GET'])
@login_required
def get_llm_config():
    """获取大模型配置"""
    try:
        user = get_current_user()
        llm_config = config_manager.llm_config.copy()

        # 从数据库覆盖
        for key in ['provider', 'model', 'api_base', 'temperature', 'max_tokens', 'enabled']:
            db_config = Config.query.filter_by(key=f'llm.{key}', user_id=user.id).first()
            if db_config:
                try:
                    value = json.loads(db_config.value)
                    # 处理布尔值
                    if key == 'enabled' and isinstance(value, str):
                        value = value.lower() == 'true'
                    llm_config[key] = value
                except:
                    llm_config[key] = db_config.value

        # 检查 API Key 是否配置
        api_key_config = Config.query.filter_by(key='llm.api_key', user_id=user.id).first()
        llm_config['has_api_key'] = bool(api_key_config and api_key_config.value)
        llm_config['api_key'] = '******' if llm_config['has_api_key'] else ''

        return success_response(llm_config)
    except Exception as e:
        return error_response(str(e))


@configs_bp.route('/configs/llm', methods=['PUT'])
@login_required
def update_llm_config():
    """更新大模型配置"""
    import logging
    from sqlalchemy.exc import IntegrityError
    logger = logging.getLogger(__name__)

    try:
        user = get_current_user()
        data = request.get_json()

        if not data:
            return error_response("请求数据为空")

        logger.info(f"Updating LLM config for user {user.id}, keys: {list(data.keys())}")

        # 更新数据库
        for key, value in data.items():
            if key == 'api_key' and value == '******':
                continue  # 不更新隐藏的 API Key

            db_key = f'llm.{key}'
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False)
            else:
                value_str = str(value)

            # 查询现有配置
            config = Config.query.filter_by(key=db_key, user_id=user.id).first()
            if config:
                logger.debug(f"Updating existing config: {db_key}")
                config.value = value_str
            else:
                # 检查是否有系统级配置（user_id=None）
                system_config = Config.query.filter_by(key=db_key, user_id=None).first()
                if system_config:
                    logger.debug(f"Creating user config overriding system config: {db_key}")
                else:
                    logger.debug(f"Creating new config: {db_key}")

                config = Config(user_id=user.id, key=db_key, value=value_str)
                db.session.add(config)

        logger.info("Committing LLM config changes...")
        db.session.commit()
        logger.info("LLM config saved successfully")

        # 更新内存配置
        current_llm = config_manager.get('llm', {})
        current_llm.update(data)
        if 'api_key' in data and data['api_key'] == '******':
            current_llm.pop('api_key', None)
        config_manager.set('llm', current_llm)

        return success_response(None, "大模型配置更新成功")
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError saving LLM config: {str(e)}")
        return error_response(f"数据库约束冲突，请刷新页面后重试: {str(e)}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to save LLM config: {str(e)}", exc_info=True)
        return error_response(str(e))


@configs_bp.route('/configs/test-llm', methods=['POST'])
@login_required
def test_llm_connection():
    """测试大模型连接"""
    try:
        user = get_current_user()
        from ..services import LLMService

        data = request.get_json() or {}

        llm_config = config_manager.llm_config.copy()

        # 从数据库读取用户级别的配置
        config_keys = ['provider', 'model', 'api_base']
        for key in config_keys:
            db_config = Config.query.filter_by(key=f'llm.{key}', user_id=user.id).first()
            if db_config:
                llm_config[key] = db_config.value

        provider = data.get('provider') or llm_config.get('provider', 'openai')
        model = data.get('model') or llm_config.get('model', 'gpt-4')
        api_base = data.get('api_base') or llm_config.get('api_base', '')

        # API Key 从数据库获取或使用传入值
        api_key = data.get('api_key')
        if not api_key or api_key == '******':
            api_key_config = Config.query.filter_by(key='llm.api_key', user_id=user.id).first()
            api_key = api_key_config.value if api_key_config else ''

        if not api_key:
            return error_response("请配置 API Key")

        service = LLMService(
            provider=provider,
            api_key=api_key,
            api_base=api_base,
            model=model
        )

        result = service.test_connection()

        if result['success']:
            return success_response(result, "连接成功")
        else:
            return error_response(result['message'])
    except Exception as e:
        return error_response(str(e))


@configs_bp.route('/configs/strategy', methods=['GET'])
@login_required
def get_strategy_config():
    """获取策略配置"""
    try:
        user = get_current_user()
        strategy_config = config_manager.strategy_config.copy()

        # 从数据库覆盖
        db_configs = Config.query.filter(
            Config.key.like('strategy.%'),
            (Config.user_id == user.id) | (Config.user_id == None)
        ).all()
        for config in db_configs:
            key = config.key.replace('strategy.', '')
            try:
                strategy_config[key] = json.loads(config.value)
            except:
                strategy_config[key] = config.value

        return success_response(strategy_config)
    except Exception as e:
        return error_response(str(e))


@configs_bp.route('/configs/strategy', methods=['PUT'])
@login_required
def update_strategy_config():
    """更新策略配置"""
    try:
        user = get_current_user()
        data = request.get_json()

        for key, value in data.items():
            db_key = f'strategy.{key}'
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False)
            else:
                value_str = str(value)

            config = Config.query.filter_by(key=db_key, user_id=user.id).first()
            if config:
                config.value = value_str
            else:
                config = Config(user_id=user.id, key=db_key, value=value_str)
                db.session.add(config)

        db.session.commit()

        # 更新内存配置
        current_strategy = config_manager.get('strategy', {})
        current_strategy.update(data)
        config_manager.set('strategy', current_strategy)

        return success_response(None, "策略配置更新成功")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


# ==================== Tushare 配置 API ====================

@configs_bp.route('/configs/tushare', methods=['GET'])
@login_required
def get_tushare_config():
    """获取Tushare配置"""
    try:
        user = get_current_user()
        tushare_config = config_manager.get('tushare', {}).copy()

        # 从数据库覆盖
        db_configs = Config.query.filter(
            Config.key.like('tushare.%'),
            (Config.user_id == user.id) | (Config.user_id == None)
        ).all()
        for cfg in db_configs:
            key = cfg.key.replace('tushare.', '')
            try:
                tushare_config[key] = json.loads(cfg.value)
            except:
                tushare_config[key] = cfg.value

        # 隐藏Token
        if tushare_config.get('token'):
            token = tushare_config['token']
            tushare_config['token'] = token[:8] + '******' if len(token) > 8 else '******'
            tushare_config['has_token'] = True
        else:
            tushare_config['has_token'] = False

        return success_response(tushare_config)
    except Exception as e:
        return error_response(str(e))


@configs_bp.route('/configs/tushare', methods=['PUT'])
@login_required
def update_tushare_config():
    """更新Tushare配置"""
    try:
        user = get_current_user()
        data = request.get_json()

        for key, value in data.items():
            db_key = f'tushare.{key}'

            # 处理Token隐藏值
            if key == 'token' and value and '******' in str(value):
                continue

            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False)
            else:
                value_str = str(value)

            config = Config.query.filter_by(key=db_key, user_id=user.id).first()
            if config:
                config.value = value_str
            else:
                config = Config(user_id=user.id, key=db_key, value=value_str)
                db.session.add(config)

        db.session.commit()

        # 更新内存配置
        current_tushare = config_manager.get('tushare', {})
        current_tushare.update(data)
        config_manager.set('tushare', current_tushare)

        # 更新Tushare服务实例
        from ..services.tushare_service import init_tushare_service
        if current_tushare.get('token'):
            init_tushare_service(
                token=current_tushare['token'],
                base_url=current_tushare.get('base_url', 'https://api.tushare.pro')
            )

        return success_response(None, "Tushare配置更新成功")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e))


@configs_bp.route('/configs/tushare/test', methods=['POST'])
@login_required
def test_tushare_connection():
    """测试Tushare连接"""
    try:
        user = get_current_user()
        from ..services.tushare_service import TushareService

        data = request.get_json() or {}

        # 获取Token
        token = data.get('token')
        if not token or '******' in token:
            token_config = Config.query.filter_by(key='tushare.token', user_id=user.id).first()
            if not token_config:
                # 尝试从配置文件获取
                token = config_manager.get('tushare', {}).get('token', '')
            else:
                token = token_config.value

        if not token:
            return error_response("请配置Tushare Token")

        base_url = data.get('base_url') or config_manager.get('tushare', {}).get('base_url', 'https://api.tushare.pro')

        # 创建服务实例并测试
        service = TushareService(token=token, base_url=base_url)
        result = service.test_connection()

        if result['success']:
            return success_response(result, "Tushare连接成功")
        else:
            return error_response(result['message'])
    except Exception as e:
        return error_response(str(e))


@configs_bp.route('/configs/data-sources', methods=['GET'])
@login_required
def get_data_sources_config():
    """获取所有数据源配置"""
    try:
        user = get_current_user()

        data_sources = {
            'tushare': {
                'name': 'Tushare Pro',
                'enabled': False,
                'has_token': False,
                'description': '专业金融数据接口，需要Token'
            },
            'akshare': {
                'name': 'AKShare',
                'enabled': False,
                'has_token': False,
                'description': '免费开源金融数据接口'
            },
            'local': {
                'name': '本地数据',
                'enabled': True,
                'description': '手动导入的本地数据'
            }
        }

        # 检查Tushare配置
        tushare_config = config_manager.get('tushare', {})
        db_tushare = Config.query.filter_by(key='tushare.token', user_id=user.id).first()

        if tushare_config.get('token') or (db_tushare and db_tushare.value):
            data_sources['tushare']['has_token'] = True
            data_sources['tushare']['enabled'] = tushare_config.get('enabled', True)

        return success_response(data_sources)
    except Exception as e:
        return error_response(str(e))