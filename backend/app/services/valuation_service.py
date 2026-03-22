#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
估值计算服务
"""

from typing import Dict, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass


class ValuationLevel(Enum):
    """估值等级"""
    EXTREMELY_LOW = "极度低估"
    LOW = "低估"
    REASONABLE_LOW = "合理偏低"
    REASONABLE = "合理"
    REASONABLE_HIGH = "合理偏高"
    HIGH = "高估"
    EXTREMELY_HIGH = "极度高估"


@dataclass
class ValuationResult:
    """估值判断结果"""
    level: ValuationLevel
    score: float
    position_suggestion: int
    action: str
    details: str


class ValuationService:
    """估值判断服务"""

    # 主要指数估值参考标准
    INDEX_REFERENCE = {
        "沪深300": {
            "pe_extremely_low": 10,
            "pe_low": 12,
            "pe_reasonable": 14,
            "pe_high": 16,
            "pe_extremely_high": 18,
        },
        "中证500": {
            "pe_extremely_low": 16,
            "pe_low": 20,
            "pe_reasonable": 25,
            "pe_high": 30,
            "pe_extremely_high": 35,
        },
        "创业板指": {
            "pe_extremely_low": 25,
            "pe_low": 32,
            "pe_reasonable": 40,
            "pe_high": 50,
            "pe_extremely_high": 60,
        },
        "中证1000": {
            "pe_extremely_low": 20,
            "pe_low": 25,
            "pe_reasonable": 32,
            "pe_high": 40,
            "pe_extremely_high": 50,
        },
        "上证50": {
            "pe_extremely_low": 8,
            "pe_low": 10,
            "pe_reasonable": 12,
            "pe_high": 14,
            "pe_extremely_high": 16,
        },
        "科创50": {
            "pe_extremely_low": 30,
            "pe_low": 40,
            "pe_reasonable": 50,
            "pe_high": 60,
            "pe_extremely_high": 80,
        },
    }

    # 估值等级对应的仓位建议
    POSITION_SUGGESTIONS = {
        ValuationLevel.EXTREMELY_LOW: (90, 100, "极度低估，建议满仓买入"),
        ValuationLevel.LOW: (70, 90, "低估，建议加大买入"),
        ValuationLevel.REASONABLE_LOW: (50, 70, "合理偏低，可正常买入"),
        ValuationLevel.REASONABLE: (40, 50, "合理，可持有或小额定投"),
        ValuationLevel.REASONABLE_HIGH: (20, 30, "合理偏高，建议减仓"),
        ValuationLevel.HIGH: (10, 20, "高估，建议大幅减仓"),
        ValuationLevel.EXTREMELY_HIGH: (0, 10, "极度高估，建议清仓"),
    }

    # 百分位阈值
    PERCENTILE_THRESHOLDS = {
        "extremely_low": 10,
        "low": 30,
        "reasonable": 50,
        "reasonable_high": 70,
        "high": 90,
    }

    def evaluate(
        self,
        index_name: str,
        pe: Optional[float] = None,
        pb: Optional[float] = None,
        pe_percentile: Optional[float] = None,
        pb_percentile: Optional[float] = None,
        rsi: Optional[float] = None
    ) -> ValuationResult:
        """
        评估估值等级

        Args:
            index_name: 指数名称
            pe: 市盈率
            pb: 市净率
            pe_percentile: PE历史百分位
            pb_percentile: PB历史百分位
            rsi: RSI指标

        Returns:
            ValuationResult: 评估结果
        """
        score = self._calculate_score(pe_percentile, pb_percentile, rsi)
        level = self._determine_level(score, pe_percentile, pb_percentile)
        pos_min, pos_max, action = self.POSITION_SUGGESTIONS[level]

        details = self._generate_details(
            index_name, pe, pb, pe_percentile, pb_percentile, rsi, level, score
        )

        return ValuationResult(
            level=level,
            score=score,
            position_suggestion=(pos_min + pos_max) // 2,
            action=action,
            details=details
        )

    def _calculate_score(
        self,
        pe_percentile: Optional[float],
        pb_percentile: Optional[float],
        rsi: Optional[float]
    ) -> float:
        """
        计算综合估值评分

        评分规则：
        - PE百分位权重50%
        - PB百分位权重30%
        - RSI权重20%（可选）

        返回0-100分，分数越低越低估
        """
        scores = []
        weights = []

        if pe_percentile is not None:
            scores.append(pe_percentile)
            weights.append(0.5)

        if pb_percentile is not None:
            scores.append(pb_percentile)
            weights.append(0.3)

        if rsi is not None:
            scores.append(rsi)
            weights.append(0.2)

        if not scores:
            return 50

        total_weight = sum(weights)
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight

        return round(weighted_score, 2)

    def _determine_level(
        self,
        score: float,
        pe_percentile: Optional[float],
        pb_percentile: Optional[float]
    ) -> ValuationLevel:
        """确定估值等级"""
        percentile = pe_percentile or pb_percentile or score

        if percentile < self.PERCENTILE_THRESHOLDS["extremely_low"]:
            return ValuationLevel.EXTREMELY_LOW
        elif percentile < self.PERCENTILE_THRESHOLDS["low"]:
            return ValuationLevel.LOW
        elif percentile < 40:
            return ValuationLevel.REASONABLE_LOW
        elif percentile < self.PERCENTILE_THRESHOLDS["reasonable"]:
            return ValuationLevel.REASONABLE
        elif percentile < self.PERCENTILE_THRESHOLDS["reasonable_high"]:
            return ValuationLevel.REASONABLE_HIGH
        elif percentile < self.PERCENTILE_THRESHOLDS["high"]:
            return ValuationLevel.HIGH
        else:
            return ValuationLevel.EXTREMELY_HIGH

    def _generate_details(
        self,
        index_name: str,
        pe: Optional[float],
        pb: Optional[float],
        pe_percentile: Optional[float],
        pb_percentile: Optional[float],
        rsi: Optional[float],
        level: ValuationLevel,
        score: float
    ) -> str:
        """生成详细说明"""
        parts = [f"指数：{index_name}"]
        parts.append(f"估值等级：{level.value}")
        parts.append(f"综合评分：{score:.1f}分（越低越低估）")

        if pe is not None:
            parts.append(f"PE：{pe:.2f}")
        if pe_percentile is not None:
            parts.append(f"PE百分位：{pe_percentile:.1f}%")
        if pb is not None:
            parts.append(f"PB：{pb:.2f}")
        if pb_percentile is not None:
            parts.append(f"PB百分位：{pb_percentile:.1f}%")
        if rsi is not None:
            parts.append(f"RSI：{rsi:.1f}")

        return " | ".join(parts)

    def get_index_reference(self, index_name: str) -> Optional[Dict]:
        """获取指数估值参考标准"""
        return self.INDEX_REFERENCE.get(index_name)

    def list_supported_indices(self) -> List[str]:
        """列出支持的指数"""
        return list(self.INDEX_REFERENCE.keys())