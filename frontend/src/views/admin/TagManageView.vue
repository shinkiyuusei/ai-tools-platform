<script setup>
import { onMounted, reactive, ref } from 'vue'

import { createTag, deleteTag, getTagList, updateTag } from '../../api/admin'
import BaseButton from '../../components/base/BaseButton.vue'
import BaseInput from '../../components/base/BaseInput.vue'
import AdminLayout from '../../layouts/AdminLayout.vue'

const list = ref([])
const dialogVisible = ref(false)
const loading = ref(false)
const form = reactive({ id: null, name: '', sortOrder: 0 })
const isEdit = ref(false)

const fetchList = async () => {
  loading.value = true
  try {
    const res = await getTagList()
    list.value = res.data.list
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  isEdit.value = false
  form.id = null
  form.name = ''
  form.sortOrder = 0
  dialogVisible.value = true
}

const openEdit = (item) => {
  isEdit.value = true
  form.id = item.id
  form.name = item.name
  form.sortOrder = item.sortOrder
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.name) return
  loading.value = true
  try {
    if (isEdit.value) {
      await updateTag(form.id, { name: form.name, sortOrder: form.sortOrder })
    } else {
      await createTag({ name: form.name, sortOrder: form.sortOrder })
    }
    dialogVisible.value = false
    fetchList()
  } finally {
    loading.value = false
  }
}

const handleDelete = async (id) => {
  if (!confirm('确定删除此标签？')) return
  await deleteTag(id)
  fetchList()
}

onMounted(fetchList)
</script>

<template>
  <AdminLayout>
    <div class="page">
      <div class="header-row">
        <h1>标签管理</h1>
        <BaseButton @click="openCreate">新增标签</BaseButton>
      </div>

      <table v-if="list.length" class="table">
        <thead>
          <tr>
            <th>ID</th><th>名称</th><th>排序</th><th>创建时间</th><th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in list" :key="item.id">
            <td>{{ item.id }}</td>
            <td>{{ item.name }}</td>
            <td>{{ item.sortOrder }}</td>
            <td>{{ item.createTime }}</td>
            <td>
              <button class="action-btn" @click="openEdit(item)">编辑</button>
              <button class="action-btn danger" @click="handleDelete(item.id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">暂无数据</div>

      <div v-if="dialogVisible" class="dialog-overlay" @click.self="dialogVisible = false">
        <div class="dialog">
          <h2>{{ isEdit ? '编辑标签' : '新增标签' }}</h2>
          <div class="form-group">
            <BaseInput v-model="form.name" placeholder="标签名称" label="名称" />
          </div>
          <div class="form-group">
            <BaseInput v-model.number="form.sortOrder" placeholder="数字越小越靠前" label="排序" />
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
  width: 440px;
  max-width: 90vw;
}

.dialog h2 {
  font-size: var(--text-lg);
  margin-bottom: var(--space-lg);
}

.form-group {
  margin-bottom: var(--space-md);
}

.dialog-actions {
  display: flex;
  gap: var(--space-sm);
  justify-content: flex-end;
  margin-top: var(--space-lg);
}
</style>
