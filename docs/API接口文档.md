# 投资理财管理系统 - API 接口文档

> 版本: v1.0
> 更新日期: 2026-03-27
> 适用范围: 微信小程序 / 移动端应用

---

## 目录

- [1. 基础信息](#1-基础信息)
- [2. 认证说明](#2-认证说明)
- [3. 公共响应格式](#3-公共响应格式)
- [4. 接口列表](#4-接口列表)
  - [4.1 认证模块](#41-认证模块)
  - [4.2 持仓管理](#42-持仓管理)
  - [4.3 账户管理](#43-账户管理)
  - [4.4 交易记录](#44-交易记录)
  - [4.5 收益分析](#45-收益分析)
  - [4.6 估值判断](#46-估值判断)
  - [4.7 AI 分析](#47-ai-分析)
  - [4.8 策略回测](#48-策略回测)
  - [4.9 图表数据](#49-图表数据)
  - [4.10 系统配置](#410-系统配置)
- [5. 数据模型](#5-数据模型)
- [6. 错误码说明](#6-错误码说明)

---

## 1. 基础信息

| 项目 | 说明 |
|-----|------|
| API 基础地址 | `http://your-domain/api/v1` |
| 协议 | HTTP/HTTPS |
| 数据格式 | JSON |
| 编码 | UTF-8 |
| 认证方式 | JWT Token (Bearer Auth) |

---

## 2. 认证说明

### 2.1 获取 Token

登录成功后，服务器返回 JWT Token，客户端需保存该 Token。

### 2.2 使用 Token

在需要认证的接口请求头中添加：

```
Authorization: Bearer <your_token>
```

### 2.3 Token 有效期

默认 24 小时，可在服务端配置调整。

---

## 3. 公共响应格式

### 3.1 成功响应

```json
{
    "success": true,
    "data": { ... },
    "message": "操作成功"
}
```

### 3.2 失败响应

```json
{
    "success": false,
    "message": "错误描述"
}
```

---

## 4. 接口列表

### 4.1 认证模块

#### 4.1.1 用户注册

**POST** `/auth/register`

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| username | string | 是 | 用户名 (3-50字符) |
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码 (至少6字符) |

**响应示例：**

```json
{
    "success": true,
    "message": "注册成功",
    "user": {
        "id": 1,
        "username": "test",
        "email": "test@example.com"
    },
    "token": "eyJ..."
}
```

---

#### 4.1.2 用户登录

**POST** `/auth/login`

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

**响应示例：**

```json
{
    "success": true,
    "message": "登录成功",
    "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com"
    },
    "token": "eyJ..."
}
```

---

#### 4.1.3 获取当前用户信息

**GET** `/auth/me`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "created_at": "2024-01-01T00:00:00"
    }
}
```

---

#### 4.1.4 修改密码

**PUT** `/auth/password`

**需要认证：** 是

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| old_password | string | 是 | 原密码 |
| new_password | string | 是 | 新密码 (至少6字符) |

**响应示例：**

```json
{
    "success": true,
    "message": "密码修改成功"
}
```

---

#### 4.1.5 用户登出

**POST** `/auth/logout`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "message": "登出成功"
}
```

---

### 4.2 持仓管理

#### 4.2.1 获取持仓列表

**GET** `/positions`

**需要认证：** 是

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| account_id | int | 否 | 账户ID，不传则返回全部 |

**响应示例：**

```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "symbol": "000001",
            "name": "平安银行",
            "asset_type": "stock",
            "product_category": "market",
            "quantity": 1000,
            "cost_price": 12.5,
            "current_price": 13.2,
            "total_cost": 12500.0,
            "market_value": 13200.0,
            "profit_rate": 0.056,
            "category": "core",
            "risk_level": "R4",
            "product_params": null,
            "mature_date": null,
            "notes": "核心仓位",
            "created_at": "2024-01-01T00:00:00"
        }
    ]
}
```

---

#### 4.2.2 获取单个持仓

**GET** `/positions/{id}`

**需要认证：** 是

**路径参数：**

| 参数 | 类型 | 说明 |
|-----|------|------|
| id | int | 持仓ID |

**响应示例：**

```json
{
    "success": true,
    "data": {
        "id": 1,
        "symbol": "000001",
        "name": "平安银行",
        "asset_type": "stock",
        ...
    }
}
```

---

#### 4.2.3 创建持仓

**POST** `/positions`

**需要认证：** 是

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| symbol | string | 条件 | 产品代码（市价型必填，其他类型可选，留空自动生成） |
| name | string | 是 | 产品名称 |
| asset_type | string | 是 | 资产类型，见[资产类型枚举](#51-资产类型) |
| quantity | int | 是 | 数量/份额 |
| cost_price | float | 是 | 成本价/本金 |
| current_price | float | 否 | 当前价格 |
| category | string | 否 | 分类: core/satellite/aggressive/stable |
| account_id | int | 否 | 账户ID，默认1 |
| notes | string | 否 | 备注 |
| product_params | object | 否 | 产品参数（JSON对象） |
| mature_date | string | 否 | 到期日 (YYYY-MM-DD) |
| risk_level | string | 否 | 风险等级: R1/R2/R3/R4/R5 |

**product_params 字段说明：**

| 字段 | 类型 | 适用资产类型 | 说明 |
|-----|------|-------------|------|
| interest_rate | float | 固定收益类 | 年化利率(%) |
| start_date | string | 固定收益类 | 起息日 |
| end_date | string | 固定收益类 | 到期日 |
| redeemable | boolean | 存款/理财 | 可提前赎回 |
| payment_cycle | string | 债券 | 付息方式: at_maturity/monthly/quarterly/yearly |
| issuer | string | 企业债/保险/信托 | 发行机构 |
| weight | float | 黄金/白银 | 重量(克) |
| purity | float | 黄金/白银 | 纯度 |

**响应示例：**

```json
{
    "success": true,
    "message": "持仓创建成功",
    "data": {
        "id": 1,
        "symbol": "000001",
        "name": "平安银行",
        ...
    }
}
```

---

#### 4.2.4 更新持仓

**PUT** `/positions/{id}`

**需要认证：** 是

**请求参数：** 同创建持仓，所有字段均为可选

**响应示例：**

```json
{
    "success": true,
    "message": "持仓更新成功",
    "data": { ... }
}
```

---

#### 4.2.5 删除持仓

**DELETE** `/positions/{id}`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "message": "持仓删除成功"
}
```

---

#### 4.2.6 同步持仓价格

**POST** `/positions/sync-prices`

**需要认证：** 是

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| account_id | int | 否 | 账户ID，不传则同步全部 |

**响应示例：**

```json
{
    "success": true,
    "message": "同步完成",
    "data": {
        "total": 10,
        "success": 9,
        "failed": 1,
        "details": [...]
    }
}
```

---

#### 4.2.7 获取资产类型配置

**GET** `/positions/asset-types`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "data": {
        "groups": [
            {
                "group": "市价型产品",
                "types": ["stock", "etf_index", "etf_sector", "fund", "gold", "silver"]
            },
            {
                "group": "固定收益类",
                "types": ["bank_deposit", "bank_current", "bank_wealth", "treasury_bond", "corporate_bond", "money_fund"]
            },
            {
                "group": "其他产品",
                "types": ["insurance", "trust", "other"]
            }
        ],
        "configs": {
            "stock": {
                "name": "股票",
                "category": "market",
                "has_realtime_price": true,
                "risk_level": "R4",
                "form_fields": []
            },
            "bank_deposit": {
                "name": "银行定期存款",
                "category": "fixed_income",
                "has_realtime_price": false,
                "risk_level": "R1",
                "form_fields": ["interest_rate", "start_date", "end_date", "redeemable"]
            }
        }
    }
}
```

---

### 4.3 账户管理

#### 4.3.1 获取账户列表

**GET** `/accounts`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "name": "主账户",
            "account_type": "personal",
            "broker": "中信证券",
            "description": "个人主账户",
            "is_active": true,
            "summary": {
                "position_count": 5,
                "total_cost": 100000.0,
                "market_value": 120000.0,
                "profit_rate": 0.2
            }
        }
    ]
}
```

---

#### 4.3.2 创建账户

**POST** `/accounts`

**需要认证：** 是

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| name | string | 是 | 账户名称 |
| account_type | string | 否 | 账户类型: personal/ira/401k/other |
| broker | string | 否 | 券商/银行 |
| description | string | 否 | 描述 |

**响应示例：**

```json
{
    "success": true,
    "message": "账户创建成功",
    "data": { ... }
}
```

---

#### 4.3.3 更新账户

**PUT** `/accounts/{id}`

**需要认证：** 是

**请求参数：** 同创建账户

---

#### 4.3.4 删除账户

**DELETE** `/accounts/{id}`

**需要认证：** 是

**注意：** 有持仓的账户无法删除

---

#### 4.3.5 获取账户汇总

**GET** `/accounts/{id}/summary`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "data": {
        "account": { ... },
        "position_count": 5,
        "total_cost": 100000.0,
        "market_value": 120000.0,
        "total_profit": 20000.0,
        "profit_rate": 0.2,
        "by_type": {
            "stock": {"count": 3, "value": 80000.0},
            "fund": {"count": 2, "value": 40000.0}
        }
    }
}
```

---

### 4.4 交易记录

#### 4.4.1 获取交易记录列表

**GET** `/trades`

**需要认证：** 是

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| page | int | 否 | 页码，默认1 |
| per_page | int | 否 | 每页数量，默认20 |
| symbol | string | 否 | 标的代码筛选 |

**响应示例：**

```json
{
    "success": true,
    "data": {
        "items": [
            {
                "id": 1,
                "symbol": "000001",
                "trade_type": "buy",
                "quantity": 100,
                "price": 12.5,
                "amount": 1250.0,
                "trade_date": "2024-01-15",
                "reason": "建仓",
                "signal_type": null,
                "notes": ""
            }
        ],
        "total": 50,
        "page": 1,
        "per_page": 20,
        "pages": 3
    }
}
```

---

#### 4.4.2 创建交易记录

**POST** `/trades`

**需要认证：** 是

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| symbol | string | 是 | 标的代码 |
| trade_type | string | 是 | 交易类型: buy/sell |
| quantity | int | 是 | 数量 |
| price | float | 是 | 成交价格 |
| trade_date | string | 是 | 交易日期 (YYYY-MM-DD) |
| reason | string | 否 | 交易原因 |
| signal_type | string | 否 | 信号类型 |
| notes | string | 否 | 备注 |

**响应示例：**

```json
{
    "success": true,
    "message": "交易记录创建成功",
    "data": { ... }
}
```

---

#### 4.4.3 删除交易记录

**DELETE** `/trades/{id}`

**需要认证：** 是

---

#### 4.4.4 获取交易统计

**GET** `/trades/statistics`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "data": {
        "total_trades": 100,
        "buy_count": 60,
        "sell_count": 40,
        "buy_amount": 500000.0,
        "sell_amount": 350000.0,
        "by_symbol": [
            {"symbol": "000001", "count": 10, "total_amount": 50000.0}
        ]
    }
}
```

---

### 4.5 收益分析

#### 4.5.1 获取收益分析

**GET** `/analysis/profit`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "data": {
        "total_cost": 100000.0,
        "market_value": 120000.0,
        "total_profit": 20000.0,
        "profit_rate": 0.2,
        "positions_count": 5,
        "profit_positions": 3,
        "loss_positions": 2,
        "signals": [...]
    }
}
```

---

#### 4.5.2 获取风险分析

**GET** `/analysis/risk`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "data": {
        "portfolio_profit_rate": 0.2,
        "total_cost": 100000.0,
        "total_value": 120000.0,
        "position_risks": [
            {
                "symbol": "000001",
                "name": "平安银行",
                "profit_rate": 0.15,
                "risk_level": "正常"
            }
        ],
        "risk_summary": {
            "profit_positions": 3,
            "loss_positions": 2,
            "high_risk_positions": 0
        }
    }
}
```

---

#### 4.5.3 获取操作信号

**GET** `/analysis/signals`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "data": {
        "stop_profit_signals": [...],
        "add_position_signals": [
            {
                "position_id": 1,
                "symbol": "000001",
                "name": "平安银行",
                "cost_price": 12.0,
                "current_price": 10.8,
                "profit_rate": -0.1,
                "signal_level": 1,
                "suggestion": "跌幅10%，可考虑加仓"
            }
        ],
        "total_stop_profit": 0,
        "total_add_position": 1
    }
}
```

---

#### 4.5.4 获取持仓分布

**GET** `/analysis/distribution`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "data": {
        "total_value": 120000.0,
        "by_type": {
            "stock": {"count": 3, "value": 80000.0, "percentage": 66.67},
            "fund": {"count": 2, "value": 40000.0, "percentage": 33.33}
        },
        "by_category": {
            "core": {"count": 3, "value": 70000.0, "percentage": 58.33},
            "satellite": {"count": 2, "value": 50000.0, "percentage": 41.67}
        },
        "by_profit": {
            "high_profit": [...],
            "profit": [...],
            "loss": [...],
            "high_loss": [...]
        }
    }
}
```

---

### 4.6 估值判断

#### 4.6.1 获取估值数据列表

**GET** `/valuations`

**需要认证：** 是

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| symbol | string | 否 | 标的代码筛选 |

**响应示例：**

```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "symbol": "000001",
            "index_name": "上证指数",
            "pe": 13.5,
            "pb": 1.25,
            "pe_percentile": 45.5,
            "pb_percentile": 42.1,
            "rsi": 55.5,
            "roe": 10.5,
            "dividend_yield": 2.5,
            "level": "normal",
            "score": 65,
            "suggestion": "持有",
            "record_date": "2024-01-15"
        }
    ]
}
```

---

#### 4.6.2 录入估值数据

**POST** `/valuations`

**需要认证：** 是

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| symbol | string | 是 | 标的代码 |
| index_name | string | 是 | 指数名称 |
| record_date | string | 是 | 记录日期 (YYYY-MM-DD) |
| pe | float | 否 | 市盈率 |
| pb | float | 否 | 市净率 |
| pe_percentile | float | 否 | PE历史百分位 (0-100) |
| pb_percentile | float | 否 | PB历史百分位 (0-100) |
| rsi | float | 否 | RSI指标 (0-100) |
| roe | float | 否 | ROE(%) |
| dividend_yield | float | 否 | 股息率(%) |

**响应示例：**

```json
{
    "success": true,
    "message": "估值数据录入成功",
    "data": {
        "valuation": { ... },
        "analysis": {
            "level": "undervalued",
            "score": 80,
            "position_suggestion": "建议仓位80%",
            "action": "买入",
            "details": "..."
        }
    }
}
```

---

#### 4.6.3 估值评估（不保存）

**POST** `/valuations/evaluate`

**需要认证：** 是

**请求参数：** 同录入估值数据

---

#### 4.6.4 获取指数估值参考

**GET** `/valuations/reference`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "data": {
        "indices": ["上证指数", "沪深300", "创业板指", "中证500"],
        "reference": {
            "上证指数": {
                "pe_range": [10, 20],
                "pb_range": [1.0, 2.0]
            }
        }
    }
}
```

---

### 4.7 AI 分析

#### 4.7.1 获取 AI 状态

**GET** `/ai/status`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "data": {
        "enabled": true,
        "provider": "openai",
        "model": "gpt-4",
        "configured": true
    }
}
```

---

#### 4.7.2 获取分析维度列表

**GET** `/ai/dimensions`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "data": [
        {
            "key": "trader_plan",
            "name": "交易员计划",
            "icon": "💼",
            "description": "具体买卖建议、目标价、止损位"
        },
        {
            "key": "technical",
            "name": "技术分析",
            "icon": "📈",
            "description": "均线系统、MACD、RSI等技术指标"
        }
    ]
}
```

---

#### 4.7.3 执行 AI 分析

**POST** `/ai/analyze`

**需要认证：** 是

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| analysis_type | string | 否 | 分析类型: single(单标的)/portfolio(全仓)，默认portfolio |
| position_id | int | 条件 | 持仓ID，单标的分析时必填 |
| dimensions | array | 否 | 分析维度列表，不传则使用默认维度 |

**响应示例：**

```json
{
    "success": true,
    "data": {
        "id": 123,
        "analysis_type": "portfolio",
        "overall_score": 7,
        "dimensions": {
            "trader_plan": {
                "analysis": "## 分析内容...",
                "score": 7
            },
            "technical": {
                "analysis": "## 技术分析...",
                "score": 6
            }
        }
    }
}
```

---

#### 4.7.4 获取分析历史

**GET** `/ai/history`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "data": [
        {
            "id": 123,
            "analysis_type": "portfolio",
            "symbol": null,
            "overall_score": 7,
            "model_name": "gpt-4",
            "created_at": "2024-01-15T10:30:00"
        }
    ]
}
```

---

#### 4.7.5 获取分析历史详情

**GET** `/ai/history/{id}`

**需要认证：** 是

---

#### 4.7.6 删除分析历史

**DELETE** `/ai/history/{id}`

**需要认证：** 是

---

### 4.8 策略回测

#### 4.8.1 获取可用策略列表

**GET** `/backtest/strategies`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "data": [
        {"value": "double_ma", "name": "双均线策略"},
        {"value": "pyramid", "name": "金字塔策略"},
        {"value": "grid", "name": "网格交易"},
        {"value": "buy_hold", "name": "买入持有"}
    ]
}
```

---

#### 4.8.2 获取可用数据源

**GET** `/backtest/data-sources`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "data": [
        {"value": "akshare", "name": "AKShare", "available": true, "free": true},
        {"value": "baostock", "name": "BaoStock", "available": true, "free": true},
        {"value": "tushare", "name": "Tushare Pro", "available": false, "free": false},
        {"value": "local", "name": "本地数据", "available": true, "free": true}
    ]
}
```

---

#### 4.8.3 运行回测

**POST** `/backtest/run`

**需要认证：** 是

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| symbol | string | 是 | 标的代码 |
| data_source | string | 否 | 数据源: akshare/baostock/tushare/local，默认akshare |
| start_date | string | 否 | 开始日期 (YYYY-MM-DD) |
| end_date | string | 否 | 结束日期 (YYYY-MM-DD) |
| initial_capital | float | 否 | 初始资金，默认100000 |
| strategies | array | 否 | 策略列表，默认["double_ma"] |
| strategy_params | object | 否 | 各策略参数 |
| asset_type | string | 否 | 资产类型: stock/fund，默认stock |

**响应示例：**

```json
{
    "success": true,
    "data": {
        "symbol": "000001",
        "data_source": "akshare",
        "asset_type": "stock",
        "initial_capital": 100000,
        "start_date": "2023-01-01",
        "end_date": "2024-01-01",
        "data_count": 244,
        "strategies": [
            {
                "strategy": "double_ma",
                "strategy_name": "双均线策略",
                "total_return": 15.5,
                "annual_return": 15.5,
                "max_drawdown": 8.2,
                "sharpe_ratio": 1.25,
                "win_rate": 55.0,
                "trade_count": 12,
                "final_value": 115500.0,
                "records": [...]
            }
        ]
    }
}
```

---

#### 4.8.4 从在线获取历史数据

**POST** `/backtest/fetch-data`

**需要认证：** 是

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| symbol | string | 是 | 标的代码 |
| name | string | 否 | 标的名称 |
| start_date | string | 是 | 开始日期 |
| end_date | string | 是 | 结束日期 |
| data_source | string | 否 | 数据源，默认akshare |
| asset_type | string | 否 | 资产类型: stock/fund |

---

#### 4.8.5 获取已导入的历史数据列表

**GET** `/backtest/price-histories`

**需要认证：** 是

---

#### 4.8.6 删除历史价格数据

**DELETE** `/backtest/price-histories/{symbol}`

**需要认证：** 是

---

### 4.9 图表数据

#### 4.9.1 获取收益曲线数据

**GET** `/charts/profit-curve`

**需要认证：** 是

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| account_id | int | 否 | 账户ID |
| days | int | 否 | 天数，默认30 |

**响应示例：**

```json
{
    "success": true,
    "data": {
        "labels": ["2024-01-01", "2024-01-02", ...],
        "profit_rates": [5.2, 5.5, ...],
        "market_values": [105200, 105500, ...],
        "total_costs": [100000, 100000, ...]
    }
}
```

---

#### 4.9.2 获取持仓分布数据

**GET** `/charts/distribution`

**需要认证：** 是

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| account_id | int | 否 | 账户ID |

**响应示例：**

```json
{
    "success": true,
    "data": {
        "by_type": {
            "stock": {"count": 3, "value": 80000.0, "percentage": 66.67}
        },
        "by_category": {
            "core": {"count": 3, "value": 70000.0, "percentage": 58.33}
        },
        "by_position": [
            {"symbol": "000001", "name": "平安银行", "value": 30000.0, "percentage": 25.0}
        ],
        "total_value": 120000.0
    }
}
```

---

#### 4.9.3 获取收益分布数据

**GET** `/charts/profit-distribution`

**需要认证：** 是

---

#### 4.9.4 获取交易汇总统计

**GET** `/charts/trade-summary`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "data": {
        "monthly": {
            "2024-01": {"buy": 50000.0, "sell": 20000.0, "buy_count": 5, "sell_count": 2},
            "2024-02": {"buy": 30000.0, "sell": 0, "buy_count": 3, "sell_count": 0}
        }
    }
}
```

---

### 4.10 系统配置

#### 4.10.1 获取所有配置

**GET** `/configs`

**需要认证：** 是

---

#### 4.10.2 获取 LLM 配置

**GET** `/configs/llm`

**需要认证：** 是

**响应示例：**

```json
{
    "success": true,
    "data": {
        "enabled": true,
        "provider": "openai",
        "model": "gpt-4",
        "api_base": "",
        "temperature": 0.7,
        "max_tokens": 2000,
        "has_api_key": true,
        "api_key": "******"
    }
}
```

---

#### 4.10.3 更新 LLM 配置

**PUT** `/configs/llm`

**需要认证：** 是

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| enabled | boolean | 否 | 是否启用 |
| provider | string | 否 | 提供商: openai/anthropic/deepseek |
| model | string | 否 | 模型名称 |
| api_key | string | 否 | API Key |
| api_base | string | 否 | API 基础地址 |
| temperature | float | 否 | 温度参数 (0-1) |
| max_tokens | int | 否 | 最大 Token 数 |

---

#### 4.10.4 测试 LLM 连接

**POST** `/configs/test-llm`

**需要认证：** 是

---

#### 4.10.5 获取策略配置

**GET** `/configs/strategy`

**需要认证：** 是

---

#### 4.10.6 更新策略配置

**PUT** `/configs/strategy`

**需要认证：** 是

---

## 5. 数据模型

### 5.1 资产类型

| 类型代码 | 显示名称 | 产品大类 | 是否实时价格 |
|---------|---------|---------|-------------|
| stock | 股票 | market | 是 |
| etf_index | 宽基ETF | market | 是 |
| etf_sector | 行业ETF | market | 是 |
| fund | 基金 | market | 是 |
| gold | 黄金 | market | 是 |
| silver | 白银 | market | 是 |
| bank_deposit | 银行定期存款 | fixed_income | 否 |
| bank_current | 银行活期存款 | fixed_income | 否 |
| bank_wealth | 银行理财产品 | fixed_income | 否 |
| treasury_bond | 国债 | fixed_income | 否 |
| corporate_bond | 企业债 | fixed_income | 否 |
| money_fund | 货币基金 | fixed_income | 是 |
| insurance | 保险理财 | manual | 否 |
| trust | 信托产品 | manual | 否 |
| other | 其他 | manual | 否 |

### 5.2 产品代码规则

| 产品大类 | 代码规则 | 示例 |
|---------|---------|------|
| market | 必须填写真实代码 | 000001, 600519 |
| fixed_income | 可选，留空自动生成 FI_YYYYMMDD_XXX | FI_20260327_001 |
| manual | 可选，留空自动生成 MF_YYYYMMDD_XXX | MF_20260327_042 |
| gold | 可选，留空自动生成 AU_XXXX | AU_0001 |
| silver | 可选，留空自动生成 AG_XXXX | AG_0042 |

### 5.3 持仓对象

```json
{
    "id": 1,
    "symbol": "000001",
    "name": "平安银行",
    "asset_type": "stock",
    "product_category": "market",
    "quantity": 1000,
    "cost_price": 12.5,
    "current_price": 13.2,
    "total_cost": 12500.0,
    "market_value": 13200.0,
    "profit_rate": 0.056,
    "category": "core",
    "risk_level": "R4",
    "product_params": null,
    "mature_date": null,
    "expected_return": null,
    "actual_return": null,
    "notes": "",
    "account_id": 1,
    "created_at": "2024-01-01T00:00:00"
}
```

### 5.4 账户对象

```json
{
    "id": 1,
    "name": "主账户",
    "account_type": "personal",
    "broker": "中信证券",
    "description": "个人主账户",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00"
}
```

### 5.5 交易记录对象

```json
{
    "id": 1,
    "symbol": "000001",
    "trade_type": "buy",
    "quantity": 100,
    "price": 12.5,
    "amount": 1250.0,
    "trade_date": "2024-01-15",
    "reason": "建仓",
    "signal_type": null,
    "notes": ""
}
```

---

## 6. 错误码说明

| HTTP 状态码 | 说明 |
|------------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或Token失效 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

**常见错误响应：**

```json
{
    "success": false,
    "message": "缺少必填字段: symbol"
}
```

```json
{
    "success": false,
    "message": "认证失败，请重新登录"
}
```

---

## 附录：小程序对接注意事项

### 1. 域名配置

在微信公众平台配置合法域名：
- `request合法域名`: 添加后端API域名

### 2. 登录流程

```
1. 小程序调用 wx.login() 获取 code
2. 将 code 发送到后端换取 openid
3. 后端创建/查找用户，返回 JWT Token
4. 小程序存储 Token，后续请求携带
```

### 3. 数据缓存建议

- Token 存储在 `wx.setStorageSync('token', token)`
- 用户信息可缓存，减少请求
- 持仓数据可缓存，下拉刷新更新

### 4. 错误处理

```javascript
// 请求拦截器示例
function request(url, options = {}) {
    const token = wx.getStorageSync('token');
    return wx.request({
        url: API_BASE + url,
        header: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        ...options,
        success(res) {
            if (res.statusCode === 401) {
                // Token 失效，跳转登录
                wx.navigateTo({ url: '/pages/login/login' });
            }
        }
    });
}
```

### 5. 安全建议

- Token 不要存储在全局变量中
- 敏感操作需验证用户身份
- 定期刷新 Token