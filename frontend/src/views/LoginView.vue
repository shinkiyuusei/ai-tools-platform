<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { login } from '../api/user'
import { useAuthStore } from '../stores/auth'
import BaseButton from '../components/base/BaseButton.vue'
import BaseInput from '../components/base/BaseInput.vue'
import AppLayout from '../layouts/AppLayout.vue'

const router = useRouter()
const auth = useAuthStore()

const form = ref({ account: '', password: '', remember: false })
const loading = ref(false)
const errorMsg = ref('')

const handleLogin = async () => {
  errorMsg.value = ''
  if (!form.value.account || !form.value.password) {
    errorMsg.value = '请输入账号和密码'
    return
  }
  loading.value = true
  try {
    const res = await login({ ...form.value })
    auth.setAuth(res.data.token, res.data.refreshToken, res.data.userInfo)
    router.push('/create')
  } catch (err) {
    errorMsg.value = err.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AppLayout>
    <section class="auth-page animate-fade-in-scale">
      <div class="auth-card">
        <div class="auth-header">
          <div class="auth-icon">◇</div>
          <h1>欢迎回来</h1>
          <p>登录以继续你的创作之旅</p>
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

        <div class="form-group">
          <BaseInput v-model="form.account" placeholder="手机号 / 邮箱" label="账号" />
        </div>
        <div class="form-group">
          <BaseInput v-model="form.password" placeholder="密码" type="password" label="密码" />
        </div>

        <label class="checkbox">
          <input v-model="form.remember" type="checkbox" />
          <span>记住我</span>
        </label>

        <BaseButton :loading="loading" block size="lg" @click="handleLogin">登 录</BaseButton>

        <div class="links">
          <router-link to="/register">创建账号</router-link>
          <router-link to="/forgot-password">忘记密码</router-link>
        </div>
      </div>
    </section>
  </AppLayout>
</template>

<style scoped>
.auth-page {
  max-width: 420px;
  margin: 0 auto;
  padding-top: var(--space-3xl);
}

.auth-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-card);
  padding: var(--space-2xl) var(--space-xl);
}

.auth-header {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.auth-icon {
  font-size: 36px;
  color: var(--color-misty-blue);
  margin-bottom: var(--space-md);
  opacity: 0.6;
}

.auth-header h1 {
  font-size: var(--text-xl);
  margin-bottom: var(--space-xs);
}

.auth-header p {
  color: var(--text-tertiary);
  font-size: var(--text-sm);
  margin: 0;
}

.error-msg {
  background: rgba(200, 85, 84, 0.08);
  border: 1px solid rgba(200, 85, 84, 0.15);
  color: var(--color-crimson-soft);
  padding: 10px 14px;
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
  font-size: var(--text-sm);
}

.form-group {
  margin-bottom: var(--space-md);
}

.checkbox {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin: var(--space-md) 0;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
}

.checkbox input {
  accent-color: var(--color-misty-blue);
}

.links {
  display: flex;
  justify-content: space-between;
  margin-top: var(--space-xl);
  font-size: var(--text-sm);
}

.links a {
  color: var(--text-tertiary);
  transition: color var(--transition-fast);
}

.links a:hover {
  color: var(--color-misty-blue-soft);
}
</style>
