# Contributing to 投资理财管理系统

感谢您考虑为投资理财管理系统做出贡献！

## 开发环境设置

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/financial-management-system.git
cd financial-management-system
```

### 2. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装 Python 依赖
pip install -r requirements.txt
```

### 3. 配置数据库

```bash
# 复制配置文件模板
cp config/config.yaml.example config/config.yaml

# 编辑配置文件，填入数据库连接信息
# 然后初始化数据库
python init_db.py
```

### 4. 启动开发服务器

```bash
./start.sh dev
```

访问 http://localhost:5000 查看应用。

## 代码规范

### Python 代码

- 使用 Python 3.8+ 特性
- 遵循 PEP 8 风格指南
- 函数和类添加类型注解
- 使用有意义的变量名

### 前端代码

- 使用原生 JavaScript，避免 jQuery
- CSS 类名使用语义化命名
- 保持代码整洁，添加必要注释

### Git 提交

- 提交信息使用中文，清晰描述变更内容
- 一个提交解决一个问题
- 提交前确保代码可运行

## Pull Request 流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m '添加某个精彩功能'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### PR 要求

- 描述清楚更改内容和目的
- 确保不引入新的 bug
- 添加必要的测试（如有）
- 更新相关文档

## 项目结构

```
financial-management-system/
├── backend/
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── models/        # 数据模型
│   │   ├── services/      # 业务逻辑
│   │   └── utils/         # 工具函数
│   └── migrations/        # 数据库迁移
├── frontend/
│   ├── css/               # 样式
│   ├── js/                # JavaScript
│   └── index.html         # 主页面
├── config/                # 配置文件
├── docs/                  # 文档
└── tests/                 # 测试（如有）
```

## 功能模块

- **持仓管理**: 多账户、多资产类型支持
- **交易记录**: 完整的交易历史追踪
- **收益分析**: 自动计算收益率、最大回撤等
- **估值判断**: PE/PB 百分位分析
- **策略回测**: 多策略对比、金字塔加仓验证
- **AI 分析**: 支持 OpenAI/Claude/DeepSeek

## 报告 Bug

请使用 GitHub Issues 报告问题，包含：

- 问题描述
- 复现步骤
- 期望行为
- 实际行为
- 系统环境信息

## 提问与讨论

如有疑问，可在 Issues 中提问，或参与 Discussions 讨论。

## 许可证

本项目采用 MIT 许可证，贡献的代码将同样采用该许可证。