<template>
  <div>
    <div class="page-header">
      <h1>持仓管理</h1>
      <button class="btn btn-primary" @click="showModal = true">新增持仓</button>
    </div>

    <div class="card">
      <div class="card-body">
        <table class="data-table">
          <thead>
            <tr>
              <th>代码</th>
              <th>名称</th>
              <th>类型</th>
              <th>数量</th>
              <th>成本价</th>
              <th>现价</th>
              <th>总成本</th>
              <th>市值</th>
              <th>收益率</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in positions" :key="p.id">
              <td>{{ p.symbol }}</td>
              <td>{{ p.name }}</td>
              <td>{{ getAssetTypeName(p.asset_type) }}</td>
              <td>{{ p.quantity }}</td>
              <td>{{ p.cost_price?.toFixed(3) }}</td>
              <td>{{ p.current_price?.toFixed(3) || '--' }}</td>
              <td>{{ formatMoney(p.total_cost) }}</td>
              <td>{{ formatMoney(p.market_value) }}</td>
              <td :class="p.profit_rate >= 0 ? 'profit' : 'loss'">
                {{ formatPercent(p.profit_rate) }}
              </td>
              <td>
                <button class="btn btn-sm btn-secondary" @click="editPosition(p)">编辑</button>
                <button class="btn btn-sm btn-secondary" @click="deletePosition(p.id)">删除</button>
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
import api from '@/api'
import { formatMoney, formatPercent, getAssetTypeName } from '@/utils/format'

const positions = ref([])
const showModal = ref(false)

async function fetchPositions() {
  const res = await api.get('/positions')
  if (res.data.success) {
    positions.value = res.data.data
  }
}

function editPosition(position) {
  // TODO
}

async function deletePosition(id) {
  if (confirm('确定删除该持仓吗？')) {
    await api.delete(`/positions/${id}`)
    await fetchPositions()
  }
}

onMounted(() => {
  fetchPositions()
})
</script>

<style lang="scss" scoped>
.profit { color: #dc3545; }
.loss { color: #28a745; }
</style>