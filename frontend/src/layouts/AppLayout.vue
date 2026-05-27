<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const isAdmin = computed(() => (auth.userInfo?.vipLevel || 0) >= 2)

const menuList = [
  { to: '/explore', label: '发现', desc: '发现故事', icon: '◇', color: 'misty' },
  { to: '/create', label: '创作', desc: 'AI 写作', icon: '◇', color: 'crimson' },
  { to: '/usercenter', label: '我的', desc: '个人中心', icon: '◇', color: 'green' },
  { to: '/favorites', label: '我的收藏', desc: '收藏作品', icon: '♥', color: 'crimson' },
]

const adminMenuList = [
  { to: '/admin/work', label: '作品卡管理', icon: '▣', color: 'gold' },
  { to: '/admin/character', label: '角色卡管理', icon: '▣', color: 'gold' },
  { to: '/admin/tag', label: '标签管理', icon: '▣', color: 'gold' },
  { to: '/admin/user', label: '用户管理', icon: '▣', color: 'gold' },
]

const errorMessage = ref('')
const sidebarCollapsed = ref(false)

const isActive = (path) => {
  return route.path.startsWith(path)
}

const handleError = (event) => {
  errorMessage.value = event.detail
  window.setTimeout(() => {
    errorMessage.value = ''
  }, 3000)
}

const handleLogout = () => {
  auth.logout()
  router.push('/explore')
}

const handleAuthExpired = () => {
  auth.setUserInfo(null)
  router.push('/login')
}

onMounted(() => {
  window.addEventListener('app:error', handleError)
  window.addEventListener('app:auth-expired', handleAuthExpired)
})

onBeforeUnmount(() => {
  window.removeEventListener('app:error', handleError)
  window.removeEventListener('app:auth-expired', handleAuthExpired)
})
</script>

<template>
  <div class="layout-shell">
    <header class="top-nav-bar">
      <div class="top-nav-inner">
        <RouterLink to="/explore" class="top-brand">
          <span class="brand-icon">◇</span>
          <span class="brand-text gradient-text-misty">知弄</span>
        </RouterLink>

        <nav class="top-nav-links">
          <RouterLink to="/explore" class="top-nav-link" :class="{ active: route.path.startsWith('/explore') }">
            {{ t('nav.explore') }}
          </RouterLink>
          <RouterLink to="/create" class="top-nav-link" :class="{ active: route.path === '/create' }">
            创作
          </RouterLink>
        </nav>

        <div class="top-nav-user">
          <template v-if="auth.isLoggedIn()">
            <span class="user-points">积分:{{ auth.userInfo?.credits ?? 0 }}</span>
            <div class="user-avatar-mini">{{ auth.userInfo?.nickname?.charAt(0) || 'U' }}</div>
            <RouterLink to="/usercenter" class="user-name-link">{{ auth.userInfo?.nickname || '用户' }}</RouterLink>
            <button class="nav-logout-btn" @click="handleLogout">{{ t('nav.logout') }}</button>
          </template>
          <template v-else>
            <RouterLink to="/login" class="top-auth-btn top-auth-btn--primary">{{ t('nav.login') }}</RouterLink>
            <RouterLink to="/register" class="top-auth-btn">{{ t('nav.register') }}</RouterLink>
          </template>
        </div>
      </div>
    </header>

    <div class="layout-body">
      <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-inner">
        <RouterLink to="/create" class="brand">
          <span class="brand-icon">◇</span>
          <span class="brand-text gradient-text-misty">知弄</span>
        </RouterLink>

        <nav class="menu">
          <RouterLink
            v-for="item in menuList"
            :key="item.to"
            :to="item.to"
            class="menu-item"
            :class="[{ active: isActive(item.to) }, `menu-item--${item.color}`]"
          >
            <span class="menu-icon">{{ item.icon }}</span>
            <span class="menu-label">{{ item.label }}</span>
            <span class="menu-desc">{{ item.desc }}</span>
          </RouterLink>
        </nav>

        <template v-if="isAdmin">
          <div class="admin-divider"><span>管理后台</span></div>
          <nav class="menu admin-menu">
            <RouterLink
              v-for="item in adminMenuList"
              :key="item.to"
              :to="item.to"
              class="menu-item"
              :class="[{ active: isActive(item.to) }, `menu-item--${item.color}`]"
            >
              <span class="menu-icon">{{ item.icon }}</span>
              <span class="menu-label">{{ item.label }}</span>
            </RouterLink>
          </nav>
        </template>

        <div class="promo-section">
          <div class="promo-card">
            <span class="promo-title">新人周卡 · 免费体验</span>
          </div>
        </div>

        <div class="auth-panel">
          <template v-if="auth.isLoggedIn()">
            <div class="user-info">
              <div class="user-avatar">{{ auth.userInfo?.nickname?.charAt(0) || 'U' }}</div>
              <div class="user-detail">
                <span class="user-name">{{ auth.userInfo?.nickname || '用户' }}</span>
                <span class="user-role">创作者</span>
              </div>
            </div>
            <a class="logout-btn" @click="handleLogout">退出</a>
          </template>
          <template v-else>
            <RouterLink to="/login" class="auth-link auth-link--primary">登录</RouterLink>
            <RouterLink to="/register" class="auth-link">注册</RouterLink>
          </template>
        </div>

        <button class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          {{ sidebarCollapsed ? '▶' : '◀' }}
        </button>
      </div>
    </aside>

    <div class="layout-main">
      <main class="main-content">
        <slot />
      </main>
    </div>
    </div>

    <Transition name="toast">
      <div v-if="errorMessage" class="toast">{{ errorMessage }}</div>
    </Transition>
  </div>
</template>

<style scoped>
.layout-shell {
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
}

/* --- Top Navigation Bar --- */
.top-nav-bar {
  position: sticky;
  top: 0;
  z-index: var(--z-header);
  background: var(--bg-glass);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border-secondary);
  height: 56px;
}

.top-nav-inner {
  max-width: var(--max-content-width);
  margin: 0 auto;
  padding: 0 var(--space-xl);
  height: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-lg);
}

.top-brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  text-decoration: none;
  flex-shrink: 0;
}

.top-brand .brand-icon {
  font-size: 20px;
  color: var(--color-misty-blue);
  flex-shrink: 0;
}

.top-brand .brand-text {
  font-size: var(--text-xl);
  font-weight: 700;
  letter-spacing: 0.04em;
}

.top-nav-links {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 0 auto;
}

.top-nav-link {
  padding: 8px 18px;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all var(--transition-fast);
  position: relative;
}

.top-nav-link:hover {
  color: var(--text-primary);
  background: var(--bg-card);
}

.top-nav-link.active {
  color: var(--text-primary);
  background: rgba(123, 156, 191, 0.1);
  border-bottom: 2px solid var(--color-misty-blue-soft);
}

.top-nav-user {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-shrink: 0;
}

.user-points {
  font-size: var(--text-xs);
  color: var(--color-candy-pink-soft);
  background: rgba(238, 162, 180, 0.1);
  padding: 4px 10px;
  border-radius: var(--radius-full);
}

.user-avatar-mini {
  width: 30px;
  height: 30px;
  border-radius: var(--radius-full);
  background: linear-gradient(135deg, var(--color-misty-blue-deep), var(--color-misty-blue));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: var(--text-xs);
  color: #fff;
  flex-shrink: 0;
}

.user-name-link {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  text-decoration: none;
  transition: color var(--transition-fast);
}
.user-name-link:hover { color: var(--text-primary); }

.nav-logout-btn {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 4px 8px;
  transition: color var(--transition-fast);
}
.nav-logout-btn:hover { color: var(--color-crimson-soft); }

.top-auth-btn {
  padding: 6px 16px;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all var(--transition-fast);
}
.top-auth-btn:hover { background: var(--bg-card); color: var(--text-primary); }
.top-auth-btn--primary {
  background: linear-gradient(135deg, var(--color-misty-blue-deep), var(--color-dark-green-deep));
  color: var(--text-primary);
}
.top-auth-btn--primary:hover { opacity: 0.9; box-shadow: var(--shadow-glow-misty); }

/* --- Layout Body --- */
.layout-body {
  display: flex;
  min-height: calc(100vh - 56px);
}

/* --- Sidebar --- */
.sidebar {
  width: var(--sidebar-width);
  min-height: calc(100vh - 56px);
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-secondary);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  flex-shrink: 0;
  transition: width var(--transition-base);
  z-index: var(--z-sidebar);
}

.sidebar.collapsed {
  width: 64px;
}

.sidebar-inner {
  display: flex;
  flex-direction: column;
  padding: var(--space-lg) var(--space-md);
  height: 100%;
  gap: var(--space-lg);
}

.sidebar.collapsed .sidebar-inner {
  padding: var(--space-lg) var(--space-sm);
  align-items: center;
}

/* --- Brand --- */
.brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  text-decoration: none;
  padding: var(--space-xs) 0;
}

.brand-icon {
  font-size: 22px;
  color: var(--color-misty-blue);
  flex-shrink: 0;
}

.brand-text {
  font-size: var(--text-2xl);
  font-weight: 700;
  letter-spacing: 0.04em;
}

.sidebar.collapsed .brand-text { display: none; }

/* --- Menu --- */
.menu {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 12px 14px;
  border-radius: var(--radius-md);
  text-decoration: none;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
  position: relative;
  overflow: hidden;
}

.menu-item::before {
  content: '';
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity var(--transition-fast);
  border-radius: inherit;
}

.menu-item--misty::before {
  background: linear-gradient(135deg, rgba(123, 156, 191, 0.12), transparent);
}

.menu-item--crimson::before {
  background: linear-gradient(135deg, rgba(200, 85, 84, 0.12), transparent);
}

.menu-item--green::before {
  background: linear-gradient(135deg, rgba(61, 107, 86, 0.12), transparent);
}

.menu-item--gold::before {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.12), transparent);
}

.menu-item:hover {
  color: var(--text-primary);
}

.menu-item:hover::before {
  opacity: 1;
}

.menu-item.active {
  color: var(--text-primary);
  background: var(--bg-card);
}

.menu-item.active::before {
  opacity: 1;
}

.menu-item--misty.active {
  border-left: 2px solid var(--color-misty-blue);
}

.menu-item--crimson.active {
  border-left: 2px solid var(--color-crimson);
}

.menu-item--green.active {
  border-left: 2px solid var(--color-dark-green);
}

.menu-item--gold.active {
  border-left: 2px solid #ffc107;
}

.menu-icon {
  font-size: 14px;
  flex-shrink: 0;
  width: 20px;
  text-align: center;
}

.menu-label {
  font-size: var(--text-base);
  font-weight: 500;
}

.menu-desc {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-left: auto;
}

.sidebar.collapsed .menu-label,
.sidebar.collapsed .menu-desc { display: none; }

/* --- Admin Divider --- */
.admin-divider {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 4px 14px 0;
}

.admin-divider span {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.admin-divider::before,
.admin-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border-secondary);
}

.sidebar.collapsed .admin-divider span,
.sidebar.collapsed .admin-divider::before,
.sidebar.collapsed .admin-divider::after {
  display: none;
}

/* --- Promo --- */
.promo-section {
  margin: var(--space-sm) 0;
}

.promo-card {
  background: linear-gradient(135deg, rgba(238, 162, 180, 0.1), rgba(200, 85, 84, 0.08));
  border: 1px solid rgba(238, 162, 180, 0.15);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  transition: all var(--transition-fast);
}

.promo-card:hover {
  border-color: rgba(238, 162, 180, 0.3);
}

.promo-title {
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-candy-pink-soft);
}

.sidebar.collapsed .promo-card {
  padding: 6px;
  align-items: center;
}

.sidebar.collapsed .promo-title { display: none; }

/* --- Auth --- */
.auth-panel {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-xs);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: linear-gradient(135deg, var(--color-misty-blue-deep), var(--color-misty-blue));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: var(--text-sm);
  color: #fff;
  flex-shrink: 0;
}

.user-detail {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 600;
  font-size: var(--text-sm);
}

.user-role {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.auth-link {
  display: block;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  text-align: center;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
  text-decoration: none;
}

.auth-link:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.auth-link--primary {
  background: linear-gradient(135deg, var(--color-misty-blue-deep), var(--color-dark-green-deep));
  color: var(--text-primary);
  font-weight: 600;
}

.auth-link--primary:hover {
  opacity: 0.9;
  box-shadow: var(--shadow-glow-misty);
}

.logout-btn {
  display: block;
  padding: 6px 10px;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: color var(--transition-fast);
}

.logout-btn:hover {
  color: var(--color-crimson-soft);
}

.sidebar.collapsed .user-detail,
.sidebar.collapsed .auth-link,
.sidebar.collapsed .logout-btn { display: none; }

.sidebar.collapsed .user-avatar {
  margin: 0 auto;
}

/* --- Collapse --- */
.collapse-btn {
  position: absolute;
  bottom: var(--space-lg);
  right: -10px;
  width: 20px;
  height: 20px;
  border-radius: var(--radius-full);
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  color: var(--text-tertiary);
  font-size: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.collapse-btn:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

/* --- Main --- */
.layout-main {
  flex: 1;
  min-width: 0;
}

.main-content {
  width: 100%;
  max-width: var(--max-content-width);
  margin: 0 auto;
  padding: var(--space-lg) var(--space-xl) var(--space-3xl);
}

/* --- Toast --- */
.toast {
  position: fixed;
  right: var(--space-xl);
  bottom: var(--space-xl);
  background: var(--bg-elevated);
  color: var(--text-primary);
  padding: 12px 20px;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border-primary);
  z-index: var(--z-toast);
  backdrop-filter: blur(12px);
}

.toast-enter-active,
.toast-leave-active {
  transition: all var(--transition-base);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(12px);
}

/* --- Responsive --- */
@media (max-width: 768px) {
  .sidebar {
    width: 64px;
  }

  .sidebar .brand-text,
  .sidebar .menu-label,
  .sidebar .menu-desc,
  .sidebar .user-detail,
  .sidebar .auth-link,
  .sidebar .logout-btn,
  .sidebar .promo-title {
    display: none;
  }

  .sidebar .sidebar-inner {
    padding: var(--space-lg) var(--space-sm);
    align-items: center;
  }

  .sidebar .menu-item {
    justify-content: center;
    padding: 12px 8px;
  }

  .sidebar .promo-card {
    padding: 10px 6px;
    align-items: center;
  }

  .sidebar .collapse-btn {
    display: none;
  }

  .main-content {
    padding: var(--space-md) var(--space-md) var(--space-2xl);
  }
}
</style>
