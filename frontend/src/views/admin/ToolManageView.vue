<script setup>
import { onMounted, reactive, ref } from 'vue'

import { createTool, deleteTool, getTagList, getToolListAdmin, updateTool } from '../../api/admin'
import BaseButton from '../../components/base/BaseButton.vue'
import BaseInput from '../../components/base/BaseInput.vue'
import BasePagination from '../../components/base/BasePagination.vue'
import AdminLayout from '../../layouts/AdminLayout.vue'

const listData = ref({ list: [], total: 0, pageNum: 1, pageSize: 10 })
const dialogVisible = ref(false)
const loading = ref(false)
const isEdit = ref(false)
const allTags = ref([])
const selectedTagIds = ref([])

const form = reactive({
  id: null, name: '', desc: '', useDesc: '', categoryId: 0, tagIds: '',
  formConfig: '', aiApi: 'deepseek', isFree: 1, isVip: 0, sortOrder: 0, status: 1,
})

const fetchList = async () => {
  loading.value = true
  try {
    const res = await getToolListAdmin({ pageNum: listData.value.pageNum, pageSize: listData.value.pageSize })
    listData.value.list = res.data.list
    listData.value.total = res.data.total
  } finally {
    loading.value = false
  }
}

const loadTags = async () => {
  try {
    const res = await getTagList()
    allTags.value = res.data.list || []
  } catch { /* */ }
}

const toggleTag = (tagId) => {
  const idx = selectedTagIds.value.indexOf(tagId)
  if (idx >= 0) selectedTagIds.value.splice(idx, 1)
  else selectedTagIds.value.push(tagId)
  form.tagIds = selectedTagIds.value.join(',')
}

const openCreate = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null, name: '', desc: '', useDesc: '', categoryId: 0, tagIds: '',
    formConfig: '', aiApi: 'deepseek', isFree: 1, isVip: 0, sortOrder: 0, status: 1,
  })
  selectedTagIds.value = []
  dialogVisible.value = true
}

const openEdit = (item) => {
  isEdit.value = true
  Object.assign(form, {
    id: item.id, name: item.name, desc: item.desc, useDesc: item.useDesc || '',
    categoryId: item.categoryId, tagIds: item.tagIds,
    formConfig: item.formConfig || '', aiApi: item.aiApi || 'deepseek',
    isFree: item.isFree, isVip: item.isVip, sortOrder: item.sortOrder, status: item.status,
  })
  selectedTagIds.value = item.tagIds
    ? item.tagIds.split(',').map(Number).filter(Boolean)
    : []
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.name) return
  loading.value = true
  try {
    let fc = form.formConfig
    if (typeof fc === 'string' && fc.trim()) {
      try { fc = JSON.parse(fc) } catch { fc = [] }
    } else if (!fc) { fc = [] }
    const data = { ...form, formConfig: fc }
    if (isEdit.value) {
      await updateTool(form.id, data)
    } else {
      await createTool(data)
    }
    dialogVisible.value = false
    fetchList()
  } catch (err) {
    window.dispatchEvent(new CustomEvent('app:error', { detail: err.message || '操作失败' }))
  } finally {
    loading.value = false
  }
}

const handleDelete = async (id) => {
  if (!confirm('确定删除此工具？')) return
  await deleteTool(id)
  fetchList()
}

const handlePageChange = (page) => {
  listData.value.pageNum = page
  fetchList()
}

onMounted(() => { fetchList(); loadTags() })
</script>

<template>
  <AdminLayout>
    <div class="page">
      <div class="header-row">
        <h1>工具管理</h1>
        <BaseButton @click="openCreate">新增工具</BaseButton>
      </div>

      <div v-if="listData.list.length" class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th><th>名称</th><th>分类</th><th>免费</th><th>会员</th><th>使用次数</th><th>状态</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in listData.list" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.categoryId }}</td>
              <td>{{ item.isFree ? '是' : '否' }}</td>
              <td>{{ item.isVip ? '是' : '否' }}</td>
              <td>{{ item.useCount }}</td>
              <td>{{ item.status === 1 ? '上架' : '下架' }}</td>
              <td>
                <button class="action-btn" @click="openEdit(item)">编辑</button>
                <button class="action-btn danger" @click="handleDelete(item.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty">暂无工具数据</div>

      <BasePagination
        v-if="listData.total > 0"
        :page-num="listData.pageNum"
        :page-size="listData.pageSize"
        :total="listData.total"
        @update:page-num="handlePageChange"
      />

      <div v-if="dialogVisible" class="dialog-overlay" @click.self="dialogVisible = false">
        <div class="dialog">
          <h2>{{ isEdit ? '编辑工具' : '新增工具' }}</h2>
          <div class="form-group">
            <BaseInput v-model="form.name" placeholder="工具名称" label="名称 *" />
          </div>
          <div class="form-group">
            <BaseInput v-model="form.desc" placeholder="简短描述" label="描述" />
          </div>
          <div class="form-group">
            <label>使用说明</label>
            <textarea v-model="form.useDesc" class="base-textarea" rows="3" placeholder="使用说明" />
          </div>
          <div class="form-row">
            <div class="form-group half">
              <BaseInput v-model.number="form.categoryId" placeholder="分类ID" label="分类ID" />
            </div>
            <div class="form-group half">
              <label>标签</label>
              <div class="tag-picker">
                <label v-for="tag in allTags" :key="tag.id" class="tag-checkbox">
                  <input
                    type="checkbox"
                    :checked="selectedTagIds.includes(tag.id)"
                    @change="toggleTag(tag.id)"
                  />
                  {{ tag.name }}
                </label>
              </div>
            </div>
          </div>
          <div class="form-group">
            <label>表单配置(JSON)</label>
            <textarea v-model="form.formConfig" class="base-textarea" rows="5" placeholder='[{"field":"topic","label":"主题","type":"text","required":true}]' />
          </div>
          <div class="form-row">
            <div class="form-group half">
              <BaseInput v-model.number="form.sortOrder" label="排序" />
            </div>
            <div class="form-group half">
              <label>状态</label>
              <select v-model.number="form.status" class="base-select">
                <option :value="1">上架</option>
                <option :value="0">下架</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group half">
              <label>免费工具</label>
              <select v-model.number="form.isFree" class="base-select">
                <option :value="1">是</option>
                <option :value="0">否</option>
              </select>
            </div>
            <div class="form-group half">
              <label>会员专属</label>
              <select v-model.number="form.isVip" class="base-select">
                <option :value="1">是</option>
                <option :value="0">否</option>
              </select>
            </div>
          </div>
          <div class="dialog-actions">
            <BaseButton variant="secondary" @click="dialogVisible = false">取消</BaseButton>
            <BaseButton :loading="loading" @click="handleSubmit">保存</BaseButton>
          </div>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<style scoped>
.page {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-card);
  padding: var(--space-xl);
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.header-row h1 {
  font-size: var(--text-lg);
  margin: 0;
}

.table-wrap {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-card);
  font-size: var(--text-sm);
  white-space: nowrap;
}

.table th {
  color: var(--text-tertiary);
  font-weight: 600;
}

.action-btn {
  border: none;
  background: none;
  color: var(--color-misty-blue-soft);
  cursor: pointer;
  font-size: var(--text-xs);
  margin-right: 12px;
}

.action-btn.danger {
  color: var(--color-crimson-soft);
}

.empty {
  text-align: center;
  padding: var(--space-3xl);
  color: var(--text-tertiary);
}

.dialog-overlay {
  position: fixed;
  inset: 0;
  background: var(--bg-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
}

.dialog {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-card);
  padding: var(--space-xl);
  width: 520px;
  max-width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
}

.dialog h2 {
  font-size: var(--text-lg);
  margin-bottom: var(--space-lg);
}

.form-group {
  margin-bottom: var(--space-md);
}

.form-group label {
  display: block;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
  font-weight: 500;
}

.form-row {
  display: flex;
  gap: var(--space-md);
}

.half {
  flex: 1;
}

.base-textarea {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-input);
  border: 1px solid var(--border-input);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
  resize: vertical;
  line-height: var(--leading-relaxed);
}

.base-textarea:focus {
  outline: none;
  border-color: var(--border-focus);
}

.base-select {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-input);
  border: 1px solid var(--border-input);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
}

.dialog-actions {
  display: flex;
  gap: var(--space-sm);
  justify-content: flex-end;
  margin-top: var(--space-lg);
}

.tag-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px;
  background: var(--bg-input);
  border: 1px solid var(--border-input);
  border-radius: var(--radius-md);
  max-height: 160px;
  overflow-y: auto;
}

.tag-checkbox {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  cursor: pointer;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}

.tag-checkbox:hover {
  background: rgba(123, 156, 191, 0.08);
}

.tag-checkbox input {
  accent-color: var(--color-misty-blue);
}

@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
    gap: 0;
  }
}
</style>
