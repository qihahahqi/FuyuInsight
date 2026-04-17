#!/bin/bash
# ===========================================
# 投资理财管理系统 - 一键启动脚本
# ===========================================
# 使用方法:
#   ./start.sh          # 生产模式（关键日志）
#   ./start.sh dev      # 开发模式（全量日志，调试用）
#   ./start.sh log      # 生产模式+日志文件（关键日志保存到 logs/）
#   ./start.sh init     # 初始化数据库
#   ./start.sh migrate  # 运行数据库迁移
#   ./start.sh stop     # 停止服务
# ===========================================

# 获取脚本所在目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="${SCRIPT_DIR}/venv"
MODE="${1:-prod}"
PORT=5001

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 清理占用端口的进程
cleanup_port() {
    local port=$1
    local pids=$(lsof -t -i :$port 2>/dev/null)
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}清理占用端口 $port 的进程...${NC}"
        for pid in $pids; do
            kill -9 $pid 2>/dev/null
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓ 已终止进程 PID: $pid${NC}"
            fi
        done
        sleep 1
        # 再次检查
        pids=$(lsof -t -i :$port 2>/dev/null)
        if [ -n "$pids" ]; then
            echo -e "${RED}警告: 端口 $port 仍被占用，请手动处理${NC}"
            return 1
        fi
    fi
    return 0
}

echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}   投资理财管理系统 v1.0.0${NC}"
echo -e "${GREEN}=======================================${NC}"

# 检查虚拟环境
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}虚拟环境不存在，正在创建...${NC}"
    python3 -m venv "$VENV_PATH"
    if [ $? -ne 0 ]; then
        echo -e "${RED}错误: 创建虚拟环境失败${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ 虚拟环境创建成功${NC}"
fi

# 激活虚拟环境
source "$VENV_PATH/bin/activate"

# 切换到项目目录
cd "$SCRIPT_DIR"

# 设置 Flask 环境变量
export FLASK_APP=run.py:app

# 检查依赖
if [ ! -f "$VENV_PATH/lib/python*/site-packages/flask/__init__.py" ] 2>/dev/null; then
    echo -e "${YELLOW}正在安装依赖...${NC}"
    pip install -r requirements.txt -q
    if [ $? -ne 0 ]; then
        echo -e "${RED}错误: 安装依赖失败${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ 依赖安装完成${NC}"
fi

# 检查配置文件
if [ ! -f "${SCRIPT_DIR}/config/config.yaml" ]; then
    if [ -f "${SCRIPT_DIR}/config/config.yaml.example" ]; then
        echo -e "${YELLOW}配置文件不存在，正在从模板创建...${NC}"
        cp "${SCRIPT_DIR}/config/config.yaml.example" "${SCRIPT_DIR}/config/config.yaml"
        echo -e "${GREEN}✓ 已创建 config/config.yaml${NC}"
        echo -e "${YELLOW}请编辑 config/config.yaml 配置数据库和 API Key${NC}"
    else
        echo -e "${RED}错误: 缺少配置文件模板${NC}"
        exit 1
    fi
fi

# 处理不同模式
case "$MODE" in
    init)
        echo -e "${YELLOW}正在初始化数据库...${NC}"
        python init_db.py
        exit $?
        ;;
    migrate)
        echo -e "${YELLOW}正在运行数据库迁移...${NC}"
        flask db upgrade
        exit $?
        ;;
    stop)
        echo -e "${YELLOW}正在停止服务...${NC}"
        # 清理所有占用端口的进程
        cleanup_port $PORT
        # 同时清理 gunicorn.pid
        if [ -f "gunicorn.pid" ]; then
            rm -f gunicorn.pid
        fi
        echo -e "${GREEN}✓ 服务已停止${NC}"
        exit 0
        ;;
    dev)
        # 开发模式 - 全量日志（DEBUG级别）
        cleanup_port $PORT
        export LOG_MODE=debug
        echo -e "${GREEN}正在以开发模式启动（全量日志）...${NC}"
        echo -e "访问地址: http://localhost:5001"
        echo -e "${YELLOW}日志级别: DEBUG（显示所有日志）${NC}"
        echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
        python run.py
        ;;
    log)
        # 生产模式 + 日志文件
        cleanup_port $PORT
        export LOG_MODE=prod-file
        echo -e "${GREEN}正在以生产模式启动（日志保存到文件）...${NC}"
        echo -e "访问地址: http://0.0.0.0:5001"
        echo -e "${YELLOW}日志级别: INFO（关键日志），保存到 logs/ 目录${NC}"
        echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
        gunicorn -c gunicorn_config.py run:app
        ;;
    prod|*)
        # 生产模式 - 关键日志（INFO级别，过滤HTTP请求等）
        cleanup_port $PORT
        export LOG_MODE=prod
        echo -e "${GREEN}正在以生产模式启动（关键日志）...${NC}"
        echo -e "访问地址: http://0.0.0.0:5001"
        echo -e "${YELLOW}日志级别: INFO（关键日志，过滤HTTP请求）${NC}"
        echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
        gunicorn -c gunicorn_config.py run:app
        ;;
esac