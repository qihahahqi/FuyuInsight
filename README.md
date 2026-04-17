# 投资理财管理系统

> ⚠️ **免责声明**
> 
> 本系统仅供个人学习和研究使用，所有分析结果仅供参考，**不构成任何投资建议**。
> 
> - 投资有风险，入市需谨慎
> - 历史收益不代表未来表现
> - 请根据自身风险承受能力做出决策
> - 本系统不承担任何投资损失责任
> 
> **本项目仅作个人技术交流和学习使用。**
> 
> 如有技术交流或学习探讨，欢迎联系：qihahahqi@163.com

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-green?logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-orange?logo=mysql)
![License](https://img.shields.io/badge/License-MIT-yellow)

**一套完整的个人投资理财管理系统**

[功能特性](#功能特性) • [快速部署](#快速部署) • [使用文档](#使用文档)

</div>

---

## 简介

投资理财管理系统是一个基于 Python + Flask + MySQL 的全栈应用，帮助投资者科学管理投资组合、跟踪交易记录、分析收益风险、判断市场估值，并利用大模型 AI 生成投资建议。

### 核心理念

**为什么不依赖 AI 投资建议？**

市面上的 AI 投资分析工具存在明显局限性：

| 问题 | 表现 |
|-----|------|
| 短视 | 只关注眼前新闻，缺乏长远规划 |
| 大众化 | 回答千篇一律，缺乏针对性 |
| 脱离实际 | 不考虑个人持仓、投资策略、风险承受能力 |
| 无法落地 | 给出建议却无法转化为可执行的操作规则 |

**我们的理念：建立属于自己的投资操作系统**

- **不求 100% 盈利**：追求最大化胜率，而非虚无缥缈的完美预测
- **拒绝跟风**：不因市场噪音而偏离自己的策略
- **避免挂在高点**：纪律性操作，不追涨杀跌
- **杜绝想当然**：每一步操作都有依据，而非凭感觉

本系统的目标：**帮你建立一套符合自身情况的、可执行的、有纪律的投资操作系统**——什么时候买、什么时候加仓减仓、什么时候止盈止损，都由系统根据你的策略参数给出明确指引，而非依赖 AI 的模糊建议。

---

**如果你认同这个理念，欢迎交流：**

- 邮箱：qihahahqi@163.com
- GitHub Issues：[提交问题或建议](https://github.com/yourusername/financial-management-system/issues)

---

## 功能特性

| 功能模块 | 描述 |
|---------|------|
| 持仓管理 | 多类型资产管理、实时收益计算、持仓分布可视化 |
| 交易记录 | 完整交易历史、自动更新成本、交易统计分析 |
| 收益分析 | 收益率计算、最大回撤、夏普比率、盈亏分布 |
| 估值判断 | PE/PB 百分位分析、估值等级、操作建议 |
| 策略回测 | 6种策略模拟、金字塔加仓验证、策略对比分析、历史保存 |
| AI 分析 | 异步任务模式、多维度分析、风险评估、进度实时追踪 |
| 多账户 | 支持多账户管理、数据隔离 |
| 数据同步 | 自动获取实时价格、定时同步 |
| 数据导入导出 | Excel/CSV 格式支持 |

---

## 技术栈

| 层级 | 技术 |
|-----|------|
| 前端 | HTML5 + CSS3 + JavaScript (原生) |
| 后端 | Python 3.8+ + Flask 2.0+ |
| 数据库 | MySQL 8.0+ |
| ORM | SQLAlchemy |
| 图表 | Chart.js |
| AI | OpenAI API / Anthropic API / 兼容接口 |

---

## 快速部署

### 环境要求

| 项目 | 要求 |
|-----|------|
| 操作系统 | Windows 10+ / Linux / macOS |
| Python | 3.8 或更高版本 |
| MySQL | 8.0 或更高版本 |
| 浏览器 | Chrome、Firefox、Edge 等现代浏览器 |

### Linux / macOS 一键部署

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/financial-management-system.git
cd financial-management-system

# 2. 初始化数据库（MySQL 需要先安装）
mysql -u root -p < init_database.sql

# 3. 启动服务（首次会自动创建虚拟环境并安装依赖）
chmod +x start.sh
./start.sh init   # 初始化数据库表结构和默认用户
./start.sh        # 开发模式启动

# 访问 http://localhost:5001
# 默认用户名: admin  密码: admin123
```

### Windows 一键部署

```cmd
# 1. 克隆项目（或下载 ZIP 解压）
git clone https://github.com/yourusername/financial-management-system.git
cd financial-management-system

# 2. 初始化数据库（在 MySQL 客户端或命令行执行）
# 方法一：MySQL 命令行
mysql -u root -p < init_database.sql

# 方法二：在 MySQL Workbench 或命令行中执行 init_database.sql 内容

# 3. 双击运行 start.bat 或在命令行执行：
start.bat init     # 初始化数据库表结构和默认用户
start.bat          # 开发模式启动

# 访问 http://localhost:5001
# 默认用户名: admin  密码: admin123
```

### 启动脚本说明

| 命令 | Linux/Mac | Windows | 说明 |
|-----|-----------|---------|------|
| 开发模式 | `./start.sh` | `start.bat` | 前台运行，方便调试 |
| 生产模式 | `./start.sh prod` | `start.bat prod` | 使用 Gunicorn |
| 初始化数据库 | `./start.sh init` | `start.bat init` | 创建表结构 |
| 停止服务 | `./start.sh stop` | Ctrl+C | 仅 Linux/Mac 支持 |

### 手动部署步骤

#### 1. 创建数据库

```sql
CREATE DATABASE myapp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'devuser'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON myapp.* TO 'devuser'@'localhost';
FLUSH PRIVILEGES;
```

#### 2. 创建虚拟环境

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows (CMD)
python -m venv venv
venv\Scripts\activate.bat

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置系统

```bash
# Linux/macOS
cp config/config.yaml.example config/config.yaml
vim config/config.yaml

# Windows
copy config\config.yaml.example config\config.yaml
notepad config\config.yaml
```

修改以下配置：
- 数据库连接信息（host、user、password）
- JWT 密钥（生产环境必须修改）
- AI API Key（可选）

#### 5. 初始化数据库

```bash
python init_db.py
```

#### 6. 启动服务

```bash
# 开发模式（所有平台）
python run.py

# 生产模式（Linux/macOS）
gunicorn -c gunicorn_config.py run:app

# 生产模式（Windows）
python -m gunicorn -c gunicorn_config.py run:app
# 或使用 waitress（Windows 推荐）
pip install waitress
waitress-serve --port=5001 run:app
```

---

## 服务器部署指南

### 生产环境部署

#### 1. 系统准备

```bash
# 安装 Python 3.8+ 和 MySQL 8.0+
sudo apt update
sudo apt install python3 python3-pip python3-venv mysql-server

# 启动 MySQL
sudo systemctl start mysql
sudo systemctl enable mysql
```

#### 2. 创建数据库

```bash
sudo mysql -u root -p
```

```sql
CREATE DATABASE myapp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'devuser'@'localhost' IDENTIFIED BY 'YOUR_SECURE_PASSWORD';
GRANT ALL PRIVILEGES ON myapp.* TO 'devuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 3. 部署应用

```bash
# 上传项目到服务器（或使用 git clone）
cd /opt
git clone https://github.com/yourusername/financial-management-system.git
cd financial-management-system

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制并修改配置
cp config/config.yaml.example config/config.yaml
vim config/config.yaml  # 修改数据库密码、JWT密钥、API Key等

# 初始化数据库
python init_db.py

# 创建日志目录
mkdir -p logs
```

#### 4. 配置 Systemd 服务

```bash
sudo vim /etc/systemd/system/financial-app.service
```

写入以下内容：

```ini
[Unit]
Description=Financial Management System
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/financial-management-system
Environment="PATH=/opt/financial-management-system/venv/bin"
ExecStart=/opt/financial-management-system/venv/bin/gunicorn -c gunicorn_config.py run:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl daemon-reload
sudo systemctl start financial-app
sudo systemctl enable financial-app

# 查看状态
sudo systemctl status financial-app
```

#### 5. 配置 Nginx 反向代理（可选）

```bash
sudo apt install nginx
sudo vim /etc/nginx/sites-available/financial-app
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/financial-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 防火墙配置

```bash
# 开放端口
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 5001  # 如果直接访问
sudo ufw enable
```

---

## 配置说明

### 数据库配置

```yaml
database:
  host: localhost
  port: 3306
  database: myapp
  user: devuser
  password: your_password
```

### AI 功能配置

```yaml
llm:
  enabled: true
  provider: "openai"     # openai / anthropic / deepseek / custom
  api_key: "your-key"
  model: "gpt-4"
```

### 金融数据源

```yaml
akshare:
  enabled: true          # 免费，无需配置

tushare:
  enabled: false
  token: "your-token"    # 需要注册获取
```

---

## 目录结构

```
financial-management-system/
├── backend/                 # 后端代码
│   └── app/
│       ├── api/            # API 接口（positions, trades, analysis 等）
│       ├── models/         # 数据模型
│       ├── services/       # 业务逻辑层
│       └── utils/          # 工具函数
├── frontend/               # 前端代码
│   ├── css/               # 样式
│   ├── js/                # JavaScript
│   └── index.html         # 主页面
├── config/                # 配置文件
│   ├── config.yaml        # 主配置（需创建）
│   └── config.yaml.example # 配置模板
├── docs/                  # 文档
│   └── 投资策略详解.md    # 策略参数说明
├── logs/                  # 日志目录
├── migrations/            # 数据库迁移脚本
├── run.py                 # 开发启动脚本
├── init_db.py             # 数据库初始化
├── init_database.sql      # 数据库创建 SQL
├── gunicorn_config.py     # 生产服务器配置
├── start.sh               # Linux/Mac 启动脚本
├── start.bat              # Windows 启动脚本
├── requirements.txt       # Python 依赖
├── README.md              # 项目文档
└── LICENSE                # MIT 许可证
```

---

## API 接口

所有 API 使用 `/api/v1` 前缀，需要登录认证（除 `/auth` 接口外）。

| 模块 | 端点 | 描述 |
|-----|------|------|
| 认证 | POST /auth/register | 用户注册 |
| 认证 | POST /auth/login | 用户登录 |
| 持仓 | GET/POST /positions | 持仓管理 |
| 交易 | GET/POST /trades | 交易记录 |
| 分析 | GET /analysis/profit | 收益分析 |
| 估值 | GET/POST /valuations | 估值判断 |
| 回测 | POST /backtest/run | 策略回测 |
| AI | POST /ai/analyze | AI 分析 |
| 账户 | GET/POST /accounts | 多账户管理 |

**小程序/移动端对接**：详见 [API接口文档.md](docs/API接口文档.md)

---

## 使用文档

### 首次使用

1. 使用默认账号登录：**用户名: admin / 密码: admin123**
2. ⚠️ **登录后立即修改密码**（点击头像 → 个人设置）
3. 进入「系统设置」配置 AI API Key（可选）
4. 在「账户管理」查看或创建投资账户
5. 在「持仓管理」添加持仓
6. 点击「同步价格」获取最新行情

### 策略回测

支持 6 种策略：

| 策略 | 适用行情 | 特点 |
|-----|---------|------|
| 双均线 | 趋势行情 | 简单稳定 |
| 布林带 | 震荡行情 | 区间操作 |
| RSI | 转折行情 | 超买超卖 |
| 动量 | 趋势行情 | 追涨杀跌 |
| 网格 | 震荡行情 | 自动套利 |
| 金字塔 | 长期持有 | 分档止盈加仓 |

详细参数配置见 [投资策略详解.md](docs/投资策略详解.md)

---

## 常见问题

### 1. 启动报错：数据库连接失败

检查 MySQL 服务是否启动，配置文件中数据库连接信息是否正确。

```bash
# Linux
sudo systemctl status mysql

# Windows - 在服务管理器中查看 MySQL 服务状态
# 或在命令行执行：
net start MySQL80
```

### 2. 启动报错：端口被占用

```bash
# Linux/macOS
lsof -i :5001
kill -9 <PID>

# Windows (CMD)
netstat -ano | findstr :5001
taskkill /PID <PID> /F

# Windows (PowerShell)
Get-NetTCPConnection -LocalPort 5001
Stop-Process -Id <PID>
```

### 3. Windows PowerShell 执行策略错误

```powershell
# 临时允许脚本执行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 4. AI 分析无响应

检查 `config.yaml` 中是否正确配置了 `llm.api_key`。

### 5. 价格同步失败

AKShare 数据源免费无需配置，Tushare 需要注册获取 Token。

### 6. Windows 中文乱码

确保：
- 文件编码为 UTF-8
- MySQL 数据库字符集为 utf8mb4
- 终端编码设置为 UTF-8（`chcp 65001`）

---

## 安全建议

1. **修改默认密码**：数据库密码、JWT 密钥
2. **启用 HTTPS**：生产环境使用 Nginx + Let's Encrypt
3. **定期备份**：备份数据库数据
4. **限制访问**：配置防火墙规则

---

## 更新日志

### v1.1.0 (2026-04-17)

- **AI 分析异步任务模式**：
  - 后台线程执行，切换页面不中断
  - 实时进度显示，维度状态追踪
  - 支持取消任务
  - 增量保存每个维度结果
- **回测历史保存**：
  - 自动保存回测结果
  - 支持查看、删除历史
  - UI 布局调整（结果在上，数据获取在下）
- **开源准备**：
  - 添加 CONTRIBUTING.md、CHANGELOG.md 等标准文件
  - GitHub Issue/PR 模板

### v1.0.0 (2026-03-26)

- 完整的持仓管理、交易记录功能
- 6种策略回测支持
- AI 多维度分析
- 多账户管理
- 自动价格同步
- 收益曲线和分布图表

---

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

---

## 免责声明

本系统仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。历史收益不代表未来表现。

---

<div align="center">

**如果这个项目对你有帮助，请给一个 Star ⭐**

</div>