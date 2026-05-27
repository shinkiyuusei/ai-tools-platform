<script setup>
import { onMounted, reactive, ref } from 'vue'

import { getUserListAdmin, updateUserAdmin, deleteUserAdmin } from '../../api/admin'
import BaseButton from '../../components/base/BaseButton.vue'
import BaseInput from '../../components/base/BaseInput.vue'
import BasePagination from '../../components/base/BasePagination.vue'
import AppLayout from '../../layouts/AppLayout.vue'

const listData = ref({ list: [], total: 0, pageNum: 1, pageSize: 10 })
const dialogVisible = ref(false)
const loading = ref(false)
const keywords = ref('')

const form = reactive({
  id: null,
  email: '',
  nickname: '',
  credits: 0,
  vipLevel: 0,
  status: 1,
})

const fetchList = async () => {
  loading.value = true
  try {
    const params = { pageNum: listData.value.pageNum, pageSize: listData.value.pageSize }
    if (keywords.value) params.keyword = keywords.value
    const res = await getUserListAdmin(params)
    listData.value.list = res.data.list
    listData.value.total = res.data.total
  } finally {
    loading.value = false
  }
}

const openEdit = (row) => {
  Object.assign(form, {
    id: row.id,
    email: row.email || '',
    nickname: row.nickname || '',
    credits: row.credits ?? 0,
    vipLevel: row.vipLevel ?? 0,
    status: row.status ?? 1,
  })
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  if (!confirm(`确认删除用户「${row.email}」？`)) return
  await deleteUserAdmin(row.id)
  fetchList()
}

const handleSave = async () => {
  await updateUserAdmin(form.id, {
    nickname: form.nickname,
    credits: form.credits,
    vipLevel: form.vipLevel,
    status: form.status,
  })
  dialogVisible.value = false
  fetchList()
}

const handleSearch = () => {
  listData.value.pageNum = 1
  fetchList()
}

const statusLabel = (s) => s === 1 ? '正常' : s === 0 ? '禁用' : s === 2 ? '已注销' : '未知'
const vipLabel = (v) => v >= 2 ? '超管' : v === 1 ? 'VIP' : '普通'

onMounted(fetchList)
</script>

<template>
  <AppLayout>
    <div class="page">
      <div class="page-header">
        <h2>用户管理</h2>
        <div class="header-actions">
          <BaseInput v-model="keywords" placeholder="搜索邮箱或昵称..." @keyup.enter="handleSearch" />
          <BaseButton @click="handleSearch">搜索</BaseButton>
        </div>
      </div>

      <div class="table-wrap">
        <table v-if="!loading">
          <thead>
            <tr>
              <th>ID</th>
              <th>邮箱</th>
              <th>昵称</th>
              <th>积分</th>
              <th>VIP</th>
              <th>状态</th>
              <th>注册时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in listData.list" :key="row.id">
              <td>{{ row.id }}</td>
              <td>{{ row.email }}</td>
              <td>{{ row.nickname }}</td>
              <td>{{ row.credits }}</td>
              <td>
                <span :class="['vip-tag', row.vipLevel >= 2 ? 'admin' : row.vipLevel === 1 ? 'vip' : 'normal']">
                  {{ vipLabel(row.vipLevel) }}
                </span>
              </td>
              <td>
                <span :class="['status-tag', row.status === 1 ? 'on' : 'off']">
                  {{ statusLabel(row.status) }}
                </span>
              </td>
              <td>{{ row.createTime?.slice(0, 10) }}</td>
              <td class="actions-cell">
                <BaseButton size="small" @click="openEdit(row)">编辑</BaseButton>
                <BaseButton size="small" class="btn-del" @click="handleDelete(row)">删除</BaseButton>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!loading && listData.list.length === 0" class="empty">暂无用户</p>
      </div>

      <BasePagination
        v-model:page-num="listData.pageNum"
        :total="listData.total"
        :page-size="listData.pageSize"
        @update:page-num="fetchList"
      />

      <div v-if="dialogVisible" class="dialog-mask" @click.self="dialogVisible = false">
        <div class="dialog-panel">
          <h3>编辑用户 #{{ form.id }}</h3>
          <div class="form-grid">
            <div class="form-group">
              <label>邮箱</label>
              <BaseInput :model-value="form.email" disabled />
            </div>
            <div class="form-group">
              <label>昵称</label>
              <BaseInput v-model="form.nickname" />
            </div>
            <div class="form-group">
              <label>积分</label>
              <BaseInput v-model.number="form.credits" type="number" />
            </div>
            <div class="form-group">
              <label>VIP 等级</label>
              <select v-model.number="form.vipLevel" class="base-select">
                <option :value="0">普通用户</option>
                <option :value="1">VIP</option>
                <option :value="2">超级管理员</option>
              </select>
            </div>
            <div class="form-group">
              <label>状态</label>
              <select v-model.number="form.status" class="base-select">
                <option :value="1">正常</option>
                <option :value="0">禁用</option>
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
.actions-cell { display: flex; gap: 6px; }
.btn-del { background: transparent; border-color: #c85554; color: #c85554; }
.empty { text-align: center; padding: 40px; color: var(--text-tertiary); }

.status-tag { display: inline-block; padding: 2px 8px; border-radius: var(--radius-full); font-size: 11px; font-weight: 500; }
.status-tag.on { background: rgba(76, 175, 142, 0.15); color: #4caf8e; }
.status-tag.off { background: rgba(200, 85, 84, 0.15); color: #c85554; }

.vip-tag { display: inline-block; padding: 2px 8px; border-radius: var(--radius-full); font-size: 11px; font-weight: 500; }
.vip-tag.normal { color: var(--text-tertiary); }
.vip-tag.vip { background: rgba(240, 160, 64, 0.15); color: #f0a040; }
.vip-tag.admin { background: rgba(255, 193, 7, 0.15); color: #e6a800; }

.dialog-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
.dialog-panel { background: var(--bg-card); border-radius: var(--radius-lg); padding: var(--space-lg); max-width: 480px; width: 90%; }
.dialog-panel h3 { margin: 0 0 var(--space-md); }
.form-grid { display: flex; flex-direction: column; gap: var(--space-md); }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group label { font-size: 12px; color: var(--text-tertiary); }
.base-select { padding: 8px 12px; background: var(--bg-elevated); border: 1px solid var(--border-input); border-radius: var(--radius-sm); color: var(--text-primary); font-size: 13px; }
.dialog-actions { display: flex; justify-content: flex-end; gap: var(--space-sm); margin-top: var(--space-lg); }
</style>
