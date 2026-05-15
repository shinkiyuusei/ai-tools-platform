<script setup>
import { reactive, ref, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

import { register, sendCode } from '../api/user'
import { useAuthStore } from '../stores/auth'
import BaseButton from '../components/base/BaseButton.vue'
import BaseInput from '../components/base/BaseInput.vue'
import AppLayout from '../layouts/AppLayout.vue'

const router = useRouter()
const auth = useAuthStore()

const form = ref({ phone: '', email: '', code: '', password: '', confirmPassword: '' })
const loading = ref(false)
const sending = ref(false)
const countdown = ref(0)
const errorMsg = ref('')

let timer = null

const handleSendCode = async () => {
  const target = form.value.phone || form.value.email
  if (!target) {
    errorMsg.value = '请先输入手机号或邮箱'
    return
  }
  sending.value = true
  try {
    await sendCode({ phone: form.value.phone, email: form.value.email, type: 'register' })
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

const handleRegister = async () => {
  errorMsg.value = ''
  if (!form.value.phone && !form.value.email) {
    errorMsg.value = '请输入手机号或邮箱'
    return
  }
  if (!form.value.code) {
    errorMsg.value = '请输入验证码'
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
      phone: form.value.phone,
      email: form.value.email,
      code: form.value.code,
      password: form.value.password,
    })
    auth.setAuth(res.data.token, res.data.refreshToken, res.data.userInfo)
    router.push('/create')
  } catch (err) {
    errorMsg.value = err.message || '注册失败'
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
          <h1>创建账号</h1>
          <p>加入知弄 · 开启你的创作之旅</p>
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

        <div class="form-group">
          <BaseInput v-model="form.phone" placeholder="手机号" label="手机号" />
        </div>
        <div class="form-group">
          <BaseInput v-model="form.email" placeholder="邮箱（选填）" label="邮箱" />
        </div>

        <div class="code-row">
          <div class="form-group code-input">
            <BaseInput v-model="form.code" placeholder="验证码" label="验证码" />
          </div>
          <BaseButton
            :loading="sending"
            :disabled="countdown > 0"
            variant="secondary"
            size="sm"
            class="code-btn"
            @click="handleSendCode"
          >
            {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
          </BaseButton>
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

.code-row {
  display: flex;
  gap: var(--space-sm);
  align-items: flex-end;
}

.code-input {
  flex: 1;
}

.code-btn {
  margin-bottom: var(--space-md);
  flex-shrink: 0;
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
