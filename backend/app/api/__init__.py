#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 模块初始化
"""

from .positions import positions_bp
from .trades import trades_bp
from .analysis import analysis_bp
from .valuations import valuations_bp
from .backtest import backtest_bp
from .ai import ai_bp
from .configs import configs_bp
from .accounts import accounts_bp
from .imports import imports_bp
from .charts import charts_bp
from .datasource import datasource_bp

__all__ = [
    'positions_bp',
    'trades_bp',
    'analysis_bp',
    'valuations_bp',
    'backtest_bp',
    'ai_bp',
    'configs_bp',
    'accounts_bp',
    'imports_bp',
    'charts_bp',
    'datasource_bp'
]