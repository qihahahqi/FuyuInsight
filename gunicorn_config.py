#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gunicorn 生产服务器配置
"""

import multiprocessing

# 服务器绑定
bind = "0.0.0.0:5001"

# 工作进程数（推荐 CPU 核心数 * 2 + 1）
workers = multiprocessing.cpu_count() * 2 + 1

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

# 日志配置
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# 保持连接超时
keepalive = 5

# 请求体最大大小（0 表示无限制）
limit_request_line = 0