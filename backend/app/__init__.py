#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask 应用工厂
"""

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import yaml
import os
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
    app = Flask(__name__,
                template_folder='../../frontend',
                static_folder='../../frontend',
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

    # 数据库配置
    db_config = config.get('database', {})
    db_uri = f"mysql+pymysql://{db_config.get('user', 'root')}:{db_config.get('password', '')}@" \
             f"{db_config.get('host', 'localhost')}:{db_config.get('port', 3306)}/" \
             f"{db_config.get('database', 'myapp')}?charset={db_config.get('charset', 'utf8mb4')}"
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
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
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

    # 主页路由
    @app.route('/')
    def index():
        from flask import send_from_directory
        return send_from_directory('../../frontend', 'index.html')

    # 初始化定时任务调度器
    try:
        from .services.scheduler_service import init_scheduler
        init_scheduler(app)
        logger.info("定时任务调度器启动成功")
    except Exception as e:
        logger.warning(f"定时任务调度器启动失败: {str(e)}")

    # 初始化日志中间件（请求日志）
    from .utils.logging import init_request_logging
    init_request_logging(app)

    return app