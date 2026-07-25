<script setup>
import { ref, onMounted } from 'vue'
import { extensionApi } from '../api/extensions'
import AppLayout from '../layouts/AppLayout.vue'
import { notifyError, notifySuccess } from '../utils/notify'

const extensions = ref([])
const loading = ref(true)

const loadExtensions = async () => {
  loading.value = true
  try {
    const res = await extensionApi.list()
    extensions.value = (res.data || []).map(e => {
      const manifest = typeof e.manifest === 'string' ? JSON.parse(e.manifest) : e.manifest
      return { ...e, manifest: manifest || {} }
    })
  } catch (e) {
    notifyError('加载扩展列表失败')
  } finally {
    loading.value = false
  }
}

const getConfig = async (extId) => {
  try {
    const res = await extensionApi.getConfig(extId)
    return res.data || {}
  } catch {
    return {}
  }
}

const saveConfig = async (extId, config) => {
  try {
    await extensionApi.setConfig(extId, config)
    notifySuccess('配置已保存')
  } catch (e) {
    notifyError(e.message || '保存失败')
  }
}

onMounted(loadExtensions)
</script>

<template>
  <AppLayout>
    <div class="marketplace-page">
      <header class="mp-header">
        <h1>扩展市场</h1>
        <p class="mp-subtitle">浏览已安装的扩展，配置个性化设置</p>
      </header>

      <div v-if="loading" class="loading-state">加载中...</div>

      <div v-else-if="extensions.length === 0" class="mp-empty">
        <p>暂无已安装的扩展</p>
        <p class="hint">管理员可在后台安装新扩展</p>
      </div>

      <div v-else class="mp-grid">
        <div
          v-for="ext in extensions"
          :key="ext.id"
          class="mp-card"
        >
          <div class="mp-card-header">
            <span class="mp-card-icon">{{ (ext.manifest.icon || '◇').slice(0, 2) }}</span>
            <div>
              <h3 class="mp-card-name">{{ ext.manifest.name?.zh || ext.manifest.name?.en || ext.id }}</h3>
              <span class="mp-card-version">v{{ ext.manifest.version || '1.0.0' }}</span>
            </div>
          </div>
          <p class="mp-card-desc">
            {{ ext.manifest.description?.zh || ext.manifest.description?.en || '暂无描述' }}
          </p>
          <div class="mp-card-meta">
            <span v-if="ext.manifest.author">{{ ext.manifest.author }}</span>
            <span :class="['mp-status', ext.status]">{{ ext.status === 'active' ? '✓ 已启用' : ext.status }}</span>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.marketplace-page { padding: 24px; max-width: 1000px; margin: 0 auto; }
.mp-header { margin-bottom: 24px; }
.mp-header h1 { font-size: var(--text-2xl); color: var(--text-primary); margin: 0; }
.mp-subtitle { color: var(--text-tertiary); margin-top: 4px; }
.mp-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.mp-card { background: var(--bg-card); border: 1px solid var(--border-primary); border-radius: var(--radius-lg); padding: 16px; }
.mp-card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.mp-card-icon { font-size: 1.5rem; }
.mp-card-name { font-size: var(--text-base); color: var(--text-primary); margin: 0; }
.mp-card-version { font-size: var(--text-xs); color: var(--text-tertiary); }
.mp-card-desc { font-size: var(--text-sm); color: var(--text-secondary); margin: 8px 0; }
.mp-card-meta { display: flex; justify-content: space-between; align-items: center; font-size: var(--text-xs); color: var(--text-tertiary); }
.mp-status.active { color: var(--color-dark-green); }
.mp-empty { text-align: center; padding: 48px 0; color: var(--text-tertiary); }
.loading-state { text-align: center; padding: 48px 0; color: var(--text-secondary); }
.hint { font-size: var(--text-xs); color: var(--text-tertiary); }
</style>
