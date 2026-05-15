<script setup>
import { RouterLink } from 'vue-router'

const menuItems = [
  { path: '/admin/category', label: '分类管理' },
  { path: '/admin/tool', label: '工具管理' },
]
</script>

<template>
  <div class="admin-layout">
    <header class="admin-header">
      <div class="header-left">
        <RouterLink class="logo" to="/create">
          <span class="logo-icon">◇</span>
          <span>知弄 · 管理后台</span>
        </RouterLink>
      </div>
      <RouterLink class="back-link" to="/create">← 返回前台</RouterLink>
    </header>
    <div class="admin-body">
      <aside class="admin-sidebar">
        <RouterLink
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="sidebar-item"
          active-class="active"
        >{{ item.label }}</RouterLink>
      </aside>
      <main class="admin-main">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin-layout {
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.admin-header {
  padding: 14px var(--space-xl);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-secondary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: var(--z-header);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--text-primary);
  text-decoration: none;
  font-size: var(--text-base);
  font-weight: 600;
}

.logo-icon {
  color: var(--color-misty-blue);
  font-size: 18px;
}

.back-link {
  color: var(--text-tertiary);
  text-decoration: none;
  font-size: var(--text-sm);
  transition: color var(--transition-fast);
}

.back-link:hover {
  color: var(--text-secondary);
}

.admin-body {
  display: flex;
}

.admin-sidebar {
  width: 200px;
  background: var(--bg-secondary);
  min-height: calc(100vh - 53px);
  padding: var(--space-md) 0;
  border-right: 1px solid var(--border-secondary);
}

.sidebar-item {
  display: block;
  padding: 12px var(--space-xl);
  text-decoration: none;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  transition: all var(--transition-fast);
  border-left: 2px solid transparent;
}

.sidebar-item:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.sidebar-item.active {
  background: rgba(123, 156, 191, 0.08);
  color: var(--color-misty-blue-soft);
  font-weight: 500;
  border-left-color: var(--color-misty-blue);
}

.admin-main {
  flex: 1;
  padding: var(--space-xl);
  min-width: 0;
}

@media (max-width: 768px) {
  .admin-sidebar {
    width: 140px;
  }

  .admin-main {
    padding: var(--space-md);
  }
}
</style>
