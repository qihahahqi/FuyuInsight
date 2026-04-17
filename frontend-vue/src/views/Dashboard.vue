<template>
  <div>
    <div class="page-header">
      <h1>首页概览</h1>
      <span class="update-time">更新时间: {{ updateTime }}</span>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">总资产</div>
        <div class="stat-value">{{ formatMoney(summary.total_value) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">总成本</div>
        <div class="stat-value">{{ formatMoney(summary.total_cost) }}</div>
      </div>
      <div class="stat-card" :class="summary.total_profit_rate >= 0 ? 'profit' : 'loss'">
        <div class="stat-label">总收益</div>
        <div class="stat-value">{{ formatMoney(summary.total_profit) }}</div>
      </div>
      <div class="stat-card" :class="summary.total_profit_rate >= 0 ? 'profit' : 'loss'">
        <div class="stat-label">收益率</div>
        <div class="stat-value">{{ formatPercent(summary.total_profit_rate) }}</div>
      </div>
    </div>

    <!-- 图表行 -->
    <div class="cards-row">
      <div class="card">
        <div class="card-header">
          <h3>收益曲线</h3>
        </div>
        <div class="card-body">
          <div class="chart-container">
            <canvas ref="profitChart"></canvas>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-header">
          <h3>持仓分布</h3>
        </div>
        <div class="card-body">
          <div class="chart-container">
            <canvas ref="distributionChart"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作信号 -->
    <div class="card">
      <div class="card-header">
        <h3>操作信号</h3>
      </div>
      <div class="card-body">
        <div class="signals-list">
          <div v-if="signals.length === 0" class="empty-text">暂无操作信号</div>
          <div
            v-for="signal in signals"
            :key="signal.symbol"
            class="signal-item"
            :class="signal.type"
          >
            <div class="signal-title">{{ signal.icon }} {{ signal.name }}</div>
            <div class="signal-desc">收益率: {{ formatPercent(signal.profit_rate) }} | {{ signal.suggestion }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 持仓列表 -->
    <div class="card">
      <div class="card-header">
        <h3>持仓列表</h3>
        <button class="btn btn-primary btn-sm" @click="showPositionModal">新增持仓</button>
      </div>
      <div class="card-body">
        <table class="data-table">
          <thead>
            <tr>
              <th>标的</th>
              <th>类型</th>
              <th>数量</th>
              <th>成本价</th>
              <th>现价</th>
              <th>市值</th>
              <th>收益率</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in positions" :key="p.id">
              <td>
                {{ p.name }}<br>
                <small class="text-muted">{{ p.symbol }}</small>
              </td>
              <td><span class="tag">{{ getAssetTypeName(p.asset_type) }}</span></td>
              <td>{{ p.quantity }}</td>
              <td>{{ p.cost_price?.toFixed(3) }}</td>
              <td>{{ p.current_price?.toFixed(3) || '--' }}</td>
              <td>{{ formatMoney(p.market_value) }}</td>
              <td :class="p.profit_rate >= 0 ? 'profit' : 'loss'">
                {{ formatPercent(p.profit_rate) }}
              </td>
              <td>
                <button class="btn btn-icon" @click="editPosition(p.id)">✏️</button>
                <button class="btn btn-icon" @click="deletePosition(p.id)">🗑️</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'
import api from '@/api'
import { formatMoney, formatPercent, getAssetTypeName } from '@/utils/format'

Chart.register(...registerables)

const updateTime = ref(new Date().toLocaleString())
const summary = ref({
  total_value: 0,
  total_cost: 0,
  total_profit: 0,
  total_profit_rate: 0
})
const positions = ref([])
const signals = ref([])
const profitChart = ref(null)
const distributionChart = ref(null)

let profitChartInstance = null
let distributionChartInstance = null

async function loadData() {
  try {
    const [summaryRes, positionsRes, signalsRes] = await Promise.all([
      api.get('/positions/summary'),
      api.get('/positions'),
      api.get('/analysis/signals')
    ])

    if (summaryRes.data.success) {
      summary.value = summaryRes.data.data
    }
    if (positionsRes.data.success) {
      positions.value = positionsRes.data.data
    }
    if (signalsRes.data.success) {
      const data = signalsRes.data.data
      signals.value = [
        ...(data.stop_profit_signals || []).map(s => ({ ...s, type: 'stop-profit', icon: '🔴' })),
        ...(data.add_position_signals || []).map(s => ({ ...s, type: 'add-position', icon: '🟡' }))
      ]
    }

    updateTime.value = new Date().toLocaleString()
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

function showPositionModal() {
  // TODO: 显示新增持仓模态框
}

function editPosition(id) {
  // TODO: 编辑持仓
}

function deletePosition(id) {
  // TODO: 删除持仓
}

onMounted(async () => {
  await loadData()

  // 初始化图表
  if (profitChart.value) {
    profitChartInstance = new Chart(profitChart.value, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: '收益率',
          data: [],
          borderColor: '#4A90E2',
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false
      }
    })
  }

  if (distributionChart.value) {
    distributionChartInstance = new Chart(distributionChart.value, {
      type: 'doughnut',
      data: {
        labels: [],
        datasets: [{
          data: [],
          backgroundColor: ['#4A90E2', '#28A745', '#FFC107', '#DC3545', '#17A2B8']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false
      }
    })
  }
})
</script>

<style lang="scss" scoped>
.cards-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.chart-container {
  height: 250px;
}

.signals-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.signal-item {
  padding: 12px 16px;
  border-radius: 8px;
  background: #f8f9fa;

  &.stop-profit {
    border-left: 4px solid #dc3545;
  }

  &.add-position {
    border-left: 4px solid #ffc107;
  }

  .signal-title {
    font-weight: 500;
  }

  .signal-desc {
    font-size: 14px;
    color: #6c757d;
    margin-top: 4px;
  }
}

.empty-text {
  text-align: center;
  padding: 20px;
  color: #9ca3af;
}

.tag {
  display: inline-block;
  padding: 2px 8px;
  background: #e5e7eb;
  border-radius: 4px;
  font-size: 12px;
}

.text-muted {
  color: #9ca3af;
}

.profit { color: #dc3545; }
.loss { color: #28a745; }

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 4px;
}
</style>