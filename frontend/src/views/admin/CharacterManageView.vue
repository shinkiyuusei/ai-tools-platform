<script setup>
import { onMounted, reactive, ref } from 'vue'
import { getCharacterListAdmin, getCharacterAdmin, updateCharacterAdmin, deleteCharacterAdmin } from '../../api/admin'
import BaseButton from '../../components/base/BaseButton.vue'
import BaseInput from '../../components/base/BaseInput.vue'
import BasePagination from '../../components/base/BasePagination.vue'
import AppLayout from '../../layouts/AppLayout.vue'

const listData = ref({ list: [], total: 0, pageNum: 1, pageSize: 10 })
const dialogVisible = ref(false)
const loading = ref(false)
const keywords = ref('')

const form = reactive({
  id: null, name: '', avatar: '', description: '',
  personality: '', background: '', tags: '',
  isPublic: 1, isVip: 0, status: 1,
  likeCount: 0, viewCount: 0, collectCount: 0,
})

const fetchList = async () => {
  loading.value = true
  try {
    const params = { pageNum: listData.value.pageNum, pageSize: listData.value.pageSize }
    if (keywords.value) params.keyword = keywords.value
    const res = await getCharacterListAdmin(params)
    listData.value.list = res.data.list
    listData.value.total = res.data.total
  } finally {
    loading.value = false
  }
}

const openDetail = async (row) => {
  try {
    const res = await getCharacterAdmin(row.id)
    Object.assign(form, {
      id: res.data.id, name: res.data.name || '', avatar: res.data.avatar || '',
      description: res.data.description || '', personality: res.data.personality || '',
      background: res.data.background || '', tags: res.data.tags || '',
      isPublic: res.data.isPublic ?? 1,
      isVip: res.data.isVip ?? 0, status: res.data.status ?? 1,
      likeCount: res.data.likeCount ?? 0, viewCount: res.data.viewCount ?? 0,
      collectCount: res.data.collectCount ?? 0,
    })
    dialogVisible.value = true
  } catch { /* */ }
}

const handleSave = async () => {
  await updateCharacterAdmin(form.id, {
    name: form.name, avatar: form.avatar, description: form.description,
    personality: form.personality, background: form.background, tags: form.tags,
    isPublic: form.isPublic, isVip: form.isVip,
    status: form.status, likeCount: form.likeCount, viewCount: form.viewCount,
    collectCount: form.collectCount,
  })
  dialogVisible.value = false
  fetchList()
}

const handleDelete = async (row) => {
  if (!confirm(`确认删除角色卡「${row.name}」？`)) return
  await deleteCharacterAdmin(row.id)
  fetchList()
}

const handleSearch = () => {
  listData.value.pageNum = 1
  fetchList()
}

onMounted(fetchList)
</script>

<template>
  <AppLayout>
    <div class="page">
      <div class="page-header">
        <h2>角色卡管理</h2>
        <div class="header-actions">
          <BaseInput v-model="keywords" placeholder="搜索角色卡..." @keyup.enter="handleSearch" />
          <BaseButton @click="handleSearch">搜索</BaseButton>
        </div>
      </div>

      <div class="table-wrap">
        <table v-if="!loading">
          <thead>
            <tr>
              <th>ID</th>
              <th>名称</th>
              <th>描述</th>
              <th>标签</th>
              <th>播放</th>
              <th>点赞</th>
              <th>收藏</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in listData.list" :key="row.id">
              <td>{{ row.id }}</td>
              <td>{{ row.name?.slice(0, 20) }}{{ row.name?.length > 20 ? '...' : '' }}</td>
              <td class="desc-cell">{{ row.description?.slice(0, 30) }}{{ row.description?.length > 30 ? '...' : '' }}</td>
              <td>{{ (row.tags || '').slice(0, 30) }}</td>
              <td>{{ row.viewCount }}</td>
              <td>{{ row.likeCount }}</td>
              <td>{{ row.collectCount }}</td>
              <td><span :class="['status-dot', row.status ? 'on' : 'off']"></span></td>
              <td class="actions-cell">
                <BaseButton size="small" @click="openDetail(row)">编辑</BaseButton>
                <BaseButton size="small" class="btn-del" @click="handleDelete(row)">删除</BaseButton>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!loading && listData.list.length === 0" class="empty">暂无角色卡</p>
      </div>

      <BasePagination v-model:page-num="listData.pageNum" :total="listData.total" :page-size="listData.pageSize" @change="fetchList" />

      <!-- Edit Dialog -->
      <div v-if="dialogVisible" class="dialog-mask" @click.self="dialogVisible = false">
        <div class="dialog-panel dialog-wide">
          <h3>编辑角色卡 #{{ form.id }}</h3>
          <div class="form-grid">
            <div class="form-group">
              <label>名称</label>
              <BaseInput v-model="form.name" />
            </div>
            <div class="form-group">
              <label>头像 URL</label>
              <BaseInput v-model="form.avatar" />
            </div>
            <div class="form-group form-span">
              <label>描述</label>
              <textarea v-model="form.description" rows="3" class="field-textarea"></textarea>
            </div>
            <div class="form-group form-span">
              <label>性格设定</label>
              <textarea v-model="form.personality" rows="4" class="field-textarea"></textarea>
            </div>
            <div class="form-group form-span">
              <label>背景故事</label>
              <textarea v-model="form.background" rows="4" class="field-textarea"></textarea>
            </div>
            <div class="form-group">
              <label>标签（逗号分隔）</label>
              <BaseInput v-model="form.tags" />
            </div>
            <div class="form-group">
              <label>播放量</label>
              <BaseInput v-model.number="form.viewCount" type="number" />
            </div>
            <div class="form-group">
              <label>点赞数</label>
              <BaseInput v-model.number="form.likeCount" type="number" />
            </div>
            <div class="form-group">
              <label>收藏数</label>
              <BaseInput v-model.number="form.collectCount" type="number" />
            </div>
            <div class="form-group">
              <label>公开</label>
              <select v-model.number="form.isPublic" class="base-select">
                <option :value="1">是</option>
                <option :value="0">否</option>
              </select>
            </div>
            <div class="form-group">
              <label>VIP</label>
              <select v-model.number="form.isVip" class="base-select">
                <option :value="0">否</option>
                <option :value="1">是</option>
              </select>
            </div>
            <div class="form-group">
              <label>状态</label>
              <select v-model.number="form.status" class="base-select">
                <option :value="1">上架</option>
                <option :value="0">下架</option>
              </select>
            </div>
          </div>
          <div class="dialog-actions">
            <BaseButton @click="dialogVisible = false">取消</BaseButton>
            <BaseButton type="primary" @click="handleSave">保存</BaseButton>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.page { padding: var(--space-lg); }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-lg); }
.page-header h2 { font-size: 20px; margin: 0; }
.header-actions { display: flex; gap: var(--space-sm); }

.table-wrap { background: var(--bg-card); border: 1px solid var(--border-card); border-radius: var(--radius-md); overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border-card); white-space: nowrap; }
th { background: var(--bg-elevated); font-weight: 600; color: var(--text-secondary); }
.desc-cell { max-width: 200px; overflow: hidden; text-overflow: ellipsis; color: var(--text-tertiary); }
.actions-cell { display: flex; gap: 6px; }
.status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; }
.status-dot.on { background: #4caf8e; }
.status-dot.off { background: #c85554; }
.btn-del { background: transparent; border-color: #c85554; color: #c85554; }
.empty { text-align: center; padding: 40px; color: var(--text-tertiary); }

/* Dialog */
.dialog-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
.dialog-panel { background: var(--bg-card); border-radius: var(--radius-lg); padding: var(--space-lg); max-width: 500px; width: 90%; max-height: 80vh; overflow-y: auto; }
.dialog-wide { max-width: 700px; }
.dialog-panel h3 { margin: 0 0 var(--space-md); }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-md); }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-span { grid-column: 1 / -1; }
.form-group label { font-size: 12px; color: var(--text-tertiary); }
.field-textarea { padding: 8px 12px; background: var(--bg-elevated); border: 1px solid var(--border-input); border-radius: var(--radius-sm); color: var(--text-primary); font-size: 13px; resize: vertical; font-family: inherit; }
.base-select { padding: 8px 12px; background: var(--bg-elevated); border: 1px solid var(--border-input); border-radius: var(--radius-sm); color: var(--text-primary); font-size: 13px; }
.dialog-actions { display: flex; justify-content: flex-end; gap: var(--space-sm); margin-top: var(--space-lg); }
</style>
