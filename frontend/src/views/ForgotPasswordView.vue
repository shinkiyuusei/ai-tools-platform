<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { resetPassword } from '../api/user'
import BaseButton from '../components/base/BaseButton.vue'
import BaseInput from '../components/base/BaseInput.vue'
import AppLayout from '../layouts/AppLayout.vue'

const router = useRouter()

const form = ref({ account: '', newPassword: '', confirmPassword: '' })
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const handleReset = async () => {
  errorMsg.value = ''
  if (!form.value.account) {
    errorMsg.value = '请输入手机号或邮箱'
    return
  }
  if (form.value.newPassword.length < 6) {
    errorMsg.value = '新密码长度不能少于6位'
    return
  }
  if (form.value.newPassword !== form.value.confirmPassword) {
    errorMsg.value = '两次密码输入不一致'
    return
  }
  loading.value = true
  try {
    await resetPassword({
      account: form.value.account,
      newPassword: form.value.newPassword,
    })
    successMsg.value = '密码重置成功，即将跳转登录页…'
    setTimeout(() => router.push('/login'), 2000)
  } catch (err) {
    errorMsg.value = err.message || '重置失败'
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
          <h1>重置密码</h1>
          <p>输入账号和新密码</p>
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
        <div v-if="successMsg" class="success-msg">{{ successMsg }}</div>

        <div class="form-group">
          <BaseInput v-model="form.account" placeholder="手机号 / 邮箱" label="账号" />
        </div>
        <div class="form-group">
          <BaseInput v-model="form.newPassword" placeholder="新密码（至少6位）" type="password" label="新密码" />
        </div>
        <div class="form-group">
          <BaseInput v-model="form.confirmPassword" placeholder="确认新密码" type="password" label="确认密码" />
        </div>
        <BaseButton :loading="loading" block size="lg" @click="handleReset">重置密码</BaseButton>

        <div class="links">
          <router-link to="/login">返回登录</router-link>
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

.success-msg {
  background: rgba(61, 107, 86, 0.08);
  border: 1px solid rgba(61, 107, 86, 0.15);
  color: var(--color-dark-green-soft);
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
