<template>
  <div class="app-container">
    <!-- 移动端顶部栏 -->
    <header class="mobile-header">
      <button class="menu-toggle" @click="toggleSidebar">
        <span></span>
        <span></span>
        <span></span>
      </button>
      <h1>理财系统</h1>
      <div class="mobile-user">
        <span>{{ authStore.user?.username || '--' }}</span>
      </div>
    </header>

    <!-- 侧边栏遮罩 -->
    <div class="sidebar-overlay" :class="{ show: sidebarVisible }" @click="toggleSidebar"></div>

    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ show: sidebarVisible }">
      <div class="logo">
        <h2>理财系统</h2>
      </div>
      <nav class="nav-menu">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: $route.path === item.path }"
          @click="closeSidebar"
        >
          <span class="icon">{{ item.icon }}</span>
          <span class="text">{{ item.name }}</span>
        </router-link>
      </nav>
      <div class="sidebar-bottom">
        <div class="account-selector">
          <label>当前账户</label>
          <select v-model="currentAccountId" class="form-input" @change="switchAccount">
            <option value="">全部账户</option>
            <option v-for="acc in accounts" :key="acc.id" :value="acc.id">
              {{ acc.name }}
            </option>
          </select>
        </div>
        <div class="user-info-panel">
          <div>
            <div class="username">{{ authStore.user?.username || '加载中...' }}</div>
            <div class="role">用户</div>
          </div>
          <button class="btn btn-sm btn-secondary" @click="logout">退出</button>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAccountStore } from '@/stores/accounts'

const router = useRouter()
const authStore = useAuthStore()
const accountStore = useAccountStore()

const sidebarVisible = ref(false)
const currentAccountId = ref('')

const navItems = [
  { path: '/', name: '首页概览', icon: '📊' },
  { path: '/positions', name: '持仓管理', icon: '💼' },
  { path: '/trades', name: '交易记录', icon: '📝' },
  { path: '/analysis', name: '收益分析', icon: '📈' },
  { path: '/valuation', name: '估值判断', icon: '💰' },
  { path: '/backtest', name: '策略回测', icon: '🔬' },
  { path: '/ai', name: 'AI 分析', icon: '🤖' },
  { path: '/settings', name: '系统设置', icon: '⚙️' }
]

const accounts = computed(() => accountStore.accounts)

function toggleSidebar() {
  sidebarVisible.value = !sidebarVisible.value
}

function closeSidebar() {
  sidebarVisible.value = false
}

function switchAccount() {
  accountStore.setCurrentAccount(currentAccountId.value)
}

function logout() {
  authStore.logout()
  router.push('/login')
}

onMounted(async () => {
  await authStore.checkAuth()
  await accountStore.fetchAccounts()
})
</script>

<style lang="scss">
@import '@/assets/main.scss';
</style>