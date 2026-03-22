# 投资理财管理系统

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-green?logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-orange?logo=mysql)
![License](https://img.shields.io/badge/License-MIT-yellow)

**一套完整的个人投资理财管理系统**

[功能特性](#功能特性) • [快速开始](#快速开始) • [使用文档](#使用文档) • [贡献指南](#贡献指南)

</div>

---

## 简介

投资理财管理系统是一个基于 Python + Flask + MySQL 的全栈应用，帮助投资者科学管理投资组合、跟踪交易记录、分析收益风险、判断市场估值，并利用大模型 AI 生成投资建议。

本系统基于经典的价值投资理念设计，内置了完整的止盈加仓策略，支持在不同市场环境下回测策略表现。

### 核心理念

- **价值投资**：基于估值水平决定买卖时机
- **风险控制**：金字塔加仓、分档止盈
- **科学决策**：多维度指标分析
- **AI 赋能**：大模型辅助决策

---

## 功能特性

### 持仓管理

- 多类型资产管理（ETF、基金、股票）
- 实时收益计算
- 持仓分布可视化
- 资产配置比例分析

### 交易记录

- 完整的交易历史
- 自动更新持仓成本
- 交易理由记录
- 交易统计分析

### 收益分析

- 单笔/组合收益率计算
- 最大回撤分析
- 夏普比率计算
- 盈亏分布统计

### 估值判断

- PE/PB 百分位分析
- 多指数估值参考
- 估值等级判断
- 操作建议生成

### 策略回测

- 多种市场场景模拟
- 金字塔加仓验证
- 分档止盈测试
- 策略对比分析

### AI 分析

- 支持 OpenAI、Claude、DeepSeek 等
- 持仓结构分析
- 风险评估报告
- 投资建议生成

---

## 技术栈


| 层级   | 技术                                  |
| ------ | ------------------------------------- |
| 前端   | HTML5 + CSS3 + JavaScript (原生)      |
| 后端   | Python 3.8+ + Flask 2.0+              |
| 数据库 | MySQL 8.0+                            |
| ORM    | SQLAlchemy                            |
| AI     | OpenAI API / Anthropic API / 兼容接口 |

---

## 快速开始

### 环境要求

- Python 3.8 或更高版本
- MySQL 8.0 或更高版本
- 现代浏览器

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/yourusername/financial-management-system.git
cd financial-management-system
```

#### 2. 创建虚拟环境

```bash
# Linux/Mac
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置数据库

创建 MySQL 数据库：

```sql
CREATE DATABASE myapp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'devuser'@'localhost' IDENTIFIED BY 'dev123456';
GRANT ALL PRIVILEGES ON myapp.* TO 'devuser'@'localhost';
FLUSH PRIVILEGES;
```

#### 5. 配置系统

编辑 `config/config.yaml`：

```yaml
database:
  host: localhost
  port: 3306
  database: myapp
  user: devuser
  password: dev123456
```

#### 6. 初始化数据库

```bash
python init_db.py
```

#### 7. 启动服务

```bash
python run.py
```

访问 http://localhost:5001 即可使用。

如需杀死服务命令：sudo kill -9 $(sudo lsof -t -i :5001)

### 局域网部署

默认绑定 `0.0.0.0`，局域网内其他设备可通过 `http://服务器IP:5000` 访问。

---

## 使用文档

### 目录结构

```
financial-management-system/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API 接口
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具函数
│   └── migrations/         # 数据库迁移
├── frontend/               # 前端代码
│   ├── css/               # 样式文件
│   ├── js/                # JavaScript
│   └── index.html         # 主页面
├── config/                # 配置文件
│   └── config.yaml        # 主配置
├── docs/                  # 文档
│   ├── DESIGN.md          # 设计文档
│   └── README.md          # 说明文档
├── run.py                 # 启动脚本
├── init_db.py             # 数据库初始化
└── requirements.txt       # 依赖列表
```

### 核心功能使用

#### 添加持仓

1. 进入「持仓管理」页面
2. 点击「新增持仓」
3. 填写标的代码、名称、成本价、数量等信息
4. 选择资产类型（宽基ETF/行业ETF/基金/股票）
5. 保存

#### 记录交易

1. 进入「交易记录」页面
2. 点击「新增交易」
3. 选择关联的持仓
4. 填写交易类型（买入/卖出）、价格、数量
5. 记录交易理由

#### 估值判断

1. 进入「估值判断」页面
2. 录入指数的 PE、PB 及其历史百分位
3. 系统自动计算估值等级
4. 查看操作建议

#### 策略回测

1. 进入「策略回测」页面
2. 设置初始资金、初始价格、模拟周期
3. 选择市场场景（牛市/熊市/震荡市等）
4. 运行回测
5. 查看收益率、最大回撤、交易记录

#### AI 分析

1. 在「系统设置」中配置大模型 API
2. 进入「AI 分析」页面
3. 点击「开始分析」
4. 查看分析报告和投资建议

---

## 策略说明

### 止盈策略（分档止盈）


| 收益率 | 操作         |
| ------ | ------------ |
| ≥15%  | 卖出 30%     |
| ≥18%  | 再卖出 30%   |
| ≥20%  | 卖出剩余 40% |
| ≥25%  | 启动移动止盈 |

### 加仓策略（金字塔加仓）


| 浮亏幅度 | 加仓比例 |
| -------- | -------- |
| -5%      | +5%      |
| -10%     | +10%     |
| -15%     | +15%     |
| -20%     | +20%     |
| -25%     | +25%     |

### 估值判断标准


| 等级     | PE 百分位 | 操作建议 |
| -------- | --------- | -------- |
| 极度低估 | <10%      | 满仓买入 |
| 低估     | 10%-30%   | 加大买入 |
| 合理偏低 | 30%-50%   | 正常定投 |
| 合理     | 50%-60%   | 持有     |
| 合理偏高 | 60%-70%   | 减仓     |
| 高估     | 70%-90%   | 大幅减仓 |
| 极度高估 | >90%      | 清仓     |

---

## 配置说明

### 策略参数配置

在「系统设置」或 `config/config.yaml` 中可配置：

```yaml
strategy:
  stop_profit_target: 0.20    # 止盈目标
  max_loss: 0.30              # 最大可接受亏损
```

### 大模型配置

```yaml
llm:
  enabled: true
  provider: "openai"          # openai / anthropic / deepseek / custom
  api_key: "your-api-key"
  api_base: "https://api.openai.com/v1"
  model: "gpt-4"
  temperature: 0.7
```

支持的提供商：

- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3-opus, Claude-3-sonnet
- **DeepSeek**: deepseek-chat
- **自定义**: 任何兼容 OpenAI API 的服务

---

## API 文档

### 基础路径

```
http://localhost:5000/api/v1
```

### 常用接口

#### 获取持仓列表

```
GET /positions
```

#### 创建持仓

```
POST /positions
{
    "symbol": "510300",
    "name": "沪深300ETF",
    "asset_type": "etf_index",
    "quantity": 5000,
    "cost_price": 4.000
}
```

#### 获取收益分析

```
GET /analysis/profit
```

#### 运行回测

```
POST /backtest/run
{
    "initial_capital": 100000,
    "initial_price": 4.0,
    "periods": 24,
    "scenario": "bull_market"
}
```

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境搭建

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest

# 代码格式化
black .
```

### 代码规范

- 遵循 PEP 8 编码规范
- 使用 Black 格式化代码
- 添加必要的注释和文档字符串

---

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

---

## 免责声明

本系统仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。历史收益不代表未来表现。

---

## 联系方式

如有问题或建议，欢迎：

- 提交 Issue
- 发送邮件至 your.email@example.com

---

<div align="center">

**如果这个项目对你有帮助，请给一个 Star ⭐**

</div>
