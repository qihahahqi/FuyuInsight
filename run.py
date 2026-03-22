#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用启动脚本
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app


def main():
    """启动应用"""
    print("=" * 60)
    print("  投资理财管理系统 v1.0")
    print("=" * 60)

    # 加载配置
    import yaml
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}

    server_config = config.get('server', {})
    host = server_config.get('host', '0.0.0.0')
    port = server_config.get('port', 5000)
    debug = server_config.get('debug', False)

    app = create_app(config)

    print(f"\n服务地址: http://{host}:{port}")
    print(f"调试模式: {'开启' if debug else '关闭'}")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 60)

    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()