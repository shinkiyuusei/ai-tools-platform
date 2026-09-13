<script setup>
import { onMounted, reactive, ref } from 'vue'

import {
  createAiModel,
  createAiProvider,
  deleteAiModel,
  deleteAiProvider,
  fetchAiModels,
  getAiProviderList,
  testAiProvider,
  testAiProviderDraft,
  updateAiModel,
  updateAiProvider,
} from '../../api/admin'
import BaseButton from '../../components/base/BaseButton.vue'
import BaseInput from '../../components/base/BaseInput.vue'
import AppLayout from '../../layouts/AppLayout.vue'

const list = ref([])
const loading = ref(false)

// ---- Provider dialog ----
const providerDialog = ref(false)
const providerForm = reactive({
  id: null,
  key: '',
  name: '',
  adapter: 'openai',
  baseUrl: '',
  apiKey: '',
  apiKeyMasked: '',
  isActive: true,
  sortOrder: 0,
})
const isEdit = ref(false)

// Result of the dialog's "测试连接". The page-level toast sits *under* the
// dialog overlay (same z-index, painted earlier in the DOM), so a result
// raised while the dialog is open has to be rendered inside the dialog.
const draftTest = reactive({ testing: false, ok: null, text: '' })

function resetDraftTest() {
  draftTest.testing = false
  draftTest.ok = null
  draftTest.text = ''
}

// ---- Model dialog ----
const modelDialog = ref(false)
const modelForm = reactive({
  id: null,
  providerId: null,
  modelId: '',
  displayName: '',
  isActive: true,
  isDefault: false,
  sortOrder: 0,
})
const isModelEdit = ref(false)

const busyId = ref(null)   // provider id currently testing/fetching
const toast = ref('')

function flash(msg) {
  toast.value = msg
  setTimeout(() => (toast.value = ''), 2500)
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getAiProviderList()
    list.value = res.data.list
  } finally {
    loading.value = false
  }
}

// ---- Provider ----
function openCreateProvider() {
  isEdit.value = false
  Object.assign(providerForm, {
    id: null, key: '', name: '', adapter: 'openai',
    baseUrl: '', apiKey: '', apiKeyMasked: '',
    isActive: true, sortOrder: 0,
  })
  resetDraftTest()
  providerDialog.value = true
}

function openEditProvider(p) {
  isEdit.value = true
  Object.assign(providerForm, p, { apiKey: '' })
  resetDraftTest()
  providerDialog.value = true
}

async function handleTestDraft() {
  if (!providerForm.baseUrl) return
  draftTest.testing = true
  draftTest.ok = null
  draftTest.text = ''
  try {
    const res = await testAiProviderDraft({
      id: providerForm.id,
      baseUrl: providerForm.baseUrl,
      // Blank on edit means "unchanged" — send the mask so the backend
      // falls back to the stored key instead of testing with an empty one.
      apiKey: providerForm.apiKey || providerForm.apiKeyMasked,
    })
    draftTest.ok = res.data.ok
    draftTest.text = res.data.ok
      ? `连接成功，上游返回 ${res.data.modelCount} 个模型`
      : `连接失败：${res.data.error}`
  } catch (e) {
    draftTest.ok = false
    draftTest.text = `测试失败：${e.message}`
  } finally {
    draftTest.testing = false
  }
}

async function handleProviderSubmit() {
  if (!providerForm.key || !providerForm.name || !providerForm.baseUrl) return
  loading.value = true
  try {
    const payload = {
      key: providerForm.key,
      name: providerForm.name,
      adapter: providerForm.adapter,
      baseUrl: providerForm.baseUrl,
      isActive: providerForm.isActive,
      sortOrder: providerForm.sortOrder,
    }
    // Send apiKey only when admin typed a new one
    if (providerForm.apiKey) payload.apiKey = providerForm.apiKey

    if (isEdit.value) {
      await updateAiProvider(providerForm.id, payload)
    } else {
      await createAiProvider(payload)
    }
    providerDialog.value = false
    fetchList()
  } finally {
    loading.value = false
  }
}

async function handleDeleteProvider(id) {
  if (!confirm('确认删除此提供商？其下所有模型会一并删除。')) return
  await deleteAiProvider(id)
  fetchList()
}

async function handleTest(id) {
  busyId.value = id
  try {
    const res = await testAiProvider(id)
    flash(res.data.ok ? `连接成功（${res.data.modelCount} 个模型）` : `连接失败：${res.data.error}`)
  } catch (e) {
    flash(`测试失败：${e.message}`)
  } finally {
    busyId.value = null
  }
}

async function handleFetchModels(id) {
  if (!confirm('从上游拉取会覆盖此提供商现有的全部模型，继续？')) return
  busyId.value = id
  try {
    const res = await fetchAiModels(id)
    flash(`已拉取 ${res.data.count} 个模型`)
    fetchList()
  } catch (e) {
    flash(`拉取失败：${e.message}`)
  } finally {
    busyId.value = null
  }
}

// ---- Model ----
function openCreateModel(providerId) {
  isModelEdit.value = false
  Object.assign(modelForm, {
    id: null, providerId, modelId: '', displayName: '',
    isActive: true, isDefault: false, sortOrder: 0,
  })
  modelDialog.value = true
}

function openEditModel(m, providerId) {
  isModelEdit.value = true
  Object.assign(modelForm, m, { providerId })
  modelDialog.value = true
}

async function handleModelSubmit() {
  if (!modelForm.modelId) return
  loading.value = true
  try {
    const payload = {
      providerId: modelForm.providerId,
      modelId: modelForm.modelId,
      displayName: modelForm.displayName || modelForm.modelId,
      isActive: modelForm.isActive,
      isDefault: modelForm.isDefault,
      sortOrder: modelForm.sortOrder,
    }
    if (isModelEdit.value) {
      await updateAiModel(modelForm.id, payload)
    } else {
      await createAiModel(payload)
    }
    modelDialog.value = false
    fetchList()
  } finally {
    loading.value = false
  }
}

async function handleDeleteModel(id) {
  if (!confirm('确认删除此模型？')) return
  await deleteAiModel(id)
  fetchList()
}

onMounted(fetchList)
</script>

<template>
  <AppLayout>
    <div class="page">
      <div class="header-row">
        <h1>AI 提供商管理</h1>
        <BaseButton @click="openCreateProvider">新增提供商</BaseButton>
      </div>

      <transition name="fade">
        <div v-if="toast" class="toast">{{ toast }}</div>
      </transition>

      <div v-if="loading" class="empty">加载中…</div>

      <section v-for="p in list" :key="p.id" class="provider-card">
        <header class="provider-head">
          <div class="provider-title">
            <span class="provider-name">{{ p.name }}</span>
            <span class="provider-key">[{{ p.key }}]</span>
            <span class="provider-adapter">{{ p.adapter }}</span>
            <span v-if="!p.isActive" class="badge-off">已停用</span>
          </div>
          <div class="provider-actions">
            <button class="action-btn" :disabled="busyId === p.id" @click="handleTest(p.id)">测试</button>
            <button class="action-btn" :disabled="busyId === p.id" @click="handleFetchModels(p.id)">拉取模型</button>
            <button class="action-btn" @click="openEditProvider(p)">编辑</button>
            <button class="action-btn danger" @click="handleDeleteProvider(p.id)">删除</button>
          </div>
        </header>

        <div class="provider-meta">
          <div><span class="meta-label">Base URL</span><code>{{ p.baseUrl }}</code></div>
          <div><span class="meta-label">API Key</span><code>{{ p.apiKeyMasked || '(未设置)' }}</code></div>
        </div>

        <table v-if="p.models?.length" class="model-table">
          <thead>
            <tr>
              <th>modelId</th><th>展示名</th><th>默认</th><th>状态</th><th>排序</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in p.models" :key="m.id">
              <td><code>{{ m.modelId }}</code></td>
              <td>{{ m.displayName }}</td>
              <td>{{ m.isDefault ? '★' : '' }}</td>
              <td>{{ m.isActive ? '启用' : '停用' }}</td>
              <td>{{ m.sortOrder }}</td>
              <td>
                <button class="action-btn" @click="openEditModel(m, p.id)">编辑</button>
                <button class="action-btn danger" @click="handleDeleteModel(m.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-inline">暂无模型，可点上方「拉取模型」从上游自动获取</div>

        <div class="model-add-row">
          <BaseButton variant="secondary" @click="openCreateModel(p.id)">+ 手动添加模型</BaseButton>
        </div>
      </section>

      <div v-if="!list.length && !loading" class="empty">暂无提供商，点击右上「新增提供商」</div>

      <!-- Provider dialog -->
      <div v-if="providerDialog" class="dialog-overlay" @click.self="providerDialog = false">
        <div class="dialog">
          <h2>{{ isEdit ? '编辑提供商' : '新增提供商' }}</h2>
          <div class="form-group">
            <BaseInput v-model="providerForm.key" :disabled="isEdit" placeholder="deepseek / openai / custom-1" label="标识 key" />
          </div>
          <div class="form-group">
            <BaseInput v-model="providerForm.name" placeholder="展示名" label="名称" />
          </div>
          <div class="form-group">
            <label class="field-label">Adapter 类</label>
            <select v-model="providerForm.adapter" class="select">
              <option value="openai">openai (兼容 OpenAI 协议)</option>
              <option value="deepseek">deepseek</option>
              <option value="gemini">gemini</option>
            </select>
          </div>
          <div class="form-group">
            <BaseInput v-model="providerForm.baseUrl" placeholder="https://api.openai.com/v1" label="Base URL" />
          </div>
          <div class="form-group">
            <BaseInput
              v-model="providerForm.apiKey"
              :placeholder="isEdit ? `${providerForm.apiKeyMasked}（不改请留空）` : 'sk-...'"
              label="API Key"
              autocomplete="new-password"
            />
          </div>
          <div class="form-group">
            <BaseButton
              variant="secondary"
              :loading="draftTest.testing"
              :disabled="!providerForm.baseUrl || draftTest.testing"
              @click="handleTestDraft"
            >
              测试连接
            </BaseButton>
            <p
              v-if="draftTest.text"
              class="draft-test-result"
              :class="draftTest.ok ? 'is-ok' : 'is-fail'"
            >
              {{ draftTest.text }}
            </p>
          </div>
          <div class="form-group form-row">
            <label class="checkbox">
              <input type="checkbox" v-model="providerForm.isActive" /> 启用
            </label>
            <label class="field-label">排序</label>
            <BaseInput v-model.number="providerForm.sortOrder" type="number" />
          </div>
          <div class="dialog-actions">
            <BaseButton variant="secondary" @click="providerDialog = false">取消</BaseButton>
            <BaseButton :loading="loading" @click="handleProviderSubmit">保存</BaseButton>
          </div>
        </div>
      </div>

      <!-- Model dialog -->
      <div v-if="modelDialog" class="dialog-overlay" @click.self="modelDialog = false">
        <div class="dialog">
          <h2>{{ isModelEdit ? '编辑模型' : '新增模型' }}</h2>
          <div class="form-group">
            <BaseInput v-model="modelForm.modelId" :disabled="isModelEdit" placeholder="gpt-4o / deepseek-v4-flash" label="modelId (请求体里的 model 字段)" />
          </div>
          <div class="form-group">
            <BaseInput v-model="modelForm.displayName" placeholder="留空则同 modelId" label="展示名" />
          </div>
          <div class="form-group form-row">
            <label class="checkbox">
              <input type="checkbox" v-model="modelForm.isActive" /> 启用
            </label>
            <label class="checkbox">
              <input type="checkbox" v-model="modelForm.isDefault" /> 设为默认
            </label>
          </div>
          <div class="form-group">
            <BaseInput v-model.number="modelForm.sortOrder" type="number" label="排序" />
          </div>
          <div class="dialog-actions">
            <BaseButton variant="secondary" @click="modelDialog = false">取消</BaseButton>
            <BaseButton :loading="loading" @click="handleModelSubmit">保存</BaseButton>
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

.toast {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  padding: 8px 16px;
  border-radius: var(--radius-md);
  z-index: var(--z-modal);
  font-size: var(--text-sm);
}

.provider-card {
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: 16px;
  margin-bottom: 16px;
}

.provider-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.provider-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.provider-name {
  font-weight: 600;
  font-size: var(--text-md);
}

.provider-key {
  color: var(--text-tertiary);
  font-size: var(--text-xs);
}

.provider-adapter {
  font-size: var(--text-xs);
  padding: 2px 6px;
  border: 1px solid var(--border-card);
  border-radius: 4px;
  color: var(--text-tertiary);
}

.badge-off {
  font-size: var(--text-xs);
  padding: 2px 6px;
  background: var(--color-crimson-soft);
  color: #fff;
  border-radius: 4px;
}

.provider-actions {
  display: flex;
  gap: 8px;
}

.provider-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
  font-size: var(--text-sm);
}

.provider-meta .meta-label {
  display: inline-block;
  width: 80px;
  color: var(--text-tertiary);
}

.provider-meta code {
  background: var(--bg-overlay);
  padding: 2px 6px;
  border-radius: 4px;
  word-break: break-all;
}

.model-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.model-table th,
.model-table td {
  padding: 8px;
  text-align: left;
  border-bottom: 1px solid var(--border-card);
}

.model-table th {
  color: var(--text-tertiary);
  font-weight: 600;
}

.empty-inline {
  color: var(--text-tertiary);
  padding: 12px 0;
  font-size: var(--text-sm);
}

.model-add-row {
  margin-top: 8px;
}

.action-btn {
  border: none;
  background: none;
  color: var(--color-misty-blue-soft);
  cursor: pointer;
  font-size: var(--text-xs);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
  width: 480px;
  max-width: 90vw;
}

.dialog h2 {
  font-size: var(--text-lg);
  margin-bottom: var(--space-lg);
}

.form-group {
  margin-bottom: var(--space-md);
}

.form-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.field-label {
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  display: block;
  margin-bottom: 4px;
}

.draft-test-result {
  margin: 8px 0 0;
  font-size: var(--text-xs);
  word-break: break-all;
}

.draft-test-result.is-ok {
  color: var(--color-misty-blue-soft);
}

.draft-test-result.is-fail {
  color: var(--color-crimson-soft);
}

.select {
  width: 100%;
  padding: 8px;
  background: var(--bg-overlay);
  border: 1px solid var(--border-card);
  border-radius: 4px;
  color: inherit;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-sm);
  cursor: pointer;
}

.dialog-actions {
  display: flex;
  gap: var(--space-sm);
  justify-content: flex-end;
  margin-top: var(--space-lg);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
