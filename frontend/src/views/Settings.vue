<template>
  <div>
    <div class="page-header">
      <h1>系统设置</h1>
    </div>

    <!-- 定时任务面板 -->
    <div class="card">
      <div class="card-header">
        <h3>定时任务管理</h3>
      </div>
      <div class="card-body">
        <div class="scheduler-status">
          <div class="status-item">
            <span class="status-label">调度器状态:</span>
            <span :class="schedulerStatus.running ? 'status-running' : 'status-stopped'">
              {{ schedulerStatus.running ? '运行中' : '已停止' }}
            </span>
          </div>
          <div class="status-item">
            <span class="status-label">今日是否交易日:</span>
            <span>{{ schedulerStatus.is_trading_day ? '是' : '否' }}</span>
          </div>
          <div class="status-item">
            <span class="status-label">同步时间点:</span>
            <span>{{ schedulerStatus.sync_hours?.join(', ') || '--' }}点</span>
          </div>
          <div class="status-item">
            <span class="status-label">任务数量:</span>
            <span>{{ schedulerStatus.jobs_count || 0 }}</span>
          </div>
        </div>
        <div class="scheduler-actions">
          <button class="btn btn-primary" @click="triggerSync" :disabled="syncing">
            {{ syncing ? '同步中...' : '立即同步价格' }}
          </button>
          <button class="btn btn-secondary" @click="loadSchedulerStatus">刷新状态</button>
        </div>
        <div v-if="syncResult" class="sync-result">
          <p>{{ syncResult.message }}</p>
        </div>
      </div>
    </div>

    <!-- 策略参数模板 -->
    <div class="card">
      <div class="card-header">
        <h3>策略参数模板</h3>
      </div>
      <div class="card-body">
        <div class="templates-grid">
          <div
            v-for="template in templates"
            :key="template.id"
            class="template-card"
            :class="{ active: selectedTemplate === template.id }"
            @click="selectTemplate(template.id)"
          >
            <div class="template-name">{{ template.name }}</div>
            <div class="template-desc">{{ template.description }}</div>
            <div class="template-preview">
              <div>止盈目标: {{ (template.params.stop_profit_target * 100).toFixed(0) }}%</div>
              <div>最大亏损: {{ (template.params.max_loss * 100).toFixed(0) }}%</div>
              <div>最大加仓: {{ (template.params.max_add_ratio * 100).toFixed(0) }}%</div>
            </div>
          </div>
        </div>
        <div class="form-actions">
          <button class="btn btn-primary" @click="applyTemplate" :disabled="!selectedTemplate">
            应用模板
          </button>
        </div>
      </div>
    </div>

    <!-- 大模型配置 -->
    <div class="card">
      <div class="card-header">
        <h3>大模型配置</h3>
      </div>
      <div class="card-body">
        <div class="form-grid">
          <div class="form-group">
            <label>厂商 / 提供商</label>
            <select v-model="config.provider" class="form-input" @change="onProviderChange">
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="deepseek">DeepSeek（深度求索）</option>
              <option value="bailian">百炼（阿里云）</option>
              <option value="qwen">通义千问</option>
              <option value="glm">智谱GLM</option>
              <option value="minimax">MiniMax</option>
              <option value="bailian-anthropic">百炼(Anthropic兼容)</option>
              <option value="custom">自定义</option>
            </select>
            <small class="form-hint" v-if="providerDescription">{{ providerDescription }}</small>
          </div>
          <div class="form-group">
            <label>API 格式</label>
            <select v-model="config.api_format" class="form-input">
              <option value="">自动判断（推荐）</option>
              <option value="openai">OpenAI 兼容格式</option>
              <option value="anthropic">Anthropic 原生格式</option>
            </select>
            <small class="form-hint">选择 API 请求格式。留空则根据厂商自动判断。</small>
          </div>
          <div class="form-group">
            <label>模型名称</label>
            <input v-model="config.model" type="text" class="form-input" placeholder="例如: deepseek-chat, gpt-4" />
            <small class="form-hint" v-if="providerModels.length">{{ providerModels.join(', ') }}</small>
          </div>
          <div class="form-group">
            <label>API Key</label>
            <input v-model="config.api_key" type="password" class="form-input" placeholder="API Key（留空则从环境变量读取）" />
            <small class="form-hint" v-if="envKeyName">环境变量: {{ envKeyName }}</small>
          </div>
          <div class="form-group">
            <label>API Base URL</label>
            <input v-model="config.api_base" type="text" class="form-input" placeholder="API地址（可选，留空使用默认地址）" />
            <small class="form-hint" v-if="defaultBaseUrl">默认地址: {{ defaultBaseUrl }}</small>
          </div>
          <!-- DeepSeek 增强参数 -->
          <template v-if="config.provider === 'deepseek'">
            <div class="form-group">
              <label>思考强度 (reasoning_effort)</label>
              <select v-model="config.reasoning_effort" class="form-input">
                <option value="">不使用深度思考</option>
                <option value="low">低 (low)</option>
                <option value="medium">中 (medium)</option>
                <option value="high">高 (high)</option>
              </select>
              <small class="form-hint">控制模型思考深度，越高分析越详细但耗时更长</small>
            </div>
            <div class="form-group">
              <label>启用深度思考模式</label>
              <select v-model="config.enable_thinking" class="form-input">
                <option :value="false">关闭</option>
                <option :value="true">启用 (thinking enabled)</option>
              </select>
              <small class="form-hint">启用后模型会进行深度思考再给出回答（仅 DeepSeek V4 等支持）</small>
            </div>
          </template>
        </div>
        <div class="form-actions">
          <button class="btn btn-secondary" @click="testConnection">测试连接</button>
          <button class="btn btn-primary" @click="saveConfig">保存配置</button>
        </div>
      </div>
    </div>

    <!-- 服务健康状态 -->
    <div class="card">
      <div class="card-header">
        <h3>服务状态</h3>
      </div>
      <div class="card-body">
        <div class="health-grid">
          <div class="health-item">
            <span class="health-label">服务版本</span>
            <span class="health-value">{{ healthStatus.version || '--' }}</span>
          </div>
          <div class="health-item">
            <span class="health-label">运行时间</span>
            <span class="health-value">{{ healthStatus.uptime_human || '--' }}</span>
          </div>
          <div class="health-item">
            <span class="health-label">数据库</span>
            <span :class="healthStatus.services?.database === 'ok' ? 'health-ok' : 'health-error'">
              {{ healthStatus.services?.database || '--' }}
            </span>
          </div>
          <div class="health-item">
            <span class="health-label">调度器</span>
            <span :class="healthStatus.services?.scheduler === 'running' ? 'health-ok' : 'health-warning'">
              {{ healthStatus.services?.scheduler || '--' }}
            </span>
          </div>
          <div class="health-item">
            <span class="health-label">LLM</span>
            <span :class="healthStatus.services?.llm === 'configured' ? 'health-ok' : 'health-warning'">
              {{ healthStatus.services?.llm || '--' }}
            </span>
          </div>
          <div class="health-item">
            <span class="health-label">数据源</span>
            <span :class="healthStatus.services?.datasource === 'configured' ? 'health-ok' : 'health-warning'">
              {{ healthStatus.services?.datasource || '--' }}
            </span>
          </div>
        </div>
        <div class="form-actions">
          <button class="btn btn-secondary" @click="loadHealthStatus">刷新状态</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useToast } from '@/composables/useNotification'

const toast = useToast()

const config = ref({
  provider: 'openai',
  api_format: '',
  model: '',
  api_key: '',
  api_base: '',
  reasoning_effort: '',
  enable_thinking: false
})

// 提供商元数据
const providerMeta = {
  openai: {
    description: 'OpenAI 官方 API，支持 GPT 系列模型',
    defaultBase: 'https://api.openai.com/v1',
    models: ['gpt-5', 'gpt-4o', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
    envKey: 'OPENAI_API_KEY'
  },
  anthropic: {
    description: 'Anthropic Claude 系列，擅长长文本分析',
    defaultBase: 'https://api.anthropic.com',
    models: ['claude-sonnet-5-20250915', 'claude-opus-4-8-20250805', 'claude-haiku-4-5-20251001'],
    envKey: 'ANTHROPIC_API_KEY'
  },
  deepseek: {
    description: 'DeepSeek 深度求索，支持深度思考模式，性价比高',
    defaultBase: 'https://api.deepseek.com',
    models: ['deepseek-chat', 'deepseek-v4-pro', 'deepseek-reasoner'],
    envKey: 'DEEPSEEK_API_KEY'
  },
  bailian: {
    description: '阿里云百炼平台，支持多种国产模型',
    defaultBase: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    models: ['qwen-turbo', 'qwen3.5-plus', 'qwen3.5-max'],
    envKey: 'BAILIAN_API_KEY'
  },
  qwen: {
    description: '通义千问系列模型',
    defaultBase: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    models: ['qwen3.5-turbo', 'qwen3.5-plus', 'qwen-max'],
    envKey: 'QWEN_API_KEY'
  },
  glm: {
    description: '智谱AI GLM系列模型',
    defaultBase: 'https://open.bigmodel.cn/api/paas/v4',
    models: ['glm-5', 'glm-5-flash', 'glm-4-plus'],
    envKey: 'GLM_API_KEY'
  },
  minimax: {
    description: 'MiniMax 大模型',
    defaultBase: 'https://api.minimax.chat/v1',
    models: ['abab6.5-chat', 'abab5.5-chat'],
    envKey: 'MINIMAX_API_KEY'
  },
  'bailian-anthropic': {
    description: '阿里云百炼 Anthropic 兼容接口',
    defaultBase: 'https://dashscope.aliyuncs.com/apps/anthropic',
    models: ['qwen3.5-turbo', 'qwen3.5-plus'],
    envKey: 'BAILIAN_API_KEY'
  },
  custom: {
    description: '自定义 OpenAI 兼容接口',
    defaultBase: '',
    models: [],
    envKey: ''
  }
}

const providerDescription = computed(() => {
  return providerMeta[config.value.provider]?.description || ''
})

const providerModels = computed(() => {
  return providerMeta[config.value.provider]?.models || []
})

const defaultBaseUrl = computed(() => {
  return providerMeta[config.value.provider]?.defaultBase || ''
})

const envKeyName = computed(() => {
  return providerMeta[config.value.provider]?.envKey || ''
})

function onProviderChange() {
  // 切换厂商时自动填入默认 API 地址
  const meta = providerMeta[config.value.provider]
  if (meta && meta.defaultBase && !config.value.api_base) {
    config.value.api_base = meta.defaultBase
  }
  // 根据厂商自动判断 API 格式
  if (config.value.provider === 'anthropic' || config.value.provider === 'bailian-anthropic') {
    // Anthropic 默认为 anthropic 格式
  } else {
    // 其他默认为 openai 格式，让用户可以通过 api_format 切换
  }
}

const schedulerStatus = ref({
  running: false,
  sync_hours: [9, 12, 14, 16],
  jobs_count: 0,
  is_trading_day: false
})

const templates = ref([])
const selectedTemplate = ref(null)
const syncing = ref(false)
const syncResult = ref(null)
const healthStatus = ref({})

async function loadConfig() {
  try {
    const res = await api.get('/configs/llm')
    if (res.data.success && res.data.data) {
      Object.assign(config.value, res.data.data)
    }
  } catch (e) {
    console.error('加载配置失败:', e)
  }
}

async function saveConfig() {
  try {
    const res = await api.put('/configs/llm', config.value)
    if (res.data.success) {
      toast.success('配置保存成功')
    } else {
      toast.error('保存失败: ' + res.data.message)
    }
  } catch (e) {
    toast.error('保存失败: ' + e.message)
  }
}

async function testConnection() {
  try {
    const res = await api.post('/configs/test-llm', config.value)
    if (res.data.success) {
      toast.success('连接成功')
    } else {
      toast.error('连接失败: ' + res.data.message)
    }
  } catch (e) {
    toast.error('连接失败: ' + e.message)
  }
}

async function loadSchedulerStatus() {
  try {
    const res = await api.get('/scheduler/status')
    if (res.data.success) {
      schedulerStatus.value = res.data.data
    }
  } catch (e) {
    console.error('获取调度器状态失败:', e)
  }
}

async function triggerSync() {
  syncing.value = true
  syncResult.value = null
  try {
    const res = await api.post('/scheduler/sync')
    if (res.data.success) {
      syncResult.value = res.data
    } else {
      syncResult.value = { message: '同步失败: ' + res.data.message }
    }
  } catch (e) {
    syncResult.value = { message: '同步失败: ' + e.message }
  }
  syncing.value = false
}

async function loadTemplates() {
  try {
    const res = await api.get('/configs/strategy/templates')
    if (res.data.success) {
      templates.value = res.data.data.templates
    }
  } catch (e) {
    console.error('获取策略模板失败:', e)
  }
}

function selectTemplate(id) {
  selectedTemplate.value = id
}

async function applyTemplate() {
  if (!selectedTemplate.value) return

  try {
    const res = await api.post(`/configs/strategy/apply-template/${selectedTemplate.value}`)
    if (res.data.success) {
      toast.success(res.data.message || '模板应用成功')
    } else {
      toast.error('应用失败: ' + res.data.message)
    }
  } catch (e) {
    toast.error('应用失败: ' + e.message)
  }
}

async function loadHealthStatus() {
  try {
    const res = await api.get('/health')
    if (res.data) {
      healthStatus.value = res.data
    }
  } catch (e) {
    console.error('获取健康状态失败:', e)
  }
}

onMounted(() => {
  loadConfig()
  loadSchedulerStatus()
  loadTemplates()
  loadHealthStatus()
})
</script>

<style lang="scss" scoped>
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.form-group {
  label {
    display: block;
    margin-bottom: 6px;
    font-weight: 500;
  }
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
}

.form-hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.4;
}

.form-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}

.scheduler-status {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.status-item {
  display: flex;
  gap: 8px;
}

.status-label {
  color: var(--text-secondary);
}

.status-running {
  color: var(--color-success);
  font-weight: 500;
}

.status-stopped {
  color: var(--color-danger);
  font-weight: 500;
}

.scheduler-actions {
  display: flex;
  gap: 12px;
}

.sync-result {
  margin-top: 12px;
  padding: 12px;
  background: var(--bg-input);
  border-radius: 6px;
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.template-card {
  padding: 16px;
  border: 2px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: var(--color-primary);
  }

  &.active {
    border-color: var(--color-primary);
    background: var(--color-primary-light);
  }

  .template-name {
    font-weight: 500;
    margin-bottom: 8px;
  }

  .template-desc {
    font-size: 14px;
    color: var(--text-secondary);
    margin-bottom: 12px;
  }

  .template-preview {
    font-size: 13px;
    color: var(--text-muted);
  }
}

.health-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.health-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.health-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.health-value {
  font-weight: 500;
}

.health-ok {
  color: var(--color-success);
}

.health-warning {
  color: var(--color-warning);
}

.health-error {
  color: var(--color-danger);
}
</style>