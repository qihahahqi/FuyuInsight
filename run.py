#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用启动脚本
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 在导入 app 之前配置日志
from backend.app.utils.logging import setup_log_level
log_mode = os.environ.get('LOG_MODE', 'prod')
setup_log_level(mode=log_mode)

from backend.app import create_app


def load_config():
    """加载配置文件"""
    import yaml
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}


# 创建应用实例（供 gunicorn 使用）
config = load_config()
app = create_app(config)


def main():
    """启动应用"""
    print("=" * 60)
    print("  投资理财管理系统 v1.0")
    print("=" * 60)

    server_config = config.get('server', {})
    host = server_config.get('host', '0.0.0.0')
    port = server_config.get('port', 5000)
    debug = server_config.get('debug', False)

    print(f"\n服务地址: http://{host}:{port}")
    print(f"调试模式: {'开启' if debug else '关闭'}")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 60)

    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()