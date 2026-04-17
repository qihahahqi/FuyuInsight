<template>
  <div>
    <div class="page-header">
      <h1>系统设置</h1>
    </div>
    <div class="card">
      <div class="card-header">
        <h3>大模型配置</h3>
      </div>
      <div class="card-body">
        <div class="form-grid">
          <div class="form-group">
            <label>提供商</label>
            <select v-model="config.provider" class="form-input">
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="deepseek">DeepSeek</option>
              <option value="bailian">百炼</option>
              <option value="qwen">通义千问</option>
              <option value="glm">智谱GLM</option>
            </select>
          </div>
          <div class="form-group">
            <label>模型</label>
            <input v-model="config.model" type="text" class="form-input" placeholder="模型名称" />
          </div>
          <div class="form-group">
            <label>API Key</label>
            <input v-model="config.api_key" type="password" class="form-input" placeholder="API Key" />
          </div>
          <div class="form-group">
            <label>API Base URL</label>
            <input v-model="config.api_base" type="text" class="form-input" placeholder="API地址" />
          </div>
        </div>
        <div class="form-actions">
          <button class="btn btn-secondary" @click="testConnection">测试连接</button>
          <button class="btn btn-primary" @click="saveConfig">保存配置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const config = ref({
  provider: 'openai',
  model: '',
  api_key: '',
  api_base: ''
})

async function loadConfig() {
  const res = await api.get('/configs/llm')
  if (res.data.success && res.data.data) {
    Object.assign(config.value, res.data.data)
  }
}

async function saveConfig() {
  const res = await api.put('/configs/llm', config.value)
  if (res.data.success) {
    alert('配置保存成功')
  }
}

async function testConnection() {
  const res = await api.post('/configs/test-llm', config.value)
  if (res.data.success) {
    alert('连接成功')
  } else {
    alert('连接失败: ' + res.data.message)
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style lang="scss" scoped>
.form-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}
</style>