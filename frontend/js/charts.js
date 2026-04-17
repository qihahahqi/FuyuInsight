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
    async renderProfitCurve(canvasId, account_id = null, days = 30) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        try {
            let url = `/api/v1/charts/profit-curve?days=${days}`;
            if (account_id) {
                url += `&account_id=${account_id}`;
            }

            // 使用 utils.request 确保带认证 token
            const data = await utils.request(url);

            if (!data || !data.labels || data.labels.length === 0) {
                canvas.parentElement.innerHTML = '<div class="text-muted" style="text-align: center; padding: 40px;">暂无历史数据<br><small>请先同步持仓价格</small></div>';
                return;
            }

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
                                    return value.toFixed(2) + '%';
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('渲染收益曲线失败:', error);
            canvas.parentElement.innerHTML = '<div class="text-muted" style="text-align: center; padding: 40px;">加载失败<br><small>' + error.message + '</small></div>';
        }
    },

    /**
     * 渲染分布饼图 - 显示每个持仓的分布
     */
    async renderDistribution(canvasId, account_id = null) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        try {
            let url = '/api/v1/charts/distribution';
            if (account_id) {
                url += `?account_id=${account_id}`;
            }

            // 使用 utils.request 确保带认证 token
            const data = await utils.request(url);

            if (!data || !data.by_position || data.by_position.length === 0) {
                canvas.parentElement.innerHTML = '<div class="text-muted" style="text-align: center; padding: 40px;">暂无持仓数据</div>';
                return;
            }

            // 销毁旧图表
            if (this.distributionChart) {
                this.distributionChart.destroy();
            }

            // 使用具体持仓数据生成扇形图
            const positions = data.by_position;

            // 生成颜色数组
            const colors = [
                '#4A90E2', '#28A745', '#FFC107', '#DC3545', '#6C757D',
                '#17A2B8', '#6610F2', '#FD7E14', '#20C997', '#E83E8C',
                '#6F42C1', '#007BFF', '#28A745', '#FFC107', '#DC3545'
            ];

            // 持仓名称作为标签
            const chartLabels = positions.map(p => p.name || p.symbol);
            const chartData = positions.map(p => p.value);
            const chartPercentages = positions.map(p => p.percentage);

            // 创建新图表
            this.distributionChart = new Chart(canvas, {
                type: 'pie',
                data: {
                    labels: chartLabels,
                    datasets: [{
                        data: chartData,
                        backgroundColor: colors.slice(0, positions.length),
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                boxWidth: 12,
                                padding: 8,
                                font: {
                                    size: 11
                                },
                                generateLabels: function(chart) {
                                    const chartData = chart.data;
                                    return chartData.labels.map((label, i) => ({
                                        text: `${label} (${chartPercentages[i]}%)`,
                                        fillStyle: chartData.datasets[0].backgroundColor[i],
                                        hidden: false,
                                        index: i
                                    }));
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const value = context.raw;
                                    const percentage = chartPercentages[context.dataIndex];
                                    return `${context.label}: ${utils.formatMoney(value)} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('渲染分布图失败:', error);
            canvas.parentElement.innerHTML = '<div class="text-muted" style="text-align: center; padding: 40px;">加载失败<br><small>' + error.message + '</small></div>';
        }
    },

    /**
     * 刷新所有图表
     */
    async refreshAll(account_id = null) {
        await Promise.all([
            this.renderProfitCurve('profit-chart', account_id),
            this.renderDistribution('distribution-chart', account_id)
        ]);
    }
};