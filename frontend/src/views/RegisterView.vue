<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { register } from '../api/user'
import { useAuthStore } from '../stores/auth'
import BaseButton from '../components/base/BaseButton.vue'
import BaseInput from '../components/base/BaseInput.vue'
import AppLayout from '../layouts/AppLayout.vue'

const router = useRouter()
const auth = useAuthStore()

const form = ref({ email: '', password: '', confirmPassword: '' })
const loading = ref(false)
const errorMsg = ref('')

const handleRegister = async () => {
  errorMsg.value = ''
  if (!form.value.email) {
    errorMsg.value = '请输入邮箱'
    return
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.value.email)) {
    errorMsg.value = '邮箱格式不正确'
    return
  }
  if (form.value.password.length < 6) {
    errorMsg.value = '密码长度不能少于6位'
    return
  }
  if (form.value.password !== form.value.confirmPassword) {
    errorMsg.value = '两次密码输入不一致'
    return
  }
  loading.value = true
  try {
    const res = await register({
      email: form.value.email,
      password: form.value.password,
    })
    auth.setUserInfo(res.data.userInfo)
    router.push('/create')
  } catch (err) {
    errorMsg.value = err.message || '注册失败'
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
          <h1>创建账号</h1>
          <p>加入知弄 · 开启你的创作之旅</p>
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

        <div class="form-group">
          <BaseInput v-model="form.email" placeholder="邮箱" label="邮箱" />
        </div>

        <div class="form-group">
          <BaseInput v-model="form.password" placeholder="密码（至少6位）" type="password" label="密码" />
        </div>
        <div class="form-group">
          <BaseInput v-model="form.confirmPassword" placeholder="确认密码" type="password" label="确认密码" />
        </div>

        <BaseButton :loading="loading" block size="lg" @click="handleRegister">注 册</BaseButton>

        <div class="links">
          <router-link to="/login">已有账号？去登录</router-link>
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

.links {
  margin-top: var(--space-xl);
  text-align: center;
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
