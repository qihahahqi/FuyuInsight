#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理工具
"""

import os
import yaml
from typing import Any, Dict, Optional


class ConfigManager:
    """配置管理器"""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = None  # 重置配置
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._load_config()

    def _load_config(self):
        """加载配置文件"""
        # 从 backend/app/utils 到项目根目录需要向上 4 层
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        config_path = os.path.join(project_root, 'config', 'config.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = {}

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项（支持点分隔符）"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def get_all(self) -> Dict:
        """获取所有配置"""
        return self._config.copy()

    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def save(self) -> None:
        """保存配置到文件"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        config_path = os.path.join(project_root, 'config', 'config.yaml')
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)

    def reload(self) -> None:
        """重新加载配置"""
        self._load_config()

    @property
    def database_config(self) -> Dict:
        """数据库配置"""
        return self._config.get('database', {})

    @property
    def server_config(self) -> Dict:
        """服务器配置"""
        return self._config.get('server', {})

    @property
    def strategy_config(self) -> Dict:
        """策略配置"""
        return self._config.get('strategy', {})

    @property
    def llm_config(self) -> Dict:
        """大模型配置"""
        return self._config.get('llm', {})


# 全局配置管理器实例
config_manager = ConfigManager()