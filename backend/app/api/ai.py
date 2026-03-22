#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 分析 API
"""

from flask import Blueprint, request
from .. import db
from ..models import Position, Valuation, Trade, Config, AIAnalysisHistory
from ..utils import success_response, error_response
from ..utils.decorators import login_required, get_current_user
from ..services import LLMService
from ..utils.config import config_manager
import json
from datetime import datetime

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/ai/status', methods=['GET'])
@login_required
def get_ai_status():
    """获取 AI 配置状态"""
    try:
        user = get_current_user()
        llm_config = config_manager.llm_config.copy()

        # 从数据库读取用户级别的配置
        config_keys = ['enabled', 'provider', 'model', 'api_base']
        for key in config_keys:
            db_config = Config.query.filter_by(key=f'llm.{key}', user_id=user.id).first()
            if db_config:
                value = db_config.value
                if key == 'enabled':
                    value = value.lower() == 'true' if isinstance(value, str) else bool(value)
                llm_config[key] = value

        # 检查用户级别的 API Key
        api_key_config = Config.query.filter_by(key='llm.api_key', user_id=user.id).first()
        has_api_key = bool(api_key_config and api_key_config.value) or bool(llm_config.get('api_key'))

        return success_response({
            'enabled': llm_config.get('enabled', False),
            'provider': llm_config.get('provider', ''),
            'model': llm_config.get('model', ''),
            'configured': has_api_key
        })
    except Exception as e:
        return error_response(str(e))


@ai_bp.route('/ai/providers', methods=['GET'])
@login_required
def get_providers():
    """获取支持的提供商列表"""
    try:
        providers = LLMService.get_supported_providers()
        return success_response(providers)
    except Exception as e:
        return error_response(str(e))


@ai_bp.route('/ai/dimensions', methods=['GET'])
@login_required
def get_dimensions():
    """获取可用的分析维度列表"""
    dimensions = [
        {'key': 'market', 'name': '市场分析', 'icon': '📊', 'description': '大盘走势、市场情绪、宏观政策影响'},
        {'key': 'fundamentals', 'name': '基本面分析', 'icon': '💰', 'description': 'PE/PB/ROE等财务指标评估'},
        {'key': 'technical', 'name': '技术分析', 'icon': '📈', 'description': '均线系统、MACD、RSI等技术指标'},
        {'key': 'capital_flow', 'name': '资金面分析', 'icon': '💵', 'description': '主力资金、北向资金、换手率'},
        {'key': 'sector', 'name': '板块分析', 'icon': '🏭', 'description': '行业表现、板块轮动、同业对比'},
        {'key': 'trader_plan', 'name': '交易员计划', 'icon': '💼', 'description': '具体买卖建议、目标价、止损位'},
        {'key': 'market_overview', 'name': '大盘分析', 'icon': '📊', 'description': '上证/深证/创业板整体走势'},
        {'key': 'news', 'name': '新闻分析', 'icon': '📰', 'description': '近期公告、行业新闻、政策影响'},
        {'key': 'bull_view', 'name': '多头观点', 'icon': '🐂', 'description': '看涨论据、催化剂、历史类比'},
        {'key': 'bear_view', 'name': '空头观点', 'icon': '🐻', 'description': '看跌风险、潜在危机、反面案例'},
        {'key': 'verdict', 'name': '综合裁决', 'icon': '⚖️', 'description': '多空辩论总结、最终建议'},
        {'key': 'aggressive', 'name': '激进策略', 'icon': '⚡', 'description': '高风险高收益方案'},
        {'key': 'conservative', 'name': '保守策略', 'icon': '🛡️', 'description': '低风险稳健方案'},
        {'key': 'neutral', 'name': '中性策略', 'icon': '⚖️', 'description': '平衡方案、动态调整机制'},
        {'key': 'investment_advice', 'name': '投资建议', 'icon': '📋', 'description': '综合评分、目标价、止损止盈'}
    ]
    return success_response(dimensions)


@ai_bp.route('/ai/test', methods=['POST'])
@login_required
def test_connection():
    """测试 AI 连接"""
    try:
        user = get_current_user()
        data = request.get_json() or {}

        # 从请求或配置获取参数
        llm_config = config_manager.llm_config

        provider = data.get('provider') or llm_config.get('provider', 'openai')
        api_key = data.get('api_key')
        api_base = data.get('api_base') or llm_config.get('api_base', '')
        model = data.get('model') or llm_config.get('model', 'gpt-4')

        # 从数据库获取用户的 API Key
        if not api_key or api_key == '******':
            api_key_config = Config.query.filter_by(key='llm.api_key', user_id=user.id).first()
            api_key = api_key_config.value if api_key_config else llm_config.get('api_key', '')

        if not api_key:
            return error_response("请配置 API Key")

        service = LLMService(
            provider=provider,
            api_key=api_key,
            api_base=api_base,
            model=model
        )

        result = service.test_connection()

        if result['success']:
            return success_response(result)
        else:
            return error_response(result['message'])
    except Exception as e:
        return error_response(str(e))


@ai_bp.route('/ai/analyze', methods=['POST'])
@login_required
def analyze():
    """AI 分析（支持单标的/全仓，多维度）"""
    try:
        user = get_current_user()
        data = request.get_json() or {}

        # 获取分析参数
        analysis_type = data.get('analysis_type', 'portfolio')  # single 或 portfolio
        position_id = data.get('position_id')  # 单标的分析时的持仓ID

        # 可用维度列表（扩展后）
        all_dimensions = [
            'market', 'fundamentals', 'technical', 'capital_flow', 'sector',
            'trader_plan', 'market_overview', 'news', 'bull_view', 'bear_view',
            'verdict', 'aggressive', 'conservative', 'neutral', 'investment_advice'
        ]

        # 默认维度（核心分析）
        default_dimensions = [
            'trader_plan', 'market_overview', 'technical', 'fundamentals',
            'bull_view', 'bear_view', 'verdict', 'investment_advice'
        ]

        # 如果请求中指定了维度，使用指定的；否则使用默认
        requested_dimensions = data.get('dimensions')
        if requested_dimensions:
            # 验证维度是否有效
            dimensions = [d for d in requested_dimensions if d in all_dimensions]
        else:
            dimensions = default_dimensions

        # 获取LLM配置
        llm_config = config_manager.llm_config.copy()
        config_keys = ['enabled', 'provider', 'model', 'api_base', 'temperature', 'max_tokens']
        for key in config_keys:
            db_config = Config.query.filter_by(key=f'llm.{key}', user_id=user.id).first()
            if db_config:
                value = db_config.value
                if key == 'enabled':
                    value = value.lower() == 'true' if isinstance(value, str) else bool(value)
                elif key in ['temperature', 'max_tokens']:
                    try:
                        value = float(value) if key == 'temperature' else int(value)
                    except:
                        pass
                llm_config[key] = value

        if not llm_config.get('enabled'):
            return error_response("AI 分析功能未启用，请在配置中开启")

        # 获取用户的 API Key
        api_key_config = Config.query.filter_by(key='llm.api_key', user_id=user.id).first()
        api_key = api_key_config.value if api_key_config else llm_config.get('api_key')

        if not api_key:
            return error_response("请先配置 API Key")

        # 创建服务实例
        service = LLMService(
            provider=llm_config.get('provider', 'openai'),
            api_key=api_key,
            api_base=llm_config.get('api_base', ''),
            model=llm_config.get('model', 'gpt-4'),
            temperature=llm_config.get('temperature', 0.7),
            max_tokens=llm_config.get('max_tokens', 2000)
        )

        result_data = {}
        overall_score = None

        if analysis_type == 'single' and position_id:
            # 单标的分析
            position = Position.query.filter_by(id=position_id, user_id=user.id).first()
            if not position:
                return error_response("持仓不存在")

            # 获取该标的的交易记录
            trades = Trade.query.filter_by(
                user_id=user.id,
                symbol=position.symbol
            ).order_by(Trade.trade_date.desc()).limit(20).all()

            # 执行多维度分析
            dimension_results = service.analyze_single_position(
                position=position.to_dict(),
                trades=[t.to_dict() for t in trades],
                dimensions=dimensions
            )

            result_data = {
                'analysis_type': 'single',
                'symbol': position.symbol,
                'dimensions': dimension_results
            }

            # 计算综合评分
            scores = [r.get('score', 0) for r in dimension_results.values() if r.get('score')]
            overall_score = int(sum(scores) / len(scores)) if scores else None

        else:
            # 全仓分析
            positions = Position.query.filter_by(user_id=user.id).all()
            if not positions:
                return error_response("暂无持仓数据，请先添加持仓")

            valuations = Valuation.query.filter_by(user_id=user.id).order_by(Valuation.record_date.desc()).limit(10).all()
            trades = Trade.query.filter_by(user_id=user.id).order_by(Trade.trade_date.desc()).limit(20).all()

            # 执行全仓分析
            analysis_result = service.analyze_portfolio(
                positions=[p.to_dict() for p in positions],
                valuations=[v.to_dict() for v in valuations],
                trades=[t.to_dict() for t in trades],
                strategy_params=config_manager.strategy_config
            )

            if not analysis_result.get('success'):
                return error_response(analysis_result.get('error', '分析失败'))

            result_data = {
                'analysis_type': 'portfolio',
                'analysis': analysis_result['analysis']
            }

        # 保存分析历史
        history = AIAnalysisHistory(
            user_id=user.id,
            position_id=position_id if analysis_type == 'single' else None,
            analysis_type=analysis_type,
            symbol=position.symbol if analysis_type == 'single' and position else None,
            dimensions=json.dumps(dimensions, ensure_ascii=False),
            analysis_content=json.dumps(result_data, ensure_ascii=False),
            overall_score=overall_score,
            model_provider=llm_config.get('provider', ''),
            model_name=llm_config.get('model', '')
        )
        db.session.add(history)
        db.session.commit()

        result_data['id'] = history.id
        if overall_score:
            result_data['overall_score'] = overall_score

        return success_response(result_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(str(e))


@ai_bp.route('/ai/history', methods=['GET'])
@login_required
def get_analysis_history():
    """获取AI分析历史记录"""
    try:
        user = get_current_user()

        history = AIAnalysisHistory.query.filter_by(user_id=user.id).order_by(
            AIAnalysisHistory.created_at.desc()
        ).limit(20).all()

        return success_response([{
            'id': h.id,
            'analysis_type': h.analysis_type,
            'symbol': h.symbol,
            'overall_score': h.overall_score,
            'model_name': h.model_name,
            'created_at': h.created_at.isoformat() if h.created_at else None
        } for h in history])
    except Exception as e:
        return error_response(str(e))


@ai_bp.route('/ai/history/<int:history_id>', methods=['GET'])
@login_required
def get_analysis_detail(history_id):
    """获取AI分析历史详情"""
    try:
        user = get_current_user()

        history = AIAnalysisHistory.query.filter_by(id=history_id, user_id=user.id).first()
        if not history:
            return error_response("记录不存在", 404)

        result = history.to_dict()
        # 解析JSON内容
        if result.get('analysis_content'):
            try:
                result['analysis_content'] = json.loads(result['analysis_content'])
            except:
                pass
        if result.get('dimensions'):
            try:
                result['dimensions'] = json.loads(result['dimensions'])
            except:
                pass

        return success_response(result)
    except Exception as e:
        return error_response(str(e))