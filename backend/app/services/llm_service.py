#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型分析服务
"""

from typing import Dict, List, Optional
import json


class LLMService:
    """大模型分析服务"""

    SUPPORTED_PROVIDERS = {
        "openai": {
            "name": "OpenAI",
            "models": ["gpt-5", "gpt-5-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"],
            "default_base": "https://api.openai.com/v1"
        },
        "anthropic": {
            "name": "Anthropic",
            "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-3-5-sonnet-20241022"],
            "default_base": "https://api.anthropic.com"
        },
        "deepseek": {
            "name": "DeepSeek",
            "models": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
            "default_base": "https://api.deepseek.com"
        },
        "bailian": {
            "name": "百炼",
            "models": ["qwen-turbo", "qwen3.5-plus", "qwen3.5-max", "qwen-max-longcontext", "qwen2.5-plus", "qwen3.5-plus"],
            "default_base": "https://dashscope.aliyuncs.com/compatible-mode/v1"
        },
        "qwen": {
            "name": "通义千问",
            "models": ["qwen3.5-turbo", "qwen3.5-plus", "qwen-max", "qwen2.5-plus", "qwen3.5-plus"],
            "default_base": "https://dashscope.aliyuncs.com/compatible-mode/v1"
        },
        "glm": {
            "name": "智谱GLM",
            "models": ["glm-5", "glm-5-flash", "glm-5-air", "glm-4-plus", "glm-5", "glm-3-turbo"],
            "default_base": "https://open.bigmodel.cn/api/paas/v4"
        },
        "bailian-anthropic": {
            "name": "百炼(Anthropic兼容)",
            "models": ["qwen3.5-turbo", "qwen3.5-plus", "qwen-max", "qwen2.5-plus", "qwen3.5-plus", "glm-5", "deepseek-chat"],
            "default_base": "https://dashscope.aliyuncs.com/apps/anthropic"
        },
        "minimax": {
            "name": "MiniMax",
            "models": ["abab6.5-chat", "abab5.5-chat", "abab5.5s-chat"],
            "default_base": "https://api.minimax.chat/v1"
        },
        "custom": {
            "name": "自定义",
            "models": [],
            "default_base": ""
        }
    }

    ANALYSIS_PROMPT_TEMPLATE = """你是一位资深的投资顾问，擅长价值投资和风险控制。请基于以下持仓数据进行专业分析。

## 持仓概况
{positions_summary}

## 市场估值数据
{valuation_data}

## 近期交易记录
{recent_trades}

## 策略参数
{strategy_params}

---

请严格按照以下格式输出分析报告（使用Markdown格式）：

## 📊 持仓结构诊断

**当前配置比例：**
- 列出每个持仓的市值占比（精确到0.1%）
- 评估配置是否合理（参考标准：单一标的不超过30%，单一类型不超过50%）

**存在的问题：**
- 具体指出当前持仓的1-3个核心问题
- 用数据说话，避免空泛描述

---

## ⚠️ 风险等级评估

**风险评分：** [低/中/高] （根据集中度、波动率、浮亏情况综合判定）

**风险来源：**
| 风险点 | 影响程度 | 说明 |
|--------|----------|------|
| 具体风险项 | 高/中/低 | 详细说明 |

**最大潜在损失预估：** 基于当前市场环境，预估可能的下跌空间

---

## 💡 具体操作建议

**立即行动项（建议在3个交易日内执行）：**
1. [具体标的] → [买入/卖出/持有/转换] → 建议仓位调整至 XX%
2. ...

**观望等待项：**
- 列出需要等待确认信号的操作

**止损/止盈价位：**
| 标的 | 止损价(跌幅) | 止盈价(涨幅) | 当前状态 |
|------|-------------|-------------|----------|
| 代码 | 价格(%) | 价格(%) | 距离止损/止盈的距离 |

---

## 📈 长期优化方案

**推荐配置模型（建议在3-6个月内逐步调整到位）：**
```
核心仓位（60%）：宽基指数基金，如沪深300、中证500
卫星仓位（25%）：行业主题/主动基金
现金/债券（15%）：流动性储备
```

**定投策略建议：**
- 推荐定投标的及金额
- 定投频率（周定投/月定投）

**需要关注的指标：**
- 列出3-5个需要定期跟踪的指标或信号

---

## 🎯 本周行动清单

- [ ] 行动项1：具体可执行的操作
- [ ] 行动项2：...
- [ ] 行动项3：...

---
*分析仅供参考，投资有风险，决策需谨慎。*"""

    def __init__(
        self,
        provider: str = "openai",
        api_key: str = "",
        api_base: str = "",
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        self.provider = provider
        self.api_key = api_key
        self.api_base = api_base or self.SUPPORTED_PROVIDERS.get(provider, {}).get("default_base", "")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None

    def _get_client(self):
        """获取API客户端"""
        if self._client is not None:
            return self._client

        if not self.api_key:
            raise ValueError("API Key 未配置")

        try:
            # OpenAI 兼容的提供商
            openai_compatible = ["openai", "deepseek", "custom", "bailian", "qwen", "glm", "minimax"]
            if self.provider in openai_compatible:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base if self.api_base else None
                )
            elif self.provider == "bailian-anthropic":
                # 百炼 Anthropic 兼容格式
                import anthropic
                self._client = anthropic.Anthropic(
                    api_key=self.api_key,
                    base_url=self.api_base
                )
            elif self.provider == "anthropic":
                import anthropic
                self._client = anthropic.Anthropic(
                    api_key=self.api_key
                )
            else:
                raise ValueError(f"不支持的提供商: {self.provider}")

            return self._client
        except ImportError as e:
            raise ImportError(f"请安装相关依赖: {e}")

    def test_connection(self) -> Dict:
        """测试连接"""
        try:
            client = self._get_client()
            openai_compatible = ["openai", "deepseek", "custom", "bailian", "qwen", "glm", "minimax"]
            if self.provider in openai_compatible:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                return {
                    "success": True,
                    "message": "连接成功",
                    "model": self.model
                }
            elif self.provider in ["anthropic", "bailian-anthropic"]:
                response = client.messages.create(
                    model=self.model,
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Hello"}]
                )
                # 处理返回内容
                content_parts = []
                for block in response.content:
                    if hasattr(block, 'text'):
                        content_parts.append(block.text)
                return {
                    "success": True,
                    "message": "连接成功",
                    "model": self.model
                }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "model": self.model
            }

    def analyze_portfolio(
        self,
        positions: List[Dict],
        valuations: List[Dict],
        trades: List[Dict],
        strategy_params: Dict
    ) -> Dict:
        """分析持仓"""

        # 构建持仓概要
        positions_summary = self._build_positions_summary(positions)

        # 构建估值数据
        valuation_data = self._build_valuation_data(valuations)

        # 构建交易记录
        recent_trades = self._build_trades_summary(trades)

        # 构建策略参数
        strategy_str = json.dumps(strategy_params, ensure_ascii=False, indent=2)

        # 构建提示词
        prompt = self.ANALYSIS_PROMPT_TEMPLATE.format(
            positions_summary=positions_summary,
            valuation_data=valuation_data,
            recent_trades=recent_trades,
            strategy_params=strategy_str
        )

        try:
            client = self._get_client()

            openai_compatible = ["openai", "deepseek", "custom", "bailian", "qwen", "glm", "minimax"]
            if self.provider in openai_compatible:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一位专业的投资顾问，擅长价值投资和风险控制。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                content = response.choices[0].message.content
            elif self.provider in ["anthropic", "bailian-anthropic"]:
                response = client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system="你是一位专业的投资顾问，擅长价值投资和风险控制。请直接输出分析结果，不要输出思考过程。",
                    messages=[{"role": "user", "content": prompt}]
                )
                # 处理百炼返回的多种content block类型
                content_parts = []
                for block in response.content:
                    # 只提取文本内容，跳过 thinking 等其他类型
                    if hasattr(block, 'text') and block.text:
                        content_parts.append(block.text)
                    elif hasattr(block, 'type'):
                        # 跳过 thinking_block 等非文本类型
                        if block.type == 'text':
                            if hasattr(block, 'text'):
                                content_parts.append(block.text)
                content = '\n'.join(content_parts)
            else:
                raise ValueError(f"不支持的提供商: {self.provider}")

            return {
                "success": True,
                "analysis": content,
                "model": self.model,
                "provider": self.provider
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": self.model,
                "provider": self.provider
            }

    def analyze_single_position(
        self,
        position: Dict,
        trades: List[Dict],
        dimensions: List[str]
    ) -> Dict:
        """分析单个持仓（多维度）"""

        # 维度分析模板（扩展为13个模块）
        dimension_prompts = {
            # 原有维度
            'market': """## 市场分析
请分析当前市场环境对该标的的影响：
1. 大盘走势及市场情绪
2. 该标的所在板块的表现
3. 宏观政策影响

请给出1-10分的评分，并说明理由。""",

            'fundamentals': """## 基本面分析
请基于以下信息进行基本面分析：
1. 估值水平（PE、PB等）
2. 盈利能力（ROE、净利率等）
3. 成长性（营收增长、利润增长）
4. 财务安全性（负债率、现金流）

请给出1-10分的评分，并说明理由。""",

            'technical': """## 技术面分析
请分析该标的的技术指标：
1. 均线系统（MA5/10/20/60排列）
2. 趋势判断（上涨/下跌/震荡）
3. 支撑位和压力位
4. RSI、MACD等指标信号

请给出1-10分的评分，并说明理由。""",

            'capital_flow': """## 资金面分析
请分析资金流向：
1. 主力资金动向
2. 成交量变化
3. 换手率水平
4. 北向资金/机构持仓变化（如有）

请给出1-10分的评分，并说明理由。""",

            'sector': """## 板块分析
请分析该标的所在板块：
1. 板块整体表现
2. 板块轮动情况
3. 该标的在板块中的相对位置
4. 板块未来发展前景

请给出1-10分的评分，并说明理由。""",

            # 新增维度
            'trader_plan': """## 💼 交易员计划
你是一位专业交易员，请制定具体的交易计划：
1. 投资建议：买入/持有/减仓/卖出
2. 目标价位（1个月/3个月/6个月）
3. 止损价位及触发条件
4. 分步建仓策略（首次仓位、加仓条件）
5. 持仓管理纪律

请以表格形式列出操作步骤和执行条件。""",

            'market_overview': """## 📊 大盘分析
请分析当前A股市场整体状况：
1. 主要指数走势（上证/深证/创业板）
2. 涨跌家数与市场情绪
3. 成交额与换手率
4. 北向资金流向
5. 市场风险等级评估（低/中/高）

请给出市场综合评分（1-10分）和仓位建议。""",

            'news': """## 📰 新闻分析
请分析近期影响该标的的重要新闻：
1. 公司公告及业绩预告
2. 行业政策变化
3. 宏观经济数据
4. 市场热点事件

评估每条新闻对该标的的影响程度（利好/利空/中性）和持续时间。""",

            'bull_view': """## 🐂 多头观点
请从看涨角度分析该标的的利好因素：
1. 核心看涨逻辑（3-5条）
2. 催化剂与时间节点
3. 历史可比案例
4. 目标价位推导过程
5. 风险收益比评估

请以专业分析师口吻撰写看涨报告。""",

            'bear_view': """## 🐻 空头观点
请从看跌角度分析该标的的风险因素：
1. 核心看跌逻辑（3-5条）
2. 潜在风险点与触发条件
3. 历史反面案例
4. 最坏情况下的估值测算
5. 止损必要性分析

请以风险控制专家口吻撰写看跌报告。""",

            'verdict': """## ⚖️ 综合裁决
作为投资委员会主席，请综合多空观点做出最终裁决：
1. 多空观点对比表
2. 核心论点采信度评分
3. 胜率与赔率评估
4. 最终建议（买入/持有/卖出）
5. 执行纪律（建仓节奏、止损止盈）

请以决策者视角给出明确、可执行的操作指令。""",

            'aggressive': """## ⚡ 激进策略
针对风险偏好较高的投资者，请设计激进投资方案：
1. 杠杆使用建议
2. 集中仓位比例
3. 短期博弈策略
4. 高风险高收益目标
5. 极端情况应对

请明确标注风险等级和适合人群。""",

            'conservative': """## 🛡️ 保守策略
针对风险厌恶型投资者，请设计稳健投资方案：
1. 分散配置建议
2. 对冲工具使用
3. 安全边际要求
4. 长期持有逻辑
5. 定期检视机制

请注重本金安全和风险控制。""",

            'neutral': """## ⚖️ 中性策略
请设计平衡型投资方案：
1. 核心仓位配置
2. 卫星仓位比例
3. 动态调整机制
4. 收益预期管理
5. 定期再平衡策略

请兼顾收益与风险，适合大多数投资者。""",

            'investment_advice': """## 📋 投资建议
请给出最终的综合投资建议：
1. 综合评分（1-10分）
2. 投资评级（强烈买入/买入/持有/减持/卖出）
3. 目标价格区间
4. 止损止盈设置
5. 建议仓位比例
6. 关键监控指标
7. 本周行动清单

请简洁明了，便于执行。"""
        }

        results = {}

        # 构建持仓信息
        position_info = f"""
## 标的信息
- 名称: {position.get('name', '')} ({position.get('symbol', '')})
- 类型: {position.get('asset_type', '')}
- 持仓数量: {position.get('quantity', 0)}
- 成本价: {position.get('cost_price', 0):.3f}
- 现价: {position.get('current_price', position.get('cost_price', 0)):.3f}
- 收益率: {(float(position.get('current_price') or position.get('cost_price', 0)) - float(position.get('cost_price', 0))) / float(position.get('cost_price', 0)) * 100:.2f}%
- 市值: {float(position.get('market_value') or position.get('total_cost', 0)):.2f}
"""

        # 构建交易记录
        trades_info = self._build_trades_summary(trades)

        # 对每个维度进行分析
        for dim in dimensions:
            if dim in dimension_prompts:
                prompt = f"""{position_info}

## 近期交易记录
{trades_info}

---

{dimension_prompts[dim]}

请以JSON格式返回结果：
{{"score": 评分数字, "analysis": "详细分析内容"}}
"""

                try:
                    client = self._get_client()
                    openai_compatible = ["openai", "deepseek", "custom", "bailian", "qwen", "glm", "minimax"]

                    if self.provider in openai_compatible:
                        response = client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": "你是一位专业的投资分析师，请客观分析并给出评分。返回JSON格式。"},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=self.temperature,
                            max_tokens=self.max_tokens
                        )
                        content = response.choices[0].message.content
                    elif self.provider in ["anthropic", "bailian-anthropic"]:
                        response = client.messages.create(
                            model=self.model,
                            max_tokens=self.max_tokens,
                            system="你是一位专业的投资分析师，请客观分析并给出评分。返回JSON格式。",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        content_parts = []
                        for block in response.content:
                            if hasattr(block, 'text') and block.text:
                                content_parts.append(block.text)
                        content = '\n'.join(content_parts)
                    else:
                        continue

                    # 解析结果
                    import re
                    json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        results[dim] = {
                            'score': result.get('score', 5),
                            'analysis': result.get('analysis', content)
                        }
                    else:
                        results[dim] = {
                            'score': 5,
                            'analysis': content
                        }

                except Exception as e:
                    results[dim] = {
                        'score': 5,
                        'analysis': f'分析失败: {str(e)}'
                    }

        return results

    def _build_positions_summary(self, positions: List[Dict]) -> str:
        """构建持仓概要"""
        if not positions:
            return "暂无持仓"

        lines = []
        total_cost = 0
        total_value = 0

        for p in positions:
            symbol = p.get('symbol', '')
            name = p.get('name', '')
            quantity = p.get('quantity', 0)
            cost_price = float(p.get('cost_price', 0))
            current_price = float(p.get('current_price') or cost_price)
            profit_rate = float(p.get('profit_rate') or 0)

            cost = cost_price * quantity
            value = current_price * quantity
            total_cost += cost
            total_value += value

            lines.append(f"- {name}({symbol}): {quantity}份, 成本{cost_price:.3f}, 现价{current_price:.3f}, 收益率{profit_rate*100:+.2f}%")

        lines.append(f"\n总成本: {total_cost:.2f}")
        lines.append(f"总市值: {total_value:.2f}")
        lines.append(f"总收益率: {(total_value - total_cost) / total_cost * 100:.2f}%" if total_cost > 0 else "总收益率: 0%")

        return "\n".join(lines)

    def _build_valuation_data(self, valuations: List[Dict]) -> str:
        """构建估值数据"""
        if not valuations:
            return "暂无估值数据"

        lines = []
        for v in valuations:
            name = v.get('index_name', '')
            pe = v.get('pe')
            pe_percentile = v.get('pe_percentile')
            level = v.get('level', '')

            line = f"- {name}: "
            if pe is not None:
                line += f"PE={pe:.2f} "
            if pe_percentile is not None:
                line += f"百分位={pe_percentile:.1f}% "
            if level:
                line += f"估值等级={level}"
            lines.append(line)

        return "\n".join(lines)

    def _build_trades_summary(self, trades: List[Dict]) -> str:
        """构建交易记录概要"""
        if not trades:
            return "暂无交易记录"

        # 只取最近10条
        recent = trades[:10]
        lines = []
        for t in recent:
            date = t.get('trade_date', '')
            symbol = t.get('symbol', '')
            trade_type = t.get('trade_type', '')
            quantity = t.get('quantity', 0)
            price = float(t.get('price', 0))
            reason = t.get('reason', '')

            lines.append(f"- {date}: {trade_type} {symbol} {quantity}份 @ {price:.3f} ({reason})")

        return "\n".join(lines)

    @classmethod
    def get_supported_providers(cls) -> Dict:
        """获取支持的提供商"""
        return cls.SUPPORTED_PROVIDERS