# 投资理财管理系统 - 分阶段技术升级实现方案

> 创建日期: 2026-04-02
> 状态: 规划阶段

---

## 概述

本方案针对投资理财管理系统的技术升级需求，分为四个阶段实施：

1. **阶段一**: Flask-Migrate 统一数据库迁移
2. **阶段二**: Pydantic 请求参数验证
3. **阶段三**: API 限流和日志审计系统
4. **阶段四**: 前端框架迁移评估与实施

---

## 阶段一: Flask-Migrate 统一数据库迁移

### 1.1 当前状态分析

**现有迁移方式:**
- `migrations/` 目录: 4个 SQL 脚本 (add_account_support.sql, add_user_auth.sql, add_admin_and_backtest.sql, fix_configs_unique_constraint.sql)
- `backend/migrations/` 目录: 5个 Python 脚本 (add_financial_products.py, add_snapshot_unique_constraint.py, etc.)
- 使用 `db.create_all()` 初始化数据库 (init_db.py)
- 没有版本控制，无法追踪迁移历史
- 无法回滚迁移

**数据库模型:**
- 11 个模型: User, Account, Position, Trade, Valuation, CashPool, Config, PortfolioSnapshot, PriceHistory, AIAnalysisHistory, IncomeRecord
- 关系完整: 用户->账户->持仓->交易记录

### 1.2 实施步骤

#### 步骤 1.2.1: 安装 Flask-Migrate

**新增依赖 (requirements.txt):**
```
Flask-Migrate>=4.0.0
```

#### 步骤 1.2.2: 配置 Flask-Migrate

**修改文件: `/home/test/financial-management-system/backend/app/__init__.py`**

需要在 create_app 函数中添加:
```python
from flask_migrate import Migrate

migrate = Migrate()

def create_app(config=None):
    # ... 现有代码 ...
    
    # 初始化 Flask-Migrate
    migrate.init_app(app, db)
    
    # ... 现有代码 ...
```

#### 步骤 1.2.3: 初始化迁移环境

**执行命令:**
```bash
cd /home/test/financial-management-system
flask db init
```

**新增目录结构:**
- `migrations_flask/` (Flask-Migrate 标准目录，与现有 migrations/ 区分)
  - `env.py`
  - `script.py.mako`
  - `versions/` (空目录，存放迁移脚本)

#### 步骤 1.2.4: 创建基线迁移

由于数据库已有数据，需要创建基线迁移:

```bash
flask db stamp head  # 标记当前数据库状态为基线
```

#### 步骤 1.2.5: 整合现有迁移脚本

**策略:** 将现有手动迁移脚本转换为 Alembic 迁移

**步骤:**
1. 使用 `flask db migrate --message "baseline"` 生成初始迁移
2. 整合 SQL 迁移脚本中的变更
3. 整合 Python 迁移脚本中的变更
4. 添加数据迁移逻辑（如果需要）

#### 步骤 1.2.6: 更新初始化流程

**修改文件: `/home/test/financial-management-system/init_db.py`**

改为使用 Flask-Migrate 替代 db.create_all():
```python
def init_database():
    app = create_app()
    
    with app.app_context():
        # 使用 Flask-Migrate 替代 db.create_all()
        from flask_migrate import upgrade
        upgrade()
        
        # 初始化默认数据...
```

### 1.3 需要修改的文件

| 文件路径 | 操作 | 说明 |
|---------|------|------|
| `requirements.txt` | 修改 | 添加 Flask-Migrate>=4.0.0 |
| `backend/app/__init__.py` | 修改 | 导入并初始化 Migrate |
| `init_db.py` | 修改 | 使用 migrate 替代 create_all |

### 1.4 新增文件

| 文件路径 | 说明 |
|---------|------|
| `migrations_flask/env.py` | Alembic 环境配置 |
| `migrations_flask/script.py.mako` | 迁移脚本模板 |
| `migrations_flask/versions/*.py` | 各版本迁移脚本 |

### 1.5 测试验证

1. **全新环境测试:**
   ```bash
   # 删除并重建数据库
   mysql -e "DROP DATABASE IF EXISTS myapp;"
   mysql -e "CREATE DATABASE myapp;"
   
   # 执行迁移
   flask db upgrade
   ```

2. **现有环境测试:**
   ```bash
   flask db current  # 应显示: head (基线版本)
   ```

3. **回滚测试:**
   ```bash
   flask db downgrade -1
   flask db upgrade
   ```

---

## 阶段二: Pydantic 请求参数验证

### 2.1 当前状态分析

**现有验证方式:**
- 手动检查必填字段: `if field not in data`
- 手动类型转换: `int(data['quantity'])`, `float(data['price'])`
- 散落在各 API 文件中
- 无统一 schema 定义
- 验证逻辑重复

**示例 (backend/app/api/positions.py 第108-112行):**
```python
required = ['name', 'asset_type', 'quantity', 'cost_price']
for field in required:
    if field not in data:
        return error_response(f"缺少必填字段: {field}")
```

**API 模块:**
- 13 个 API 蓝图: auth, positions, trades, accounts, analysis, valuations, backtest, ai, configs, imports, charts, admin, datasource

### 2.2 实施步骤

#### 步骤 2.2.1: 安装 Pydantic

**新增依赖 (requirements.txt):**
```
pydantic>=2.0.0
```

#### 步骤 2.2.2: 创建 Schema 目录结构

**新增目录:**
```
backend/app/schemas/
    __init__.py
    base.py          # 基础 Schema 类
    auth.py          # 认证相关 Schema
    position.py      # 持仓相关 Schema
    trade.py         # 交易相关 Schema
    account.py       # 账户相关 Schema
    valuation.py     # 估值相关 Schema
    analysis.py      # 分析相关 Schema
    backtest.py      # 回测相关 Schema
    ai.py            # AI 分析相关 Schema
    config.py        # 配置相关 Schema
```

#### 步骤 2.2.3: 定义基础 Schema

**新增文件: `backend/app/schemas/base.py`**

定义基础 Schema 类，包含:
- BaseSchema: 基础配置 (from_attributes=True, str_strip_whitespace=True)
- BaseCreateSchema: 创建操作基类
- BaseUpdateSchema: 更新操作基类
- BaseResponseSchema: 响应基类

#### 步骤 2.2.4: 定义各模块 Schema

**持仓 Schema 示例 (`backend/app/schemas/position.py`):**

```python
class PositionCreate(BaseCreateSchema):
    name: str = Field(..., min_length=1, max_length=50)
    asset_type: str = Field(...)
    quantity: int = Field(..., gt=0)
    cost_price: float = Field(..., gt=0)
    symbol: Optional[str] = Field(None, max_length=20)
    current_price: Optional[float] = Field(None, ge=0)
    category: Optional[str] = None
    account_id: Optional[int] = 1
    # ... 其他字段

    @field_validator('asset_type')
    def validate_asset_type(cls, v):
        valid_types = ['stock', 'etf_index', 'etf_sector', 'fund', ...]
        if v not in valid_types:
            raise ValueError(f'无效的资产类型: {v}')
        return v
```

#### 步骤 2.2.5: 创建验证装饰器

**新增文件: `backend/app/utils/validation.py`**

```python
def validate_body(schema_class: Type):
    """验证请求体装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json()
                validated = schema_class.model_validate(data)
                request.validated_data = validated
            except ValidationError as e:
                # 格式化错误响应
                errors = {field: msg for ...}
                return jsonify({'success': False, 'errors': errors}), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_query(schema_class: Type):
    """验证查询参数装饰器"""
    # 类似实现
```

#### 步骤 2.2.6: 更新 API 使用 Schema

**修改示例 (`backend/app/api/positions.py`):**

```python
from ..schemas.position import PositionCreate, PositionUpdate
from ..utils.validation import validate_body

@positions_bp.route('/positions', methods=['POST'])
@login_required
@validate_body(PositionCreate)
def create_position():
    data = request.validated_data  # 已验证的数据
    # 使用 data 创建持仓...
```

### 2.3 需要修改的文件

| 文件路径 | 操作 | 说明 |
|---------|------|------|
| `requirements.txt` | 修改 | 添加 pydantic>=2.0.0 |
| `backend/app/api/auth.py` | 修改 | 使用 Schema 验证 |
| `backend/app/api/positions.py` | 修改 | 使用 Schema 验证 |
| `backend/app/api/trades.py` | 修改 | 使用 Schema 验证 |
| `backend/app/api/accounts.py` | 修改 | 使用 Schema 验证 |
| `backend/app/api/admin.py` | 修改 | 使用 Schema 验证 |
| `backend/app/api/valuations.py` | 修改 | 使用 Schema 验证 |
| `backend/app/api/ai.py` | 修改 | 使用 Schema 验证 |
| `backend/app/api/backtest.py` | 修改 | 使用 Schema 验证 |
| `backend/app/api/configs.py` | 修改 | 使用 Schema 验证 |
| `backend/app/api/analysis.py` | 修改 | 使用 Schema 验证 |
| `backend/app/api/charts.py` | 修改 | 使用 Schema 验证 |
| `backend/app/api/datasource.py` | 修改 | 使用 Schema 验证 |

### 2.4 新增文件

| 文件路径 | 说明 |
|---------|------|
| `backend/app/schemas/__init__.py` | Schema 包初始化 |
| `backend/app/schemas/base.py` | 基础 Schema 定义 |
| `backend/app/schemas/auth.py` | 认证相关 Schema |
| `backend/app/schemas/position.py` | 持仓相关 Schema |
| `backend/app/schemas/trade.py` | 交易相关 Schema |
| `backend/app/schemas/account.py` | 账户相关 Schema |
| `backend/app/schemas/valuation.py` | 估值相关 Schema |
| `backend/app/schemas/analysis.py` | 分析相关 Schema |
| `backend/app/schemas/backtest.py` | 回测相关 Schema |
| `backend/app/schemas/ai.py` | AI 分析相关 Schema |
| `backend/app/schemas/config.py` | 配置相关 Schema |
| `backend/app/utils/validation.py` | 验证装饰器 |

### 2.5 测试验证

1. **单元测试 Schema:**
```python
from backend.app.schemas.position import PositionCreate

# 正常情况
data = PositionCreate(name="沪深300ETF", asset_type="etf_index", quantity=1000, cost_price=4.0)

# 异常情况
try:
    PositionCreate(name="", asset_type="invalid", quantity=-1, cost_price=0)
except ValidationError as e:
    print(e.errors())
```

2. **API 测试:**
```bash
# 测试缺少必填字段
curl -X POST http://localhost:5000/api/v1/positions \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{"name": "test"}'
# 预期返回: {"success": false, "errors": {"asset_type": "...", "quantity": "..."}}
```

---

## 阶段三: API 限流和日志审计系统

### 3.1 当前状态分析

**现有状态:**
- 使用 `print()` 进行调试输出 (如 decorators.py 第19行)
- 只有基本 Python logging (未充分使用)
- 没有 before_request/after_request 钩子
- 没有请求日志记录
- 没有审计日志表
- 没有 API 限流

### 3.2 实施步骤

#### 步骤 3.2.1: 安装限流依赖

**新增依赖 (requirements.txt):**
```
Flask-Limiter>=3.0.0  # API 限流
```

#### 步骤 3.2.2: 创建审计日志模型

**新增模型文件: `backend/app/models/audit.py`**

```python
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50), nullable=False)  # CREATE/UPDATE/DELETE/LOGIN
    resource_type = db.Column(db.String(50), nullable=False)  # POSITION/TRADE/USER
    resource_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    request_method = db.Column(db.String(10))
    request_path = db.Column(db.String(255))
    response_status = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        db.Index('idx_audit_user', 'user_id'),
        db.Index('idx_audit_action', 'action'),
        db.Index('idx_audit_resource', 'resource_type', 'resource_id'),
        db.Index('idx_audit_time', 'created_at'),
    )
```

#### 步骤 3.2.3: 创建请求日志中间件

**新增文件: `backend/app/utils/logging.py`**

```python
def setup_request_logging(app):
    @app.before_request
    def before_request():
        g.start_time = time.time()
        g.request_id = request.headers.get('X-Request-ID', str(time.time_ns()))
        logger.info(f"[{g.request_id}] Request started: {request.method} {request.path}")
        
    @app.after_request
    def after_request(response):
        elapsed = time.time() - g.get('start_time', time.time())
        logger.info(f"[{g.request_id}] Completed: status={response.status_code} time={elapsed:.3f}s")
        response.headers['X-Request-ID'] = g.request_id
        response.headers['X-Response-Time'] = f"{elapsed:.3f}s"
        return response
```

#### 步骤 3.2.4: 创建审计日志服务

**新增文件: `backend/app/services/audit_service.py`**

```python
class AuditService:
    @staticmethod
    def log(action, resource_type, resource_id=None, details=None, user_id=None):
        # 获取当前用户和请求信息
        # 创建审计日志记录
        
    @staticmethod
    def log_create(resource_type, resource_id, data):
        # 记录创建操作
        
    @staticmethod
    def log_update(resource_type, resource_id, old_data, new_data):
        # 记录更新操作，对比变更
        
    @staticmethod
    def log_delete(resource_type, resource_id, data):
        # 记录删除操作
```

#### 步骤 3.2.5: 配置限流

**修改文件: `backend/app/__init__.py`**

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # 生产环境建议 Redis
)

def create_app(config=None):
    # ...
    limiter.init_app(app)
    
    from .utils.logging import setup_request_logging
    setup_request_logging(app)
```

#### 步骤 3.2.6: 应用限流到 API

**修改示例:**

```python
from .. import limiter

@positions_bp.route('/positions', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def create_position():
    # ...

@auth_bp.route('/auth/login', methods=['POST'])
@limiter.limit("5 per minute")  # 登录限流更严格
def login():
    # ...
```

#### 步骤 3.2.7: 添加审计日志到关键操作

**修改示例 (`backend/app/api/positions.py`):**

```python
from ..services.audit_service import AuditService

@positions_bp.route('/positions', methods=['POST'])
@login_required
def create_position():
    # 创建逻辑...
    db.session.commit()
    AuditService.log_create('POSITION', position.id, position.to_dict())
    return success_response(position.to_dict())

@positions_bp.route('/positions/<int:position_id>', methods=['PUT'])
@login_required
def update_position(position_id):
    old_data = position.to_dict()
    # 更新逻辑...
    db.session.commit()
    AuditService.log_update('POSITION', position.id, old_data, position.to_dict())
    return success_response(position.to_dict())

@positions_bp.route('/positions/<int:position_id>', methods=['DELETE'])
@login_required
def delete_position(position_id):
    data = position.to_dict()
    db.session.delete(position)
    db.session.commit()
    AuditService.log_delete('POSITION', position_id, data)
    return success_response(None, "持仓删除成功")
```

### 3.3 需要修改的文件

| 文件路径 | 操作 | 说明 |
|---------|------|------|
| `requirements.txt` | 修改 | 添加 Flask-Limiter>=3.0.0 |
| `backend/app/__init__.py` | 修改 | 添加限流和日志初始化 |
| `backend/app/api/auth.py` | 修改 | 添加限流和审计日志 |
| `backend/app/api/positions.py` | 修改 | 添加限流和审计日志 |
| `backend/app/api/trades.py` | 修改 | 添加限流和审计日志 |
| `backend/app/api/admin.py` | 修改 | 添加限流和审计日志 |
| `backend/app/api/accounts.py` | 修改 | 添加限流和审计日志 |
| `backend/app/api/valuations.py` | 修改 | 添加限流和审计日志 |
| `backend/app/api/configs.py` | 修改 | 添加限流和审计日志 |
| `backend/app/api/ai.py` | 修改 | 添加限流和审计日志 |
| `backend/app/api/backtest.py` | 修改 | 添加限流和审计日志 |
| `backend/app/api/imports.py` | 修改 | 添加限流和审计日志 |
| `backend/app/api/charts.py` | 修改 | 添加限流 |
| `backend/app/api/datasource.py` | 修改 | 添加限流 |
| `backend/app/models/__init__.py` | 修改 | 导入 AuditLog |
| `backend/app/utils/decorators.py` | 修改 | 移除 print() 调试 |

### 3.4 新增文件

| 文件路径 | 说明 |
|---------|------|
| `backend/app/models/audit.py` | 审计日志模型 |
| `backend/app/utils/logging.py` | 请求日志中间件 |
| `backend/app/services/audit_service.py` | 审计日志服务 |

### 3.5 数据库变更

**新增表: `audit_logs`**
- 字段: id, user_id, action, resource_type, resource_id, details, ip_address, user_agent, request_method, request_path, response_status, created_at
- 索引: idx_audit_user, idx_audit_action, idx_audit_resource, idx_audit_time

### 3.6 测试验证

1. **限流测试:**
```bash
for i in {1..60}; do
  curl -X GET http://localhost:5000/api/v1/positions -H "Authorization: Bearer token"
done
# 预期: 在达到限制后返回 429 Too Many Requests
```

2. **审计日志测试:**
```sql
SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;
```

3. **请求日志测试:**
```bash
tail -f logs/app.log
```

---

## 阶段四: 前端框架迁移评估

### 4.1 当前状态分析

**前端文件:**
- `frontend/js/app.js`: 3997 行 (约 38000 tokens)
- `frontend/js/auth.js`: 认证相关
- `frontend/js/charts.js`: 图表相关
- `frontend/js/admin.js`: 管理后台
- `frontend/css/style.css`: 样式
- `frontend/*.html`: 5个 HTML 页面 (index.html, login.html, register.html, admin.html, admin-login.html)

**问题:**
- 单文件过大 (app.js 3997 行)
- 缺乏模块化
- 状态管理分散
- 代码复用困难
- 维护成本高

### 4.2 技术选型评估

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **Vue 3 + Vite** | 学习曲线平缓，单文件组件清晰，渐进式迁移可行，中文社区活跃 | 需要构建工具 | ★★★★★ (5/5) |
| **React + Vite** | 组件化成熟，生态丰富 | 学习曲线陡峭，JSX 语法差异大 | ★★★★☆ (4/5) |
| **原生 JS + ES6 模块** | 无构建依赖，改动最小 | 无法根本解决状态管理问题 | ★★★☆☆ (3/5) |

**推荐: Vue 3 渐进式迁移**

### 4.3 Vue 3 项目结构设计

```
frontend-vue/
├── src/
│   ├── main.js                 # 应用入口
│   ├── App.vue                 # 根组件
│   ├── router/
│   │   └── index.js            # 路由配置
│   ├── stores/
│   │   ├── auth.js             # 认证状态 (Pinia)
│   │   ├── positions.js        # 持仓状态
│   │   ├── accounts.js         # 账户状态
│   │   └── ui.js               # UI 状态
│   ├── views/                  # 页面组件
│   │   ├── Dashboard.vue
│   │   ├── Positions.vue
│   │   ├── Trades.vue
│   │   ├── Analysis.vue
│   │   ├── Valuations.vue
│   │   ├── Backtest.vue
│   │   ├── AI.vue
│   │   ├── Settings.vue
│   │   └── Admin.vue
│   ├── components/             # 可复用组件
│   │   ├── common/             # 通用组件
│   │   │   ├── Navbar.vue
│   │   │   ├── Toast.vue
│   │   │   ├── Modal.vue
│   │   │   ├── Loading.vue
│   │   │   └── Card.vue
│   │   ├── positions/          # 持仓组件
│   │   ├── trades/             # 交易组件
│   │   ├── charts/             # 图表组件
│   │   └── forms/              # 表单组件
│   ├── utils/
│   │   ├── api.js              # API 请求封装
│   │   ├── format.js           # 格式化工具
│   │   ├── auth.js             # 认证工具
│   │   └── constants.js        # 常量定义
│   ├── styles/
│   │   ├── main.css
│   │   ├── variables.css
│   │   └── components.css
├── public/
│   └── index.html
├── vite.config.js
├── package.json
```

### 4.4 核心组件示例

**状态管理 (stores/positions.js):**
```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const usePositionsStore = defineStore('positions', () => {
  const positions = ref([])
  const loading = ref(false)
  const error = ref(null)
  
  const totalCost = computed(() => 
    positions.value.reduce((sum, p) => sum + p.total_cost, 0)
  )
  
  const marketValue = computed(() => 
    positions.value.reduce((sum, p) => sum + (p.market_value || p.total_cost), 0)
  )
  
  const profitRate = computed(() => 
    marketValue.value > 0 ? (marketValue.value - totalCost.value) / totalCost.value : 0
  )
  
  async function fetchPositions(accountId = null) { /* ... */ }
  async function createPosition(data) { /* ... */ }
  async function updatePosition(id, data) { /* ... */ }
  async function deletePosition(id) { /* ... */ }
  
  return { positions, loading, error, totalCost, marketValue, profitRate, ... }
})
```

### 4.5 迁移策略

**策略: 并行开发，逐步替换**

| 阶段 | 内容 | 文件数 | 时间估算 |
|------|------|--------|----------|
| 第一阶段 | 基础设施 (Vite配置, 路由, 状态管理, 认证) | ~5 | 1-2天 |
| 第二阶段 | 核心页面 (Dashboard, Positions, Trades) | ~15 | 3-5天 |
| 第三阶段 | 高级功能 (Analysis, Valuations, Backtest, AI) | ~10 | 2-3天 |
| 第四阶段 | 管理后台 (Admin, Settings) | ~8 | 2-3天 |
| 第五阶段 | 整合优化 (移除旧前端, 性能优化) | 测试 | 2-3天 |
| **总计** | | **~40文件** | **10-16天** |

### 4.6 依赖项

**前端依赖 (package.json):**
```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "axios": "^1.6.0",
    "flatpickr": "^4.6.0",
    "chart.js": "^4.4.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-vue": "^5.0.0"
  }
}
```

### 4.7 测试验证

1. **功能测试:** 所有 API 功能正常
2. **兼容性测试:** Chrome, Firefox, Safari, Edge
3. **性能测试:** 首屏加载 < 2s
4. **响应式测试:** 桌面端、平板端、移动端

---

## 实施顺序与依赖关系

```
阶段一 (Flask-Migrate) 
    |
    v
阶段二 (Pydantic 验证) ----> 阶段三 (限流+审计)
    |                           |
    v                           v
阶段四 (前端迁移)
```

**建议顺序:**
1. 阶段一和阶段二可以并行进行
2. 阶段三依赖阶段一的数据库迁移能力
3. 阶段四可以独立进行，但建议在后端稳定后开始

---

## 风险与缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 数据库迁移失败 | 数据丢失 | 先备份数据，测试环境验证 |
| Pydantic 验证过于严格 | API 行为变化 | 渐进式添加验证，充分测试 |
| 限流影响正常用户 | 用户投诉 | 监控限流日志，动态调整限制 |
| 前端迁移周期长 | 功能中断 | 并行运行，逐步切换 |

---

## 文件清单汇总

### 全部新增文件

| 文件路径 | 阶段 |
|---------|------|
| `migrations_flask/env.py` | 一 |
| `migrations_flask/script.py.mako` | 一 |
| `migrations_flask/versions/*.py` | 一 |
| `backend/app/schemas/*.py` (11个文件) | 二 |
| `backend/app/utils/validation.py` | 二 |
| `backend/app/models/audit.py` | 三 |
| `backend/app/utils/logging.py` | 三 |
| `backend/app/services/audit_service.py` | 三 |
| `frontend-vue/src/*` (~40个文件) | 四 |

### 全部修改文件

| 文件路径 | 阶段 |
|---------|------|
| `requirements.txt` | 一/二/三 |
| `backend/app/__init__.py` | 一/三 |
| `init_db.py` | 一 |
| `backend/app/api/*.py` (13个文件) | 二/三 |
| `backend/app/models/__init__.py` | 三 |
| `backend/app/utils/decorators.py` | 三 |

---

*本方案将随实施进展持续更新。*