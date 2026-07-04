#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用启动脚本
"""

import os
import sys
import warnings

# ============================================
# 加载 .env 环境变量文件（必须最先执行）
# ============================================
try:
    from dotenv import load_dotenv
    # 从 run.py 所在目录（项目根目录）加载 .env
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ 已加载环境变量文件: {env_path}")
    else:
        # 尝试加载默认 .env
        load_dotenv()
except ImportError:
    # python-dotenv 未安装，跳过（环境变量需手动设置）
    pass

# 抑制 pkg_resources 弃用警告（来自 py_mini_racer 等依赖）
warnings.filterwarnings('ignore', message='pkg_resources is deprecated')
warnings.filterwarnings('ignore', category=UserWarning, module='py_mini_racer')

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

    # 开发模式启用自动重载
    log_mode = os.environ.get('LOG_MODE', 'prod')
    debug = log_mode == 'debug'
    use_reloader = debug  # 开发模式启用自动重载

    print(f"\n服务地址: http://{host}:{port}")
    print(f"调试模式: {'开启' if debug else '关闭'}")
    if debug:
        print("自动重载: 开启（修改代码后自动重启）")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 60)

    # Flask 开发模式：debug=True 启用调试，use_reloader=True 启用自动重载
    app.run(host=host, port=port, debug=debug, use_reloader=use_reloader)


if __name__ == '__main__':
    main()