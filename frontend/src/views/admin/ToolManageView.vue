<script setup>
import { onMounted, reactive, ref } from 'vue'

import { createTool, deleteTool, getToolListAdmin, updateTool } from '../../api/admin'
import BaseButton from '../../components/base/BaseButton.vue'
import BaseInput from '../../components/base/BaseInput.vue'
import BasePagination from '../../components/base/BasePagination.vue'
import AppLayout from '../../layouts/AppLayout.vue'

const listData = ref({ list: [], total: 0, pageNum: 1, pageSize: 10 })
const dialogVisible = ref(false)
const loading = ref(false)
const isEdit = ref(false)

const form = reactive({
  id: null, name: '', icon: '', desc: '', useDesc: '',
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

const openCreate = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null, name: '', icon: '', desc: '', useDesc: '',
    formConfig: '', aiApi: 'deepseek', isFree: 1, isVip: 0, sortOrder: 0, status: 1,
  })
  dialogVisible.value = true
}

const openEdit = (item) => {
  isEdit.value = true
  Object.assign(form, {
    id: item.id, name: item.name, icon: item.icon || '', desc: item.desc || '',
    useDesc: item.useDesc || '',
    formConfig: typeof item.formConfig === 'string' ? item.formConfig : JSON.stringify(item.formConfig || {}, null, 2),
    aiApi: item.aiApi || 'deepseek', isFree: item.isFree ?? 1, isVip: item.isVip ?? 0,
    sortOrder: item.sortOrder ?? 0, status: item.status ?? 1,
  })
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

onMounted(fetchList)
</script>

<template>
  <AppLayout>
    <div class="page">
      <div class="header-row">
        <h1>工具管理</h1>
        <BaseButton @click="openCreate">新增工具</BaseButton>
      </div>

      <div v-if="listData.list.length" class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th><th>图标</th><th>名称</th><th>AI接口</th><th>免费</th><th>VIP</th><th>排序</th><th>状态</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in listData.list" :key="item.id">
              <td>{{ item.id }}</td>
              <td><img v-if="item.icon" :src="item.icon" class="icon-preview" /></td>
              <td>{{ item.name }}</td>
              <td>{{ item.aiApi || '-' }}</td>
              <td>{{ item.isFree ? '是' : '否' }}</td>
              <td>{{ item.isVip ? '是' : '否' }}</td>
              <td>{{ item.sortOrder }}</td>
              <td><span :class="['status-tag', item.status === 1 ? 'on' : 'off']">{{ item.status === 1 ? '上架' : '下架' }}</span></td>
              <td class="actions-cell">
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
        <div class="dialog dialog-wide">
          <h2>{{ isEdit ? '编辑工具' : '新增工具' }}</h2>
          <div class="dialog-body">
            <!-- 基础信息 -->
            <div class="form-row">
              <div class="form-group flex-2">
                <BaseInput v-model="form.name" placeholder="工具名称" label="名称 *" />
              </div>
              <div class="form-group flex-1">
                <BaseInput v-model="form.icon" placeholder="图标URL" label="图标" />
              </div>
            </div>
            <div class="form-group">
              <label>描述</label>
              <textarea v-model="form.desc" class="base-textarea" rows="2" placeholder="简短描述" />
            </div>
            <div class="form-group">
              <label>使用说明</label>
              <textarea v-model="form.useDesc" class="base-textarea" rows="3" placeholder="详细使用说明" />
            </div>

            <!-- AI接口 -->
            <div class="form-row">
              <div class="form-group half">
                <label>AI 接口</label>
                <select v-model="form.aiApi" class="base-select">
                  <option value="deepseek">DeepSeek</option>
                  <option value="openai">OpenAI</option>
                  <option value="claude">Claude</option>
                  <option value="qwen">通义千问</option>
                  <option value="glm">智谱GLM</option>
                  <option value="moonshot">Moonshot</option>
                  <option value="">无</option>
                </select>
              </div>
              <div class="form-group half">
                <BaseInput v-model.number="form.sortOrder" label="排序" placeholder="越小越靠前" />
              </div>
            </div>

            <!-- 表单配置 -->
            <div class="form-group">
              <label>表单配置 (JSON)</label>
              <textarea v-model="form.formConfig" class="base-textarea mono" rows="8" placeholder='[{"field":"topic","label":"主题","type":"text","required":true}]' />
            </div>

            <!-- 状态和权限 -->
            <div class="form-row">
              <div class="form-group half">
                <label>状态</label>
                <select v-model.number="form.status" class="base-select">
                  <option :value="1">上架</option>
                  <option :value="0">下架</option>
                </select>
              </div>
              <div class="form-group half">
                <label>免费工具</label>
                <select v-model.number="form.isFree" class="base-select">
                  <option :value="1">是</option>
                  <option :value="0">否</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group half">
                <label>会员专属</label>
                <select v-model.number="form.isVip" class="base-select">
                  <option :value="1">是</option>
                  <option :value="0">否</option>
                </select>
              </div>
            </div>
          </div>
          <div class="dialog-actions">
            <BaseButton variant="secondary" @click="dialogVisible = false">取消</BaseButton>
            <BaseButton :loading="loading" @click="handleSubmit">保存</BaseButton>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
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

.icon-preview {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  object-fit: cover;
  background: var(--bg-tertiary);
}

.status-tag {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
}

.status-tag.on {
  color: #4caf8e;
  background: rgba(76, 175, 142, 0.1);
}

.status-tag.off {
  color: #c85554;
  background: rgba(200, 85, 84, 0.1);
}

.actions-cell {
  display: flex;
  gap: 6px;
}

.action-btn {
  border: none;
  background: none;
  color: var(--color-misty-blue-soft);
  cursor: pointer;
  font-size: var(--text-xs);
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
  align-items: flex-start;
  justify-content: center;
  z-index: var(--z-modal);
  padding-top: 40px;
}

.dialog {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-card);
  padding: var(--space-xl);
  width: 640px;
  max-width: 92vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.dialog-wide {
  width: 720px;
}

.dialog h2 {
  font-size: var(--text-lg);
  margin: 0 0 var(--space-lg);
  flex-shrink: 0;
}

.dialog-body {
  overflow-y: auto;
  flex: 1;
  padding-right: var(--space-sm);
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

.flex-1 { flex: 1; }
.flex-2 { flex: 2; }

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
  font-family: inherit;
}

.base-textarea.mono {
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.5;
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
  padding-top: var(--space-md);
  border-top: 1px solid var(--border-card);
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
    gap: 0;
  }
}
</style>
