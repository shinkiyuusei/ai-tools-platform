<script setup>
import { ref, onMounted } from 'vue'
import { extensionApi } from '../../api/extensions'
import AppLayout from '../../layouts/AppLayout.vue'
import { notifyError, notifySuccess } from '../../utils/notify'

const extensions = ref([])
const loading = ref(true)
const showInstallForm = ref(false)
const installForm = ref({
  id: '',
  name: '',
  version: '1.0.0',
  description: '',
  author: '',
  permissions: [],
})

const loadAll = async () => {
  loading.value = true
  try {
    const res = await extensionApi.list()
    extensions.value = (res.data || []).map(e => {
      const m = typeof e.manifest === 'string' ? JSON.parse(e.manifest) : e.manifest
      return { ...e, manifest: m || {} }
    })
  } catch (e) {
    notifyError('加载扩展列表失败')
  } finally {
    loading.value = false
  }
}

const toggleStatus = async (ext) => {
  try {
    const newStatus = ext.status === 'active' ? 'inactive' : 'active'
    await extensionApi.updateStatus(ext.id, newStatus)
    ext.status = newStatus
    notifySuccess(`扩展已${newStatus === 'active' ? '启用' : '禁用'}`)
  } catch (e) {
    notifyError(e.message || '操作失败')
  }
}

const uninstall = async (ext) => {
  if (!confirm(`确定卸载扩展 "${ext.id}"？`)) return
  try {
    await extensionApi.uninstall(ext.id)
    extensions.value = extensions.value.filter(e => e.id !== ext.id)
    notifySuccess('扩展已卸载')
  } catch (e) {
    notifyError(e.message || '卸载失败')
  }
}

const install = async () => {
  const { id, name, version, description, author, permissions } = installForm.value
  if (!id.trim() || !name.trim()) {
    notifyError('ID 和名称不能为空')
    return
  }
  try {
    await extensionApi.install(id.trim(), {
      id: id.trim(),
      name: { zh: name.trim() },
      version: version.trim(),
      description: { zh: description.trim() },
      author: author.trim(),
      permissions,
    })
    notifySuccess('安装成功')
    showInstallForm.value = false
    installForm.value = { id: '', name: '', version: '1.0.0', description: '', author: '', permissions: [] }
    loadAll()
  } catch (e) {
    notifyError(e.message || '安装失败')
  }
}

onMounted(loadAll)
</script>

<template>
  <AppLayout>
    <div class="admin-page">
      <header class="admin-header">
        <h1>扩展管理</h1>
        <button class="btn-primary" @click="showInstallForm = !showInstallForm">
          {{ showInstallForm ? '取消' : '+ 安装扩展' }}
        </button>
      </header>

      <!-- Install form -->
      <div v-if="showInstallForm" class="install-form">
        <div class="form-row">
          <label>ID <input v-model="installForm.id" placeholder="com.example.my-ext" /></label>
          <label>名称 <input v-model="installForm.name" placeholder="我的扩展" /></label>
        </div>
        <div class="form-row">
          <label>版本 <input v-model="installForm.version" placeholder="1.0.0" /></label>
          <label>作者 <input v-model="installForm.author" placeholder="作者名" /></label>
        </div>
        <label>描述 <input v-model="installForm.description" placeholder="简短描述" /></label>
        <button class="btn-primary" @click="install">确认安装</button>
      </div>

      <!-- Table -->
      <div v-if="loading" class="loading-state">加载中...</div>
      <table v-else class="admin-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>名称</th>
            <th>版本</th>
            <th>作者</th>
            <th>状态</th>
            <th>安装时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ext in extensions" :key="ext.id">
            <td><code>{{ ext.id }}</code></td>
            <td>{{ ext.manifest.name?.zh || ext.manifest.name?.en || ext.id }}</td>
            <td>{{ ext.manifest.version }}</td>
            <td>{{ ext.manifest.author || '-' }}</td>
            <td><span :class="['status-tag', ext.status]">{{ ext.status }}</span></td>
            <td>{{ (ext.install_time || '').slice(0, 10) }}</td>
            <td class="actions">
              <button @click="toggleStatus(ext)">
                {{ ext.status === 'active' ? '禁用' : '启用' }}
              </button>
              <button class="danger" @click="uninstall(ext)">卸载</button>
            </td>
          </tr>
          <tr v-if="extensions.length === 0">
            <td colspan="7" style="text-align:center;color:var(--text-tertiary)">暂无扩展</td>
          </tr>
        </tbody>
      </table>
    </div>
  </AppLayout>
</template>

<style scoped>
.admin-page { padding: 24px; max-width: 1100px; margin: 0 auto; }
.admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.admin-header h1 { font-size: var(--text-xl); margin: 0; color: var(--text-primary); }
.install-form { background: var(--bg-card); border: 1px solid var(--border-primary); border-radius: var(--radius-lg); padding: 16px; margin-bottom: 20px; }
.install-form label { display: block; margin-bottom: 8px; font-size: var(--text-sm); color: var(--text-secondary); }
.install-form input { width: 100%; padding: 6px 10px; background: var(--bg-primary); border: 1px solid var(--border-primary); border-radius: var(--radius-sm); color: var(--text-primary); }
.form-row { display: flex; gap: 12px; margin-bottom: 8px; }
.form-row label { flex: 1; }
.admin-table { width: 100%; border-collapse: collapse; }
.admin-table th, .admin-table td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border-primary); font-size: var(--text-sm); }
.admin-table th { color: var(--text-secondary); font-weight: 600; }
.status-tag { font-size: var(--text-xs); padding: 2px 8px; border-radius: var(--radius-sm); }
.status-tag.active { background: rgba(61, 107, 86, 0.2); color: var(--color-dark-green); }
.status-tag.inactive { background: rgba(158, 158, 170, 0.2); color: var(--text-tertiary); }
.actions { display: flex; gap: 8px; }
.actions button { font-size: var(--text-xs); padding: 4px 10px; border: 1px solid var(--border-primary); border-radius: var(--radius-sm); background: transparent; color: var(--text-secondary); cursor: pointer; }
.actions button:hover { border-color: var(--text-tertiary); }
.actions button.danger { color: var(--color-crimson); border-color: rgba(200, 85, 84, 0.3); }
.btn-primary { padding: 8px 16px; background: var(--color-misty-blue); color: #fff; border: none; border-radius: var(--radius-md); cursor: pointer; font-size: var(--text-sm); }
.loading-state { text-align: center; padding: 48px; color: var(--text-secondary); }
</style>
