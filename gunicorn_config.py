#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gunicorn 生产服务器配置
"""

import multiprocessing
import os

# 服务器绑定
bind = "0.0.0.0:5001"

# 工作进程数（测试环境用少量 workers）
# 生产环境建议: CPU核心数 * 2 + 1，但测试环境用2-4个即可
workers = min(multiprocessing.cpu_count() * 2 + 1, 4)

# 每个工作进程的线程数
threads = 2

# 工作模式
worker_class = "sync"

# 超时时间（秒）
timeout = 120

# 最大请求数后重启工作进程
max_requests = 1000
max_requests_jitter = 100

# 守护进程模式
daemon = False

# 进程 ID 文件
pidfile = "gunicorn.pid"

# 确保日志目录存在
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 日志配置 - 根据模式调整
log_mode = os.environ.get('LOG_MODE', 'prod')
if log_mode == 'debug':
    # 开发模式：所有日志输出到控制台
    accesslog = '-'  # 输出到控制台
    errorlog = '-'   # 错误也输出到控制台
    loglevel = 'debug'
elif log_mode == 'prod-file':
    # 生产+日志文件模式
    accesslog = None
    errorlog = 'logs/error.log'
    loglevel = 'warning'
else:
    # 生产模式：错误输出到控制台，不记录访问日志
    accesslog = None
    errorlog = '-'  # 错误输出到控制台
    loglevel = 'warning'

# 控制台输出（启动信息）
capture_output = True

# 保持连接超时
keepalive = 5

# 请求体最大大小（0 表示无限制）
limit_request_line = 0

# 显示启动信息（只在调试时开启）
print_config = False

# 传递环境变量给工作进程（格式: KEY=VALUE）
raw_env = [f'LOG_MODE={log_mode}']