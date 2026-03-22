/**
 * 图表模块 - 使用 Chart.js
 */

const Charts = {
    // 收益曲线图实例
    profitChart: null,
    // 分布饼图实例
    distributionChart: null,

    /**
     * 渲染收益曲线图
     */
    async renderProfitCurve(canvasId, account_id = 1, days = 30) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        try {
            const response = await fetch(`/api/v1/charts/profit-curve?account_id=${account_id}&days=${days}`);
            const result = await response.json();

            if (!result.success || !result.data.labels.length) {
                canvas.parentElement.innerHTML = '<div class="text-muted" style="text-align: center; padding: 40px;">暂无历史数据</div>';
                return;
            }

            const data = result.data;

            // 销毁旧图表
            if (this.profitChart) {
                this.profitChart.destroy();
            }

            // 创建新图表
            this.profitChart = new Chart(canvas, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: '收益率 (%)',
                        data: data.profit_rates,
                        borderColor: '#4A90E2',
                        backgroundColor: 'rgba(74, 144, 226, 0.1)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 2,
                        pointHoverRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `收益率: ${context.raw.toFixed(2)}%`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('渲染收益曲线失败:', error);
        }
    },

    /**
     * 渲染分布饼图
     */
    async renderDistribution(canvasId, account_id = null) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        try {
            let url = '/api/v1/charts/distribution';
            if (account_id) {
                url += `?account_id=${account_id}`;
            }

            const response = await fetch(url);
            const result = await response.json();

            if (!result.success || !result.data.by_type || Object.keys(result.data.by_type).length === 0) {
                canvas.parentElement.innerHTML = '<div class="text-muted" style="text-align: center; padding: 40px;">暂无持仓数据</div>';
                return;
            }

            const data = result.data;

            // 销毁旧图表
            if (this.distributionChart) {
                this.distributionChart.destroy();
            }

            // 准备数据
            const labels = {
                'etf_index': '宽基ETF',
                'etf_sector': '行业ETF',
                'fund': '基金',
                'stock': '股票'
            };

            const chartLabels = Object.keys(data.by_type).map(k => labels[k] || k);
            const chartData = Object.values(data.by_type).map(v => v.value);
            const colors = ['#4A90E2', '#28A745', '#FFC107', '#DC3545', '#6C757D'];

            // 创建新图表
            this.distributionChart = new Chart(canvas, {
                type: 'doughnut',
                data: {
                    labels: chartLabels,
                    datasets: [{
                        data: chartData,
                        backgroundColor: colors,
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((context.raw / total) * 100).toFixed(1);
                                    return `${context.label}: ${utils.formatMoney(context.raw)} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('渲染分布图失败:', error);
        }
    },

    /**
     * 刷新所有图表
     */
    async refreshAll(account_id = 1) {
        await Promise.all([
            this.renderProfitCurve('profit-chart', account_id),
            this.renderDistribution('distribution-chart', account_id)
        ]);
    }
};