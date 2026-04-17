/**
 * 投资理财管理系统 - 前端 JavaScript
 */

// API 基础路径
const API_BASE = '/api/v1';

// 持仓排序状态
let positionsSortBy = 'created_at';
let positionsSortOrder = 'desc';

// 工具函数
const utils = {
    // 格式化金额
    formatMoney(value) {
        if (value === null || value === undefined) return '--';
        return new Intl.NumberFormat('zh-CN', {
            style: 'currency',
            currency: 'CNY',
            minimumFractionDigits: 2
        }).format(value);
    },

    // 格式化百分比
    formatPercent(value, showSign = true) {
        if (value === null || value === undefined) return '--';
        const percent = (value * 100).toFixed(2);
        return showSign ? `${percent > 0 ? '+' : ''}${percent}%` : `${percent}%`;
    },

    // 格式化日期
    formatDate(dateStr) {
        if (!dateStr) return '--';
        return dateStr.split('T')[0];
    },

    // 显示 Toast
    showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    },

    // API 请求
    async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        const response = await Auth.fetch(url, mergedOptions);

        if (!response) {
            throw new Error('认证失败，请重新登录');
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.message || '请求失败');
        }

        return data.data;
    }
};

// 日期选择器模块
const DatePicker = {
    defaultConfig: {
        locale: 'zh',
        dateFormat: 'Y-m-d',
        allowInput: true,
        clickOpens: true
    },

    // 初始化单个日期选择器
    init(selector, options = {}) {
        const config = { ...this.defaultConfig, ...options };
        return flatpickr(selector, config);
    },

    // 初始化日期范围选择器（开始和结束联动）
    initRange(startId, endId, options = {}) {
        const startConfig = {
            ...this.defaultConfig,
            ...options,
            onChange: function(selectedDates) {
                if (selectedDates[0]) {
                    const endPicker = document.querySelector(`#${endId}`)?._flatpickr;
                    if (endPicker) {
                        endPicker.set('minDate', selectedDates[0]);
                    }
                }
            }
        };

        const endConfig = {
            ...this.defaultConfig,
            ...options,
            onChange: function(selectedDates) {
                if (selectedDates[0]) {
                    const startPicker = document.querySelector(`#${startId}`)?._flatpickr;
                    if (startPicker) {
                        startPicker.set('maxDate', selectedDates[0]);
                    }
                }
            }
        };

        flatpickr(`#${startId}`, startConfig);
        flatpickr(`#${endId}`, endConfig);
    },

    // 设置日期范围
    setRange(startId, endId, startDate, endDate) {
        const startPicker = document.querySelector(`#${startId}`)?._flatpickr;
        const endPicker = document.querySelector(`#${endId}`)?._flatpickr;

        if (startPicker && startDate) {
            startPicker.setDate(startDate);
        }
        if (endPicker && endDate) {
            endPicker.setDate(endDate);
        }
    }
};

// 页面管理
const pageManager = {
    currentPage: 'dashboard',
    currentAccountId: 1,

    init() {
        // 绑定导航点击事件
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.showPage(page);
            });
        });

        // 加载账户列表
        this.loadAccounts();
    },

    async loadAccounts() {
        try {
            const accounts = await utils.request(`${API_BASE}/accounts`);
            const select = document.getElementById('account-select');
            select.innerHTML = '<option value="">全部账户</option>';

            accounts.forEach(acc => {
                const option = document.createElement('option');
                option.value = acc.id;
                option.textContent = acc.name;
                if (acc.id === this.currentAccountId) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
        } catch (error) {
            console.error('加载账户失败:', error);
        }
    },

    switchAccount(accountId) {
        this.currentAccountId = accountId ? parseInt(accountId) : null;
        // 刷新当前页面数据
        this.loadPageData(this.currentPage);
    },

    showPage(pageName) {
        // 更新导航状态
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.page === pageName) {
                item.classList.add('active');
            }
        });

        // 切换页面
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        document.getElementById(`page-${pageName}`).classList.add('active');

        this.currentPage = pageName;

        // 移动端关闭侧边栏
        const sidebar = document.querySelector('.sidebar');
        const overlay = document.querySelector('.sidebar-overlay');
        const menuToggle = document.querySelector('.menu-toggle');
        if (sidebar && sidebar.classList.contains('show')) {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
            menuToggle.classList.remove('active');
        }

        // 加载页面数据
        this.loadPageData(pageName);
    },

    async loadPageData(pageName) {
        switch (pageName) {
            case 'dashboard':
                await dashboardPage.load(this.currentAccountId);
                break;
            case 'positions':
                await positionsPage.load(this.currentAccountId);
                break;
            case 'trades':
                await tradesPage.load();
                break;
            case 'analysis':
                await analysisPage.load();
                break;
            case 'valuation':
                await valuationPage.load();
                break;
            case 'backtest':
                await backtestPage.load();
                break;
            case 'ai':
                await aiPage.load();
                break;
            case 'settings':
                await settingsPage.load();
                break;
        }
    }
};

// 首页模块
const dashboardPage = {
    async load(accountId = null) {
        try {
            const params = accountId ? `?account_id=${accountId}` : '';

            // 加载汇总数据
            const summary = await utils.request(`${API_BASE}/positions/summary${params}`);

            // 更新统计卡片
            document.getElementById('total-value').textContent = utils.formatMoney(summary.total_value);
            document.getElementById('total-cost').textContent = utils.formatMoney(summary.total_cost);
            document.getElementById('total-profit').textContent = utils.formatMoney(summary.total_profit);
            document.getElementById('profit-rate').textContent = utils.formatPercent(summary.total_profit_rate);

            // 设置收益卡片样式（盈利红色，亏损绿色）
            const totalProfitCard = document.getElementById('total-profit-card');
            const profitRateCard = document.getElementById('profit-rate-card');

            totalProfitCard.classList.remove('profit', 'loss');
            profitRateCard.classList.remove('profit', 'loss');

            if (summary.total_profit_rate >= 0) {
                totalProfitCard.classList.add('profit');
                profitRateCard.classList.add('profit');
            } else {
                totalProfitCard.classList.add('loss');
                profitRateCard.classList.add('loss');
            }

            // 更新时间
            document.getElementById('update-time').textContent = `更新时间: ${new Date().toLocaleString()}`;

            // 加载持仓列表
            await this.loadPositions(accountId);

            // 加载信号
            await this.loadSignals();

            // 加载图表 - 不传account_id让后端自动获取用户账户
            const daysInput = document.getElementById('profit-days');
            const days = daysInput ? parseInt(daysInput.value) : 30;
            await Charts.renderProfitCurve('profit-chart', accountId, parseInt(days));
            await Charts.renderDistribution('distribution-chart', accountId);

        } catch (error) {
            utils.showToast(error.message, 'error');
        }
    },

    async loadPositions(accountId = null) {
        // 构建请求参数
        let params = [];
        if (accountId) {
            params.push(`account_id=${accountId}`);
        }
        params.push(`sort_by=${positionsSortBy}`);
        params.push(`sort_order=${positionsSortOrder}`);

        const positions = await utils.request(`${API_BASE}/positions?${params.join('&')}`);
        const tbody = document.querySelector('#positions-table tbody');
        tbody.innerHTML = '';

        positions.forEach(p => {
            const tr = document.createElement('tr');
            const profitClass = p.profit_rate >= 0 ? 'profit' : 'loss';
            tr.innerHTML = `
                <td>${p.name}<br><small class="text-muted">${p.symbol}</small></td>
                <td><span class="tag">${this.getAssetTypeLabel(p.asset_type)}</span></td>
                <td>${p.quantity}</td>
                <td>${p.cost_price.toFixed(3)}</td>
                <td>${p.current_price ? p.current_price.toFixed(3) : '--'}</td>
                <td>${utils.formatMoney(p.market_value)}</td>
                <td class="${profitClass}">${utils.formatPercent(p.profit_rate)}</td>
                <td>
                    <button class="btn btn-icon" onclick="editPosition(${p.id})">✏️</button>
                    <button class="btn btn-icon" onclick="deletePosition(${p.id})">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // 更新排序图标
        this.updateSortIcons();
    },

    updateSortIcons() {
        // 更新表头排序图标
        const headers = document.querySelectorAll('#positions-table th.sortable');
        headers.forEach(th => {
            th.classList.remove('asc', 'desc');
        });

        // 找到当前排序的列并添加图标
        const sortByMap = {
            'market_value': 5,  // 市值列索引
            'profit_rate': 6    // 收益率列索引
        };

        if (sortByMap[positionsSortBy]) {
            const columnIndex = sortByMap[positionsSortBy];
            const header = document.querySelector(`#positions-table th:nth-child(${columnIndex + 1})`);
            if (header) {
                header.classList.add(positionsSortOrder);
            }
        }
    },

    async loadSignals() {
        const signals = await utils.request(`${API_BASE}/analysis/signals`);
        const container = document.getElementById('signals-list');
        container.innerHTML = '';

        // 显示所有持仓状态
        const allPositions = signals.all_positions || [];

        if (allPositions.length === 0) {
            container.innerHTML = '<div class="text-muted" style="padding: 20px; text-align: center;">暂无持仓数据</div>';
            return;
        }

        // 按收益率排序（盈利在前，亏损在后，按收益率绝对值排序）
        allPositions.sort((a, b) => {
            if (a.profit_rate >= 0 && b.profit_rate < 0) return -1;
            if (a.profit_rate < 0 && b.profit_rate >= 0) return 1;
            return b.profit_rate - a.profit_rate;
        });

        allPositions.forEach(p => {
            const div = document.createElement('div');
            const hasSignal = p.stop_profit_signal || p.add_position_signal;
            div.className = hasSignal ? (p.stop_profit_signal ? 'signal-item stop-profit' : 'signal-item add-position') : 'signal-item normal';

            // 构建状态信息：收益率 + 已加仓 + 已减仓
            const profitLabel = p.profit_rate >= 0 ? '收益率' : '浮亏';
            const profitValue = utils.formatPercent(p.profit_rate);
            const addRatioLabel = `已加仓${(p.add_position_ratio * 100).toFixed(0)}%`;
            const soldRatioLabel = `已减仓${(p.sold_ratio * 100).toFixed(0)}%`;

            // 建议信息（有信号时显示建议份额和金额）
            let suggestionHtml = '';
            if (hasSignal && p.suggestion) {
                suggestionHtml = `<div class="signal-desc">${p.suggestion}</div>`;
                // 如果有建议操作份额/金额，添加快捷操作按钮
                if (p.suggestion_quantity > 0 && p.suggestion_amount > 0) {
                    suggestionHtml += `
                        <div style="margin-top: 8px;">
                            <button class="btn btn-sm btn-outline" onclick="event.stopPropagation(); applySuggestion(${p.position_id}, '${p.symbol}', '${p.name}', ${p.current_price}, ${p.suggestion_quantity}, '${p.asset_type}', '${p.stop_profit_signal ? 'sell' : 'buy'}')">
                                快捷操作
                            </button>
                        </div>
                    `;
                }
            } else {
                // 无信号时显示持有状态
                suggestionHtml = `<div class="signal-desc" style="color: var(--text-muted);">${p.signal_level || '继续持有'}</div>`;
            }

            div.innerHTML = `
                <div class="signal-title">
                    ${hasSignal ? (p.stop_profit_signal ? '🔴' : '🟡') : '⚪'}
                    ${p.name} <small>${p.symbol}</small>
                    <span style="float: right; font-weight: 500; color: ${p.profit_rate >= 0 ? 'var(--danger-color)' : 'var(--success-color)'};">
                        ${profitValue}
                    </span>
                </div>
                <div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">
                    ${addRatioLabel} | ${soldRatioLabel}
                </div>
                ${suggestionHtml}
                <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">
                    持有${p.quantity}份 | 成本: ${p.cost_price.toFixed(3)} | 现价: ${p.current_price.toFixed(3)}
                </div>
            `;
            div.onclick = () => showPositionDetail(p.position_id);
            div.style.cursor = 'pointer';
            container.appendChild(div);
        });
    },

    getAssetTypeLabel(type) {
        const labels = {
            // 市价型产品
            'stock': '股票',
            'etf_index': '宽基ETF',
            'etf_sector': '行业ETF',
            'fund': '基金',
            'gold': '黄金',
            'silver': '白银',
            // 固定收益类
            'bank_deposit': '银行定期存款',
            'bank_current': '银行活期存款',
            'bank_wealth': '银行理财产品',
            'treasury_bond': '国债',
            'corporate_bond': '企业债',
            'money_fund': '货币基金',
            // 其他产品
            'insurance': '保险理财',
            'trust': '信托产品',
            'other': '其他'
        };
        return labels[type] || type;
    },

    getProductCategory(assetType) {
        const categories = {
            // 市价型
            'stock': 'market',
            'etf_index': 'market',
            'etf_sector': 'market',
            'fund': 'market',
            'gold': 'market',
            'silver': 'market',
            // 固定收益型
            'bank_deposit': 'fixed_income',
            'bank_current': 'fixed_income',
            'bank_wealth': 'fixed_income',
            'treasury_bond': 'fixed_income',
            'corporate_bond': 'fixed_income',
            'money_fund': 'fixed_income',
            // 手动录入型
            'insurance': 'manual',
            'trust': 'manual',
            'other': 'manual'
        };
        return categories[assetType] || 'market';
    },

    getAssetTypeGroups() {
        return [
            {
                group: '市价型产品',
                types: [
                    { value: 'stock', label: '股票' },
                    { value: 'etf_index', label: '宽基ETF' },
                    { value: 'etf_sector', label: '行业ETF' },
                    { value: 'fund', label: '基金' },
                    { value: 'gold', label: '黄金' },
                    { value: 'silver', label: '白银' }
                ]
            },
            {
                group: '固定收益类',
                types: [
                    { value: 'bank_deposit', label: '银行定期存款' },
                    { value: 'bank_current', label: '银行活期存款' },
                    { value: 'bank_wealth', label: '银行理财产品' },
                    { value: 'treasury_bond', label: '国债' },
                    { value: 'corporate_bond', label: '企业债' },
                    { value: 'money_fund', label: '货币基金' }
                ]
            },
            {
                group: '其他产品',
                types: [
                    { value: 'insurance', label: '保险理财' },
                    { value: 'trust', label: '信托产品' },
                    { value: 'other', label: '其他' }
                ]
            }
        ];
    },

    getProductParamFields() {
        return {
            interest_rate: { name: '年化利率', type: 'number', unit: '%', placeholder: '如: 3.5' },
            start_date: { name: '起息日', type: 'date' },
            end_date: { name: '到期日', type: 'date' },
            redeemable: { name: '可提前赎回', type: 'checkbox' },
            payment_cycle: {
                name: '付息方式', type: 'select',
                options: [
                    { value: 'at_maturity', label: '到期付息' },
                    { value: 'monthly', label: '按月付息' },
                    { value: 'quarterly', label: '按季付息' },
                    { value: 'yearly', label: '按年付息' }
                ]
            },
            interest_type: {
                name: '计息方式', type: 'select',
                options: [
                    { value: 'simple', label: '单利' },
                    { value: 'compound', label: '复利' }
                ]
            },
            issuer: { name: '发行机构', type: 'text', placeholder: '如: 工商银行' },
            risk_level: {
                name: '风险等级', type: 'select',
                options: [
                    { value: 'R1', label: 'R1-低风险' },
                    { value: 'R2', label: 'R2-中低风险' },
                    { value: 'R3', label: 'R3-中风险' },
                    { value: 'R4', label: 'R4-中高风险' },
                    { value: 'R5', label: 'R5-高风险' }
                ]
            },
            weight: { name: '重量', type: 'number', unit: '克', placeholder: '如: 10' },
            purity: { name: '纯度', type: 'number', placeholder: '如: 0.9999' },
            buy_channel: {
                name: '购买渠道', type: 'select',
                options: [
                    { value: 'bank', label: '银行' },
                    { value: 'platform', label: '交易平台' },
                    { value: 'physical', label: '实物购买' }
                ]
            }
        };
    },

    getFormFieldsForAssetType(assetType) {
        const fieldMapping = {
            'stock': [],
            'etf_index': [],
            'etf_sector': [],
            'fund': [],
            'gold': ['weight', 'purity', 'buy_channel'],
            'silver': ['weight', 'purity', 'buy_channel'],
            'bank_deposit': ['interest_rate', 'start_date', 'end_date', 'redeemable'],
            'bank_current': ['interest_rate'],
            'bank_wealth': ['interest_rate', 'start_date', 'end_date', 'redeemable', 'risk_level'],
            'treasury_bond': ['interest_rate', 'start_date', 'end_date', 'payment_cycle'],
            'corporate_bond': ['interest_rate', 'start_date', 'end_date', 'payment_cycle', 'issuer'],
            'money_fund': ['interest_rate'],
            'insurance': ['interest_rate', 'start_date', 'end_date', 'issuer'],
            'trust': ['interest_rate', 'start_date', 'end_date', 'issuer'],
            'other': []
        };
        return fieldMapping[assetType] || [];
    }
};

// 持仓管理页面
const positionsPage = {
    async load(accountId = null) {
        // 构建请求参数
        let params = [];
        if (accountId) {
            params.push(`account_id=${accountId}`);
        }
        params.push(`sort_by=${positionsSortBy}`);
        params.push(`sort_order=${positionsSortOrder}`);

        const positions = await utils.request(`${API_BASE}/positions?${params.join('&')}`);
        const tbody = document.querySelector('#positions-full-table tbody');
        tbody.innerHTML = '';

        positions.forEach(p => {
            const tr = document.createElement('tr');
            const profitClass = p.profit_rate >= 0 ? 'profit' : 'loss';
            tr.innerHTML = `
                <td><a href="#" onclick="showPositionDetail(${p.id}); return false;" style="color: var(--primary-color);">${p.symbol}</a></td>
                <td><a href="#" onclick="showPositionDetail(${p.id}); return false;">${p.name}</a></td>
                <td><span class="tag">${dashboardPage.getAssetTypeLabel(p.asset_type)}</span></td>
                <td>${p.category || '--'}</td>
                <td>${p.quantity}</td>
                <td>${p.cost_price.toFixed(3)}</td>
                <td>${p.current_price ? p.current_price.toFixed(3) : '--'}</td>
                <td>${utils.formatMoney(p.total_cost)}</td>
                <td>${utils.formatMoney(p.market_value)}</td>
                <td class="${profitClass}">${utils.formatPercent(p.profit_rate)}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="showPositionDetail(${p.id})">详情</button>
                    <button class="btn btn-sm btn-secondary" onclick="editPosition(${p.id})">编辑</button>
                    <button class="btn btn-sm btn-danger" onclick="deletePosition(${p.id})">删除</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // 更新排序图标
        this.updateSortIcons();
    },

    updateSortIcons() {
        // 更新表头排序图标
        const headers = document.querySelectorAll('#positions-full-table th.sortable');
        headers.forEach(th => {
            th.classList.remove('asc', 'desc');
        });

        // 找到当前排序的列并添加图标
        const sortByMap = {
            'total_cost': 7,   // 总成本列索引
            'market_value': 8, // 市值列索引
            'profit_rate': 9   // 收益率列索引
        };

        if (sortByMap[positionsSortBy]) {
            const columnIndex = sortByMap[positionsSortBy];
            const header = document.querySelector(`#positions-full-table th:nth-child(${columnIndex + 1})`);
            if (header) {
                header.classList.add(positionsSortOrder);
            }
        }
    }
};

// 交易记录页面
const tradesPage = {
    async load() {
        const data = await utils.request(`${API_BASE}/trades`);
        const tbody = document.querySelector('#trades-table tbody');
        tbody.innerHTML = '';

        data.items.forEach(t => {
            const tr = document.createElement('tr');
            const typeClass = t.trade_type === 'buy' ? 'tag success' : 'tag danger';
            const typeLabel = t.trade_type === 'buy' ? '买入' : '卖出';
            tr.innerHTML = `
                <td>${utils.formatDate(t.trade_date)}</td>
                <td>${t.symbol}</td>
                <td><span class="${typeClass}">${typeLabel}</span></td>
                <td>${t.quantity}</td>
                <td>${t.price.toFixed(3)}</td>
                <td>${utils.formatMoney(t.amount)}</td>
                <td>${t.reason || '--'}</td>
                <td>
                    <button class="btn btn-icon" onclick="deleteTrade(${t.id})">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }
};

// 收益分析页面
const analysisPage = {
    async load() {
        const data = await utils.request(`${API_BASE}/analysis/profit`);

        document.getElementById('analysis-total-cost').textContent = utils.formatMoney(data.total_cost);
        document.getElementById('analysis-total-value').textContent = utils.formatMoney(data.total_value);
        document.getElementById('analysis-profit').textContent = utils.formatMoney(data.total_profit);
        document.getElementById('analysis-count').textContent = data.position_count;

        // 显示详情
        const container = document.getElementById('analysis-details');
        container.innerHTML = '';

        data.details.forEach(d => {
            const div = document.createElement('div');
            div.className = 'signal-item';
            const profitClass = d.profit_rate >= 0 ? 'profit' : 'loss';
            // 获取已加仓和已减仓比例
            const addRatio = d.current_state?.add_position_ratio || 0;
            const soldRatio = d.current_state?.sold_ratio || 0;

            div.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${d.position.name}</strong>
                        <small class="text-muted" style="margin-left: 8px;">${d.position.symbol}</small>
                    </div>
                    <div class="${profitClass}" style="font-weight: 600;">
                        ${utils.formatPercent(d.profit_rate)}
                    </div>
                </div>
                <div style="margin-top: 4px; font-size: 12px; color: var(--text-secondary);">
                    已加仓${(addRatio * 100).toFixed(0)}% | 已减仓${(soldRatio * 100).toFixed(0)}%
                </div>
                <div style="margin-top: 8px; font-size: 12px; color: var(--text-secondary);">
                    成本: ${utils.formatMoney(d.total_cost)} | 市值: ${utils.formatMoney(d.market_value)} |
                    盈亏: <span class="${profitClass}">${utils.formatMoney(d.profit_amount)}</span>
                </div>
                ${d.signal_level !== '持有' && d.signal_level !== '观察' ?
                    `<div style="margin-top: 8px;"><span class="tag ${d.stop_profit_signal ? 'success' : 'warning'}">${d.signal_level}</span> ${d.suggestion}</div>` :
                    `<div style="margin-top: 8px; color: var(--text-muted);">${d.signal_level || '继续持有'}</div>`}
            `;
            container.appendChild(div);
        });
    }
};

// 估值判断页面
const valuationPage = {
    async load() {
        // 加载估值参考
        const ref = await utils.request(`${API_BASE}/valuations/reference`);
        this.showReference(ref);

        // 加载估值数据
        const valuations = await utils.request(`${API_BASE}/valuations`);
        const tbody = document.querySelector('#valuations-table tbody');
        tbody.innerHTML = '';

        valuations.forEach(v => {
            const tr = document.createElement('tr');
            const levelClass = this.getLevelClass(v.level);
            tr.innerHTML = `
                <td>${utils.formatDate(v.record_date)}</td>
                <td>${v.index_name}</td>
                <td>${v.pe ? v.pe.toFixed(2) : '--'}</td>
                <td>${v.pe_percentile ? v.pe_percentile.toFixed(1) + '%' : '--'}</td>
                <td>${v.pb ? v.pb.toFixed(2) : '--'}</td>
                <td><span class="tag ${levelClass}">${v.level || '--'}</span></td>
                <td>${v.score ? v.score.toFixed(1) : '--'}</td>
                <td>${v.suggestion || '--'}</td>
            `;
            tbody.appendChild(tr);
        });
    },

    showReference(ref) {
        const container = document.getElementById('valuation-reference');
        container.innerHTML = '';

        Object.entries(ref.reference).forEach(([name, data]) => {
            const div = document.createElement('div');
            div.className = 'signal-item';
            div.innerHTML = `
                <div style="font-weight: 600; margin-bottom: 8px;">${name}</div>
                <div style="font-size: 12px; color: var(--text-secondary);">
                    极低估: PE < ${data.pe_extremely_low} |
                    低估: PE < ${data.pe_low} |
                    合理: PE < ${data.pe_reasonable} |
                    高估: PE < ${data.pe_high}
                </div>
            `;
            container.appendChild(div);
        });
    },

    getLevelClass(level) {
        if (!level) return '';
        if (level.includes('极度低估') || level.includes('低估')) return 'success';
        if (level.includes('高估')) return 'danger';
        if (level.includes('合理偏高')) return 'warning';
        return '';
    }
};

// 下载估值数据模板
async function downloadValuationTemplate() {
    try {
        const response = await Auth.fetch(`${API_BASE}/valuations/template`);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = '估值数据导入模板.xlsx';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        utils.showToast('下载模板失败', 'error');
    }
}

// 导入估值数据
async function importValuations(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await Auth.fetch(`${API_BASE}/valuations/import`, {
            method: 'POST',
            body: formData
            // 不设置 Content-Type，让浏览器自动设置 multipart/form-data
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || '导入失败');
        }

        const result = await response.json();
        if (!result.success) {
            throw new Error(result.message || '导入失败');
        }

        utils.showToast(result.data.message || `成功导入 ${result.data.success_count} 条数据`);
        await valuationPage.load();
    } catch (error) {
        utils.showToast('导入失败: ' + error.message, 'error');
    }
}

// 导出估值数据
async function exportValuations() {
    try {
        const response = await Auth.fetch(`${API_BASE}/valuations/export`);
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.message || '导出失败');
        }
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `估值数据_${new Date().toISOString().slice(0, 10)}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        utils.showToast(error.message || '导出失败', 'error');
    }
}

// 绑定估值导入文件选择事件
document.addEventListener('DOMContentLoaded', function() {
    const valuationImportFile = document.getElementById('valuation-import-file');
    if (valuationImportFile) {
        valuationImportFile.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                importValuations(e.target.files[0]);
                e.target.value = ''; // 清空选择
            }
        });
    }
});

// 回测页面
const backtestPage = {
    strategies: [],
    dataSources: [],

    async load() {
        // 加载策略列表
        try {
            this.strategies = await utils.request(`${API_BASE}/backtest/strategies`);
            this.renderStrategies();
        } catch (error) {
            console.error('加载策略列表失败:', error);
        }

        // 加载数据源列表
        try {
            this.dataSources = await utils.request(`${API_BASE}/backtest/data-sources`);
            this.renderDataSources();
        } catch (error) {
            console.error('加载数据源列表失败:', error);
        }

        // 加载已导入的数据列表
        await loadImportedDataList();

        // 加载快速选择列表
        await loadQuickSelectSymbols();

        // 初始化日期选择器（使用Flatpickr）
        const today = new Date().toISOString().split('T')[0];
        const sixMonthsAgo = new Date(Date.now() - 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

        // 在线获取日期选择器
        DatePicker.initRange('backtest-fetch-start', 'backtest-fetch-end', {
            defaultDate: [sixMonthsAgo, today]
        });
        DatePicker.setRange('backtest-fetch-start', 'backtest-fetch-end', sixMonthsAgo, today);

        // 回测参数日期选择器
        DatePicker.initRange('backtest-start-date', 'backtest-end-date', {
            defaultDate: [sixMonthsAgo, today]
        });
        DatePicker.setRange('backtest-start-date', 'backtest-end-date', sixMonthsAgo, today);

        // 绑定快捷按钮事件
        this.bindQuickButtons();
    },

    renderStrategies() {
        const container = document.getElementById('strategy-checkboxes');
        if (!container) return;

        let html = '';
        this.strategies.forEach(s => {
            html += `
                <label class="checkbox-label">
                    <input type="checkbox" name="strategy" value="${s.value}" checked>
                    <span>${s.name}</span>
                    <small class="text-muted" style="margin-left: 8px;">${s.description || ''}</small>
                </label>
            `;
        });
        container.innerHTML = html;
    },

    renderDataSources() {
        const select = document.getElementById('backtest-data-source');
        const status = document.getElementById('ds-status');
        if (!select) return;

        let html = '';
        this.dataSources.forEach(ds => {
            if (ds.value === 'akshare' || ds.value === 'baostock') {
                html += `<option value="${ds.value}">${ds.name} (免费)</option>`;
            } else if (ds.value === 'tushare') {
                const available = ds.available ? '' : ' (未配置)';
                html += `<option value="tushare" ${!ds.available ? 'disabled' : ''}>${ds.name}${available}</option>`;
            } else if (ds.value === 'local') {
                const count = ds.count ? ` (${ds.count}条)` : '';
                html += `<option value="local">本地数据${count}</option>`;
            }
        });
        select.innerHTML = html;

        // 更新状态显示
        if (status) {
            const selectedSource = select.value;
            if (selectedSource === 'akshare' || selectedSource === 'baostock') {
                status.textContent = '免费';
                status.style.background = '#28a745';
            } else if (selectedSource === 'tushare') {
                status.textContent = '需要Token';
                status.style.background = '#ffc107';
            } else {
                status.textContent = '';
            }
        }
    },

    bindQuickButtons() {
        // 数据获取区域的快捷按钮
        document.querySelectorAll('#online-fetch-section .time-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('#online-fetch-section .time-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                backtestPage.setDateRangeByButton(this.dataset.range, 'backtest-fetch-start', 'backtest-fetch-end');
            });
        });

        // 回测参数区域的快捷按钮
        document.querySelectorAll('.quick-date-buttons .quick-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.quick-date-buttons .quick-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                backtestPage.setDateRangeByButton(this.dataset.range, 'backtest-start-date', 'backtest-end-date');
            });
        });
    },

    setDateRangeByButton(range, startId, endId) {
        const today = new Date();
        const end = today.toISOString().split('T')[0];
        let start;

        switch(range) {
            case '1m': start = new Date(new Date().setMonth(today.getMonth() - 1)); break;
            case '3m': start = new Date(new Date().setMonth(today.getMonth() - 3)); break;
            case '6m': start = new Date(new Date().setMonth(today.getMonth() - 6)); break;
            case '1y': start = new Date(new Date().setFullYear(today.getFullYear() - 1)); break;
            case '2y': start = new Date(new Date().setFullYear(today.getFullYear() - 2)); break;
            case '3y': start = new Date(new Date().setFullYear(today.getFullYear() - 3)); break;
            case '5y': start = new Date(new Date().setFullYear(today.getFullYear() - 5)); break;
            case 'all': start = new Date('2000-01-01'); break;
            default: start = new Date(new Date().setMonth(today.getMonth() - 6));
        }

        const startDateStr = start.toISOString().split('T')[0];

        // 设置flatpickr日期选择器（如果存在）
        const startPicker = document.querySelector(`#${startId}`)?._flatpickr;
        const endPicker = document.querySelector(`#${endId}`)?._flatpickr;

        if (startPicker) {
            startPicker.setDate(startDateStr);
        }
        if (endPicker) {
            endPicker.setDate(end);
        }

        // 同时设置原生input值（确保生效）
        const startInput = document.getElementById(startId);
        const endInput = document.getElementById(endId);
        if (startInput) {
            startInput.value = startDateStr;
        }
        if (endInput) {
            endInput.value = end;
        }
    },

    getSelectedStrategies() {
        const checkboxes = document.querySelectorAll('input[name="strategy"]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    },

    getStrategyParams() {
        const params = {};

        // 双均线参数
        const maShort = document.getElementById('param-ma-short')?.value;
        const maLong = document.getElementById('param-ma-long')?.value;
        if (maShort && maLong) {
            params['double_ma'] = { short: parseInt(maShort), long: parseInt(maLong) };
        }

        // 布林带参数
        const bollWindow = document.getElementById('param-boll-window')?.value;
        const bollK = document.getElementById('param-boll-k')?.value;
        if (bollWindow && bollK) {
            params['bollinger'] = { window: parseInt(bollWindow), k: parseFloat(bollK) };
        }

        // RSI参数
        const rsiPeriod = document.getElementById('param-rsi-period')?.value;
        const rsiOversold = document.getElementById('param-rsi-oversold')?.value;
        const rsiOverbought = document.getElementById('param-rsi-overbought')?.value;
        if (rsiPeriod) {
            params['rsi'] = {
                period: parseInt(rsiPeriod),
                oversold: parseInt(rsiOversold),
                overbought: parseInt(rsiOverbought)
            };
        }

        // 动量参数
        const momPeriod = document.getElementById('param-mom-period')?.value;
        const momThreshold = document.getElementById('param-mom-threshold')?.value;
        if (momPeriod) {
            params['momentum'] = { period: parseInt(momPeriod), threshold: parseFloat(momThreshold) };
        }

        // 网格参数
        const gridLevels = document.getElementById('param-grid-levels')?.value;
        const gridSpacing = document.getElementById('param-grid-spacing')?.value;
        if (gridLevels && gridSpacing) {
            params['grid'] = { levels: parseInt(gridLevels), spacing: parseFloat(gridSpacing) };
        }

        // 金字塔参数
        const pyrAddTimes = document.getElementById('param-pyr-add-times')?.value;
        const pyrAddPercent = document.getElementById('param-pyr-add-percent')?.value;
        const pyrStopProfit = document.getElementById('param-pyr-stop-profit')?.value;
        if (pyrAddTimes) {
            params['pyramid'] = {
                add_times: parseInt(pyrAddTimes),
                add_percent: parseFloat(pyrAddPercent),
                stop_profit: parseFloat(pyrStopProfit)
            };
        }

        return params;
    }
};

// AI 分析页面
const aiPage = {
    async load() {
        const status = await utils.request(`${API_BASE}/ai/status`);
        const container = document.getElementById('ai-status');

        container.innerHTML = `
            <div style="display: flex; gap: 16px; flex-wrap: wrap;">
                <div class="signal-item">
                    <div class="signal-title">状态</div>
                    <div>${status.enabled ? '✅ 已启用' : '❌ 未启用'}</div>
                </div>
                <div class="signal-item">
                    <div class="signal-title">提供商</div>
                    <div>${status.provider || '--'}</div>
                </div>
                <div class="signal-item">
                    <div class="signal-title">模型</div>
                    <div>${status.model || '--'}</div>
                </div>
                <div class="signal-item">
                    <div class="signal-title">API Key</div>
                    <div>${status.configured ? '✅ 已配置' : '❌ 未配置'}</div>
                </div>
            </div>
        `;

        // 加载持仓列表用于单标的分析
        await this.loadPositions();

        // 加载历史记录
        await this.loadHistory();
    },

    async loadPositions() {
        try {
            const positions = await utils.request(`${API_BASE}/positions`);
            const select = document.getElementById('ai-position-select');
            select.innerHTML = '<option value="">请选择持仓标的</option>';

            positions.forEach(p => {
                const option = document.createElement('option');
                option.value = p.id;
                option.textContent = `${p.name} (${p.symbol}) - ${utils.formatPercent(p.profit_rate)}`;
                select.appendChild(option);
            });
        } catch (error) {
            console.error('加载持仓列表失败:', error);
        }
    },

    async loadHistory() {
        try {
            // 加载两种历史：旧的分析历史和新的异步任务历史
            const oldHistory = await utils.request(`${API_BASE}/ai/history`);
            const taskHistory = await utils.request(`${API_BASE}/ai/tasks`);
            const container = document.getElementById('ai-history-list');

            // 合并历史记录
            const allHistory = [];

            // 旧历史记录
            if (oldHistory && oldHistory.length > 0) {
                oldHistory.forEach(h => {
                    allHistory.push({
                        id: h.id,
                        type: 'old',
                        created_at: h.created_at,
                        analysis_type: h.analysis_type,
                        symbol: h.symbol,
                        model_name: h.model_name,
                        overall_score: h.overall_score,
                        status: 'completed'
                    });
                });
            }

            // 新任务历史记录（只显示已完成的）
            if (taskHistory && taskHistory.length > 0) {
                taskHistory.forEach(t => {
                    if (t.status === 'completed' || t.status === 'failed') {
                        allHistory.push({
                            id: t.id,
                            type: 'task',
                            created_at: t.created_at,
                            analysis_type: t.analysis_type,
                            symbol: t.symbol,
                            model_name: t.model_name,
                            overall_score: t.overall_score,
                            status: t.status
                        });
                    }
                });
            }

            // 按时间排序
            allHistory.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

            if (allHistory.length === 0) {
                container.innerHTML = '<div class="text-muted" style="text-align: center; padding: 20px;">暂无历史记录</div>';
                return;
            }

            let html = '<table class="data-table"><thead><tr><th>时间</th><th>类型</th><th>标的</th><th>模型</th><th>评分</th><th>状态</th><th>操作</th></tr></thead><tbody>';
            allHistory.forEach(h => {
                const scoreDisplay = h.overall_score ? `<span class="tag ${h.overall_score >= 6 ? 'success' : h.overall_score >= 4 ? 'warning' : 'danger'}">${h.overall_score}/10</span>` : '--';
                const statusDisplay = h.status === 'completed' ? '<span class="tag success">完成</span>' : h.status === 'failed' ? '<span class="tag danger">失败</span>' : '<span class="tag">完成</span>';
                const viewFunc = h.type === 'task' ? `viewAITaskResult(${h.id})` : `viewAIHistory(${h.id})`;
                const deleteFunc = h.type === 'task' ? `deleteAITask(${h.id})` : `deleteAIHistory(${h.id})`;

                html += `
                    <tr>
                        <td>${utils.formatDate(h.created_at)}</td>
                        <td><span class="tag">${h.analysis_type === 'single' ? '单标的' : '全仓'}</span></td>
                        <td>${h.symbol || '全部持仓'}</td>
                        <td>${h.model_name || '--'}</td>
                        <td>${scoreDisplay}</td>
                        <td>${statusDisplay}</td>
                        <td>
                            <button class="btn btn-sm btn-secondary" onclick="${viewFunc}">查看</button>
                            <button class="btn btn-sm btn-danger" onclick="${deleteFunc}" style="margin-left: 4px;">删除</button>
                        </td>
                    </tr>
                `;
            });
            html += '</tbody></table>';
            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = '<div class="text-muted" style="text-align: center; padding: 20px;">加载历史记录失败</div>';
        }
    }
};

// 设置页面
const settingsPage = {
    async load() {
        const llmConfig = await utils.request(`${API_BASE}/configs/llm`);

        document.getElementById('llm-provider').value = llmConfig.provider || 'openai';
        document.getElementById('llm-model').value = llmConfig.model || 'gpt-4';
        document.getElementById('llm-base').value = llmConfig.api_base || '';
        document.getElementById('llm-temperature').value = llmConfig.temperature || 0.7;
        document.getElementById('llm-max-tokens').value = llmConfig.max_tokens || 2000;

        // 显示 API Key 状态
        const apiKeyInput = document.getElementById('llm-key');
        if (llmConfig.has_api_key) {
            apiKeyInput.value = '******';
            apiKeyInput.placeholder = '已配置（输入新值可修改）';
        } else {
            apiKeyInput.value = '';
            apiKeyInput.placeholder = 'sk-...';
        }

        // 策略配置
        const strategyConfig = await utils.request(`${API_BASE}/configs/strategy`);
        document.getElementById('strategy-stop-profit').value = strategyConfig.stop_profit_target || 0.20;
        document.getElementById('strategy-max-loss').value = strategyConfig.max_loss || 0.30;

        // Tushare配置
        await this.loadTushareConfig();

        // 数据源状态
        await this.loadDatasourceStatus();
    },

    async loadTushareConfig() {
        try {
            const tushareConfig = await utils.request(`${API_BASE}/configs/tushare`);
            const tokenInput = document.getElementById('tushare-token');
            const baseUrlInput = document.getElementById('tushare-base-url');
            const statusText = document.getElementById('tushare-status-text');

            // 检查元素是否存在（可能当前页面不在设置页面）
            if (!tokenInput || !baseUrlInput || !statusText) {
                console.log('Tushare配置元素不存在，跳过加载');
                return;
            }

            if (tushareConfig.has_token) {
                tokenInput.value = '******';
                tokenInput.placeholder = '已配置（输入新值可修改）';
                statusText.textContent = '状态: ✅ 已配置';
                statusText.parentElement.style.background = 'rgba(46, 204, 113, 0.1)';
            } else {
                tokenInput.value = '';
                tokenInput.placeholder = '输入Tushare Pro Token';
                statusText.textContent = '状态: ❌ 未配置';
                statusText.parentElement.style.background = 'rgba(220, 53, 69, 0.1)';
            }

            baseUrlInput.value = tushareConfig.base_url || 'https://api.tushare.pro';
        } catch (error) {
            console.error('加载Tushare配置失败:', error);
        }
    },

    async loadDatasourceStatus() {
        try {
            const result = await utils.request(`${API_BASE}/datasource/status`);

            // 更新股票数据源状态
            const stockTag = document.getElementById('stock-datasource-tag');
            const stockType = document.getElementById('stock-datasource-type');
            const stockStatus = document.getElementById('stock-datasource-status-text');

            if (stockTag && result.stock) {
                const stockConfig = result.stock;
                if (stockConfig.current === 'tushare' && stockConfig.sources.tushare.status === 'configured') {
                    stockTag.textContent = 'Tushare Pro';
                    stockTag.style.background = '#007bff';
                    if (stockType) stockType.value = 'tushare';
                    if (stockStatus) stockStatus.textContent = '状态: ✅ 使用用户配置的Tushare';
                } else {
                    stockTag.textContent = 'AKShare + BaoStock';
                    stockTag.style.background = '#28a745';
                    if (stockType) stockType.value = 'default';
                    if (stockStatus) stockStatus.textContent = '状态: ✅ 使用免费数据源';
                }
            }

            // 更新基金数据源状态
            const fundTag = document.getElementById('fund-datasource-tag');
            const fundType = document.getElementById('fund-datasource-type');
            const fundStatus = document.getElementById('fund-datasource-status-text');

            if (fundTag && result.fund) {
                const fundConfig = result.fund;
                if (fundConfig.current === 'tushare' && fundConfig.sources.tushare.status === 'configured') {
                    fundTag.textContent = 'Tushare Pro';
                    fundTag.style.background = '#007bff';
                    if (fundType) fundType.value = 'tushare';
                    if (fundStatus) fundStatus.textContent = '状态: ✅ 使用用户配置的Tushare';
                } else if (fundConfig.current === 'akshare') {
                    fundTag.textContent = 'AKShare';
                    fundTag.style.background = '#fd7e14';
                    if (fundType) fundType.value = 'akshare';
                    if (fundStatus) fundStatus.textContent = '状态: ✅ 优先使用AKShare';
                } else if (fundConfig.current === 'eastmoney') {
                    fundTag.textContent = '天天基金';
                    fundTag.style.background = '#17a2b8';
                    if (fundType) fundType.value = 'eastmoney';
                    if (fundStatus) fundStatus.textContent = '状态: ✅ 优先使用天天基金';
                } else {
                    fundTag.textContent = 'AKShare + 天天基金';
                    fundTag.style.background = '#28a745';
                    if (fundType) fundType.value = 'default';
                    if (fundStatus) fundStatus.textContent = '状态: ✅ 使用免费数据源（自动切换）';
                }
            }
        } catch (error) {
            console.error('加载数据源状态失败:', error);
        }
    }
};

// 模态框管理
const modalManager = {
    show(title, content, footer = '') {
        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-body').innerHTML = content;
        document.getElementById('modal-footer').innerHTML = footer;
        const overlay = document.getElementById('modal-overlay');
        overlay.classList.add('show');

        // 阻止modal内容区域的点击事件冒泡到overlay
        const modal = document.getElementById('modal-container');
        modal.addEventListener('click', (e) => {
            e.stopPropagation();
        }, { once: true });
    },

    close() {
        document.getElementById('modal-overlay').classList.remove('show');
    }
};

// 全局ESC关闭弹窗
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' || e.key === 'Esc') {
        // 关闭主弹窗
        const modalOverlay = document.getElementById('modal-overlay');
        if (modalOverlay && modalOverlay.classList.contains('show')) {
            closeModal();
            return;
        }
        // 关闭持仓详情弹窗
        const detailModal = document.getElementById('position-detail-modal');
        if (detailModal && detailModal.style.display === 'flex') {
            closePositionDetail();
            return;
        }
    }
});

// 显示持仓模态框
function showPositionModal(position = null) {
    const isEdit = position !== null;
    const title = isEdit ? '编辑持仓' : '新增持仓';

    // 生成资产类型选择器（分组显示）
    let assetTypeOptions = '';
    dashboardPage.getAssetTypeGroups().forEach(group => {
        assetTypeOptions += `<optgroup label="${group.group}">`;
        group.types.forEach(type => {
            const selected = isEdit && position.asset_type === type.value ? 'selected' : '';
            assetTypeOptions += `<option value="${type.value}" ${selected}>${type.label}</option>`;
        });
        assetTypeOptions += '</optgroup>';
    });

    // 获取当前资产类型的动态字段（编辑模式）
    let dynamicFieldsHtml = '';
    if (isEdit && position.asset_type) {
        dynamicFieldsHtml = renderDynamicFields(position.asset_type, position.product_params || {});
    }

    // 默认资产类型
    const defaultAssetType = isEdit ? position.asset_type : 'stock';
    const defaultCategory = dashboardPage.getProductCategory(defaultAssetType);

    const content = `
        <form id="position-form">
            <div class="form-grid">
                <div class="form-group" id="symbol-group">
                    <label id="symbol-label">产品代码</label>
                    <input type="text" name="symbol" id="symbol-input" class="form-input"
                           value="${isEdit ? position.symbol : ''}" placeholder="如: 000001">
                    <small id="symbol-hint" style="color: #666; font-size: 12px;"></small>
                </div>
                <div class="form-group">
                    <label>产品名称 *</label>
                    <input type="text" name="name" class="form-input" required
                           value="${isEdit ? position.name : ''}" placeholder="如: 招商银行定期存款">
                </div>
            </div>
            <div class="form-grid">
                <div class="form-group">
                    <label>资产类型 *</label>
                    <select name="asset_type" class="form-input" required onchange="onAssetTypeChange(this.value, ${isEdit ? JSON.stringify(position.product_params || {}) : 'null'})">
                        ${assetTypeOptions}
                    </select>
                </div>
                <div class="form-group">
                    <label>分类</label>
                    <select name="category" class="form-input">
                        <option value="">未分类</option>
                        <option value="core" ${isEdit && position.category === 'core' ? 'selected' : ''}>核心仓位</option>
                        <option value="satellite" ${isEdit && position.category === 'satellite' ? 'selected' : ''}>卫星仓位</option>
                        <option value="aggressive" ${isEdit && position.category === 'aggressive' ? 'selected' : ''}>进攻仓位</option>
                        <option value="stable" ${isEdit && position.category === 'stable' ? 'selected' : ''}>稳健仓位</option>
                    </select>
                </div>
            </div>
            <div class="form-grid">
                <div class="form-group">
                    <label id="quantity-label">数量/份额 *</label>
                    <input type="number" name="quantity" class="form-input" required min="1"
                           value="${isEdit ? position.quantity : '1'}">
                </div>
                <div class="form-group">
                    <label id="cost-label">买入价格/本金 *</label>
                    <input type="number" name="cost_price" class="form-input" required step="0.01"
                           value="${isEdit ? position.cost_price : ''}" placeholder="买入价格或本金金额">
                </div>
            </div>
            <div class="form-grid" id="current-price-row">
                <div class="form-group">
                    <label>当前价格</label>
                    <input type="number" name="current_price" class="form-input" step="0.0001"
                           value="${isEdit && position.current_price ? position.current_price : ''}">
                </div>
            </div>
            <!-- 动态字段区域 -->
            <div id="dynamic-fields">
                ${dynamicFieldsHtml}
            </div>
            <div class="form-group">
                <label>备注</label>
                <textarea name="notes" class="form-input" rows="2">${isEdit && position.notes ? position.notes : ''}</textarea>
            </div>
        </form>
    `;
    const footer = `
        <button class="btn btn-secondary" onclick="closeModal()">取消</button>
        <button class="btn btn-primary" onclick="savePosition(${isEdit ? position.id : null})">保存</button>
    `;
    modalManager.show(title, content, footer);

    // 初始化时触发一次资产类型变化
    if (!isEdit) {
        onAssetTypeChange('stock', null);
    }
}

// 资产类型变化时的动态字段渲染
function onAssetTypeChange(assetType, existingParams = null) {
    const category = dashboardPage.getProductCategory(assetType);
    const currentPriceRow = document.getElementById('current-price-row');
    const quantityLabel = document.getElementById('quantity-label');
    const costLabel = document.getElementById('cost-label');
    const dynamicFieldsContainer = document.getElementById('dynamic-fields');
    const symbolGroup = document.getElementById('symbol-group');
    const symbolLabel = document.getElementById('symbol-label');
    const symbolInput = document.getElementById('symbol-input');
    const symbolHint = document.getElementById('symbol-hint');

    // 根据产品类别调整标签和显示
    if (category === 'fixed_income' || category === 'manual') {
        currentPriceRow.style.display = 'none';
        quantityLabel.textContent = '数量/份额';
        costLabel.textContent = '本金金额 *';

        // 固定收益/手动产品：代码可选，显示提示
        symbolLabel.textContent = '产品代码';
        symbolInput.removeAttribute('required');
        symbolInput.placeholder = '可选，留空自动生成';
        symbolHint.textContent = '可自定义代码（如：GY001），留空系统自动生成';
        symbolHint.style.display = 'block';
    } else if (assetType === 'gold' || assetType === 'silver') {
        currentPriceRow.style.display = 'grid';
        quantityLabel.textContent = '重量(克)';
        costLabel.textContent = '买入单价 *';

        // 贵金属：代码可选
        symbolLabel.textContent = '产品代码';
        symbolInput.removeAttribute('required');
        symbolInput.placeholder = '可选，如 AU001';
        symbolHint.textContent = '可自定义代码，留空系统自动生成';
        symbolHint.style.display = 'block';
    } else {
        currentPriceRow.style.display = 'grid';
        quantityLabel.textContent = '数量/份额 *';
        costLabel.textContent = '成本价 *';

        // 市价产品：代码必填
        symbolLabel.textContent = '产品代码 *';
        symbolInput.setAttribute('required', 'required');
        symbolInput.placeholder = '如: 000001';
        symbolHint.textContent = '请输入股票/ETF/基金代码（纯数字）';
        symbolHint.style.display = 'block';
    }

    // 渲染动态字段
    dynamicFieldsContainer.innerHTML = renderDynamicFields(assetType, existingParams || {});
}

// 渲染动态字段
function renderDynamicFields(assetType, existingParams) {
    const fieldKeys = dashboardPage.getFormFieldsForAssetType(assetType);
    const allFields = dashboardPage.getProductParamFields();

    let html = '';
    if (fieldKeys.length > 0) {
        html = '<div class="form-grid" style="grid-template-columns: repeat(2, 1fr);">';
    }

    fieldKeys.forEach(key => {
        const field = allFields[key];
        if (!field) return;

        const value = existingParams[key] || '';
        const fieldId = `param_${key}`;

        html += `<div class="form-group"><label>${field.name}</label>`;

        switch (field.type) {
            case 'select':
                html += `<select name="params_${key}" id="${fieldId}" class="form-input">`;
                html += `<option value="">请选择</option>`;
                field.options.forEach(opt => {
                    const selected = value === opt.value ? 'selected' : '';
                    html += `<option value="${opt.value}" ${selected}>${opt.label}</option>`;
                });
                html += '</select>';
                break;

            case 'checkbox':
                const checked = value === true || value === 'true' ? 'checked' : '';
                html += `<label class="checkbox-label" style="display: flex; align-items: center; gap: 8px;">
                    <input type="checkbox" name="params_${key}" id="${fieldId}" ${checked}>
                    <span>${field.name}</span>
                </label>`;
                break;

            case 'date':
                html += `<input type="date" name="params_${key}" id="${fieldId}" class="form-input" value="${value}">`;
                break;

            default: // text, number
                const step = field.type === 'number' ? 'step="0.0001"' : '';
                const placeholder = field.placeholder ? `placeholder="${field.placeholder}"` : '';
                const unit = field.unit ? ` <span style="color: #666;">${field.unit}</span>` : '';
                html += `<input type="${field.type}" name="params_${key}" id="${fieldId}" class="form-input" ${step} ${placeholder} value="${value}">${unit}`;
        }

        html += '</div>';
    });

    if (fieldKeys.length > 0) {
        html += '</div>';
    }

    return html;
}

// 保存持仓
async function savePosition(id = null) {
    const form = document.getElementById('position-form');
    const formData = new FormData(form);
    const data = {};
    const params = {};

    // 分离基础字段和参数字段
    for (let [key, value] of formData.entries()) {
        if (key.startsWith('params_')) {
            params[key.substring(7)] = value;
        } else {
            data[key] = value;
        }
    }

    // 转换数值类型
    data.quantity = parseInt(data.quantity) || 1;
    data.cost_price = parseFloat(data.cost_price) || 0;

    // 设置产品类别
    data.product_category = dashboardPage.getProductCategory(data.asset_type);

    // 处理产品代码：非市价产品可自动生成
    if (!data.symbol || data.symbol.trim() === '') {
        if (data.product_category === 'fixed_income') {
            // 固定收益产品：FI_年月日_随机数
            const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
            const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
            data.symbol = `FI_${dateStr}_${random}`;
        } else if (data.product_category === 'manual') {
            // 手动录入产品：MF_年月日_随机数
            const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
            const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
            data.symbol = `MF_${dateStr}_${random}`;
        } else if (data.asset_type === 'gold') {
            // 黄金：AU_随机数
            const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
            data.symbol = `AU_${random}`;
        } else if (data.asset_type === 'silver') {
            // 白银：AG_随机数
            const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
            data.symbol = `AG_${random}`;
        }
    }

    // 添加产品参数
    if (Object.keys(params).length > 0) {
        // 处理复选框
        const checkboxFields = ['redeemable'];
        checkboxFields.forEach(field => {
            const checkbox = document.getElementById(`param_${field}`);
            if (checkbox) {
                params[field] = checkbox.checked;
            }
        });

        // 处理数值字段
        const numberFields = ['interest_rate', 'weight', 'purity'];
        numberFields.forEach(field => {
            if (params[field] !== undefined && params[field] !== '') {
                params[field] = parseFloat(params[field]);
            }
        });

        data.product_params = params;

        // 从参数中提取到期日和风险等级
        if (params.end_date) {
            data.mature_date = params.end_date;
        }
        if (params.risk_level) {
            data.risk_level = params.risk_level;
        }
    }

    try {
        if (id) {
            await utils.request(`${API_BASE}/positions/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
            utils.showToast('持仓更新成功');
        } else {
            await utils.request(`${API_BASE}/positions`, {
                method: 'POST',
                body: JSON.stringify(data)
            });
            utils.showToast('持仓创建成功');
        }
        closeModal();
        pageManager.loadPageData(pageManager.currentPage);
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 显示持仓详情
async function showPositionDetail(id) {
    const modal = document.getElementById('position-detail-modal');
    const body = document.getElementById('position-detail-body');
    const title = document.getElementById('position-detail-title');

    body.innerHTML = '<div class="loading">加载中...</div>';
    modal.style.display = 'flex';

    // 阻止modal内容区域的点击事件冒泡
    modal.querySelector('.modal').addEventListener('click', (e) => {
        e.stopPropagation();
    }, { once: true });

    try {
        const detail = await utils.request(`${API_BASE}/positions/${id}/detail`);
        const basic = detail.basic;
        const metrics = detail.metrics;
        const trades = detail.trades || [];
        const history = detail.history || [];

        title.textContent = `${basic.name} (${basic.symbol})`;

        const profitClass = basic.profit_rate >= 0 ? 'profit' : 'loss';
        const assetTypeLabel = {
            'etf_index': '宽基ETF',
            'etf_sector': '行业ETF',
            'fund': '基金',
            'stock': '股票'
        }[basic.asset_type] || basic.asset_type;

        let html = `
            <!-- 基础信息 -->
            <div class="card" style="margin-bottom: 16px;">
                <div class="card-header"><h4>基础信息</h4></div>
                <div class="card-body">
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">资产类型</div>
                            <div class="stat-value">${assetTypeLabel}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">持仓数量</div>
                            <div class="stat-value">${basic.quantity}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">成本价</div>
                            <div class="stat-value">${basic.cost_price.toFixed(3)}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">现价</div>
                            <div class="stat-value">${basic.current_price ? basic.current_price.toFixed(3) : '--'}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">总成本</div>
                            <div class="stat-value">${utils.formatMoney(basic.total_cost)}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">市值</div>
                            <div class="stat-value">${utils.formatMoney(basic.market_value)}</div>
                        </div>
                        <div class="stat-card ${profitClass}">
                            <div class="stat-label">收益率</div>
                            <div class="stat-value">${utils.formatPercent(basic.profit_rate)}</div>
                        </div>
                        <div class="stat-card ${profitClass}">
                            <div class="stat-label">盈亏金额</div>
                            <div class="stat-value">${utils.formatMoney(basic.profit_amount)}</div>
                        </div>
                    </div>
                    ${basic.notes ? `<div style="margin-top: 12px;"><strong>备注:</strong> ${basic.notes}</div>` : ''}
                </div>
            </div>

            <!-- 快捷操作 -->
            <div class="card" style="margin-bottom: 16px;">
                <div class="card-header"><h4>快捷操作</h4></div>
                <div class="card-body" style="display: flex; gap: 12px; flex-wrap: wrap;">
                    <button class="btn btn-success" onclick="showQuickTradeModal(${id}, '${basic.symbol}', '${basic.name}', 'buy', ${basic.current_price || basic.cost_price}, '${basic.asset_type}', ${basic.quantity})">📈 买入</button>
                    <button class="btn btn-danger" onclick="showQuickTradeModal(${id}, '${basic.symbol}', '${basic.name}', 'sell', ${basic.current_price || basic.cost_price}, '${basic.asset_type}', ${basic.quantity})">📉 卖出</button>
                    <button class="btn btn-secondary" onclick="editPosition(${id})">✏️ 编辑持仓</button>
                </div>
            </div>
        `;

        // 根据资产类型显示不同指标（带字段级加载状态）
        if (basic.asset_type === 'stock' && metrics) {
            const renderMetricValue = (value, formatter, fieldKey) => {
                if (value === null || value === undefined) {
                    return `<span class="loading-text" id="metric-${fieldKey}"><span class="mini-spinner"></span>加载中...</span>`;
                }
                return formatter ? formatter(value) : value;
            };

            html += `
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-header"><h4>估值指标</h4></div>
                    <div class="card-body">
                        <div class="stats-grid">
                            <div class="stat-card"><div class="stat-label">PE-TTM</div><div class="stat-value">${renderMetricValue(metrics.valuation?.pe_ttm, v => v.toFixed(2), 'pe_ttm')}</div></div>
                            <div class="stat-card"><div class="stat-label">PB</div><div class="stat-value">${renderMetricValue(metrics.valuation?.pb, v => v.toFixed(2), 'pb')}</div></div>
                            <div class="stat-card"><div class="stat-label">PEG</div><div class="stat-value">${renderMetricValue(metrics.valuation?.peg, v => v.toFixed(2), 'peg')}</div></div>
                            <div class="stat-card"><div class="stat-label">股息率</div><div class="stat-value">${renderMetricValue(metrics.valuation?.dividend_yield, v => (v * 100).toFixed(2) + '%', 'dividend_yield')}</div></div>
                        </div>
                    </div>
                </div>
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-header"><h4>盈利能力</h4></div>
                    <div class="card-body">
                        <div class="stats-grid">
                            <div class="stat-card"><div class="stat-label">ROE</div><div class="stat-value">${renderMetricValue(metrics.profitability?.roe, v => (v * 100).toFixed(2) + '%', 'roe')}</div></div>
                            <div class="stat-card"><div class="stat-label">毛利率</div><div class="stat-value">${renderMetricValue(metrics.profitability?.gross_margin, v => (v * 100).toFixed(2) + '%', 'gross_margin')}</div></div>
                            <div class="stat-card"><div class="stat-label">净利率</div><div class="stat-value">${renderMetricValue(metrics.profitability?.net_margin, v => (v * 100).toFixed(2) + '%', 'net_margin')}</div></div>
                            <div class="stat-card"><div class="stat-label">ROIC</div><div class="stat-value">${renderMetricValue(metrics.profitability?.roic, v => (v * 100).toFixed(2) + '%', 'roic')}</div></div>
                        </div>
                    </div>
                </div>
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-header"><h4>技术指标</h4></div>
                    <div class="card-body">
                        <div class="stats-grid">
                            <div class="stat-card"><div class="stat-label">MA5</div><div class="stat-value">${renderMetricValue(metrics.technical?.ma5, v => v.toFixed(3), 'ma5')}</div></div>
                            <div class="stat-card"><div class="stat-label">MA10</div><div class="stat-value">${renderMetricValue(metrics.technical?.ma10, v => v.toFixed(3), 'ma10')}</div></div>
                            <div class="stat-card"><div class="stat-label">MA20</div><div class="stat-value">${renderMetricValue(metrics.technical?.ma20, v => v.toFixed(3), 'ma20')}</div></div>
                            <div class="stat-card"><div class="stat-label">MA60</div><div class="stat-value">${renderMetricValue(metrics.technical?.ma60, v => v.toFixed(3), 'ma60')}</div></div>
                            <div class="stat-card"><div class="stat-label">换手率</div><div class="stat-value">${renderMetricValue(metrics.capital_flow?.turnover_rate, v => v.toFixed(2) + '%', 'turnover_rate')}</div></div>
                        </div>
                    </div>
                </div>
            `;
        } else if ((basic.asset_type === 'etf_index' || basic.asset_type === 'etf_sector') && metrics) {
            const renderMetricValue = (value, formatter, fieldKey) => {
                if (value === null || value === undefined) {
                    return `<span class="loading-text" id="metric-${fieldKey}"><span class="mini-spinner"></span>加载中...</span>`;
                }
                return formatter ? formatter(value) : value;
            };

            html += `
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-header"><h4>收益指标</h4></div>
                    <div class="card-body">
                        <div class="stats-grid">
                            <div class="stat-card"><div class="stat-label">近1月</div><div class="stat-value">${renderMetricValue(metrics.returns?.return_1m, v => v.toFixed(2) + '%', 'return_1m')}</div></div>
                            <div class="stat-card"><div class="stat-label">近3月</div><div class="stat-value">${renderMetricValue(metrics.returns?.return_3m, v => v.toFixed(2) + '%', 'return_3m')}</div></div>
                            <div class="stat-card"><div class="stat-label">近6月</div><div class="stat-value">${renderMetricValue(metrics.returns?.return_6m, v => v.toFixed(2) + '%', 'return_6m')}</div></div>
                            <div class="stat-card"><div class="stat-label">近1年</div><div class="stat-value">${renderMetricValue(metrics.returns?.return_1y, v => v.toFixed(2) + '%', 'return_1y')}</div></div>
                        </div>
                    </div>
                </div>
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-header"><h4>风险指标</h4></div>
                    <div class="card-body">
                        <div class="stats-grid">
                            <div class="stat-card"><div class="stat-label">最大回撤</div><div class="stat-value">${renderMetricValue(metrics.risk?.max_drawdown, v => v.toFixed(2) + '%', 'max_drawdown')}</div></div>
                            <div class="stat-card"><div class="stat-label">波动率</div><div class="stat-value">${renderMetricValue(metrics.risk?.volatility, v => v.toFixed(2) + '%', 'volatility')}</div></div>
                            <div class="stat-card"><div class="stat-label">夏普比率</div><div class="stat-value">${renderMetricValue(metrics.risk?.sharpe_ratio, v => v.toFixed(3), 'sharpe_ratio')}</div></div>
                        </div>
                    </div>
                </div>
            `;
        } else if (basic.asset_type === 'fund' && metrics) {
            const renderMetricValue = (value, formatter, fieldKey) => {
                if (value === null || value === undefined) {
                    return `<span class="loading-text" id="metric-${fieldKey}"><span class="mini-spinner"></span>加载中...</span>`;
                }
                return formatter ? formatter(value) : value;
            };

            // 基金专用指标（不显示PE等股票指标）
            html += `
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-header"><h4>净值信息</h4></div>
                    <div class="card-body">
                        <div class="stats-grid">
                            <div class="stat-card"><div class="stat-label">单位净值</div><div class="stat-value">${renderMetricValue(metrics.nav_info?.unit_nav, v => v.toFixed(4), 'unit_nav')}</div></div>
                            <div class="stat-card"><div class="stat-label">累计净值</div><div class="stat-value">${renderMetricValue(metrics.nav_info?.acc_nav, v => v.toFixed(4), 'acc_nav')}</div></div>
                            <div class="stat-card"><div class="stat-label">净值日期</div><div class="stat-value">${metrics.nav_info?.nav_date || '--'}</div></div>
                        </div>
                    </div>
                </div>
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-header"><h4>收益指标</h4></div>
                    <div class="card-body">
                        <div class="stats-grid">
                            <div class="stat-card"><div class="stat-label">近1月</div><div class="stat-value">${renderMetricValue(metrics.returns?.return_1m, v => v.toFixed(2) + '%', 'return_1m')}</div></div>
                            <div class="stat-card"><div class="stat-label">近3月</div><div class="stat-value">${renderMetricValue(metrics.returns?.return_3m, v => v.toFixed(2) + '%', 'return_3m')}</div></div>
                            <div class="stat-card"><div class="stat-label">近6月</div><div class="stat-value">${renderMetricValue(metrics.returns?.return_6m, v => v.toFixed(2) + '%', 'return_6m')}</div></div>
                            <div class="stat-card"><div class="stat-label">近1年</div><div class="stat-value">${renderMetricValue(metrics.returns?.return_1y, v => v.toFixed(2) + '%', 'return_1y')}</div></div>
                        </div>
                    </div>
                </div>
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-header"><h4>风险指标</h4></div>
                    <div class="card-body">
                        <div class="stats-grid">
                            <div class="stat-card"><div class="stat-label">最大回撤</div><div class="stat-value">${renderMetricValue(metrics.risk?.max_drawdown, v => v.toFixed(2) + '%', 'max_drawdown')}</div></div>
                            <div class="stat-card"><div class="stat-label">夏普比率</div><div class="stat-value">${renderMetricValue(metrics.risk?.sharpe_ratio, v => v.toFixed(3), 'sharpe_ratio')}</div></div>
                        </div>
                    </div>
                </div>
            `;
        }

        // 历史数据曲线
        if (history.length > 0) {
            const chartId = `position-history-chart-${id}`;
            html += `
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-header"><h4>${basic.asset_type === 'fund' ? '净值走势' : '价格走势'} (近1年)</h4></div>
                    <div class="card-body">
                        <div style="height: 300px;">
                            <canvas id="${chartId}"></canvas>
                        </div>
                    </div>
                </div>
            `;

            // 延迟渲染图表
            setTimeout(() => {
                renderPositionHistoryChart(chartId, history, basic.asset_type, basic.cost_price);
            }, 100);
        }

        // 交易记录
        html += `
            <div class="card">
                <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                    <h4>交易记录</h4>
                    <button class="btn btn-sm btn-primary" onclick="showQuickTradeModal(${id}, '${basic.symbol}', '${basic.name}', 'buy', ${basic.current_price || basic.cost_price}, '${basic.asset_type}', ${basic.quantity})">+ 新增交易</button>
                </div>
                <div class="card-body">
                    ${trades.length > 0 ? `
                        <table class="data-table">
                            <thead>
                                <tr><th>日期</th><th>类型</th><th>数量</th><th>价格</th><th>金额</th><th>理由</th></tr>
                            </thead>
                            <tbody>
                                ${trades.map(t => `
                                    <tr>
                                        <td>${utils.formatDate(t.trade_date)}</td>
                                        <td><span class="tag ${t.trade_type === 'buy' ? 'success' : 'danger'}">${t.trade_type === 'buy' ? '买入' : '卖出'}</span></td>
                                        <td>${t.quantity}</td>
                                        <td>${t.price.toFixed(3)}</td>
                                        <td>${utils.formatMoney(t.amount)}</td>
                                        <td>${t.reason || '--'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    ` : '<div class="text-muted" style="text-align: center; padding: 20px;">暂无交易记录，点击上方按钮添加</div>'}
                </div>
            </div>
        `;

        html += `<div style="margin-top: 16px; font-size: 12px; color: var(--text-muted);">* 数据来源于免费接口（AKShare/天天基金），部分指标可能需要时间计算</div>`;

        body.innerHTML = html;

        // 异步加载缺失的指标字段
        loadMissingMetrics(id, detail);

    } catch (error) {
        body.innerHTML = `<div style="color: var(--danger-color); padding: 20px;">加载失败: ${error.message}</div>`;
    }
}

// 加载缺失的指标数据
async function loadMissingMetrics(positionId, detail) {
    const metrics = detail.metrics || {};
    const basic = detail.basic;
    const assetType = basic?.asset_type;

    // 收集缺失的字段
    const missingFields = [];

    if (assetType === 'stock') {
        const stockFields = [
            { key: 'pe_ttm', category: 'valuation' },
            { key: 'pb', category: 'valuation' },
            { key: 'peg', category: 'valuation' },
            { key: 'dividend_yield', category: 'valuation' },
            { key: 'roe', category: 'profitability' },
            { key: 'gross_margin', category: 'profitability' },
            { key: 'net_margin', category: 'profitability' },
            { key: 'roic', category: 'profitability' },
            { key: 'ma5', category: 'technical' },
            { key: 'ma10', category: 'technical' },
            { key: 'ma20', category: 'technical' },
            { key: 'ma60', category: 'technical' },
            { key: 'turnover_rate', category: 'capital_flow' }
        ];

        for (const field of stockFields) {
            const value = metrics[field.category]?.[field.key];
            if (value === null || value === undefined) {
                missingFields.push(field.key);
            }
        }
    } else if (assetType === 'fund') {
        const fundFields = [
            { key: 'unit_nav', category: 'nav_info' },
            { key: 'acc_nav', category: 'nav_info' },
            { key: 'return_1m', category: 'returns' },
            { key: 'return_3m', category: 'returns' },
            { key: 'return_1y', category: 'returns' }
        ];

        for (const field of fundFields) {
            const value = metrics[field.category]?.[field.key];
            if (value === null || value === undefined) {
                missingFields.push(field.key);
            }
        }
    }

    // 如果有缺失字段，尝试从API获取
    if (missingFields.length > 0) {
        try {
            const result = await utils.request(
                `${API_BASE}/positions/${positionId}/fetch-metrics?fields=${missingFields.join(',')}`
            );

            // 更新各字段
            if (result.metrics) {
                for (const [key, value] of Object.entries(result.metrics)) {
                    updateMetricField(key, value, assetType);
                }
            }

            // 显示错误信息
            if (result.errors) {
                for (const [key, error] of Object.entries(result.errors)) {
                    const el = document.getElementById(`metric-${key}`);
                    if (el) {
                        el.innerHTML = `<span class="metric-error" title="${error}">加载失败</span>`;
                    }
                }
            }
        } catch (error) {
            console.error('获取指标失败:', error);
            // 所有缺失字段显示错误
            for (const key of missingFields) {
                const el = document.getElementById(`metric-${key}`);
                if (el) {
                    el.innerHTML = `<span class="metric-error" title="${error.message}">加载失败</span>`;
                }
            }
        }
    }
}

// 更新指标字段显示
function updateMetricField(key, value, assetType) {
    const el = document.getElementById(`metric-${key}`);
    if (!el) return;

    el.classList.remove('loading-text');

    if (value === null || value === undefined) {
        el.textContent = '--';
        return;
    }

    // 根据字段类型格式化
    const formatters = {
        'pe_ttm': v => v.toFixed(2),
        'pb': v => v.toFixed(2),
        'peg': v => v.toFixed(2),
        'dividend_yield': v => (v * 100).toFixed(2) + '%',
        'roe': v => (v * 100).toFixed(2) + '%',
        'gross_margin': v => (v * 100).toFixed(2) + '%',
        'net_margin': v => (v * 100).toFixed(2) + '%',
        'roic': v => (v * 100).toFixed(2) + '%',
        'ma5': v => v.toFixed(3),
        'ma10': v => v.toFixed(3),
        'ma20': v => v.toFixed(3),
        'ma60': v => v.toFixed(3),
        'turnover_rate': v => v.toFixed(2) + '%',
        'unit_nav': v => v.toFixed(4),
        'acc_nav': v => v.toFixed(4),
        'return_1m': v => v.toFixed(2) + '%',
        'return_3m': v => v.toFixed(2) + '%',
        'return_6m': v => v.toFixed(2) + '%',
        'return_1y': v => v.toFixed(2) + '%'
    };

    const formatter = formatters[key];
    el.textContent = formatter ? formatter(value) : value;
}

// 渲染持仓历史图表
function renderPositionHistoryChart(canvasId, historyData, assetType, costPrice) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !historyData || historyData.length === 0) return;

    const ctx = canvas.getContext('2d');

    // 准备数据
    const labels = historyData.map(d => d.date);
    const prices = historyData.map(d => d.close || d.nav);

    // 创建图表
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: assetType === 'fund' ? '单位净值' : '收盘价',
                    data: prices,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.1,
                    fill: true
                },
                {
                    label: '成本价',
                    data: Array(prices.length).fill(costPrice),
                    borderColor: 'rgb(255, 99, 132)',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y.toFixed(3);
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxTicksLimit: 10
                    }
                },
                y: {
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(3);
                        }
                    }
                }
            }
        }
    });
}

// 关闭持仓详情
function closePositionDetail() {
    document.getElementById('position-detail-modal').style.display = 'none';
}

// 编辑持仓
async function editPosition(id) {
    const position = await utils.request(`${API_BASE}/positions/${id}`);
    showPositionModal(position);
}

// 删除持仓
async function deletePosition(id) {
    if (!confirm('确定要删除这个持仓吗？')) return;

    try {
        await utils.request(`${API_BASE}/positions/${id}`, { method: 'DELETE' });
        utils.showToast('持仓删除成功');
        pageManager.loadPageData(pageManager.currentPage);
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 持仓排序
function sortPositions(sortBy) {
    // 如果点击的是当前排序字段，切换排序方向
    if (positionsSortBy === sortBy) {
        positionsSortOrder = positionsSortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        // 切换排序字段，默认降序
        positionsSortBy = sortBy;
        positionsSortOrder = 'desc';
    }

    // 重新加载持仓列表
    pageManager.loadPositions(pageManager.currentAccountId);
}

// 持仓管理页面排序
function sortPositionsFull(sortBy) {
    // 如果点击的是当前排序字段，切换排序方向
    if (positionsSortBy === sortBy) {
        positionsSortOrder = positionsSortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        // 切换排序字段，默认降序
        positionsSortBy = sortBy;
        positionsSortOrder = 'desc';
    }

    // 重新加载持仓管理页面
    positionsPage.load(pageManager.currentAccountId);
}

// 显示交易模态框
function showTradeModal() {
    const today = new Date().toISOString().split('T')[0];
    const content = `
        <form id="trade-form">
            <div class="form-grid">
                <div class="form-group">
                    <label>标的代码</label>
                    <input type="text" name="symbol" class="form-input" required>
                </div>
                <div class="form-group">
                    <label>交易类型</label>
                    <select name="trade_type" class="form-input" required>
                        <option value="buy">买入</option>
                        <option value="sell">卖出</option>
                    </select>
                </div>
            </div>
            <div class="form-grid">
                <div class="form-group">
                    <label>数量</label>
                    <input type="number" name="quantity" class="form-input" required min="1">
                </div>
                <div class="form-group">
                    <label>价格</label>
                    <input type="number" name="price" class="form-input" required step="0.0001">
                </div>
            </div>
            <div class="form-grid">
                <div class="form-group">
                    <label>交易日期</label>
                    <input type="text" name="trade_date" id="trade-date-picker" class="form-input" required value="${today}">
                </div>
            </div>
            <div class="form-group">
                <label>交易理由</label>
                <input type="text" name="reason" class="form-input" placeholder="如：低估建仓">
            </div>
        </form>
    `;
    const footer = `
        <button class="btn btn-secondary" onclick="closeModal()">取消</button>
        <button class="btn btn-primary" onclick="saveTrade()">保存</button>
    `;
    modalManager.show('新增交易', content, footer);

    // 初始化日期选择器
    setTimeout(() => {
        DatePicker.init('#trade-date-picker', { defaultDate: today });
    }, 100);
}

// 快捷交易弹窗（从持仓详情发起）
let currentQuickTradePositionId = null;
let currentQuickTradeAssetType = null;
let currentQuickTradeQuantity = null;

function showQuickTradeModal(positionId, symbol, name, tradeType, price, assetType, quantity) {
    currentQuickTradePositionId = positionId;
    currentQuickTradeAssetType = assetType || 'stock';
    currentQuickTradeQuantity = quantity || 0;

    const today = new Date().toISOString().split('T')[0];
    const displayPrice = price ? price.toFixed(3) : '';

    // 判断是否只能整数
    const isIntegerOnly = ['stock', 'etf_index', 'etf_sector'].includes(currentQuickTradeAssetType);
    const stepAttr = isIntegerOnly ? 'step="1" min="1"' : 'step="0.01" min="0.01"';
    const placeholderText = isIntegerOnly ? '输入股数（整数）' : '输入份额（可小数）';

    // 卖出时显示快捷比例按钮
    let quickRatioButtons = '';
    if (tradeType === 'sell' && currentQuickTradeQuantity > 0) {
        quickRatioButtons = `
            <div class="quick-ratio-buttons" style="margin-bottom: 8px; display: flex; gap: 8px; flex-wrap: wrap;">
                <button type="button" class="btn btn-sm btn-outline" onclick="applySellRatio(0.25)">1/4</button>
                <button type="button" class="btn btn-sm btn-outline" onclick="applySellRatio(0.333)">1/3</button>
                <button type="button" class="btn btn-sm btn-outline" onclick="applySellRatio(0.5)">1/2</button>
                <button type="button" class="btn btn-sm btn-outline" onclick="applySellRatio(1)">全仓</button>
            </div>
        `;
    }

    const content = `
        <form id="quick-trade-form">
            <div class="form-grid">
                <div class="form-group">
                    <label>标的代码</label>
                    <input type="text" name="symbol" class="form-input" value="${symbol}" readonly style="background: #f5f5f5;">
                </div>
                <div class="form-group">
                    <label>标的名称</label>
                    <input type="text" class="form-input" value="${name}" readonly style="background: #f5f5f5;">
                </div>
            </div>
            <div class="form-grid">
                <div class="form-group">
                    <label>交易类型</label>
                    <select name="trade_type" class="form-input" required onchange="toggleQuickRatioButtons(this.value)">
                        <option value="buy" ${tradeType === 'buy' ? 'selected' : ''}>买入</option>
                        <option value="sell" ${tradeType === 'sell' ? 'selected' : ''}>卖出</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>数量</label>
                    ${quickRatioButtons}
                    <input type="number" name="quantity" id="quick-trade-quantity" class="form-input"
                           required ${stepAttr} placeholder="${placeholderText}">
                    <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">
                        当前持仓: ${currentQuickTradeQuantity} ${isIntegerOnly ? '股' : '份'}
                    </div>
                </div>
            </div>
            <div class="form-grid">
                <div class="form-group">
                    <label>价格</label>
                    <input type="number" name="price" class="form-input" required step="0.0001" value="${displayPrice}" placeholder="输入价格">
                </div>
                <div class="form-group">
                    <label>交易日期</label>
                    <input type="text" name="trade_date" id="quick-trade-date-picker" class="form-input" required value="${today}">
                </div>
            </div>
            <div class="form-group">
                <label>交易理由</label>
                <input type="text" name="reason" class="form-input" placeholder="如：低估加仓、止盈卖出">
                <input type="hidden" name="signal_type" id="quick-trade-signal-type">
                <input type="hidden" name="asset_type" value="${currentQuickTradeAssetType}">
            </div>
        </form>
    `;
    const footer = `
        <button class="btn btn-secondary" onclick="closeModal()">取消</button>
        <button class="btn btn-primary" onclick="saveQuickTrade()">确认交易</button>
    `;
    modalManager.show('快捷交易', content, footer);

    // 初始化日期选择器
    setTimeout(() => {
        DatePicker.init('#quick-trade-date-picker', { defaultDate: today });
    }, 100);
}

// 应用卖出比例
function applySellRatio(ratio) {
    const quantityInput = document.getElementById('quick-trade-quantity');
    const signalTypeInput = document.getElementById('quick-trade-signal-type');
    const isIntegerOnly = ['stock', 'etf_index', 'etf_sector'].includes(currentQuickTradeAssetType);

    let sellQty = currentQuickTradeQuantity * ratio;

    if (isIntegerOnly) {
        sellQty = Math.floor(sellQty);
        if (sellQty < 1) sellQty = 1;
    } else {
        // 基金：保留两位小数
        sellQty = Math.floor(sellQty * 100) / 100;
        if (sellQty < 0.01) sellQty = currentQuickTradeQuantity; // 小数份额最小卖全部
    }

    quantityInput.value = sellQty;

    // 设置信号类型（用于后端更新止盈状态）
    if (ratio <= 0.35) {
        signalTypeInput.value = 'stop_profit_1';
    } else if (ratio <= 0.55) {
        signalTypeInput.value = 'stop_profit_2';
    } else if (ratio >= 0.9) {
        signalTypeInput.value = 'stop_profit_3';
    }
}

// 切换交易类型时显示/隐藏快捷按钮
function toggleQuickRatioButtons(tradeType) {
    const buttonsContainer = document.querySelector('.quick-ratio-buttons');
    if (buttonsContainer) {
        buttonsContainer.style.display = tradeType === 'sell' ? 'flex' : 'none';
    }
    // 清空数量输入
    const quantityInput = document.getElementById('quick-trade-quantity');
    if (quantityInput) {
        quantityInput.value = '';
    }
    // 清空信号类型
    const signalTypeInput = document.getElementById('quick-trade-signal-type');
    if (signalTypeInput) {
        signalTypeInput.value = '';
    }
}

// 从信号列表快捷操作（使用建议的份额/金额）
function applySuggestion(positionId, symbol, name, currentPrice, suggestionQuantity, assetType, tradeType) {
    // 打开快捷交易弹窗，并自动填充建议的数量
    showQuickTradeModal(positionId, symbol, name, tradeType, currentPrice, assetType, 0);

    // 延迟填充建议数量（等待弹窗创建）
    setTimeout(() => {
        const quantityInput = document.getElementById('quick-trade-quantity');
        if (quantityInput) {
            // 根据资产类型决定数量精度
            const isIntegerOnly = ['stock', 'etf_index', 'etf_sector'].includes(assetType);
            if (isIntegerOnly) {
                quantityInput.value = Math.floor(suggestionQuantity);
            } else {
                // 基金允许小数，保留两位
                quantityInput.value = Math.floor(suggestionQuantity * 100) / 100;
            }
        }
        // 设置信号类型
        const signalTypeInput = document.getElementById('quick-trade-signal-type');
        if (signalTypeInput) {
            if (tradeType === 'sell') {
                signalTypeInput.value = 'stop_profit_signal';
            } else {
                signalTypeInput.value = 'add_position_signal';
            }
        }
    }, 150);
}

// 保存快捷交易
async function saveQuickTrade() {
    const form = document.getElementById('quick-trade-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // 根据资产类型决定数量解析方式
    const isIntegerOnly = ['stock', 'etf_index', 'etf_sector'].includes(currentQuickTradeAssetType);

    if (isIntegerOnly) {
        data.quantity = parseInt(data.quantity);
    } else {
        // 基金等允许小数份额，保留两位小数
        data.quantity = parseFloat(data.quantity);
        data.quantity = Math.floor(data.quantity * 100) / 100;
    }

    data.price = parseFloat(data.price);

    if (!data.quantity || data.quantity <= 0) {
        utils.showToast('请输入有效的数量', 'error');
        return;
    }
    if (!data.price || data.price <= 0) {
        utils.showToast('请输入有效的价格', 'error');
        return;
    }

    // 获取信号类型（如果有）
    const signalTypeInput = document.getElementById('quick-trade-signal-type');
    if (signalTypeInput && signalTypeInput.value) {
        data.signal_type = signalTypeInput.value;
    }

    // 传入资产类型（用于后端判断）
    data.asset_type = currentQuickTradeAssetType;

    try {
        await utils.request(`${API_BASE}/trades`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        utils.showToast('交易记录创建成功');
        closeModal();

        // 刷新持仓详情页面
        if (currentQuickTradePositionId) {
            showPositionDetail(currentQuickTradePositionId);
        }

        // 同时刷新列表页数据
        pageManager.loadPageData(pageManager.currentPage);
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 保存交易
async function saveTrade() {
    const form = document.getElementById('trade-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    data.quantity = parseInt(data.quantity);
    data.price = parseFloat(data.price);

    try {
        await utils.request(`${API_BASE}/trades`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        utils.showToast('交易记录创建成功');
        closeModal();
        pageManager.loadPageData(pageManager.currentPage);

        // 如果持仓详情弹窗打开，刷新它
        const detailModal = document.getElementById('position-detail-modal');
        if (detailModal && detailModal.style.display === 'flex' && currentQuickTradePositionId) {
            showPositionDetail(currentQuickTradePositionId);
        }
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 删除交易
async function deleteTrade(id) {
    if (!confirm('确定要删除这条交易记录吗？')) return;

    try {
        await utils.request(`${API_BASE}/trades/${id}`, { method: 'DELETE' });
        utils.showToast('交易记录删除成功');
        pageManager.loadPageData(pageManager.currentPage);
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 显示估值模态框
function showValuationModal() {
    const content = `
        <form id="valuation-form">
            <div class="form-grid">
                <div class="form-group">
                    <label>标的代码</label>
                    <input type="text" name="symbol" class="form-input" required placeholder="如：000300">
                </div>
                <div class="form-group">
                    <label>指数名称</label>
                    <input type="text" name="index_name" class="form-input" required placeholder="如：沪深300">
                </div>
            </div>
            <div class="form-grid">
                <div class="form-group">
                    <label>PE</label>
                    <input type="number" name="pe" class="form-input" step="0.01">
                </div>
                <div class="form-group">
                    <label>PE 百分位(%)</label>
                    <input type="number" name="pe_percentile" class="form-input" step="0.1" min="0" max="100">
                </div>
            </div>
            <div class="form-grid">
                <div class="form-group">
                    <label>PB</label>
                    <input type="number" name="pb" class="form-input" step="0.0001">
                </div>
                <div class="form-group">
                    <label>PB 百分位(%)</label>
                    <input type="number" name="pb_percentile" class="form-input" step="0.1" min="0" max="100">
                </div>
            </div>
            <div class="form-grid">
                <div class="form-group">
                    <label>RSI</label>
                    <input type="number" name="rsi" class="form-input" step="0.1" min="0" max="100">
                </div>
                <div class="form-group">
                    <label>记录日期</label>
                    <input type="date" name="record_date" class="form-input" required value="${new Date().toISOString().split('T')[0]}">
                </div>
            </div>
        </form>
    `;
    const footer = `
        <button class="btn btn-secondary" onclick="closeModal()">取消</button>
        <button class="btn btn-primary" onclick="saveValuation()">保存</button>
    `;
    modalManager.show('录入估值', content, footer);
}

// 保存估值
async function saveValuation() {
    const form = document.getElementById('valuation-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // 转换数值类型
    ['pe', 'pe_percentile', 'pb', 'pb_percentile', 'rsi'].forEach(key => {
        if (data[key]) data[key] = parseFloat(data[key]);
    });

    try {
        await utils.request(`${API_BASE}/valuations`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        utils.showToast('估值数据保存成功');
        closeModal();
        pageManager.loadPageData(pageManager.currentPage);
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 运行回测
async function runBacktest() {
    const dataSource = document.getElementById('backtest-data-source').value;
    const symbol = document.getElementById('backtest-symbol').value;
    const initialCapital = parseFloat(document.getElementById('backtest-capital').value) || 100000;

    // 获取时间范围
    const startDate = document.getElementById('backtest-start-date').value;
    const endDate = document.getElementById('backtest-end-date').value;

    // 获取资产类型
    const assetTypeRadio = document.querySelector('input[name="backtest-asset-type"]:checked');
    const assetType = assetTypeRadio ? assetTypeRadio.value : 'stock';

    // 获取选中的策略
    const strategies = backtestPage.getSelectedStrategies();
    if (strategies.length === 0) {
        utils.showToast('请选择至少一个策略', 'error');
        return;
    }

    if (!symbol) {
        utils.showToast('请选择或输入标的代码', 'error');
        return;
    }

    const container = document.getElementById('backtest-result');
    container.innerHTML = '<div class="loading">回测运行中，请稍候...</div>';

    const data = {
        symbol: symbol,
        data_source: assetType === 'fund' ? 'eastmoney' : dataSource,
        asset_type: assetType,
        initial_capital: initialCapital,
        start_date: startDate,
        end_date: endDate,
        strategies: strategies,
        strategy_params: backtestPage.getStrategyParams()
    };

    try {
        const result = await utils.request(`${API_BASE}/backtest/run`, {
            method: 'POST',
            body: JSON.stringify(data)
        });

        renderBacktestResult(result);
    } catch (error) {
        container.innerHTML = `<div class="text-muted" style="color: var(--danger-color);">${error.message}</div>`;
    }
}

// 渲染回测结果
function renderBacktestResult(result) {
    const container = document.getElementById('backtest-result');

    let html = `
        <div style="margin-bottom: 16px;">
            <h4>回测结果</h4>
            <div style="font-size: 12px; color: var(--text-muted);">
                标的: ${result.symbol} |
                类型: ${result.asset_type === 'fund' ? '基金' : '股票/ETF'} |
                数据源: ${result.data_source === 'tushare' ? 'Tushare' : result.data_source === 'eastmoney' ? '天天基金' : '本地数据'} |
                数据量: ${result.data_count} 条 |
                时间范围: ${result.start_date} ~ ${result.end_date}
            </div>
        </div>
        <div class="stats-grid" style="margin-bottom: 16px;">
            <div class="stat-card">
                <div class="stat-label">初始资金</div>
                <div class="stat-value">${utils.formatMoney(result.initial_capital)}</div>
            </div>
        </div>
    `;

    // 策略对比表格
    html += `
        <table class="data-table" style="margin-bottom: 16px;">
            <thead>
                <tr>
                    <th>策略</th>
                    <th>总收益率</th>
                    <th>年化收益</th>
                    <th>最大回撤</th>
                    <th>夏普比率</th>
                    <th>胜率</th>
                    <th>交易次数</th>
                    <th>最终资产</th>
                </tr>
            </thead>
            <tbody>
    `;

    result.strategies.forEach(s => {
        const profitClass = s.total_return >= 0 ? 'profit' : 'loss';
        html += `
            <tr>
                <td>${s.strategy_name}</td>
                <td class="${profitClass}">${s.total_return.toFixed(2)}%</td>
                <td>${s.annual_return.toFixed(2)}%</td>
                <td>${s.max_drawdown.toFixed(2)}%</td>
                <td>${s.sharpe_ratio.toFixed(3)}</td>
                <td>${s.win_rate.toFixed(1)}%</td>
                <td>${s.trade_count}</td>
                <td>${utils.formatMoney(s.final_value)}</td>
            </tr>
        `;
    });

    html += '</tbody></table>';

    // 各策略详情
    html += '<div class="accordion">';
    result.strategies.forEach((s, index) => {
        html += `
            <div class="accordion-item">
                <div class="accordion-header" onclick="toggleAccordion(${index})">
                    <span>${s.strategy_name} - ${s.summary}</span>
                    <span>▼</span>
                </div>
                <div class="accordion-content" id="accordion-${index}" style="display: none;">
                    ${s.records && s.records.length > 0 ? `
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>日期</th>
                                    <th>价格</th>
                                    <th>操作</th>
                                    <th>股数</th>
                                    <th>金额</th>
                                    <th>总资产</th>
                                    <th>收益率</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${s.records.map(r => {
                                    let actionText = r.action;
                                    let actionClass = '';
                                    if (r.action === '买入' || r.action.includes('加仓')) {
                                        actionText = r.action;
                                        actionClass = 'success';
                                    } else if (r.action === '卖出' || r.action === '清仓' || r.action.includes('止盈')) {
                                        actionText = r.action;
                                        actionClass = 'danger';
                                    } else {
                                        actionText = '持有';
                                        actionClass = '';
                                    }
                                    return `
                                    <tr>
                                        <td>${r.date}</td>
                                        <td>${r.price.toFixed(3)}</td>
                                        <td>${actionClass ? `<span class="tag ${actionClass}">${actionText}</span>` : actionText}</td>
                                        <td>${r.shares}</td>
                                        <td>${utils.formatMoney(r.amount)}</td>
                                        <td>${utils.formatMoney(r.total_value)}</td>
                                        <td class="${r.profit_rate >= 0 ? 'profit' : 'loss'}">${r.profit_rate.toFixed(2)}%</td>
                                    </tr>
                                `}).join('')}
                            </tbody>
                        </table>
                    ` : '<div class="text-muted">暂无交易记录</div>'}
                </div>
            </div>
        `;
    });
    html += '</div>';

    container.innerHTML = html;
}

// 折叠面板切换
function toggleAccordion(index) {
    const content = document.getElementById(`accordion-${index}`);
    if (content) {
        content.style.display = content.style.display === 'none' ? 'block' : 'none';
    }
}

// 切换回测结果/历史Tab
function switchBacktestTab(tab) {
    const resultContainer = document.getElementById('backtest-result-container');
    const historyContainer = document.getElementById('backtest-history-container');
    const resultBtn = document.getElementById('bt-tab-result');
    const historyBtn = document.getElementById('bt-tab-history');

    if (tab === 'result') {
        resultContainer.style.display = 'block';
        historyContainer.style.display = 'none';
        resultBtn.classList.add('active');
        historyBtn.classList.remove('active');
    } else {
        resultContainer.style.display = 'none';
        historyContainer.style.display = 'block';
        resultBtn.classList.remove('active');
        historyBtn.classList.add('active');
        loadBacktestHistory();
    }
}

// 加载回测历史列表
async function loadBacktestHistory() {
    const container = document.getElementById('backtest-history-list');

    try {
        const history = await utils.request(`${API_BASE}/backtest/history`);

        if (!history || history.length === 0) {
            container.innerHTML = '<div class="text-muted" style="text-align: center; padding: 20px;">暂无历史记录</div>';
            return;
        }

        let html = '<table class="data-table"><thead><tr><th>时间</th><th>标的</th><th>时间范围</th><th>最佳策略</th><th>最佳收益</th><th>操作</th></tr></thead><tbody>';
        history.forEach(h => {
            const returnDisplay = h.best_return ? `<span class="${h.best_return >= 0 ? 'profit' : 'loss'}">${h.best_return.toFixed(2)}%</span>` : '--';
            html += `
                <tr>
                    <td>${utils.formatDate(h.created_at)}</td>
                    <td>${h.symbol} ${h.name ? `(${h.name})` : ''}</td>
                    <td>${h.start_date} ~ ${h.end_date}</td>
                    <td>${h.best_strategy || '--'}</td>
                    <td>${returnDisplay}</td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="viewBacktestHistory(${h.id})">查看</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteBacktestHistory(${h.id})" style="margin-left: 4px;">删除</button>
                    </td>
                </tr>
            `;
        });
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = '<div class="text-muted" style="text-align: center; padding: 20px;">加载历史记录失败</div>';
    }
}

// 查看回测历史详情
async function viewBacktestHistory(historyId) {
    // 切换到结果Tab
    switchBacktestTab('result');

    const container = document.getElementById('backtest-result');
    container.innerHTML = '<div class="loading">加载历史详情...</div>';

    try {
        const result = await utils.request(`${API_BASE}/backtest/history/${historyId}`);

        if (result.results) {
            renderBacktestResult(result.results);
        } else {
            container.innerHTML = '<div class="text-muted">暂无详细数据</div>';
        }
    } catch (error) {
        container.innerHTML = `<div class="text-muted" style="color: var(--danger-color);">${error.message}</div>`;
    }
}

// 删除回测历史
async function deleteBacktestHistory(historyId) {
    if (!confirm('确定要删除这条回测历史吗？')) {
        return;
    }

    try {
        await utils.request(`${API_BASE}/backtest/history/${historyId}`, {
            method: 'DELETE'
        });
        utils.showToast('删除成功');
        await loadBacktestHistory();
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 场景对比
async function compareBacktest() {
    const symbol = document.getElementById('backtest-symbol').value;

    if (!symbol) {
        utils.showToast('请输入标的代码', 'error');
        return;
    }

    const container = document.getElementById('backtest-result');
    container.innerHTML = '<div class="loading">对比分析中...</div>';

    const data = {
        symbol: symbol,
        initial_capital: parseFloat(document.getElementById('backtest-capital').value) || 100000
    };

    try {
        const result = await utils.request(`${API_BASE}/backtest/compare`, {
            method: 'POST',
            body: JSON.stringify(data)
        });

        let html = `
            <div style="margin-bottom: 16px;">
                <h4>策略对比</h4>
                <div style="font-size: 12px; color: var(--text-muted);">
                    初始资金: ${utils.formatMoney(result.initial_capital)} |
                    标的: ${result.symbol} |
                    数据量: ${result.data_count} 条
                </div>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>策略</th>
                        <th>总收益率</th>
                        <th>最大回撤</th>
                        <th>夏普比率</th>
                        <th>胜率</th>
                        <th>交易次数</th>
                        <th>最终资产</th>
                    </tr>
                </thead>
                <tbody>
        `;

        result.comparison.forEach(c => {
            const profitClass = c.total_return >= 0 ? 'profit' : 'loss';
            html += `
                <tr>
                    <td>${c.strategy_name}</td>
                    <td class="${profitClass}">${c.total_return.toFixed(2)}%</td>
                    <td>${c.max_drawdown.toFixed(2)}%</td>
                    <td>${c.sharpe_ratio.toFixed(3)}</td>
                    <td>${c.win_rate.toFixed(1)}%</td>
                    <td>${c.trade_count}</td>
                    <td>${utils.formatMoney(c.final_value)}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `<div class="text-muted" style="color: var(--danger-color);">${error.message}</div>`;
    }
}

// 切换资产类型（股票/基金）
function toggleAssetType() {
    const assetTypeRadio = document.querySelector('input[name="backtest-asset-type"]:checked');
    const assetType = assetTypeRadio ? assetTypeRadio.value : 'stock';
    const datasourceSection = document.getElementById('stock-datasource-section');
    const symbolLabel = document.getElementById('symbol-label');
    const nameLabel = document.getElementById('name-label');
    const symbolInput = document.getElementById('backtest-stock-symbol');
    const nameInput = document.getElementById('backtest-stock-name');
    const quickSelectLabel = document.getElementById('quick-select-label');

    if (assetType === 'fund') {
        // 基金模式：隐藏数据源选择，使用天天基金
        datasourceSection.style.display = 'none';
        symbolLabel.textContent = '基金代码';
        nameLabel.textContent = '基金名称';
        symbolInput.placeholder = '如: 000001';
        nameInput.placeholder = '如: 华夏成长混合';
        if (quickSelectLabel) quickSelectLabel.textContent = '快速选择基金';
    } else {
        // 股票模式：显示数据源选择
        datasourceSection.style.display = 'block';
        symbolLabel.textContent = '股票代码';
        nameLabel.textContent = '股票名称';
        symbolInput.placeholder = '如: 601168';
        nameInput.placeholder = '如: 西部矿业';
        if (quickSelectLabel) quickSelectLabel.textContent = '快速选择股票';
    }

    // 更新快速选择列表
    loadQuickSelectSymbols();

    // 清空当前选择
    clearQuickSelect();
}

// 快速选择列表数据缓存
let quickSelectData = { stocks: [], funds: [] };

// 加载快速选择列表
async function loadQuickSelectSymbols() {
    try {
        const result = await utils.request(`${API_BASE}/backtest/quick-select-symbols`);
        if (result) {
            quickSelectData.stocks = result.stocks || [];
            quickSelectData.funds = result.funds || [];
            updateQuickSelectDropdown();
        }
    } catch (error) {
        console.error('加载快速选择列表失败:', error);
    }
}

// 更新快速选择下拉框
function updateQuickSelectDropdown() {
    const assetTypeRadio = document.querySelector('input[name="backtest-asset-type"]:checked');
    const assetType = assetTypeRadio ? assetTypeRadio.value : 'stock';
    const select = document.getElementById('quick-select-symbol');

    if (!select) return;

    const items = assetType === 'fund' ? quickSelectData.funds : quickSelectData.stocks;

    let html = '<option value="">-- 从已有数据中选择或手动输入 --</option>';
    items.forEach(item => {
        const displayText = item.name ? `${item.symbol} - ${item.name}` : item.symbol;
        html += `<option value="${item.symbol}" data-name="${item.name || ''}">${displayText}</option>`;
    });

    select.innerHTML = html;
}

// 快速选择变化时
function onQuickSelectChange() {
    const select = document.getElementById('quick-select-symbol');
    const symbolInput = document.getElementById('backtest-stock-symbol');
    const nameInput = document.getElementById('backtest-stock-name');

    if (select.value) {
        symbolInput.value = select.value;
        const selectedOption = select.options[select.selectedIndex];
        const name = selectedOption.getAttribute('data-name');
        if (name) {
            nameInput.value = name;
        }
    }
}

// 手动输入代码时清空快速选择
function onSymbolInput() {
    const select = document.getElementById('quick-select-symbol');
    const symbolInput = document.getElementById('backtest-stock-symbol');

    if (select.value !== symbolInput.value) {
        select.value = '';
    }
}

// 清空选择
function clearQuickSelect() {
    const select = document.getElementById('quick-select-symbol');
    const symbolInput = document.getElementById('backtest-stock-symbol');
    const nameInput = document.getElementById('backtest-stock-name');

    if (select) select.value = '';
    if (symbolInput) symbolInput.value = '';
    if (nameInput) nameInput.value = '';
}

// 切换数据源选项
function toggleDataSourceOptions() {
    const dataSource = document.getElementById('backtest-data-source').value;
    const onlineSection = document.getElementById('online-fetch-section');
    const localSection = document.getElementById('local-import-section');
    const status = document.getElementById('ds-status');

    // 显示/隐藏相应区域
    if (dataSource === 'local') {
        onlineSection.style.display = 'none';
        localSection.style.display = 'block';
    } else {
        onlineSection.style.display = 'block';
        localSection.style.display = 'none';
    }

    // 更新状态显示
    if (status) {
        if (dataSource === 'akshare' || dataSource === 'baostock') {
            status.textContent = '免费';
            status.style.background = '#28a745';
        } else if (dataSource === 'tushare') {
            status.textContent = '需要Token';
            status.style.background = '#ffc107';
        } else {
            status.textContent = '';
        }
    }

    // 更新标的下拉框
    updateLocalSymbolSelect();
}

// 更新本地数据下拉框
async function updateLocalSymbolSelect() {
    const select = document.getElementById('backtest-symbol');
    try {
        const histories = await utils.request(`${API_BASE}/backtest/price-histories`);
        if (histories && histories.length > 0) {
            select.innerHTML = histories.map(h => {
                const displayText = h.name ? `${h.symbol} - ${h.name}` : h.symbol;
                return `<option value="${h.symbol}">${displayText} (${h.count}条)</option>`;
            }).join('');
        } else {
            select.innerHTML = '<option value="">请先导入数据</option>';
        }
    } catch (error) {
        console.error('更新本地数据列表失败:', error);
    }
}

// 从在线数据源获取数据（AKShare/BaoStock/Tushare）
async function fetchOnlineData() {
    const dataSource = document.getElementById('backtest-data-source').value;
    const symbol = document.getElementById('backtest-stock-symbol').value.trim();
    const name = document.getElementById('backtest-stock-name').value.trim();
    const startDate = document.getElementById('backtest-fetch-start').value;
    const endDate = document.getElementById('backtest-fetch-end').value;
    const resultDiv = document.getElementById('fetch-result');

    // 获取资产类型
    const assetTypeRadio = document.querySelector('input[name="backtest-asset-type"]:checked');
    const assetType = assetTypeRadio ? assetTypeRadio.value : 'stock';

    if (!symbol) {
        utils.showToast(assetType === 'fund' ? '请输入基金代码' : '请输入股票代码', 'error');
        return;
    }

    resultDiv.innerHTML = '<div class="loading">正在获取数据...</div>';

    try {
        const data = {
            symbol: symbol,
            name: name || symbol,
            data_source: assetType === 'fund' ? 'eastmoney' : dataSource,
            asset_type: assetType,
            start_date: startDate,
            end_date: endDate
        };

        const result = await utils.request(`${API_BASE}/backtest/fetch-data`, {
            method: 'POST',
            body: JSON.stringify(data)
        });

        if (result.success) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <strong>获取成功!</strong>
                    获取到 ${result.count} 条${result.asset_type === 'fund' ? '基金净值' : '股票'}数据，已保存到数据库
                    <br><small>时间范围: ${result.start_date} ~ ${result.end_date}</small>
                </div>
            `;

            // 刷新已导入数据列表和标的下拉框
            await loadImportedDataList();
            await updateLocalSymbolSelect();
            // 刷新快速选择列表
            await loadQuickSelectSymbols();

            // 自动选择刚获取的标的
            const symbolSelect = document.getElementById('backtest-symbol');
            if (symbolSelect) {
                symbolSelect.value = symbol;
            }
        } else {
            resultDiv.innerHTML = `<div class="alert alert-warning">${result.message || '获取失败'}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger">获取失败: ${error.message}</div>`;
    }
}

// 设置Tushare日期范围
function setTushareDateRange(range, btn) {
    // 更新按钮状态
    const section = document.getElementById('tushare-fetch-section');
    section.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    const today = new Date();
    let startDate = new Date();

    switch (range) {
        case 'month':
            startDate.setMonth(today.getMonth() - 1);
            break;
        case 'quarter':
            startDate.setMonth(today.getMonth() - 3);
            break;
        case 'halfyear':
            startDate.setMonth(today.getMonth() - 6);
            break;
        case 'year':
            startDate.setFullYear(today.getFullYear() - 1);
            break;
        case '2years':
            startDate.setFullYear(today.getFullYear() - 2);
            break;
        case '3years':
            startDate.setFullYear(today.getFullYear() - 3);
            break;
    }

    document.getElementById('tushare-start-date').value = startDate.toISOString().split('T')[0];
    document.getElementById('tushare-end-date').value = today.toISOString().split('T')[0];
}

// 从Tushare获取数据
async function fetchTushareData() {
    const symbol = document.getElementById('tushare-symbol').value.trim();
    const startDate = document.getElementById('tushare-start-date').value;
    const endDate = document.getElementById('tushare-end-date').value;

    if (!symbol) {
        utils.showToast('请输入股票代码', 'error');
        return;
    }

    if (!startDate || !endDate) {
        utils.showToast('请选择日期范围', 'error');
        return;
    }

    const container = document.getElementById('tushare-fetch-result');
    container.innerHTML = '<div class="loading">获取数据中...</div>';

    try {
        const result = await utils.request(`${API_BASE}/backtest/fetch-data`, {
            method: 'POST',
            body: JSON.stringify({
                symbol: symbol,
                start_date: startDate,
                end_date: endDate
            })
        });

        container.innerHTML = `
            <div class="signal-item" style="background: rgba(46, 204, 113, 0.1);">
                ✅ ${result.message}<br>
                数据量: ${result.count} 条 | 时间范围: ${result.date_range.start} ~ ${result.date_range.end}
            </div>
        `;

        // 自动填充回测标的
        document.getElementById('backtest-symbol').value = symbol;

        // 刷新数据列表
        await loadImportedDataList();
    } catch (error) {
        container.innerHTML = `<div class="text-muted" style="color: var(--danger-color);">${error.message}</div>`;
    }
}

// 下载导入模板
async function downloadBacktestTemplate() {
    try {
        const response = await Auth.fetch(`${API_BASE}/backtest/template`);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = '历史价格数据导入模板.xlsx';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        utils.showToast('下载模板失败', 'error');
    }
}

// 导入历史价格数据
async function importPriceData() {
    const symbol = document.getElementById('import-symbol').value.trim();
    const name = document.getElementById('import-name').value.trim();
    const fileInput = document.getElementById('import-file');

    if (!symbol) {
        utils.showToast('请输入标的代码', 'error');
        return;
    }

    if (!fileInput.files || fileInput.files.length === 0) {
        utils.showToast('请选择数据文件', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('symbol', symbol);
    formData.append('name', name);
    formData.append('file', fileInput.files[0]);

    try {
        const response = await Auth.fetch(`${API_BASE}/backtest/import-prices`, {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (result.success) {
            utils.showToast(result.data.message);
            document.getElementById('import-result').innerHTML = `
                <div class="signal-item" style="background: rgba(46, 204, 113, 0.1);">
                    ✅ 导入成功：${result.data.count} 条数据，时间范围：${result.data.date_range.start} ~ ${result.data.date_range.end}
                </div>
            `;
            // 清空输入
            document.getElementById('import-symbol').value = '';
            document.getElementById('import-name').value = '';
            fileInput.value = '';
            // 刷新数据列表
            await loadImportedDataList();
        } else {
            utils.showToast(result.message || '导入失败', 'error');
        }
    } catch (error) {
        utils.showToast('导入失败: ' + error.message, 'error');
    }
}

// 加载已导入的数据列表
async function loadImportedDataList() {
    try {
        const histories = await utils.request(`${API_BASE}/backtest/price-histories`);
        const container = document.getElementById('imported-data-list');
        const select = document.getElementById('backtest-symbol');

        if (!histories || histories.length === 0) {
            container.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 20px;">暂无导入数据</div>';
            select.innerHTML = '<option value="">请先获取数据</option>';
            return;
        }

        // 更新表格
        let html = '<table class="data-table"><thead><tr><th>代码</th><th>名称</th><th>类型</th><th>数据条数</th><th>开始日期</th><th>结束日期</th><th>操作</th></tr></thead><tbody>';
        histories.forEach(h => {
            const typeLabel = h.asset_type === 'fund' ? '基金' : '股票';
            html += `
                <tr>
                    <td>${h.symbol}</td>
                    <td>${h.name || '--'}</td>
                    <td>${typeLabel}</td>
                    <td>${h.count}</td>
                    <td>${h.start_date || '--'}</td>
                    <td>${h.end_date || '--'}</td>
                    <td><button class="btn btn-sm btn-warning" onclick="deletePriceHistory('${h.symbol}')">删除</button></td>
                </tr>
            `;
        });
        html += '</tbody></table>';
        container.innerHTML = html;

        // 更新下拉框 - 显示代码和名称
        select.innerHTML = histories.map(h => {
            const displayText = h.name ? `${h.symbol} - ${h.name}` : h.symbol;
            return `<option value="${h.symbol}">${displayText} (${h.count}条)</option>`;
        }).join('');
    } catch (error) {
        console.error('加载数据列表失败:', error);
    }
}

// 删除历史价格数据
async function deletePriceHistory(symbol) {
    if (!confirm(`确定要删除 ${symbol} 的历史数据吗？`)) {
        return;
    }

    try {
        await utils.request(`${API_BASE}/backtest/price-histories/${symbol}`, {
            method: 'DELETE'
        });
        utils.showToast('删除成功');
        await loadImportedDataList();
        await loadQuickSelectSymbols();
    } catch (error) {
        utils.showToast('删除失败', 'error');
    }
}

// AI 分析
let aiTaskId = null;
let aiPollInterval = null;

// 维度名称映射
const dimNames = {
    'market': { name: '市场分析', icon: '📊' },
    'fundamentals': { name: '基本面分析', icon: '💰' },
    'technical': { name: '技术分析', icon: '📈' },
    'capital_flow': { name: '资金面分析', icon: '💵' },
    'sector': { name: '板块分析', icon: '🏭' },
    'trader_plan': { name: '交易员计划', icon: '💼' },
    'market_overview': { name: '大盘分析', icon: '📊' },
    'news': { name: '新闻分析', icon: '📰' },
    'bull_view': { name: '多头观点', icon: '🐂' },
    'bear_view': { name: '空头观点', icon: '🐻' },
    'verdict': { name: '综合裁决', icon: '⚖️' },
    'aggressive': { name: '激进策略', icon: '⚡' },
    'conservative': { name: '保守策略', icon: '🛡️' },
    'neutral': { name: '中性策略', icon: '⚖️' },
    'investment_advice': { name: '投资建议', icon: '📋' },
    'suggestion': { name: '综合建议', icon: '📋' }
};

async function runAIAnalysis() {
    const container = document.getElementById('ai-result');
    const tabsContainer = document.getElementById('ai-result-tabs');
    const progressContainer = document.getElementById('ai-progress-container');

    // 隐藏之前的结果
    tabsContainer.style.display = 'none';
    container.innerHTML = '';

    // 获取分析类型
    const analysisType = document.querySelector('input[name="ai-analysis-type"]:checked')?.value || 'single';

    // 获取分析维度
    const dimensions = Array.from(document.querySelectorAll('input[name="ai-dimension"]:checked')).map(cb => cb.value);

    if (dimensions.length === 0) {
        utils.showToast('请选择至少一个分析维度', 'error');
        return;
    }

    const data = {
        analysis_type: analysisType,
        dimensions: dimensions
    };

    // 单标的分析需要获取选中的持仓
    if (analysisType === 'single') {
        const positionId = document.getElementById('ai-position-select').value;
        if (!positionId) {
            utils.showToast('请选择要分析的标的', 'error');
            return;
        }
        data.position_id = parseInt(positionId);
    }

    try {
        // 先同步最新价格
        showAIProgress('正在同步最新价格数据...', 0, dimensions);
        progressContainer.style.display = 'block';
        document.getElementById('ai-cancel-btn').style.display = 'none';

        try {
            const syncResult = await utils.request(`${API_BASE}/sync-prices`, {
                method: 'POST'
            });
            console.log('价格同步结果:', syncResult);
        } catch (syncError) {
            console.warn('价格同步失败，使用缓存数据:', syncError);
        }

        // 启动异步分析任务
        showAIProgress('正在启动分析任务...', 0, dimensions);

        const taskResult = await utils.request(`${API_BASE}/ai/analyze/start`, {
            method: 'POST',
            body: JSON.stringify(data)
        });

        aiTaskId = taskResult.task_id;
        document.getElementById('ai-cancel-btn').style.display = 'inline-block';

        // 开始轮询进度
        startAIPolling(aiTaskId, dimensions);

    } catch (error) {
        progressContainer.style.display = 'none';
        container.innerHTML = `<div class="text-muted" style="color: var(--danger-color);">${error.message}</div>`;
        tabsContainer.style.display = 'none';
    }
}

function showAIProgress(currentText, progress, dimensions) {
    const progressContainer = document.getElementById('ai-progress-container');
    const progressFill = document.getElementById('ai-progress-fill');
    const progressPercent = document.getElementById('ai-progress-percent');
    const progressCurrent = document.getElementById('ai-progress-current');
    const dimensionsStatus = document.getElementById('ai-dimensions-status');

    progressContainer.style.display = 'block';
    progressFill.style.width = `${progress}%`;
    progressPercent.textContent = `${progress}%`;
    progressCurrent.textContent = currentText;

    // 显示维度状态列表
    let statusHtml = '';
    dimensions.forEach(dim => {
        const dimInfo = dimNames[dim] || { name: dim, icon: '📄' };
        statusHtml += `<span class="ai-dimension-status pending" id="dim-status-${dim}">${dimInfo.icon} ${dimInfo.name} ⏳</span>`;
    });
    dimensionsStatus.innerHTML = statusHtml;
}

function startAIPolling(taskId, dimensions) {
    // 清除之前的轮询
    if (aiPollInterval) {
        clearInterval(aiPollInterval);
    }

    // 每2秒轮询一次
    aiPollInterval = setInterval(async () => {
        try {
            const status = await utils.request(`${API_BASE}/ai/analyze/status/${taskId}`);

            updateAIPProgressUI(status, dimensions);

            if (status.status === 'completed') {
                clearInterval(aiPollInterval);
                aiPollInterval = null;
                document.getElementById('ai-cancel-btn').style.display = 'none';
                await loadAIResult(taskId);
            } else if (status.status === 'failed' || status.status === 'cancelled') {
                clearInterval(aiPollInterval);
                aiPollInterval = null;
                document.getElementById('ai-cancel-btn').style.display = 'none';
                document.getElementById('ai-result').innerHTML = `<div class="text-muted" style="color: var(--danger-color);">${status.error_message || '分析失败'}</div>`;
            }
        } catch (error) {
            console.error('轮询进度失败:', error);
        }
    }, 2000);
}

function updateAIPProgressUI(status, dimensions) {
    const progressFill = document.getElementById('ai-progress-fill');
    const progressPercent = document.getElementById('ai-progress-percent');
    const progressCurrent = document.getElementById('ai-progress-current');

    const percentage = status.progress_percentage || 0;
    progressFill.style.width = `${percentage}%`;
    progressPercent.textContent = `${percentage}%`;

    if (status.current_dimension) {
        const dimInfo = dimNames[status.current_dimension] || { name: status.current_dimension, icon: '📄' };
        progressCurrent.textContent = `正在分析: ${dimInfo.icon} ${dimInfo.name}`;
    }

    // 更新各维度状态
    if (status.dimensions_status) {
        for (const [dim, dimStatus] of Object.entries(status.dimensions_status)) {
            const statusEl = document.getElementById(`dim-status-${dim}`);
            if (statusEl) {
                const dimInfo = dimNames[dim] || { name: dim, icon: '📄' };
                let icon = '⏳';
                let className = 'pending';

                if (dimStatus.status === 'completed') {
                    icon = '✅';
                    className = 'completed';
                } else if (dimStatus.status === 'running') {
                    icon = '🔄';
                    className = 'running';
                } else if (dimStatus.status === 'failed') {
                    icon = '❌';
                    className = 'failed';
                }

                statusEl.className = `ai-dimension-status ${className}`;
                statusEl.innerHTML = `${dimInfo.icon} ${dimInfo.name} ${icon}`;

                // 显示评分
                if (dimStatus.score) {
                    statusEl.innerHTML += ` <span style="font-weight: 500;">(${dimStatus.score}分)</span>`;
                }
            }
        }
    }
}

async function loadAIResult(taskId) {
    const container = document.getElementById('ai-result');
    const tabsContainer = document.getElementById('ai-result-tabs');
    const progressContainer = document.getElementById('ai-progress-container');

    try {
        const result = await utils.request(`${API_BASE}/ai/analyze/result/${taskId}`);

        // 隐藏进度条
        progressContainer.style.display = 'none';

        // 使用统一的结果显示函数
        displayAIResult(result, container, tabsContainer);

        // 刷新历史记录
        await aiPage.loadHistory();

    } catch (error) {
        progressContainer.style.display = 'none';
        container.innerHTML = `<div class="text-muted" style="color: var(--danger-color);">${error.message}</div>`;
    }
}

async function cancelAIAnalysisTask() {
    if (!aiTaskId) return;

    try {
        await utils.request(`${API_BASE}/ai/tasks/${aiTaskId}/cancel`, {
            method: 'POST'
        });

        if (aiPollInterval) {
            clearInterval(aiPollInterval);
            aiPollInterval = null;
        }

        document.getElementById('ai-cancel-btn').style.display = 'none';
        document.getElementById('ai-progress-current').textContent = '分析已取消';
        utils.showToast('分析任务已取消');

    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 查看异步任务结果
async function viewAITaskResult(taskId) {
    const container = document.getElementById('ai-result');
    const tabsContainer = document.getElementById('ai-result-tabs');
    const progressContainer = document.getElementById('ai-progress-container');

    progressContainer.style.display = 'none';

    try {
        const result = await utils.request(`${API_BASE}/ai/analyze/result/${taskId}`);
        displayAIResult(result, container, tabsContainer);
    } catch (error) {
        container.innerHTML = `<div class="text-muted" style="color: var(--danger-color);">${error.message}</div>`;
        tabsContainer.style.display = 'none';
    }
}

// 删除异步任务
async function deleteAITask(taskId) {
    if (!confirm('确定要删除这条分析记录吗？')) {
        return;
    }

    try {
        await utils.request(`${API_BASE}/ai/tasks/${taskId}`, {
            method: 'DELETE'
        });
        utils.showToast('删除成功');
        await aiPage.loadHistory();
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 统一显示AI分析结果
function displayAIResult(result, container, tabsContainer) {
    const tabsHeader = document.getElementById('ai-tabs-header');
    const tabsContent = document.getElementById('ai-tabs-content');

    // 确定维度结果来源
    const dimensionsResult = result.dimensions_result || (result.dimensions ? result.dimensions : {});

    if (dimensionsResult && Object.keys(dimensionsResult).length > 1) {
        // 多维度分析结果 - 使用Tab切换
        container.innerHTML = '';
        tabsContainer.style.display = 'block';

        // 生成Tab头部
        let headerHtml = '';
        let contentHtml = '';
        const dimKeys = Object.keys(dimensionsResult);
        dimKeys.forEach((dim, index) => {
            const dimInfo = dimNames[dim] || { name: dim, icon: '📄' };
            const content = dimensionsResult[dim];
            const score = content.score ? `<span class="tag ${content.score >= 6 ? 'success' : content.score >= 4 ? 'warning' : 'danger'}">${content.score}分</span>` : '';

            headerHtml += `<button class="ai-tab-btn ${index === 0 ? 'active' : ''}" onclick="switchAITab('${dim}')">${dimInfo.icon} ${dimInfo.name} ${score}</button>`;

            const analysisText = content.analysis || '';
            contentHtml += `
                <div class="ai-tab-panel ${index === 0 ? 'active' : ''}" id="tab-panel-${dim}">
                    <div class="ai-dimension-result">
                        ${score ? `<div style="margin-bottom: 12px;"><span style="font-weight: 600;">评分：</span>${score}</div>` : ''}
                        <div class="analysis-content">${typeof marked !== 'undefined' ? marked.parse(analysisText) : analysisText}</div>
                    </div>
                </div>
            `;
        });

        tabsHeader.innerHTML = headerHtml;
        tabsContent.innerHTML = contentHtml;

        // 综合评分显示
        const overallScore = result.overall_score;
        if (overallScore) {
            const scoreClass = overallScore >= 6 ? 'success' : overallScore >= 4 ? 'warning' : 'danger';
            container.innerHTML = `
                <div class="signal-item" style="margin-bottom: 16px; background: rgba(74, 144, 226, 0.1); padding: 12px; border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600;">🎯 综合评分</span>
                        <span class="tag ${scoreClass}" style="font-size: 18px; padding: 6px 16px;">${overallScore}/10</span>
                    </div>
                </div>
            `;
        } else {
            container.innerHTML = '';
        }
    } else if (dimensionsResult && Object.keys(dimensionsResult).length === 1) {
        // 单维度分析结果
        tabsContainer.style.display = 'none';
        const dim = Object.keys(dimensionsResult)[0];
        const content = dimensionsResult[dim];
        const dimInfo = dimNames[dim] || { name: dim, icon: '📄' };
        const score = content.score ? `<span class="tag ${content.score >= 6 ? 'success' : content.score >= 4 ? 'warning' : 'danger'}">${content.score}分</span>` : '';

        container.innerHTML = `
            <div class="ai-dimension-result">
                <h4>${dimInfo.icon} ${dimInfo.name} ${score}</h4>
                <div class="analysis-content">${typeof marked !== 'undefined' ? marked.parse(content.analysis || '') : content.analysis || ''}</div>
            </div>
        `;
    } else if (result.analysis) {
        // 全仓分析结果
        tabsContainer.style.display = 'none';
        container.innerHTML = `<div class="ai-analysis-content">${typeof marked !== 'undefined' ? marked.parse(result.analysis) : result.analysis}</div>`;
    } else {
        tabsContainer.style.display = 'none';
        container.innerHTML = '<div class="text-muted">暂无分析结果</div>';
    }
}

// 切换AI分析Tab
function switchAITab(dim) {
    // 更新Tab按钮状态
    document.querySelectorAll('.ai-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.ai-tab-btn[onclick="switchAITab('${dim}')"]`).classList.add('active');

    // 更新Tab内容显示
    document.querySelectorAll('.ai-tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    document.getElementById(`tab-panel-${dim}`).classList.add('active');
}

// 切换AI分析类型
function toggleAIAnalysisType() {
    const analysisType = document.querySelector('input[name="ai-analysis-type"]:checked')?.value;
    const singleOptions = document.getElementById('ai-single-options');

    if (analysisType === 'single') {
        singleOptions.style.display = 'block';
    } else {
        singleOptions.style.display = 'none';
    }
}

// 查看AI分析历史
async function viewAIHistory(id) {
    try {
        const result = await utils.request(`${API_BASE}/ai/history/${id}`);
        const container = document.getElementById('ai-result');
        const tabsContainer = document.getElementById('ai-result-tabs');
        const progressContainer = document.getElementById('ai-progress-container');

        progressContainer.style.display = 'none';

        if (result.analysis_content) {
            const content = typeof result.analysis_content === 'string' ? JSON.parse(result.analysis_content) : result.analysis_content;

            // 构造统一格式
            const unifiedResult = {
                dimensions_result: content.dimensions || null,
                analysis: content.analysis || null,
                overall_score: content.overall_score || result.overall_score
            };

            displayAIResult(unifiedResult, container, tabsContainer);
        } else {
            container.innerHTML = '<div class="text-muted">暂无分析结果</div>';
            tabsContainer.style.display = 'none';
        }
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 删除AI分析历史
async function deleteAIHistory(id) {
    if (!confirm('确定要删除这条分析记录吗？')) {
        return;
    }

    try {
        await utils.request(`${API_BASE}/ai/history/${id}`, {
            method: 'DELETE'
        });
        utils.showToast('删除成功');
        await aiPage.loadHistory();
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 测试 LLM 连接
async function testLLMConnection() {
    const data = {
        provider: document.getElementById('llm-provider').value,
        model: document.getElementById('llm-model').value,
        api_base: document.getElementById('llm-base').value,
        api_key: document.getElementById('llm-key').value
    };

    try {
        const result = await utils.request(`${API_BASE}/configs/test-llm`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        utils.showToast('连接成功');
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 保存 LLM 配置
async function saveLLMConfig() {
    const data = {
        provider: document.getElementById('llm-provider').value,
        model: document.getElementById('llm-model').value,
        api_base: document.getElementById('llm-base').value,
        temperature: parseFloat(document.getElementById('llm-temperature').value),
        max_tokens: parseInt(document.getElementById('llm-max-tokens').value),
        enabled: true  // 保存配置时自动启用
    };

    const apiKey = document.getElementById('llm-key').value;
    if (apiKey && apiKey !== '******') {
        data.api_key = apiKey;
    }

    try {
        await utils.request(`${API_BASE}/configs/llm`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        utils.showToast('配置保存成功，AI分析已启用');
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 保存策略配置
async function saveStrategyConfig() {
    const data = {
        stop_profit_target: parseFloat(document.getElementById('strategy-stop-profit').value),
        max_loss: parseFloat(document.getElementById('strategy-max-loss').value)
    };

    try {
        await utils.request(`${API_BASE}/configs/strategy`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        utils.showToast('策略配置保存成功');
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 保存Tushare配置
async function saveTushareConfig() {
    const token = document.getElementById('tushare-token').value;
    const baseUrl = document.getElementById('tushare-base-url').value;

    const data = {};
    if (token && token !== '******') {
        data.token = token;
    }
    if (baseUrl) {
        data.base_url = baseUrl;
    }

    if (Object.keys(data).length === 0) {
        utils.showToast('没有需要保存的配置', 'warning');
        return;
    }

    try {
        await utils.request(`${API_BASE}/configs/tushare`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        utils.showToast('Tushare配置保存成功');
        await settingsPage.loadTushareConfig();
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 测试Tushare连接
async function testTushareConnection() {
    const token = document.getElementById('tushare-token').value;
    const baseUrl = document.getElementById('tushare-base-url').value;
    const statusText = document.getElementById('tushare-status-text');

    statusText.textContent = '状态: 测试中...';
    statusText.parentElement.style.background = 'rgba(108, 117, 125, 0.1)';

    const data = {};
    if (token && token !== '******') {
        data.token = token;
    }
    if (baseUrl) {
        data.base_url = baseUrl;
    }

    try {
        const result = await utils.request(`${API_BASE}/configs/tushare/test`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        statusText.textContent = `状态: ✅ 连接成功 - 积分: ${result.points || 'N/A'}`;
        statusText.parentElement.style.background = 'rgba(46, 204, 113, 0.1)';
        utils.showToast('Tushare连接成功');
    } catch (error) {
        statusText.textContent = `状态: ❌ 连接失败 - ${error.message}`;
        statusText.parentElement.style.background = 'rgba(220, 53, 69, 0.1)';
        utils.showToast(error.message, 'error');
    }
}

// 更新 LLM 模型选项
function updateLLMModels() {
    const provider = document.getElementById('llm-provider').value;
    const modelSelect = document.getElementById('llm-model');

    const models = {
        openai: [
            { value: 'gpt-4', label: 'GPT-4' },
            { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
            { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
        ],
        anthropic: [
            { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' },
            { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet' },
            { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku' }
        ],
        deepseek: [
            { value: 'deepseek-chat', label: 'DeepSeek Chat' },
            { value: 'deepseek-coder', label: 'DeepSeek Coder' }
        ],
        bailian: [
            { value: 'qwen-turbo', label: 'Qwen Turbo' },
            { value: 'qwen-plus', label: 'Qwen Plus' },
            { value: 'qwen-max', label: 'Qwen Max' },
            { value: 'qwen-max-longcontext', label: 'Qwen Max Long Context' }
        ],
        qwen: [
            { value: 'qwen-turbo', label: 'Qwen Turbo' },
            { value: 'qwen-plus', label: 'Qwen Plus' },
            { value: 'qwen-max', label: 'Qwen Max' },
            { value: 'qwen-max-longcontext', label: 'Qwen Max Long Context' }
        ],
        glm: [
            { value: 'glm-4', label: 'GLM-4' },
            { value: 'glm-4-flash', label: 'GLM-4 Flash' },
            { value: 'glm-4-air', label: 'GLM-4 Air' },
            { value: 'glm-3-turbo', label: 'GLM-3 Turbo' }
        ],
        minimax: [
            { value: 'abab6.5-chat', label: 'ABAB 6.5 Chat' },
            { value: 'abab5.5-chat', label: 'ABAB 5.5 Chat' },
            { value: 'abab5.5s-chat', label: 'ABAB 5.5S Chat' }
        ],
        custom: []
    };

    modelSelect.innerHTML = '';
    (models[provider] || []).forEach(m => {
        const option = document.createElement('option');
        option.value = m.value;
        option.textContent = m.label;
        modelSelect.appendChild(option);
    });
}

// 关闭模态框
function closeModal() {
    modalManager.close();
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 检查登录状态
    if (!Auth.isLoggedIn()) {
        window.location.href = 'login.html';
        return;
    }

    // 显示当前用户信息
    const user = Auth.getUser();
    if (user) {
        const userSpan = document.getElementById('current-username');
        if (userSpan) {
            userSpan.textContent = user.username;
        }
        // 移动端用户名
        const mobileUserSpan = document.getElementById('mobile-username');
        if (mobileUserSpan) {
            mobileUserSpan.textContent = user.username;
        }
    }

    pageManager.init();
    pageManager.showPage('dashboard');
});

// 切换侧边栏（移动端）
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    const menuToggle = document.querySelector('.menu-toggle');

    sidebar.classList.toggle('show');
    overlay.classList.toggle('show');
    menuToggle.classList.toggle('active');
}

// 切换账户
function switchAccount(accountId) {
    pageManager.switchAccount(accountId);
}

// 点击模态框外部关闭
// 刷新收益曲线
function refreshProfitChart() {
    const activeBtn = document.querySelector('.time-btn.active');
    const days = activeBtn ? parseInt(activeBtn.dataset.days) : 30;
    const accountId = pageManager.currentAccountId;
    Charts.renderProfitCurve('profit-chart', accountId, days);
}

// 选择时间范围
function selectTimeRange(btn, days) {
    // 更新按钮状态
    document.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // 刷新图表
    const accountId = pageManager.currentAccountId;
    Charts.renderProfitCurve('profit-chart', accountId, days);
}

// 显示自定义日期范围
function showCustomDateRange() {
    // 创建自定义日期面板
    const panel = document.getElementById('custom-date-panel') || createCustomDatePanel();
    panel.classList.add('show');

    // 设置默认日期
    const today = new Date().toISOString().split('T')[0];
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    document.getElementById('custom-start-date').value = thirtyDaysAgo;
    document.getElementById('custom-end-date').value = today;
}

// 创建自定义日期面板
function createCustomDatePanel() {
    const panel = document.createElement('div');
    panel.id = 'custom-date-panel';
    panel.className = 'date-range-panel';
    panel.innerHTML = `
        <h4>选择日期范围</h4>
        <div class="quick-date-options">
            <button class="quick-date-btn" onclick="setQuickDateRange('week')">本周</button>
            <button class="quick-date-btn" onclick="setQuickDateRange('month')">本月</button>
            <button class="quick-date-btn" onclick="setQuickDateRange('quarter')">本季度</button>
            <button class="quick-date-btn" onclick="setQuickDateRange('year')">今年</button>
            <button class="quick-date-btn" onclick="setQuickDateRange('last-month')">上月</button>
            <button class="quick-date-btn" onclick="setQuickDateRange('last-year')">去年</button>
        </div>
        <div class="date-range-inputs">
            <div class="form-group">
                <label>开始日期</label>
                <input type="date" id="custom-start-date" class="form-input">
            </div>
            <div class="form-group">
                <label>结束日期</label>
                <input type="date" id="custom-end-date" class="form-input">
            </div>
        </div>
        <div class="date-range-actions">
            <button class="btn btn-secondary" onclick="closeCustomDatePanel()">取消</button>
            <button class="btn btn-primary" onclick="applyCustomDateRange()">确定</button>
        </div>
    `;
    document.body.appendChild(panel);

    // 点击外部关闭
    panel.addEventListener('click', (e) => {
        if (e.target === panel) {
            panel.classList.remove('show');
        }
    });

    return panel;
}

function closeCustomDatePanel() {
    const panel = document.getElementById('custom-date-panel');
    if (panel) {
        panel.classList.remove('show');
    }
}

// 设置快捷日期范围
function setQuickDateRange(range) {
    const today = new Date();
    let startDate, endDate = today;

    switch (range) {
        case 'week':
            startDate = new Date(today);
            startDate.setDate(today.getDate() - today.getDay());
            break;
        case 'month':
            startDate = new Date(today.getFullYear(), today.getMonth(), 1);
            break;
        case 'quarter':
            const quarterMonth = Math.floor(today.getMonth() / 3) * 3;
            startDate = new Date(today.getFullYear(), quarterMonth, 1);
            break;
        case 'year':
            startDate = new Date(today.getFullYear(), 0, 1);
            break;
        case 'last-month':
            startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            endDate = new Date(today.getFullYear(), today.getMonth(), 0);
            break;
        case 'last-year':
            startDate = new Date(today.getFullYear() - 1, 0, 1);
            endDate = new Date(today.getFullYear() - 1, 11, 31);
            break;
    }

    document.getElementById('custom-start-date').value = startDate.toISOString().split('T')[0];
    document.getElementById('custom-end-date').value = endDate.toISOString().split('T')[0];
}

// 关闭自定义日期面板
function closeCustomDatePanel() {
    const panel = document.getElementById('custom-date-panel');
    if (panel) {
        panel.classList.remove('show');
    }
}

// 应用自定义日期范围
function applyCustomDateRange() {
    const startDate = document.getElementById('custom-start-date').value;
    const endDate = document.getElementById('custom-end-date').value;

    if (!startDate || !endDate) {
        utils.showToast('请选择开始和结束日期', 'error');
        return;
    }

    if (new Date(startDate) > new Date(endDate)) {
        utils.showToast('开始日期不能大于结束日期', 'error');
        return;
    }

    // 更新按钮状态
    document.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
    const customBtn = document.querySelector('.time-btn[data-days="custom"]');
    if (customBtn) {
        customBtn.classList.add('active');
    }

    // 计算天数
    const days = Math.ceil((new Date(endDate) - new Date(startDate)) / (1000 * 60 * 60 * 24));

    // 刷新图表
    const accountId = pageManager.currentAccountId;
    Charts.renderProfitCurve('profit-chart', accountId, days);

    closeCustomDatePanel();
}

// ========== 导入导出 ==========

// 导出持仓
async function exportPositions() {
    const accountId = pageManager.currentAccountId;
    try {
        const response = await Auth.fetch(`${API_BASE}/export/positions${accountId ? '?account_id=' + accountId : ''}`);
        const contentType = response.headers.get('content-type');

        if (contentType && contentType.includes('application/json')) {
            const result = await response.json();
            utils.showToast(result.message || '导出失败', result.success ? 'success' : 'error');
            return;
        }

        // 下载文件
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'positions.xlsx';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        utils.showToast(error.message || '导出失败', 'error');
    }
}

// 导出交易记录
async function exportTrades() {
    const accountId = pageManager.currentAccountId;
    try {
        const response = await Auth.fetch(`${API_BASE}/export/trades${accountId ? '?account_id=' + accountId : ''}`);
        const contentType = response.headers.get('content-type');

        if (contentType && contentType.includes('application/json')) {
            const result = await response.json();
            utils.showToast(result.message || '没有可导出的交易记录', result.success ? 'success' : 'warning');
            return;
        }

        // 下载文件
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'trades.xlsx';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        utils.showToast(error.message || '导出失败', 'error');
    }
}

// 显示导入模态框（持仓）
function showImportModal() {
    const content = `
        <div style="text-align: center; padding: 20px;">
            <p>支持 Excel (.xlsx, .xls) 和 CSV 文件格式</p>
            <p style="color: var(--text-muted); font-size: 12px;">
                <strong>必填字段：</strong>代码、名称、数量、成本价<br>
                <strong>可选字段：</strong>类型、现价、总成本、市值、收益率、分类、备注
            </p>
            <div style="margin-top: 16px;">
                <button class="btn btn-primary" onclick="document.getElementById('import-file').click()">选择文件</button>
                <a href="${API_BASE}/import/template" class="btn btn-secondary" style="margin-left: 8px;">下载模板</a>
            </div>
        </div>
    `;
    modalManager.show('导入持仓', content, '');
}

// 显示交易记录导入模态框
function showTradesImportModal() {
    const content = `
        <div style="text-align: center; padding: 20px;">
            <p>支持 Excel (.xlsx, .xls) 文件格式</p>
            <p style="color: var(--text-muted); font-size: 12px;">
                <strong>必填字段：</strong>日期、代码、类型、数量、价格<br>
                <strong>可选字段：</strong>金额、理由、备注
            </p>
            <div style="margin-top: 16px;">
                <button class="btn btn-primary" onclick="document.getElementById('import-trades-file').click()">选择文件</button>
                <a href="${API_BASE}/import/trades/template" class="btn btn-secondary" style="margin-left: 8px;">下载模板</a>
            </div>
        </div>
    `;
    modalManager.show('导入交易记录', content, '');
}

// 持仓文件选择处理
document.getElementById('import-file').addEventListener('change', async function(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('account_id', pageManager.currentAccountId);

    try {
        const response = await Auth.fetch(`${API_BASE}/import/positions`, {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (result.success) {
            utils.showToast(result.message);
            closeModal();
            pageManager.loadPageData(pageManager.currentPage);
        } else {
            utils.showToast(result.message, 'error');
        }
    } catch (error) {
        utils.showToast(error.message, 'error');
    }

    // 清空文件选择
    this.value = '';
});

// 交易记录文件选择处理
const tradesFileInput = document.getElementById('import-trades-file');
if (tradesFileInput) {
    tradesFileInput.addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await Auth.fetch(`${API_BASE}/import/trades`, {
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            if (result.success) {
                utils.showToast(result.message);
                closeModal();
                pageManager.loadPageData(pageManager.currentPage);
            } else {
                utils.showToast(result.message, 'error');
            }
        } catch (error) {
            utils.showToast(error.message, 'error');
        }

        // 清空文件选择
        this.value = '';
    });
}

// ============ 数据源相关函数 ============

// 同步持仓价格
async function syncPositionPrices() {
    try {
        utils.showToast('正在同步持仓价格和近一周历史数据...');

        const result = await utils.request(`${API_BASE}/sync-prices`, {
            method: 'POST'
        });

        const msg = result.message || `成功更新 ${result.updated} 条持仓价格`;
        const historyMsg = result.history_updated ? `，获取 ${result.history_updated} 条历史数据` : '';
        utils.showToast(msg + historyMsg);

        // 刷新当前页面数据
        if (pageManager.currentPage === 'dashboard') {
            await dashboardPage.load(pageManager.currentAccountId);
        } else if (pageManager.currentPage === 'positions') {
            await positionsPage.load(pageManager.currentAccountId);
        }
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 获取持仓历史数据（后台分批获取）
let historyFetchInterval = null;

async function fetchPositionHistory() {
    try {
        // 先检查是否已有任务在运行
        const progressResult = await utils.request(`${API_BASE}/fetch-history/progress`);

        if (progressResult.status === 'running') {
            utils.showToast('已有获取任务在运行，请等待完成');
            showFetchProgress();
            return;
        }

        // 启动后台获取任务
        const result = await utils.request(`${API_BASE}/fetch-history/background`, {
            method: 'POST',
            body: JSON.stringify({ years: 10 })
        });

        if (result.success) {
            utils.showToast(result.message || '后台获取任务已启动');
            showFetchProgress();
        } else {
            utils.showToast(result.message || '启动失败', 'error');
        }
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 显示获取进度
async function showFetchProgress() {
    // 每5秒检查一次进度
    if (historyFetchInterval) {
        clearInterval(historyFetchInterval);
    }

    historyFetchInterval = setInterval(async () => {
        try {
            const progress = await utils.request(`${API_BASE}/fetch-history/progress`);

            if (progress.status === 'running') {
                const symbol = progress.current_symbol || '';
                const name = progress.current_name || '';
                const completed = progress.completed || 0;
                const total = progress.total || 0;
                const pct = total > 0 ? Math.round(completed / total * 100) : 0;

                utils.showToast(`${name} (${symbol}) - 进度: ${completed}/${total} (${pct}%)`);
            } else if (progress.status === 'completed') {
                clearInterval(historyFetchInterval);
                historyFetchInterval = null;
                utils.showToast(progress.message || '获取完成！', 'success');
            } else if (progress.status === 'stopped') {
                clearInterval(historyFetchInterval);
                historyFetchInterval = null;
                utils.showToast(progress.message || '已停止', 'warning');
            } else if (progress.status === 'error') {
                clearInterval(historyFetchInterval);
                historyFetchInterval = null;
                utils.showToast(progress.message || '获取失败', 'error');
            }
        } catch (error) {
            clearInterval(historyFetchInterval);
            historyFetchInterval = null;
        }
    }, 5000);
}

// 停止获取任务
async function stopFetchHistory() {
    try {
        await utils.request(`${API_BASE}/fetch-history/stop`, { method: 'POST' });

        if (historyFetchInterval) {
            clearInterval(historyFetchInterval);
            historyFetchInterval = null;
        }

        utils.showToast('已停止获取任务', 'warning');
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 测试股票数据源
async function testStockDatasource() {
    const statusText = document.getElementById('stock-datasource-status-text');
    statusText.textContent = '状态: 测试中...';
    statusText.parentElement.style.background = 'rgba(108, 117, 125, 0.1)';

    try {
        const result = await utils.request(`${API_BASE}/datasource/test`, {
            method: 'POST',
            body: JSON.stringify({ source: 'akshare', asset_type: 'stock' })
        });

        if (result.success) {
            statusText.textContent = '状态: ✅ 连接成功';
            statusText.parentElement.style.background = 'rgba(46, 204, 113, 0.1)';
            utils.showToast('股票数据源连接成功');
        } else {
            statusText.textContent = `状态: ❌ ${result.message}`;
            statusText.parentElement.style.background = 'rgba(220, 53, 69, 0.1)';
        }
    } catch (error) {
        statusText.textContent = `状态: ❌ ${error.message}`;
        statusText.parentElement.style.background = 'rgba(220, 53, 69, 0.1)';
        utils.showToast(error.message, 'error');
    }
}

// 测试基金数据源
async function testFundDatasource() {
    const statusText = document.getElementById('fund-datasource-status-text');
    statusText.textContent = '状态: 测试中...';
    statusText.parentElement.style.background = 'rgba(108, 117, 125, 0.1)';

    try {
        const result = await utils.request(`${API_BASE}/datasource/test`, {
            method: 'POST',
            body: JSON.stringify({ source: 'eastmoney', asset_type: 'fund' })
        });

        if (result.success) {
            statusText.textContent = '状态: ✅ 连接成功';
            statusText.parentElement.style.background = 'rgba(46, 204, 113, 0.1)';
            utils.showToast('基金数据源连接成功');
        } else {
            statusText.textContent = `状态: ❌ ${result.message}`;
            statusText.parentElement.style.background = 'rgba(220, 53, 69, 0.1)';
        }
    } catch (error) {
        statusText.textContent = `状态: ❌ ${error.message}`;
        statusText.parentElement.style.background = 'rgba(220, 53, 69, 0.1)';
        utils.showToast(error.message, 'error');
    }
}

// 保存股票数据源配置
async function saveStockDatasourceConfig() {
    const type = document.getElementById('stock-datasource-type').value;
    const token = document.getElementById('stock-tushare-token').value;
    const url = document.getElementById('stock-tushare-url').value;

    const data = { type };
    if (token && token !== '******') {
        data.tushare_token = token;
    }
    if (url) {
        data.tushare_base_url = url;
    }

    try {
        const result = await utils.request(`${API_BASE}/datasource/config/stock`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        utils.showToast(result.message || '股票数据源配置保存成功');
        await settingsPage.loadDatasourceStatus();
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}

// 保存基金数据源配置
async function saveFundDatasourceConfig() {
    const type = document.getElementById('fund-datasource-type').value;
    const token = document.getElementById('fund-tushare-token').value;

    const data = { type };
    if (token && token !== '******') {
        data.tushare_token = token;
    }

    try {
        const result = await utils.request(`${API_BASE}/datasource/config/fund`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        utils.showToast(result.message || '基金数据源配置保存成功');
        await settingsPage.loadDatasourceStatus();
    } catch (error) {
        utils.showToast(error.message, 'error');
    }
}