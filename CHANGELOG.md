# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-04-17

### Added

- **AI 分析异步任务模式**: 
  - 后台线程执行，切换页面不中断分析
  - 实时进度显示，维度状态追踪（✅完成、🔄进行中、⏳待分析、❌失败）
  - 支持取消正在进行的分析任务
  - 增量保存每个维度结果，中途失败不丢失已完成结果
  - 新增 AIAnalysisTask、AIAnalysisDimension 数据表

- **回测历史保存**: 
  - 自动保存每次回测结果
  - 支持查看历史详情、删除历史记录
  - 唯一性约束防止重复保存相同参数的回测
  - UI 布局调整（结果区在上，参数区在中，数据获取区在下）

- **开源准备**:
  - 新增 CONTRIBUTING.md 贡献指南
  - 新增 CHANGELOG.md 版本日志
  - 新增 CODE_OF_CONDUCT.md 行为准则
  - 新增 SECURITY.md 安全政策
  - 新增 GitHub Issue 模板（bug_report.md、feature_request.md）
  - 新增 GitHub PR 模板

### Fixed

- 修复回测历史 results 字段长度问题（改为 LONGTEXT）
- 修复 session rollback 后访问 user 属性导致的错误

## [1.0.0] - 2026-03-26

### Added

- **持仓管理**: 多账户支持，股票/基金/债券等多种资产类型
- **交易记录**: 完整的交易历史追踪，自动计算成本
- **收益分析**: 实时收益率、最大回撤、夏普比率计算
- **估值判断**: PE/PB 百分位分析，估值等级判断
- **策略回测**: 
  - 多策略对比（双均线、布林带、RSI、动量、网格、金字塔）
  - 多数据源支持（AKShare、BaoStock、Tushare、本地导入）
  - 股票/基金回测支持
- **AI 分析**: 
  - 多维度分析（技术、基本面、资金面、板块等）
  - 多模型支持（OpenAI GPT-4、Claude、DeepSeek）
- **数据导入导出**: Excel/CSV 格式支持
- **多账户管理**: 自定义账户类型，数据隔离
- **收益曲线图表**: Chart.js 可视化

### Technical

- Flask 2.0+ 后端架构
- SQLAlchemy ORM
- 原生 JavaScript 前端
- Chart.js 图表库
- 多数据源适配器模式