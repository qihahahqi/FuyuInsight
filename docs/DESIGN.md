# 理财管理系统 - 系统设计文档

> 版本：V1.0
> 创建日期：2026-03-20
> 作者：Claude Code

---

## 一、系统概述

### 1.1 项目简介

本系统是一个基于 Python + MySQL 的个人理财管理系统，旨在帮助投资者：

- 管理投资组合和持仓记录
- 跟踪交易历史和收益表现
- 基于估值指标做出投资决策
- 回测投资策略在不同市场环境下的表现
- 利用大模型 API 分析持仓并给出建议

### 1.2 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Frontend)                        │
│  HTML5 + CSS3 + JavaScript (现代化响应式设计)                 │
│  白色灰色主题 | 圆角卡片设计 | 移动端适配                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        后端 (Backend)                         │
│  Python 3.8+ | Flask 框架 | SQLAlchemy ORM                   │
│  RESTful API | 蓝图模块化设计                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ SQLAlchemy
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        数据库 (Database)                      │
│  MySQL 8.0+                                                  │
│  持仓表 | 交易记录表 | 估值数据表 | 系统配置表                 │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 核心功能模块

| 模块 | 功能描述 |
|------|----------|
| **持仓管理** | 持仓录入、修改、删除、查看 |
| **交易记录** | 买卖记录管理、交易历史查询 |
| **收益分析** | 收益率计算、盈亏统计、持仓汇总 |
| **估值判断** | PE/PB 百分位分析、估值等级判断、操作建议 |
| **策略回测** | 模拟不同市场环境、验证策略有效性 |
| **AI 分析** | 大模型分析持仓、生成投资建议 |
| **系统配置** | 参数配置、大模型 API 配置 |

---

## 二、数据库设计

### 2.1 ER 图

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   positions  │       │   trades     │       │  valuations  │
│  (持仓表)     │       │  (交易表)     │       │  (估值表)     │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │       │ id (PK)      │       │ id (PK)      │
│ symbol       │◄──────│ position_id  │       │ symbol       │
│ name         │       │ trade_type   │       │ pe           │
│ asset_type   │       │ quantity     │       │ pb           │
│ quantity     │       │ price        │       │ pe_percentile│
│ cost_price   │       │ amount       │       │ pb_percentile│
│ current_price│       │ trade_date   │       │ rsi          │
│ total_cost   │       │ reason       │       │ record_date  │
│ market_value │       │ created_at   │       │ level        │
│ profit_rate  │       └──────────────┘       │ created_at   │
│ stop_profit  │                              └──────────────┘
│ add_position │
│ created_at   │       ┌──────────────┐       ┌──────────────┐
│ updated_at   │       │  cash_pool   │       │   configs    │
└──────────────┘       │  (现金池表)   │       │  (配置表)     │
                       ├──────────────┤       ├──────────────┤
                       │ id (PK)      │       │ id (PK)      │
                       │ amount       │       │ key          │
                       │ event        │       │ value        │
                       │ event_date   │       │ description  │
                       │ created_at   │       │ updated_at   │
                       └──────────────┘       └──────────────┘
```

### 2.2 数据表详细设计

#### 2.2.1 持仓表 (positions)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 主键 |
| symbol | VARCHAR(20) | NOT NULL, UNIQUE | 标的代码（如 510300） |
| name | VARCHAR(50) | NOT NULL | 标的名称（如 沪深300ETF） |
| asset_type | VARCHAR(20) | NOT NULL | 资产类型：etf_index/etf_sector/fund/stock |
| quantity | INT | NOT NULL, DEFAULT 0 | 持仓数量（股/份） |
| cost_price | DECIMAL(10,4) | NOT NULL, DEFAULT 0 | 成本价 |
| current_price | DECIMAL(10,4) | DEFAULT NULL | 当前价格 |
| total_cost | DECIMAL(12,2) | NOT NULL, DEFAULT 0 | 总成本 |
| market_value | DECIMAL(12,2) | DEFAULT NULL | 当前市值 |
| profit_rate | DECIMAL(8,4) | DEFAULT NULL | 收益率 |
| stop_profit_triggered | JSON | DEFAULT NULL | 止盈触发状态 |
| add_position_ratio | DECIMAL(5,4) | DEFAULT 0 | 已加仓比例 |
| category | VARCHAR(20) | DEFAULT NULL | 分类：core/satellite/aggressive |
| notes | TEXT | DEFAULT NULL | 备注 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

#### 2.2.2 交易记录表 (trades)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 主键 |
| position_id | INT | FOREIGN KEY | 关联持仓 ID |
| symbol | VARCHAR(20) | NOT NULL | 标的代码 |
| trade_type | VARCHAR(10) | NOT NULL | 交易类型：buy/sell |
| quantity | INT | NOT NULL | 交易数量 |
| price | DECIMAL(10,4) | NOT NULL | 交易价格 |
| amount | DECIMAL(12,2) | NOT NULL | 交易金额 |
| trade_date | DATE | NOT NULL | 交易日期 |
| reason | VARCHAR(100) | DEFAULT NULL | 交易理由 |
| signal_type | VARCHAR(20) | DEFAULT NULL | 信号类型：stop_profit/add_position/manual |
| notes | TEXT | DEFAULT NULL | 备注 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### 2.2.3 估值数据表 (valuations)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 主键 |
| symbol | VARCHAR(20) | NOT NULL | 标的代码 |
| index_name | VARCHAR(50) | NOT NULL | 指数名称 |
| pe | DECIMAL(10,2) | DEFAULT NULL | 市盈率 |
| pb | DECIMAL(10,4) | DEFAULT NULL | 市净率 |
| pe_percentile | DECIMAL(5,2) | DEFAULT NULL | PE 历史百分位 |
| pb_percentile | DECIMAL(5,2) | DEFAULT NULL | PB 历史百分位 |
| rsi | DECIMAL(5,2) | DEFAULT NULL | RSI 指标 |
| roe | DECIMAL(5,2) | DEFAULT NULL | ROE |
| dividend_yield | DECIMAL(5,2) | DEFAULT NULL | 股息率 |
| level | VARCHAR(20) | DEFAULT NULL | 估值等级 |
| score | DECIMAL(5,2) | DEFAULT NULL | 综合评分 |
| suggestion | VARCHAR(100) | DEFAULT NULL | 操作建议 |
| record_date | DATE | NOT NULL | 记录日期 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### 2.2.4 现金池表 (cash_pool)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 主键 |
| amount | DECIMAL(12,2) | NOT NULL | 金额（正为入，负为出） |
| balance | DECIMAL(12,2) | NOT NULL | 余额 |
| event | VARCHAR(100) | NOT NULL | 事件描述 |
| event_date | DATE | NOT NULL | 事件日期 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### 2.2.5 系统配置表 (configs)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 主键 |
| key | VARCHAR(50) | NOT NULL, UNIQUE | 配置键 |
| value | TEXT | NOT NULL | 配置值 |
| description | VARCHAR(200) | DEFAULT NULL | 配置说明 |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

---

## 三、核心指标计算方法

### 3.1 收益率指标

#### 3.1.1 单笔持仓收益率

```
收益率 = (当前价格 - 成本价) / 成本价 × 100%

盈亏金额 = 当前市值 - 总成本
当前市值 = 当前价格 × 持仓数量
总成本 = 成本价 × 持仓数量
```

#### 3.1.2 投资组合收益率

```
组合收益率 = (总市值 - 总成本) / 总成本 × 100%

总成本 = Σ(各持仓成本价 × 各持仓数量)
总市值 = Σ(各持仓当前价格 × 各持仓数量)
```

#### 3.1.3 时间加权收益率 (TWR)

适用于有多次资金进出的情况：

```
TWR = [(1 + R1) × (1 + R2) × ... × (1 + Rn)] - 1

其中 Ri 为第 i 期的收益率
```

#### 3.1.4 年化收益率

```
年化收益率 = (1 + 总收益率)^(365/持有天数) - 1
```

### 3.2 风险指标

#### 3.2.1 最大回撤 (Maximum Drawdown)

```
最大回撤 = (峰值 - 谷值) / 峰值 × 100%

计算方法：
1. 找到历史最高点（峰值）
2. 从峰值往后找最低点（谷值）
3. 计算回撤幅度
4. 遍历所有时间点，取最大值
```

#### 3.2.2 波动率 (Volatility)

```
波动率 = 标准差(日收益率) × √252

其中 252 为一年的交易日数
```

#### 3.2.3 夏普比率 (Sharpe Ratio)

```
夏普比率 = (组合收益率 - 无风险利率) / 组合波动率

无风险利率通常取 3%（国债利率）
```

### 3.3 估值指标

#### 3.3.1 综合估值评分

```
综合评分 = PE百分位 × 0.5 + PB百分位 × 0.3 + RSI × 0.2

评分越低表示越低估
```

#### 3.3.2 估值等级划分

| 等级 | PE 百分位 | PE 绝对值(沪深300) | RSI | 操作建议 |
|------|-----------|-------------------|-----|----------|
| 极度低估 | <10% | <10 | <30 | 满仓买入 |
| 低估 | 10%-30% | 10-12 | 30-40 | 加大买入 |
| 合理偏低 | 30%-50% | 12-14 | 40-50 | 正常定投 |
| 合理 | 50%-60% | 14-16 | 50-60 | 持有不动 |
| 合理偏高 | 60%-70% | 16-18 | 60-70 | 减仓观望 |
| 高估 | 70%-90% | 18-20 | 70-80 | 分批卖出 |
| 极度高估 | >90% | >20 | >80 | 清仓 |

### 3.4 止盈加仓信号

#### 3.4.1 止盈信号

| 收益率 | 信号等级 | 操作 |
|--------|----------|------|
| ≥15% | 第一档止盈 | 卖出 30% |
| ≥18% | 第二档止盈 | 再卖出 30% |
| ≥20% | 第三档止盈 | 卖出剩余 40% |
| ≥25% | 移动止盈 | 设置回撤 10% 清仓 |

#### 3.4.2 加仓信号（金字塔加仓法）

| 浮亏幅度 | 加仓比例 | 说明 |
|----------|----------|------|
| -5% | +5% | 第一档加仓 |
| -10% | +10% | 第二档加仓 |
| -15% | +15% | 第三档加仓 |
| -20% | +20% | 第四档加仓 |
| -25% | +25% | 第五档加仓 |
| -30% | 观望 | 极端情况，暂停加仓 |

**加仓触发条件（必须同时满足）：**
1. 当前估值处于低估区间（百分位 <30%）
2. 持仓浮亏达到加仓阈值
3. 现金池有足够资金
4. 非系统性风险导致的下跌

---

## 四、API 接口设计

### 4.1 RESTful API 规范

```
基础路径: /api/v1

请求格式: JSON
响应格式: JSON

统一响应格式:
{
    "success": true/false,
    "data": {...},
    "message": "操作成功",
    "timestamp": "2026-03-20T10:00:00"
}
```

### 4.2 接口列表

#### 持仓管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /positions | 获取持仓列表 |
| GET | /positions/{id} | 获取单个持仓 |
| POST | /positions | 创建持仓 |
| PUT | /positions/{id} | 更新持仓 |
| DELETE | /positions/{id} | 删除持仓 |
| GET | /positions/summary | 持仓汇总统计 |

#### 交易管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /trades | 获取交易记录 |
| POST | /trades | 创建交易记录 |
| GET | /trades/statistics | 交易统计 |

#### 收益分析

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /analysis/profit | 收益分析 |
| GET | /analysis/risk | 风险指标 |
| GET | /analysis/signals | 操作信号 |

#### 估值判断

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /valuations | 获取估值数据 |
| POST | /valuations | 录入估值数据 |
| GET | /valuations/evaluate | 估值评估 |
| GET | /valuations/reference/{index} | 获取指数估值参考 |

#### 回测模拟

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /backtest/run | 运行回测 |
| GET | /backtest/scenarios | 获取市场场景 |

#### AI 分析

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /ai/analyze | AI 分析持仓 |
| GET | /ai/status | 获取 AI 配置状态 |

#### 系统配置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /configs | 获取配置 |
| PUT | /configs | 更新配置 |
| POST | /configs/test-llm | 测试大模型连接 |

---

## 五、前端页面设计

### 5.1 页面结构

```
├── 首页 (Dashboard)
│   ├── 总资产卡片
│   ├── 收益率卡片
│   ├── 持仓分布饼图
│   └── 操作信号提醒
│
├── 持仓管理
│   ├── 持仓列表（表格）
│   ├── 新增/编辑持仓（表单）
│   └── 持仓详情（卡片）
│
├── 交易记录
│   ├── 交易列表（表格）
│   └── 新增交易（表单）
│
├── 收益分析
│   ├── 收益统计卡片
│   ├── 收益曲线图
│   └── 风险指标展示
│
├── 估值判断
│   ├── 估值数据录入
│   ├── 估值等级展示
│   └── 操作建议
│
├── 策略回测
│   ├── 参数配置
│   ├── 回测结果展示
│   └── 场景对比
│
├── AI 分析
│   ├── 分析报告
│   └── 投资建议
│
└── 系统设置
    ├── 策略参数配置
    ├── 大模型 API 配置
    └── 数据库配置
```

### 5.2 设计规范

#### 颜色方案

```css
/* 主色调 */
--primary-color: #4A90E2;      /* 主蓝色 */
--secondary-color: #6C757D;    /* 次要灰色 */

/* 背景色 */
--bg-primary: #FFFFFF;         /* 主背景白 */
--bg-secondary: #F8F9FA;       /* 次背景灰 */
--bg-card: #FFFFFF;            /* 卡片背景 */

/* 文字色 */
--text-primary: #212529;       /* 主文字黑 */
--text-secondary: #6C757D;     /* 次文字灰 */

/* 状态色 */
--success-color: #28A745;      /* 盈利绿 */
--danger-color: #DC3545;       /* 亏损红 */
--warning-color: #FFC107;      /* 警告黄 */
--info-color: #17A2B8;         /* 信息蓝 */

/* 边框和阴影 */
--border-radius: 12px;         /* 圆角 */
--box-shadow: 0 2px 8px rgba(0,0,0,0.1);
```

#### 卡片设计

```html
<div class="card">
    <div class="card-header">
        <h3 class="card-title">标题</h3>
    </div>
    <div class="card-body">
        内容区域
    </div>
</div>
```

---

## 六、配置系统设计

### 6.1 配置文件结构

```yaml
# config/config.yaml
server:
  host: "0.0.0.0"
  port: 5000
  debug: false

database:
  host: "localhost"
  port: 3306
  database: "myapp"
  user: "devuser"
  password: "dev123456"
  charset: "utf8mb4"

strategy:
  stop_profit_target: 0.20      # 止盈目标
  max_loss: 0.30                # 最大亏损
  stop_profit_levels:           # 止盈阈值
    - [0.15, 0.30]              # [阈值, 卖出比例]
    - [0.18, 0.30]
    - [0.20, 0.40]
  add_position_levels:          # 加仓阈值
    - [-0.05, 0.05]
    - [-0.10, 0.10]
    - [-0.15, 0.15]
    - [-0.20, 0.20]
    - [-0.25, 0.25]

llm:
  enabled: true
  provider: "openai"            # openai / anthropic / custom
  api_key: ""
  api_base: ""
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 2000
```

### 6.2 配置优先级

```
数据库配置 > 配置文件 > 默认值
```

用户可以在网页端修改配置，修改后会同步到数据库和配置文件。

---

## 七、大模型集成设计

### 7.1 支持的 LLM 提供商

| 提供商 | API 地址 | 模型 |
|--------|----------|------|
| OpenAI | https://api.openai.com/v1 | gpt-4, gpt-3.5-turbo |
| Anthropic | https://api.anthropic.com | claude-3-opus, claude-3-sonnet |
| DeepSeek | https://api.deepseek.com | deepseek-chat |
| 自定义 | 用户配置 | 用户配置 |

### 7.2 分析 Prompt 模板

```
你是一位专业的投资顾问。请根据以下持仓数据，给出投资分析和建议。

## 持仓概况
{positions_summary}

## 市场估值数据
{valuation_data}

## 近期交易记录
{recent_trades}

请从以下角度分析：
1. 持仓结构分析（是否分散、仓位是否合理）
2. 风险评估（最大回撤、波动率）
3. 操作建议（是否需要调整仓位）
4. 长期投资建议

请用简洁、专业的语言回答。
```

---

## 八、部署说明

### 8.1 环境要求

- Python 3.8+
- MySQL 8.0+
- 现代浏览器（Chrome、Firefox、Edge、Safari）

### 8.2 安装步骤

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置数据库
# 修改 config/config.yaml 中的数据库配置

# 4. 初始化数据库
python init_db.py

# 5. 启动服务
python run.py
```

### 8.3 局域网访问

服务默认绑定 `0.0.0.0`，局域网内其他设备可通过 `http://服务器IP:5000` 访问。

---

## 九、扩展性设计

### 9.1 模块化设计

系统采用蓝图（Blueprint）模块化设计，便于扩展新功能：

```
backend/app/
├── api/
│   ├── positions.py    # 持仓 API
│   ├── trades.py       # 交易 API
│   ├── analysis.py     # 分析 API
│   ├── valuations.py   # 估值 API
│   ├── backtest.py     # 回测 API
│   ├── ai.py           # AI API
│   └── configs.py      # 配置 API
├── services/
│   ├── profit_service.py
│   ├── valuation_service.py
│   ├── backtest_service.py
│   └── llm_service.py
└── models/
    ├── position.py
    ├── trade.py
    └── ...
```

### 9.2 插件机制

预留插件接口，支持：
- 自定义策略指标
- 第三方数据源接入
- 自定义分析报告模板

---

## 十、版本规划

### V1.0（当前版本）

- ✅ 持仓管理
- ✅ 交易记录
- ✅ 收益分析
- ✅ 估值判断
- ✅ 策略回测
- ✅ AI 分析
- ✅ 系统配置

### V1.1（计划中）

- 数据导入导出
- 历史数据可视化
- 移动端适配优化

### V2.0（远期规划）

- 多账户管理
- 实时行情接入
- 自动化交易

---

*本文档将随项目迭代持续更新。*