<template>
  <!-- 全局通知组件 -->
  <Toast />
  <ConfirmDialog />

  <!-- 登录/注册页面 - 不显示侧边栏 -->
  <div v-if="isLoginPage" class="auth-page">
    <router-view />
  </div>

  <!-- 主应用 - 已登录后显示 -->
  <div v-else class="app-container">
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
        <template v-for="item in navItems" :key="item.path || item.name">
          <!-- 直接路由链接（叶子节点） -->
          <router-link
            v-if="item.type === 'link'"
            :to="item.path"
            class="nav-item"
            :class="{ active: $route.path === item.path }"
            @click="closeSidebar"
          >
            <span class="icon" v-html="item.icon"></span>
            <span class="text">{{ item.name }}</span>
          </router-link>

          <!-- 可折叠分组 -->
          <div v-else-if="item.type === 'group'" class="nav-group">
            <div
              class="nav-group-header"
              @click="toggleGroup(item.name)"
            >
              <span class="icon" v-html="item.icon"></span>
              <span class="text">{{ item.name }}</span>
              <span
                class="group-arrow"
                :class="{ expanded: expandedGroups[item.name] }"
              >&#9662;</span>
            </div>
            <div
              class="nav-group-children"
              :class="{ expanded: expandedGroups[item.name] }"
            >
              <router-link
                v-for="child in item.children"
                :key="child.path"
                :to="child.path"
                class="nav-item nav-child"
                :class="{ active: $route.path === child.path }"
                @click="closeSidebar"
              >
                <span class="icon" v-html="child.icon"></span>
                <span class="text">{{ child.name }}</span>
              </router-link>
            </div>
          </div>
        </template>
      </nav>
      <!-- 侧边栏底部用户区 -->
      <div class="sidebar-bottom">
        <div class="user-info-bar">
          <div class="user-avatar">{{ userInitial }}</div>
          <span class="username">{{ authStore.user?.username || '加载中...' }}</span>
          <button class="theme-toggle-btn" @click="themeStore.toggleTheme()" :title="themeStore.theme === 'dark' ? '切换亮色' : '切换暗色'">
            {{ themeStore.theme === 'dark' ? '☀️' : '🌙' }}
          </button>
        </div>
        <button class="logout-btn" @click="handleLogout">退出登录</button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 顶部搜索栏 -->
      <div class="top-bar">
        <div class="global-search">
          <span class="search-icon" v-html="icons.search"></span>
          <input
            v-model="searchQuery"
            type="text"
            class="search-input"
            placeholder="搜索持仓、交易、标的..."
            @input="onSearchInput"
          />
          <span v-if="searching" class="search-spinner"></span>
        </div>
        <div class="top-bar-right">
          <span class="connection-dot" :class="{ connected: true }" title="服务已连接"></span>
        </div>
      </div>
      <!-- 搜索结果下拉 -->
      <Transition name="dropdown-fade">
        <div v-if="searchResults.length > 0 || searchNoResult" class="search-results-panel" @click.stop>
          <div v-if="searchNoResult" class="search-no-result">未找到匹配结果</div>
          <div v-else class="search-result-list">
            <div
              v-for="item in searchResults"
              :key="item.id"
              class="search-result-item"
              @click="goToSearchResult(item)"
            >
              <span class="result-icon">{{ item.icon }}</span>
              <div class="result-info">
                <span class="result-title">{{ item.title }}</span>
                <span class="result-sub">{{ item.sub }}</span>
              </div>
              <span class="result-type">{{ item.type }}</span>
            </div>
          </div>
        </div>
      </Transition>
      <router-view v-slot="{ Component }">
        <Transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </Transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useConfirm } from '@/composables/useNotification'
import api from '@/api'
import Toast from '@/components/Toast.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const confirm = useConfirm()

const sidebarVisible = ref(false)

// 全局搜索
const searchQuery = ref('')
const searching = ref(false)
const searchResults = ref([])
const searchNoResult = ref(false)
let searchTimer = null

function onSearchInput() {
  clearTimeout(searchTimer)
  const q = searchQuery.value.trim()
  if (!q) {
    searchResults.value = []
    searchNoResult.value = false
    return
  }
  searching.value = true
  searchTimer = setTimeout(async () => {
    try {
      const res = await api.get('/admin/search', { params: { q } })
      if (res.data?.success) {
        searchResults.value = res.data.data || []
        searchNoResult.value = searchResults.value.length === 0
      }
    } catch {
      searchResults.value = []
      searchNoResult.value = true
    } finally {
      searching.value = false
    }
  }, 500)
}

function goToSearchResult(item) {
  searchQuery.value = ''
  searchResults.value = []
  if (item.route) {
    router.push(item.route)
  }
}

// 判断是否是登录/注册页面
const isLoginPage = computed(() => {
  return route.path === '/login' || route.path === '/register'
})

// SVG 图标 - 专业线条风格
const icons = {
  home: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
  chart: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
  briefcase: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
  list: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>',
  trending: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
  dollar: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
  beaker: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 3h15M6 3v16a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V3M6 14h12"/></svg>',
  cpu: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>',
  gear: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>',
  shield: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  search: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'
}

const navItems = computed(() => {
  const items = [
    { type: 'link', path: '/', name: '首页概览', icon: icons.home },
    {
      type: 'group',
      name: '投资分析',
      icon: icons.chart,
      children: [
        { path: '/positions', name: '持仓管理', icon: icons.briefcase },
        { path: '/trades', name: '交易记录', icon: icons.list },
        { path: '/analysis', name: '收益分析', icon: icons.trending },
        { path: '/valuation', name: '估值判断', icon: icons.dollar }
      ]
    },
    {
      type: 'group',
      name: '量化工具',
      icon: icons.beaker,
      children: [
        { path: '/backtest', name: '策略回测', icon: icons.beaker },
        { path: '/ai', name: 'AI 分析', icon: icons.cpu }
      ]
    },
    { type: 'link', path: '/settings', name: '系统设置', icon: icons.gear }
  ]

  if (authStore.user?.is_admin) {
    items.push({ type: 'link', path: '/admin', name: '管理后台', icon: icons.shield })
  }

  return items
})

// 分组折叠状态（默认展开"投资分析"）
const expandedGroups = reactive({
  '投资分析': true,
  '量化工具': false
})

function toggleGroup(name) {
  expandedGroups[name] = !expandedGroups[name]
}

// 用户名首字（用于头像）
const userInitial = computed(() => {
  const username = authStore.user?.username
  return username ? username.charAt(0).toUpperCase() : '?'
})

function toggleSidebar() {
  sidebarVisible.value = !sidebarVisible.value
}

function closeSidebar() {
  sidebarVisible.value = false
}

async function handleLogout() {
  const confirmed = await confirm.danger('确定要退出登录吗？')
  if (confirmed) {
    authStore.logout()
    router.push('/login')
  }
}
</script>

<style lang="scss">
@import '@/assets/main.scss';

.auth-page {
  min-height: 100vh;
}

// ============================================
// 侧边栏底部 — 用户信息和主题切换
// ============================================
.sidebar-bottom {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.user-info-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: var(--radius-md);

  .username {
    flex: 1;
    font-size: var(--text-sm);
    font-weight: var(--weight-medium);
    color: var(--text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.theme-toggle-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-full);
  background: transparent;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background var(--transition-fast);
  flex-shrink: 0;

  &:hover {
    background: var(--bg-hover);
  }
}

.logout-btn {
  width: 100%;
  padding: 8px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-fast);

  &:hover {
    color: var(--color-danger);
    border-color: var(--color-danger);
  }
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: var(--weight-semibold);
  flex-shrink: 0;
}

// ============================================
// 页面过渡动画
// ============================================
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

// ============================================
// 顶部搜索栏
// ============================================
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-6);
  gap: var(--spacing-4);
}

.global-search {
  position: relative;
  flex: 1;
  max-width: 480px;

  .search-icon {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    opacity: 0.4;
    display: flex;

    :deep(svg) {
      width: 16px;
      height: 16px;
    }
  }

  .search-input {
    width: 100%;
    padding: 9px 36px 9px 36px;
    background: var(--bg-input);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    font-size: var(--text-sm);
    color: var(--text-primary);
    outline: none;
    transition: border-color var(--transition-fast);

    &::placeholder {
      color: var(--text-muted);
    }

    &:focus {
      border-color: var(--color-primary);
      box-shadow: var(--shadow-glow);
    }
  }

  .search-spinner {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    width: 14px;
    height: 14px;
    border: 2px solid var(--border-color);
    border-top-color: var(--color-primary);
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);

  .connection-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-success);

    &.connected {
      background: var(--color-success);
    }
  }
}

// 搜索结果面板
.search-results-panel {
  position: absolute;
  top: 56px;
  left: 0;
  right: 0;
  max-width: 480px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  z-index: 150;
  max-height: 320px;
  overflow-y: auto;
  margin-left: var(--spacing-8);
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  transition: background var(--transition-fast);

  &:hover {
    background: var(--bg-hover);
  }

  .result-icon {
    font-size: 16px;
  }

  .result-info {
    flex: 1;
    overflow: hidden;

    .result-title {
      display: block;
      font-size: var(--text-sm);
      color: var(--text-primary);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .result-sub {
      display: block;
      font-size: var(--text-caption);
      color: var(--text-muted);
    }
  }

  .result-type {
    font-size: var(--text-caption);
    color: var(--text-muted);
    background: var(--bg-input);
    padding: 2px 6px;
    border-radius: var(--radius-sm);
  }
}

.search-no-result {
  padding: 24px;
  text-align: center;
  color: var(--text-muted);
  font-size: var(--text-sm);
}

// ============================================
// 导航分组 - 可折叠二级菜单
// ============================================
.nav-group {
  margin-bottom: 2px;
}

.nav-group-header {
  display: flex;
  align-items: center;
  padding: 12px 14px;
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-base);
  font-weight: var(--weight-semibold);
  white-space: nowrap;
  border-left: 3px solid transparent;
  user-select: none;

  .icon {
    margin-right: 14px;
    font-size: 20px;
    width: 24px;
    text-align: center;
  }

  .text {
    font-size: var(--text-base);
    flex: 1;
  }

  .group-arrow {
    font-size: 12px;
    color: var(--text-muted);
    transition: transform var(--transition-fast);
    flex-shrink: 0;
    margin-left: auto;

    &.expanded {
      transform: rotate(180deg);
    }
  }

  &:hover {
    background: var(--bg-hover);
  }
}

.nav-group-children {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease;

  &.expanded {
    max-height: 500px;
  }

  .nav-child {
    padding-left: 26px;

    .text {
      font-size: calc(var(--text-base) - 1px);
    }

    .icon {
      font-size: 17px;
    }
  }
}
</style>
