# 投资理财管理系统 - 功能改进实现方案

## 一、AI 分析改为后台异步任务

### 1.1 设计目标

- 支持切换页面不打断分析
- 分析一个维度保存一个维度（增量保存）
- 失败的维度标记为"分析失败"，不影响其他维度
- 前端显示进度和状态

### 1.2 新增数据库表

#### 表1: AIAnalysisTask（分析任务表）

```sql
CREATE TABLE ai_analysis_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    position_id INT NULL COMMENT '持仓ID（单标的分析时）',
    analysis_type VARCHAR(20) COMMENT 'single/portfolio',
    symbol VARCHAR(20) NULL COMMENT '标的代码（单标的分析时）',
    dimensions TEXT COMMENT '分析维度JSON列表',
    status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending/running/completed/failed/cancelled',
    progress INT DEFAULT 0 COMMENT '进度百分比(0-100)',
    completed_dimensions INT DEFAULT 0 COMMENT '已完成维度数',
    total_dimensions INT DEFAULT 0 COMMENT '总维度数',
    overall_score INT NULL COMMENT '综合评分',
    model_provider VARCHAR(50),
    model_name VARCHAR(100),
    error_message TEXT NULL COMMENT '错误信息',
    started_at DATETIME NULL,
    completed_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_user_status (user_id, status),
    INDEX idx_created (created_at)
);
```

#### 表2: AIAnalysisDimension（维度分析结果表）

```sql
CREATE TABLE ai_analysis_dimensions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_id INT NOT NULL COMMENT '关联任务ID',
    user_id INT NOT NULL COMMENT '用户ID（便于直接查询）',
    dimension VARCHAR(50) NOT NULL COMMENT '维度标识',
    dimension_name VARCHAR(100) COMMENT '维度名称',
    analysis_content TEXT COMMENT '分析内容',
    score INT NULL COMMENT '该维度评分',
    status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending/running/completed/failed',
    error_message TEXT NULL COMMENT '错误信息',
    started_at DATETIME NULL,
    completed_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_task (task_id),
    INDEX idx_user_task (user_id, task_id),
    UNIQUE KEY uix_task_dimension (task_id, dimension)
);
```

### 1.3 后端 API 修改点

#### 修改文件: backend/app/api/ai.py

**新增接口:**

1. `POST /ai/analyze/start` - 启动异步分析任务
   - 返回 task_id
   - 创建任务记录和维度子任务记录

2. `GET /ai/analyze/status/<task_id>` - 查询任务进度
   - 返回 status, progress, completed_dimensions, total_dimensions
   - 返回各维度状态列表

3. `GET /ai/analyze/result/<task_id>` - 获取完整分析结果
   - 返回所有维度结果和综合评分

4. `GET /ai/tasks` - 获取用户的任务列表
   - 支持分页、状态筛选

5. `POST /ai/tasks/<task_id>/cancel` - 取消正在进行的任务

**修改逻辑:**

- 原有的 `/ai/analyze` 改为异步任务启动入口
- 后台任务使用 Celery 或线程池执行（建议使用 threading + queue 简化依赖）
- 每完成一个维度立即写入数据库

#### 新增文件: backend/app/services/ai_task_service.py

```python
# 核心逻辑
class AIAnalysisTaskService:
    def start_analysis_task(user_id, analysis_type, dimensions, position_id=None):
        # 1. 创建任务记录
        # 2. 创建维度子任务记录
        # 3. 启动后台线程执行分析
        # 4. 返回 task_id
    
    def run_dimension_analysis(task_id, dimension):
        # 1. 更新维度状态为 running
        # 2. 调用 LLMService 分析
        # 3. 成功：保存结果，更新状态为 completed
        # 4. 失败：保存错误信息，更新状态为 failed
        # 5. 更新任务进度
    
    def get_task_progress(task_id):
        # 返回进度信息
    
    def cancel_task(task_id):
        # 设置取消标记，停止后续分析
```

### 1.4 前端修改点

#### 修改文件: frontend/js/app.js

**修改 runAIAnalysis 函数:**

```javascript
async function runAIAnalysis() {
    // 1. 调用启动接口获取 task_id
    const result = await utils.request(`${API_BASE}/ai/analyze/start`, {
        method: 'POST',
        body: JSON.stringify(data)
    });
    
    const taskId = result.task_id;
    
    // 2. 显示进度容器
    showProgressContainer(taskId);
    
    // 3. 启动轮询
    startProgressPolling(taskId);
}

async function startProgressPolling(taskId) {
    const pollInterval = setInterval(async () => {
        const status = await utils.request(`${API_BASE}/ai/analyze/status/${taskId}`);
        
        // 更新进度显示
        updateProgressUI(status);
        
        // 增量更新已完成的维度结果
        updateCompletedDimensions(status.dimensions);
        
        // 任务完成或失败时停止轮询
        if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(pollInterval);
            showFinalResult(taskId);
        }
    }, 2000);  // 每2秒轮询
}
```

**新增 UI 元素:**

- 进度条容器（显示百分比和已完成维度数）
- 维度状态列表（每个维度显示：待分析/分析中/已完成/失败）
- 增量结果展示区域（分析完成立即显示）

#### 修改文件: frontend/index.html

在 AI 分析页面添加进度显示区域：

```html
<!-- AI 分析进度区域 -->
<div id="ai-progress-container" style="display: none;">
    <div class="card">
        <div class="card-header">
            <h3>分析进度</h3>
        </div>
        <div class="card-body">
            <div class="progress-bar">
                <div class="progress-fill" id="ai-progress-bar"></div>
                <span id="ai-progress-text">0%</span>
            </div>
            <div id="ai-dimension-status-list"></div>
        </div>
    </div>
</div>

<!-- 增量结果显示区域 -->
<div id="ai-incremental-results"></div>
```

---

## 二、策略回测改进

### 2.1 设计目标

- UI 布局调整：回测结果放到上面，数据获取放到下面
- 新增回测历史记录保存功能
- 按日期+标的+回测区间唯一标识，不可重复
- 支持查看和删除历史记录

### 2.2 新增数据库表

#### 表: BacktestHistory（回测历史表）

```sql
CREATE TABLE backtest_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    symbol VARCHAR(20) NOT NULL COMMENT '标的代码',
    symbol_name VARCHAR(100) COMMENT '标的名称',
    asset_type VARCHAR(20) DEFAULT 'stock' COMMENT 'stock/fund/etf',
    data_source VARCHAR(20) COMMENT '数据源',
    start_date DATE NOT NULL COMMENT '回测开始日期',
    end_date DATE NOT NULL COMMENT '回测结束日期',
    initial_capital DECIMAL(12,2) DEFAULT 100000 COMMENT '初始资金',
    strategies TEXT COMMENT '策略列表JSON',
    strategy_params TEXT COMMENT '策略参数JSON',
    result_data TEXT COMMENT '回测结果JSON',
    best_strategy VARCHAR(50) COMMENT '最佳策略',
    best_return DECIMAL(10,4) COMMENT '最佳收益率',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user (user_id),
    INDEX idx_symbol (symbol),
    INDEX idx_created (created_at),
    UNIQUE KEY uix_user_symbol_range (user_id, symbol, start_date, end_date)
);
```

### 2.3 后端 API 修改点

#### 修改文件: backend/app/api/backtest.py

**新增接口:**

1. `GET /backtest/history` - 获取回测历史列表
   - 支持分页、symbol 筛选

2. `GET /backtest/history/<id>` - 获取历史详情
   - 返回完整回测结果

3. `DELETE /backtest/history/<id>` - 删除历史记录

**修改逻辑:**

- `POST /backtest/run` 返回结果后，自动保存到 BacktestHistory
- 检查唯一约束，避免重复保存

#### 修改文件: backend/app/models/models.py

添加 BacktestHistory 模型类：

```python
class BacktestHistory(db.Model):
    __tablename__ = 'backtest_history'
    # 字段定义...
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'symbol', 'start_date', 'end_date', 
                            name='uix_user_symbol_range'),
    )
```

### 2.4 前端修改点

#### 修改文件: frontend/index.html

**UI 布局调整（行344-599）:**

调整为：
```
[回测结果]（上）
  - 显示最新回测结果
  - 快速切换查看历史记录
[回测历史]（新增）
  - 列表展示所有历史记录
  - 支持查看详情、删除
[回测参数]（中）
  - 标的选择、初始资金
  - 时间范围
  - 策略选择
[数据获取]（下）
  - 资产类型、数据源
  - 在线获取/本地导入
  - 已导入数据列表
```

#### 修改文件: frontend/js/app.js

**新增函数:**

```javascript
// 加载回测历史列表
async function loadBacktestHistory() {
    const result = await utils.request(`${API_BASE}/backtest/history`);
    renderBacktestHistoryList(result);
}

// 查看历史详情
async function viewBacktestHistory(historyId) {
    const result = await utils.request(`${API_BASE}/backtest/history/${historyId}`);
    renderBacktestResult(result.result_data);
}

// 删除历史记录
async function deleteBacktestHistory(historyId) {
    if (!confirm('确定要删除这条回测记录吗？')) return;
    await utils.request(`${API_BASE}/backtest/history/${historyId}`, {
        method: 'DELETE'
    });
    loadBacktestHistory();
}

// 运行回测后自动保存
async function runBacktest() {
    // ... 运行回测 ...
    const result = await utils.request(`${API_BASE}/backtest/run`, {...});
    
    // 显示结果（结果已自动保存到数据库）
    renderBacktestResult(result);
    
    // 刷新历史列表
    loadBacktestHistory();
}
```

---

## 三、项目开源准备

### 3.1 需新增的文件

#### 文件1: CONTRIBUTING.md

```markdown
# 贡献指南

感谢您考虑为本项目做出贡献！

## 如何贡献

### 报告问题
- 使用 GitHub Issues 提交问题
- 请提供详细的复现步骤和环境信息

### 提交代码
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 代码规范
- Python: 遵循 PEP 8 规范
- JavaScript: 使用 ES6+ 语法
- 提交前请确保测试通过

### 开发环境设置
详见 README.md 的部署指南
```

#### 文件2: CHANGELOG.md

```markdown
# 更新日志

## [1.1.0] - 待发布

### 新增
- AI 分析异步任务支持
- 回测历史记录保存功能
- 项目开源文档

### 改进
- 回测页面 UI 布局优化

## [1.0.0] - 2026-03-26

### 新增
- 完整的持仓管理功能
- 6种策略回测支持
- AI 多维度分析
- 多账户管理
- 自动价格同步
```

#### 文件3: CODE_OF_CONDUCT.md

```markdown
# 行为准则

## 我们的承诺
为营造开放和友好的环境，我们承诺...

## 标准
- 尊重不同观点
- 接受建设性批评
- 关注对社区最有利的事情

## 执行
违规行为可通过 GitHub Issues 报告
```

### 3.2 需新增的 .github 目录结构

```
.github/
├── ISSUE_TEMPLATE/
│   ├── bug_report.md       # Bug 报告模板
│   ├── feature_request.md  # 功能请求模板
│   └── question.md         # 问题讨论模板
└── PULL_REQUEST_TEMPLATE/
│   └── pull_request.md     # PR 模板
```

#### ISSUE_TEMPLATE/bug_report.md

```markdown
---
name: Bug 报告
about: 报告一个 Bug
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug 描述
请简要描述遇到的问题

## 复现步骤
1. 进入 '...'
2. 点击 '...'
3. 看到错误

## 预期行为
应该发生什么

## 环境信息
- 操作系统: 
- Python 版本: 
- 数据库版本: 
```

#### ISSUE_TEMPLATE/feature_request.md

```markdown
---
name: 功能请求
about: 提出新功能建议
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## 功能描述
请描述您希望添加的功能

## 使用场景
什么情况下需要这个功能

## 建议方案
如果有实现思路，请简要说明
```

#### PULL_REQUEST_TEMPLATE/pull_request.md

```markdown
## 更改描述
请简要描述本次更改的内容

## 更改类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 代码重构

## 测试情况
请说明如何测试了这些更改

## 相关 Issue
关联的 Issue 编号（如有）
```

### 3.3 README.md 更新要点

- 添加贡献者致谢章节
- 添加 Star History 图表（可选）
- 更新版本信息
- 添加项目徽章（如：开源协议、构建状态）
- 更新截图（如有）

### 3.4 config.yaml 安全检查

已排除敏感信息（通过 .gitignore）：
- `config/config.yaml` 已被排除
- `config.yaml.example` 无敏感信息

---

## 四、实现顺序建议

### Phase 1: AI 分析异步任务（高优先级）
1. 创建数据库表（AIAnalysisTask, AIAnalysisDimension）
2. 创建后端服务（ai_task_service.py）
3. 修改 API 接口
4. 修改前端轮询逻辑和 UI

### Phase 2: 回测改进（中优先级）
1. 创建数据库表（BacktestHistory）
2. 修改回测 API 保存逻辑
3. 添加历史查询/删除接口
4. 调整前端 UI 布局

### Phase 3: 开源准备（低优先级）
1. 创建 CONTRIBUTING.md
2. 创建 CHANGELOG.md
3. 创建 CODE_OF_CONDUCT.md
4. 创建 .github 目录和模板
5. 更新 README.md
6. 验证 .gitignore 排除敏感文件

---

## 五、依赖关系

- AI 异步任务：依赖数据库表创建
- 回测历史：依赖数据库表创建
- 开源文档：独立任务，无依赖

---

## 六、潜在风险

1. **AI 异步任务并发问题**：多用户同时分析可能资源竞争
   - 解决：使用任务队列限制并发数

2. **数据库迁移**：新增表需要迁移脚本
   - 解决：使用 Flask-Migrate 生成迁移

3. **前端轮询频率**：过于频繁可能增加服务器负担
   - 解决：使用指数退避策略

---

## 七、文件修改清单

| 文件路径 | 修改类型 | 说明 |
|---------|---------|------|
| backend/app/models/models.py | 修改 | 新增 AIAnalysisTask、AIAnalysisDimension、BacktestHistory 模型 |
| backend/app/models/__init__.py | 修改 | 导出新模型 |
| backend/app/api/ai.py | 修改 | 新增异步任务接口，修改原有接口 |
| backend/app/api/backtest.py | 修改 | 新增历史记录接口，修改回测保存逻辑 |
| backend/app/services/ai_task_service.py | 新增 | AI 异步任务服务 |
| backend/app/__init__.py | 修改 | 注册新蓝图（如需要） |
| frontend/js/app.js | 修改 | 新增轮询逻辑、进度显示、历史记录功能 |
| frontend/index.html | 修改 | 调整回测页面布局、新增进度区域 |
| CONTRIBUTING.md | 新增 | 贡献指南 |
| CHANGELOG.md | 新增 | 更新日志 |
| CODE_OF_CONDUCT.md | 新增 | 行为准则 |
| .github/ISSUE_TEMPLATE/bug_report.md | 新增 | Bug 报告模板 |
| .github/ISSUE_TEMPLATE/feature_request.md | 新增 | 功能请求模板 |
| .github/PULL_REQUEST_TEMPLATE/pull_request.md | 新增 | PR 模板 |
| README.md | 修改 | 添加贡献者、更新版本 |

---

### Critical Files for Implementation

List 3-5 files most critical for implementing this plan:
- /home/test/financial-management-system/backend/app/models/models.py
- /home/test/financial-management-system/backend/app/api/ai.py
- /home/test/financial-management-system/backend/app/api/backtest.py
- /home/test/financial-management-system/frontend/js/app.js
- /home/test/financial-management-system/frontend/index.html