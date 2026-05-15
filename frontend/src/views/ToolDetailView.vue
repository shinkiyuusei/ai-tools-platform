<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'

import { generateByTool, getToolDetail } from '../api/tool'
import { useAuthStore } from '../stores/auth'
import BaseButton from '../components/base/BaseButton.vue'
import BaseInput from '../components/base/BaseInput.vue'
import TagBadge from '../components/TagBadge.vue'
import AppLayout from '../layouts/AppLayout.vue'

const route = useRoute()
const auth = useAuthStore()

const loading = ref(false)
const result = ref('')
const detail = ref({
  name: '', desc: '', useDesc: '',
  formConfig: [], isFree: true, isVip: false, useCount: 0,
})
const formState = reactive({})

const buildFormState = (config) => {
  config.forEach((field) => {
    if (field.type === 'select' || field.type === 'text' || field.type === 'textarea') {
      formState[field.field] = ''
    }
  })
}

onMounted(async () => {
  const response = await getToolDetail(route.params.toolId)
  detail.value = response.data
  buildFormState(detail.value.formConfig || [])
})

const submitGenerate = async () => {
  loading.value = true
  try {
    const response = await generateByTool(route.params.toolId, { ...formState })
    const data = response.data
    if (data.recordId) {
      result.value = data.result || ''
    } else if (data.taskId) {
      result.value = `异步任务已提交 (taskId: ${data.taskId})，请等待完成…`
    }
  } catch (err) {
    result.value = ''
    window.dispatchEvent(new CustomEvent('app:error', { detail: err.message || '生成失败' }))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AppLayout>
    <section class="page animate-fade-in">
      <div class="detail-header-card">
        <div class="detail-header">
          <h1>{{ detail.name }}</h1>
          <div class="header-meta">
            <span class="badge" :class="detail.isFree ? 'free' : 'vip'">
              {{ detail.isFree ? '免费' : '会员专属' }}
            </span>
            <span class="use-count">已创作 {{ detail.useCount }} 次</span>
          </div>
        </div>
        <p class="desc">{{ detail.desc }}</p>
        <div v-if="detail.tags?.length" class="detail-tags">
          <TagBadge v-for="tag in detail.tags" :key="tag.id" :tag="tag" />
        </div>
        <p class="tip">{{ detail.useDesc }}</p>
      </div>

      <div class="card">
        <h2>创作配置</h2>
        <p class="card-sub">调整参数开始你的故事创作</p>

        <div v-if="!auth.isLoggedIn() && !detail.isFree" class="login-tip">
          该内容需要登录后使用，请先 <router-link to="/login">登录</router-link>
        </div>

        <div v-for="field in detail.formConfig" :key="field.field" class="form-field">
          <label>
            {{ field.label }}
            <span v-if="field.required" class="required">*</span>
          </label>

          <select
            v-if="field.type === 'select'"
            v-model="formState[field.field]"
            class="base-select"
          >
            <option value="">{{ field.placeholder || '请选择' }}</option>
            <option v-for="opt in field.options" :key="opt" :value="opt">{{ opt }}</option>
          </select>

          <textarea
            v-else-if="field.type === 'textarea'"
            v-model="formState[field.field]"
            class="base-textarea"
            :placeholder="field.placeholder"
            rows="4"
          />

          <BaseInput
            v-else
            v-model="formState[field.field]"
            :placeholder="field.placeholder"
          />
        </div>

        <div class="actions">
          <BaseButton
            :loading="loading"
            :disabled="!auth.isLoggedIn() && !detail.isFree"
            size="lg"
            @click="submitGenerate"
          >开始创作</BaseButton>
        </div>
      </div>

      <div v-if="result" class="card result-card">
        <div class="result-header">
          <h2>创作结果</h2>
          <span class="result-badge">新生成</span>
        </div>
        <div class="result-box">
          <p>{{ result }}</p>
        </div>
      </div>
    </section>
  </AppLayout>
</template>

<style scoped>
.page {
  display: grid;
  gap: var(--space-lg);
}

/* --- Detail Header --- */
.detail-header-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-card);
  padding: var(--space-xl);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-md);
  gap: var(--space-md);
}

.detail-header h1 {
  font-size: var(--text-2xl);
  margin: 0;
}

.header-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--space-sm);
  flex-shrink: 0;
}

.badge {
  font-size: var(--text-xs);
  padding: 4px 14px;
  border-radius: var(--radius-full);
  font-weight: 600;
}

.badge.free {
  background: rgba(61, 107, 86, 0.15);
  color: var(--color-dark-green-soft);
}

.badge.vip {
  background: rgba(238, 162, 180, 0.15);
  color: var(--color-candy-pink);
}

.use-count {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.desc {
  color: var(--text-secondary);
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  margin-bottom: var(--space-sm);
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: var(--space-sm);
}

.tip {
  color: var(--text-tertiary);
  font-size: var(--text-sm);
  font-style: italic;
}

/* --- Card --- */
.card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-card);
  padding: var(--space-xl);
}

.card h2 {
  font-size: var(--text-lg);
  margin-bottom: var(--space-xs);
}

.card-sub {
  color: var(--text-tertiary);
  font-size: var(--text-sm);
  margin-bottom: var(--space-xl);
}

/* --- Login Tip --- */
.login-tip {
  background: rgba(123, 156, 191, 0.08);
  border: 1px solid rgba(123, 156, 191, 0.15);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-lg);
}

.login-tip a {
  color: var(--color-misty-blue-soft);
  font-weight: 500;
}

/* --- Form --- */
.form-field {
  margin-bottom: var(--space-lg);
}

.form-field label {
  display: block;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}

.required {
  color: var(--color-crimson-soft);
}

.base-select {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-input);
  border: 1px solid var(--border-input);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
  transition: all var(--transition-fast);
  cursor: pointer;
}

.base-select:focus {
  outline: none;
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(123, 156, 191, 0.1);
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
  transition: all var(--transition-fast);
}

.base-textarea:focus {
  outline: none;
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(123, 156, 191, 0.1);
}

.actions {
  padding-top: var(--space-sm);
}

/* --- Result --- */
.result-card {
  animation: fadeInUp 0.5s ease-out;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.result-header h2 {
  margin-bottom: 0;
}

.result-badge {
  font-size: var(--text-xs);
  color: var(--color-dark-green-soft);
  background: rgba(61, 107, 86, 0.12);
  padding: 2px 10px;
  border-radius: var(--radius-full);
}

.result-box {
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  border: 1px solid var(--border-card);
}

.result-box p {
  font-family: var(--font-serif);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

/* --- Responsive --- */
@media (max-width: 768px) {
  .detail-header {
    flex-direction: column;
  }

  .header-meta {
    flex-direction: row;
    align-items: center;
    gap: var(--space-md);
  }
}
</style>
