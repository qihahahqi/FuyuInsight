#!/bin/bash
# 投资理财管理系统 - 一键启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="/home/test/financial-management-system/venv"
MODE="${1:-dev}"  # 默认开发模式，可选: dev, prod

# 检查虚拟环境是否存在
if [ ! -d "$VENV_PATH" ]; then
    echo "错误: 虚拟环境不存在: $VENV_PATH"
    echo "请先创建虚拟环境或修改脚本中的 VENV_PATH"
    exit 1
fi

# 激活虚拟环境
source "$VENV_PATH/bin/activate"

# 切换到项目目录
cd "$SCRIPT_DIR"

# 启动应用
if [ "$MODE" = "prod" ]; then
    echo "正在以生产模式启动投资理财管理系统..."
    gunicorn -c gunicorn_config.py run:app
else
    echo "正在以开发模式启动投资理财管理系统..."
    python run.py
fi