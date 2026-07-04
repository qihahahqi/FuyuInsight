#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask 应用工厂
"""

# ============================================
# 加载 .env 环境变量文件（必须最先执行）
# ============================================
import os
try:
    from dotenv import load_dotenv
    # 查找项目根目录的 .env
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _project_root = os.path.dirname(os.path.dirname(os.path.dirname(_current_dir)))
    _env_path = os.path.join(_project_root, '.env')
    if os.path.exists(_env_path):
        load_dotenv(_env_path)
except ImportError:
    pass

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import yaml
import logging

db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
logger = logging.getLogger(__name__)


def load_config():
    """加载配置文件"""
    # 项目根目录（backend 的父目录）
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config_path = os.path.join(project_root, 'config', 'config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


def create_app(config=None):
    """创建 Flask 应用"""
    # Vue 前端路径 - 直接使用 frontend/dist
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    vue_dist = os.path.join(project_root, 'frontend', 'dist')

    app = Flask(__name__,
                template_folder=vue_dist,
                static_folder=vue_dist,
                static_url_path='')

    # 加载配置
    if config is None:
        config = load_config()

    # 基础配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JSON_AS_ASCII'] = False

    # JWT 配置
    jwt_config = config.get('jwt', {})
    app.config['JWT_SECRET_KEY'] = jwt_config.get('secret_key', os.environ.get('JWT_SECRET', 'jwt-dev-secret-key'))
    app.config['JWT_EXPIRES_HOURS'] = jwt_config.get('expires_hours', 24)

    # 数据库配置 - SQLite（本地文件存储，方便迁移）
    db_config = config.get('database', {})
    db_path = db_config.get('path', 'data/app.db')
    # 如果是相对路径，转为项目根目录下的绝对路径
    if not os.path.isabs(db_path):
        db_path = os.path.join(project_root, db_path)
    # 确保 data 目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db_uri = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # 生产模式下不显示 SQL 日志
    app.config['SQLALCHEMY_ECHO'] = False

    # 存储配置到 app.config
    app.config['APP_CONFIG'] = config

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db, directory='migrations/alembic')
    limiter.init_app(app)
    # CORS 配置 - 从配置文件读取允许的域名
    cors_config = config.get('cors', {})
    allowed_origins = cors_config.get('allowed_origins', [
        'http://localhost:5001',
        'http://127.0.0.1:5001',
        'https://fuyuhuice.online'
    ])
    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    # 注册蓝图
    from .api.auth import auth_bp
    from .api.positions import positions_bp
    from .api.trades import trades_bp
    from .api.analysis import analysis_bp
    from .api.valuations import valuations_bp
    from .api.backtest import backtest_bp
    from .api.ai import ai_bp
    from .api.configs import configs_bp
    from .api.accounts import accounts_bp
    from .api.imports import imports_bp
    from .api.charts import charts_bp
    from .api.admin import admin_bp
    from .api.datasource import datasource_bp
    from .api.health import health_bp
    from .api.scheduler import scheduler_bp

    app.register_blueprint(auth_bp, url_prefix='/api/v1')
    app.register_blueprint(positions_bp, url_prefix='/api/v1')
    app.register_blueprint(trades_bp, url_prefix='/api/v1')
    app.register_blueprint(analysis_bp, url_prefix='/api/v1')
    app.register_blueprint(valuations_bp, url_prefix='/api/v1')
    app.register_blueprint(backtest_bp, url_prefix='/api/v1')
    app.register_blueprint(ai_bp, url_prefix='/api/v1')
    app.register_blueprint(configs_bp, url_prefix='/api/v1')
    app.register_blueprint(accounts_bp, url_prefix='/api/v1')
    app.register_blueprint(imports_bp, url_prefix='/api/v1')
    app.register_blueprint(charts_bp, url_prefix='/api/v1')
    app.register_blueprint(admin_bp, url_prefix='/api/v1')
    app.register_blueprint(datasource_bp, url_prefix='/api/v1')
    app.register_blueprint(health_bp, url_prefix='/api/v1')  # 健康检查接口
    app.register_blueprint(scheduler_bp, url_prefix='/api/v1')  # 定时任务管理

    # 主页路由 - Vue SPA
    @app.route('/')
    def index():
        from flask import send_file
        index_path = os.path.join(app.template_folder, 'index.html')
        if os.path.exists(index_path):
            return send_file(index_path)
        return "前端未构建，请运行: cd frontend-vue && npm install && npm run build"

    # 所有 404 错误返回 index.html（Vue SPA fallback）
    @app.errorhandler(404)
    def spa_fallback(e):
        from flask import request, send_file
        # API 路由 404 返回 JSON 错误
        if request.path.startswith('/api/'):
            return {'success': False, 'message': '接口不存在'}, 404
        # 静态资源 404 返回空
        if request.path.startswith('/assets/'):
            return '', 404
        # 其他路由返回 index.html（让 Vue Router 处理）
        index_path = os.path.join(app.template_folder, 'index.html')
        if os.path.exists(index_path):
            return send_file(index_path)
        return "前端未构建", 404

    # 初始化定时任务调度器
    try:
        from .services.scheduler_service import init_scheduler
        init_scheduler(app)
        logger.info("定时任务调度器启动成功")
    except Exception as e:
        logger.warning(f"定时任务调度器启动失败: {str(e)}")

    # 清理僵尸任务（服务重启时将running状态的任务标记为interrupted）
    try:
        with app.app_context():
            from .models import AIAnalysisTask, AIAnalysisDimension
            # 查找所有running状态的任务
            running_tasks = AIAnalysisTask.query.filter_by(status='running').all()
            if running_tasks:
                logger.info(f"发现 {len(running_tasks)} 个僵尸任务，正在清理...")
                for task in running_tasks:
                    task.status = 'interrupted'
                    task.error_message = '服务重启，任务被中断'
                    # 将pending状态的维度标记为failed
                    pending_dims = AIAnalysisDimension.query.filter_by(
                        task_id=task.id, status='pending'
                    ).all()
                    for dim in pending_dims:
                        dim.status = 'failed'
                        dim.error_message = '服务中断'
                db.session.commit()
                logger.info(f"僵尸任务清理完成")
    except Exception as e:
        logger.warning(f"僵尸任务清理失败: {str(e)}")

    # 初始化日志中间件（请求日志）
    from .utils.logging import init_request_logging
    init_request_logging(app)

    return app