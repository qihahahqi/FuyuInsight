#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 分析异步任务服务
支持后台执行、增量保存、进度查询
"""

import threading
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask import Flask

logger = logging.getLogger(__name__)


class AIAnalysisTaskService:
    """AI 分析异步任务服务"""

    def __init__(self):
        self._tasks = {}  # task_id -> 线程对象
        self._stop_flags = {}  # task_id -> stop_flag

    def start_task(self, app: Flask, user_id: int, analysis_type: str,
                   dimensions: List[str], position_id: Optional[int] = None,
                   symbol: Optional[str] = None, model_provider: str = 'openai',
                   model_name: str = 'gpt-4') -> Dict[str, Any]:
        """
        启动异步分析任务

        Args:
            app: Flask 应用实例
            user_id: 用户 ID
            analysis_type: 分析类型 (single/portfolio)
            dimensions: 分析维度列表
            position_id: 持仓 ID（单标的分析时）
            symbol: 标的代码（单标的分析时）
            model_provider: 模型提供商
            model_name: 模型名称

        Returns:
            启动状态和任务信息
        """
        from .. import db
        from ..models import AIAnalysisTask, AIAnalysisDimension

        with app.app_context():
            # 创建任务记录
            task = AIAnalysisTask(
                user_id=user_id,
                analysis_type=analysis_type,
                position_id=position_id,
                symbol=symbol,
                dimensions=json.dumps(dimensions, ensure_ascii=False),
                status='pending',
                progress=0,
                total_dimensions=len(dimensions),
                model_provider=model_provider,
                model_name=model_name
            )
            db.session.add(task)
            db.session.commit()

            task_id = task.id

            # 创建维度记录（初始状态为 pending）
            for dim in dimensions:
                dim_record = AIAnalysisDimension(
                    task_id=task_id,
                    dimension=dim,
                    status='pending'
                )
                db.session.add(dim_record)
            db.session.commit()

        # 启动后台线程
        stop_flag = threading.Event()
        self._stop_flags[task_id] = stop_flag

        thread = threading.Thread(
            target=self._run_analysis_loop,
            args=(app, task_id, user_id, analysis_type, dimensions, position_id, symbol, model_provider, model_name, stop_flag),
            daemon=True
        )
        thread.start()
        self._tasks[task_id] = thread

        logger.info(f"[AI分析] 任务 {task_id} 已启动: type={analysis_type}, dimensions={dimensions}")

        return {
            'success': True,
            'task_id': task_id,
            'status': 'pending',
            'message': '分析任务已启动',
            'progress': 0,
            'total_dimensions': len(dimensions)
        }

    def _run_analysis_loop(self, app: Flask, task_id: int, user_id: int,
                           analysis_type: str, dimensions: List[str],
                           position_id: Optional[int], symbol: Optional[str],
                           model_provider: str, model_name: str,
                           stop_flag: threading.Event):
        """
        后台分析循环 - 逐维度执行并增量保存
        """
        from .. import db
        from ..models import AIAnalysisTask, AIAnalysisDimension, Position, Valuation, Trade, Config
        from .llm_service import LLMService
        from ..utils.config import config_manager

        with app.app_context():
            try:
                # 更新任务状态为 running
                task = AIAnalysisTask.query.get(task_id)
                if not task:
                    return

                task.status = 'running'
                task.updated_at = datetime.utcnow()
                db.session.commit()

                logger.info(f"[AI分析] 任务 {task_id} 开始执行")

                # 获取 LLM 配置
                llm_config = config_manager.llm_config.copy()
                config_keys = ['api_key', 'api_base', 'temperature', 'max_tokens']
                for key in config_keys:
                    db_config = Config.query.filter_by(key=f'llm.{key}', user_id=user_id).first()
                    if db_config:
                        if key == 'temperature':
                            try:
                                llm_config[key] = float(db_config.value)
                            except:
                                pass
                        elif key == 'max_tokens':
                            try:
                                llm_config[key] = int(db_config.value)
                            except:
                                pass
                        else:
                            llm_config[key] = db_config.value

                # 获取用户的 API Key
                api_key_config = Config.query.filter_by(key='llm.api_key', user_id=user_id).first()
                api_key = api_key_config.value if api_key_config else llm_config.get('api_key')

                if not api_key:
                    task.status = 'failed'
                    task.error_message = '未配置 API Key'
                    task.updated_at = datetime.utcnow()
                    db.session.commit()
                    logger.error(f"[AI分析] 任务 {task_id} 失败: 未配置 API Key")
                    return

                # 创建 LLM 服务
                llm_service = LLMService(
                    provider=model_provider or llm_config.get('provider', 'openai'),
                    api_key=api_key,
                    api_base=llm_config.get('api_base', ''),
                    model=model_name or llm_config.get('model', 'gpt-4'),
                    temperature=llm_config.get('temperature', 0.7),
                    max_tokens=llm_config.get('max_tokens', 2000)
                )

                # 收集数据
                positions = []
                valuations = []
                trades = []

                if analysis_type == 'single' and position_id:
                    position = Position.query.filter_by(id=position_id, user_id=user_id).first()
                    if position:
                        positions = [position.to_dict()]
                        position_trades = Trade.query.filter_by(
                            user_id=user_id, symbol=position.symbol
                        ).order_by(Trade.trade_date.desc()).limit(20).all()
                        trades = [t.to_dict() for t in position_trades]
                else:
                    positions = [p.to_dict() for p in Position.query.filter_by(user_id=user_id).all()]
                    valuations = [v.to_dict() for v in Valuation.query.filter_by(user_id=user_id).order_by(Valuation.record_date.desc()).limit(10).all()]
                    trades = [t.to_dict() for t in Trade.query.filter_by(user_id=user_id).order_by(Trade.trade_date.desc()).limit(20).all()]

                # 逐维度分析
                completed_count = 0
                total_score = 0
                score_count = 0

                for dim in dimensions:
                    # 检查是否被取消
                    if stop_flag.is_set():
                        task.status = 'cancelled'
                        task.error_message = '用户取消'
                        task.updated_at = datetime.utcnow()
                        db.session.commit()
                        logger.info(f"[AI分析] 任务 {task_id} 已取消")
                        return

                    # 更新当前维度
                    task.current_dimension = dim
                    task.updated_at = datetime.utcnow()
                    db.session.commit()

                    logger.info(f"[AI分析] 任务 {task_id} 开始分析维度: {dim}")

                    # 获取维度记录
                    dim_record = AIAnalysisDimension.query.filter_by(task_id=task_id, dimension=dim).first()
                    if dim_record:
                        dim_record.status = 'running'
                        dim_record.updated_at = datetime.utcnow()
                        db.session.commit()

                    try:
                        # 调用 LLM
                        if analysis_type == 'single':
                            result = llm_service.analyze_single_position(
                                position=positions[0] if positions else {},
                                trades=trades,
                                dimensions=[dim]
                            )
                            if result.get(dim):
                                analysis_text = result[dim].get('analysis', '')
                                score = result[dim].get('score')
                            else:
                                analysis_text = ''
                                score = None
                        else:
                            result = llm_service.analyze_portfolio_by_dimension(
                                positions=positions,
                                valuations=valuations,
                                trades=trades,
                                strategy_params=config_manager.strategy_config,
                                dimension=dim
                            )
                            if result.get('success'):
                                analysis_text = result.get('analysis', '')
                                # 提取评分
                                from ..api.ai import extract_score_from_analysis
                                score = extract_score_from_analysis(analysis_text)
                            else:
                                analysis_text = f"分析失败: {result.get('error', '未知错误')}"
                                score = None

                        # 保存维度结果
                        if dim_record:
                            dim_record.status = 'completed'
                            dim_record.analysis = analysis_text
                            dim_record.score = score
                            dim_record.updated_at = datetime.utcnow()
                            db.session.commit()

                        completed_count += 1
                        task.progress = completed_count

                        if score:
                            total_score += score
                            score_count += 1

                        logger.info(f"[AI分析] 任务 {task_id} 维度 {dim} 完成: score={score}")

                    except Exception as e:
                        logger.error(f"[AI分析] 任务 {task_id} 维度 {dim} 失败: {str(e)}")
                        if dim_record:
                            dim_record.status = 'failed'
                            dim_record.error_message = str(e)
                            dim_record.updated_at = datetime.utcnow()
                            db.session.commit()

                        completed_count += 1
                        task.progress = completed_count

                # 计算综合评分
                overall_score = int(total_score / score_count) if score_count > 0 else None

                # 更新任务完成状态
                task.status = 'completed'
                task.progress = len(dimensions)
                task.overall_score = overall_score
                task.current_dimension = None
                task.completed_at = datetime.utcnow()
                task.updated_at = datetime.utcnow()
                db.session.commit()

                logger.info(f"[AI分析] 任务 {task_id} 完成: overall_score={overall_score}")

            except Exception as e:
                logger.error(f"[AI分析] 任务 {task_id} 异常: {str(e)}")
                try:
                    task = AIAnalysisTask.query.get(task_id)
                    if task:
                        task.status = 'failed'
                        task.error_message = str(e)
                        task.updated_at = datetime.utcnow()
                        db.session.commit()
                except:
                    pass

    def get_task_status(self, task_id: int) -> Dict[str, Any]:
        """获取任务状态"""
        from ..models import AIAnalysisTask, AIAnalysisDimension

        task = AIAnalysisTask.query.get(task_id)
        if not task:
            return {
                'success': False,
                'error': '任务不存在'
            }

        # 获取各维度状态
        dimensions_status = {}
        dim_records = AIAnalysisDimension.query.filter_by(task_id=task_id).all()
        for dim in dim_records:
            dimensions_status[dim.dimension] = {
                'status': dim.status,
                'score': dim.score,
                'has_analysis': bool(dim.analysis)
            }

        return {
            'success': True,
            'task_id': task_id,
            'status': task.status,
            'progress': task.progress,
            'total_dimensions': task.total_dimensions,
            'progress_percentage': task.get_progress_percentage(),
            'current_dimension': task.current_dimension,
            'overall_score': task.overall_score,
            'dimensions_status': dimensions_status,
            'error_message': task.error_message,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'updated_at': task.updated_at.isoformat() if task.updated_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None
        }

    def get_task_result(self, task_id: int) -> Dict[str, Any]:
        """获取完整分析结果"""
        from ..models import AIAnalysisTask, AIAnalysisDimension

        task = AIAnalysisTask.query.get(task_id)
        if not task:
            return {
                'success': False,
                'error': '任务不存在'
            }

        # 获取各维度结果
        dimensions_result = {}
        dim_records = AIAnalysisDimension.query.filter_by(task_id=task_id).all()
        for dim in dim_records:
            dimensions_result[dim.dimension] = {
                'status': dim.status,
                'score': dim.score,
                'analysis': dim.analysis,
                'error_message': dim.error_message
            }

        return {
            'success': True,
            'task_id': task_id,
            'analysis_type': task.analysis_type,
            'symbol': task.symbol,
            'position_id': task.position_id,
            'dimensions': json.loads(task.dimensions) if task.dimensions else [],
            'status': task.status,
            'overall_score': task.overall_score,
            'model_provider': task.model_provider,
            'model_name': task.model_name,
            'dimensions_result': dimensions_result,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None
        }

    def get_user_tasks(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """获取用户任务列表"""
        from ..models import AIAnalysisTask

        tasks = AIAnalysisTask.query.filter_by(user_id=user_id).order_by(
            AIAnalysisTask.created_at.desc()
        ).limit(limit).all()

        return [t.to_dict() for t in tasks]

    def cancel_task(self, task_id: int) -> Dict[str, Any]:
        """取消任务"""
        from ..models import AIAnalysisTask

        task = AIAnalysisTask.query.get(task_id)
        if not task:
            return {
                'success': False,
                'error': '任务不存在'
            }

        if task.status not in ['pending', 'running']:
            return {
                'success': False,
                'error': f'任务状态为 {task.status}, 无法取消'
            }

        # 设置停止标志
        if task_id in self._stop_flags:
            self._stop_flags[task_id].set()

        # 更新状态（如果线程还没处理）
        if task.status == 'pending':
            task.status = 'cancelled'
            task.error_message = '用户取消'
            task.updated_at = datetime.utcnow()

        logger.info(f"[AI分析] 任务 {task_id} 用户请求取消")

        return {
            'success': True,
            'message': '取消请求已发送',
            'task_id': task_id
        }

    def delete_task(self, task_id: int) -> Dict[str, Any]:
        """删除任务及其维度结果"""
        from .. import db
        from ..models import AIAnalysisTask

        task = AIAnalysisTask.query.get(task_id)
        if not task:
            return {
                'success': False,
                'error': '任务不存在'
            }

        # 只能删除已完成/失败/取消的任务
        if task.status in ['pending', 'running']:
            return {
                'success': False,
                'error': '任务正在运行，请先取消'
            }

        db.session.delete(task)
        db.session.commit()

        # 清理内存中的引用
        if task_id in self._tasks:
            del self._tasks[task_id]
        if task_id in self._stop_flags:
            del self._stop_flags[task_id]

        logger.info(f"[AI分析] 任务 {task_id} 已删除")

        return {
            'success': True,
            'message': '任务已删除'
        }


# 全局服务实例
ai_task_service = AIAnalysisTaskService()