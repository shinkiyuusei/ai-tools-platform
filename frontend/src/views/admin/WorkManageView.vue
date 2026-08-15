<script setup>
import { onMounted, reactive, ref } from 'vue'
import { getWorkListAdmin, getWorkAdmin, updateWorkAdmin, deleteWorkAdmin } from '../../api/admin'
import BaseButton from '../../components/base/BaseButton.vue'
import BaseInput from '../../components/base/BaseInput.vue'
import BasePagination from '../../components/base/BasePagination.vue'
import AppLayout from '../../layouts/AppLayout.vue'

const listData = ref({ list: [], total: 0, pageNum: 1, pageSize: 10 })
const dialogVisible = ref(false)
const loading = ref(false)
const keywords = ref('')
const formContent = ref('')
const openings = ref([{ label: '', text: '' }])

const form = reactive({
  id: null, name: '', cover: '', desc: '', tags: '',
  categoryId: 0, useCount: 0, status: 1,
})
const writingStyle = ref({
  contentMode: 'nsfw', sensoryDensity: 'high', pacingPreference: 'slow',
  powerIntensity: 'extreme', proseStyle: 'direct', wordCount: 1500,
})
const showWritingStyle = ref(false)

function addOpening() {
  if (openings.value.length >= 10) return
  openings.value.push({ label: '', text: '' })
}

function removeOpening(index) {
  if (openings.value.length <= 1) return
  openings.value.splice(index, 1)
}

const fetchList = async () => {
  loading.value = true
  try {
    const params = { pageNum: listData.value.pageNum, pageSize: listData.value.pageSize }
    if (keywords.value) params.keyword = keywords.value
    const res = await getWorkListAdmin(params)
    listData.value.list = res.data.list
    listData.value.total = res.data.total
  } finally {
    loading.value = false
  }
}

const openDetail = async (row) => {
  try {
    const res = await getWorkAdmin(row.id)
    const d = res.data

    const rawOpenings = d.openings || []
    openings.value = rawOpenings.length > 0
      ? rawOpenings.map(o => ({ label: o.label || '', text: o.text || '' }))
      : [{ label: '', text: '' }]

    Object.assign(form, {
      id: d.id,
      name: d.name || '',
      cover: d.cover || '',
      desc: d.desc || '',
      tags: Array.isArray(d.tags) ? d.tags.map(t => t.name || t).join(', ') : (d.tags || ''),
      categoryId: d.category || 0,
      useCount: d.useCount ?? 0,
      status: d.status ?? 1,
    })
    if (d.writingStyle) {
      writingStyle.value = { ...writingStyle.value, ...d.writingStyle }
    }
    formContent.value = JSON.stringify(d.content || {}, null, 2)
    dialogVisible.value = true
  } catch { /* */ }
}

const handleSave = async () => {
  let content
  try {
    content = formContent.value.trim() ? JSON.parse(formContent.value) : {}
  } catch {
    alert('Content JSON 格式错误，请检查后重试')
    return
  }

  const payload = {
    name: form.name,
    cover: form.cover,
    desc: form.desc,
    category: form.categoryId,
    useCount: form.useCount,
    status: form.status,
    writingStyle: writingStyle.value,
    content,
    openingStatements: openings.value.filter(o => o.text.trim()),
  }

  if (form.tags) {
    payload.tags = form.tags.split(',').map(t => {
      const trimmed = t.trim()
      return { name: trimmed, type: 'app' }
    })
  }

  await updateWorkAdmin(form.id, payload)
  dialogVisible.value = false
  fetchList()
}

const handleDelete = async (row) => {
  if (!confirm(`确认删除作品卡「${row.name}」？`)) return
  await deleteWorkAdmin(row.id)
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
        <h2>作品卡管理</h2>
        <div class="header-actions">
          <BaseInput v-model="keywords" placeholder="搜索作品..." @keyup.enter="handleSearch" />
          <BaseButton @click="handleSearch">搜索</BaseButton>
        </div>
      </div>

      <div class="table-wrap">
        <table v-if="!loading">
          <thead>
            <tr>
              <th>ID</th>
              <th>名称</th>
              <th>封面</th>
              <th>描述</th>
              <th>分类</th>
              <th>Token消耗</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in listData.list" :key="row.id">
              <td>{{ row.id }}</td>
              <td>{{ row.name?.slice(0, 20) }}{{ row.name?.length > 20 ? '...' : '' }}</td>
              <td><img v-if="row.cover" :src="row.cover" class="cover-thumb" /></td>
              <td class="desc-cell">{{ row.desc?.slice(0, 40) }}{{ row.desc?.length > 40 ? '...' : '' }}</td>
              <td>{{ row.categoryId }}</td>
              <td>{{ row.useCount }}</td>
              <td>
                <span :class="['status-tag', row.status === 1 ? 'on' : row.status === 2 ? 'admin' : 'off']">
                  {{ row.status === 1 ? '上架' : row.status === 2 ? '管理员可见' : '下架' }}
                </span>
              </td>
              <td class="actions-cell">
                <BaseButton size="small" @click="openDetail(row)">编辑</BaseButton>
                <BaseButton size="small" class="btn-del" @click="handleDelete(row)">删除</BaseButton>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!loading && listData.list.length === 0" class="empty">暂无作品卡</p>
      </div>

      <BasePagination v-model:page-num="listData.pageNum" :total="listData.total" :page-size="listData.pageSize" @update:page-num="fetchList" />

      <div v-if="dialogVisible" class="dialog-mask" @click.self="dialogVisible = false">
        <div class="dialog-panel dialog-wide">
          <h3>编辑作品卡 #{{ form.id }}</h3>
          <div class="form-grid">
            <div class="form-group">
              <label>名称</label>
              <BaseInput v-model="form.name" />
            </div>
            <div class="form-group">
              <label>封面 URL</label>
              <BaseInput v-model="form.cover" />
            </div>
            <div class="form-group form-span">
              <label>描述</label>
              <textarea v-model="form.desc" rows="3" class="field-textarea"></textarea>
            </div>
            <div class="form-group">
              <label>标签（逗号分隔）</label>
              <BaseInput v-model="form.tags" />
            </div>
            <div class="form-group">
              <label>分类 ID</label>
              <BaseInput v-model.number="form.categoryId" type="number" />
            </div>
            <div class="form-group">
              <label>Token消耗</label>
              <BaseInput v-model.number="form.useCount" type="number" />
            </div>
            <div class="form-group">
              <label>状态</label>
              <select v-model.number="form.status" class="base-select">
                <option :value="1">上架</option>
                <option :value="0">下架</option>
                <option :value="2">仅超级管理员可见</option>
              </select>
            </div>
            <div class="form-group form-span">
              <label>开场白 ({{ openings.length }}/10)</label>
              <div v-for="(item, idx) in openings" :key="idx" class="opening-editor-item">
                <div class="opening-item-header">
                  <span class="opening-item-num">#{{ idx + 1 }}</span>
                  <button v-if="openings.length > 1" class="btn-remove-sm" @click="removeOpening(idx)">×</button>
                </div>
                <BaseInput v-model="item.label" placeholder="标题" />
                <textarea v-model="item.text" rows="2" class="field-textarea" placeholder="开场白内容" />
              </div>
              <button class="btn-add-opening" @click="addOpening">+ 添加开场白</button>
            </div>
            <div class="form-group form-span">
              <button class="btn-toggle-ws" @click="showWritingStyle = !showWritingStyle">
                {{ showWritingStyle ? '▼' : '▶' }} 写作风格配置
              </button>
            </div>
            <div v-show="showWritingStyle" class="form-group form-span ws-inline">
              <div class="ws-inline-group">
                <div class="ws-inline-row">
                  <span class="ws-inline-label">内容模式</span>
                  <label class="ws-toggle-label">
                    <span :class="{ on: writingStyle.contentMode === 'normal' }">正常</span>
                    <input type="checkbox" class="ws-checkbox"
                      :checked="writingStyle.contentMode === 'nsfw'"
                      @change="writingStyle.contentMode = writingStyle.contentMode === 'nsfw' ? 'normal' : 'nsfw'" />
                    <span :class="{ on: writingStyle.contentMode === 'nsfw' }">NSFW</span>
                  </label>
                </div>
                <div class="ws-inline-row">
                  <span class="ws-inline-label">感官密度</span>
                  <select v-model="writingStyle.sensoryDensity" :disabled="writingStyle.contentMode !== 'nsfw'" class="base-select">
                    <option value="low">轻量</option>
                    <option value="medium">均衡</option>
                    <option value="high">过载</option>
                  </select>
                </div>
                <div class="ws-inline-row">
                  <span class="ws-inline-label">叙事节奏</span>
                  <select v-model="writingStyle.pacingPreference" :disabled="writingStyle.contentMode !== 'nsfw'" class="base-select">
                    <option value="slow">慢热</option>
                    <option value="balanced">均衡</option>
                    <option value="fast">快节奏</option>
                  </select>
                </div>
                <div class="ws-inline-row">
                  <span class="ws-inline-label">支配强度</span>
                  <select v-model="writingStyle.powerIntensity" :disabled="writingStyle.contentMode !== 'nsfw'" class="base-select">
                    <option value="mild">温和</option>
                    <option value="medium">标准</option>
                    <option value="extreme">极限</option>
                  </select>
                </div>
                <div class="ws-inline-row">
                  <span class="ws-inline-label">文风倾向</span>
                  <select v-model="writingStyle.proseStyle" :disabled="writingStyle.contentMode !== 'nsfw'" class="base-select">
                    <option value="literary">文学化</option>
                    <option value="direct">直白</option>
                  </select>
                </div>
                <div class="ws-inline-row">
                  <span class="ws-inline-label">目标字数</span>
                  <div class="ws-wordcount-wrap">
                    <input type="range" v-model.number="writingStyle.wordCount"
                      :min="writingStyle.contentMode === 'nsfw' ? 1000 : 400"
                      :max="writingStyle.contentMode === 'nsfw' ? 3000 : 1500"
                      :disabled="writingStyle.contentMode !== 'nsfw'" step="100" class="ws-range" />
                    <span class="ws-wordcount-val">{{ writingStyle.wordCount }} 字</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="form-group form-span">
              <label>Content JSON（高级编辑）</label>
              <textarea v-model="formContent" rows="12" class="field-textarea code-area"></textarea>
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
.desc-cell { max-width: 240px; overflow: hidden; text-overflow: ellipsis; color: var(--text-tertiary); }
.cover-thumb { width: 40px; height: 40px; border-radius: 4px; object-fit: cover; }
.actions-cell { display: flex; gap: 6px; }
.status-tag { display: inline-block; padding: 2px 8px; border-radius: var(--radius-full); font-size: 11px; font-weight: 500; }
.status-tag.on { background: rgba(76, 175, 142, 0.15); color: #4caf8e; }
.status-tag.off { background: rgba(200, 85, 84, 0.15); color: #c85554; }
.status-tag.admin { background: rgba(255, 193, 7, 0.15); color: #e6a800; }
.btn-del { background: transparent; border-color: #c85554; color: #c85554; }
.empty { text-align: center; padding: 40px; color: var(--text-tertiary); }

.dialog-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
.dialog-panel { background: var(--bg-card); border-radius: var(--radius-lg); padding: var(--space-lg); max-width: 500px; width: 90%; max-height: 80vh; overflow-y: auto; }
.dialog-wide { max-width: 750px; }
.dialog-panel h3 { margin: 0 0 var(--space-md); }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-md); }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-span { grid-column: 1 / -1; }
.form-group label { font-size: 12px; color: var(--text-tertiary); }
.field-textarea { padding: 8px 12px; background: var(--bg-elevated); border: 1px solid var(--border-input); border-radius: var(--radius-sm); color: var(--text-primary); font-size: 13px; resize: vertical; font-family: inherit; }
.code-area { font-family: 'Cascadia Code', 'Fira Code', monospace; font-size: 12px; }
.opening-editor-item {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: var(--space-sm);
  margin-bottom: var(--space-xs);
}
.opening-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.opening-item-num {
  font-size: 11px;
  color: var(--text-tertiary);
  font-weight: 600;
}
.btn-remove-sm {
  font-size: 14px;
  background: none;
  border: none;
  color: var(--color-crimson-soft);
  cursor: pointer;
  padding: 2px 6px;
  line-height: 1;
}
.btn-add-opening {
  display: block;
  width: 100%;
  padding: 8px;
  border: 1px dashed var(--border-primary);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-tertiary);
  font-size: 12px;
  cursor: pointer;
  margin-top: 4px;
}
.btn-add-opening:hover {
  border-color: var(--color-misty-blue-soft);
  color: var(--color-misty-blue-soft);
}
.base-select { padding: 8px 12px; background: var(--bg-elevated); border: 1px solid var(--border-input); border-radius: var(--radius-sm); color: var(--text-primary); font-size: 13px; }
.dialog-actions { display: flex; justify-content: flex-end; gap: var(--space-sm); margin-top: var(--space-lg); }

/* writingStyle inline */
.btn-toggle-ws {
  width: 100%; padding: 10px 14px; border: 1px dashed var(--border-primary); border-radius: var(--radius-md);
  background: transparent; color: var(--text-tertiary); font-size: 13px; cursor: pointer; text-align: left;
  transition: all var(--transition-fast);
}
.btn-toggle-ws:hover { border-color: #f0a040; color: #f0a040; }
.ws-inline { background: var(--bg-elevated); border: 1px solid var(--border-card); border-radius: var(--radius-md); padding: 14px; }
.ws-inline-group { display: flex; flex-direction: column; gap: 12px; }
.ws-inline-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.ws-inline-label { font-size: 12px; color: var(--text-secondary); white-space: nowrap; }
.ws-toggle-label { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text-tertiary); cursor: pointer; }
.ws-toggle-label span.on { color: var(--text-primary); font-weight: 600; }
.ws-checkbox { display: none; }
.ws-toggle-label input[type="checkbox"] { appearance: none; width: 40px; height: 22px; background: var(--bg-tertiary); border-radius: 11px; position: relative; cursor: pointer; outline: none; margin: 0 4px; }
.ws-toggle-label input[type="checkbox"]:checked { background: #f0a040; }
.ws-toggle-label input[type="checkbox"]::after { content: ''; position: absolute; top: 2px; left: 2px; width: 18px; height: 18px; background: #fff; border-radius: 50%; transition: transform 0.2s; }
.ws-toggle-label input[type="checkbox"]:checked::after { transform: translateX(18px); }
.ws-wordcount-wrap { display: flex; align-items: center; gap: 10px; }
.ws-range { flex: 1; height: 6px; -webkit-appearance: none; appearance: none; background: var(--bg-tertiary); border-radius: 3px; outline: none; }
.ws-range::-webkit-slider-thumb { -webkit-appearance: none; width: 16px; height: 16px; border-radius: 50%; background: #f0a040; cursor: pointer; }
.ws-wordcount-val { font-size: 12px; font-weight: 600; color: #f0a040; min-width: 52px; text-align: right; }
</style>
