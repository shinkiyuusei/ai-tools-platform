<script setup>
import { ref, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

import { resetPassword, sendCode } from '../api/user'
import BaseButton from '../components/base/BaseButton.vue'
import BaseInput from '../components/base/BaseInput.vue'
import AppLayout from '../layouts/AppLayout.vue'

const router = useRouter()

const form = ref({ account: '', code: '', newPassword: '', confirmPassword: '' })
const step = ref(1)
const loading = ref(false)
const sending = ref(false)
const countdown = ref(0)
const errorMsg = ref('')
const successMsg = ref('')

let timer = null

const handleSendCode = async () => {
  if (!form.value.account) {
    errorMsg.value = '请输入手机号或邮箱'
    return
  }
  sending.value = true
  try {
    await sendCode({ phone: form.value.account, email: form.value.account, type: 'reset' })
    step.value = 2
    countdown.value = 60
    timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        clearInterval(timer)
        timer = null
      }
    }, 1000)
  } catch (err) {
    errorMsg.value = err.message || '发送失败'
  } finally {
    sending.value = false
  }
}

const handleReset = async () => {
  errorMsg.value = ''
  if (!form.value.code) {
    errorMsg.value = '请输入验证码'
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
      code: form.value.code,
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

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <AppLayout>
    <section class="auth-page animate-fade-in-scale">
      <div class="auth-card">
        <div class="auth-header">
          <div class="auth-icon">◇</div>
          <h1>重置密码</h1>
          <p>通过手机号或邮箱重置</p>
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
        <div v-if="successMsg" class="success-msg">{{ successMsg }}</div>

        <template v-if="step === 1">
          <div class="form-group">
            <BaseInput v-model="form.account" placeholder="手机号 / 邮箱" label="账号" />
          </div>
          <BaseButton :loading="sending" block size="lg" @click="handleSendCode">获取验证码</BaseButton>
        </template>

        <template v-else>
          <div class="form-group">
            <BaseInput v-model="form.code" placeholder="验证码" label="验证码" />
          </div>
          <div class="code-info">
            <span v-if="countdown > 0">{{ countdown }}s 后可重新发送</span>
            <a v-else class="resend" @click="handleSendCode">重新发送</a>
          </div>
          <div class="form-group">
            <BaseInput v-model="form.newPassword" placeholder="新密码（至少6位）" type="password" label="新密码" />
          </div>
          <div class="form-group">
            <BaseInput v-model="form.confirmPassword" placeholder="确认新密码" type="password" label="确认密码" />
          </div>
          <BaseButton :loading="loading" block size="lg" @click="handleReset">重置密码</BaseButton>
        </template>

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

.code-info {
  margin: -var(--space-sm) 0 var(--space-md);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.resend {
  color: var(--color-misty-blue-soft);
  cursor: pointer;
}

.resend:hover {
  color: var(--color-misty-blue);
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
